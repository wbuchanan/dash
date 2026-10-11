# Section 31: Legend geometry and keys

> Part of: WP-31 · GAPS3 rows: D4, C13 · Risk: yellow · Batch: 10 · Depends on: 01 · Blocks: 39 · Tasks: 4, 2 commits · Case-id prefix: U31

## Overview

**What is wrong today.** GAPS3 D4 (GAPS3.md:154): "Legend: `holes colfirst textfirst stack symxsize symysize symplacement keygap rowgap colgap textwidth forcesize region() bplacement() span title() subtitle() note() caption() bmargin() nobox color()` named; scheme `cols` dropped when `position()` given; corner clocks centred on a side; `pos(0)` goes top-right; `ring(0)` alone leaves Bokeh's top_right (help promises "inside the plot region"); `legend(label(1))` with no text dropped silently; key size fixed; keys with the same text and style not merged." Evidence `dash_render.py:37094, :37105, :28394-28425, :28059-28063, :28325-28327, :28514`. GAPS3 C13 (:132): "histogram-only graph draws a legend; twoway draws none." Evidence `:28514`. At `6370ca4` `_DASH_LEGEND_SUBOPTS` (:37094-37096) is `on off position ring order label lastlabel cols rows size`; `_dash_legend_unsupported` (:37105-37112) names every other token; placement (:28394-28425) moves the legend to `_DASH_CLOCK_SIDE[clock]` with `location="center"` (`_dash_move_legend`, :28200), reads the scheme's `legend_cols` only `if not placed and not m_ring` (:28410), does nothing for `ring(0)` without `position()`, and sends `pos(0)` to `_DASH_CLOCK_SIDE.get(0, "right")`; `_DASH_LEGEND_LABEL_RE` (:37103) needs a blank after the number so `label(1)` matches nothing; `_dash_legend_keys` (:39925) makes one key per layer, never merging two with the same text; the show rule (:28514) counts keys with no type exemption.

