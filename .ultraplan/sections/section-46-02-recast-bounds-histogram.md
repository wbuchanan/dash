# Section 46-02: recast(): second bound kept; histogram recast style; RH-8 documented

> Part of: WP-46 (recast() and horizontal, P14) · Items: RH-3, RH-5, RH-8 · Risk: yellow · Batch: 46.2 · Depends on: 46-01 · Blocks: none · Tasks: 6, 3 commits · Case-id prefix: Q4602

## Overview

**What is wrong today.**
- **RH-3 (with RH-4).** "A range source or ciplot() drawn as a yx type leaves the second bound out of the axis, the default title and the key." twoway: `rline lo hi x, recast(line)` "the line runs through lo, but the y axis spans both bounds (8..51, ticks 10-50) and is titled Lovar/Hivar"; `(rcap lo hi x, recast(scatter)) (scatter y x)` keys "Lovar/Hivar" (y2xview_g.class:60-75: ranges = min/max of yvar and y2var). dash: "The y axis is 7.2..41.8 (ticks 10-40), titled Lovar, and the key is Lovar" -- dash.ado:6660 `if "\`_rc_kind'" == "range2yx" local yvar "\`yvar1'"` drops yvar2. RH-4: `lfitci y x, ciplot(area|bar|scatter)` -- twoway's y axis spans both limits (10..50), dash's 9.4..36.1: `GlyphMapper._dash_draw_range_as` (dash_render.py:26601-26635) hands a yx target to `_dash_draw_xy_as(fig, source, xcol, locol, ...)` with the lower limit only (:26618-26620).
- **RH-5 (with RH-6, RH-7).** "histogram recast(): drawn in the target's style (twoway keeps the histogram style), bars one unit wide (twoway uses the bin width), and 0 left out of the height axis." twoway restyles every recast histogram view `style(histogram)` (twoway_histogram_parse.class:188: stcolor fill #3191ff, outline #5faaff at 4.86) and sets `bar_size = barwidth*(100-gap)/100` for every viewtype (:193); the unswapped serset carries a zero series (:160-170), so 0 is in the y extent (`histogram y, recast(area)` on three equal bins: y 0..0.0303). dash: the target's p1 chain (`_dash_draw_xy_as` docstring :26554-26557), `VBar width = 1`, and `_dash_tag_eval_extent` (:61880-61931) returns early on any recast (:61897-61898), so on that data the axis is "-1.02..1.08" with ticks -0.97/1.03.
- **RH-8 (documented, Q25).** "histogram/rbar with recast() plus horizontal: twoway draws a broken swapped serset; dash draws a clean transpose." twoway: `histogram, recast(bar|area|spike|rbar) horizontal` draws vertical bars a bin wide at x = height (P06 xs -5.47..5.53), rbar draws nothing (P08), `recast(rline) horizontal` draws the height curve twice (Q23), `rbar lo hi x, recast(rcap) horizontal` draws x = lo against y = hi (P12); "Only recast(line), (scatter) and (connected) come out as a clean transpose". Ruling Q25: keep dash's clean transpose; list twoway's broken picture under Differences with a measured example (Appendix B HR-21, this section's).

**After this section.** A range source drawn as a yx type, and ciplot() drawn as one, keep both bounds on the axis and are titled and keyed with both bounds, in both modes and after a move; a recast histogram is drawn in the histogram's own style, its bars a bin wide (gap included), 0 on its height axis; dash.sthlp's Differences lists RH-8 with its measured example, pinned by a help-claim test and a probe showing dash's transpose.

**Why together.** All three are the recast drawing path of derived and range sources (`_dash_draw_range_as`, `map_histogram`'s recast branches, `_dash_tag_eval_extent`), and the saved page's recast refit (`dash_recast_data`) -- this section's JS twin.

**Test order and commit rule.** Per item, RH-3, RH-5, RH-8: a test task (failure saved, no commit) then a fix task committing `(WP-46 <id>)`. 46-02-01 also measures RH-3 and RH-5 into the recast fixture. No full suite inside the section.

### Section decisions

- **D-46-02.a -- the bound extent renderer.** The second bound joins the axis through an invisible extent renderer drawn from the same source and view as the layer (the pattern map_contour uses for its extent scatter, :24309 docstring): `fig.scatter(x=<x col>, y=<hi col>, source=<the layer's source>, view=<the layer's view>, size=0, fill_alpha=0, line_alpha=0)` tagged `"dash_bound_extent"`, turned with the layer when horizontal. It follows a filter move with no new JS (the view filters it), is kept out of the legend (no label) and out of hover exactly as contour's extent scatter is.
- **D-46-02.b -- titles and key.** A range2yx layer writes `"recast_hi": "<yvar2>"` in its spec (dash.ado); `_dash_legend_key` and `_dash_axis_default_titles` key and title it as its range source would be keyed and titled (the range type's own rule for two y variables), not by the first bound.
- **D-46-02.c -- ciplot yx targets.** `_dash_draw_range_as` passes the upper limit to `_dash_draw_xy_as(..., hicol=hicol)`, which adds a `y2` column to its fresh source and the extent renderer over it; the saved refit's recast roles gain `"y2"` (`dash_recast_data(cols, xs, ys, prev, y2s)`), written from the refitted upper limit; the served redraw rebuilds the source through the mapper, so it carries `y2` already.
- **D-46-02.d -- histogram style.** The recast target is drawn with the histogram's own resolved colours and width: the fill (`color`/`fcolor`), the outline and line (`lcolor`, `mlcolor`) and the line width (`lwidth`, `mlwidth`) that `map_histogram` uses for its bars are put into the target's options copy unless the user gave that option; `_HIST_RECAST_KEYS` are stripped from the yx branch too.
- **D-46-02.e -- bar width and centres.** A `bar` target takes `barwidth = (_hr[0] - _hl[0])` (the bin width after gap, as the rbar branch :22234-22238); every yx target's x is `(_hl + _hr) / 2` (gap and baroffset included) at build and in the saved recount (`_FILTER_JS` :34613-34615, :34655-34657 read `edges` today).
- **D-46-02.f -- zero on the height axis.** `_dash_tag_eval_extent` stamps `{"letter": "x" if horizontal else "y", "v": [0.0]}` for a recast histogram (any target) instead of returning; the stamp is constant, so no move rewrites it.
- **D-46-02.g -- RH-8's sentence.** Under Differences (dash.sthlp `{marker differences}`): one line "{cmd:histogram} and {cmd:rbar} with {cmd:recast()} and {cmd:horizontal} are drawn turned; {cmd:twoway} draws a broken picture there -- see {help dash##recast:Recast}"; the topic note in the Recast paragraph gives the measured example (`histogram mpg, recast(bar) horizontal`: twoway draws upright bars a bin wide at x = the bin's height on an x axis of -5.47..5.53; `rbar lo hi x, recast(rcap) horizontal` draws x = lo against y = hi; dash draws the exact transpose of the upright layer in both cases).

## Risk: [yellow] -- axis extents of recast layers and the saved recount

**Why.** The extent renderer reaches the axis hull of every recast range layer; the histogram style change recolours every recast histogram.

**Risk factors.** 1. `_dash_refinish_axes`/`_DASH_AXIS_FINISH_JS` read glyph coordinates of renderers; the extent renderer must be one they read (contour's precedent) and one hover/legend skip. 2. `dash_recast_data` is shared by histogram and kdensity recounts (:34611-34658, :34759); the new `y2s` argument defaults to absent. 3. RH-5's style must not override a user's colour.

**Mitigation.** Pytest on the extent in both modes and after a saved move (node through test/js_runner.py) and a served move; the fixture's axis ranges (P17-P19, P27/P28, P23/P24, R08 re-measured) as truth; parity entries.

## Dependencies

- **Depends on:** 46-01 (kinds and orientation of recast layers).
- **Blocks:** none (WE of WP-46 follows).
- **Parallel batch:** 46.2 alone; JS = yes (`_FILTER_JS`).

## Evidence

- dash.ado `_dash_process_segment` :6655-6688 (range2yx `yvar` :6660); spec writer `_rcf` :7107-7110, plot JSON :7149, :7156.
- `_RECAST_DRAWN` :26543; `_dash_draw_xy_as(self, fig, source, xcol, ycol, target, options, color_idx=0)` :26546-26585 (fresh source `pts` with `x`, `y`; options strip only `recast`, `type` :26575-26576); `_HIST_RECAST_KEYS`, `_CIPLOT_RANGE`, `_FIT_DRAW_KEYS` :26587-26599; `_dash_draw_range_as` :26601-26635.
- `map_histogram` :22094; range recast branch :22227-22246 (strips `_HIST_RECAST_KEYS`; rbar barwidth :22234-22238); yx branch :22247-22272 (`_mid` from `axis_edges` :22250-22254; full `options` passed :22256-22258; `_tag_recast(..., self._hist_agg_config(...), ...)` :22262-22269); `_tag_recast(added, xs, ys, cfg, rows)` :22366-22412 (`recast_cols` roles).
- `_dash_tag_eval_extent` :61880-61931 (recast early return :61897-61898; histogram `vals = [0.0]` :61904-61906).
- `_FILTER_JS`: `dash_recast_data(cols, xs, ys, prev)` :34420-34432; `_prev` :34529; histogram recount for a recast target :34611-34616 and :34652-34658 (`_mx` from `edges[b]`, `edges = ac.bin_edges` :34551); kdensity :34668, :34759.
- `_dash_legend_key` :58149 (and `_dash_axis_default_titles`, grep `def _dash_axis_default_titles`): range types' keys and titles (re-read their two-variable rule).
- twoway: y2xview_g.class:60-75; twoway_histogram_parse.class:148-157, :160-193; twoway_yxview_parse.class:319-324, :456-468, :973-978; scheme-stcolor.scheme:65-68 (histogram colours).
- Fixtures: recast_truth.json (scripts/extract_recast_truth.do; `D-histogram-line` counts only; `W-rl-line` counts only -- no axis truth); horizontal_truth.json (46-01's rows).
- Pinned tests (flip in place): test/test_recast.py `TestRecastKeepsTheSeriesLabel::test_key` (:184-188; `{"type": "line", "recast_from": "rline", ...}` keyed `"mpg"` -> the range key with both bounds; "was a dash-internal pin with no twoway truth: twoway keys Lovar/Hivar"); `TestBaseRecast::test_drawn_as_the_target` (:206-217; the rline->line layer equals a plain line -> equals a plain line plus one `dash_bound_extent` renderer, compared without it); `TestDerivedRecast::test_bar_is_one_unit_wide` (:171-176) is kdensity's and stays (only histogram changes); `_DERIVED` (:87-99) `("histogram", "line", ["Line"])` stays. test/test_recast_refit.py (`test_js_equals_python`, `test_turned_histogram_line_follows_the_move`) must stay green with the new centres (they compare JS with Python). test/test_recast_range_pc.py:123 `test_rbar_is_the_histograms_bar` stays green. test/test_wp31_truth.cscript U41-16 (:10812-10826, colours only) and test_wp30_truth.cscript RC-20 (`rline y y2 x, recast(line)|Line:8`, glyph counts) -- re-run; a Scatter count change is a flip with the reason.

## User stories

- US-46-02.1 As the Stata user with an existing twoway command, I want `rline lo hi x, recast(line)` and `lfitci y x, ciplot(area)` to keep both bounds on the axis and in the key, as twoway does.
- US-46-02.2 As the Stata user, I want `histogram mpg, recast(bar)` drawn in the histogram's colours with bars as wide as the bins and 0 on the axis, as twoway draws it.
- US-46-02.3 As the Stata user, I want the help to tell me where dash's recast histogram with horizontal differs from twoway's broken picture.

## Business requirements

- BR-46-02.1 A range source drawn as a yx type, and ciplot() drawn as one, put both bounds in the axis range, the default axis title and the key; after a filter move too.
- BR-46-02.2 A recast histogram takes the histogram's fill, outline and line width (unless the user sets them), bars one bin wide after gap(), and 0 on its height axis.
- BR-46-02.3 dash.sthlp's Differences lists RH-8 in one line linked to a measured note.

## Technical requirements

- TR-46-02.1 dash.ado (:6660): keep `local yvar "\`yvar1'"` and add `local _rc_hi "\`yvar2'"`; the spec writer (:7107) appends `,"recast_hi":"\`_rc_hi'"` to `_rcf` when `_rc_kind == "range2yx"`; the exported variables include yvar2 (it is already a plot variable of the segment; confirm the layer's variable list written for `_dash_write_data` still names it, grep `yvar2` in the spec writer).
- TR-46-02.2 `_make_figure_body` is not edited: the extent renderer is added inside the yx target's draw. For a base-recast plot, `_dash_add_glyph` (:61775) receives the plot's options; dash.ado also writes option `recast_hi` (add `recast_hi` to the option-name list at :5429 after `typesfx`), so `_dash_add_glyph` -- after the mapper returns, when `str((options or {}).get("recast_hi", "") or "")` names a column of *source* -- adds the extent renderer (D-46-02.a) with `x=xvar`, `y=recast_hi`, the same `view`. Tag it `["dash_bound_extent"]`; `_dash_is_swatch` must return False for it and the legend builder skip it (it has no `legend_label`); keep it out of the HoverTool's `renderers` the way contour's extent scatter is (re-read map_contour's `extent` lines after :24470).
- TR-46-02.3 `_dash_legend_key(p)` and `_dash_axis_default_titles`: when `p.get("recast_hi")` and `p.get("recast_from")` is a range type, key and title as for a plot of type `recast_from` with `yvar1 = p["yvar"]`, `yvar2 = p["recast_hi"]` (call the existing range branch with a dict copy carrying those keys). `_dash_axis_default_titles` is the body 44-01 (MS-11, WP-44) rewrote to twoway's region rule: the change goes inside its per-plot series step, so the region walk and its `...` are untouched (re-read it at the WP-46 base).
- TR-46-02.4 RH-4: `_dash_draw_xy_as(self, fig, source, xcol, ycol, target, options, color_idx=0, hicol=None)`: when *hicol*, `pts` gains `"y2": np.asarray(data[hicol], float)` (in x order, as `y`), and after the target draws, the extent renderer `fig.scatter(x="x", y="y2", source=pts, size=0, fill_alpha=0, line_alpha=0, tags=["dash_bound_extent"])`; `_dash_draw_range_as` (:26619) passes `hicol=hicol`. The ci fit's saved refit: find where the ciplot target's source is rewritten after a move (grep `ciplot` in `_FILTER_JS` and in `_tag_recast`-like taggers of the fit layers); add role `"y2"` to its `recast_cols` and pass the refitted upper limit as `y2s` to `dash_recast_data`.
- TR-46-02.5 JS twin: `function dash_recast_data(cols, xs, ys, prev, y2s)` -- `else if (role === 'y2') out[k] = y2s ? y2s.slice() : (old && old.length === xs.length ? Array.from(old) : xs.map(() => NaN));` before the `old` branch. In the histogram recount (:34613-34615, :34655-34657) the midpoints become `(_hl[b] + _hr[b]) / 2` (the gap- and baroffset-adjusted edges the same block computes for the bars; re-read where `_hl`/`_hr` are built above :34646) -- matching TR-46-02.7.
- TR-46-02.6 RH-5 style (D-46-02.d): in `map_histogram`'s two recast branches, build `_hs = self._dash_hist_role_opts(options, color_idx)` (new GlyphMapper method beside `_tag_recast`): from the same resolved values the bar branch uses for its fill, outline and width (re-read `map_histogram`'s bar colour lines before the recast branches), return `{"color": fill, "fcolor": fill, "lcolor": line, "mlcolor": line, "mfcolor": fill, "lwidth": lw, "mlwidth": lw}` minus any key the user's *options* hold (and minus `color` when the user gave `color` or `fcolor`); merge into `_hopts` (range branch) and into the yx branch's options copy.
- TR-46-02.7 RH-6: the yx branch uses `_yopts = {k: v for k, v in options.items() if k not in self._HIST_RECAST_KEYS}` plus `recast`, merged with `_hs`; for target `bar`, `_yopts["barwidth"] = "%.17g" % float(_hr[0] - _hl[0])` when bins exist; `_mid["x"] = (np.asarray(_hl, float) + np.asarray(_hr, float)) / 2.0`.
- TR-46-02.8 RH-7: `_dash_tag_eval_extent` (:61897): replace the early return with `if str((options or {}).get("recast", "") or "").strip() and pt != "histogram": return`; the histogram branch (:61904-61906) then stamps 0 for recast layers too (letter by `_dash_is_horizontal_opts(options)`).
- TR-46-02.9 RH-8 help (R3, D-46-02.g): add the Differences line (in the "Differences from twoway" list, after the last drawing item; re-read the list's numbering) and the topic note at the end of the Recast paragraph (dash.sthlp :3581-3615; give it a `{marker recast}` if none exists, checking no marker of that name is taken). Correct :3591-3593 "{cmd:bar} (one x unit wide)" to "({cmd:histogram}: one bin wide; the others: one x unit wide)" and :3588-3589 "a range type named as a yx type draws its first bound" to "... draws its first bound and keeps both on the axis, in its title and key".
- TR-46-02.10 function_test_map.py rows for `_dash_hist_role_opts` (as `GlyphMapper._dash_hist_role_opts`); no copy-list entry (GlyphMapper is copied whole).

## Boundaries

- No change to histogram/rbar recast with horizontal drawing (RH-8: documented only, Q25); no change to kdensity's one-unit recast bars (twoway's rule for derived fits, register A60).
- Do not edit `_dash_hz_check`/`_dash_recast_opt` beyond TR-46-02.1's two lines (46-01 landed).
- `_dash_legend_key`'s key shapes and horizontal kdensity key are 43-04's (RH-13); only the recast_hi key text is touched here.

## Stata truth

Extend `scripts/extract_recast_truth.do` (R7) with axis-reading probes (each drawn; from the SVG through scripts/svg_truth.py: the y (or x) axis label values and range, the axis title texts, the legend texts, the first bar rect's width in data units, the histogram fills/strokes and stroke widths):

| id | cmd |
|---|---|
| RB-01 | `twoway rline y y2 x, recast(line)` |
| RB-02 | `twoway (rcap y y2 x, recast(scatter)) (scatter y x)` |
| RB-03 | `twoway rbar y y2 x, recast(bar)` |
| RB-04 | `twoway lfitci mpg weight, ciplot(area)`; RB-05 `ciplot(bar)`; RB-06 `ciplot(scatter)` (sysuse auto) |
| RH5-01 | `twoway histogram mpg, recast(bar)` (fill, stroke, width, bar width = bin width) |
| RH5-02 | `twoway histogram mpg, recast(area)`; RH5-03 `recast(spike)`; RH5-04 `recast(scatter)`; RH5-05 `recast(bar) gap(50)` |
| RH5-06 | three equal bins: `clear`, `set obs 3`, `gen y = _n`, `twoway histogram y, recast(area)`; RH5-07 `recast(dropline)` (y axis 0..0.0303) |
| RH8-01 | `twoway histogram mpg, recast(bar) horizontal` (xs range: the broken picture) |
| RH8-02 | `twoway rbar y y2 x, recast(rcap) horizontal` |

Regenerate test/fixtures/recast_truth.json through `scripts/stata_slot.sh`; `git add -f`.

## TDD test stubs

In test/test_recast.py (`_MODES`):
- RH-3: `TestRangeRecastBounds::test_axis_spans_both_bounds[mode-RB-01|RB-03]` (y range covers the fixture's label range; red), `::test_key_and_title[mode-RB-01|RB-02]` (red), `::test_after_a_move[saved|served]` (a filter keeping half the rows: the extent renderer's rows equal the layer's; red), `::test_ciplot_yx_spans_both_limits[mode-RB-04|RB-05|RB-06]` (red), `::test_js_y2_role` (node: `dash_recast_data` with role y2; red).
- RH-5: `TestHistogramRecast::test_histogram_style[mode-RH5-01..04]` (fill/line colour and width = the plain histogram's; red), `::test_bar_is_a_bin_wide[mode-RH5-01|RH5-05]` (red), `::test_zero_on_the_height_axis[mode-RH5-06|RH5-07]` (red), `::test_user_colour_wins[mode]` (guard), `::test_js_centres_equal_python` (node, gap(50); red).
- RH-8: `test/test_help_claims_9.py::TestRecastHorizontalDifference::test_the_sentence` (the `_between(_help(), ...)` pattern of test/test_help_claims_1.py reads the Differences line and the topic note; red), `::test_dash_draws_the_transpose[mode]` (`histogram mpg, recast(bar) horizontal` draws HBar renderers whose right edges are the bin heights; guard of today's behaviour).

cscript cases (test/test_wp46_truth.cscript blocks `* ==== S02 RH-3: ... ====`, `S02 RH-5`, `S02 RH-8`):
- Q4602-1 RB-01 under dash and twoway live: dash's built page y range covers twoway's axis labels' range (read with cert_svg.do for twoway, the page's Range1d for dash).
- Q4602-2 RH5-06 under dash: the page's height axis start is at or below 0.
- Q4602-3 `dash histogram mpg, recast(bar) horizontal name(q3)`: rc 0, the page holds an HBar (the documented transpose).

Pinned tests to flip: as Evidence lists.

Parity (R8): `_case("rline recast(line) both bounds", ...)`, `_case("lfitci ciplot(bar)", ...)`, `_case("histogram recast(bar) gap(50)", ...)` (the existing "histogram recast(rbar) gap(50)" entry :2601 is the model).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| second bound | pytest TestRangeRecastBounds; node; Q4602-1 | RB-01..06 | yes |
| histogram recast | pytest TestHistogramRecast; node; Q4602-2 | RH5-01..07 | yes |
| RH-8 documented | help-claim test; Q4602-3 | RH8-01/02 | yes |

- AC-46-02.1 Each item's tests red at its base, green after; failure texts saved.
- AC-46-02.2 Q4602-1..3 PASS; test_recast.py, test_recast_refit.py, test_recast_range_pc.py, test_horizontal.py, test_mode_parity.py, test_help_conformance.py green.
- AC-46-02.3 RH-3 and RH-5 Tracked `Closed in WP-46 ...`; RH-8 `Documented in WP-46 ...`.

## Tasks

**Commit boundary.** 46-02-01/02 -> `Keep a recast range layer's second bound on its axis, title and key (WP-46 RH-3)`; 46-02-03/04 -> `Draw a recast histogram in its own style, a bin wide, from zero (WP-46 RH-5)`; 46-02-05/06 -> `Document recast() with horizontal on histogram and rbar (WP-46 RH-8)`. Branch `wp46-s02`.

<task type="auto" id="46-02-01">
  <name>Measure recast axes, write RH-3 tests</name>
  <files>scripts/extract_recast_truth.do, test/fixtures/recast_truth.json, test/test_recast.py</files>
  <action><![CDATA[Add the probes of "Stata truth" to scripts/extract_recast_truth.do (old rows unchanged), run it through `scripts/stata_slot.sh`, `git add -f` the fixture. Add the RH-3 stubs and the S02 RH-3 block (Q4602-1) to test/test_wp46_truth.cscript, adding `S02` to its run list `w46_run`. Run `python3 -m pytest test/test_recast.py::TestRangeRecastBounds -q -n0 -rf > <scratch>/46-02-01-failure.txt 2>&1; true` and the block. Do not commit.]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/recast_truth.json'))['probes'];print(p['RB-01']['ylabels'], p['RB-02']['legend'], p['RH5-06']['ylabels'][0])"` prints labels reaching 50, a legend entry joining both bound labels with "/", and `0`; `grep -c FAILED <scratch>/46-02-01-failure.txt` is at least 6; the file holds `Q4602-1 FAIL`.]]></verify>
  <done>twoway's recast axes were recorded and RH-3's tests were shown failing.</done>
</task>

<task type="auto" id="46-02-02">
  <name>Keep the second bound, commit RH-3</name>
  <files>dash.ado, dash_render.py, dash.sthlp</files>
  <action><![CDATA[Apply TR-46-02.1 to TR-46-02.5 and TR-46-02.9's :3588-3589 sentence. Flip test/test_recast.py:184-188 and :206-217 in place with their reasons (R9). Run `python3 -m pytest test/test_recast.py test/test_recast_refit.py test/test_recast_range_pc.py test/test_js_runner.py test/test_ci_band_style.py test/test_ciplot_colours.py test/test_fit_options.py -q -n0`, then `python3 -m pytest test/test_mode_parity.py -k recast -q -n0` (one `-k` per run), and the S02 block; re-run test/test_wp30_truth.cscript's RC block once (`WP30_ONLY` of its block id; re-read) and flip RC-20 there only if its Scatter count moved. Append the RH-3 parity entries of TDD stubs (Parity) to `CORPUS` in test/test_mode_parity.py. Close RH-3 (BUGS, Tracked, GAPS4_OPEN (test/test_tracking_documents.py), CHANGELOG "a range type or ciplot() drawn as a yx type keeps both bounds on the axis and in its title and key, as twoway does; rline lo hi x, recast(line) drew y 7.2..41.8 keyed Lovar, now 8..51 keyed Lovar/Hivar (WP-46, RH-3)"; TWOWAY_COVERAGE_AUDIT.md: grep `recast` and `ciplot`, the matching row gains "[WP-46 RH-3: corrected -- a recast range layer keeps its second bound on the axis, title and key]"). Before the commit take BRIEF's closing steps (1)-(3) for RH-3 (Notes "Before every commit" gives each command in full): (1) delete RH-3's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `RH-3 (documented)` or `RH-3 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py RH-3` and delete every row it prints from its `*_KNOWN` table -- a difference RH-3's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with RH-3. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[both pytest runs 0 failed; `python3 -m pytest test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0` passes; `Q4602-1 PASS`; `git log -1 --format=%s` ends `(WP-46 RH-3)`.]]></verify>
  <done>Recast range layers keep both bounds in both modes and after a move; RH-3 is closed.</done>
</task>

<task type="auto" id="46-02-03">
  <name>Write the histogram recast tests</name>
  <files>test/test_recast.py, test/test_wp46_truth.cscript</files>
  <action><![CDATA[Add the TestHistogramRecast stubs and the S02 RH-5 block (Q4602-2). Run them into `<scratch>/46-02-03-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/46-02-03-failure.txt` is at least 6; the file holds `Q4602-2 FAIL`.]]></verify>
  <done>RH-5's regression tests were shown failing on the base.</done>
</task>

<task type="auto" id="46-02-04">
  <name>Style and size recast bins, commit RH-5</name>
  <files>dash_render.py, dash.sthlp, test/function_test_map.py</files>
  <action><![CDATA[Apply TR-46-02.5's centres, TR-46-02.6 to TR-46-02.8, TR-46-02.10 and TR-46-02.9's :3591-3593 correction. Run `python3 -m pytest test/test_recast.py test/test_recast_refit.py test/test_histogram_edge_rule.py test/test_histogram_scheme_style.py test/test_histogram_spurious_bin.py test/test_function_test_map.py -q -n0`, then `python3 -m pytest test/test_link_groups_brush.py -k recast -q -n0`, and the S02 block; re-run test/test_wp31_truth.cscript's U41-16 block once. Append the RH-5 parity entry of TDD stubs (Parity) to `CORPUS` in test/test_mode_parity.py. Close RH-5 (BUGS, Tracked, GAPS4_OPEN (test/test_tracking_documents.py), CHANGELOG "histogram with recast() draws in the histogram's own style, bars a bin wide, with 0 on its axis, as twoway does; histogram mpg, recast(bar) drew bars one mpg wide in the bar colour (WP-46, RH-5)"; TWOWAY_COVERAGE_AUDIT.md's histogram row gains "[WP-46 RH-5: corrected -- a recast histogram drawn in its own style, a bin wide, from 0]"). Before the commit take BRIEF's closing steps (1)-(3) for RH-5 (Notes "Before every commit" gives each command in full): (1) delete RH-5's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `RH-5 (documented)` or `RH-5 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py RH-5` and delete every row it prints from its `*_KNOWN` table -- a difference RH-5's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with RH-5. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[both pytest runs 0 failed; `python3 -m pytest test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0` passes; `Q4602-2 PASS`; `git log -1 --format=%s` ends `(WP-46 RH-5)`.]]></verify>
  <done>Recast histograms follow twoway's style, width and extent in both modes; RH-5 is closed.</done>
</task>

<task type="auto" id="46-02-05">
  <name>Write the RH-8 help-claim test</name>
  <files>test/test_help_claims_9.py, test/test_wp46_truth.cscript</files>
  <action><![CDATA[Append the class `TestRecastHorizontalDifference` (both stubs) to test/test_help_claims_9.py (the file exists; 44-02 and 45-03 edited its tuple pin -- add the class at the end and leave the rest untouched), and the S02 RH-8 block (Q4602-3). Run them into `<scratch>/46-02-05-failure.txt` (the sentence test red; the transpose guard and Q4602-3 green). Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/46-02-05-failure.txt` prints 1; the block log shows `Q4602-3 PASS`.]]></verify>
  <done>RH-8's help-claim test was shown failing on the base and the transpose probe passed.</done>
</task>

<task type="auto" id="46-02-06">
  <name>Document RH-8 and commit</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[Apply TR-46-02.9's Differences line and topic note (D-46-02.g, with RH8-01/02's measured ranges from the fixture). Run `python3 -m pytest test/test_help_claims_9.py test/test_help_conformance.py test/test_tracking_documents.py -q -n0` and the S02 block. Close RH-8 in the documented form (PD-4: "Documented <date> (WP-46, RH-8). dash.sthlp Differences from twoway and the Recast paragraph state that dash draws histogram and rbar recast with horizontal as the exact transpose where twoway draws a broken swapped picture (measured: histogram mpg, recast(bar) horizontal). Pinned by test/test_help_claims_9.py::TestRecastHorizontalDifference::test_the_sentence, Q4602-3. Closes GAPS4 RH-8 (WP-46, RH-8)."), its Tracked line in the Documented form, its GAPS4_OPEN (test/test_tracking_documents.py) line; one CHANGELOG line under "### Fixed in WP-46" (PD-7): "The help states that histogram and rbar with recast() and horizontal are drawn as the transpose of the upright layer, where twoway draws a broken picture (WP-46, RH-8)"; TWOWAY_COVERAGE_AUDIT.md's recast/horizontal row gains "[WP-46 RH-8: documented -- the transpose kept; twoway's broken picture under Differences]". Before the commit take BRIEF's closing steps (1)-(3) for RH-8 -- RH-8 closes Documented, so its `RH-8 (documented)` rows stay in the ledger and in every `*_KNOWN` table, and step (2) prints plain rows only -- (Notes "Before every commit" gives each command in full): (1) delete RH-8's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `RH-8 (documented)` or `RH-8 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py RH-8` and delete every row it prints from its `*_KNOWN` table -- a difference RH-8's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with RH-8. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest 0 failed; `python3 -m pytest test/test_corpus_ledger.py -q -n0` passes; `Q4602-3 PASS`; `grep -c "RH-8 Tracked:\*\* Documented in WP-46" GAPS4.md` prints 1; `git log -1 --format=%s` ends `(WP-46 RH-8)`.]]></verify>
  <done>RH-8 is documented under Differences with its measured example and pinned; the item is closed Documented.</done>
</task>

## Section completion criteria

- Three commits, failing tests first; Q4602-1..3 PASS; the JS twin pinned by node; flips carry reasons; no test deleted.
- `GlyphMapper._dash_hist_role_opts` in function_test_map.py; `dash_recast_data`'s y2 role covered by node.

## Notes

- **Help paragraphs owned (R3):** dash.sthlp :3581-3615 (Recast), the one Differences line for RH-8 (Appendix B HR-21's recast+horizontal quirk; 48-04 checks it).
- **Merge rules:** R1, R3, R5, R7, R8, R9, R12 (`_FILTER_JS` this batch).
- **Owns beyond the manifest's cell (for the orchestrator; REVIEW-4 R4-21):** `_dash_legend_key` (the recast_hi key text), `_dash_axis_default_titles` (inside 44-01's per-plot step), `_dash_add_glyph` (the extent renderer), dash.ado's spec writer and option-name list, `dash_recast_data` in `_FILTER_JS`. 46-02 is alone in batch 46.2.
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp46-s02`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Trap:** the extent renderer must never become the layer's "first renderer" a caller reads (`_dash_draw_xy_as` returns `added[0]`; add the extent after taking it).
- **Trap:** `_tag_recast` reads the target's own columns (:22270 comment); add `y2` after it runs or include it in its roles.
- **Commit-body lines:** `Regression: test/test_recast.py::TestRangeRecastBounds::test_axis_spans_both_bounds[saved-RB-01] -- failed at <base> with <text>` (per item); `Flipped: test/test_recast.py::TestRecastKeepsTheSeriesLabel::test_key -- the first-bound key was wrong because twoway keys Lovar/Hivar`; `Fixture: test/fixtures/recast_truth.json (scripts/extract_recast_truth.do)`; `BUGS.md: "<title>" (closed|documented)`; `GAPS4: <id> Tracked`.
