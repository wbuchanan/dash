# Section 30: Textbox placement and added-text style

> Part of: WP-31 · GAPS3 rows: D3, D13 · Risk: yellow · Batch: 10 · Depends on: 01 · Blocks: -- · Tasks: 4, 2 commits · Case-id prefix: U30

## Overview

**What is wrong today.** GAPS3 D3 (GAPS3.md:153): "Textbox sub-options on titles (`position ring span justification alignment orientation box bexpand margin bmargin tstyle fcolor lcolor lwidth lpattern lstyle bcolor width height linegap placement`) named; `_dash_textbox_place` exists but is wired only to scheme clocks." Evidence `dash_render.py:37117 _DASH_TEXTBOX_HONOURED, :37246`. GAPS3 D13 (:163): "Added text: `tstyle()` and the other textbox sub-options named; `$name` in drawn labels not macro-expanded." Evidence `dash.ado:7829-7889; dash_render.py:37323`. At `6370ca4` `_DASH_TEXTBOX_HONOURED` is `{"size", "color", "prefix", "suffix", "axis"}` (:37117-37118); `_dash_textbox` (:37121-37160) names every other textbox token through `_dash_report_suboptions`, so `title("T", position(6))` draws T above the plot and prints `dash: title(): ignoring position(6)`. `_dash_textbox_place(clock, just)` (:37246-37286) maps a clock to `(side, align)` but is called only with the scheme's `text_clock` (apply_to_figure :11512, `_dash_text_annotations` :37394, `_dash_by_panel_label` :37656). For added text, dash.ado's `_dash_at_opts` (:7819-7895) reads `TSTYle(string)` (:7820) and puts `tstyle` in the "noted" list `_nt` (:7870-7874) that is named and not drawn; `_DASH_ADDED_TEXT_HONOURED` (:37323-37326) has no `tstyle`; and the text of a `text()` copy reaches `_dash_at_parse` (:7909) as written, so a `$name` the command line kept (a registered spec, or text protected by `macval()` on the way) is drawn as the literal `$name`.

**After this section** `title()`, `subtitle()`, `note()` and `caption()` honour `position(#)`, `ring(#)`, `span`, `justification()`, `alignment()`, `margin()`, `linegap()`, `box`/`nobox`, `bcolor()`, `fcolor()`, `lcolor()`, `lwidth()`, `lpattern()`, `bmargin()`, `bexpand`, `tstyle()` and `placement()` in both modes, on the Title (or, inside the plot region, Label) model that draws the box: `position()` through `_dash_textbox_place`'s clock table (above/below, left/center/right), `ring(0)` as a `Label` pinned by `Node` coordinates to the frame's compass point, `justification` as the text alignment, `alignment` as `vertical_align`, box/colours/width/pattern/margin as `border_line_*`, `background_fill_*` and `padding`, `tstyle()` as the base size/colour from `SchemeParser.textbox_style`. `orientation()`, `width()` and `height()` are documented as what a Bokeh Title cannot express (M17) and stay named. Added text (`text()`/`ttext()`) honours `tstyle()` the same way, and a `$name` or `${name}` in its text is expanded once at registration, in dash.ado, by a bounded textual substitution of `st_global()` (never through a command line), after twoway's behaviour on `"$x"` and `"$$f$$"` is measured.

**Why two rows share this section.** Both rows are the textbox grammar: D3 on the four main boxes, D13 on added text. They share `_textbox_size`/`_textbox_color`, the `_DASH_TBSTYLE_ROWS` table (:36812-36827) and `SchemeParser.textbox_style` (:10085). S27 (batch 9) draws the edge titles as tagged `Title`s; S30's title helper styles them by tag but does not move them (S27 Notes).

**Test order and commit rule (BRIEF).** Two cycles, two commits. D3: 30-01 writes `test/test_textbox_placement.py` and the extract script, runs red, saves `<scratch>/30-01-failure.txt`; 30-02 wires placement and the box; 30-03 certifies, flips, documents and commits `(WP-31 D3)`. D13: 30-04 creates `test/test_added_text_style.py` (the D13 classes; one regression test file per row, DECISIONS A14) against the D3 tree, runs it red (saved `<scratch>/30-04-failure.txt`), fixes dash.ado and the renderer, certifies and commits `(WP-31 D13)`. No test-only commit; no `pytest.mark` row device.

### Section decisions (this file; binding on the executor)

