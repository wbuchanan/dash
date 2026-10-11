# Section 20: Weighted markers (aweight marker sizes on the marker types)

> Part of: WP-31 · GAPS3 rows: C9 · Risk: yellow · Batch: 7 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U20

## Overview

**What is wrong today.** GAPS3 C9 (GAPS3.md:128): "Weighted scatter markers are not sized by `[aw]`." Evidence dash_render.py:14944-14973 (`map_scatter`'s size path: `size=self.scheme.default_marker_size(color_idx)` at :14950, then `_apply_marker_opts` for `msize()`; no weight is read) and dash.ado:5367 (`local _wt_honoured "lfit qfit lfitci qfitci lpoly lpolyci fpfit fpfitci histogram kdensity mspline mband"`: on every other type the weight is accepted, NOT written to the spec, and named in the note by type (:5734-5736 `_seg_wtok`). TWOWAY_COVERAGE_AUDIT.md:61 ("`aweight` does not size markers"), :120 ("raw glyph weights are ignored, including scatter aweight marker sizing"). twoway sizes the markers of every yxview type that draws markers by the weight (`B/y/yxview.class:422-423` `if 0`.wvar' { ._draw_weighted_points }`; `:792-822`).

**After this section** `scatter y x [aw=w]` (and `[fw=w]`, `[pw=w]`: twoway's `_draw_weighted_points` reads `.wvar` whatever the weight type -- measured U20-01) draws each marker with **area proportional to its weight**, scaled as twoway scales it (`yxview.class:792-822`, read 10oct2026):
```
local max = max_wted_symsize.gmval (scheme numstyle max_wted_symsize 10; default 10)
if .scale_by_max == 0 (the default, :32):  scale = 1.5 / sqrt(w_min)      // "1.5 std symsize"
else:                                       scale = 1 / sqrt(w_max)
if scale * sqrt(w_max) > max:               scale = max / sqrt(w_max)
gdi scatterweight serset x y wvar scale     // marker i drawn at symbolsize scale*sqrt(w_i) (relative units)
```
So the smallest weight draws a marker of 1.5 relative units (1.5 × 2.88 pt = 4.32 pt = 5.76 px at dash's reference, `OptionTranslator.resolve_size`'s rule "a number is Stata's relative unit, 2.88 pt" and `PX_PER_PT = 4/3`, dash_render.py:7016, 7098-7120), the others `1.5*sqrt(w_i/w_min)` units, and if the largest would exceed 10 units every marker is scaled down so the largest is 10. A negative weight → twoway prints `negative weights not allowed, plot ignored` and draws no markers (`:794-797`); a missing weight drops the row (twoway's touse). The same rule applies to every marker type that takes a weight: scatter, connected (markers only), dot (the marker, not the dot rows), dropline (the marker), rscatter, rcapsym (the end markers), rconnected (markers), pcscatter, pccapsym (`yxview_parse:185` admits `[aw fw pw]` for every yxview type; the pc and range views draw markers through the same `_draw_points`/`_draw_weighted_points`). The weight is honoured, written to the spec as `weight`/`wexp`, and no longer named for these types; on line, area, bar, spike, rbar, rspike, rcap, rline, rarea, tsline, tsrline, pcspike, pcarrow, pcbarrow (no markers) twoway accepts and ignores the weight and says nothing, and so does dash (Q36: an option that draws nothing different is silent): the note stops for ALL glyph types and `_wt_honoured` becomes the list of types that WRITE the weight (the computing types plus the marker types), while the non-marker glyph types write nothing and say nothing (D-20a). rpcap and rpspike (S21, merged after S20 in batch 7) register their own names in `_wt_honoured` and `_DASH_WEIGHT_ACCEPTS` if S21's extractor shows twoway sizes their y3 marker; S20 owns the weighted-marker machinery they use.

**Why one section.** One rule in one helper, applied in the marker-drawing mappers S20 owns in batch 7 (index: "map_scatter size path: 20").

**Test order and commit rule.** One row, one commit `(WP-31 C9)`: 20-01 tests + extractor; 20-02 dash.ado + renderer; 20-03 certify/document/commit.

### Section decisions (binding on the executor)

- **D-20a. Weights on glyph types stop being named.** twoway accepts `[aw]` on every yxview type and draws nothing different where there are no markers; it prints nothing. dash prints nothing either (Q36) and writes `weight`/`wexp` into the spec only for the types that use it (the marker types and the computing types), so an unweighted spec text is byte-identical to today's for line/bar/area. The help's weights paragraph (TWOWAY_COVERAGE_AUDIT.md:120-129 matrix and dash.sthlp's weight section, grep `{marker weights}`) is rewritten accordingly (R3: S20 owns it).
- **D-20b. One helper, both modes.** `_dash_weighted_sizes(w, default_px, max_units=10.0, ref_in=4.0)` (module-level, copied by name) returns an array of pixel diameters: `w_min = min(w > 0)`, `scale = 1.5/sqrt(w_min)`, `if scale*sqrt(w_max) > max_units: scale = max_units/sqrt(w_max)`, `units_i = scale*sqrt(w_i)`, `px_i = units_i * 2.88 * (4/3) * (ref_in/4.0)` -- the same conversion `translate_msize` applies to a bare number (`T.resolve_size(value, "marker", ...) * T.PX_PER_PT`, :7577-7594); `default_px` is unused by the rule but kept so a scheme's `max_wted_symsize` stub, when dash reads it (D-20c), can scale. `msize()` with a weight: twoway's `_draw_weighted_points` ignores the marker size (the symbolsize is the weight's) -- measured U20-02; if twoway ignores `msize()`, dash ignores it silently; if it multiplies, dash multiplies.
- **D-20c. `max_wted_symsize` is read from the scheme.** `SchemeParser` gains `max_wted_symsize` (numstyle; s2color 10; default 10 when absent, as `yxview.class:803` `cond(max, max, 10)`); the stub is added to `dash-s2color.scheme` and the shipped scheme files with each Stata scheme's value (M7: a number, no colour space issue).
- **D-20d. Negative and missing weights.** A negative weight: the layer's markers are not drawn and twoway's text `negative weights not allowed, plot ignored` is printed once through `_dash_warn_once` (the existing note path, both modes); a missing weight drops the row from the marker set (twoway's sample); zero weights: `sqrt(0) = 0` → a 0 px marker (twoway draws nothing visible; measured U20-03 whether the row is kept or dropped).
- **D-20e. Linked selection and the saved move.** The size column `__dash_wsize` is a per-row column on the marker's source (saved page: the row filter keeps it; served: the mapper recomputes it). twoway's scale uses the DRAWN sample's `w_min`/`w_max`, so after a filter move the sizes must be recomputed from the kept rows. The served app re-runs the mapper (exact). S20 cannot recompute on the saved page (S22 owns `_FILTER_JS` in batch 7): the saved page's marker sizes after a move are redrawn by S52 (batch 17), DECISIONS A23 -- a `__dash_wsize` recompute in `_FILTER_JS` from the kept rows' weights through a JS twin of `_dash_weighted_sizes`. S20 opens no residual BUGS entry and writes no help sentence about the saved page; `TestAfterAMove::test_saved` is written xfail(strict) with reason `fixed in S52 (batch 17), DECISIONS A23` and S52 flips it.

## Risk: [yellow] -- marker sizes change on every weighted marker layer; the weight stops being named on fourteen types

**Why.** A per-row `size` field replaces a scalar on the Scatter glyph; `_apply_marker_opts`'s `msize()` path assumes a scalar `glyph.size` (:13268-13292 reads `_cur = glyph.size`); the mlabel radius (`_mlabel_radius_px`) reads the marker size for label placement.

**Risk factors.** 1. `_apply_marker_opts` and `_mlabel_radius_px` on a field-valued size. 2. Linked brushing copies (`nonselection_glyph`, `muted_glyph`) must carry the same size field (test_brushed_copies.py pins widths for bars; markers' sizes similarly). 3. The spec's `weight`/`wexp` keys now appear for marker types: `_DASH_WEIGHT_ACCEPTS` (:397) does not list them, so `_layer_weight_column` would say "refused"; it must gain the marker types with `("aw","fw","pw")`. 4. The note's disappearance on fourteen types: test_help_claims/test_weights-style pins (grep `named in the note by type`). 5. `rscatter`'s stacked source doubles rows: the weight column is stacked too.

**Mitigation.** 1. `_apply_marker_opts`: when `glyph.size` is a field spec, `msize()` is ignored silently per D-20b's measurement (or multiplies the column); `_mlabel_radius_px` takes the per-row size column when present (labels placed per marker). 2. `TestBrushedCopiesCarryTheSize`. 3. Extend `_DASH_WEIGHT_ACCEPTS` with the nine marker types; `_DASH_WEIGHT_INERT` unchanged. 4. Flips with reasons. 5. Stack the weight with the ends.

## Dependencies

- **Depends on: 01.** **Blocks:** none. **Parallel batch 7** with S22 (`_FILTER_JS`) and S21 (plot-type registration for rpcap/rpspike). S20 edits `map_scatter`'s size path, the marker-drawing mappers' size kwarg, `_apply_marker_opts`'s size read, `_mlabel_radius_px`, `_DASH_WEIGHT_ACCEPTS`, dash.ado's `_wt_honoured`; S21 adds new mappers and does not edit these (S21's rpcap/rpspike markers take the weight through the same helper if S21 lands after -- note for the merger: S20 before S21).

## Evidence

Anchors at `6370ca4`.

### The size path

dash_render.py:14944-14973 (`map_scatter`):
```
14946        _scatter_kwargs: dict = dict(
14947            x=eff_x,
14948            y=eff_y,
14949            source=plot_source,
14950            marker=marker,
14951            size=self.scheme.default_marker_size(color_idx),
...
14968        r = fig.scatter(**_scatter_kwargs)
14969        self._apply_marker_opts(r, options, traits=(_hollow, _factor))
```
`_apply_marker_opts` (:13243-13330) reads `msize` at :13268-13292 (`_cur = glyph.size`, `glyph.size = max(0.0, self.tr.translate_msize(options["msize"], float(_cur), _ref))`). Other marker sites: `map_rscatter` :20323-20335 (`size=self.scheme.default_marker_size(color_idx)`), `map_rcapsym` :19177, :19183, `map_pccapsym` :19959, `map_pcscatter` :19520ff, `map_dropline` (its Scatter), `map_connected`/`map_rconnected`/`map_dot` through `map_scatter`.

### The weight plumbing

dash.ado:5355-5400: `_wt_honoured` list (:5367), the refusal table (iweight everywhere r(101); lowess every weight; histogram fw only; kdensity/lpoly/lpolyci no pw; scatteri/pci/pcarrowi `weights not allowed` r(198)); :5399 and :5579 write `weight`/`wexp` into s() for honoured types; :5734-5736 the note token `[aweight=w]` for the others; :5901 `_seg_wv` (the weight variable in the layer's sample). dash_render.py:397-409 `_DASH_WEIGHT_ACCEPTS`; `_dash_weight_spec(options)` (:22002) returns `(wtype, wexp)`; `GlyphMapper._layer_weight_column` (:15737-15756) → `"refused"` when the type is not in the table; `_layer_weights` (:15771-15884) → `(cols..., w, wtype)` with notes for refused/inert/non-numeric/negative.

### twoway's rule (`B/y/yxview.class`, read 10oct2026)

```
 27    double wvar                // weight variable id
 32    scale_by_max    = 0
422    if 0`.wvar' {              // weighted
423        ._draw_weighted_points
792 program _draw_weighted_points
793    if (! 0`.style.marker.drawn')  exit
795    if 0`.serset[`.wvar'].min' < 0 {
796        di as error "negative weights not allowed, plot ignored"
797        exit
798    }
802    local max = 0`.`.`.plotregion'.graphs[1]'.style.max_wted_symsize.gmval'
803    local max = cond(`max' , `max', 10)
805    if `.scale_by_max' == 0 {
806        local scale = 1.5 / sqrt(`.`wtseries'.min')
807    }
808    else {
809        local scale = 1 / sqrt(`.`wtseries'.max')
810    }
813    if `scale' * sqrt(`.`wtseries'.max') > `max' {
814        local scale = `max' / sqrt(`.`wtseries'.max')
815    }
820    gdi scatterweight `.serset.id' `.xvar' `.yvar' `.wvar' `scale'
```
`scheme-s2color.scheme:47 numstyle max_wted_symsize 10`; `style/graphstyle-default.style:44 set max_wted_symsize scheme max_wted_symsize`. `gdi scatterweight` is compiled: the per-marker size `scale*sqrt(w_i)` in symbolsize relative units is the reading of "1.5 std symsize" and is PROVED by the fixture (W01: the SVG marker radii of `scatter mpg weight [aw=price]` vs the radius of an unweighted `msize(1.5)` marker -- equal for the smallest weight -- and `r_i/r_min = sqrt(w_i/w_min)` within 2%).

### Fixtures on disk

`stat_truth.json` (weight_acceptance, WP-18). New: `weighted_markers_truth.json`.

### Pinned tests to flip (never delete)

- Tests asserting the weight note on glyph types: `grep -rn "named in the note by type\|aweight.*ignoring\|\[aw" test/*.py test/*.cscript` -- expected: test/test_help_claims_6.py (6 hits), test/test_layer_reports.py:1, test_statistical_helpers.py (weights on estimators -- unchanged), test_twoway_option_parity.cscript weight cases (`grep -n "weight" test/test_twoway_option_parity.cscript | grep -i "note\|ignor"`). Each that expects the note for scatter/connected/dot/dropline/rscatter/rcapsym/rconnected/pcscatter/pccapsym (or line/bar/area under D-20a) is flipped with `Flipped (WP-31 C9): twoway sizes markers by the weight and says nothing (weighted_markers_truth.json W01); on markerless types twoway is silent too`.
- test/test_unsupported_report_is_true.py: no option change (weights are not options); `NOT_IN_FILE`/`LIVE_VALUES` untouched.
- test/test_glyphs.py marker size tests (`glyph.size > 8` forms) are unweighted: unchanged.
- TWOWAY_COVERAGE_AUDIT.md rows 61, 68, 120-129 (the weight matrix gains a "Marker types" row: aweight, fweight, pweight size the markers).

## User stories

- US-20.1 As a Stata user pasting `twoway scatter mpg weight [aw=price]`, I want marker areas proportional to price, scaled as twoway scales them.
- US-20.2 As a Stata user, I want the same on connected, dot, dropline, rscatter, rcapsym, rconnected, pcscatter and pccapsym markers.
- US-20.3 As a Stata user, I want a negative weight to draw no markers with twoway's message, and no note for a weight on a type that draws nothing different.
- US-20.4 As a dashboard user, I want the served app to rescale the markers after a filter move (the saved page's rescale is S52's, batch 17).

## Business requirements

- BR-20.1 On every marker type, with `[aw|fw|pw]`, marker i's diameter in relative units is `scale*sqrt(w_i)` with twoway's `scale` and the scheme's `max_wted_symsize` cap; the smallest weight is 1.5 units.
- BR-20.2 Negative weights: twoway's message once, no markers; missing weights drop the row; `msize()` behaves as measured.
- BR-20.3 No weight is named on any glyph type; the refusal table (iweight, lowess, histogram, pweight on kdensity/lpoly, immediates) is unchanged.
- BR-20.4 Sizes follow the drawn sample in the served app; the saved page's marker sizes after a move are redrawn by S52 (batch 17), DECISIONS A23.

## Technical requirements

- TR-20.1 **dash.ado**: :5367 `_wt_honoured` becomes `"lfit qfit lfitci qfitci lpoly lpolyci fpfit fpfitci histogram kdensity mspline mband scatter connected dot dropline rscatter rcapsym rconnected pcscatter pccapsym"` with the comment `// WP-31 C9: the marker types size their markers by the weight (yxview.class _draw_weighted_points); the markerless glyph types take a weight and draw nothing different, as twoway does, and say nothing`; :5734-5736: delete the `_seg_wtok` note token (the weight is never named); keep every refusal (:5370-5395). The spec keys `weight`/`wexp` are written by :4458's `weight wexp` for the honoured list as today.
- TR-20.2 **Renderer helper**: `_dash_weighted_sizes(w, max_units=10.0, ref_in=4.0)` after `_dash_weight_spec` (:22002-22040); copy list: functions tuple after `_dash_reference_lines` (:47223); function_test_map.py `'_dash_weighted_sizes': 'test/test_weighted_markers.py::TestTheRule::test_matches_twoway'`. Arithmetic as D-20b; returns `np.ndarray` of px; NaN for a missing weight; raises nothing (an empty or all-missing array returns an empty array / all NaN).
- TR-20.3 **`_DASH_WEIGHT_ACCEPTS`** (:397-409) gains `"scatter": ("aw","fw","pw"), "connected": ..., "dot": ..., "dropline": ..., "rscatter": ..., "rcapsym": ..., "rconnected": ..., "pcscatter": ..., "pccapsym": ...`; `_layer_weights` (:15771) is reused to read the column: in `map_scatter` after `plot_source` is final (:14944): `_w = self._marker_weights(plot_source, options, "scatter")` (new method: `_dash_weight_spec(options)`; if `wtype` is None → None; else the column `wexp` from `plot_source.data` as floats; a negative → `_dash_warn_once(("weight-negative-markers", layer), "negative weights not allowed, plot ignored")` and return "skip"); when an array: `plot_source.data["__dash_wsize"] = _dash_weighted_sizes(_w, self.scheme.max_wted_symsize)` and `_scatter_kwargs["size"] = "__dash_wsize"`; when "skip": `_scatter_kwargs["size"] = 0.0` and the renderer stays visible (twoway draws no markers but keeps the plot's key). Same pattern in `map_rscatter` (stack the weight with the two ends), `map_rcapsym` (both end markers), `map_pcscatter`, `map_pccapsym`, `map_dropline`'s Scatter; `map_connected`, `map_rconnected`, `map_dot` inherit through `map_scatter`.
- TR-20.4 **`_apply_marker_opts`** (:13268-13292): `if isinstance(glyph.size, str)` (a field) → apply D-20b's measured rule for `msize()` (ignore silently, or multiply the column by the ratio `translate_msize(value)/default`); `_mlabel_radius_px(options, default)` callers in the weighted mappers pass the per-row column: `_apply_mlabel_opts` gains an optional `radius_col` argument used when given (a LabelSet offset per row needs a column: `x_offset`/`y_offset` as fields -- read `_apply_mlabel_opts` :14104 before editing; if its offsets are scalars, compute per-row offsets into two new `__dash_mlab_dx/dy` columns on the label source).
- TR-20.5 **Scheme**: `SchemeParser.max_wted_symsize` property reading `numstyle max_wted_symsize`, default 10.0; the stub added to `dash-s2color.scheme` and the shipped scheme files; `test_unread_scheme_directives.py` read set extended.
- TR-20.6 **Brushed copies**: where the renderer's `nonselection_glyph`/`muted_glyph` are built (grep `nonselection_glyph` in the marker mappers or `_dash_brush_copies`), the size field is carried (a copy built with `glyph.clone()` carries it; one built with explicit kwargs must pass `size=glyph.size`).

## Boundaries

- No `_FILTER_JS` (S22). No new plot type (S21). No change to the computing types' weights or to the refusal table. Dot rows (S18) are not weighted (twoway's dots are `gdi point`s; only `_draw_points` is weighted).
- `msize()` under a weight: the measured rule only.

## Stata truth

New `scripts/extract_weighted_markers_truth.do` → `test/fixtures/weighted_markers_truth.json`; `sysuse auto` (keep in 1/8 for readable SVGs):
- `W01` `twoway scatter mpg weight [aw=price] in 1/8, name(w1)` → `graph export` SVG: marker circle radii by observation (sorted by price), and `twoway scatter mpg weight in 1/8, msize(1.5)` radii (the 1.5-unit reference) and `msize(10)` (the cap reference); whether `.w1.plotregion1.plot1.wvar` is set; `.graphs[1].style.max_wted_symsize.gmval`.
- `W02` `[fw=rep78]`, `[pw=price]`: radii (whether the same rule applies); `W03` `[aw=price] msize(huge)`: radii vs W01 (whether msize() changes them); `W04` a weight variable with one value 1 and one 10000 (`gen w = cond(_n==1, 10000, 1)`): the cap (largest radius equals the `msize(10)` reference); `W05` a negative weight: rc, message text, marker count 0; `W06` a zero weight and a missing weight: marker count; `W07` `twoway line mpg weight [aw=price]`: rc 0, no message (silence on markerless types); `W08` `twoway dot mpg weight [aw=price] in 1/8`: marker radii (dots unchanged); `W09` `rscatter lo hi weight [aw=price]`: radii per end.
`_meta`, `git add -f`, test_fixtures_are_committed.py.

## TDD test stubs

New `test/test_weighted_markers.py`:
- Test: `_dash_weighted_sizes([1,4,9])` = `[1.5, 3.0, 4.5]` units × 3.84 px; the cap: `[1, 10000]` → largest 10 units; NaN stays NaN -- `TestTheRule::test_arithmetic`, `::test_cap`, `::test_missing` (red).
- Test: the rule reproduces W01/W02/W04 radii ratios within 2% and the smallest equals the `msize(1.5)` reference -- `TestTheRule::test_matches_twoway[probe]` (red).
- Test: `scatter [aw=price]` draws `size="__dash_wsize"` with the rule's values, both modes -- `TestScatter::test_size_field[mode]` (red); the brushed copies carry it -- `::test_brushed_copies_carry_the_size[mode]` (red); `msize(huge)` behaves as W03 -- `::test_msize_rule[mode]` (red).
- Test: each marker type (connected dot dropline rscatter rcapsym rconnected pcscatter pccapsym) sizes its markers; rscatter's two ends -- `TestEveryMarkerType::test_sized[mode-type]` (red).
- Test: a negative weight → no markers (size 0) and twoway's text once; a missing weight drops the row; zero per W06 -- `TestBadWeights::test_negative[mode]`, `::test_missing`, `::test_zero` (red).
- Test: the served app rescales after a move -- `TestAfterAMove::test_served` (red); the saved page rescales after a move -- `::test_saved`, xfail(strict) with reason `fixed in S52 (batch 17), DECISIONS A23`; S52 flips it.
- Test: dash.ado's `_wt_honoured` equals the list; no `_seg_wtok`; `_DASH_WEIGHT_ACCEPTS` has the nine; the helper on the copy list; the scheme stub read -- `TestTheAdoText::test_lists`, `TestTheServedCopy::test_name`, `TestScheme::test_max_wted_symsize` (red).

cscript, block `* ==== S20 C9: weighted markers ====`:
- U20-01 `dash scatter mpg weight [aw=price] in 1/8, name(u20)`: no `ignoring` note, rc 0; the spec carries `"weight":"aweight"`, `"wexp"`; the python render's `__dash_wsize` ratios equal twoway's W01 radius ratios within 2% (radii from the SVG the block exports: `graph export` of twoway's run in the same session); the smallest equals dash's `msize(1.5)` scatter size.
- U20-02 `[aw=price] msize(huge)`: dash follows W03 (equal sizes to U20-01 if twoway ignores msize; scaled if not).
- U20-03 `gen wneg = -1 in 1`, `scatter mpg weight [aw=wneg]`: dash prints `negative weights not allowed, plot ignored` (`cert_log_has`), rc equals twoway's; a zero/missing weight per W06.
- U20-04 `dash line mpg weight [aw=price]`: rc 0, no note (was named); `dash bar mpg weight [fw=rep78]`: rc 0, no note.
- U20-05 `dash rscatter lo hi weight [aw=price]`: both ends sized; `dash dot mpg weight [aw=price]`: the marker sized, the dot rows (S18) at their style size.
- U20-06 the refusals stay: `scatteri 1 2 [aw=price]` → `weights not allowed` r(198); `lowess mpg weight [aw=price]` → r(101) `weights not allowed` (compared with twoway).

Parity (R8): CORPUS `_case("scatter aweight", [plot_for("scatter", {"weight":"aweight","wexp":"price"})])`, `_case("rscatter aweight", ...)`, `_case("dot aweight", ...)`; MOVE_CORPUS `_case("scatter aweight after a move", ...)`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| the size rule | pytest TestTheRule; U20-01 | weighted_markers_truth W01 W02 W04 | -- |
| scatter and the marker types | pytest TestScatter/TestEveryMarkerType; U20-01/05 | W01 W08 W09 | yes |
| msize under a weight | pytest; U20-02 | W03 | yes |
| bad weights | pytest TestBadWeights; U20-03 | W05 W06 | yes |
| silence on markerless types; refusals kept | U20-04, U20-06 | W07, stat_truth weight_acceptance | n/a |
| moves | TestAfterAMove | -- | served exact; saved fixed in S52 (batch 17) |

AC-20.1 stubs green (the saved xfail strict); AC-20.2 U20-01..06 PASS; AC-20.3 dash.sthlp's weights section rewritten (marker types sized; markerless types silent); AC-20.4 TWOWAY_COVERAGE_AUDIT.md rows 61, 68, 120 and the matrix annotated `[WP-31 C9, commit pending: corrected -- weighted marker sizes]` (the merger's step k.3b fills the sha, DECISIONS A11).

## Tasks

**Commit boundary.** 20-01, 20-02 steps; 20-03 commits `Size markers by the weight as twoway does on every marker type (WP-31 C9)` on `wp31-s20`.

<task type="auto" id="20-01">
  <name>Write the failing weighted-marker tests and the truth extractor</name>
  <files>test/test_weighted_markers.py, scripts/extract_weighted_markers_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_weighted_markers_truth.do on scripts/extract_default_base_truth.do's skeleton with probes W01-W09 of "Stata truth" (marker radii from `graph export` SVG through test/cert_svg.do's `svg_truth.svg_document`, matched to observations by their (x, y) data position mapped through the axes; the `msize(1.5)` and `msize(10)` reference radii; `.graphs[1].style.max_wted_symsize.gmval`; refusal rc/text via `capture noisily`). Run through the slot wrapper; `git add -f test/fixtures/weighted_markers_truth.json`; register it. Create test/test_weighted_markers.py with every stub (TestTheRule, TestScatter, TestEveryMarkerType, TestBadWeights, TestAfterAMove with the strict xfail, TestTheAdoText, TestTheServedCopy, TestScheme). Run `python3 -m pytest test/test_weighted_markers.py -q -p no:randomly > <scratch>/20-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/20-01-failure.txt prints >= 12; python3 -c "import json;d=json.load(open('test/fixtures/weighted_markers_truth.json'));r=d['W01']['radii'];print(len(r), d['W01']['max_wted_symsize'])" prints 8 10.]]></verify>
  <done>The weighted-marker tests fail against the batch-7 base and twoway's marker radii, cap, msize interaction and refusal texts are committed.</done>
</task>

<task type="auto" id="20-02">
  <name>Honour the weight on the marker types in dash.ado and both renderers</name>
  <files>dash.ado, dash_render.py, dash-s2color.scheme</files>
  <action><![CDATA[dash.ado: TR-20.1 (:5367 list and comment; delete the note token at :5734-5736 and the `_seg_wtok` use that follows). dash_render.py: TR-20.2 (`_dash_weighted_sizes` after `_dash_weight_spec` :22002-22040, copy-list entry after "_dash_reference_lines" :47223), TR-20.3 (`_DASH_WEIGHT_ACCEPTS` :397-409; `GlyphMapper._marker_weights` method beside `_layer_weight_column` :15737; the `size` field in map_scatter :14944-14968, map_rscatter :20323-20335, map_rcapsym :19170-19190, map_pcscatter :19520-19530, map_pccapsym :19950-19960, map_dropline's Scatter), TR-20.4 (`_apply_marker_opts` :13268-13292 field branch per W03; `_apply_mlabel_opts` :14104 per-row radius when the size is a field), TR-20.5 (`SchemeParser.max_wted_symsize`; the stub in dash-s2color.scheme and every shipped scheme file with Stata's values; test_unread_scheme_directives.py read set), TR-20.6 (brushed copies carry the field). Add function_test_map.py's `_dash_weighted_sizes` entry (TR-20.2; a test map, implied by A13). Flip the tests found by `grep -rln "named in the note by type\|\[aw" test/*.py` that expected the weight note on a glyph type (docstring reason of Evidence). Run `python3 -m pytest test/test_weighted_markers.py test/test_glyphs.py -k "Scatter or Dot or Marker" test/test_help_claims_6.py test/test_layer_reports.py test/test_statistical_helpers.py -k weight test/test_brushed_copies.py test/test_unread_scheme_directives.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_mode_parity.py -k aweight -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed (the saved xfail xfailed); `grep -c "_seg_wtok" dash.ado` prints 0; `python3 -c "import dash_render as d;print(d._DASH_WEIGHT_ACCEPTS['scatter'])"` prints ('aw', 'fw', 'pw'); `grep -c "max_wted_symsize" dash-s2color.scheme` prints 1.]]></verify>
  <done>Both renderers size every marker type's markers by the weight with twoway's rule and cap, dash.ado writes the weight for them and names it on no glyph type.</done>
</task>

<task type="auto" id="20-03">
  <name>Certify, document and commit C9</name>
  <files>test/test_wp31_truth.cscript, test/test_mode_parity.py, dash.sthlp</files>
  <action><![CDATA[Append `* ==== S20 C9: weighted markers ====` (U20-01..U20-06; this section's one row, so its one block) above the marker (after S19's block if present) and run with `WP31_ONLY=S20`; U20-06 compares against `capture noisily twoway` in the same block. Append the Parity (R8) CORPUS and MOVE_CORPUS entries to test/test_mode_parity.py under `# WP-31 C9: weighted markers`. dash.sthlp: rewrite the weights section (grep `{marker weights}`; the paragraph that says a weight on the glyph types is "accepted and named in the note") to: "On scatter, connected, dot, dropline, rscatter, rcapsym, rconnected, pcscatter and pccapsym an aweight, fweight or pweight sizes the markers as twoway does: the smallest weight draws a 1.5-unit marker, every other `1.5*sqrt(w/wmin)` units, scaled down together so the largest is at most the scheme's max_wted_symsize (10); a negative weight draws no markers, with twoway's words. On line, area, bar, spike, the range lines and bars and the pc lines twoway accepts a weight and draws nothing different, and so does dash, saying nothing. The served app rescales the markers to the rows a filter keeps." (S52, batch 17, extends the sentence to both modes when it redraws the saved page's sizes, DECISIONS A23). TWOWAY_COVERAGE_AUDIT.md: rows 61, 68 and the weight matrix at :120-129 (add the marker-types row; annotate `[WP-31 C9, commit pending: corrected -- weighted marker sizes]`; the merger's step k.3b fills the sha, DECISIONS A11). BUGS.md: close C9's entry (Resolution form; the Resolution ends "the saved page's marker sizes after a move are redrawn by S52 (batch 17), DECISIONS A23"; no residual entry is opened). GAPS3 §9: `- **C9 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b fills the sha, DECISIONS A11). Replace the `<!-- WP-31 C9 -->` markers (Results: "scatter mpg weight [aw=price]: markers sized by price (was: one size, the weight named)"; Changed behaviour: "a weight on a glyph type is no longer named in the note; a negative weight draws no markers, twoway's `negative weights not allowed, plot ignored`"). Run `python3 -m pytest test/test_weighted_markers.py test/test_function_test_map.py test/test_help_conformance.py test/test_tracking_documents.py -q`; commit with the BRIEF body; grep for `claude|anthropic`.]]></action>
  <verify><![CDATA[Stata log shows "U20-01 PASS" .. "U20-06 PASS"; pytest 0 failed; `git log -1 --format=%s` ends "(WP-31 C9)"; `grep -c "max_wted_symsize" dash.sthlp` prints >= 1; `grep -c "C9 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `grep -c "weighted marker sizes" BUGS.md` counts no open (`- [ ]`) entry.]]></verify>
  <done>C9 is closed in one commit with tests, fixture, help, audit, BUGS.md, GAPS3 and CHANGELOG lines; the saved page's rescale after a move is S52's (batch 17).</done>
</task>

## Section completion criteria

- Stubs green (saved xfail strict); U20-01..06 PASS; flips with reasons.
- `_dash_weighted_sizes` on the copy list and in function_test_map.py; `_DASH_WEIGHT_ACCEPTS` has the nine marker types; `max_wted_symsize` read from every shipped scheme.
- Help, audit, BUGS.md closed (no residual), GAPS3 C9 Tracked `Closed in WP-31 ... commit pending`, CHANGELOG in the one commit.

## Notes

- **Renderer order:** the size field is set at construction (`fig.scatter(size="__dash_wsize")`) so `_apply_marker_opts`'s factor/hollow logic sees a field and takes the measured `msize()` branch.
- **Copy list (R2):** `_dash_weighted_sizes` after `_dash_reference_lines` (:47223); `_marker_weights` and the scheme property are class members.
- **Spec stability:** an unweighted layer's `"options"` text is unchanged (the `weight`/`wexp` keys are written only when a weight is given, as :4433-4437's comment promises).
- **Fixture rule (R7)**; **python_exec hazard**.
- **Security:** the weight expression reaches the renderer as a validated variable name (`_seg_wexp` is a variable `_dash_process_segment` generated or confirmed); the size column holds numbers only.
- **Merge rules cited:** R1, R2, R3 (S20 owns the weights section and the audit matrix), R7, R8, R9, R12 (S20 is batch 7's `map_scatter` size-path owner; S22 owns `_FILTER_JS`; S21 adds mappers only).
- **Commit body lines:** `Regression: test/test_weighted_markers.py::TestTheRule::test_matches_twoway[W01] -- failed at <base> with <text>`; `Flipped: test/test_help_claims_6.py::<node> -- "the weight is named on scatter" was wrong because twoway sizes the markers and says nothing (weighted_markers_truth.json W01, W07)`; `Fixture: test/fixtures/weighted_markers_truth.json (scripts/extract_weighted_markers_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS3: C9 Tracked`.
- **Decisions for maintainer ratification:** D-20a (no note on markerless glyph types), D-20b (`msize()` under a weight follows the measurement). D-20e is settled by DECISIONS A23 (the saved page's marker sizes after a move are redrawn by S52, batch 17) and is not for ratification.
- **For S52 (batch 17).** Recompute `__dash_wsize` in `_FILTER_JS` from the kept rows' weight column with a JS twin of `_dash_weighted_sizes` (the scheme's `max_wted_symsize` travels in the layer's config), flip `test/test_weighted_markers.py::TestAfterAMove::test_saved` from xfail(strict) to a plain test, and extend the help's weights sentence to "Both modes rescale the markers to the rows a filter keeps".
