# Section 21: rpcap and rpspike drawn; sunflower and matamatrix refused by name

> Part of: WP-31 · GAPS3 rows: B1, B2, B3 · Risk: yellow · Batch: 7 · Depends on: 01 · Blocks: 57 · Tasks: 4, 3 commits · Case-id prefix: U21

## Overview

**What is wrong today.** GAPS3 B1 (GAPS3.md:110): "`rpcap`, `rpspike` refused by name r(198) with advice." dash.ado:4889-4900 answers `dash rpcap y ylow yhigh x` with `dash: 'rpcap' is a twoway plot type dash does not draw: it marks a point on a range. Use Stata's own twoway rpcap, or draw the two together: dash (rcap ylow yhigh x) (scatter y x).` and `exit(198)`; test_parser.cscript P1A-59 (:598-623) pins exactly that. twoway draws both since Stata 19 (`twoway_rpcap_parse.class:12` inherits `twoway_y3xview_parse`; research/stata-ground-truth.md §2). GAPS3 B2 (:111): "`sunflower` falls to the generic 'unrecognised plot type'; absent from the help's Not-drawn list" -- `dash sunflower mpg weight` is answered `dash: unrecognised plot type 'sunflower'.` plus the `Supported:` list (dash.ado:4901-4909), as if twoway had no such type. GAPS3 B3 (:112): "`matamatrix()` is read as a varlist and refused r(101)/r(111)" -- `dash scatter matamatrix(M)` reaches `_dash_parse_varpart_std` and is refused as a variable not found, naming `matamatrix(M)` as if it were a variable.

**After this section** `dash rpcap y1 y2 y3 x` and `dash rpspike y1 y2 y3 x` are parsed as twoway parses them (exactly four numeric variables, `y3xview_parse:34-51`), written to the spec as a range layer plus the marker variable, and drawn in both renderers: a spike from (x, y1) to (x, y2), caps of total width equal to the marker size at both ends (rpcap only), and a marker at (x, y3) in the layer's marker style; the y axis ranges over all three y variables; the legend key is the cap or spike line with the marker; `horizontal` swaps the axes. `sunflower` and `matamatrix()` are refused by name, r(198), with a measured sentence of advice each, and the help's "Not drawn" paragraph names four types (contour, contourline, sunflower, matamatrix) until S26 reduces it to two (rpcap and rpspike are drawn by S21 itself). Because S26 (batch 9) removes contour and contourline from the refused set later, this section edits the paragraph to the four names and S26 edits it down to two: the paragraph is owned by S21 in batch 7 and S26 in batch 9 (R3 table, index).

**Why these rows share this section.** All three are plot-type registration work in the same four places (`_dash_plottype_families`, `_dash_undrawn_plottype`, the var-count branch, the renderer's type sets) and the same tests (test_every_plot_type_draws, test_mode_parity `TestTheCorpusIsComplete`, test_help_plot_types `_REFUSED`, test_parser.cscript P1A-59). S21 is batch 7's plot-type registration owner (index batch table); S20 (map_scatter size path) and S22 (`_FILTER_JS`) touch none of these.

**Test order and commit rule (rule 7, BRIEF).** Three cycles, three commits `(WP-31 B1)`, `(WP-31 B2)`, `(WP-31 B3)`. 21-01 writes B1's failing tests and the extractor, runs them against the unmodified tree, saves `<scratch>/21-01-failure.txt`, never commits. 21-02 makes B1 true in dash.ado, dash_parse.mata and dash_render.py, flips P1A-59 and the `_REFUSED` tuple, appends the parity cases, and commits B1 (21-01 appended B1's truth block, the section's first row). 21-03 does B2 and B3 as two commits (their failing tests are written against the tree B1's commit leaves); each row's closing step appends its own truth block (`* ==== S21 B2: ... ====`, `* ==== S21 B3: ... ====`) and its own regression test file (DECISIONS A14). 21-04 updates the help, TWOWAY_COVERAGE_AUDIT.md and dash.pkg and is folded into B3's commit. No test-only commit exists. Every Tracked line is written with `commit pending`; the merger's step k.3b fills the sha (DECISIONS A11).

### Section decisions (binding on the executor)