- **D-30.a The clock table is `_dash_textbox_place`'s.** `position(#)` with ring > 0 gives `(side, align) = _dash_textbox_place(clock, just)` where `just` is `justification()` when given else the scheme's `horizontal <style>`; clocks 2-4 and 8-10 go to the nearer horizontal side as the docstring says (:37264-37270), documented with the measured example `title("T", position(3))` (twoway: right of the plot; dash: above, right-aligned). `ring(#)` with # > 0 orders boxes on one side: the larger ring is inserted further from the frame, by inserting after the last model whose recorded ring is smaller (each box carries `tags=["dash_textbox", "<key>", "ring=<n>"]`; `_dash_edge_titles`' models count as rings 1 and 2; the legend as 3). Defaults: title 7, subtitle 6, caption 5, note 4 (`scheme-s2color.scheme:1947-1950`, stubs added to the schemes, TR-30.7).
- **D-30.b `ring(0)` and `position(0)` are `Label`s.** A box at ring 0 is drawn inside the plot region as a `Label(x=Node(target="frame", symbol=sx), y=Node(target="frame", symbol=sy), anchor=a, ...)` with `(sx, sy, a)` from the clock: 12 (center, top, top_center); 1, 2 (right, top, top_right); 3 (right, center, center_right); 4, 5 (right, bottom, bottom_right); 6 (center, bottom, bottom_center); 7, 8 (left, bottom, bottom_left); 9 (left, center, center_left); 10, 11 (left, top, top_left); 0 (center, center, center). `position(0)` with any ring is the centre (title_options.sthlp remarks3 :75-78); `span` at position(0) is ignored with twoway's note "(option span ignored for position(0))" (measured, U30-7). The Label goes to `fig.center[0]` as the in-band Label does (:37398-37406), for the renderer-order reason recorded there.
- **D-30.c `span` is honoured as a no-op above/below** (a side-panel Title already spans the figure) and the unspanned default's narrower box is the documented difference (M17); `bexpand` likewise.
- **D-30.d Box geometry.** `box` -> `border_line_color = lcolor() or scheme textbox line colour` (the `color textbox` the added-text path already reads as `text_option_line_color`); `nobox` -> `border_line_color=None, background_fill_color=None`; `bcolor()` -> fill and border colour; `fcolor()`/`bfcolor()` -> fill; `lwidth()` -> `border_line_width` (Stata units through `OptionTranslator.resolve_size(v, "line", default)`); `lpattern()` -> `border_line_dash` (the line-pattern translator `_dash_lpattern_dash` the reference lines use); `margin()` -> `padding` as `_dash_added_text_opts` computes it (the margin ladder, :37460-37470); `linegap()` -> `text_line_height` (a ratio: Bokeh's default is 1.2, so `1.2 + gap_pt / size_pt`, or the fixture's `linegap_3` rule if it measures otherwise -- R3c-F16); `bmargin()` -> `standoff` (Title) or the Label's offset; `alignment()` -> on a `Title` `vertical_align` ("top"/"middle"/"bottom" from twoway's top/middle/baseline... "baseline" maps to "bottom"); on a ring-0 `Label` (Bokeh 3.8 `Label` has no `vertical_align`, R3-06) the anchor's vertical component (`top_*`/`center_*`/`bottom_*`) replaces the clock's; `placement()` on a ring-0 Label -> its `anchor` through `_DASH_ADDED_TEXT_PLACE`; `tstyle()` -> `scheme.textbox_style(name)` as the base size/colour (size()/color() still win); an unknown style name draws the default with twoway's note "named style <x> not found in class textboxstyle, default attributes used" (measured text, U30-8). `orientation()`, `width()`, `height()` stay named (a Title has no angle or fixed box).
- **D-30.e `$name` expansion is a textual substitution in Mata.** New `_dash_at_globals(s)` replaces every `$name` and `${name}` (name `[A-Za-z_][A-Za-z0-9_]{0,31}`) with `st_global(name)`; `$$` and `$` followed by anything else are left as written; applied once to each copy's text lines in `_dash_at_parse`'s caller before the records are written (dash.ado:7909-7940). twoway's own behaviour on `text(... "$x")` with `global x` set and on `"$$f$$"` is measured first (U30-10/U30-11) and the fixture's result is the rule the test pins; if twoway leaves `$x` literal in some form, the substitution follows twoway's measured form, never this paragraph's guess. User text never reaches a command line (`macval` throughout, the comment at dash.ado:155-160).

## Risk: [yellow] -- the four main boxes of every figure can move, and user text gains a substitution path

**Why.** `_dash_text_annotations` and `_dash_figure_title` are rewritten around one helper; `fig.center` gains Labels; dash.ado's added-text registration gains a text transform.

**Risk factors.** 1. Panel ordering across S27's edge titles, the legend (S31, same batch) and the boxes. 2. The in-band economist note (`in_band`, :37392-37397) must keep its band. 3. A `$` substitution must never evaluate: no `display`, no macro expansion of user text. 4. The by() chrome rows call the same helper with `sides=`. 5. Batch 10 partner S31 edits `_dash_move_legend`/`_dash_apply_legend`; S30 reads legend rings but does not edit those functions.

**Mitigation.** 1. `TestRingOrder` reads every side panel's order with title ring 7, subtitle 6, legend 3, edge titles 1-2. 2. `TestEconomistBandUnchanged` is a guard (test_scheme_chrome.py's `TestTextboxesSitAtTheirClock` stays green). 3. `TestGlobalsAreSubstitutedNotEvaluated` feeds `$x` with `global x` set to `` `=1+1' `` and `"\`c(pwd)'"` and asserts the drawn text is the global's raw value. 4. `TestOnAByGraph`. 5. Both sections' Boundaries; the merger lands S29, S30, S31 in that order.

## Dependencies

- **Depends on: 01.** Markers `<!-- WP-31 D3 -->`, `<!-- WP-31 D13 -->`; BUGS entries; the truth script.
- **Blocks: --.** S31 (same batch) makes `_dash_move_legend`'s insertion index skip models whose tags hold `ring=<n>` with n <= 3 (S31 TR-31.2, DECISIONS A31), so a user `ring(1)`/`ring(2)` box lands inside the legend in both modes; S30 only writes the tags. S36 (by-remainder) may reuse the helper.
- **Parallel batch: 10**, merge order S29, S30, S31. **Can run with S29 and S31**: S29 edits `_FILTER_JS`; S31 edits `_dash_apply_legend`, `_dash_move_legend`, `_DASH_LEGEND_SUBOPTS`, `_dash_legend_unsupported`, `_dash_scheme_chrome`; S30 edits none of those and S31 edits none of `_dash_textbox*`, `_dash_text_annotations`, `_dash_figure_title`, `_dash_added_text*`, `_DASH_TBSTYLE_ROWS`, `_dash_at_*`.

## Evidence

All anchors at `6370ca4`.

### The honoured set and the namer (dash_render.py)

```python
37117 _DASH_TEXTBOX_HONOURED = frozenset({"size", "color", "prefix", "suffix",
37118                                     "axis"})
37152             elif nm in _DASH_TEXTBOX_HONOURED:
37153                 continue
37154             bad.append(t)
37155         _dash_report_suboptions(option, bad, seen, key)
```
`_dash_textbox` returns `(text, opts)` where `opts` is `_parse_textbox_opt`'s dict of every sub-option (:6281); only the named ones are refused in the note, the dict still carries them. `_dash_figure_title` (:37180-37213) reads `size`/`color` only. `_dash_text_annotations` (:37329-37414) places by `scheme.text_clock` and `scheme.text_just` (:37387-37394), builds `Title(text, align, text_font_style="normal", text_font_size, text_color, background_fill_color=fill)` (:37408-37413) or, in the economist band, a `Label` with `Node` coordinates (:37398-37406). The clock table:

```python
37246 def _dash_textbox_place(clock, just) -> "tuple[str, str]":
      11, 10 ("above","left"); 12, 0 ("above", J); 1, 2 ("above","right");
      3, 4, 5 ("below","right"); 6 ("below", J); 7, 8, 9 ("below","left")
