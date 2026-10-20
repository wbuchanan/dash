# Section 18: Dot rows (twoway dot geometry, dotextend(), ndots(), the d-options)

> Part of: WP-31 · GAPS3 rows: B5b (rows and d-options; S03 owns B5a: base()/recast()) · Risk: yellow · Batch: 6 · Depends on: 03 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U18

## Overview

**What is wrong today.** GAPS3 B5 (GAPS3.md:114; S01 splits it into `B5a`, S03's, and `B5b`, this section's -- A21): "`dot` is drawn as a plain scatter: no dot rows; `dotextend()`, `ndots()`, `dsymbol dcolor dfcolor dsize dlcolor dlwidth dlalign` undeclared (generic note), `dstyle()`/`dlstyle()` pending; `base()` on dot written to the spec and never read; `recast()` on dot dropped with no note." Evidence dash_render.py:18910-18937 `map_dot` -- `return self.map_scatter(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)` under a docstring that admits "approximates the visual output"; dash.ado:1346-1348 names `dstyle`/`dlstyle` as pending; `DOTEXtend NDOTs DSTYle Dsymbol DColor DFColor DSIZe DLSTYle DLColor DLWidth DLAlign` are not declared (the last seven fall to the catch-all). dash.sthlp:236-260 lists `dot` among the types drawn "as twoway describes" (GAPS3 J2 flags the sentence) and :5040-5046 names dstyle/dlstyle as kept and not drawn. test/test_glyphs.py `TestMapDot` (:277-304) pins dot = scatter (GAPS3 K1).

