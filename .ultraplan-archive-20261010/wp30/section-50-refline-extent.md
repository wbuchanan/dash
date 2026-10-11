# Section 50: xline/yline extend, noextend and style() (P1.21 part b)

> Part of: WP-30 · Items: P1.21b (entry `P1.21b`; GAPS2-B22-e, the style() part of GAPS2-B22-d) · Risk: yellow · Batch: 17 (merge order S48, S49, S50; lands last, regenerates) · Depends on: 21, 39, 47 · Blocks: 57 · Tasks: 12, 1 commit · Case prefix: XE

## Review amendments

- Fixed (minor): 50-03 regenerated the 26 scheme files and `scheme_truth.json` without listing them; its `<files>` now names the extractor and both generated sets (as S33's and S36's regenerations do), and the conditional re-derivation of `test_the_directive_count_is_what_the_help_says`'s bounds (S24's rename of `test_80_to_140_directives`) with the help sentence it reads moved to 50-11.
- Checked at HEAD: `_DASH_REFLINE_SUBOPTS` 26221, the xline/yline loop 26236, the per-value `add_layout` 26370, the saved call 30396, the served generated line 35263, `SchemeParser._yesno` 6671, `_init_properties` 6806 and its xyline reads 6989-6993, `_FALLBACK_PROPS` 5728 with `"linewidth xyline"` 5805, the extractor's `xyline_truth` 953 and `expected_directives` 1371, `_dash_range_hull` TEST_ONLY at function_test_map.py:835, copy-list `"_dash_refline_draw",` 33383, and s2color's `yesno xyline_extend_low/high yes` at :2164-2165.
- Checked: M5 (nothing new refused; E5), M6 (the three sub-options silent, twoway's own note for an unknown style()), M1 (exact inset by the per-side plot-region margin, both modes, after moves through the finishers only, never `_FILTER_JS`); the JS twin writes fixed properties only (rule 1); the fixture verify's 0.0265 is 63.36 of 2388.33.
- Checked (batch 17): S50 is the batch's only regenerator and finisher editor; S48 edits `SchemeParser.apply_to_figure` and adds a method, not `_init_properties`; S49 does not touch the reference-line functions (its transposition reads only each layer's own annotation slice, which the lines precede); S48's by() size pass scales the Arrows' `line_width` as it scales Spans.
- Checked: `test_no_directive_for_what_dash_does_not_draw`'s pattern does not match the two `xyline_extend` keys, so it stays green.
- (cross-file pass) 50-11: the directive-count help sentence is named as the earlier sections left it, not as "80 to 140 directives" (S15 now moves it in batch 5).
- The review pass applied both lenses.

**Binding readings applied in this file** (M1, M5, M6; register P1.21.4, P1.21.6; index A152, A153, R1-R12, IR-17):
- **P1.21.4 / A69 (M1).** An unextended line is drawn exactly: a Bokeh `Arrow` with no heads, in data units, from the axis's scale at one end to the other (the plot region less twoway's plot-region margin, E4), re-finished after every filter move in both modes through S21's `_dash_refinish_axes` (served) and `_DASH_AXIS_FINISH_JS` (saved), never through `_FILTER_JS`.
- **P1.21.6 (M1).** The Arrow is drawn at the level S39 gives the Spans (`underlay`: above the grid, below the glyphs) and joins S39's bulk add.
- **M5.** Nothing new is refused: twoway accepts every form here (E5); `ex ex`, `NOEXTEND` and `style() style()` are S39's refusals (S39's scope: unknown, short, repeated or capitalised sub-options).
- **M6.** `extend`, `noextend` and `style(default|extended|unextended)` are drawn and no longer named. An unknown `style()` name gets twoway's own note, as twoway prints it.
- **Manifest.** "under margin(zero) noextend equals extend (S47's model)": the inset is the plot-region margin S47 resolves, per side.
- **A152 / R11.** S50 is batch 17's scheme regenerator (two `yesno` keys, all 26 files and `scheme_truth.json`, landing last) and its only finisher editor (`_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS` and S21's `_dash_axis_plan`, which S35 and S47 also extended as their batches' finisher editors). `_dash_range_hull` is read only: the tests use it as the oracle and it stays TEST_ONLY (never called at run time).
- **R12.** S50 edits none of `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets` or an applier.

**Section decisions.**
- **D-50a. Span or Arrow.** A copy whose two ends are both extended stays a `Span` (unchanged pages); a copy with an unextended end becomes an `Arrow(end=None)`. Measured in research (headless Chrome, scratch `arrow_demo.png`): an Arrow is one path, so stcolor's dashed xyline draws dashed and the frame clips it; a degenerate `BoxAnnotation` drew a dashed horizontal line solid.
- **D-50b. The inset is a frame fraction.** S21 pads a hull by f/(1−2f) of its span, so each end of the finished range lies exactly f × (range span) beyond the hull. An unextended end is therefore `start + f_lo × (end − start)` (and `end − f_hi × (end − start)`), in log10 space on a log axis, with S47's per-side fractions. This is twoway's own rule (E4: the inset is the plot-region margin), so it needs no data pass and is the same number the JS twin computes.
- **D-50c. Which end is low.** twoway's `xyline_extend_low` is the physical bottom of an xline and the left of a yline, whatever the axis direction (E4, reversed probe). In Bokeh, `start` is always drawn at the bottom or left, so "low" is the `start` end.
- **D-50d. Where the ends are written.** At build: inside `_dash_axis_plan`, which both modes call once after every range is final (saved `render()` step 5b; served after the graph loop). After a move: at the end of `_dash_refinish_axes` (served) and at the end of `dash_axis_finish` in `_DASH_AXIS_FINISH_JS` (saved). On zoom or pan nothing is rewritten: an unextended end is a data position and stays at the scale's end, as twoway draws it.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:132 (P1.21): "`noextend` is only named". GAPS2.md:595-604 (B22) adds `style()`. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-21.md` §1):

```
dash … xline(3000, noextend)           full-frame Span; noextend named     (twoway: inset by the plot-region margin)
dash … xline(3000, style(unextended))  Span; style() named                  (twoway: inset)
served (test_mode_parity harness)      the same Spans and notes
```