```
The textbox grammar rows: `_DASH_TBSTYLE_ROWS` (:36812-36827): `tstyle angle size color justification alignment margin linegap nobox box bmargin placement bfcolor fcolor bcolor blstyle blwidth blcolor blpattern blalign lstyle lwidth lcolor lpattern lalign orientation`. `_DASH_SZTEXTBOX_ROWS` (:36942): `width height bexpand nobexpand`. Added text: `_DASH_ADDED_TEXT_HONOURED` (:37323-37326) `size color justification orientation box nobox fcolor lcolor lwidth margin placement`; `_dash_added_text_opts` (:37417-37500) resolves them, the margin ladder into `padding`; `_dash_added_text` (:37505-37628) builds the `Label` with `border_line_color`, `border_line_width`, `background_fill_color`, `padding`, `anchor`, `angle` (:37603-37620).

### Added text in dash.ado

`_dash_at_opts` (:7819-7895): `syntax [, AXes(string) YAXis(integer 1) XAXis(integer 1) TSTYle(string) *]` (:7820); the second `syntax` (:7845-7853) reads the textbox options; the noted list (:7870-7874) is `width height astextbox noastextbox bexpand nobexpand drawview ascircle tstyle angle alignment linegap bmargin lpattern lstyle lalign blpattern blstyle blalign`; `_dash_at_canon()` (dash_parse.mata:9290) writes the canonical honoured names. `_dash_added_text` (:7901-7947): `_dash_at_parse(st_local("_dash_txt"), ...)` (:7909) reads the copies; `_dash_at_copy`, `_dash_at_opts` per copy (:7912-7913); `_dash_at_records` (:7938) writes the JSON records.

### Stata's rule (research/stata-ground-truth.md §9, §10)

Non-numbered titles: position/ring from the scheme (`clockdir title_position 12`, `subtitle 12`, `caption 7`, `note 7`; rings 7/6/5/4, :1920-1923, :1947-1950); `ring(0)` -> "on" the plot region (`_fr_title_parse_and_log.ado:94-100, 116-118`); `inside`/`outside` accepted as 0/1 (:104-111); span ignored at position(0) with "(option span ignored for position(0))" (:136-139); box_alignment and horizontal justification derived from the clock (`clockdir.class:90-125`: 12/6/0 center, 1-5 right, else left; 9/3/0 center, 4-8 bottom, else top). Textbox semantics (§10): justification = horizontal alignment inside the box; alignment = vertical (baseline/middle/top); margin = text-to-border distance; linegap; width/height override; box/nobox; bcolor/fcolor/lcolor only with box; lpattern forces centre alignment; bmargin = border to container; bexpand; placement(compassdir). Parser mapping (`_fr_tbstyle_parse_and_log.ado:11-24, 37-60`): justification->horizontal, alignment->vertical, box->drawbox, placement->box_alignment, bcolor->fillcolor+line colour, bfcolor/fcolor->fillcolor. dash-s2color.scheme has `clockdir title_position`/`subtitle_position` (:357-358) and the note/caption clocks (:359-360), no `gridringstyle title_ring` .. `note_ring` (research §11 "Absent").

### Fixtures on disk

`test/fixtures/text_truth.json` (scripts/extract_text_truth.do): the main boxes' size/colour truth. `test/fixtures/added_text_truth.json` (scripts/extract_added_text_truth.do): placement anchors, orientation, `_meta.orient`. Both are read, not rewritten.

### Tests that pin today's behaviour (flip, never delete)

- test_graph_options.py::TestNote / ::TestCaption / ::TestSubtitle (:189-354): assert the scheme side; a case asserting that `position()` is named must flip.
- test_scheme_chrome.py::TestTextboxesSitAtTheirClock (:180) and ::TestTextboxPlace (:500): the table; unchanged unless a test asserts that user clocks are ignored.
- test_axis_options.py::TestTitleTextFidelity (:463): any node asserting "position() is named" flips.
- test_added_text*.py (grep `tstyle`): the node asserting `tstyle()` is named flips; test_help_claims_*.cscript cases that pin the note text for `title(, position())` or `text(, tstyle())` flip in the area script.

## User stories

- US-30.1 As a Stata analyst, I want `title("T", position(6))` to put the title below the plot, as twoway does, so my do-file's layout survives.
- US-30.2 As a Stata analyst, I want `note("N", ring(0) position(1))` drawn inside the plot region at the top right.
- US-30.3 As a Stata analyst, I want `caption("C", box bcolor(gs14) margin(medium))` drawn in a filled, bordered box.
- US-30.4 As a Stata analyst, I want `text(30 2000 "Peak", tstyle(heading))` drawn in the heading style, and `text(... "$label")` to show my global's value.

## Business requirements

- BR-30.1 The listed textbox sub-options on the four main boxes are drawn in both modes; nothing is printed for them; `orientation()`, `width()`, `height()` are named and documented.
- BR-30.2 `position()` follows twoway's clock; `ring(0)`/`position(0)` draw inside the plot region at the compass point; rings order the boxes on a side.
- BR-30.3 Box, fill, border colour/width/pattern and margins follow twoway's option semantics; `nobox` removes them.
- BR-30.4 `tstyle()` sets the base style on main boxes and added text; `size()`/`color()` still win; an unknown name draws the default with twoway's note.
- BR-30.5 `$name`/`${name}` in added text draws the global's value, never evaluated; `$$` is left as twoway leaves it (measured).

## Technical requirements

- TR-30.1 **Honoured set.** `_DASH_TEXTBOX_HONOURED` (:37117) becomes `frozenset({"size", "color", "prefix", "suffix", "axis", "position", "ring", "span", "nospan", "justification", "alignment", "margin", "linegap", "box", "nobox", "bcolor", "bfcolor", "fcolor", "lcolor", "lwidth", "lpattern", "lstyle", "bmargin", "bexpand", "nobexpand", "tstyle", "placement"})`. `_dash_textbox`'s loop (:37140-37154) is unchanged otherwise, so `orientation`, `width`, `height`, `angle`, `blstyle`.. stay named.
- TR-30.2 **One styling helper.** New module function `_dash_textbox_style(model, opts, fig, scheme, option, *, base_size, base_color)` placed directly after `_dash_textbox_place` (:37286): reads `opts` (the dict from `_dash_textbox`) and sets on a `Title` or `Label` the properties of D-30.d, in this order: `tstyle` (base from `scheme.textbox_style(name)` when scheme and the name resolves, else the note of D-30.d through `_dash_style_note(option, name, "textbox style", "the scheme's default")`), then `_textbox_size`/`_textbox_color` as `_dash_text_annotations` does today (:37384-37392), then `justification` -> `align` (Title) / `text_align` (Label) when in `("left", "center", "right")`, `alignment` -> `vertical_align` on a `Title` only (`top`->"top", `middle`->"middle", `baseline`/`bottom`->"bottom"); on a `Label` the anchor's vertical component (`top_*`/`center_*`/`bottom_*`; `Label` has no `vertical_align` in Bokeh 3.8, R3-06), box/colours/width/pattern/margin/linegap (D-30.d). Returns the model. Imports inside the function.
- TR-30.3 **Placement helper.** New `_dash_textbox_position(fig, key, opts, scheme, default_clock, default_ring, just_default) -> (mode, side_or_anchor, align, ring)` after `_dash_textbox_style`: `clock = position() when it fullmatches [0-9]|1[0-2] else default_clock` (twoway draws the default for 13/06/3.0, the legend rule at :28392); `ring = ring() when a non-negative integer else default_ring`; `inside`/`outside` words as 0/1; if `clock == 0` or `ring == 0`: mode "inside" with the D-30.b anchor triple; else mode "side" with `_dash_textbox_place(clock, just)`; `span` at position(0) prints the measured note.
- TR-30.4 **Inserting by ring.** New `_dash_textbox_insert(fig, side, model, ring)`: `panel = list(getattr(fig, side))`; the model gets `tags += ["ring=%d" % ring]`; insert after the last non-Axis model whose ring tag (edge titles: `dash_edge_title` ring 1/2 by key digit; a `Legend`: 3; `dash_textbox`: its tag; anything else: 0) is `<= ring`, else directly after the axes; `setattr(fig, side, panel)`. Replaces `fig.add_layout(Title(...), side)` at :37408-37413 and the title's own placement (:11512-11516 sets `fig.title.align`/`title_location`; `_dash_figure_title` keeps `fig.title` as the model when the user gives no position/ring, and otherwise sets `fig.title.text = ""`... no: it sets `fig.title = None` and draws the title as a `dash_textbox` Title through the same path so ring 7 ordering holds).
- TR-30.5 **Rewire the callers.** `_dash_figure_title` (:37180): `text, opts = _dash_textbox(raw, "title", seen, key)`; when `opts` has any of `position ring span box ...` (any key outside `{"size", "color", "prefix", "suffix"}`) or always (one path, D-30.a): compute `_dash_textbox_position(fig, "title", opts, scheme, scheme.text_clock["title"], 7, scheme.text_just["heading"])`, build the `Title`/`Label` with `_dash_textbox_style`, insert by ring, and set `fig.title = None` so Bokeh's own title slot is empty (the dashboard header `_dash_header_models` is separate and unchanged). `fig.title = None` is legal (`Either(Null, Instance(Title))`), but `grep -n "fig\.title\." dash_render.py` lists 10 sites at `6370ca4` (export names, header, tests): guard each with `fig.title is not None`, and test_label_sinks.py's `Title` carrier must still find the tagged `dash_textbox` Title (R3c-F19). `_dash_text_annotations` (:37329): replace the `side, align = _dash_textbox_place(clock, just)` (:37394) and the model construction (:37398-37413) with the three helpers, defaults from `scheme.text_clock` and the new `scheme.text_ring` (TR-30.7), keeping the `in_band` rule and the `sides` filter (a ring-0 box is drawn only when `sides is None`). `_dash_by_panel_label` (:37656) and `apply_to_figure` (:11512) are unchanged (scheme clocks). The saved and served call order is unchanged (`_dash_figure_title` then `_dash_text_annotations`, both modes).
- TR-30.6 **Edge titles.** `_dash_edge_titles` (S27) models already carry `dash_edge_title`; `_dash_textbox_insert` treats them as rings 1/2. S30 does not edit `_dash_edge_titles`.
- TR-30.7 **Scheme stubs (R7).** The four title rings only: `gridringstyle title_ring 7`, `subtitle_ring 6`, `caption_ring 5`, `note_ring 4` (`legend_ring 3` is S31's, TR-31.9, in the legend group -- DECISIONS A31). scripts/extract_scheme_truth.py gets a NEW directive group `group(["Textbox rings."], [scalar("gridringstyle", "title_ring", "title_ring"), scalar("gridringstyle", "subtitle_ring", "subtitle_ring"), scalar("gridringstyle", "caption_ring", "caption_ring"), scalar("gridringstyle", "note_ring", "note_ring")])` placed directly AFTER the `group(["Marker size and legend placement."], [...])` block (:2221-2225), and four truth entries `"<k>_ring": scalar("<k>_ring", "gridringstyle", ["<k>_ring"], lambda t: _as_number(t.strip()), class_default=False)` placed directly BEFORE the `"legend_position"` entry (:1914), after the `margin_ladder_*` comprehension (:1912); S31's ten entries go after `legend_rows` (:1921), so the two sections' hunks are disjoint; `SchemeParser.text_ring: dict = {k: self._bounded_int(f"gridringstyle {k}_ring", d, 0, 9, "ring") for k, d in (("title", 7), ("subtitle", 6), ("caption", 5), ("note", 4))}` after `text_clock` (:10636). Run the generator twice; `git add -f test/fixtures/scheme_truth.json`.
- TR-30.8 **Added text `tstyle()`.** dash.ado `_dash_at_opts`: remove `tstyle` from the noted foreach (:7870-7874); dash_parse.mata `_dash_at_canon` (:9290): add `v = st_local("tstyle"); if (v != "") out = out + " tstyle(" + v + ")"` after the `color` line. dash_render.py: `_DASH_ADDED_TEXT_HONOURED` gains `"tstyle"`; `_dash_added_text_opts` (:37417) resolves `o.get("tstyle")` through `scheme.textbox_style(name)` into `base_pt`/`base_color` before `size`/`color` (unknown name: the D-30.d note). Both modes share these module functions (copy list already carries them).
- TR-30.9 **`$name` expansion (D-30.e).** dash_parse.mata: new `string scalar _dash_at_globals(string scalar s)` after `_dash_at_orient` (:9220-9260): a loop over `regexm(s, "\\$(\\{([A-Za-z_][A-Za-z0-9_]{0,31})\\}|([A-Za-z_][A-Za-z0-9_]{0,31}))")` replacing each match with `st_global(name)` (bounded total length 4,000 characters; a result over it is cut and the copy is refused r(198) with dash's one sentence `text(): expanded text is too long`); `$$` and a `$` followed by anything else unchanged. Called from `_dash_at_copy` (:9156) on each line of the copy's text before `_dash_at_opts` runs (dash.ado:7912). Add `_dash_at_globals` to `_dash_require_mata`'s `_needed` list (dash.ado:448-479, alphabetical), the dash_parse.mata header index and test/program_coverage_map.py (`"test_wp31_truth.cscript:U30-10"`).
- TR-30.10 **Copy lists (R2).** Functions tuple: `"_dash_textbox_style", "_dash_textbox_position", "_dash_textbox_insert",` after `"_dash_textbox_place",` (:47213). No new constant (the honoured set is already listed, :46634). test/function_test_map.py: the three names -> `test/test_textbox_placement.py::TestPlacement::test_clock_table`, `::TestBox::test_box_props`, `::TestRingOrder::test_rings_on_one_side`.
- TR-30.11 **Help (R3).** The title/subtitle/note/caption paragraph (under `{marker region_options}`; S27 added "Edge titles" beside it) gains "Textbox options": the honoured list, the clock table with the side rule and its measured example, ring(0)/position(0), the box options, `tstyle()`, and the named three. The `{marker added_text}` section (:583) gains `tstyle()` and the `$name` rule. Unsupported section: no paragraph names these sub-options today (they are reported by the generic note); test_help_conformance.py's definition check (:825) needs an entry for `tstyle` if it lists sub-options (the executor runs it). TWOWAY_COVERAGE_AUDIT.md:136 "most textbox suboptions are warned and ignored" gains `[WP-31 D3: corrected -- placement, box and style sub-options drawn; orientation(), width(), height() named]` and the added-text line `[WP-31 D13: corrected -- tstyle() drawn, globals expanded]` (no sha in a document line, DECISIONS A11).

## Boundaries

- Does not edit `_dash_apply_legend`, `_dash_move_legend`, `_dash_scheme_chrome`, `_DASH_LEGEND_*` (S31, same batch), `_dash_edge_titles` (S27), `_dash_by_panel_label`/`apply_to_figure`'s scheme placement, `_FILTER_JS` (S29), `_make_figure_body`, the served template, `_dash_option_rules`, any axis code.
- Does not draw `orientation()`, `width()`, `height()` on titles (documented), nor `angle()`/`blstyle`-family tokens.
- Never evaluates user text: no `display`, no `=` expression, no command line.

## Stata truth

Script `scripts/extract_textbox_truth.do` -> `test/fixtures/textbox_truth.json` (R7 form; `sysuse auto`; each `quietly twoway scatter mpg weight, <opts> name(u30k, replace)` then class values; SVG where geometry is needed):

| key | options | values |
|---|---|---|
| pos_k (k in 0..12) | `title("T", position(k))` | `.u30k.title.position`/`.ring` members (recorded via `classutil describe`), SVG x/y of "T" relative to the plot region box |
| ring0_k (k in 1,3,6,9,12) | `note("N", ring(0) position(k))` | SVG x/y of "N" inside the plot region |
| span_pos0 | `title("T", position(0) span)` | the logged note line (expect "(option span ignored for position(0))") |
| box | `caption("C", box bcolor(gs14) lcolor(red) lwidth(thick) margin(medium))` | SVG rect fill/stroke/stroke-width around "C" |
| tstyle_heading | `note("N", tstyle(heading))` | SVG font-size of "N" (expect heading's) |
| tstyle_bad | `note("N", tstyle(nosuch))` | `_rc` and the logged note (expect the "named style ... not found in class textboxstyle" text) |
| at_tstyle | `text(30 2000 "P", tstyle(heading))` | SVG font-size |
| global_plain | `global u30x "hello"` then `text(30 2000 "\$u30x")` (the `\$` escape keeps the do-file's own macro expansion off the probe, so twoway receives the literal `$u30x`; the script records the command string twoway ran in the row's `command` member) | SVG text; `command` |
| global_dollars | `global u30f "F"` then `text(30 2000 "\$\$u30f\$\$")` (escaped the same way) | SVG text, recorded verbatim; `command` |
| global_braces | `text(30 2000 "\${u30x}!")` (escaped) | SVG text; `command` |
| linegap_3 | `note("N1" "N2", linegap(3))` vs `note("N1" "N2")` | SVG y delta between the two lines, divided by the font size (the `text_line_height` rule of D-30.d) |

Run `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s30 $WT/scripts/extract_textbox_truth.do`; `git add -f`. `test_textbox_placement.py::TestTheFixture` names it. The three `global_*` rows write their probes with `\$` escapes (or `macval()`), because an unescaped `$u30x` expands in the do-file before twoway sees it; the fixture row's `command` member is the string twoway ran (R3c-F15).

## TDD test stubs

### Regression tests, `test/test_textbox_placement.py` (new; red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, go)`; `_box(fig, key)` returns the model tagged `["dash_textbox", key]` and its panel/ring; fixture at module level; drawing classes parametrized by mode.

