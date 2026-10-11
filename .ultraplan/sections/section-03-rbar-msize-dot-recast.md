# Section 03: rbar mwidth/msize and dot's base() and recast()

> Part of: WP-31 · GAPS3 rows: C2, B5 (base/recast parts only; entry B5a) · Risk: green · Batch: 1 · Depends on: 01 · Blocks: 18 · Tasks: 3, 2 commits · Case-id prefix: U03

## Overview

**What is wrong today.** GAPS3 C2 (GAPS3.md:121): "`rbar ..., msize()` (the bar width twoway then uses with `mwidth`) is written and **silently** unread; `mwidth` is named." Evidence dash_render.py:18512-18650 `map_rbar`. GAPS3 B5 (GAPS3.md:114), the two parts this section owns: "`base()` on dot written to the spec and never read; `recast()` on dot dropped with no note" (evidence dash.ado:2575, `_dash_recast_opt`'s `if "`ptype'" == "dot" exit` at :2582). The dot rows, `dotextend()`, `ndots()` and the `d*` options are S18's (batch 6), which builds on the base this section fixes.

**What twoway does.** research/stata-ground-truth.md §12: `mwidth` switches rbar's viewtype to `rbarm` (`y2xview_parse:77-79`); rbarm draws rectangles of half-width `marker.size.gmval/2` converted to data units by `gbeta/xbeta` (`yxview_rbarm_draw.ado:10-31`), so the bar is as wide as a marker of its `msize()`, in screen terms, whatever the x spacing; with rbarm, `barwidth()` edits `marker(size())` (`y2xview_parse:144-150`); help `twoway_rbar.sthlp:130-152`. Without `mwidth`, twoway factors `msize()` into the marker style and draws no marker: nothing changes, silently. §5: dot's `base()` is pushed as `.base` and "only widens the axis via `register_with_scale`" (`yxview.class:1583-1587`); the dots themselves start from the axis's own base (0 if spanned, else the nearer edge), not from `base()`. `recast()` on dot: `twoway_yxview_parse.class:186,246-247` reads `RECASTas(string)` as `type` on every yxview type, dot included -- what it then draws must be MEASURED (D-03.c).

**After this section** `mwidth` is declared on rbar (and histogram, which parses through rbar) and drawn: the bars become `Rect` glyphs with `width_units="screen"` as wide as a marker of the layer's `msize()` (the scheme's `symbolsize p#` by default), unchanged by x spacing, zoom or a filter move, in both renderers; `barwidth()` beside `mwidth` is read as twoway reads it (the fixture decides); `msize()` without `mwidth` is named once in the note; `_dash_rep_und_tab`'s `mwidth` row is deleted. `base()` on dot widens the y axis as twoway's does and draws nothing else; `recast()` on dot does what the measurement says (drawn, refused or named). Two commits: `(WP-31 C2)` and `(WP-31 B5a)`.