After S39 (batch 14), positions, refusals and `lstyle()` are drawn, and `extend`, `noextend` and `style()` are recorded per copy and still named (S39's scope leaves them to S50). Every line still spans the whole frame.

**After this section**, in the saved page and the served app, before and after every filter move, in every by() panel and on second axes:
- `noextend`, `style(unextended)` and a scheme whose `yesno xyline_extend_low/high` say `no` draw the line from the axis's scale to its scale, inset from the frame by the plot-region margin (63.36 of 2880 SVG units under s2color, 2.2%); `extend` and `style(extended)` win in either order; `style(default)` and `style()` read the scheme;
- under `plotregion(margin(zero))` an unextended line runs to the frame, as twoway draws it;
- the ends follow the axis after every move; the line never widens an axis;
- `style(nosuch)` draws the default extent with twoway's note.

**Test order and commit rule (rule 7).** One cycle on `wp30-s50`: 50-01 and 50-02 write the fixture and every regression test against the unmodified batch-17 base and save `$S/50-P1.21b-failure.txt` (no commit); 50-03 to 50-11 fix, regenerate, flip and document; 50-12 closes the entry and makes the commit, which lands last in batch 17.

## Risk: [yellow] — the axis-finisher chain in both modes, a JS twin, and a scheme regeneration

**Why.**
- `_dash_reference_lines`, `_dash_refline_instances`, `_dash_refline_draw` LOW (3 each; research §5), each copied into the served app by name (treat as MEDIUM).
- `_dash_refinish_axes`, `_dash_axis_plan` (S21's) and `_DASH_AXIS_FINISH_JS`: new since `c96facd`; impact at 17.0 (S35 recorded `_dash_axis_plan` among the finisher symbols it extended).
- `SchemeParser._init_properties` LOW (1, this pass); `_FALLBACK_PROPS` UNKNOWN (constant; grep).
- `ServerAppBuilder._glyph_layer_lines` HIGH (4).
- `scripts/extract_scheme_truth.py` and the 26 generated files (A152).

**Risk factors.**
1. Ends written before every range is final (a by() graph's shared range is written panel by panel) would be stale.
2. The JS twin could write a property named by JSON (rule 1), or disagree with Python.
3. S47's per-side margin may be stored in a form S21's plan does not carry.
4. A generated scheme file patched by hand, or a pre-existing key changed by the regeneration.
5. 10,000 lines (S39's `reflines` limit) would make a large plan.

**Mitigation.**
1. D-50d: ends are written only where S21 already knows every range is final; `TestByPanels` checks both panels after a move that changes the shared range.
2. The JS writes `y_start`/`y_end` or `x_start`/`x_end` in a fixed branch on the plan's `letter` (`"x"` or `"y"`, checked), reads plan fields through `hasOwnProperty`, writes only finite numbers; `TestJsEqualsPython::test_random_moves` runs 200 seeded moves.
3. 50-05 reads S47's stamps at the base; `TestPerSideMargins` pins `margin(l=10 b=0)` against E4; if no per-side form exists, 50-05 stops and reports (finisher contract).
4. One extractor run, compared with the pre-run files: only the two new keys may change (R7).
5. Only unextended copies become Arrows; `TestTheBudget` bounds the served re-finish (≤ 0.05 s added for 1,000 such lines) and the saved finish (≤ 0.1 s, node), inside A9's budgets.

## Dependencies

- **Depends on: 21, 39, 47.**
  - S21 (batch 7): the finished `Range1d`s with `_dash_margin_f` (and `reset_start/reset_end`), `_dash_refinish_axes(figures, facet_map)`, `_dash_axis_plan(figures, facet_map, zoom=True)` with its per-panel per-axis entries (`letter`, `name`, `kind`, `margin`, `range` model index) and `models`, `_DASH_AXIS_FINISH_JS` with `dash_axis_finish(plan, models)`, the `axis_plans_json`/`axis_models` args and step 5b; non-renderer annotations stay out of the hull (S21 reads GlyphRenderers only).
  - S39 (batch 14): positions expanded, `lstyle()` resolved, Spans collected and added in bulk at `level="underlay"`, the per-copy record of `extend`, `noextend` and `style()` in `_dash_refline_instances` (named until S50), S10's refline abbreviation table (`st`, `noex`, `ex`), the finite check, the unknown-lstyle note path.
  - S47 (batch 16): `plotregion(margin())` per side through `_dash_plot_margin` and `_dash_padded_range`; S50 reads its per-side fractions.
  - S01: entry `P1.21b`, its key, the marker `<!-- WP-30 P1.21b -->` (Results that change), the stub `* ==== S50 P1.21b: xline/yline extend, noextend and style() ====`, the anchors `# WP-30 S50 (P1.21b): xline/yline extend, noextend and style() (P1.21 part b)`.
- **Blocks: 57** (the served worker audits the final move path, `_dash_refinish_axes` included).
- **Parallel batch: 17**, last. **Can run with** S48 (by() layout; it adds `SchemeParser.by_indiv_margin` and one line of `apply_to_figure`, not `_init_properties`) and S49 (horizontal: the figure body, the template, axis helpers): no shared function. Neither partner touches a scheme file or the extractor.

## Evidence

Anchors at `c96facd`; S21, S35, S39 and S47 move them; re-find by symbol at `batch-17-base`.

### E1. Lines are Spans over the whole frame (dash_render.py 26221-26371)

```python
26221 _DASH_REFLINE_SUBOPTS = frozenset({"lcolor", "lpattern", "lwidth"})
...
26236    for opt, dim in (("xline", "height"), ("yline", "width")):
...
26369    for v in values:
26370        fig.add_layout(Span(location=v, dimension=dim, **kw))
```
Both modes call one helper: saved `_dash_reference_lines(fig, graph_opts, _seen, _gkey, self.scheme)` (30396, early in `_make_figure_body`, before any layer is drawn), served `"        _dash_reference_lines(fig, go, _reported_subopts, gname, _DASH_SCHEME)",` (35263). A `yline(#, axis(2))` copy draws on `y2` (`range_name`, 26364-26366). S39 replaces the per-value `add_layout` with one bulk `fig.center` assignment and sets the level.

### E2. The scheme's xyline style is read; its extend keys are not

`SchemeParser._init_properties` (6806) reads `color xyline`, `linepattern xyline`, `linewidth xyline` (6989-6993). `_yesno(key, default)` (6671) reads a `yesno` directive. `_FALLBACK_PROPS` (5728) holds `"linewidth xyline": "medium"` (5805) and no extend key. `scripts/extract_scheme_truth.py` resolves the xyline line style (`xyline_truth`, 953-968) and writes directives through `expected_directives` (1371). No dash scheme file holds `xyline_extend` (grep, this pass).

### E3. Stata's rule (read as text)

`_gs_parse_and_log_lines.ado` (v1.1.6): `syntax anything [, STyle(string) NOEXtend EXtend LSTyle() LColor() LWidth() LPattern() LAlign() AXis(passthru)]`; the edits are `style` first, then `extend_low(no) extend_high(no)` for `noextend`, then `extend_low(yes) extend_high(yes)` for `extend`, then the line edits, all applied to one `gridlinestyle` per copy. `gridlinestyle-default.style`: `set extend_low scheme xyline_extend_low`, `set extend_high scheme xyline_extend_high`, `set linestyle scheme xyline`; `-extended.style`: yes, yes, xyline; `-unextended.style`: no, no, xyline. `scheme-s2color.scheme:2164-2165` and `scheme-economist.scheme:383-384`: `yesno xyline_extend_low yes`, `yesno xyline_extend_high yes`; every other shipped scheme inherits them.

### E4. twoway's truth (research §2; this pass `p50.do`, `p51.do`, s2color, SVG plot region x 390.80-3859.02, y 100.86-2489.19, min(W,H) 2880)

```
probe                                               xline(3000) y ends          yline(20) x ends
default                                             2489.19 .. 100.86 (frame)   390.80 .. 3859.02 (frame)
noextend (both)                                     2425.82 .. 164.22           454.16 .. 3795.66      inset 63.36 = 2.2% x 2880
user scheme (#include s2color, xyline_extend_low no) 2425.82 .. 100.86          454.16 .. 3859.02      low end only
  same + xline(, extend) yline(, style(extended))   frame                       frame
style(Unextended) / style()                         frame + note / frame        (note:  named style Unextended not found in class gridlinestyle, default attributes used)
noextend + yscale(log)                              2425.82 .. 164.22           454.16 .. 3795.66 at y 1314.76
noextend + plotregion(margin(l=10 b=0))             2489.19 .. 164.22           678.77 .. 3795.66      b=0 no inset; l=10 → 288
xline(, style(unextended) extend)                   frame                       noextend lstyle(p1): inset, #1A476F
low=no scheme, xscale(reverse) yscale(reverse)      2425.82 .. 100.86           454.16 .. 3859.02      bottom and left inset still
(scatter)(scatter, yaxis(2)), yline(5000, axis(2) noextend) xline(3000, noextend)
                                                    2170.27 .. 164.22           454.16 .. 3505.71      inset 63.36 on both
xline(3000, noextend) by(foreign)                   2323.23 .. 312.11 per panel                        inset 53.84 = 0.85 x 63.36
```
Research §2 adds: stcolor's default is extended and `noextend` insets 71.3 = 2.2% × 3240; `plotregion(margin(zero))` makes noextend equal extend; `margin(large)` insets 230.4 (8%); `xscale(range(1000 6000))` keeps the inset at the plot margin; `style(nosuch)` is noted "…class gridlinestyle…" and drawn as the default; `extend` beats `noextend` and `style(unextended)` in either order.

### E5. Nothing here is refused by twoway

Every row of E4 is rc 0. The refusals of the sub-option grammar (`s()`, `noe`, `e`, `NOEXTEND`, `ex ex`, `style() style()`) are S39's (research §2 "Sub-options").

### E6. Tests that pin today's behaviour (re-measured by 50-09)

- `test/test_suboption_warnings.py` row "xline lstyle noextend" (:72-74 at `c96facd`; S39 removed `lstyle(foreground)` from its expected names): `noextend` leaves the expected names.
- S39's own tests asserting that `extend`, `noextend` and `style()` are named (in its test file; grep `noextend` at the base) and `test/test_suboption_reporting.cscript` SR-06 if it still names them.
- `test/test_mode_parity.py` notes that name `noextend` (grep).
- `test/test_help_claims_8.py::TestTheShippedFiles::test_the_directive_count_is_what_the_help_says` (`test_80_to_140_directives` at :1014 of `c96facd`, renamed by S24; bounds as S36 left them): two more directives per file; re-derived only if red (R10).
- Not flips: `test/test_axis_options.py:288-289` is `yscale(noextend)`, a different option.

### E7. The finisher contract S50 extends (section-21 TR-21.9-TR-21.12, as S35 and S47 extended them)

- `_dash_refinish_axes(figures, facet_map)` re-finishes each graph group (`_dash_finish_count_ticks(f, refinish=True)` per figure, then `_dash_common_count_ticks(group, letters)`); it is called in `_on_filter_change` after step 3 and before "# 4. Recompute filter-mode KPIs".
- `_dash_axis_plan(figures, facet_map, zoom=True)` returns `(plan_json, models)`: per group `share`, per panel per axis `letter`, `name`, `kind`, `mode`, `n`, `hold`, `held`, `explicit`, `extra`, `scale`, `reverse`, `margin`, `range`/`ticker` model indexes, `layers`, `bars`; `json.dumps(…, allow_nan=False)`; no user text but field names. S35 added `units`/`cunits`; S47 added the inner box (re-read at the base).
- `_DASH_AXIS_FINISH_JS` defines `dash_natscale`, `dash_axis_ticks`, `dash_axis_extent`, `dash_axis_pad`, `dash_axis_compute` and `dash_axis_finish(plan, models)`; it writes ticks, then `reset_start/reset_end`, then `start/end`, and emits `rng.change` when only ticks change. `_FILTER_JS` ends with `if (typeof axis_plans_json !== "undefined" && axis_models) { dash_axis_finish(JSON.parse(axis_plans_json), axis_models); }`.
- Saved wiring: `DashRenderer.render()` step 5b, right after `_build_filter_widgets`, writes `axis_plans_json` and `axis_models` into every filter callback's args; served: one plan after the graph loop. Zoom: one `CustomJS(code=_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS)` per document re-ticks over the visible range and re-hulls nothing.
- `_dash_range_hull(rng, kind=None, margin=None)` inverts the pad; TEST_ONLY (function_test_map.py:835), so S50's run-time code never calls it.

## User stories

- **US-50.1** As a twoway user, I want `xline(3000, noextend)` and `yline(20, style(unextended))` to stop at the axis's scale, as in my Stata graph, in both modes and after I move a filter.
- **US-50.2** As a twoway user with my own scheme, I want `yesno xyline_extend_low no` honoured.
- **US-50.3** As a dashboard publisher, I want lines that span the frame to stay exactly as they are.

## Business requirements

- **BR-50.1** Each copy's two ends are extended or not by twoway's rule: the scheme's `xyline_extend_low`/`_high` (yes by default); `style(default)` and `style()` the scheme; `style(extended)` both yes; `style(unextended)` both no; then `noextend` both no; then `extend` both yes; an unknown style name is the default with twoway's note. Abbreviations through S10's table (`st`, `noex`, `ex`).
- **BR-50.2** An extended end reaches the frame; an unextended end sits at the axis's scale, inset by that side's plot-region margin (0 under `margin(zero)`); low is the bottom of an xline and the left of a yline, on reversed axes too; on a log axis the inset is in log units.
- **BR-50.3** The same holds on a second axis (`yline(#, axis(2))` spans the x axis's scale), in every by() panel (with the panel's margin), on date axes and after every saved and served filter move; zoom and pan leave an unextended end at its data position.
- **BR-50.4** Lines never widen an axis; style, pattern, width, level and position are S39's, unchanged.
- **BR-50.5** A copy with both ends extended draws exactly as before (a Span).
- **BR-50.6** `extend`, `noextend` and `style()` are not named in any note.

## Technical requirements

- **TR-50.1 Scheme keys.** `scripts/extract_scheme_truth.py`: resolve `yesno xyline_extend_low` and `yesno xyline_extend_high` through each scheme's include chain with provenance (as `xyline_truth` resolves the line style), record `xyline_extend_low`/`xyline_extend_high` (booleans) in `scheme_truth.json`, and emit both directives through `expected_directives`. `SchemeParser._init_properties`, directly after the three xyline reads (6993): `self.xyline_extend_low = self._yesno("yesno xyline_extend_low", True)` and `…_high`. `_FALLBACK_PROPS` gains `"yesno xyline_extend_low": "yes"` and `"yesno xyline_extend_high": "yes"` after `"linewidth xyline"` (5805).
- **TR-50.2 `_dash_refline_extent_flags(style, scheme, opt, seen=None, key="") -> (low, high)`** (after `_dash_refline_draw`): BR-50.1's order. `style` is the copy's recorded sub-options (S39's dict, keys canonicalised by S10's table). An unknown `style()` name (case as typed: `Unextended` is unknown) gives one note `(note:  named style <name> not found in class gridlinestyle, default attributes used)` through the path S39 uses for its unknown-`lstyle()` note, at most 80 printable characters of the name echoed. `scheme` None reads yes, yes.
- **TR-50.3 `_dash_refline_draw`** (S39's form; edit in place): for each copy, `low, high = _dash_refline_extent_flags(...)`; when both are true, S39's Spans as today; otherwise, per position v, `Arrow(end=None, start=None, line_* = S39's kw, level = S39's level, x_start=v, x_end=v, y_start=v0, y_end=v0)` for an xline (x and y exchanged for a yline; `v0` is the location itself, a finite placeholder overwritten at build), on the copy's range (`x_range_name`/`y_range_name` as S39 sets the Span's), added to S39's bulk list; and `fig._dash_refline_arrows.append((arrow, letter, low, high))`, `letter` the axis the line spans (`"y"` for an xline, `"x"` for a yline). A Python attribute, never serialised. S39's recorded `extend`/`noextend`/`style` leave its named list (wherever S39 names them; edit that line only).
- **TR-50.4 `_dash_refline_extents(fig) -> None`** (after `_dash_refline_extent_flags`): for each recorded Arrow, `rng` is `fig.y_range` for letter "y" and `fig.x_range` for "x" (the line spans the primary range of the other axis; a y2 line spans x). When `rng` is a `Range1d` carrying S21's margin stamp: `s, e = rng.start, rng.end` (log10 of each on a log axis, `fig._dash_date_kinds`/S21's kind read as S21's plan reads it); `f_lo, f_hi` = S47's per-side fractions for that axis (start side = bottom or left), else `rng._dash_margin_f` for both; `lo = s if low else s + f_lo × (e − s)`; `hi = e if high else e − f_hi × (e − s)` (10** back on log); write `arrow.y_start, arrow.y_end = lo, hi` (or `x_*`) only when both are finite. Any other range is left as it is. Idempotent; reads no data.

  ```python
  def _dash_refline_extents(fig):
      for arrow, letter, low, high in getattr(fig, "_dash_refline_arrows", ()):
          rng = fig.y_range if letter == "y" else fig.x_range
          f_lo, f_hi = _s47_sides(fig, rng, letter)      # S47's per-side fractions, else (f, f)
          if f_lo is None:                               # not a finished Range1d
              continue
          log = <the axis kind is "log">
          s, e = float(rng.start), float(rng.end)
          if log: s, e = math.log10(s), math.log10(e)
          lo = s if low else s + f_lo * (e - s)
          hi = e if high else e - f_hi * (e - s)
          if log: lo, hi = 10 ** lo, 10 ** hi
          if math.isfinite(lo) and math.isfinite(hi):
              if letter == "y": arrow.y_start, arrow.y_end = lo, hi
              else:             arrow.x_start, arrow.x_end = lo, hi
  ```
  `_s47_sides` stands for whatever S47 stores (inline in the function; no new helper name is required).
- **TR-50.5 Build-time ends.** In S21's `_dash_axis_plan` (finisher; one editor per batch), first statement of its per-figure loop: `_dash_refline_extents(fig)`, with a comment that every range is final here in both modes (D-50d).
- **TR-50.6 Saved re-finish.**
  - `_dash_axis_plan`: each panel entry gains `"lines": [{"arrow": <models index>, "range": <models index of rng>, "letter": "x"|"y", "kind": <the axis kind S21 writes>, "margin": [f_lo, f_hi], "low": 0|1, "high": 0|1}]`, the Arrows appended to `models` (deduplicated, as S21 deduplicates).
  - `_DASH_AXIS_FINISH_JS`: a new function `dash_refline_extent(panel, models)`, called by `dash_axis_finish` for each panel after every range of every group is written. It reads `lines` with `Object.prototype.hasOwnProperty.call`, takes `models[ln.range]`'s `start`/`end`, applies TR-50.4's arithmetic (`Math.log10`/`Math.pow(10, …)` on `"log"`), and writes through a fixed branch: `if (ln.letter === "y") { a.y_start = lo; a.y_end = hi; } else if (ln.letter === "x") { a.x_start = lo; a.x_end = hi; }`, only when both are finite and only when they differ from the current values. No other line of the constant changes; `_FILTER_JS` is not edited.

  ```javascript
  function dash_refline_extent(panel, models) {
    var own = Object.prototype.hasOwnProperty;
    if (!own.call(panel, "lines")) return;
    for (var i = 0; i < panel.lines.length; i++) {
      var ln = panel.lines[i], a = models[ln.arrow], r = models[ln.range];
      if (!a || !r || (ln.letter !== "x" && ln.letter !== "y")) continue;
      var s = r.start, e = r.end, lg = ln.kind === "log";
      if (lg) { s = Math.log10(s); e = Math.log10(e); }
      var lo = ln.low ? s : s + ln.margin[0] * (e - s);
      var hi = ln.high ? e : e - ln.margin[1] * (e - s);
      if (lg) { lo = Math.pow(10, lo); hi = Math.pow(10, hi); }
      if (!isFinite(lo) || !isFinite(hi)) continue;
      if (ln.letter === "y") { if (a.y_start !== lo) a.y_start = lo; if (a.y_end !== hi) a.y_end = hi; }
      else { if (a.x_start !== lo) a.x_start = lo; if (a.x_end !== hi) a.x_end = hi; }
    }
  }
  ```
  `ln.margin` is the pair the plan writes at build; a filter move never changes a margin, so the build-time pair stays right.
- **TR-50.7 Served re-finish.** `_dash_refinish_axes(figures, facet_map)`: after its group loop, `_dash_refline_extents(f)` for every figure it re-finished.
- **TR-50.8 Copy list (R2 row S50).** Functions tuple, new lines directly after S39's names after `"_dash_refline_draw",` (33383): `# xline/yline extent (WP-30 P1.21b).` and `"_dash_refline_extent_flags", "_dash_refline_extents",`. No constant is added.
- **TR-50.9 Test harness.** `test/js_runner.py`: `stand_in` encodes `x_start`, `x_end`, `y_start`, `y_end` for `Arrow`; `RUNNER` returns them for `Arrow` only; the commit writes them back (the S21 pattern for Range1d). `test/test_mode_parity.py` `_annotations` profiles `Arrow` (class, level, the four ends rounded to 1e-9 relative, dash, colour, width) if it does not already.
- **TR-50.10 Registries.** `test/function_test_map.py` under S50's anchor: `_dash_refline_extent_flags`, `_dash_refline_extents`. No Stata program.
- **TR-50.11 Security (rule 1).** The JS is a module constant with no user text; the plan carries numbers, letters from a fixed set and model indexes; property names are fixed in code (critic of p1-09 item 7, applied here); the note echoes at most 80 printable characters through the note channel; no `shell=True` in the extractor or tests.

## Boundaries

- **Not edited:** `_FILTER_JS`; `_dash_hull_ranges`, `_dash_padded_range`, `_dash_range_hull`, `_dash_plot_margin`, `_dash_default_ticker` (read only; `_dash_range_hull` stays TEST_ONLY); `_dash_refline_instances` beyond S39's named-list line; `_dash_route_line_copies`; S39's refusals in dash.ado and Mata; the zoom JS (`_DASH_AXIS_ZOOM_JS`).
- **Batch partners:** S48 (by() layout, `apply_to_figure`'s one line, `SchemeParser.by_indiv_margin`); S49 (`_make_figure_body`, the template, the axis-variable helpers). S50 lands last and regenerates.
- **Residuals:** an extended end of a copy whose other end is unextended (only a user scheme with one `xyline_extend_*` key set to no) stays at the frame of the page's last re-finish when the reader zooms out past it (Notes for the closeout); P2.54 (out-of-range lines clipped at the frame) is unchanged.

## Stata truth

New `scripts/extract_refline_extent_truth.do` (S02's form; `DASH_REPO`, `adopath ++ "<repo>/"`, `global dash_nobrowser 1`); it writes a scratch user scheme `scheme-dashxlow.scheme` (`#include s2color`, `yesno xyline_extend_low no`) and `scheme-dashxhigh.scheme` into its own work directory, adds that directory to the ado-path, and runs `capture noisily twoway scatter mpg weight, <opts>` for E01-E26: default, `noextend`, `extend`, `style(unextended)`, `style(extended)`, `style(default)`, `style(nosuch)`, `style(Unextended)`, `style()`, `noextend extend`, `style(unextended) extend`, `scheme(dashxlow)`, `scheme(dashxhigh)`, `scheme(dashxlow)` with `extend`, `yscale(log) noextend`, `plotregion(margin(zero)) noextend`, `plotregion(margin(large)) noextend`, `plotregion(margin(l=10 b=0)) noextend`, `scheme(dashxlow) xscale(reverse) yscale(reverse)`, the two-axis probe of E4, `by(foreign) noextend`, `scheme(stcolor) noextend`, `scheme(economist) noextend`, `xscale(range(1000 6000)) noextend`, a `%td` x with `xline(<date>, noextend)`, `noextend lstyle(p1)`; each with `xline(3000…)` and `yline(20…)`. Per probe: rc, every `(note:` line, `.Graph.plotregion1.{x,y}scale.curmin/curmax` (none under by()), the plot-region rect(s) and, per line, its colour and SVG ends read through `scripts/svg_truth.py`, with `low_inset` and `high_inset` (inset ÷ the plot region's extent along the line; 0 when extended). Writes `test/fixtures/refline_extent_truth.json` (`git add -f`, D12 `_meta`).

| Key | Content |
|---|---|
| `_meta` | `stata_version`, `born_date`, `dash_commit`, `extracted`, `scheme` per probe |
| `probes.<E##>.rc`, `.notes` | return code and every `(note:` line |
| `probes.<E##>.scale` | `{"x": [curmin, curmax], "y": [curmin, curmax]}` (absent under by()) |
| `probes.<E##>.region` | plot-region rect(s), SVG units |
| `probes.<E##>.xline` / `.yline` | per drawn line: `colour`, `ends` (SVG), `low_inset`, `high_inset` (fractions of the region along the line), `at` (position in data units) |

Truth block (S50's in `test/test_wp30_truth.cscript`, helpers above its header): XE-01..XE-10 build `dash scatter mpg weight, <opts> saving(…)` for E02, E04, E10, E13, E15, E17, E18, E20, E21, E25 and compare each Arrow's ends (read from the page by a python block) with twoway's curmin/curmax or frame for the same probe in the same run; XE-11 builds the server app for E02 and compares its document's Arrow ends.

## TDD test stubs

New `test/test_refline_extent.py` (helpers `_T`; `_both(spec)` through `test_mode_parity._standalone/_served`; `_arrows(fig)`; `_saved_move`/`_served_move` as S21's `test_default_axes.py`). Red at the base unless marked guard.

- Test: `TestTheFlags::test_rule[<style>-<flags>]` — `_dash_refline_extent_flags` over every combination of scheme (yes/yes, no/yes, yes/no), `style()` (none, default, extended, unextended, nosuch, empty) and `extend`/`noextend` in both orders equals BR-50.1. Red: AttributeError.
- Test: `TestTheFlags::test_unknown_style_note` — `style(nosuch)` and `style(Unextended)` give twoway's note once; a 10,000-character name echoes at most 80 characters. Red.
- Test: `TestTheExtent::test_probe[E02|E04|E10|E11|E13|E14|E26-saved|served]` — Arrow (or Span) per copy as the fixture's insets; Arrow ends equal `dr._dash_range_hull(rng, kind, margin=…)` at each unextended end and the range ends at each extended end. Red: Spans.
- Test: `TestTheExtent::test_all_extended_stays_a_span[E01|E03|E05|E06|E09]` — a Span and no Arrow; the document JSON equals the base's for E01. Red for none (guard rows marked).
- Test: `TestPerSideMargins::test_margin[zero|large|l10b0-saved|served]` — ends equal E4 (zero: the frame; l=10 b=0: bottom at the frame, left at 10 units). Red.
- Test: `TestLowIsPhysical::test_reversed[saved|served]` — E19: the bottom and left ends unextended on reversed axes. Red.
- Test: `TestLogAxis::test_noextend[saved|served]` — E15 ends in log units. Red.
- Test: `TestSecondAxis::test_y2_line_spans_x[saved|served]` — E20. Red.
- Test: `TestByPanels::test_each_panel[saved|served]` and `::test_after_a_move_that_moves_the_shared_range[saved|served]`. Red.
- Test: `TestDateAxis::test_td_noextend[saved|served]` — E25. Red.
- Test: `TestNoHull::test_lines_never_widen` — with `yline(1000, noextend)` far outside the data, the y range equals the range without it, in both modes. Guard (S21's rule) plus the Arrow's presence (red).
- Test: `TestAfterAFilterMove::test_range_move[saved|served]` and `::test_dropdown_move[saved|served]` — after the move the ends equal the new range's inset ends; saved through js_runner (node, not skipped). Red.
- Test: `TestJsEqualsPython::test_random_moves` — 200 seeded moves: `dash_refline_extent` equals `_dash_refline_extents` within 1e-9 relative. Red.
- Test: `TestThePlanCarriesNoUserText::test_plan_and_code[saved|served]` — the `lines` entries hold only numbers, the letters x/y and kinds; the filter callbacks' code is still `_FILTER_JS`; a plan with `"letter": "constructor"` or `"__proto__"` writes nothing (node). Red.
- Test: `TestZoomLeavesTheEnds::test_zoom[saved|served]` — running the zoom CustomJS leaves the Arrow ends. Red (no Arrow).
- Test: `TestTheBudget::test_served_and_saved` — 1,000 unextended lines: served `_dash_refinish_axes` adds ≤ 0.05 s; saved finish ≤ 0.1 s (best of 3). Red.
- Test: `TestTheSchemeKeys::test_every_scheme[<26>]` — `xyline_extend_low/high` True for every shipped scheme, as `scheme_truth.json`; the fallback True. Red.
- Test: `TestNotNamed::test_no_note[extend|noextend|style(unextended)|st(extended)|noex]`. Red.
- Browser, new `test/test_refline_extent_chrome.py` (skips without Chrome; red under DASH_STRICT if skipped): `TestInChrome::test_dashed_noextend_draws_dashed_and_inset` (stcolor) and `::test_after_a_move`.
- Shared: `test/test_mode_parity.py` CORPUS `_case("xline/yline noextend and style() (WP-30 P1.21b)", [_sc()], go={"xline": "3000, noextend", "yline": "20, style(unextended)"})` and `MOVE_CORPUS` `_move_case("noextend after a range move", _MOVES[1], [_sc()], go={"xline": "3000, noextend"})`.
- cscript: XE-01..XE-11.

### Mutation table (each must turn a named test red)

| Mutation | Red test |
|---|---|
| `extend` checked before `noextend` (noextend wins) | `TestTheFlags::test_rule` (`noextend extend`) |
| low taken as the data minimum on a reversed axis | `TestLowIsPhysical::test_reversed[saved]` |
| inset by S21's single f under `margin(l=10 b=0)` | `TestPerSideMargins::test_margin[l10b0-served]` |
| inset in data units on a log axis | `TestLogAxis::test_noextend[saved]` |
| `_dash_axis_plan` skips `_dash_refline_extents` | `TestTheExtent::test_probe[E02-saved]` |
| `_dash_refinish_axes` skips it | `TestAfterAFilterMove::test_range_move[served]` |
| `dash_axis_finish` skips `dash_refline_extent` | `TestAfterAFilterMove::test_range_move[saved]` |
| the JS writes `a[ln.letter + "_start"]` | `TestThePlanCarriesNoUserText::test_plan_and_code[saved]` |
| every copy drawn as an Arrow | `TestTheExtent::test_all_extended_stays_a_span[E01]` |
| `"_dash_refline_extents"` dropped from the copy list | `TestTheServedAppCarriesEveryName` |

### Pinned tests to flip (R9)

E6's list, each with `Flipped (WP-30 P1.21b): <name> named was wrong because twoway draws it (refline_extent_truth.json <probe>)`, recorded in `$S/50-flips.txt`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| The flag rule, the note | `TestTheFlags` | E01-E14 | n/a |
| Extent, margins, low end, log, y2, by(), dates | `TestTheExtent` … `TestDateAxis`; XE-01..XE-10 | `refline_extent_truth.json` | yes |
| Spans kept | `TestTheExtent::test_all_extended_stays_a_span` | E01 | yes |
| After moves, zoom | `TestAfterAFilterMove`, `TestZoomLeavesTheEnds`, MOVE_CORPUS | — | yes |
| JS twin and safety | `TestJsEqualsPython`, `TestThePlanCarriesNoUserText` | — | saved (node) |
| Budget | `TestTheBudget` | — | yes |
| Browser | `test_refline_extent_chrome.py` | — | saved |
| Scheme keys | `TestTheSchemeKeys`, `test_scheme_fidelity.py`, the regeneration comparison | `scheme_truth.json` | n/a |
| Registries | maps, G4 guards | — | served |

**Acceptance criteria.**
- **AC-50.1** (BR-50.1, BR-50.2) every fixture probe's per-end extension and end positions match in both modes; XE-01..XE-11 PASS.
- **AC-50.2** (BR-50.3) the move, by(), y2, date and zoom tests pass; node tests not skipped.
- **AC-50.3** (BR-50.4, BR-50.5) `TestNoHull` and the Span rows pass; E01's page is unchanged.
- **AC-50.4** (BR-50.6) no note names the three sub-options.
- **AC-50.5** the regeneration changed only the two keys in each of the 26 files and `scheme_truth.json`; the full run green; flips recorded; G7 0 twice.

## Tasks

**Commit boundary.** Tasks 50-01 to 50-12 form the one commit of entry `P1.21b`, made by 50-12 on `wp30-s50` with the subject `Stop unextended reference lines at the axis scale and read the scheme's extend keys (WP-30 P1.21b)`; it lands last in batch 17 (A152). `$S`, `$SLOT` as in section 48; `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s50`. Cscripts through the driver with `WP30_ONLY=S50`. Confirm `$S/batch-17-impact.txt` records the approval before the first edit of `_dash_axis_plan`, `_dash_refinish_axes` and `_glyph_layer_lines`.

<task type="auto" id="50-01">
  <name>Write the extent fixture and tests</name>
  <files>scripts/extract_refline_extent_truth.do, test/test_refline_extent.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-17-base.txt"` and the branch is `wp30-s50`; stop otherwise. Create the extractor as "Stata truth" describes and run it through the slot with `DASH_REPO="$WT"`. Create `test/test_refline_extent.py` with every stub, naming new symbols (`dr._dash_refline_extent_flags`, `dr._dash_refline_extents`, the JS function `dash_refline_extent`) so they fail now; append the CORPUS and MOVE_CORPUS cases and, if `_annotations` does not profile `Arrow`, its Arrow branch. Run `python3 -m pytest test/test_refline_extent.py -q -n 6 -p no:cacheprovider -rf > "$S/50-new.log" 2>&1`. Write `$S/50-P1.21b-failure.txt` (base sha, failing nodes, guards). Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/refline_extent_truth.json')); p=d['probes']; print(round(p['E02']['xline'][0]['low_inset'],4), round(p['E01']['xline'][0]['low_inset'],4), p['E13']['yline'][0]['high_inset'] > 0, all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')))"` prints `0.0265 0.0 True True` (63.36 of 2388.33); `grep -c FAILED "$S/50-new.log"` is at least 30.]]></verify>
  <done>The twoway extent fixture existed and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="50-02">
  <name>Write the truth block cases</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Put the `_s50_*` helpers directly above S01's `* ==== S50 P1.21b: xline/yline extend, noextend and style() ====` header and XE-01..XE-11 between S01's S50 start and end lines, in the `WP30_ONLY` gate form. Run the block through the driver on the unmodified tree; append the FAIL lines to `$S/50-P1.21b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "XE-(0[1-9]|1[01]) FAIL" "$S/run_test_wp30_truth.log"` is at least 10.]]></verify>
  <done>The twoway comparisons were in S50's block and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="50-03">
  <name>Transcribe the extend keys</name>
  <files>scripts/extract_scheme_truth.py, dash-*.scheme, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Make TR-50.1's extractor part. Copy `test/fixtures/scheme_truth.json` and the 26 `dash-*.scheme` files to `$S/50-schemes-old/`, run the extractor as its header says, and compare with a scratch script `$S/50-cmp.py`: every pre-existing property and directive of every scheme unchanged, only `yesno xyline_extend_low`/`_high` added. Save the comparison to `$S/50-schemes-cmp.txt`. Never patch a generated file by hand (R7). Run `test/test_help_claims_8.py::TestTheShippedFiles` (the directive-count pin, `test_the_directive_count_is_what_the_help_says` after S24's rename) and record in `$S/50-notes.txt` whether it is red (its bounds are 50-11's).
  ]]></action>
  <verify><![CDATA[`tail -1 "$S/50-schemes-cmp.txt"` reads `unchanged: 26 schemes; added keys only`; `grep -c "^yesno xyline_extend_low" "$WT"/dash-*.scheme | grep -c ":1$"` prints 26; `python3 -m pytest test/test_scheme_fidelity.py test/test_scheme_fallback_provenance.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every shipped scheme carried the two extend keys its StataCorp chain sets, regenerated and verified key by key.</done>
</task>

<task type="auto" id="50-04">
  <name>Read the keys and decide each end</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Make TR-50.1's SchemeParser and `_FALLBACK_PROPS` parts and TR-50.2's `_dash_refline_extent_flags` after `_dash_refline_draw`, with a docstring quoting E3's edit order. Find S39's unknown-lstyle note path at the base (`grep -n "class linestyle" dash_render.py`) and use the same helper for the gridlinestyle note. Map the function under S50's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_refline_extent.py -q -n0 -p no:cacheprovider -k "TestTheFlags or TestTheSchemeKeys"` passes; `python3 -m pytest test/test_scheme_coercion.py test/test_scheme_consumption.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Each copy's two ends were decided by twoway's edit order from the scheme, style(), noextend and extend.</done>
</task>

<task type="auto" id="50-05">
  <name>Draw unextended copies as Arrows</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Make TR-50.3 in `_dash_refline_draw` (S39's bulk list and level; remove `extend`, `noextend` and `style` from the line where S39 names them) and TR-50.4's `_dash_refline_extents`. Read S47's per-side margin stamp at the base (`grep -n "_dash_margin" dash_render.py`); if a finished Range1d carries neither S47's per-side fractions nor S21's `_dash_margin_f`, stop and report. Map `_dash_refline_extents` under S50's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -c "import sys; sys.path.insert(0,'$WT'); import dash_render as d; print(d._dash_refline_extents.__name__)"` prints `_dash_refline_extents`; `python3 -m pytest test/test_refline_extent.py -q -n0 -p no:cacheprovider -k "all_extended_stays_a_span or NotNamed or NoHull"` passes; `python3 -m pytest test/test_reference_lines.py test/test_suboption_warnings.py -q -n 6 -p no:cacheprovider` reports 0 failed except E6's flips.]]></verify>
  <done>Copies with an unextended end were drawn as headless Arrows at S39's level and recorded for the finisher, and fully extended copies stayed Spans.</done>
</task>

<task type="auto" id="50-06">
  <name>Place the ends at build</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_axis_plan` is the batch's finisher (R11; impact from `$S/batch-17-impact.txt`). Make TR-50.5 (the first statement of its per-figure loop) and TR-50.6's plan entries (`lines`, Arrows appended to `models`). Change no other plan field.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_refline_extent.py -q -n 6 -p no:cacheprovider -k "TestTheExtent or PerSideMargins or LowIsPhysical or LogAxis or SecondAxis or DateAxis or test_each_panel"` passes for the saved and served build rows; `python3 -m pytest test/test_default_axes.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Both modes placed every unextended end at the finished axis's scale at build, and the saved plan carried each line.</done>
</task>

<task type="auto" id="50-07">
  <name>Re-finish the ends after moves</name>
  <files>dash_render.py, test/js_runner.py</files>
  <action><![CDATA[
    Make TR-50.6's `dash_refline_extent` in `_DASH_AXIS_FINISH_JS` and its call at the end of `dash_axis_finish`, and TR-50.7's call in `_dash_refinish_axes`. Touch no other line of the constant, not `_DASH_AXIS_ZOOM_JS` and not `_FILTER_JS`. Make TR-50.9's js_runner extension for Arrow. Add TR-50.8's copy-list lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_refline_extent.py -q -n 6 -p no:cacheprovider -k "AfterAFilterMove or JsEqualsPython or NoUserText or Zoom or Budget or after_a_move"` passes, node tests not skipped; `python3 -m pytest test/test_js_runner.py test/test_natscale_js.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>After every saved and served filter move the ends followed the new scale, through a fixed JS branch that reads no property name from data.</done>
</task>

<task type="auto" id="50-08">
  <name>Check the lines in Chrome</name>
  <files>test/test_refline_extent_chrome.py</files>
  <action><![CDATA[
    Create the browser test of the stubs with `responsive_probe.find_chrome()` and the skip form of `test_by_scales_chrome.py`; it reads the drawn line's pixel ends from a canvas screenshot or the RangeProbe pattern S21's chrome test uses, before and after `move_range_slider(0.3)`, under the shipped CSP.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_refline_extent_chrome.py -q -n0 -p no:cacheprovider -rs` reports 2 passed and no skip.]]></verify>
  <done>Chrome drew stcolor's dashed unextended line dashed and inset, and moved its ends with the axis.</done>
</task>

<task type="auto" id="50-09">
  <name>Flip the naming pins</name>
  <files>test/test_suboption_warnings.py, test/test_reference_lines.py, test/test_suboption_reporting.cscript</files>
  <action><![CDATA[
    Re-measure E6 on this tree: `noextend` leaves the "xline lstyle noextend" row's expected names in `test/test_suboption_warnings.py`; S39's test file (named `test/test_reference_lines.py` here; use S39's name at the base) and SR-06 in `test/test_suboption_reporting.cscript` stop expecting `extend`, `noextend` and `style()` to be named, where they do. One `Flipped:` line per node in `$S/50-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_suboption_warnings.py test/test_reference_lines.py -q -n 6 -p no:cacheprovider` reports 0 failed; `test_suboption_reporting.cscript` through the driver ends with its PASSED line.]]></verify>
  <done>Every pin that named extend, noextend or style() asserted them drawn, with reasons.</done>
</task>

<task type="auto" id="50-10">
  <name>Pass the truth block and parity</name>
  <files>test/test_wp30_truth.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
    Run S50's block through the driver on this tree; correct only a case's page reading if it misread a correct page (never an expectation from twoway's side), and record any such correction in `$S/50-notes.txt`. In `test/test_mode_parity.py`, drop `noextend` from any expected note that still names it (E6), with a `Flipped:` line in `$S/50-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -cE "XE-(0[1-9]|1[01]) PASS" "$S/run_test_wp30_truth.log"` prints 11; `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>twoway and both dash modes agreed on every extent case in the truth block, and the parity corpus expected no note for the drawn sub-options.</done>
</task>

<task type="auto" id="50-11">
  <name>Document extend and noextend</name>
  <files>dash.sthlp, test/test_help_claims_8.py</files>
  <action><![CDATA[
    If 50-03 recorded the directive-count pin red, re-derive its bounds from the regenerated files and write them, with the help's directive-count sentence it reads ("80 to 140 directives" at `c96facd`, as S15/S24/S36 left it at this base), as `# <old> -> <new>: P1.21b extend keys` (R10), with a `Flipped:` line in `$S/50-flips.txt`; otherwise leave both. In "Axis and Display Options" (R3 row S50), after S39's reference-line text (find by text), add one paragraph: `extend`, `noextend` and `style(default|extended|unextended)` as twoway reads them, the scheme's `xyline_extend` keys, the inset by the plot-region margin (none under `margin(zero)`), the ends following every filter move; and remove the three from any sentence that still calls them named (S39's or the "Reference lines" text). Lines at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_8.py test/test_refline_extent.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "noextend" "$WT/dash.sthlp"` is at least 1.]]></verify>
  <done>The help documented the extent sub-options and the scheme keys.</done>
</task>

<task type="auto" id="50-12">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Title `WP30_OPEN["P1.21b"]` ("xline() and yline() noextend, extend and style() are only named, so every line spans the whole frame"): close in place with "Notes: BUGS.md Resolution"; delete only its `WP30_OPEN` line; replace `<!-- WP-30 P1.21b -->` with "Notes: CHANGELOG line". Run test_tracking_documents.py, test_refline_extent.py, test_scheme_fidelity.py, the maps, test_fixtures_are_committed.py and the truth block. `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/50-full-1.log"`, read on `exit=`. Stage exactly the files of `$S/50-files.txt` (including the 26 scheme files) plus these three, with `git add -f test/fixtures/refline_extent_truth.json test/fixtures/scheme_truth.json`; G6, G7, branch check, commit, G7.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/50-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.21b -->' "$WT/CHANGELOG.md"` prints 0; `python3 -c "import sys; sys.path.insert(0, '$WT/test'); import test_tracking_documents as t; print('P1.21b' in t.WP30_OPEN)"` prints `False`; the subject ends `(WP-30 P1.21b)`; G7 prints 0.]]></verify>
  <done>Entry P1.21b was closed naming existing tests, its marker replaced, and one green commit on wp30-s50 was ready to land last in batch 17.</done>
</task>

## Section completion criteria

- Every copy's ends follow twoway's rule; unextended ends sit at the scale, inset by the per-side plot-region margin, in both modes, before and after moves, in by() panels, on second and date axes; Spans unchanged where both ends extend.
- The JS twin agrees with Python and writes only fixed properties; budgets met.
- The 26 scheme files and `scheme_truth.json` carry the two keys, regenerated; fixture committed; flips recorded; one green commit `(WP-30 P1.21b)`, landing last.

## Notes

- **No open maintainer question.**
- **S39's and S47's names.** S39's bulk list, level constant, recorded sub-option keys and note helper, and S47's per-side margin stamp, are read at the base; use their names, never re-implement them.
- **Why not `_dash_hull_ranges`.** Research §3 proposed resolving the ends there; under S21 a by() graph's shared range is written panel by panel, so ends written in `_dash_hull_ranges` could be stale. `_dash_axis_plan` runs once after every range is final in both modes (D-50d).
- **Shared lines with S48 and S49.** `test/test_mode_parity.py`: CORPUS and MOVE_CORPUS cases from the batch, and S49 may also extend `_annotations` (HBar/HArea): the merger keeps every branch. S50 lands last, so its regeneration runs on a tree holding S48's and S49's changes; a conflict in a generated file is resolved by re-running the extractor (R7).
- **python_exec hazard.** Check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Merge rules.** R1: S50's truth block only. R2: S50's anchor after S39's names. R3: "Axis and Display Options" (S50's row). R4/R5: the one `P1.21b` marker, the entry, the key. R7: one new fixture and extractor; the scheme regeneration by one extractor run, landing last (A152); a conflict means re-running it on the merged tree. R8: one CORPUS and one MOVE_CORPUS case, the Arrow profile. R9: E6. R10: the directive-count pin only if red. R11: S50 is batch 17's finisher editor (`_dash_axis_plan`, `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes`), keeping A9's budgets.
- **Landing (merger).** detect-changes names `_dash_refline_draw`, `_dash_refline_extent_flags`, `_dash_refline_extents`, `_dash_axis_plan`, `_dash_refinish_axes`, `SchemeParser._init_properties`, `_glyph_layer_lines`, the extractor's symbols and test symbols; the constant edits (`_FALLBACK_PROPS`, `_DASH_AXIS_FINISH_JS`) show as their containers.
- **Commit message.** Body: `$S/50-P1.21b-failure.txt`; Overview's measured block; TR-50.1-TR-50.11 in both modes; `Regression: test/test_refline_extent.py::<Class>::<test> -- failed at <base sha> with <text>` per node (`test/test_wp30_truth.cscript XE-01`); the `Flipped:` lines; `Fixture: test/fixtures/refline_extent_truth.json (scripts/extract_refline_extent_truth.do)` and `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`; `BUGS.md: "xline() and yline() noextend, extend and style() are only named, so every line spans the whole frame" (closed)`.
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.21b). xline() and yline() decide each copy's two ends by twoway's edit order -- the scheme's yesno xyline_extend_low and xyline_extend_high (now read by SchemeParser and carried by the 26 shipped schemes), then style(default|extended|unextended), then noextend, then extend -- with an unknown style() noted as twoway notes it (_dash_refline_extent_flags); a copy with an unextended end is drawn as a headless Arrow at the axis's scale, inset by that side's plot-region margin, low being the bottom or left end, on second, log and date axes and in every by() panel (_dash_refline_draw, _dash_refline_extents), placed at build in both modes (_dash_axis_plan) and again after every filter move in the served app (_dash_refinish_axes) and the saved page (_DASH_AXIS_FINISH_JS), never widening an axis; copies with both ends extended stay Spans. Pinned by test/test_refline_extent.py::TestTheExtent::test_probe, test/test_refline_extent.py::TestPerSideMargins::test_margin, test/test_refline_extent.py::TestAfterAFilterMove::test_range_move, test/test_refline_extent.py::TestJsEqualsPython::test_random_moves, test/test_wp30_truth.cscript XE-01; fixture test/fixtures/refline_extent_truth.json. Residual, deferred (WP-30): when a user scheme extends only one end, that end stays at the frame of the last re-finish if the reader zooms out past it; an out-of-range line is clipped at the frame (P2.54).
  ```
- **CHANGELOG line** (replaces its marker in place):

  ```
  ### Results that change
  - `xline()` and `yline()` with `noextend` or `style(unextended)` stop at the axis's scale, inset from the frame by the plot-region margin, as twoway draws them: `dash scatter mpg weight, xline(3000, noextend)` drew the line across the whole plot region and named `noextend`, and now draws it from 10 to 41 on the mpg scale (2.2% of the graph's smaller side short of each edge under s2color), following the axis after every filter move; `extend` and `style(extended)` win; a scheme's `yesno xyline_extend_low` and `xyline_extend_high` are read. (WP-30, P1.21b)
  ```
- **Notes for the closeout (S58; A145).** GAPS2.md B22 (:595-604): parts d (style()) and e (noextend) closed by `<sha>`, with S39's a, b, d (lstyle) parts; TWOWAY_COVERAGE_AUDIT.md:139 (reference-line sub-options no longer warn); DROPIN-REMAINING.md:132's extent half. New P2 row: a one-end-extended copy (asymmetric user scheme) does not follow zoom-out past the last re-finish's frame. AGENTS.md invariant: "an unextended reference line is an Arrow whose ends only `_dash_refline_extents` and `dash_refline_extent` write, from the finished range and its margin." Unverified: Stata 14-18.5 (M2).