- Test: fixture stamped and complete -- `TestTheFixture::test_meta_is_stamped`, `::test_every_case_was_measured` (guard after 30-01).
- Test: `title("T", position(k))` for k in 1..12 lands on `_dash_textbox_place(k, just)`'s side with its align, and `fig.title is None` -- `TestPlacement::test_clock_table[mode-k]` (red: title stays above, note printed).
- Test: `note("N", ring(0) position(k))` draws a `Label` in `fig.center[0]` with `Node` x/y symbols and anchor of D-30.b -- `TestInside::test_ring0_anchor[mode-k]` (red); `position(0)` is the centre -- `::test_position0_is_centre[mode]` (red).
- Test: `title("T", position(0) span)` prints twoway's note once -- `::test_span_at_zero_notes[mode]` (red).
- Test: on one side, title (7) outside subtitle (6) outside legend (3) outside t2title (2) outside t1title (1) -- `TestRingOrder::test_rings_on_one_side[mode]` (red); a `ring(2)` subtitle sits inside every `dash_textbox` box of ring 4+ and outside the edge titles (panel index order among the textbox and edge-title models only) -- `::test_user_ring_moves_inside[mode]` (red). The legend-relative order of a ring <= 3 box is S31's pin (`_dash_move_legend`'s `ring=<n>` skip, TR-31.2) and is not asserted here, so the D3 commit is green without S31.
- Test: `caption("C", box bcolor(gs14) lcolor(red) lwidth(thick) margin(medium))` -> `border_line_color` red, `background_fill_color` gs14's hex, `border_line_width` the thick px, `padding` the medium ladder px; `nobox` -> both None -- `TestBox::test_box_props[mode]`, `::test_nobox[mode]` (red).
- Test: `justification(left)` -> align left; `alignment(top)` -> `vertical_align == "top"` on a side `Title`, and on a ring-0 `Label` an anchor starting `top_` (parametrized by model type, R3-06); `linegap(3)` -> `text_line_height` equals the fixture's `linegap_3` rule (`1.2 + gap_pt/size_pt` or measured) -- `TestTextProps::test_each[mode-sub]` (red).
- Test: `tstyle(heading)` on note gives heading's size/colour; `size(small)` still wins; `tstyle(nosuch)` draws the default and notes twoway's words once -- `TestTstyle::test_base_style[mode]`, `::test_size_wins[mode]`, `::test_unknown_named_once[mode]` (red).
- Test: `orientation(vertical)`, `width(20)`, `height(5)` are named once and the box drawn -- `TestStillNamed::test_named_once[mode-sub]` (guard for the naming; red for "drawn" today? no: drawn today too -- guard).
- Test: no note for any honoured sub-option -- `TestSilentWhenHonoured::test_no_note[sub]` (red).
- Test: economist's in-band note keeps its Label band -- `TestEconomistBandUnchanged::test_band[mode]` (guard).
- Test: a by() graph draws the boxes once on the chrome rows, ring-0 boxes on no panel twice -- `TestOnAByGraph::test_once[mode]` (red).
- Test: hostile sub-option values (`lcolor(</script>)`, `tstyle(<img>)`) reach no HTML and the model's text is the raw user text -- `TestHostile::test_values_do_not_reach_html` (guard).
### Regression tests, `test/test_added_text_style.py` (new in 30-04; D13; red at the D3 tree)

