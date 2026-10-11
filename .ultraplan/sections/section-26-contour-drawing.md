# Section 26: Contour and contourline drawn: registration, options, colours, key, cap (B4 part b)

> Part of: WP-31 · GAPS3 rows: B4b · Risk: red · Batch: 9 · Depends on: 23 · Blocks: 29, 57 · Tasks: 4, 1 commit · Case-id prefix: U26

## Overview

**What is wrong today.** GAPS3 B4 (GAPS3.md:113): "`contour`, `contourline` refused by name." dash.ado:4891-4893 answers both with `dash: 'contour' is a twoway plot type dash does not draw: it needs a surface interpolated over a grid...` r(198); dash_parse.mata:1802-1810 lists both in `_dash_undrawn_plottype`; test_parser.cscript P1A-49..51 and test_help_plot_types `_REFUSED` pin it. After S23 (batch 8) the renderer holds twoway's surface (`_dash_contour_surface`), but no plot type reaches it.

**After this section** `dash contour z y x` and `dash contourline z y x` register (exactly three numeric variables, `zyx2view_parse:68-85`) with a new spec key `zvar`, and both renderers draw them through Bokeh's `figure.contour(x=gx, y=gy, z=gz, levels=..., fill_color=..., line_color=...)` (bokeh-web.md §1; verified 10oct2026 on both installed Bokehs): filled bands between twoway's cuts for contour, lines at the cuts for contourline. Cuts come from `ccuts()`, `levels(#)` (with `minmax`), else the z-axis ticks (`zlabel(#7)` default) as `zyx2view_g.class:254-352` chooses them; colours from `crule(hue|chue|intensity|linear)` between `scolor()`/`ecolor()` (scheme `color contour_begin blue`, `contour_end red`), or `ccolors()`, by `zyx2style.class`'s arithmetic; labels from `clabels()`/`format()`; a colour key (`ContourColorBar`) placed by `clegend()` (scheme `clockdir zyx2legend_position 3` = right) or off; `interp()` passed to S23's surface; `horizontal` swaps x and y. In the served app the layer refits after a filter move with no extra code (`_dash_redraw_for` registers any layer whose mapper built its own source, dash_render.py:49585-49604). On the saved page the layer is frozen and marked `(grid unfiltered)` until S29 (batch 10) adds the JS twin; above the cap (`surface["capped"]`) it stays frozen in both modes' saved pages and a note names the bound.

**Why this split (A1).** The drawing is one session's work on top of tested helpers; the saved-page refit is another (S29).

**Test order and commit rule (rule 7, BRIEF).** One cycle, one commit `(WP-31 B4b)`. 26-01 writes `test/test_contour_layers.py` red, the truth block U26-1..U26-9, saves `<scratch>/26-01-failure.txt`, never commits. 26-02 registers the types in dash.ado/dash_parse.mata and adds the options. 26-03 adds the mappers, the readers and the colour key in both modes, flips the pins. 26-04 updates help/audit/pkg, closes B4b and commits.

### Section decisions (binding on the executor)