**Test order and commit rule (rule 7, BRIEF).** Row C2: 03-01 writes the extractor (both rows' probes), runs it, writes `test/test_rbar_mwidth.py` and `test/test_dot_base_recast.py` red, saves `<scratch>/03-01-failure.txt`, no commit; 03-02 declares and draws `mwidth`, flips, certifies and commits `(WP-31 C2)`. Row B5a: 03-03 writes nothing new that is test-first beyond 03-01's second file (written against the tree 03-02 leaves: its failures are appended to `<scratch>/03-03-failure.txt` after 03-02's commit), fixes dot, certifies and commits `(WP-31 B5a)`.

### Section decisions (binding on the executor)

- **D-03.a `mwidth` is drawn as a screen-unit Rect.** `map_rbar` with `mwidth` draws `fig.rect(x=xvar, y="__dash_rbar_mid", height="__dash_rbar_h", width=<px>, width_units="screen", height_units="data", ...)` where the two columns are `(y1+y2)/2` and `|y2-y1|` of the layer's own source and `<px>` is `_apply_marker_opts`'s pixel size for `msize()` (default `self.scheme.default_marker_size(color_idx)`). Bokeh's `VBar` has no screen-unit width; `Rect` does (`width_units` enum `screen|data`, Bokeh 3.8). A value width, never a field: the same on the empty path.
- **D-03.b `msize()` without `mwidth` is named.** twoway reads it into a marker style that draws nothing; dash names it once (`_dash_fold_typed`, new list `_ms_named "rbar"`), DISCOVERY Q36's "options still not drawn are named". `mwidth` itself is silent once drawn.
- **D-03.c dot `recast()` branches on the measurement.** `scripts/extract_rbar_dot_truth.do` runs `capture noisily twoway dot mpg weight, recast(line)` and `recast(scatter)`, recording rc, the message line and the SVG's `<path>` count and `<circle>` count against `twoway dot mpg weight` and `twoway line mpg weight`. (i) rc 0 and the SVG is the target's (line: one path, no dot rows) -> delete the `dot` exit in `_dash_recast_opt` so dot takes the yx recast path; (ii) rc 198 -> refuse with the measured line and code in `_dash_recast_opt`'s dot branch; (iii) rc 0 and the SVG is still dot's -> name `recast()` on dot in the note (`_dash_fold_typed`). The executor writes the branch the fixture selects and records the other two as not taken in the test's docstring.
- **D-03.d dot `base()` widens the axis only.** `map_dot` reads `options["base"]` through `_stat_option_float(options, "base", None, "dot")` and, when finite, tags its renderer `r._dash_axis_include = {"y": base}` so `_dash_axis_hull`/`_dash_layer_extent` (dash_render.py:33125, :32157) include the value in the y extent exactly as an explicit `base()` of bar reaches the hull at `6370ca4` (the executor reads how `map_bar`'s `base_val` reaches `_dash_layer_extent` -- grep `base` in :32157-32270 -- and uses the same hook; if that hook is the glyph's `bottom`, dot adds an invisible zero-size `Scatter` at (x, base) is NOT acceptable: use the hull tag the finishers read). The dots' own geometry is S18's.
- **D-03.e Both rows, one extractor.** One `scripts/extract_rbar_dot_truth.do` and one fixture `test/fixtures/rbar_dot_truth.json` serve C2 and B5a; the fixture is committed in C2's commit and named by both test files.

## Risk: [green] -- one new glyph form on an opt-in path; dot changes only its axis and recast

**Why.** `mwidth` is opt-in; without it rbar is unchanged. dot's drawing is untouched (S18's); only the axis extent and the recast route move.

**Risk factors.** 1. A `Rect` is not a `VBar`: tests that read `glyph.width`/`VBar` for rbar (test_bar_range_geometry.py, test_axis_extents.py `TestBars`) must not see the mwidth path unless they ask for it. 2. The hull reads glyph extents by type; a `Rect` with screen width needs no x half-width added (the hull's x extent for a Rect in screen units is the centre). 3. Batch partners S02 and S04 touch the `syntax` block and the counts. 4. `histogram ..., mwidth`: parses through rbar in twoway; dash's histogram path is `map_histogram` -> bars; the fixture measures it; if rc 0 and drawn, dash names it on histogram (residual to S12, distribution options) rather than drawing it there.

**Mitigation.** 1. The mwidth path is taken only when `options.get("mwidth")` is set; `test_without_mwidth_nothing_changes` pins VBar. 2. `test_axis_extents.py` gains one guard case (rbar mwidth extent == y1..y2 and the x centres). 3. Declarations appended at the end of the `syntax` block; counts 199 -> 200 after S02 (merge order 04, 02, 03). 4. D-03.b's naming list covers histogram's `mwidth` as named.

## Dependencies

- **Depends on: 01.** BUGS entries "C2" and "B5a", GAPS3 lines, CHANGELOG markers, `S03` truth block.
- **Blocks: 18** (dot rows, batch 6): S18 draws the dot rows from the axis base this section leaves correct and must not re-read `base()` for the rows (twoway does not).
- **Parallel batch: 1**, merge order 04, 02, 03. Can run with S04 (`_dash_option_rules`, `_dash_validate_opts`) and S02 (pc mappers): none edits `map_rbar`, `map_dot`, `_dash_recast_opt` or `_dash_axis_hull`. S03 adds no rule token.

## Evidence

Anchors at `6370ca4`.

### map_rbar never reads msize

dash_render.py `map_rbar` (def :18512): the width is `bar_width = 1.0` or `barwidth`/`width` through `_stat_option_float` (:18540-18551) then `self._bar_extent(xvar, source.data[xvar], bar_width, fig=fig, options=options)` (:18552-18554, WP-30 P1.17a); the glyph is a `VBar`; `_apply_fill_opts` and `_apply_line_opts(r, options, role="aline")` (:18645-18648); no `options["msize"]`, no `mwidth`. dash.ado declares `MSIze(string asis)` (:1168) for every type; `mwidth` is undeclared: `_dash_rep_und_tab` row `("mwidth", "mwidth", "mw", "0", "histogram rbar", "0", "")` (dash_parse.mata:6277) so the generic note names it. `dash rbar yl yh weight, msize(large)` is rc 0 with no note (the spec carries `"msize":"large"`).

### map_dot

dash_render.py :18910-18937: `return self.map_scatter(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)`. `base` reaches the spec (`_dash_plot_opts_to_json` key list :4443) and `map_scatter` ignores it. test_glyphs.py `TestMapDot` (:293-320) pins a Scatter renderer (unchanged by this section).

### _dash_recast_opt

dash.ado :2575-2635; :2582 `if "`ptype'" == "dot" exit` -- recast on dot returns before any target is set, with no note (GAPS3 B5 "dropped with no note"). The derived route for the yx types is :2590-2634 (`_rc_class yxtype`, spellings `_sp_yx`, `sreturn local _recast_target`).

### The hull

`_dash_layer_extent(renderers, range_attr, name, kind=None, role="data")` (:32157) and `_dash_axis_hull(fig, e)` (:33125) compute each axis's extent from the drawn glyphs; `_dash_finish_auto_bases(fig)` (:32115) is the bar/spike/dropline/area base (WP-30 P1.17b). How an explicit `base()` of bar enters the extent at `6370ca4` is read by 03-03 (D-03.d).

### Fixtures on disk

`test/fixtures/bar_geometry_truth.json` (rbar widths); `test/fixtures/default_base_truth.json` (bar/spike/dropline/area bases and y scales: `.plotregion1.yscale.curmin/curmax`); none for dot.

### Existing tests that pin today's behaviour

| Node | Today | After |
|---|---|---|
| test/test_unsupported_report_is_true.py:725 `== 196` (199 after S02) | -- | 200 with `# 199 -> 200: C2 mwidth declared`; `LIVE_VALUES["mwidth"] = ({"mwidth": "mwidth", "msize": "large"}, {"mwidth": "mwidth", "msize": "tiny"}, "rbar", {})` |
| test/test_glyphs.py::TestMapDot (:293-320) | Scatter renderer | unchanged (guard) |
| test/test_option_validation.cscript (no rbar msize case) | -- | U03-05 added |
| any test asserting `dash rbar ..., msize(x)` logs no note (grep `rbar` + `msize` in test/*.py and *.cscript at 03-01) | no note | note names `msize()`; flipped with the reason |
| test/test_recast*.py / test_help_claims naming `recast()` on dot (grep `dot.*recast\|recast.*dot`) | dropped silently | per D-03.c; flipped |

## User stories

- **US-03.1** As a twoway user, I want `dash rbar yl yh x, mwidth msize(large)` to draw bars as wide as a large marker, as twoway does.
- **US-03.2** As a twoway user, I want `msize()` on rbar without `mwidth` named in the note rather than dropped in silence.
- **US-03.3** As a twoway user, I want `dot ..., base(#)` to widen the axis as in twoway, and `recast()` on dot to behave as twoway's does.

## Business requirements

- **BR-03.1** With `mwidth`, each rbar bar's width in pixels equals the width of a `scatter ..., msize(same)` marker on the same figure (the scheme's `symbolsize p#` by default), in both modes, at any x spacing, before and after a filter move; its vertical extent is y1..y2.
- **BR-03.2** With `mwidth` and `barwidth(#)`, the width follows the fixture's reading of twoway (`barwidth()` edits the marker size).
- **BR-03.3** Without `mwidth`, rbar is drawn exactly as today, and a given `msize()` is named once in the note; `mwidth` itself is never named on rbar.
- **BR-03.4** `dot ..., base(#)` includes `#` in the y axis extent and changes no glyph; `dot` without `base()` is unchanged.
- **BR-03.5** `dot ..., recast(x)` does what twoway does: drawn as x, refused with twoway's line, or named -- per the fixture.
- **BR-03.6** Saved page and served app agree (parity cases).

## Technical requirements

- **TR-03.1 dash.ado declarations.** `syntax` block: add `MWidth ///` before the trailing `*` (:1238; after S02's line when present). `sreturn local mwidth` after `sreturn local msize`. JSON key list (:4441-4458): add `mwidth` after `barwidth base`. `_dash_fold_typed` (:2201-2272): after the `arrow_types` block add
  ```stata
      // WP-31 C2: rbar draws msize() only with mwidth (twoway's rbarm);
      // without it the size reaches a marker style nothing draws, so it is
      // named.  mwidth on histogram is named until section 12.
      mata: st_local("_ft", strofreal(st_global("s(msize)") != "" & st_global("s(mwidth)") == ""))
      if "`ptype'" == "rbar" & `_ft' local named "`named' msize"
      mata: st_local("_ft", strofreal(st_global("s(mwidth)") != ""))
      if "`ptype'" == "histogram" & `_ft' local named "`named' mwidth"
  ```
  `_dash_rep_und_tab`: delete the `mwidth` row (dash_parse.mata:6277); add `mwidth` to `_dash_rep_unique` (:6200). No rule token (a flag).
- **TR-03.2 `map_rbar` mwidth path.** After the `_rb_sel`/copy block (:18537-18540) and before the width block (:18541), insert:
  ```python
          if str(options.get("mwidth", "") or "").strip():
              return self._map_rbar_mwidth(fig, source, y1var, y2var, xvar,
                                           options, color_idx)
  ```
  New method `_map_rbar_mwidth(self, fig, source, y1var, y2var, xvar, options, color_idx)` directly after `map_rbar`: `px` = the pixel size `_apply_marker_opts` gives `msize()` (copy its `resolve_size(..., "msize", ...)` call and conversion verbatim; default `self.scheme.default_marker_size(color_idx)`); when `"barwidth" in options` and the fixture's `mwidth_barwidth.rule` says `marker size`, `px` is instead the marker size `resolve_size(options["barwidth"], "msize", default)` gives; columns `self._RBAR_MID = "__dash_rbar_mid"` = `(y1 + y2) / 2.0` and `self._RBAR_H = "__dash_rbar_h"` = `abs(y2 - y1)` as float64 arrays written into `source.data` (NaN where either is NaN); `r = fig.rect(x=xvar, y=self._RBAR_MID, width=px, width_units="screen", height=self._RBAR_H, height_units="data", source=source, fill_color=<the same _fill_base map_rbar computes>, line_color=<the same>, legend_label=y1var, **self._scheme_alpha_kw(color_idx, "rbar"))`; then the same `_style_restyle`, bfcolor/blcolor, `_apply_fill_opts`, `_apply_line_opts(r, options, role="aline")` sequence as `map_rbar` (:18560-18648) -- factor that sequence into `_rbar_finish(self, r, options, color_idx, _fill_base, _f)` called by both paths so it is written once; `r.tags = ["dash_rbar_mwidth"]`; returns `[r]`. The empty path (`_is_empty`) builds the two empty columns and the same `Rect`.
- **TR-03.3 `map_dot` base.** Replace the one-line body (:18937) with:
  ```python
          rs = self.map_scatter(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)
          # base(): twoway registers it with the y scale and draws the dots
          # from the axis's own base (yxview.class:1583-1587; WP-31 B5a).
          _b = _stat_option_float(options, "base", None, "dot")
          if _b is not None and math.isfinite(_b):
              for r in rs:
                  r._dash_axis_include = {"y": float(_b)}
          return rs
  ```
  and make `_dash_layer_extent` (:32157) widen the y extent by `r._dash_axis_include["y"]` when the attribute exists (one `getattr(r, "_dash_axis_include", None)` read beside the glyph extent; `_dash_layer_extent` is on the copy list already -- grep `"_dash_layer_extent",` in :46822-47270; if it is not, add it after `_dash_reference_lines`, R2). If 03-03's reading of the tree finds an existing hook for bar's explicit base (D-03.d), use that hook instead and record it in the docstring.
- **TR-03.4 `_dash_recast_opt` dot branch (D-03.c).** Replace `if "`ptype'" == "dot" exit` (:2582) with: (i) nothing (the line is deleted; dot is already in `_yx` and `_sp_yx`, so the yx route handles it); or (ii) `if "`ptype'" == "dot" { display as error "<measured line>"; exit <rc> }`; or (iii) `if "`ptype'" == "dot" { sreturn local _pending `"`s(_pending)' recast"'; exit }` (and `recast` stays `PLOT_VALUES`-named on dot in test_unsupported_report_is_true.py). For (i) the renderer's recast path (`_dash_draw_xy_as`, reached by `_dash_add_glyph` for a spec with `recast`) needs no change: dot's `(y, x)` shape is scatter's.
- **TR-03.5 Served copy (R2).** `_map_rbar_mwidth`, `_rbar_finish`, `_RBAR_MID`, `_RBAR_H` are `GlyphMapper` members; `fig.rect` needs no import. `_dash_layer_extent`'s edit travels on its copy-list entry.
- **TR-03.6 Maps.** function_test_map.py under `# WP-31 S03 (C2, B5a)`: `'GlyphMapper._map_rbar_mwidth': 'test/test_rbar_mwidth.py::TestMwidth::test_the_width_is_the_marker_size'`, `'GlyphMapper._rbar_finish': 'test/test_rbar_mwidth.py::TestWithoutMwidth::test_nothing_changes'`. program_coverage_map.py: none new.
- **TR-03.7 Help (R3).** dash.sthlp: the rbar sentence in Plot types (grep `{ul:Bars and range caps.}`, WP-30 S14's paragraph, now S03's for the rbar/mwidth sentence only): add "with mwidth each bar is as wide as a marker of its msize() (the scheme's symbol size by default), in screen units, as twoway's rbar mwidth draws; without mwidth msize() is accepted and named." dot's entry under Plot types: "base() widens the y axis as in twoway and does not move the dots; recast() <per D-03.c>". Unsupported list: `msize()` on rbar sentence ("named without mwidth"), `mwidth` on histogram.
- **TR-03.8 Security.** Sizes through `resolve_size`; the flag tested for presence; no new text sink.

## Boundaries

- Not S03's: the dot rows, `dotextend() ndots() dstyle dlstyle dsymbol dcolor dfcolor dsize dlcolor dlwidth dlalign` (S18); `map_bar`, `_bar_extent`, `barwidth()` without `mwidth` (WP-30 S14's rule stands); histogram's own drawing (S12); `_dash_option_rules` (S04 this batch); the `_apply_*` appliers; `_dash_finish_auto_bases` beyond reading how bar's base enters the extent; the scheme files.

## Stata truth

**New extractor** `scripts/extract_rbar_dot_truth.do` (head form of scripts/extract_default_base_truth.do; `ZR_` globals; twoway only), run as `DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s03 $WT/scripts/extract_rbar_dot_truth.do`, writing `test/fixtures/rbar_dot_truth.json` (`git add -f`). Data `sysuse auto`, `gen yl = mpg - 1`, `gen yh = mpg + 1`; `set scheme s2color`; SVGs read with `scripts/svg_truth.py`:

| Key | Command | Recorded |
|---|---|---|
| `rbar.plain`, `rbar.mwidth`, `rbar.mwidth_<m>` for m in `small large vlarge 2` | `twoway rbar yl yh weight[, mwidth [msize(m)]]` | `.Graph.plotregion1.plot1.style.marker.size.val`, the view type (`.plot1.classname` or `mwidth` flag), SVG rect widths (px), canvas W,H, `ratio = 100*width/min(W,H)` |
| `rbar.msize_only` | `twoway rbar yl yh weight, msize(large)` | rect widths equal `rbar.plain`'s; rc |
| `rbar.mwidth_barwidth` | `twoway rbar yl yh weight, mwidth barwidth(.3)` and `barwidth(3)` | rect widths; `marker.size.val`; `rule` = "marker size" when the width tracks the number as a size, "x units" otherwise |
| `rbar.spacing` | `twoway rbar yl yh turn, mwidth` (closer x) | rect widths equal `rbar.mwidth`'s |
| `histogram.mwidth` | `twoway histogram mpg, mwidth` | rc, message line, rect widths vs `twoway histogram mpg` |
| `dot.base` | `twoway dot mpg weight, base(0)` / `base(50)` / none | `.plotregion1.yscale.curmin/curmax`, `.yaxis1.major.min/max`; dot `<circle>` count and y positions equal the no-base graph's |
| `dot.recast_line`, `dot.recast_scatter` | `capture noisily twoway dot mpg weight, recast(line)` / `recast(scatter)` | rc, message line, SVG `<path>` and `<circle>` counts against `twoway dot mpg weight` and `twoway line mpg weight` |
| `refusals` | `twoway rbar yl yh weight, mwidth mwidth`; `twoway scatter mpg weight, mwidth` | rc and message |

**Truth block** `* ==== S03 C2: rbar mwidth and dot base/recast ====` (S01's header) in `test/test_wp31_truth.cscript`; helpers `_u03_*` above it:
- **U03-01** `dash rbar yl yh weight, mwidth`: the Rect's `width` equals the pixel size dash gives `scatter ..., msize(medium)`'s marker, `width_units == "screen"`, both modes; twoway's `ratio` equals its `marker.size.val` within 1% (fixture guard).
- **U03-02** `mwidth msize(large)` and `mwidth` on `turn`: the width equals dash's large marker; equal at both spacings, both modes.
- **U03-03** `dash rbar yl yh weight, msize(large)` (no mwidth): VBar width 1 as before; the log names `msize()` once.
- **U03-04** `dash dot mpg weight, base(50)`: both modes' y range includes 50 and the Scatter y values equal the no-base graph's; twoway's `curmax >= 50`.
- **U03-05** (area script test_option_validation.cscript) `dash dot mpg weight, recast(line)` rc and line equal twoway's; with rc 0 and branch (i), dash's spec carries `"recast":"line"` and the saved page draws a Line glyph and no dot Scatter.
- **U03-06** (area) `dash rbar yl yh weight, mwidth mwidth` refused as twoway refuses the repeat; `dash scatter mpg weight, mwidth` named/refused as twoway's rc says.

## TDD test stubs

### Regression tests, `test/test_rbar_mwidth.py` (new; red at `6370ca4` unless guard)

- Test: fixture stamped; `rbar.mwidth.ratio` within 1% of `marker.size.val` -- `TestTheFixture::test_meta_is_stamped`, `::test_twoways_width_is_its_msize` (guard after 03-01).
- Test: `map_rbar(..., {"mwidth": "mwidth"})` returns one `Rect` with `width_units == "screen"`, `width ==` the pixel size `map_scatter` gives a default marker, `y` field `__dash_rbar_mid`, `height` field `__dash_rbar_h` -- `TestMwidth::test_the_width_is_the_marker_size`, `::test_the_vertical_extent_is_y1_y2` (red: VBar).
- Test: `msize(small|large|vlarge|2)` scale as `map_scatter`'s -- `::test_msize_scales_the_width[m]` (red).
- Test: the width is equal at x spacing 1 and 5 and after a saved move (node) and a served move -- `::test_the_width_does_not_follow_the_spacing`, `TestTheWidthHoldsAcrossAMove::test_saved`, `::test_served` (red).
- Test: `mwidth barwidth(.3)` follows the fixture's `rule` -- `::test_barwidth_with_mwidth` (red).
- Test: without `mwidth` the glyph is the same VBar as at base with the same width, line and fill -- `TestWithoutMwidth::test_nothing_changes` (guard).
- Test: the empty layer with `mwidth` is a Rect with empty columns -- `::test_an_empty_layer` (red).
- Test: tags `dash_rbar_mwidth` -- `::test_the_tag` (red).

### Regression tests, `test/test_dot_base_recast.py` (new; written in 03-01, red at `6370ca4`)

- Test: `map_dot(..., {"base": "50"})` returns Scatter renderers carrying `_dash_axis_include == {"y": 50.0}` and the saved page's y range (`_dash_layer_extent`) includes 50; without `base()` no attribute -- `TestDotBase::test_the_extent_includes_base`, `::test_no_base_no_tag` (red / guard).
- Test: both modes' y range includes base -- `::test_both_modes[mode]` (red).
- Test: the dots' y values are unchanged by `base()` -- `::test_the_dots_do_not_move` (guard).
- Test: `_dash_recast_opt`'s body has no `"dot" exit` line; dot with `recast(line)` behaves per the fixture branch -- `TestDotRecast::test_the_branch_is_the_fixtures` (red: the exit line exists).

### Cases in cscripts

- `test_wp31_truth.cscript` U03-01..U03-04 (red); `test_option_validation.cscript` U03-05, U03-06 (red).

### Flips

- test_unsupported_report_is_true.py: `LIVE_VALUES["mwidth"]` added; count 199 -> 200 (`# 199 -> 200: C2 mwidth declared`); if `PLOT_VALUES["recast"]` or a `_CONTEXT` names dot, per D-03.c.
- Any node 03-01's grep finds asserting no note for rbar `msize()` or silence for dot `recast()`: flipped with "Flipped (WP-31 C2|B5a): ...".

### Parity corpus (R8; guards)

`test/test_mode_parity.py` under `# WP-31 C2/B5a`: `CORPUS` "rbar mwidth msize(large)", "dot base(50)"; `MOVE_CORPUS` "rbar mwidth, dropdown to Foreign" (`_MOVES[0]`).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| mwidth width == marker size, spacing, msize | pytest `TestMwidth`; U03-01, U03-02 | `rbar.mwidth*`, `rbar.spacing` | yes |
| Moves | pytest `TestTheWidthHoldsAcrossAMove`; MOVE_CORPUS | -- | yes |
| msize without mwidth named | U03-03; test_unsupported_report_is_true.py | `rbar.msize_only` | n/a |
| dot base extent | pytest `TestDotBase`; U03-04 | `dot.base` | yes |
| dot recast | pytest `TestDotRecast`; U03-05 | `dot.recast_*` | yes (branch i) |
| Repeats and foreign type | U03-06 | `refusals` | n/a |

**Acceptance criteria**
- **AC-03.1** `rbar ..., mwidth` draws Rects of screen width equal to the marker size of the same `msize()`, equal at two spacings and after moves, both modes.
- **AC-03.2** Without `mwidth` rbar is byte-identical in its glyph properties to `6370ca4`'s; `msize()` is named once.
- **AC-03.3** `dot ..., base(#)` widens the y extent in both modes and moves no dot.
- **AC-03.4** `dot ..., recast(x)` matches the fixture's branch; the `dot exit` line is gone.
- **AC-03.5** U03-01..U03-06 PASS, no SKIP; the named pytest files 0 failed.

## Tasks

**Commit boundary.** 03-01 and 03-02 form the C2 commit, subject `Draw rbar bars as wide as their msize() with mwidth, as twoway does (WP-31 C2)`; 03-03 the B5a commit, subject `Widen the axis for dot base() and route dot recast() as twoway does (WP-31 B5a)`, both on `wp31-s03` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s03`. Bodies: the saved failure text, the measured defect, what changed where (both renderers), then `Regression:`, `Flipped:`, `Fixture: test/fixtures/rbar_dot_truth.json (scripts/extract_rbar_dot_truth.do)` (C2's body; B5a's cites the same fixture), `BUGS.md: "<title>" (closed)`, `GAPS3: C2 Tracked` / `GAPS3: B5a Tracked`.

<task type="auto" id="03-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_rbar_dot_truth.do, test/test_rbar_mwidth.py, test/test_dot_base_recast.py</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints `wp31-s03`; `mkdir -p <scratch>/s03`. Create scripts/extract_rbar_dot_truth.do by the "Stata truth" table (head from scripts/extract_default_base_truth.do lines 1-60 with ZR_ globals; SVG export per graph; the python block with scripts/svg_truth.py reading rect widths, path and circle counts; `_meta`; `sort_keys=True`; SVGs erased); run it through the slot; `git add -f test/fixtures/rbar_dot_truth.json`. Read `dot.recast_line` and write the D-03.c branch taken to `<scratch>/s03/recast-branch.txt` (i, ii or iii with the rc and line). Create test/test_rbar_mwidth.py and test/test_dot_base_recast.py with the classes of "TDD test stubs" (the recast test asserting the branch in the file). Grep the tests for pins (`grep -ln "rbar.*msize\|msize.*rbar\|dot.*recast\|recast.*dot" test/*.py test/*.cscript`) and list affected nodes in `<scratch>/s03/03-flips.txt`. Run `python3 -m pytest test/test_rbar_mwidth.py test/test_dot_base_recast.py -q -n0 -p no:cacheprovider -rf > <scratch>/s03/03-01.log 2>&1`; write `<scratch>/03-01-failure.txt` (base sha, the failing nodes of test_rbar_mwidth.py with reasons, guards passed) and `<scratch>/03-03-failure.txt` (the failing nodes of test_dot_base_recast.py). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/rbar_dot_truth.json'));print(sorted(d['_meta']), 'rbar' in d, 'dot' in d)"` prints the five meta keys and `True True`; `grep -c FAILED <scratch>/s03/03-01.log` is at least 8; `test -s <scratch>/s03/recast-branch.txt`; `test -s <scratch>/03-01-failure.txt`.]]></verify>
  <done>twoway's rbar mwidth widths, dot base scale and dot recast behaviour were recorded in a stamped fixture, the recast branch was decided from it, and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="03-02">
  <name>Declare and draw mwidth, close C2</name>
  <files>dash.ado, dash_render.py, dash_parse.mata</files>
  <action><![CDATA[
    Make TR-03.1 (dash.ado `MWidth` before `*` after S02's line if present; sreturn; JSON key; `_dash_fold_typed` block; dash_parse.mata `_dash_rep_und_tab` row deleted, `_dash_rep_unique` gains `mwidth`), TR-03.2 and TR-03.5 in dash_render.py (`_map_rbar_mwidth`, `_rbar_finish` factored out of `map_rbar` and used by both paths, the two columns, the tag), TR-03.6's function_test_map.py entries and the test_unsupported_report_is_true.py entry and count (`# 199 -> 200: C2 mwidth declared`; if S02 has not landed on this base, `# 196 -> 197` and tell the merger). Flip the C2 nodes of `<scratch>/s03/03-flips.txt` in place with `Flipped:` lines. Write U03-01..U03-03 in S01's `S03` block of test/test_wp31_truth.cscript (helpers above the header) and U03-06 in test/test_option_validation.cscript (after the last case, before `// Summary`, header lines). Append the C2 parity cases. Run through the driver `WP31_ONLY=S03` the truth script and test_option_validation.cscript; run `python3 -m pytest test/test_rbar_mwidth.py test/test_bar_range_geometry.py test/test_axis_extents.py test/test_glyphs.py test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_help_conformance.py test/test_function_test_map.py test/test_mode_parity.py -k "not B5a" -q -p no:cacheprovider`. Make TR-03.7's rbar help sentences and the Unsupported list's msize/mwidth sentences; TWOWAY_COVERAGE_AUDIT.md row 73: append ` [WP-31 C2: corrected -- mwidth draws the bar as wide as its msize()]`. Close S01's "C2" BUGS.md entry in BRIEF's form (functions GlyphMapper.map_rbar/_map_rbar_mwidth, _dash_fold_typed; both renderers; pinned by test/test_rbar_mwidth.py::TestMwidth::test_the_width_is_the_marker_size, test/test_wp31_truth.cscript U03-01; fixture test/fixtures/rbar_dot_truth.json; Residual, deferred (WP-31): mwidth on histogram is named (section 12)); GAPS3 §9 C2 -> Closed with the sha (write the line, commit, amend GAPS3.md once with the sha); CHANGELOG: replace `<!-- WP-31 C2 -->` under `### Results that change` with `- rbar ..., mwidth draws each bar as wide as a marker of its msize() in screen units (the scheme's symbol size by default), as twoway's rbar mwidth does; dash drew one x unit and ignored msize() in silence. msize() without mwidth is named. (WP-31, C2)` and under `### Fixed in WP-31` with `- rbar mwidth and msize() are drawn in both renderers. (WP-31, C2)`. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Stage the C2 files only (not test/test_dot_base_recast.py; `git add -f` the fixture), check names, write `<scratch>/s03/msg-c2.txt`, grep for `claude|anthropic` (0), commit, re-grep.
  ]]></action>
  <verify><![CDATA[`grep -c "U03-0[1-3] PASS" <scratch>/s03/run_test_wp31_truth.log` prints 3; `grep -c "U03-06 PASS" <scratch>/s03/run_test_option_validation.log` prints 1; `grep -c SKIP` on both logs prints 0; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 C2)`; `grep -c "(WP-31, C2)" CHANGELOG.md` prints 2; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>rbar drew screen-width bars from msize() under mwidth in both renderers, named msize() without it, and C2 was closed in one green commit on wp31-s03.</done>
</task>

<task type="auto" id="03-03">
  <name>Fix dot base and recast, close B5a</name>
  <files>dash.ado, dash_render.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[
    Re-run `python3 -m pytest test/test_dot_base_recast.py -q -n0 -p no:cacheprovider -rf > <scratch>/s03/03-03.log 2>&1` against the tree 03-02 left and refresh `<scratch>/03-03-failure.txt`. Read how `map_bar`'s explicit `base()` reaches the y extent at this tree (`grep -n "base" dash_render.py | sed -n` over :32115-32300 and `_dash_finish_auto_bases`), then make TR-03.3 (`map_dot` tag; `_dash_layer_extent` reads `_dash_axis_include`, or the existing hook if one serves) and TR-03.4's branch from `<scratch>/s03/recast-branch.txt` in `_dash_recast_opt`. Write U03-04 in the `S03` block and U03-05 in test_option_validation.cscript; append the B5a parity case `dot base(50)`. Flip the B5a nodes of `<scratch>/s03/03-flips.txt` (recast on dot) with `Flipped:` lines. Run the two cscripts through the driver and `python3 -m pytest test/test_dot_base_recast.py test/test_glyphs.py test/test_axis_extents.py test/test_recast*.py test/test_unsupported_report_is_true.py test/test_mode_parity.py -k "dot" -q -p no:cacheprovider`. Make TR-03.7's dot help sentences; TWOWAY_COVERAGE_AUDIT.md row 68: append ` [WP-31 B5a: corrected -- base() widens the axis; recast() <drawn|refused|named> as twoway]`. Close S01's "B5a" BUGS.md entry in BRIEF's form (functions GlyphMapper.map_dot, _dash_layer_extent, _dash_recast_opt; pinned by test/test_dot_base_recast.py::TestDotBase::test_the_extent_includes_base, test/test_wp31_truth.cscript U03-04, test/test_option_validation.cscript U03-05; fixture test/fixtures/rbar_dot_truth.json; Residual, deferred (WP-31): the dot rows and the d-options are section 18 (GAPS3 B5 Tracked)); GAPS3 §9 B5a -> Closed with the sha (commit, then amend GAPS3.md once); CHANGELOG: replace `<!-- WP-31 B5a -->` under `### Results that change` with `- dot ..., base(#) widens the y axis to include # as twoway does and no longer sits unread in the spec; recast() on dot is <drawn as the target|refused r(198) "<line>"|named in the note>, as twoway does (it was dropped in silence). (WP-31, B5a)` and under `### Fixed in WP-31` with `- dot's base() and recast() behave as twoway's. (WP-31, B5a)`; if branch (ii), also replace the `### Changed behaviour` marker with `- recast() on dot is refused, r(198), with twoway's line <line>; dash dropped it in silence. (WP-31, B5a)`, else delete that marker line. Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q -n0 -p no:cacheprovider`. Stage the B5a files, write `<scratch>/s03/msg-b5a.txt`, grep (0), commit, re-grep.
  ]]></action>
  <verify><![CDATA[`grep -c "U03-04 PASS" <scratch>/s03/run_test_wp31_truth.log` prints 1 and `grep -c "U03-0[1-4] PASS"` prints 4; `grep -c "U03-05 PASS" <scratch>/s03/run_test_option_validation.log` prints 1; `grep -c '"dot" exit' dash.ado` prints 0; the pytest runs report 0 failed; `git log -1 --format=%s` ends `(WP-31 B5a)`; `grep -c '<!-- WP-31 B5a -->' CHANGELOG.md` prints 0; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>dot's base() widened the axis in both renderers without moving a dot, recast() on dot followed twoway's measured behaviour, and B5a was closed in one green commit on wp31-s03.</done>
</task>

## Section completion criteria

- `rbar ..., mwidth` draws screen-width Rects equal to the marker size, both modes, through moves; without `mwidth` nothing changes and `msize()` is named; `mwidth` row gone from `_dash_rep_und_tab`.
- `dot ..., base(#)` widens the y extent; `recast()` on dot per the fixture; the `dot exit` line gone.
- U03-01..U03-06 PASS; the named pytest files green; flips recorded; two commits `(WP-31 C2)`, `(WP-31 B5a)`; two BUGS entries closed; two GAPS3 lines rewritten; markers replaced.

## Notes

- **Rect, not VBar, only under mwidth.** `test_bar_range_geometry.py` and `test_axis_extents.py::TestBars` read VBar widths; they never pass `mwidth`, so they stay green. The hull reads a `Rect` in screen width as its centre x (no data half-width); check `_dash_layer_extent`'s Rect handling before relying on it (`grep -n "Rect" dash_render.py | sed -n` over :32157-32270).
- **Factor once.** `_rbar_finish` is the fill/line/bfcolor/blcolor sequence of `map_rbar` :18560-18648 moved into one method so the two paths cannot drift; `test_nothing_changes` compares the VBar's properties with a snapshot taken before the refactor (write the snapshot in the test from the base tree's values at 03-01).
- **dot's base is the hull's, not the dots'.** S18 draws the rows from the axis base (0 if spanned, else the nearer edge, research §5); `base()` only enters the extent. Do not make the rows start at `base()`.
- **python_exec hazard**: check `~/.stata19/console/stata19.rc` after each cscript run.
- **Shared files (R1-R13).** R1: the S03 block and two area cases. R2: no module-level name; `_dash_layer_extent` is already copied (verify). R3: the rbar sentence in WP-30 S14's paragraph and dot's entry only. R4: C2's two markers, B5a's two or three. R5: two entries. R6: `MWidth` appended; `_dash_rep_unique` alphabetical; `_dash_fold_typed` gains one block. R7: one fixture for two rows. R8: two CORPUS, one MOVE_CORPUS. R9: flips recorded. R10: 199 -> 200 with comment (after S02). R12: S03 edits no hot function.
- **For S18 (batch 6).** `map_dot` returns `map_scatter`'s renderers with the `_dash_axis_include` tag; S18 adds the dot-row renderers beside them and must keep the tag on the marker renderer.
- **For S12 (batch 4).** `histogram ..., mwidth` is named by `_dash_fold_typed` (TR-03.1); S12 decides whether to draw it.