- D13: `text(30 2000 "P", tstyle(heading))` draws heading's size in both modes; `_DASH_ADDED_TEXT_HONOURED` has `tstyle` -- `TestAddedTextTstyle::test_drawn[mode]` (red).
- D13: `$u30x`, `${u30x}` substituted (fixture `global_plain`/`global_braces`), `$$u30f$$` as the fixture's `global_dollars` -- `TestGlobals::test_substituted[case]` (red; runs the parser through `_dash_serve_spec`'s spec JSON written by the probe, module docstring names the commands).
- D13: a global holding `` `=1+1' `` or `` `c(pwd)' `` is drawn verbatim (not evaluated) -- `TestGlobalsAreSubstitutedNotEvaluated::test_raw` (red: the text is the literal `$name`; after the fix the raw value).

### Cases in cscripts

- `test/test_wp31_truth.cscript` block `* ==== S30 D3: Textbox placement ====`: U30-1 (position 3/6/9/12 title: twoway's SVG side vs dash's panel), U30-2 (ring(0) anchors), U30-3 (box rect fill/stroke vs dash's props), U30-4 (tstyle heading size), U30-5 (ring order in SVG y vs dash panel index), U30-6 (by(): once); block `* ==== S30 D13: Added text style and globals ====`: U30-9 (at_tstyle), U30-10 (global_plain), U30-11 (global_dollars/braces).
- `test/test_option_validation.cscript`: U30-7 (`position(0) span` note text equal), U30-8 (`tstyle(nosuch)` note text equal, `_rc` equal).

### Flips (in place, each with a `Flipped:` line)

- test_graph_options.py / test_axis_options.py nodes asserting that `position()`/`ring()`/`box` on a main box is named (grep `"position(" ` in those files; each flips to the drawn expectation).
- The added-text test asserting `tstyle()` is named (grep `tstyle` in test/test_added_text*.py) flips to "drawn".
- test_help_claims_*.cscript cases pinning the note text for these sub-options flip in place under their own ids with a comment `* flipped WP-31 D3`.

### Parity corpus (R8; appended, guards at base)

test_mode_parity.py under `# WP-31 D3/D13 (section 30): textbox placement`: `CORPUS` cases `"title position(6) subtitle ring(0) pos(1) caption box"`, `"note tstyle(heading) margin(medium)"`, `"text() tstyle(heading)"`; `MOVE_CORPUS` case `_move_case("ring(0) note after a dropdown move (WP-31 D3)", _MOVES[0], [plot_for("scatter")], go={"note": "N, ring(0) position(1)"})`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Clock table placement | pytest + U30-1 | textbox_truth.json | yes |
| ring(0)/position(0) Labels | pytest + U30-2 | textbox_truth.json | yes |
| Box/fill/border/margin | pytest + U30-3 | textbox_truth.json | yes |
| Ring order on a side | pytest + U30-5 | -- | yes |
| tstyle on boxes and added text | pytest + U30-4/U30-9 | textbox_truth.json | yes |
| Notes for span@0 and unknown style | cscript U30-7/U30-8 | live twoway | n/a |
| Global substitution, never evaluated | pytest + U30-10/U30-11 | textbox_truth.json | n/a (parser) |
| Help/audit agree | pytest test_help_conformance.py | -- | n/a |

Acceptance: AC-30.1 every red stub green in both modes; AC-30.2 U30-1..U30-11 PASS, no SKIP; AC-30.3 guards green (economist band, hostile values); AC-30.4 test_csp.py, test_label_sinks.py, test_scheme_chrome.py green; AC-30.5 two green commits `(WP-31 D3)`, `(WP-31 D13)`.

## Tasks

**Commit boundary.** 30-01..30-03 form the D3 commit, subject `Draw title, subtitle, note and caption textbox options where twoway draws them (WP-31 D3)`; 30-04 forms the D13 commit, subject `Draw added-text tstyle() and expand globals at registration (WP-31 D13)`; both on `wp31-s30` in `$WT`. Bodies per BRIEF: the saved failure text, the measured defect, what changed where (both modes), `Regression:` lines, `Flipped:` lines, `Fixture: test/fixtures/textbox_truth.json (scripts/extract_textbox_truth.do)` and `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)` (D3), `BUGS.md: "<title>" (closed)`, `GAPS3: D3 Tracked` / `GAPS3: D13 Tracked`. CHANGELOG: D3 Results `dash scatter mpg weight, title("T", position(6)): title above, note printed -> title below the plot region (WP-31 D3)`; D13 Results `dash scatter mpg weight, text(30 2000 "$x"): drew $x -> draws the global's value (WP-31 D13)`. No tooling names.

<task type="auto" id="30-01">
  <name>Measure twoway and write failing D3 tests</name>
  <files>scripts/extract_textbox_truth.do, test/fixtures/textbox_truth.json, test/test_textbox_placement.py</files>
  <action><![CDATA[
    Check the cut (`wp31-s30`, batch-10 base sha); `mkdir -p <scratch>/s30`. Create scripts/extract_textbox_truth.do (head from scripts/extract_default_base_truth.do:21-48) with every row of "Stata truth", SVG exports read through cert_svg.do's reader, `classutil describe .u30k.title` in `_meta.members`; run it through `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s30 ...`; `git add -f test/fixtures/textbox_truth.json`. Create test/test_textbox_placement.py with exactly the D3 classes of "TDD test stubs" (not the D13 classes: 30-04 creates test/test_added_text_style.py, DECISIONS A14); run `python3 -m pytest test/test_textbox_placement.py -q -n0 -p no:cacheprovider -rf > <scratch>/s30/30-01.log 2>&1`; write `<scratch>/30-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/textbox_truth.json'));print(sorted(d['_meta'])[:4], d['span_pos0']['note'][:12], d['global_plain']['text'])"` prints `['born_date', 'dash_commit', 'extracted', 'members'] (option span hello`; `grep -c FAILED <scratch>/s30/30-01.log` is at least 25; no FAILED line names TestTheFixture, TestEconomistBandUnchanged, TestHostile or TestStillNamed; `test -s <scratch>/30-01-failure.txt`.]]></verify>
  <done>twoway's textbox placement, box geometry, style notes and global expansion were recorded in a stamped fixture, and every D3 regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="30-02">
  <name>Wire placement, box and tstyle on the main boxes</name>
  <files>dash_render.py, scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Apply TR-30.1 to TR-30.5, TR-30.7 and TR-30.10 in dash_render.py: the honoured set (:37117); `_dash_textbox_style`, `_dash_textbox_position`, `_dash_textbox_insert` after `_dash_textbox_place` (:37286) with imports inside; `SchemeParser.text_ring` after `text_clock` (:10636); rewrite `_dash_figure_title` (:37180-37213) and `_dash_text_annotations`' model construction (:37394-37413) around the helpers, keeping `in_band`, `sides` and the by() subtitle rule; the three copy-list names after `"_dash_textbox_place",` (:47213) and the function_test_map.py entries. Apply TR-30.7 to scripts/extract_scheme_truth.py (the four `gridringstyle` directives in the new `group(["Textbox rings."], [...])` after the legend group :2221-2225 and the four truth entries before `"legend_position"` :1914; `legend_ring` is S31's), run the generator twice with `--out test/fixtures/scheme_truth.json`, `git add -f` the fixture. Run `python3 -m pytest test/test_textbox_placement.py test/test_graph_options.py test/test_scheme_chrome.py test/test_edge_titles.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "not Chrome" > <scratch>/s30/30-02.log 2>&1`; flip the red pins named in "Flips" in place with the reason in their docstrings.
  ]]></action>
  <verify><![CDATA[`grep -c "gridringstyle note_ring 4" dash-*.scheme | grep -vc ":1$"` prints 0; `python3 -c "import dash_render as d; print(sorted(d._DASH_TEXTBOX_HONOURED)[:3], 'position' in d._DASH_TEXTBOX_HONOURED)"` prints `['alignment', 'axis', 'bcolor'] True`; `grep -c FAILED <scratch>/s30/30-02.log` prints 0 after the flips.]]></verify>
  <done>Both renderers placed the four main boxes by the user's clock and ring, drew ring-0 boxes inside the plot region, drew box, fill, border, margin, justification, alignment, linegap and tstyle() as twoway does, and every scheme carried the ring stubs.</done>
