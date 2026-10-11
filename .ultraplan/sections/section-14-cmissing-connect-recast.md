# Section 14: cmissing(n) on areas and estimators, connect() on rarea, recast() to range and pc types

> Part of: WP-31 · GAPS3 rows: C6, C7 · Risk: yellow · Batch: 5 · Depends on: 01 · Blocks: -- · Tasks: 3, 2 commits · Case-id prefix: U14

## Overview

**What is wrong today.** GAPS3 C6 (GAPS3.md:125): "`cmissing(n)` on area/rarea and on estimator-generated missing points (lowess, lpoly, lpolyci, fpfit, fpfitci, lfitci, qfitci, mband, mspline); `connect()` other than direct on rarea: named, not drawn." Evidence dash.ado:2712 (`local cm_named "area rarea fpfit fpfitci lfitci lowess lpoly lpolyci qfitci"`) and :2775-2776 (`if !("ptype" == "rarea" & _cn_nondirect) local _cn_rm "connect"` / `if !(_cn_no & ptype in cm_named) local _cn_rm "_cn_rm cmissing"`): `_dash_connect_opt` leaves `cmissing` on the pending list for those types when the value is `n`, and `connect` on rarea when the style is not direct, so the generic note names them and the renderer draws the bridged form. GAPS3 C7 (GAPS3.md:126): "`recast()` histogram to a range type or unknown name named; `recast()` on pci/pcarrowi named; twoway draws them." Evidence dash.ado:2577-2581 (`local _rc_lit "pci pcarrowi"` → `_dash_recast_named`) and :2616-2635 (an unknown name on histogram → named; a range target on a derived type → `_dash_recast_named`). The help lists both under "Not drawn" (dash.sthlp:5097-5106).