**After this section** `map_dot` draws twoway's picture (research/stata-ground-truth.md §5; `B/y/yxview_dot_draw.ado`):
- A row of dots per observation along the x axis (or the y axis under `horizontal`), 75 dots by default (`num_dots = 75`, `yxview.class:73`), spaced `delta = (max - min)/(ndots - 1)` over the axis scale's current `[min, max]` (`yxview_dot_draw.ado:25`), starting at the **base** -- 0 when the scale spans 0, else the scale end nearer 0 (`:10-23`) -- and running to BOTH scale ends under `dotextend(yes)` (the default, `:72-91`) or to the observation's value under `dotextend(no)` (`:54-69`); a dot at every `base + k*delta` toward the end, capped at 10,000 steps (`:94-115`).
- The dots are tiny circles in the `dots` marker style: `symbol dots circle`, `symbolsize dots vtiny` (0.1 relative units = 0.384 px at dash's reference; drawn at a 1 px floor so they show), `color dots black`, outline `linewidth dotmark thin`, `color dotmarkline black` (`scheme-s2color.scheme:255, 406, 399, 512, 1224`); the observation's marker is drawn afterwards in `markerstyle p#dot` (symbol p#dot → p circle, size p#dot → p medium).
- `ndots(#)`, `dotextend(yes|no)`, and the d-options `dstyle(markerstyle) dsymbol(symbol) dcolor(color) dfcolor(color) dsize(size) dlstyle(linestyle) dlcolor(color) dlwidth(width) dlalign(align)` style the dots as the m-options style markers (`twoway_dot.sthlp:34-56`; minimums per `cmdab`: `dotex`, `ndot`, `dsty`, `d`, `dc`, `dfc`, `dsiz`, `dlsty`, `dlc`, `dlw`, `dla`). The dot rows take `colorvar()`'s colour when S15's call colours the marker (D-18d). `base()` is read as S03 left it (S03 reads `base()` on dot into the spec and the axis range; S18 reads the base from the axis exactly as twoway does, so `base()` matters only through the range it widens -- `yxview.class:1583-1587`, the help's "default base(0)" is effective only through the scale).

**Why this section and what stays S03's.** S03 (batch 1) owns `base()`'s axis effect on dot and the `recast()` note as row `B5a`; S18 owns the geometry and the d-options as row `B5b` (manifest: "dot-rows: B5b"). A4 gives a split row one BUGS.md entry and one GAPS3 Tracked line per part: S03 writes `B5a`'s line, S18 writes only `B5b`'s (`- **B5b Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.`).

**Test order and commit rule.** One row, one commit `(WP-31 B5b)`: 18-01 tests + extractor; 18-02 dash.ado; 18-03 renderer; 18-04 certify/document/commit.

### Section decisions (binding on the executor)

- **D-18a. The dots follow the axis after a move.** The rows depend on the axis scale's `[min, max]`; `_dash_finish_auto_bases` (dash_render.py:32115) already refills the base column of bar/spike/dropline/area from the finished axis in both modes, and `_dash_refinish_axes` (:32271) re-finishes the axis after a served move. The dot rows are therefore NOT a fixed column of points: `map_dot` draws them as a Bokeh **`Scatter` over a source dash fills from the axis range** -- `_dash_finish_auto_bases` is extended (S18 is its editor in batch 6; no other batch-6 section touches it) to rebuild each `dash_dots:` tagged source's `x`/`y` columns from the figure's finished range (`fig.y_range.start/end` or `x_range` under horizontal) with the rule above. On the saved page the dots are frozen at the build's range (the JS cannot rebuild them in S18: S19 owns `_FILTER_JS`); because twoway's dots are a background texture over the fixed scale, a saved move that keeps the scale draws them right, and a move that changes the scale (axis rescale is not done on the saved page for fixed ranges) leaves them right too. Whether the saved figure's range follows the kept rows (a DataRange1d, under which the dots would stop short of a widened range) is measured by 18-01's `TestAfterASavedMove`; if red, S18 files a residual for S19/S22's JS slot (M12) rather than editing `_FILTER_JS`.
- **D-18b. One dots renderer per layer.** All rows' dots go in one `ColumnDataSource({"x": [...], "y": [...], "__dash_row": [obs index]})` and one `fig.scatter(marker="circle", size=<dsize px>, fill_color=<dcolor>, line_color=<dlcolor>, line_width=<dlwidth px>)` renderer tagged `dash_dots`, drawn BEFORE the marker renderer (twoway draws dots, then `_draw_points`); it carries no hover tool and no legend entry (twoway keys the marker only), and is excluded from the brush (its row ids are null; `_dash_join_glyph`'s convention).
- **D-18c. Size floor.** `symbolsize vtiny` is 0.1 relative = 0.384 px; Bokeh draws nothing visible under 1 px, so the dots take `max(px, 1.0)`; `dsize()` is read through `self.tr.translate_msize(value, default_px, ref)` exactly as `msize()` is (:13268-13292) with the same floor.
- **D-18d. Colour chain.** Default dot fill/outline are the scheme's `color dots`/`color dotmarkline` (black in s2color; read through `SchemeParser` by adding the two stubs to the colour chain the parser reads -- `SchemeParser` is copied whole, no copy-list entry); `dstyle(p#)`/`dstyle(name)` resolves through the same markerstyle chain `mstyle()` uses (`_style_value(options, "marker", ...)` pattern) with `dots` as the base style; `dcolor()`/`dfcolor()`/`dlcolor()` through `parse_color_alpha`; `dsymbol()` through `OptionTranslator.symbol_traits`; `dlwidth()` through `translate_lwidth`; `dlalign()` is accepted and named once (Bokeh has no stroke alignment; `mlalign()` is treated the same elsewhere -- S08 batch 3 decides mlalign; S18 copies S08's rule for dlalign). Under `colorvar()`, the dots of each observation take the observation's mapped colour (`colorvar_options.sthlp:178` "the color for dots, bars, and markers"): the dots source carries the colour column repeated per dot and S15's `_apply_colorvar(..., add_key=False)` is called on the dots renderer.
- **D-18e. `horizontal`.** `dot` is in `_DASH_HORIZONTAL_TYPES` (:31835); under `horizontal` the rows run along the y axis at the observation's x (`yxview_dot_draw.ado:7-17` `dropx`), i.e. swap the roles exactly as the existing horizontal transpose does for the marker.

## Risk: [yellow] -- a new background renderer per dot layer that follows the axis, in both modes

**Why.** 75 × N points per layer (74 obs → 5,550 dots on auto) rebuilt on every axis finish; a new tag, a new finisher branch, nine new options.

**Risk factors.** 1. Performance: 100,000 rows × 75 dots = 7.5 M points (M10's 2 s bound); twoway caps steps at 10,000 per row, not per layer. 2. The saved page's range behaviour (D-18a). 3. test_glyphs TestMapDot flips; test_mode_parity "dot" profiles change; `test_server_layer_defects.plot_for` builds dot specs. 4. The brush/KPI must ignore the dots (null row ids). 5. `ndots(1)` → delta division by zero (`ndots - 1 = 0`): twoway's behaviour measured (U18-02).

**Mitigation.** 1. `_DASH_DOTS_MAX = 2_000_000` module constant (copy list, constants tuple after `_DASH_STALE_STATUS_HTML`): above it the rows are drawn at `ndots` reduced so the total fits, with one note naming the reduction (M12-style note, not silence); test_estimator_cost.py gains `test_dot_rows_under_two_seconds` at 100,000 rows. 2. Measured in 18-01; residual if red. 3. Flips with reasons; corpus entries. 4. `__dash_row` null ids; `TestBrushIgnoresDots`. 5. Fixture decides (`ndots(1)` probably r(198) `option ndots() ...` or draws one dot).

## Dependencies

- **Depends on: 03** (S03's `base()` on dot and the `recast()` note; S18 reads the finished axis, never `base()` directly). **Blocks:** none.
- **Parallel batch 6** with S19 (`_FILTER_JS`) and S17 (`_apply_colorvar` body, `_make_figure_body` color_idx line). S18 edits `map_dot`, `_dash_finish_auto_bases`, `SchemeParser`'s dots stubs, dash.ado's declarations and the pending block lines :1346-1347: dstyle/dlstyle leave the pending block entirely (they are drawn on dot; on other types twoway accepts them and draws nothing different -- silent, D-12a's rule), so the two lines are deleted.

## Evidence

Anchors at `6370ca4`.

### Today's mapper

dash_render.py:18910-18937: docstring "renders a standard scatter ... approximates", body `return self.map_scatter(...)`. `map_dropline` (:18943-19090) shows the pattern S18 follows for a two-renderer layer with its own source (`_dl_cols`, `_view_mask`, `_tag_base`).

### The finishers

`_dash_finish_auto_bases(fig)` (:32115-32200) walks `fig.renderers` for `dash_base:` tags and fills the base column from the finished axis. Its callers are :33407 (in `_dash_finish_count_ticks(fig, refinish=False, skip=())`, :33346) and :33500 (in `_dash_common_count_ticks(figs, letters)`, :33410); `_dash_refinish_axes` (:32271-32301, the served post-move re-finish) does NOT call it (R2-33). TR-18.3 names :33500 as the served re-finish hook to check first. The dots finisher is a second loop in the same function keyed on the `dash_dots:` tag (JSON: `{"letter": "y"|"x", "ndots": 75, "extend": true, "n": N}`), reading the observation values from the layer's marker source (stored on the dots source as `src._dash_dots_values`), the finished range from `fig.y_range`/`fig.x_range` (`start`/`end`, the smaller is `min`), computing base, delta and the dot positions, and writing `x`/`y`.

### The scheme

`scheme-s2color.scheme`: `:255 symbolsize dots vtiny`, `:406 color dots black`, `:399 color dotmarkline black`, `:512 symbol dots circle`, `:1224 linewidth dotmark thin`, `:580 linepattern dotmark solid`; `style/symbolsize-vtiny.style` `set val .1 relative`; `style/markerstyle-dots.style`, `style/linestyle-dots.style`, `style/linestyle-p#dotmark.style`, `style/seriesstyle-p#dot.style:9 set dots scheme dots`, `style/markerstyle-p#dot.style` (symbol p#dot → p, size p#dot → p medium 1.52778). `dash-s2color.scheme` lacks the `dots`/`dotmark`/`dotmarkline` stubs (research §11): 18-03 adds the five lines to `dash-s2color.scheme` and every shipped scheme file (the regeneration script, if any -- grep scripts/ for the scheme writer; else by hand with the measured values) and `SchemeParser` reads `color dots`, `color dotmarkline`, `symbolsize dots`, `linewidth dotmark`, `symbol dots` through its existing stub readers.

### twoway's geometry (`yxview_dot_draw.ado`, read 10oct2026)

```
 7  local dropx = "`.bar_drop_to.stylename'" == "x"
 9-17  min/max = plotregion yscale.curmin/curmax (dropx) else xscale
18-23  base = 0 if min <= 0 & max >= 0 else cond(max < 0, max, min)
25  local delta = (`max' - `min') / (`.num_dots'-1)
31-36  dots_extend.istrue ? draw_full_dots : draw_value_dots
38-50  ._draw_points (markers), x/y swapped when !dropx
54-69  draw_value_dots: per obs, draw_dots pos base value
72-91  draw_full_dots: per obs, draw_dots pos base min, and pos base max
94-115 draw_dots: if abs(end-base)/delta > 10000 exit; delta sign toward end; forvalues v = base(delta)end { gdi point }
```
Note `dropx` means the y scale is used (the dots run along y). Which axis the rows run along for the default `twoway dot mpg weight` is measured in U18-01 (expected: along x, horizontal rows of dots at each y -- `twoway_dot.sthlp` describes "dots ... along the x axis"); the fixture settles it and the mapper follows the fixture.

### Fixtures on disk

`default_base_truth.json` (the base rule per type incl. the axis scale values); `horizontal_truth.json`. New: `dot_truth.json`.

### Pinned tests to flip (never delete)

- test/test_glyphs.py `TestMapDot::test_dot_returns_renderer` (:282: `isinstance(r, GlyphRenderer)` -- map_dot now returns a list `[dots_r, marker_r]`; flip to the list form), `::test_dot_produces_scatter_glyph` (:288, the marker renderer is `r[1]`), `::test_dot_mcolor_applied` (:293, on `r[1]`), `::test_dot_msize_applied` (:298). Docstrings: `Flipped (WP-31 B5b): map_dot draws twoway's dot rows before the marker (dot_truth.json D01).`
- test/test_server_layer_defects.py `plot_for` (:80) and test_mode_parity CORPUS "dot" entry: the profile changes (two renderers); no flip, because the parity test compares saved vs served, not a stored profile.
- test/test_unsupported_report_is_true.py: `PLOT_VALUES["dstyle"]` (:116 `("p3","p5","scatter")`), `["dlstyle"]` → `LIVE_VALUES` on `dot`. Under s2color every p#dot marker style is `dots` (black), so a pair of `dstyle()` values differs only under a scheme whose p#dot styles differ. Rule: `({"dstyle":"p3"}, {"dstyle":"p7"}, "dot", {"scheme":"<a shipped scheme whose p3dot and p7dot differ>"})`, the scheme found by grepping the shipped scheme files in 18-02; if no shipped scheme differs, classify `dstyle`/`dlstyle` under the comment `# honoured; indistinguishable under every shipped scheme, proved in test_dot_rows.py::TestStyle::test_dstyle` and prove them there against a hand-written scheme file (the existing `test_scheme_*` fixtures write scheme files to tmp). Counts (A33): the plot pending count (-2 for dstyle/dlstyle, +1 for dlalign's new pending line, TR-18.6) and the declared plot count (+9: `DOTEXtend NDOTs Dsymbol DColor DFColor DSIZe DLColor DLWidth DLAlign`) are recounted at the section's base with the file's `_declared_*()` helpers and written `# <measured old> -> <new>: B5b <why>`, never as numbers copied from this plan.
- test/test_help_claims_8.py: nothing (dstyle/dlstyle leave the blocks).
- dash.sthlp:236-260 (J2: `dot` "as twoway describes" becomes true), :5040-5046 (the "Dot and marker back-line styles" entry loses dstyle/dlstyle, keeps bmlinestyle), :1998-2008 if that is dot's paragraph (grep `{cmd:dot}` near "dotextend" in dash.sthlp; the research anchor :1998-2008 is the reflow paragraph at 6370ca4 -- find the dot sentence by grep), the `base()` synopt (S12's :3068-3078 says "on dot it matters only with dotextend(no) (section 18)" -- S18 rewrites that clause to the honoured form).

## User stories

- US-18.1 As a Stata user pasting `twoway dot mpg weight`, I want the rows of dots twoway draws behind each marker.
- US-18.2 As a Stata user, I want `dotextend(no)`, `ndots(30)`, `dcolor(gray)`, `dsize(small)` to style the rows as twoway does.
- US-18.3 As a Stata user, I want `dot ..., horizontal` rows along the y axis, and `colorvar()` to colour the rows with the markers.
- US-18.4 As a dashboard user, I want the rows to span the axis after a filter move in the served app.

## Business requirements

- BR-18.1 Every dot layer draws 75 dots per observation (or `ndots()`), from the axis base to both ends (or to the value under `dotextend(no)`), in the scheme's dots style, before the marker; nothing is printed.
- BR-18.2 The nine d-options and `ndots()`/`dotextend()` are honoured; `dlalign()` is named once (Bokeh cannot align a stroke).
- BR-18.3 The rows follow the axis in the served app after a move; the saved page's behaviour is measured and either exact or filed.
- BR-18.4 The dots are not brushed, not hovered, not keyed, and not counted by KPIs.

## Technical requirements

- TR-18.1 **Declare** after `DSTyle(string asis)       DLstyle(string asis)      BMLinestyle(string asis) ///` (:1206): `DOTEXtend(string) NDOTs(string) Dsymbol(string asis) DColor(string asis) DFColor(string asis) DSIZe(string asis) DLColor(string asis) DLWidth(string asis) DLAlign(string asis) ///` -- check `Dsymbol` (`d`) against test_abbreviations.py's prefix rule: `d` collides with `density`? `DENsity`'s minimum is `den`, so `d` alone is free; `DColor` `dc` vs `DISCrete` `disc`: free. `sreturn` lines after :1524; JSON keys after `dstyle dlstyle bmlinestyle` (:4452): `dotextend ndots dsymbol dcolor dfcolor dsize dlcolor dlwidth dlalign`; stylelist keys: `dsymbol dcolor dfcolor dsize dlcolor dlwidth` join `_dash_stylelist_keys()` (dash_parse.mata:5283-5292) as per-y lists like their m-twins; `_dash_p_drops` (:4415-4430) gains them (p() sets the whole seriesstyle, dots included -- the existing comment at :4427 says so). Rules: `dsize=style dlwidth=style,0,10000,u dcolor=colour dfcolor=colour dlcolor=colour ndots=int,2,10000 dotextend=enum,yes|no` (twoway's `yesno` names: measured U18-02 for `dotextend(y)`/`dotextend(0)`; write the accepted set from the fixture). Delete the pending lines :1346-1347 (`dstyle`, `dlstyle`) and their comment's two clauses.
- TR-18.2 **Renderer `map_dot`** (replace :18910-18937): build the marker through `map_scatter` as today (so `colorvar`, mlabel, jitter, hover, the key stay), then the dots: `vals = <the marker source's y (or x under horizontal) finite values>`, `pos = <the x (or y) values>`; `ndots = int(_stat_option_float(options, "ndots", 75, "dot", lo=2, hi=10000) or 75)`; `extend = str(options.get("dotextend", "yes")).strip().lower() not in ("no", "n")`; the dots source `ColumnDataSource({"x": [], "y": [], "__dash_row": []})` tagged `dash_dots:` + compact JSON `{"letter": "y", "ndots": ndots, "extend": extend}` with `src._dash_dots_pos = pos`, `src._dash_dots_vals = vals`; the renderer `dr = fig.scatter(x="x", y="y", source=src, marker=<dsymbol or scheme symbol dots>, size=max(1.0, <dsize px or scheme symbolsize dots px>), fill_color=<dcolor/dfcolor or scheme color dots>, line_color=<dlcolor or scheme color dotmarkline>, line_width=<dlwidth px or scheme linewidth dotmark px>)` added BEFORE the marker (Bokeh draws renderers in `fig.renderers` order: insert the dots renderer at the marker's index: `fig.renderers.remove(dr); fig.renderers.insert(fig.renderers.index(marker_r), dr)`); `dr.tags += ["dash_dots"]`; no hover; `legend_label` absent; `self._apply_colorvar(fig, dr, src, options, add_key=False)` after the dots source gains the colour column repeated per dot (built in the finisher: the finisher writes `__dash_row` and copies the marker source's colorvar column by row). Return `[dr, marker_r]`.
- TR-18.3 **Finisher**: in `_dash_finish_auto_bases(fig)` (:32115) add the loop: for each renderer tagged `dash_dots:...`: `lo, hi = sorted((rng.start, rng.end))` of `fig.y_range` (letter y) or `fig.x_range` (x); `base = 0.0 if lo <= 0 <= hi else (hi if hi < 0 else lo)`; `delta = (hi - lo)/(ndots - 1)`; for each observation i with value v_i at position p_i: ends = `[lo, hi]` if extend else `[v_i]`; for each end: `k_max = min(10000, floor(abs(end - base)/delta))`, positions `base + sign(end-base)*k*delta` for k = 0..k_max; write `y` = positions, `x` = p_i repeated (swapped under letter x), `__dash_row` = None; the total capped by `_DASH_DOTS_MAX` (reduce `ndots` proportionally, note once). On a date axis the finished range is in epoch ms and the dots are placed in ms (no unit conversion: positions are axis units already). The served re-finish: `_dash_refinish_axes` (:32271-32301) does NOT call `_dash_finish_auto_bases` (R2-33); the function's callers are :33407 (`_dash_finish_count_ticks`) and :33500 (`_dash_common_count_ticks`). 18-03 checks :33500 first as the served re-finish hook: if `_dash_common_count_ticks` runs on the served move path (trace the served move handler to it), the dots are re-finished after every move and `TestAfterAServedMove` is green. Only if :33500 is not on the move path does the S35 residual apply: `_dash_refinish_axes` has R11 owners S24/S33/S35/S45 -- NOT S18 -- so the served dots re-finish is then filed for S35 (batch 12) and `TestAfterAServedMove` is xfail strict until then.
- TR-18.4 **Scheme**: `SchemeParser` gains readers `dots_color`, `dotmarkline_color`, `dots_size_px`, `dotmark_line_width_px`, `dots_symbol` (methods; copied with the class) over the stubs `color dots`, `color dotmarkline`, `symbolsize dots`, `linewidth dotmark`, `symbol dots`, with s2color's values as defaults when a scheme file lacks them; add the five stub lines to `dash-s2color.scheme` and the other shipped scheme files (values from each Stata scheme file: `grep -n "dots\|dotmark" /Applications/StataNow/ado/base/s/scheme-*.scheme`), and extend `test_unread_scheme_directives.py`'s read set.
- TR-18.5 **Constants/copy list**: `_DASH_DOTS_MAX = 2_000_000` in the constants tuple after `_DASH_STALE_STATUS_HTML` (R2); no new module-level function (the finisher is an existing copied function; the geometry is a `GlyphMapper` staticmethod `_dot_positions(lo, hi, base, delta, vals, pos, extend, ndots)` so test_estimator_cost can time it). function_test_map.py: `'GlyphMapper._dot_positions': 'test/test_dot_rows.py::TestGeometry::test_positions_match_twoway'`.
- TR-18.6 **Tests/pins**: Evidence's flips and LIVE_VALUES entries: `"dotextend": ({"dotextend":"no"},{"dotextend":"yes"},"dot",{})`, `"ndots": ({"ndots":"10"},{"ndots":"40"},"dot",{})`, `"dsymbol": ({"dsymbol":"square"},{"dsymbol":"triangle"},"dot",{})`, `"dcolor"`, `"dfcolor"`, `"dlcolor"` with red/blue, `"dsize": ({"dsize":"small"},{"dsize":"large"},"dot",{})`, `"dlwidth": ({"dlwidth":"thin"},{"dlwidth":"thick"},"dot",{})`, `dlalign`: twoway accepts it and dash names it once, so it gets a pending line `if `: length local dlalign' local _dash_pending ...` and a PLOT_VALUES entry `("inside","outside","dot")`; the plot pending count's net move is -2 +1, written per A33 (`# <measured old> -> <new>: B5b dstyle() dlstyle() drawn, dlalign() named`).

## Boundaries

- No `_FILTER_JS`/`_dash_stale_kind` (S19). No `_apply_colorvar` body (S17; S18 calls it). No `_dash_refinish_axes` (R11). No `base()` semantics beyond reading the finished axis (S03). No `recast()` on dot (S03: silent).
- `dlalign()`: named, not drawn (Bokeh limit), like `mlalign()`.

## Stata truth

New `scripts/extract_dot_truth.do` → `test/fixtures/dot_truth.json`; `sysuse auto`:
- `D01` `twoway dot mpg weight in 1/5, name(d1)`: `.d1.plotregion1.plot1.num_dots`, `.dots_extend`, `.bar_drop_to.stylename`, `.plotregion1.yscale.curmin/curmax`, `.xscale.curmin/curmax`; the SVG: the dot circles' centres (grouped by the observation row they share), their radius and fill; the marker circles' radius.
- `D02` `dotextend(no)`, `D03` `ndots(10)`, `D04` `ndots(1)` (rc/text), `D05` `dotextend(0)`/`dotextend(y)` (accepted spellings), `D06` `horizontal`, `D07` `dcolor(red) dsize(medium) dlcolor(blue) dlwidth(thick) dsymbol(square)` SVG attributes, `D08` `dstyle(p3)` under `scheme(s1color)` fill, `D09` `dot mpg weight, colorvar(rep78) colordiscrete` (dot fills follow the level?), `D10` `dot mpg weight, base(50)` axis range (S03's; recorded for the combined line), `D11` `dlalign(outside)` rc.
`_meta`, `git add -f`, test_fixtures_are_committed.py.

## TDD test stubs

New `test/test_dot_rows.py`:
- Test: `map_dot` returns `[dots, marker]`; the dots renderer is a Scatter tagged `dash_dots`, drawn before the marker, no legend, no hover -- `TestShape::test_two_renderers[mode]`, `::test_order_and_tags[mode]` (red).
- Test: after the axis finish, the dot positions equal `_dot_positions` from the finished range (75 per end, base rule, delta) and match D01's SVG centres (scaled to data units through the axis) -- `TestGeometry::test_positions_match_twoway`, `::test_base_rule[lo-hi]` (red); `dotextend(no)` runs to the value -- `::test_extend_no[mode]` (red); `ndots(10)` -- `::test_ndots[mode]` (red); `horizontal` swaps -- `::test_horizontal[mode]` (red).
- Test: default style: size `max(1, vtiny px)`, fill `color dots`, outline `color dotmarkline`, width `linewidth dotmark` -- `TestStyle::test_scheme_defaults[mode]` (red); each d-option -- `::test_d_option[mode-opt]` (red); `dstyle(p3)` under a scheme whose p3dot differs -- `::test_dstyle` (red); `dlalign()` named once -- `::test_dlalign_named` (red).
- Test: `colorvar()` colours the dots per observation -- `TestColorvar::test_dots_take_the_mapping[mode]` (red; depends on D09).
- Test: the dots have null row ids and are absent from the brush selection and KPI counts -- `TestBrushIgnoresDots::test[mode]` (red).
- Test: served move re-finishes the rows (`TestAfterAServedMove::test_span_follows_axis`; xfail strict if TR-18.3's residual applies); saved move keeps them right or is filed -- `TestAfterASavedMove::test_measured` (the 18-01 measurement; red or xfail per D-18a).
- Test: 100,000 rows × 75 dots under 2 s in `_dot_positions` -- test_estimator_cost.py `TestDotRows::test_under_two_seconds` (red: no function).
- Test: `_DASH_DOTS_MAX` on the copy list; dash.ado declares the nine and names none but dlalign -- `TestTheServedCopy::test_constant`, `TestTheAdoText::test_declared` (red).

cscript, block `* ==== S18 B5b: dot rows ====` (the section's one row; appended by 18-04, the closing task, A14):
- U18-01 `dash dot mpg weight in 1/5, name(u18)`: python render: 5 observations × 2 ends × ~75 dots; the positions equal twoway's D01 centres in data units within 1e-6 of delta; the first dot of each run is at the base twoway's class values give; no note.
- U18-02 `ndots(1)`, `dotextend(maybe)`, `dlalign(x)`: dash rc/text equal twoway's; `dotextend(0)` accepted iff twoway accepts it.
- U18-03 `dot mpg weight, dcolor(red) dsize(medium)`: the dots renderer's fill is #ff0000 and its size equals `map_scatter`'s medium marker size, both modes.
- U18-04 `dot mpg weight, horizontal`: the rows run along y (x constant per run) in dash's render; twoway D06 `bar_drop_to` agrees.
RC-07's dot half in test_twoway_option_parity.cscript (`dot ignores recast() silently`) is S03's and is not flipped here.

Parity (R8): CORPUS `_case("dot default rows", [plot_for("dot")])` (the bare entry exists; add `_case("dot dotextend(no) ndots(20) dcolor(gray)", ...)`, `_case("dot horizontal", ...)`, `_case("dot colorvar", ...)`); MOVE_CORPUS `_case("dot rows after a move", [plot_for("dot")])`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| geometry (base, delta, extend, ndots, horizontal) | pytest TestGeometry; U18-01/04 | dot_truth D01-D06 | yes |
| style and d-options | pytest TestStyle; U18-03 | D07 D08 | yes |
| colorvar on dots | pytest TestColorvar | D09 | yes |
| brush/KPI exclusion | pytest TestBrushIgnoresDots | -- | yes |
| moves | pytest TestAfterA*Move | -- | measured |
| refusals/spellings | U18-02 | D04 D05 D11 | n/a |
| cost | test_estimator_cost TestDotRows | -- | -- |

AC-18.1 stubs green (xfails strict where filed); AC-18.2 U18-01..04 PASS; AC-18.3 dash.sthlp dot paragraph rewritten (dotextend, ndots, d-options documented; :5040-5046 loses dstyle/dlstyle; :236-260's "as twoway describes" now true for dot); AC-18.4 audit row 68 annotated `[WP-31 B5b, commit pending: corrected -- ...]`; AC-18.5 the GAPS3 `B5b Tracked` line reads `Closed in WP-31, BUGS.md "<title>", commit pending.` (S03 owns `B5a`'s line).

## Tasks

**Commit boundary.** 18-01..18-03 steps; 18-04 commits `Draw twoway's dot rows with dotextend(), ndots() and the d-options (WP-31 B5b)` on `wp31-s18`.

<task type="auto" id="18-01">
  <name>Write the failing dot tests and the dot truth extractor</name>
  <files>test/test_dot_rows.py, scripts/extract_dot_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_dot_truth.do on scripts/extract_default_base_truth.do's skeleton with probes D01-D11 (class values `.d1.plotregion1.plot1.num_dots`, `.dots_extend` read as a string, `.bar_drop_to.stylename`, the scales' curmin/curmax; SVG circles through test/cert_svg.do's `svg_truth.svg_document`, grouped into runs by shared y (or x) coordinate; refusal rc/text with `capture noisily`). Run through the slot wrapper; `git add -f test/fixtures/dot_truth.json`; register it. Create test/test_dot_rows.py with every stub (TestShape, TestGeometry, TestStyle, TestColorvar, TestBrushIgnoresDots, TestAfterAServedMove, TestAfterASavedMove, TestTheServedCopy, TestTheAdoText) and add `TestDotRows::test_under_two_seconds` to test/test_estimator_cost.py (timing `GlyphMapper._dot_positions` on 100,000 rows; it fails red with AttributeError until the function exists, which is the point -- no skip). Run `python3 -m pytest test/test_dot_rows.py test/test_estimator_cost.py::TestDotRows -q -p no:randomly > <scratch>/18-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/18-01-failure.txt prints >= 15; python3 -c "import json;d=json.load(open('test/fixtures/dot_truth.json'));print(d['D01']['num_dots'], d['D01']['dots_extend'])" prints 75 and twoway's extend value.]]></verify>
  <done>The dot-row tests fail against the batch-6 base and twoway's dot geometry, style and refusal truth is committed.</done>
</task>

<task type="auto" id="18-02">
  <name>Declare the dot options in dash.ado</name>
  <files>dash.ado, dash_parse.mata, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[Apply TR-18.1: the nine declarations after :1206; sreturns after :1524; JSON keys after :4452; the six stylelist keys in `_dash_stylelist_keys()` (dash_parse.mata:5283-5292); `_dash_p_drops` (:4415-4430) gains them; rules in `_dash_option_rules` (:2990-3008) with `dotextend`'s accepted spellings and `ndots`'s bounds from dot_truth.json D04/D05; delete the pending lines :1346-1347 (dstyle, dlstyle) and add `if `: length local dlalign' local _dash_pending `"`_dash_pending' dlalign"'` in their place with the comment `// WP-31 B5b: dlalign() is accepted and named: a stroke cannot be aligned in Bokeh (as mlalign())`. test_unsupported_report_is_true.py: move dstyle/dlstyle to LIVE_VALUES (Evidence's pair rule), add the LIVE entries of TR-18.6, `PLOT_VALUES["dlalign"] = ("inside", "outside", "dot")`; recount the plot pending and declared plot counts at the section's base with the file's `_declared_*()` helpers and write `# <measured old> -> <new>: B5b dstyle() dlstyle() drawn, dlalign() named` and `# <measured old> -> <new>: B5b the nine dot options declared` (A33). Run `python3 -m pytest test/test_dot_rows.py::TestTheAdoText test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_help_claims_8.py -k dlalign -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed; `grep -c "DOTEXtend(string) NDOTs(string)" dash.ado` prints 1; `grep -c "_dash_pending' dstyle" dash.ado` prints 0.]]></verify>
  <done>dash.ado declares, validates and stores dotextend(), ndots() and the d-options, names dlalign() alone, and drops dstyle()/dlstyle() from the pending list.</done>
</task>

<task type="auto" id="18-03">
  <name>Draw the dot rows in both renderers</name>
  <files>dash_render.py, dash-s2color.scheme, test/function_test_map.py</files>
  <action><![CDATA[Apply TR-18.2 (replace map_dot :18910-18937; the `_dot_positions` staticmethod beside it), TR-18.3 (the `dash_dots:` loop in `_dash_finish_auto_bases` :32115-32200; `_dash_refinish_axes` :32271-32301 does not call it -- check first whether its caller at :33500 (`_dash_common_count_ticks`) runs on the served move path; if it does, the served re-finish is covered and `TestAfterAServedMove` is green; if it does not, do NOT edit `_dash_refinish_axes` (R11): mark `TestAfterAServedMove` xfail strict with reason `WP-31 B5b residual: served re-finish of dot rows (S35)` and note it for 18-04's residual entry), TR-18.4 (SchemeParser readers for the five stubs with s2color defaults; the five stub lines added to dash-s2color.scheme and each other shipped scheme file with the values grepped from Stata's scheme files; extend test_unread_scheme_directives.py's read set), TR-18.5 (`_DASH_DOTS_MAX` constant and its copy-list entry after "_DASH_STALE_STATUS_HTML"; function_test_map.py entry for `_dot_positions`). Flip test/test_glyphs.py TestMapDot's four tests (:277-304) to the `[dots, marker]` form with the Flipped docstrings. Run `python3 -m pytest test/test_dot_rows.py test/test_glyphs.py::TestMapDot test/test_estimator_cost.py::TestDotRows test/test_unread_scheme_directives.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py test/test_mode_parity.py -k dot -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed (xfailed allowed only for the filed residual); `python3 -c "import dash_render as d;print(d._DASH_DOTS_MAX)"` prints 2000000; `grep -c "symbolsize dots" dash-s2color.scheme` prints 1.]]></verify>
  <done>Both renderers draw twoway's dot rows from the finished axis, styled by the scheme's dots style and the d-options, before the marker.</done>
</task>

<task type="auto" id="18-04">
  <name>Certify, document and commit B5b</name>
  <files>test/test_wp31_truth.cscript, dash.sthlp, TWOWAY_COVERAGE_AUDIT.md</files>
  <action><![CDATA[Append `* ==== S18 B5b: dot rows ====` (U18-01..U18-04) above the marker (after S17's block) and run with `WP31_ONLY=S18`. dash.sthlp: find dot's paragraph (grep `dotextend` and `{cmd:dot}` in the plot-types section; if none exists, add one after the `{ul:Join order}` paragraph): "dash draws dot as twoway does: 75 dots per observation (ndots(#)) from the axis base to both ends (dotextend(yes)) or to the value (dotextend(no)), in the scheme's dots style, styled by dstyle() dsymbol() dcolor() dfcolor() dsize() dlstyle() dlcolor() dlwidth(); dlalign() is accepted and named (Bokeh cannot align a stroke); the rows follow the axis in the served app after a filter move [and on the saved page / and are frozen at the build's axis on the saved page -- per 18-01's measurement]"; remove dstyle/dlstyle from the "Dot and marker back-line styles" Unsupported entry (:5040-5046; keep bmlinestyle) and add dlalign there under the marker-outline entry; rewrite S12's clause in the `base()` synopt ("on dot it matters only with dotextend(no) (section 18)") to "on dot, where it widens the axis the rows span". TWOWAY_COVERAGE_AUDIT.md row 68: `[WP-31 B5b, commit pending: corrected -- dot rows, dotextend(), ndots(), the d-options drawn]`. BUGS.md: close S18's `B5b` entry (Resolution form; Residual clauses for any xfail filed in 18-03 and for the saved-page measurement if red); GAPS3 §9: write `- **B5b Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (or `Partly closed` naming the residual entry if one was filed; the merger's step k.3b rewrites `pending` to the landed sha; `B5a`'s line is S03's and is not touched); replace the `<!-- WP-31 B5b -->` markers (Results: "dot mpg weight: 75 dots per observation across the axis (was: markers only)"). Run `python3 -m pytest test/test_dot_rows.py test/test_help_conformance.py test/test_help_plot_types.py test/test_tracking_documents.py -q`; commit; grep for `claude|anthropic`.]]></action>
  <verify><![CDATA[Stata log shows "U18-01 PASS" .. "U18-04 PASS"; pytest 0 failed; `git log -1 --format=%s` ends "(WP-31 B5b)"; `grep -c 'B5b Tracked:\*\* Closed in WP-31\|B5b Tracked:\*\* Partly closed in WP-31' GAPS3.md` prints 1; `grep -c "dotextend" dash.sthlp` prints >= 2.]]></verify>
  <done>B5b (the rows-and-options half of dot) is closed in one commit with its tests, fixture, help, audit, BUGS.md, the B5b GAPS3 line and CHANGELOG lines.</done>
</task>

## Section completion criteria

- Stubs green; U18-01..04 PASS; TestMapDot flipped with reasons; counts moved.
- `_DASH_DOTS_MAX` on the copy list; `_dot_positions` in function_test_map.py; the dots stubs in every shipped scheme file.
- Help, audit, BUGS.md, the `B5b` GAPS3 line (`commit pending`), CHANGELOG in the one commit; residuals (served re-finish, saved range) filed if measured red.

## Notes

- **Renderer order:** dots BEFORE the marker (twoway `yxview_dot_draw.ado:31-50`); insert the dots renderer at the marker's index in `fig.renderers`.
- **Copy list (R2):** `_DASH_DOTS_MAX` after `_DASH_STALE_STATUS_HTML` in the constants tuple; `_dot_positions` is a staticmethod (copied with the class).
- **Finisher ownership:** `_dash_finish_auto_bases` has no other batch-6 editor; `_dash_refinish_axes` is R11's (never edited here) and does not call the finisher -- the served hook to check is its caller at :33500 (TR-18.3).
- **Scheme files:** the five stubs' values per scheme come from Stata's own `scheme-*.scheme` files (RGB names only, M7).
- **Fixture rule (R7)**; **python_exec hazard**.
- **Security:** d-option values pass the same translators as the m-options; the dots source holds numbers only; no text reaches HTML.
- **Merge rules cited:** R1, R2, R3 (S18 owns dot's help paragraph and the :5040-5046 entry), R7, R8, R9, R10, R11 (not S18's), R12 (S18 is batch 6's `map_dot` owner).
- **Commit body lines:** `Regression: test/test_dot_rows.py::TestGeometry::test_positions_match_twoway -- failed at <base> with <text>`; `Flipped: test/test_glyphs.py::TestMapDot::test_dot_returns_renderer -- "map_dot returns one GlyphRenderer" was wrong because twoway draws dot rows before the marker (dot_truth.json D01)`; `Fixture: test/fixtures/dot_truth.json (scripts/extract_dot_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS3: B5b Tracked`.
- **Decisions for maintainer ratification:** D-18a (rows rebuilt from the finished axis; saved-page behaviour measured, residual if red), D-18c (1 px floor), D-18d (dlalign named), the `dlalign` pending line (the plot pending count moves -2 +1, written per A33).
