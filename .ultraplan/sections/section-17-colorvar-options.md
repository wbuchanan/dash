# Section 17: The colorvar option remainder, colorformissing(), colorvar(i.var), clegend(), plegend(), pcycle()

> Part of: WP-31 · GAPS3 rows: C8b · Risk: yellow · Batch: 6 · Depends on: 15 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U17

## Overview

**What is wrong today.** GAPS3 C8 (GAPS3.md:127), part b: "`colorlist()`, `coloruseplegend` pending (`_use_plegend` read into a dead variable); `colorstart() colorend() colorformissing() colorfillonly colorkeysrange colorrule() clegend() plegend() pcycle()` undeclared, generic note; dash's own `colormissing()` is not Stata's `colorformissing()` spelling; `colorvar(i.var)` r(111)." Evidence: dash.ado:1330-1331 (`if ... colorlist ... _dash_pending`, `coloruseplegend`), the declarations `COLORLIst(string asis)` (:1203) and `COLORUSEPLEGend` (:1181) with no reader; dash_render.py:13734 `_use_plegend = bool(options.get("coloruseplegend"))  # noqa: F841`; dash_parse.mata:6288-6296 (`_dash_rep_und_tab` rows colorallowmultiple, colorend, colorfillonly, colorformissing, colorkeysrange, colorkeysreverse, colorotherlabel, colorrule, colorstart), :6300 `clegend`, :6323-6324 `pcycle`, `plegend`; dash.ado:2194 (`colorvar(nosuchvar)` is r(111); `i.rep78` is no variable, so r(111)). The help's "colorvar() sub-options" entry (dash.sthlp:5048-5054) lists colorlist/coloruseplegend as not honoured and :4185-4188 says `colorrule() colorstart() colorend() colorformissing()` are named.