</task>

<task type="auto" id="30-03">
  <name>Certify, document and commit D3</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[
    Append the S30 D3 block (`* ==== S30 D3: Textbox placement ====`, U30-1..U30-6) above the marker line and U30-7/U30-8 to test_option_validation.cscript (`*! U30-7..U30-8` header lines); drivers per BRIEF with `WP31_ONLY=S30`; run both through the slot. Append the parity cases (R8). Apply TR-30.11's D3 half to dash.sthlp and TWOWAY_COVERAGE_AUDIT.md. Close the D3 BUGS.md entry, rewrite `D3 Tracked` to the Closed form ending `commit pending.` (DECISIONS A11; the merger's step k.3b writes the sha), replace `<!-- WP-31 D3 -->`. Run `python3 -m pytest test/test_textbox_placement.py test/test_help_conformance.py test/test_tracking_documents.py test/test_label_sinks.py test/test_csp.py -q -p no:cacheprovider`; `git add -A`; commit with the D3 body; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.
  ]]></action>
  <verify><![CDATA[`grep -c "U30-[1-8] PASS" <scratch>/s30/*.log` sums to 8, `grep -c SKIP <scratch>/s30/run_truth.log` prints 0; `grep -c "Textbox options" dash.sthlp` is at least 1; `grep -c "^- \*\*D3 Tracked:\*\* Closed in WP-31.*commit pending\.$" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 D3)`.]]></verify>
  <done>D3 was certified against twoway, documented, tracked and landed as one green commit on wp31-s30.</done>
