# Section 41-06: by() panel-label sub-options and raw values

> Part of: WP-41 (by() fidelity, P6) · Items: BY-10, BY-16 · Risk: yellow · Batch: 41.1 · Depends on: none · Blocks: 41-02 · Tasks: 5, 2 commits · Case-id prefix: Q4106

## Overview

**What is wrong today.**
- **BY-10.** "Panel-label sub-options twoway draws are named: justification(), nobexpand, lwidth()/lpattern(), span, alignment(), linegap(), bmargin(), placement(), orientation()". Measured by the audit on stcolor: `subtitle(, justification(left)) by(foreign)` "left-aligns the labels (x 570 vs 1652)"; `subtitle(, nobexpand)` "shrinks the label box to the text (width 484 vs 2197)"; `subtitle(, lwidth(vthick) lcolor(black))` "outlines the box (stroke 38.6)"; `subtitle(, span)` "widens the box over the y-axis area (x 339..2863)"; `subtitle(, alignment(top) height(15))` "moves the text (y 242 vs 258)"; "Width and height alone draw no difference, P4==P0". dash: "Each is named 'subtitle() sub-option(s) not implemented and ignored', and the label is drawn centred with a full-width box." Cause: `_dash_by_panel_label` (dash_render.py:54861) passes only `_DASH_BY_LABEL_BOX_WORDS + ("position", "ring", "bexpand", "nobexpand")` as extra (:54883-54886) and names `nobexpand` outside ring(0) (:54926-54928); `_dash_by_label_box` (:56028) draws a full-width horizontal ColorBar with the text left (`t = 0.0 if align == "left" else 0.5`, :56099-56100) or centred.
- **BY-16 (with BY-17).** "a date variable is written as dates (twoway writes 14610); a value label holding double quotes stays one line". `_dash_facet_label` (:37067) titles a date panel through `date_formatter` (:37128-37132); a quoted value label is one string.

**After this section.** The panel label row draws justification(), nobexpand, the box outline's lwidth()/lpattern(), span, alignment() with height(), linegap(), bmargin(), placement() and orientation() as twoway draws them, in both modes; width() and height() alone are taken in silence (twoway draws nothing different); a date by() variable's panels read its Stata number (subtitleformat(var) still gives the formatted date, as twoway); a value label holding quoted parts is drawn one line per part.

**Why together.** Both items are the panel label row: its text (BY-16) and its box (BY-10). 41-02 (batch 41.2) builds on the label row for its titles and depends on this section.

**Test order and commit rule.** BY-10 first: 41-06-01 measures both items into one fixture and writes BY-10's failing tests (no commit); 41-06-02 draws them and commits `(WP-41 BY-10)`. 41-06-03 writes BY-16's failing tests (no commit); 41-06-04 fixes and commits `(WP-41 BY-16)`. 41-06-05 is the maintainer checkpoint on the browser screenshots. No full suite inside the section.

### Section decisions

