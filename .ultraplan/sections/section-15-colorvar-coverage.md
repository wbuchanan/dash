# Section 15: colorvar() on every type twoway colours, jitter() on the four range and pc marker types

> Part of: WP-31 · GAPS3 rows: C8a · Risk: yellow · Batch: 5 · Depends on: 01 · Blocks: 17 · Tasks: 4, 1 commit · Case-id prefix: U15

## Overview

**What is wrong today.** GAPS3 C8 (GAPS3.md:127), part a: "`colorvar()` drawn on 4 types only (scatter connected rconnected dot); `jitter()` named on rscatter rcapsym pcscatter pccapsym". Evidence dash.ado:2205 (`local cv_types "scatter connected rconnected dot"`), :2218-2225 (`local jit_undrawn "rscatter rcapsym pcscatter pccapsym"` and the loop naming `jitter jitterseed jseed` there); dash_render.py:13734 and the single call site of `_apply_colorvar` at :14970 inside `map_scatter` (map_connected, map_rconnected and map_dot reach it only because they call `map_scatter`). On every other type `_dash_fold_typed` names `colorvar` and its companions in the generic note and the layer is drawn in the series colour; dash.sthlp:4140-4152 says so. twoway accepts `colorvar()` on every yxview-derived type and colours markers, lines and bars; it drops it silently on `area`/`rarea` and on the classes that set `.allowcolorvar = 0` (the fits, smoothers and kdensity from the sources; histogram and scatteri are measured in U15-01; `twoway_yxview_parse.class:206-208`: `if inlist(viewtype, "area", "rarea") | allowcolorvar != "1" { local colorvar "" }`); it refuses `colorvar()` with more than one y on scatter line tsline bar connected dot dropline spike (`:231-236`, r(198) `option colorvar() cannot be combined with multiple y variables in a <type> plot`). jitter is a FactorPlot option of every yxview type (`:755-803` `JITTER JITTERSEED`) and moves every marker the type draws.

**After this section** `_apply_colorvar` is called at the end of every glyph mapper whose type twoway colours, mapping the colour properties the glyph has (`fill_color` and/or `line_color`) and adding the key once per layer; on `area`/`rarea` and the `allowcolorvar = 0` types the option is dropped silently (nothing drawn, nothing printed -- twoway's behaviour, Q36); `_dash_fold_typed`'s `cv_types` block is replaced by the measured silent-drop list; `jitter()`/`jitterseed()`/`jseed()` jitter every marker of rscatter, rcapsym, pcscatter and pccapsym through `_apply_jitter` (:11647) with `_jitter_seed` (:11736), and leave the pending list on those types.

**Why this section (and what S17 holds).** A1 splits C8: S15 is coverage (every type, jitter); S17 (batch 6) is the option remainder (`colorlist()`, `coloruseplegend`, `colorstart/end/rule/fillonly/keysrange/keysreverse/allowmultiple/otherlabel`, `colorformissing()` alias, `colorvar(i.var)`, `clegend()`, `plegend()`, `pcycle()`). S15 lands the one call per mapper S17 then extends.

**Test order and commit rule.** One row (C8a), one commit `(WP-31 C8a)`: 15-01 tests + extractor; 15-02 dash.ado; 15-03 renderer; 15-04 certify/document/commit.

### Section decisions (binding on the executor)

- **D-15a. The silent-drop list is measured, not inferred.** `scripts/extract_colorvar_types_truth.do` runs `twoway <type> ..., colorvar(z)` for every type dash draws and records rc and whether `.Graph.plotregion1.plot1.colorvar` (or the serset's variable list) carries `z`; the types where it does not and rc is 0 form `cv_silent` in `_dash_fold_typed` (expected from the sources: area rarea lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mband mspline kdensity function pci pcarrowi; histogram and scatteri to be measured). On a `cv_silent` type dash writes nothing to the spec for `colorvar` and its companions (so the renderer never sees them) and names nothing.
- **D-15b. One key per layer.** A mapper that draws several renderers (dropline: Segment + Scatter; rcapsym: spine + two markers; rscatter: two markers; rconnected: two markers + lines; pccapsym: segment + markers; rcap: spine + caps) calls `_apply_colorvar` on each renderer with `add_key=True` for the first and `add_key=False` for the rest, so the figure has one key; twoway draws one key per layer.
- **D-15c. Which property is mapped.** `_apply_colorvar` sets `glyph.fill_color` and `glyph.line_color` to the colour spec where the glyph class has the property (`hasattr(glyph, "fill_color")`), so a `Line`/`Segment`/`MultiLine` gets its `line_color` only and a `VBar`/`Quad`/`Scatter` both -- twoway colours "markers, lines, bars" and, unless `colorfillonly` (S17), both fill and outline (`colorvar_options.sthlp:178-186`).
- **D-15d. jitter on the four types.** Every marker of the layer is moved by `_apply_jitter(x, y, pct, seed)` with the seed from `_jitter_seed(options)`; rscatter's two markers and pccapsym's two ends are jittered as separate point sets drawn from the same seeded generator in draw order (first all low/first ends, then all high/second ends) -- twoway's `gdi gm_jitter` jitters each marker it draws in sequence, so the measurement (U15-03) checks the displacement bound (|dx| <= pct% of the x range) and the count, not the exact positions (Stata's RNG is not reproduced; dash has never claimed it: test_jitter.py:22-60).
- **D-15e. The multi-y refusal.** `colorvar()` with two or more y variables on scatter line tsline bar connected dot dropline spike is refused with twoway's measured text r(198) in `_dash_process_segment` after the parse (today dash draws k layers each coloured; measured text comes from the fixture T01). Other types (rscatter etc. have fixed variable counts) are unaffected.

## Risk: [yellow] -- one call added to twenty-odd mappers, a per-type refusal and the end of a named-not-drawn surface

**Why.** Every glyph mapper changes by one call; the key placement (`_COLORVAR_LEGEND_NAME`, ColorBar) runs per layer; `_dash_fold_typed` is shared with S17.

**Risk factors.** 1. A mapper's renderer list: calling `_apply_colorvar` on a renderer whose source lacks the colorvar column (a computed source such as a histogram's) returns early (:13704 `varname not in source.data`), silently -- but twoway does draw histogram colours if measured so; then the bins' source needs the colour column (per-bin value is undefined: histogram is `allowcolorvar=0` in all likelihood; the fixture decides). 2. The hover tool: colour columns `__dash_cvar<k>_<var>` must not appear in tooltips (`_dash_hover_layer_vars` filters the `__dash` prefix already). 3. test_jitter.py:433 pins the naming of jitter on the four types. 4. `test_colorvar_truth.py` compares bins against `colorvar_truth.json` for scatter: unchanged. 5. S17 edits `_apply_colorvar`'s body in batch 6; S15 edits its call sites and the property rule only.