- **D-26a. Spec keys.** `{"type":"contour","zvar":z,"yvar":y,"xvar":x,"options":{...}}`. The new key `zvar` joins `_dash_extract_vars` (dash_parse.mata:2855-2857) and `_DASH_PLOT_VAR_KEYS` (dash_render.py:36470) and every reader listed in TR-26.6.
- **D-26b. A new family `_pt_contour` ("contour contourline") in dash.ado and `_DASH_CONTOUR_TYPES` in the renderer**, with its own var-count branch and its own branch in `_make_figure_body` and `_dash_draw_layer`, before the range branch.
- **D-26c. Levels passed to Bokeh.** Fill levels `lv = [lo] + cuts + [hi]` with `lo = min(zmin, cuts[0]) - 1`, `hi = max(zmax, cuts[-1]) + 1` (twoway has `#cuts + 1` levels: below the first cut, between, above the last; `zyx2view_g.class:299-300`). Bokeh fills `len(lv) - 1 = #cuts + 1` bands and draws lines at every level: the `lo`/`hi` lines lie outside the data so no segment is drawn. contourline passes `levels = cuts` with `line_color` only (fill source empty, bokeh-web.md §1). Fill `line_width` 0 (Bokeh's default for the fill glyph); twoway's `gm_linewidth .001`.
- **D-26d. Cut selection** (`zyx2view_g.class:254-352`, stata-ground-truth.md §3): `ccuts(numlist)` as given (sorted; `zlabel(cuts)` also set). Else `levels(#)`: `# - 1` cuts `zmin + i*(zmax - zmin)/#`, `i = 1..#-1`; `minmax` prepends `zmin` and appends `zmax`. Else the z-axis ticks: `_dash_natscale_ticks(zmin, zmax, 7)` (the `zlabel(#7)` default; the user's `zlabel()` rule or list replaces it through the existing zlabel reader at :12047) dropping the first and last when the ticks come from a rule and there are more than two; if empty, `[zmax]` (`:281-295`). `ccuts()` with `levels()` is refused r(198) `option ccuts() cannot be combined with option levels()` (`zyx2view_parse:121-124`; text measured by the extractor).
- **D-26e. Colour arithmetic** (`zyx2style.class:160-337`, read 10oct2026), `L = #levels`, `dif = max(L-1, 1)`, `i = 1..L`, `i1 = i-1`:
  - `linear`: `round(b + i1*(e-b)/dif)` per RGB channel (b = scolor RGB, e = ecolor RGB); `revlinear` swaps b and e.
  - `intensity`: ecolor at intensity `i/L` (scolor ignored) through `GlyphMapper._blend_intensity(hex, i/L)` (:12590).
  - `hue` (default; scheme `zyx2rule contour hue`): `h = h0 + i1*(h1-h0)/dif`, clamped at 0, applied to scolor's HSV as `_colour_hsv(h, s0, v0)` (:7372) where `(h0, s0, v0)` is scolor's HSV and `h1` ecolor's hue.
  - `chue`: `if h1 <= h0: h1 += 360` then as hue (no clamp).
  - `phue`: scheme p1..p15 then hues -- out of scope (stata-ground-truth.md §3 names it; the parse-class list `zyx2rule.class:17` includes it): refused r(198) with twoway's words only if twoway refuses; otherwise drawn as `hue` and named in the note. The extractor records `crule(phue)`'s rc.
  - `ccolors(list)`: one colour per level, the last repeated (`:115-138`).
  Stata's HSV convention is the one `_colour_hsv` already implements (E3: `"hsv 209 .766 .435"` is `#19456e`). The fixture records the drawn RGB per level per rule; `TestColours` pins dash's output to it.
- **D-26f. Labels.** Level label `i` = `clabels()[i]` else `string(cut_i, fmt)` with `format()` else the z variable's display format (`zyx2view_g.class:227-247`), through `_dash_fmt`. The key's tick labels use them (`ContourColorBar` `major_label_overrides`).
- **D-26g. The key.** `cr.construct_color_bar(title=<ztitle() or z's label>)` added at `clegend()`'s side: `position(3)`/default -> `"right"`, 9 -> `"left"`, 6 -> `"below"`, 12 -> `"above"`; `clegend(off)` draws none; `width()` -> `ContourColorBar.width`; `title()` -> its title. The ordinary legend gets no key for the layer (`numkeys 0`, `twoway_contour_parse.class:32`). contourline's key is the ordinary legend's `plegend()` -- out of scope: contourline draws no key, named in the note.
- **D-26h. Options drawn, pending, refused.** Drawn: `ccuts levels minmax crule scolor ecolor ccolors clabels format interp clegend horizontal vertical zlabel ztitle zscale clwidths clpatterns` (the last two on contourline: vector `line_width`/`line_dash` per level) and `reversekey` (reverses the key's levels). Pending (named in the note, help Unsupported): `heatmap outlines colorlines xcuts xlevels ycuts ylevels heatlabel tw_heatmap showxycuts`. `colorvar()` on contour: dropped as twoway drops it (`.allowcolorvar=0`), named. Refused r(198) with the extractor's text: `ccuts()+levels()`, a second contour/contourline plot (`multiple contour, heatmap, or patch plots not allowed` / `multiple contourline plots not allowed`, `twowaygraph_g.class:349-376`), string z (`yxview_parse:120`, text measured).
- **D-26i. The cap note (A8).** Text fixed here: `dash: contour draws an approximate surface: <n> distinct points exceed the <_DASH_CONTOUR_EXACT_MAX> twoway's grid is reproduced for, so a 100 x 100 grid over the data's range is drawn instead; the saved page does not recompute it.` printed through `_dash_note` once per layer in both modes.
- **D-26j. Stale cue.** `_DASH_COMPUTED_ONLY_TYPES` gains both types; `_dash_stale_kind` returns `"grid"` for them (the suffix `(grid unfiltered)` exists); S29 makes it return None within the cap and leaves `"grid"` above it (`options` cannot see `capped`, so S29 reads the surface's flag through the frozen tag; recorded for S29).

## Risk: [red] -- a new data model (three roles, a derived 2-D source), a new Bokeh renderer class, colour arithmetic in HSV, and two renderers

**Why.** `ContourRenderer` is not a `GlyphRenderer`: every place that walks `fig.renderers` for `data_source`, `glyph`, legend keys, hover, brushed copies (`_sync_brushed_copies`), transposition and the served redraw's source pairing meets a renderer with `fill_renderer`/`line_renderer` children instead.

**Risk factors.**
1. `_dash_add_glyph`'s `finally: GlyphMapper._sync_brushed_copies(fig, _before)` reads `.glyph` on new renderers: a ContourRenderer has none.
2. Served redraw pairs sources by position (`agg_sources[(gname,pi)]['sources']`); the mapper must return the two child sources in a fixed order.
3. `_dash_transpose_layer` maps glyph classes (`_DASH_TRANSPOSE`); a contour under `horizontal` is turned by swapping gx/gy in the mapper instead.
4. Hover: `_dash_build_hover` picks a renderer per shape; a MultiPolygons fill with `lower_levels/upper_levels` columns needs its own tooltip row or none.
5. Hue arithmetic: Stata's HSV of a named colour must match `_colour_hsv`'s inverse; the fixture decides.
6. The z axis has no Bokeh axis: `zlabel()`'s reader (:12047, the colorvar key) is reused for the key's ticks.

**Mitigation.**
1. `_sync_brushed_copies` skips renderers without `glyph` (one `getattr(r, "glyph", None) is None: continue` line; pinned).
2. `map_contour` returns `[cr]` and tags `cr._dash_contour_sources = [fill_src, line_src]`; `_dash_draw_layer` collects child sources for ContourRenderers (TR-26.7).
3. TR-26.5: `horizontal` swaps `(gx, gy, gz.T)` before `figure.contour`; `_dash_is_horizontal` is not called for the family (the layer is drawn turned).
4. One HoverTool row `z: @lower_levels .. @upper_levels` on the fill renderer for contour, `z: @levels` on the line renderer for contourline (`_dash_build_hover` `_band` shape pattern).
5. `TestColours` compares every level's hex with the fixture's `.cstyles[i].color.rgb` for the four rules.
6. The `zlabel()` list/rule reader is called with `(zmin, zmax)`; tested.

## Dependencies

- **Depends on: 23** (`_dash_contour_surface`, constants, `contour_truth.json`).
- **Blocks: 29** (the JS twin needs `_dash_agg_config` with `type, xvar, yvar, zvar, cuts, interp, cap` and the two child sources), **57** (an example page).
- **Parallel batch: 9**, merge order S28, S26, S27. **Can run with S27 and S28**: S27 edits title placement; S28 edits `_FILTER_JS`. S26 is batch 9's editor of `_make_figure_body`, `_generate_app_source` (one branch in `_dash_draw_layer`, one in `_hover_cols_of`) and plot-type registration; it does not edit `_FILTER_JS`, `_dash_option_rules` (TR-26.3 adds rule tokens -- S26 is the batch-9 rules editor; S27/S28 add none), the appliers or `_dash_layout_cell`.

## Evidence

All anchors at `6370ca4` plus S23's additions (names, not lines).

### Refusal and oracles

dash.ado:4889-4900 (S21 Evidence); dash_parse.mata:1802-1810; test_parser.cscript P1A-49 (:301-315), P1A-50 (:318-328), P1A-51 (:331-353: the token echoed as typed, inside a multi-plot command, not for a prefix); test_help_plot_types.py:28 `_REFUSED`; test_help_claims_1.py "four types are refused" (after S21: "two" then "four" with sunflower/matamatrix; after S26: "two": sunflower, matamatrix); TWOWAY_COVERAGE_AUDIT.md:14, :24, :101-102; dash.pkg:5 ("forty-two" after S21 -> "forty-four"); the Supported list dash.ado:4901-4909; `_expand_plottype_str` table (dash_parse.mata:1703-1742; full names only: measured 23sep2026 "cont .. contou, contourl .. contourlin are not plot types").

### Bokeh (bokeh-web.md §1; probed 10oct2026)

`p.contour(x, y, Z, levels, fill_color=[...], line_color="black")` -> `ContourRenderer(fill_renderer, line_renderer, levels)`; fill source columns `xs ys lower_levels upper_levels fill_color [hatch_pattern]` with `xs[i]` = `[polygon][ring][points]`; line source `xs ys levels`; `cr.construct_color_bar(title=)` -> `ContourColorBar`; `cr.set_data(contour_data(x, y, Z, levels))` refits in Python; lines-only leaves the fill source `{'xs': [], 'ys': [], 'lower_levels': [], 'upper_levels': []}`. Vector `line_width`/`line_dash` of length `len(levels)`; vector `fill_color` of length `len(levels)-1`.

### Stata (stata-ground-truth.md §3; classes read 10oct2026)

Parser `zyx2view_parse:110-119` options; `:121-124` ccuts+levels refusal; `:157-159` ccuts sets zlabel; cut selection `zyx2view_g.class:254-352` (quoted in S23's reading: ticks of the z axis, first/last dropped under a rule with >2 ticks; empty -> `overallmax`; `set_ccuts_from_levels` `:356-373`); colours `zyx2style.class:166-337` (linear/revlinear/intensity/hue/chue, quoted in D-26e); `ccolors()` `:115-138`; labels `zyx2view_g.class:227-247`; drawing `yxview_contour_draw.ado:24-43` (`gdi filledcontour`), `yxview_contourline_draw.ado:15-45`; keys `levels` for contour, `levels-1` contourline (`:209-221`); `clegend()` grammar `clegend_option.sthlp:15-31`; scheme `clockdir zyx2legend_position 3`, `gridringstyle zyx2legend_ring 4`, `gsize clegend_width huge`, `color contour_begin blue`, `contour_end red`, `zyx2rule contour hue`. Multiple-plot refusals `twowaygraph_g.class:349-376`.

### Renderer anchors

`_DASH_RANGE_TYPES` :25958; `_dash_glyph_dispatch` :41883; `_dash_add_glyph` :42344 (and `_sync_brushed_copies` in its `finally`); `_make_figure_body` branches :43981-44035, frozen tagging :44049-44060; served `_dash_draw_layer` :49137-49257, `_hover_cols_of` :49259, registration :49585-49604; readers `_dash_layer_axis_names` :1252, `_dash_axis_vars` :1288, `_dash_layer_tick_format` :1358, `_dash_layer_series` :39826, `_dash_hover_layer_vars` :40053, `_dash_build_hover` :40081, `_dash_legend_keys` :39925; `_DASH_COMPUTED_ONLY_TYPES` :1884, `_dash_stale_kind` :1913; `_DASH_HORIZONTAL_TYPES` :31835; `_dash_natscale_ticks` :28994; `_colour_hsv` :7372; `_blend_intensity` :12590; `parse_color_alpha` :7284; zlabel reader :12047; `_dash_option_rules` plot tokens dash.ado:2990-3008; `_dash_parse_plot_opts` syntax :1167-1239, sreturns :1403-1530, JSON keys :4441-4458, `_dash_p_drops` :4415-4430; `_dash_rep_und_tab` dash_parse.mata:6250-6324 (rows for ccuts/crule/... if any: `grep -n "ccuts\|crule\|scolor" dash_parse.mata` found none at 6370ca4, so no row to delete).

## User stories

- **US-26.1** As a Stata user, I want `twoway contour z y x` and `contourline z y x` pasted into dash to draw twoway's filled bands or lines with twoway's cuts and colours so that my do-file runs unchanged.
- **US-26.2** As the same user, I want `ccuts()`, `levels()`, `minmax`, `crule()`, `scolor()`, `ecolor()`, `ccolors()`, `clabels()`, `format()`, `interp()`, `clegend()` honoured, and what is not drawn named.
- **US-26.3** As a served-dashboard viewer, I want the contour refit when a filter moves; as a saved-page viewer, I want to see that it was not.
- **US-26.4** As a user with very many points, I want a bounded drawing and a note saying it is approximate.

## Business requirements

- **BR-26.1** Both types register with three variables; counts and string z are refused with twoway's rc and words; a second contour plot is refused as twoway refuses it.
- **BR-26.2** Cuts follow twoway's selection; colours follow twoway's rule arithmetic; labels follow `clabels()`/`format()`.
- **BR-26.3** contour fills `#cuts + 1` bands; contourline draws `#cuts` lines; the key shows the levels; `clegend(off)` removes it.
- **BR-26.4** Served: refit after a move; saved: frozen and marked until S29; above the cap: approximate, noted, frozen.
- **BR-26.5** Options not drawn are named once; no silent difference.

## Technical requirements

- **TR-26.1 dash.ado registration.** `_dash_plottype_families`: `c_local _pt_contour "contour contourline"`. Var-count branch after S21's `_pt_rangept` branch: `_dash_parse_varpart_3v`; `nv != 3` -> one variable `too few variables specified` r(102), else `<ptype> requires 3 variables: <vl>` with `exit cond(nv < 3, 102, 103)` (the sentence replaced by the extractor's `counts.*` text if twoway's differs); `local zvar = word(vl,1)`, `yvar` word 2, `xvar` word 3. vfields: `""zvar":"..","yvar":"..","xvar":".."`. `_seg_xv` falls to `xvar`. Type lists: `_hz_htypes`/`_hz_vtypes` (:2301-2302) gain both; `_so_ser`, `mv_range`, `jit_undrawn`, `_wt_honoured`, `_ts_sortx`: none (twoway's zyx2 parser takes no weight: `varlist(min=3 max=3 numeric)`; a weight is refused with twoway's text, measured). Delete the contour branch of the `_pt_nodraw` block (:4891-4893) and both names from `_dash_undrawn_plottype`; Supported list gains `contour contourline`. Multiple-plot check: after the segments are read in `_dash_plot` (near :6984, beside `_dash_line_check`), count segments of type contour (or contourline) per graph; two -> `_dash_say("err", <measured text>)`, `exit 198`.
- **TR-26.2 dash.ado options.** `_dash_parse_plot_opts` syntax (:1167-1239) gains `CCUTs(string asis) LEVels(string) MINMAX CRULE(string asis) SColor(string asis) EColor(string asis) CColors(string asis) CLABels(string asis) FORMAT(string asis) Interp(string asis) CLEGend(string asis) CLWidths(string asis) CLPatterns(string asis) REVersekey HEATMAP OUTlines COLORLines` (minimums from `zyx2view_parse:110-119`; `format()` is also a contourline option name -- check it does not collide with an existing dash spelling; if `FORMAT` is taken, declare it as twoway spells it and fold). sreturns for each (:1403-1530); JSON keys appended to the list (:4441-4458): `ccuts levels minmax crule scolor ecolor ccolors clabels format interp clegend clwidths clpatterns reversekey`; pending lines for `heatmap outlines colorlines` (the `_dash_pending` form at :1320-1387). `_dash_option_rules` plot tokens (:2990-3008): `levels=int,2,1000@contour|contourline ccuts=numlist,1@contour|contourline crule=enum,hue|chue|intensity|linear|revlinear|phue@contour|contourline interp=enum,thinplatespline|shepard|none@contour|contourline scolor=colour ecolor=colour` and the S04 applicability table rows restricting all of them to the two types (text from the extractor). `clegend()` is a graph option (`[G-3]`): declare `CLEGend(string asis)` in `_dash_parse_graph_opts` (:933-966) and the plot parser's `g_` set, add to the seven key lists (:5776, 6714, 6748, 6849, 6924, 6956, 7339) and `_dash_rep_unique`. The ccuts+levels refusal: in `_dash_process_segment` after `_dash_validate_opts` (:5584): `if "`s(ccuts)'" != "" & "`s(levels)'" != "" { mata: _dash_say("err", "<measured text>"); exit 198 }`.
- **TR-26.3 dash_parse.mata.** `_expand_plottype_str` rows `("contour","contour") \ ("contourline","contourline")` -- order matters: `contourline` must be matched before `contour` would (the loop returns the first row whose minimum the name reaches and whose full name it begins: "contourline" begins "contour"? No: `substr("contour",1,11)` is "contour" ≠ "contourline"; "contour" against the contourline row: `substr("contourline",1,7) == "contour"` and `strlen("contour") >= strlen("contourline")` is false, so it does not match. Either order is safe; place `contour` first). `_dash_undrawn_plottype` tuple becomes `("sunflower")` (S21 left `("contour","contourline","sunflower")`). `_dash_extract_vars` keys (:2855): add `char(34)+"zvar"+char(34)+":"` after `"xvar"`. `_dash_computed_plot_cells` (:9514-9560): contour's cells are bounded by the surface (`min(n_unique, 1000)²` nodes at most) -- add both types to the types list `_dash_computed_cells` treats as bounded by `_dash_computed_plot_cells()`.
- **TR-26.4 renderer registration.** `_DASH_CONTOUR_TYPES = frozenset({"contour", "contourline"})` after `_DASH_RANGEPT_TYPES`; `_DASH_PLOT_VAR_KEYS` (:36470) gains `"zvar"`; `_DASH_COMPUTED_ONLY_TYPES` (:1884) gains both; `_dash_stale_kind` (:1913): `if t in _DASH_CONTOUR_TYPES: return "grid"` before the histogram line; `_dash_glyph_dispatch` `dispatch` gains `"contour": mapper.map_contour, "contourline": mapper.map_contourline`; `_dash_add_glyph` gains keyword `zvar=""` and, for the family, calls `fn(fig, source, yvar, xvar, options, view=view, color_idx=color_idx, zvar=zvar)` and includes `zvar` in `_vars_needed`; `_sync_brushed_copies`: skip a renderer with no `glyph`. `_make_figure_body`: `elif ptype.lower() in _DASH_CONTOUR_TYPES:` branch before the rangept branch, `pzvar = plot.get("zvar", "")`, `_frozen_vars = [pzvar, plot.get("yvar"), pxvar]`, `self._add_glyph(..., zvar=pzvar)`. Served `_dash_draw_layer`: the same branch using `_dash_layer_source(g_df, df, xvar, yvar, '', gname, _ln, _shared, _shared_pos, _fallback, extra_cols=_hv + [plot.get('zvar','')] + ...)` then `_dash_add_glyph(..., zvar=plot.get('zvar',''))`; the source collection loop (:49244-49251) also appends `getattr(_rr, '_dash_contour_sources', [])` for a ContourRenderer; `_hover_cols_of` tip list gains `'zvar'`. `_DASH_HORIZONTAL_TYPES`/`_DASH_VERTICAL_TYPES`: add both. `_dash_tag_hull_roles`: the ContourRenderer's extent is its `gx`/`gy` range -- give it the x and y roles by tagging the fill and line child renderers.
- **TR-26.5 the mappers** (after `map_rpspike`):
  ```python
  def map_contour(self, fig, source, yvar, xvar, options, view=None,
                  color_idx=0, zvar="", lines_only=False):
      x, y, z = GlyphMapper._masked(source, view, xvar, yvar, zvar)
      interp = _dash_contour_interp(options)                 # canonical word
      surf = _dash_contour_surface(x, y, z, interp)
      gx, gy, gz = surf["gx"], surf["gy"], surf["gz"]
      if _dash_is_horizontal_opts(options):                  # horizontal: swap roles
          gx, gy, gz = gy, gx, gz.T
      cuts = _dash_contour_cuts(options, surf["zmin"], surf["zmax"], zfmt=self._fmt_of(zvar))
      colours = _dash_contour_colours(options, len(cuts) + 1, self.scheme)
      labels = _dash_contour_labels(options, cuts, self._fmt_of(zvar))
      if surf["note"] == "degenerate" or gx.size < 2 or gy.size < 2:
          return self._mark_needs_points(_empty_contour(fig), "fewer than two distinct x or y values")
      if lines_only:
          cr = fig.contour(x=gx, y=gy, z=gz, levels=list(cuts),
                           line_color=_dash_contour_line_colours(options, colours, cuts, self.scheme),
                           line_width=_dash_contour_clwidths(options, len(cuts), self),
                           line_dash=_dash_contour_clpatterns(options, len(cuts), self))
      else:
          lo = min(surf["zmin"], cuts[0]) - 1.0; hi = max(surf["zmax"], cuts[-1]) + 1.0
          cr = fig.contour(x=gx, y=gy, z=gz, levels=[lo] + list(cuts) + [hi],
                           fill_color=colours)
      cr._dash_contour_sources = [cr.fill_renderer.data_source, cr.line_renderer.data_source]
      cr._dash_agg_source = cr.fill_renderer.data_source
      cr._dash_agg_config = {"type": "contour" if not lines_only else "contourline",
                             "xvar": xvar, "yvar": yvar, "zvar": zvar,
                             "cuts": [float(c) for c in cuts], "interp": interp,
                             "cap": _DASH_CONTOUR_EXACT_MAX, "capped": bool(surf["capped"]),
                             "horizontal": bool(_dash_is_horizontal_opts(options)),
                             "fill_color": list(colours) if not lines_only else [],
                             "lo": lo if not lines_only else None, "hi": hi if not lines_only else None}
      cr._dash_agg_rows = GlyphMapper._agg_member_ids(source, view)
      cr._dash_contour_capped = bool(surf["capped"])
      if surf["capped"]:
          _dash_note(_DASH_CONTOUR_CAP_NOTE % (surf["n_unique"], _DASH_CONTOUR_EXACT_MAX))
      if not lines_only and str(options.get("clegend", "")).strip().lower() != "off":
          cb = cr.construct_color_bar(title=_dash_contour_key_title(options, zvar, self))
          cb.major_label_overrides = {float(c): lab for c, lab in zip(cuts, labels)}
          if str(options.get("reversekey", "")).strip(): cb.levels = list(reversed(cb.levels))
          fig.add_layout(cb, _dash_clegend_side(options))
      return [cr]

  def map_contourline(self, fig, source, yvar, xvar, options, view=None, color_idx=0, zvar=""):
      return self.map_contour(fig, source, yvar, xvar, options, view=view,
                              color_idx=color_idx, zvar=zvar, lines_only=True)
  ```
  Module helpers (all on the copy list, R2): `_dash_contour_interp(options)` (canonical word of `interp()`, abbreviations per the fixture's `interp_abbrev`, default `thinplatespline`); `_dash_contour_cuts(options, zmin, zmax, zfmt)` (D-26d); `_dash_contour_colours(options, L, scheme)` (D-26e: `ccolors()` first, else `crule` with `scolor()`/`ecolor()` or the scheme's `contour_begin`/`contour_end` -- add `color contour_begin blue` and `color contour_end red` to dash-s2color.scheme and the other shipped schemes with Stata's values, read through `SchemeParser`); `_dash_contour_labels(options, cuts, zfmt)` (D-26f); `_dash_contour_line_colours(options, colours, cuts, scheme)` (contourline: `colorlines` pending, so a single line colour `scheme.default_color(0, "line")`; with `ccolors()` per-level colours); `_dash_contour_clwidths`/`_dash_contour_clpatterns` (vectors through `OptionTranslator.translate_lwidth`/the pattern translator, one per cut, the last repeated); `_dash_clegend_side(options)` (D-26g); `_dash_contour_key_title`; `_DASH_CONTOUR_CAP_NOTE` (D-26i text with two `%s`); `_dash_is_horizontal_opts(options)` (reads `horizontal`/`vertical`; a tiny wrapper of the existing `_dash_is_horizontal(plot)` logic on the options dict).
- **TR-26.6 readers.** `_dash_layer_axis_names`: for the family, x -> `("xvar",)`, y -> `("yvar",)` (horizontal swaps as `_dash_role_letter` does); `_dash_axis_vars`: unchanged (reads `xvar`/`yvar`); `_dash_layer_tick_format`: `xvar`'s/`yvar`'s own formats (the serset's columns); `_dash_layer_series`: `(L(y), L(x))` with the z label kept for the key; `_dash_hover_layer_vars`: `("xvar", "yvar", "zvar")`; `_dash_build_hover`: a `_contour` shape: fill renderer -> tooltip `[("z", "@lower_levels{0.00} to @upper_levels{0.00}")]`, line renderer -> `[("z", "@levels")]`, `mode="mouse"`; `_dash_legend_keys`: skip ContourRenderers.
- **TR-26.7 served registration.** `_dash_draw_layer`'s source loop gathers the ContourRenderer's two child sources (TR-26.4), so `agg_sources[(gname,pi)]['sources']` has them in `[fill, line]` order and `_dash_redraw_for` returns the fresh pair in the same order; `_dash_move_apply` step 3 copies data by position (dash_render.py:50195-50378), so no other change. The mapper must return the ContourRenderer only (so `fig.renderers[_before:]` holds `[cr]`) and expose the child sources on `_dash_contour_sources`.
- **TR-26.8 copy list (R2).** Functions after `_dash_contour_surface` (S23's last entry): `"_dash_contour_interp", "_dash_contour_cuts", "_dash_contour_colours", "_dash_contour_labels", "_dash_contour_line_colours", "_dash_contour_clwidths", "_dash_contour_clpatterns", "_dash_clegend_side", "_dash_contour_key_title", "_dash_is_horizontal_opts",`; constants after `_DASH_CONTOUR_INTERPS`: `"_DASH_CONTOUR_TYPES", "_DASH_CONTOUR_CAP_NOTE",`. The served header's bokeh import list (:48014-48035ff) needs no `ContourRenderer` import (`figure.contour` builds it); `ContourColorBar` is built by `construct_color_bar`.
- **TR-26.9 tests and maps.** function_test_map.py entries for `GlyphMapper.map_contour`, `map_contourline` and the ten helpers; program_coverage_map.py: none new (no new ado program; if the multiple-plot check becomes `_dash_contour_once`, add it with `test_parser.cscript:U26-9`). `_plot_for` and `plot_for`: `{"type": ptype, "zvar": "z"/"price", "yvar": "y"/"mpg", "xvar": "x"/"weight", "options": {}}`; test_horizontal.py:315 gains both; test_plottype_families.py asserts `_pt_contour == _DASH_CONTOUR_TYPES`; test_saved_stale_cue.py `_FROZEN` (:58) gains `"contour", "contourline"` with `_kind_of` returning `"grid"` (S29 flips them out within the cap); test_embedded_cells.py `TestTheTwoLanguagesAgree` (computed-only sets equal) follows TR-26.3.

## Boundaries

- No JavaScript: `_FILTER_JS`, `js_runner.py`, the `else if (ac.type === ...)` branches are S29's (S28 owns `_FILTER_JS` in batch 9).
- Do not edit S23's helpers; call them.
- Do not draw `heatmap`, `outlines`, `colorlines`, `phue` (named), `plegend()` for contourline, `xcuts/ycuts/xlevels/ylevels`.
- Do not edit `_dash_transpose_layer`, `_dash_layout_cell`, the appliers, `_dash_refinish_axes`.
- Scheme files: RGB names only (`color contour_begin blue`): no HSV in scheme files (M7).

## Stata truth

Extend `scripts/extract_contour_truth.do` (S23's script; a second block appended at its end, prefix `ZD_`, written to the same fixture under new top-level keys so S23's cases are untouched -- the fixture is regenerated whole, never hand-patched, R7). Probes on auto (`z=mpg y=weight x=length`) with `name()`:

| Key | Command | Recorded |
|---|---|---|
| `draw.default` | `twoway contour mpg weight length` | `.plotregion1.plot1.style.ccutsopt` (the cuts), `.style.levels.val`, `.style.cstyles[i].color.rgb` for i=1..L, `.zaxis1.major.tick_values`, the dserset `z y x levels` rows (`serset` dump as S23's `filled` rows), `.legend.keys` (0), the clegend's position/ring (`.clegend.position`, `.ring`) |
| `draw.ccuts` | `..., ccuts(15 20 25 30)` | cuts, levels, rgb per level, `zlabel` set |
| `draw.levels5`, `draw.levels5_minmax` | `..., levels(5)` / `levels(5) minmax` | cuts (expected 4 / 6), rgb |
| `draw.crule_<r>` for linear intensity hue chue phue | `..., crule(<r>) scolor(navy) ecolor(gold)` | rgb per level; rc for phue |
| `draw.ccolors` | `..., ccolors(red blue green)` | rgb per level (the last repeated) |
| `draw.clabels`, `draw.format` | `..., clabels(a b c d) ccuts(..)` / `format(%4.1f)` | `.style.labels[i]` (or the clegend's tick labels: `.clegend.<axis>.major.labels`) |
| `draw.interp_shepard`, `draw.interp_none` | | dserset rows |
| `draw.hz` | `..., horizontal` | `.plot1.bar_drop_to.stylename` and the dserset (x/y swapped) |
| `draw.clegend_off`, `draw.clegend_pos9`, `draw.clegend_width` | `clegend(off)` / `clegend(position(9))` / `clegend(width(20))` | presence, `.clegend.position`, `.clegend.width` |
| `line.default`, `line.ccuts`, `line.clwidths`, `line.clpatterns`, `line.reversekey` | `twoway contourline ...` | dserset rows, `.legend.keys` (= #cuts), `.style.lwstyles[i]`, `.style.lpstyles[i]` |
| `refuse.ccuts_levels`, `refuse.two_contours`, `refuse.two_lines`, `refuse.contour_and_line`, `refuse.string_z`, `refuse.weight`, `refuse.counts_1..4`, `refuse.option_on_scatter.<opt>` for ccuts crule scolor interp | each `capture noisily twoway ...` | rc, error line |
| `scheme.contour_begin`, `.contour_end`, `.zyx2rule` | `.Graph` class `.style.bshade.color.rgb`, `.eshade.color.rgb`, `.style.rule` | values (expected blue/red/hue) |

Truth block `* ==== S26 B4b: contour and contourline ====` in `test/test_wp31_truth.cscript` (U26 cases; a `python:` helper renders saved and served from `_dash_serve_spec`):
- **U26-1** `dash contour mpg weight length, name(u261)` registers with `zvar=mpg yvar=weight xvar=length`; both modes draw one ContourRenderer; `cr.levels[1:-1]` equal the fixture's `draw.default` cuts (rtol 1e-9); fill colours equal the fixture's rgb per level.
- **U26-2** polygons: for each level, the drawn `xs/ys` rings' area (shoelace, holes negative) equals the area of the fixture's dserset polygons of that level within 2% (twoway's compiled polygon cut and contourpy's differ in vertex placement; the level set is the same -- compared as area and as a 200×200 rasterised mask agreement >= 98%).
- **U26-3** `ccuts(15 20 25 30)`: `levels[1:-1] == [15,20,25,30]`; `levels(5)`: 4 cuts equal the fixture's; `levels(5) minmax`: 6.
- **U26-4** colours under each `crule` with `scolor(navy) ecolor(gold)` equal the fixture's rgb per level; `ccolors(red blue green)` repeats green.
- **U26-5** `clabels()`/`format()`: the ContourColorBar's `major_label_overrides` values equal the fixture's labels.
- **U26-6** contourline: one ContourRenderer with an empty fill source and `#cuts` line levels; `clwidths(thin medium thick)`/`clpatterns(solid dash dot)` give vectors; `reversekey` reverses the bar's levels.
- **U26-7** `horizontal`: the surface's x axis is weight's range.
- **U26-8** served refit: `_on_filter_change` to foreign==1 changes the fill source's `xs` and the recomputed cuts equal `dash contour ... if foreign==1`'s; saved: the layer is tagged frozen with kind `grid` and the status line is present.
- **U26-9** refusals (test_parser.cscript, same ids continue): `ccuts() levels()` together -> rc 198 and twoway's line; two contour plots -> rc 198 and twoway's line; string z -> twoway's rc/line; `dash contour mpg weight` -> rc 102 and twoway's line; `dash scatter mpg weight, ccuts(1 2)` -> rc 198 `option ccuts() not allowed` (S04's applicability table).
- **U26-10** cap: a 1001-point dataset -> the note text (D-26i) logged once; both modes draw a (100,100)-grid surface; the saved page tags the layer frozen.

## TDD test stubs

### Regression tests, `test/test_contour_layers.py` (new; red at the batch-9 base)

- Test: a `contour` spec draws one `ContourRenderer` with `#cuts+1` fill colours and `#cuts+2` levels in both modes -- `TestContourDraws::test_renderer_levels_and_colours[mode]` (red: "no glyph mapper for plot type 'contour'").
- Test: `contourline` draws lines only (empty fill source, `len(levels) == #cuts`) -- `TestContourlineDraws::test_lines_only[mode]` (red).
- Test: default cuts = `_dash_natscale_ticks(zmin, zmax, 7)[1:-1]`; `ccuts`, `levels(5)`, `levels(5) minmax` -- `TestCuts::test_each_rule` (red).
- Test: colours per rule vs fixture (`draw.crule_*`, `draw.ccolors`, `draw.default`) -- `TestColours::test_each_rule[rule]` (red).
- Test: labels from `clabels()`/`format()`/z's format -- `TestLabels::test_each_source` (red).
- Test: key placement by `clegend()`: right by default, left at 9, absent under off, width honoured -- `TestTheKey::test_placement[mode]` (red).
- Test: horizontal swaps axes -- `TestHorizontal::test_swapped[mode]` (red).
- Test: `interp(shepard)`/`interp(none)` reach the surface; `interp(bogus)` is refused upstream (dash.ado) and, in a hand-written spec, draws empty with the note -- `TestInterp::test_each[mode]` (red).
- Test: served redraw refits after a move; saved page marks `(grid unfiltered)` -- `TestMoves::test_served_refits`, `::test_saved_is_marked` (red).
- Test: above the cap: `capped`, note once, frozen in both saved builds -- `TestTheCap::test_note_and_frozen[mode]` (red).
- Test: `_sync_brushed_copies` tolerates a ContourRenderer -- `TestBrushedCopies::test_no_glyph_is_skipped` (red: AttributeError).
- Test: polygon level sets equal twoway's dserset polygons by area (2%) and raster mask (98%) on `draw.default`, `draw.ccuts`, `line.default` -- `TestAgainstTheFixture::test_level_sets[case]` (red).
- Test: `_dash_hover_layer_vars`, `_dash_layer_axis_names`, `_dash_layer_series` for the family -- `TestTheReaders::test_each` (red).
- Test: every new name on the copy list; served source defines it -- `TestServedCarries::test_names` (red).
- Test: scheme files hold `color contour_begin`/`contour_end` -- `TestScheme::test_stubs_present` (red).

### cscript cases: U26-1..U26-8, U26-10 (truth block); U26-9 (test_parser.cscript).

### Pinned tests to flip (R9)

- test_parser.cscript P1A-49, P1A-50 -> `dash contour mpg weight length, name(p1a49)` rc 0, a spec with `zvar`; P1A-51 keeps its prefix part (`cont`, `contou` unrecognised) and its multi-plot part now asserts rc 0. `Flipped: ... -- the refusal was dash's gap; twoway draws contour`.
- test_help_plot_types.py `_REFUSED` -> `("sunflower", "matamatrix")`; test_help_claims_1.py count -> two.
- test_saved_stale_cue.py `_FROZEN` gains both (a new pin S29 flips).
- test_mode_parity.py CORPUS: `_case("contour", [plot_for("contour")])`, `_case("contourline", ...)`, `_case("contour ccuts", [plot_for("contour", {"ccuts": "15 20 25"})])`, `_case("contour crule(linear)", ...)`, `_case("contour horizontal", ...)`, `_case("contourline clwidths", ...)`; MOVE_CORPUS: `_move_case("contour, dropdown to Foreign", _MOVES[0], [plot_for("contour")])` with the oracle `_saved_with_qualifier` (the Python re-run) -- the saved page's JS is S29's; `_MOVED_LAYERS` gains the two child sources; `_EMPTIED_LAYERS` (:2858) a contour emptied by a move draws an empty fill source.
- test_unsupported_report_is_true.py: new `LIVE_VALUES` entries for `ccuts levels crule scolor ecolor ccolors clabels interp clegend clwidths clpatterns` (two values that render differently), `PLOT_VALUES` for `heatmap outlines colorlines`; counts at :725-726 move with `# 196 -> <n>: WP-31 B4b <why>`.
- test_help_conformance.py: the Unsupported list gains the three pending names; `TestTheUnsupportedSectionIsTrue` both ways.
- dash.pkg "forty-two" -> "forty-four"; TWOWAY_COVERAGE_AUDIT.md:101-102 -> Drawn.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| registration, counts, refusals | cscript U26-9, test_parser flips | contour_truth.json refuse.* | n/a |
| cuts, colours, labels, key | pytest TestCuts/TestColours/TestLabels/TestTheKey; cscript U26-1,3,4,5 | contour_truth.json draw.* | yes |
| level sets vs twoway | pytest TestAgainstTheFixture; cscript U26-2 | filled/line/dserset rows | yes |
| served refit, saved mark | pytest TestMoves; cscript U26-8; MOVE_CORPUS | -- | yes |
| cap | pytest TestTheCap; cscript U26-10 | -- | yes |
| registry oracles | test_mode_parity Complete, every_plot_type_draws, plottype_families, help_plot_types, horizontal, stale_cue, embedded_cells | -- | n/a |

Acceptance: **AC-26.1** both types draw in both modes with twoway's cuts and colours; **AC-26.2** level sets match the dserset (area 2%, mask 98%); **AC-26.3** served refit, saved marked; **AC-26.4** cap noted and frozen; **AC-26.5** refusals in twoway's words; **AC-26.6** pending options named; **AC-26.7** one green commit.

## Tasks

**Commit boundary.** 26-01..26-04 = one commit `Draw contour and contourline with twoway's cuts, colours and key (WP-31 B4b)`.

<task type="auto" id="26-01">
  <name>Extend the extractor and write failing tests</name>
  <files>scripts/extract_contour_truth.do, test/test_contour_layers.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Append the ZD_ block to scripts/extract_contour_truth.do per "Stata truth" (every probe `capture noisily`, class values read after `graph display`/`name()`, dserset rows dumped with `serset set`/`serset use` as scripts/extract_stat_truth.do's method (2) describes at :26-33) and regenerate test/fixtures/contour_truth.json whole (`DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s26 $WT/scripts/extract_contour_truth.do`); S23's keys must be present and unchanged in meaning (`python3 -m pytest test/test_contour_interp.py -q -n0 -p no:cacheprovider` stays green). Create test/test_contour_layers.py with every stub; append the S26 block (U26-1..U26-8, U26-10) above the marker in test_wp31_truth.cscript and U26-9 to test_parser.cscript after S21's U21 cases. Run the pytest file (`tee <scratch>/26-01-failure.txt`) and the two cscripts through the driver (red), appending FAIL lines. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "no glyph mapper for plot type 'contour'\|FAILED" <scratch>/26-01-failure.txt` is at least 10; `python3 -c "import json;d=json.load(open('test/fixtures/contour_truth.json'));print(sorted(k for k in d if k in ('draw','line','refuse','scheme','cases','grid')))"` prints `['cases', 'draw', 'grid', 'line', 'refuse', 'scheme']`; test_contour_interp.py reports 0 failed.]]></verify>
  <done>The drawing truth was measured from twoway's class values and dsersets, and the contour layer tests failed against the batch-9 base with the text saved.</done>
</task>

<task type="auto" id="26-02">
  <name>Register the types and their options in Stata</name>
  <files>dash.ado, dash_parse.mata, dash-s2color.scheme</files>
  <action><![CDATA[Make TR-26.1, TR-26.2 and TR-26.3 (family, var-count branch with the fixture's `refuse.counts_*` words, vfields with `zvar`, option declarations, sreturns, JSON keys, pending lines, rule tokens and applicability rows, `clegend()` as a graph option in the seven lists and `_dash_rep_unique`, the ccuts+levels and multiple-plot refusals with the fixture's words, `_pt_nodraw` contour branch deleted, Supported line, Mata table rows, `_dash_undrawn_plottype` down to sunflower, `_dash_extract_vars` gains `zvar`, `_dash_computed_cells` bound). Add `color contour_begin blue` and `color contour_end red` to dash-s2color.scheme and to every other shipped `dash-*.scheme` with that scheme's Stata values (read from `/Applications/StataNow/ado/base/s/scheme-<name>.scheme`; s2color: :419-420). Run test_parser.cscript through the driver (U26-9 and the flipped P1A-49..51 PASS; U26-1.. still red until 26-03), then `python3 -m pytest test/test_abbreviations.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_embedded_cells.py -q -p no:cacheprovider` (the two test files' counts and entries updated per "Pinned tests to flip"; test_help_conformance needs 26-04's Unsupported lines -- make the Unsupported-list edit now).]]></action>
  <verify><![CDATA[`grep -c "U26-9 PASS\|P1A-49 PASS\|P1A-50 PASS\|P1A-51 PASS" <scratch>/s26/run_test_parser.log` prints 4; the pytest run reports 0 failed; `grep -c '"zvar"' dash_parse.mata` is at least 1; `grep -c "contour_begin" dash-s2color.scheme` prints 1; `grep -c '"contour", "contourline"' dash_parse.mata` prints 0 (the undrawn tuple no longer names them).]]></verify>
  <done>dash.ado parsed contour and contourline as three-variable layers with twoway's options, refusals and words, wrote zvar to the spec, and the schemes carried the contour colour stubs.</done>
</task>

<task type="auto" id="26-03">
  <name>Draw both types in both renderers</name>
  <files>dash_render.py, test/function_test_map.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Make TR-26.4 (set, var key, computed-only set, stale kind, dispatch, `_dash_add_glyph` zvar, brushed-copies skip, both figure-body branches, served source collection and hover columns, orientation tuples, hull roles), TR-26.5 (the two mappers and the ten helpers with the D-26d/D-26e/D-26f arithmetic and the D-26i note constant), TR-26.6 (readers, hover shape, legend skip), TR-26.7, TR-26.8 (copy-list entries) and TR-26.9's maps and test edits (`_plot_for`, `plot_for`, test_horizontal, test_plottype_families, `_FROZEN`, CORPUS/MOVE_CORPUS/_MOVED_LAYERS/_EMPTIED_LAYERS, `_REFUSED`, help-claims count). Run test_contour_layers.py, test_contour_interp.py, test_every_plot_type_draws.py, test_plottype_families.py, test_help_plot_types.py, test_horizontal.py, test_saved_stale_cue.py, test_server_layer_defects.py, test_function_test_map.py, test_glyphs.py, test_brushed_copies.py, `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "contour or Complete"`, and the S26 truth block through the driver (`WP31_ONLY=S26`).]]></action>
  <verify><![CDATA[Every run reports 0 failed; `grep -c "U26-\(1\|2\|3\|4\|5\|6\|7\|8\|10\) PASS" <scratch>/s26/run_test_wp31_truth.log` prints 9 and the log ends `ALL CHECKS PASSED`; `grep -c "def map_contour\|def map_contourline" dash_render.py` prints 2; `grep -c '"_dash_contour_cuts",' dash_render.py` prints 1.]]></verify>
  <done>contour and contourline were drawn through Bokeh's contour renderer in both modes with twoway's cuts, colours, labels and key, refit when served, marked when saved, and bounded above the cap.</done>
</task>

<task type="auto" id="26-04">
  <name>Document, close B4b and commit</name>
  <files>dash.sthlp, TWOWAY_COVERAGE_AUDIT.md, dash.pkg</files>
  <action><![CDATA[dash.sthlp: Plot types table gains a `{synopt:surface}{cmd:contour}, {cmd:contourline}{p_end}` line; the Not-drawn paragraph (S21's text) becomes `{ul:Not drawn.}  Two {cmd:twoway} plot types are not drawn by {cmd:dash}: {cmd:sunflower} ... and {cmd:matamatrix(}{it:name}{cmd:)} ...` keeping S21's advice sentences; add after S21's rpcap paragraph `{ul:contour and contourline.}  Three variables {it:z y x}. The surface is {cmd:twoway}'s: a thin-plate spline (kernel sqrt(x^2+y^2) with a linear trend) or Shepard's inverse-distance-squared weights over the distinct x by distinct y grid of the data, duplicates taking the smallest z, {opt interp(none)} drawing observed cells only; cuts from {opt ccuts()}, {opt levels(#)} with {opt minmax}, else the z-axis labels ({opt zlabel()}); colours from {opt crule()} between {opt scolor()} and {opt ecolor()} or from {opt ccolors()}; labels from {opt clabels()} and {opt format()}; the key by {opt clegend()}. {it:Difference from twoway:} the surface is exact up to 1,000 distinct points; above that a 100 x 100 grid over the data's range is drawn, a note says so, and the saved page does not recompute the layer after a filter move (the served app does). Polygons are cut by a different algorithm from {cmd:twoway}'s, so vertices differ while the level sets agree. {opt heatmap}, {opt outlines}, {opt colorlines} and {cmd:contourline}'s {opt plegend()} key are named in a note and not drawn; {opt crule(phue)} is drawn as {opt crule(hue)}.`; the Unsupported section (:4967-5136) gains `{phang2}{ul:Contour options.} {opt heatmap}, {opt outlines}, {opt colorlines} ...`; the Server Mode paragraph names contour among the layers served redraws. TWOWAY_COVERAGE_AUDIT.md:14, :24, :101-102 -> Drawn (WP-31 B4b); dash.pkg "forty-two" -> "forty-four" (and the pinned count test with `# 42 -> 44: WP-31 B4b`). Run `python3 -m pytest test/test_help_conformance.py test/test_help_plot_types.py test/test_help_claims_1.py test/test_version_floor.py test/test_tracking_documents.py -q -p no:cacheprovider`. Close BUGS.md "B4b" (Resolution naming map_contour/map_contourline, the helpers, both renderers, pinned by test/test_contour_layers.py::TestAgainstTheFixture::test_level_sets, test/test_wp31_truth.cscript U26-2; fixture test/fixtures/contour_truth.json; residual: the saved-page refit (B4c, section 29) and the cap), rewrite the B4 Tracked line (`Partly closed ... sections 23 and 26 ...; open: the saved-page refit (section 29)`), replace `<!-- WP-31 B4b -->` under `### Fixed in WP-31` with `- contour and contourline are drawn in both modes with twoway's surface, cuts, colours, labels and key; dash refused both by name r(198). Above 1,000 distinct points a 100 x 100 grid is drawn and noted. (WP-31, B4b)` and under `### Changed behaviour` with `- ccuts() with levels(), a second contour plot, a string z and contour options on other types are refused with twoway's words, r(198). (WP-31, B4b)`. Stage every changed file (dash.ado dash_parse.mata dash_render.py dash-*.scheme dash.sthlp TWOWAY_COVERAGE_AUDIT.md dash.pkg scripts/extract_contour_truth.do the test files BUGS.md GAPS3.md CHANGELOG.md) and `git add -f test/fixtures/contour_truth.json`; commit with BRIEF's body forms.]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -c "{ul:contour and contourline.}" dash.sthlp` prints 1; `grep -c '<!-- WP-31 B4b -->' CHANGELOG.md` prints 0; `git log -1 --format=%s` ends `(WP-31 B4b)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The help, audit and package described contour and contourline as drawn with their differences, and B4b was committed green with the B4 Tracked line partly closed.</done>
</task>

## Section completion criteria

- Both types register with `zvar`, draw in both modes with twoway's cuts, colours, labels and key; level sets match the dserset (area 2%, mask 98%).
- Served refit with no extra code; saved page marked `(grid unfiltered)`; cap noted and frozen.
- Refusals and pending options as D-26h; help/Unsupported/audit/pkg updated in the commit.
- U26-1..U26-10 PASS; P1A-49..51, `_REFUSED`, `_FROZEN`, counts flipped with reasons; one green commit.

## Notes

- **Renderer order.** The contour branch goes before the rangept and range branches in both `_make_figure_body` and `_dash_draw_layer`; the ContourRenderer is appended to `fig.renderers` by `figure.contour`, so `fig.renderers[_before:]` is `[cr]`.
- **`_dash_add_glyph`'s guard** checks `_check_vars(source, yvar, xvar, zvar)`.
- **Masked rows.** `GlyphMapper._masked(source, view, *cols)` drops rows where any of x, y, z is missing (twoway's `varlist(numeric)` keeps rows; the generator keeps missings but the Mata drops them -- `twoway__contour_gen.ado:11` "sic keep missings"); the fixture's `input.n_rows` vs `n_unique` shows the effect.
- **Bokeh 3.8 property set.** `ContourColorBar.major_label_overrides` exists in 3.8 (ColorBar property); no `*_outline_width`.
- **The default cut rule and `zlabel()`.** `zlabel(#5)` or a list replaces the `#7` ticks; the existing zlabel reader (:12047) returns rule/list; pass `(zmin, zmax)`.
- **python_exec hazard**: check `~/.stata19/console/stata19.rc` after each driver run.
- **Shared files (R1-R13).** R1: one S26 block; U26-9 in test_parser.cscript. R2: ten functions after `_dash_contour_surface`, two constants after `_DASH_CONTOUR_INTERPS`. R3: the Not-drawn paragraph (re-owned from S21), the new contour paragraph, the Unsupported contour lines, one Server Mode sentence. R4: two markers. R5: B4b entry; B4 Tracked line in the Partly-closed form. R6: `clegend` joins the seven key lists together; no new ado program unless the multiple-plot check is factored (then `version 19`, `_needed`, header index, coverage map). R7: the fixture regenerated whole. R8: corpus appended. R9: flips recorded. R10: unsupported counts and the forty-four pin. R12: S26 is batch 9's editor of `_make_figure_body`, `_generate_app_source` and `_dash_option_rules`.
- **For S29.** `_dash_agg_config` keys: `type xvar yvar zvar cuts interp cap capped horizontal fill_color lo hi`; `_dash_agg_source` is the fill source; the line source is `cr._dash_contour_sources[1]` -- S29 needs both on the page: register the line source as a second agg source entry with `type: "contourline_of"`, or hand both through one entry (`agg_sources[ai]` is the fill source; S29 adds `ac.line_source_index`). Recommendation to S29: in `DashRenderer.render()` step 3b (:46219-46237) register the ContourRenderer twice -- `(fill_src, cfg)` and `(line_src, dict(cfg, part="line"))` -- so the JS branch finds each by `ac.part`.
- **For S57.** Example `sysuse auto; dash contour mpg weight length, ccuts(15 20 25 30)`.