- **D-41-06.a -- the box stays a ColorBar; nobexpand uses the Title.** The expanded box stays `_dash_by_label_box`'s ColorBar (the one Bokeh model that spans the frame and outlines four edges, its docstring). Under `nobexpand` (ring above 0) the ColorBar is not built: the `dash_by_label` Title is shown with `background_fill_color` = the box fill, `border_line_color/width/dash` = the outline and `padding` = the box margin -- a Title's background covers its text only, which is nobexpand's box (measured in the docstring of `_dash_by_label_box`).
- **D-41-06.b -- layout-time placement.** justification() and placement() insets and `span` need the frame's pixel width, known only after layout: `_DASH_SPAN_JS` gains one item kind `"bylabel"` (`[cb, "bylabel", just, inset_rel, span_flag, "", 0, ""]`) that sets the ColorBar's one tick to `inset_px / W` (left), `1 - inset_px / W` (right) or `0.5`, and for span sets `cb.width` to the panel canvas's width and `cb.location` to `[-left_border, 0]`. Registered through `_dash_span(fig, cb, "bylabel", ...)` (dash_render.py:38984), so both modes and resizes follow.
- **D-41-06.c -- placement() under an expanded box** changes nothing unless the fixture's L13 differs from L00; then it moves the text as justification() does. Under nobexpand it is the Title's `align` (e/ne/se right, w/nw/sw left, else center).
- **D-41-06.d -- raw value.** A date by() variable with no value label is written as Stata writes the number into a macro (`14610`), from its Stata units (`_dash_date_units`); a value label still wins; `subtitleformat(var)` writes the variable's display format (dates), as today's subtitleformat path does.
- **D-41-06.e -- quoted parts.** A label (value label or raw string) whose text parses as two or more Stata double-quoted or compound-quoted strings (`"a" "b"`, `` `"a"' `"b"' ``) is drawn one line per part, joined with "\n" in the Title and the ColorBar's tick label; the box height grows by `(lines - 1) x (font x linegap factor)`.

## Risk: [yellow] -- every by() graph's label row, both modes

**Why.** Every by() panel draws a label; a mistake moves every label. The ColorBar trick is fragile in BokehJS.

**Risk factors.** 1. `_DASH_SPAN_JS` is shared by legends, titles and keys; a new kind must not touch other items. 2. A multi-line ColorBar tick label needs `major_label_text_line_height`; check in headless Chrome. 3. orientation(vertical) turns the text: the ColorBar's label angle is not a Bokeh property, so vertical labels use the Title path with a turned `Label` (see TR-41-06.6).

**Mitigation.** Chrome checks in both modes for L01, L03, L06, L07, Q01 (test_legend_span_browser.py's harness); unit tests on each property; the default label (no sub-option) is a guard that must not move (L00).

## Dependencies

- **Depends on:** none.
- **Blocks:** 41-02 (draws by()'s edge titles beside the label row).
- **Parallel batch:** 41.1 with 41-01 (owns `_FILTER_JS` and `_generate_app_source_body`) and 41-03 (owns `_dash_layout_cell` this batch).
- **Can run with:** both; this section edits `_dash_by_panel_label`, `_dash_by_label_box`, `_dash_by_label_inside`, `_dash_facet_label` and `_DASH_SPAN_JS` only.

## Evidence

- `_dash_by_panel_label(fig, label, graph_opts, scheme=None, seen=None, key="")` :54861-54960: `_dash_textbox_or_default(...)` :54883-54886; position/ring branch :54899-54919; margin named at ring(0) :54920-54924; nobexpand named outside ring(0) :54926-54928; the Title :54933-54944; `title._dash_box_opts` :54945-54946.
- `_DASH_BY_LABEL_BOX_WORDS` :55020-55026.
- `_dash_by_label_box(fig, scheme, mult=1.0)` :56028-56152: font and height `h = int(round(font + (top + bottom) * unit * mult))` :56096-56098; `align`/`t` :56099-56100; outline width `line = by_label_line_pt * px * mult` :56101; outline colour :56104-56126; the ColorBar :56128-56145 (`bar_line_color`, `bar_line_width`, `FixedTicker(ticks=[t])`, `major_label_text_align`, `label_standoff=int(-(h + font) // 2 - 2)`).
- `_dash_by_label_inside` :54963 (ring(0)).
- `_DASH_SPAN_JS` :38690, `_dash_span(fig, model, kind=None, side="", place="", offset=0.0, ref="", margin=0.0, mode="")` :38984 (items `[model, kind, side, place, offset, ref, margin, mode]`).
- `_dash_facet_label` :37067-37157: date branch :37128-37132; subtitleformat branch :37134-37150; plain text :37155.
- Bokeh 3.8/3.9 (checked): ColorBar has `bar_line_dash`, `bar_line_width`, `major_label_text_line_height`, `width`, `location`, `margin`; Title has `align`, `vertical_align`, `background_fill_*`, `border_line_*` (incl. `border_line_dash`), `padding`, `standoff`, `offset`, `text_line_height`; Label has `angle`.
- twoway: bygraph_g.class:497 (the label is the panel's subtitle(), before the user's options); RunGraph :427-497 (`: label (var) value`, quoting :456-492); textbox_options.sthlp.
- Fixtures: `by_remainder_truth.json` sub_pos*, sub_* (box colours, position, ring); `by_chrome_truth.json` label_box. No probe of the BY-10 words or of a date/quoted label.
- Pinned tests (flip in place): test/test_by_label_position.py and test/test_by_remainder.py may assert a named `nobexpand` or `margin` (grep `nobexpand\|not implemented` in both; flip only those whose word this section draws). test/test_by_text.py `TestOverallTextMatchesTwoway` (guard). Any test asserting a date panel reads `01jan2000`: `grep -rn "01jan2000\|02jan2000" test/ | grep -i "by\|facet"` -- flip each with the reason "twoway writes the number".

## User stories

- US-41-06.1 As the Stata user with an existing twoway command, I want `subtitle(, justification(left) nobexpand lwidth(thick) span)` on a by() graph to draw its panel labels as twoway draws them, so that my labels look the same.
- US-41-06.2 As the Stata user, I want a date by() variable's panels labelled as twoway labels them (14610), and a value label holding quoted parts split into lines, so that my panel titles read the same.

## Business requirements

- BR-41-06.1 Each listed sub-option changes the panel label row where twoway's does, within the fixture's tolerance (2 px on a 5400-unit canvas mapped to the page), with no note.
- BR-41-06.2 width() and height() alone, and placement() under an expanded box when twoway draws nothing different, are taken in silence.
- BR-41-06.3 A date by() variable with no value label titles its panels with the Stata number; subtitleformat(var) writes its display format.
- BR-41-06.4 A label of two or more quoted parts is drawn one line per part.

## Technical requirements

- TR-41-06.1 `_dash_by_panel_label`: extra words become `_DASH_BY_LABEL_BOX_WORDS + ("position", "ring", "bexpand", "nobexpand", "justification", "lwidth", "lpattern", "span", "alignment", "linegap", "bmargin", "placement", "orientation", "width", "height")` (the textbox reader's spellings; re-read `_DASH_TEXTBOX_HONOURED` :53826 for the canonical names). Remove the nobexpand note (:54926-54928). Store on the Title `title._dash_label_opts = {k: opts[k] for k in those eleven words if k in opts}`. justification -> `title.align` ("left", "right", "center"; twoway's `l`, `r`, `c` spellings through the existing `_dash_textbox_style` reader).
- TR-41-06.2 `_dash_by_label_box`: (a) `nobexpand` (and not ring(0)) -> no ColorBar: `title.visible = True`, `title.background_fill_color = fill`, `title.background_fill_alpha = 1.0`, `title.border_line_color = outline`, `title.border_line_width = round(line, 3)`, `title.border_line_dash` from lpattern, `title.padding = int(round((top + bottom) / 2 * unit * mult))`; return the Title. (b) lwidth(#|name) -> `line = OptionTranslator.translate_lwidth(...) * mult`, lpattern -> `box.bar_line_dash = OptionTranslator.translate_lpattern(<the word>)` (dash_render.py:9019, the translator lines use; re-read). (c) justification/placement -> `_dash_span(fig, box, "bylabel", place=<"left"|"right"|"center">, offset=<inset_rel>)` where inset_rel is the fixture's L01 `(text_x - box_x) / min(canvas_w, canvas_h)` recorded as a constant `_DASH_BY_LABEL_INSET_REL` beside `_DASH_BY_LABEL_BOX_WORDS`. (d) span -> the same item with `mode="span"`. (e) alignment(top|bottom|middle|baseline) with height(#): the box height `h = max(h, height_rs * unit * mult)`; `label_standoff` places the text's top at the box's inner top edge (top), its bottom at the inner bottom edge (bottom, baseline), centred otherwise -- `label_standoff = int(-(h + font) // 2 - 2)` is today's middle; top `= int(-h + top * unit * mult)`, bottom `= int(-font - bottom * unit * mult)`; check against L07/L08 within 2 px. (f) linegap(#) -> `box.major_label_text_line_height = 1 + linegap_rs * unit / font`; lines > 1 grow `h` by `(lines - 1) * font * box.major_label_text_line_height`. (g) bmargin(marginstyle) -> `box.margin` = the four sides' largest in px (`_dash_margin_sides` :40390) times mult. (h) width() and height() without alignment(): silent.
- TR-41-06.3 `_DASH_SPAN_JS` (:38690): a branch for `kind === "bylabel"`: `const fv = Bokeh.index.find_one(fig)`; `W = fv.frame.bbox.width`; the item's place `"left"` -> `cb.ticker.ticks = [Math.min(0.5, it[4] * Math.min(fv.bbox.width, fv.bbox.height) / W)]`, `"right"` -> `1 - that`, else `[0.5]`, setting `cb.major_label_text_align` to the place; mode `"span"` -> `cb.width = fv.bbox.width - (fv.bbox.width - fv.frame.bbox.right)` and `cb.location = [-(fv.frame.bbox.left), 0]`; write only on change (compare first), as the other kinds do.
- TR-41-06.4 orientation(vertical|rvertical) -> the label is drawn through `_dash_by_label_inside`'s Label path at the row (a `Label` with `angle = pi/2` or `-pi/2`, text at the box's centre), the ColorBar box kept for the fill with `h` = the text's width estimate `len(text) * 0.6 * font` (the overhangs estimate, :27730); horizontal/rhorizontal (`angle = pi`) the same. Pin against L14 within 4 px; if the fixture shows twoway draws L14 as L00, take it silently instead (D-41-06.c rule).
- TR-41-06.5 `_dash_facet_label`: the date branch (:37128-37132) runs only when `subtitle_format == "var"`; otherwise a date variable's value is converted with `_dash_date_units(np.array([val], float), _kind)[0]` and written by `GlyphMapper._mlabel_value_text(<stata number>, vlabels)` (the value label wins, else the macro form `14610`). Then (both for labels and strings) `parts.append(_dash_quoted_lines(text))`.
- TR-41-06.6 New `def _dash_quoted_lines(text)` after `_dash_facet_label`: when `text.strip()` is two or more Stata strings -- `"..."` or `` `"..."' `` separated by blanks, nothing else -- return them joined by "\n" (each unquoted); otherwise *text* unchanged. Linear; never raises. Copy list: `"_dash_quoted_lines",` after `"_dash_by_panel_label", "_dash_by_text_cell",` (:67464). function_test_map.py row.
- TR-41-06.7 Help (R3): dash.sthlp :3278-3287 rewritten to: "...and a date variable's with its number ({cmd:14610}), as {cmd:twoway} writes it ({cmd:subtitleformat(var)} writes its dates); ... A value label holding several quoted parts is drawn one line per part, as in {cmd:twoway}." and :5382-5385's "names the other placement and box sub-options" replaced by "draws {cmd:justification()}, {cmd:nobexpand}, {cmd:lwidth()}, {cmd:lpattern()}, {cmd:span}, {cmd:alignment()}, {cmd:linegap()}, {cmd:bmargin()}, {cmd:placement()} and {cmd:orientation()} on the label row as {cmd:twoway} does". Remove those words from the Unsupported list if listed.

## Boundaries

- Do not edit `_dash_layout_cell` (41-03 this batch), `_FILTER_JS` and `_generate_app_source_body` (41-01), `_dash_by_chrome` (41-02), `_dash_by_keys`/`_dash_by_side` (41-04).
- The stale sentence dash.sthlp:3290-3292 (BY-9) is 48-01's; the clock 3/9 beside-placement is 41-05's (BY-19).
- No change to the label at ring(0) beyond the new words (WP-31 D3b stays).

## Stata truth

New `scripts/extract_by_label_truth.do` -> `test/fixtures/by_label_truth.json` (skeleton of scripts/extract_by_text_truth.do; stcolor; `_meta` complete). Base `scatter mpg weight, by(foreign)`; each probe adds the graph option shown; from the SVG (scripts/svg_truth.py) record the label box rects (x, y, w, h, fill, stroke, stroke-width, stroke-dasharray), every label text (string, x, y, anchor, angle) and the panels' plot-region rects:

| id | option | id | option |
|---|---|---|---|
| L00 | (none) | L08 | `subtitle(, alignment(bottom) height(15))` |
| L01 | `subtitle(, justification(left))` | L09 | `subtitle(, height(15))` |
| L02 | `subtitle(, justification(right))` | L10 | `subtitle(, linegap(3))` with Q01's label |
| L03 | `subtitle(, nobexpand)` | L11 | `subtitle(, bmargin(medium))` |
| L04 | `subtitle(, lwidth(vthick) lcolor(black))` | L12 | `subtitle(, nobexpand placement(e))` |
| L05 | `subtitle(, lpattern(dash) lcolor(black))` | L13 | `subtitle(, placement(e))` |
| L06 | `subtitle(, span)` | L14 | `subtitle(, orientation(vertical))` |
| L07 | `subtitle(, alignment(top) height(15))` | L15 | `subtitle(, width(30))` |

Plus D01 `by(d)` with `gen d = mdy(1,1,2000) + foreign`, `format d %td`; D02 `by(d, subtitleformat(var))`; Q01 `label define ql 0 \x60"\"Dom\" \"estic\""\x27 1 "Foreign"`, `label values foreign ql`, `by(foreign)` (backticks written `\x60`). `git add -f`; name it in test/test_fixtures_are_committed.py.

## TDD test stubs

New `test/test_by_label_options.py` (`_MODES = ("saved", "served")`):
- BY-10: `TestLabelOptions::test_no_note[mode-L01..L15]` (no "subtitle() sub-option" warning; red for L01-L08, L10-L14), `::test_justification[mode]` (Title.align and the span item place; red), `::test_nobexpand_draws_the_title_box[mode]` (no ColorBar, Title visible with the box fill/outline; red), `::test_outline_width_and_pattern[mode]` (bar_line_width = translate_lwidth(vthick) x mult; bar_line_dash; red), `::test_span_item[mode]` (red), `::test_alignment_height[mode]` (label_standoff per TR-41-06.2(e); red), `::test_linegap[mode]` (red), `::test_bmargin[mode]` (red), `::test_orientation[mode]` (red), `::test_default_unchanged[mode]` (L00 guard).
- BY-10 browser (headless Chrome, both modes, the harness of test/test_legend_span_browser.py): `TestLabelOptionsInChrome::test_positions_match_twoway[mode-L01|L03|L06|L07]` -- the text's x (or y) and the box's width relative to the panel's plot region within 2 px after mapping the fixture's units to the page (red). Tier (REVIEW R3-39): every parameter but `[saved-L01]` is `pytest.param(..., marks=pytest.mark.release)`, so the default tier runs one Chrome case for the item and `make test-release` the rest; every targeted run in the tasks runs all of them.
- BY-16: `TestPanelValues::test_date_is_the_number[mode]` (D01 texts `14610`, `14611`; red), `::test_subtitleformat_var_keeps_dates[mode]` (D02; guard), `::test_quoted_parts_are_lines[mode]` (Q01: "Dom\nestic"; red), `::test_quoted_lines_unit` (`_dash_quoted_lines`; red).

cscript cases (test/test_wp41_truth.cscript `* ==== S06 BY-10: panel-label sub-options ====`, `* ==== S06 BY-16: panel label values ====`, each directly above the first `* ==== S` header numbered above 06, else above the marker):
The panel label's sub-option note ("subtitle() sub-option(s) not implemented and ignored", dash_render.py:53486) and the labels themselves are made by Python at build, which a `name()` registration never runs, so both cases build the page:
- Q4106-1 `dash clear`; `dash scatter mpg weight, subtitle(, justification(left) nobexpand) by(foreign) name(q1)` rc 0; `quietly log using "<tmp>/q1.log", text replace name(_q4106)`; `capture noisily dash build, saving("<tmp>/q1.html", replace) nobrowser` rc 0; `quietly log close _q4106`; `cert_log_has "<tmp>/q1.log", needle("not implemented")` (test/cert_helpers.do:182) with `r(found) == 0`. Red at base: the build names justification() and nobexpand.
- Q4106-2 D01 (`generate d = mdy(1,1,2000) + foreign`, `format d %td`): `dash scatter mpg weight, by(d) saving("<tmp>/q2.html", replace)` rc 0; a `python:` reader of the page (each `<script type="application/json" id=...>` block loaded with `bokeh.document.Document.from_json`, as test/test_wp29_truth.cscript's `_fx_plots_saved`, :1350, loads it) collects the text of every `Title` named `dash_by_label`; they are `14610` and `14611`, as twoway writes them. Red at base: they read 01jan2000 and 02jan2000.

Pinned tests to flip: the greps of Evidence.

Parity (R8): `_case("by() label justification(left) nobexpand", [plot_for("scatter", {})], go={"by": "foreign", "subtitle": ", justification(left) nobexpand"})`, `_case("by() date panels", ...)` built on a date column as the existing date-by entries are (grep `by` with a date in test_mode_parity.py).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| sub-options drawn, silent | pytest TestLabelOptions; Q4106-1 | L00-L15 | yes |
| positions | Chrome TestLabelOptionsInChrome | L01, L03, L06, L07 | yes |
| raw date, quoted lines | pytest TestPanelValues; Q4106-2 | D01, D02, Q01 | yes |
| parity | CORPUS | -- | yes |

- AC-41-06.1 Every red stub red at its base, green after; failure texts saved.
- AC-41-06.2 Q4106-1/2 PASS; Chrome tests pass in both modes.
- AC-41-06.3 test_by_label_position.py, test_by_remainder.py, test_by_text.py, test_legend_span_browser.py green.
- AC-41-06.4 BY-10 and BY-16 Tracked lines Closed.

## Tasks

**Commit boundary.** 41-06-01/02: `Draw the by() panel label's sub-options as twoway draws them (WP-41 BY-10)`; 41-06-03/04: `Write by() date panels as numbers and split quoted labels into lines (WP-41 BY-16)`. 41-06-05 checkpoint. Branch `wp41-s06`; `$WT` is the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp41-s06` (BRIEF "Pull form": commands use this absolute path). Before each commit: run `git pull --ff-only . main` in $WT (CLAUDE.md rule 4; BRIEF "Pull form": `Already up to date.` when the batch base already contains main; if it refuses, stop and report to the orchestrator, never a merge commit on a section branch), run `gitnexus detect-changes --scope all --repo .` in $WT (the global CLI; `.gitnexus/` is git-ignored and absent from a worktree; re-run when it reports `partial` or `truncated`) and `python3 -m pytest test/test_cscript_hygiene.py -k "TestTheWpTruthScripts and wp41" -q -n0`.

<task type="auto" id="41-06-01">
  <name>Measure labels and write BY-10 tests</name>
  <files>scripts/extract_by_label_truth.do, test/fixtures/by_label_truth.json, test/test_by_label_options.py</files>
  <action><![CDATA[Create scripts/extract_by_label_truth.do with every probe of "Stata truth" (L00-L15, D01, D02, Q01), run it through `scripts/stata_slot.sh`, `git add -f` the fixture and name it in test/test_fixtures_are_committed.py's list (41-01 and 41-03 append to the same list in 41.1: the merger needs that file in picks.sh's `addmerge.py ours-first` list -- name it in the hand-back); record L01's `(text_x - box_x) / min(canvas_w, canvas_h)` and whether L13 equals L00 and L14 equals L00 in `<scratch>/41-06-measured.txt`. Create test/test_by_label_options.py with the BY-10 stubs (unit and Chrome). Append the S06 BY-10 block (Q4106-1) to test/test_wp41_truth.cscript. Run `python3 -m pytest test/test_by_label_options.py -k "LabelOptions" -q -n0 -rf > <scratch>/41-06-01-failure.txt 2>&1; true` and the block (`WP41_ONLY=S06`), appending its FAIL line. Do not commit.]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/by_label_truth.json'))['probes'];print(p['D01']['texts'][:2], p['L03']['boxes'][0]['w'] < p['L00']['boxes'][0]['w'])"` prints `['14610', '14611'] True`; `grep -c FAILED <scratch>/41-06-01-failure.txt` is at least 10; the file holds `Q4106-1 FAIL`.]]></verify>
  <done>twoway's panel-label drawing was recorded in a stamped fixture and BY-10's tests were shown failing on the base.</done>
</task>

<task type="auto" id="41-06-02">
  <name>Draw the label sub-options and commit</name>
  <files>dash_render.py, dash.sthlp</files>
  <action><![CDATA[Run `gitnexus impact _dash_by_panel_label --direction upstream --repo dash`, the same for `_dash_by_label_box`, `_dash_by_label_inside` and `_dash_span`; report HIGH or CRITICAL (an UNKNOWN result is confirmed with `grep -n`). Apply TR-41-06.1 to TR-41-06.4 and TR-41-06.7's BY-10 sentence, with `_DASH_BY_LABEL_INSET_REL` = the measured L01 value and the L13/L14 rules of D-41-06.c as measured. Flip the pins the greps found (R9). Run `python3 -m pytest test/test_by_label_options.py -k LabelOptions -q -n0`, then, with no `-k` (a `-k` applies to every file on its command line and would deselect the pins this task flips), `python3 -m pytest test/test_by_label_position.py test/test_by_remainder.py test/test_by_text.py test/test_legend_span_browser.py -q -n0`, and the S06 block. Append the parity entry to test/test_mode_parity.py's `CORPUS` (R8). Close BY-10 (BUGS PD-4, Tracked, GAPS4_OPEN, CHANGELOG under `### Fixed in WP-41`: "by() panel labels draw subtitle()'s justification(), nobexpand, lwidth(), lpattern(), span, alignment(), linegap(), bmargin(), placement() and orientation(), which were named and ignored (WP-41, BY-10)"). The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h), before the commit: (1) run `awk -F'\t' '$1 == "BY-10" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the plain rows; a `BY-10 (documented)` or `BY-10 (residual)` row stays, A-10) and `git add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py BY-10` and delete every `<file>:<line>` row it prints from its `*_KNOWN` table (staging each file it edits) -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion 33-10 names (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`; `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN`, e.g. `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `ABBREV_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (D-33-10.a; no ruling of this section keeps one, so none is expected: the label sub-options are drawn as twoway draws them (D-41-06.a to D-41-06.c)) -- then rerun, with no `-k`, each test file whose table it edited (its comparison reads the table, so a deleted row whose difference remains fails there) and run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); both pass; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the driver) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`, D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes) and add its `Fixture:` line to the commit body. Then the Commit boundary's pre-commit checks: `git pull --ff-only . main` in $WT (BRIEF "Pull form"; `Already up to date.` at the batch base; a refusal stops the task and is reported), `gitnexus detect-changes --scope all --repo .` and, when a cscript changed, the hygiene test the Commit boundary names. Commit per BRIEF; grep the message.]]></action>
  <verify><![CDATA[Both pytest runs report 0 failed; `Q4106-1 PASS`; `awk -F'\t' '$1 == "BY-10"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py BY-10` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s` ends `(WP-41 BY-10)`.]]></verify>
  <done>The panel label row draws every listed sub-option in both modes, no ledger or known-differences row names BY-10 alone, and BY-10 is closed.</done>
</task>

<task type="auto" id="41-06-03">
  <name>Write the BY-16 failing tests</name>
  <files>test/test_by_label_options.py, test/test_wp41_truth.cscript</files>
  <action><![CDATA[Add the TestPanelValues stubs and the S06 BY-16 block (Q4106-2). Run `python3 -m pytest test/test_by_label_options.py::TestPanelValues -q -n0 -rf > <scratch>/41-06-03-failure.txt 2>&1; true` and the block, appending its FAIL line. List the date-label pins from the Evidence grep in `<scratch>/41-06-flips.txt`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/41-06-03-failure.txt` is at least 3; the file holds `Q4106-2 FAIL`.]]></verify>
  <done>BY-16's regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="41-06-04">
  <name>Write raw values and commit BY-16</name>
  <files>dash_render.py, dash.sthlp, test/function_test_map.py</files>
  <action><![CDATA[Run `gitnexus impact _dash_facet_label --direction upstream --repo dash`; report HIGH or CRITICAL (UNKNOWN confirmed with `grep -n`). Apply TR-41-06.5, TR-41-06.6 and TR-41-06.7's BY-16 sentences. Flip the pins in `<scratch>/41-06-flips.txt` in place ("twoway writes the number"). Run `python3 -m pytest test/test_layout_facets.py test/test_server_facets.py test/test_by_*.py -k "label or facet or date" -q -n0` (the glob holds test_by_label_options.py), then, separately with no `-k`, `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py -q -n0` (`_dash_quoted_lines`'s copy-list entry and map row, TR-41-06.6), and the S06 block. Append the date parity entry to test/test_mode_parity.py's `CORPUS` (R8). Close BY-16 (BUGS, Tracked, GAPS4_OPEN; CHANGELOG under `### Fixed in WP-41` -- a drawing change, nothing accepted or refused differently: "by() panels of a date variable read its number, as twoway writes it; by(d) drew 01jan2000, now 14610; a value label of quoted parts is split into lines (WP-41, BY-16)"). The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h), before the commit: (1) run `awk -F'\t' '$1 == "BY-16" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the plain rows; a `BY-16 (documented)` or `BY-16 (residual)` row stays, A-10) and `git add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py BY-16` and delete every `<file>:<line>` row it prints from its `*_KNOWN` table (staging each file it edits) -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion 33-10 names (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`; `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN`, e.g. `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `ABBREV_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (D-33-10.a; no ruling of this section keeps one, so none is expected: the values are written as twoway writes them (D-41-06.d, D-41-06.e)) -- then rerun, with no `-k`, each test file whose table it edited (its comparison reads the table, so a deleted row whose difference remains fails there) and run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); both pass; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the driver) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`, D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes) and add its `Fixture:` line to the commit body. Then the Commit boundary's pre-commit checks: `git pull --ff-only . main` in $WT (BRIEF "Pull form"; `Already up to date.` at the batch base; a refusal stops the task and is reported), `gitnexus detect-changes --scope all --repo .` and, when a cscript changed, the hygiene test the Commit boundary names. Commit.]]></action>
  <verify><![CDATA[Both pytest runs report 0 failed; `Q4106-2 PASS`; `awk -F'\t' '$1 == "BY-16"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py BY-16` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s` ends `(WP-41 BY-16)`.]]></verify>
  <done>Date panels read their Stata number and quoted labels split into lines in both modes, no ledger or known-differences row names BY-16 alone; BY-16 is closed.</done>
</task>

<task type="checkpoint" id="41-06-05">
  <name>Approve the label screenshots</name>
  <files>none</files>
  <action><![CDATA[Ask the maintainer to compare seven pairs of pictures. Each pair is one command drawn twice: by twoway (its SVG, from the fixture's work directory) and by dash, the same command with `dash` in place of `twoway` (headless-Chrome screenshots of the saved page and the served app). Present each pair under its number with its full command, the item it closes and one plain sentence of what to compare -- in these words:
    1. `twoway scatter mpg weight, subtitle(, justification(left)) by(foreign)` (BY-10): the panel labels (Domestic, Foreign) sit at the left end of their label bars, not in the middle.
    2. `twoway scatter mpg weight, subtitle(, nobexpand) by(foreign)` (BY-10): each label's shaded box is only as wide as its text, not the panel's full width.
    3. `twoway scatter mpg weight, subtitle(, lwidth(vthick) lcolor(black)) by(foreign)` (BY-10): each label box has a thick black outline.
    4. `twoway scatter mpg weight, subtitle(, span) by(foreign)` (BY-10): each label box reaches left over the y-axis labels, across the panel's full width.
    5. `twoway scatter mpg weight, subtitle(, alignment(top) height(15)) by(foreign)` (BY-10): each label box is taller and its text sits at the top of the box.
    6. `twoway scatter mpg weight, subtitle(, orientation(vertical)) by(foreign)` (BY-10): the label text is turned exactly as twoway turns it (if twoway draws it as with no option, dash does too).
    7. `twoway scatter mpg weight, by(foreign)` after the fixture's Q01 lines, which give Domestic a value label of two quoted parts, "Dom" and "estic" (BY-16): that panel's label reads on two lines, Dom over estic.
    Below the pairs, state in one sentence each the two rules taken from the measurement (`<scratch>/41-06-measured.txt`): whether `subtitle(, placement(e))` moves the label (L13) and whether `subtitle(, orientation(vertical))` turns it (L14), and what dash therefore does. Then say what each answer does. "Approve" keeps the drawing the two commits already hold; nothing is changed and the section is handed back. Naming a pair (its number or command) means: that probe is measured again, the drawing is corrected to match twoway, the item's tests and cscript block are run again, and the correction is put into that item's own commit, with that item's corpus ledger and known-differences steps (1)-(3) run again on it, before the hand-back -- `git branch wp41-s06-keep HEAD`, `git reset --hard <the item's sha>`, the correction, `git commit --amend --no-edit`, `git cherry-pick <the item's sha>..wp41-s06-keep` (nothing to replay when the item is BY-16, the last commit), `git branch -D wp41-s06-keep` (no interactive rebase).]]></action>
  <verify><![CDATA[The maintainer answers "approve", or names the pairs to redo; each named pair's item commit was amended as the action says and its tests and block ran green again.]]></verify>
  <done>The maintainer approved the drawn panel labels, pair by pair.</done>
</task>

## Section completion criteria

- Two commits, failing tests first; Q4106-1/2 PASS; Chrome tests green in both modes; no test deleted.
- `_dash_quoted_lines` on the served copy tuple; `_DASH_SPAN_JS`'s new kind covered by the Chrome tests.
- No plain `BY-10` or `BY-16` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py <id>` prints none for each); corpus_ledger.json is regenerated by `scripts/corpus/ledger.py`; the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script if Q3309-1 reported any change for a guard example (an improved verdict or a changed field).

## Notes

- **Help paragraphs owned (R3):** dash.sthlp :3278-3287 (panel label values), :5382-5385 (text boxes on by()). 41-03 edits :3264-3270 in the same batch, eight lines above; neither section reflows across :3271-3277 (REVIEW R3-38).
- **Merge rules:** R1, R2, R3, R5, R7, R8, R9.
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** Each closing task (41-06-02 for BY-10, 41-06-04 for BY-16) deletes its item's plain rows of scripts/corpus/ledger.tsv, regenerates corpus_ledger.json (D-33-05.i), deletes every row `python3 test/known_differences.py <id>` prints and runs the hygiene command it prints (D-33-10.h; 33-12's `BY_TYPES_KNOWN` and `BY_POSITION_KNOWN` list rows under any by() id their runs found, D-33-12.d/g) and regenerates corpus_guard_truth.json if Q3309-1 reports any change for a guard example (33-09, D-33-09.c), before its own commit.
- **Task count.** Two items in five tasks: two per item and the checkpoint (BRIEF "Task counts").
- **Trap:** the label Title is hidden once the ColorBar is drawn (:56150); under nobexpand it must stay visible and no ColorBar may be added -- `_dash_by_label_box` is idempotent by the ColorBar's name, so the nobexpand path must mark the Title (`title._dash_boxed = True`) to stay idempotent.
- **Trap:** `_dash_by_scale_panel` (:36855) scales Title text and padding by by()'s multiplier; the Title box path inherits that, the ColorBar path computes its own `mult`.
- **Commit-body lines:** `Regression: test/test_by_label_options.py::TestLabelOptions::test_no_note[saved-L01] -- failed at <base> with <text>`; `Fixture: test/fixtures/by_label_truth.json (scripts/extract_by_label_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: <id> Tracked`.