**Mitigation.** 1. D-15a: the renderer never receives `colorvar` on a silent type (dash.ado drops it), and a hand-written spec on such a type returns early as today. 2. Guard test in TestTooltips. 3. Flip with reason. 4. No change to the binning. 5. Disjoint hunks; S15's property rule is the `hasattr` loop replacing :13972-13975 and :14068-14071 (`glyph.fill_color = color_spec; glyph.line_color = color_spec`).

## Dependencies

- **Depends on: 01.** **Blocks: 17** (S17 extends the per-mapper call with the option remainder and reads `cv_silent`).
- **Parallel batch 5** with S16 (`_FILTER_JS`) and S14 (`_dash_connect_opt`, `_dash_recast_opt`, map_area/map_rarea bodies). S15's hunks in map_area/map_rarea: none (area/rarea are silent-drop types). S15 touches `_dash_fold_typed` and the mapper tails; S14 the mapper bodies above those tails -- `patch -p1` merges; the merger lands S14 first.

## Evidence

Anchors at `6370ca4`.

### `_dash_fold_typed` (dash.ado:2201-2297)

```
2205    local cv_types "scatter connected rconnected dot"
2206    local cv_drawn = 0
...
2210    mata: st_local("_ft", strofreal(st_global("s(colorvar)") != ""))
2211    if `: list ptype in cv_types' & `_ft' local cv_drawn = 1
2212    if !`cv_drawn' {
2213        foreach o in colorvar colordiscrete colorcuts colpalette colornlevels colormissing colorlevels colorvarminmax {
2214            mata: st_local("_ft", strofreal(st_global("s(`o')") != ""))
2215            if `_ft' local named "`named' `o'"
2216        }
2217    }
2218    local jit_undrawn "rscatter rcapsym pcscatter pccapsym"
...
2221    mata: st_local("_ft", strofreal(st_global("s(jitter)") != ""))
2222    if `: list ptype in jit_undrawn' & `_ft' {
2223        foreach o in jitter jitterseed jseed {
2224            mata: st_local("_ft", strofreal(st_global("s(`o')") != ""))
2225            if `_ft' local named "`named' `o'"
2226        }
2227    }
```
The comment at :2228-2233 is stale (GAPS3 F5, S46's) -- S15 does not touch it beyond the lines it deletes.

### The renderer

- `_apply_colorvar(self, fig, renderer, source, options, add_key=True)` (:13664-14103): returns at :13704 when `varname not in source.data`; the discrete path sets `glyph.fill_color = color_spec; glyph.line_color = color_spec` (:13972-13975), the continuous path likewise (:14068-14071); the key is a `Legend` (:14007) or `ColorBar` (:14033).
- The one call: `map_scatter` :14970 `self._apply_colorvar(fig, r, plot_source, options, add_key=colorvar_key)`. `map_connected` (:15123-15165) calls `map_line` then `map_scatter`; `map_rconnected` (:18856-18942) calls `map_scatter(..., colorvar_key=False)` for the second end; `map_dot` (:18910-18937) returns `map_scatter(...)`.
- Mappers with no call (the renderer each returns): `map_line` :15002 (Line via `_dash_join_glyph`), `map_bar` :15272 (VBar), `map_spike` :15558 (Segment, `_apply_line_opts(r, options, role="aline")` :15607), `map_dropline` :18943 (Segment + Scatter), `map_rbar` :18512 (VBar), `map_rspike` :18650 (Segment), `map_rcap` :18693 (Segment + two `dash_cap` Scatters), `map_rline` :18771 (two Lines), `map_rcapsym` :19094 (Segment + two Scatters), `map_rscatter` :20227 (one Scatter over a stacked source `x`,`y` of both ends, :20323-20335), `map_tsline` :20167, `map_tsrline` :20196, `map_pcspike` :19363, `map_pcarrow` :19683, `map_pcbarrow` :19777, `map_pcscatter` :19478 (Scatter over `dot_src`), `map_pccapsym` :19863 (Segment + Scatter :19957), `map_scatteri` :19216 (literal: no data variable; silent-drop candidate -- the fixture decides), `map_histogram` :17911 (Quad over bins).
- Jitter: `_apply_jitter(x_arr, y_arr, jitter_pct, seed)` (:11647-11735), `_jitter_seed(options)` (:11736-11770), `_build_jitter_source` (:12264-12315) for a single scatter; `map_dropline` jitters inline (:18995-19003) and `map_scatteri` (:19260-19268) -- the pattern S15 copies into the four mappers.

### twoway's rule (research/stata-ground-truth.md §1.2)

`twoway_yxview_parse.class:185-201` declares `COLORVar(string)` and its companions for every yxview type; `:206-208` drops it silently on area/rarea and when `.allowcolorvar != 1`; `:213-218` `i.var`; `:231-236` the multi-y refusal with its exact text (quoted in Evidence above). `colorvar_options.sthlp:73-75`: "the color of the markers, lines, bars, ... be determined by the values of colorvar".

### Fixtures on disk

`colorvar_truth.json`, `colorvar_qualifier_truth.json` (scatter bins and domains, WP-29/30). New: `colorvar_types_truth.json`.

### Pinned tests to flip (never delete)

- test/test_jitter.py:433ff (the test whose docstring says "What it does instead, measured 24sep2026: the value is named in the note" for the four types) -- flip to "drawn, not named" with the reason; `test_jitterseed_is_not_reported_as_unsupported` (:347) is unchanged (pending block counts: the four-type naming lives in `_dash_fold_typed`, not the block).
- test/test_help_claims_7.cscript HC7-02 (program_coverage_map: `_dash_fold_typed` is pinned there) -- re-run; if it asserts the note on a non-cv type, flip.
- test/test_help_conformance.py: the Unsupported section has no colorvar entry for the type restriction; the paragraph at dash.sthlp:4140-4152 is S15's (R3) and the `colorvar() sub-options` entry (:5048-5054) is S17's.
- TWOWAY_COVERAGE_AUDIT.md rows 28 ("colorvar() outside scatter, connected, rconnected, and dot markers"), 61-65, 68, 72, 74, 77, 79, 85, 98, 118.
- test/test_unsupported_report_is_true.py: `jitter` is already LIVE on scatter; no count moves (no pending-block line changes). `_dash_fold_typed`'s naming is outside the blocks.

## User stories

- US-15.1 As a Stata user pasting `twoway bar mpg weight, colorvar(rep78)`, I want the bars coloured by rep78 with twoway's key.
- US-15.2 As a Stata user, I want `line`, `spike`, `dropline`, `rbar`, `rcap`, `rspike`, `rline`, `rscatter`, `rcapsym`, `tsline`, `tsrline` and the pc types coloured by `colorvar()`.
- US-15.3 As a Stata user, I want `lfit ..., colorvar(z)` to draw the fit in the series colour and say nothing, as twoway does.
- US-15.4 As a Stata user, I want `rscatter lo hi x, jitter(5)` and `pcscatter ..., jitter(5)` to jitter the markers.
- US-15.5 As a Stata user, I want `scatter y1 y2 x, colorvar(z)` refused as twoway refuses it.

## Business requirements

- BR-15.1 Every type twoway colours by `colorvar()` is coloured in both modes with one key per layer; the companions dash already draws (`colordiscrete colorcuts colorlevels colorvarminmax colpalette colornlevels colormissing`) apply there too.
- BR-15.2 On the silent-drop types nothing is coloured and nothing is printed.
- BR-15.3 `jitter()`, `jitterseed()`, `jseed()` move every marker of rscatter, rcapsym, pcscatter, pccapsym and are not named.
- BR-15.4 `colorvar()` with several y variables on the eight types is refused with twoway's words and rc.

## Technical requirements

- TR-15.1 **dash.ado `_dash_fold_typed`**: replace :2205-2217 by `local cv_silent "<measured list>"` and: `if `: list ptype in cv_silent' { foreach o in colorvar colordiscrete colorcuts colpalette colornlevels colormissing colorlevels colorvarminmax { sreturn local `o' "" } }` (drop silently: the JSON writer then writes none); delete :2218-2227 (the jitter naming). Comment: `// WP-31 C8a: colorvar() is drawn on every type twoway colours (test/fixtures/colorvar_types_truth.json); on cv_silent twoway drops it without a word (twoway_yxview_parse.class:206-208), and so does dash.`
- TR-15.2 **dash.ado multi-y refusal**: in `_dash_process_segment` after `_dash_fold_typed` (:5594), `if `: list ptype in "scatter line tsline bar connected dot dropline spike"' & nser > 1 & colorvar given { _dash_say("err", <fixture T01 text>); exit 198 }` -- the text is typed once from `colorvar_types_truth.json` T01 and proved by U15-04. (The segment's y count is `nser`, the variable `_dash_connect_opt` already receives.)
- TR-15.3 **Renderer property rule**: replace :13972-13975 and :14068-14071 by a loop `for _p in ("fill_color", "line_color"): if hasattr(glyph, _p): setattr(glyph, _p, color_spec)` (D-15c); S17 later narrows it for `colorfillonly`.
- TR-15.4 **Renderer call sites** (each `self._apply_colorvar(fig, r, <source>, options[, add_key=False])` at the mapper's end, before its hover tool, with the source the renderer draws from): `map_line` (the `_dash_join_glyph` renderer: Bokeh's `Line` glyph takes one `line_color`, not a field, so Line-glyph layers (line, rline, tsline, tsrline, connected's line, rconnected's lines) keep the glyph and take one scalar colour per layer, that of the first finite row's mapped level -- D-15f below; the join rebuild's null colour values at synthetic vertices are therefore never mapped), `map_bar` (VBar, `clean_source`), `map_spike` (Segment), `map_dropline` (Segment with add_key True, Scatter add_key False -- both from the dropline's own `_dl_cols` source: add the colour column to `_dl_cols` as `xvar`/`yvar` are added :19004-19008), `map_rbar`, `map_rspike`, `map_rcap` (spine; caps add_key False), `map_rcapsym` (spine; two markers False), `map_rscatter` (the stacked source: add the colorvar column twice, once per end, in the stack at :20323-20335), `map_pcspike`, `map_pcarrow`/`map_pcbarrow` (the Arrow's line_color is on the Arrow model, not a glyph: colour the segment renderer; heads are S02's -- leave them), `map_pcscatter` (`dot_src` gets the column stacked for both ends), `map_pccapsym` (segment True; markers False), `map_histogram`/`map_scatteri`: only if the fixture shows twoway colours them (else nothing).
- **D-15f. Line glyphs take one colour per layer.** Bokeh's `Line`/`Segment`-as-path glyphs cannot vary colour along the path; twoway colours a line by the level of each segment's start. dash colours the whole line by the layer's FIRST finite row's mapped colour (a scalar `line_color`: build the colour spec as today, then read `palette[bin_index_of_first_row]` -- no Bokeh transform), adds the key for the layer, and says nothing (Q36 forbids a note for a drawn option); the difference is documented in the help paragraph (M17: "where Bokeh cannot express it, document with a measured example"). Segment glyphs (spike, dropline, rspike, rcap, rcapsym, pcspike, pccapsym) ARE vector-coloured (one segment per row).
- TR-15.5 **Jitter** in `map_rscatter`, `map_rcapsym`, `map_pcscatter`, `map_pccapsym`: after the marker arrays are built and before `fig.scatter`, `_jit = _stat_option_float(options, "jitter", 0.0, "<type>", lo=0.0, hi=100.0)`; `if _jit: xs, ys = _apply_jitter(xs, ys, min(100.0, _jit), _jitter_seed(options))` on the stacked marker arrays (both ends in one call, D-15d); the spine/segment keeps the unjittered coordinates (twoway jitters markers only: `_draw_points` under `gm_jitter`).
- TR-15.6 **Tests/pins**: test_unsupported_report_is_true.py unchanged (no block line changes); function_test_map.py unchanged (no new function; the property loop is inside `_apply_colorvar`); program_coverage_map.py unchanged.
- TR-15.7 **Help** (R3, S15 owns dash.sthlp:4140-4152 and the "Which observations" paragraph's first sentence): rewrite to "dash draws it on every plot type twoway colours -- markers, bars, spikes, drop lines, range bars and caps are coloured observation by observation; a line (line, rline, tsline, tsrline, the connecting line of connected and rconnected) takes one colour, that of its first observation's level, where twoway colours each segment (measured: `twoway line mpg weight, colorvar(rep78) sort` draws 5 colours along one line); on area, rarea, the fits and smoothers, kdensity, function, pci and pcarrowi twoway drops colorvar() without a word, and so does dash."

## Boundaries

- No `_apply_colorvar` body change beyond TR-15.3 (S17 owns the option readers in batch 6).
- No `_FILTER_JS` (S16), no `_dash_connect_opt`/`_dash_recast_opt`/map_area/map_rarea bodies (S14).
- `colorlist()`, `coloruseplegend`, the undeclared colour options, `colorformissing()`, `colorvar(i.var)`, `clegend/plegend/pcycle`: S17.
- Arrow heads' colour: S02 (batch 1) owns `map_pcarrow`/`map_pcbarrow` heads; S15 colours their segments only.
- Weighted marker sizes: S20; dot rows: S18 (S18 colours the rows through the same call S15 adds to `map_dot`'s marker; see S18 Notes).

## Stata truth

New `scripts/extract_colorvar_types_truth.do` → `test/fixtures/colorvar_types_truth.json`; `sysuse auto`, `gen z = rep78`, `gen lo = mpg-2`, `gen hi = mpg+2`, `gen y2 = mpg+5`, `gen x2 = weight+500`:
- `C_<type>` for every type in the m6 list of test/test_twoway_option_parity.cscript:4605 (the per-type command forms): `capture noisily twoway <cmd>, colorvar(z) name(c1)`; record `rc`, `.c1.plotregion1.plot1.colorvar` (string), the serset variable names (`.plot1.serset` → `serset summarize`), and whether `.c1.plotregion1.plot1.levelvar` is set; `cv_silent` = the types with rc 0 and an empty colorvar.
- `T01` `twoway scatter mpg price weight, colorvar(z)` rc and message; `T02` `twoway line mpg price weight, colorvar(z)`.
- `L01` `twoway line mpg weight, colorvar(z) sort` → `graph export` SVG: the number of distinct stroke colours among the path elements (the measured example for the help).
- `J01..J04` `twoway rscatter lo hi weight, jitter(5) jitterseed(1)`, `rcapsym`, `pcscatter mpg weight y2 x2`, `pccapsym`: the SVG marker positions vs the unjittered run (count equal, max |dx| <= 5% of the x range, at least one marker moved).
`_meta`, `git add -f`, test_fixtures_are_committed.py.

## TDD test stubs

New `test/test_colorvar_coverage.py`:
- Test: for each type in the fixture's coloured set (parametrised), a spec with `colorvar(rep78)` yields a renderer whose glyph `fill_color` or `line_color` is a `{"field","transform"}` spec (Segment/VBar/Quad/Scatter) or, for Line glyphs, a scalar equal to the first row's mapped colour, both modes -- `TestEveryColouredType::test_coloured[mode-type]` (red for every type but scatter connected rconnected dot).
- Test: exactly one colour key per layer for the multi-renderer types -- `::test_one_key[mode-type]` (red).
- Test: for each silent type, the renderer keeps the scheme colour, no key, no warning -- `TestSilentTypes::test_nothing_drawn_nothing_said[mode-type]` (guard: the renderer never saw the option; the ado test below is the red one).
- Test: dash.ado's `_dash_fold_typed` has `cv_silent` equal to the fixture's silent set and no `cv_types`/`jit_undrawn` -- `TestTheAdoText::test_lists_match_the_fixture` (red).
- Test: `__dash_cvar` columns never reach tooltips -- `TestTooltips::test_no_colour_column[mode]` (guard).
- Test: jitter on the four types moves markers within pct% of the range, same seed → same picture, spine unmoved -- `TestJitterFourTypes::test_moves[mode-type]`, `::test_seeded`, `::test_spine_unjittered` (red).
- Test: the Line one-colour rule equals the first finite row's bin colour -- `TestLineOneColour::test_first_row` (red).
- Test: fixture meta -- `TestTheFixture::test_meta` (guard).

cscript, block `* ==== S15 C8a: colorvar coverage and jitter ====` (the section's one row; appended by 15-04, the closing task, A14):
- U15-01 for every type in the fixture: `capture noisily dash <cmd>, colorvar(z) name(u15)`: rc equals twoway's; the log has no `ignoring unsupported option(s): colorvar` line; on the coloured types the spec carries `"colorvar":"z"`, on the silent ones it does not.
- U15-02 `dash bar mpg weight, colorvar(z)`: the python render's VBar `fill_color` is a field spec in both modes.
- U15-03 `dash rscatter lo hi weight, jitter(5) jitterseed(1)`: no note; render markers within 5% of range; twoway J01 moved too.
- U15-04 `dash scatter mpg price weight, colorvar(z)`: rc 198, message equals twoway's T01 (`cert_log_has`).
- U15-05 `dash lfit mpg weight, colorvar(z)`: rc 0, no note, no `colorvar` in the spec (silent drop).

Parity (R8): CORPUS `_case("bar colorvar", [plot_for("bar", {"colorvar":"rep78"})])`, `_case("rcap colorvar", ...)`, `_case("line colorvar", ...)`, `_case("rscatter jitter", ...)`, `_case("pccapsym jitter", ...)`; MOVE_CORPUS `_case("bar colorvar after a move", ...)`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| coloured types | pytest TestEveryColouredType; U15-01/02 | colorvar_types_truth C_* | yes |
| silent types | pytest TestSilentTypes/TestTheAdoText; U15-05 | C_* | yes |
| multi-y refusal | U15-04 | T01 T02 | n/a |
| jitter four types | pytest TestJitterFourTypes; U15-03 | J01-J04 | yes |
| line one colour | pytest TestLineOneColour; help example | L01 | yes |

AC-15.1 stubs green; AC-15.2 U15-01..05 PASS; AC-15.3 dash.sthlp:4140-4152 rewritten with the measured L01 example; AC-15.4 audit rows 28, 61-65, 68, 72, 74, 77, 79, 85, 118 annotated `[WP-31 C8a, commit pending: corrected -- colorvar() drawn on every type twoway colours; jitter() on rscatter rcapsym pcscatter pccapsym]` (the merger's step k.3b rewrites `pending` to the landed sha).

## Tasks

**Commit boundary.** 15-01..15-03 steps; 15-04 commits `Draw colorvar() on every plot type twoway colours and jitter() on rscatter, rcapsym, pcscatter and pccapsym (WP-31 C8a)` on `wp31-s15`.

<task type="auto" id="15-01">
  <name>Write the failing coverage tests and the per-type truth extractor</name>
  <files>test/test_colorvar_coverage.py, scripts/extract_colorvar_types_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_colorvar_types_truth.do on scripts/extract_default_base_truth.do's skeleton with the probes C_<type> (loop over the m6 command list copied from test/test_twoway_option_parity.cscript:4605, each `capture noisily twoway <cmd>, colorvar(z) name(c1, replace)`, recording rc, `.c1.plotregion1.plot1.colorvar` and the serset variable names), T01, T02, L01 (SVG via `graph export`, distinct stroke colours counted with test/cert_svg.do's reader) and J01-J04 (marker positions with and without jitter); run through the slot wrapper; `git add -f test/fixtures/colorvar_types_truth.json`; register it. Create test/test_colorvar_coverage.py with every stub (TestEveryColouredType, TestSilentTypes, TestTheAdoText, TestTooltips, TestJitterFourTypes, TestLineOneColour, TestTheFixture), parametrising the type lists FROM the fixture. Run `python3 -m pytest test/test_colorvar_coverage.py -q -p no:randomly > <scratch>/15-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/15-01-failure.txt prints >= 20; python3 -c "import json;d=json.load(open('test/fixtures/colorvar_types_truth.json'));print(sorted(t for t in d if t.startswith('C_') and d[t]['rc']==0 and not d[t]['colorvar']))" prints the silent list (expected to include C_area, C_rarea, C_lfit, C_kdensity, C_pci).]]></verify>
  <done>The coverage tests fail against 6370ca4 and twoway's per-type colorvar acceptance, the multi-y refusal text and the jitter displacements are committed.</done>
</task>

<task type="auto" id="15-02">
  <name>Replace the type lists in dash.ado and add the multi-y refusal</name>
  <files>dash.ado, test/test_jitter.py</files>
  <action><![CDATA[In `_dash_fold_typed` (dash.ado:2201-2297) apply TR-15.1: replace :2205-2217 with the `cv_silent` list copied from the fixture and the silent-drop `sreturn local <o> ""` loop; delete :2218-2227 (jit_undrawn naming); update the program's header comment. In `_dash_process_segment` after :5594 add TR-15.2's refusal with T01's text typed from the fixture. Flip test/test_jitter.py's four-type naming test (:433ff) to assert that the note names none of jitter/jitterseed/jseed on rscatter rcapsym pcscatter pccapsym (docstring: `Flipped (WP-31 C8a): twoway jitters every marker (colorvar_types_truth.json J01-J04); dash draws it now`). Run `python3 -m pytest test/test_colorvar_coverage.py::TestTheAdoText test/test_jitter.py test/test_unsupported_report_is_true.py -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed; `grep -c "cv_types\|jit_undrawn" dash.ado` prints 0; `grep -c 'local cv_silent' dash.ado` prints 1.]]></verify>
  <done>dash.ado hands colorvar() and jitter() to the renderer on every type twoway draws them on, drops colorvar() silently where twoway does, and refuses the multi-y form with twoway's words.</done>
</task>

<task type="auto" id="15-03">
  <name>Route every glyph mapper through the colour mapper and jitter the four types</name>
  <files>dash_render.py</files>
  <action><![CDATA[Apply TR-15.3 (the `hasattr` property loop at :13972-13975 and :14068-14071), TR-15.4 (one `self._apply_colorvar(...)` call per mapper listed, with the add_key rule D-15b and the Line one-colour rule D-15f -- implement D-15f as a small method `GlyphMapper._colorvar_scalar(source, options)` that runs the same binning as `_apply_colorvar` on the first finite row and returns a hex colour, or None; a method, so no copy-list entry) and TR-15.5 (jitter in map_rscatter :20323-20335, map_rcapsym :19170-19190, map_pcscatter :19520-19530, map_pccapsym :19950-19960 before their `fig.scatter` calls). Run `python3 -m pytest test/test_colorvar_coverage.py test/test_colorvar_truth.py test/test_colorvar_forms.py test/test_colorvar_legend.py test/test_glyphs.py test/test_jitter.py test/test_mode_parity.py -k "colorvar or jitter" -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed; `grep -c "self._apply_colorvar(" dash_render.py` prints >= 18.]]></verify>
  <done>Both renderers colour every type twoway colours by colorvar() with one key per layer and jitter the markers of the four range and pc types.</done>
</task>

<task type="auto" id="15-04">
  <name>Certify, document and commit C8a</name>
  <files>test/test_wp31_truth.cscript, dash.sthlp, TWOWAY_COVERAGE_AUDIT.md</files>
  <action><![CDATA[Append `* ==== S15 C8a: colorvar coverage and jitter ====` (U15-01..U15-05) above the marker line (after S14's blocks) and run with `WP31_ONLY=S15` through the slot wrapper. Rewrite dash.sthlp:4140-4152 per TR-15.7 with L01's measured count in the example sentence. TWOWAY_COVERAGE_AUDIT.md rows 28, 61, 62, 63, 64, 65, 68, 72, 74, 77, 79, 85, 118: append the C8a annotation `[WP-31 C8a, commit pending: corrected -- ...]`. Close the C8a BUGS.md entry (Resolution form; pinned by test/test_colorvar_coverage.py::TestEveryColouredType::test_coloured[saved-bar], test/test_wp31_truth.cscript U15-01; fixture colorvar_types_truth.json), write the GAPS3 line `- **C8a Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b rewrites `pending` to the landed sha), replace the `<!-- WP-31 C8a -->` markers (Results: "bar mpg weight, colorvar(rep78): bars coloured by rep78 with a key (was: series colour, named)"; Changed behaviour: "scatter y1 y2 x, colorvar(z) is refused, twoway's `option colorvar() cannot be combined with multiple y variables in a scatter plot`"). Run `python3 -m pytest test/test_colorvar_coverage.py test/test_help_conformance.py test/test_help_claims_7.py test/test_tracking_documents.py -q`; commit with the BRIEF body; grep for `claude|anthropic`.]]></action>
  <verify><![CDATA[Stata log shows "U15-01 PASS" .. "U15-05 PASS"; pytest 0 failed; `git log -1 --format=%s` ends "(WP-31 C8a)"; `grep -c 'C8a Tracked:\*\* Closed in WP-31' GAPS3.md` prints 1; `grep -c "every plot type twoway colours" dash.sthlp` prints 1.]]></verify>
  <done>C8a is closed in one commit: colorvar() coverage and the four-type jitter, with tests, fixture, help, audit, BUGS.md, GAPS3 and CHANGELOG lines.</done>
</task>

## Section completion criteria

- Stubs green; U15-01..05 PASS; test_jitter flip with reason; no count changes needed (verified by test_unsupported_report_is_true).
- `cv_silent` in dash.ado equals the fixture's silent set; every coloured mapper calls `_apply_colorvar` once per renderer with one key.
- Help paragraph rewritten with the measured example; audit rows annotated; BUGS/GAPS3/CHANGELOG closed.

## Notes

- **Renderer order:** `_apply_colorvar` after `_apply_marker_opts`/`_apply_line_opts`/`_apply_fill_opts` and before the hover tool, as in `map_scatter`, so an explicit `mcolor()` is overridden by the mapping as twoway's colorvar overrides the series colour.
- **Copy list (R2):** nothing module-level is added; `_colorvar_scalar` is a method.
- **Fixture rule (R7):** the `cv_silent` list in dash.ado is typed once from the fixture and pinned by `TestTheAdoText::test_lists_match_the_fixture`.
- **Served app:** the colour column `__dash_cvar<k>_<var>` is written on the mapper's own source in both modes; `_dash_redraw_for` re-runs the mapper so moves recolour.
- **python_exec hazard** as in every section.
- **Security:** `colorvar` reaches a Bokeh field only after `_dash_is_stata_name` (:13710); the stacked sources copy the column by name.
- **Merge rules cited:** R1, R3 (S15 owns dash.sthlp:4140-4152), R7, R8, R9, R12 (S15 is batch 5's `_apply_colorvar`/`_dash_fold_typed` owner).
- **Commit body lines:** `Regression: test/test_colorvar_coverage.py::TestEveryColouredType::test_coloured[saved-bar] -- failed at 6370ca4 with <text>`; `Flipped: test/test_jitter.py::<node> -- "named on the four types" was wrong because twoway jitters them (colorvar_types_truth.json J01-J04)`; `Fixture: test/fixtures/colorvar_types_truth.json (scripts/extract_colorvar_types_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS3: C8a Tracked`.
- **Decisions for maintainer ratification:** D-15a (measured silent list, dropped in dash.ado), D-15f (one colour per Line glyph, documented as an M17 difference).

## Addendum (14oct2026, DECISIONS D14): batch 1-4 gaps added to this section

### A3d: jitter() takes jit, shorter than twoway's minimum

**Gap.** dash's plot `syntax` declares `JITter`, so `jit()` is taken; twoway's minimum for jitter() is longer and `twoway scatter mpg weight, jit(5)` is refused as an unknown option (found by S08; pinned today in test/test_abbreviations.py `_SHORTER_THAN_TWOWAY`).

**Requirement.** Measure twoway's minimum for jitter() (each prefix `j`..`jitter` on scatter, rc and first error line); raise dash's declaration to it so every spelling twoway refuses is refused with twoway's rc and line, and every spelling it takes is taken. Remove `jitter` from `_SHORTER_THAN_TWOWAY` (flip, with a `Flipped:` line); regenerate test/fixtures/abbrev_truth.json only through scripts/extract_abbrev_truth.do if its counts change. Add a Changed-behaviour line naming the refused spelling.

**Tests.** test/test_abbreviations.py (the live pin) and a `U15-<k>` case in test/test_abbreviations.cscript comparing `dash scatter mpg weight, jit(5)` with twoway's. Fits S15 because S15 already edits jitter() (the four range types) in batch 5.

**Process (binding, as for every row).** Task 1 of this row writes the failing tests and saves `<scratch>/15-A3d-failure.txt`; then the fix; then ONE commit with subject ending `(WP-31 A3d)`. The closing task flips the BUGS.md entry "jitter() takes jit, shorter than twoway's minimum" to `- [x]` with a Resolution in the BRIEF's closed form ending `Closes GAPS3 A3 (WP-31, A3d).`, deletes the `"A3d":` line from `WP31_OPEN` in test/test_tracking_documents.py, rewrites GAPS3.md's `- **A3d Tracked:**` line to `Closed in WP-31, BUGS.md "jitter() takes jit, shorter than twoway's minimum", commit pending.`, and replaces `<!-- WP-31 A3d -->` in place under `### Changed behaviour (may need your do-files changed)` with a line ending `(WP-31, A3d)`. Measure twoway first (an extract script or a live probe in the cscript); where the measurement contradicts this addendum, the measurement wins and the deviation is recorded. Refusal/message cases go to the area cscript under the `U15` prefix; drawing comparisons go to a `* ==== S15 A3d: ... ====` block in test/test_wp31_truth.cscript. dash replaces twoway (DECISIONS D13): never use `dash twoway` in a probe.
