# Section 27: Edge titles t1title..r2title

> Part of: WP-31 · GAPS3 rows: D2 · Risk: yellow · Batch: 9 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U27

## Overview

**What is wrong today.** GAPS3 D2 (GAPS3.md:152): "`t1title`..`r2title`, `title2`, `subtitle2` pending; the latter two are twoway refusals, not options." Evidence `dash.ado:1016-1035; dash_render.py:36868-36871`. At `6370ca4` the eight edge titles are declared (`T1title(string asis) ... R2title(string asis)`, dash.ado:948-950; `t()`, `b()`, `l()`, `r()` are their abbreviations, the comment at :967-969), stored (`sreturn local t1title ...`, :1106-1113), written to `graph_options` (seven key lists, :7344-7345) and named in the pending blocks (b1title :1011, b2title :1012, l1title :1021, l2title :1022, r1title :1025, r2title :1026, t1title :1029, t2title :1030; the plot parser's twins at :1356-1387). `TITLE2(string)` and `SUBTITLE2(string)` (:950-951) are declared too and named pending (:1028, :1031; plot :1372, :1375), yet twoway has no such options: `twoway scatter mpg weight, title2("x")` is refused r(198). The renderer draws none of the ten; its only knowledge of the names is the legend sub-option table's stage 5 (`("t1title", "t1", "r")` ..., dash_render.py:36865-36871), which is `legend(t1title())`, a different option. The help's Unsupported section says "dash draws title(), subtitle(), note(), caption() and the axis titles only" (dash.sthlp:4986-4995) and TWOWAY_COVERAGE_AUDIT.md:136 records "Alternative edge titles `t1title()` through `r2title()` are ignored".

**After this section** both modes draw the eight edge titles where twoway draws them: `t1title()`/`t2title()` above the plot region, `b1title()`/`b2title()` below, `l1title()`/`l2title()` to the left and `r1title()`/`r2title()` to the right, the `1` titles in ring 1 (nearest the plot region, inside the legend's ring 3) and the `2` titles in ring 2; `l`/`r` titles are vertical text. The `1` titles are the scheme's `subheading` text box (`gsize subheading` medium, `color subheading`), the `2` titles its `body` box (`gsize body` medsmall, `color body`), as `textboxstyle t1title subheading` ... `textboxstyle r2title body` say (scheme-s2color.scheme:1331-1338), stubs this section adds to every shipped scheme. `size()`, `color()`, `prefix` and `suffix` are honoured as on `title()`; the remaining textbox sub-options are named (S30, batch 10, wires `justification`/`alignment`/box on the four main boxes; the edge titles take S30's helper when it lands, Notes). `title2()` and `subtitle2()` are refused r(198) with twoway's words, measured in the extract script, in the graph parser and inside a segment alike, and leave the pending lists, the help and the audit.

**Why one section.** D2's two halves share the ten syntax entries and the two pending blocks; the refusal and the drawing land in one commit so the Unsupported list, the help and the declared-option classification move once.

**Test order and commit rule (BRIEF).** One cycle, one commit `(WP-31 D2)`: 27-01 measures twoway, writes `test/test_edge_titles.py`, runs it red, saves `<scratch>/27-01-failure.txt`, never commits; 27-02 refuses `title2()`/`subtitle2()` in dash.ado, removes the ten pending lines, draws the eight titles in the renderer and regenerates the schemes; 27-03 appends U27 cases, flips the pins, rewrites help/audit/BUGS/GAPS3/CHANGELOG and commits.

### Section decisions (this file; binding on the executor)

- **D-27.a Edge titles are side-panel `Title` models inserted at the ring's place.** A `Title` in `fig.above`/`fig.below` is horizontal and in `fig.left`/`fig.right` is drawn turned on its side by BokehJS (`TitleView._get_position`; the `_dash_textbox_place` docstring, dash_render.py:37264-37270, relies on the same), which is exactly twoway's vertical `l`/`r` text. Ring order is list order: the models are inserted directly after the panel's `Axis` models, ring 2 first and ring 1 second, so the `1` title sits nearest the frame, the `2` title next, and everything already in the panel (legend, note, caption, subtitle) stays outside. Every edge title carries `tags=["dash_edge_title", "<key>"]`.
- **D-27.b `_dash_move_legend` skips edge titles.** Its insertion index (`next(i for i, m in enumerate(panel) if not isinstance(m, Axis))`, :28195-28196) becomes the first model that is neither an `Axis` nor tagged `dash_edge_title`, so a legend moved after the titles are drawn still lands in ring 3. S31 (batch 10) edits the legend builders after this and keeps the skip.
- **D-27.c `position()` and `ring()` on an edge title are named**, as today for every unhonoured sub-option, because twoway's help forbids them (`title_options.sthlp:42`); `span` is also named (a side-panel Title already spans the figure's width, so twoway's plot-region-wide default is the one Bokeh cannot express: documented with the measured example, M17). `orientation()` is named: `l`/`r` are vertical and `t`/`b` horizontal by position.
- **D-27.d by() graphs.** `t1title`..`b2title` are drawn once on the by() chrome's head and foot rows (the hook `_dash_by_chrome` already uses for note/caption, :37725-37729), in ring order; `l1title`..`r2title` on a by() graph are a documented residual for S36 (by-remainder, batch 12): an open BUGS.md entry "l/r edge titles on by() graphs" and the GAPS3 D2 Tracked line in the "Partly closed" form (M12).
- **D-27.e The refusal words are measured, never typed from memory.** The fixture's `refuse_title2`/`refuse_subtitle2` keys hold twoway's `_rc` and message; dash.ado prints that message through `_dash_say("err", ...)` and exits with that rc, both in `_dash_parse_graph_opts` and in `_dash_parse_plot_opts`' graph part. `title(A) title(B)` stays merged (two lines) as today: `_dash_rep_reduce` joins the copies before `syntax` sees them, so the second copy never binds to `title2()` (guard test).

## Risk: [yellow] -- every side panel of every figure may gain models, and the legend's insertion rule changes

**Why.** Eight new graph_options keys reach the panels in both modes; `_dash_move_legend` changes its index rule; 26 scheme files are regenerated; two options turn from "named" to "refused".

**Risk factors.** 1. Panel order: a title inserted at the wrong index puts the legend inside the edge titles. 2. The by() chrome rows are built once for the grid (`_dash_by_chrome`); an edge title drawn on each panel as well would appear twice. 3. The refusal must not catch a merged `title(A) title(B)`. 4. Served/saved order: text annotations run before `_dash_reference_lines` served and after it saved (:37356-37360 note); edge titles are side-panel models, unaffected by the centre layer, but the executor must add the call at the same relative point in both. 5. Help-conformance and unsupported-report pins count the pending blocks.

**Mitigation.** 1. `TestRingOrder` reads `fig.above`/`fig.below` indices for t1, t2, legend, note, caption. 2. `TestOnAByGraph` counts one `dash_edge_title` per key across the grid. 3. `TestTitleCopiesStayMerged` is a guard. 4. Both call sites named by anchor in TR-27.5. 5. Flipped in 27-03 with `# <measured old> -> <new>` comments (R10, A33).

## Dependencies

- **Depends on: 01** (BUGS entries, GAPS3 Tracked line, CHANGELOG markers `<!-- WP-31 D2 -->` in Results and in Changed behaviour, the truth script).
- **Blocks: --.** S30 (batch 10) reuses `_dash_edge_titles`' Title models when it wires justification/box on text boxes; S31 (batch 10) keeps D-27.b in `_dash_move_legend`; S36 (batch 12) closes D-27.d's residual.
- **Parallel batch: 9**, merge order S28, S26, S27. **Can run with S26 and S28**: S26 registers contour (`map_contour`, the type tables), S28 edits `_FILTER_JS`; neither touches `_dash_text_annotations`, `_dash_move_legend`, `_dash_by_chrome`, the pending blocks' title lines, the scheme files or dash.sthlp's title paragraphs. S26 edits `_dash_option_rules` (contour tokens) in batch 9; S27 does not touch the rules table.

## Evidence

All anchors at `6370ca4`.

### The declarations and pending lines (dash.ado)

```
948        T1title(string asis)      T2title(string asis)      B1title(string asis) ///
949        B2title(string asis)      L1title(string asis)      L2title(string asis) ///
950        R1title(string asis)      R2title(string asis)      TITLE2(string) ///
951        SUBTITLE2(string)         NODRAW                    PLAY(string) ///
1011    if `: length local b1title' local _dash_pending `"`_dash_pending' b1title"'
1012    if `: length local b2title' local _dash_pending `"`_dash_pending' b2title"'
1021    if `: length local l1title' local _dash_pending `"`_dash_pending' l1title"'
1022    if `: length local l2title' local _dash_pending `"`_dash_pending' l2title"'
1025    if `: length local r1title' local _dash_pending `"`_dash_pending' r1title"'
1026    if `: length local r2title' local _dash_pending `"`_dash_pending' r2title"'
1028    if `: length local subtitle2' local _dash_pending `"`_dash_pending' subtitle2"'
1029    if `: length local t1title' local _dash_pending `"`_dash_pending' t1title"'
1030    if `: length local t2title' local _dash_pending `"`_dash_pending' t2title"'
1031    if `: length local title2' local _dash_pending `"`_dash_pending' title2"'
```
The plot parser repeats the ten lines (:1356-1387; `subtitle2` :1372, `title2` :1375). `sreturn` lines :1106-1115; `g_title2`/`g_subtitle2` :1600-1601. The key lists carry `t1title t2title b1title b2title l1title l2title r1title r2title title2 subtitle2` (:5782-5783 and the six twins). `_dash_rep_cat` puts the ten in category "T" (dash_parse.mata:6172-6174). dash_parse.mata:6029 notes "title(A) title(B) never reaches the catch-all: -syntax- binds the second to title2()" -- the pre-reduce scan; after `_dash_rep_reduce` the merged copy is one `title()`.

### The renderer's text boxes (dash_render.py)

`_dash_text_annotations` (:37329-37414) draws note, caption and subtitle as `Title` rows through `fig.add_layout(Title(text=..., align=align, text_font_style="normal", text_font_size=size, text_color=color, background_fill_color=fill), side)`, sizes from `scheme.subheading_font_size`/`body_font_size`/`note_text_font_size` (:37381-37386), sides from `_dash_textbox_place` (:37394). `_dash_figure_title` (:37180) applies `size()`/`color()` through `_textbox_size`/`_textbox_color`. `_dash_move_legend` (:28179-28200) inserts the legend after the axes. `_dash_by_chrome` (:37701) draws the grid's head/foot boxes with `_dash_text_annotations(head, ..., sides=("above",))` and `(foot, ..., sides=("below",))` (:37726-37729). Call order, saved (`_make_figure_body`, :43776-43830 excerpt lines 247-295): `apply_to_figure` -> `_dash_figure_title` -> `_dash_style_axis_titles` -> `_dash_add_secondary_axes` -> `_dash_reference_lines` -> `_dash_text_annotations` -> `_dash_added_text` -> `_dash_apply_axis_options`; served (`_dash_figure_for`, :49443-49484 excerpt lines 64-104): `apply_to_figure` -> `_dash_add_secondary_axes` -> `_dash_figure_title` -> `_dash_style_axis_titles` -> `_dash_text_annotations` -> `_dash_reference_lines` -> `_dash_added_text` -> `_dash_apply_axis_options`.

### Stata's rule (research/stata-ground-truth.md §9)

Syntax `t1title() t2title() b1title() b2title() l1title() l2title() r1title() r2title()` with `tinfo`; twoway only; `position()` not allowed with them (`title_options.sthlp:42`); l/r titles are vertical (`:12-13`). Rings: t1/b1/l1/r1 = 1, t2/b2/l2/r2 = 2, legend 3, note 4, caption 5, subtitle 6, title 7 (`:54-75`). Parser (`_fr_title_parse_and_log.ado`): ring defaults to the digit (`:66-70`), position from the letter (l leftof, r rightof, t above, b below, `:179-195`), l/r `orientation(vertical)` (`:75-78`). Scheme: `textboxstyle t1title/b1title/l1title/r1title subheading`, `t2title/b2title/l2title/r2title body` (`scheme-s2color.scheme:1331-1338`); `gsize subheading medium` (:140), `body medsmall` (:137). dash-s2color.scheme carries `gsize subheading`/`body`, `color subheading`/`body`, `horizontal subheading`/`body` (:156-157, :169-170, :354-355) and no `textboxstyle t1title..r2title` (research §11 "Absent").

### Fixtures on disk

None for edge titles. `test/fixtures/text_truth.json` (scripts/extract_text_truth.do) holds the main boxes' truth and is not edited.

### Tests that pin today's behaviour (flip, never delete)

- test_unsupported_report_is_true.py: `"t1title": ("t1", "tA", "scatter")` (:149), `"title2": ("T2", "TT", "scatter")` (:151) and the b/l/r/t2/subtitle2 entries beside them; counts :240-262 and :725-726.
- test_help_conformance.py::TestTheUnsupportedSectionIsTrue (:938-960) and :825 (an option twoway lacks must have a help definition: `title2`/`subtitle2` are absent from abbrev_truth.json, so their help entry moves from Unsupported to the refusal sentence).
- test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed (:1410) follows the pending blocks.
- test_scheme_chrome.py::TestTheChromeKeysAreRead (:383): gains the eight `textboxstyle` stubs.

## User stories

- US-27.1 As a Stata analyst, I want `t1title("Source: NHTS")` and `b1title(...)` drawn above and below the plot region as twoway draws them so that my do-file's titles appear on the dashboard.
- US-27.2 As a Stata analyst, I want `l1title()`/`r1title()` drawn as vertical text beside the plot so that a secondary description reads like twoway's.
- US-27.3 As a Stata analyst, I want `title2()` refused with twoway's message so that a typo is caught, not silently named.
- US-27.4 As a dashboard reader, I want the ring order (edge titles inside the legend, the legend inside note/caption) preserved in the saved page and the served app.

## Business requirements

- BR-27.1 The eight edge titles are drawn in both modes at twoway's side and ring, with no note printed (Q36).
- BR-27.2 The `1` titles use the scheme's subheading size and colour, the `2` titles the body's; `size()`/`color()`/`prefix`/`suffix` win over the scheme.
- BR-27.3 `l`/`r` titles are vertical.
- BR-27.4 `title2()` and `subtitle2()` are refused with twoway's return code and words, in the graph part and inside a segment.
- BR-27.5 `title(A) title(B)` still draws two lines.
- BR-27.6 On a by() graph the t/b titles appear once, on the grid.

## Technical requirements

- TR-27.1 **dash.ado refusal.** In `_dash_parse_graph_opts`, directly after `syntax` (:966) and before the abbreviation comment (:967): `foreach _t2 in title2 subtitle2 { if `: length local `_t2'' { mata: _dash_say("err", "<measured words with `_t2'>"); exit <measured rc> } }` -- the words are the fixture's `refuse_title2.msg` with the option name substituted (twoway's form is expected to be `option title2() not allowed`, r(198); the executor copies the fixture's text verbatim). The same block in `_dash_parse_plot_opts` after its `syntax`. Keep `TITLE2(string)`/`SUBTITLE2(string)` declared so the spelling binds and is refused rather than falling to the catch-all; delete their `sreturn` lines (:1114-1115, :1600-1601), their names in the seven key lists and in `_dash_rep_cat`'s "T" list (dash_parse.mata:6174), and the two pending lines in each parser.
- TR-27.2 **dash.ado unpend.** Delete the eight edge-title pending lines in both blocks (:1011-1012, :1021-1022, :1025-1026, :1029-1030 and the plot parser's eight). Nothing else changes: the keys are already stored and written.
- TR-27.3 **SchemeParser.** Add to `_TEXTBOX_STYLES` (:10071 region) nothing (the style names map through `textbox_style`); instead add `self.edge_title_styles: dict = {k: self._choice(f"textboxstyle {k}", ("subheading", "body", "heading", "small_body"), "subheading" if k[1] == "1" else "body", "textbox style") for k in ("t1title", "t2title", "b1title", "b2title", "l1title", "l2title", "r1title", "r2title")}` after `self.text_clock` (:10632-10636). The size and colour of a style name come from `self.textbox_style(name)` (:10085), which already resolves `subheading`/`body`.
- TR-27.4 **The drawer.** New module function `_dash_edge_titles(fig, graph_opts, seen=None, key="", scheme=None, *, sides=None)` placed directly after `_dash_text_annotations` (:37414) and before `_dash_added_text_opts`. Body: `from bokeh.models import Axis, Title`; for `(k, side, ring)` in the fixed order `(("t2title","above",2), ("t1title","above",1), ("b2title","below",2), ("b1title","below",1), ("l2title","left",2), ("l1title","left",1), ("r2title","right",2), ("r1title","right",1))`: skip when `sides` is given and `side not in sides`; `raw = graph_opts.get(k, "")`; skip when empty; `text, opts = _dash_textbox(raw, k, seen, key)` (its honoured set is `size color prefix suffix axis`; `axis` is named for a non-axis title by the existing rule); skip when no text; style name `scheme.edge_title_styles[k]` when `scheme` else `"subheading"`/`"body"` by ring; `size_default, color_default = scheme.textbox_style(style)` (fallback `_DASH_TEXTBOX_DEFAULTS["subtitle"]`'s px/colour for ring 1 and `["caption"]`'s for ring 2 when no scheme); `px = _textbox_size(opts, size_default, OptionTranslator.size_ref_of(fig), f"{k}(size)")`; `colour, alpha = _textbox_color(opts, None, base=color_default, colours=getattr(fig, "_dash_scheme_colours", None), with_alpha=True)`; `align = scheme.text_just.get(style, "center")` when scheme else `"center"`; build `Title(text=text, align=align, text_font_style="normal", text_font_size=px or size_default, text_color=colour or color_default, tags=["dash_edge_title", k], **({"text_alpha": alpha} if alpha is not None else {}))`; insert: `panel = list(getattr(fig, side)); at = next((i for i, m in enumerate(panel) if not isinstance(m, Axis) and "dash_edge_title" not in (m.tags or [])), len(panel))` -- then, because ring 2 was inserted first and must stay outside ring 1, a ring-1 title is inserted at `at` and a ring-2 title at the index after the last `dash_edge_title` already in the panel if any, else `at`; `setattr(fig, side, panel)`. Text is a canvas `Title` (a text sink test_label_sinks.py already inventories as `Title.text`).
- TR-27.5 **Call sites.** Saved `_make_figure_body`: directly after `_dash_text_annotations(fig, graph_opts, _seen, _gkey, self.scheme)` (:43806 region, excerpt line 283) add `_dash_edge_titles(fig, graph_opts, _seen, _gkey, self.scheme)`. Served template (`_generate_app_source`, the `_dash_figure_for` line `"        _dash_text_annotations(fig, go, _reported_subopts, gname, _DASH_SCHEME)",` at :49472 region, excerpt line 93): add the string line `"        _dash_edge_titles(fig, go, _reported_subopts, gname, _DASH_SCHEME)",` after it. S27 is batch 9's one `_generate_app_source` editor (R12; S26 and S28 do not edit the template: S26's contour drawing lands in the shared glyph layer, S28 in `_FILTER_JS`). `_dash_by_chrome` (:37726-37729): after each `_dash_text_annotations(head|foot, ...)` call add `_dash_edge_titles(head, boxes, seen, key, scheme, sides=("above",))` and `_dash_edge_titles(foot, boxes, seen, key, scheme, sides=("below",))`; in the by() panel path, the per-panel call skips t/b titles when `graph_opts` has `by` with panels (the `_by_panels` test at :37374-37375), so they appear once (D-27.d); l/r titles are not drawn on by() panels (residual).
- TR-27.6 **`_dash_move_legend`** (:28195-28196): `at = next((i for i, m in enumerate(panel) if not isinstance(m, Axis) and "dash_edge_title" not in (getattr(m, "tags", None) or [])), len(panel))`.
- TR-27.7 **Copy lists (R2).** Functions tuple: `"_dash_edge_titles",` after `"_dash_text_annotations",` (:47216). No new constant. `test/function_test_map.py`: `"_dash_edge_titles": "test/test_edge_titles.py::TestEdgeTitlesAreDrawn::test_each_side_and_ring"`.
- TR-27.8 **Scheme stubs (R7).** In scripts/extract_scheme_truth.py, beside the directive `("textboxstyle", "note", ...)` that writes `textboxstyle note small_body` (grep `"textboxstyle", "note"`), add the eight `("textboxstyle", "<k>title", ...)` directives reading `textboxstyle <k>title` with the scheme chain's fallback (`subheading` for ring 1, `body` for ring 2, the values at scheme-s2color.scheme:1331-1338), and the matching truth entries beside `note`'s. Run `/opt/homebrew/bin/python3.14 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` twice; `git add -f test/fixtures/scheme_truth.json`. Every `dash-*.scheme` gains eight lines `textboxstyle t1title subheading` ... `textboxstyle r2title body`.
- TR-27.9 **Help (R3).** Delete the "Alternative titles" Unsupported paragraph (dash.sthlp:4986-4995). In the paragraph that documents `title()`, `subtitle()`, `note()` and `caption()` (under `{marker region_options}`, :3402-3511; the executor locates it with `grep -n "subtitle(" dash.sthlp` in that range) add a paragraph "Edge titles": the eight options, their rings and sides, l/r vertical, the subheading/body styles, `size()`/`color()`/`prefix`/`suffix` honoured, `position()`/`ring()`/`span` named, the width difference (M17: a Title spans the figure, twoway centres on the plot region), and the by() residual. In the Unsupported section's refusal list (the `{cmd:region()} of {cmd:legend()}` sentence at :5120-5125) add `title2()` and `subtitle2()` as refused with twoway's words. TWOWAY_COVERAGE_AUDIT.md:136 gains `[WP-31 D2, commit pending: corrected -- the eight edge titles drawn; title2()/subtitle2() refused as twoway refuses them]` (the merger's step k.3b fills the sha, A11); :169 loses `b1title`, `b2title`, `l1title`, `l2title`, `r1title`, `r2title`, `subtitle2`, `t1title`, `t2title`, `title2`.
- TR-27.10 **Classification.** test_unsupported_report_is_true.py: the eight edge titles move to `LIVE_VALUES` with two texts (`("t1title": ("Alpha", "Beta", "scatter"))`); `title2`/`subtitle2` move to a refused classification: at `6370ca4` the file has none, so add `REFUSED = {"title2": "refused r(198) with twoway's words (WP-31 D2)", "subtitle2": <same>}` beside `NOT_IN_FILE` (:420) and subtract `set(REFUSED)` in `test_every_declared_option_is_classified` (:725); if an earlier batch has added such a set by the batch-9 base, the two names join it instead. Counts move with `# <measured old> -> <new>: D2 ...` comments: pending graph -10 and pending plot -10 (eight drawn, two refused), the old value recounted at the batch-9 base with the file's `_graph_pending()`/`_plot_pending()` helpers, never S24's planned figure; declared graph unchanged (DECISIONS A33).

## Boundaries

- Does not edit `_dash_figure_title`, `_dash_textbox`, `_dash_textbox_place`, `_DASH_TEXTBOX_HONOURED` (S30, batch 10), `_dash_apply_legend` beyond the one-line index rule in `_dash_move_legend` (S31 owns the builders in batch 10), `_dash_option_rules` (S26 is batch 9's editor), `_FILTER_JS` (S28), `_make_figure_body` beyond the one call line, or any axis code.
- Does not draw l/r titles on by() panels (D-27.d residual) and does not honour `position()`/`ring()`/`span` on edge titles (D-27.c).

## Stata truth

Script `scripts/extract_edge_title_truth.do` -> `test/fixtures/edge_title_truth.json` (R7 form: `_meta` complete; `shell git rev-parse HEAD` to a file; `Macro.getLocal`; `git add -f`). Cases (`sysuse auto`; each `quietly twoway scatter mpg weight, <opts> name(u27k, replace)`; one `classutil describe .u27k` recorded in `_meta.members`, then the title objects' members `classutil describe .u27k.t1title` once):

| key | options | values |
|---|---|---|
| ring_t1 .. ring_r2 | `t1title("T1")` ... `r2title("R2")` (eight graphs) | `.u27k.<k>.ring`, `.u27k.<k>.position` (or the members describe names), `.u27k.<k>.style.name` (expect subheading/body) |
| vertical_l1 | `l1title("L1")`, SVG export | the text element's `rotate(` angle (expect -90) |
| svg_order | `t1title("T1") t2title("T2") note("N") caption("C") subtitle("S") title("T")`, SVG export | y of each text (T1 nearest the plot, then T2, N, C, S, T) |
| sizes | `t1title("T1") t2title("T2")`, SVG | font sizes of T1 and T2 (medium 3.8194 vs medsmall 3.4722 in SVG units) |
| refuse_title2 | `capture noisily twoway scatter mpg weight, title2("x")` | `_rc` and the logged line |
| refuse_subtitle2 | `capture noisily twoway scatter mpg weight, subtitle2("x")` | `_rc` and the logged line |
| merged_title | `title("A") title("B")` | `.u27k.title.text` array length (expect 2) and `_rc` 0 |
| by_tb | `t1title("T1") b1title("B1") by(foreign)` | count of T1/B1 texts in the SVG (expect 1 each) |

Run: `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s27 $WT/scripts/extract_edge_title_truth.do`. `test_edge_titles.py::TestTheFixture` names the fixture.

## TDD test stubs

### Regression tests, `test/test_edge_titles.py` (new; red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, go)` renders one scatter in both modes (test_axis_options.py's helpers); `_edge(fig, k)` returns the `Title` tagged `["dash_edge_title", k]` and its panel index; fixture read at module level. Drawing classes parametrized `mode in ("saved", "served")`.

- Test: fixture stamped; every truth key present -- `TestTheFixture::test_meta_is_stamped`, `::test_every_case_was_measured` (guard after 27-01).
- Test: each of the eight options draws exactly one `Title` with its text in its side panel (`above`/`below`/`left`/`right`) -- `TestEdgeTitlesAreDrawn::test_each_side_and_ring[mode-k]` (red: no model).
- Test: ring 1 sits nearer the frame than ring 2: index(t1) < index(t2) in `fig.above`; same for b, l, r -- `TestRingOrder::test_one_inside_two[mode-side]` (red).
- Test: with a legend at 6 o'clock and a caption, `fig.below` order is axes, b1title, b2title, legend, caption -- `::test_legend_and_note_stay_outside[mode]` (red).
- Test: the `1` titles have `text_font_size == scheme.textbox_style("subheading")[0]` and `text_color` its colour; the `2` titles the body's -- `TestStyles::test_ring_one_is_subheading[mode]`, `::test_ring_two_is_body[mode]` (red).
- Test: `t1title("X", size(large) color(red))` draws large red; `prefix`/`suffix` as on title() -- `::test_size_color_prefix_suffix[mode]` (red).
- Test: `t1title("X", position(3))`, `ring(2)`, `span`, `orientation(horizontal)` are named once and the title is still drawn -- `TestNamedSubOptions::test_named_once[mode-sub]` (red: the whole option is named today).
- Test: the eight options print no note -- `TestSilentWhenHonoured::test_no_note[k]` (red).
- Test: `textboxstyle t1title` .. `r2title` present in all 26 shipped schemes and read into `edge_title_styles` -- `TestSchemes::test_every_scheme_names_the_styles` (red: AttributeError).
- Test: a by() graph with `t1title() b1title()` has one `dash_edge_title` per key across the grid (on the chrome head/foot), and l/r titles are not drawn -- `TestOnAByGraph::test_once_on_the_grid[mode]`, `::test_lr_not_drawn_residual[mode]` (red).
- Test: `title("A") title("B")` draws `"A\nB"` and no refusal -- `TestTitleCopiesStayMerged::test_two_lines` (guard; runs the parser through `_dash_serve_spec`'s JSON in 27-01's probe).
- Test: hostile text (`</title><script>`) is the Title's text verbatim and appears in the saved HTML only inside the Bokeh JSON -- `TestTextIsACanvasSink::test_raw_title_text` (guard).

### Cases in cscripts

- `test/test_wp31_truth.cscript` block `* ==== S27 D2: Edge titles ====`: U27-1 (each of the eight keys: twoway's `.ring`/side from the live `.Graph` against dash's panel/index through a `python:` render), U27-2 (SVG y order of T1, T2, note, caption, subtitle, title vs dash's panel order), U27-3 (l1title vertical: twoway's `rotate(-90)`; dash's model is in `fig.left`), U27-4 (sizes: subheading/body vs dash's pt), U27-5 (by(): one T1 and one B1 in both). Red at base except the twoway halves.
- `test/test_option_validation.cscript`: U27-6 `dash scatter mpg weight, title2("x")` and U27-7 `subtitle2("x")` have twoway's `_rc` and words in the same run (red: dash prints a note and returns 0); U27-8 `dash scatter mpg weight || scatter price weight, title2("x")` inside a segment, same words (red); U27-9 `title("A") title("B")` rc 0 in both (guard).

### Flips (in place, each with a `Flipped:` line)

- test_unsupported_report_is_true.py: the eight edge titles to `LIVE_VALUES`; `title2`/`subtitle2` to the refused set; counts :240-262 (`# <measured old> -> <old - 10>: D2 edge titles drawn, title2/subtitle2 refused`, the old value recounted at the base, A33) and the plot block count by the same ten.
- test_scheme_chrome.py::TestTheChromeKeysAreRead: the stub set gains the eight `textboxstyle <k>title` keys.
- test_help_conformance.py:825 (an option twoway lacks must have a help entry): `title2`/`subtitle2`'s entry is now the refusal sentence; the test's locator follows the Unsupported section, so the sentence stays inside `{marker unsupported}`.

### Parity corpus (R8; appended, guards at base)

test_mode_parity.py under `# WP-31 D2 (section 27): edge titles`: `CORPUS` cases `"t1title b1title l1title r1title"` (all four `1` titles with texts) and `"t2title with legend(pos(6)) and caption"`; one `MOVE_CORPUS` case `_move_case("t1title after a dropdown move (WP-31 D2)", _MOVES[0], [plot_for("scatter")], go={"t1title": "T1", "b2title": "B2"})` (titles are static; the case proves the panels survive a move in both modes).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Eight titles drawn at side/ring | pytest test_edge_titles.py + U27-1 | edge_title_truth.json | yes |
| Ring order vs legend/note/caption | pytest + U27-2 | edge_title_truth.json | yes |
| l/r vertical | pytest (panel) + U27-3 (SVG angle) | edge_title_truth.json | yes |
| Styles subheading/body | pytest + U27-4 | scheme_truth.json | yes |
| by(): once on the grid | pytest + U27-5 | -- | yes |
| title2()/subtitle2() refused | cscript U27-6..U27-8 | live twoway | n/a |
| Merged title() copies unchanged | cscript U27-9 + guard | -- | n/a |
| Help/Unsupported/audit agree | pytest test_help_conformance.py | -- | n/a |

Acceptance: AC-27.1 every red stub green in both modes; AC-27.2 U27-1..U27-9 PASS through the driver, no SKIP; AC-27.3 `title(A) title(B)` unchanged; AC-27.4 the scheme generator's second run changes nothing; AC-27.5 test_help_conformance.py, test_unsupported_report_is_true.py, test_label_sinks.py, test_csp.py green.

## Tasks

**Commit boundary.** Tasks 27-01 to 27-03 form the one D2 commit, subject `Draw the eight edge titles and refuse title2()/subtitle2() as twoway does (WP-31 D2)`, made by 27-03 on `wp31-s27` in `$WT=<worktrees>/wp31-s27`. Body: `<scratch>/27-01-failure.txt`, the measured defect, what changed where (both modes; the template line; `_dash_move_legend`'s index; the 26 schemes), `Regression:` lines for test_edge_titles.py nodes, `test/test_wp31_truth.cscript U27-1..U27-5`, `test/test_option_validation.cscript U27-6..U27-8`, one `Flipped:` line per flip, `Fixture: test/fixtures/edge_title_truth.json (scripts/extract_edge_title_truth.do)`, `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`, `BUGS.md: "<D2 title>" (closed)`, `GAPS3: D2 Tracked` (Partly closed form naming the l/r-on-by() residual entry). The CHANGELOG `<!-- WP-31 D2 -->` markers: Results `dash scatter mpg weight, t1title("T1"): not drawn -> drawn above the plot region in ring 1 (WP-31 D2)`; Changed behaviour `title2() and subtitle2() are refused, "<measured words>", r(198), as twoway refuses them; they were named as unsupported (WP-31 D2)`. No tooling names.

<task type="auto" id="27-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_edge_title_truth.do, test/fixtures/edge_title_truth.json, test/test_edge_titles.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals the batch-9 base sha and the branch is `wp31-s27`; `mkdir -p <scratch>/s27`. Create scripts/extract_edge_title_truth.do from scripts/extract_default_base_truth.do's head (:21-48) with the "Stata truth" cases (SVG exports read with cert_svg.do's reader; `classutil describe` output of `.u27k` and `.u27k.t1title` stored in `_meta.members`); run `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s27 $WT/scripts/extract_edge_title_truth.do`; `git add -f test/fixtures/edge_title_truth.json`. Check `refuse_title2.rc` is 198 and record its `msg` in the module docstring of the new test. Create test/test_edge_titles.py with exactly the classes of "TDD test stubs / Regression tests". Run `python3 -m pytest test/test_edge_titles.py -q -n0 -p no:cacheprovider -rf > <scratch>/s27/27-01.log 2>&1`; write `<scratch>/27-01-failure.txt` (base sha, each failing node and reason, the guards that passed). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/edge_title_truth.json'));print(sorted(d['_meta'])[:4], d['refuse_title2']['rc'], d['merged_title']['n'])"` prints `['born_date', 'dash_commit', 'extracted', 'members'] 198 2`; `grep -c FAILED <scratch>/s27/27-01.log` is at least 16; no FAILED line names TestTheFixture, TestTitleCopiesStayMerged or TestTextIsACanvasSink; `test -s <scratch>/27-01-failure.txt`.]]></verify>
  <done>twoway's edge-title rings, sides, styles, vertical angle, by() counts and the title2()/subtitle2() refusals were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="27-02">
  <name>Refuse title2, draw edge titles, add stubs</name>
  <files>dash.ado, dash_render.py, scripts/extract_scheme_truth.py</files>
  <action><![CDATA[
    dash.ado: apply TR-27.1 (the two refusal blocks with the fixture's words; delete the four `sreturn` lines and the two names in the seven key lists; in dash_parse.mata:6174 remove the two names from `_dash_rep_cat`'s "T" list, one data edit) and TR-27.2 (delete the eight edge-title pending lines in both blocks and the two title2/subtitle2 lines in both). dash_render.py: TR-27.3 (`edge_title_styles` after `text_clock`), TR-27.4 (`_dash_edge_titles` after `_dash_text_annotations`), TR-27.5 (the saved call after :43806's `_dash_text_annotations`, the template string line after :49472's, the two `_dash_by_chrome` calls and the by()-panel skip), TR-27.6 (`_dash_move_legend` index), TR-27.7 (copy-list entry after `"_dash_text_annotations",` :47216; function_test_map.py entry). scripts/extract_scheme_truth.py: TR-27.8; run the generator twice with `--out test/fixtures/scheme_truth.json`; `git add -f test/fixtures/scheme_truth.json`. Run `python3 -m pytest test/test_edge_titles.py test/test_graph_options.py test/test_scheme_chrome.py test/test_statistical_helpers.py test/test_mode_parity.py -k "not Chrome and (edge or Title or Legend or Carries or scheme)" -q -p no:cacheprovider > <scratch>/s27/27-02.log 2>&1`.
  ]]></action>
  <verify><![CDATA[`grep -c "_dash_pending' \([tblr][12]title\|title2\|subtitle2\)\"" dash.ado` prints 0; `grep -c "textboxstyle r2title body" dash-*.scheme | grep -vc ":1$"` prints 0; `grep -c "_dash_edge_titles" dash_render.py` is at least 5 (def, saved call, template line, two by-chrome calls, copy list); `grep -c FAILED <scratch>/s27/27-02.log` prints 0 for test_edge_titles.py nodes.]]></verify>
  <done>Both renderers drew the eight edge titles in their rings and styles, the legend kept ring 3, every scheme carried the eight textbox-style stubs, and title2()/subtitle2() were refused with twoway's words.</done>
</task>

<task type="auto" id="27-03">
  <name>Certify, flip, document and commit D2</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[
    Append the S27 block (`* ==== S27 D2: Edge titles ====` ... `* ==== end S27 ====`, U27-1..U27-5) above the marker line of test/test_wp31_truth.cscript and U27-6..U27-9 to test/test_option_validation.cscript (`*! U27-6..U27-9` header lines; each compares dash's logged line and `_rc` with `capture noisily twoway` in the same run). Drivers as in BRIEF ("Running one cscript"; `WP31_ONLY=S27`); run both through `scripts/stata_slot.sh <scratch>/s27 ...`. Flip the pins (TDD "Flips"; TR-27.10) and append the parity cases (R8). Apply TR-27.9 to dash.sthlp and TWOWAY_COVERAGE_AUDIT.md. Close the D2 BUGS.md entry (BRIEF form, with the `Residual, deferred (WP-31): l/r edge titles on by() graphs (S36)` clause), open the residual entry at the END of BUGS.md in the open form graded S3, rewrite the GAPS3 `D2 Tracked` line to `- **D2 Tracked:** Partly closed in WP-31 (section 27, commit pending): the eight edge titles drawn, title2()/subtitle2() refused; open: l/r edge titles on by() graphs (BUGS.md "<residual title>").` (write `commit pending`; the merger's step k.3b fills the sha, DECISIONS A11), replace both `<!-- WP-31 D2 -->` markers. Run `python3 -m pytest test/test_edge_titles.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_tracking_documents.py test/test_label_sinks.py -q -p no:cacheprovider`; `git add -A`; commit with the "Commit boundary" body; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.
  ]]></action>
  <verify><![CDATA[`grep -c "U27-[1-9] PASS" <scratch>/s27/*.log` sums to 9 and `grep -c SKIP <scratch>/s27/run_truth.log` prints 0; `grep -c "Alternative titles" dash.sthlp` prints 0 and `grep -c "Edge titles" dash.sthlp` is at least 1; `grep -c "^- \*\*D2 Tracked:\*\* Partly closed in WP-31" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 D2)`.]]></verify>
  <done>D2 was certified against twoway, its pins flipped with reasons, its help, audit, BUGS, GAPS3 and CHANGELOG lines rewritten, the by() l/r residual opened, and one green commit landed on wp31-s27.</done>
</task>

## Section completion criteria

- Eight edge titles drawn in both modes at twoway's side and ring, `1` titles subheading and `2` titles body, l/r vertical, `size()`/`color()`/`prefix`/`suffix` honoured, nothing printed.
- The legend stays in ring 3 outside the edge titles; note/caption/subtitle outside the legend.
- `title2()`/`subtitle2()` refused with twoway's measured words and rc in the graph part and inside a segment; `title(A) title(B)` unchanged.
- Every shipped scheme carries `textboxstyle t1title..r2title`; `scheme_truth.json` regenerated.
- U27-1..U27-9 PASS; flips recorded; help, Unsupported list, audit, BUGS.md (one closed, one residual opened), GAPS3 §9 and CHANGELOG updated in the one `(WP-31 D2)` commit.

## Notes

- **Renderer order.** The edge-title call follows `_dash_text_annotations` in both modes; the centre-layer difference (reference lines before/after) does not affect side panels.
- **Copy lists (R2):** `"_dash_edge_titles",` after `"_dash_text_annotations",` (:47216); `SchemeParser.edge_title_styles` travels with the class.
- **R12:** S27 is batch 9's one `_generate_app_source` editor (one added string line) and edits `_make_figure_body` by one call line; S26 and S28 touch neither (their Boundaries).
- **R6:** no new program; `_dash_rep_cat`'s "T" list is a data edit; the seven key lists change together (two names removed).
- **R1:** the S27 block only, in section order after S26's; the refusal cases in test_option_validation.cscript under U27 ids.
- **R3:** S27 owns the "Edge titles" paragraph it adds, the Unsupported paragraph it removes and the refusal sentence it extends.
- **R5/R12 (M12):** the by() l/r residual is an open BUGS.md entry graded S3 and a "Partly closed" Tracked line; S36 closes it.
- **For S30 (batch 10):** edge titles are `Title` models tagged `dash_edge_title`; S30's justification/box helper may style them by tag but must not move them.
- **For S31 (batch 10):** keep D-27.b's skip when editing `_dash_move_legend`.
- **python_exec hazard:** check `~/.stata19/console/stata19.rc` after each slot run; exit 222 is not a pass.
- **Commit-body line forms** are BRIEF's with `failed at 6370ca4`.
