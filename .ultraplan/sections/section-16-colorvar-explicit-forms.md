# Section 16: colorvar explicit forms (X2)

> Part of: WP-28 · Gaps: X2 · Risk: yellow · Batch: 2 · Depends on: 02 · Blocks: 12, 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **02** · Blocks **12, 19** · Risk **yellow** · Commits: one commit (X2) → CHANGELOG `Results that change`

- D10: drop the phantom "rebuild the Mata library" step in 16-03/16-04 (no .mlib exists; dash_parse.mata is run from dash.ado).
- Use `svg_document` for per-marker order; `svg_fills`/`cert_svg_fills` give per-colour counts.
- D7: split 16-01 and 16-07.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

GAPS2 X2 measured, at `91d97be`: "`colorvar(rep78) colordiscrete colorcuts(2 4)` gives ≤2 / 2–4 / >4, so rep78 = 1, 3 and 5 are coloured as ranges where twoway draws them gray. `colorcuts(0 2 4)` keeps an empty '≤0' level. No note is printed for either case. `colorlevels()`, `colorrule()`, `colorstart()`, `colorend()` and `colorvarminmax` are only named in a note (dash.sthlp:2501-2503). dash.ado declares no `zlabel()`, `ztitle()` or `zscale()`." The mapper `GlyphMapper._apply_colorvar` (`dash_render.py:6338-6655`) takes its interval path whatever `colordiscrete` says (6456-6479), never looks at the column minimum, reads `colornlevels` (dash's spelling) but not `colorlevels` (Stata's), and the ado layer sends `colorlevels()` through `*` to the ignoring note and refuses a second `colorvarminmax` from a table of undeclared options.

After this section the explicit forms match Stata's `colorvar_options.sthlp:95-140` exactly: under `colordiscrete` with `colorcuts()` each cut IS a level and every other value joins missing in gray; cuts below the column minimum are dropped, and the minimum is used if all are below it; `colorlevels(#)` makes #−1 equal cuts (Stata's spelling of what dash already does under `colornlevels()`); `colorvarminmax` adds the minimum and maximum to the cuts and to the key's ticks; `colorcuts()` with `colorlevels()` is refused with r(198) as twoway refuses it; and the graph-level `zlabel()`, `ztitle()` and `zscale()` are declared in dash.ado and drawn on the colour key — the title of the Legend or ColorBar, the ColorBar's ticks and label text, and the ColorBar's mapper range, log scale and direction. Once honoured, none of these prints anything (DISCOVERY Q22); what a z option asks for that the key cannot draw is named once through `_dash_report_suboptions`.

What does NOT change (DISCOVERY Q5, PRD §7): the unbinned continuous default — a 256-colour palette and a ColorBar — stays, and dash.sthlp:2503-2507 stays; `colorrule()`, `colorstart()` and `colorend()` stay named in the note. So there is no CHANGELOG "Results that change" line for the default; there are lines for the two measured symptoms.

These changes share one section because they are one function and one option family: the level arithmetic moves out of `_apply_colorvar` into two module-level helpers both renderers copy, dash.ado gains the two plot options and three graph options in every place a plot or graph key is listed, and one Stata-measured fixture of twoway's marker fill groups pins the whole grid.

**Test order (CLAUDE.md rule 7): task 16-01 writes every failing test for the section**, runs them against the unmodified tree and records the failure in its commit message. Tasks 16-02 to 16-07 turn them green; 16-08 closes the BUGS.md entry and updates the help and CHANGELOG.

## Risk: [yellow] — one mapper function rewritten in the middle, five option keys threaded through eleven ado/Mata sites, and a new SVG fixture whose marker order must be proved before it is trusted

**Why.** `_apply_colorvar` is copied whole into the served app (`GlyphMapper` at 24698-24700), so the Python change reaches both modes for free, but the graph-level z options must reach the mapper from two different figure builders (saved `_make_figure_body` 21938, served template 26120) that the audit already found order things differently ([A §0.2]). The ado side has seven copies of the graph-key list; one missed copy silently drops a z option in one code path only.

**Risk factors.**
1. The seven `foreach` lists (dash.ado 3951, 4481, 4512, 4602, 4656, 4687, 4942) and the two syntax/sreturn pairs must all gain the same three keys, or a z option survives registration but is dropped at JSON time (or the reverse).
2. `colorvarminmax` leaves Mata's `_dash_rep_und_tab` (4362); if it is not added to `_dash_rep_unique` (4271-4292) the "given twice" refusal `test_twoway_option_parity.cscript:1507-1508` pins is lost.
3. Twoway draws markers in observation order, which the fixture relies on to compare a factor per observation; it is asserted by a self-check probe, not assumed.
4. `test_function_audit.py` names the nested `_assign_cut`/`_assign_nlev` closures in `test/function_test_map.py:107-108`; moving the arithmetic to module level changes the qualnames and `test_function_test_map.py` fails until the map is updated in the same commit.
5. S17 edits one line of the same function (the string path at 6527). Disjoint hunks, but both agents must stay out of each other's region.

**Mitigation.** A cscript asserts every z option and both new plot options register, reach the spec and are drawn with no note; the fixture's self-check probe (`colorvar(foreign) colordiscrete`) proves marker order against the data before any other probe is trusted; the function map is edited in the task that moves the closures; the boundaries below name S17's line.

## Dependencies

- **Depends on:** 02 — `scripts/svg_truth.py` (`svg_document(path)` with its `circles`/`paths` lists in document order, `svg_marker_fills(path) -> {colour: {"n", "kinds", "opacity"}}`, `svg_texts(path) -> list[dict]`) and `test/cert_svg.do` (`cert_svg_export [, name() file()]` → `r(rc)`, `r(file)`; `cert_svg_fills, file() [markers list()]` → `r(n)` distinct colours, `r(colours)`, `r(list)` a TSV `colour n kinds opacities`; each clobbers r(), as `cert_file_has` does; loaded after `cscript` and before any `cd`; `exit 222` SKIP when `c(python_exec)` is empty). These are S02's fixed names as its section file states them.
- **Blocks:** 19 (closeout).
- **Parallel batch:** 2. **Can run with:** 11, 12, 13, 14, 15, 17. The only shared edit region is `_apply_colorvar`'s string path (S17, one line at 6527); see Boundaries.
- Why: everything else this section touches — the numeric paths of `_apply_colorvar`, the colorvar option keys in dash.ado, the z keys, `_dash_rep_cat` — is read by no other section.

## Evidence

### The mapper: `GlyphMapper._apply_colorvar` (`dash_render.py:6338-6655`, only caller `map_scatter` 7229)

Option reads (research [A §X2]): `force_discrete` 6376, `colornlevels` 6422-6428, `colorcuts` 6430-6437 (split on blanks, sorted, `None` on any non-number), numeric test 6439-6447, then

```python
 6449        needs_binning = cuts is not None or nlevels is not None
 6450        use_discrete  = force_discrete or not is_numeric or needs_binning
 ...
 6456            if is_numeric and (force_discrete or needs_binning):
 6457                color_field = f"_cvar_{varname}_bin"
 6458
 6459                if cuts is not None:
 6460                    # User-supplied boundaries: bins are (-∞, c0], (c0, c1], …, (cN, +∞)
 6461                    n_bins = len(cuts) + 1
 ...
 6473                    def _assign_cut(v: float) -> str:
 6474                        if np.isnan(v):
 6475                            return "__missing__"
 6476                        idx = int(np.searchsorted(cuts, v, side="left"))
 6477                        return labels[min(idx, n_bins - 1)]
```

`colordiscrete` is read into `force_discrete` and then only decides *whether* to bin, never *how*: with `cuts` present the interval branch runs. Nothing compares a cut with `np.nanmin(col_vals)`. The `colornlevels` branch (6481-6498) is already Stata's `colorlevels(#)` arithmetic — `edges = np.linspace(lo_v, hi_v, nlevels + 1)`, `inner = edges[1:-1]`, `searchsorted(inner, v, side="left")` — under dash's own spelling. The plain `colordiscrete` branch (6500-6511) keys one level per distinct value with value labels through `_vlookup` (6396-6407). The string path is 6517-6533 (S17's line 6527). Palette 6539-6555; the discrete key is a `Legend(items, title=var_display, name=_COLORVAR_LEGEND_NAME)` added at 6566-6597 with one invisible swatch renderer per factor (`_DASH_SWATCH_PREFIX`, 18708) and a `"(missing)"` item; the continuous key is `LinearColorMapper(palette, low=lo, high=hi, nan_color=missing_color)` plus `ColorBar(color_mapper=mapper, ..., title=var_display)` at 6599-6629 (GAPS2's "6424-6446" is stale). The layer's own plot-legend item is stripped at 6644-6655. `_COLORVAR_LEGEND_NAME = "_dash_clegend"` (2012) is already in the served constants list (24327).

The mapper carries per-render metadata the renderers attach: `self.variable_labels`, `value_label_names`, `value_labels` (5437; set by `_dash_attach_labels` 18745, called at 21113 saved and 25875 served on `_DASH_MAPPER`, the module-global mapper the served app builds at 24741). That is the pattern the z options follow: a per-figure attribute set by the figure builder, read by `_apply_colorvar`.

### Where the z options would come from

