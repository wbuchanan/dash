# Section 02: Arrowheads from the marker options

> Part of: WP-31 · GAPS3 rows: C1 (B27's arrow part) · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U02

## Overview

**What is wrong today.** GAPS3 C1 (GAPS3.md:120) reads: "pcarrow/pcbarrow/pcarrowi: head `msize() mcolor() mfcolor() mlcolor() mlwidth()` are declared, written to the spec and **silently** not read; heads are fixed `OpenHead(size=10)`; pcbarrow's `NormalHead` has no `fill_color` so its heads fill black; `mangle()`, `barbsize()`, `headlabel` undeclared (generic note); a row missing only its second point is dropped whole. test_phase4_plots.py P4-18/P4-20 pin the black heads." Evidence dash_render.py:19683-19861 (`map_pcarrow`, `map_pcbarrow`), :19660-19662 (`_add_arrow_heads`). B27 (GAPS3 §4.B) carries the arrow part of the same gap under the drop-in register.

**What twoway draws** (research/stata-ground-truth.md §6, from `B/y/yxview_pcarrow_draw.ado` and `B/_/_gr_arrowhead.ado`): the shaft in the series' arrow line style; the head by `_gr_arrowhead ang msz barbsz x0 y0 x1 y1` with `ang` = `marker.angle` (default `anglestyle stdarrow` 28.64 degrees), `msz` = `marker.size` (`symbolsize parrow medium`, dash-s2color.scheme:528), `bsz` = `marker.backsize` (`symbolsize parrowbarb zero`). With `bsz == 0` the head is two open strokes of length `msz` from the tip at angles `pi + phi +/- ang` (back along the shaft). With `bsz > 0` it is a filled polygon: tip, A = tip + msz*(cos(pi+phi+ang), sin(pi+phi+ang)), B = tip + bsz*cos(ang)*(cos(pi+phi), sin(pi+phi)), C = tip + msz*(cos(pi+phi-ang), sin(pi+phi-ang)), back to the tip (`arrowhead_barb`, `_gr_arrowhead.ado:46-73`, read 10oct2026). `barbsize() = msize()` puts B at the foot of the perpendicular from A: a right angle at A (`twoway_pcarrow.sthlp:158-162`). pcbarrow draws the same head at the start point too. Head colour is `markerstyle p#arrow`: fill `p#arrowfill` -> `color p#`, line `linestyle p#arrow` -> the shaft's colour and `linewidth p medium`. The head's line pattern cannot be changed (`sthlp:181-183`). Labels go at the tail unless `headlabel` (`yxview_pcarrow_draw.ado:48-60`). `_gr_arrowhead` exits when a transformed endpoint is missing (`:15-23`): no head for a one-point row; whether the shaft's `gdi line` draws anything, or the point a marker, is measured by this section's extractor.

**After this section** both renderers size every head from `msize()` (default the scheme's `symbolsize parrow`), stroke it in `mcolor()`/`mlcolor()` at `mlwidth()` (default the shaft's colour and the scheme's arrow line width), fill it (pcbarrow and any `barbsize() > 0`) in `mfcolor()` defaulting to the series colour `color p#`, never black; `barbsize()` is declared and chooses open strokes (0) or a filled head (> 0); `mangle()` is declared and named (D-02.b); `headlabel` is declared and moves the labels to the second point on the three arrow types; a row whose second point is missing is drawn as twoway's extractor shows (D-02.d). P4-18 and P4-20 are flipped. The spec, the saved page and the served app share one mapper path.

**Test order and commit rule (rule 7, BRIEF).** 02-01 writes the extractor, runs it, writes `test/test_arrowheads.py` red, saves `<scratch>/02-01-failure.txt`, no commit. 02-02 declares the three options in dash.ado. 02-03 draws the heads in the shared mapper and flips the pins. 02-04 certifies, documents, closes C1 and commits once `(WP-31 C1)`.

### Section decisions (binding on the executor)

- **D-02.a Bokeh `Arrow` heads with per-row size columns.** The head stays ONE `Arrow` annotation over the shaft's source (the WP-22 vectorised form, `_add_arrow_heads`), with `end=OpenHead(size="__dash_head_px", ...)` for `barbsize() == 0` and `end=NormalHead(size="__dash_head_px", fill_color=..., ...)` for `barbsize() > 0`. `__dash_head_px` is a data column of `pc_source` (so a saved move copies it with the row and a served redraw rebuilds it), holding the head length in pixels `L = msz_px / sqrt(1.25)`: BokehJS draws OpenHead/NormalHead from the tip to (+/-0.5 s, s), a stroke of length `s*sqrt(1.25)`, and twoway's stroke is `msz`; `msz_px` is `OptionTranslator.resolve_size(options["msize"], "msize", default)` converted as `_apply_marker_opts` converts a marker size, default `self.scheme.default_arrow_size(color_idx)` (TR-02.1).
- **D-02.b `mangle()` is declared, read and named.** Bokeh's heads have a fixed half-angle (atan(0.5) = 26.57 degrees against twoway's 28.64, and `barbsize()`'s depth is fixed too): a value other than the default cannot be drawn by an `Arrow`, and research/bokeh-web.md §3 says a custom head glyph would be needed. Ruling: `mangle()` goes on the pending list (named once in the note), and the 2.07-degree difference of the default head is documented under M17 with the measured example. Reversible: a later section may draw a custom head (a `Patches` glyph in screen units does not exist in Bokeh 3.8; a `Scatter(marker="triangle")` has no tip at the point). **Decision for maintainer ratification.**
- **D-02.c `barbsize()` is drawn as open-or-filled.** 0 (the default) -> OpenHead; > 0 -> NormalHead whose `size` column is `L` (the barb depth cannot be set; documented). A negative or non-numeric value is refused by a rule `barbsize=style,0,10000` (a symbolsize: names and numbers) added to `local plot` -- the ONE rule token this section adds, in batch 1, where S04 owns `_dash_option_rules` (R12): S02 hands the token text to S04's 04-02 to insert, or inserts it after S04 merges (merge order 04, 02); the executor checks `grep -c "barbsize=" dash.ado` before editing.
- **D-02.d One-point rows follow the fixture.** `scripts/extract_arrowhead_truth.do` measures `pcarrow y1 x1 y2 x2` with one row's `y2` missing: SVG line count and marker count against the all-present graph. If twoway draws a marker for that row, dash draws `fig.scatter` at (x1, y1) for rows with a missing second point in the scheme's `symbol p#`/`symbolsize p#` and the shaft colour; if twoway draws nothing, dash keeps dropping the row and the GAPS3 Task sentence "keep a one-point row as a marker" is recorded as measured-false in the BUGS resolution. Either way `_pc_clean_with_label` keeps a `__dash_pc_onepoint` flag so the rule is one function.
- **D-02.e `headlabel` is drawn on the three arrow types, named on the other pc types.** The `HEADlabel` flag is accepted on every yxyx and y3x type (research §1.3), so it is declared once; pcspike/pcscatter/pccapsym/pci get it on the pending list until S34 (C17) draws it there; `_dash_rep_und_tab`'s `headlabel` row is deleted (its readers then count a second copy through `_dash_rep_unique`, where `headlabel` is added).

## Risk: [yellow] -- every pcarrow/pcbarrow/pcarrowi page changes look; three new declarations move the counts and the abbreviation tests

**Why.** Head size and colour change on every arrow dashboard in both modes; the per-row size column must survive a saved move (row copy) and a served redraw (data copy). Three declarations touch the `syntax` block, the pending blocks, `_dash_rep_und_tab`, the JSON key list, and four test files that count declarations.

**Risk factors.** 1. Pinned heads: P4-18, P4-20 (NormalHead, black); test_pccapsym_pcarrowi.py:233 (OpenHead at the end -- still true by default); test_saved_filter_layers.py:315-335 (`_add_arrow_heads` signature); test_server.py:1228-1258 ("Arrow"/"OpenHead" in the app source). 2. `msize()` on the arrow types is also the mlabel radius (`_mlabel_radius_px`): the head size and the label gap must read the same number. 3. A `size` column of a `DataAnnotation` is a `NumberSpec` field: BokehJS reads it from the source; an empty source still needs the column. 4. Batch partners: S04 owns `_dash_option_rules` and the applies table (no row for the three new options: they are accepted on every yxview type); S03 declares `MWidth` in the same `syntax` block and moves the same counts.

**Mitigation.** 1. 02-01 lists the red nodes from a simulated mapper; 02-03 flips them in place (R9). 2. One helper `_arrow_head_px(options, color_idx)` feeds both. 3. `_pc_clean_with_label` adds the column on every path, the empty frame included; `test_an_empty_layer_keeps_the_column`. 4. The three declarations are appended at the END of the `syntax` block before `*` and the pending lines after the last existing one, so S03's hunks (its own appended lines) merge after S02's; counts: S02 196 -> 199, S03 then 199 -> 200 (merge order 04, 02, 03; the merger reconciles the two `# old -> new` lines).

## Dependencies

- **Depends on: 01** (BUGS.md "C1" entry; GAPS3 Tracked line; CHANGELOG markers; `S02` block in `test_wp31_truth.cscript`).
- **Blocks: --.** S34 (C17, batch 11) later draws `headlabel` on the other pc types and removes the pending name S02 leaves.
- **Parallel batch: 1**, merge order 04, 02, 03. Can run with S04 (rules table, `_dash_validate_opts`) and S03 (`map_rbar`, `map_dot`, `_dash_recast_opt`): none edits the pc mappers, `_pc_clean_with_label`, `_add_arrow_heads`, `_apply_marker_opts` or the parity CORPUS lines S02 adds. The barbsize rule token (D-02.c) is the one touch of S04's function and is inserted after S04 lands.

## Evidence

Anchors at `6370ca4`.

### The heads today

dash_render.py `map_pcarrow` (def :19683), :19767-19769; `map_pcbarrow` (def :19777), :19851-19854:

```python
19767        self._add_arrow_heads(fig, pc_source, y1var, x1var, y2var, x2var,
19768                              color, arrow_lw,
19769                              end=OpenHead(size=10, line_color=color, **_hk),
...
19851                              end=NormalHead(size=10, line_color=color, **_hk),
19852                              start=NormalHead(size=10, line_color=color,
19853                                               **_hk),
```

`size=10` is fixed; `NormalHead` has no `fill_color` (Bokeh default black). `_add_arrow_heads` (:19647-19681) builds the one `Arrow` with `x_start={"field": x1var}` etc. over `pc_source`. `color` is `self.scheme.default_color(color_idx, "pcarrow")` then `lcolor`/`color` (:19737-19744); `msize mcolor mfcolor mlcolor mlwidth` are never read in either mapper (grep over :19683-19861: no `options["m`). `_apply_mlabel_opts` is called with `radius_px=self._mlabel_radius_px(options, self.scheme.default_marker_size(color_idx))` (:19773, :19858): the label gap reads `msize()`, the head does not.

`_pc_clean_with_label` (:19611-19645) returns `clean.dropna(subset=coords)`: a row missing any of the four coordinates is dropped whole.

`map_pcarrowi` (:20114) draws through `map_pcarrow` from literal values (test_pccapsym_pcarrowi.py:222 `test_it_draws_what_pcarrow_draws_from_the_same_numbers`), so it inherits every change.

### The declarations today

dash.ado `_dash_parse_plot_opts` `syntax` (:1167-1239) declares `MColor MFColor MLColor MLWidth MSIze` (:1168-1170, :1230) and not `MANGle`, `BARBSize` or `HEADlabel`. `_dash_rep_und_tab` (dash_parse.mata:6250-6324) has `("headlabel", "headlabel", "head", "0", pcs, "0", "")` (:6276) and no row for mangle/barbsize, which fall to the catch-all and the generic note. `_dash_fold_typed` (:2264-2269) names `mstyle mlstyle` on `arrow_types` (WP-30 P1.14a).

### Scheme stubs

dash-s2color.scheme:528 `symbolsize parrow medium`; research §11 lists as absent `symbolsize parrowbarb zero`, `anglestyle parrow stdarrow`, `anglestyle parrowbarb zero`, `markerstyle p#arrow`, `linestyle p#arrow/p#arrowline`. `SchemeParser` already reads `symbolsize parrow` as `"symbolsize parrow": "medium"` in its defaults (dash_render.py:8103) and `plot_line_width(color_idx, "arrowline")` (:10983, kind table :10945-10960). `OptionTranslator.resolve_size(value, kind, default_pt, ref_in)` (:7098) is S08's resolver (WP-30), kind `"msize"`; `_apply_marker_opts` (:13243) is the call to copy for the conversion from points to pixels. `_dash_anglestyle_degrees` (:6386) reads an anglestyle name or degrees (used by mlabangle at :14303): `mangle()` is parsed with it for the note's wording only (D-02.b).

### Fixtures on disk

None for arrows. `test/fixtures/marker_linewidth_truth.json` holds the arrowline width chain (research, `plot_line_width` docstring).

### Existing tests that pin today's behaviour (flip, never delete)

| Node | Today | After |
|---|---|---|
| test/test_phase4_plots.py::TestMapPcbarrow::test_pcbarrow_uses_normal_head_on_both_ends (P4-18, :230) | NormalHead both ends | OpenHead both ends by default (barbsize 0); NormalHead both ends with `{"barbsize": "medium"}`; `fill_color` == the series colour, never black |
| test/test_phase4_plots.py::TestMapPcbarrow::test_pcbarrow_differs_from_pcarrow_head_type (P4-20, :258) | pcarrow OpenHead, pcbarrow NormalHead | both OpenHead by default; pcbarrow has a `start` head and pcarrow none |
| test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_it_draws_what_pcarrow_draws_from_the_same_numbers (:233) | `all(isinstance(a.end, OpenHead))` | unchanged (guard) |
| test/test_saved_filter_layers.py:315-335 (`_add_arrow_heads(..., end=OpenHead())`) | signature `(fig, src, y1, x1, y2, x2, color, lw, end=, start=, line_alpha=)` | unchanged signature; the test's source gains no column, so the heads use the default `size` -- guard |
| test/test_server.py:1241, :1258 | `"Arrow" in source or "OpenHead"/"NormalHead"` | unchanged (guard) |
| test/test_unsupported_report_is_true.py:725 `== 196` | 196 | 199 with `# 196 -> 199: C1 mangle barbsize headlabel declared` |
| test/test_help_conformance.py::TestEveryDashOnlyOptionIsDocumented | -- | the three are twoway spellings (abbrev_truth.json may lack them: then add `{phang2}` entries in the pcarrow paragraph) |
| test/test_abbreviations.py::test_no_prefix_is_claimed_by_two_options (:406), ::test_declared_minimums_cover_stata_minimums (:277) | -- | `MANGle` vs `MALpha`/`MARKER`: `mang` is free; `BARBSize` vs `BARWidth`: `barb` is free; `HEADlabel`: `head` is free (checked by grep of the syntax block at `6370ca4`) |

## User stories

- **US-02.1** As a twoway user, I want `dash pcarrow y1 x1 y2 x2, msize(large) mcolor(red)` to draw larger red heads, so the picture matches my Stata graph.
- **US-02.2** As a twoway user, I want pcbarrow's heads in the series colour, not black.
- **US-02.3** As a twoway user, I want `barbsize(medium)` to fill the heads and `headlabel` to put the labels at the head, as twoway does.
- **US-02.4** As a dashboard reader, I want heads that keep their size and colour after a filter move in both modes.

## Business requirements

- **BR-02.1** The head length equals the marker length a `scatter ..., msize(same)` draws on the same figure, the scheme's `symbolsize parrow` by default; it does not change with zoom, x spacing or a filter move.
- **BR-02.2** The head's stroke colour is `mcolor()`/`mlcolor()` (mlcolor wins), else the shaft's colour; its fill (when filled) is `mfcolor()`, else `mcolor()`, else the series colour `color p#`; its line width is `mlwidth()`, else the scheme's arrow line width. Nothing is black by default.
- **BR-02.3** `barbsize(0)` or none draws open strokes; `barbsize(#>0)` draws a filled head; a bad value is refused as a size is refused.
- **BR-02.4** `headlabel` puts the layer's labels at (x2, y2) on pcarrow, pcbarrow and pcarrowi; without it they stay at (x1, y1).
- **BR-02.5** `mangle()` is accepted and named once in the note; no silence.
- **BR-02.6** A row whose second point is missing is drawn as twoway draws it (the fixture decides); a row whose first point is missing draws nothing.
- **BR-02.7** Saved page and served app draw identical heads before and after a move.

## Technical requirements

- **TR-02.1 `GlyphMapper._arrow_head_px(self, options, color_idx) -> float`** (new method, after `_add_arrow_heads`): default `d = self.scheme.default_arrow_size(color_idx)` (TR-02.2); when `"msize" in options`, the value through the SAME call `_apply_marker_opts` makes for `msize()` at `6370ca4` (read :13243-13300; copy the `resolve_size(..., "msize", ...)` call and its points-to-pixels conversion verbatim, including its note on a bad value); returns pixels. `L = px / math.sqrt(1.25)` is computed by the caller.
- **TR-02.2 `SchemeParser.default_arrow_size(self, index=0) -> float`** (new, after `default_marker_size` :10936-10943): the pixel size of `symbolsize parrow` (the `"symbolsize parrow"` property, :8103), resolved by the same ladder `default_marker_size` uses for `symbolsize p`; falls back to `default_marker_size(index)`.
- **TR-02.3 `_pc_clean_with_label`** (:19611-19645): add the column `self._HEAD_PX = "__dash_head_px"` filled with `L` (one float per row; `clean[self._HEAD_PX] = L` after the dropna); add `self._PC_ONEPOINT = "__dash_pc_onepoint"` = 1 where x1,y1 present and x2 or y2 missing, 0 else, kept only when D-02.d says twoway draws the point (else dropped as today). Signature gains `head_px: float = 0.0` keyword (default keeps every other caller -- pcspike, pccapsym, pcscatter -- unchanged). Class attributes, no copy-list entry (R2: class members travel).
- **TR-02.4 Heads.** In `map_pcarrow` replace :19767-19769 with:
  ```python
          _hpx = self._arrow_head_px(options, color_idx)
          _hl = self._arrow_head_line(options, color, arrow_lw)   # (line_color, line_width)
          _hf = self._arrow_head_fill(options, self.scheme.default_color(color_idx, "scatter"))
          _bs = self._arrow_barb(options)                          # 0.0 or > 0.0
          _mk = (NormalHead if _bs > 0 else OpenHead)
          _hkw = dict(size=self._HEAD_PX, line_color=_hl[0], line_width=_hl[1], **_hk)
          if _bs > 0:
              _hkw["fill_color"] = _hf
          self._add_arrow_heads(fig, pc_source, y1var, x1var, y2var, x2var,
                                color, arrow_lw, end=_mk(**_hkw), line_alpha=_la)
  ```
  and in `map_pcbarrow` the same with `start=_mk(**_hkw)` too. `_arrow_head_line`: `mlcolor` then `mcolor` through `self.tr.parse_color_alpha(v, key, base=color)`, else `color`; width `mlwidth` through the lwidth translator `_apply_line_opts` uses (`translate_lwidth`), else `self.scheme.plot_line_width(color_idx, "arrowline") or arrow_lw`. `_arrow_head_fill`: `mfcolor` then `mcolor` through `parse_color_alpha`, else the series colour. `_arrow_barb`: `options.get("barbsize")` through `resolve_size(v, "msize", 0.0)`; `0.0` when absent or `"0"`; a bad value already refused by the rule (D-02.c). `_pc_clean_with_label` is called with `head_px=L` where `L = _hpx / math.sqrt(1.25)`.
- **TR-02.5 Labels.** `_apply_mlabel_opts(fig, pc_source, options, x1var, y1var, ...)` (:19773, :19858) becomes `(..., x2var if _dash_flag(options, "headlabel") else x1var, y2var if ... else y1var, radius_px=self._mlabel_radius_px(options, _hpx), ...)`: the label radius reads the head size (one number, D-02.a). `_dash_flag(options, name)` is an existing helper if one exists (grep `def _dash_flag`); else `str(options.get("headlabel", "")).strip() != ""`.
- **TR-02.6 One-point rows (D-02.d).** When the fixture's `onepoint.markers` > `onepoint.markers_all_present`, add after the shaft in both mappers: `_op = pc_source.data[self._PC_ONEPOINT]`; if any: `fig.scatter(x=x1var, y=y1var, source=pc_source, view=CDSView(filter=BooleanFilter([bool(v) for v in _op])), marker=self.scheme.default_symbol(color_idx), size=self.scheme.default_marker_size(color_idx), fill_color=color, line_color=color)`, returned with `seg`. Else nothing, and the docstring records the measurement.
- **TR-02.7 dash.ado declarations.** In `_dash_parse_plot_opts`'s `syntax` block, before the trailing `*` (:1238), add the line `MANGle(string asis) BARBSize(string asis) HEADlabel ///`. `sreturn local mangle`, `barbsize`, `headlabel` after `sreturn local msize` (:1403-1530). Pending block (:1320-1387): add `if `: length local mangle' local _dash_pending `"`_dash_pending' mangle"'` after the last pending line (D-02.b); and `headlabel` named by `_dash_fold_typed` on `pcspike pccapsym pcscatter pci` only (new list `_hl_named` in :2264-2269's style, D-02.e). JSON key list (:4441-4458): add `barbsize headlabel` after `mlabvposition mlabtextstyle` (mangle is pending, not written). `_dash_stylelist_keys()` (dash_parse.mata:5283): add `barbsize` after `msize` (a per-y list like msize). `_dash_rep_und_tab`: delete the `headlabel` row (:6276); add `headlabel` to `_dash_rep_unique` (:6200). The barbsize rule token `barbsize=style,0,10000 ` goes after `msize=style` in `local plot` (D-02.c, after S04 lands).
- **TR-02.8 Served copy (R2).** `_arrow_head_px`, `_arrow_head_line`, `_arrow_head_fill`, `_arrow_barb`, `_HEAD_PX`, `_PC_ONEPOINT` are `GlyphMapper` members; `default_arrow_size` a `SchemeParser` member: copied with the classes. `OpenHead`/`NormalHead` are already in both import lists (:165-166, :48047-48048). No module-level name added. `CDSView`/`BooleanFilter` (TR-02.6) are already imported where `_view_mask` builds views.
- **TR-02.9 Maps.** function_test_map.py under `# WP-31 S02 (C1): arrowheads`: `'GlyphMapper._arrow_head_px': 'test/test_arrowheads.py::TestTheHeadSize::test_default_is_the_schemes_parrow'`, `'GlyphMapper._arrow_head_line'`, `'GlyphMapper._arrow_head_fill'`, `'GlyphMapper._arrow_barb'` to their tests, `'SchemeParser.default_arrow_size'` likewise. program_coverage_map.py: no new program.
- **TR-02.10 Tests that count declarations.** test_unsupported_report_is_true.py: `PLOT_VALUES["mangle"] = ("30", "60", "pcarrow")`; `LIVE_VALUES["barbsize"] = ({"barbsize": "medium"}, {}, "pcarrow", {})`, `LIVE_VALUES["headlabel"] = ({"headlabel": "headlabel"}, {}, "pcarrow", _ML_PC)` where `_ML_PC = {"mlabel": "foreign"}` suits the pc frame (check `_spec`'s pc plot variables); counts 196 -> 199 (`# 196 -> 199: C1 mangle barbsize headlabel declared`), `test_the_blocks_were_actually_found` plot 42 -> 43 after S04's 43 -> 42 (`# 42 -> 43: C1 mangle named`). test_abbreviations.py: nothing to edit unless abbrev_truth.json lacks the three (then `test_declared_minimums_cover_stata_minimums` is silent and test_help_conformance.py:825 needs `{phang2}` entries, TR-02.11).
- **TR-02.11 Help (R3).** dash.sthlp pcarrow paragraph (grep `{ul:pcarrow` under Plot types) gains: heads sized by msize() (symbolsize parrow by default), stroked in mcolor()/mlcolor() at mlwidth(), filled in mfcolor() when barbsize() is positive, open strokes otherwise; headlabel moves the labels to the head; mangle() is accepted and named (Bokeh draws one head angle, 26.57 degrees against twoway's 28.64; and barbsize() sets open or filled, not the barb's depth) -- the M17 measured example: `pcarrow ..., mangle(45)` twoway head half-angle 45, dash 26.57. Unsupported list: add `mangle()` with that sentence; `headlabel` on pcspike/pccapsym/pcscatter/pci ("drawn on the arrow types; named on the other paired types until section 34").
- **TR-02.12 Security.** No user text reaches HTML: colours pass `parse_color_alpha`, sizes `resolve_size`; the flag is tested for presence. No new JS.

## Boundaries

- Not S02's: `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts` (called, not edited); `map_pcspike`, `map_pccapsym`, `map_pcscatter`, `map_pci` (S34 draws headlabel there); `_dash_option_rules` beyond the one `barbsize=` token after S04 lands; the applies table (S04); `mstyle`/`mlstyle` naming on arrows (unchanged); the scheme files (no stub added: `symbolsize parrowbarb zero` and `anglestyle parrow` are read as constants 0 and 28.64 in code, with a comment citing scheme-s2color.scheme:277, :1970); `_FILTER_JS`; `_generate_app_source`; `_make_figure_body`.

## Stata truth

**New extractor** `scripts/extract_arrowhead_truth.do` (head form of scripts/extract_default_base_truth.do; `ZH_` globals; twoway only), run as `DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s02 $WT/scripts/extract_arrowhead_truth.do`, writing `test/fixtures/arrowhead_truth.json` (`git add -f`). Data by `input`: `y1 x1 y2 x2` five rows `(1 1 2 2) (2 1 3 3) (3 2 4 2) (4 3 5 4) (5 4 6 6)`; a copy with row 3's `y2 = .` (`y2m`). Each graph `set scheme s2color`, exported to SVG and read with `scripts/svg_truth.py` (`svg_lines`, `svg_document`):

| Key | Command | Recorded |
|---|---|---|
| `heads.default` | `twoway pcarrow y1 x1 y2 x2` | `.Graph.plotregion1.plot1.style.marker.size.val`, `.marker.angle.val`, `.marker.backsize.val`; SVG: count of `<line>`/`<path>` strokes beyond the five shafts (two per head = 10), their lengths (px), canvas W,H |
| `heads.msize_<m>` for m in `small large vlarge 2 *2` | `..., msize(m)` | the same |
| `heads.barb_<b>` for b in `medium large` | `..., barbsize(b)` | filled `<path>`/`<polygon>` count (5), their vertex count (4) and fill colour; `marker.backsize.val` |
| `heads.mangle_45` | `..., mangle(45)` | `marker.angle.val` (45); stroke angles from the SVG |
| `heads.colours` | `..., mcolor(red) mlcolor(blue) mfcolor(green) barbsize(medium) mlwidth(thick)` | head stroke colour (blue), fill (green), stroke width vs default |
| `heads.pcbarrow` | `twoway pcbarrow y1 x1 y2 x2` | head count (20 strokes = 2 per end), colours (series colour, not black) |
| `onepoint` | `twoway pcarrow y1 x1 y2m x2` | SVG shaft count (4 or 5), stroke count, marker (`<circle>`) count vs the all-present graph's; rc |
| `headlabel` | `twoway pcarrow y1 x1 y2 x2, mlabel(x1) headlabel` and without | label `<text>` x positions vs the x1/x2 pixel positions |
| `refusals` | `pcarrow ..., barbsize(-1)`, `barbsize(abc)`, `mangle(abc)` | rc and the message line |

The 28.64-degree default and `symbolsize parrow medium` are confirmed by `marker.angle.val` and `marker.size.val` (1.52778 relative, as rcap's in WP-30).

**Truth block** `* ==== S02 C1: Arrowheads ====` in `test/test_wp31_truth.cscript` (S01's header, R1); python helpers `_u02_heads(sp, dp)` above the header:
- **U02-01** default head: dash's `__dash_head_px` column equals the pixel size dash gives `scatter ..., msize(medium)`'s marker divided by sqrt(1.25), both modes (the generated app built from `_dash_serve_spec`); twoway's `marker.size.val` is 1.52778 and `angle.val` 28.64 (fixture guard).
- **U02-02** `msize(large)`: the column scales as the fixture's stroke lengths scale (large/default ratio within 2%), both modes.
- **U02-03** `barbsize(medium)`: the end head is a `NormalHead` with `fill_color` == the series colour; default: `OpenHead`; pcbarrow default: `OpenHead` at both ends, both modes.
- **U02-04** `mcolor(red) mlcolor(blue) mfcolor(green) barbsize(medium)`: head line blue, fill green, both modes.
- **U02-05** one-point row: dash draws what the fixture's `onepoint` says (a marker, or nothing), both modes.
- **U02-06** `headlabel`: the LabelSet's x field is x2, else x1, both modes.

**Area cases** in `test/test_option_validation.cscript` (R1): **U02-07** `dash pcarrow y1 x1 y2 x2, barbsize(-1)` rc and line equal twoway's (`capture noisily` in the same run); **U02-08** `mangle(45)` rc 0 and the note names `mangle()` once; `headlabel headlabel` refused as twoway refuses a repeat (`capture noisily twoway ... , headlabel headlabel`).

## TDD test stubs

### Regression tests, `test/test_arrowheads.py` (new; red at `6370ca4` unless marked guard)

Helpers: `_arrows(fig)` = `[a for a in fig.center if isinstance(a, Arrow)]`; `_draw(type, options, df=None)` through `GM().map_<type>(figure(), ColumnDataSource(df), "y1","x1","y2","x2", options)`; both-modes classes use test_server_layer_defects `plot_for` with the pc frame and the served `make_document` as test_date_range's `_served`.

- Test: fixture stamped; `heads.default.angle` 28.64, `size.val` 1.52778 -- `TestTheFixture::test_meta_is_stamped`, `::test_twoways_defaults` (guard after 02-01).
- Test: default head `size` is the field `__dash_head_px` and the column equals `default_arrow_size / sqrt(1.25)` -- `TestTheHeadSize::test_default_is_the_schemes_parrow[type]` for pcarrow, pcbarrow, pcarrowi (red: `size == 10`).
- Test: `msize(large)` scales the column as `map_scatter`'s marker scales -- `::test_msize_scales_the_head[type-m]` (red).
- Test: `_arrow_head_px` equals `_mlabel_radius_px`'s input (one number) -- `::test_the_label_radius_reads_the_same_size` (red).
- Test: default end head is OpenHead; `barbsize(medium)` NormalHead with `fill_color` == series colour; `barbsize(0)` OpenHead -- `TestBarbsize::test_open_by_default[type]`, `::test_filled_when_positive[type]`, `::test_zero_is_open` (red for pcbarrow default and fill).
- Test: `mlcolor` wins over `mcolor` for the stroke; `mfcolor` wins for the fill; `mlwidth(thick)` widens the head line; default stroke == shaft colour, default fill == `default_color(i, "scatter")`, never `"black"` -- `TestHeadColours::test_stroke`, `::test_fill`, `::test_width`, `::test_nothing_is_black[type]` (red).
- Test: `headlabel` labels at (x2, y2), else (x1, y1) -- `TestHeadlabel::test_at_the_head[type]`, `::test_at_the_tail_without` (red).
- Test: one-point row per fixture -- `TestOnePointRows::test_as_twoway_draws[type]` (red if a marker is drawn; guard otherwise), a first point missing draws nothing -- `::test_first_point_missing_draws_nothing` (guard).
- Test: the column survives a saved move (node, `_FILTER_JS`) and a served move -- `TestTheHeadHoldsAcrossAMove::test_saved`, `::test_served` (red: no column).
- Test: an empty layer keeps the field spec and the column -- `::test_an_empty_layer_keeps_the_column` (red).
- Test: `mangle(45)` is on `s(_pending)` text path: the spec has no `mangle` key and the parser's pending block names it (reads dash.ado) -- `TestMangleIsNamed::test_pending_line_exists` (red).

### Cases in cscripts

- `test_wp31_truth.cscript` U02-01..U02-06 (red at base except fixture guards); `test_option_validation.cscript` U02-07 (red), U02-08 (red: today a generic note names mangle() too -- the assertion is the count ONE and the word `mangle()`; flips to the pending-list wording).

### Flips

- P4-18, P4-20 (Evidence table), docstring "Flipped (WP-31 C1): twoway's default head is two open strokes in the series colour; a filled head needs barbsize()".
- test_unsupported_report_is_true.py counts and entries (TR-02.10).

### Parity corpus (R8; guards)

`test/test_mode_parity.py` under `# WP-31 C1: arrowheads`: `CORPUS` "pcarrow msize(large) mcolor(red)", "pcbarrow barbsize(medium) mfcolor(green)", "pcarrowi headlabel with labels" (extend the existing pcarrowi case's options with `headlabel`); `MOVE_CORPUS` "pcarrow msize(large), dropdown to Foreign" with `_MOVES[0]`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Head size default and msize | pytest `TestTheHeadSize`; U02-01, U02-02 | `heads.default`, `heads.msize_*` | yes |
| Open vs filled, colours | pytest `TestBarbsize`, `TestHeadColours`; U02-03, U02-04 | `heads.barb_*`, `heads.colours`, `heads.pcbarrow` | yes |
| headlabel | pytest `TestHeadlabel`; U02-06 | `headlabel` | yes |
| One-point row | pytest `TestOnePointRows`; U02-05 | `onepoint` | yes |
| Moves | pytest `TestTheHeadHoldsAcrossAMove`; MOVE_CORPUS | -- | yes |
| Refusal and note | U02-07, U02-08 | `refusals` | n/a |
| Declarations | test_unsupported_report_is_true.py, test_abbreviations.py, test_help_conformance.py | abbrev_truth.json | n/a |

**Acceptance criteria**
- **AC-02.1** `__dash_head_px` equals `scatter`'s `msize` pixel size / sqrt(1.25) for default, small, large, vlarge, 2, *2, both modes, before and after a move.
- **AC-02.2** No head has `fill_color == "black"` by default; pcbarrow's default heads are OpenHead in the series colour.
- **AC-02.3** `barbsize(#>0)` gives NormalHead filled in mfcolor/mcolor/series colour; `barbsize(-1)` is refused as twoway refuses it.
- **AC-02.4** `headlabel` moves labels to x2,y2 on the three arrow types; named on the other pc types.
- **AC-02.5** U02-01..U02-08 PASS, no SKIP; `python3 -m pytest test/test_arrowheads.py test/test_phase4_plots.py test/test_pccapsym_pcarrowi.py test/test_saved_filter_layers.py test/test_server.py test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_help_conformance.py test/test_function_test_map.py -q -p no:cacheprovider` 0 failed.

## Tasks

**Commit boundary.** 02-01 to 02-04 form the one C1 commit, subject `Draw arrowheads from the marker options and the scheme, as twoway does (WP-31 C1)`, made by 02-04 on `wp31-s02` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s02`. Body: `<scratch>/02-01-failure.txt`, the measured defect (heads `OpenHead(size=10)`, pcbarrow black), what changed where (both renderers through the shared mapper), then `Regression:` lines, `Flipped: test/test_phase4_plots.py::TestMapPcbarrow::test_pcbarrow_uses_normal_head_on_both_ends -- NormalHead both ends was wrong because twoway's default head is two open strokes (C1)` and the P4-20 line, `Fixture: test/fixtures/arrowhead_truth.json (scripts/extract_arrowhead_truth.do)`, `BUGS.md: "<S01's C1 title>" (closed)`, `GAPS3: C1 Tracked`.

<task type="auto" id="02-01">
  <name>Measure twoway heads and write failing tests</name>
  <files>scripts/extract_arrowhead_truth.do, test/fixtures/arrowhead_truth.json, test/test_arrowheads.py</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints `wp31-s02`; `mkdir -p <scratch>/s02`. Create scripts/extract_arrowhead_truth.do by the "Stata truth" table (head copied from scripts/extract_default_base_truth.do lines 1-60 with ZH_ globals; `input` the five rows; each graph `graph export "${ZH_WORK}/<key>.svg", replace`; a final `python:` block using scripts/svg_truth.py's `svg_document` and `svg_lines` to count strokes, polygons, circles and text positions, writing the JSON with `_meta` and `sort_keys=True`; every SVG erased). Run it through the slot; `git add -f test/fixtures/arrowhead_truth.json`. Check `heads.default.angle == 28.64`, `heads.default.size_val` within 1e-4 of 1.52778, `heads.pcbarrow` fill colour is not black, and record `onepoint` (D-02.d). Create test/test_arrowheads.py with the classes of "TDD test stubs" (module docstring: the defect, the probe commands, D-02.d's reading of `onepoint`). Run `python3 -m pytest test/test_arrowheads.py -q -n0 -p no:cacheprovider -rf > <scratch>/s02/02-01.log 2>&1`; write `<scratch>/02-01-failure.txt` (base sha, failing nodes with reasons, guards passed). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/arrowhead_truth.json'));print(sorted(d['_meta']), d['heads']['default']['angle'])"` prints the five meta keys and `28.64`; `grep -c FAILED <scratch>/s02/02-01.log` is at least 12; `grep -c "TestTheFixture" <scratch>/s02/02-01.log | grep -v FAILED`; `test -s <scratch>/02-01-failure.txt`.]]></verify>
  <done>twoway's head geometry, colours, one-point behaviour and refusals were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="02-02">
  <name>Declare mangle barbsize headlabel</name>
  <files>dash.ado, dash_parse.mata, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[
    Make TR-02.7 in dash.ado: the `syntax` line before `*` (:1238), the three `sreturn local` lines after `sreturn local msize`, the `mangle` pending line after the last existing pending line of the plot block, the `_hl_named` list in `_dash_fold_typed` (:2264-2269 style) naming `headlabel` on pcspike pccapsym pcscatter pci, `barbsize headlabel` in the JSON key list after `mlabvposition mlabtextstyle`. In dash_parse.mata: `barbsize` after `msize` in `_dash_stylelist_keys()` (:5283-5292); delete the `headlabel` row of `_dash_rep_und_tab` (:6276); add `headlabel` to `_dash_rep_unique` (:6200) in alphabetical place. If `grep -c "BEGIN applies" dash.ado` prints 1 (S04 has landed on this worktree's base), add the token `barbsize=style,0,10000 ` after `msize=style` in `local plot`; else write the token to `<scratch>/s02/rule-token.txt` for 02-04 to insert after the merge and note it in the hand-back. Make TR-02.10's edits in test_unsupported_report_is_true.py (entries and counts with their comments). Run `python3 -m pytest test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_help_conformance.py test/test_option_validation.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[`grep -c "MANGle(string asis) BARBSize(string asis) HEADlabel" dash.ado` prints 1; `grep -c '"headlabel",    "headlabel"' dash_parse.mata` prints 0; `grep -c "_dash_pending' mangle" dash.ado` prints 1; the pytest run reports 0 failed, or fails only in test_help_conformance.py::TestEveryDashOnlyOptionIsDocumented (then 02-04's help entries fix it, and the node is listed in the hand-back).]]></verify>
  <done>mangle(), barbsize() and headlabel were declared with twoway's minimum abbreviations, written to the spec where drawn and named where not, with the counting tests moved.</done>
</task>

<task type="auto" id="02-03">
  <name>Draw the heads and flip the pins</name>
  <files>dash_render.py, test/test_phase4_plots.py, test/function_test_map.py</files>
  <action><![CDATA[
    Make TR-02.1 to TR-02.6 and TR-02.8 in dash_render.py: `default_arrow_size` on SchemeParser after `default_marker_size`; `_HEAD_PX`, `_PC_ONEPOINT`, `_arrow_head_px`, `_arrow_head_line`, `_arrow_head_fill`, `_arrow_barb` on GlyphMapper after `_add_arrow_heads`; the column in `_pc_clean_with_label` (keyword `head_px=0.0`, column added on every path, the empty frame included); the head construction in `map_pcarrow` and `map_pcbarrow`; the label coordinates per `headlabel`; the one-point marker only if the fixture's `onepoint.markers` exceeds the all-present count. Do not edit `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts`, `_add_arrow_heads`'s signature, or any pc mapper but these two. Flip P4-18 and P4-20 per Evidence (docstrings gain the Flipped sentence); append the two `Flipped:` lines to `<scratch>/s02/02-flips.txt`. Add TR-02.9's function_test_map.py entries. Run `python3 -m pytest test/test_arrowheads.py test/test_phase4_plots.py test/test_pccapsym_pcarrowi.py test/test_saved_filter_layers.py test/test_server.py test/test_function_test_map.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "size=10" dash_render.py` prints 0 within `sed -n "/def map_pcarrow(/,/def map_pccapsym/p" dash_render.py`; `grep -c "__dash_head_px" dash_render.py` is at least 2.]]></verify>
  <done>Both renderers drew every arrowhead sized by msize(), coloured and filled from the marker options and the scheme, open or filled by barbsize(), labelled at the head with headlabel, with the size travelling as a data column through moves.</done>
</task>

<task type="auto" id="02-04">
  <name>Certify, document, close C1 and commit</name>
  <files>test/test_wp31_truth.cscript, dash.sthlp, BUGS.md</files>
  <action><![CDATA[
    If `<scratch>/s02/rule-token.txt` exists, `git -C $WT merge --no-edit s3-bugs` (S04 landed) and insert the token per D-02.c. Write U02-01..U02-06 inside S01's `S02` block of test/test_wp31_truth.cscript (helpers `_u02_*` directly above the header; every file under the script's work directory, erased after), and U02-07, U02-08 in test/test_option_validation.cscript after its last case and before `// Summary` with header lines. Append the parity CORPUS/MOVE_CORPUS cases under `# WP-31 C1: arrowheads` in test/test_mode_parity.py. Run both cscripts through the driver (`WP31_ONLY=S02` for the truth script; driver form in BRIEF "Running one cscript") and `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "pcarrow or pcbarrow or pcarrowi"`. Make TR-02.11 in dash.sthlp (pcarrow paragraph; Unsupported list `mangle()` entry; headlabel sentence); TWOWAY_COVERAGE_AUDIT.md rows 71, 82, 83: append ` [WP-31 C1: corrected -- heads from msize()/mcolor()/mfcolor()/mlcolor()/mlwidth(), barbsize() and headlabel drawn; mangle() named]`. Close S01's "C1" BUGS.md entry in BRIEF's Resolution form (functions: GlyphMapper.map_pcarrow, map_pcbarrow, _pc_clean_with_label, _arrow_head_px, SchemeParser.default_arrow_size; both renderers; pinned by test/test_arrowheads.py::TestTheHeadSize::test_default_is_the_schemes_parrow, test/test_wp31_truth.cscript U02-01; fixture test/fixtures/arrowhead_truth.json; Residual, deferred (WP-31): mangle() and the barb depth are not drawn, Bokeh's head angle is fixed at 26.57 degrees (GAPS3 C1 Tracked, D-02.b)); GAPS3 §9 C1 line -> `Partly closed in WP-31 (section 02, commit <sha>): heads sized, coloured, filled, headlabel; open: mangle() and barb depth (BUGS.md "<S01's C1 title>")` if the maintainer ratified D-02.b, else Closed. CHANGELOG: replace `<!-- WP-31 C1 -->` under `### Results that change` with `- pcarrow, pcbarrow and pcarrowi heads are sized by msize() (the scheme's symbolsize parrow, 1.53 relative units, by default; they were a fixed 10 pixels), stroked in mcolor()/mlcolor() at mlwidth() and filled in mfcolor() or the series colour (pcbarrow's heads were black); barbsize() chooses open strokes or a filled head and headlabel moves the labels to the head. (WP-31, C1)`, under `### Fixed in WP-31` with `- Arrowheads follow the marker options and the scheme in both renderers. (WP-31, C1)`; under `### Changed behaviour` with `- barbsize(-1) and other bad sizes on the arrow types are refused, r(198), as twoway refuses them; dash named them in a note. (WP-31, C1)`. Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider`. Stage the files of 02-01..02-04 (`git add -f` the fixture), check the staged names, write `<scratch>/s02/msg.txt` in the boundary's form, grep it for `claude|anthropic` (0), commit, re-grep.
  ]]></action>
  <verify><![CDATA[`grep -c "U02-0[1-6] PASS" <scratch>/s02/run_test_wp31_truth.log` prints 6; `grep -c "U02-0[78] PASS" <scratch>/s02/run_test_option_validation.log` prints 2; `grep -c "SKIP" ` on both logs prints 0; `git log -1 --format=%s` ends `(WP-31 C1)`; `grep -c '<!-- WP-31 C1 -->' CHANGELOG.md` prints 0; `grep -c "(WP-31, C1)" CHANGELOG.md` prints 3; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Stata certified the heads against twoway's in both modes, the help and audit described them, C1 was closed or partly closed in BUGS.md and GAPS3 with its residual named, and one green commit on wp31-s02 was ready for the merger.</done>
</task>

## Section completion criteria

- Heads sized from `msize()` (scheme default), coloured and filled from the marker options, open or filled by `barbsize()`, `headlabel` honoured on the three arrow types, in both modes, through moves.
- `mangle()` declared and named once; `headlabel` named on the other pc types; `_dash_rep_und_tab` row gone.
- P4-18/P4-20 flipped with reasons; counts moved; U02-01..U02-08 PASS; parity cases green.
- BUGS.md C1 closed (residual named), GAPS3 Tracked rewritten, three CHANGELOG lines, one commit `(WP-31 C1)`.

## Notes

- **The size column, not a value.** `OpenHead(size=10)` was a value; `size="__dash_head_px"` is a field, so the saved filter script's derived-copy loop carries it with every row and the served redraw rebuilds it with the source. Never mix a value on one path and a field on another (the WP-30 S14 lesson, D-14c).
- **`_add_arrow_heads` stays a staticmethod with the same signature**: test_saved_filter_layers.py:315-335 calls it directly with `end=OpenHead()`.
- **Head angle.** BokehJS `OpenHead`/`NormalHead` vertices are (0.5 s, s), (0, 0), (-0.5 s, s): half-angle atan(0.5) = 26.565 degrees, stroke s*sqrt(1.25). twoway's 28.64 is `anglestyle stdarrow`. The 2.07-degree difference is the documented M17 example; do not scale the size to compensate.
- **pcarrowi** goes through `map_pcarrow`; its labels' clock positions (test_pccapsym_pcarrowi.py:256-290) are unchanged; with `headlabel` the clock applies at the head.
- **python_exec hazard**: check `~/.stata19/console/stata19.rc` after 02-01 and 02-04.
- **Shared files (R1-R13).** R1: the S02 block and two area cases. R2: no module-level name. R3: the pcarrow paragraph and the Unsupported list's two sentences. R4: three C1 markers. R5: one entry. R6: `syntax` line appended before `*`; `_dash_rep_unique` alphabetical; `_dash_stylelist_keys` extended. R7: new fixture. R8: three CORPUS, one MOVE_CORPUS. R9: two flips. R10: 196 -> 199 and 42 -> 43 with comments (after S04's 43 -> 42; the merger orders the comments 04, 02, 03). R12: S02 edits no hot function but the one rule token after S04 lands.
- **For S34 (C17).** `headlabel` is declared and reaches the spec; S34 draws it in `map_pcspike`, `map_pccapsym`, `map_pcscatter`, `map_pci` and removes the `_hl_named` list.
- **Decision for maintainer ratification.** D-02.b (mangle named, head angle documented, barb depth fixed) and D-02.d's reading of `onepoint`.
