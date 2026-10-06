# Section 53: Shared axes and keys under by() (P1.15 part c)

> Part of: WP-30 · Items: P1.15 part c (entry `P1.15c`; GAPS2-B16-c (the i*/noi* axes and noedgelabel), GAPS2-B16-d (legend() inside by()), GAPS2-B26-d, GAPS2-B31-c, AUDIT-71, AUDIT-72, the WP-29 S10 axis-2-title note and the WP-29 S07 clegend note) · Risk: yellow · Batch: 18 (merge order S51, S52, S53; S53 regenerates the scheme files and lands last) · Depends on: 10, 15, 19, 21, 31, 48 · Blocks: none · Tasks: 14, 1 commit · Case prefix: BYA

## Review amendments

- Fixed (major, contract with S48): S48's D-48e leaves `margin by_indiv` (the space between panels) to S53's regeneration, but TR-53.1 did not list it; it is now a regenerated key, which S48's `SchemeParser.by_indiv_margin` reads.
- Fixed (major, red pins the plan missed): the regeneration adds 19 directives per file and keys that match `test_no_directive_for_what_dash_does_not_draw`'s `margin` and `tick` patterns (`margin by_indiv`, `yesno by_indiv_xticks`, `yesno by_indiv_yticks`), so that pin and `test_the_directive_count_is_what_the_help_says` would turn red. Both are in E5 and flipped in 53-12 (now with `test/test_help_claims_8.py` in its files), and 53-11 re-derives the help's directive numbers (R10).
- Fixed (major, M1 correctness): `legend(at(k))` and `clegend(at(k))` holes count in twoway's `full_n`, which moves the panels (E4 p46: two panels and `at(3)` make a 2×2 grid) and S48's size multiplier; TR-53.9 now has `_dash_by_side` and `_dash_layout_cell` call S48's `_dash_by_positions` with the same two holes, pinned by `TestOneLegend::test_a_hole_counts_in_the_grid`.
- Fixed (minor): `TestTheUnitFunctions::test_spellings_agree_with_the_grammar` keeps `_DASH_BY_AXES_SPELLINGS` equal to S48's `_DASH_BY_GRAMMAR`, which dash.ado's refusals use (Q-48.1: every word outside it is refused).
- Fixed (minor, Q-28.1 ruling): the panel label's filled box is out of scope (S28's `_dash_by_panel_label` draws the label; it is not trivially in S53's code); the Note says so and the closeout files it as a P2 row.
- Fixed (minor): Notes give S48's helper signatures as TR-48.8 defines them.
- Checked at HEAD: `_dash_reflow` 24465 with `grid.cols = _DASH_BS_TRACK` and the container query at :24513-24518, the axis-2 title default under by() :23086-23094, `doc.add_root(layout)` :36379, copy-list `"_dash_reflow",` 33354, `_COLORVAR_LEGEND_NAME` 3599, `_DASH_SWATCH_PREFIX` 25512; s2color's by() keys (:729, :1925-1954, :2191-2210).
- Checked: M5 (no new refusal here; S48 refuses by() words), M6 (`legend(off)` outside by() and twoway's ignored forms silent; `legend(ring(0))` drawn differently and named once); rule 1 (titles reach the stack script only as JSON data, constant names, CSP-run CustomJS).
- Checked (batch 18): S53 alone edits `_generate_app_source`, `_build_sources_and_figures`, `_dash_layout_cell`, `_dash_reflow`, `_dash_parse_by`, `SchemeParser._init_properties`, the extractor and the scheme files; S52's axis functions and S51's Stata/Mata functions are not touched; it regenerates and lands last (A152).
- Cross-file (notes file): index 18.0's expected list omits S53's `_dash_layout_cell` and `_dash_parse_by` (CRITICAL), `_generate_app_source` and `_glyph_layer_lines` (HIGH); R10 should name S53 (18) as a mover of the directive-count pin.
- Rejected: `<files>none</files>` is allowed by BRIEF (53-12 now edits one file anyway).
- The review pass applied both lenses.
- (ratification 06oct2026) Row 36 (S28 Q-28.1, D-28e) answered "Add to S53": S53 now draws twoway's filled box behind each by() panel label, in the scheme's fill and outline. This supersedes the "Fixed (minor, Q-28.1 ruling)" line above and the old Boundaries and Notes wording.
- (ratification 06oct2026) Where the box is written: Overview, Risk 7, Dependencies (S28, S13, S30, S48), Evidence E6 (twoway measured under ten schemes; four Bokeh drawing routes measured in headless Chrome), US-53.6, BR-53.8, TR-53.1 (four regenerated keys), TR-53.8 (the colour-key pass skips the box), TR-53.12 to TR-53.15, the new TR-53.17 `_dash_by_label_box`, the Stata truth probes and BYA-06, `TestTheLabelBox` and its Chrome case, the new task 53-08, AC-53.7, the BUGS Resolution and the CHANGELOG line.
- (ratification 06oct2026) Task numbers: the old 53-08..53-13 are now 53-09..53-14. Amendment lines above that name 53-11 or 53-12 use the old numbers.
- (ratification 06oct2026) Batch 18 re-checked. The box adds one new S53 function, a copy-list name in S53's own block, and keys in S53's own regeneration and `SchemeParser._init_properties`. S53 still edits none of S51's Stata/Mata functions, nothing of S52's (`_dash_apply_z_options` included), and none of S28's helpers. S28's `dash_by_label` Title is only read and hidden, and `_dash_by_panel_label` is not edited.
- (ratification 06oct2026) Out of scope, residual: twoway restyles the box from the graph's `subtitle(, fcolor() lcolor() nobox)` (measured, E6). dash keeps naming those sub-options as it does today (`_DASH_TEXTBOX_HONOURED`, which S53 does not edit), and draws the scheme's box. The orchestrator decides whether S58 files a P2 row for it (Notes).

## Overview

**What is wrong today.** DROPIN-REMAINING.md:105-112 (P1.15): "`legend()` and `i*` axes … named and ignored; every panel draws a legend and repeats both axes". WP-29 notes: an explicit axis-2 title is drawn on every panel where twoway draws none; a colour key is drawn on every panel where twoway draws one only under `by(, clegend(on))`, showing the first panel's mapping. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-15.md` §1, critic; both modes alike):

```
(scatter mpg weight)(lfit mpg weight), by(foreign)
  each panel: legends 1 (2 items, visible), y axis visible "Mileage (mpg)", x axis visible "Weight (lbs.)"
  twoway: no panel legend, one overall legend (panel 1 has 2 keys); y axis on the left panel only, x axis on both bottom panels; titles once (l1title, b1title)
(scatter mpg weight)(scatter price weight, yaxis(2)), by(foreign) ytitle2(Price)
  each panel: y axes [(True, 'Mileage (mpg)'), (True, 'Price')]       twoway: no axis-2 title anywhere; axis 2 on the rightmost panel only (p27)
scatter mpg weight, colorvar(price) by(foreign)  [and by(foreign, clegend(on))]
  saved and served: 1 ColorBar per panel                                 twoway: none (q06); with clegend(on) one, panel 1's mapping (q07)
colorvar(rep78) colordiscrete by(foreign): a "_dash_clegend" Legend per panel, Domestic 6 items, Foreign 4 (critic 2)
by(foreign, legend(off) iyaxes noedgelabel …): drawn as if absent and named "by() sub-option(s) not implemented and ignored"
```

**After this section**, in the saved page and the served app, before and after every filter move:
- Each panel draws only the axes twoway's `set_outer_axes` draws: y on the leftmost panel of each row, x on the bottom panel of each column, the edge panel labelled unless `noedgelabel` or `compact`, the second y axis on the rightmost panel only; `iyaxes`/`ixaxes` (and `noi*`, `iylabels`, `iyticks`, `iytitles` and their x and `no` forms, `individual`) and a rescaled axis (WP-29) turn individual axes on as twoway does.
- The y and x axis titles are drawn once, beside and below the panels (twoway's l1title/b1title), unless `noytitles`/`noxtitles`; `iytitles`/`ixtitles` keep them per panel; no panel draws an axis-2 title.
- One legend, cloned from panel 1's keys, is drawn when panel 1 has more than one key, placed by `by(, legend(position() ring() at() span off on))` else the scheme's `by_legend_position`; `ilegends` keeps per-panel legends only; `legend(on)` outside by() adds them to the overall one; `legend(off)` outside by() is ignored, silently, as twoway ignores it.
- At most one colour key: none unless `by(, clegend(on))`, then one key showing panel 1's mapping (ColorBar or discrete), placed by `clegend(position() at())` else the scheme's `zyx2legend_position`; it follows panel 1 after a move.
- On a narrow screen, where the panel grid stacks into one column, every panel shows its axes and titles again (D3 a, register P1.15.3).
- The grid keeps one merged toolbar; the forms twoway ignores under by() stay silent (M6, with S31's axis silence).
- The scheme files carry twoway's `by_*`, `by_legend_*` and `zyx2legend_*` keys.
- (ratification row 36) Each panel label sits in twoway's filled box. The box spans the panel's plot region and sits on its top edge, filled with the scheme's by-label textbox colour and outlined in `bylabel_outline`: s2color bluishgray on bluishgray, stcolor gs15 on gs15, s1color ltkhaki outlined black, economist `ebg`. Its height is the label's text plus the subheading margins. The box is drawn on every panel, the Total panel included, and in both modes before and after every move.

**Why one section.** These are P1.15's shared-chrome parts (research §7 split, part 3; A138): they act on the panels S48 places, inside the chrome frame S28 builds, on axes S21/S31 finished, with keys S19 wrote and legend sub-options S10 reads. One entry, `P1.15c`, one post-pass family, one fixture and one regeneration. The panel label's box (ratification row 36) is chrome on the same panels, drawn by the same post-pass from keys of the same regeneration.

**Test order and commit rule (rule 7).** One cycle on `wp30-s53`: 53-01 and 53-02 write the fixture and every regression test (pytest, Chrome, truth cases) and run them against the unmodified batch-18 base, saving `$S/53-P1.15c-failure.txt` (no commit); 53-03 to 53-13 fix, regenerate, flip and document; 53-14 closes the entry and commits. No test-only commit exists, and no commit is red.

## Risk: [yellow] — three CRITICAL layout symbols, a page script that must run under the CSP, and a scheme regeneration

**Why.** (research §5, critic 3; re-run at 18.0)
- `DashRenderer._build_sources_and_figures` CRITICAL (14 impacted); `_dash_reflow` CRITICAL (12, 4 direct); `_dash_layout_cell` CRITICAL (10, 3 direct, 8 processes); `_dash_parse_by` CRITICAL (32, 9 direct, 16 processes).
- `ServerAppBuilder._generate_app_source` HIGH (5); `ServerAppBuilder._glyph_layer_lines` HIGH (4); `SchemeParser` LOW by graph but built by every render: HIGH.
- Read, not edited: `_dash_apply_legend`, `GlyphMapper._apply_colorvar`, `_dash_add_secondary_axes`, `_dash_finish_secondary_axes`, `_dash_share_by_scales` (CRITICAL 8), `_dash_by_tokens` (CRITICAL 49), S28's `_dash_by_chrome`/`_dash_by_frame_grid`, S48's position helper.
- `DashRenderer.render` (the saved document hook) and `_dash_tab_panels` (not edited): the 18.0 run records them.

**Risk factors.**
1. Hiding inner axes leaves stacked phone-width panels unlabelled unless a script turns them back on, and a page script must run under S04's CSP.
2. BokehJS writes `outer_width`/`inner_width` with `no_change` (bokeh.js 3.9.0 :45323-45328, checked for this file), so no `js_on_change` fires on resize; a hook needs a document-ready event and window resizes.
3. A legend in one Plot cannot draw renderers of another; clones must stay out of filter, brush and redraw paths.
4. Side cells (y title, legend) in a grid whose every column is `minmax(0, 1fr)` (`_dash_reflow`) would be as wide as a panel.
5. Many existing tests assert a legend, axis or ColorBar on every panel.
6. A regeneration in a batch where S52 edits only Python and S51 only Stata: one regenerator, last (A152).
7. (ratification row 36) Bokeh has no plain "box behind a title spanning the plot region" (E6). A `Title`'s own background spans only its text. A `BoxAnnotation` outside the frame is clipped away. An extra axis draws only one edge of the outline. The box is therefore a `ColorBar`, and the label's text is drawn by it, while S28's `Title` stays in the model hidden, so code or tests that count ColorBars, or read the label's visibility, can misread it.

**Mitigation.**
1. `_DASH_BY_STACK_JS` (a module constant, no user text) runs as a `CustomJS` on the document's `document_ready` event, re-checked on window resizes; the Chrome test runs it at 375 and 1400 px under the shipped CSP in both modes (IR-17 P1.15.3).
2. Measured: a `Document.js_on_event("document_ready", …)` callback is serialised by `components()` when the models are that document's roots (two roots, `'DASHREADY' in script` True), and dropped otherwise (False); TR-53.10 builds that document in the saved path; the served app has `doc` in `make_document`.
3. Clone renderers carry `_DASH_SWATCH_PREFIX` names (`_dash_is_swatch`) on one-row NaN sources in a cell outside `figures`; research's prototype drew them; `TestTheChromeIsNotData` asserts no clone in any filter callback's args or served redraw list.
4. `_dash_reflow` gives side-cell columns a `max-content` track and counts only panel columns for the stack threshold.
5. 53-01 greps and re-measures every pin; flips are listed in `$S/53-flips.txt` with reasons.
6. S53 merges last in batch 18 and regenerates through the extractor only (R7).
7. The box `ColorBar` is named `dash_by_label_box`, uses its own one-colour mapper, and is built after `_dash_by_keys` removes the panels' colour keys. `TestColourKeyUnderBy` and every flipped colour-key pin exclude it by name. S28's probe still reads the hidden Title's text. `TestTheLabelBox` and the Chrome case check that the drawn text equals that Title's finished text and that the box spans the plot region (E6).

## Dependencies

- **Depends on: 10, 15, 19, 21, 31, 48.**
  - S10 (batch 4): the legend sub-option table and readers (`_dash_legend_parts`, `_dash_legend_arg`, `_DASH_LEGEND_SUBOPTS` with `pos`, `posi`, `r`, `c`, `at`), through which `by(, legend())` and `clegend()` are read.
  - S15 (batch 5): `SchemeParser.axis_side`/`axis_flags` (edge axes follow `axis_side`, S15 Notes) and the title boxes the cells use.
  - S19 (batch 7): `_dash_axis_default_titles` (S19 Blocks: "S53 (titles once under by())"), the keys in panel 1's legend.
  - S21 (batch 7): common by() ranges and ticks (`_dash_common_count_ticks`), so outer axes label every panel's shared scale.
  - S31 (batch 11): `by_graph` silence of `off`, `nolabels`, `noticks`, `titlegap` (TR-31.10), `_dash_axis_alternate` (an `alt` y axis is the edge axis on the other side).
  - S48 (batch 17): the panel positions (`rows()`, `cols()`, `holes()`, `colfirst`; research's `_dash_by_positions`, re-found by symbol), `compact` (its spacing), the by() refusals and the parsed by() options S53 extends.
  - S28 (batch 10, through S48): chrome cells as bare `Plot`s, `_dash_by_chrome`, `_dash_by_frame_grid(grid, chrome, ncols)`, `_dash_by_chrome_figures`, the label `Title`s (`dash_by_label`, from `_dash_by_panel_label`, read and hidden by TR-53.17, never edited), `_dash_by_text_options`.
  - (ratification row 36) S13 (batch 5): `OptionTranslator.resolve_size` with the line kind, used for the box's outline width. S30 (batch 10): `SchemeParser._color`, which resolves the box colours the regeneration writes. S48: its by() size multiplier, applied to the box's margins and outline (re-found at the base).
  - S01: entry `P1.15c`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.15c -->` in the WP-30 group of `### Results that change`, the S53 stub `* ==== S53 P1.15c: Shared axes and keys under by() ====`, and the anchors `# WP-30 S53 (P1.15c): Shared axes and keys under by() (P1.15 part c)`.
  - Read: S04 (CSP; its headless-Chrome checker), S06 (notes), S24/S33 (colour-key chrome), S35 (y2/x2 kinds), S43/S47 (the last batches' renderer state).
- **Blocks:** none.
- **Parallel batch: 18**, merge order S51, S52, S53; S53 lands last (A152, regenerator).
- **Can run with:** S51 (Stata/Mata only) and S52 (`_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_axis_add`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_apply_z_options`, the finishers, Mata `_dash_rep_merge` and `_dash_axis_pieces`, dash.ado `_dash_axis_expand`'s comment). S53 edits none of them and they edit none of S53's; S53 is batch 18's only editor of `_generate_app_source`, `_build_sources_and_figures`, `_dash_layout_cell`, `_dash_reflow`, `_dash_parse_by`, `SchemeParser`, the extractor and the scheme files (R12).

## Evidence

Anchors at `c96facd` (dash_render.py 37,689 lines, dash.sthlp 3,822); S28 and S48 rewrote the by() paths since. The executor re-finds every symbol at `batch-18-base`.

### E1. The layout cell and reflow (dash_render.py)

`_dash_layout_cell` (25001) builds `gridplot(rows, sizing_mode="stretch_width")` for a faceted name and returns `_dash_name_save(_dash_reflow(grid))` (S28 frames it with `_dash_by_frame_grid`; S48 places panels by position). `_dash_reflow` (24465) makes every column `_DASH_BS_TRACK` and stacks a grid of `ncols` columns below `ncols × _DASH_MIN_COLUMN_PX` with a container query:

```python
24513        grid.cols = _DASH_BS_TRACK
24514        if ncols < 2:
24515            return grid
24516        css = (":host { container-type: inline-size; } "
24517               "@container (max-width: %.2fpx) { :host > .bk-GridBox { "
24518               "display: flex; flex-direction: column; } }"
```

`ncols` is the largest child column + 1 (:24506-24511), so a side cell would raise the threshold.

### E2. by() sub-options are named (dash_render.py:19856, 19941)

`_DASH_BY_SUPPORTED` holds cols, missing, total and the rescale words; S28 added the text sub-options and S48 rows/holes/colfirst/compact/iscale/imargin/style; every other word (`legend()`, `iyaxes`, `noedgelabel`, `ilegends`, `clegend()`) reaches `_dash_parse_by`'s one note.

### E3. The axis-2 title under by() (dash_render.py:23086-23093)

```python
23086        if str(graph_opts.get("by", "") or "").strip():
23087            dflt = ""
...
23093        text, opts = _dash_textbox_or_default(
23094            graph_opts.get(f"{n}title2", ""), f"{n}title2", dflt, seen, key)
```

The default is already empty under by(); an explicit `ytitle2()` is drawn on every panel (WP-29 S10 note). S53 clears it in its post-pass, so `_dash_add_secondary_axes` is not edited.

### E4. twoway's rules (StataNow 19.5; bygraph_g.class and research §2)

- Outer axes (`set_outer_axes` :916-992; `set_outer_axes_edges_only` :999-): with `edgelabel`, per row the y axes of panels at its leftmost column are drawn, per column the x axes of its bottom panel (an "edge" panel above a hole keeps its x axis); without it only the global left column and bottom row. Measured: p06 (2×2 with 3 panels: (1,1) y only, (1,2) x only, (2,1) both); `noedgelabel` and `compact` drop the edge x axis (p23, p24; `bygraphstyle-compact.style` sets `edgelabel no`); `iyaxes ixaxes` draw every axis (p21); `ixaxes` with total (p43); `iytick` alone changes nothing (p44); holes/colfirst move the rule with the panels (p08, p09, p40, p41); rescale turns individual axes on (`indiv_yaxes(yes)`, :363-385).
- Titles: l1title/b1title once from panel 1 (p01), empty when layers' titles differ (p02, S19's rule); no per-panel titles (`ytl=0 xtl=0`) unless `iytitle ixtitle` (p22); no axis-2 title (p27 `y2tl=0`, r1 empty); axis 2 only on the rightmost panel (p27).
- Legend (`SetLegend` :569-626): panels draw none; one overall legend copied from panel 1, drawn when it has >1 key (p01, p02); `by(, legend(off))` none (p03); `legend(off)` outside ignored (p04); `legend(on)` outside: per-panel and overall (p34); `ilegends` per-panel only (p32; `if indiv_legends exit`); `legend(at(4) pos(0))` in hole 4 (p05), `at(3)` with 2 panels a 2×2 grid (p46); `legend(pos(6))` below (r04), `pos(12) ring(0)` top inside (r06); contents from outside `legend(order(2 1))` (r04); default `by_legend_position` stcolor 3, s2color 6, economist 12, ring `by_legend_ring` 3.
- Colour key (`SetClegend` :628-): `if indiv_legends exit`; drawn only with `on`/`draw` (q06 none, q07 one), from panel 1 (`by_clegend_*` probes of `test/fixtures/colorvar_qualifier_truth.json`); position `zyx2legend_position` (bygraphstyle-default.style; s2color 3), `at()` a hole.
- Option spellings (`parse_settings` :266-283): `IXaxes IYaxes IXLabels IYLabels IXTicks IYTicks IXTitles IYTitles XTitles YTitles NOEDGElabel EDGElabel NOINDividual INDividual ILEGends` and their `NO` forms. Measured for this file (`$S/s51-53/probe.do`, records `B|…`, 04oct2026): `ix` → ixaxes, `iy` → iyaxes, `ixl` → ixlabels, `ixt` and `ixti` → ixticks (not ixtitles), `ixtit` → ixtitles, `noixt` → ixticks off, `noedge` → edgelabel off, `ileg` → ilegends; defaults ixticks, iyticks, ixlabels, edgelabel, outer titles on, ixaxes, iyaxes, ixtitles, iytitles, ilegends off.
- Scheme keys (grep of `ado/base/s/scheme-*.scheme`, 04oct2026): `clockdir by_legend_position` (3, 6, 12), `gridringstyle by_legend_ring 3`, `yesno by_edgelabel yes`, `by_outer_{x,y}{axes,titles} yes`, `by_indiv_{x,y}{axes,titles} no`, `by_indiv_{x,y}{labels,ticks} yes`, `by_indiv_as_whole no`, and bygraphstyle-default's `zyx2legend_position` (s2color `clockdir zyx2legend_position 3`).

### E5. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 53-01)

- `test/test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows::test_each_by_panel_maps_its_own_rows` (its second half asserts a ColorBar per panel; each panel's mapping stays twoway's, the bars go: none without `clegend(on)`).
- `test/test_colorvar_forms.py` (:310-312, the by() half of `test_a_z_option_on_a_discrete_key_is_named_once`): re-measured; under by() with no key drawn twoway prints nothing for `zlabel()` (M6), so the expectation becomes 0 notes unless 53-01's fixture shows otherwise.
- `test/test_mode_parity.py:1914` ("by() with an unimplemented sub-option": S48 moved it; S53 moves it again only if its words are now implemented).
- Shipped-file pins the regeneration turns red (measured against the HEAD tests): `test/test_help_claims_8.py::TestTheShippedFiles::test_no_directive_for_what_dash_does_not_draw` (:1104; its pattern `margin|…|tick(?!_label)` matches `margin by_indiv`, `yesno by_indiv_xticks` and `yesno by_indiv_yticks`): the pattern then applies outside the `by() axes and keys (WP-30 P1.15c)` group, as S36 exempted its own group, because S48 and S53 draw those keys; `::test_the_directive_count_is_what_the_help_says` (S24's rename of `test_80_to_140_directives`, bounds as S50 left them): 19 more directives per file, so its bounds and the help's numbers it reads are re-derived (R10).
- Candidates from the research flip list, re-measured: `test_help_claims_5.py` :478, :533, :545, :558, :652, :774, :802, :842, :1329 and HC5-07; `test_server_facets.py::TestAnUnimplementedBySuboptionIsNamed` (:491); `test_reserved_names.py`; `test_scheme_review_fixes.py`; `test_layout_facets.py`; `test_by_suboptions.cscript`; scheme fidelity tests for the new keys. 53-01 runs `grep -rln "by(\|\"by\"" test/*.py` and the new tests together, and every red pre-existing node is classified (pin to flip, or regression) in `$S/53-flips.txt`.

### E6. The panel label's box (ratification row 36; S28 D-28e; measured 06oct2026)

**twoway** (StataNow 19.5 through `scripts/stata_slot.sh`; scratch `…/wp30/s53box/box.do`, parsed by `parse.py`; `sysuse auto`, `twoway scatter mpg weight, by(foreign)`; SVG units, 10 = 1 pt). bygraphstyle-default.style draws the label as `subtitle(, astextbox box blcolor(scheme bylabel_outline))`. The fill is the `fillcolor` of the scheme's `textboxstyle subtitle`: textboxstyle-subheading.style `set fillcolor scheme textbox`, textboxstyle-subheading_gs.style `set fillcolor scheme bylabel_outline`. The outline is `bylabel_outline` at the `linewidth` of the style's linestyle (`textbox` → `foreground`, `foreground_center` → `foreground`). The box spans the panel's plot region exactly (same x and width as its region rect) and sits on its top edge:

```
scheme     fill     outline  stroke   box h / label font   box x, width = plot region's
s2color    #D9E6EB  #D9E6EB  4.90     122.89 / 93.56        388.33, 1683.50 (yes)
s2mono     #D0D0D0  #D9E6EB  4.90     122.89 / 93.56        yes
s1color    #E5DAA5  #000000  4.90     122.89 / 93.56        yes
s1mono     #D0D0D0  #000000  4.90     122.89 / 93.56        yes
s1rcolor   #90353B  #FFFFFF  4.90     122.89 / 93.56        yes (label text white)
sj         #D0D0D0  #D9E6EB  3.18      79.88 / 60.81        252.41, 1094.27 (yes)
stcolor    #F0F0F0  #F0F0F0  5.51     138.38 / 105.13       553.33, 2196.62 (yes; one rect with fill and stroke)
stmono1    #FFFFFF  #FFFFFF  5.51     138.38 / 105.13       yes
sttrans    #D9E6EB  #D9E6EB  5.51     138.38 / 105.13       478.91, 2345.46 (yes)
economist  #C6D3DF  #C6D3DF  3.00     105.29 / 51.43        yes (label left-justified, inset 29.6 units)
by(foreign rep78)  s2color  115.59 / 87.99 (smaller panels, same rule);  by(foreign, total): the Total panel boxed too
subtitle(, fcolor(red) lcolor(blue))  fill #FF0000, outline #0000FF    subtitle(, nobox)  no box
by(foreign, subtitle(, fcolor(red)))  unchanged (by()'s own subtitle is the overall one)
```

The stroke is 0.17 rs in every scheme at by()'s size multiplier (s2color 4.90 / 28.8; stcolor 5.51 / 32.4; sj 3.18 / 18.72). The box height minus the font size is the subheading margins at the same multiplier: s2color `margin subheading vsmall` = 0.6 + 0.6 rs, × 0.85 = 1.02 rs, against 29.33 / 28.8 = 1.018 rs measured. economist's `esubhead` margin has a zero top. Every s2color-family scheme's `color textbox` equals its `color bylabel_outline` except s2mono and sj (gs13 / bluishgray), s1color, s1mono and s1rcolor, so a visible outline matters.

**Bokeh 3.9.0 routes** (headless Chrome screenshots of a 400 × 300 figure, frame x 30-394, scratch `…/s53box/node*.py`; red fill, blue outline):
- `Title(background_fill_color=…)`: bokeh.js `TextAnnotationView` paints a rect of the text's size plus `padding`, so the fill covers the text only.
- `BoxAnnotation` with `Node(target="frame", symbol="top", offset=-22)` edges, in the centre or added to `"above"`: nothing drawn. An annotation without a side-panel layout is clipped to the frame (`AnnotationView.needs_clip`), and the side panel does not lay it out.
- An extra `LinearAxis` in `"above"` with `background_fill_color`: fill x 30-394, y 1-30 (the frame's width). Its axis line draws one edge only, so a full outline is impossible.
- **`ColorBar`**, horizontal, `padding=0`, `margin=0`, `height=24`, one-colour `LinearColorMapper(palette=[fill], low=0, high=1)`, `bar_line_color` the outline, `major_tick_line_color=None`, `ticker=FixedTicker(ticks=[t])`, `major_label_overrides={t: text}`, `major_label_text_baseline="middle"`, `label_standoff=-(24 + 16) // 2 - 2`, inserted at index 0 of `fig.above`. Fill x 30-394 × y 1-23, outline 29-395 × 0-24 (all four edges), frame top at 25. A 16 px label sits at y 7-19: centred at x 180-245 (`t=0.5`, centre 212.5 against the frame's 212) and left at x 31-70 (`t=0`, `major_label_text_align="left"`). Right (`t=1`) ended at x 371, 23 px short of the edge, so it is not used without a Chrome check. A hidden `Title` (`visible=False`) takes no space: the frame top stays 25.

## User stories

- **US-53.1** As a twoway user, I want `scatter y x, by(g)` to show axes only on the outer panels with each axis title once, so the panels have room and look like Stata's.
- **US-53.2** As a twoway user, I want `iyaxes`, `ixaxes`, `noedgelabel` and the other `i*` options to change which axes are drawn exactly as in Stata.
- **US-53.3** As a twoway user with several layers, I want one legend for the whole array, placed by `by(, legend(pos(6)))` or `at()`, not one per panel.
- **US-53.4** As a twoway user with `colorvar()`, I want no colour key per panel, and one key showing the first panel's mapping when I ask with `by(, clegend(on))`.
- **US-53.5** As a phone user, I want stacked panels to show their axes so each one can be read alone.
- **US-53.6** As a twoway user, I want each by() panel's label drawn in the scheme's shaded box across the top of the panel, as Stata draws it, so the panels read as Stata's do (ratification row 36).

## Business requirements

- **BR-53.1** Panel axes follow E4's outer-axes rule for every grid S48 produces (rows, cols, holes, colfirst, total), with edge labels unless `noedgelabel` or `compact`; the `i*`/`noi*`/`individual` options and rescaled axes turn individual axes, labels, ticks and titles on and off as twoway does; on a second y axis only the rightmost panel of each row draws it.
- **BR-53.2** The y and x axis titles are drawn once beside and below the array (from panel 1, by S19's rule) unless `noytitles`/`noxtitles`; no panel draws an axis-2 title.
- **BR-53.3** One overall legend (panel 1's keys, as `legend()` outside by() orders and labels them) is drawn when panel 1 has more than one key or `by(, legend(on))`, and not with `by(, legend(off))`; it sits at `by(, legend(position()))` else the scheme's `by_legend_position`, or in grid hole `at()`; `ilegends` draws per-panel legends only; `legend(on)` outside by() draws both; `legend(off)` outside by() changes nothing and prints nothing.
- **BR-53.4** No colour key is drawn under by() unless `by(, clegend(on))`; then one key, from panel 1's mapping (continuous or discrete), placed by `clegend(position() at())` else the scheme's `zyx2legend_position`; it reflects panel 1 after a move. A level has the same colour in every panel (guard first, register P1.15.8).
- **BR-53.5** When the panel grid stacks into one column, every panel shows its axes and its own axis titles, and the outer title cells hide; when it widens again, twoway's layout returns.
- **BR-53.6** The saved page and the served app draw the same chrome before and after every filter move; the grid's toolbar holds one save tool that saves `<name>.png`.
- **BR-53.7** The forms twoway ignores under by() print nothing (M6); a form dash draws differently (`legend(ring(0))` outside the panels) is named once.
- **BR-53.8** (ratification row 36) Every by() panel with a label (the Total panel included) draws the label inside a box. The box spans the panel's plot region and sits on its top edge. It is filled with the scheme's by-label fill (the `fillcolor` of its `textboxstyle subtitle`) and outlined all round in `bylabel_outline`, at the `foreground` line width × by()'s size multiplier. Its height is the label's text plus the scheme's subheading margins at the same multiplier. The label keeps S28's text, size, colour and justification. A panel without a label (`subtitle("")`) draws no box. Both modes draw the same box before and after every filter move. The box is not data, not a colour key and not clickable.

## Technical requirements

- **TR-53.1 Scheme keys (A152; S53 regenerates, last).** `scripts/extract_scheme_truth.py` resolves through the include chain and writes into each of the 26 `dash-<name>.scheme` files and `test/fixtures/scheme_truth.json`: `clockdir by_legend_position`, `gridringstyle by_legend_ring`, `clockdir zyx2legend_position`, `gridringstyle zyx2legend_ring`, and `yesno by_edgelabel`, `by_outer_xaxes`, `by_outer_yaxes`, `by_outer_xtitles`, `by_outer_ytitles`, `by_indiv_xaxes`, `by_indiv_yaxes`, `by_indiv_xlabels`, `by_indiv_ylabels`, `by_indiv_xticks`, `by_indiv_yticks`, `by_indiv_xtitles`, `by_indiv_ytitles`, `by_indiv_as_whole`, and `margin by_indiv` (s2color `small`, scheme-s2color.scheme:729; S48's D-48e contract: S48's `SchemeParser.by_indiv_margin` then reads it from every shipped file, its transcribed table backing only a file without the key); and for the label box (ratification row 36, E6): `color by_label_fill` (dash's derived key: the scheme's `textboxstyle subtitle` resolved to its style file's `set fillcolor scheme <key>`, then `color <key>`, written as `#RRGGBB` with a provenance comment), `color bylabel_outline`, `linewidth foreground` and `margin subheading` (top and bottom in rs, resolved through `margin-<name>.style` and the scheme's `gsize <…>margin` keys). Each is emitted only when no earlier regeneration already writes it (re-grep at `batch-18-base`). All go in one emitted group headed "by() axes and keys (WP-30 P1.15c)". `SchemeParser._init_properties` reads them into `by_legend_position` (int 0-12, default 6), `by_legend_ring`, `zyx2_position` (default 3), `zyx2_ring`, and a dict `by_flags` (yes → True); and `by_label_fill`, `by_label_outline` (colours through `SchemeParser._color`), `by_label_line_pt` (the `foreground` width in points through `OptionTranslator.resolve_size(…, "line", …)`) and `by_label_margin_rs` (top, bottom). All have `_FALLBACK_PROPS` entries at s2color's values (`#D9E6EB`, `#D9E6EB`, 0.2 rs × 2.88, (0.6, 0.6)). Every pre-existing property of every scheme is verified unchanged (R7).
- **TR-53.2 New constant `_DASH_BY_AXES_SPELLINGS`** (after `_DASH_BY_RESCALE_KEYS`): each key (`ixaxes`, `iyaxes`, `ixlabels`, `iylabels`, `ixticks`, `iyticks`, `ixtitles`, `iytitles`, `xtitles`, `ytitles`, `edgelabel`, `individual`, `ilegends`, and the `no` forms) to the tuple of its spellings from its minimum to its full name, transcribed from `parse_settings` with E4's measured ambiguity rule (`ixt`, `ixti` → ixticks; ixtitles from `ixtit`); lower case only. A comment cites bygraph_g.class:266-283 and the probe records.
- **TR-53.3 New `_dash_by_axes_options(by_raw, scheme=None) -> dict`** (after S28's by() text helpers): from the scheme's `by_flags` (or the s2color defaults), applies each typed word from `_dash_by_tokens` of the sub-options (positive and `no` forms set or clear; both given → the fixture's xor rule, probe `iyaxes noiyaxes`); `compact` (S48's parse) and `style(compact)` clear `edgelabel`; `individual` sets `indiv_as_whole`; `legend` and `clegend` raw values are the merged arguments of every `legend(`/`leg…(` and `clegend(` token (spellings per S10's table; repeated copies' sub-options joined, last wins per setting); returns `{"flags": {…}, "legend": str, "clegend": str}`. Total, linear, never raises.
- **TR-53.4 `_dash_parse_by`** (in place, CRITICAL; warn): one branch before the `style` branch: tokens `_DASH_BY_AXES_SPELLINGS` or the legend/clegend readers recognise pass silently, with a comment "drawn by `_dash_by_side` (WP-30 P1.15c)"; its 5-tuple and every other branch unchanged.
- **TR-53.5 New `_dash_by_axis_flags(positions, opts) -> dict`** (pure): `positions` maps panel index to `(row, col)` (S48's output, holes absent); returns per panel `{"y": bool, "x": bool, "y2": bool, "x2": bool, "ylab": bool, "xlab": bool, "ytick": bool, "xtick": bool, "ytitle": bool, "xtitle": bool}` by E4's two rules (edgelabel or edges only), `indiv_*axes` (every panel), `indiv_as_whole` (every panel, every title), `indiv_*labels/ticks` (labels and ticks of individually drawn axes), `indiv_*titles` (per-panel titles), and `rescaled` letters passed in `opts["rescaled"]` (WP-29's `_dash_by_rescale` result; a rescaled letter is individual). `y2` is True for the panel with the largest column in each row; `x2` for the panel with the smallest row in each column. Unit-tested against every fixture grid.
- **TR-53.6 New `_dash_by_outer_axes(figs, positions, opts)`**: for each panel figure and its flags, `axis.visible` of every primary y/x axis (`_dash_primary_axes`) and every y2/x2 axis (by `y_range_name`/`x_range_name`); on a drawn individual axis, `major_label_text_font_size = "0px"` when its labels are off and `major_tick_in = major_tick_out = 0` when its ticks are off (S31's look otherwise kept); `axis_label = None` on every y2/x2 axis (E4 p27) and on primary axes whose per-panel title is off. It returns `{"y": text, "x": text, "labels": [(axis, text), …]}`: panel 1's primary titles read before clearing (S19's resolved text, S29's translation already applied) and every cleared `(axis, text)` for TR-53.9. Never touches ranges or tickers.
- **TR-53.7 New `_dash_by_cell(scheme, name, frame=(1, 1))`**: a bare `Plot` built as S28's `_dash_by_text_cell` builds one (no axis, grid or tool, `toolbar_location=None`, `outline_line_color=None`, the scheme's fills), named one of `dash_by_ytitle`, `dash_by_xtitle`, `dash_by_legend`, `dash_by_clegend`, `dash_by_ruler`.
  - Title cells: a `Title(text=…)` added `"left"` (vertical) or `"below"`, sized and coloured from the scheme's axis-title textbox (as `_dash_style_axis_titles` reads it), `align="center"`.
  - `dash_by_ruler`: a zero-height cell spanning the panel columns, added only when no other spanning cell exists (TR-53.9's width reference).
- **TR-53.8 New `_dash_by_keys(figs, opts, scheme) -> dict`** (the legends and colour keys):
  - Panel legends (`fig.legend`, excluding `_COLORVAR_LEGEND_NAME`): `visible = False` unless `ilegends` or the graph's own `legend(on)` (E4 p32, p34).
  - Overall legend unless `ilegends`: `parts = _dash_legend_parts(opts["legend"])` (S10); off/nodraw → none; else drawn when on/draw or panel 1's legend has more than one item. The cell `dash_by_legend` holds, for each item of panel 1's legend in order, clones of its renderers: `GlyphRenderer(data_source=ColumnDataSource({f: [nan] for f in <the fields the glyph's dataspecs name>}), glyph=type(g)(**g.properties_with_values(include_defaults=False)), name=f"{_DASH_SWATCH_PREFIX}by_{i}")`, and one `Legend(items=[LegendItem(label=item.label, renderers=clones)], …)` styled as panel 1's legend (orientation, columns, text font and colour copied), `click_policy="none"`, added on the cell's side that faces the panels.
  - Placement: `position()` through the clock-to-side mapping `_dash_apply_legend` uses (re-found), else `scheme.by_legend_position`; `at(k)` → the hole k (TR-53.9); `ring(0)` → the same side cell, named once ("by(, legend(ring(0))) is drawn beside the panels"); `span` is the cell's default, silent.
  - Colour keys: every panel's `ColorBar` (any named `dash_by_label_box` excepted: TR-53.17 adds the label boxes after this pass, and the exception guards a re-run) and `_COLORVAR_LEGEND_NAME` legend are removed from its layout lists. Unless `ilegends`, `clegend()` with `on`/`draw` → the cell `dash_by_clegend`: a `ColorBar` whose `color_mapper` is panel 1's mapper object (the same model, so a move that updates panel 1's mapper updates the key) with panel 1's bar's ticker and formatter, or, for a discrete key, clones of panel 1's `_dash_clegend` swatches as above; placed by `clegend(position() at())` else `scheme.zyx2_position`.
  - Returns `{"legend": cell or None, "legend_side": side, "legend_at": k or 0, "clegend": …, "clegend_side": …, "clegend_at": …}`.
- **TR-53.9 New `_dash_by_side(figs, positions, graph_opts, scheme, seen=None, key="") -> dict`** (the post-pass) and **`_dash_by_side_grid(grid, side, nrows, ncols) -> int`**:
  - `_dash_by_side`: `opts = _dash_by_axes_options(graph_opts.get("by"), scheme)` plus `opts["rescaled"]`; `flags = _dash_by_axis_flags(positions, opts)`; `titles = _dash_by_outer_axes(figs, positions, opts)`; title cells when `outer_ytitles`/`outer_xtitles` and the text is non-empty; `keys = _dash_by_keys(…)`; the stack hook of TR-53.10. Stored on the first panel figure as `_dash_by_side` (as S28 stores `_dash_by_chrome`).
  - `_dash_by_side_grid`: shifts every panel child right by 1 when a y-title cell exists and places it at `(0, 0, nrows, 1)`; the x-title cell at `(nrows, c0, 1, ncols)`; a legend or key cell on side right at `(0, last + 1, nrows, 1)`, left before the y-title column, above at row 0 (shifting the rest down) and below after the x-title row, each spanning; an `at(k)` cell at hole k's position (S48's positions with `legend_at`; if S48's helper has no such parameter, S53 adds `legend_at` as twoway's `legend_hole`, counted in `full_n`, with a unit test). It returns the total column count, passed as `ncols` to S28's `_dash_by_frame_grid`. Every side child is a 5-tuple; panel tuples keep their form.
  - Positions with the key holes: `_dash_by_side` computes `positions` with S48's own call, `_dash_by_positions(n, _dash_by_grid_options(graph_opts.get("by")), legend_at=<legend at()>, clegend_at=<clegend at()>)`, and stores both hole numbers in its result; `_dash_layout_cell` reads `side` before S48's placement and passes the same two numbers to that call, so the panels' cells, `full_n` and S48's size multiplier count the holes as twoway's `full_n` does (E4 p05, p46), and the axis flags and the grid agree.
  - `_dash_layout_cell` (in place, CRITICAL; warn): `side = getattr(figs[0], "_dash_by_side", None)` is read first and its holes passed to S48's placement (above); `cn = _dash_by_side_grid(grid, side, nrows, ncols)` when `side`; then S28's frame with `cn`; then `_dash_reflow`, `_dash_name_save`. `gridplot()` still makes the grid (one merged `SaveTool`).
  - `_dash_reflow` (in place, CRITICAL; warn): for a grid whose children include `Plot`s named `dash_by_ytitle`, `dash_by_legend`, `dash_by_clegend` in their own column, `grid.cols` becomes a dict giving those columns `"max-content"` and the others `_DASH_BS_TRACK`; `ncols` for the stack threshold counts only columns holding a child whose `name` does not start with `dash_by_` (a panel figure). Its docstring gains one paragraph.
- **TR-53.10 The stacked view (D3 a; register P1.15.3; IR-17).**
  - `_DASH_BY_STACK_JS` (module constant; no user text; no BokehJS view internals): `check()` reads `ruler.outer_width` and `panels[0].outer_width` inside `try` (unset → 0); while either is 0 it retries with `setTimeout(check, 500)` up to 120 times; `stacked = panels.length > 1 && pw > 0.75 * rw`; it sets each listed axis's `visible`, restores or clears each listed axis's `axis_label` from `JSON.parse(labels_json)`, and sets each title cell's `visible = !stacked`, only when the state changed. On first run it adds one `window` `resize` listener (debounced with `requestAnimationFrame` then `setTimeout(check, 100)`).
  - `_dash_by_stack_hook(...)` builds `CustomJS(name="dash_by_stack", args={"panels": figs, "axes": <axes TR-53.6 hid>, "labels_json": json.dumps(<cleared titles>, allow_nan=False), "cells": <title cells>, "ruler": <x-title cell, else S28's head or foot cell, else dash_by_ruler>}, code=_DASH_BY_STACK_JS)` when the grid has two or more panel columns. User text (titles) travels only in `labels_json`, as data.
  - `_dash_by_stack_hooks(models) -> list`: every `CustomJS` named `dash_by_stack` among `m.references()` of the given roots.
  - Saved (`DashRenderer.render`, after `file_html(_dummy_col, …)` and before `components(all_models)`): when `_dash_by_stack_hooks(all_models)` is non-empty, `doc = Document()`, `doc.add_root(m)` for each of `all_models`, `doc.js_on_event("document_ready", *hooks)`; `components(all_models)` then serialises the callbacks (measured, Risk mitigation 2).
  - Served (template, after `doc.add_root(layout)`, :36379): `_hooks = _dash_by_stack_hooks([layout])` and, when non-empty, `doc.js_on_event("document_ready", *_hooks)`.
  - The code runs as every `CustomJS` does under S04's CSP; the Chrome test checks it.
- **TR-53.17 New `_dash_by_label_box(fig, scheme, mult=1.0) -> ColorBar | None`** (ratification row 36; E6). It is called by `_dash_by_side` for every panel figure, after `_dash_by_keys`, with S48's by() size multiplier as `mult` (re-found).
  - It finds S28's label: the first `Title` named `dash_by_label` in any side list of `fig`. With none, or with empty text, it returns None and adds nothing.
  - It builds `ColorBar(name="dash_by_label_box", orientation="horizontal", padding=0, margin=0, color_mapper=LinearColorMapper(palette=[scheme.by_label_fill], low=0, high=1), bar_line_color=scheme.by_label_outline, bar_line_width=<by_label_line_pt × 4/3 × mult px>, border_line_color=None, background_fill_alpha=0, major_tick_line_color=None, minor_tick_line_color=None, ticker=FixedTicker(ticks=[t]), major_label_overrides={t: <the Title's text>}, major_label_text_align=<"center" | "left" | "right">, major_label_text_baseline="middle", major_label_text_font_size/…_color/…_font_style/…_font=<the Title's>, height=<H>, label_standoff=-(H + F) // 2 - 2)`, where:
    - F is the Title's font size in px (`OptionTranslator.css_to_pt` × 4/3);
    - H is round(F + (top + bottom of `by_label_margin_rs`) × 3.84 × mult);
    - t is 0.5 for a centred label and 0 for a left one (economist). A right-justified scheme takes t = 1 only after the Chrome case passes for it (E6), and is otherwise drawn centred and named in the Notes;
    - the left inset (economist 29.6 units) is not drawn (Notes).
  - The box is inserted into the Title's own side list at the Title's index, and the Title is set `visible=False`. It stays in the model as the label's text record, so S28's probe and the canvas-text passes still read it, and a hidden Title takes no space (E6).
  - The text is copied after the label's text is final. At `batch-18-base` the executor re-finds where S09's `_dash_finish_graph_text`, S28's second text pass and S29's translation run relative to `_dash_by_side`. If any of them runs later, the box's `major_label_overrides` value is finished by that same pass (through `_dash_by_chrome_figures`, which then lists the box). `TestTheLabelBox::test_the_label_is_drawn_in_the_box` pins this with a TeX and an SMCL value label.
  - The function never raises. Colours are scheme values, the text is the Title's (canvas), and the names are constants.
- **TR-53.11 Wiring, both modes.**
  - Saved `_build_sources_and_figures` (CRITICAL; warn): in the facet branch, after S28's `_dash_by_chrome` assignment, `self.figures[<first panel>]._dash_by_side = _dash_by_side(<the graph's panel figures in facet order>, <S48's positions for them>, graph_options, self.scheme, getattr(self, "_reported_subopts", None), name)`; S28's canvas-text pass also walks the new title cells (`_dash_by_chrome_figures` gains them through `_dash_by_side`'s cells, so S29's SMCL and S09's TeX rules apply).
  - Served template: the same generated lines after S28's, with `figures`, `_facet_map`, `go`, `_DASH_SCHEME`, `_reported_subopts`, `gname`.
- **TR-53.12 Served copy list** (R2 row S53): on new lines directly after `"_dash_reflow",` (33354): `# by() axes and keys (WP-30 P1.15c).`, `"_dash_by_axes_options", "_dash_by_axis_flags", "_dash_by_outer_axes",`, `"_dash_by_cell", "_dash_by_keys", "_dash_by_side", "_dash_by_side_grid",`, `"_dash_by_stack_hook", "_dash_by_stack_hooks", "_dash_by_label_box",`. `_DASH_BY_AXES_SPELLINGS` and `_DASH_BY_STACK_JS` reach the app as S28's `_DASH_BY_TEXT_SPELLINGS` does (TR-28.8, `_supply_missing_constants`); the served-name guards confirm it. `_dash_parse_by`, `_dash_layout_cell`, `_dash_reflow` change in place.
- **TR-53.13 Registries.** `test/function_test_map.py` under S53's anchor, alphabetical: the ten functions of TR-53.12, each to its `test/test_by_axes_keys.py::TestTheUnitFunctions::test_<name>` (`_dash_by_label_box` to `TestTheLabelBox::test_unit`). No Stata program.
- **TR-53.14 Help** (R3: "Faceting with by()", S53's in batch 18): document the outer-axes rule, `noedgelabel`, the `i*`/`noi*` options and `individual`, titles once and no axis-2 title, the one legend (`by(, legend())`, `at()`, `ilegends`, `legend(on)` outside), the one colour key under `by(, clegend(on))` showing panel 1's mapping, phone-width stacking, that the overall key is not clickable, and that each panel label is drawn in the scheme's filled box across the panel (and that `subtitle()`'s `fcolor()`, `lcolor()` and `nobox` do not restyle it in dash; ratification row 36); remove the sentences that call these named and ignored (re-grepped after S28's and S48's edits). Lines at most 79 characters.
- **TR-53.15 Security (rule 1).** New text sinks are canvas only (`Title.text` in the title cells, `LegendItem.label` copied from panel 1, and the label box's `major_label_overrides` value copied from S28's Title); they are registered in `test/test_label_sinks.py` (`TestTextSinks`). No user text becomes a model name, a property name or code: cell, hook and clone names are constants or built from integers; titles reach the script only as JSON data in `args`. `_dash_by_axes_options` matches tokens against a constant table, linearly; clones read field names from the glyph's own dataspecs, never from input. The scheme extractor parses files as data (M7's guards unchanged).
- **TR-53.16 Guard first (register P1.15.8).** Before removing per-panel keys, `TestColourKeyUnderBy::test_a_level_has_one_colour` asserts, in both modes, that a discrete level's colour is the same in every panel; if it is red at the base, the section stops and reports (a colour-assignment defect outside this scope).

## Boundaries

- **Batch partners:** S51's Stata/Mata functions; S52's axis-parser, applier, `_dash_axis_add`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_apply_z_options`, finisher and Mata/ado functions. S53 edits none.
- **Not edited:** `_dash_apply_legend`, `GlyphMapper._apply_colorvar`, `_dash_add_secondary_axes`, `_dash_finish_secondary_axes`, `_dash_share_by_scales`, `_make_figure_body`, `_build_filter_widgets`, `_FILTER_JS`, `_dash_tab_panels`, `_dash_name_save`, S28's text helpers (only called), dash.ado, dash_parse.mata.
- **Not this section's:** `by(, graphregion() plotregion())` stay named (IR-9; S58 files a P2 item); `subtitle(, fcolor() lcolor() bcolor() box nobox)` restyling the panel box (named as today, E6; ratification row 36 covers the scheme's box only); the box's left inset under a left-justified scheme; `subtitle(, ring(0) pos())` (P2.4); alternate by() axes (`by_alternate_*`, commented out in bygraph_g.class); `shrink`/`ishrink`; a clickable overall legend.
- **Tracking documents:** S58 only (A145).

## Stata truth

New extractor `scripts/extract_by_chrome_truth.do` → `test/fixtures/by_chrome_truth.json` (the name PLAN.md gives and S28's D-28c leaves to S53), in S02's path-free form (TR-02.9 stanza; `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `set graphics off`, `version 19`), `_meta` as S28's extractor writes it (four keys; the python block never calls Stata, no `shell=True`, a backtick as `\x60`).

- **Recorder** (research's truth_by.do): per probe `rc`, `rows`, `cols`, `holes`, `legend_hole`; per panel k (`.Graph.graphs[k]`) `yaxis1`, `xaxis1`, `yaxis2` `draw_view`, their `title.draw_view`, `legend.draw_view`, `clegend.draw_view`; overall `l1title`, `b1title`, `r1title` text, `.legend.draw_view`, `.clegend.draw_view`; `.style.{indiv_*, outer_*, edgelabel, indiv_legends}.istrue`; the legend's side from the exported SVG through `scripts/svg_truth.py`.
- **Label-box probes** (ratification row 36, E6). `scatter mpg weight, by(foreign)` runs under every scheme of `SchemeParser._BUILTIN_NAMES` (26), plus `by(foreign rep78)`, `by(foreign, total)`, `subtitle(, fcolor(red) lcolor(blue))` and `subtitle(, nobox)` under s2color. Per panel the recorder keeps, from the SVG through `scripts/svg_truth.py`, the rect or rects drawn just before the label's `<text>`: fill, stroke, stroke-width, x, y, width and height. It also keeps the panel's plot-region rect, the label's font size, anchor and x, and `units_per_rs`. The two `subtitle()` probes are recorded, not asserted (residual).
- **Probes** (`sysuse auto`; `(scatter mpg weight)(lfit mpg weight)` unless named): p01-p06, p08, p09, p18-p24, p27, p32-p34, p40, p41, p43, p44, p46, q06, q07 (and the discrete `colorvar(rep78) colordiscrete`), r04-r06 under stcolor; p02 under s2color and economist; E4's abbreviation probes; `iyaxes noiyaxes` and `noiyaxes iyaxes`; `by(foreign rep78, compact)`; `yrescale`.
- **Run:** `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_by_chrome_truth.do"` (log `$S/extract_by_chrome_truth.log`). `git add -f test/fixtures/by_chrome_truth.json`.

**S53 block of `test/test_wp30_truth.cscript`** (fills S01's stub; helpers `_s53_*` above its header): **BYA-01** p06's per-panel axis draw flags from twoway against dash's saved page (python reader of the page's figures' axis `visible`); **BYA-02** p27 (axis 2 rightmost, no axis-2 title); **BYA-03** p02 one legend and its side under stcolor and s2color; **BYA-04** q07 one colour key; **BYA-05** `ixt` reads as ixticks in both; **BYA-06** (ratification row 36) the label box under s2color and stcolor: twoway's box fill and outline (from its SVG) equal dash's saved and served `dash_by_label_box` palette colour and `bar_line_color`, case-insensitive.

## TDD test stubs

New `test/test_by_axes_keys.py`. Imports: `dash_render as dr`; `test_mode_parity` `_render_pair`, `_spec`, `plot_for`; `test_served_filter_move` `_move as _served_move`; `test_saved_filter_layers` `_render`, `_move`; S28's find-panel-by-label test helper (its name re-found at the base); `colour_bins as cb`. `_FIX = json.load(test/fixtures/by_chrome_truth.json)`; `_MODES = ("saved", "served")`.

Regression tests (red at the batch-18 base unless marked guard):
- Test: the fixture has the four `_meta` keys and every probe — `TestTheFixture::test_it_is_stamped` (guard after 53-01)
- Test: `_dash_by_axis_flags` equals the fixture's per-panel y/x/y2 draw flags for every probe's grid — `TestTheUnitFunctions::test__dash_by_axis_flags` (and one `test_<name>` per TR-53.12 function)
- Test: per probe, both modes, each panel's drawn axes equal the fixture's — `TestOuterAxes::test_probe[mode-<id>]`
- Test: titles once: no panel `axis_label` (unless `iytitles`), the title cells hold p01's l1/b1 text, no axis-2 title anywhere (p27) — `TestAxisTitlesOnce::test_probe[mode-<id>]`
- Test: legends: panel legends hidden, one overall cell with panel 1's labels in order (r04 `order(2 1)`), none for p01/p03, per-panel only for p32, both for p34, the cell's side per scheme (stcolor right, s2color below, economist above), `at(4)` in the hole — `TestOneLegend::test_probe[mode-<id>]`
- Test: clones are named with `_DASH_SWATCH_PREFIX`, appear in no filter callback's args, no served redraw list and no CSV — `TestTheChromeIsNotData::test_clones_are_not_data[mode]`
- Test: colour keys: no `ColorBar` (other than one named `dash_by_label_box`) and no `_dash_clegend` on any panel; with `clegend(on)` one key cell whose mapper is panel 1's (continuous and discrete) — `TestColourKeyUnderBy::test_key[mode-<case>]`
- Test (guard first, TR-53.16): a discrete level has one colour in every panel — `TestColourKeyUnderBy::test_a_level_has_one_colour[mode]`
- Test: after a served `_served_move` and a saved `_move`, the key's bounds equal panel 1's mapper bounds and every axis flag is unchanged — `TestAfterAFilterMove::test_chrome_holds[mode]`
- Test: `by(foreign, legend(off) iyaxes noedgelabel ilegends clegend(on) ixt)` names none of them; `legend(off)` outside by() prints nothing; `legend(ring(0))` inside by() is named once — `TestTheNotes::test_silent_and_named[mode]`
- Test: the grid has one `SaveTool` and `_dash_name_save` names it `<name>` — `TestTheToolbar::test_one_save_tool[mode]` (guard)
- Test: `_dash_reflow` gives side columns `max-content` and counts panel columns only — `TestTheUnitFunctions::test_reflow_side_columns`
- Test: every spelling in `_DASH_BY_AXES_SPELLINGS` is a valid spelling of the same name in S48's `_DASH_BY_GRAMMAR` (minimum and ambiguity rule alike), so dash.ado's refusals and the renderer's reading never disagree — `TestTheUnitFunctions::test_spellings_agree_with_the_grammar`
- Test: with `by(foreign, legend(at(3) pos(0)))` on two panels, the grid is 2×2 with the legend in cell 3, and the panels' by() size multiplier is the one for `full_n` 3 (E4 p46) — `TestOneLegend::test_a_hole_counts_in_the_grid[mode]`
- Test: the saved page's script holds `document_ready` and `dash_by_stack`; the served document has the callback — `TestTheStackHook::test_attached[mode]`
- Test: the 26 scheme files carry the TR-53.1 keys with the values `scheme_truth.json` records; `SchemeParser` reads them — `TestTheSchemeKeys::test_every_scheme`
- Test: dash.sthlp "Faceting with by()" documents the options and no longer calls them ignored — `TestTheHelp::test_it_documents_shared_axes_and_keys`
- Test (ratification row 36): `_dash_by_label_box` on a hand-built figure with a `dash_by_label` Title returns a `ColorBar` named `dash_by_label_box`, inserted at the Title's index, and hides the Title; it returns None with no Title or an empty one — `TestTheLabelBox::test_unit`
- Test [mode-scheme] over the 26 schemes: each panel's box fill (`color_mapper.palette[0]`) and `bar_line_color` equal the fixture's twoway fill and outline (case-insensitive), and `bar_line_width` equals the fixture's stroke in px at the reference, ± 0.15 px — `TestTheLabelBox::test_scheme_colours[mode-<scheme>]`
- Test [mode]: the box's height over the label's font px equals the fixture's box height over font size ± 5 % (s2color, stcolor, economist, the two-variable probe) — `TestTheLabelBox::test_height_follows_the_text_and_margins`
- Test [mode]: the drawn text (`major_label_overrides` value) equals the hidden Title's text, for a plain label, a TeX label (`$x$`) and an SMCL label (`{bf:x}`), after every text pass; font size, colour and style equal the Title's; economist's is left-aligned (`t == 0`) — `TestTheLabelBox::test_the_label_is_drawn_in_the_box`
- Test [mode]: `by(foreign, total)` boxes all three panels; `subtitle("")` draws no box; `subtitle(, fcolor(red))` keeps the scheme's fill and is named once as today — `TestTheLabelBox::test_which_panels_have_a_box`
- Test [mode]: after a saved `_move` and a served `_served_move`, every box keeps its fill, outline, height and text; with `colorvar(price) by(foreign, clegend(on))` the box's mapper is still `low=0, high=1` with its tick inside, and it is no panel's colour key — `TestTheLabelBox::test_after_a_filter_move`
- Chrome [mode] (`test_by_axes_keys_browser.py`): at 1400 px each box's filled pixels span its panel's frame ± 1 px and end on the frame's top edge, and the label's dark pixels lie inside the box. Under s1color the outline pixels are black on all four sides — `TestInChrome::test_label_box[mode]`

New `test/test_by_axes_keys_browser.py` (headless Chrome; skips without Chrome as `test_by_scales_chrome.py` does): at 1400 px inner axes hidden and title cells shown; at 375 px every panel's axes and titles shown and the cells hidden; back at 1400 px restored; no CSP violation in the console (S04's checker), both modes — `TestInChrome::test_stacking[mode]`; the save button writes `<name>.png` — `TestInChrome::test_save_button`.

`test/test_mode_parity.py`: two `CORPUS` and one `MOVE_CORPUS` case tagged `"WP-30 P1.15c"` (p02 two layers; `colorvar(price) by(foreign, clegend(on))`; p27 dual axis), with the parity profile extended by per-axis `visible`, the cell names and each `dash_by_label_box`'s fill, outline and text.

`test/test_label_sinks.py`: register the title cells' `Title.text`, the overall legend's `LegendItem.label` and the label box's `major_label_overrides` value in `TestTextSinks` (raw, canvas).

### Pinned tests to flip (R9; re-measured, never trusted)

E5's list, classified by 53-01 in `$S/53-flips.txt`; each flip keeps its node and states why, e.g. `Flipped: test/test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows::test_each_by_panel_maps_its_own_rows -- a ColorBar on every panel was wrong because twoway draws none under by() without clegend(on) (q06); each panel's mapping is unchanged`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Option spellings, flags | `TestTheUnitFunctions`; truth BYA-05 | `by_chrome_truth.json` | n/a |
| Outer axes, titles | `TestOuterAxes`, `TestAxisTitlesOnce`; BYA-01, BYA-02 | fixture | yes |
| Legend | `TestOneLegend`, `TestTheChromeIsNotData`; BYA-03 | fixture | yes |
| Colour key | `TestColourKeyUnderBy`; BYA-04 | fixture, `colorvar_qualifier_truth.json` | yes |
| After moves | `TestAfterAFilterMove`; parity MOVE_CORPUS | auto | yes |
| Notes | `TestTheNotes` | — | yes |
| Stacking, CSP, save | `test_by_axes_keys_browser.py`; `TestTheStackHook` | auto | yes |
| Panel label box (ratification row 36) | `TestTheLabelBox`; Chrome `test_label_box`; BYA-06 | `by_chrome_truth.json` label-box probes | yes |
| Scheme keys | `TestTheSchemeKeys`; scheme fidelity tests | `scheme_truth.json` | n/a |
| Sinks, registries, tracking | `test_label_sinks.py`, map, served-name guards (G4), tracking | — | n/a |

**Acceptance criteria.**
- **AC-53.1** (BR-53.1, BR-53.2) `TestOuterAxes` and `TestAxisTitlesOnce` pass for every fixture probe in both modes; BYA-01, BYA-02 PASS.
- **AC-53.2** (BR-53.3) `TestOneLegend` and `TestTheChromeIsNotData` pass; BYA-03 PASS.
- **AC-53.3** (BR-53.4) `TestColourKeyUnderBy` (its guard first) passes; BYA-04 PASS.
- **AC-53.4** (BR-53.5, BR-53.6) the Chrome tests pass in both modes, not skipped, with no CSP violation; `TestAfterAFilterMove` and `TestTheToolbar` pass.
- **AC-53.5** (BR-53.7) `TestTheNotes` passes.
- **AC-53.7** (BR-53.8; ratification row 36) `TestTheLabelBox` passes for all 26 schemes in both modes and after moves. The Chrome `test_label_box` passes, not skipped. BYA-06 PASS.
- **AC-53.6** The 26 scheme files and `scheme_truth.json` come from one extractor run, every earlier property unchanged; flips carry reasons; the full suite reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 53-01 to 53-14 form one commit, made by 53-14 on `wp30-s53` with the subject `Draw by() panels with outer axes, one legend and one colour key, as twoway does (WP-30 P1.15c)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s53`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S53 "$SLOT" "$S" "$S/run_<script>.do"`. Each edit of a CRITICAL symbol is preceded by a warning line in the task log (Risk).

<task type="auto" id="53-01">
  <name>Write the fixture and failing tests</name>
  <files>scripts/extract_by_chrome_truth.do, test/test_by_axes_keys.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-18-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s53`; stop otherwise. Create `scripts/extract_by_chrome_truth.do` as "Stata truth" describes (the label-box probes included) and run it through `$SLOT` with `DASH_REPO="$WT"`; compare it with E4 and E6 probe by probe (a difference stops the section). Create `test/test_by_axes_keys.py` with every stub, `TestTheLabelBox` included (new names fail with AttributeError now; the box tests fail because no panel has a `dash_by_label_box`) and append the three parity cases and the profile fields. Run it with `-n 6 -rf` into `$S/53-new.log`, then run `grep -rln 'by(\|"by"' test/*.py` files with `-n 6` and classify each red pre-existing node in `$S/53-flips.txt` (pin to flip, with its reason). If `test_a_level_has_one_colour` is red, stop and report (TR-53.16). Write `$S/53-P1.15c-failure.txt` (base sha, failing nodes, then guards). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/by_chrome_truth.json')); print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), len(d['probes']) >= 40)"` prints `True True`; `grep -c FAILED "$S/53-new.log"` is at least 12; `grep -c "test_a_level_has_one_colour" "$S/53-P1.15c-failure.txt"` prints 0 (it is a passing guard); `git -C "$WT" diff --name-only -- dash_render.py` prints nothing.]]></verify>
  <done>The by() chrome fixture existed, every regression test was shown failing on the unmodified tree, and the pins to flip were classified.</done>
</task>

<task type="auto" id="53-02">
  <name>Write the Chrome and truth cases</name>
  <files>test/test_by_axes_keys_browser.py, test/test_wp30_truth.cscript, test/test_label_sinks.py</files>
  <action><![CDATA[
    Create `test/test_by_axes_keys_browser.py` from `test/test_by_scales_chrome.py`'s harness (same skip rule, S04's CSP console check) with the tests of "TDD test stubs", `TestInChrome::test_label_box` included. Fill S01's S53 stub of `test/test_wp30_truth.cscript` with BYA-01..BYA-06 (helpers `_s53_*` above the S53 header). Register the new sinks in `test/test_label_sinks.py` (they fail until the cells exist). Run all three on the unmodified shipped files and append the failures to `$S/53-P1.15c-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys_browser.py -q -n0 -p no:cacheprovider -rf` reports failures, not skips (Chrome present, as for test_by_scales_chrome.py); `grep -cE "BYA-0[1-6] FAIL" "$S/run_test_wp30_truth.log"` is at least 5.]]></verify>
  <done>The browser, truth and sink cases were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="53-03">
  <name>Regenerate the schemes with by keys</name>
  <files>scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json, dash-*.scheme</files>
  <action><![CDATA[
    Add TR-53.1's keys (the four label-box keys included, each only if no earlier regeneration writes it) to the extractor's resolvers and one emitted group, then run it once with the arguments its header gives, rewriting the 26 `dash-*.scheme` files and `test/fixtures/scheme_truth.json` (never by hand, R7). Verify with a short `python3 -c` diff of the old and new `scheme_truth.json` that every pre-existing property of every scheme is unchanged, writing the result to `$S/53-scheme-diff.txt`. Staging is 53-14's.
  ]]></action>
  <verify><![CDATA[`grep -c "by_legend_position" "$WT"/dash-*.scheme | grep -c ":1$"` prints 26; `grep -c "by_label_fill" "$WT"/dash-*.scheme | grep -c ":1$"` prints 26; `tail -1 "$S/53-scheme-diff.txt"` reads `0 pre-existing properties changed`; `python3 -m pytest test/test_scheme_fidelity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The 26 scheme files and the scheme fixture carried twoway's by() axis, legend and key settings, every earlier property unchanged.</done>
</task>

<task type="auto" id="53-04">
  <name>Read the by keys and options</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add TR-53.1's `SchemeParser._init_properties` reads (the `by_label_*` properties included) and `_FALLBACK_PROPS` entries; `_DASH_BY_AXES_SPELLINGS` (TR-53.2); `_dash_by_axes_options` (TR-53.3); the silent branch in `_dash_parse_by` (TR-53.4; warn: CRITICAL). Add their map keys under S53's anchor. Run `TestTheSchemeKeys`, the `axes_options` unit test, `test_by_scales.py` and `test_server_facets.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_by_axes_keys.py::TestTheSchemeKeys" test/test_by_scales.py -q -n 6 -p no:cacheprovider` reports 0 failed; `python3 -m pytest test/test_by_axes_keys.py -q -n 6 -p no:cacheprovider -k "axes_options"` reports 0 failed.]]></verify>
  <done>The scheme's by() settings and every i*, edge, legend and clegend spelling were read, and those words were no longer named.</done>
</task>

<task type="auto" id="53-05">
  <name>Draw outer axes and titles once</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_dash_by_axis_flags` (TR-53.5), `_dash_by_outer_axes` (TR-53.6) and `_dash_by_cell` (TR-53.7) after S28's by() helpers, each with a docstring citing E4's probe ids. Run the unit tests for the three and `TestOuterAxes`/`TestAxisTitlesOnce` through direct calls on built panels (the wiring comes in 53-09).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys.py -q -n 6 -p no:cacheprovider -k "axis_flags or outer_axes or by_cell"` reports 0 failed.]]></verify>
  <done>Per-panel axis flags matched twoway's for every fixture grid and the outer axes and title cells could be built.</done>
</task>

<task type="auto" id="53-06">
  <name>Build one legend and colour key</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_dash_by_keys` (TR-53.8) with the clone rule (properties copied with `properties_with_values(include_defaults=False)`, one-row NaN sources over the glyph's own dataspec fields, `_DASH_SWATCH_PREFIX` names) and the ColorBar bound to panel 1's mapper. Run its unit test and `TestTheChromeIsNotData`'s unit half.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys.py -q -n 6 -p no:cacheprovider -k "by_keys"` reports 0 failed.]]></verify>
  <done>One legend cell of panel 1's keys and at most one colour key cell could be built, with clones that are not data.</done>
</task>

<task type="auto" id="53-07">
  <name>Place side cells in the grid</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_dash_by_side` and `_dash_by_side_grid` (TR-53.9), adding `legend_at` to S48's position helper only if it lacks it (with its unit test in the same file's TestTheUnitFunctions). Warn, then edit `_dash_layout_cell` and `_dash_reflow` (both CRITICAL) per TR-53.9. Add the TR-53.12 copy-list lines after `"_dash_reflow",`. Run `test_by_axes_keys.py -k "side or reflow"`, `test_layout_facets.py`, `test_by_scales.py` and the served-name guards.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys.py test/test_layout_facets.py -q -n 6 -p no:cacheprovider -k "side or reflow or facet"` reports only the 53-01 flips still to make as failures (listed in `$S/53-flips.txt`); `python3 -m pytest test/test_statistical_helpers.py test/test_resource_limits.py -q -n 6 -p no:cacheprovider -k "ServedApp"` reports 0 failed.]]></verify>
  <done>Title, legend and key cells sat beside the panels in narrow tracks, framed by S28's head and foot, with panel columns alone deciding the stacking width.</done>
</task>

<task type="auto" id="53-08">
  <name>Draw the panel label box</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Ratification row 36; E6; TR-53.17. Add `_dash_by_label_box` after `_dash_by_side_grid`, with a docstring citing E6's twoway table and the four measured Bokeh routes (why a ColorBar). Call it from `_dash_by_side` for every panel figure, after `_dash_by_keys`, with S48's size multiplier. Give `_dash_by_keys`' colour-key removal the `dash_by_label_box` exception (TR-53.8). Append `"_dash_by_label_box",` to S53's copy-list block (TR-53.12) and its map key (TR-53.13). Re-find, at the base, the canvas-text passes that run after `_dash_by_side` in each mode, and route the box's label through them if any runs later (TR-53.17). Do not edit `_dash_by_panel_label` or any other S28 helper, `_DASH_TEXTBOX_HONOURED`, `_dash_textbox` or `_dash_apply_z_options` (S52's). Run `TestTheLabelBox -k unit` and the Chrome `test_label_box` in saved mode on a direct build; the wiring of both modes is 53-09's.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_by_axes_keys.py::TestTheLabelBox::test_unit" test/test_function_test_map.py -q -n0 -p no:cacheprovider` reports 0 failed; `grep -c '"_dash_by_label_box",' "$WT/dash_render.py"` prints 1.]]></verify>
  <done>Each panel label could be drawn in the scheme's filled and outlined box across the panel's plot region, with the label's own text and style, and the box was neither data nor a colour key.</done>
</task>

<task type="auto" id="53-09">
  <name>Wire the post-pass in both modes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_build_sources_and_figures` is CRITICAL and `_generate_app_source` HIGH. Add TR-53.11's saved call after S28's chrome assignment and the generated served lines after S28's, and let S28's canvas-text pass reach the title cells. Run `TestOuterAxes`, `TestAxisTitlesOnce`, `TestOneLegend`, `TestColourKeyUnderBy`, `TestTheLabelBox`, `TestAfterAFilterMove`, `TestTheNotes`, `TestTheToolbar`, and `test_mode_parity.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "not Stack and not browser"` reports 0 failed apart from nodes `$S/53-flips.txt` lists for 53-11/53-12.]]></verify>
  <done>Both modes drew outer axes, titles once, one legend, at most one colour key and each panel label in its scheme box, before and after filter moves.</done>
</task>

<task type="auto" id="53-10">
  <name>Show axes on stacked panels</name>
  <files>dash_render.py, test/test_by_axes_keys_browser.py</files>
  <action><![CDATA[
    Add `_DASH_BY_STACK_JS`, `_dash_by_stack_hook` and `_dash_by_stack_hooks` (TR-53.10) and their call in `_dash_by_side`; attach the hooks in `DashRenderer.render` (the document wrapper before `components()`) and in the template after `doc.add_root(layout)`. Run `TestTheStackHook` and the Chrome file in both modes; if the saved page shows no callback, stop and report (the measured `components()` behaviour changed).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_by_axes_keys.py::TestTheStackHook" test/test_by_axes_keys_browser.py -q -n0 -p no:cacheprovider -rs` reports 0 failed and 0 skipped.]]></verify>
  <done>Stacked panels showed their axes and titles at phone width and twoway's layout returned when wide, in both modes under the CSP.</done>
</task>

<task type="auto" id="53-11">
  <name>Flip the colour-key and legend pins</name>
  <files>test/test_colorvar_truth.py, test/test_colorvar_forms.py, test/test_help_claims_5.py</files>
  <action><![CDATA[
    Flip, in place and never deleting, the nodes `$S/53-flips.txt` lists in these three files, each with a comment citing its E4 probe and a `Flipped:` line appended to the file; keep each node's twoway-true assertions (each panel's own mapping, etc.). Run the three files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colorvar_truth.py test/test_colorvar_forms.py test/test_help_claims_5.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The colour-key, legend and help-claim pins asserted twoway's by() chrome with their reasons.</done>
</task>

<task type="auto" id="53-12">
  <name>Flip remaining pins and document</name>
  <files>dash.sthlp, test/test_server_facets.py, test/test_help_claims_5.cscript</files>
  <action><![CDATA[
    Make the help edits of TR-53.14 in "Faceting with by()" (re-grep after S28 and S48; R3), and re-derive, from the regenerated 26 files, the directive-count numbers of the help sentence `test_the_directive_count_is_what_the_help_says` reads (the "What the shipped files are" paragraph; R10's count prose, its only S53 edit outside "Faceting with by()"). Flip the remaining listed nodes in these two test files in place with reasons; a listed node in any other file stops the section for a re-plan (one more task), never an unlisted edit. Run `TestTheHelp`, `test_help_conformance.py`, both files (the cscript through the driver) and `test_by_suboptions.cscript`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_by_axes_keys.py::TestTheHelp" test/test_help_conformance.py test/test_server_facets.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -cE "HC5-[0-9]+ FAIL" "$S/run_test_help_claims_5.log"` prints 0.]]></verify>
  <done>The help documented shared axes and keys under by() and every remaining pin carried its reason.</done>
</task>

<task type="auto" id="53-13">
  <name>Flip the shipped-file pins and run the suites</name>
  <files>test/test_help_claims_8.py</files>
  <action><![CDATA[
    Flip in place, never deleting, the two `TestTheShippedFiles` pins of E5: `test_no_directive_for_what_dash_does_not_draw`'s pattern applies outside the `by() axes and keys (WP-30 P1.15c)` group (inside it `margin by_indiv` and the `by_indiv_*ticks` keys are allowed, because S48 and S53 draw them), and `test_the_directive_count_is_what_the_help_says`'s bounds are re-derived from the regenerated files (min and max rounded outward to ten, as S36 did) with `# <old> -> <new>: P1.15c by() keys`; append both `Flipped:` lines to `$S/53-flips.txt`. Then run with `-n 6`: `test_by_axes_keys.py`, `test_by_text.py` (S28's), S48's by() tests, `test_by_scales.py`, `test_layout_facets.py`, `test_server_facets.py`, `test_colorvar_truth.py`, `test_mode_parity.py`, `test_label_sinks.py`, `test_scheme_fidelity.py`, `test_help_claims_8.py`, `test_function_test_map.py`, `test_fixtures_are_committed.py` and the served-name guards (G4); with `-n0`: the two Chrome files. Through the driver: the S53 truth block, `test_by_suboptions.cscript`, `test_help_claims_5.cscript`. Check `~/.stata19/console/stata19.rc` still holds `python_exec`; a SKIP is not a pass.
  ]]></action>
  <verify><![CDATA[Every pytest run, `test/test_help_claims_8.py` among them, reports 0 failed and the Chrome files 0 skipped; `grep -cE "BYA-0[1-6] PASS" "$S/run_test_wp30_truth.log"` prints 6; `python3 -m pytest "test/test_by_axes_keys_browser.py::TestInChrome::test_label_box" -q -n0 -p no:cacheprovider -rs` reports 0 failed and 0 skipped; `grep -c SKIP "$S/run_test_wp30_truth.log"` prints 0.]]></verify>
  <done>Every changed test file, the browser tests and the section's script cases passed in the worktree.</done>
</task>

<task type="auto" id="53-14">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.15c"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution". Delete only the `"P1.15c"` key line. Replace `<!-- WP-30 P1.15c -->` in place with "Notes: CHANGELOG line". Run `test_tracking_documents.py -n0`; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/53-full.log"` in the background, waited for on its `exit=` line, never relaunched (E6). Stage exactly the files 53-01 to 53-14 changed, `git add -f test/fixtures/by_chrome_truth.json test/fixtures/scheme_truth.json`; check the staged names (G6). Write `$S/53-message.txt`, check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/53-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.15c -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.15c": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.15c)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.15c was closed naming existing tests, its marker carried the old and new by() chrome, and one green commit on wp30-s53 was ready for the merger to land last.</done>
</task>

## Section completion criteria

- Under by(), both modes draw twoway's outer axes, edge labels and individual axes for every fixture grid, the axis titles once and no axis-2 title, before and after moves.
- One legend (panel 1's keys) where and when twoway draws it; per-panel legends only with `ilegends`; none of the clones is data.
- No colour key per panel; one key from panel 1's mapping under `by(, clegend(on))`, following panel 1 after a move.
- (ratification row 36) Each panel label sits in twoway's filled box from the scheme, spanning the panel's plot region, in both modes and after moves, for all 26 schemes.
- Stacked panels show their axes at phone width in both modes under the CSP; the grid keeps one save tool.
- The by() words this section draws are no longer named; the forms twoway ignores are silent.
- The 26 scheme files and `scheme_truth.json` carry the by() keys from one extractor run; `by_chrome_truth.json` is generated, stamped and committed with `-f`.
- One green commit `(WP-30 P1.15c)` on `wp30-s53` closes the entry, deletes its key and replaces its marker.

## Notes

- **S48's names.** S48's TR-48.8 defines `_dash_by_positions(n_panels, opts, legend_at=0, clegend_at=0, limit=None) -> (cells, nrows, ncols, extra)` and `_dash_by_grid_options(by_raw)` (with `compact` and `style`); they are re-read at `batch-18-base`, and if they differ, S53 uses S48's and adapts `_dash_by_axis_flags`' input in one place.
- **S28's Q-28.1: ratified 06oct2026 (row 36), CHANGED to "Add to S53".** This supersedes the orchestrator's earlier out-of-scope ruling. S53 draws the box (TR-53.17) without editing `_dash_by_panel_label`. It reads S28's `dash_by_label` Title, draws the label in a `ColorBar` box, and hides the Title (E6 says why). The scheme keys come from this section's regeneration (TR-53.1). The left inset under economist is not drawn, and a right-justified label is drawn only after its Chrome check.
- **Document wrapper.** The saved path's `Document` exists only when a stack hook does; a page without by() grids is serialised exactly as before (TestTheStackHook asserts no `document_ready` on a plain page).
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor and the truth block then fail or SKIP. Check after each slot run.
- **Merge rules for the shared files.**
  - R1: S53's own truth block only; no area cscript gains cases (S48 owns by() refusals in `test_by_suboptions.cscript`); HC5 flips edit only their named cases.
  - R2: the copy-list block after `"_dash_reflow",`; map keys under S53's anchor.
  - R3: "Faceting with by()" only, after S28 and S48.
  - R4/R5: the one `P1.15c` marker, entry and key.
  - R7: the scheme regeneration by 53-03's single extractor run; on a conflict the merger re-runs the extractor on the merged tree (S53 lands last, so none is expected); `by_chrome_truth.json` from S53's own extractor.
  - R8: three corpus cases and two profile fields; `ALLOWED`/`_MUST_WARN` untouched. R9: `$S/53-flips.txt`. R10: the directive-count pin and the help numbers it reads (53-12, 53-13). R12: S53 is batch 18's editor of `_generate_app_source` and `_build_sources_and_figures`; it does not edit `_make_figure_body`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name the ten new functions, `_dash_parse_by`, `_dash_layout_cell`, `_dash_reflow`, `DashRenderer._build_sources_and_figures`, `DashRenderer.render`, `ServerAppBuilder._generate_app_source`, `ServerAppBuilder._glyph_layer_lines`, `SchemeParser._init_properties` and the extractor's symbols, plus test symbols.
- **Commit message.** Subject as in "Commit boundary". Body: `$S/53-P1.15c-failure.txt`; the measured defect (Overview's block); what changed and where (TR-53.1-TR-53.14, both modes, the stacked view and how it is attached); then `Regression: test/test_by_axes_keys.py::<Class>::<test> -- failed at <base sha> with <text>` per node (and `test/test_by_axes_keys_browser.py::TestInChrome::test_stacking`, `test/test_wp30_truth.cscript BYA-01`); the `Flipped:` lines of `$S/53-flips.txt`; `Fixture: test/fixtures/by_chrome_truth.json (scripts/extract_by_chrome_truth.do)`, `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`; `BUGS.md: "<WP30_OPEN["P1.15c"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.15c). Under by() each panel draws only the axes twoway's outer-axes rule draws (y on the left of each row, x at the bottom of each column, edge labels unless noedgelabel or compact, the second y axis on the rightmost panel), the i*/noi* options, individual and rescaled axes turn individual axes, labels, ticks and titles on as in twoway, the axis titles are drawn once beside and below the panels and no axis-2 title per panel, one legend cloned from panel 1's keys is placed by by(, legend(position() at())) or the scheme's by_legend_position (ilegends for per-panel legends), and one colour key from panel 1's mapping only under by(, clegend(on)); each panel label is drawn in the scheme's filled and outlined box across the panel's plot region (_dash_by_label_box); stacked phone-width panels show their axes again; in _dash_by_axes_options, _dash_by_axis_flags, _dash_by_outer_axes, _dash_by_keys, _dash_by_label_box, _dash_by_side, _dash_by_side_grid, _dash_layout_cell, _dash_reflow and the stack hook, with the by_* scheme keys in the 26 scheme files, in the saved page and the served app and after filter moves. Pinned by test/test_by_axes_keys.py::TestOuterAxes::test_probe, test/test_by_axes_keys.py::TestAxisTitlesOnce::test_probe, test/test_by_axes_keys.py::TestOneLegend::test_probe, test/test_by_axes_keys.py::TestColourKeyUnderBy::test_key, test/test_by_axes_keys.py::TestTheLabelBox::test_scheme_colours, test/test_by_axes_keys_browser.py::TestInChrome::test_stacking, test/test_by_axes_keys_browser.py::TestInChrome::test_label_box, test/test_wp30_truth.cscript BYA-01; fixture test/fixtures/by_chrome_truth.json. Residual, deferred (WP-30): by(, graphregion() plotregion()) stay named (IR-9); legend(ring(0)) is drawn beside the panels and named; the overall legend is not clickable; subtitle(, fcolor() lcolor() nobox) do not restyle the panel box and stay named.
  ```
- **CHANGELOG line** (replaces the marker in place, in the WP-30 group of Results that change):

  ```
  - by() panels share their axes and keys as twoway's do: `dash scatter mpg weight || lfit mpg weight, by(foreign)` drew both axes, both axis titles and a legend on every panel, and now draws the y axis on the left panel, the x axis under each column, each axis title once and one legend for the array (placed by `by(, legend())` or the scheme), with `iyaxes`, `ixaxes`, `noedgelabel`, `ilegends` and the other by() axis options honoured instead of named; a second y axis and its title are no longer repeated on every panel; `colorvar()` under by() draws no colour key unless `by(, clegend(on))`, which draws one from the first panel; each panel's label is drawn in the scheme's shaded box across the top of the panel, as twoway draws it (s2color bluish gray; it was plain text); on a phone-width screen stacked panels keep their axes. (WP-30, P1.15c)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B16:** with S28 (b), S48 (a, e) and S53 (c, d) landed, B16 is `Closed in WP-30` naming the three entries and commits; **B26-d** and **B31-c** closed by `<sha>` (B31 with S28's parts).
  - **TWOWAY_COVERAGE_AUDIT.md:143** (AUDIT-71, AUDIT-72): tagged closed by `<sha>`.
  - **DROPIN-REMAINING.md:105-112 (P1.15):** "Closed by <S28 sha>, <S48 sha>, <sha> (WP-30 S28, S48, S53)"; the WP-29 axis-2-title and clegend notes closed by `<sha>`.
  - **New P2 rows:** `by(, legend(ring(0)))` inside the array (drawn beside it); a clickable overall by() legend; by()'s alternate axes (`by_alternate_*`). There is no row for the panel label's filled box: S53 draws it (ratification row 36). A row for `subtitle(, fcolor() lcolor() nobox)` restyling it is the orchestrator's call (Notes for the orchestrator).
  - **AGENTS.md invariant:** "by() chrome cells are bare `Plot`s named `dash_by_*`; legend and key clones carry `_DASH_SWATCH_PREFIX` names and live only in those cells; the stacked view is the one `dash_by_stack` CustomJS per grid; a by() panel's label is drawn by the `ColorBar` named `dash_by_label_box`, and S28's `dash_by_label` Title stays hidden as its text record."
  - **Unverified:** twoway's by() rules on Stata 14-18.5 (not run, M2); schemes beyond stcolor, s2color and economist are read from their files, not drawn by twoway here.

### Notes for the orchestrator (ratification 06oct2026)

- **index.md** (not edited here):
  - 18.0's expected list is unchanged by the box. `_dash_by_label_box` is new, and `_dash_by_side`/`_dash_by_keys` are S53's own new functions.
  - R2's S53 row gains `"_dash_by_label_box",` in S53's block after `"_dash_reflow",`.
  - The section table's task count for S53 is now 14. Its complexity L stands.
- **section-28:** no change needed beyond what it already says (D-28e and Q-28.1 point to S53). S53 hides, not removes, the `dash_by_label` Title, so S28's `panel_label(fig)` probe and its Title tests keep reading text, size and colour. A test of S28's that asserts the Title is *visible* is a 53-01 flip, with the reason "the label is drawn by `dash_by_label_box` (ratification row 36)".
- **section-58:** "files no P2 row for the box" holds. Decide whether to file one P2 row for `subtitle(, fcolor() lcolor() bcolor() box nobox)` restyling the panel box: twoway honours them (E6), and dash names them through `_DASH_TEXTBOX_HONOURED`, which no WP-30 section widens for subtitle.
- **Batch 18:** no partner conflict (Review amendments). S52's `_dash_apply_z_options` creates the colour-key ColorBars, and S53's `_dash_by_keys` removes them by type. The `dash_by_label_box` exception keeps the two apart.