**After this section** every colorvar option of `twoway_yxview_parse.class:185-201` is declared and drawn as `colorvar_options.sthlp` describes (research/stata-ground-truth.md §1.2; the option list at `colorvar_options.sthlp:143-200`):
- `colorrule(crule [%# [*#]])`: how the level colours are made -- `hue` (default: equally spaced hues between `colorstart()` and `colorend()`), `chue` (hues the other way round the wheel when end < start), `phue` (the scheme's p1..p15, then hue), `intensity` (equally spaced intensities of `colorend()`, `colorstart()` ignored), `linear` (RGB interpolation start→end); `%#` an opacity and `*#` an intensity applied to every level. `colorstart(colorstyle)`, `colorend(colorstyle)`: the rule's ends; defaults measured (U17-01 reads `.plot1.colorstart`/`.colorend`/`.colorrule` and the SVG fill colours of a `colorlevels(5)` scatter).
- `colorlist(colorstylelist)`: one colour per level in order (wins over `colorrule()`; fewer colours than levels: twoway's behaviour measured, U17-02).
- `colorfillonly`: the mapping colours fills only; outlines keep the series colour.
- `colorformissing(colorstyle)`: Stata's spelling of dash's `colormissing()`; both read, `colorformissing()` wins when both are given (twoway has only one; measured U17-03 that dash's `colormissing()` is refused by twoway r(198) -- it stays dash's own).
- `colorkeysrange`: the discrete key's entries show each level's interval as a range ("ranged bars, similar to a colour bar", `:193-195`): the key entry text becomes `lo - hi` and the swatch a bar; `colorkeysreverse`: the key's order reversed; `colorallowmultiple`: a `colorvar()` layer beside another `colorvar()` layer in one graph is allowed (today dash draws two keys; twoway refuses the second without this flag -- measured U17-04, the refusal text copied); `colorotherlabel(string)`: the label of the "other" entry under `colordiscrete` with cuts (research: the values outside the cut levels), replacing dash's "(missing)" text for those rows.
- `coloruseplegend`: the discrete key is drawn as the plot legend (Bokeh `Legend` -- already dash's discrete path) and twoway refuses it without `colordiscrete` (`yxview_parse:226-228` text copied); `colorvar(i.var)` implies `colordiscrete coloruseplegend` (`:213-218`).
- `clegend(clegend_options)`: the contour/colour key's placement and size (`clegend_option.sthlp`: `position(clockpos) ring(#) bmargin() width() height() altaxis title() ...`); dash applies `position()`, `ring()`, `width()`, `height()`, `title()`, `off|on` to the ColorBar (continuous key) and names the rest once; `plegend(legend_options)`: the plot legend's options when `coloruseplegend` puts the colour keys there (dash routes them through the existing `legend()` reader, `_dash_legend_*`); `pcycle(#)`: the number of plot styles before p# recycles (`twowaygraph_g.class:474` `seriesid = mod(serid-1, pcycle)+1`): the colour index `color_idx` passed to every mapper becomes `color_idx % pcycle`.

**Why this section.** S15 (batch 5) made `_apply_colorvar` reach every type; S17 extends its readers and declares the names; one section because every option lands in the same function and the same `_dash_fold_typed` companion list.

**Test order and commit rule.** One row (C8b), one commit `(WP-31 C8b)`: 17-01 tests + extractor; 17-02 dash.ado/Mata; 17-03 renderer; 17-04 certify/document/commit.

### Section decisions (binding on the executor)

- **D-17a. twoway's level colours are measured, then reproduced.** `colorrule(hue)` with the defaults produces a specific set of colours for k levels; the extractor records the SVG fill colours of `scatter mpg weight, colorvar(rep78) colordiscrete` (5 levels) and `colorlevels(3|8)` under the default rule, under `colorrule(linear) colorstart(red) colorend(blue)`, `colorrule(intensity) colorend(navy)`, `colorrule(phue)`, `colorrule(chue)` and `colorrule(hue %50 *1.5)`. The renderer's `_dash_colorrule_palette(rule, start, end, k, opacity, intensity, scheme_p)` (new module-level helper, copied by name) must reproduce each measured list to within 1/255 per channel; `hue`/`chue` interpolate HSV hue at full saturation/value between the start and end hues (Stata's `colorstyle` HSV), `linear` interpolates RGB, `intensity` scales `end` toward white (Stata's intensity: `*#` < 1 lighter, > 1 darker -- the measured list decides the formula; the task writes it from the fixture). twoway's defaults for `colorstart`/`colorend` are not assumed: the values the fixture records (D01) become the Python defaults. The colour bar's continuous palette keeps dash's `colpalette()` when given, else the rule's 256-step palette.
- **D-17b. `colorformissing()` is an alias, `colormissing()` stays.** dash.ado declares `COLORFORMISSing(string asis)` and folds it onto `colormissing` in the alias block (:1264-1299), rightmost wins; `colormissing()` keeps its help as dash's own (twoway refuses it).
- **D-17c. `clegend()` on a Legend key is named.** A discrete key is a Bokeh Legend; twoway's `clegend()` applies to the contour/colour key; on a discrete key under `coloruseplegend` twoway puts the keys in the plot legend and `clegend()` has no key to place -- dash names `clegend()` once there with `_dash_style_note` and applies `plegend()` to the Legend.
- **D-17d. `pcycle(#)` is a graph option.** Declared in `_dash_parse_graph_opts` and in the plot parser's graph list (`g_pcycle`), added to the seven key lists (R6) and `_dash_rep_unique`; the renderer reads `graph_opts.get("pcycle")` once per figure in `_make_figure_body` and the served `_dash_figure_for` and passes `color_idx % pcycle` to `_dash_add_glyph`. `_make_figure_body` has no other batch-6 editor (owner table: S19 `_FILTER_JS`, S18 `map_dot`), so S17 is its editor.
- **D-17e. `colorallowmultiple`.** twoway's refusal of two `colorvar()` layers without the flag is copied (text from U17-04) in `_dash_plot` where the graph's plots are known (near the `_dash_report_ignored` call, :7307); with the flag, each layer keeps its own key as today.

## Risk: [yellow] -- a palette algorithm proved against measured colours, ten new readers in one function, one graph option through seven lists

**Why.** `_apply_colorvar` is 440 lines and shared by every mapper (after S15); the colour arithmetic has to match Stata's `colorstyle` HSV/RGB rules; `pcycle` touches both figure builders.

**Risk factors.** 1. Stata's HSV hue interpolation details (direction, saturation) are compiled; only measurement settles them. 2. `colorkeysrange` changes legend item text that `test_colorvar_legend.py` and `test_colorvar_truth.py` pin for the default (unchanged without the flag). 3. The seven graph key lists must agree (test_abbreviations.py:773). 4. Counts: the declared plot count, the declared graph count and the plot pending count all move (colorlist, coloruseplegend leave the pending block); each is written as the value measured at the section's base -> new, never as a number planned from another section (A33). 5. `coloruseplegend` without `colordiscrete` becomes a refusal (CHANGELOG Changed behaviour).

**Mitigation.** 1. D-17a: the helper is pinned to the fixture's colour lists; where a rule cannot be matched within tolerance the task STOPS and reports (checkpoint-free rule: do not approximate silently -- note the rule in BUGS.md as a residual and keep twoway's measured list as a lookup for k <= 15). 2. Flag-gated paths only. 3. One edit per list, the test proves it. 4. R10 comments. 5. M5 line.

## Dependencies

- **Depends on: 15** (the per-mapper call and `cv_silent`). **Blocks:** none.
- **Parallel batch 6** with S19 (`_FILTER_JS`) and S18 (`map_dot`). S17 edits `_apply_colorvar`'s body, the alias block, the graph key lists, `_make_figure_body`'s `color_idx` line and the served `_dash_figure_for`'s; S18 edits `map_dot` only (its colorvar call is S15's, unchanged).

## Evidence

Anchors at `6370ca4` (S15's batch-5 changes shift `_apply_colorvar` by a few lines; symbols are authoritative).

### Declarations and readers today

dash.ado:1181 `COLORUSEPLEGend`, :1203 `COLORLIst(string asis)`, :1180-1182 `COLORVar(string) COLPALette(string) COLORDIScrete`, `COLORMissing(string)`; :1330-1331 pending lines; :4446-4447 JSON keys `colorvar colpalette colordiscrete coloruseplegend colornlevels colorcuts colormissing colorlevels colorvarminmax ... colorlist`. dash_render.py `_apply_colorvar` :13664: `palette_key = options.get("colpalette")` (:13729), `_use_plegend` dead (:13734), `missing_color` from `colormissing` (:13739-13752), `nlevels`/`_levels` (:13789-13809), `cuts` (:13812-13818), `minmax` (:13822), discrete path builds `factors`, `CategoricalColorMapper(factors=..., palette=...)` (:13966), `Legend(items=legend_items, title=var_display, ...)` (:14007), continuous `LinearColorMapper(palette=palette, low=lo, high=hi, nan_color=missing_color)` (:14027) and `ColorBar` (:14033). The palette comes from `_PALETTE_MAP` (grep) keyed by `colpalette`; discrete default is the scheme's p colours.

### `_dash_rep_und_tab` rows to delete (dash_parse.mata)

:6288 colorallowmultiple, :6289 colorend, :6290 colorfillonly, :6291 colorformissing, :6292 colorkeysrange, :6293 colorkeysreverse, :6294 colorotherlabel, :6295 colorrule, :6296 colorstart, :6300 clegend (graph-wide "1"), :6323 pcycle, :6324 plegend. `_dash_rep_unique` (:6207-6214) gains `pcycle` (graph option taken once; measured U17-05) -- the plot-level colour options are rightmost-wins in `syntax` (string options repeated are r(198) `option X() not allowed`; measured U17-05 for colorrule()).

### twoway (research/stata-ground-truth.md §1.2; sources)

`twoway_yxview_parse.class:185-201` declarations (`COLORSTart COLOREnd COLORLEVels COLORRule COLORCUTs COLORLIst COLORKEYSREVerse COLORALLOWMULTIPLE COLORKEYSRANge COLORVARMINMax COLORFILLONLY COLORFORMISSing COLOROTHERLABel COLORDIScrete COLORUSEPLEGend`); `:213-218` `i.var`; `:226-228` the coloruseplegend-needs-colordiscrete message `you must specify option colordiscrete with option coloruseplegend`; `:342-395` colorrule parsing (`gettoken crule rest : colorrule, parse("*%")`, `invalid colorrule specification`); `:399-436` the attribute stores. `twowaygraph_g.class:175-179` pcycle editstyle, `:395-396, 536-545` coloruseplegend → plegend's zaxis; `:474` seriesid cycle. `colorvar_options.sthlp:143-200` the semantics quoted in Overview.

### Fixtures on disk

`colorvar_truth.json` (bins), `colorvar_qualifier_truth.json`. New: `colorvar_options_truth.json`.

### Pinned tests to flip

- test/test_unsupported_report_is_true.py `PLOT_VALUES["colorlist"]` (:96), `["coloruseplegend"]` (:97) → `LIVE_VALUES` (`"colorlist": ({**_CV,"colordiscrete":"colordiscrete","colorlist":"red blue green"}, {**_CV,"colordiscrete":"colordiscrete","colorlist":"navy maroon orange"}, "scatter", {})`, `"coloruseplegend"`: dash's discrete key is always drawn as a Bokeh Legend, which is twoway's plot-legend form, so `coloruseplegend` is honoured by construction and changes nothing visible on its own (D-17c). Rule: classify `coloruseplegend` in `LIVE_VALUES` with the `colorkeysreverse` pair as the differing side -- `({"colorvar":"foreign","colordiscrete":"colordiscrete","coloruseplegend":"coloruseplegend"}, {"colorvar":"foreign","colordiscrete":"colordiscrete","coloruseplegend":"coloruseplegend","colorkeysreverse":"colorkeysreverse"}, "scatter", {})` -- and the comment `# coloruseplegend: the flag itself is dash's default key form (a Legend); the pair proves its companion colorkeysreverse` (both sides carry the flag; `coloruseplegend` also joins `FLAGS`). Counts (A33): the plot pending count, the declared plot count and the declared graph count are each recounted at the section's base with the file's `_declared_*()` helpers in 17-02 and written `# <measured old> -> <new>: C8b <why>` (pending: colorlist() and coloruseplegend drawn, -2; declared plot: the nine plot options plus `clegend`, `plegend`, `pcycle`, which are declared in both parsers' blocks, +12; declared graph: `clegend plegend pcycle`, +3). The old values are never copied from this file or another section's.
- test/test_help_claims_8.py `_CONTEXT` (:1380): entries for colorlist/coloruseplegend are no longer needed (they leave the pending blocks); add none.
- test/test_colorvar_legend.py, test_colorvar_truth.py: unchanged without flags.
- dash.sthlp:4185-4188, :5048-5054 (S17 owns both, R3); test_help_conformance `TestTheUnsupportedSectionIsTrue` requires the :5048-5054 entry removed.

## User stories

- US-17.1 As a Stata user, I want `colorvar(rep78) colordiscrete colorlist(red blue green orange navy)` to colour the five levels as listed.
- US-17.2 As a Stata user, I want `colorrule(linear) colorstart(white) colorend(navy)` to shade the levels from white to navy.
- US-17.3 As a Stata user, I want `colorformissing(gray)` accepted as twoway spells it, and `colorvar(i.rep78)` to draw discrete keys in the legend.
- US-17.4 As a Stata user, I want `colorfillonly` to leave outlines in the series colour, `colorkeysrange` to show each level's range in the key, `colorkeysreverse` to reverse it, `colorotherlabel("other")` to label the leftover values.
- US-17.5 As a Stata user, I want `clegend(position(6))` to move the colour bar, `plegend(off)` to hide the plot legend holding the colour keys, and `pcycle(3)` to recycle p1-p3.

## Business requirements

- BR-17.1 Each option draws what `colorvar_options.sthlp` describes, with level colours matching twoway's to 1/255 per channel for the measured rules.
- BR-17.2 `coloruseplegend` without `colordiscrete`, a second `colorvar()` layer without `colorallowmultiple`, and a bad `colorrule()` are refused with twoway's words and rc.
- BR-17.3 `colorformissing()` and `colormissing()` are one option; `colorvar(i.var)` draws.
- BR-17.4 `clegend()`, `plegend()` and `pcycle()` are honoured where Bokeh can express them; a `clegend()` sub-option dash cannot place is named once.
- BR-17.5 Nothing is printed for an honoured option.

## Technical requirements

- TR-17.1 **Declare (plot parser :1167-1239)**: after `COLORLEVels(string)       COLORVARMINMax ///` (:1183): `COLORSTart(string asis) COLOREnd(string asis) COLORRule(string asis) COLORFILLONLY COLORFORMISSing(string asis) COLORKEYSRANge COLORKEYSREVerse COLORALLOWMULTIPLE COLOROTHERLABel(string asis) ///`; graph options in both parsers: `CLEGend(string asis) PLEGend(string asis) PCYCle(string)` (twoway's minimums `cleg`, `pleg`, `pcyc` per `_dash_rep_und_tab`'s own shortest-spelling column :6300, :6323-6324). `sreturn local` for each (plot keys after :1524; `g_clegend g_plegend g_pcycle` in the `g_` block :1532-1607 and the graph parser's :1046-1121). Alias fold (:1264-1299): `if `"`macval(colorformissing)'"' != "" local colormissing : copy local colorformissing` (rightmost wins: twoway has one option; dash's `colormissing()` given with it -- `colorformissing()` wins). JSON plot keys after `colorvarminmax` (:4447): `colorstart colorend colorrule colorfillonly colorkeysrange colorkeysreverse colorallowmultiple colorotherlabel`; the seven graph key lists (:5776, 6714, 6748, 6849, 6924, 6956, 7339) each gain `clegend plegend pcycle` after `legend`; `_dash_rep_cat`: `clegend`, `plegend` → "I" (merged like legend(); :6180), `pcycle` "R"; `_dash_rep_unique` gains `pcycle` (U17-05 decides the others). `_dash_option_rules` plot tokens: `colorstart=colour colorend=colour` (kind `colour` refuses a comma RGB as the others), `colorotherlabel` none; graph `pcycle=int,<lo>,<hi>` with the bound twoway enforces, measured by U17-05's P02 (`pcycle(0)`, `pcycle(16)`) and written from the fixture.
- TR-17.2 **Delete** the twelve `_dash_rep_und_tab` rows listed in Evidence; the pending lines :1330-1331; add `colorformissing` to `_dash_fold_typed`'s companion list (S15's `cv_silent` loop) so it is dropped on silent types too, and the eight new companions likewise.
- TR-17.3 **Refusals** (dash.ado, `_dash_process_segment` after S15's multi-y check): `coloruseplegend` without `colordiscrete` → `yxview_parse:226-228`'s text (fixture R01), r(198); `colorrule()` not in `hue chue phue intensity linear` (first token before `%`/`*`) → `invalid colorrule specification` r(198) (fixture R02); `colorvar(i.var)`: in the colorvar var check (:2194 region) strip a leading `i.`/`I.`, set `colordiscrete` and `coloruseplegend`, then `confirm numeric variable`. In `_dash_plot`: two plots with `colorvar` and no `colorallowmultiple` on any → fixture R03's text, rc.
- TR-17.4 **Renderer `_apply_colorvar`**: (a) read `rule, opacity, intensity = _dash_colorrule_parse(options.get("colorrule"))` (new module-level helper: splits on `%`/`*` as `yxview_parse:342-395`; returns `("hue", None, None)` by default); `start = self.tr.parse_color_alpha(options.get("colorstart"), "colorstart")`, `end` likewise; `colorlist = _dash_stylelist_split(options.get("colorlist"))` (the existing stylelist splitter the appliers use for `mcolor(a b)`; translate each through `parse_color_alpha`); (b) the discrete palette: `colorlist` if given (a list shorter than the levels follows fixture D03: cycled if twoway cycles, refused with twoway's text if twoway refuses), else `_dash_colorrule_palette(rule, start, end, len(factors), opacity, intensity, [self.scheme.default_color(i, "scatter") for i in range(15)])` (D-17a; the `phue` rule uses the scheme list), else today's palette when `colpalette()` is given (dash's own wins when typed); the continuous palette: `colpalette()` if given, else the rule's 256 steps; (c) `colorfillonly`: the property loop (S15's `hasattr` loop) sets `fill_color` only; (d) `colorkeysrange`: legend item labels become `f"{lo} - {hi}"` from `_dash_colorvar_bins`' interval bounds (`_dash_colorvar_bins` already returns labels; add a `ranged=True` argument producing the range text with `number_text`); (e) `colorkeysreverse`: on a discrete key `legend_items.reverse()`; on a continuous key the flag is named once (`_dash_style_note("colorkeysreverse", "", "continuous key", "drawn unreversed")`), because twoway reverses the key and not the mapping, and Bokeh cannot reverse a ColorBar's direction without reversing its mapper; (f) `colorotherlabel`: replaces the "(missing)" item text for the rows outside the cuts under `colordiscrete` with cuts (`_dash_colorvar_bins`' `has_missing` path: split "missing" (NaN) from "other" (finite, outside) so the two labels can differ; both coloured `missing_color` unless twoway colours "other" otherwise -- fixture D05 decides); (g) `coloruseplegend`: delete the dead `_use_plegend` line; the discrete path already draws a Legend. (h) `clegend()`: `_dash_clegend_opts(text)` (new module-level helper reusing `_dash_legend_*`'s sub-option tokenizer for `position() ring() width() height() title() off on`) applied to `_cbar` (`location` from the clock through the existing clock→location table used for `legend(position())`; `width`/`height` through `resolve_size`; `title`; `visible=False` for off); other sub-options named once. (i) `plegend()`: when the key is a Legend and `graph_opts["plegend"]` is given, apply it through the same path `legend()` takes (`_dash_apply_legend_opts`-equivalent: find the function `_make_figure_body` calls with `graph_opts.get("legend")` and call it with `plegend`'s text on `_legend`).
- TR-17.5 **pcycle** (D-17d): `_make_figure_body` and the served `_dash_figure_for`: `pc = _dash_pcycle(graph_opts)` (module-level helper returning an int in [1, 15] or None) and `color_idx = (idx % pc) if pc else idx` where `color_idx` is computed for `_dash_add_glyph`.
- TR-17.6 **Copy list (R2)**: `_dash_colorrule_parse`, `_dash_colorrule_palette`, `_dash_clegend_opts`, `_dash_pcycle` after `_dash_reference_lines` (:47223); function_test_map.py entries each → `test/test_colorvar_options.py::<class>::<test>`; `_dash_colorvar_bins`'s new argument needs no entry (existing function).
- TR-17.7 **Tests/pins**: LIVE_VALUES entries for `colorlist`, `coloruseplegend` (Evidence rule), `colorstart`, `colorend`, `colorrule`, `colorfillonly`, `colorformissing`, `colorkeysrange`, `colorkeysreverse`, `colorallowmultiple` (two layers; the harness renders one plot -- classify in `NOT_IN_FILE`-style with a dedicated test and comment), `colorotherlabel`; graph `clegend`, `plegend`, `pcycle` with pairs (`{"pcycle":"1"}` vs `{"pcycle":"2"}` on a two-y scatter). FLAGS gains `coloruseplegend colorfillonly colorkeysrange colorkeysreverse colorallowmultiple`. Counts per A33: each pin recounted at the section's base with `_declared_plot()`/`_declared_graph()` and the pending reader, written `# <measured old> -> <new>: C8b <why>`.

## Boundaries

- No `_FILTER_JS` (S19). No `map_dot` (S18). No `cv_silent` list change (S15's measured list; S17 adds names to the companion loop only).
- `colpalette()`, `colornlevels()`, `colormissing()` stay dash's own and documented as such.
- Contour's `clegend()` (S26, batch 9) reuses `_dash_clegend_opts`; S17 writes it for the ColorBar only.

## Stata truth

New `scripts/extract_colorvar_options_truth.do` → `test/fixtures/colorvar_options_truth.json`; `sysuse auto`:
- `D01` `scatter mpg weight, colorvar(rep78) colordiscrete name(d1)`: `.d1.plotregion1.plot1.colorrule/.colorstart/.colorend` (defaults) and the SVG marker fill colours per level (sorted by level); `D02` `colorlevels(3)`, `colorlevels(8)` under the default rule; `D03` `colorlist(red blue)` with 5 levels (rc, colours or message); `D04` `colorrule(linear) colorstart(white) colorend(navy)`; `D05` `colordiscrete colorcuts(3 4) colorotherlabel("rest")` key texts and the "rest" colour; `D06` `colorrule(intensity) colorend(navy)`; `D07` `colorrule(phue)`; `D08` `colorrule(chue) colorstart(blue) colorend(red)`; `D09` `colorrule(hue %50 *1.5)` (fill-opacity and colours); `D10` `colorfillonly` (stroke colours = series colour); `D11` `colorkeysrange colorlevels(4)` key texts; `D12` `colorkeysreverse` key order; `D13` `colorvar(i.rep78)` → `.plot1.colordiscrete`, `.coloruseplegend`.
- `R01` `coloruseplegend` without colordiscrete (rc, text); `R02` `colorrule(bogus)`; `R03` two colorvar layers without `colorallowmultiple` and with; `R04` `colormissing(red)` (twoway rc 198 expected: dash's own).
- `G01` `clegend(position(6) ring(1) width(5) height(20) title("Z"))` on a continuous colorvar: `.clegend.style.*` and the SVG box; `G02` `plegend(off)` with `coloruseplegend`; `U17-05`-feeding `P01` `pcycle(2)` on `scatter mpg price weight`: `.plotregion1.plot<k>.seriesid` and the marker colours for k = 1..3 (expected p1, p2, p1; the fixture decides); `P02` `pcycle(0)`, `pcycle(16)`, `pcycle(2) pcycle(3)` rc/text.
`_meta`, `git add -f`, test_fixtures_are_committed.py.

## TDD test stubs

New `test/test_colorvar_options.py`:
- Test: `_dash_colorrule_parse` on `"hue"`, `"linear %40 *2"`, `""`, `"bogus"` -- `TestColorruleParse::test_forms` (red).
- Test: `_dash_colorrule_palette` reproduces D01, D02, D04, D06, D07, D08, D09 colour lists within 1/255 -- `TestColorrulePalette::test_matches_twoway[probe]` (red).
- Test: `colorlist(red blue green)` colours the levels in order in both modes; D03's short-list behaviour -- `TestColorlist::test_in_order[mode]`, `::test_short_list` (red).
- Test: `colorfillonly` leaves `line_color` scalar -- `TestFillonly::test_outline_kept[mode]` (red); `colorformissing(gray)` equals `colormissing(gray)` and wins when both given -- `TestFormissing::test_alias[mode]` (red).
- Test: `colorkeysrange` item labels are `lo - hi` texts equal to D11's; `colorkeysreverse` reverses the Legend; on a ColorBar the flag is named once -- `TestKeys::test_range[mode]`, `::test_reverse[mode]`, `::test_reverse_on_colorbar_named` (red).
- Test: `colorotherlabel("rest")` labels the outside-cuts rows and keeps "(missing)" for NaN -- `TestOtherlabel::test_two_labels[mode]` (red).
- Test: `colorvar(i.rep78)` in a spec written by dash carries `colordiscrete`/`coloruseplegend` (read the saved spec in the cscript; the pytest half reads `_dash_fold_typed`'s text) -- `TestIVar::test_ado_text` (red).
- Test: `clegend(position(6) width(5))` moves/sizes the ColorBar; `plegend(off)` hides the Legend; `pcycle(2)` gives plot 3 p1's colour -- `TestClegend::test_position_width[mode]`, `TestPlegend::test_off[mode]`, `TestPcycle::test_recycles[mode]` (red); the four helpers on the copy list -- `TestTheServedCopy::test_names` (red).
- Test: the seven graph key lists agree (test_abbreviations.py:773 already) -- guard; dash.ado declares the fifteen and `_dash_rep_und_tab` has none of the twelve rows -- `TestTheAdoText::test_declared` (red).

cscript, block `* ==== S17 C8b: colorvar options ====` (the section's one row; appended by 17-04, the closing task, A14):
- U17-01 `dash scatter mpg weight, colorvar(rep78) colordiscrete`: render fill colours equal D01's list within 1/255, both modes; no note.
- U17-02 `colorlist(red blue)` with 5 levels: dash rc/colours equal D03.
- U17-03 `colorformissing(gray)`: dash rc 0, no note; `colormissing(gray)`: dash rc 0 (dash's own), twoway R04 rc 198 (asserted on twoway so the help sentence stays true).
- U17-04 refusals R01, R02, R03: dash rc and message equal twoway's (`cert_log_has`).
- U17-05 `pcycle(2)` colours plot 3 as p1 in dash's render; `pcycle(0)`/`pcycle(16)`/twice: dash rc = twoway rc; `colorrule(hue) colorrule(linear)` twice: rc equal.
- U17-06 `colorvar(i.rep78)`: dash rc 0 (was 111), spec carries colordiscrete and coloruseplegend; `clegend(position(6))` and `plegend(off)`: rc 0, no note.

Parity (R8): CORPUS `_case("colorvar colorrule(linear) colorstart(white) colorend(navy)", ...)`, `_case("colorvar colorlist", ...)`, `_case("colorvar colorfillonly colorkeysrange", ...)`, `_case("colorvar clegend(position(6))", go={"clegend":"position(6)"})`, `_case("pcycle(2) three series", go={"pcycle":"2"})`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| colorrule/start/end palettes | pytest TestColorrulePalette; U17-01 | colorvar_options_truth D01-D09 | yes |
| colorlist | pytest TestColorlist; U17-02 | D03 | yes |
| fillonly/formissing/keysrange/keysreverse/otherlabel | pytest; U17-03 | D05 D10-D12 | yes |
| refusals | U17-04, U17-05 | R01-R03, P02 | n/a |
| i.var, clegend, plegend, pcycle | pytest TestIVar/TestClegend/TestPlegend/TestPcycle; U17-05/06 | D13 G01 G02 P01 | yes |

AC-17.1 stubs green; AC-17.2 U17-01..06 PASS; AC-17.3 dash.sthlp:5048-5054 entry removed, :4140-4210 rewritten (synoptset gains the new options; the sentence "colorrule() ... are named in the note" deleted); AC-17.4 audit rows 118, 140 annotated.

## Tasks

**Commit boundary.** 17-01..17-03 steps; 17-04 commits `Draw twoway's colorvar options, alias colorformissing(), accept colorvar(i.var), honour clegend(), plegend() and pcycle() (WP-31 C8b)` on `wp31-s17`.

<task type="auto" id="17-01">
  <name>Write the failing option tests and the colour truth extractor</name>
  <files>test/test_colorvar_options.py, scripts/extract_colorvar_options_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_colorvar_options_truth.do on scripts/extract_default_base_truth.do's skeleton with probes D01-D13, R01-R04, G01-G02, P01-P02 of "Stata truth" (class values through `.d1.plotregion1.plot1.<attr>`; marker fills through `graph export` SVG read with test/cert_svg.do's `svg_truth.svg_document`, grouped by level order; refusal texts via `capture noisily` and a tempfile log). Run it through the slot wrapper; `git add -f test/fixtures/colorvar_options_truth.json`; register the name. Create test/test_colorvar_options.py with every stub, reading the expected colour lists FROM the fixture. Run `python3 -m pytest test/test_colorvar_options.py -q -p no:randomly > <scratch>/17-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/17-01-failure.txt prints >= 18; python3 -c "import json;d=json.load(open('test/fixtures/colorvar_options_truth.json'));print(d['D01']['colorrule'], len(d['D01']['fills']))" prints the default rule name and 5.]]></verify>
  <done>The option tests fail against the batch-6 base and twoway's level colours, key texts and refusal texts are committed.</done>
</task>

<task type="auto" id="17-02">
  <name>Declare the fifteen options, the alias and the refusals in Stata</name>
  <files>dash.ado, dash_parse.mata, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[Apply TR-17.1 (plot declarations after :1183; graph declarations `CLEGend PLEGend PCYCle` in both parsers; sreturns; the colorformissing fold at :1264-1299; JSON keys after :4447; the seven graph key lists at :5776, 6714, 6748, 6849, 6924, 6956, 7339 each gaining `clegend plegend pcycle` after `legend`; `_dash_rep_cat` "I" for clegend/plegend at dash_parse.mata:6180; `_dash_rep_unique` pcycle; the rules `colorstart=colour colorend=colour` and pcycle's measured bound), TR-17.2 (delete the twelve `_dash_rep_und_tab` rows at :6288-6296, :6300, :6323-6324 and the pending lines :1330-1331; extend S15's companion loop in `_dash_fold_typed` with the nine new names) and TR-17.3 (the three refusals with texts typed from R01-R03; the `i.` strip at the colorvar check near :2194). test_unsupported_report_is_true.py: TR-17.7 (LIVE_VALUES, FLAGS; the plot pending, declared plot and declared graph counts each recounted at the section's base with the file's `_declared_*()` helpers and written `# <measured old> -> <new>: C8b <why>` -- never a number copied from this plan, A33). Run `python3 -m pytest test/test_colorvar_options.py::TestTheAdoText test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_help_claims_8.py -k "Unsupported" -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed; `grep -c '"colorrule"' dash_parse.mata` prints 0; `grep -c "clegend plegend pcycle" dash.ado` prints 7.]]></verify>
  <done>dash.ado declares every twoway colorvar option plus clegend(), plegend() and pcycle(), folds colorformissing() onto colormissing(), accepts colorvar(i.var) and refuses what twoway refuses with its words.</done>
</task>

<task type="auto" id="17-03">
  <name>Draw the options in the colour mapper and the figure builders</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Apply TR-17.4 (a)-(i) in `_apply_colorvar` (:13664-14103 at the batch-6 base; the readers after `minmax` :13822, the palette choice at the `CategoricalColorMapper` :13966 and `LinearColorMapper` :14027 sites, the property loop S15 added, the Legend/ColorBar sites :14007/:14033), with the four module-level helpers placed after `_dash_colorvar_field` (:36585-36600) and appended to the functions copy tuple after "_dash_reference_lines" (:47223); TR-17.5 in `_make_figure_body` (the `color_idx` passed to `_dash_add_glyph` in the branches :43981-44023) and the served template's `_dash_figure_for`/`_dash_draw_layer` (:49137-49225). Write `_dash_colorrule_palette`'s arithmetic FROM the fixture: start with HSV-hue interpolation (hue, chue), RGB interpolation (linear), intensity scaling of `end` toward white for `*#` < 1 and toward black above (intensity), and the scheme's p1..p15 then hue (phue); if any D-probe is not matched within 1/255 after the formula is fitted, stop, record the rule's measured list as a lookup table for k <= 15 with a `# WP-31 C8b: formula unknown, measured colours` comment, and report it in the hand-back (D-17a). Add the function_test_map.py entries. Run `python3 -m pytest test/test_colorvar_options.py test/test_colorvar_coverage.py test/test_colorvar_truth.py test/test_colorvar_forms.py test/test_colorvar_legend.py test/test_glyphs.py -k Colorvar test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py test/test_mode_parity.py -k "colorvar or pcycle" -q`.]]></action>
  <verify><![CDATA[pytest prints 0 failed; `grep -c "_use_plegend" dash_render.py` prints 0; `python3 -c "import dash_render as d;print(all(callable(getattr(d,n)) for n in ('_dash_colorrule_parse','_dash_colorrule_palette','_dash_clegend_opts','_dash_pcycle')))"` prints True.]]></verify>
  <done>Both renderers draw colorrule()/colorstart()/colorend()/colorlist()/colorfillonly/colorkeysrange/colorkeysreverse/colorotherlabel()/coloruseplegend, clegend() on the colour bar, plegend() on the key legend and pcycle() on the series cycle.</done>
</task>

<task type="auto" id="17-04">
  <name>Certify, document and commit C8b</name>
  <files>test/test_wp31_truth.cscript, dash.sthlp, TWOWAY_COVERAGE_AUDIT.md</files>
  <action><![CDATA[Append `* ==== S17 C8b: colorvar options ====` (U17-01..U17-06) above the marker (after S15's block) and run with `WP31_ONLY=S17`. dash.sthlp: delete the "colorvar() sub-options" Unsupported entry (:5048-5054); in the colorvar section (:4140-4210) add synopt rows for `colorrule() colorstart() colorend() colorlist() colorfillonly colorformissing() colorkeysrange colorkeysreverse colorallowmultiple colorotherlabel() coloruseplegend` with one-line meanings from colorvar_options.sthlp and the note that `colorformissing()` is twoway's spelling of `colormissing()`; replace the sentence "twoway's other colorvar options, colorrule(), colorstart(), colorend() and colorformissing(), are named in the note" by "every colorvar option twoway takes is drawn; colorkeysreverse on a continuous key is named, because the colour bar cannot be reversed without reversing the mapping"; add `clegend()`, `plegend()`, `pcycle()` entries to the graph options synoptset (grep `{synopt:{opt legend(` dash.sthlp for the anchor) with `clegend()`'s honoured sub-options listed. TWOWAY_COVERAGE_AUDIT.md rows 118 and 140: `[WP-31 C8b, commit pending: corrected -- every colorvar option drawn; clegend(), plegend(), pcycle() honoured]`. Close the C8b BUGS.md entry (Resolution form naming test/test_colorvar_options.py::TestColorrulePalette::test_matches_twoway[D01], U17-01, the fixture, and a Residual clause if D-17a fell back to a lookup table), write the GAPS3 line `- **C8b Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b rewrites `pending` to the landed sha), replace the `<!-- WP-31 C8b -->` markers (Results: "scatter mpg weight, colorvar(rep78) colordiscrete: levels in twoway's hue colours (was: the scheme's p colours)"; Changed behaviour: "coloruseplegend without colordiscrete, a second colorvar() layer without colorallowmultiple and a bad colorrule() are refused, twoway's words"; Changed behaviour: "colorvar(i.var) now draws (was r(111))"). Run `python3 -m pytest test/test_colorvar_options.py test/test_help_conformance.py test/test_tracking_documents.py -q`; commit; grep for `claude|anthropic`.]]></action>
  <verify><![CDATA[Stata log shows "U17-01 PASS" .. "U17-06 PASS"; pytest 0 failed; `git log -1 --format=%s` ends "(WP-31 C8b)"; `grep -c 'C8b Tracked:\*\* Closed in WP-31' GAPS3.md` prints 1; `grep -c "colorvar() sub-options" dash.sthlp` prints 0.]]></verify>
  <done>C8b is closed in one commit with its tests, fixture, help, audit, BUGS.md, GAPS3 and CHANGELOG lines.</done>
</task>

## Section completion criteria

- Stubs green; U17-01..06 PASS; counts moved with comments; `_use_plegend` gone.
- Four helpers on the copy list and in function_test_map.py; seven graph key lists agree; twelve `_dash_rep_und_tab` rows gone.
- Help, audit, BUGS.md, GAPS3, CHANGELOG in the one commit; any palette-formula fallback reported.

## Notes

- **Renderer order:** `colorlist` > `colpalette` (dash's own, typed) > `colorrule` for the discrete palette -- twoway has no colpalette, so a typed colpalette() is the user's explicit choice; document in the help line.
- **Copy list (R2):** the four helpers after `_dash_reference_lines` (:47223); `_dash_colorvar_bins`' new argument is an existing name.
- **Seven key lists (R6):** test_abbreviations.py:773 proves them; edit all seven in one task.
- **Fixture rule (R7)**; **python_exec hazard**; **security:** colour names go through `parse_color_alpha` (never raw to Bokeh); `colorotherlabel` text is Legend label DATA (Bokeh escapes), never markup; `clegend(title())` text through the same path `legend(title())` takes.
- **Merge rules cited:** R1, R2, R3 (S17 owns dash.sthlp:4140-4210 and :5048-5054), R6, R8, R9, R10, R12 (S17 is batch 6's `_apply_colorvar` and `_make_figure_body` editor).
- **Commit body lines:** `Regression: test/test_colorvar_options.py::TestColorrulePalette::test_matches_twoway[D01] -- failed at <base> with <text>`; `Fixture: test/fixtures/colorvar_options_truth.json (scripts/extract_colorvar_options_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS3: C8b Tracked`.
- **Decisions for maintainer ratification:** D-17a (measured palettes with a lookup fallback), D-17b (alias direction), D-17c (clegend named on a Legend key), D-17d (pcycle as a graph option through the seven lists), the colorkeysreverse-on-ColorBar naming.
