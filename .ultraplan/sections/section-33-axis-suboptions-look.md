# Section 33: Axis sub-options and the axis look

> Part of: WP-31 · GAPS3 rows: D6, D7, E6 · Risk: yellow · Batch: 11 · Depends on: 24 · Blocks: -- · Tasks: 4, 3 commits · Case-id prefix: U33

## Overview

**What is wrong today.** GAPS3 D6 (GAPS3.md:156): "Axis sub-options `labgap labstyle tstyle gstyle alternate altgap gmin gmax gextend custom tlstyle tlwidth tlcolor tlpattern glwidth glcolor glpattern labjustification labalignment` named; `##5` read as `#5`; `minmax` over all layers unverified; label forms twoway refuses drawn anyway." Evidence dash_render.py:36969-36976 (`_DASH_AXLABEL_HONOURED`, eighteen names) and :30269 (`_DASH_AXIS_RULE_RE = re.compile(r"\A#{1,2}\s*(\d+)\s*(.*)\Z")`, whose comment says "A double hash is read the same as a single one"). GAPS3 D7 (:157): "Axis-scale look: `fill outergap() extend noextend fextend lstyle atanh logit log1m` named; two `yscale(alt)` toggle back in twoway; `gsize axis_title_gap` unread; `zlabel()/zscale()` look words named." Evidence :31980 (`_DASH_SCALE_LOOK_SUBOPTS`, nine names) and :36922-36945 (`_DASH_AXSCALE_SUBOPT_TABLE`). GAPS3 E6 (:185): "Line-width edges: `*#` multiplies before the 0.3 pt floor; 10,000-unit bound; `tlwidth()/glwidth()` named not drawn." Evidence :7161 (`line_px`), :7180 (the floor), :7245 (`translate_lwidth`'s `default_pt = d * 0.75`, where *d* is a pixel width a site already floored).

Every one of these sub-options reaches `_dash_parse_axis_spec` (:30272) or `_dash_scale_look` (:38584) through twoway's own tables, is resolved to its full name, and is then put on the `unsupported` list and printed once by `_dash_report_suboptions` (:36777) as "dash: xlabel() sub-option(s) not implemented and ignored: labgap(small) tlwidth(thick)". The user sees a note where twoway draws.

**After this section**, in both renderers, `xlabel()/ylabel()/xtick()/ytick()` draw `labgap()`, `labjustification()`, `labalignment()`, `alternate`, `altgap()`, `tlwidth()`, `tlcolor()`, `tlpattern()`, `glwidth()`, `glcolor()`, `glpattern()`, `nogmin`/`nogmax` (`gmin`/`gmax` are Bokeh's default) and, as measured, `gextend`/`nogextend` and `custom`; `##N` on a label or tick option does what twoway does with it (measured: the rule is for minor sets only); `minmax` ticks the extremes of every layer on the axis; the label forms twoway refuses are refused r(198) in twoway's words. `xscale()/yscale()` draw `outergap()`, `noextend`/`extend`/`fextend` and `lstyle()`; `fill`/`fillspace` is what twoway does with it (measured); a second `alt` toggles the side back; the scheme's `gsize axis_title_gap` is the default title gap; the look words of `zlabel()`/`zscale()` are as silent as twoway is on a non-contour graph (measured). `*#` on a line width multiplies the unfloored default and the 0.3 pt floor applies after; the 10,000-unit bound follows twoway (measured); `tlwidth()`/`glwidth()` go through `translate_lwidth` with the floor rule. Once an option is drawn nothing is printed for it (DISCOVERY Q36). `labstyle() tstyle() gstyle() tlstyle() glstyle()` (style *names* whose files dash does not read) stay named, documented, and are the recorded residual (D-33.g).

**Why these rows share this section.** All three edit the two axis appliers and their tables (`_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_apply_tick_look`, `_dash_scale_look`, `_dash_apply_scale_look`) and `OptionTranslator.translate_lwidth`, which the tick and grid widths call; the index names S33 as batch 11's one editor of the axis label/scale appliers and of the axis finishers (R11).

**Test order and commit rule (rule 7, M6).** Three commits, one per row, in the order D6, D7, E6: `(WP-31 D6)`, `(WP-31 D7)`, `(WP-31 E6)`. 33-01 writes the extractor, runs it, writes the three regression test files (one per row, A14) and ONLY the D6 truth block (`* ==== S33 D6: Axis label, tick and grid sub-options ====`, U33-01..U33-04), runs them against the unmodified tree and saves `<scratch>/33-01-failure.txt`; it never commits. 33-02 draws D6 and commits it with only D6's test file and the D6 block; 33-03 appends the D7 block (`* ==== S33 D7: Axis-scale look ====`, U33-05/U33-06) and commits D7; 33-04 appends the E6 block (`* ==== S33 E6: Line-width edges ====`, U33-08) and commits E6. No test-only commit; no red commit: each row's commit stages its own test file and its own cscript block (one truth block per GAPS3 row, DECISIONS A14), so no commit stages red cases of a later row.

### Section decisions (this file; binding on the executor)

- **D-33.a `alternate` is two axes.** Bokeh has no alternating label offset. `alternate` on `xlabel()`/`ylabel()` keeps the axis's own ticker and gives it a `CustomJSTickFormatter` that returns the base formatter's text for even-indexed ticks and `""` for odd ones, and adds a twin `LinearAxis` on the same side (`fig.add_layout(twin, side)`) with the same `ticker`, the complementary formatter, `axis_line_color=None`, `major_tick_in=major_tick_out=0`, `minor_tick_in=minor_tick_out=0`, `axis_label=None`, `major_label_standoff` set so the twin's label row sits `altgap()` (default: the label font size in px, twoway's default gap of one label height) below the first row. **Measured first (33-02, before coding):** Bokeh lays the twin out in its own side panel OUTSIDE the first axis's panel, which already spans the first axis's labels, so a standoff of `first standoff + gap` would put the second row about two label heights below the first; 33-02 therefore exports both modes to PNG/SVG once, measures the two label rows' y delta against the fixture's `alternate.default`, and sets the twin's standoff to `max(0, gap - first_panel_height)` where the first panel's height is the first axis's `major_label_standoff + font_px + major_tick_out`; the measured rule and its residual difference (if any) go in the help under M17. Bokeh stacks the twin outside the first, which is the two-row look twoway draws. The formatter code is the module constant `_DASH_ALT_LABEL_JS` (constant text; the parity travels in `args`), of the form `if (index % 2 !== parity) return ""; return base.doFormat(ticks, {loc: 0})[index];` -- BokehJS passes `index` and `ticks` as formatter arguments (bokeh.js:36566 `new Function("tick","index","ticks",...)`), and formatting the whole tick list keeps `BasicTickFormatter`'s precision choice, which is made from the full list -- with `args={"parity": 0|1, "base": <the axis's formatter before the swap>}`; it never reads user text. The twin is tagged `dash_alt_axis` so `_dash_finish_count_ticks`, `_dash_by_scale_panel` and S35's secondary-axis code skip it (`_dash_primary_axes` already filters by `*_range_name`; the twin keeps the primary range name, so it is tagged and the finishers test the tag).
- **D-33.b `gmin`/`gmax` are no-ops; `nogmin`/`nogmax` drop the end grid lines.** Bokeh draws a grid line at every tick including one at the range's end, which is twoway's `gmin gmax`. `nogmin` (`nogmax`) installs on the Grid a `CustomJSTicker` whose `major_code` is `_DASH_GRID_NOEND_JS`: the base ticker's majors less any within `1e-9 * (end - start)` of `cb_data.start` (`cb_data.end`), under the existing `_DASH_TICK_*_JS` pattern (positions never travel in code). Measured in 33-01 (truth table `grid_ends`); if twoway's default already drops the end lines, the rule is inverted in `_dash_apply_axis_spec` (default `nogmin nogmax`, `gmin`/`gmax` restore) and the test fixture decides -- the executor follows the fixture, not this sentence.
- **D-33.c `##N` on a label or tick option follows the measurement.** stata-ground-truth.md §8: "##N ignored, only allowed for minor ticks" (tickset_g.class:991) when applied to a major set. 33-01 measures `ylabel(##5)` (tick count and any log line). If twoway draws the default ticks and prints a line, dash's `_dash_parse_axis_spec` sets `mode="default"` for a `##N` head and `out["double_hash"] = N`, and `_dash_apply_axis_options` prints twoway's line verbatim through `_dash_warn_once` (one copy per graph); if twoway draws `#N`, today's reading stays and only the comment at :30269 changes. S24 (batch 8) owns `##N` on `xmlabel()/xmtick()` and measures `##N` on `xlabel()/xtick()` in its U24-5 fixture (S24 D-24.d): **33-01 re-reads S24's U24-5 fixture at the batch-11 base before writing** -- if S24 found twoway refuses the form and added the dash.ado refusal, D-33.c becomes a guard (the refusal test only) and no renderer branch is written; if S24 found twoway draws the default with a printed line, S33 owns the renderer rule above. S33 owns the label/tick side only and must not touch S24's minor-set branch.
- **D-33.d `minmax` reads every layer.** New helper `_dash_axis_layer_values(frame, plots, letter, date_vars)` returns one float Series of every coordinate column the graph's layers draw on axis *letter* (x: each plot's `xvar`; y: each plot's `yvar`, `yvars`, and range bounds `lo`/`hi` -- the keys `_dash_extract_vars` and `_DASH_PLOT_VAR_KEYS` already enumerate), dates in Stata units through `_dash_date_units` when the axis has no date kind. `_dash_apply_axis_options` passes it as `values` when `spec["mode"] == "minmax"` and *plots* is given; a direct caller without *plots* keeps today's one-variable column.
- **D-33.e Refused label forms are measured, then refused in Mata.** 33-01 probes the candidate forms `ylabel("a")`, `ylabel(1 "a" "b")`, `ylabel(none 1 2)`, `ylabel(minmax 1)`, `ylabel(#3 #4)`, `ylabel(1(1))`, `ylabel(,)` and records rc and the first error line. New Mata `_dash_axlabel_refusal(text)` (dash_parse.mata, after `_dash_layout_refusal`'s section, header index entry, `_needed` list) returns "" or twoway's line for exactly the forms whose rc is not 0; dash.ado `_dash_validate_opts` calls it for `xlabel ylabel xtick ytick` after `_dash_subopt_check zlabel` (:6991) and exits with twoway's rc through `_dash_say("err", ...)`. Forms twoway accepts are not touched.
- **D-33.f Two `alt` toggle.** `_dash_scale_look` counts `alternate` tokens across the merged copies (`_dash_rep_merge` joins copies with ", "; the tokens survive); `alternate` is true when the count is odd. Measured in 33-01 (`scale_alt2`); if twoway keeps the alternate side on two copies, the rule is "any", and the test flips to that.
- **D-33.g Style names stay named.** `labstyle() tstyle() gstyle() tlstyle() glstyle()` name Stata style files (`textstyle-*.style`, `tickstyle-*.style`, `gridstyle-*.style`, `linestyle-*.style`) that dash does not read; S44 (batch 15, style-file resolver) is the owner of reading them. They stay in `unsupported`, the help names them, and the D6 BUGS.md Resolution records them as the residual with a GAPS3 "Partly closed" line. Because S01's tracking reader requires a Partly line to name an OPEN entry, 33-02 opens the residual entry `D6b` at the end of BUGS.md in BRIEF's open form (`- [ ] Title: Axis style names labstyle() tstyle() gstyle() tlstyle() glstyle() are named, not read`; `Suggested fix: WP-31 section 44 (style-file resolver): textstyle/tickstyle/gridstyle files`; `Graded S3 (WP-31): a style name falls to the scheme default; the picture differs only when a non-default style file is named`), and the D6 Partly line names it (`open: the five style names (BUGS.md "Axis style names ... are named, not read")`). Cross-file: S44's D-44c must add `textstyle`, `tickstyle`, `gridstyle` and a step closing D6b, or S61 files D6b under M12 (DECISIONS/REVIEW-3 R3-05; recorded for the merger).
- **D-33.h `outergap()` is `min_border`.** `xscale(outergap(#))` adds the size (gap kind, `resolve_size`, px) to `fig.min_border_bottom`; `yscale(outergap(#))` to `fig.min_border_left`; under `alt` the other side. Under by() twoway draws it as if absent (the `by_graph` rule of `titlegap()`), so does dash.
- **D-33.i `noextend` is `Axis.bounds`.** `noextend` tags the axis `fig._dash_noextend = {letter}`; `_dash_finish_count_ticks` (both modes, the saved page through `dash_axis_finish`) sets `axis.bounds = (first_tick, last_tick)` for a tagged axis after the ticks are final, and `"auto"` otherwise. `extend` and `fextend` both leave `bounds="auto"` (the Bokeh frame already includes the plot-region margin, so a line to the plot region's edge and one through the margin coincide); the difference is documented in the help with the measured lengths. S33 is batch 11's editor of `_dash_finish_count_ticks`/`_DASH_AXIS_FINISH_JS` (R11); the JS twin is `dash_axis_noextend(a, ticks)` added inside `dash_axis_finish` after the ticker write.
- **D-33.j The floor is applied once, after the multiply.** `translate_lwidth` gains `default_pt=None`; when given it is the unfloored default in points and `default_px` is ignored. Every call site whose default is a floored pixel width (`line_px(...)` or a glyph's `line_width`) passes the role's unfloored points instead (`SchemeParser.linewidth_pt(role)` -- a new accessor over the existing `_LWIDTH_RS` ladder reading -- or the scheme's measured points). `line_px` is unchanged.

## Risk: [yellow] -- two appliers every axis passes through, one new axis per alternate side, and a width rule every line reads

**Why.** `_dash_apply_axis_spec` and `_dash_apply_scale_look` run on every figure in both modes; `translate_lwidth` is called by every line, bar outline, tick and grid.

**Risk factors.**
1. The twin axis (D-33.a) is a new `LinearAxis` on a primary range: `_dash_primary_axes` returns it, so the finishers would tick it twice and `_dash_axis_alternate` could move it alone.
2. `CustomJSTickFormatter.doFormat` on a `DatetimeTickFormatter` returns strings through the same call in 3.8 and 3.9 (bokeh-web.md §10: no model removed); a future change would blank labels.
3. `Axis.bounds` in data units on a log axis takes the data values, not their logs; a mixed date axis takes Stata units.
4. Pinned tests assert today's note for these sub-options (test_axis_options.py, test_axis2_suboptions.py `TestUnusedSecondAxisOptionsAreNamed`, test_subopt_abbrev.py `TestAxisAbbreviations`, test_help_claims_*).
5. Changing the width default at a call site changes a drawn width wherever the default was sub-floor (vvvthin, vvthin roles).
6. Batch partners: S32 edits figure sizing (`min_border` for `fxsize/fysize/scale`), S34 edits dash.ado's syntax block and mlabel readers. `min_border_*` is written by both S32 and S33.

**Mitigation.**
1. The twin carries `tags=["dash_alt_axis"]`; `_dash_primary_axes` gains one line excluding tagged axes; `test_the_twin_is_not_finished` pins it.
2. `TestAlternate::test_the_formatter_calls_the_base` runs the formatter code under node with a stub `base` and the installed BokehJS `doFormat` signature read from `bokeh/server/static/js/bokeh.js`.
3. `test_noextend_on_a_log_axis` and `test_noextend_on_a_date_axis` pin the units.
4. Every pinned test is flipped in place in the row's commit (TDD stubs, "Flips").
5. 33-04's `grep -n "translate_lwidth(" dash_render.py` enumerates the sites; each is listed in the commit body with its old and new default; `test_line_width_edges.py::TestCallSites` asserts no site passes a floored px as the default.
6. S33 adds to `min_border_*` (`+=`), never assigns; S32's values survive. The merger lands S32 first (index batch 11 order 32, 33, 34).

## Dependencies

- **Depends on: 24** (batch 8, minor ticks and labels): S24 lands the minor-set `##N` rule on `xmlabel()/xmtick()` and the second LabelSet; S33's `##N` edit (D-33.c) is confined to the `xlabel/ylabel/xtick/ytick` branch of `_dash_parse_axis_spec` and must re-read S24's code at the batch-11 base. S24's `_DASH_AXIS_FINISH_JS` edit (R11 batch 8) is the base S33's `dash_axis_noextend` is written on.
- **Blocks:** none. S35 (batch 12) edits the finishers next and reads `dash_alt_axis`; S45 (batch 15) edits them after.
- **Parallel batch: 11**, merge order 32, 33, 34. **Can run with S32 and S34:** S32 edits `_dash_layout_cell`, `_dash_figure_aspect`'s siblings (`_dash_frame_aspect`, `_dash_frame_sizes`, `_dash_overhangs`), `_make_figure_body`'s tail, the template's tail line, `_dash_option_rules` and `scale()` (`_dash_apply_scale`); S34 edits dash.ado's `syntax` and the mlabel readers and dash_parse.mata's mlabel tables. S33 edits none of those; its dash.ado edit is one call in `_dash_validate_opts` after :6991 and its Mata function is new.

## Evidence

All anchors at `6370ca4` (dash_render.py 52,280 lines; dash.ado 11,039; dash_parse.mata 9,789; dash.sthlp 5,207). Re-read before editing.

### The label sub-options

`_DASH_AXLABEL_SUBOPT_TABLE` (:36881-36913) names every sub-option of axis_label_options.sthlp in twoway's two stages. `_DASH_AXLABEL_HONOURED` (:36969-36976):

```python
36969 _DASH_AXLABEL_HONOURED = frozenset({
36970     "format", "labsize", "angle", "grid", "nogrid", "valuelabels",
36971     "novaluelabels", "norescale",
36973     "add",
36975     "labels", "nolabels", "ticks", "noticks", "labcolor", "tlength",
36976     "tposition"})
```

`_dash_parse_axis_spec` (:30272) resolves the tail's tokens with `_dash_subopt_resolve([_toks], _DASH_AXLABEL_SUBOPT_TABLE)` (:30322-30323) and puts anything not in the honoured set on `out["unsupported"]` (:30326-30328); `_dash_apply_axis_options` (:31601) prints them at :31693 through `_dash_report_suboptions`. `_dash_apply_axis_spec` (:30426) sets `major_label_standoff = 0` for `nolabels` (:30614), `labcolor` at :30615-30619, the grid at :30631-30638:

```python
30631    if spec["grid"] is not None:
30632        for g in grid_obj:
30633            if spec["grid"]:
30634                if g.grid_line_color is None:
30635                    g.grid_line_color = grid_color or "#e5e5e5"
30636            else:
30637                g.grid_line_color = None
```

The tick look (`_dash_apply_tick_look`, :30752-30815) writes `major_tick_in/out` from `tlength()`/`tposition()` and `major_tick_line_color` (:30812-30815); nothing writes `major_tick_line_width` or `major_tick_line_dash`. `_dash_apply_tick_option` (:31465) draws `xtick()` positions as the axis's minor ticks under a `CustomJSTicker` (`_DASH_TICK_MAJOR_JS`, `_DASH_TICK_EXTRA_JS`, `_DASH_TICK_EVERY_JS`, :30918-30925).

### `##N`, `minmax`

```python
30269 _DASH_AXIS_RULE_RE = re.compile(r"\A#{1,2}\s*(\d+)\s*(.*)\Z", re.S)
```

The docstring at :30262-30266: "A double hash is read the same as a single one: no probe of this section distinguishes them." `minmax` (`mode == "minmax"`, :30511) reads *values*, which `_dash_apply_axis_options` passes as `col = frame[var]` (:31637), *var* being `xvar`/`yvar` -- the first layer's variable only.

### The scale look

```python
31980 _DASH_SCALE_LOOK_SUBOPTS = frozenset({
31981     "off", "on", "noline", "line", "lcolor", "lwidth", "lpattern",
31982     "alternate", "titlegap"})
```

`_dash_scale_spec` (:38553) names the rest (:38570-38575). `_dash_scale_look` (:38584) reads `"alternate": "alternate" in names` -- presence, not parity. `_dash_apply_scale_look` (:30816) writes `axis_label_standoff` from `titlegap()` (:30870-30882, default `axis_obj.axis_label_standoff * 0.75` pt = Bokeh's 5 px) and calls `_dash_axis_alternate` (:30886) which moves the axis across (:30895-30908). No scheme stub sets the default standoff: `gsize axis_title_gap` is read nowhere (`grep -c axis_title_gap dash_render.py` prints 0).

### Line widths

```python
7167     def line_px(pt: Any) -> float:
7180         return max(p, T._LWIDTH_FLOOR_PT) * T.PX_PER_PT
7602     def translate_lwidth(value: str, default_px: Any = None,
7603                          ref_in: float = 4.0) -> float:
7624         default_pt = (d * 0.75 if d is not None
7625                       else T._LWIDTH_RS["medium"] * T.PT_PER_RS)
7626         pt = T.resolve_size(value, "line", default_pt, ref_in)
7630         return T.line_px(pt)
```

`resolve_size` (:7098) applies `*#` to *default_pt* (:7133-7135) and bounds the line kind at 10,000 units (:7108-7110, `_LWIDTH_MAX_RS`). A site that passes a drawn width (already through `line_px`) as *default_px* hands the floored value to the multiply.

### Stata rules (research/stata-ground-truth.md)

- §8: `##N` "allowed with mlabel()/mtick() only (axis_label_options.sthlp :62-68)"; "##N ignored, only allowed for minor ticks" (tickset_g.class:991).
- §11: `gsize tick tiny` (1.3888), `tickgap half_tiny`, `tick_label medsmall`; `linewidth minortick thin`; grids `linestyle major_grid` from the scheme.
- §10: `justification` = horizontal alignment of text, `alignment` = vertical (`textbox_options.sthlp` :39-51).
- axis_scale_options.sthlp (read by the executor at `/Applications/StataNow/ado/base/a/axis_scale_options.sthlp`): `alt` "an alternate location"; `outergap(relativesize)` the gap between the axis labels and the graph's edge; `noextend`/`extend`/`fextend` the axis line's extent; `fill`/`nofill` (`fillspace`) relevant to `graph combine` only.

### Tests that pin today's behaviour (flip in place, never delete)

- test/test_axis_options.py::TestAxisLabelGrammar -- every node asserting a `labgap`/`alternate`/`tl*`/`gl*` token in the `unsupported` list or in a warning.
- test/test_axis_options.py::TestAxisScale -- nodes asserting `outergap`/`noextend`/`fextend`/`lstyle` are named.
- test/test_axis2_suboptions.py::TestUnusedSecondAxisOptionsAreNamed -- the names S33 draws on axis 1 stay named on axis 2 only where S35 has not landed (S35 is batch 12: no flip here; the test is read, not changed, unless it names axis-1 behaviour).
- test/test_subopt_abbrev.py::TestAxisAbbreviations, ::TestAxisInOneCopy -- nodes asserting `labgap(small)` or `glc(red)` end on the unsupported list.
- test/test_help_claims_*.py and test_help_conformance.py nodes that read the help's sentence "named in a warning" for these sub-options (33-02's grep lists them).
- test/test_line_width_edges.py does not exist; test_option_sizes.py / test_line_widths.py nodes pinning `translate_lwidth("*2", default_px=0.4)` to 0.8 px are flipped by 33-04.

The exact red list is measured by 33-01 on a simulated fix and written to `<scratch>/33-flips.txt`.

## User stories

- **US-33.1** As a Stata user pasting `ylabel(, labgap(small) tlwidth(thick) glpattern(dash))`, I want the label gap, tick width and grid pattern drawn as twoway draws them so that the dashboard matches my graph without a note.
- **US-33.2** As a Stata user with long x labels, I want `xlabel(, alternate)` to stagger the labels on two rows so that none overlap.
- **US-33.3** As a Stata user, I want `ylabel(minmax)` to label the extremes of every layer, not the first one, so that a two-layer graph is labelled as twoway labels it.
- **US-33.4** As a Stata user who typed a label form twoway refuses, I want dash to refuse it with the same words so that my do-file behaves the same under both.
- **US-33.5** As a Stata user, I want `yscale(noextend)`, `yscale(outergap(5))` and the scheme's title gap drawn, and `yscale(alt) yscale(alt)` to leave the axis where twoway leaves it.
- **US-33.6** As a scheme author using `lwidth(*2)` over a very thin default, I want the width twoway draws (the multiply before the floor).

## Business requirements

- **BR-33.1** Each sub-option in the D6 list except the five style names is drawn in both renderers and produces no note.
- **BR-33.2** `##N` on `xlabel/ylabel/xtick/ytick` draws what twoway draws and prints what twoway prints (measured).
- **BR-33.3** `minmax` labels the least and greatest value drawn on that axis over every layer.
- **BR-33.4** Every label form the fixture records with rc != 0 is refused with twoway's rc and first line.
- **BR-33.5** `outergap()`, `noextend`, `lstyle()` are drawn; `extend`/`fextend`/`fill` behave as the fixture says; two `alt` copies toggle as twoway toggles; the default title gap is the scheme's `axis_title_gap`; `zlabel()/zscale()` look words print what twoway prints on a non-contour graph.
- **BR-33.6** `lwidth(*#)` equals twoway's width for a sub-0.3 pt default; the 10,000-unit bound follows the measurement; `tlwidth()`/`glwidth()` widths follow the same rule.
- **BR-33.7** Nothing drawn today changes unless the fixture says twoway draws it differently.

## Technical requirements

Sub-option -> Bokeh property map (D6; `_dash_apply_axis_spec` for `xlabel/ylabel`, the same keys through `_dash_apply_tick_look` for `xtick/ytick`):

| Sub-option (full name) | Parsed key in `_dash_parse_axis_spec` | Bokeh property on the axis / grid | Value rule |
|---|---|---|---|
| `labgap(size)` | `labgap` | `Axis.major_label_standoff` | `resolve_size(v, "gap", axis.major_label_standoff * 0.75)` pt x 4/3, rounded, clamped [-100, 100]; a bad name: `_dash_style_note(..., "size", "medium")` |
| `labjustification(left/center/right)` | `labjust` | `Axis.major_label_text_align` | the word; else note, unchanged |
| `labalignment(top/middle/bottom/baseline)` | `labalign` | `Axis.major_label_text_baseline` | `baseline` -> `"alphabetic"`; else the word |
| `alternate` | `alternate` (True) | twin `LinearAxis` + two `CustomJSTickFormatter` (D-33.a) | twin tagged `dash_alt_axis` |
| `altgap(size)` | `altgap` | twin's `major_label_standoff` | first axis's standoff + size px; default the label font size in px |
| `tlwidth(lwidth)` | `tlwidth` | `Axis.major_tick_line_width` | `translate_lwidth(v, default_pt=<scheme tick width pt>)` |
| `tlcolor(color)` | `tlcolor` | `Axis.major_tick_line_color` | through the same colour reader as `labcolor` (:30615-30619) |
| `tlpattern(lpattern)` | `tlpattern` | `Axis.major_tick_line_dash` | `translate_lpattern(v)`; a bad name: `_dash_style_note(..., "line pattern", "solid")` |
| `glwidth(lwidth)` | `glwidth` | `Grid.grid_line_width` | `translate_lwidth(v, default_pt=<scheme major_grid width pt>)` |
| `glcolor(color)` | `glcolor` | `Grid.grid_line_color` | colour reader; turns the grid on as `grid` does |
| `glpattern(lpattern)` | `glpattern` | `Grid.grid_line_dash` | `translate_lpattern(v)` |
| `nogmin` / `nogmax` | `gmin`/`gmax` (False) | `Grid.ticker` = `CustomJSTicker(major_code=_DASH_GRID_NOEND_JS, args={base, drop_start, drop_end})` | D-33.b |
| `gmin` / `gmax` | `gmin`/`gmax` (True) | none | Bokeh's default (D-33.b; fixture may invert) |
| `gextend` / `nogextend` | `gextend` | none or documented | fixture `grid_extend` decides: identical SVG -> silent no-op |
| `custom` | `custom` (True) | none | fixture `custom` decides: identical SVG -> silent no-op; else stays named |

- **TR-33.1** `_DASH_AXLABEL_HONOURED` (:36969) gains the fourteen names above plus `gmin nogmin gmax nogmax gextend nogextend custom alternate altgap labjustification labalignment`; the comment line `# WP-31 D6: the stylable sub-options.` precedes them. The five style names are not added.
- **TR-33.2** `_dash_parse_axis_spec` (:30300-30340): new `out` keys `labgap labjust labalign alternate altgap tlwidth tlcolor tlpattern glwidth glcolor glpattern gmin gmax gextend custom double_hash` (None/False defaults), each filled in the `elif _nm == ...` chain after the `tposition` branch; `_DASH_AXIS_RULE_RE` becomes `re.compile(r"\A(#{1,2})\s*(\d+)\s*(.*)\Z", re.S)` and the head reader sets `double_hash` when group 1 is `##` (D-33.c).
- **TR-33.3** `_dash_apply_axis_spec` (:30426): after the `labcolor` block (:30619) apply labgap/labjust/labalign/tl*/alternate; after the grid block (:30638) apply gl*/gmin/gmax. The tick properties go through `_dash_apply_tick_look`'s `pre` prefix (`major`), so `xtick()`'s copy (`minor`) gets them as `minor_tick_line_*`.
- **TR-33.4** `_dash_alt_axes(fig, axis_obj, spec, ref_in)` new module function (D-33.a), called from `_dash_apply_axis_options` after `_dash_apply_axis_spec` (it needs *fig*); constants `_DASH_ALT_LABEL_JS`, `_DASH_GRID_NOEND_JS`. Copy list: constants after `"_DASH_TICK_EVERY_JS",` (:46653); function after `"_dash_apply_scale_look",` in the functions tuple (grep its line). `_dash_primary_axes` excludes axes whose `tags` holds `dash_alt_axis`.
- **TR-33.5** `_dash_axis_layer_values(frame, plots, letter, date_vars)` (D-33.d), module-level, after `_dash_apply_axis_options`; copy-list entry after `"_dash_apply_scale_look",`; `test/function_test_map.py` entry naming `test/test_axis_look_options.py::TestMinmax::test_every_layer`.
- **TR-33.6** Mata `_dash_axlabel_refusal(string scalar text)` (D-33.e) in dash_parse.mata directly after `_dash_layout_refusal` (ends :1679), header index line after `_dash_layout_refusal`'s, `_needed` entry (dash.ado:448-479, alphabetical), `test/program_coverage_map.py` entry naming `test_option_validation.cscript:U33-07`. dash.ado: after line :6991 `_dash_subopt_check zlabel`, insert `foreach _ax in xlabel ylabel xtick ytick { ... mata: st_local("_axr", _dash_axlabel_refusal(st_local("_ax_val"))) ... if length -> mata: _dash_say("err", ...); exit <rc from fixture> }` (the values are the merged option locals the JSON writer reads at :7339-7415; the executor uses the same local names).
- **TR-33.7** D7: `_DASH_SCALE_LOOK_SUBOPTS` (:31980) gains `"outergap", "noextend", "extend", "fextend", "lstyle"` and, as the fixture says, `"nofillspace", "fillspace"`; `_dash_scale_look` returns `outergap`, `extend` (one of `"no"`, `"yes"`, `"f"`, None), `lstyle`, and `alternate` by parity (D-33.f); `_dash_apply_scale_look` draws `outergap` (D-33.h), `lstyle` (the scheme's line style bundle: the `_bundle` call `_dash_region_spec` makes for its `lstyle()` at :6504-6560, reused by name), and tags `fig._dash_noextend` (D-33.i). `_dash_finish_count_ticks` (:33346) sets `bounds` for tagged axes; `_DASH_AXIS_FINISH_JS` gains `function dash_axis_noextend(a, ticks)` directly before `function dash_axis_same`, called in `dash_axis_finish` after each ticker write; the plan (`_dash_axis_plan`, :32310) carries `"noextend": 1` per axis entry (no user text).
- **TR-33.8** `SchemeParser.axis_title_gap` (new property, after `default_marker_size`) reads `gsize axis_title_gap`; `_dash_apply_axis_options` sets `axis_label_standoff` to its px on both primary axes before `titlegap()` is read; the stub reaches the shipped `dash-*.scheme` files THROUGH THE GENERATOR, never by hand (the files are `scripts/extract_scheme_truth.py` output; a hand edit is erased at the next run and never reaches `scheme_truth.json`): add the truth entry `axis_title_gap` (gsize) beside the tick gsizes in the truth-entry region of scripts/extract_scheme_truth.py and the directive `scalar("gsize", "axis_title_gap", "axis_title_gap")` in the gsize directive group; run `scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` twice (idempotent); `git add -f test/fixtures/scheme_truth.json` and the regenerated `dash-*.scheme`. `SchemeParser.axis_title_gap` default when a scheme has no stub: `minuscule` (scheme-s2color.scheme:152). S30/S31 (batch 10) edit the generator in other groups (title rings, legend ring); S33's hunk is the gsize group only, applied after batch 10 lands.
- **TR-33.9** `zlabel()`/`zscale()` look words: `_dash_scale_spec` (:38570-38575) and the zlabel reader print what the fixture `zlook` records: nothing when twoway prints nothing (the `honoured` set then includes the look names for `zscale` on a non-contour graph), or twoway's line verbatim.
- **TR-33.10** E6: `translate_lwidth(value, default_px=None, ref_in=4.0, default_pt=None)` (D-33.j); `SchemeParser.linewidth_pt(role)`; every call site listed by `grep -n "translate_lwidth(" dash_render.py` whose default is a floored px passes `default_pt=`. The 10,000-unit bound: the fixture `lw_bound` decides -- twoway rc 0 keeps `_LWIDTH_MAX_RS` as a draw-time clamp with `_dash_style_note(option, value, "line width", "10,000 units")`; a twoway refusal is NOT applied by S33: S32 is batch 11's `_dash_option_rules` editor (DECISIONS A15) and applies the one-token `lwidth` bound change exactly as this sentence states it (the bound value becomes the fixture's refused threshold, the words twoway's) as part of its rules edit; S33 records the measured rc and line in the fixture (`lw.bound_20000`) and in `<scratch>/s33/handback.txt` for the merger, keeps the draw-time clamp with the note until S32's token lands, and its `TestLwidthBound::test_refused` reads the fixture and is marked a guard until the batch-11 merge (it goes green when S32's token is in the merged tree).
- **TR-33.11** Help (R3): the "Axis and Display Options" paragraphs that say these sub-options are "named in a warning" (dash.sthlp:3512-4140, the lines 33-02's grep finds for `labgap`, `alternate`, `tlwidth`, `glwidth`, `outergap`, `noextend`, `lstyle`) are rewritten to say they are drawn, with one measured example each for `alternate` and `noextend`; the Unsupported list (:4968-5136) has no line for these (they are sub-options, not options), so none is removed; TWOWAY_COVERAGE_AUDIT.md row "Axes" (:137) gains ", labgap(), alternate, tick and grid line widths, colours and patterns, outergap(), noextend" in its honoured column.
- **TR-33.12** Parity (R8): `test_mode_parity.py` `CORPUS` entries `"ylabel alternate labgap"`, `"ylabel glwidth nogmin"`, `"yscale noextend outergap"`, `"xline lwidth(*2) under vvthin"` under `# WP-31 D6/D7/E6`; `MOVE_CORPUS` `"ylabel alternate, dropdown"` (the twin axis survives a move).

### Code and verbatim texts (copy, do not paraphrase)

**`_DASH_ALT_LABEL_JS`** (constant; args `parity`, `base`):

```js
if ((index % 2) !== parity) return "";
const out = base.doFormat(ticks, {loc: 0});
return (out && out.length > index) ? out[index] : "";
```

**`_DASH_GRID_NOEND_JS`** (`CustomJSTicker.major_code`; args `base`, `drop_start`, `drop_end`):

```js
const r = base.get_ticks(cb_data.start, cb_data.end, cb_data.range, cb_data.cross_loc).major;
const lo = Math.min(cb_data.start, cb_data.end), hi = Math.max(cb_data.start, cb_data.end);
const tol = 1e-9 * Math.max(1e-300, hi - lo);
return r.filter((v) => !(drop_start && Math.abs(v - lo) <= tol) && !(drop_end && Math.abs(v - hi) <= tol));
```

**`_dash_alt_axes(fig, axis_obj, spec, ref_in)`** (module function, after `_dash_apply_axis_options`):

```python
def _dash_alt_axes(fig, axis_obj, spec, ref_in=4.0):
    """xlabel(, alternate [altgap()]) as a tagged twin axis (WP-31 D6, D-33.a)."""
    if not spec.get("alternate"):
        return []
    from bokeh.models import LinearAxis, CustomJSTickFormatter
    T = OptionTranslator
    made = []
    for ax in list(axis_obj):
        side = next((s for s in ("below", "above", "left", "right")
                     if any(a is ax for a in getattr(fig, s))), None)
        if side is None or "dash_alt_axis" in (ax.tags or []):
            continue
        base = ax.formatter
        ax.formatter = CustomJSTickFormatter(
            args={"parity": 0, "base": base}, code=_DASH_ALT_LABEL_JS)
        font_px = T.css_px(ax.major_label_text_font_size)  # the label height
        gap = font_px
        if spec.get("altgap") is not None:
            try:
                gap = T.resolve_size(str(spec["altgap"]), "gap",
                                     font_px * 0.75, ref_in) * T.PX_PER_PT
            except (ValueError, TypeError):
                _dash_style_note(f"{spec.get('option', 'label')}(altgap)",
                                 spec["altgap"], "size", "medium")
        twin = LinearAxis(ticker=ax.ticker, axis_line_color=None,
                          major_tick_in=0, major_tick_out=0,
                          minor_tick_in=0, minor_tick_out=0,
                          major_label_standoff=max(0, int(round(
                              gap - _dash_axis_panel_px(ax)))),  # measured rule, D-33.a
                          major_label_text_font_size=ax.major_label_text_font_size,
                          major_label_text_color=ax.major_label_text_color,
                          major_label_orientation=ax.major_label_orientation,
                          formatter=CustomJSTickFormatter(
                              args={"parity": 1, "base": base},
                              code=_DASH_ALT_LABEL_JS),
                          tags=["dash_alt_axis"])
        for attr in ("x_range_name", "y_range_name"):
            setattr(twin, attr, getattr(ax, attr))
        fig.add_layout(twin, side)
        made.append(twin)
    return made
```

`_dash_axis_panel_px(ax)` is a small module helper beside `_dash_alt_axes`: `ax.major_label_standoff + OptionTranslator.css_to_pt(ax.major_label_text_font_size) * 96 / 72 + ax.major_tick_out`, the first axis's panel height in px; its constant is corrected to the measured delta in 33-02 (D-33.a) and it joins the functions copy tuple after `_dash_alt_axes`.

`T.css_px` exists if `OptionTranslator.css_pt` has a px inverse; else read the font size with `float(str(size).rstrip("pt")) * T.PX_PER_PT` inline (the executor checks `grep -n "def css_" dash_render.py`).

**`_dash_axis_layer_values(frame, plots, letter, date_vars)`:**

```python
def _dash_axis_layer_values(frame, plots, letter, date_vars=None):
    """Every value the graph's layers draw on axis *letter* (WP-31 D6, D-33.d):
    minmax reads all layers, as twoway's axis does.  Dates in Stata units."""
    cols = getattr(frame, "columns", [])
    out = []
    for p in plots or ():
        for key in _DASH_AXIS_VAR_KEYS[letter]:
            for v in _dash_extract_vars(p, key):
                if v in cols:
                    s = pd.to_numeric(frame[v], errors="coerce")
                    k = (date_vars or {}).get(v)
                    if k in _STATA_DATE_KINDS:
                        s = pd.Series(_dash_date_units(s, k))
                    out.append(s)
    if not out:
        return None
    return pd.concat(out, ignore_index=True).dropna()
```

`_DASH_PLOT_VAR_KEYS` (:36470) is a FLAT tuple `("yvar","xvar","var","yvar1","yvar2","y1var","x1var","y2var","x2var")`, not a dict, and the range types' bound keys (`lo hi y1 y2`) are not in it; `_dash_extract_vars` is a dash.ado program at 6370ca4, not a renderer function. S33 therefore adds a small module dict `_DASH_AXIS_VAR_KEYS = {"x": ("xvar", "var", "x1var", "x2var"), "y": ("yvar", "yvar1", "yvar2", "y1var", "y2var")}` beside `_DASH_PLOT_VAR_KEYS`, extended with the range-type bound keys the renderer's own var reader enumerates (33-02 greps the mapper that reads each range type's bounds -- `map_rarea`/`map_rbar`/`map_rcap` -- and lists the keys it finds in the commit body); `yvars` lists are flattened.

**Mata `_dash_axlabel_refusal`** (one row per refused fixture form; the table is written from the fixture by 33-02 and must equal it):

```
// _dash_axlabel_refusal(text): twoway's refusal line for an xlabel()/
// ylabel()/xtick()/ytick() value it refuses (WP-31 D6), "" otherwise.
string scalar _dash_axlabel_refusal(string scalar text)
{
    string scalar s
    s = strtrim(text)
    // rows: (regex over the typed value, twoway's line); from
    // test/fixtures/axis_look_truth.json refusals.* with rc != 0
    if (regexm(s, "^\"[^\"]*\"$")) return("<fixture line for \"a\">")
    return("")
}
```

**Help sentences** (Axis and Display Options; replace the "named in a warning" clauses for these names):

`{cmd:labgap()}, {cmd:labjustification()}, {cmd:labalignment()}, {cmd:alternate}, {cmd:altgap()}, {cmd:tlwidth()}, {cmd:tlcolor()}, {cmd:tlpattern()}, {cmd:glwidth()}, {cmd:glcolor()}, {cmd:glpattern()}, {cmd:gmin}, {cmd:gmax}, {cmd:nogmin} and {cmd:nogmax} are drawn as {cmd:twoway} draws them; {cmd:alternate} staggers the labels on two rows, the second row {cmd:altgap()} below the first (one label height by default).  {cmd:labstyle()}, {cmd:tstyle()}, {cmd:gstyle()}, {cmd:tlstyle()} and {cmd:glstyle()} name Stata style files {cmd:dash} does not read and are named in a note.  {cmd:##}{it:#} on a label or tick option is for minor ticks only, as in {cmd:twoway}: <the fixture's sentence on what twoway draws and prints>.  {cmd:minmax} labels the least and greatest value of every layer on the axis.`

`{cmd:xscale()} and {cmd:yscale()} draw {cmd:outergap()} (space between the axis and the graph's edge), {cmd:noextend} (the axis line runs from the first to the last tick), {cmd:extend} and {cmd:fextend} (the line spans the plot region and its margin, which coincide in {cmd:dash}: {it:difference from twoway}, where {cmd:extend} stops at the plot region's edge) and {cmd:lstyle()}; a second {cmd:alt} toggles the side back, as in {cmd:twoway}.  The default gap between the axis title and its labels is the scheme's {cmd:gsize axis_title_gap}.`

**BUGS.md Resolution (D6; the title is S01's):** `  - Resolution: Fixed <ddmonyyyy> (WP-31, D6). _dash_parse_axis_spec reads labgap(), labjustification(), labalignment(), alternate, altgap(), tlwidth(), tlcolor(), tlpattern(), glwidth(), glcolor(), glpattern(), gmin, gmax, nogmin, nogmax, gextend, nogextend and custom; _dash_apply_axis_spec and _dash_apply_tick_look draw them on the axis and grid properties; _dash_alt_axes draws alternate as a tagged twin axis; a ## rule on a label or tick option does what twoway does with it; _dash_axis_layer_values gives minmax every layer; _dash_axlabel_refusal refuses the label forms twoway refuses, in its words; in both renderers. Pinned by test/test_axis_look_options.py::TestLabelLook::test_labgap, test/test_axis_look_options.py::TestAlternate::test_twin, test/test_axis_look_options.py::TestMinmax::test_every_layer, test/test_wp31_truth.cscript U33-01, test/test_option_validation.cscript U33-07; fixture test/fixtures/axis_look_truth.json. Residual, deferred (WP-31): labstyle() tstyle() gstyle() tlstyle() glstyle() name style files and stay named until section 44 reads them (GAPS3 D6 Tracked). Closes GAPS3 D6 (WP-31, D6).`

**CHANGELOG lines:**
- Results (D6): `- Axis label, tick and grid sub-options are drawn. dash scatter mpg weight, ylabel(, labgap(large) tlwidth(thick) glwidth(thick) grid) drew the default gap and widths and printed a sub-option note, now twoway's gap and widths and no note; xlabel(, alternate) staggers the labels on two rows; ylabel(minmax) on two layers labelled the first layer's extremes, now every layer's. (WP-31, D6)`
- Changed behaviour (D6): `- The axis label forms twoway refuses -- <the fixture's forms, comma-separated> -- are refused with twoway's return code and words; dash drew them. (WP-31, D6)`
- Results (D7): `- yscale(alt) yscale(alt) moved the y axis to the right, now <the fixture's side>; yscale(noextend) drew the axis line across the whole frame, now from the first to the last tick; yscale(outergap(5)) had no effect, now widens the border by twoway's gap; the default axis title gap is the scheme's gsize axis_title_gap (Bokeh's 5 px before). (WP-31, D7)`
- Results (E6): `- lwidth(*2) over a default thinner than 0.3 pt drew twice the floored width (0.8 px for a vvthin xyline), now twoway's: twice the raw width, then the floor (<the fixture's px>). tlwidth() and glwidth() are drawn. (WP-31, E6)`

## Boundaries

- Not `xmlabel()/xmtick()` or any minor-set rule (S24, batch 8); not the second axis's `ylabel2()/xlabel2()` appliers or `_dash_finish_secondary_axes` (S35, batch 12); not date `#N` ticks (S45).
- Not `_dash_option_rules` at all (S32's this batch, A15; the `lwidth` bound token rides S32's rules edit); not `_FILTER_JS`, `_generate_app_source`, `_make_figure_body`, `_build_filter_widgets` (R12).
- Not the style-file reader (S44): `labstyle tstyle gstyle tlstyle glstyle` stay named (D-33.g).
- No scheme colour spaces beyond RGB/RGBA (M7); the `gsize axis_title_gap` stubs are sizes.
- Not `_dash_layout_cell`, `_dash_figure_aspect`'s siblings, `_make_figure_body`'s tail or `fxsize/fysize/scale` (S32); `min_border_*` is only added to (`+=`), and S32's `_dash_overhangs` adds too, so both survive in either merge order.
- Not the `dash-*.scheme` files by hand: the `axis_title_gap` stub goes through scripts/extract_scheme_truth.py (TR-33.8).

## Stata truth

**New extractor** `scripts/extract_axis_look_truth.do`, in the path-free form of `scripts/extract_by_grid_truth.do` (:1-45: `DASH_REPO` else `c(pwd)`, the quote/backtick check, `set graphics off`, `global dash_nobrowser 1`), run only as `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s33/x $WT/scripts/extract_axis_look_truth.do`. It writes `test/fixtures/axis_look_truth.json` (`git add -f`), `_meta` = `stata_version born_date dash_commit extracted source` (the commit through `shell git rev-parse HEAD > file`, read by the python block; never `shell=True`; backticks as `\x60`). twoway only; `sysuse auto`, `set scheme s2color`; every graph exported to SVG and read by `scripts/svg_truth.py` (`svg_document`, `svg_lines`, `svg_axis_reading`); every SVG erased.

| Key | twoway command | Recorded |
|---|---|---|
| `labgap.<small,large,n3>` | `scatter mpg weight, ylabel(, labgap(small))` ... | px between tick end and label text (SVG), label font size |
| `labjust.<left,center,right>`, `labalign.<top,middle,bottom,baseline>` | `ylabel(, labjustification(left))` ... | label text x / y relative to the tick |
| `alternate.default`, `alternate.altgap_large` | `xlabel(1500(500)5000, alternate)`, `..., alternate altgap(large))` | two distinct label y values, their difference in px |
| `tl.width_thick`, `tl.color_red`, `tl.pattern_dash` | `ylabel(, tlwidth(thick))`, `tlcolor(red)`, `tlpattern(dash)` | tick line stroke width, colour, dasharray |
| `gl.width_thick`, `gl.color_red`, `gl.pattern_dash` | `ylabel(, grid glwidth(thick))` ... | grid line stroke width, colour, dasharray |
| `grid_ends.default`, `grid_ends.nogmin_nogmax`, `grid_ends.gmin_gmax` | `ylabel(10 20 30 40, grid)`, `..., grid nogmin nogmax)`, `..., grid gmin gmax)` | count of horizontal grid lines and whether lines sit at the axis ends |
| `grid_extend.<default,gextend,nogextend>` | `ylabel(, grid gextend)` ... | grid line length px |
| `custom.<with,without>` | `ylabel(10 20 30, custom)` / `ylabel(10 20 30)` | the SVG documents' equality (less ids) |
| `double_hash.ylabel`, `double_hash.ytick` | `capture noisily twoway scatter mpg weight, ylabel(##5)` / `ytick(##5)` | rc, every log line, major tick count |
| `minmax.two_layers` | `scatter mpg weight || scatter price weight, ylabel(minmax)` | the two label texts |
| `refusals.<form>` for `"a"`, `1 "a" "b"`, `none 1 2`, `minmax 1`, `#3 #4`, `1(1)`, `,` | `capture noisily twoway scatter mpg weight, ylabel(<form>)` | rc, first error line |
| `scale.outergap_5`, `scale.noextend`, `scale.extend`, `scale.fextend`, `scale.fill` | `yscale(outergap(5))`, `yscale(noextend)` ... | axis line y-extent px, plot-region box px, canvas px |
| `scale_alt2.one`, `scale_alt2.two` | `yscale(alt)`, `yscale(alt) yscale(alt)` | side of the y labels (x of label text vs plot box) |
| `scale.lstyle_grid` | `yscale(lstyle(grid))` | axis line colour, width, dash |
| `title_gap.default` | `scatter mpg weight` | px between the y labels' left edge and the title; `gsize axis_title_gap` stub value |
| `zlook.zlabel`, `zlook.zscale` | `capture noisily twoway scatter mpg weight, zlabel(, labsize(small))` / `zscale(alt)` | rc, log lines |
| `lw.star2_vvthin`, `lw.star2_medium`, `lw.bound_20000` | `xline(3000, lwidth(*2))` under a scheme file whose `linewidth xyline` is `vvthin` (written to the work dir), `..., lwidth(*2))` default, `capture noisily ... lwidth(20000)` | stroke width px; rc and line |

**Truth blocks** (R1, A14: one per row): `test/test_wp31_truth.cscript`, headers `* ==== S33 D6: Axis label, tick and grid sub-options ====` (U33-01..U33-04, appended by 33-01, staged by 33-02), `* ==== S33 D7: Axis-scale look ====` (U33-05, U33-06, appended and staged by 33-03), `* ==== S33 E6: Line-width edges ====` (U33-08, appended and staged by 33-04), each in the WP-30 gate form with `WP31_ONLY`/`w31_run`, helpers `_ul_*` above the header, each case ending `_w31_done U33-0k "<what>"`:
- **U33-01** `dash scatter mpg weight, ylabel(, labgap(large) tlwidth(thick) glwidth(thick) glpattern(dash) grid)`: saved and served figures' `major_label_standoff`, `major_tick_line_width`, grid width and dash equal the fixture's values converted at dash's reference; the log holds no `sub-option(s) not implemented`.
- **U33-02** `xlabel(1500(500)5000, alternate)`: both modes have one axis tagged `dash_alt_axis` on `below`; two formatters with parities 0 and 1.
- **U33-03** `ylabel(minmax)` on two layers: the labelled ticks equal the fixture's two texts.
- **U33-04** `ylabel(##5)`: dash's log lines equal twoway's (`double_hash.ylabel`) and the tick count equals twoway's.
- **U33-05** `yscale(noextend) yscale(outergap(5))`: `bounds` is the first/last tick in both modes; `min_border_left` grew by the fixture's px.
- **U33-06** `yscale(alt) yscale(alt)`: the y axis is on the side the fixture says.
- **U33-07** (test_option_validation.cscript, appended before `// Summary`): each `refusals.<form>` with rc != 0: `capture dash scatter mpg weight, ylabel(<form>)` rc and error line equal `capture noisily twoway ...`'s in the same run; forms with rc 0 run rc 0 under dash.
- **U33-08** `xline(3000, lwidth(*2))` under the vvthin scheme: dash's Span `line_width` equals `line_px(2 * vvthin_pt)`; `lwidth(20000)` follows the fixture (rc 0 and a note, or twoway's refusal line).

## TDD test stubs

### Regression tests, red at `6370ca4` unless marked guard

`test/test_axis_look_options.py` (D6; helpers `_figs(mode, spec)` as test_axis_options.py builds saved and served figures; fixture read once):
- Test: the fixture exists with five `_meta` keys and every key of the truth table -- `TestTheFixture::test_meta`, `::test_keys` (guard after 33-01).
- Test: `labgap(large)` sets `major_label_standoff` to the fixture's px at dash's reference, both modes -- `TestLabelLook::test_labgap[mode]` (red: unsupported list).
- Test: `labjustification`, `labalignment` set align/baseline; `baseline` is `alphabetic` -- `::test_justification[mode-word]`, `::test_alignment[mode-word]` (red).
- Test: `tlwidth tlcolor tlpattern` set the three `major_tick_line_*`; on `xtick()` the `minor_tick_line_*` -- `TestTickLook::test_major[mode-sub]`, `::test_minor_via_xtick[mode-sub]` (red).
- Test: `glwidth glcolor glpattern` set the Grid's three properties and turn the grid on -- `TestGridLook::test_each[mode-sub]` (red).
- Test: `nogmin nogmax` install a `CustomJSTicker` with `_DASH_GRID_NOEND_JS`; `gmin gmax` leave the ticker (or the inverse, per fixture `grid_ends`) -- `::test_end_lines[mode]` (red); the JS drops the end ticks under node -- `::test_noend_js_drops_ends` (red: constant missing).
- Test: `alternate` adds one axis tagged `dash_alt_axis` on the same side with the complementary parity and `axis_line_color None`; `altgap(large)` sets its standoff -- `TestAlternate::test_twin[mode]`, `::test_altgap[mode]` (red); the formatter code calls `base.doFormat` under node -- `::test_the_formatter_calls_the_base` (red); the twin is excluded by `_dash_primary_axes` and `_dash_finish_count_ticks` -- `::test_the_twin_is_not_finished` (red).
- Test: `##5` on ylabel gives `double_hash == 5`, `mode == "default"`, and the warning text equals the fixture's line (or `#5` if the fixture says so) -- `TestDoubleHash::test_label[mode]`, `::test_tick[mode]` (red).
- Test: `minmax` ticks the two-layer extremes -- `TestMinmax::test_every_layer[mode]` (red: first layer only); `_dash_axis_layer_values` on x, y, range bounds and a date -- `::test_helper_columns` (red: no helper).
- Test: no note is printed for any drawn sub-option -- `TestSilentWhenHonoured::test_no_warning[mode-sub]` (red).
- Test: `_DASH_AXLABEL_HONOURED` names exactly the honoured set and excludes the five style names -- `TestTheHonouredSet::test_members` (red).

`test/test_axis_scale_look.py` (D7):
- Test: `outergap(5)` adds the fixture's px to `min_border_left` (y) / `min_border_bottom` (x) and not under by() -- `TestOutergap::test_each[mode-axis]`, `::test_not_under_by` (red).
- Test: `noextend` sets `bounds` to the first and last tick after the finish; `extend`, `fextend` leave `auto`; log and date axes in their units -- `TestExtend::test_noextend[mode]`, `::test_extend_words[mode]`, `::test_noextend_on_a_log_axis`, `::test_noextend_on_a_date_axis` (red).
- Test: `dash_axis_noextend` under node equals `_dash_finish_count_ticks`'s bounds -- `::test_js_equals_python` (red).
- Test: `lstyle(grid)` sets the axis line colour, width and dash from the scheme's grid style -- `TestLstyle::test_grid[mode]` (red).
- Test: one `alt` moves the axis, two leave it (or per fixture) -- `TestAltParity::test_one`, `::test_two` (red).
- Test: `axis_label_standoff` defaults to the scheme's `axis_title_gap` px -- `TestTitleGap::test_default[mode-scheme]` (red: 5).
- Test: `zlabel(, labsize(small))` and `zscale(alt)` on scatter print what the fixture says -- `TestZLook::test_each[mode]` (red if twoway is silent).
- Test: `fill` follows `scale.fill` -- `TestFill::test_as_twoway` (red or guard per fixture).

`test/test_line_width_edges.py` (E6):
- Test: `translate_lwidth("*2", default_pt=0.1)` is `line_px(0.2)` = 0.4 px, not 0.8 -- `TestFloorAfterMultiply::test_sub_floor_default` (red: 0.8).
- Test: `default_pt` wins over `default_px`; `default_px` alone keeps today's path -- `::test_precedence`, `::test_px_fallback` (red/guard).
- Test: no call site passes `line_px(` or a `.line_width` as `default_px` -- `TestCallSites::test_no_floored_default` (red; reads dash_render.py source).
- Test: `SchemeParser.linewidth_pt("xyline")` under the vvthin scheme file is vvthin's points -- `::test_scheme_points` (red).
- Test: `xline(3000, lwidth(*2))` under the vvthin scheme draws `line_px(2 * vvthin_pt)` in both modes -- `TestDrawn::test_xline_star2[mode]` (red).
- Test: `tlwidth(*2)`, `glwidth(*2)` take the scheme tick/grid points as their default -- `::test_tick_and_grid_defaults[mode]` (red).
- Test: `lwidth(20000)` does what the fixture says -- `TestTheBound::test_as_twoway` (red or guard).

### Cases in cscripts
- `test_wp31_truth.cscript` U33-01..U33-06, U33-08 (red at base); `test_option_validation.cscript` U33-07 (red for the refused forms, guard for rc 0 forms).

### Flips (in place, each with a `Flipped:` line; red at base after the flip)
From `<scratch>/33-flips.txt`: the nodes under Evidence "Tests that pin today's behaviour"; each docstring gains "twoway draws labgap(), alternate, the tick and grid look, outergap(), noextend and lstyle() (WP-31 D6/D7)" or "twoway multiplies a line width before the 0.3 pt floor (WP-31 E6)".

### Parity corpus (R8; guards at base)
TR-33.12's `CORPUS` and `MOVE_CORPUS` entries; `ALLOWED` and `_MUST_WARN` untouched.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Label, tick, grid look | pytest `TestLabelLook`, `TestTickLook`, `TestGridLook`; U33-01 | `labgap.* tl.* gl.*` | yes |
| alternate / altgap | pytest `TestAlternate` (node for the formatter); U33-02 | `alternate.*` | yes |
| nogmin/nogmax, gextend, custom | pytest `TestGridLook::test_end_lines`, node | `grid_ends.* grid_extend.* custom.*` | yes |
| ##N | pytest `TestDoubleHash`; U33-04 | `double_hash.*` | yes |
| minmax over layers | pytest `TestMinmax`; U33-03 | `minmax.two_layers` | yes |
| Refused forms | cscript U33-07 | `refusals.*` | n/a |
| outergap, extend words, lstyle, alt parity, title gap, z look, fill | pytest test_axis_scale_look.py; U33-05, U33-06 | `scale.* scale_alt2.* title_gap.* zlook.*` | yes |
| Width floor, bound, tick/grid widths | pytest test_line_width_edges.py; U33-08 | `lw.*` | yes |
| Parity | `python3 -m pytest test/test_mode_parity.py -q -n0` | -- | yes |

**Acceptance criteria**
- **AC-33.1** Every D6 sub-option but the five style names is drawn in both modes with no note; the properties equal the fixture's values converted at dash's reference within 0.5 px.
- **AC-33.2** `##5` on `ylabel()`/`ytick()` draws twoway's tick count and prints twoway's line verbatim (or nothing).
- **AC-33.3** `ylabel(minmax)` on two layers labels the fixture's two texts.
- **AC-33.4** Every refused form in the fixture is refused by dash with the same rc and first line; every accepted form runs rc 0.
- **AC-33.5** `noextend` bounds, `outergap()` border, `lstyle()` line, the `alt` parity rule, the scheme title gap and the z-look silence match the fixture, both modes, and `dash_axis_noextend` equals the Python under node.
- **AC-33.6** `translate_lwidth("*2", default_pt=0.1)` is 0.4 px; no call site passes a floored default; `lwidth(20000)` matches the fixture.
- **AC-33.7** `WP31_ONLY=S33` prints U33-01..U33-06, U33-08 PASS; test_option_validation.cscript prints U33-07 PASS and ALL CHECKS PASSED; no SKIP.
- **AC-33.8** Three green commits `(WP-31 D6)`, `(WP-31 D7)`, `(WP-31 E6)` on `wp31-s33`.

## Tasks

**Commit boundary.** 33-01 commits nothing. 33-02 makes the D6 commit, subject `Draw the axis label, tick and grid sub-options as twoway draws them (WP-31 D6)`; 33-03 the D7 commit, `Draw the axis-scale look: outergap, noextend, lstyle, alt parity, the scheme title gap (WP-31 D7)`; 33-04 the E6 commit, `Floor line widths after the multiply and draw tick and grid widths (WP-31 E6)`. Each on `wp31-s33` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s33`, after the section's own tests and the cscripts it changed ran green (M9; no full suite). Bodies in BRIEF's forms: the saved failure text, the measured defect, the change, then `Regression:`, `Flipped:` (one per flip), `Fixture: test/fixtures/axis_look_truth.json (scripts/extract_axis_look_truth.do)` (D6 only; D7 and E6 name it as shared), `BUGS.md: "<title>" (closed)`, `GAPS3: <row> Tracked`. No tooling or vendor names.

<task type="auto" id="33-01">
  <name>Measure twoway and write the failing tests</name>
  <files>scripts/extract_axis_look_truth.do, test/fixtures/axis_look_truth.json, test/test_axis_look_options.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals `<scratch>/batch-11-base.txt` and the branch is `wp31-s33`; `mkdir -p <scratch>/s33/x`. Create scripts/extract_axis_look_truth.do by the "Stata truth" table (copy the head of scripts/extract_by_grid_truth.do :1-45; the vvthin scheme is written to the work directory as a copy of /Applications/StataNow/ado/base/s/scheme-s2color.scheme with its `linewidth xyline` line set to vvthin and `#include` removed), run it through the slot, `git add -f test/fixtures/axis_look_truth.json`, and record under `<scratch>/s33/measured.txt` the branch values this file leaves to the fixture: `grid_ends` (D-33.b), `double_hash` (D-33.c), `refusals` (D-33.e), `scale_alt2` (D-33.f), `custom`, `grid_extend`, `scale.fill`, `zlook`, `lw.bound_20000`. Create test/test_axis_look_options.py, test/test_axis_scale_look.py and test/test_line_width_edges.py with exactly the classes of "TDD test stubs", each branching test reading its rule from the fixture. Append ONLY the D6 block (`* ==== S33 D6: Axis label, tick and grid sub-options ====`, U33-01..U33-04) to test/test_wp31_truth.cscript above `* ==== append new blocks above this line ====` and U33-07 to test/test_option_validation.cscript before `// Summary` (the D7 and E6 blocks are appended by 33-03 and 33-04, A14). Re-read S24's U24-5 fixture entry for `##N` on `xlabel()` (D-33.c) and record the branch in `<scratch>/s33/measured.txt`. Run `python3 -m pytest test/test_axis_look_options.py test/test_axis_scale_look.py test/test_line_width_edges.py -q -n0 -p no:cacheprovider -rf > <scratch>/s33/33-01.log 2>&1`, then the two cscripts through the driver (`WP31_ONLY=S33`), and write `<scratch>/33-01-failure.txt`: the base sha, each failing node and FAIL case with its one-line reason, then the guards that passed. Simulate the fix on a scratch copy only far enough to list the pinned nodes that go red, into `<scratch>/33-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/axis_look_truth.json'));print(sorted(d['_meta']))"` prints `['born_date', 'dash_commit', 'extracted', 'source', 'stata_version']`; `grep -c FAILED <scratch>/s33/33-01.log` is at least 40; no FAILED line names `TestTheFixture`; `grep -c "U33-0[1-4] FAIL\|U33-07 FAIL" <scratch>/s33/run_test_wp31_truth.log <scratch>/s33/run_test_option_validation.log` totals at least 4; `grep -c SKIP <scratch>/s33/run_test_wp31_truth.log` prints 0; `test -s <scratch>/33-01-failure.txt`.]]></verify>
  <done>twoway's axis look, refusals and width edges were recorded in a stamped fixture, and every regression test and case was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="33-02">
  <name>Draw the label, tick and grid sub-options</name>
  <files>dash_render.py, dash_parse.mata, dash.ado</files>
  <action><![CDATA[
    In dash_render.py: extend `_DASH_AXLABEL_HONOURED` (:36969) per TR-33.1; `_dash_parse_axis_spec` (:30272) per TR-33.2 (new keys, the `##` group, the `elif` branches after `tposition`); `_dash_apply_axis_spec` (:30426) and `_dash_apply_tick_look` (:30752) per the TR map (labgap after :30619; tl* through `pre + "_tick_line_width"` etc. next to :30812-30815; gl*/gmin/gmax after :30638, the `nogmin`/`nogmax` ticker as `_DASH_GRID_NOEND_JS` beside `_DASH_TICK_EVERY_JS` at :30925); add `_dash_alt_axes` (D-33.a) and `_DASH_ALT_LABEL_JS`, call it from `_dash_apply_axis_options` after `_dash_apply_axis_spec` (:31676-31686); one line in `_dash_primary_axes` excluding `dash_alt_axis`; `_dash_axis_layer_values` (D-33.d) and its use at :31637 when `spec["mode"] == "minmax"`; the `double_hash` warning per the fixture (D-33.c). Copy-list entries: `"_DASH_ALT_LABEL_JS", "_DASH_GRID_NOEND_JS",` after `"_DASH_TICK_EVERY_JS",` (:46653); `"_dash_alt_axes", "_dash_axis_layer_values",` after `"_dash_apply_scale_look",` in the functions tuple. In dash_parse.mata add `_dash_axlabel_refusal` after `_dash_layout_refusal` (:1679) for the fixture's refused forms only, with its header-index line; in dash.ado add the `_needed` entry (alphabetical, :448-479) and the `foreach _ax in xlabel ylabel xtick ytick` check after :6991 (TR-33.6). Add `test/function_test_map.py` entries for the two new functions and `test/program_coverage_map.py` for the Mata one. Flip the D6 nodes of `<scratch>/33-flips.txt` in place. Help (TR-33.11): rewrite the "named in a warning" sentences for these sub-options in Axis and Display Options (:3512-4140), add the `alternate` and `noextend` measured examples' sentences for alternate only here; TWOWAY_COVERAGE_AUDIT.md :137. Close the D6 BUGS.md entry (Resolution per BRIEF, naming `_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_apply_tick_look`, `_dash_alt_axes`, `_dash_axis_layer_values`, `_dash_axlabel_refusal`, both renderers; `Residual, deferred (WP-31): labstyle() tstyle() gstyle() tlstyle() glstyle() stay named until the style-file resolver (section 44) reads them (GAPS3 D6 Tracked)`), open the residual entry `D6b` at the end of BUGS.md (D-33.g's open form), rewrite the D6 Tracked line to the "Partly closed" form naming D6b's title as the open entry (the sha field reads `commit pending`; the merger's step k.3b writes the sha, DECISIONS A11), replace the `<!-- WP-31 D6 -->` markers (a Results line: `ylabel(, labgap(large) tlwidth(thick)) drew the default gap and width with a note, now twoway's`; a Changed-behaviour line naming the refused forms with twoway's words). Run `python3 -m pytest test/test_axis_look_options.py test/test_axis_options.py test/test_subopt_abbrev.py test/test_help_conformance.py test/test_tracking_documents.py test/test_statistical_helpers.py -q -p no:cacheprovider` and the two cscripts through the driver. Stage dash_render.py dash_parse.mata dash.ado dash.sthlp TWOWAY_COVERAGE_AUDIT.md BUGS.md CHANGELOG.md GAPS3.md scripts/extract_axis_look_truth.do test/test_axis_look_options.py test/test_wp31_truth.cscript test/test_option_validation.cscript test/function_test_map.py test/program_coverage_map.py the flipped D6 test files and `git add -f test/fixtures/axis_look_truth.json`; NOT test_axis_scale_look.py or test_line_width_edges.py. Commit with the D6 subject and body; grep the message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[That pytest run reports 0 failed; `WP31_ONLY=S33` driver log shows `U33-01 PASS` through `U33-04 PASS` and no SKIP; test_option_validation.cscript log shows `U33-07 PASS` and `ALL CHECKS PASSED`; `git log -1 --format=%s` ends `(WP-31 D6)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D6 -->' CHANGELOG.md` prints 0; `git show --stat HEAD | grep -c "test_axis_scale_look\|test_line_width_edges"` prints 0.]]></verify>
  <done>The label, tick and grid sub-options, alternate, the ##N rule, minmax over every layer and twoway's refused forms were drawn or refused in both renderers, their pins flipped, and D6 was committed as one green commit.</done>
</task>

<task type="auto" id="33-03">
  <name>Draw the axis-scale look</name>
  <files>dash_render.py, scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    (The help, TWOWAY_COVERAGE_AUDIT.md, test/test_axis_scale_look.py's flips, the cscript block and the tracking documents are implied edits of this closing task, DECISIONS A13.) Re-run `python3 -m pytest test/test_axis_scale_look.py -q -n0 -p no:cacheprovider -rf > <scratch>/s33/33-03-red.log 2>&1` on the D6 tree (expect red) and append its text to `<scratch>/33-01-failure.txt` under a `D7` heading. In dash_render.py: `_DASH_SCALE_LOOK_SUBOPTS` (:31980) per TR-33.7; `_dash_scale_look` (:38584) returns `outergap`, `extend`, `lstyle` and the parity `alternate` (D-33.f, per the fixture's `scale_alt2`); `_dash_apply_scale_look` (:30816) draws `outergap` (D-33.h: `fig.min_border_left = (fig.min_border_left if fig.min_border_left is not None else fig.min_border) + px`, or `min_border_bottom` for x -- Bokeh's property is `min_border_bottom`, `min_border_below` does not exist and raises; the other side under alt, nothing under by()), `lstyle` (the scheme line bundle), and sets `fig._dash_noextend` (D-33.i); `_dash_finish_count_ticks` (:33346) sets `bounds` for tagged axes and `"auto"` otherwise; `_dash_axis_plan` (:32310) writes `"noextend": 1` per axis entry; `_DASH_AXIS_FINISH_JS` gains `dash_axis_noextend` before `function dash_axis_same` and its call in `dash_axis_finish` after the ticker write; `SchemeParser.axis_title_gap` (default `minuscule`) and its use in `_dash_apply_axis_options` (TR-33.8); the `gsize axis_title_gap` stub through scripts/extract_scheme_truth.py (truth entry beside the tick gsizes, directive `scalar("gsize", "axis_title_gap", "axis_title_gap")`; run `scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` twice; `git add -f test/fixtures/scheme_truth.json` and the regenerated `dash-*.scheme`); the twin-axis label geometry measured first (D-33.a: export both modes once, measure the two label rows' y delta against `alternate.default`, set the standoff rule, record the numbers in `<scratch>/s33/measured.txt`); `zlabel()/zscale()` look words per the fixture `zlook` (TR-33.9); `fill` per `scale.fill`. Flip the D7 nodes of `<scratch>/33-flips.txt`. Help: the xscale()/yscale() paragraph (Axis and Display Options; the sentence at :3650-3700 region found by `grep -n "outergap" dash.sthlp`) says outergap(), noextend, extend, fextend and lstyle() are drawn, with the measured `noextend` example (axis line from the first to the last tick; twoway's `fextend` and `extend` coincide in dash because the frame includes the margin) and the two-`alt` rule; TWOWAY_COVERAGE_AUDIT.md :137 gains `xscale()/yscale() look`. Append the D7 truth block (`* ==== S33 D7: Axis-scale look ====`, U33-05, U33-06) above the marker line and run it through the driver. Close the D7 BUGS.md entry, rewrite its Tracked line to the Closed form ending `commit pending.` (A11), replace `<!-- WP-31 D7 -->` (Results: `yscale(alt) yscale(alt)` old side -> twoway's; `yscale(noextend)` drew the full line, now first to last tick). Run `python3 -m pytest test/test_axis_scale_look.py test/test_axis_look_options.py test/test_axis_options.py test/test_refline_extent.py test/test_saved_axis_finish.py test/test_tracking_documents.py test/test_statistical_helpers.py -q -p no:cacheprovider` (the finish-JS tests are whichever files `grep -l dash_axis_finish test/*.py` lists) and the truth block through the driver. Stage dash_render.py, scripts/extract_scheme_truth.py, the regenerated dash-*.scheme files, `git add -f test/fixtures/scheme_truth.json`, dash.sthlp, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, CHANGELOG.md, GAPS3.md, test/test_axis_scale_look.py, test/test_wp31_truth.cscript, test/function_test_map.py, the flipped D7 files; commit with the D7 subject; grep the message.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; the driver log shows `U33-05 PASS` and `U33-06 PASS`, no SKIP; `grep -c "gsize axis_title_gap" dash-s2color.scheme` prints 1 and `grep -c axis_title_gap scripts/extract_scheme_truth.py` is at least 2 and `python3 -c "import json;print('axis_title_gap' in json.load(open('test/fixtures/scheme_truth.json'))['s2color'])"` prints True (the fixture's per-scheme key as the file lays it out); `git -C . status --porcelain dash-*.scheme` is empty after a second generator run; `grep -c "D7 Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 D7)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D7 -->' CHANGELOG.md` prints 0.]]></verify>
  <done>outergap(), noextend, lstyle(), the alt parity, the scheme title gap and the z-look silence were drawn in both renderers with the saved page's finisher twin, and D7 was committed green.</done>
</task>

<task type="auto" id="33-04">
  <name>Floor widths after the multiply</name>
  <files>dash_render.py, test/test_line_width_edges.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Re-run `python3 -m pytest test/test_line_width_edges.py -q -n0 -p no:cacheprovider -rf > <scratch>/s33/33-04-red.log 2>&1` on the D7 tree and append its text to `<scratch>/33-01-failure.txt` under `E6`. In dash_render.py: `translate_lwidth(value, default_px=None, ref_in=4.0, default_pt=None)` (:7602; D-33.j: `default_pt` wins, else today's `d * 0.75`, else medium); `SchemeParser.linewidth_pt(role)` after `default_marker_size`; for every site `grep -n "translate_lwidth(" dash_render.py` lists whose default argument is a `line_px(...)` result or a renderer's `line_width`, pass `default_pt=self.scheme.linewidth_pt("<role>")` (the role the site's comment or default names; `xyline` for reference lines, `p#` for series lines, `axisline` for the axis, `tick`/`major_grid` for 33-02's tick and grid widths) and record each site, old and new, in `<scratch>/s33/33-04-sites.txt`; the 10,000-unit bound per the fixture `lw.bound_20000` (TR-33.10). Flip the E6 nodes of `<scratch>/33-flips.txt`. Append TR-33.12's parity entries under `# WP-31 D6/D7/E6`. Help: the lwidth() sentence in Marker and Transparency Options (`grep -n "0.3 pt" dash.sthlp`) says `*#` multiplies the default before the floor; TWOWAY_COVERAGE_AUDIT.md unchanged. Append the E6 truth block (`* ==== S33 E6: Line-width edges ====`, U33-08) above the marker line and run it through the driver. Close the E6 BUGS.md entry, rewrite its Tracked line to the Closed form ending `commit pending.` (A11), replace `<!-- WP-31 E6 -->` (Results: `xline(3000, lwidth(*2))` under a vvthin xyline drew 0.8 px, now the fixture's value). Run `python3 -m pytest test/test_line_width_edges.py test/test_axis_look_options.py test/test_option_sizes.py test/test_reference_lines.py test/test_mode_parity.py test/test_tracking_documents.py -q -p no:cacheprovider` (plus every file `grep -l translate_lwidth test/*.py` lists) and the truth block through the driver. Stage dash_render.py dash.sthlp BUGS.md CHANGELOG.md GAPS3.md test/test_line_width_edges.py test/test_wp31_truth.cscript test/test_mode_parity.py test/function_test_map.py and the flipped E6 files; commit with the E6 subject; grep the message. Write `<scratch>/s33/handback.txt`: the three shas, the measured `lw.bound_20000` rc and line for S32's rules token (A15), the twin-axis standoff numbers, and D6b for S44/S61.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; the driver log shows `U33-08 PASS`, no SKIP; `python3 -c "from dash_render import OptionTranslator as T;print(T.translate_lwidth('*2', default_pt=0.1))"` prints 0.4; `grep -c "line_px(" <(grep "translate_lwidth(" dash_render.py)` prints 0; `grep -c "E6 Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 E6)`; `git log -3 --format=%s | grep -c "(WP-31 D6)\|(WP-31 D7)\|(WP-31 E6)"` prints 3; `git log -3 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 E6 -->' CHANGELOG.md` prints 0.]]></verify>
  <done>Line widths were floored once after the multiply at every call site, tick and grid widths followed the rule, the bound followed the measurement, and E6 was committed green as the section's third commit.</done>
</task>

## Section completion criteria

- Every D6 sub-option but the five style names is drawn in both modes without a note; `alternate` is the tagged twin axis; `##N`, `minmax` and the refused forms follow the fixture.
- `outergap()`, `noextend`/`extend`/`fextend`, `lstyle()`, the `alt` parity, the scheme's `axis_title_gap` and the z-look silence follow the fixture in both modes; the saved finisher's `dash_axis_noextend` equals the Python.
- `translate_lwidth` floors after the multiply at every site; `tlwidth()/glwidth()` drawn; the bound follows the fixture.
- `axis_look_truth.json` stamped and named by three test files; U33-01..U33-08 PASS through the driver; every flip recorded with its reason.
- Three green commits on `wp31-s33`; three BUGS.md entries closed (D6 with its residual); three Tracked lines rewritten (D6 "Partly closed" naming D6b, the others `commit pending`); the residual entry D6b open; three truth blocks (one per row); three markers replaced; help, audit and both maps updated.

## Notes

- **S24's code is the base.** `_dash_parse_axis_spec` and `_DASH_AXIS_FINISH_JS` were edited by S24 in batch 8; re-read them before 33-02 and 33-03. Edit only the `xlabel/ylabel/xtick/ytick` reading of `##` and add `dash_axis_noextend` as a new function; never move S24's LabelSet code.
- **The twin axis and the finishers.** `_dash_finish_count_ticks`, `_dash_common_count_ticks`, `_dash_axis_alternate` and S35's `_dash_finish_secondary_axes` iterate side lists; each must skip `dash_alt_axis`. The one-line `_dash_primary_axes` exclusion covers the first three; S35 (batch 12) is told in its Notes to test the tag.
- **CustomJS code is constant text.** `_DASH_ALT_LABEL_JS` and `_DASH_GRID_NOEND_JS` hold no user text; parities, drop flags and the base ticker/formatter travel in `args`. The CSP tests (test_csp.py) are unaffected: Bokeh model callbacks are not inline scripts.
- **Copy lists (R2).** Two constants after `"_DASH_TICK_EVERY_JS",`; two functions after `"_dash_apply_scale_look",`; `SchemeParser` and `OptionTranslator` methods travel with their classes. `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` is the guard.
- **python_exec hazard** (project memory): check `~/.stata19/console/stata19.rc` after each cscript run; a SKIP is not a pass.
- **Shared files.** R1: the U33 block only, U33-07 in test_option_validation.cscript before `// Summary`; R3: Axis and Display Options and the lwidth sentence only; R4: three markers replaced; R5: three entries, three Tracked lines; R6: one Mata function, one `_needed` entry, one check in `_dash_validate_opts`; R7: one extractor, `git add -f`; R8: corpus appended; R9: flips in place; R10: no declared count moves (sub-options are not pending-list entries); R11: S33 is batch 11's finisher editor; R12: S33 edits no `_apply_*` applier (tick and grid widths are set in the axis appliers, not the glyph appliers), not `_make_figure_body`, not `_FILTER_JS`.
- **Commit-body line forms** are BRIEF's; `failed at` is `batch-11-base.txt`'s sha for D6, the D6 sha for D7, the D7 sha for E6.
- **For S35 (batch 12).** `ylabel2()/xlabel2()` take the same `_dash_parse_axis_spec` keys; S35 applies them to the second axis through `_dash_apply_axis_spec` unchanged. The twin axis of `alternate` on axis 2 is S35's.
- **For S44 (batch 15).** The five style names are the recorded D6 residual: once `textstyle-*.style`, `tickstyle-*.style`, `gridstyle-*.style` and `linestyle-*.style` are read, `labstyle tstyle gstyle tlstyle glstyle` join `_DASH_AXLABEL_HONOURED` and the D6 Tracked line becomes Closed.
- **Decisions for maintainer ratification.** D-33.a (two axes for `alternate`), D-33.b (end grid lines by a CustomJSTicker), D-33.g (style names deferred to S44 through the open residual D6b -- S44's D-44c must gain textstyle/tickstyle/gridstyle or S61 files D6b under M12), D-33.i (`extend`/`fextend` coincide in Bokeh; documented difference under M17), the ordering of three commits from one 33-01 (three test files so no commit is red).
