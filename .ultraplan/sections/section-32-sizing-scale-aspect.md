# Section 32: Sizing: scale(), fxsize()/fysize(), overhangs, aspectratio()

> Part of: WP-31 · GAPS3 rows: D5, E11 · Risk: yellow · Batch: 11 · Depends on: 01 · Blocks: -- · Tasks: 4, 2 commits · Case-id prefix: U32

## Overview

**What is wrong today.** GAPS3 D5 (GAPS3.md:155): "`scale()`, `fxsize()`, `fysize()`, `xoverhangs`, `yoverhangs` pending, never read; `aspectratio()` shapes the figure not the plot region, loses to `xsize/ysize`, and `aspectratio(#, placement())` is refused as 'not a positive number'." Evidence `dash.ado:1028-1048, :3047, :3166-3190; dash_render.py:21362-21366, :43721`. GAPS3 E11 (:190): "Sizes are relative to a 4-inch reference and `scale()` is pending (see D5)." Evidence `dash_render.py:7098, :7221, :11450`. At `6370ca4`: `SCALE FXSIZE FYSIZE XOVERHANGs YOVERHANGs` are declared (dash.ado:944-945, :952), named pending (:1019-1020 fxsize/fysize, :1027 scale, :1039 xoverhangs, :1042 yoverhangs; plot twins :1356-1387) and written to `graph_options`; `aspectratio=num,0` (:3047) is the rule that refuses `aspectratio(0.5, placement(e))` because the whole value is not a number; `_dash_figure_aspect` (dash_render.py:21332-21378) returns `xs/ys` first (:21363-21367) and `1.0/ar` only when neither size is given (:21376-21377), and the value becomes `fig_kwargs["aspect_ratio"]` (:43721-43722), the WHOLE figure's width/height, where twoway's `aspectratio()` is the plot region's height/width (`test_graph_options.py:156-161` records the 2026 measurement: aspectratio(0.25) on a 600x600 export gives a plot region 542x152). `OptionTranslator.resolve_size(value, kind, default_pt, ref_in=4.0)` (:7098) converts absolute units at the figure's reference `size_ref_of(fig)` (:7221; `fig._dash_size_ref_in` stamped by `apply_to_figure`, :11450), with no multiplier anywhere for `scale()`.