Saved `_make_figure_body` reads `graph_opts = graph_spec.get("graph_options", {})` at 21938 and already has the note context at 21949-21950: `_seen = getattr(self, "_reported_subopts", None)`, `_gkey = graph_opts.get("name", "")`. The served template reads `go = g.get('graph_options', {})` at 26120 and keeps `_reported_subopts = set()` at 25967. Both call `map_scatter` through the layer loop (22132-22303 saved; 26277-26393 served), and `map_scatter` calls `_apply_colorvar(fig, r, plot_source, options)` with the *plot* options only (7229). The parsers to reuse: `_dash_parse_axis_spec(raw)` (16605) returns `mode`/`ticks`/`count`/`labels`/`format`/`unsupported`; `_dash_apply_axis_spec` (16738-16800) is the pattern — `FixedTicker(ticks=...)`, `major_label_overrides={float(k): v}`, `_dash_count_ticker(N)` for `#N`; `_dash_scale_spec(raw, option, seen, key)` (19001) returns `{"log","reverse","lo","hi"}` and names everything outside `_DASH_SCALE_SUBOPTS` (18998); `_dash_textbox(raw, option, seen, key)` (18861) returns `(text, opts)` and names sub-options outside `_DASH_TEXTBOX_HONOURED` (18858, `size`/`color`), with `_textbox_size`/`_textbox_color` (2577-2611) reading the two it honours. `_dash_axis_count_ticks(lo, hi, N, kind)` (used by `_dash_place_count_ticks` 17276) is dash's own tick model for a count of ticks over a range. Bokeh's `ColorBar` has `ticker`, `major_label_overrides`, `title`, `title_text_font_size` and `title_text_color` (verified against the installed 3.9.0); `LogColorMapper` exists in `bokeh.models`.

### dash.ado: where a plot option and a graph option live

Plot syntax 911-913: `COLORVar(string) COLPALette(string) COLORDIScrete COLORUSEPLEGend COLORNlevels(string) COLORCUTs(string asis) COLORMissing(string)`; sreturn 1141-1146; rules in `_dash_option_rules` 1867-1869:

```
 1867        colornlevels=int,2,256 ///
 1868        colpalette=enum,viridis|magma|inferno|plasma|cividis|turbo|greys|blues|reds ///
 1869        colorcuts=numlist,1  colorvar=var  mlabel=var  range=numlist,2,2 ///
```

`_dash_validate_value`'s `numlist` kind (2122-2148) expands `colorcuts(0(2)4)` to `"0 2 4"` before the renderer sees it. JSON keys in `_dash_plot_opts_to_json` 2856-2860 (`... colorvar colpalette colordiscrete coloruseplegend colornlevels colorcuts colormissing ...`). `_dash_fold_typed` (1672-1690) names the companions on types that do not draw colorvar from the list at 1684: `foreach o in colorvar colordiscrete colorcuts colpalette colornlevels colormissing`. An existing "may not be combined" refusal to copy: `options discrete and bins() may not be combined` at 2359-2412.

Graph syntax 699-724 (the graph parser) and 899-958 (the plot parser carries every graph option as well); sreturn blocks 801-856 and 1206-1262 (`g_*`); the seven graph-key `foreach` lists, identical text each time:

```
 3951    foreach gkey in title subtitle note caption name saving xtitle ytitle xlabel ///
 3952            ylabel xline yline legend by xscale yscale aspectratio scheme ///
 ...
 3956            t2title b1title b2title l1title l2title r1title r2title title2 ///
 3957            subtitle2 nodraw play replace {
```

at 3951, 4481, 4512, 4602, 4656, 4687 and 4942 (the last writes `graph_options` JSON). Mata `_dash_rep_cat` (dash_parse.mata, the function ending at 4258) classes a repeated graph option: titles `T` (4247-4250), labels/ticks `L` (4251-4252), scales `S` (4254). `_dash_rep_unique` (4271-4292) lists the options twoway refuses twice, `colorvar colordiscrete colorcuts` among them. `_dash_rep_und_tab` (4318-4400) is the undeclared-take-once table with `("colorvarminmax", "colorvarminmax", "colorvarminm", "0", "*", "0", "")` at 4362 beside `colorrule`/`colorstart`/`colorend`/`colorformissing`, which stay.

### Stata's rule (`/Applications/StataNow/ado/base/c/colorvar_options.sthlp`, research [D §6 — the report's own section number; RESEARCH.md cites it as D §7])

- `:92` `colordiscrete` "treats colorvar as a discrete variable."
- `:95-98` `colorcuts(numlist)` and `colorlevels(#)` "may not be combined. If neither option is specified, the values used for the major ticks on the z axis are used as cuts."
- `:111-116` `colorcuts`: values "will be sorted, and the levels determined as follows: (-infinity,n_1], (n_1, n_2], …, (n_{k-1}, n_k], (n_k, infinity). Any values below the minimum for colorvar are ignored; if all values are below the minimum, the minimum value will be used as the cut."
- `:119-121` with `colordiscrete`: "the values in numlist will be the levels. Any values that are not included in these levels will be grouped with missing values and displayed in gray."
- `:124-128` `colorlevels(#)` "creates # - 1 equally spaced cuts between the minimum and maximum of colorvar"; `:131-134` with `colordiscrete` the levels are n_1..n_k, "rarely specified".
- `:137-140` `colorvarminmax` "specifies that the minimum and maximum of colorvar be included in the list of cuts. The major ticks on the z axis will also be updated to include the minimum and maximum values."
- Parser spellings (`twoway_yxview_parse.class:146-148,186-200`): `COLORLEVels`, `COLORVARMINMax`; a second copy of either is "option … not allowed", r(198) (`test_twoway_option_parity.cscript:1507-1508` measures `colorvarminmax colorvarminmax`).
- z options: `zlab:el` (`axis_label_options.sthlp:32`), `zti:tle` "contour legend axis title" (`axis_title_options.sthlp:37`), `zsc:ale` (`axis_scale_options.sthlp:38`, documented for contour). Whether they act on a scatter's colorvar key is one of research [D]'s open probes (item 5); the extract script records it and dash draws them on the key either way, as the PRD requires.

### Fixtures on disk

`test/fixtures/rejected_options.json` holds the historical probes (631-647, 703-719, 5308-5316, 5388-5396): `twoway scatter mpg weight, colorlevels(4) colorvar(price)` rc 0 / dash r(198) "option colorlevels() not allowed", and the same for `colorvarminmax`. No colorvar truth fixture exists; `test/fixtures/data/auto.csv` holds only `mpg` and `weight`, so the new fixture carries the colorvar column values it was measured on.

### Existing tests that pin today's behaviour (flip or extend; never delete)

- `test/test_help_claims_7.cscript` HC7-02, lines 316-325: runs `dash scatter mpg weight, colorvar(price) colorlevels(4) colorrule(hue) colorformissing(red)` and asserts the note names `colorlevels() colorrule() colorformissing()`. **Flips**: the note must name `colorrule() colorformissing()` and must NOT name `colorlevels()`.
- `test/test_glyphs.py::TestApplyColorvarOptions::test_colorcuts_produces_correct_bin_count` (3487) and `::test_colorcuts_bin_labels_correct` (3502): `colorcuts(2000 3000)` on weight (min 1760) and on `[1000, 2500, 4000]` — both cuts lie above each minimum, so these **hold** under the new rule; 16-01 adds a sibling that puts a cut below the minimum.
- `test/test_function_audit.py::TestColorCutsPutEachPointInItsLabelledBin` (309-359) and `::TestColorLevelsPutEachPointInItsLabelledBin` (colornlevels): the assertions hold (no cut below a minimum), but `test/function_test_map.py:107-108` names `GlyphMapper._apply_colorvar.<locals>._assign_cut` and `._assign_nlev`; those closures become the module-level helpers of TR-16.3 and the map entries **flip** to the new qualnames in the same commit (`test_function_test_map.py` fails otherwise).
- `test/test_colorvar_legend.py` (all classes): `colordiscrete` without cuts — unchanged, must stay green.
- `test/test_mode_parity.py` colorvar cases 1141-1150: unchanged; the corpus gains the explicit forms (TR-16.11).
- `test/test_label_sinks.py` Sinks 584 (`ColorBar.title`) and 590 (`Legend.title`): the key title gains a second source, `ztitle()`; two Sinks are added, none removed.
- `test/test_twoway_option_parity.cscript:1507-1508` (`colorvarminmax colorvarminmax` → "option colorvarminmax not allowed"): must still pass once `colorvarminmax` is declared, through `_dash_rep_unique`.
- `test/test_unsupported_report_is_true.py` reads the pending blocks: nothing new is pending, so no change, but it must stay green.

## User stories

- **US-16.1** As the Stata user pasting twoway syntax, I want `colorvar(rep78) colordiscrete colorcuts(2 4)` to colour rep78 = 2 and rep78 = 4 and draw 1, 3, 5 and missing in gray, so that the dashboard shows the groups twoway shows.
- **US-16.2** As the Stata user, I want a cut below the variable's minimum to be dropped (and the minimum used if every cut is below it), so that `colorcuts(0 2 4)` on rep78 draws no empty "≤0" key.
- **US-16.3** As the Stata user, I want `colorlevels(#)` and `colorvarminmax`, twoway's spellings, to work and print nothing, so that a working twoway command pastes without edits.
- **US-16.4** As the Stata user, I want `colorcuts()` with `colorlevels()` refused with r(198) as twoway refuses it, so that a mistake is not drawn in silence.
- **US-16.5** As the Stata user, I want `ztitle("Repair")` to title the colour key, `zlabel(1(1)5)` to tick a colour bar and `zscale(range()/log/reverse)` to set its range, scale and direction, in both modes.
- **US-16.6** As the maintainer, I want the explicit forms pinned by twoway's own marker fill groups on auto and nlsw88, so that the rule is measured, not modelled.