**After this section.**
- C6: `area`/`rarea` under `cmissing(n)` are split at each row missing in x or y (twoway closes a polygon at the last finite point and opens a new one after the gap); the outline already goes through `_dash_join_glyph`; the fill is drawn from the join's vertex list with two base-collapsed vertices per gap (D-14a). `connect(stairstep|stepstair|ascending|none)` on rarea builds both bounds' vertices with `_dash_join_vertices` (the renderer's existing function, :40956) and fills between them. The estimators' own missing points -- lowess/lpoly at an x with no neighbours, lpolyci's undefined band, fpfit/fpfitci at a non-positive x under a log power, lfitci/qfitci's missing band with df = 0, mband/mspline's empty band -- break the line under `cmissing(n)` and are bridged under the default, as twoway's serset draws them; each estimator mapper passes its computed source through `_dash_join_glyph` already (`_render_ci_band` :12515; map_lowess, map_lpoly, map_mband, map_mspline: verify in 14-02 and route the two that do not). So for the estimators the Python side is one check per mapper and the dash.ado change is the `cm_named` list; `_dash_connect_opt` takes `cmissing` off the pending list for all of them.
- C7: `histogram ..., recast(rarea|rbar|rspike|rcap|rcapsym|rscatter|rline|rconnected)` draws the bins as the range type over `(x = bin centre, y1 = 0, y2 = height)`, through a new `GlyphMapper._dash_draw_range_as` (shared with S11's `ciplot()`; whichever lands first defines it, the other reuses -- S11 is batch 4, so S14 reuses it: Boundaries); an unknown name on histogram prints twoway's two notes and draws rspike (y2xtype's fallback, dash.ado:2626), as `_dash_recast_opt` already does for the other y2x sources. `pci`/`pcarrowi ..., recast(pcspike|pcarrow|pcbarrow|pcscatter|pccapsym)` draw the literal's four coordinates as the target through `_dash_pc_dispatch`; an unknown name → the two notes and pcspike.

**Why one section.** Both rows are `_dash_connect_opt`/`_dash_recast_opt` edits with their renderer twins (`_dash_draw_xy_as`, `_dash_join_glyph`), owned by S14 in batch 5 (index owner table).

**Test order and commit rule.** Two rows, two commits: C6 first (14-01 tests → 14-02 fix/commit `(WP-31 C6)`), then C7's failing tests are written against the tree C6 leaves (14-03 tests + fix + commit `(WP-31 C7)`); 14-03 is one task because C7's dash.ado and renderer change are each under twenty lines, but it still writes its tests first and saves `<scratch>/14-C7-failure.txt` before editing code.

### Section decisions (binding on the executor)

- **D-14a. The area fill under cmissing(n) is a VArea over the join's vertices with base-collapsed gap vertices.** For a gap between finite rows j and k (every row between them missing in x or y), the fill's vertex list gets, after row j, a vertex `(x_j, y1 = base, y2 = base)` and, before row k, `(x_k, base, base)`; between them the polygon has zero height, so no fill shows, and the outline (drawn by `_dash_join_glyph` from the same rows under cmissing(n)) breaks at the gap. VArea has no stroke, so the zero-height strip is invisible. Measured against twoway's SVG in U14-01: the filled regions' x extents equal twoway's polygons' extents. `rarea` likewise with `y1`, `y2` the two bounds.
- **D-14b. The saved page's fill re-bridging after a filter move is fixed by S52 (batch 17), DECISIONS A23.** The saved page's `dash_join_rebuild` (`_FILTER_JS` :24665) rebuilds a LINE's vertices from `_dash_join`'s `{x, y, style, cmiss}`; it writes null in every other column at a synthetic vertex, so the fill's base column is null there and VArea skips the vertex -- the gap re-bridges after a move. S14 cannot edit `_FILTER_JS` (S16 owns it in batch 5, R12). The served app redraws through the mapper and is exact. S14 records `"kind": "area"` on `src._dash_join` (TR-14.3) so that S52's `dash_join_rebuild` reads `spec.kind === "area"` and writes the base at synthetic vertices; the saved page's re-bridging after a move is done by S52 (batch 17), DECISIONS A23. No residual BUGS.md entry is opened for it and C6's Tracked line reads Closed; S14's BUGS.md Resolution text names S52 for the saved-page move (M8 forbids a silent difference; the fix lands in the same work package).
- **D-14c. connect() on rarea.** Both bounds are expanded with `_dash_join_vertices(xs, ys_k, style, cmiss)` for k = 1, 2; the two vertex lists are aligned by construction (the same rows and the same insertions, since the x column is shared and the finite mask is `isfinite(x) & isfinite(y1) & isfinite(y2)` for both); the VArea is drawn over them. `map_rarea` draws no outline line today (:18421-18512: one `fig.varea` at :18492), so none is added.
- **D-14d. Histogram recast to a range type keeps the stale behaviour C16 describes** (GAPS3 C16 is S46's); S14 only routes the drawing. The recast histogram's source carries `x, y1, y2` and no `_dash_agg_config`, exactly as the yx recast does today (:17995-18003).
- **D-14e. pci/pcarrowi recast.** `_dash_recast_opt` canonicalises the name through `_sp_pc` with class yxyxtype (the existing loop :2606-2615) instead of `_dash_recast_named`; `s(_recast_target)` is written and `s(_recast_kind) literal`; the renderer's literal branch (`map_pci_literal` :19427, `map_pcarrowi` :20114) draws through `_dash_pc_dispatch(self)[target]` on a source of the literal's four columns when `options["recast"]` is set.

## Risk: [yellow] -- area geometry changes in both modes; two option programs; the saved move is S52's

**Why.** `map_area`/`map_rarea` gain a vertex-expansion path; `_dash_connect_opt` and `_dash_recast_opt` are the gatekeepers of four options; the pending list and help change for two rows.

**Risk factors.** 1. A VArea over expanded vertices changes the row count of the area's source: the hover tool and the brush read row ids (synthetic rows carry null ids as `_dash_join_glyph` does). 2. The saved move re-bridges until S52 lands (D-14b; batch 17, DECISIONS A23). 3. The parity tests for area/rarea (`test_mode_parity` CORPUS "area", "rarea") compare profiles: both modes expand identically, so no divergence. 4. Flipping `PLOT_VALUES["cmissing"]`/`["connect"]` moves the plot pending count down by two (written as the value measured at the section's base -> new, A33). 5. test_recast.py `TestTheHelp::test_recast_is_documented_and_named_only_where_not_drawn` (:279) reads the help's "Not drawn" sentence.

**Mitigation.** 1. Reuse `_dash_join_glyph`'s column rules (null row id and null carried columns at synthetic vertices; :41030-41060) by factoring its data-rebuild into a helper `_dash_join_rebuild_data(data, xcol, ycols, xi, yi, extra)` that both the line and the fill call (one editor: S14). 2. D-14b: S52 (batch 17) fixes the saved page's re-bridging after a move. 3. `TestBothModes` in the new test. 4. R10 comments. 5. The sentence is rewritten in 14-03 and the test's expectation updated in place (flip, with reason).

## Dependencies

- **Depends on: 01** (tracking). Reuses S11's `GlyphMapper._dash_draw_range_as` (batch 4) -- if absent at the batch-5 base, 14-03 defines it with S11's signature `(fig, source, xcol, locol, hicol, target, options, color_idx)`.
- **Blocks:** none. **Parallel batch 5** with S16 (`_FILTER_JS`) and S15 (`_apply_colorvar`, `_dash_fold_typed`). S14 edits `_dash_connect_opt`, `_dash_recast_opt`, `map_area`, `map_rarea`, `_dash_join_glyph`'s helper split, `map_histogram`'s recast branch and the literal pc mappers; S15 edits none of these (it routes colour through a call added at each mapper's end -- a one-line hunk per mapper that `patch -p1` merges; the merger lands S14 before S15 per the batch order).

## Evidence

Anchors at `6370ca4`.

### `_dash_connect_opt` (dash.ado:2703-2777)

```
2712    local cm_named "area rarea fpfit fpfitci lfitci lowess lpoly lpolyci qfitci"
...
2771    mata: st_local("_cn_p", st_global("s(_pending)"))
2772    local _cn_rm ""
2773    if !("`ptype'" == "rarea" & `_cn_nondirect') local _cn_rm "connect"
2774    if !(`_cn_no' & `: list ptype in cm_named') local _cn_rm "`_cn_rm' cmissing"
2775    local _cn_k : list _cn_p - _cn_rm
2776    sreturn local _pending `"`_cn_k'"'
```
`cm_refuse` (:2711) lists the types that refuse an unknown cmissing element with rc 101. The pending block names `cmissing` and `connect` on every type (:1327-1331) and this program removes them where drawn.

### `_dash_recast_opt` (dash.ado:2540-2640)

```
2577    if "`ptype'" == "dot" exit
2578    local _rc_lit "pci pcarrowi"
2579    if `: list ptype in _rc_lit' {
2580        _dash_recast_named `_rc_word'
2581        exit
2582    }
...
2616    if "`_rc_name'" == "" {
2617        if "`ptype'" == "histogram" {
2618            _dash_recast_named `_rc_word'
2619            exit
2620        }
2621        mata: _dash_note("named style ", st_local("_rc_v"), " not found in class `_rc_class', default attributes used")
2622        mata: _dash_note("`_rc_class' not found in scheme, default attributes used", "", "")
...
2628    if `: list ptype in _derived' {
2629        if "`_rc_name'" == "function" exit
2630        if !`: list _rc_name in _yx' {
2631            // histogram drawn as a range type (P2.44).
2632            _dash_recast_named `_rc_word'
2633            exit
2634        }
```
`_dash_recast_named word` (:2665-2671) appends the word to `s(_pending)`.

### The renderer

- `_dash_join_vertices(xs, ys, style, cmiss)` (dash_render.py:40956-41007) returns `(xi, yi)` row indices with -1 breaks; `_dash_join_glyph(mapper, fig, options, line_kwargs, role, hover)` (:41008-41100) rebuilds the source's data from them (x from `xi`, y from `yi`, other columns from the owning row or null) and records `src._dash_join = {x, y, style, cmiss}` for the saved page's rebuild (:24665 `dash_join_rebuild`, :24844 `_djoin`).
- `map_area` (:15166-15271) draws `fig.varea(x=xvar, y1=_y1_col, y2=yvar, source=area_source, ...)` over `_join_order`'s rows (:15186-15200) -- no `_dash_join_vertices`; `map_rarea` (:18421-18512) `fig.varea(x=xvar, y1=y1var, y2=y2var, source=source, ...)` (:18492) with `view`; neither reads `connect`/`cmissing`.
- `map_histogram` (:17911-18060) recast: `if options.get("recast"): return self._mark_silent(_tag(self._dash_draw_xy_as(...)))`-style branch at :17995-18003 for yx targets only (the spec never carries a range target today because dash.ado names it).
- `_dash_draw_xy_as` (:20693-20730) dispatches `_dash_glyph_dispatch(self)[0][target](fig, pts, "y", "x", opts, view=None, color_idx=color_idx, **kw)`; `_RECAST_DRAWN` (:20690) the eight yx names; `_dash_pc_dispatch` (:41938-41951) the five pc mappers `(fig, source, y1, x1, y2, x2, options, ...)` -- read `_dash_add_pc_glyph` (:42407) for the exact argument order before 14-03.
- `map_pci_literal` (:19427), `map_pcarrowi` (:20114): draw from `values` (`[[y1,x1,y2,x2],...]`); `options["recast"]` unread.

### twoway's rules

- cmissing/connect: `yxview_parse:755-803` FactorPlot `Connect CMISSings` for every type; `connect_truth.json` (WP-30 P1.8a, `scripts/extract_connect_truth.do`) holds the vertex rules; areas: twoway's area view closes each finite run to the base (measured in U14-01 from the SVG: one `<path>`/polygon per run).
- recast: `recast_truth.json` (`scripts/extract_recast_truth.do`) holds the y2xtype class names; `histogram` is y2xtype (`twoway_histogram_parse.class:16` via rbar), so `recast(rarea)` draws the bars' `(x, 0, height)` as an rarea; `pci` inherits yxyxview (`twoway_pci_parse.class`), so its class is yxyxtype.

### Fixtures on disk

`test/fixtures/connect_truth.json`, `recast_truth.json`. New: `area_cmissing_truth.json` (Stata truth).

### Pinned tests to flip (never delete)

- test/test_unsupported_report_is_true.py `PLOT_VALUES["cmissing"] = ("n","y","area")` (:95) and `["connect"] = ("direct","stairstep","rarea")` (:99) → move to `LIVE_VALUES` with `# Flipped (WP-31 C6): ... was wrong because twoway splits the area (area_cmissing_truth.json A01)`; `test_the_blocks_were_actually_found`'s plot pending count moves down by two, written as the value measured at the section's base -> new (`# <measured old> -> <new>: C6 cmissing() and connect() drawn everywhere`), recounted with the file's `_declared_*()` helpers (A33).
- test/test_connect_options.py `TestTheAdoTables::test_they_are_the_fixtures` (:691-710) pins `cm_named`'s list against the fixture -- flip to the new (empty) list with the reason; `TestTheHelp::test_documented` (:712) reads the help's cmissing sentence.
- test/test_recast.py `TestTheHelp::test_recast_is_documented_and_named_only_where_not_drawn` (:277-290) and `TestTheFixture::test_the_option_surface_record_holds_the_written_spec` (:265).
- test/test_twoway_option_parity.cscript RC-07 (:4128-4143): "dot ignores recast() silently; pci and histogram's range targets are named" → flip the pci/histogram half (dot stays S03's).
- test/test_help_claims_8.py `_CONTEXT`: no entry needed (cmissing/connect leave the pending list).

## User stories

- US-14.1 As a Stata user, I want `area mpg weight, cmissing(n)` to leave a gap where a value is missing, as twoway does.
- US-14.2 As a Stata user, I want `rarea lo hi x, connect(stairstep)` drawn as steps.
- US-14.3 As a Stata user, I want `lowess mpg weight, cmissing(n)` to break where the smoother has no value, not bridge it.
- US-14.4 As a Stata user, I want `histogram mpg, recast(rarea)` and `pci 1 2 3 4, recast(pcarrow)` drawn as twoway draws them.

## Business requirements

- BR-14.1 Under `cmissing(n)` an area, rarea or estimator layer breaks at every missing point in both modes' first picture and every served move; the saved page's re-bridging after a move is done by S52 (batch 17), DECISIONS A23.
- BR-14.2 `connect()` styles on rarea draw the vertices twoway draws for both bounds.
- BR-14.3 A histogram recast to a range type and a pci/pcarrowi recast to a pc type are drawn as the target; an unknown name prints twoway's two notes and draws the class default.
- BR-14.4 No note names a drawn option.

## Technical requirements

- TR-14.1 **dash.ado `_dash_connect_opt`**: replace :2712 by `local cm_named ""` with the comment `// WP-31 C6: cmissing(n) is drawn on every type (area/rarea split the fill; the estimators break their line at their own missing points)`; replace :2773-2774 by `local _cn_rm "connect cmissing"` (both always removed from the pending list; the refusals above are unchanged). The pending-block lines :1327-1331 (`cmissing`, `connect`) are deleted and their comment removed (plot parser only; the graph parser has no such lines).
- TR-14.2 **dash.ado `_dash_recast_opt`**: delete :2578-2582 (the `_rc_lit` block); add `else if `: list ptype in _rc_lit' local _rc_class yxyxtype` to the class ladder (:2588-2591) with `local _rc_lit "pci pcarrowi"` defined above it; after the name loop, for `_rc_lit` types write `sreturn local _recast_target "`_rc_name'"` and `sreturn local _recast_kind literal` and `exit` (an unknown name falls to :2621-2626's notes and pcspike). Delete :2617-2620 (the histogram unknown-name special case) so histogram takes y2xtype's fallback (rspike) with the two notes; delete :2630-2634 so a range target on histogram writes `_recast_target`/`derived` like a yx one; `_dash_recast_named` then has no caller: delete the program (:2665-2671) and its `program_coverage_map.py` entry (it is ado, not Mata, so no `_needed` list is involved). The `_derived` list (:2589) keeps `histogram`; the renderer decides by target class.
- TR-14.3 **Renderer, areas**: factor `_dash_join_glyph`'s data rebuild (:41030-41060) into module-level `_dash_join_rebuild_data(data, xcol, ycols, xi, yi, fill_cols=None)` where `ycols` is a tuple of y columns rebuilt from `yi` and `fill_cols` a dict `{col: value}` written at synthetic vertices (the base). `map_area`: `style, cmiss = _dash_join_spec(options)`; when `cmiss == "n"` or `style != "direct"`: `xi, yi = _dash_join_vertices(x, y, style, "n" if cmiss == "n" else "y")`; build the gap vertices of D-14a by scanning `xi` for -1 breaks: replace each -1 by the pair `(j, j)` and `(k, k)` with `y2` forced to the base -- implement as: after `_dash_join_vertices`, for each break at position p (xi[p] == -1), set `xi[p] = xi[p-1]`, mark `collapse[p] = True`, insert another vertex `xi = xi[p+1]` also collapsed; `_dash_join_rebuild_data(..., fill_cols={yvar: base_col_value, _y1_col: base})` writes `y2 = base` at collapsed vertices. Record `area_source._dash_join = {"x": xvar, "y": yvar, "style": style, "cmiss": cmiss, "kind": "area"}` (the extra key is ignored by today's JS and read by S52's). `map_rarea`: the same with `ycols = (y1var, y2var)`; twoway closes an rarea polygon on its own two bounds, so both bounds are collapsed to `y1_j` at j and `y1_k` at k and the strip has zero height. Views: the view-masked source path (`view is not None`) must take the rows first (`_view_mask`, `_subset_source`, as map_scatter does :14906-14914) before expanding.
- TR-14.4 **Renderer, estimators**: in 14-02 grep each of `map_lowess` (:16655), `map_lpoly` (:17107), `map_mband` (:20494), `map_mspline` (:20341) for `_dash_join_glyph`; any that calls `fig.line(` directly is routed through `_dash_join_glyph(self, fig, options, kwargs, role="line")` with the same kwargs; the ci mappers already go through `_render_ci_band`. Nothing else: the estimators' missing points are already NaN rows in their sources.
- TR-14.5 **Renderer, recast**: `map_histogram` recast branch (:17995-18003): `if target in _DASH_RANGE_TYPES: return self._dash_draw_range_as(fig, hist_source, "centre", "zero", "top", target, options, color_idx)` where `centre = (left+right)/2`, `zero` a zeros column (the histogram's base is 0 in twoway's serset); else the yx path as today. `map_pci_literal`/`map_pcarrowi`: when `options.get("recast")` in `_dash_pc_dispatch(self)`: build `ColumnDataSource({"y1":..,"x1":..,"y2":..,"x2":..})` from `values` and call the target mapper with the argument order `_dash_add_pc_glyph` uses; `opts` without `recast`/`type`.
- TR-14.6 **Tests/pins**: LIVE_VALUES `"cmissing": ({"cmissing":"n"},{"cmissing":"y"},"area",{})`, `"connect": ({"connect":"stairstep"},{"connect":"direct"},"rarea",{})` with the Flipped comments; the plot pending count written per A33 (`# <measured old> -> <new>: C6 ...`). `function_test_map.py`: `'_dash_join_rebuild_data': 'test/test_area_cmissing.py::TestAreaSplit::test_fill_collapses_at_the_gap[saved]'`. Copy list: `_dash_join_rebuild_data` after `_dash_reference_lines` (:47223) (R2).

## Boundaries

- No `_FILTER_JS`/`js_runner.py`/`_dash_stale_kind` edit (S16). No `_apply_colorvar`/`_dash_fold_typed` edit (S15). No `map_dot` recast (S03: "dot ignores recast() silently" stays, dash.ado:2577).
- `cm_refuse` and the rc-101 refusal of an unknown cmissing element (dash.ado:2749-2756) unchanged.
- A recast histogram's stale marking (GAPS3 C16) is S46's.

## Stata truth

New `scripts/extract_area_cmissing_truth.do` → `test/fixtures/area_cmissing_truth.json`; `sysuse auto`, `replace mpg = . in 10/12`:
- `A01` `twoway area mpg weight in 1/20, cmissing(n) sort` → `graph export` SVG; the filled polygons' x extents (count and [xmin, xmax] per polygon) read with `svg_truth.svg_document` (test/cert_svg.do's reader); `A02` the same with `cmissing(y)` (one polygon).
- `R01` `twoway rarea lo hi weight in 1/20, connect(stairstep) sort` serset and the polygon vertex count; `R02` `rarea ..., cmissing(n)` polygon count.
- `E01` `twoway lowess mpg weight, cmissing(n)` -- the serset's missing rows (count) and the SVG path count (one path per run); `E02` `lpolyci mpg weight, cmissing(n)`.
- `H01` `twoway histogram mpg, recast(rarea) name(h1)`: `.h1.plotregion1.plot1.viewtype`/`.plot1.style.type` and the serset (x, low, high); `H02` `recast(bogus)`: the two notes and the drawn type (`rspike`); `P01` `twoway pci 20 2000 30 4000, recast(pcarrow)`: `.plot1.viewtype`; `P02` `pcarrowi 20 2000 30 4000, recast(pcscatter)`.
`_meta`, `git add -f`, test_fixtures_are_committed.py entry.

## TDD test stubs

New `test/test_area_cmissing.py` (C6) and `test/test_recast_range_pc.py` (C7):
- Test: `area ..., cmissing(n)` with a missing y in the middle: the VArea's source has two collapsed vertices where y2 == y1 == base at the gap's edges, and the outline Line breaks (NaN) there, both modes -- `TestAreaSplit::test_fill_collapses_at_the_gap[mode]` (red); the filled x extents equal A01's polygons -- `::test_matches_twoway_extents` (red); `cmissing(y)` unchanged (one run) -- `::test_default_bridges` (guard).
- Test: rarea `connect(stairstep)` vertices equal `_dash_join_vertices` on both bounds, both modes -- `TestRareaConnect::test_stairs[mode]` (red); `cmissing(n)` on rarea splits -- `::test_split[mode]` (red).
- Test: lowess/lpoly/mband/mspline with a missing point under cmissing(n) have a NaN vertex in their line source (not dropped) -- `TestEstimatorsBreak::test_each[type]` (red for any mapper routed in TR-14.4; guard otherwise).
- Test: the served app draws the split after a move -- `TestAfterAMove::test_served_split` (red); the saved page's re-bridging after a move is done by S52 (batch 17), DECISIONS A23, and S52 writes the saved-move test there (none here).
- Test: `_dash_join_rebuild_data` writes null row ids and the base at synthetic vertices -- `TestTheHelper::test_rows` (red); copy list -- `TestTheServedCopy::test_name` (red).
- Test: dash.ado's `cm_named` is empty and `_dash_connect_opt` removes both names on every type (read the ado text) -- `TestTheAdoText::test_lists` (red); the pending blocks no longer name cmissing/connect -- `::test_not_pending` (red).
- C7: `histogram mpg, recast(rarea)` draws a VArea over bin centres with y1 = 0, y2 = height, both modes -- `TestHistogramRangeRecast::test_rarea[mode]` (red); each range target -- `::test_each_target[target]` (red); `recast(bogus)` → two notes and rspike -- `TestUnknownName::test_histogram_notes_and_rspike` (red); `pci ..., recast(pcarrow)` → an Arrow/segment renderer of the pcarrow mapper -- `TestPciRecast::test_pcarrow[mode]` (red); `pcarrowi ..., recast(pcscatter)` -- `::test_pcarrowi[mode]` (red); dash.ado writes `_recast_kind literal` -- `TestTheAdoText::test_literal_kind` (red).

cscript, block `* ==== S14 C6: cmissing and connect on areas ====` and `* ==== S14 C7: recast to range and pc types ====` (one block per row, A14: the C6 block is appended by 14-02, the C7 block by 14-03, C7's closing task -- never by 14-01):
- U14-01 `area mpg weight in 1/20, cmissing(n) sort`: dash's filled x extents (python read of the render) equal twoway's SVG polygon extents (`_bg_svg_caps`-style reader on `graph export`); the note names neither `cmissing` nor `connect` (`cert_log_has` 0).
- U14-02 `rarea lo hi weight, connect(stairstep)`: vertex count equals twoway's serset-derived count; `connect(J)` rc 0 both.
- U14-03 `lowess mpg weight, cmissing(n)` (with `mpg` missing in 10/12): no note; dash's line source holds NaN rows.
- U14-04 `histogram mpg, recast(rarea)`: dash's render is a VArea; `recast(bogus)`: dash prints the two notes twoway prints (`cert_log_has` each) and draws rspike; rc 0 both.
- U14-05 `pci 20 2000 30 4000, recast(pcarrow)` and `pcarrowi ..., recast(pcscatter)`: dash's spec carries `"recast":"pcarrow"`; the render draws the target; twoway `.plot1.viewtype` equals the target.
Flip in test_twoway_option_parity.cscript RC-07 (:4128-4143): pci/histogram range targets are no longer named (keep the dot half; new expected text).

Parity (R8): CORPUS `_case("area cmissing(n)", ...)`, `_case("rarea connect(stairstep) cmissing(n)", ...)`, `_case("histogram recast(rarea)", ...)`, `_case("pci recast(pcarrow)", ...)`; MOVE_CORPUS `_case("rarea cmissing(n) after a move", ...)`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| area/rarea split | pytest TestAreaSplit/TestRareaConnect; U14-01/02 | area_cmissing_truth A01 A02 R01 R02 | yes (saved move: S52, batch 17) |
| estimators break | pytest TestEstimatorsBreak; U14-03 | E01 E02 | yes |
| histogram range recast | pytest TestHistogramRangeRecast; U14-04 | H01 H02 | yes |
| pci/pcarrowi recast | pytest TestPciRecast; U14-05 | P01 P02 | yes |
| ado lists, help, counts | pytest TestTheAdoText, test_connect_options, test_recast, test_unsupported | -- | -- |

AC-14.1 stubs green; AC-14.2 U14-01..05 PASS, RC-07 flipped and PASS; AC-14.3 dash.sthlp:5097-5106 "Not drawn" entry loses cmissing/connect/recast sentences (only `play()` remains) and the plot-types "Connecting and missing values" paragraph says every type breaks; AC-14.4 TWOWAY_COVERAGE_AUDIT.md rows 27, 62, 63, 64, 72, 78, 85, 86, 114, 145, 146, 169 annotated for C6/C7.

## Tasks

**Commit boundary.** 14-01 (tests, no commit) + 14-02 (fix, commit `Split area, rarea and estimator layers at missing points under cmissing(n) and draw connect() on rarea (WP-31 C6)`); 14-03 (tests, fix, commit `Draw recast() of histogram to a range type and of pci/pcarrowi to a pc type (WP-31 C7)`).

<task type="auto" id="14-01">
  <name>Write the failing C6 tests and the area truth extractor</name>
  <files>test/test_area_cmissing.py, scripts/extract_area_cmissing_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_area_cmissing_truth.do on scripts/extract_default_base_truth.do's skeleton measuring A01, A02, R01, R02, E01, E02, H01, H02, P01, P02 of "Stata truth" (SVG polygons read with test/cert_svg.do's `svg_truth.svg_document`, as test/test_wp30_truth.cscript:3045-3080 `_bg_svg_caps` reads vlines; class values with `local v = `.h1.plotregion1.plot1.viewtype''); run it with `DASH_REPO=<repo> scripts/stata_slot.sh <scratch> <repo>/scripts/extract_area_cmissing_truth.do`; `git add -f test/fixtures/area_cmissing_truth.json`; register it in test_fixtures_are_committed.py. Create test/test_area_cmissing.py with the C6 stubs (TestAreaSplit, TestRareaConnect, TestEstimatorsBreak, TestAfterAMove (served only: the saved-page move is S52's, A23), TestTheHelper, TestTheServedCopy, TestTheAdoText). Run `python3 -m pytest test/test_area_cmissing.py -q -p no:randomly > <scratch>/14-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/14-01-failure.txt prints >= 8; python3 -c "import json;print(sorted(json.load(open('test/fixtures/area_cmissing_truth.json'))))" lists A01 A02 E01 E02 H01 H02 P01 P02 R01 R02 _meta.]]></verify>
  <done>The C6 regression tests fail against 6370ca4 and twoway's area, rarea, estimator and recast truth is committed.</done>
</task>

<task type="auto" id="14-02">
  <name>Split areas and estimators at missing points and commit C6</name>
  <files>dash.ado, dash_render.py, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[dash.ado: TR-14.1 (`cm_named` emptied with the comment; `_cn_rm "connect cmissing"`; delete the pending lines :1327-1331 and their comment). dash_render.py: TR-14.3 (factor `_dash_join_rebuild_data` out of `_dash_join_glyph` :41030-41060, add it to the functions copy tuple after "_dash_reference_lines" :47223; `map_area` :15186-15230 and `map_rarea` :18421-18492 vertex expansion with the base-collapsed gap vertices; `_dash_join` records gain `"kind": "area"`), TR-14.4 (route any estimator mapper still calling `fig.line(` directly through `_dash_join_glyph`). test_unsupported_report_is_true.py: TR-14.6 (move cmissing/connect to LIVE_VALUES with Flipped comments; the plot pending count recounted with the file's `_declared_*()` helpers at the section's base and written `# <measured old> -> <new>: C6 cmissing() and connect() drawn everywhere`, A33). Flip test/test_connect_options.py `TestTheAdoTables::test_they_are_the_fixtures` (:691-710) to the emptied `cm_named` with the docstring reason, and `TestTheHelp::test_documented` (:712) to the new help sentence (written in this task: rewrite dash.sthlp's "Not drawn" entry at :5097-5106 to keep only the `play()` and the recast sentences -- the recast sentence goes in 14-03 -- and the plot-types "Connecting and missing values" paragraph (grep `{ul:Connecting and missing values` dash.sthlp) to say cmissing(n) breaks area, rarea and every estimator at their missing points). Add function_test_map.py's entry. Append `* ==== S14 C6: cmissing and connect on areas ====` (U14-01..03) to test/test_wp31_truth.cscript above the marker (the C6 block only; C7's is 14-03's, A14); run `WP31_ONLY=S14 scripts/stata_slot.sh <scratch> <scratch>/run_wp31.do`. TWOWAY_COVERAGE_AUDIT.md rows 27, 62, 63, 64, 72, 78, 85, 86, 114, 145, 169: append `[WP-31 C6, commit pending: corrected -- cmissing(n) drawn on every type; connect() drawn on rarea]`. BUGS.md: close C6's entry (Resolution form; its text includes the sentence "the saved page's re-bridging after a move is done by S52 (batch 17), DECISIONS A23"; no residual entry is opened). GAPS3 §9 C6 line: `- **C6 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b rewrites `pending` to the landed sha). Replace the `<!-- WP-31 C6 -->` markers (Results: "area mpg weight, cmissing(n): the fill breaks at a missing row (was: bridged, named)"). Run `python3 -m pytest test/test_area_cmissing.py test/test_connect_options.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_tracking_documents.py test/test_mode_parity.py -k "area or rarea" -q`; commit with the BRIEF body (failure text from <scratch>/14-01-failure.txt, Regression/Flipped/Fixture/BUGS.md/GAPS3 lines); grep the message for `claude|anthropic`.]]></action>
  <verify><![CDATA[pytest prints 0 failed; the Stata log shows "U14-01 PASS" "U14-02 PASS" "U14-03 PASS"; `grep -c 'local cm_named ""' dash.ado` prints 1; `grep -c 'C6 Tracked:\*\* Closed in WP-31' GAPS3.md` prints 1; `grep -c "S14 C7:" test/test_wp31_truth.cscript` prints 0; `git log -1 --format=%s` ends "(WP-31 C6)".]]></verify>
  <done>C6 is committed: areas, rareas and estimators split at missing points under cmissing(n), rarea draws connect() styles, nothing is named; the saved page's re-bridging after a move is S52's (batch 17, A23).</done>
</task>

<task type="auto" id="14-03">
  <name>Draw recast() to range and pc targets and commit C7</name>
  <files>test/test_recast_range_pc.py, dash.ado, dash_render.py</files>
  <action><![CDATA[Create test/test_recast_range_pc.py with the C7 stubs (TestHistogramRangeRecast, TestUnknownName, TestPciRecast, TestTheAdoText::test_literal_kind); run `python3 -m pytest test/test_recast_range_pc.py -q -p no:randomly > <scratch>/14-C7-failure.txt; true` against the C6 tree. Then dash.ado TR-14.2 (`_dash_recast_opt` :2577-2634: the literal class, the histogram fallback and range targets; delete `_dash_recast_named` :2665-2671 and its program_coverage_map.py entry) and dash_render.py TR-14.5 (`map_histogram` :17995-18003 range branch through `_dash_draw_range_as` -- define the method after `_dash_draw_xy_as` :20730 if S11's is absent; `map_pci_literal` :19427 and `map_pcarrowi` :20114 recast branches through `_dash_pc_dispatch`). Flip test/test_recast.py `TestTheHelp` (:277-290) and `TestTheFixture::test_the_option_surface_record_holds_the_written_spec` (:265) in place with docstring reasons; flip test_twoway_option_parity.cscript RC-07 (:4128-4143) so pci and histogram's range targets are expected drawn (dot still silent). Rewrite dash.sthlp's recast sentence in the "Not drawn" entry (:5101-5104) -- delete it -- and the `{phang}{ul:Recast.}` paragraph (grep `{ul:Recast.}`) to say histogram takes y2xtype's names (rarea rbar rspike rcap rcapsym rscatter rline rconnected) and pci/pcarrowi yxyxtype's. Append `* ==== S14 C7: recast to range and pc types ====` (U14-04, U14-05) above the marker (C7's block is appended here, by C7's closing task, A14); run `WP31_ONLY=S14` and test_twoway_option_parity.cscript through the slot wrapper. TWOWAY_COVERAGE_AUDIT.md row 146 and row 98: `[WP-31 C7, commit pending: corrected -- recast() to range and pc types drawn]`. Close C7's BUGS.md entry, write the GAPS3 C7 line `- **C7 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.`, replace the `<!-- WP-31 C7 -->` markers (Results: "histogram mpg, recast(rarea): drawn as an rarea (was: named, bars drawn)"). Run `python3 -m pytest test/test_recast_range_pc.py test/test_recast.py test/test_help_conformance.py test/test_program_coverage_map.py test/test_tracking_documents.py test/test_mode_parity.py -k recast -q`; commit; grep the message.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/14-C7-failure.txt prints >= 5; pytest prints 0 failed; the Stata logs show "U14-04 PASS" "U14-05 PASS" and "RC-07 PASS"; `grep -c "program define _dash_recast_named" dash.ado` prints 0; `grep -c 'C7 Tracked:\*\* Closed in WP-31' GAPS3.md` prints 1; `git log -1 --format=%s` ends "(WP-31 C7)".]]></verify>
  <done>C7 is committed: a histogram recast to a range type and a pci/pcarrowi recast to a pc type are drawn as twoway draws them, an unknown name takes the class default with twoway's notes.</done>
</task>

## Section completion criteria

- Two commits, each with red-then-green tests, flips with reasons, fixture, help, audit, BUGS.md, GAPS3 line and CHANGELOG lines.
- `_dash_join_rebuild_data` on the copy list; `_dash_recast_named` gone from dash.ado and program_coverage_map.py; `cm_named` empty; pending blocks name neither cmissing nor connect.
- No residual BUGS.md entry for D-14b: the saved page's re-bridging after a move is done by S52 (batch 17), DECISIONS A23; the C6 and C7 Tracked lines both read `Closed in WP-31, ..., commit pending` until the merger's step k.3b fills the sha.

## Notes

- **Renderer order:** in `map_area` the fill is added first, then the outline through `_dash_join_glyph`, as today; the fill's synthetic vertices carry null row ids so the brush and the KPIs ignore them (`_dash_join_glyph`'s rule).
- **Copy list (R2):** `_dash_join_rebuild_data` after `_dash_reference_lines` (:47223); `_dash_draw_range_as` is a method.
- **S11 overlap:** if S11 defined `_dash_draw_range_as` in batch 4, reuse it unchanged; a second definition would shadow the first and fail `test_function_test_map.py`.
- **RC-07 flip:** keep the dot half of the case verbatim; only the pci/histogram assertions change, with the WP-31 C7 reason in the display text.
- **Fixture rule (R7)** and the python_exec hazard as in every section.
- **Security:** no new text path; `recast` names are canonicalised by dash.ado's spelling table and checked by membership (`_RECAST_DRAWN`, `_DASH_RANGE_TYPES`, `_dash_pc_dispatch` keys) before dispatch; `getattr` on user text never occurs.
- **Merge rules cited:** R1, R2, R8, R9, R10, R12 (S14 is batch 5's `_dash_connect_opt`/`_dash_recast_opt` editor; S16 owns `_FILTER_JS`; S15 the appliers).
- **Commit body lines:** `Regression: test/test_area_cmissing.py::TestAreaSplit::test_fill_collapses_at_the_gap[saved] -- failed at 6370ca4 with <text>`; `Flipped: test/test_unsupported_report_is_true.py PLOT_VALUES cmissing -- "named and inert on area" was wrong because twoway splits the area (area_cmissing_truth.json A01)`; `Fixture: test/fixtures/area_cmissing_truth.json (scripts/extract_area_cmissing_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS3: C6 Tracked` / `GAPS3: C7 Tracked`.
- **Decisions for maintainer ratification:** D-14a (base-collapsed gap vertices instead of a Patches glyph). D-14b is settled by DECISIONS A23 (the saved page's re-bridging after a move is done by S52, batch 17) and is not up for ratification.