**After this section** both modes draw the legend as twoway's `legend_g` lays it out where Bokeh's `Legend` can express it: `symxsize()`/`symysize()` -> `glyph_width`/`glyph_height` (scheme defaults 13 units / medsmall), `keygap()` -> `label_standoff` (vsmall), `rowgap()` -> `spacing` (tiny), `region(margin())`/`bmargin()` -> `padding`/`margin` (small/small), `region(lcolor() fcolor() lwidth() lpattern())` and `nobox` -> the border and fill, `color()` -> `label_text_color`, `textwidth()` -> `label_width`, `title()` -> `title`, `holes()` -> blank `LegendItem`s, `colfirst` -> the items permuted so Bokeh's row-first grid shows twoway's column-first order, `bplacement()` -> `location` within the side panel, `span` and `forcesize` -> honoured no-ops (a side-panel legend already spans; Bokeh's keys are always the fixed size). The clock table gains corners (1 and 11 at the ends of the top panel, 2/4 at the ends of the right panel, 5/7 of the bottom, 8/10 of the left), `position(0)` is the centre of the plot region, and `ring(0)` alone is inside at the scheme's clock (s2color 6 -> `bottom_center`); the scheme's `cols` stays when `position()` is given. `label(#)` with no text blanks key #; two keys with the same text and the same style are drawn once; a graph of histograms only draws no legend. `textfirst`, `stacked`, `symplacement()`, `colgap()`, `subtitle()`, `note()`, `caption()` on the legend are documented as not expressible (M17; research/bokeh-web.md §4 "text-first NOT feasible") and stay named. The ten legend stubs twoway's scheme carries are added to every shipped scheme.

**Why two rows share this section.** C13 is one clause of the same show rule D4's `label(#)` and merge rules edit (:28514); they share `_dash_apply_legend` and `_dash_legend_keys`.

**Test order and commit rule (BRIEF).** Two cycles, two commits: D4 (31-01 red tests and fixture; 31-02 the geometry and clock fix; 31-03 certify, flip, document, commit `(WP-31 D4)`), then C13 (31-04: creates `test/test_legend_histogram_only.py` -- one regression test file per row, DECISIONS A14 -- runs it red, the histogram exemption, U31 case, commit `(WP-31 C13)`). No `pytest.mark` row device.

### Section decisions (this file; binding on the executor)

- **D-31.a Sizes are Stata sizes through `OptionTranslator.resolve_size`** with kind `"text"` (the gsize ladder: medsmall 3.4722, vsmall 2.0833, tiny 1.3888, small, large 4.8611; a bare number is Stata's relative unit, 2.88 pt at the 4-inch reference) and `OptionTranslator.size_ref_of(fig)`, converted to whole pixels by `int(round(pt * 96 / 72))` -- Bokeh's `glyph_width`, `glyph_height`, `label_standoff`, `spacing`, `padding`, `margin` are `Int`. Defaults come from the new scheme attributes (TR-31.3): symxsize 13 -> 50 px, symysize medsmall -> 13 px, keygap vsmall -> 8 px, rowgap tiny -> 5 px, `margin legend small` -> `padding`, `margin legend_boxmargin small` -> `margin`, each the scheme's `gsize <x>margin` ladder value through the margin ladder `_dash_added_text_opts` uses (:37460-37470).
- **D-31.b Clock table.** For ring > 0: `_DASH_CLOCK_SIDE` is kept; a new `_DASH_CLOCK_PANEL_LOCATION = {11: "top_left", 12: "center", 1: "top_right", 2: "top_right", 3: "center", 4: "bottom_right", 5: "bottom_right", 6: "center", 7: "bottom_left", 8: "bottom_left", 9: "center", 10: "top_left"}` gives the `location` inside the side panel (`_dash_move_legend` gains a `location` argument, default `"center"`); `bplacement(compass)` overrides it (`n/ne/e/se/s/sw/w/nw/c` -> `top_center/top_right/center_right/bottom_right/bottom_center/bottom_left/center_left/top_left/center`). `position(0)` -> inside, `location="center"` (the plot region's centre, title_options.sthlp remarks3 :75-78), `_DASH_CLOCK_INSIDE[0] = "center"`. `ring(0)` without `position()` -> inside at `_DASH_CLOCK_INSIDE[scheme clock]` (s2color 6 -> `bottom_center`, `_fr_legend_parse_and_log.ado:86-91, 111-114`). The scheme's `cols`/`rows` apply whenever the user gave neither `cols()` nor `rows()`, position or not (`legend_g.class:274-285`: "if neither > 0 then cols = 2").
- **D-31.c Holes and the rows/cols rule.** `holes(numlist)` inserts `LegendItem(label={"value": ""}, renderers=[])` at the listed 1-based positions (counted in the final sequence, after order()/lastlabel(); twoway counts holes among n, `legend_g.class:274-285`); `n = keys + holes`; rows given -> `cols = 1 + int((n-1)/rows)`, cols given -> `rows = 1 + int((n-1)/cols)`, neither -> scheme cols (2); the pair is set as `ncols`/`nrows` (both; Bokeh takes both as given). `colfirst`: items are permuted so that index `k` (0-based) of twoway's column-first order appears at row-major index `(k mod rows) * cols + (k div rows)`, holes padding the last column; `nocolfirst` is the default.
- **D-31.d Merge rule.** Two keys whose text and style (the renderer's glyph properties: marker, colours, line width, dash, fill alpha, size -- the `_dash_key_signature` of TR-31.6) are equal are one `LegendItem` holding both renderer lists, numbered by the first; `order()`/`label()` numbers keep referring to twoway's plot numbers (the merged key answers to both). Measured first (U31-6): twoway's `legend_g` merges when label and style agree; the fixture's result is the rule.
- **D-31.e `label(#)` with no text** blanks the key (text `""`), measured in U31-5; if twoway instead refuses it, dash.ado refuses with the same words and the renderer rule is not added (the fixture decides).
- **D-31.f Histogram-only graphs draw no legend** unless `legend(on)`: the show rule (:28514) gains `and not _hist_only` where `_hist_only` is "every layer's type is `histogram`" (measured in U31-9: `twoway histogram mpg || histogram price` draws no legend). `legend(on)` still forces one.

## Risk: [yellow] -- every legend of every dashboard changes size and position

**Why.** `_dash_apply_legend` and `_dash_move_legend` are the one legend path for both modes and the by() cell copies `glyph_width`/`glyph_height`/`spacing`/`padding`/`label_standoff` (:38088-38093), so every multi-key graph and every by() grid re-lays its legend.

**Risk factors.** 1. Pinned legend positions and sizes across many files (`_DASH_CLOCK_INSIDE`, `location == "center"`, `ncols` assertions). 2. The merge rule changes key numbering seen by `order()`/`label()`. 3. The colorvar colour key (`_COLORVAR_LEGEND_NAME`) must stay untouched. 4. S30 (same batch) inserts text boxes by ring; `_dash_move_legend` must keep S27's `dash_edge_title` skip. 5. The by() cell's `Legend` copy must take the new props.

**Mitigation.** 1. 31-01's measured red list; flips with reasons (R9). 2. `TestMergeKeepsNumbers` pins `order(2 1)` and `label(2 "x")` on a merged graph against the fixture. 3. `TestColourKeyUntouched` (guard). 4. TR-31.5 keeps the skip; S30 Boundaries. 5. The prop list at :38088-38093 already copies the five props; `TestByCellLegend` checks them.

## Dependencies

- **Depends on: 01.** Markers `<!-- WP-31 D4 -->` (Results) and `<!-- WP-31 C13 -->` (Results); BUGS entries; truth script.
- **Blocks: 39** (tabs-layout-legend-edges, batch 13): S39's legend label edges read the merged keys and the holes.
- **Parallel batch: 10**, merge order S29, S30, S31. **Can run with S29 and S30**: S29 edits `_FILTER_JS`; S30 edits `_dash_textbox*`, `_dash_text_annotations`, `_dash_figure_title`, `_dash_added_text*`, `_dash_at_*`; S31 edits none of those. Both S30 and S31 edit scripts/extract_scheme_truth.py and regenerate the schemes, in disjoint hunks (DECISIONS A31): S31 owns the legend group `Marker size and legend placement.` (:2221-2225; `gridringstyle legend_ring 3` included) and the ten truth entries after `legend_rows` (:1921); S30 adds a new group `Textbox rings.` after it and four entries before `legend_position` (:1914). Merger rule (index.md:145): S29 and S30 applied whole; S31's diff produced with `git -C <wt> diff -- . ':(exclude)dash-*.scheme' ':(exclude)test/fixtures/scheme_truth.json'`, applied, then the generator run once after the batch-10 merge (`scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`, twice, `git add -f`).

## Evidence

All anchors at `6370ca4`.

### The honoured set and the placement (dash_render.py)

```python
37094 _DASH_LEGEND_SUBOPTS = frozenset({
37095     "on", "off", "position", "ring", "order", "label", "lastlabel",
37096     "cols", "rows", "size"})
37103 _DASH_LEGEND_LABEL_RE = re.compile(r"\s*\+?(\d{1,6})(\s.*)", re.S)
28392     m_pos = _dash_legend_arg(_calls, ("position",), r"([0-9]|1[0-2])")
28393     m_ring = _dash_legend_arg(_calls, ("ring",), r"(\d+)")
28394     inside = bool(m_ring) and m_ring.group(1) == "0"
28397         if m_pos:
28400             if inside:
28401                 legend.location = _DASH_CLOCK_INSIDE.get(clock, "top_right")
28402             else:
28403                 side = _DASH_CLOCK_SIDE.get(clock, "right")
28404                 _dash_move_legend(fig, legend, side)
28410         if not placed and not m_ring and chrome.get("legend_position"):
28423                 if cols > 0 and (horizontal or cols > 1):
28424                     legend.ncols = cols
28514     show = not (turned_off or (n_keys < 2 and not forced_on))
```
`_DASH_CLOCK_SIDE`/`_DASH_CLOCK_INSIDE` (:28059-28071) have no 0 entry. `_dash_move_legend` (:28179-28200) inserts after the axes and sets `location = "center"`. `_dash_scheme_chrome` (:28217-28232) returns `legend_bg_color`, `legend_border_color`, `label_text_font_size`, `label_text_color`, `legend_position`, `legend_cols`, `legend_rows`. The by() cell copies `orientation ncols nrows label_text_* background_* border_* glyph_width glyph_height spacing padding label_standoff title title_text_*` (:38088-38093). `SchemeParser.legend_position`/`legend_cols`/`legend_rows` (:10675-10684). The legend sub-option table (:36839-36876) already names every twoway sub-option by stage, so no parser work is needed: `_dash_legend_parts`/`_dash_legend_arg` (:28080, :28110) read them.

### Stata's rule (research/stata-ground-truth.md §7)

Scheme: `numstyle legend_rows 0`/`legend_cols 2`; `gsize key_label medsmall`, `legend_key_xsize 13`, `legend_key_ysize medsmall`, `legend_key_gap vsmall`, `legend_row_gap tiny`, `legend_col_gap large`; `clockdir legend_position 6`; `gridringstyle legend_ring 3`; `color legend white`, `legend_line black`; `margin legend small`, `legend_key_region tiny`, `legend_boxmargin small`; `compass2dir legend_fillpos center`; `yesno legend_col_first/text_first/stacked/force_keysz/span no` (lines in the table at §7). Rows/cols rule and placement programs `legend_g.class:274-302`; `ring(0)` -> "on plotregion1" with `box_alignment = legend_position.compass2style` (`_fr_legend_parse_and_log.ado:86-91, 111-114, 126-129`); clock -> compass (1 NE .. 12 N, 0 center; `clockdir.class:14-15, 78-84`); `span` -> spancols/spanrows, ignored in ring 0; `bplacement()` -> box_alignment (:324-326); `label(# "text")` needs an integer (:350-359). dash-s2color.scheme has `color legend`/`legend_line` (:38-39), `gsize key_label` (:172), `clockdir legend_position 6` (:101), `numstyle legend_cols 2` (:102), `legend_rows 0` (:179), none of the ten others (research §11 "Absent").

### Bokeh (research/bokeh-web.md §4)

`glyph_width/height: Int`, `label_standoff: Int`, `spacing: Int`, `padding: Int | (x,y) | (l,r,t,b)`, `margin: Int`, `ncols/nrows: Positive Int | 'auto'`, `location: Enum | (Float, Float)`, `border_line_*`, `background_fill_*`, `title`, `title_location`, `label_width/label_height`, `label_text_align`; `LegendItem(label="", renderers=[])` constructs as a hole (verified again under 3.9.0 for this file); text-first and stacked are not expressible (the item element is `glyph_el, label_el` with no property to swap and no `stylesheets` prop).

### Fixtures on disk

`test/fixtures/text_truth.json` (`l_lastlabel_*`, `l_order_beats_label`, `l_one_dash`) and `test/fixtures/axis_truth.json` (`c_order1`) hold key-order truth and are read, not rewritten; `test/fixtures/key_text_truth.json` the key texts.

### Tests that pin today's behaviour (flip, never delete)

- test_axis_options.py::TestLegendRule (:313) and ::TestLegendOptions (:355): nodes asserting `location == "top_right"` for `ring(0)`, `location == "center"` for corner clocks, `ncols` dropped with `position()`, or the show rule on histogram graphs.
- test_graph_options.py::TestLegend (:247), ::TestLegendLabels (:476): nodes asserting `label(1)` is ignored or two same-text keys.
- test_legend_order.py::TestKeysAreNumberedByPlot (:309): unchanged unless it pins unmerged duplicates.
- test_by_grid.py (legend in the by() cell) and test_scheme_chrome.py::TestTheChromeKeysAreRead (:383, gains the ten stubs).
- test_subopt_abbrev.py::TestLegendAbbreviations (:291) / ::TestLegendInOneCopy (:329): nodes asserting a token is "unsupported" flip for the newly honoured names.
- test_help_claims_*.cscript cases pinning `legend(holes(...))` or `legend(symxsize())` as named flip in the area script.

## User stories

- US-31.1 As a Stata analyst, I want `legend(ring(0))` inside the plot region at the bottom, `legend(pos(1))` at the top right and `legend(pos(0))` in the centre, as twoway places them.
- US-31.2 As a Stata analyst, I want `legend(symxsize(5) keygap(1) rowgap(2) region(lcolor(none)))` to resize the keys and remove the box.
- US-31.3 As a Stata analyst, I want `legend(holes(2) cols(2))` and `legend(colfirst)` to lay the keys out as twoway does.
- US-31.4 As a Stata analyst, I want two identical series to share one key, `label(2)` to blank a key, and a histogram-only graph to carry no legend, as in twoway.

## Business requirements

- BR-31.1 The sub-options of the "After this section" list are drawn in both modes with nothing printed; the four not expressible are named and documented with a measured example.
- BR-31.2 Default key geometry equals the scheme's (symxsize 13, symysize medsmall, keygap vsmall, rowgap tiny, margins small).
- BR-31.3 Corner clocks sit at the ends of their side; `position(0)` is the centre; `ring(0)` alone is inside at the scheme's clock; the scheme's columns survive `position()`.
- BR-31.4 Holes, rows/cols arithmetic, colfirst, merge and `label(#)` follow the measured twoway rules.
- BR-31.5 A histogram-only graph draws no legend unless `legend(on)`.

## Technical requirements

- TR-31.1 **Honoured set.** `_DASH_LEGEND_SUBOPTS` (:37094) gains `"holes", "colfirst", "nocolfirst", "title", "region", "bplacement", "span", "nospan", "symxsize", "symysize", "keygap", "rowgap", "textwidth", "forcesize", "noforcesize", "nobox", "box", "color", "bmargin", "bexpand", "nobexpand"`; `textfirst`, `notextfirst`, `stacked`, `nostacked`, `symplacement`, `colgap`, `subtitle`, `note`, `caption`, `width`, `height` stay named.
- TR-31.2 **Clock tables.** `_DASH_CLOCK_INSIDE[0] = "center"`; new `_DASH_CLOCK_PANEL_LOCATION` (D-31.b) and `_DASH_BPLACEMENT_LOCATION` (compass -> location) after `_DASH_CLOCK_INSIDE` (:28071). `_dash_move_legend(fig, legend, side, location="center")` sets `legend.location = location` and keeps the S27 skip (`not isinstance(m, Axis) and "dash_edge_title" not in (getattr(m, "tags", None) or [])`); the insertion index ALSO skips every model whose tags hold `ring=<n>` with `n <= chrome.get("legend_ring", 3)` (S30's `_dash_textbox_insert` tags each box `ring=<n>`; a user `ring(1)`/`ring(2)` box must sit inside the legend -- R3c-F8, DECISIONS A31), i.e. the legend goes after the last axis, `dash_edge_title` or low-ring model of the panel.
- TR-31.3 **SchemeParser.** After `legend_rows` (:10684): `self.legend_key_xsize = self._gsize_units("gsize legend_key_xsize", 13.0)`, `self.legend_key_ysize = self._gsize_units("gsize legend_key_ysize", "medsmall")`, `self.legend_key_gap = ... ("gsize legend_key_gap", "vsmall")`, `self.legend_row_gap = ... ("gsize legend_row_gap", "tiny")`, `self.legend_col_gap = ... ("gsize legend_col_gap", "large")` (read, documented, not drawn), `self.legend_margin = self._margin_px("margin legend", "small")`, `self.legend_boxmargin = self._margin_px("margin legend_boxmargin", "small")`, `self.legend_ring = self._bounded_int("gridringstyle legend_ring", 3, 0, 9, "ring")`, `self.legend_col_first = self._yesno("yesno legend_col_first", False)`, `self.legend_span = self._yesno("yesno legend_span", False)`. `_gsize_units(key, default)` returns the value in Stata units (a gsize name through the ladder `OptionTranslator` carries, a bare number as is); `_margin_px` uses the margin ladder. `_dash_scheme_chrome` (:28217) adds the keys `legend_key_xsize`, `legend_key_ysize`, `legend_key_gap`, `legend_row_gap`, `legend_margin`, `legend_boxmargin`, `legend_col_first` to its dict (both modes pass the dict).
- TR-31.4 **Geometry in `_dash_apply_legend`.** New step 3b after the chrome loop (:28367-28380): for every plot legend, `lg.glyph_width = px(chrome["legend_key_xsize"])`, `lg.glyph_height = px(chrome["legend_key_ysize"])`, `lg.label_standoff = px(chrome["legend_key_gap"])`, `lg.spacing = px(chrome["legend_row_gap"])`, `lg.padding = chrome["legend_margin"]`, `lg.margin = chrome["legend_boxmargin"]`, where `px(units) = int(round(units * 2.88 * 96 / 72 * ref_in / 4.0))` with `ref_in = OptionTranslator.size_ref_of(fig)`; then the user's `symxsize()`, `symysize()`, `keygap()`, `rowgap()` through `T.resolve_size(arg, "text", default_pt, ref_in)` -> px (ValueError -> `_dash_style_note("legend(<typed>)", arg, "size", "the scheme's default")`, the step-7 pattern :28470-28490); `textwidth(#)` -> `label_width = px`; `region(...)`: parse its argument with `_parse_textbox_opt('"", ' + arg)` and set `border_line_color` (lcolor), `background_fill_color` (fcolor/color inside region), `border_line_width` (lwidth, `resolve_size(.., "line", ..)`), `border_line_dash` (lpattern via the reference lines' pattern translator), `padding` (margin ladder); `nobox` -> `border_line_color=None, background_fill_color=None`; `box` -> the scheme's box; `color(c)` -> `label_text_color` through `_textbox_color`; `title(text)` -> `lg.title = _textbox_lines(...)` joined with "\n", `title_location="above"` (twoway's leg_title is above); `bmargin(...)` -> `margin`; `span`/`nospan`, `forcesize`/`noforcesize`, `bexpand`/`nobexpand` consumed as no-ops.
- TR-31.5 **Placement rewrite** (:28394-28425): `clock = int(m_pos.group(1)) if m_pos else chrome.get("legend_position")`; `ring = int(m_ring.group(1)) if m_ring else chrome.get("legend_ring", 3)`; if `m_pos and clock == 0`: inside, `location="center"`; elif `ring == 0`: inside, `location = _DASH_CLOCK_INSIDE.get(clock, "bottom_center")`; else: `side = _DASH_CLOCK_SIDE.get(clock, "below")`, `loc = _DASH_BPLACEMENT_LOCATION[bplacement] if bplacement else _DASH_CLOCK_PANEL_LOCATION[clock]`, `_dash_move_legend(fig, legend, side, loc)`, orientation horizontal for above/below. Then rows/cols (D-31.c) replace step 6 (:28434-28465): `n = len(legend.items) + len(holes)`; `rows()`/`cols()` through the existing `_one_count`; neither -> `cols = chrome["legend_cols"] or 2`, `rows = 1 + (n-1)//cols`; both set on every plot legend as `ncols`/`nrows` (a side legend keeps `ncols=1` only when the scheme's cols is 1; the "cols > 1" clause at :28423 is deleted: Stata's rule has no such clause, measured U31-3).
- TR-31.6 **Keys.** `_dash_legend_keys` (:39925) gains the merge: after the loop, keys with equal `(text, _dash_key_signature(renderers))` are folded into the first (`renderers` concatenated; the folded numbers recorded in `item.tags = ["dash_key_numbers", "1", "3"]` so `order()`/`label()` resolve both numbers to the one item in step 1-2 (:28310-28360: `texts`/`items_by_n` map every folded number to the same `LegendItem`). New module function `_dash_key_signature(renderers) -> tuple` after `_dash_legend_key` (:39924): for each renderer the glyph class name and the values of `line_color, line_width, line_dash, fill_color, fill_alpha, line_alpha, marker, size` when present (a field spec -> its field name). `label(#)` with no text: `_DASH_LEGEND_LABEL_RE` becomes `r"\s*\+?(\d{1,6})(\s.*)?"` and a match with `group(2) is None` sets the key's lines to `[""]` (D-31.e; if the fixture says twoway refuses, dash.ado's `_dash_legend_check` (the legend validator the Stata side runs; grep `label(` in dash.ado's legend checks) refuses with the words and this clause is not added). `holes()`: after `seq` is built (:28360), insert the blanks at the 1-based positions (`_dash_expand_numlist`, limit 300, values > len+holes ignored as twoway ignores them -- measured U31-4); `colfirst` permutes `seq` per D-31.c using the final `rows`/`cols`.
- TR-31.7 **C13.** Step 8 (:28510-28514): `_hist_only = bool(plot_renderers) and all(str(p.get("type", "")).lower() == "histogram" for p, _ in plot_renderers)`; `show = not (turned_off or (n_keys < 2 and not forced_on) or (_hist_only and not forced_on))`.
- TR-31.8 **Copy lists (R2).** Constants: `"_DASH_CLOCK_PANEL_LOCATION", "_DASH_BPLACEMENT_LOCATION",` after `"_DASH_CLOCK_SIDE", "_DASH_CLOCK_INSIDE",` (:46617). Functions: `"_dash_key_signature",` after `"_dash_legend_key"` wherever it appears in the tuple (grep; it is near `_dash_legend_keys`). function_test_map.py: `"_dash_key_signature": "test/test_legend_geometry.py::TestMerge::test_same_text_and_style_is_one_key"`.
- TR-31.9 **Scheme stubs (R7).** scripts/extract_scheme_truth.py: truth entries after `legend_rows` (:1921) for `legend_key_xsize`, `legend_key_ysize`, `legend_key_gap`, `legend_row_gap`, `legend_col_gap` (gsize), `legend_ring` (gridringstyle), `legend_margin`, `legend_boxmargin` (margin), `legend_col_first`, `legend_span` (yesno), each `scalar(<out>, <cls>, [<key>], lambda t: t.strip(), class_default=False)`; directives in the "Marker size and legend placement" group (:2221-2225) for the ten (`legend_ring` included: S31 owns it; S30's four title rings go in a separate new group after this one, DECISIONS A31). Run twice with `--out test/fixtures/scheme_truth.json`; `git add -f`. Every `dash-*.scheme` gains `gsize legend_key_xsize 13`, `gsize legend_key_ysize medsmall`, `gsize legend_key_gap vsmall`, `gsize legend_row_gap tiny`, `gsize legend_col_gap large`, `gridringstyle legend_ring 3`, `margin legend small`, `margin legend_boxmargin small`, `yesno legend_col_first no`, `yesno legend_span no` (each scheme's own values, transcribed).
- TR-31.10 **Help (R3).** The legend paragraph (dash.sthlp, `grep -n "legend(" dash.sthlp | awk -F: '$1>3402 && $1<3511'`; the `{cmd:ring(0)}` sentences at :867-871 region) is rewritten: the honoured sub-options with their Bokeh meaning in Stata's words, the clock table (corners, 0, ring(0) default), the rows/cols/holes/colfirst rules, the merge and `label(#)` rules, the histogram rule, and the four not expressible (`textfirst`, `stacked`, `symplacement()`, `colgap()`; `subtitle()`/`note()`/`caption()` of the legend) with the measured example. Unsupported section: the `{cmd:region()} of {cmd:legend()}` clause (:5120-5125) is removed. TWOWAY_COVERAGE_AUDIT.md:140 gains `[WP-31 D4: corrected -- legend geometry, clocks, holes, colfirst, merge, label(#)]` and `[WP-31 C13: corrected -- histogram-only graphs draw no legend]` (no sha in a document line, DECISIONS A11).
- TR-31.11 **Served copy.** No template edit: the served app calls `_dash_apply_legend(... chrome=_dash_scheme_chrome(_DASH_SCHEME) ...)`; the chrome dict gains keys inside `_dash_scheme_chrome`. test_legend_order.py::TestTheServedCopy (:433) guards the copy.

## Boundaries

- Does not edit `_dash_textbox*`, `_dash_text_annotations`, `_dash_figure_title`, `_dash_edge_titles` (S27/S30), `_FILTER_JS` (S29), `_make_figure_body`, the template, `_dash_option_rules`, the colorvar key (`_COLORVAR_LEGEND_NAME` legends are skipped as today), the by() legend placement rules of WP-30 P1.15c (`by_legend_position`/`by_legend_ring`) beyond receiving the new props through the :38088 copy.
- Does not draw `textfirst`, `stacked`, `symplacement()`, `colgap()`, legend `subtitle()`/`note()`/`caption()` (documented).

## Stata truth

Script `scripts/extract_legend_geometry_truth.do` -> `test/fixtures/legend_geometry_truth.json` (R7 form). `sysuse auto`; base plot `scatter mpg weight || scatter price weight` (`u31k`), SVG exports read with cert_svg.do's reader; class values from `.u31k.legend` (members recorded by `classutil describe .u31k.legend` in `_meta.members`):

| key | legend() | values |
|---|---|---|
| default_geometry | (none) | `.legend.style.key_xsize/.key_ysize/.key_gap/.row_gap/.col_gap` (or the describe names), key symbol line length and label gap in the SVG |
| clock_k (k 0..12) | `pos(k)` | legend box centre x/y relative to the plot region box, from the SVG |
| ring0_default | `ring(0)` | box centre (expect bottom-centre inside the plot region) |
| cols_with_pos | `pos(3)` | `.legend.cols`/`.rows` (expect scheme cols 2 kept: measured, D-31.b) |
| holes | `holes(2) cols(2)` with three series | `.legend.holes`, key positions in the SVG |
| colfirst | `colfirst cols(2)` with four series | key order in the SVG (column-first) |
| label_blank | `label(1)` | `_rc`, `.legend.labels[1]` or the logged line (D-31.e) |
| merge | `scatter mpg weight || scatter mpg weight` | number of keys drawn (expect 1 if twoway merges) and `.legend.keys` |
| merge_style | `scatter mpg weight || scatter mpg weight, mcolor(red)` | number of keys (expect 2) |
| hist_only | `twoway histogram mpg || histogram price` | legend drawn? (`.legend.draw_view` or SVG key count; expect none) |
| hist_on | the same with `legend(on)` | drawn (expect yes) |
| region | `region(lcolor(red) fcolor(gs14) lwidth(thick))` | SVG rect stroke/fill/width |
| sizes | `symxsize(5) symysize(2) keygap(1) rowgap(3)` | SVG key geometry |
| bplacement | `pos(6) bplacement(w)` | box x relative to the plot region (expect left end) |
| title | `title("Keys")` | `.legend.title.text` |

Run `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s31 $WT/scripts/extract_legend_geometry_truth.do`; `git add -f`. `test_legend_geometry.py::TestTheFixture` names it.

## TDD test stubs

### Regression tests, `test/test_legend_geometry.py` (new; red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, go, plots)` (two scatters by default); `_legend(fig)` the plot legend (not `_COLORVAR_LEGEND_NAME`); `_panel_of(fig, legend)`; fixture at module level; drawing classes parametrized by mode.

- Test: fixture stamped and complete -- `TestTheFixture::*` (guard after 31-01).
- Test: default `glyph_width == 50`, `glyph_height == 13`, `label_standoff == 8`, `spacing == 5`, `padding`/`margin` the small ladder px under s2color; stcolor's own values -- `TestDefaultGeometry::test_scheme_sizes[mode-scheme]` (red).
- Test: `symxsize(5) symysize(2) keygap(1) rowgap(3)` -> 19/8/4/12 px (2.88 pt per unit at 4 in); `symxsize(*2)` doubles; `symxsize(bogus)` notes and keeps the default -- `TestSizeOptions::test_each[mode-opt]`, `::test_multiplier[mode]`, `::test_bad_value_noted[mode]` (red).
- Test: `pos(1)` -> `fig.above`, `location == "top_right"`; `pos(11)` -> `top_left`; `pos(2)` -> `fig.right`, `top_right`; `pos(4)` -> `bottom_right`; `pos(5)`/`pos(7)` below ends; `pos(8)`/`pos(10)` left ends; 12/3/6/9 `center` -- `TestClockTable::test_corners_and_sides[mode-clock]` (red: corners are `center`).
- Test: `pos(0)` -> inside, `location == "center"` -- `::test_zero_is_the_centre[mode]` (red: right side).
- Test: `ring(0)` alone -> inside, `bottom_center` under s2color, `center_right` under stcolor (position 3) -- `::test_ring0_takes_the_scheme_clock[mode-scheme]` (red: top_right).
- Test: `pos(3)` keeps `ncols == 2` under s2color (fixture `cols_with_pos`) -- `::test_scheme_cols_survive_position[mode]` (red).
- Test: `bplacement(w)` with `pos(6)` -> `center_left` -- `::test_bplacement[mode]` (red).
- Test: a `Title` the test itself appends to the side panel with tags `["dash_textbox", "subtitle", "ring=2"]` (S30's tag form) has a lower panel index than the legend after `_dash_apply_legend`, and one tagged `ring=4` a higher index -- `::test_ring_tags_order_the_legend[mode]` (red: the legend is inserted right after the axes and edge titles).
- Test: `holes(2) cols(2)` on three series -> four items, item 2 blank with no renderers; `nrows == 2` -- `TestHolesAndGrid::test_holes[mode]` (red); `rows(3)` on four keys -> `ncols == 2`; `cols(3)` -> `nrows == 2` -- `::test_rows_cols_arithmetic[mode-case]` (red for ncols/nrows both set).
- Test: `colfirst cols(2)` on four keys -> items `[1, 3, 2, 4]` -- `::test_colfirst_permutes[mode]` (red).
- Test: `region(lcolor(red) fcolor(gs14) lwidth(thick))` -> border/fill/width; `nobox` -> both None; `color(blue)` -> `label_text_color`; `title("Keys")` -> `title == "Keys"`; `textwidth(20)` -> `label_width` px -- `TestBoxAndText::test_each[mode-opt]` (red).
- Test: `span`, `forcesize`, `bexpand`, `nospan` are consumed with no note; `textfirst`, `stacked`, `symplacement(e)`, `colgap(2)`, `subtitle("s")` are named once -- `TestNamedAndSilent::test_silent[mode-word]` (red), `::test_named[mode-word]` (guard).
- Test: two identical scatters -> one `LegendItem` with two renderers tagged `dash_key_numbers 1 2`; `order(2 1)` still draws it once; `label(2 "B")` renames it -- `TestMerge::test_same_text_and_style_is_one_key[mode]`, `TestMergeKeepsNumbers::test_order_and_label[mode]` (red); a colour difference keeps two keys -- `::test_different_style_keeps_two[mode]` (guard).
- Test: `label(1)` blanks key 1 (or, per fixture, is refused by dash.ado with twoway's words) -- `TestLabelBlank::test_blank_or_refused` (red).
- Test: the by() cell legend carries the new props -- `TestByCellLegend::test_props_copied[mode]` (red).
- Test: the colorvar colour key is untouched by every option above -- `TestColourKeyUntouched::test_unchanged[mode]` (guard).
### Regression tests, `test/test_legend_histogram_only.py` (new in 31-04; C13; red at the D4 tree)

- C13: `histogram mpg || histogram price` -> `legend.visible is False`; `legend(on)` -> True; a histogram beside a scatter -> True -- `TestHistogramOnly::test_no_legend[mode]`, `::test_on_forces[mode]`, `::test_mixed_draws[mode]` (red for the first).
- Test: no note for any honoured sub-option -- `TestSilentWhenHonoured::test_no_note[sub]` (red).
- Test: `title()` text and `label()` text are DOM text nodes (test_label_sinks.py's `LegendItem.label` sink) -- a `Carrier` for `Legend.title` is added to test_label_sinks.py (guard there).

### Cases in cscripts

- `test/test_wp31_truth.cscript` block `* ==== S31 D4: Legend geometry ====`: U31-1 (default key geometry: twoway's key_xsize/ysize/gap values vs dash's px through the 2.88-pt rule), U31-2 (clock_k centres: side and end per clock vs dash's panel/location), U31-3 (cols_with_pos), U31-4 (holes and colfirst orders), U31-5 (label_blank: both sides' outcome equal), U31-6 (merge and merge_style key counts), U31-7 (region/sizes SVG vs dash props), U31-8 (bplacement, title). Block `* ==== S31 C13: Histogram-only legend ====`: U31-9 (hist_only and hist_on drawn flags equal in twoway and dash).
- `test/test_option_validation.cscript`: U31-10 `legend(symxsize(bogus))` note words equal twoway's; U31-11 `legend(holes(0))`/`holes(2.5)` refusals equal (`holes(numlist integer >0 max=300)`).

### Flips (in place, each with a `Flipped:` line)

- test_axis_options.py::TestLegendOptions nodes on `ring(0)` top_right, corner `center`, `ncols` with position; test_graph_options.py::TestLegend/TestLegendLabels nodes on `label(1)` ignored and duplicate keys; test_subopt_abbrev.py nodes listing the newly honoured names as unsupported; test_help_claims_*.cscript cases on the legend note text; test_scheme_chrome.py::TestTheChromeKeysAreRead (ten stubs). Each docstring gains "twoway's legend_g geometry (WP-31 D4)".

### Parity corpus (R8; appended, guards at base)

test_mode_parity.py under `# WP-31 D4/C13 (section 31): legend geometry`: `CORPUS` cases `"legend(pos(1) symxsize(5) keygap(1))"`, `"legend(ring(0))"`, `"legend(holes(2) cols(2) colfirst) three series"`, `"two identical scatters merged"`, `"histogram only, no legend"`; `MOVE_CORPUS` case `_move_case("legend(ring(0) holes(2)) after a dropdown move (WP-31 D4)", _MOVES[0], [plot_for("scatter"), plot_for("line")], go={"legend": "ring(0) holes(2)"})`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Default geometry from the scheme | pytest + U31-1 | legend_geometry_truth.json, scheme_truth.json | yes |
| Clock table, pos(0), ring(0), bplacement | pytest + U31-2/U31-8 | legend_geometry_truth.json | yes |
| Scheme cols with position | pytest + U31-3 | legend_geometry_truth.json | yes |
| Holes, rows/cols, colfirst | pytest + U31-4 | legend_geometry_truth.json | yes |
| label(#), merge | pytest + U31-5/U31-6 | legend_geometry_truth.json | yes |
| region/sizes/title/color | pytest + U31-7 | legend_geometry_truth.json | yes |
| Histogram-only | pytest + U31-9 | legend_geometry_truth.json | yes |
| Notes/refusals | cscript U31-10/U31-11 | live twoway | n/a |
| by() cell copy | pytest | -- | yes |

Acceptance: AC-31.1 every red stub green in both modes; AC-31.2 U31-1..U31-11 PASS, no SKIP; AC-31.3 guards green (colour key, different-style keys, named words); AC-31.4 the generator's second run changes nothing; AC-31.5 test_legend_order.py, test_label_sinks.py, test_by_grid.py, test_csp.py green; AC-31.6 two green commits.

## Tasks

**Commit boundary.** 31-01..31-03 form the D4 commit, subject `Lay the legend out as twoway's legend_g does: geometry, clocks, holes, merge (WP-31 D4)`; 31-04 the C13 commit, subject `Draw no legend on a histogram-only graph, as twoway does (WP-31 C13)`; both on `wp31-s31`. Bodies per BRIEF (failure text, measured defect, changes in both modes, `Regression:`/`Flipped:`/`Fixture:` lines -- `legend_geometry_truth.json (scripts/extract_legend_geometry_truth.do)`, `scheme_truth.json (scripts/extract_scheme_truth.py)` -- `BUGS.md:`, `GAPS3:`). CHANGELOG Results: D4 `dash scatter mpg weight || scatter price weight, legend(ring(0)): top right -> inside at the bottom centre, keys 13 x medsmall (WP-31 D4)`; C13 `dash histogram mpg || histogram price: a two-key legend -> no legend (WP-31 C13)`. No tooling names.

<task type="auto" id="31-01">
  <name>Measure twoway and write failing D4 tests</name>
  <files>scripts/extract_legend_geometry_truth.do, test/fixtures/legend_geometry_truth.json, test/test_legend_geometry.py</files>
  <action><![CDATA[
    Check the cut (`wp31-s31`, batch-10 base sha); `mkdir -p <scratch>/s31`. Create scripts/extract_legend_geometry_truth.do (head from scripts/extract_default_base_truth.do:21-48) with every row of "Stata truth"; run it through `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s31 ...`; `git add -f test/fixtures/legend_geometry_truth.json`. Read `label_blank`, `merge` and `hist_only` and record their outcomes in the module docstring (they fix D-31.d/e/f's branch). Create test/test_legend_geometry.py with exactly the D4 classes of "TDD test stubs" (not C13's `TestHistogramOnly`: 31-04 creates test/test_legend_histogram_only.py, DECISIONS A14); run `python3 -m pytest test/test_legend_geometry.py -q -n0 -p no:cacheprovider -rf > <scratch>/s31/31-01.log 2>&1`; write `<scratch>/31-01-failure.txt`. Run the pinned files named in "Flips" and record their currently-green nodes that must flip in `<scratch>/s31/31-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/legend_geometry_truth.json'));print(sorted(d['_meta'])[:4], d['hist_only']['drawn'], d['merge']['keys'])"` prints `['born_date', 'dash_commit', 'extracted', 'members'] 0 1` (or the measured values, recorded); `grep -c FAILED <scratch>/s31/31-01.log` is at least 30; no FAILED line names TestTheFixture, TestColourKeyUntouched, `test_different_style_keeps_two` or `test_named`; `test -s <scratch>/31-01-failure.txt`.]]></verify>
  <done>twoway's legend geometry, clock positions, holes, merge, label(#) and histogram rules were recorded in a stamped fixture, and every D4 regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="31-02">
  <name>Draw the legend geometry and clocks</name>
  <files>dash_render.py, scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Apply TR-31.1 to TR-31.6 and TR-31.8 in dash_render.py in this order: the honoured set (:37094); the two clock constants after :28071 and `_DASH_CLOCK_INSIDE[0]`; `_dash_move_legend`'s `location` argument keeping S27's skip and adding the `ring=<n>` (n <= legend ring) skip (:28179-28200); SchemeParser attributes after :10684 and `_dash_scheme_chrome`'s keys (:28217-28232); step 3b, the placement rewrite (:28394-28425), the rows/cols/holes/colfirst rule replacing step 6 (:28434-28465), the `label(#)` regex and clause (:37103, :28325-28327), all inside `_dash_apply_legend`; `_dash_key_signature` after `_dash_legend_key` (:39924) and the merge in `_dash_legend_keys` (:39925-39965); copy-list entries and the function_test_map.py entry. Apply TR-31.9 to scripts/extract_scheme_truth.py (the ten directives inside the `Marker size and legend placement.` group :2221-2225, the ten truth entries after `legend_rows` :1921; do not touch S30's `Textbox rings.` region); run the generator twice with `--out test/fixtures/scheme_truth.json`; `git add -f`. Run `python3 -m pytest test/test_legend_geometry.py test/test_legend_order.py test/test_axis_options.py test/test_graph_options.py test/test_by_grid.py test/test_scheme_chrome.py test/test_subopt_abbrev.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "not Chrome" > <scratch>/s31/31-02.log 2>&1`; flip the nodes in `<scratch>/s31/31-flips.txt` in place with the reason, and nothing outside those files (a red node elsewhere stops the task and is reported).
  ]]></action>
  <verify><![CDATA[`grep -c "gsize legend_key_xsize" dash-*.scheme | grep -vc ":1$"` prints 0; `python3 -c "import dash_render as d; print(d._DASH_CLOCK_INSIDE[0], d._DASH_CLOCK_PANEL_LOCATION[1], 'holes' in d._DASH_LEGEND_SUBOPTS)"` prints `center top_right True`; `grep -c FAILED <scratch>/s31/31-02.log` prints 0 after the flips.]]></verify>
  <done>Both renderers laid the legend out with the scheme's key geometry, twoway's clock table, holes, rows/cols arithmetic, colfirst, merged identical keys and blank label(#) keys, and every scheme carried the ten legend stubs.</done>
</task>

<task type="auto" id="31-03">
  <name>Certify, document and commit D4</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[
    Append the S31 D4 block (`* ==== S31 D4: Legend geometry ====`, U31-1..U31-8) above the marker line and U31-10/U31-11 to test_option_validation.cscript; drivers per BRIEF (`WP31_ONLY=S31`); run both through the slot. Append the parity cases (R8) and the `Legend.title` Carrier to test_label_sinks.py. Apply TR-31.10's D4 half to dash.sthlp and TWOWAY_COVERAGE_AUDIT.md. Close the D4 BUGS.md entry, rewrite `D4 Tracked` to the Closed form ending `commit pending.` (DECISIONS A11; the merger's step k.3b writes the sha), replace `<!-- WP-31 D4 -->`. Run `python3 -m pytest test/test_legend_geometry.py test/test_help_conformance.py test/test_tracking_documents.py test/test_label_sinks.py test/test_mode_parity.py -k "D4 or legend or sink or Unsupported" -q -p no:cacheprovider`; `git add -A`; commit with the D4 body; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.
  ]]></action>
  <verify><![CDATA[`grep -c "U31-\([1-8]\|10\|11\) PASS" <scratch>/s31/*.log` sums to 10 and `grep -c SKIP <scratch>/s31/run_truth.log` prints 0; `grep -c "region()} of {cmd:legend()}" dash.sthlp` prints 0; `grep -c "^- \*\*D4 Tracked:\*\* Closed in WP-31.*commit pending\.$" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 D4)`.]]></verify>
  <done>D4 was certified against twoway, documented, tracked and landed as one green commit on wp31-s31.</done>
</task>

<task type="auto" id="31-04">
  <name>Exempt histogram-only graphs and commit C13</name>
  <files>dash_render.py, test/test_legend_histogram_only.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[
    Create test/test_legend_histogram_only.py with exactly C13's `TestHistogramOnly` class of "TDD test stubs"; run `python3 -m pytest test/test_legend_histogram_only.py -q -n0 -p no:cacheprovider -rf > <scratch>/s31/31-04-base.log 2>&1` on the D4 tree and write `<scratch>/31-04-failure.txt` (`test_no_legend` red in both modes). Apply TR-31.7 (:28510-28514). Append the S31 C13 block (`* ==== S31 C13: Histogram-only legend ====`, U31-9) above the marker line and run it (`WP31_ONLY=S31`). Flip any pinned node asserting a legend on a histogram-only graph (test_axis_options.py::TestLegendRule; test_glyphs.py histogram cases -- grep `histogram` with `legend` in test/) in place with the reason. Add the histogram sentence to the legend help paragraph in dash.sthlp; the audit line (TR-31.10 C13 half). Close the C13 BUGS.md entry, rewrite `C13 Tracked` to the Closed form ending `commit pending.` (A11), replace `<!-- WP-31 C13 -->`. Run `python3 -m pytest test/test_legend_histogram_only.py test/test_legend_geometry.py test/test_axis_options.py test/test_glyphs.py test/test_tracking_documents.py -q -p no:cacheprovider -k "legend or Legend or hist or tracking"`; commit with the C13 body; no tooling names.
  ]]></action>
  <verify><![CDATA[`grep -c "U31-9 PASS" <scratch>/s31/run_truth.log` prints 1; `grep -n "_hist_only" dash_render.py | wc -l` is at least 2; `grep -c "^- \*\*C13 Tracked:\*\* Closed in WP-31.*commit pending\.$" GAPS3.md` prints 1; `git show --stat HEAD | grep -c test_legend_histogram_only.py` prints 1; `git log -1 --format=%s` ends `(WP-31 C13)` and `git log -2 --format=%s | tail -1` ends `(WP-31 D4)`.]]></verify>
  <done>Histogram-only graphs drew no legend unless legend(on), certified against twoway and landed as the C13 commit.</done>
</task>

## Section completion criteria

- The honoured legend set is drawn in both modes with twoway's defaults and nothing printed; the five not expressible are named and documented with a measured example.
- Corner clocks, `position(0)`, `ring(0)` alone, `bplacement()` and the scheme's columns follow twoway; holes/rows/cols/colfirst, merge and `label(#)` follow the fixture.
- Histogram-only graphs draw no legend unless `legend(on)`.
- Every shipped scheme carries the ten legend stubs; U31-1..U31-11 PASS; flips recorded; help, Unsupported list, audit, BUGS.md, GAPS3 §9 and CHANGELOG updated in two commits.

## Notes

- **Renderer order.** The saved renderer applies the legend in `_rebuild_legend` after the layers; the served app in `_dash_figure_for` after the glyphs; both pass `_dash_scheme_chrome(scheme)`, so the new chrome keys reach both without a template edit.
- **Copy lists (R2):** constants after `"_DASH_CLOCK_SIDE", "_DASH_CLOCK_INSIDE",` (:46617); `"_dash_key_signature",` after `_dash_legend_key`'s entry; `SchemeParser` attributes travel with the class.
- **R12:** no hot function edited; `_dash_apply_legend` and `_dash_move_legend` are S31's for batch 10 (index owner table: "legend builders: 31").
- **R1:** two blocks (D4, C13) and two area cases under U31 ids.
- **R3:** S31 owns the legend paragraph and the Unsupported clause it removes.
- **R7:** `legend_geometry_truth.json` new; `scheme_truth.json` and the `dash-*.scheme` files regenerated. S31's generator hunks (legend group, entries after `legend_rows`) and S30's (new `Textbox rings.` group, entries before `legend_position`) are disjoint; the merger applies S29 and S30 whole, S31's diff with `git -C <wt> diff -- . ':(exclude)dash-*.scheme' ':(exclude)test/fixtures/scheme_truth.json'`, then runs `scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` twice after the batch-10 merge and `git add -f` (DECISIONS A31, index.md:145).
- **R9/R10:** flips only inside the files 31-01 lists; counts untouched (no pending-block change: the legend sub-options were never pending-block entries).
- **S27's skip** in `_dash_move_legend` is kept (D-27.b); the `ring=<n>` (n <= 3) skip is added beside it (A31), read from S30's tags once both land -- S31's own test builds the tagged Title itself, so it is green without S30.
- **Security:** `title()`/`label()` text stays a DOM text node; `region()` colours go through the colour grammar; sizes through `resolve_size` (bounded 64 characters).
- **For S39 (batch 13):** merged items carry `dash_key_numbers` tags; holes are `LegendItem`s with no renderers; read, do not rebuild.
- **Decisions for the maintainer:** D-31.a's px conversion (2.88 pt per unit at the reference) and D-31.d's merge signature are this file's rulings within M17; ratify or amend before batch 10.