- **D-21a. No new spec keys.** rpcap/rpspike are written with `yvar1` (y1, the spike's first end), `yvar2` (y2, the other end), `yvar` (y3, the marker) and `xvar`. `_dash_extract_vars` (dash_parse.mata:2855-2857) and `_DASH_PLOT_VAR_KEYS` (dash_render.py:36470) already list all four, so the data JSON carries them and the served placeholder names them without a list change (research/codebase-mechanics.md §2: "rpcap/rpspike ... can reuse yvar + yvar1 + yvar2 + xvar").
- **D-21b. A new routing family `_pt_rangept` ("rpcap rpspike") in dash.ado, and a renderer set `_DASH_RANGEPT_TYPES`.** The two types are not added to `_pt_range`: that family's branch demands exactly three variables and test_plottype_families.py pins `_pt_range == _DASH_RANGE_TYPES`. The new family is routed by the range branch's machinery (`_dash_parse_varpart_4v`, which the pc branch already uses) with twoway's words for the count: one variable `too few variables specified` r(102); two or three `rpcap requires 4 variables: <vl>` r(102); five or more the same words r(103) -- the same pattern the pc branch uses (dash.ado:5038-5059), the sentence measured by the extractor (research/stata-ground-truth.md §2: "you must specify four variables with twoway rpcap" needs measurement; the extractor records twoway's exact text and dash prints that text).
- **D-21c. The mappers are compositions, not copies.** `map_rpcap` calls `self.map_rcap(fig, source, y1var, y2var, xvar, options, view=, color_idx=)` and then `self.map_scatter(fig, source, y3var, xvar, options, view=, color_idx=, colorvar_key=False)`; `map_rpspike` calls `map_rspike` then `map_scatter`. Nothing in map_rcap/map_rspike/map_scatter is edited (S20 owns map_scatter's size path this batch; R12). The cap width is already the marker size (WP-30 P1.17a: `size=self.scheme.default_marker_size(color_idx)` and `msize()` through `_apply_marker_opts`, dash_render.py:18737-18762), so `msize()` sizes caps and marker together, as twoway's help says ("msize() sets the cap width and the size of the marker symbol", `twoway_rpcap.sthlp:114-115`).
- **D-21d. Legend key.** One legend entry for the layer: `legend_label` of the spike is `y1var` (map_rcap/map_rspike set it); the marker is added to the same legend item by giving it the same `legend_label` through `_dash_legend_entries` (it groups renderers by key text, dash_render.py:39970). twoway's key is `draw_rcap_only` + `draw_scatter` (`y3xkey_g.class:124-150`); Bokeh draws a composite key from both renderers of one item.
- **D-21e. Axis title.** `_dash_layer_series` (dash_render.py:39826) gets a `_DASH_RANGEPT_TYPES` branch: the y label is `L(y1)/L(y2)/L(y3)` when the three labels differ, else the shared label (`y3xview_g.class:122-164`); `_dash_layer_axis_names(plot, "yvar")` returns `("yvar1", "yvar2", "yvar")` for the family so the y axis ranges and is formatted over all three (dash_render.py:1252-1285; `y3xview_g.class:79-99`).
- **D-21f. sunflower and matamatrix refusals.** `_dash_undrawn_plottype` keeps `contour contourline rpcap rpspike` out (rpcap/rpspike leave in B1; contour/contourline leave in S26) and gains `sunflower`. `matamatrix(` is detected before the plot-type lookup: a varpart whose first token begins `matamatrix(` (case-insensitive, as `yxview_parse:152-182` detects it) is refused by name on every type. The advice sentences are measured from Stata's own help text (`twoway_sunflower.sthlp:35-39`, `twoway_mata.sthlp:13`) by the extractor and quoted in dash.ado verbatim: rpcap's branch pattern at dash.ado:4891-4899 is reused. Twoway's own text for `sunflower` is rc 0 (it draws), so no twoway rc is matched; the refusal is dash's own with the manual's words.

## Risk: [yellow] -- a new routing family touches dash.ado's segment parser, five renderer type lists and six test oracles

**Why.** A plot type is registered in nine places on the Stata side and the renderer (research/codebase-mechanics.md §2 "Every file rpcap or contour must touch"); `TestTheCorpusIsComplete` fails on any one of them missing. The var-count branch is in `_dash_process_segment`, the parser's spine.

**Risk factors.**
1. Spec-key reuse: a renderer path reading `yvar` on a layer that also has `yvar1`/`yvar2` (hover, axis vars, tick format, series labels, hull roles) may pick the wrong role.
2. The served `_dash_draw_layer` has a range branch keyed on `_DASH_RANGE_TYPES` (dash_render.py:49190); the new family needs its own branch there and in `_make_figure_body` (:43995-44001), with `_dash_range_source` carrying `yvar` as an extra column.
3. test_horizontal.py and `_DASH_HORIZONTAL_TYPES`/`_DASH_VERTICAL_TYPES` (:31835-31846): rpcap/rpspike take `horizontal`/`vertical` (`y3xview_parse:57`), and `_dash_transpose_layer` must rotate the composed renderers (caps are tagged `dash_cap`, so S49's transpose already rotates them).
4. The help's Not-drawn paragraph is edited by S21 (batch 7) and S26 (batch 9): sequential, not concurrent.
5. P1A-59 flips: the cscript asserts the refusal text; after B1 it must assert a registered spec.

**Mitigation.**
1. TR-21.6 names every reader that keys on the family and gives each its branch; `test_rangept_layers.py::TestTheReaders` pins each.
2. `extra_cols=[plot['yvar']]` on the range-source call (TR-21.5) and a parity entry per type.
3. TR-21.7 adds both names to both orientation tuples and dash.ado's `_hz_htypes`/`_hz_vtypes`; test_horizontal.py's `_RANGE` set (:315) gains them.
4. R3: this file owns the paragraph in batch 7; S26's file re-owns it in batch 9.
5. Flipped in place with a `Flipped:` line (R9).

## Dependencies

- **Depends on: 01** (tracking foundation: BUGS.md entries B1-B3, the GAPS3 Tracked lines, the CHANGELOG markers, `test_wp31_truth.cscript` block `// 70.`).
- **Blocks: 57** (examples: an rpcap example page).
- **Parallel batch: 7**, merge order S22, S20, S21. **Can run with S20 and S22**: S20 edits `map_scatter`'s size path (called, not edited, here); S22 edits `_FILTER_JS` and `_dash_stale_kind` (not touched here: rpcap/rpspike are row layers, never computed, so no stale cue and no JS branch).

## Evidence

All anchors at `6370ca4`.

### The refusal today

dash.ado:4889-4900:
```
        mata: st_local("_pt_nodraw", _dash_undrawn_plottype(st_local("plottype")))
        if "`_pt_nodraw'" != "" {
            if "`_pt_nodraw'" == "contour" | "`_pt_nodraw'" == "contourline" {
                local _pt_why "it needs a surface interpolated over a grid. ..."
            }
            else {
                local _pt_rng = cond("`_pt_nodraw'" == "rpcap", "rcap", "rspike")
                local _pt_why "it marks a point on a range. Use Stata's own twoway `_pt_nodraw', or draw the two together: dash (`_pt_rng' ylow yhigh x) (scatter y x)."
            }
            mata: _dash_say("err", "dash: '", st_local("plottype"), "' is a twoway plot type dash does not draw: " + st_local("_pt_why"))
            exit(198)
        }
```
dash_parse.mata:1802-1810: `if (anyof(("contour", "contourline", "rpcap", "rpspike"), s)) return(s)`. The families: dash.ado:4516-4529 (`_pt_range "rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline"`, `_pt_pc "pcspike pcarrow pcbarrow pcscatter pccapsym"`). The pc var-count branch (:5038-5059) is the pattern for four variables. The JSON vfields (:5792-5830) write `yvar1,yvar2,xvar` for `_pt_range` and `yvar,xvar` for the default.

### The renderer

`_DASH_RANGE_TYPES` (dash_render.py:25958), `_DASH_PC_TYPES` (:25967), `_dash_glyph_dispatch` (:41883-41935; `range_dispatch` :41920-41930), `_dash_add_glyph` (:42344-42404: range types take `(fig, source, y1, y2, x, options, view=, color_idx=)`), `_make_figure_body` range branch (:43995-44001), served `_dash_draw_layer` range branch (:49190-49211, `_dash_range_source(g_df, y1var, y2var, xvar, mlabel, extra_cols=...)` :39481). `map_rcap` (:18693-18762) draws spine + two `dash` markers sized `default_marker_size(color_idx)`, `msize()` through `_apply_marker_opts`; `map_rspike` (:18650-18691) one Segment; `map_scatter` (:14865, signature `(fig, source, yvar, xvar, options, view=None, color_idx=0, colorvar_key=True)`). Readers keyed on the family: `_dash_layer_axis_names` (:1252), `_dash_axis_vars` (:1288), `_dash_layer_tick_format` (:1358; `ptype in _DASH_RANGE_TYPES` at :1404), `_dash_layer_series` (:39826; :39874), `_dash_hover_layer_vars` (:40053), `_DASH_HORIZONTAL_TYPES`/`_DASH_VERTICAL_TYPES` (:31835-31846).

### Stata's rule (research/stata-ground-truth.md §2)

Roles var1 = `yvar`, var2 = `.y2var`, var3 = `.y3var`, var4 = x (`y3xview_parse:87-102`). Drawing (`yxview_rpcap_draw.ado:14-33`, read at 6370ca4): `gdi line x y1 x y2`, then at each end `gm_rmoveto -sz/2 0; gm_rlineto sz 0` with `sz = .style.marker.size.gmval`; then `._draw_points` with `.yvar` set to `.y3var` (:61-77). rpspike identical without caps. Horizontal swaps dims (:39-58). Legend key `y3xkey_g.class:124-150`. y range over the three y vars (`y3xview_g.class:79-99`). Axis title `label(y1)/label(y2)/label(y3)` when they differ (`y3xview_g.class:122-164`). sunflower (§4): `twoway_sunflower.sthlp:35-39` "twoway sunflower is a special type of twoway graph. We recommend the sunflower command over twoway sunflower". matamatrix (§4): `twoway_mata.sthlp:13` "[G-2] twoway mata -- Two-way graphs of mata matrices"; `yxview_parse:152-182` detects the `matamatrix(` prefix.

### Tests that pin today's behaviour (flip, never delete)

- test/test_parser.cscript P1A-59 (:598-623): rpcap/rpspike refused r(198) with the advice; `rpca`/`rpspik` "unrecognised plot type".
- test/test_help_plot_types.py:28 `_REFUSED = ("contour", "contourline", "rpcap", "rpspike")` and `test_the_types_dash_refuses_are_named_as_not_drawn`, `test_dash_ado_refuses_them_by_name`.
- test/test_help_claims_1.py `TestThePlotTypesSection::test_it_says_four_types_are_refused_and_so_does_item_5` (function_test_map.py:599 names it): "four" becomes "six" after B2/B3 (S26 later makes it "two").
- TWOWAY_COVERAGE_AUDIT.md:14-15, :24, :101-104; dash.pkg:5 "forty twoway plot types" (the count measured at the section's base, plus two; "forty" at `6370ca4`).
- test/test_parser.cscript P1A-56 ("all 40 plot types are routed by family lists") -- the count line, if asserted, moves by two from the value measured at the base, with `// <measured old> -> <measured old + 2>: WP-31 B1 rpcap and rpspike drawn` (R10, A33).

## User stories

- **US-21.1** As a Stata user pasting `twoway rpcap y1 y2 y3 x` into dash, I want the range, its caps and the point drawn as twoway draws them so that my do-file runs unchanged.
- **US-21.2** As the same user, I want `rpspike` drawn the same way without caps.
- **US-21.3** As a user with `twoway sunflower` or `matamatrix()` in a do-file, I want dash to tell me by name that it does not draw them and what to use so that I am not told my plot type is "unrecognised" or my matrix "not found".
- **US-21.4** As a dashboard viewer, I want a filter move to keep the spike, caps and marker of the kept rows in both the saved page and the served app.

## Business requirements

- **BR-21.1** `dash rpcap y1 y2 y3 x` and `dash rpspike y1 y2 y3 x` register and draw; any other variable count is refused with twoway's return code and words.
- **BR-21.2** rpcap draws a spike from y1 to y2 at x with caps as wide as the marker, and a marker at y3; rpspike the same without caps; `msize()` sizes caps and marker together; `horizontal` turns the layer.
- **BR-21.3** The y axis spans min/max over y1, y2, y3; its title is the three labels joined with `/` when they differ.
- **BR-21.4** One legend key per layer, showing the spike (with caps for rpcap) and the marker.
- **BR-21.5** `sunflower` and `matamatrix()` are refused r(198) with a sentence naming the type and the advice; the help lists them under Not drawn.
- **BR-21.6** Both renderers draw the same picture before and after a filter move.

## Technical requirements

- **TR-21.1 dash.ado families.** In `_dash_plottype_families` (:4516-4529) add after the `_pt_pc` line: `c_local _pt_rangept "rpcap rpspike"` with a header-comment line `//   _pt_rangept  y1 y2 y3 x                      rpcap rpspike`.
- **TR-21.2 dash.ado var-count branch.** In `_dash_process_segment`, after the `_pt_pc` branch (:5038-5059) and before `_pt_literal` (:5060), add:
  ```
  else if `: list ptype in _pt_rangept' {
      _dash_parse_varpart_4v `macval(varpart)'
      local vl = "`s(varlist)'"
      local nv : word count `vl'
      if `nv' != 4 {
          if `nv' == 1 {
              display as error "too few variables specified"
              exit 102
          }
          mata: _dash_say("err", "`ptype' requires 4 variables: ", st_local("vl"), "")
          exit cond(`nv' < 4, 102, 103)
      }
      local yvar1 = word("`vl'", 1)
      local yvar2 = word("`vl'", 2)
      local yvar  = word("`vl'", 3)
      local xvar  = word("`vl'", 4)
      mata: st_local("if_cl", st_global("s(if_clause)"))
      mata: st_local("in_cl", st_global("s(in_clause)"))
  }
  ```
  The two sentences are replaced by the extractor's measured text (Stata truth) if twoway's differ; the rc pattern (102 below, 103 above) is the measured one for every 4-variable type (:5041-5043 comment). In the vfields block (:5792-5830) add after the `_pt_range` branch: `else if `: list ptype in _pt_rangept' { ... local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","yvar":"`_jyv'","xvar":"`_jxv'""' }` with the four `_dash_json_str` calls. `_seg_xv` (:5761-5765) already falls to `xvar` for the family. Add `rpcap rpspike` to `mv_range` (:2132), `_so_ser` (:2471), `_rng` (:2586; recast class y2xtype) with `_sp_rng` spellings `rpcap:5 rpspike:7` (twoway takes no abbreviation: P1A-59's measurement), `_hz_htypes` and `_hz_vtypes` (:2301-2302), `_ts_sortx` (:5671); not to `jit_undrawn` (:2218: jitter on the marker is drawn by map_scatter), not to `_pt_nots`, `_cap_types` (barwidth() on rpcap: twoway's answer is measured by the extractor; if r(198), add both names to `_cap_types` :5567). **Weights (R2-32).** twoway's y3xview draws the y3 marker through `_draw_points`, which S20 (batch 7, merged before S21) shows is sized by `[aw fw pw]`; the extractor's `draw.rpcap_weight` probe (`twoway rpcap lo hi turn weight [aw=price]`) records whether the marker radii vary with the weight. If they do, 21-02 registers the two names: in dash.ado a new line directly after `_wt_honoured`'s line (:5367, S20's hunk) `local _wt_honoured "`_wt_honoured' rpcap rpspike"  // WP-31 B1: the y3 marker is sized by the weight (y3xview _draw_points)`, and in dash_render.py a statement after the `_DASH_WEIGHT_ACCEPTS` literal (:397-409, S20's hunk) `_DASH_WEIGHT_ACCEPTS.update({"rpcap": ("aw", "fw", "pw"), "rpspike": ("aw", "fw", "pw")})` -- new lines, not edits of S20's, so the two worktrees' patches apply in merge order S20 then S21. S20 owns the weighted-marker machinery (`_marker_weights`, `_dash_weighted_sizes`, `map_scatter`'s size field, present on the merged tree); S21 only registers the two names, and its own test pins the registration (`TestWeightRegistered::test_names_listed`), while the sized marker is asserted on the merged tree by the parity corpus (`_case("rpcap aweight", [plot_for("rpcap", {"weight": "aweight", "wexp": "price"})])`) at the batch's G2. If the radii do not vary, neither name is registered and the probe's record says so. Remove `rpcap rpspike` from the refusal comment and the `else` branch at :4895-4898 (the branch now serves no name until S26 removes the whole block; leave the contour branch as is). Supported list (:4901-4909): add `rpcap rpspike` to the last line.
- **TR-21.3 dash_parse.mata.** `_expand_plottype_str` table (:1703-1742): append `("rpcap","rpcap") \ ("rpspike","rpspike")` after `("pcarrowi","pcarrowi")` (full names only, measured 23sep2026 P1A-59). `_dash_undrawn_plottype` (:1802-1810): the tuple becomes `("contour", "contourline", "sunflower")` after B2 (B1 removes two names, B2 adds one); update the 2b header comment (:1790-1801) to name sunflower and matamatrix. New function `_dash_matamatrix_typed(string scalar varpart)` returning the `matamatrix(...)` token as typed (through `_dash_rep_toks`/`_dash_rep_optname`, the `_dash_barwidth_typed` pattern at :6514-6528) or `""`; add to the header index and to `_dash_require_mata`'s `_needed` (dash.ado:448-479) in alphabetical place.
- **TR-21.4 dash.ado refusals (B2, B3).** Before the `_dash_undrawn_plottype` call (:4889) add the matamatrix check: `mata: st_local("_pt_mm", _dash_matamatrix_typed(st_local("varpart")))` / `if "`_pt_mm'" != "" { mata: _dash_say("err", "dash: ", st_local("_pt_mm"), " is a twoway mata matrix plot, which dash does not draw. Use Stata's own twoway " + st_local("plottype") + " matamatrix(), or getmata the columns into variables and draw them: dash " + st_local("plottype") + " y x."); exit(198) }`. In the `_pt_nodraw` block add `else if "`_pt_nodraw'" == "sunflower" { local _pt_why "it bins points into density petals. Use Stata's own sunflower command, which Stata recommends over twoway sunflower, or dash scatter y x with jitter() or colorvar()." }`. The exact two sentences are fixed here (D-21f); the extractor records the manual's lines they paraphrase.
- **TR-21.5 renderer registration.** After `_DASH_PC_TYPES` (:25967) add `_DASH_RANGEPT_TYPES = frozenset({"rpcap", "rpspike"})` with a comment. `_dash_glyph_dispatch` `range_dispatch` (:41920-41930): add `"rpcap": mapper.map_rpcap, "rpspike": mapper.map_rpspike,` after `"rscatter"`. `_dash_add_glyph` (:42344): the range call passes `y2var`; y3 travels as a keyword, not as a spec option (D-21a: no new spec key). Change the range call to `rfn(fig, source, yvar, y2var, xvar, options, view=view, color_idx=color_idx, **_jkw)` unchanged, and add before it: `if pt in _DASH_RANGEPT_TYPES: _jkw["y3var"] = y3var` where `_dash_add_glyph` gains a keyword `y3var=""`. `_make_figure_body` (:43995-44001): add an `elif ptype.lower() in _DASH_RANGEPT_TYPES:` branch before the `_RANGE_TYPES` one, reading `plot.get("yvar1")`, `plot.get("yvar2")`, `plot.get("yvar")` and calling `self._add_glyph(..., y2var=py2var, y3var=py3var, ...)` (`_add_glyph` forwards `**kw`). Served `_dash_draw_layer` (:49190-49211): add the same branch before the `_DASH_RANGE_TYPES` branch, calling `_dash_range_source(g_df, y1var, y2var, xvar, opts.get('mlabel',''), extra_cols=_hv + [yvar] + _dash_option_columns(opts, df.columns), ...)` so the marker's column rides along, then `_dash_add_glyph(..., y2var=y2var, y3var=yvar, ...)`. `_hover_cols_of` (:49259) already lists `yvar yvar1 yvar2`.
- **TR-21.6 the mappers.** In `GlyphMapper`, after `map_rcapsym` (:19094-19214) add:
  ```python
  def map_rpcap(self, fig, source, y1var, y2var, xvar, options, view=None,
                color_idx=0, y3var=""):
      """rpcap: map_rcap's spike and caps, then the marker at y3 (WP-31 B1)."""
      rs = self.map_rcap(fig, source, y1var, y2var, xvar, options,
                         view=view, color_idx=color_idx)
      pt = self.map_scatter(fig, source, y3var, xvar, options, view=view,
                            color_idx=color_idx, colorvar_key=False)
      pt.tags = list(getattr(pt, "tags", [])) + ["dash_rangept_marker"]
      return list(rs) + [pt]
  ```
  and `map_rpspike` the same over `map_rspike`. No glyph property of `pt` is edited. The marker's `legend_label` is set by map_scatter to `y3var` and read by `_dash_legend_keys`; TR-21.6a: in `_dash_legend_keys` (the pairs builder `_dash_legend_entries` reads, :39970), a renderer tagged `dash_rangept_marker` joins the key of the preceding renderer of the same layer (D-21d). Readers (D-21e): `_dash_layer_axis_names` (:1278-1282): `elif ptype in _DASH_RANGE_TYPES | _DASH_RANGEPT_TYPES and letter == "y": keys = ("yvar1", "yvar2") + (("yvar",) if ptype in _DASH_RANGEPT_TYPES else ())`; `_dash_layer_tick_format` (:1404) and `_dash_layer_series` (:39874): treat the family as range, with the series label `L(y1)/L(y2)/L(y3)` (collapse equal labels); `_dash_hover_layer_vars` (:40053): keys `("xvar", "yvar1", "yvar2", "yvar")` for the family; `_DASH_HORIZONTAL_TYPES` and `_DASH_VERTICAL_TYPES` (:31835-31846): add both names after `"rscatter"`; `_dash_tag_hull_roles` (called at :44032): the marker renderer takes the y role.
- **TR-21.7 tests and maps.** function_test_map.py: `'GlyphMapper.map_rpcap': 'test/test_rangept_layers.py::TestRpcapDraws::test_spike_caps_and_marker[saved]'`, `'GlyphMapper.map_rpspike': 'test/test_rangept_layers.py::TestRpspikeDraws::test_spike_and_marker[saved]'`. program_coverage_map.py: `"_dash_matamatrix_typed": ("test_wp31_truth.cscript:U21-10",)`. test_every_plot_type_draws.py `_plot_for` (:181): a `_pt_rangept` branch returning `{"type": ptype, "yvar1": "lo", "yvar2": "hi", "yvar": "y", "xvar": "x", "options": {}}`; test_server_layer_defects.py `plot_for` (:80): `_RANGEPT = {"rpcap", "rpspike"}` branch `{"type": ptype, "yvar1": "mpg", "yvar2": "price", "yvar": "foreign", "xvar": "weight", "options": o}`; test_horizontal.py:315 list gains both; test_plottype_families.py: `assert set(fams["_pt_rangept"]) == set(dr._DASH_RANGEPT_TYPES)` and the routing-order tuple gains `"_pt_rangept"`.
- **TR-21.8 served copy list (R2).** `_DASH_RANGEPT_TYPES` is appended to the constants tuple after `_DASH_STALE_STATUS_HTML` (dash_render.py:46584-46784 region); no new module function (the mappers are class methods, copied whole). Guard: `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`.

## Boundaries

- Do not edit `map_rcap`, `map_rspike`, `map_scatter`, `_apply_marker_opts` (S20 owns the size path in batch 7), `_FILTER_JS`, `_dash_stale_kind`, `js_runner.py` (S22), `_dash_option_rules` (S05/S06 landed; no rule change needed), `_dash_transpose_layer`.
- Do not add `zvar` or touch contour/contourline anywhere (S23/S26/S29). The `_pt_nodraw` block keeps its contour branch; S26 deletes it.
- Do not draw sunflower or read `matamatrix()` by value (PRD §7).
- Do not touch `_DASH_RANGE_TYPES` membership or `_pt_range`.

## Stata truth

Extract script `scripts/extract_rangept_truth.do` (new; the `extract_default_base_truth.do` header pattern: DASH_REPO guards, `adopath ++`, load mata and ado, `global dash_nobrowser 1`, `shell git -C ... rev-parse HEAD > git_head.txt`, python block reads it through `Macro.getLocal`/`Macro.getGlobal`, `_meta` with `stata_version born_date dash_commit extracted source`, `sort_keys`). Probes, on `sysuse auto` with `local y1 = turn - 5`, `y2 = turn + 5`, y3 = `turn`, x = `weight` (generated variables `lo hi`):

| Key | Command | Recorded |
|---|---|---|
| `counts.rpcap_1`..`_5`, `counts.rpspike_*` | `capture noisily twoway rpcap <1..5 vars>` | `rc`, the error line (logged at linesize 255, as test_parser's `_p1a_logrun`) |
| `draw.rpcap` | `twoway rpcap lo hi turn weight, name(t1)` | `.t1.plotregion1.plot1.style.marker.size.gmval` (cap width = marker size), the serset's `N`, the four variable names and roles (`.plot1.yvar .y2var .y3var .xvar`), `.yaxis1.major.min/max`, `.yaxis1.title.text`, legend key count `.legend.keys` |
| `draw.rpcap_msize` | `..., msize(large)` | `marker.size.gmval` |
| `draw.rpcap_hz` | `..., horizontal` | `.plot1.bar_drop_to.stylename` ("y") |
| `draw.rpcap_weight` | `twoway rpcap lo hi turn weight [aw=price], name(tw)` | rc, `.tw.plotregion1.plot1.wvar`, the marker radii from the exported SVG (S20's W01 method) and whether they vary with price (feeds the R2-32 registration in TR-21.2) |
| `draw.rpspike` | `twoway rpspike lo hi turn weight` | the same fields |
| `title.differs` / `title.same` | with/without `label variable` on lo hi | `.yaxis1.title.text` |
| `barwidth.rpcap` | `twoway rpcap ..., barwidth(.5)` | rc and line (feeds `_cap_types`) |
| `advice.sunflower` | none (reads `twoway_sunflower.sthlp` lines 35-39 via `file read`) | the two sentences |
| `advice.matamatrix` | `twoway scatter matamatrix(nosuch)` | rc and twoway's line ("nosuch is not a mata matrix") |

Run: `DASH_REPO=<wt> scripts/stata_slot.sh <scratch> <wt>/scripts/extract_rangept_truth.do` -> `test/fixtures/rangept_truth.json`; `git add -f`; named by `test_rangept_layers.py::TestTheFixture`.

Truth blocks in `test/test_wp31_truth.cscript`: one per row (DECISIONS A14), each above the marker line, after the last `* ==== end S<NN> ====`, with `local only : env WP31_ONLY`, `if inlist("\`only'", "", "S21") & \`: list posof "S21" in w31_run' {`, start/end display lines. B1's block `* ==== S21 B1: rpcap and rpspike ====` (U21-1..U21-7, appended by 21-01), B2's `* ==== S21 B2: sunflower refused ====` (U21-9, appended by 21-03's B2 step) and B3's `* ==== S21 B3: matamatrix refused ====` (U21-10, appended by 21-03's B3 step):
- **U21-1** `dash rpcap lo hi turn weight, name(u211)` registers; the spec's plot has `yvar1=lo yvar2=hi yvar=turn xvar=weight type=rpcap`; `_dash_serve_spec` + a `python:` helper renders saved and served: each figure has one Segment, two `dash` Scatters tagged `dash_cap` and one marker Scatter; the marker's y column is `turn`; cap `size` equals the marker `size`.
- **U21-2** the same for rpspike: one Segment and one marker, no `dash_cap`.
- **U21-3** y range: both modes' `y_range` start/end equal the fixture's `.yaxis1.major.min/max` within the natscale padding rule dash already applies to rcap (compare with `dash rcap lo hi weight || scatter turn weight`'s range: equal).
- **U21-4** `msize(large)`: cap size == marker size in both modes, larger than the default.
- **U21-5** `horizontal`: the Segment is x0=lo,x1=hi,y0=y1=weight; the marker's x column is `turn`.
- **U21-6** y title: `lo/hi/turn` text when labels differ (fixture `title.differs`); the one label when equal.
- **U21-7** a filter move (served `_on_filter_change` to foreign==1; saved through `_FILTER_JS` under node via `test_saved_filter_layers._move` style) keeps the three renderers' row counts equal to the kept rows.

Area-script case (test_parser.cscript, appended after the P1A-59 region beside the P1A-59 flip; B1's):
- **U21-8** `dash rpcap turn weight` -> rc 102, line equals twoway's (`capture noisily twoway rpcap turn weight` in the same run); `dash rpcap lo hi turn weight price` -> rc 103, line equals twoway's; `dash rpcap turn` -> "too few variables specified" r(102).

B2's and B3's truth-block cases:
- **U21-9** (block `S21 B2`) `dash sunflower mpg weight` -> rc 198, line holds `dash: 'sunflower' is a twoway plot type dash does not draw: it bins points into density petals.`; `dash sunflow mpg weight` -> "unrecognised plot type" (twoway takes no abbreviation; measured in the extractor).
- **U21-10** (block `S21 B3`) `dash scatter matamatrix(M)` with `mata: M = (1,2\3,4)` -> rc 198, line holds `matamatrix(M) is a twoway mata matrix plot, which dash does not draw`; `dash scatter MATAMATRIX(M)` the same (case-insensitive, as `yxview_parse:152` lowers it); `dash scatter mpg weight, legend(label(1 "matamatrix(M)"))` rc 0 (quoted text is not read).

## TDD test stubs

### Regression tests, `test/test_rangept_layers.py` (new; red at 6370ca4 unless marked guard)

Helpers: `_render(mode, plot, df)` saved via `DashRenderer(...).render()` and served via `ServerAppBuilder` + `make_document` (test_date_range.py `_saved`/`_served`); `plot_for` from test_server_layer_defects; fixture read once.

- Test: a spec `{"type":"rpcap","yvar1","yvar2","yvar","xvar"}` draws one Segment, two `dash_cap` Scatters and one marker Scatter whose y field is `yvar` -- `TestRpcapDraws::test_spike_caps_and_marker[mode]` (red: "no glyph mapper for plot type 'rpcap'").
- Test: rpspike draws one Segment and one marker, no cap -- `TestRpspikeDraws::test_spike_and_marker[mode]` (red).
- Test: cap `size` equals marker `size` by default and under `msize(large)` -- `TestCapWidthIsMarkerSize::test_default_and_msize[mode]` (red).
- Test: `_dash_layer_axis_names(plot, "yvar")` returns the three y names; the figure's y range covers min(y1,y2,y3)..max -- `TestTheReaders::test_axis_names_and_range[mode]` (red).
- Test: `_dash_layer_series` gives `lo/hi/turn` with differing labels, one label when equal -- `TestTheReaders::test_series_label` (red).
- Test: `_dash_hover_layer_vars` lists x, y1, y2, y3 -- `TestTheReaders::test_hover_vars` (red).
- Test: `horizontal` transposes all four renderers (Segment x0/x1 are y1/y2; marker x is y3) -- `TestHorizontal::test_turned[mode]` (red).
- Test: one legend item per layer carrying both the spike and the marker renderers -- `TestLegendKey::test_one_key_two_renderers[mode]` (red).
- Test: after a filter move (saved JS under node, served `_on_filter_change`) the three sources' row counts equal the kept rows -- `TestMoves::test_rows_follow_the_filter[mode]` (red).
- Test: fixture `_meta` keys and every key of the truth table -- `TestTheFixture::test_meta_and_keys` (guard after 21-01).
- Test: `_DASH_RANGEPT_TYPES` is in the served copy list and the served app defines it -- `TestServedCarries::test_constant_copied` (red).
- Test: when the fixture's `draw.rpcap_weight` radii vary, dash.ado's `_wt_honoured` text and `_DASH_WEIGHT_ACCEPTS` hold both names; else neither -- `TestWeightRegistered::test_names_listed` (red when the fixture says they vary).

### Regression tests per row (DECISIONS A14; new files, red at the B1 tree)

- `test/test_sunflower_refusal.py` (B2): `_dash_undrawn_plottype`'s tuple in dash_parse.mata holds `"sunflower"`; dash.ado's `_pt_nodraw` block holds the sunflower sentence of TR-21.4; the help's Not-drawn paragraph names `{cmd:sunflower}` -- `TestSunflowerRefused::test_tuple`, `::test_sentence`, `::test_help`.
- `test/test_matamatrix_refusal.py` (B3): `_dash_matamatrix_typed` is defined in dash_parse.mata and listed in `_needed`; dash.ado calls it before the `_dash_undrawn_plottype` call and holds the matamatrix sentence; the help names `{cmd:matamatrix(}` -- `TestMatamatrixRefused::test_function_and_needed`, `::test_sentence`, `::test_help`.

### cscript cases: U21-1..U21-7 (block S21 B1), U21-8 (test_parser.cscript), U21-9 (block S21 B2), U21-10 (block S21 B3).

### Pinned tests to flip (R9)

- test_parser.cscript P1A-59 -> asserts `dash rpcap lo hi turn weight, name(p1a59b)` rc 0 and a registered spec with the four keys; the `rpca`/`rpspik` prefix part stays. `Flipped: test_parser.cscript P1A-59 -- the refusal was dash's gap, twoway draws rpcap/rpspike`.
- test_help_plot_types.py `_REFUSED` -> `("contour", "contourline", "sunflower", "matamatrix")` (B2/B3 commit; the B1 commit sets `("contour", "contourline")`), `test_dash_ado_refuses_them_by_name` reads `_dash_undrawn_plottype` for the first three and the `matamatrix` check for the last.
- test_help_claims_1.py `test_it_says_four_types_are_refused_and_so_does_item_5` -> the count word follows `len(_REFUSED)` measured at the base ("four" at `6370ca4`): two after B1, three after B2, four after B3.
- test_mode_parity.py `TestTheCorpusIsComplete`: no flip -- the corpus gains `_case("rpcap", [plot_for("rpcap")])`, `_case("rpspike", [plot_for("rpspike")])`, `_case("rpcap msize(large)", ...)`, `_case("rpcap horizontal", ...)`, `_case("rpcap aweight", ...)` when the weight is registered (TR-21.2), and `_move_case("rpcap, dropdown to Foreign", _MOVES[0], [plot_for("rpcap")])`, `_move_case("rpspike, dropdown to Foreign", ...)`; `_MOVED_LAYERS` (:2837-2846) gains both types with three sources (spine/caps source, marker source).
- test_parser.cscript P1A-56: the plot-type count, if asserted numerically, is recounted at the base and moved by two with `// <measured old> -> <measured old + 2>: WP-31 B1 rpcap and rpspike drawn` (R10, A33).
- test_unsupported_report_is_true.py / test_help_conformance.py: no change (no new option).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| rpcap/rpspike geometry | pytest test_rangept_layers.py | rangept_truth.json | yes |
| var-count refusals, twoway's words | cscript U21-8 (live twoway beside dash) | -- | n/a |
| sunflower/matamatrix refusals | cscript U21-9 (block B2), U21-10 (block B3); pytest test_sunflower_refusal.py, test_matamatrix_refusal.py | rangept_truth.json advice keys | n/a |
| weight on the y3 marker | pytest TestWeightRegistered; parity `rpcap aweight` at G2 | rangept_truth.json `draw.rpcap_weight` | yes |
| ranges, titles, keys vs twoway class values | cscript U21-1..U21-6 | rangept_truth.json | yes |
| moves | pytest TestMoves, cscript U21-7, MOVE_CORPUS | -- | yes |
| registration completeness | test_mode_parity TestTheCorpusIsComplete, test_every_plot_type_draws, test_plottype_families, test_help_plot_types | -- | n/a |

Acceptance: **AC-21.1** both types draw in both modes with cap width == marker size; **AC-21.2** counts refused with twoway's rc/words; **AC-21.3** y range/title over three vars; **AC-21.4** sunflower and matamatrix refused by name, listed in the help; **AC-21.5** every registry test green; **AC-21.6** three green commits.

## Tasks

**Commit boundary.** 21-01 + 21-02 = commit `(WP-31 B1)`; 21-03 makes two commits `(WP-31 B2)` then `(WP-31 B3)`; 21-04's help/audit/pkg edits are staged into the B3 commit (its closing step). Subjects: `Draw rpcap and rpspike as twoway does (WP-31 B1)`, `Refuse sunflower by name with advice (WP-31 B2)`, `Refuse matamatrix() by name with advice (WP-31 B3)`.

<task type="auto" id="21-01">
  <name>Write failing tests and the extractor</name>
  <files>test/test_rangept_layers.py, scripts/extract_rangept_truth.do, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create scripts/extract_rangept_truth.do per "Stata truth" (header, guards and python block copied from scripts/extract_default_base_truth.do:1-60 and :160-200 with the ZB_ prefix renamed ZR_), run it with `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s21 $WT/scripts/extract_rangept_truth.do`, and check test/fixtures/rangept_truth.json has `_meta` and every key of the table. Create test/test_rangept_layers.py with every stub under "TDD test stubs" (both modes parametrized). Append the S21 B1 block (U21-1..U21-7) above `* ==== append new blocks above this line ====` in test/test_wp31_truth.cscript. Run `python3 -m pytest test/test_rangept_layers.py -q -n0 -p no:cacheprovider 2>&1 | tee <scratch>/21-01-failure.txt` against the unmodified tree, and the truth block through the driver (`WP31_ONLY=S21`), appending its FAIL lines to the same file. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "no glyph mapper for plot type 'rpcap'\|FAILED" <scratch>/21-01-failure.txt` is at least 9; `python3 -c "import json;d=json.load(open('test/fixtures/rangept_truth.json'));print(sorted(d['_meta']))"` prints `['born_date', 'dash_commit', 'extracted', 'source', 'stata_version']`; `grep -c "U21-[1-7] FAIL" <scratch>/s21/run_test_wp31_truth.log` is at least 1.]]></verify>
  <done>The rpcap/rpspike regression tests and truth block failed against the unmodified tree, the fixture was written, and the failure text was saved.</done>
</task>

<task type="auto" id="21-02">
  <name>Draw rpcap and rpspike in both modes</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[Make TR-21.1, TR-21.2 (families, var-count branch, vfields, type lists, Supported line, refusal branch trimmed; the weight registration lines if the fixture's `draw.rpcap_weight` radii vary -- R2-32) and TR-21.3's table rows; remove `rpcap`, `rpspike` from `_dash_undrawn_plottype`'s tuple. Make TR-21.5, TR-21.6 and TR-21.8 in dash_render.py (set, dispatch, `y3var` keyword through `_dash_add_glyph`, the two mappers after `map_rcapsym`, the reader branches, the orientation tuples, the copy-list constant). Then in a second step (same commit) update the tests of TR-21.7: `_plot_for`, `plot_for`, test_horizontal.py:315, test_plottype_families.py, function_test_map.py, flip P1A-59, set test_help_plot_types `_REFUSED = ("contour", "contourline")`, flip test_help_claims_1's "four" to "two", append the CORPUS/MOVE_CORPUS entries and `_MOVED_LAYERS` rows, append U21-8 to test_parser.cscript. Run test_rangept_layers.py, test_every_plot_type_draws.py, test_plottype_families.py, test_help_plot_types.py, test_horizontal.py, test_server_layer_defects.py, test_function_test_map.py, test_program_coverage_map.py, `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "rpcap or rpspike or Complete"`, and test_parser.cscript and the S21 block through the driver. Close BUGS.md "B1" (Resolution form of BRIEF), rewrite the GAPS3 B1 Tracked line to `- **B1 Tracked:** Closed in WP-31, BUGS.md "<B1 title>", commit pending.` (the merger's step k.3b fills the sha, DECISIONS A11), replace the `<!-- WP-31 B1 -->` marker under `### Fixed in WP-31` with `- rpcap and rpspike are drawn: a spike from y1 to y2 at x, caps as wide as the marker (rpcap), and the marker at y3, in both modes; dash refused both by name r(198). (WP-31, B1)`. Stage dash.ado dash_parse.mata dash_render.py the test files scripts/extract_rangept_truth.do BUGS.md GAPS3.md CHANGELOG.md and `git add -f test/fixtures/rangept_truth.json`; commit `Draw rpcap and rpspike as twoway does (WP-31 B1)` with the BRIEF body lines (Regression:, Flipped: P1A-59, Flipped: _REFUSED, Fixture:, BUGS.md:, GAPS3:).]]></action>
  <verify><![CDATA[Every pytest run above reports 0 failed; `grep -c "U21-[1-8] PASS" <scratch>/s21/run_test_wp31_truth.log <scratch>/s21/run_test_parser.log` totals 8 and both logs end `ALL CHECKS PASSED`; `grep -c '"rpcap"' dash_render.py` is at least 4; `grep -c "B1 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 B1)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>rpcap and rpspike were parsed as four-variable layers and drawn in both renderers with twoway's geometry, and B1 was committed green.</done>
</task>

<task type="auto" id="21-03">
  <name>Refuse sunflower and matamatrix by name</name>
  <files>dash.ado, dash_parse.mata, test/test_wp31_truth.cscript</files>
  <action><![CDATA[B2 first: create test/test_sunflower_refusal.py (B2's regression test file, A14) and append B2's truth block `* ==== S21 B2: sunflower refused ====` (U21-9) above the marker line after the S21 B1 block; run both against the B1 tree (red: "unrecognised plot type"), save the FAIL lines to <scratch>/21-03-B2-failure.txt. Make TR-21.3's sunflower tuple entry and TR-21.4's sunflower branch; set test_help_plot_types `_REFUSED = ("contour", "contourline", "sunflower")` and test_help_claims_1's count word to three (flipped tests, implied); run test_sunflower_refusal.py, the S21 blocks through the driver (`WP31_ONLY=S21`), test_help_plot_types.py and test_help_claims_1.py (the help edit of 21-04 is needed for test_help_plot_types to pass: make the Not-drawn paragraph edit of 21-04 now, naming sunflower, and matamatrix in the B3 step). Close BUGS.md "B2", rewrite the Tracked line to `- **B2 Tracked:** Closed in WP-31, BUGS.md "<B2 title>", commit pending.` (the merger's step k.3b fills the sha, DECISIONS A11), replace the `<!-- WP-31 B2 -->` marker under `### Changed behaviour (may need your do-files changed)` with `- sunflower is refused by name, r(198): "dash: 'sunflower' is a twoway plot type dash does not draw: it bins points into density petals. Use Stata's own sunflower command ..."; it was answered "unrecognised plot type". (WP-31, B2)`; commit `Refuse sunflower by name with advice (WP-31 B2)`. B3 next: create test/test_matamatrix_refusal.py (B3's regression test file, A14) and append B3's truth block `* ==== S21 B3: matamatrix refused ====` (U21-10) after the B2 block; run both red, save <scratch>/21-03-B3-failure.txt; add `_dash_matamatrix_typed` (TR-21.3), its `_needed` entry and header index line, the dash.ado check (TR-21.4), program_coverage_map.py entry; `_REFUSED` gains "matamatrix" and the help-claims count word becomes four; run test_matamatrix_refusal.py, the S21 blocks through the driver, test_help_plot_types.py, test_help_claims_1.py, test_program_coverage_map.py, test_no_orphans.py, test_abbreviations.py. Close "B3", rewrite the Tracked line to `- **B3 Tracked:** Closed in WP-31, BUGS.md "<B3 title>", commit pending.` (DECISIONS A11), marker under Changed behaviour: `- matamatrix() is refused by name, r(198), with advice to getmata the columns; it was read as a variable list and refused r(101)/r(111). (WP-31, B3)`. Do not commit yet: 21-04 adds to this commit.]]></action>
  <verify><![CDATA[`git log -1 --format=%s` ends `(WP-31 B2)`; `grep -c "U21-9 PASS\|U21-10 PASS" <scratch>/s21/run_test_wp31_truth.log` prints 2 after the B3 step; `grep -c "^\* ==== S21 B[123]: " test/test_wp31_truth.cscript` prints 3; `ls test/test_sunflower_refusal.py test/test_matamatrix_refusal.py` lists both; `grep -c "B2 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `grep -c '"sunflower"' dash_parse.mata` is at least 1; `grep -c "_dash_matamatrix_typed" dash.ado dash_parse.mata test/program_coverage_map.py` totals at least 4.]]></verify>
  <done>sunflower and matamatrix() were refused by name with advice, B2 was committed, and B3's code, tests and tracking edits were staged for 21-04's commit.</done>
</task>

<task type="auto" id="21-04">
  <name>Update the help, audit and package, commit B3</name>
  <files>dash.sthlp, dash.pkg</files>
  <action><![CDATA[dash.sthlp: the Plot types table (:252-259) gains `rpcap`, `rpspike` on the range line; the Not-drawn paragraph (:572-581) reads: `{ul:Not drawn.}  Four {cmd:twoway} plot types are not drawn by {cmd:dash}: {cmd:contour} and {cmd:contourline}, which interpolate a surface over a grid from their three variables; {cmd:sunflower}, which bins points into density petals; and {cmd:matamatrix(}{it:name}{cmd:)}, which plots a Mata matrix. Each is refused with {cmd:r(198)} and a message naming what to use instead: {cmd:twoway} itself, {cmd:dash scatter} {it:y x}{cmd:,} {cmd:colorvar(}{it:z}{cmd:)} for the first two, Stata's {cmd:sunflower} command for the third, and {cmd:getmata} into variables for the last. ...` keeping its last three sentences; add after the pccapsym paragraph (:346-349) `{ul:rpcap and rpspike.}  Four variables {it:y1 y2 y3 x}: a spike from {it:y1} to {it:y2} at {it:x}, caps as wide as the marker ({cmd:rpcap}), and the marker at {it:y3}; {opt msize()} sizes caps and marker together; the y axis spans all three; {cmd:horizontal} turns the layer. Drawn in both modes and redrawn from the kept rows after a filter move.` (S26 later rewrites the Not-drawn paragraph to two names.) TWOWAY_COVERAGE_AUDIT.md:14-15, :24, :101-104: rpcap/rpspike rows become "Drawn (WP-31 B1)"; add rows for sunflower and matamatrix "Explicitly refused (WP-31 B2/B3)". dash.pkg:5: recount the plot types at the base (the word is "forty" at `6370ca4`) and write the count plus two ("forty-two" if the base still says forty); check test_version_floor.py and test_help_claims_*.py for a pinned count and move each with `# <measured old> -> <measured old + 2>: WP-31 B1 rpcap and rpspike drawn` (A33). Run `python3 -m pytest test/test_help_conformance.py test/test_help_plot_types.py test/test_help_claims_1.py test/test_version_floor.py -q -p no:cacheprovider`. Stage dash.sthlp TWOWAY_COVERAGE_AUDIT.md dash.pkg dash.ado dash_parse.mata test/test_wp31_truth.cscript test/test_matamatrix_refusal.py test/test_help_plot_types.py test/test_help_claims_1.py test/program_coverage_map.py BUGS.md GAPS3.md CHANGELOG.md; commit `Refuse matamatrix() by name with advice (WP-31 B3)` with the body lines (the saved <scratch>/21-03-B3-failure.txt text first).]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -c "{ul:rpcap and rpspike.}" dash.sthlp` prints 1; `grep -c "{cmd:sunflower}" dash.sthlp` is at least 2; `grep -c '<!-- WP-31 B[123] -->' CHANGELOG.md` prints 0; `grep -c "B[123] Tracked:\*\* Closed in WP-31" GAPS3.md` prints 3; `git log -3 --format=%s | grep -c "(WP-31 B[123])"` prints 3; `git log -3 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The help, audit and package described rpcap/rpspike as drawn and sunflower/matamatrix as refused, and B3 was committed green.</done>
</task>

## Section completion criteria

- `dash rpcap`/`rpspike` with four variables draw in both modes (spike, caps = marker size, marker at y3; y range over three; one key; horizontal turned); other counts refused with twoway's rc and words (U21-8).
- `sunflower` and `matamatrix()` refused by name r(198) with the fixed sentences; help's Not-drawn names four (contour, contourline, sunflower, matamatrix) until S26.
- Every registry oracle green: TestTheCorpusIsComplete, test_every_plot_type_draws, test_plottype_families, test_help_plot_types, test_horizontal, function_test_map, program_coverage_map, no_orphans.
- rangept_truth.json stamped and named; U21-1..U21-10 PASS (three truth blocks S21 B1/B2/B3, U21-8 in test_parser.cscript); test_rangept_layers.py, test_sunflower_refusal.py and test_matamatrix_refusal.py green (one regression file per row, A14); P1A-59 and `_REFUSED` flipped with reasons.
- Three green commits on `wp31-s21`; BUGS.md B1-B3 closed; the three Tracked lines read `Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b fills the sha); markers replaced.

## Notes

- **Renderer order.** The saved `_make_figure_body` tests `_RANGE_TYPES` after `_PC_TYPES`; put the `_DASH_RANGEPT_TYPES` branch before `_RANGE_TYPES` in both modes so `yvar1` is never read by the plain-range branch.
- **`_dash_add_glyph`'s guard** (:42360-42363) checks `[yvar, xvar, y2var]`; include `y3var` in `_vars_needed` for the family so a missing marker variable draws nothing with the note, as the other guards do.
- **Hover.** `_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, ...)` (:40081) takes the first layer's variables; for the family pass `y1var=yvar1`, `y2var=yvar2` and add `yvar` through `hover_extra` so the tooltip shows all four.
- **python_exec hazard** (project memory): check `~/.stata19/console/stata19.rc` after each driver run; a SKIP (exit 222) is not a pass.
- **Shared files (R1-R13).** R1: three S21 blocks in the truth script, one per row (A14); U21-8 in test_parser.cscript beside the P1A-59 flip (S20/S22 append nothing there). R2: one constant after `_DASH_STALE_STATUS_HTML`; the weight registration (if any) is a new `_DASH_WEIGHT_ACCEPTS.update(...)` statement and a new dash.ado line after `_wt_honoured`, never an edit of S20's lines (merge order S20 then S21). R3: the Not-drawn paragraph and the new rpcap paragraph; S26 re-edits Not-drawn in batch 9. R4: three markers replaced. R5: three entries, three Tracked lines. R6: `_needed` gains `_dash_matamatrix_typed` in alphabetical place; `version 19` in no new program (none added; the Mata function is in the parser section). R7: one new fixture. R8: CORPUS/MOVE_CORPUS appended; `ALLOWED` untouched. R9: P1A-59, `_REFUSED`, the help-claims count flipped in place. R10: the plot-type count moves by two from the value measured at the base, with the comment (A33). R12: S21 edits `_make_figure_body` (one branch) and `_generate_app_source` (one branch in `_dash_draw_layer`): S21 is batch 7's editor of both; S20 and S22 do not edit them (S22 edits `_FILTER_JS` only).
- **Commit-body line forms** are BRIEF's: `Regression: test/test_rangept_layers.py::TestRpcapDraws::test_spike_caps_and_marker[saved] -- failed at 6370ca4 with "no glyph mapper for plot type 'rpcap'"`, `Flipped: test/test_parser.cscript P1A-59 -- ...`, `Fixture: test/fixtures/rangept_truth.json (scripts/extract_rangept_truth.do)`, `BUGS.md: "<B1 title>" (closed)`, `GAPS3: B1 Tracked`.
- **For S26 (batch 9).** The `_pt_nodraw` block keeps its contour branch and sunflower branch; S26 deletes the contour branch and rewrites Not-drawn to "Two ... sunflower and matamatrix()". `_REFUSED` becomes `("sunflower", "matamatrix")`.
- **For S57.** examples/ gains an rpcap page (`sysuse auto; gen lo = turn-5; gen hi = turn+5; dash rpcap lo hi turn weight`).