## Business requirements

- **BR-16.1** Under `colordiscrete` with `colorcuts(numlist)`, the listed values are the levels; every other value, missing included, is drawn in the `colormissing()` colour (gray by default) under one key entry.
- **BR-16.2** With `colorcuts()` (either path) a cut below the variable's minimum is dropped; if all cuts are below the minimum, the minimum is the only cut. Cuts are sorted and de-duplicated.
- **BR-16.3** `colorlevels(#)` gives #−1 equally spaced cuts between the minimum and maximum, hence # interval levels; under `colordiscrete` the #−1 cut values are the levels. `colornlevels(#)` keeps working and gives the same result.
- **BR-16.4** `colorvarminmax` adds the minimum and maximum to the cuts of `colorcuts()`/`colorlevels()`; on the continuous key it adds the minimum and maximum as ticks.
- **BR-16.5** `colorcuts()` and `colorlevels()` together are refused with r(198) and twoway's wording; a second copy of `colorlevels()` or `colorvarminmax` is refused as twoway refuses it.
- **BR-16.6** `ztitle()`, `zlabel()` and `zscale()` are accepted anywhere twoway accepts a graph option, register without a note, and are drawn on the colour key: the title on a Legend or ColorBar; ticks, tick text, `#N`, `none` and `minmax` on a ColorBar; `range()` (widening only), `log` and `reverse` on a ColorBar's mapper. A z option that asks for something the key cannot draw (a z sub-option outside those, or `zlabel()`/`zscale()` on a discrete key) is named once in the note.
- **BR-16.7** Nothing about the unbinned default changes: a continuous variable without `colordiscrete`, `colorcuts()`, `colorlevels()` or `colornlevels()` still gets the palette and the ColorBar dash.sthlp:2503-2507 documents.
- **BR-16.8** The saved page and the served app draw the same factor per observation, the same number of levels and the same key title.
- **BR-16.9** Any text from `ztitle()` reaches the page as data (Legend title is a DOM text node, ColorBar title is canvas text — both raw as today's `var_display`, never HTML-escaped and never interpolated into script); a z option value is never executed or echoed unescaped by dash.ado.

## Technical requirements

- **TR-16.1** dash.ado plot syntax (911-913) gains `COLORLEVels(string) COLORVARMINMax`; sreturn (1141-1146) gains `colorlevels` and `colorvarminmax`; `_dash_option_rules` (1867) gains `colorlevels=int,2,256` beside `colornlevels=int,2,256`; the JSON key list (2856-2860) and `_dash_fold_typed`'s companion list (1684) gain both; after the rules run, a plot carrying both `colorcuts` and `colorlevels` is refused "options colorcuts() and colorlevels() may not be combined", r(198), by the pattern at 2359-2412 (if the cscript's live twoway probe prints other words, use twoway's words).
- **TR-16.2** dash_parse.mata: the `colorvarminmax` row leaves `_dash_rep_und_tab` (4362); `"colorlevels"` and `"colorvarminmax"` join the `anyof(...)` list in `_dash_rep_unique` (4278-4282) so a second copy is refused as typed; `_dash_rep_cat` maps `"zlabel"` → `"L"`, `"ztitle"` → `"T"`, `"zscale"` → `"S"`.
- **TR-16.3** `dash_render.py` gains two module-level helpers, added to the served function list (24466-24687) and to `test/function_test_map.py`:
  - `_dash_colorvar_cuts(col_vals, cuts, levels, minmax)` → the effective sorted, de-duplicated cut list: `levels` (an int ≥ 2 from `colorlevels`/`colornlevels`) gives `np.linspace(lo, hi, levels + 1)[1:-1]`; explicit `cuts` drop every value `< nanmin(col_vals)` and become `[nanmin]` when none remain; `minmax` appends `nanmin` and `nanmax`. Returns `[]` when there are no finite values.
  - `_dash_colorvar_bins(col_vals, cuts, discrete, label_of)` → `(labels, binned, has_missing)`: interval mode as today (`≤c1`, `c1–c2`, `>ck`, `searchsorted(side="left")`, so a value on a cut is in the bin below); discrete mode: `labels = [label_of(c) for c in cuts]` (value label if any, else `f"{c:g}"`) and each value is its own label when `float(v)` equals a cut exactly, else `"__missing__"`. NaN is always `"__missing__"`.
- **TR-16.4** `_apply_colorvar` reads `colorlevels` alongside `colornlevels` (either sets `nlevels`; both given, `colorlevels` wins — the ado layer never sends both), reads `colorvarminmax` as a flag, and replaces the bodies at 6459-6498 with calls to the two helpers; the `colordiscrete`-alone branch (6500-6511) and the string branch (6517-6533) are untouched. The `_vlookup` closure is passed as `label_of`. Under `colordiscrete` + cuts the "(missing)" key entry keeps its label.
- **TR-16.5** `GlyphMapper` gains `z_options: dict` (keys `zlabel`, `ztitle`, `zscale`, raw strings) and `z_context: tuple` (`seen`, graph key), both defaulting to `{}`/`(None, "")` in `__init__` (5437 region). The saved `_make_figure_body` sets them right after `_gkey` (21950) from `graph_opts`; the served template sets them on `_DASH_MAPPER` right after `go = g.get('graph_options', {})` (26120) with `_reported_subopts` and `gname`. Both reset them to the defaults after the figure's layer loop, so a later figure without z options draws none.
- **TR-16.6** A module-level `_dash_apply_z_options(fig, key_obj, mapper_obj, zopts, seen, key)` (served list, function map), called at the end of both key-building branches of `_apply_colorvar`:
  - `ztitle`: `text, opts = _dash_textbox(raw, "ztitle", seen, key)`; `key_obj.title = "\n".join(text_lines)` (an empty text removes the title); `_textbox_size`/`_textbox_color` → `title_text_font_size`/`title_text_color` where given. On both Legend and ColorBar.
  - `zlabel` on a ColorBar: `spec = _dash_parse_axis_spec(raw)`; `explicit` → `FixedTicker(ticks)` and `major_label_overrides={float(k): v}`; `count` → `_dash_count_ticker(N)`; `none` → `FixedTicker([])`; `minmax` → `FixedTicker([lo, hi])`; `spec["unsupported"]` and a `format()`/`labsize()`/`angle()`/`grid` token are named through `_dash_report_suboptions("zlabel", ..., seen, key)`. On a discrete Legend, `zlabel()` is named once: `_dash_report_suboptions("zlabel", [raw], seen, key)` with the token text `"<not drawn on a discrete key>"` replaced by the raw option so the note reads as the user wrote it.
  - `zscale` on a ColorBar: `spec = _dash_scale_spec(raw, "zscale", seen, key)`; `lo`/`hi` widen the mapper's `low`/`high` only (never narrow, D §3); `reverse` reverses the palette; `log` swaps in a `LogColorMapper` with the same palette and bounds when `low > 0`, else warns once (`_dash_warn_once(("zscale","log",key), ...)`) and keeps the linear mapper. On a discrete Legend, named once as for `zlabel`.
  - `colorvarminmax` with neither cuts nor levels (continuous key): `ColorBar.ticker = FixedTicker(sorted({lo, hi} ∪ set(_dash_axis_count_ticks(lo, hi, 5, ""))))`, unless `zlabel()` set the ticker, which wins.
- **TR-16.7** dash.ado graph syntax (699-724 and 899-958) gains `ZLABel(string asis) ZTItle(string asis) ZSCale(string asis)`; both sreturn blocks (801-856, 1206-1262) gain `zlabel`, `ztitle`, `zscale` (`g_` prefixed in the second); all seven `foreach` lists gain `zlabel ztitle zscale` in the same position (after `subtitle2`). Nothing is added to `_dash_pending` (768-797): these are drawn.
- **TR-16.8** `scripts/extract_colorvar_truth.do` writes `test/fixtures/colorvar_truth.json` (Stata truth section below); `test/test_colorvar_truth.py` reads it and is named in `test/test_fixtures_are_committed.py`'s reader list by the existing mechanism (a test file that names the fixture).
- **TR-16.9** `test/test_colorvar_forms.cscript` (new, registered in `test/run_all_cscripts.do` after test_help_claims_7) drives dash.ado and, through `_dash_serve_spec, specpath() datapath()`, the real spec and data JSON into a `python:` block that renders both modes.
- **TR-16.10** Security (rule 1): `ztitle` text is carried as a Bokeh property value, never into `CustomJS.code`; `zlabel` label text goes through the same `args`/`major_label_overrides` route `_dash_apply_axis_spec` uses (16783-16798); dash.ado reads the three z values by value (`mata: st_global("s(...)")`) like the other graph options and never `display`s them.
- **TR-16.11** `test/test_mode_parity.py` `CORPUS` gains `_case`s for `colordiscrete colorcuts(2 4)`, `colorcuts(0 2 4)`, `colorlevels(4)`, `colorvarminmax`, `ztitle("Repair")`, `zlabel(1(1)5)` and `zscale(log)`, so the profile diff proves BR-16.8.

## Boundaries

- **The continuous default stays** (DISCOVERY Q5, PRD §7): no change to 6599-6629 beyond what `_dash_apply_z_options` adds; `colpalette()` keeps its meaning; dash.sthlp:2503-2507's sentence stays.
- **`colorrule()`, `colorstart()`, `colorend()` stay named** in the note; their `_dash_rep_und_tab` rows stay. Do not honour them "while there".
- **S17 owns line 6527** (`strs = ["" if v is None or str(v) == "nan" else str(v) ...]`) in the string path; this section does not touch 6517-6533. Both land in batch 2; the hunks are disjoint.
- **S07 (G5) owns the ASCII regex at 6365**; leave it.
- **S14 owns `_dash_parse_axis_spec`** (B1): this section calls it as it stands and does not change it; if S14 lands first, `zlabel(1 "one" 2 "two")` gains the text form for free, and the test for it in 16-01 is written against numlist-only labels so it passes either way.
- **S15 owns `_dash_apply_legend`/`_rebuild_legend`**; the colour key's title is set on the Legend object `_apply_colorvar` builds, before those run, and `_rebuild_legend` already leaves `_COLORVAR_LEGEND_NAME` legends alone.
- **No CHANGELOG line for the default** and no new plot type (PRD §7).
- **`coloruseplegend`** is untouched.

## Stata truth

**Script:** `scripts/extract_colorvar_truth.do` → `test/fixtures/colorvar_truth.json`, modelled on `scripts/extract_axis_truth.do` (probe registration `zp id group dataset body opts` at 106-118; run loop 395-428 with `graph export "<id>.svg", name(zqg) replace`; one trailing `python:` block that never calls Stata and writes a backtick as `\x60`). The python block does `sys.path.insert(0, "<repo>/scripts")` and imports `svg_fills` from `svg_truth` (S02). Header comment carries the invocation:

```
mkdir -p /tmp/dash-s16 && cd /tmp/dash-s16 && STATATMP=/tmp/dash-s16/tmp/ \
  arch -arm64 /usr/local/bin/stata-mp -b do \
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_colorvar_truth.do
```

(`STATATMP` with the trailing slash, apart from the log's directory; never the GUI; at most three Stata sessions at once across the batch.)

**Reading the markers.** S02's `svg_fills`/`svg_marker_fills` return per-colour counts, not a per-marker list, so the per-observation truth comes from `svg_document(path)`: its `circles` and `paths` lists in document order, each element carrying its fill (lower-cased `#rrggbb`), restricted to the marker elements (the plot region's `<rect>`s are not markers; `svg_marker_fills` shows which colours are marker colours and with what counts, and the per-marker list's colour counts must equal it — assert that in the python block). `svg_texts(path)` supplies `key_texts`.

**Probes** (`twoway scatter <y> <x>, <opts> name(zqg, replace)`, every one also run with `nodraw` first to record `rc`):

| id | dataset | body | opts |
|---|---|---|---|
| `selfcheck_foreign` | auto | `scatter mpg weight` | `colorvar(foreign) colordiscrete` |
| `default_rep78` | auto | `scatter mpg weight` | `colorvar(rep78)` |
| `disc_rep78` | auto | `scatter mpg weight` | `colorvar(rep78) colordiscrete` |
| `disc_cuts_2_4` | auto | `scatter mpg weight` | `colorvar(rep78) colordiscrete colorcuts(2 4)` |
| `cuts_2_4` | auto | `scatter mpg weight` | `colorvar(rep78) colorcuts(2 4)` |
| `cuts_0_2_4` | auto | `scatter mpg weight` | `colorvar(rep78) colorcuts(0 2 4)` |
| `disc_cuts_0_2_4` | auto | `scatter mpg weight` | `colorvar(rep78) colordiscrete colorcuts(0 2 4)` |
| `cuts_all_below` | auto | `scatter mpg weight` | `colorvar(rep78) colorcuts(-3 0)` |
| `levels_price_4` | auto | `scatter mpg weight` | `colorvar(price) colorlevels(4)` |
| `levels_price_4_minmax` | auto | `scatter mpg weight` | `colorvar(price) colorlevels(4) colorvarminmax` |
| `cuts_price_minmax` | auto | `scatter mpg weight` | `colorvar(price) colorcuts(5000 10000) colorvarminmax` |
| `disc_levels_price_4` | auto | `scatter mpg weight` | `colorvar(price) colordiscrete colorlevels(4)` |
| `cuts_and_levels` | auto | `scatter mpg weight` | `colorvar(price) colorcuts(5000) colorlevels(4)` (rc and message only) |
| `levels_twice` | auto | `scatter mpg weight` | `colorvar(price) colorlevels(4) colorlevels(3)` (rc and message only) |
| `ztitle_disc` | auto | `scatter mpg weight` | `colorvar(rep78) colordiscrete colorcuts(2 4) ztitle("Repair")` |
| `zlabel_price` | auto | `scatter mpg weight` | `colorvar(price) zlabel(4000(4000)16000)` |
| `zscale_log` | auto | `scatter mpg weight` | `colorvar(price) zscale(log)` |
| `zscale_rev` | auto | `scatter mpg weight` | `colorvar(price) zscale(reverse)` |
| `nlsw_disc_grade` | nlsw88 | `scatter wage ttl_exp` | `colorvar(grade) colordiscrete colorcuts(12 16)` |
| `nlsw_levels_wage_5` | nlsw88 | `scatter wage ttl_exp` | `colorvar(wage) colorlevels(5)` |
| `nlsw_cuts_ttl` | nlsw88 | `scatter wage ttl_exp` | `colorvar(ttl_exp) colorcuts(5 10 15)` |
| `nlsw_disc_age` | nlsw88 | `scatter wage ttl_exp` | `colorvar(age) colordiscrete` |

**Fixture keys**, per probe: `command` (the full line as run), `dataset`, `rc`, `message` (the last error line when rc ≠ 0), `n_markers`, `fill_groups` (one small integer per marker in SVG document order, group ids in first-seen order), `n_groups`, `fills` (the hex per group id), `colorvar` (the variable name), `values` (the colorvar column, one entry per observation in dataset order, `null` for missing; `mpg`/`weight` or `wage`/`ttl_exp` are never missing in these datasets, so every observation draws a marker), `marker_order` (`"observation"` when the self-check holds, else `"unknown"`), and `key_texts` (the `text` field of every `svg_texts` entry to the right of the plot region — the key's labels and title — U+00A0 already normalised by S02). A top-level `_meta` records the Stata version, the date, the `svg_truth` functions used, and the self-check verdict.

**Self-check:** `selfcheck_foreign` must give exactly two fill groups whose members are exactly the observations with `foreign == 0` and `foreign == 1` in order; the python block asserts this and writes `marker_order = "observation"` for every probe. If it does not hold, it writes `"unknown"` and the pytest compares partitions as sorted group-size lists instead of per observation (weaker, still a truth). Never silently pass.

`git add -f test/fixtures/colorvar_truth.json` (`.git/info/exclude` hides `*.json`); `test/test_colorvar_truth.py` names the fixture so `test_fixtures_are_committed.py` accepts it.

## TDD test stubs

All new pytest stubs live in `test/test_colorvar_forms.py` (unit and both-mode) and `test/test_colorvar_truth.py` (fixture-driven), created by 16-01. Each names its pre-fix failure.

Regression tests that fail at `91d97be`:

- Test: `test_colordiscrete_with_cuts_makes_each_cut_a_level` — `test/test_colorvar_forms.py::TestColordiscreteWithCuts::test_colordiscrete_with_cuts_makes_each_cut_a_level`. Through a `_bins(options, values)` helper copied from `test_function_audit.py:296-306`, `{"colordiscrete": "yes", "colorcuts": "2 4"}` over `[1,2,3,4,5,nan]` gives binned `["__missing__","2","__missing__","4","__missing__","__missing__"]` and factors `["2","4","__missing__"]`. Pre-fix: `["≤2","≤2","2–4","2–4",">4","__missing__"]`.
- Test: `test_a_cut_below_the_minimum_is_dropped` — `::TestCutsBelowTheMinimum::test_a_cut_below_the_minimum_is_dropped`. `colorcuts(0 2 4)` over `[1,2,3,4,5]` gives factors `["≤2","2–4",">4"]`, no `≤0`. Pre-fix: four factors.
- Test: `test_all_cuts_below_the_minimum_use_the_minimum` — `colorcuts(-3 0)` over `[1,2,3]` gives factors `["≤1",">1"]`. Pre-fix: three factors, all rows in `>0`.
- Test: `test_colorlevels_gives_levels_minus_one_cuts` — `::TestColorlevels::test_colorlevels_gives_levels_minus_one_cuts`. `{"colorlevels": "4"}` over `np.linspace(0, 12, 13)` gives four factors with cuts at 3, 6, 9, identical to `{"colornlevels": "4"}`. Pre-fix: `colorlevels` is not read; the mapper takes the continuous path (`LinearColorMapper`), so `_cvar_v_bin` is absent — an `AssertionError`/`KeyError`, not a wrong number.
- Test: `test_colorlevels_under_colordiscrete_makes_the_cut_values_the_levels` — `{"colordiscrete": "yes", "colorlevels": "4"}` over `[0, 3, 6, 9, 12]` gives factors `["3","6","9","__missing__"]` and 0 and 12 gray.
- Test: `test_colorvarminmax_adds_min_and_max_to_the_cuts` — `::TestColorvarminmax::...` `{"colorcuts": "5", "colorvarminmax": "yes"}` over `[1, 5, 9]` gives factors `["≤1","1–5","5–9",">9"]`. Pre-fix: `["≤5",">5"]`.
- Test: `test_colorvarminmax_alone_ticks_the_colour_bar_at_min_and_max` — a continuous `{"colorvarminmax": "yes"}` leaves a `ColorBar` whose `ticker` is a `FixedTicker` containing `lo` and `hi`. Pre-fix: the bar has Bokeh's default ticker.
- Test: `test_the_helper_drops_cuts_below_the_minimum` — `::TestTheCutHelper::...` unit tests of `_dash_colorvar_cuts` (rule 3): sorted and de-duplicated; below-min dropped; all-below → `[min]`; `levels=4` → three interior points; `minmax` appends min and max; no finite values → `[]`. Pre-fix: `AttributeError: module 'dash_render' has no attribute '_dash_colorvar_cuts'`.
- Test: `test_the_bin_helper_in_both_modes` — unit tests of `_dash_colorvar_bins` (interval and discrete; NaN always missing; a value on a cut goes below). Pre-fix: `AttributeError`.
- Test: `test_ztitle_titles_the_discrete_key` and `test_ztitle_titles_the_colour_bar` — `::TestZOptions::...`, both modes through `test_mode_parity._standalone`/`_served` (or `test_suboption_warnings._both`): `graph_options={"ztitle": "Repair"}` gives `Legend(name="_dash_clegend").title == "Repair"` for the discrete case and `ColorBar.title == "Repair"` for the continuous one, and **no warning** containing `ztitle`. Pre-fix: dash.ado is not involved in a pytest (the spec is written directly), so the pre-fix failure is the title still reading `rep78`/`price`.
- Test: `test_zlabel_ticks_the_colour_bar` — `{"zlabel": "4000(4000)16000"}` on `colorvar(price)` gives `ColorBar.ticker` a `FixedTicker` with `[4000, 8000, 12000, 16000]`; `{"zlabel": "#3"}` a `BasicTicker`-derived ticker with `desired_num_ticks` 3; `{"zlabel": "none"}` an empty `FixedTicker`. Pre-fix: default ticker.
- Test: `test_zscale_range_widens_log_switches_reverse_flips` — `zscale(range(0 20000))` → `mapper.low == 0`, `high == 20000`; `zscale(range(5000 6000))` leaves the data bounds (widen only); `zscale(log)` → `LogColorMapper`; `zscale(reverse)` → the palette reversed. Pre-fix: `LinearColorMapper` at the data bounds.
- Test: `test_a_z_option_on_a_discrete_key_is_named_once` — `zlabel(1(1)5)` with `colordiscrete` warns once with `zlabel` in the text, and a `by()` graph of three panels still warns once (the `seen` set). Pre-fix: no warning.
- Test: `test_an_unknown_z_sub_option_is_named` — `ztitle("Repair", orientation(vertical))` names `orientation(vertical)`; `zscale(alt)` names `alt`; `zlabel(1(1)5, format(%9.2f))` names `format(%9.2f)`. Pre-fix: no warning.
- Test: `test_both_modes_draw_the_same_levels` — `::TestBothModes::...` for each of the explicit forms, the saved and served scatter renderers carry the same `_cvar_<var>_bin` column and the same mapper factors (rule 3 both-modes coverage beyond the parity corpus).
- Test: `test_ztitle_text_is_data_not_markup` — `ztitle("<b>x</b> & y")` reaches `Legend.title`/`ColorBar.title` verbatim (raw, as `var_display` is today) and appears nowhere inside a `CustomJS.code` string in the document. Pre-fix: title not applied.
- Test: `test_every_probe_partitions_the_observations_as_twoway_does` — `test/test_colorvar_truth.py::TestAgainstTwoway::...`, parametrised over every probe in `colorvar_truth.json` with `rc == 0`: build a frame from the probe's `values` (plus `mpg`/`weight` stand-ins from `np.arange`), render the same options through `_apply_colorvar` (and through the saved renderer for the z probes), and assert (a) the number of distinct non-gray factors plus one-if-any-gray equals `n_groups`, and (b) when `marker_order == "observation"`, the partition of observations by dash's factor equals the partition by `fill_groups` (compare as canonical relabellings); else compare sorted group sizes. The `default_rep78` probe is asserted only for `n_markers` (the continuous default is not compared, DISCOVERY Q5). The `cuts_and_levels` and `levels_twice` probes assert `rc == 198` and the message text is recorded for the cscript. If the fixture is missing, `pytest.fail("section 16 task 16-02 must land first: test/fixtures/colorvar_truth.json is missing")` — never skip.
- Test: `test_the_fixture_self_check_held` — `_meta.marker_order_selfcheck == "observation"` (a fixture written from an SVG whose marker order is unknown is a weaker truth and the test says so).

Pinned tests to flip (same commit as the fix that flips them):
- `test/test_help_claims_7.cscript` HC7-02 316-325 → the note names `colorrule() colorformissing()` and not `colorlevels()` (task 16-07).
- `test/function_test_map.py:107-108` → `_dash_colorvar_cuts` and `_dash_colorvar_bins` entries naming `test/test_colorvar_forms.py::TestTheCutHelper::test_the_helper_drops_cuts_below_the_minimum` and `::TestTheBinHelper::test_the_bin_helper_in_both_modes`; the two `<locals>` entries are removed (task 16-05). `test/test_function_audit.py`'s two class docstrings are reworded to name the helpers.
- `test/test_label_sinks.py` Sink table → two new Sinks for `ztitle` (task 16-06).

**Mutation table** (apply, see the named test die, revert):

| break this | test that must die |
|---|---|
| in `_dash_colorvar_cuts`, drop the `c < lo` filter | `test_a_cut_below_the_minimum_is_dropped` |
| in `_dash_colorvar_bins` discrete mode, use `searchsorted` instead of equality | `test_colordiscrete_with_cuts_makes_each_cut_a_level` |
| read `colornlevels` only, not `colorlevels` | `test_colorlevels_gives_levels_minus_one_cuts` |
| forget `minmax` in the helper | `test_colorvarminmax_adds_min_and_max_to_the_cuts` |
| set `z_options` in the saved builder only | `test_ztitle_titles_the_colour_bar[served]` |
| leave `zlabel ztitle zscale` out of the 4942 list | `test_colorvar_forms.cscript` CV-05 (the spec JSON lacks the key) |
| leave `colorvarminmax` out of `_dash_rep_unique` | `test_twoway_option_parity.cscript` f32 (1507) |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| cut/level arithmetic (`_dash_colorvar_cuts`, `_dash_colorvar_bins`) | pytest unit | none | n/a (module-level, copied) |
| discrete+cuts, below-min, colorlevels, colorvarminmax through `_apply_colorvar` | pytest via `_bins` helper | none | yes (`TestBothModes`) |
| z options on Legend/ColorBar, naming once, unknown sub-options | pytest both modes | none | yes |
| every explicit form against twoway's fill groups | pytest | `colorvar_truth.json` | saved (mapper is shared) |
| parity profile | pytest `test_mode_parity` corpus | its own | yes |
| ado registration, JSON keys, refusals, no note, live SVG vs page | cscript `test_colorvar_forms.cscript` | live Stata | yes (python: block renders both) |
| HC7-02 flip | cscript | live | n/a |
| security: ztitle text as data | pytest + cscript (hostile value never echoed) | none | yes |

Acceptance criteria:
- **AC-16.1** `dash scatter mpg weight, colorvar(rep78) colordiscrete colorcuts(2 4)` draws three groups — rep78 = 2, rep78 = 4, and gray — matching twoway's fill groups on auto observation for observation, in both modes, with no note.
- **AC-16.2** `colorcuts(0 2 4)` on rep78 draws three interval levels and no "≤0" key; `colorcuts(-3 0)` draws two levels split at 1.
- **AC-16.3** `colorlevels(4)` registers (rc 0), is not named, and gives four groups equal to `colornlevels(4)`'s; `colorvarminmax` registers and adds min and max to the cuts; a second copy of either is refused as twoway refuses it.
- **AC-16.4** `colorcuts(2 4) colorlevels(4)` is r(198) in dash with twoway's wording.
- **AC-16.5** `ztitle("Repair")` titles the key in both modes; `zlabel(4000(4000)16000)` ticks the colour bar at those four values; `zscale(log)` gives a log mapper; none prints a note; the three keys appear in `graph_options` JSON.
- **AC-16.6** `test_colorvar_truth.py` passes against a fixture whose self-check recorded `"observation"`.
- **AC-16.7** The full pytest suite and the cert suite are green; `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` pass with the new helpers listed.

## Tasks

<task type="auto" id="16-01">
  <name>Write the failing tests for the section</name>
  <files>test/test_colorvar_forms.py (new), test/test_colorvar_truth.py (new)</files>
  <action>
    Create both files under `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/`. Write only tests; do not touch `dash_render.py`, `dash.ado` or `dash_parse.mata`.
    1. `test_colorvar_forms.py`: module docstring stating the two measured symptoms in the words of the Overview (16-08 lifts them into CHANGELOG); header block copied from `test/test_function_audit.py` (its `_bins(options, values)` helper at 296-306, `_LE`/`_DASH` constants, `dr`, `ColumnDataSource`, `figure`); both-mode helpers imported from `test_mode_parity` (`_standalone`, `_served`, `_spec`) as `test_suboption_warnings.py:33-37` does, plus `from conftest import make_spec, make_data_json`. A 20-row frame like `test_colorvar_legend.py::_df` with `rep78` and `price`, value labels `_VL`/`_VLN` from that file. Write every stub named under "TDD test stubs" with exactly those class and test names: `TestColordiscreteWithCuts`, `TestCutsBelowTheMinimum`, `TestColorlevels`, `TestColorvarminmax`, `TestTheCutHelper`, `TestTheBinHelper`, `TestZOptions`, `TestBothModes`. The z tests write `ztitle`/`zlabel`/`zscale` into `graph_options` directly. The `zlabel` test uses numlist forms only (`4000(4000)16000`, `#3`, `none`), never `value "text"` pairs (S14 owns that grammar). For "named once" use `warnings.catch_warnings(record=True)` and count records whose message contains `zlabel`.
    2. `test_colorvar_truth.py`: loads `test/fixtures/colorvar_truth.json` through a module-level `_truth()` that calls `pytest.fail("section 16 task 16-02 must land first: test/fixtures/colorvar_truth.json is missing")` when absent (a skip certifies nothing); parametrises `TestAgainstTwoway::test_every_probe_partitions_the_observations_as_twoway_does` over the probe ids; builds the frame from each probe's `values`; renders through `_apply_colorvar` with the probe's options parsed from its `command` (a small `_opts_of(command)` that reads `colorvar()`, `colordiscrete`, `colorcuts()`, `colorlevels()`, `colorvarminmax`, `ztitle()`, `zlabel()`, `zscale()` — write it in the test, it is not production code); compares partitions as described in the stub (`marker_order` decides per-observation vs sizes). Add `test_the_fixture_self_check_held`.
    3. Run both files against the unmodified tree; paste the failure summary into the commit message (`0 passed` in forms apart from any that pass by construction — list those — and one `pytest.fail` per truth test).
    Commit on `s3-bugs`; no AI references in the message.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_colorvar_forms.py test/test_colorvar_truth.py -q 2>&1 | tail -20` collects with no error; `test_colordiscrete_with_cuts_makes_each_cut_a_level` fails with the interval labels (`≤2`, `2–4`, `>4`) in its assertion message, `TestTheCutHelper` fails with `AttributeError`, and every truth test fails with the "must land first" message.]]></verify>
  <done>Both test files exist, collect cleanly, and every regression test fails on the unmodified tree for the reason its stub names.</done>
</task>

<task type="auto" id="16-02">
  <name>Measure twoway's colorvar fill groups into a fixture</name>
  <files>scripts/extract_colorvar_truth.do (new), test/fixtures/colorvar_truth.json (new)</files>
  <action><![CDATA[
    Write `scripts/extract_colorvar_truth.do` on the `extract_axis_truth.do` pattern (registration program `zp`, run loop with `sysuse` per dataset change, `capture noisily` the command with `name(zqg, replace)`, `graph export "<id>.svg"`, a record file, one trailing `python:` block). Register the 22 probes of the "Stata truth" table; for `cuts_and_levels` and `levels_twice` record `rc` and the last error line only (run under `capture` with the log captured, as `test_help_claims_7.cscript`'s `_zh7_run` does). Before the loop, for each dataset write the colorvar columns (`foreign rep78 price` on auto; `grade wage ttl_exp age` on nlsw88) to the record file as one line per observation so the python block can attach `values`. In the python block: `sys.path.insert(0, os.path.join(REPO, "scripts"))`, `from svg_truth import svg_document, svg_marker_fills, svg_texts` (S02), take the marker elements of `svg_document(path)` (`circles` and `paths`) in document order, assert their colour counts equal `svg_marker_fills(path)`'s `n` per colour, map each marker's fill to a group id in first-seen order, fill `key_texts` from `svg_texts`, run the self-check on `selfcheck_foreign` exactly as the "Stata truth" section says, write `marker_order` for every probe, write `_meta` (Stata version from `c(stata_version)` recorded in the record file, date, `svg_truth` function names used, self-check verdict), and `json.dump(doc, fh, indent=2, sort_keys=True)`. The block never calls Stata and writes a backtick as `\x60`.
    Run it: `mkdir -p /tmp/dash-s16 && cd /tmp/dash-s16 && STATATMP=/tmp/dash-s16/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_colorvar_truth.do` (never the GUI; count your concurrent Stata sessions). Read the `.log` for `r(` lines. Then `git add -f test/fixtures/colorvar_truth.json`.
  ]]></action>
  <verify>`python3 -c "import json;d=json.load(open('test/fixtures/colorvar_truth.json'));print(d['_meta']['marker_order_selfcheck'], d['disc_cuts_2_4']['n_groups'], d['cuts_0_2_4']['n_groups'], d['cuts_and_levels']['rc'])"` prints `observation 3 3 198` (the group counts are what twoway drew; if `disc_cuts_2_4` is not 3, read the SVG before trusting either number). `python3 -m pytest test/test_colorvar_truth.py -q -k self_check` passes; `python3 -m pytest test/test_fixtures_are_committed.py -q` passes.</verify>
  <done>`test/fixtures/colorvar_truth.json` holds twoway's fill groups, values and return codes for all 22 probes with the marker-order self-check recorded, and is force-added to git.</done>
</task>

<task type="auto" id="16-03">
  <name>Declare colorlevels and colorvarminmax in dash.ado and Mata</name>
  <files>dash.ado, dash_parse.mata</files>
  <action>
    dash.ado: (1) plot syntax 911-913 gains `COLORLEVels(string) COLORVARMINMax`; (2) sreturn after 1146: `sreturn local colorlevels : copy local colorlevels` and `colorvarminmax`; (3) `_dash_option_rules` 1867: add `colorlevels=int,2,256` beside `colornlevels`; (4) JSON key list 2856-2860: add `colorlevels colorvarminmax` after `colormissing`; (5) `_dash_fold_typed` 1684: add both to the `foreach o in ...` companion list; (6) after the plot rules are validated (beside the `discrete and bins()` refusal at 2359-2412), when both `s(colorcuts)` and `s(colorlevels)` are non-empty: `display as error "options colorcuts() and colorlevels() may not be combined"` and `exit 198` — then compare with the fixture's `cuts_and_levels.message` and use twoway's words if they differ. Read each value with `mata: st_local(..., st_global("s(...)"))` as 1681 does, never in quotes.
    dash_parse.mata: remove the `colorvarminmax` row (4362) from `_dash_rep_und_tab`; add `"colorlevels", "colorvarminmax"` to the `anyof((...))` list in `_dash_rep_unique` (4278-4282) so a second copy is "option colorlevels() not allowed" / "option colorvarminmax not allowed", r(198), as the fixture's `levels_twice.message` and `test_twoway_option_parity.cscript:1507-1508` say. Rebuild the Mata library the way the repo does (see the `lmata`/`mlib` step the Makefile or dash_setup runs; do not hand-edit the .mlib).
    Note: the `test_unsupported_report_is_true.py` guard reads pending blocks; nothing here is pending.
  </action>
  <verify><![CDATA[From a scratch dir with `STATATMP=<dir>/tmp/`, `arch -arm64 /usr/local/bin/stata-mp -b do` a five-line do-file: `sysuse auto` / `dash scatter mpg weight, colorvar(price) colorlevels(4) colorvarminmax name(g1)` / `dash scatter mpg weight, colorvar(price) colorcuts(2 4) colorlevels(4) name(g2)` / `dash scatter mpg weight, colorvar(price) colorvarminmax colorvarminmax name(g3)`; the log shows rc 0 with no "ignoring unsupported" line for g1, `r(198)` with the combined-options message for g2, and "option colorvarminmax not allowed" r(198) for g3. `python3 -m pytest test/test_twoway_option_parity*.py -q` (if any) stays green.]]></verify>
  <done>`colorlevels()` and `colorvarminmax` register, validate, travel to the spec JSON and are refused twice or combined exactly as twoway refuses them; `colorvarminmax` no longer sits in the undeclared table.</done>
</task>

<task type="auto" id="16-04">
  <name>Declare zlabel, ztitle and zscale as graph options</name>
  <files>dash.ado, dash_parse.mata</files>
  <action>
    dash.ado: add `ZLABel(string asis) ZTItle(string asis) ZSCale(string asis)` to the graph syntax block (699-724, after `YTI2(string asis)`) and to the plot syntax block (899-958, same place); add `sreturn local zlabel : copy local zlabel`, `ztitle`, `zscale` to 801-856 and `sreturn local g_zlabel : copy local zlabel` etc. to 1206-1262; add ` zlabel ztitle zscale` after `subtitle2` in each of the seven `foreach` lists at 3951, 4481, 4512, 4602, 4656, 4687 and 4942 — verify with `grep -c 'subtitle2 zlabel ztitle zscale nodraw play replace' dash.ado`, which must print 7. Do not add them to `_dash_pending` (768-797).
    dash_parse.mata `_dash_rep_cat`: add `"ztitle"` to the T tuple (4247-4250), `"zlabel"` to the L tuple (4251-4252) and `"zscale"` to the S tuple (4254). Rebuild the Mata library.
    Security: the values are read by value like every graph option (the `foreach gk` loops call `st_global`), never displayed; add a cscript row in 16-07 with `ztitle("\`x'")` to prove it.
  </action>
  <verify>`grep -c 'subtitle2 zlabel ztitle zscale nodraw play replace' dash.ado` prints 7; `grep -c 'ZLABel(string asis) ZTItle(string asis) ZSCale(string asis)' dash.ado` prints 2; `grep -c 'g_zscale' dash.ado` prints 1. A scratch do-file `dash scatter mpg weight, colorvar(rep78) colordiscrete ztitle("Repair") zlabel(1(1)5) zscale(range(0 6)) name(g1)` followed by `_dash_serve_spec, specpath("s.json") datapath("d.json")` runs rc 0 with no note, and `python3 -c "import json;g=json.load(open('s.json'))['graphs'][0]['graph_options'];print(g['ztitle'],g['zlabel'],g['zscale'])"` prints `Repair 1 2 3 4 5 range(0 6)` (the numlist is expanded only if the graph-option check loop normalises it; either spelling is acceptable here — the renderer parses both).</verify>
  <done>The three z options register anywhere a graph option registers, survive the repeat merge in their categories, and reach `graph_options` in the spec JSON.</done>
</task>

<task type="auto" id="16-05">
  <name>Rewrite the explicit forms in the mapper</name>
  <files>dash_render.py, test/function_test_map.py, test/test_function_audit.py</files>
  <action><![CDATA[
    In `dash_render.py`, immediately before `class GlyphMapper` (search for its banner; about 5351), add the two module-level helpers of TR-16.3, `_dash_colorvar_cuts(col_vals, cuts, levels, minmax)` and `_dash_colorvar_bins(col_vals, cuts, discrete, label_of)`, with docstrings quoting `colorvar_options.sthlp:111-134` and the Stata rule for each branch. In `_apply_colorvar`: read `colorlevels` next to `colornlevels` (6422-6428; `int()` with the same guard; `colorlevels` wins when both), read `minmax = bool(options.get("colorvarminmax"))`, and replace the bodies at 6459-6498 with: `eff = _dash_colorvar_cuts(col_vals, cuts, nlevels, minmax)`; `labels, binned, has_missing = _dash_colorvar_bins(col_vals, eff, force_discrete and cuts is not None or (force_discrete and nlevels is not None), _vlookup)`. Keep the `colordiscrete`-alone branch (6500-6511) and the string branch (6517-6533, S17's) untouched. Keep `_vlookup` as it is. Add both helper names to the served function list (24466-24687) beside `_dash_report_suboptions`.
    `test/function_test_map.py`: replace the two `<locals>` entries at 107-108 with `'_dash_colorvar_cuts': 'test/test_colorvar_forms.py::TestTheCutHelper::test_the_helper_drops_cuts_below_the_minimum'` and `'_dash_colorvar_bins': 'test/test_colorvar_forms.py::TestTheBinHelper::test_the_bin_helper_in_both_modes'`. `test/test_function_audit.py`: reword the two class docstrings (309-315 and the colornlevels class) to name the helpers; add to `TestColorCutsPutEachPointInItsLabelledBin` one test `test_a_cut_below_the_minimum_is_dropped_here_too` (cuts `500 2000 3000` over the same values → the same three bins).
    Verify the served copy: `python3 -m pytest test/test_statistical_helpers.py -q -k CarriesEveryName test/test_resource_limits.py -q -k DefinesEveryName`.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_colorvar_forms.py -q -k "not ZOptions and not BothModes" 2>&1 | tail -3` shows every cut/level test passing; `python3 -m pytest test/test_colorvar_truth.py -q 2>&1 | tail -3` passes for every probe except the four z probes (which 16-06 closes) and reports which; `python3 -m pytest test/test_function_test_map.py test/test_function_audit.py test/test_glyphs.py test/test_colorvar_legend.py -q` passes.]]></verify>
  <done>`colordiscrete` with `colorcuts()` draws the cuts as levels and the rest gray, cuts below the minimum are dropped, `colorlevels()` and `colorvarminmax` are honoured, the arithmetic lives in two copied and mapped helpers, and every non-z fixture probe matches twoway.</done>
</task>

<task type="auto" id="16-06">
  <name>Draw the z options on the colour key in both modes</name>
  <files>dash_render.py, test/test_label_sinks.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    `dash_render.py`: (1) `GlyphMapper.__init__` (5437 region) gains `self.z_options = {}` and `self.z_context = (None, "")`. (2) Add module-level `_dash_apply_z_options(fig, key_obj, mapper_obj, zopts, seen, key)` implementing TR-16.6 exactly, above `_apply_colorvar`'s class or beside `_dash_scale_spec` (19001); it imports `FixedTicker`, `LogColorMapper` locally; add it to the served function list and to `test/function_test_map.py` naming `test/test_colorvar_forms.py::TestZOptions::test_zscale_range_widens_log_switches_reverse_flips`. (3) Call it at the end of both key branches of `_apply_colorvar`: after `fig.add_layout(Legend(...))` (6595) with the Legend and `mapper`, and after the `ColorBar` is built (6620-6625) with the bar and `mapper` — build the bar into a local first so its `ticker` can be set. Under `colorvarminmax` with no cuts/levels, set the continuous bar's ticker per TR-16.6 before the z options run so `zlabel()` wins. (4) Saved `_make_figure_body`: after `_gkey = ...` (21950) set `self.mapper.z_options = {k: graph_opts.get(k, "") for k in ("zlabel", "ztitle", "zscale")}` and `self.mapper.z_context = (_seen, _gkey)`; after the layer loop ends (22303) reset both. (5) Served template: after `"        go = g.get('graph_options', {})",` (26120) emit the same two assignments on `_DASH_MAPPER` with `_reported_subopts` and `gname`; reset them after the layer loop (26393). Every string in the template is a Python source line inside a list of strings — mind the quoting the neighbouring lines use.
    `test/test_label_sinks.py`: add two `Sink` rows beside 584 and 590 — `Sink("colorbar_title_from_ztitle", "zt", ("ColorBar",), "title", "canvas")` and `Sink("colorvar_legend_title_from_ztitle", "zt", ("Legend",), "title", "text")` — following the file's registration pattern (the `tag()` payload at 260 and the case list around 299-303, one case with `colorvar(price)` and one with `colorvar(rep) colordiscrete`, each with `ztitle(<tag>)` in `graph_options`).
    `test/test_mode_parity.py`: add the seven `_case` entries of TR-16.11 after the colorvar cases at 1141-1150.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colorvar_forms.py test/test_colorvar_truth.py test/test_label_sinks.py -q 2>&1 | tail -3` all pass; `python3 -m pytest test/test_mode_parity.py -q -k "colorvar or ztitle or zlabel or zscale" 2>&1 | tail -3` passes; `python3 -m pytest test/test_statistical_helpers.py -q -k CarriesEveryName test/test_resource_limits.py -q -k DefinesEveryName test/test_function_test_map.py -q` passes.]]></verify>
  <done>`ztitle()` titles the key, `zlabel()` ticks and labels the colour bar, `zscale()` widens, logs or reverses its mapper, each in both modes, what the key cannot draw is named once, and the new title source is registered as a text sink.</done>
</task>

<task type="auto" id="16-07">
  <name>Certify the forms end to end from dash.ado</name>
  <files>test/test_colorvar_forms.cscript (new), test/run_all_cscripts.do, test/test_help_claims_7.cscript</files>
  <action><![CDATA[
    Write `test/test_colorvar_forms.cscript` on the `test_help_claims_7.cscript` pattern (`cscript` header, `cert_helpers.do`, the `_zh7_run`/`_zh7_logged` style helpers renamed `_cv_*`, `sysuse auto`, `global dash_nobrowser 1`). Load `cert_svg.do` beside `cert_helpers.do`, after `cscript` and before any `cd` (S02's load rule). Rows: CV-01 `twoway scatter mpg weight, colorvar(rep78) colordiscrete colorcuts(2 4), name(zcv0)` → `cert_svg_export, name(zcv0)` (`r(file)`) then `cert_svg_fills, file("<r(file)>") markers` → `r(n)` is the number of colour groups and `r(list)` a TSV whose `n` column holds each group's marker count (read it with `import delimited` into a frame, or `file read`) → then `dash scatter mpg weight, colorvar(rep78) colordiscrete colorcuts(2 4) name(zcv1)` with no note, `_dash_serve_spec, specpath("`s'") datapath("`d'")`, and a `python:` block (`sys.path.insert(0, "<repo>")`, `import dash_render`) that renders `DashRenderer(s, d, out)` and reads the scatter renderer's `fill_color["transform"].factors` and the `_cvar_rep78_bin` column counts, and builds `ServerAppBuilder(s, d).build(app)` then `exec`s the app source with its curdoc attach replaced (the `_load_app` recipe in `test/test_adversarial_matrix.py`) and reads the same from the served document; write both group-count and group-size results to `st_global`s and assert in Stata that they equal twoway's r() values. CV-02 `colorcuts(2 4) colorlevels(4)`: twoway's rc and dash's rc equal (198), dash's message equals twoway's last error line (captured logs). CV-03 `colorlevels(4)` and `colorvarminmax`: rc 0, no note, both keys in the spec JSON (`cert_file_has`). CV-04 `colorlevels(4) colorlevels(3)` and `colorvarminmax colorvarminmax`: dash's rc and words equal twoway's. CV-05 `ztitle("Repair") zlabel(1(1)5) zscale(range(0 6))`: rc 0, no note, all three keys in the spec JSON, and the python block sees `Legend.title == "Repair"` (discrete) in both modes. CV-06 hostile: `ztitle("\`x'")` and `ztitle("<script>")` register rc 0, the log never shows an expanded macro, and the page holds the text only as a Bokeh property value (the python block asserts the string is absent from every `CustomJS.code`). CV-07 `colorvar(price) colorlevels(4) colorrule(hue) colorformissing(red)`: the note names `colorrule() colorformissing()` and not `colorlevels()`.
    Register the script in `test/run_all_cscripts.do` after the test_help_claims_7 block (copy its RUN/SKIP/PASS/FAIL block; `test_cscript_hygiene.py:418` requires registration). Flip HC7-02 in `test_help_claims_7.cscript` 320-325: the needle becomes `"colorrule() colorformissing()"` and a second `_zh7_logged` asserts `colorlevels()` is NOT found (`r(found) == 0`), with the comment updated.
    Run: `cd <scratch> && STATATMP=<scratch>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do <repo>/test/test_colorvar_forms.cscript` and the same for `test_help_claims_7.cscript`; a `python:` block that SKIPs because `c(python_exec)` is empty is a failure to investigate (`set python_exec /opt/anaconda3/bin/python3, permanently` if many sessions dropped it), not a pass.
  ]]></action>
  <verify>Both cscript logs end without `r(` and with their PASS summary; `grep -c 'test_colorvar_forms.cscript' test/run_all_cscripts.do` is at least 4; `python3 -m pytest test/test_cscript_hygiene.py -q` passes.</verify>
  <done>A certification script proves, from dash.ado through both renderers, that the explicit forms and the z options register, are drawn and match one live twoway export, and HC7-02 pins the note's new shape.</done>
</task>

<task type="auto" id="16-08">
  <name>Close X2 in BUGS.md, dash.sthlp and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    `dash.sthlp` 2478-2507: add two `synopt` rows — `{cmdab:colorlev:els(}{it:#}{cmd:)}` "# levels: # - 1 equally spaced cuts between the minimum and maximum (Stata's spelling; colornlevels() is the same)" and `{cmdab:colorvarminm:ax}` "add the minimum and maximum of varname to the cuts, and to the colour bar's ticks" — and rewrite the paragraph at 2499-2503: `colorvar()`, `colordiscrete`, `colorcuts()`, `colorlevels()` and `colorvarminmax` are Stata 18's own and drawn as Stata draws them: under `colordiscrete` the cuts are the levels and every other value is drawn in `colormissing()`'s colour with the missing values; a cut below the minimum is ignored and the minimum is used if all are; `colorcuts()` and `colorlevels()` may not be combined. `colorrule()`, `colorstart()`, `colorend()` and `colorformissing()` stay named in the note. Keep 2503-2507's continuous-default sentence word for word. Add a short paragraph after it: the colour key's own axis options `ztitle()`, `zlabel()` and `zscale()` are taken as graph options and drawn on the key — the title on either key; ticks, `#N`, `none` and `minmax` and `range()`/`log`/`reverse` on the colour bar; on a discrete key `zlabel()` and `zscale()` are named in the note. Add the three to the graph-option table where `xlabel()`/`xtitle()`/`xscale()` are listed (grep `xsc:ale` in dash.sthlp), each pointing at this section.
    `CHANGELOG.md`: under `### Results that change` → `**Colours, schemes and appearance**` (113) add: "`colorvar(rep78) colordiscrete colorcuts(2 4)` drew three interval colours (≤2, 2–4, >4); it now draws rep78 = 2 and rep78 = 4 in two colours and every other value gray, as twoway does. `colorcuts(0 2 4)` on rep78 drew an empty ≤0 key; a cut below the variable's minimum is now dropped. (WP-28, X2)". Under `### New`: `colorlevels(#)`, `colorvarminmax`, `zlabel()`, `ztitle()`, `zscale()`; under `### Fixed`: the note no longer names `colorlevels()`/`colorvarminmax`.
    `BUGS.md`: one closed entry, `- [x] Title: colordiscrete with colorcuts() is read as intervals, cuts below the minimum are kept, and colorlevels(), colorvarminmax and the z options are not drawn`, with File Names and Line Numbers (`dash_render.py: GlyphMapper._apply_colorvar; dash.ado: the plot and graph syntax blocks; dash_parse.mata: _dash_rep_unique, _dash_rep_und_tab, _dash_rep_cat`), Description (the GAPS2 X2 symptom, cited), Suggested fix, and Resolution "Fixed <date> (WP-28, X2). ... Pinned by test/test_colorvar_truth.py::TestAgainstTwoway::test_every_probe_partitions_the_observations_as_twoway_does, test/test_colorvar_forms.py::TestColordiscreteWithCuts::test_colordiscrete_with_cuts_makes_each_cut_a_level and test/test_colorvar_forms.cscript CV-01..CV-07, which failed on the unfixed code." — exactly once each field, in order, no AI references. Grep the entry, the help and the CHANGELOG for `claude|anthropic` before committing.
    Then the full suite once: `python3 -m pytest test/ -q` (parallel by default; never a second concurrent full run) and `scripts/run_cert_suite.sh` if the batch's Stata budget allows, else the two cscripts of 16-07 plus `test_twoway_option_parity.cscript` and `test_unsupported_report_is_true.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no skips in strict mode; `python3 -m pytest test/test_tracking_documents.py test/test_help_claims_7.py -q` passes (the closed entry names tests that exist); `grep -n 'colorlevels' dash.sthlp` shows the synopt row and no "named in the note" mention of it.]]></verify>
  <done>X2 is closed in BUGS.md naming its regression tests, dash.sthlp documents the explicit forms and the z options while keeping the continuous default, CHANGELOG records the two changed pictures, and the full suite is green.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" passes; the tests listed under "pinned tests to flip" are flipped in the commits named, none deleted.
- `test/fixtures/colorvar_truth.json` exists, is committed with `git add -f`, records `marker_order_selfcheck == "observation"`, and `test_colorvar_truth.py` passes against it.
- dash.ado accepts `colorlevels()`, `colorvarminmax`, `zlabel()`, `ztitle()`, `zscale()` everywhere twoway accepts them, prints no note for them, refuses `colorcuts()` with `colorlevels()` and a repeated `colorlevels()`/`colorvarminmax` as twoway does.
- `grep -c 'subtitle2 zlabel ztitle zscale nodraw play replace' dash.ado` is 7.
- The served copy lists and `test/function_test_map.py` carry `_dash_colorvar_cuts`, `_dash_colorvar_bins`, `_dash_apply_z_options`.
- `test_colorvar_forms.cscript` and the flipped HC7-02 pass under `arch -arm64 /usr/local/bin/stata-mp -b`.
- BUGS.md carries the closed X2 entry; dash.sthlp and CHANGELOG are updated; the full pytest suite is green with no skips.

## Notes

- **Marker order.** Do not assume twoway writes markers in observation order; the self-check probe decides, and the pytest's comparison mode follows `marker_order`. Missing colorvar values are drawn (gray), so every observation of these datasets has a marker.
- **S02's contracts, as its section file fixes them:** `svg_fills`/`svg_marker_fills` are per-colour count dicts, not per-marker lists — the per-observation order comes from `svg_document(path)`'s `circles`/`paths`; `cert_svg_fills` answers `r(n)`, `r(colours)` and a TSV in `r(list)`, not `r(n_groups)`/`r(sizes)`. If S02's landed code differs again, adapt the extract script and cscript only — the fixture keys and the pytest stay.
- **Served copy.** `_apply_colorvar` travels inside `GlyphMapper` (copied whole), but the three new module-level helpers do not travel unless added to the function list at 24466-24687; the guard tests fail loudly, so run them after 16-05 and 16-06.
- **Two renderers, two attribute sites.** The mapper object is shared by every figure in a render (`self.mapper`, `_DASH_MAPPER`); forgetting the reset after the layer loop leaks one graph's `ztitle` onto the next graph's key. The both-modes test with two graphs, one titled, is in `TestZOptions`.
- **Seven lists.** The `grep -c` in 16-04's verify is the guard; a key in six lists registers and is then dropped at JSON time (or the reverse), which no single-mode test sees.
- **`_dash_rep_unique`.** Moving `colorvarminmax` out of the undeclared table without adding it there loses the "given twice" refusal that `test_twoway_option_parity.cscript:1507-1508` pins.
- **`colorlevels` vs `colornlevels`.** Same arithmetic; both stay. `colorlevels=int,2,256` follows the task's rule; twoway's own floor for `colorlevels(1)` is not measured here (record it as a note in the cscript if it differs).
- **Range widening only.** `zscale(range())` narrows nothing, as B2 (S18) establishes for the plot axes; a narrower range is ignored silently, which is twoway's rule (D §3).
- **S17's line.** The string path at 6527 belongs to S17; merging both diffs with `patch -p1` is clean because 16-05 edits 6459-6498 only. Do not "tidy" the string branch.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; a cscript whose `python:` block skips is not a pass — check `c(python_exec)` first.
- **Fixtures are hidden by `.git/info/exclude`**: `git add -f`, every time.