</task>

<task type="auto" id="30-04">
  <name>Draw added-text tstyle, expand globals, commit D13</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[
    Create test/test_added_text_style.py with exactly the D13 classes of "TDD test stubs" (`TestAddedTextTstyle`, `TestGlobals`, `TestGlobalsAreSubstitutedNotEvaluated`); run `python3 -m pytest test/test_added_text_style.py -q -n0 -p no:cacheprovider -rf > <scratch>/s30/30-04-base.log 2>&1` on the D3 tree and write `<scratch>/30-04-failure.txt` (every node must be red). Apply TR-30.8 (dash.ado :7870-7874; dash_parse.mata `_dash_at_canon` :9290; dash_render.py `_DASH_ADDED_TEXT_HONOURED` :37323 and `_dash_added_text_opts` :37417) and TR-30.9 (`_dash_at_globals` after `_dash_at_orient`, its call in `_dash_at_copy`, the `_needed` list dash.ado:448-479, the header index, program_coverage_map.py). Append the S30 D13 block (`* ==== S30 D13: Added text style and globals ====`, U30-9..U30-11) above the marker line and run it (`WP31_ONLY=S30`). Flip the `tstyle` pin named in "Flips". Apply TR-30.11's D13 half (added_text help section; audit line). Close the D13 BUGS.md entry, rewrite `D13 Tracked` to the Closed form ending `commit pending.` (A11), replace `<!-- WP-31 D13 -->`. Run `python3 -m pytest test/test_textbox_placement.py test/test_added_text_style.py test/test_added_text*.py test/test_program_coverage_map.py test/test_tracking_documents.py -q -p no:cacheprovider`; commit with the D13 body; no tooling names.
  ]]></action>
  <verify><![CDATA[`grep -c "U30-\(9\|10\|11\) PASS" <scratch>/s30/run_truth.log` prints 3; `grep -c "_dash_at_globals" dash.ado dash_parse.mata test/program_coverage_map.py | awk -F: '{s+=$2} END {print s}'` is at least 4; `grep -c "^- \*\*D13 Tracked:\*\* Closed in WP-31.*commit pending\.$" GAPS3.md` prints 1; `git show --stat HEAD | grep -c test_added_text_style.py` prints 1; `git log -1 --format=%s` ends `(WP-31 D13)` and `git log -2 --format=%s | tail -1` ends `(WP-31 D3)`.]]></verify>
  <done>Added text drew tstyle() through the scheme's textbox styles and expanded globals by substitution at registration, certified against twoway and landed as the D13 commit.</done>