**After this section** `scale(#)` multiplies every drawn size of the figure in both modes -- text (titles, axis titles, tick labels, legend labels, added text, minor labels), markers, line widths (glyphs, axes, ticks, grids, reference lines, borders), tick lengths, standoffs and legend key geometry -- by `#`, as twoway's `scale()` does, through one post-pass over the finished figure, so every renderer path and every later section's sizes are covered without editing them. `fysize(#)` draws the figure `#` percent of its height, `fxsize(#)` gives it `#` percent of the width it would take in its row (CSS `flex-grow` on Bokeh's flex `Row`, Bokeh 3's layout engine; both modes). `aspectratio(#[, placement(compass)])` is parsed as twoway parses it and `aspectratio(#, placement(x))` is accepted; with `xsize()`/`ysize()` it shapes the PLOT REGION (Bokeh's frame, sized in Python: `frame_width`/`frame_height` from the figure size minus the scheme's border estimate, `min_border_*` from `placement()`), so it survives the sizes; without sizes the figure keeps `1/#` as its own ratio, as today, and the chrome correction is documented under M17 (DECISIONS A16; no page JavaScript). `xoverhangs`/`yoverhangs` are measured on twoway's `.Graph` and, if they change only the graph region's margins (the expected finding: Bokeh's layout already reserves room for every end label), are honoured as no-ops and documented; if they change the plot region's size, their effect is drawn (D-32.d). E11 is closed by `scale()` plus a help paragraph stating the reference rule (relative sizes are Stata units of 2.88 pt at the scheme's `graphsize`-derived reference; `xsize()`/`ysize()` move the reference as twoway's do).

**Why two rows share this section.** E11 is D5's `scale()` half plus a documentation duty on the same reference machinery (`resolve_size`, `size_ref_of`).

**Test order and commit rule (BRIEF).** Two cycles, two commits: D5 (32-01 red tests and fixture; 32-02 dash.ado parsing and the renderer; 32-03 certify, flip, document, commit `(WP-31 D5)`), then E11 (32-04: the reference test and help paragraph, commit `(WP-31 E11)`).

### Section decisions (this file; binding on the executor)

- **D-32.a `scale()` is a post-pass, not a per-site change.** New `_dash_apply_scale(fig, factor)` runs after every option is applied (saved: the last statement of `_make_figure_body` before the figure is returned, after `_dash_apply_axis_options`; served: the template line after `_dash_apply_axis_options` in `_dash_figure_for`). It multiplies: every `Axis`'s `major_label_text_font_size`, `axis_label_text_font_size`, `major_tick_in/out`, `minor_tick_in/out`, `axis_label_standoff`, `major_label_standoff`, `axis_line_width`, `major_tick_line_width`, `minor_tick_line_width`; every `Grid`'s `grid_line_width`, `minor_grid_line_width`; every `Title`/`Label`/`LabelSet`'s `text_font_size` (a `LabelSet` field size is left), `border_line_width`, `padding`, `x_offset`/`y_offset`; every `Legend`'s `label_text_font_size`, `title_text_font_size`, `glyph_width`, `glyph_height`, `label_standoff`, `spacing`, `padding`, `margin`; every `Span`'s `line_width`; every glyph renderer's glyph `line_width` (value specs only) and `size` (value specs; a field spec's column is multiplied in the renderer's `data_source` when the column name starts with `__dash_` -- dash's own derived size columns -- and left when it is a user column); the `nonselection_glyph`/`muted_glyph`/`hover_glyph` twins alike; `Arrow` heads' `size`. CSS sizes are read with `OptionTranslator.css_to_pt` and written with `css_pt(pt * factor)`; `Int` properties as `max(0, int(round(v * factor)))`. The served redraw copies glyph specs, so the scaled constants persist across a move; the saved page's `_FILTER_JS` rewrites data columns only, so `__dash_` size columns are regenerated unscaled after a move -- `_dash_apply_scale` therefore also records `fig._dash_scale = factor` and the saved renderer's size-column writers (`__dash_msize*`, S20's weighted markers) read it when they rebuild; test `TestScaleHoldsAcrossAMove` pins both modes. Gaps twoway scales (margins between boxes) are not scaled (documented, M17).
- **D-32.b `fxsize()`/`fysize()`.** `fysize(#)`: when the figure has `aspect_ratio`, `aspect_ratio *= 100 / #` (height shrinks to `#` %); else `height = max(_MIN_FIGURE_HEIGHT, round(height * # / 100))`. `fxsize(#)`: `fig.styles = {**fig.styles, "flex-grow": f"{#/100:g}", "flex-basis": "0px"}` so a Bokeh `Row` (a `FlexBox`, CSS `display: flex`) gives it `#/100` of a full-width sibling's share, which is twoway's "# percent of its normal width" when the siblings are at 100; a figure alone in its row takes the whole row (twoway: `fxsize()` alone narrows the graph -- the difference is documented, M17). Verified in a Chrome test (the DevTools harness test_csp_browser.py uses) that the host element's width is `#`% of a 100-sibling's; the `styles` dict is a Bokeh property, no raw CSS reaches the page (rule 1). Both are read in `_dash_layout_cell` (:35899; S32 is batch 11's `_dash_layout_cell` editor, R12) where the figure's grid cell is known, from `gopts_of(name)`.
- **D-32.c `aspectratio()` sets frame sizes, not a callback (DECISIONS A16).** dash.ado splits `aspectratio(#, placement(compass))` into `aspectratio` (the number, validated by the existing `num,0` rule) and a new graph key `aspectplacement` (canonical compass via `_dash_at_place`, dash_parse.mata:9196; an unknown name gets twoway's measured words, U32-7). Renderer: `_dash_figure_aspect` returns the figure ratio from `xsize/ysize` as today and, separately, `_dash_frame_aspect(graph_opts) -> float | None` returns `ar` (height/width). In `_make_figure_body` and `_dash_figure_for`, when `ar` is given: (i) **without `xsize/ysize`** the figure keeps `aspect_ratio = 1/ar` as today (the figure's ratio, not the frame's; the chrome makes the frame's ratio differ by the border widths -- documented under M17 with the fixture's measured difference, `placement()` accepted and documented as not drawn in this case); (ii) **with `xsize/ysize`** the figure size is known in Python (`width`/`height` px from the sizes at the dpi rule `_dash_figure_aspect` already uses), so `_dash_frame_sizes(fig, ar, placement, width, height)` sets `fig.frame_width`/`fig.frame_height` to the largest frame of ratio `ar` that fits `width - (bl + br)` x `height - (bt + bb)`, where `bl/br/bt/bb` are the scheme's border estimate (the `min_border_*` the scheme applier set, else `fig.min_border`, plus the axis panel estimate `_dash_scheme_chrome` gives for the figure's axes and titles), and `min_border_left/right/top/bottom` from `placement()` (`c` centres the slack; `w`/`e` push it to the right/left; `n`/`s` to the bottom/top; corners both; the opposite side keeps its estimate). Bokeh honours `frame_width`/`frame_height` as fixed frame dimensions (bokeh.js:44611-44614, probed on 3.8.0), so the plot region sits where twoway's `placement()` puts it. No page JavaScript: BokehJS sets `inner_width`/`inner_height` with `no_change: true` (bokeh.js:45196-45201), so a `js_on_change` on them never fires; no callback is written.
- **D-32.d Overhangs** are decided by the fixture: `xoverhangs` on `scatter mpg weight, xlabel(1760 "a very long first label" 4840)` is measured as the plot region's width before/after (`.Graph.plotregion1` box in the SVG). Expected: the graph region grows and the plot region shrinks by the label's overhang; Bokeh already sizes `min_border` to the labels, so dash draws no clipped label with or without the option -> honoured no-op, documented. If the fixture shows twoway does more (a plot-region move), the option sets `min_border_left/right` (x) or `top/bottom` (y) to the measured overhang in px; the test pins whichever the fixture says.
- **D-32.e The reference (E11).** `size_ref_in` stays the scheme's `graphsize`-derived inch value; `xsize()`/`ysize()` already move it when both are given (WP-30 P1.12a); the test pins that `xsize(8) ysize(4)` moves the reference to twoway's rule (min of the two? measured: twoway's relative sizes are relative to the smaller graph dimension -- U32-8 measures a `size(5)` title at xsize 8/ysize 4 vs 4/4) and the help states the rule. `scale()` never changes the reference; it multiplies afterwards.

## Risk: [yellow] -- every size on every figure can change, the layout cell gains CSS, and fixed-size figures gain frame sizes

**Why.** `_dash_apply_scale` touches every model class; `_dash_layout_cell` and the template gain lines; `_dash_option_rules` gains S32's three tokens plus S33's `lwidth` bound and S34's `lalign`/`mlalign` enum tokens (A15); `frame_width`/`frame_height` are set on fixed-size figures.

**Risk factors.** 1. A property multiplied twice (post-pass after a served redraw) or missed (a model class not listed). 2. `fxsize` relies on Bokeh's flex layout honouring an inline style. 3. `frame_width`/`frame_height` larger than the figure's inner box (a bad border estimate) makes Bokeh grow the figure past `xsize/ysize`. 4. `aspectratio` tests pin `fig.aspect_ratio == 1/1.5` (test_graph_options.py:156-162, test_geometry.py:216-262). 5. Batch 11: S33 edits the axis appliers (`_dash_apply_axis_spec`, `_dash_scale_look`), S34 dash.ado's syntax; S32's post-pass must run after S33's appliers and S32's dash.ado edits must not touch S34's lines.

**Mitigation.** 1. `_dash_apply_scale` is idempotent per figure (`fig._dash_scaled = factor` guard) and the test walks `fig.select(...)` for every class with a size property, asserting each equals base x factor. 2. The Chrome test and a documented fallback (`max_width`). 3. `_dash_frame_sizes` clamps the frame to the inner box and the test exports the saved page to PNG once (Chrome harness) and asserts the figure's host box equals `xsize/ysize` within 2 px. 4. Flipped: the figure ratio stays `1/ar` without sizes (guard), the frame rule is the new assertion. 5. The post-pass is a separate function called at the end; S32's dash.ado edits are the pending lines, the `aspectratio` split helper and the rules tokens (its own three plus S33's and S34's, A15), none in `_dash_parse_plot_opts`' option syntax S34 edits (Boundaries).

## Dependencies

- **Depends on: 01.** Markers `<!-- WP-31 D5 -->` (Results, Changed behaviour: `aspectratio(#, placement())` now accepted), `<!-- WP-31 E11 -->` (Requirements); BUGS entries; truth script.
- **Blocks: --.** S48 (data table, batch 16) and S53 (export, batch 18) read `fig._dash_scale` if they draw text.
- **Parallel batch: 11**, merge order S32, S33, S34. **Can run with S33 and S34**: S33 edits `_dash_apply_axis_spec`/`_dash_scale_look`/`_dash_apply_scale_look`; S34 edits `_dash_parse_plot_opts`' syntax and the mlabel readers; S32 edits `_dash_layout_cell`, `_dash_figure_aspect`, `_make_figure_body`'s tail, the template's tail line, `_dash_option_rules` (S32 is batch 11's rules editor, DECISIONS A15: it adds its own `scale`/`fxsize`/`fysize` tokens, S33's `lwidth` bound change and S34's `lalign`/`mlalign` enum tokens as disjoint tokens; S33 and S34 read them and do not edit the table) and dash.ado's graph parser only. Neither S33 nor S34 edits `_dash_fit_frame`/`_dash_figure_size` (no such functions exist): S32's renderer edits are `_dash_layout_cell`, `_dash_figure_aspect`'s siblings and `_make_figure_body`'s tail.

## Evidence

All anchors at `6370ca4`.

### dash.ado

```
944        XSIZe(string)             YSIZe(string)             FXSIZE(string) ///
945        FYSIZE(string)            SCALE(string)             TEXT(string asis) ///
952        XOVERHANGs                YOVERHANGs                REPLACE ///
1019    if `: length local fxsize' local _dash_pending `"`_dash_pending' fxsize"'
1020    if `: length local fysize' local _dash_pending `"`_dash_pending' fysize"'
1027    if `: length local scale' local _dash_pending `"`_dash_pending' scale"'
1039    if `: length local xoverhangs' local _dash_pending `"`_dash_pending' xoverhangs"'
1042    if `: length local yoverhangs' local _dash_pending `"`_dash_pending' yoverhangs"'
3047        xsize=style,1,100  ysize=style,1,100  aspectratio=num,0  hover=varlist  by=byvarlist ///
6823    local _g_unique "saving scheme aspectratio xsize ysize scale fxsize fysize nodraw play"
```
`ASPectratio(string)` (:939); `sreturn local aspectratio` (:1062), `g_aspectratio` (:1548); the seven key lists hold `aspectratio ... xsize ysize fxsize fysize scale` (:7340-7343). `_dash_validate_value`'s `num` branch (:3166-3190) builds "a number of at least 0" for the whole value.

### dash_render.py

```python
21363     if xs is not None or ys is not None:
21364         w = xs if xs is not None else scheme_x
21365         h = ys if ys is not None else scheme_y
21366         if w and h:
21367             return float(w) / float(h)
21369     raw_ar = str(graph_opts.get("aspectratio", "") or "").strip()
21376         elif ar is not None:
21377             return 1.0 / float(ar)
43721         if aspect_ratio is not None:
43722             fig_kwargs["aspect_ratio"] = aspect_ratio
```
`_make_figure_body` calls `aspect_ratio = self._resolve_aspect_ratio(graph_opts)` (:43691) which calls `_dash_figure_aspect(graph_opts, sx, sy)` (:43549); the template's `_dash_figure_for` has `_ar = _dash_figure_aspect(go, _SCHEME_GRAPHSIZE_X, _SCHEME_GRAPHSIZE_Y)` and `_fig_kw['aspect_ratio'] = _ar` (:49393-49397). The by() array rescales `aspect_ratio` by `nr/nc` (:35947-35950). `_MAX_FIGURE_HEIGHT = 560`, `_MIN_FIGURE_HEIGHT = 160` (:466-467). `_dash_layout_cell(name, figures, facet_map, kpi_divs, gopts_of)` (:35899) builds each grid cell and reads `gopts_of(name)` (the graph's options) for `by`. `OptionTranslator.resolve_size` (:7098-7140): `*#` multiplies `default_pt`; a number is 2.88 pt; `pt`/`in`/`cm` converted at `ref_in`; names from the kind's ladder; `size_ref_of(fig)` (:7221-7231) reads `fig._dash_size_ref_in`, stamped at :11450 from `self.size_ref_in`. Bokeh 3.9.0 `figure` properties include `frame_width`, `frame_height`, `aspect_ratio`, `min_border_*`, `inner_width`, `inner_height`, `outer_width`, `outer_height` (probed for this file); `Row` is a `FlexBox`.

### Stata's rule

`scale(#)` (`region_options.sthlp`: "specifies a multiplier that affects the size of all text, markers and line widths in a graph", default 1); `fxsize(#)`/`fysize(#)` (graph combine's `fxsize`: "the graph is # percent of its normal width"); `aspectratio(#[, placement(compassdir)])` (`aspect_option.sthlp`: ratio of the plot region's height to width; `placement()` places the plot region within the available space when the ratio leaves slack); `xoverhangs`/`yoverhangs` (`advanced_options.sthlp`: the graph region is widened so the first/last tick labels do not run off). Measured values come from the fixture (U32), never from this paragraph.

### Fixtures on disk

`test/fixtures/size_units_truth.json` (scripts/extract_size_units_truth.do; WP-30 P1.12a: the 2.88-pt unit and the reference) and `test/fixtures/geometry_truth.json` are read, not rewritten.

### Tests that pin today's behaviour (flip, never delete)

- test_graph_options.py::TestAspectRatio (:152-187): `test_aspectratio_is_inverted_for_bokeh` stays green (no sizes -> figure ratio `1/1.5`); `test_aspectratio_invalid_ignored` stays; a new sibling pins the frame rule.
- test_geometry.py::TestAspectRatio (:216-262) and ::TestExplicitSize (:121): any node asserting `aspectratio()` is dropped when `xsize/ysize` are given flips.
- test_unsupported_report_is_true.py: `"fxsize": ("50", "80", "scatter")` (:114), `"scale": ("1.5", "0.5", "scatter")` (:141), `"xoverhangs": ("xoverhangs", "", "scatter")` (:158), `fysize`/`yoverhangs`; counts :240-262.
- test_option_validation.cscript / test_help_claims_*.cscript cases pinning `aspectratio(0.5, placement(e))` as refused "not a positive number" flip in the area script.

## User stories

- US-32.1 As a Stata analyst, I want `scale(1.5)` to enlarge every text, marker and line by half, as in twoway, so a dashboard for a projector reads well.
- US-32.2 As a Stata analyst, I want `aspectratio(1)` to make the plot region square, and `aspectratio(1, placement(e))` to be accepted and honoured, even with `xsize()`/`ysize()`.
- US-32.3 As a Stata analyst, I want `fysize(50)` to halve a graph's height and `fxsize(60)` to narrow it beside a full-width graph.
- US-32.4 As a Stata analyst, I want `xoverhangs` accepted silently with no label clipped.

## Business requirements

- BR-32.1 `scale(#)` multiplies every drawn size by `#` in both modes and holds across filter moves; `#` must be positive, else twoway's refusal words.
- BR-32.2 `fysize(#)` and `fxsize(#)` change the figure's height and row share as described; 1-100 (twoway's bounds measured, U32-6).
- BR-32.3 `aspectratio(#[, placement()])` shapes the plot region, is accepted with `placement()`, survives `xsize()`/`ysize()`; the figure without sizes keeps `1/#` as its own ratio.
- BR-32.4 `xoverhangs`/`yoverhangs` are honoured as the fixture dictates and printed about by nothing.
- BR-32.5 The size reference rule is documented and pinned (E11).

## Technical requirements

- TR-32.1 **dash.ado.** Delete the five pending lines in both blocks. After `syntax` in `_dash_parse_graph_opts` (and the plot parser's graph part): `if `: length local aspectratio' { _dash_aspect_split `"`macval(aspectratio)'"' ; local aspectratio `"`s(num)'"' ; local aspectplacement `"`s(place)'"' }` where new `program define _dash_aspect_split, sclass` (`version 19`; after `_dash_parse_graph_opts`'s helpers) does `gettoken num rest : 0, parse(",")`, `syntax [, PLACEment(string)]` on the rest (anything else -> twoway's words from the fixture `aspect_bad_sub`, r(198)), canonicalises `placement` through `mata: st_local("_pl", _dash_at_place(st_local("placement")))` (an unknown compass -> the fixture's `aspect_bad_place` words), returns `s(num)` and `s(place)`. Declare the new graph key `aspectplacement`: add it to the seven key lists after `aspectratio`, `sreturn local aspectplacement` after :1062 (and `g_` after :1548), `_g_unique` (:6823) gains `aspectplacement`. Rules (:3047): keep `aspectratio=num,0`; add `scale=num,0  fxsize=num,0,100  fysize=num,0,100` on the same continuation (bounds from the fixture U32-6; if twoway accepts 0 or >100, the bounds follow the fixture). **Batch-11 rules edits ridden by S32 (A15):** on the same `_dash_option_rules` edit add S34's two plot-option enum tokens `lalign=enum,inside,outside,center  mlalign=enum,inside,outside,center` (the value set S34's TR-34.1 names; read S34's section text at the cut for the exact words) and apply S33's `lwidth` bound change exactly as S33's TR-33.10 states it (a one-token bound value; if S33's fixture does not call for it, no change). S33 and S34 read these tokens and do not edit the table. `_dash_require_mata` unchanged (no new Mata); test/program_coverage_map.py gains `"_dash_aspect_split": "test_wp31_truth.cscript:U32-5"`.
- TR-32.2 **`_dash_apply_scale(fig, factor)`** (D-32.a) placed directly after `_dash_figure_aspect` (:21378); `factor = _stat_option_float(graph_opts, "scale", None, "graph", lo=0.0)`; `None`/`1.0` -> return; guard `fig._dash_scaled`; walk `fig.select(Axis)`, `fig.select(Grid)`, `fig.center + fig.above + fig.below + fig.left + fig.right` for `Title`/`Label`/`LabelSet`/`Legend`/`Span`/`Arrow`, and `fig.renderers` for glyph specs (`r.glyph`, `r.nonselection_glyph`, `r.muted_glyph`, `r.hover_glyph` when models); `fig._dash_scale = factor`. Imports inside. Called as the last statement before `return fig` in `_make_figure_body` (after `_dash_apply_axis_options`, :43834 region) and as a template string line after the `_dash_apply_axis_options(fig, go, ...)` line in `_dash_figure_for` (:49483 region): `"        _dash_apply_scale(fig, _stat_option_float(go, 'scale', None, 'graph', lo=0.0))",`. S32 is batch 11's `_make_figure_body` and `_generate_app_source` editor (R12; one line each).
- TR-32.3 **Size columns after a move.** The saved renderer's derived size-column writers (`__dash_msize` family; grep `__dash_msize` in dash_render.py and `_FILTER_JS`) multiply by `fig._dash_scale` where they build the column in Python; the JS rebuild reads the factor from a `scale` argument the filter callback gets (`_build_filter_widgets` passes `dash_scale=<factor>` in `args`; S32 is not batch 11's `_build_filter_widgets` editor -- index: none listed -- so this one argument is S32's edit, recorded for the merger). If no size column exists at the batch-11 base (S20 landed in batch 7: check `grep -c "__dash_msize" dash_render.py`), this item is a no-op and the test asserts the glyph's constant size only.
- TR-32.4 **fxsize/fysize** in `_dash_layout_cell` (:35899): `go = gopts_of(name)`; `fy = _stat_option_float(go, "fysize", None, "graph", lo=0.0, hi=100.0)`; `fx = ... "fxsize" ...`; apply D-32.b to each figure of the cell before the cell is built; `fig.styles` is a dict property (`UIElement.styles`).
- TR-32.5 **aspectratio** (D-32.c, A16): new `_dash_frame_aspect(graph_opts) -> float | None` after `_dash_figure_aspect` (the number through `_stat_option_float(..., lo=0.0)`, > 0); new `_dash_frame_sizes(fig, ar, placement, width, height) -> None` after it: computes the border estimate (`fig.min_border_<side>` if not None else `fig.min_border`, plus the axis/title panel estimate from `_dash_scheme_chrome` (:28217)), the largest frame of ratio `ar` inside the remaining box, sets `fig.frame_width`/`fig.frame_height` (ints) and the `min_border_*` of the slack sides from `placement` (`c` default). Called in `_make_figure_body` after the figure is made (after :43725's figure call) and in the template after `_fig_kw['aspect_ratio'] = _ar` (:49397), **only when `xsize` or `ysize` is given** (`width`/`height` are the px the figure was given); without sizes nothing is called and `_dash_figure_aspect` keeps giving `1/ar`. `_dash_figure_aspect` is unchanged (the figure's own ratio: sizes first, else `1/ar`). `placement` is `graph_opts.get("aspectplacement")`. No `CustomJS`, no `_DASH_ASPECT_JS`, no `_dash_aspect_callback`.
- TR-32.6 **Overhangs** (D-32.d): `_dash_overhangs(fig, graph_opts)` after `_dash_frame_aspect`: reads `xoverhangs`/`yoverhangs`; per the fixture either returns (no-op; the function exists so the tests and the help have one name) or ADDS the measured overhang to `min_border_*` (`fig.min_border_left = (fig.min_border_left if fig.min_border_left is not None else fig.min_border) + px`; `+=`, never an assignment, so S33's `outergap` `+=` and D-32.c's placement borders are kept). Called beside `_dash_apply_scale` in both modes (last).
- TR-32.7 **Copy lists (R2).** No new constant. Functions: the tuple at :47452 holds bare identifiers (`_dash_graph_color, _dash_figure_aspect, _fit_grid,`), so add `_dash_apply_scale, _dash_frame_aspect, _dash_frame_sizes, _dash_overhangs,` (bare names) directly after `_dash_figure_aspect,`. function_test_map.py entries for the four and for `_dash_aspect_split` in program_coverage_map.py.
- TR-32.8 **Help (R3).** `{marker geometry}` (dash.sthlp:4275-4328) is rewritten: precedence (xsize/ysize for the figure; aspectratio for the plot region with placement; scheme graphsize), `scale()`, `fxsize()`/`fysize()` with the row-share rule and the alone-in-a-row difference, overhangs' measured outcome, the reference rule (E11; relative sizes are 2.88 pt per unit at the scheme's reference, moved by xsize/ysize as measured). Delete the Unsupported paragraphs "Sizing for graph combine, and scale()" (:5006-5014) and "Room for long end labels" (:5064-5067). TWOWAY_COVERAGE_AUDIT.md:142 gains `[WP-31 D5: corrected -- scale(), fxsize()/fysize(), aspectratio() on the plot region with placement(), overhangs]`; :169 loses `fxsize`, `fysize`, `scale`, `xoverhangs`, `yoverhangs`.
- TR-32.9 **Classification.** test_unsupported_report_is_true.py: `scale`, `fxsize`, `fysize` to `LIVE_VALUES` (`"scale": ("1.5", "0.5", "scatter")` renders differently by construction); `xoverhangs`/`yoverhangs` to `LIVE_VALUES` if drawn, else to the "accepted no-op" classification the file uses (ALIASES/NOT_IN_FILE are wrong; add `NOOP = {...}` to the subtracted sets with a comment naming the fixture); counts with `# old -> new: D5 ...`; declared graph +1 (`aspectplacement`) with `# 89 -> 90: D5 aspectratio placement key` (after S24's 85 -> 89).

## Boundaries

- Does not edit `OptionTranslator.resolve_size`/`size_ref_of` (E11 is documentation plus a pin), any `_apply_*` applier, `_dash_apply_axis_spec`/`_dash_scale_look` (S33), `_dash_parse_plot_opts`' plot option syntax or the mlabel readers (S34), `_FILTER_JS` beyond reading a `dash_scale` argument if TR-32.3 applies, `_dash_refinish_axes`/`_DASH_AXIS_FINISH_JS` (S33 is batch 11's R11 editor), legends, titles, axes.
- Does not scale margins between boxes (documented).
- Adds no page JavaScript (A16); `_FILTER_JS` is read only for TR-32.3's `dash_scale` argument.
- Does not edit `_dash_option_rules` beyond the tokens named in TR-32.1 (its own three, S33's `lwidth` bound, S34's two enum tokens).

## Stata truth

Script `scripts/extract_sizing_truth.do` -> `test/fixtures/sizing_truth.json` (R7 form; `sysuse auto`; SVG exports through cert_svg.do; class values from `.u32k`):

| key | command | values |
|---|---|---|
| scale_15 | `scatter mpg weight, scale(1.5) title("T")` vs `scale(1)` | title font-size, tick-label font-size, marker radius, axis stroke-width ratios (expect 1.5 each) |
| scale_bad | `capture noisily twoway scatter mpg weight, scale(0)` and `scale(-1)`, `scale(x)` | `_rc` and words |
| fysize_50 | `scatter mpg weight, fysize(50)` | `.u32k.graphsize` or SVG height ratio vs the default |
| fxsize_50 | `scatter mpg weight, fxsize(50)` | SVG width ratio |
| fx_bad | `fxsize(0)`, `fxsize(150)`, `fxsize(x)` | `_rc` and words (the bounds) |
| ar_1 | `scatter mpg weight, aspectratio(1)` | plot region box w/h from the SVG (expect 1); graph size unchanged |
| ar_sizes | `aspectratio(1) xsize(8) ysize(4)` | plot region w/h (expect 1), graph 8x4; plot region centred |
| ar_place_e | `aspectratio(1) xsize(8) ysize(4) placement(e)` -> `aspectratio(1, placement(e)) xsize(8) ysize(4)` | plot region x (expect right-aligned) |
| aspect_bad_sub | `aspectratio(1, foo)` | `_rc` and words |
| aspect_bad_place | `aspectratio(1, placement(xx))` | `_rc` and words |
| overhang_x | `scatter mpg weight, xlabel(1760 "a very long first label" 4840)` with and without `xoverhangs` | plot region box, graph region box (D-32.d) |
| overhang_y | the y analogue with `yoverhangs` | boxes |
| ref_sizes | `title("T", size(5))` at default, at `xsize(8) ysize(4)`, at `xsize(4) ysize(8)` | title font-size in SVG units and inches (E11's reference rule) |

Run `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s32 $WT/scripts/extract_sizing_truth.do`; `git add -f`. `test_sizing.py::TestTheFixture` names it.

## TDD test stubs

### Regression tests, `test/test_sizing.py` (new, D5) and `test/test_size_reference.py` (new, E11: `TestReference` only, A14); red at `6370ca4` unless marked guard

Helpers: `_figs(mode, go, plots)`; `_sizes(fig)` collects every scaled property of D-32.a into `{(model_id, prop): value}`; fixture at module level; drawing classes parametrized by mode.

- Test: fixture stamped and complete -- `TestTheFixture::*` (guard after 32-01).
- Test: `scale(1.5)` makes every collected size 1.5 x the unscaled figure's (text in pt, Int props rounded), markers and line widths included; `scale(1)` changes nothing; the figure is marked `_dash_scaled` -- `TestScale::test_every_size_scales[mode]`, `::test_one_is_identity[mode]` (red: no change, note printed).
- Test: a second `_dash_apply_scale` call changes nothing (idempotent) -- `::test_idempotent` (red: AttributeError).
- Test: after a saved move (node) and a served move the glyph sizes are still scaled -- `TestScaleHoldsAcrossAMove::test_saved`, `::test_served` (red).
- Test: `scale(0)`, `scale(-1)`, `scale(x)` refused by dash.ado with twoway's words (parser probe through `_dash_serve_spec`) -- `TestScaleBounds::test_refused[case]` (red: accepted and named).
- Test: `fysize(50)` halves `height` (or doubles `aspect_ratio`) within `_MIN_FIGURE_HEIGHT`; `fxsize(50)` sets `styles["flex-grow"] == "0.5"` -- `TestFxFy::test_fysize[mode]`, `::test_fxsize[mode]` (red).
- Test: Chrome: a row of `fxsize(50)` beside a default figure gives host widths 1:2 within 2 px -- `TestFxFyInChrome::test_row_share` (red; uses test_csp_browser.py's harness; skipped only where that harness skips, with the same marker).
- Test: `aspectratio(1)` alone keeps `fig.aspect_ratio == 1.0`, sets no `frame_width`/`frame_height` (both None) and the help names the chrome difference -- `TestAspect::test_alone_keeps_figure_ratio[mode]` (guard for the ratio; red for the help sentence), `TestAspectIsDocumented::test_help_names_the_difference` (red).
- Test: `aspectratio(1) xsize(8) ysize(4)` keeps `aspect_ratio == 2.0` and sets `frame_width == frame_height` (ints) equal to the largest square inside the figure's inner box (`width - bl - br`, `height - bt - bb` from the same estimate the code uses), `js_property_callbacks` unchanged -- `::test_survives_sizes[mode]` (red: no frame sizes).
- Test: `aspectratio(1, placement(e))` is accepted (parser probe) and with sizes `min_border_left > min_border_right` (slack pushed left; `w` the reverse, `n`/`s` the vertical twins, `c` equal within 1 px) -- `::test_placement_accepted[mode]`, `::test_placement_borders[mode-place]` for `place` in `c e w n s ne sw` (red: refused / no borders).
- Test: Chrome (test_csp_browser.py's harness, same skip marker): the saved page with `aspectratio(1) xsize(8) ysize(4)` has a plot-region box with w/h within 0.02 of 1 and the figure host box 2:1 within 2 px -- `TestAspectInChrome::test_frame_is_square` (red).
- Test: `xoverhangs`/`yoverhangs` print nothing and (per fixture) change `min_border_*` as measured or not at all -- `TestOverhangs::test_per_fixture[mode]` (red: note printed).
- Test: E11: `size_ref_of(fig)` under `xsize(8) ysize(4)` equals the fixture's reference rule (`ref_sizes`), the title's pt follows it; `scale(2)` leaves the reference unchanged and doubles the pt -- `TestReference::test_sizes_follow_the_reference[mode]`, `::test_scale_leaves_the_reference[mode]` (red for the second; the first is a guard if WP-30 P1.12a already matches, else red).
- Test: no note for the five options or `placement()` -- `TestSilentWhenHonoured::test_no_note[option]` (red).

### Cases in cscripts

- `test/test_wp31_truth.cscript` block `* ==== S32 D5: Sizing ====`: U32-1 (scale_15 ratios vs dash's), U32-2 (fysize/fxsize ratios vs dash's height/flex), U32-3 (ar_1 without sizes: twoway's plot-region ratio recorded beside dash's figure ratio and the documented difference), U32-4 (ar_sizes/ar_place_e), U32-5 (`aspectratio(1, placement(e))` parsed: `s(num)`/`s(place)`), U32-9 (overhangs per fixture). Block `* ==== S32 E11: Size reference ====`: U32-8 (ref_sizes vs dash's `size_ref_of`).
- `test/test_option_validation.cscript`: U32-6 (`scale(0)`, `fxsize(150)` words equal twoway's), U32-7 (`aspectratio(1, foo)`, `aspectratio(1, placement(xx))` words equal).

### Flips (in place, each with a `Flipped:` line)

- test_geometry.py nodes asserting `aspectratio()` is ignored with sizes; test_unsupported_report_is_true.py entries and counts (TR-32.9); test_option_validation.cscript / test_help_claims_*.cscript cases on `aspectratio(#, placement())` "not a positive number".

### Parity corpus (R8; appended, guards at base)

test_mode_parity.py under `# WP-31 D5/E11 (section 32): sizing`: `CORPUS` cases `"scale(1.5)"`, `"aspectratio(1, placement(e)) xsize(8) ysize(4)"`, `"fysize(50)"`; `MOVE_CORPUS` case `_move_case("scale(1.5) after a dropdown move (WP-31 D5)", _MOVES[0], [plot_for("scatter")], go={"scale": "1.5"})`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| scale() on every size | pytest + U32-1 | sizing_truth.json | yes |
| scale() holds across moves | pytest (node + served) | -- | yes |
| scale/fxsize bounds | cscript U32-6 | live twoway | n/a |
| fysize/fxsize | pytest + Chrome + U32-2 | sizing_truth.json | yes |
| aspectratio frame rule, placement, sizes | pytest + node + U32-3/4/5 | sizing_truth.json | yes |
| aspectratio sub-option refusals | cscript U32-7 | live twoway | n/a |
| overhangs | pytest + U32-9 | sizing_truth.json | yes |
| reference rule (E11) | pytest + U32-8 | sizing_truth.json | yes |
| no new page JavaScript | pytest test_csp.py (guard) | -- | saved |

Acceptance: AC-32.1 every red stub green; AC-32.2 U32-1..U32-9 PASS, no SKIP; AC-32.3 test_csp.py, test_serve_token.py, test_geometry.py, test_by_grid.py green; AC-32.4 two green commits.

## Tasks

**Commit boundary.** 32-01..32-03 form the D5 commit, subject `Draw scale(), fxsize()/fysize(), overhangs and aspectratio() on the plot region with placement() (WP-31 D5)`; 32-04 the E11 commit, subject `Pin and document the size reference rule (WP-31 E11)`; both on `wp31-s32`. Bodies per BRIEF. CHANGELOG: D5 Results `dash scatter mpg weight, scale(1.5): unchanged -> every text, marker and line 1.5 x (WP-31 D5)`; D5 Changed behaviour `aspectratio(#, placement()) is accepted and drawn; it was refused "not a positive number" (WP-31 D5)`; E11 Requirements `relative sizes are Stata units of 2.88 pt at the scheme's reference, moved by xsize()/ysize() as twoway moves it (WP-31 E11)`. No tooling names.

<task type="auto" id="32-01">
  <name>Measure twoway and write failing D5 tests</name>
  <files>scripts/extract_sizing_truth.do, test/fixtures/sizing_truth.json, test/test_sizing.py</files>
  <action><![CDATA[
    Check the cut (`wp31-s32`, batch-11 base sha); `mkdir -p <scratch>/s32`. Create scripts/extract_sizing_truth.do (head from scripts/extract_default_base_truth.do:21-48) with every row of "Stata truth"; run it through `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s32 ...`; `git add -f test/fixtures/sizing_truth.json`. Read `overhang_x`/`overhang_y` and record D-32.d's branch, `fx_bad`/`scale_bad` bounds and `ref_sizes` in the module docstring. Create test/test_sizing.py with exactly the D5 classes of "TDD test stubs" (every class except `TestReference`, which is E11's and goes in its own file in 32-04; one regression test file per row, A14); run `python3 -m pytest test/test_sizing.py -q -n0 -p no:cacheprovider -rf > <scratch>/s32/32-01.log 2>&1`; write `<scratch>/32-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/sizing_truth.json'));print(sorted(d['_meta'])[:4], d['ar_1']['plot_ratio'], d['aspect_bad_place']['rc'])"` prints `['born_date', 'dash_commit', 'extracted', 'source'] 1.0 198` (within 0.02 for the ratio; the rc as measured); `grep -c FAILED <scratch>/s32/32-01.log` is at least 18; no FAILED line names TestTheFixture; `test -s <scratch>/32-01-failure.txt`.]]></verify>
  <done>twoway's scale ratios, fxsize/fysize effects and bounds, plot-region aspect geometry with placement, sub-option refusals, overhang effects and the size reference were recorded in a stamped fixture, and every D5 regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="32-02">
  <name>Parse and draw scale, fx/fysize, aspect, overhangs</name>
  <files>dash.ado, dash_render.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    dash.ado: apply TR-32.1 (five pending lines deleted in both blocks; `_dash_aspect_split` with `version 19`, its calls after both `syntax` lines, `aspectplacement` in the seven key lists, `sreturn`s, `_g_unique`; the three rule tokens on :3047's continuation) and the program_coverage_map.py entry. dash_render.py: TR-32.2 (`_dash_apply_scale` after :21378; the saved call before `return fig`; the template string line after the `_dash_apply_axis_options` line in `_dash_figure_for`), TR-32.3 (per the `__dash_msize` grep), TR-32.4 (`_dash_layout_cell`), TR-32.5 (`_dash_frame_aspect`, `_dash_frame_sizes`, both call sites, sizes given only), TR-32.6 (`_dash_overhangs` per the fixture, `+=`), TR-32.7 (copy lists, bare names; function_test_map.py). Run `python3 -m pytest test/test_sizing.py test/test_graph_options.py test/test_geometry.py test/test_by_grid.py test/test_csp.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "not Chrome" > <scratch>/s32/32-02.log 2>&1`; flip the nodes named in "Flips" in place with the reason (test_geometry.py, test_unsupported_report_is_true.py with TR-32.9).
  ]]></action>
  <verify><![CDATA[`grep -c "_dash_pending' \(scale\|fxsize\|fysize\|xoverhangs\|yoverhangs\)\"" dash.ado` prints 0; `grep -c "program define _dash_aspect_split" dash.ado` prints 1; `python3 -c "import dash_render as d; print(callable(d._dash_apply_scale), callable(d._dash_frame_sizes), hasattr(d, '_DASH_ASPECT_JS'), hasattr(d, '_dash_aspect_callback'))"` prints `True True False False`; `grep -c FAILED <scratch>/s32/32-02.log` prints 0 after the flips.]]></verify>
  <done>Both renderers scaled every size by scale(), honoured fysize()/fxsize() in the layout cell, shaped the plot region by aspectratio() with placement() through frame sizes set in Python when xsize/ysize are given, and treated the overhangs as the fixture dictated; dash.ado parsed aspectratio(#, placement()) and refused bad scale/fx/fy values with twoway's words.</done>
</task>

<task type="auto" id="32-03">
  <name>Certify, document and commit D5</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[
    Append the S32 D5 block (`* ==== S32 D5: Sizing ====`, U32-1..U32-5, U32-9) above the marker line and U32-6/U32-7 to test_option_validation.cscript (`*! U32-6..U32-7`); drivers per BRIEF (`WP31_ONLY=S32`); run both through the slot. Append the parity cases (R8). Apply TR-32.8's D5 half to dash.sthlp (the geometry section; delete the two Unsupported paragraphs) and TWOWAY_COVERAGE_AUDIT.md. Close the D5 BUGS.md entry, rewrite `D5 Tracked` to the Closed form ending `commit pending.` (DECISIONS A11; the merger's step k.3b writes the sha), replace both `<!-- WP-31 D5 -->` markers. Run `python3 -m pytest test/test_sizing.py test/test_help_conformance.py test/test_unsupported_report_is_true.py test/test_tracking_documents.py test/test_mode_parity.py -k "D5 or scale or aspect or Unsupported or tracking" -q -p no:cacheprovider`; `git add -A`; commit with the D5 body; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.
  ]]></action>
  <verify><![CDATA[`grep -c "U32-[1-7] PASS\|U32-9 PASS" <scratch>/s32/*.log` sums to 8 and `grep -c SKIP <scratch>/s32/run_truth.log` prints 0; `grep -c "Sizing for graph combine" dash.sthlp` prints 0 and `grep -c "Room for long end labels" dash.sthlp` prints 0; `grep -c "^- \*\*D5 Tracked:\*\* Closed in WP-31.*commit pending\.$" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 D5)`.]]></verify>
  <done>D5 was certified against twoway, documented, tracked and landed as one green commit on wp31-s32.</done>
</task>

<task type="auto" id="32-04">
  <name>Pin the size reference and commit E11</name>
  <files>test/test_size_reference.py, test/test_wp31_truth.cscript, dash.sthlp</files>
  <action><![CDATA[
    Create test/test_size_reference.py (new; E11's own file, A14) with exactly the `TestReference` class of "TDD test stubs"; run `python3 -m pytest test/test_size_reference.py -q -n0 -p no:cacheprovider -rf > <scratch>/s32/32-04-base.log 2>&1` on the D5 tree and write `<scratch>/32-04-failure.txt` (`test_scale_leaves_the_reference` red at the D5 tree only if 32-02 did not already satisfy it: if every `TestReference` node is green, record that E11 is closed by D5's code and the test is a guard, and say so in the commit body and the BUGS Resolution). Append the S32 E11 block (`* ==== S32 E11: Size reference ====`, U32-8) above the marker line and run it (`WP31_ONLY=S32`). Add the reference paragraph to the geometry section (TR-32.8's E11 half). Close the E11 BUGS.md entry, rewrite `E11 Tracked` to the Closed form ending `commit pending.` (A11), replace `<!-- WP-31 E11 -->` (Requirements). Run `python3 -m pytest test/test_sizing.py test/test_size_reference.py test/test_tracking_documents.py test/test_help_conformance.py -q -p no:cacheprovider`; commit with the E11 body; no tooling names.
  ]]></action>
  <verify><![CDATA[`grep -c "U32-8 PASS" <scratch>/s32/run_truth.log` prints 1; `grep -c "2.88" dash.sthlp` is at least 1; `grep -c "^- \*\*E11 Tracked:\*\* Closed in WP-31.*commit pending\.$" GAPS3.md` prints 1; `git show --stat HEAD | grep -c test_size_reference.py` prints 1; `git log -1 --format=%s` ends `(WP-31 E11)` and `git log -2 --format=%s | tail -1` ends `(WP-31 D5)`.]]></verify>
  <done>The size reference rule was pinned against twoway, documented in the help and landed as the E11 commit.</done>
</task>

## Section completion criteria

- `scale()` multiplies every drawn size in both modes and holds across moves; bad values refused in twoway's words.
- `fysize()`/`fxsize()` change the figure's height and row share; bounds as measured.
- `aspectratio(#[, placement()])` is parsed, shapes the plot region through Python frame sizes when `xsize()`/`ysize()` are given, keeps the figure ratio (documented) without them; `_dash_figure_aspect`'s figure ratio unchanged; no new page JavaScript.
- Overhangs honoured as the fixture dictates; nothing printed for the five options.
- The reference rule pinned and documented; U32-1..U32-9 PASS; flips recorded; help, Unsupported list, audit, BUGS.md, GAPS3 §9 and CHANGELOG updated in two commits.

## Notes

- **Renderer order.** `_dash_apply_scale` and `_dash_overhangs` are the LAST calls on a figure in both modes (after `_dash_apply_axis_options`); S33's appliers run before them, so their sizes are scaled too. The legend is applied in `_rebuild_legend` (saved) AFTER `_make_figure_body` returns: `_dash_apply_scale` must therefore also be called from `_rebuild_legend`'s end for the legend props only when `fig._dash_scale` is set (a second, legend-only pass; the idempotence guard is per model class: `fig._dash_scaled_legend`). The executor confirms the served order (`_dash_apply_legend` inside `_dash_figure_for` before the scale line) and places the legend pass accordingly.
- **Copy lists (R2):** no constant; the four bare names after `_dash_figure_aspect,` in the function tuple (:47452).
- **R12:** S32 is batch 11's `_make_figure_body`, `_generate_app_source`, `_dash_layout_cell` and `_dash_option_rules` editor (one line, one line, one block; the rules tokens of TR-32.1 including S33's `lwidth` bound and S34's `lalign`/`mlalign` enum tokens, A15); S33 and S34 must not touch them -- the merger checks their Boundaries. TR-32.3's `_build_filter_widgets` argument, if needed, is reported to the merger as the one deviation.
- **R6:** `_dash_aspect_split` is a new program (`version 19`, program_coverage_map); the seven key lists gain `aspectplacement` together; `_g_unique` gains it.
- **R1:** two blocks (D5, E11) and two area cases under U32 ids.
- **R3:** S32 owns the geometry section and the two Unsupported paragraphs it removes.
- **R7:** `sizing_truth.json` new.
- **Security (M11):** no page JavaScript is added; `placement()` reaches the renderer as a canonical compass word from `_dash_at_place` and becomes integers in `min_border_*`; test_csp.py stays a guard.
- **python_exec hazard** as in every section.
- **Decisions for the maintainer:** D-32.c is settled by DECISIONS A16 (Python frame sizes with xsize/ysize; the figure ratio without, documented under M17; no callback). D-32.b (CSS `flex-grow` for `fxsize`, kept with its Chrome check; fallback `max_width`, A16) is this file's ruling within M17/M11; ratify before batch 11.

## Addendum (14oct2026, DECISIONS D14): batch 1-4 gaps added to this section

### A3c: aspectratio() takes asp, shorter than twoway's minimum

**Gap.** dash takes `asp()` for aspectratio(); twoway's minimum is longer (found by S08; pinned in `_SHORTER_THAN_TWOWAY`).

**Requirement.** Measure twoway's minimum for aspectratio(); raise dash's declaration to it; flip the pin; a Changed-behaviour line.

**Tests.** test/test_abbreviations.py and a `U32-<k>` case in test/test_abbreviations.cscript. Fits S32 because S32 rewrites aspectratio() in batch 11.

**Process (binding, as for every row).** Task 1 of this row writes the failing tests and saves `<scratch>/32-A3c-failure.txt`; then the fix; then ONE commit with subject ending `(WP-31 A3c)`. The closing task flips the BUGS.md entry "aspectratio() takes asp, shorter than twoway's minimum" to `- [x]` with a Resolution in the BRIEF's closed form ending `Closes GAPS3 A3 (WP-31, A3c).`, deletes the `"A3c":` line from `WP31_OPEN` in test/test_tracking_documents.py, rewrites GAPS3.md's `- **A3c Tracked:**` line to `Closed in WP-31, BUGS.md "aspectratio() takes asp, shorter than twoway's minimum", commit pending.`, and replaces `<!-- WP-31 A3c -->` in place under `### Changed behaviour (may need your do-files changed)` with a line ending `(WP-31, A3c)`. Measure twoway first (an extract script or a live probe in the cscript); where the measurement contradicts this addendum, the measurement wins and the deviation is recorded. Refusal/message cases go to the area cscript under the `U32` prefix; drawing comparisons go to a `* ==== S32 A3c: ... ====` block in test/test_wp31_truth.cscript. dash replaces twoway (DECISIONS D13): never use `dash twoway` in a probe.