</task>

## Section completion criteria

- The honoured textbox set of TR-30.1 is drawn on title, subtitle, note and caption in both modes; `orientation()`, `width()`, `height()` are named and documented.
- Clock placement, ring(0)/position(0) Labels, ring order, box geometry and tstyle() match the fixture; twoway's two notes are reproduced word for word.
- Added text draws `tstyle()`; `$name`/`${name}` are substituted, never evaluated; `$$` follows the measured form.
- Every scheme carries the ring stubs; U30-1..U30-11 PASS; flips recorded; help, audit, BUGS.md, GAPS3 §9 and CHANGELOG updated in two commits.

## Notes

- **Renderer order.** `_dash_figure_title` then `_dash_text_annotations` in both modes; ring-0 Labels go to `fig.center[0]` for the Span-order reason at :37356-37360.
- **Copy lists (R2):** three functions after `"_dash_textbox_place",` (:47213); `SchemeParser.text_ring` and `textbox_style` travel with the class.
- **R12:** S30 edits none of the hot functions; no template line (both modes call the module functions already).
- **R6:** `_dash_at_globals` is Mata: `_needed` list, header index, program_coverage_map; no new ado program.
- **R1:** two blocks (D3, D13) in the truth script, both under S30's header region; two refusal/note cases in test_option_validation.cscript.
- **R3:** S30 owns the "Textbox options" paragraph and the added_text section's two additions; S27's "Edge titles" paragraph is not edited.
- **R7:** `textbox_truth.json` new; `scheme_truth.json` and the 26 `dash-*.scheme` files regenerated. S30's generator edit is the new `Textbox rings.` directive group and four truth entries before `legend_position`; S31's is the legend group (`legend_ring` included) and ten entries after `legend_rows` -- disjoint hunks (DECISIONS A31). Merger rule (index.md:145): apply S29 and S30 whole; produce S31's diff with `git -C <wt> diff -- . ':(exclude)dash-*.scheme' ':(exclude)test/fixtures/scheme_truth.json'`, apply it, then run the generator once after the batch-10 merge (`scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`, twice, `git add -f test/fixtures/scheme_truth.json`).
- **Security (rule 1):** `_dash_at_globals` reads `st_global` only; no user text is written to a command line; colour and style names reach Bokeh only through the colour grammar and `textbox_style`'s bounded name check.
- **python_exec hazard** as in every section.
- **For S31 (same batch):** `_dash_textbox_insert` writes `ring=<n>` tags; S31's TR-31.2 makes `_dash_move_legend`'s insertion index skip, besides axes and `dash_edge_title` models (S27 D-27.b), every model whose tags hold `ring=<n>` with n <= 3 (R3c-F8, DECISIONS A31), so a user `ring(2)` box sits inside the legend in both modes once both land; S30 asserts only the textbox/edge-title order.
- **Decisions for maintainer ratification:** D-30.c (`span`/`bexpand` honoured as no-ops; the unspanned narrower box is the documented difference) and D-30.e (the `$$` form follows the fixture's `global_dollars` row) are this file's rulings within M17; ratify before batch 10.

## Addendum (15oct2026, DECISIONS D21): row D2b added to this section

### D2b: Edge titles name position(), ring(), span and orientation() where twoway draws them

**Gap.** S27 draws the eight edge titles (`_dash_edge_titles`, `_DASH_EDGE_TITLES`, `SchemeParser.edge_title_styles`) at their default places and names `position()`, `ring()`, `span` and `orientation()` given inside them.

**Requirement.** Measure twoway's placement of each edge title under those sub-options (SVG positions, rotation), and route them through `_dash_textbox_place` exactly as this section does for title()/subtitle()/note()/caption(), both modes; nothing named once drawn.

**Fits S30** because S30 wires user position() and ring() through `_dash_textbox_place` for titles and owns the textbox placement code in batch 10.

**Process (binding).** As every row: measure twoway first (the measurement wins over this text; record a deviation); failing tests first with saved failure text; ONE commit with subject ending `(WP-31 D2b)`; close the BUGS.md entry "Edge titles name position(), ring(), span and orientation() where twoway draws them" (Resolution ending `Closes GAPS3 D2 (WP-31, D2b).`), delete its `"D2b":` WP31_OPEN line, rewrite GAPS3.md's `- **D2b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 D2b -->` under `### Results that change` with a line ending `(WP-31, D2b)`. dash replaces twoway (D13).

