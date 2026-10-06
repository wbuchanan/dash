# Section 48: by() grid and size (P1.15 part b)

> Part of: WP-30 · Items: P1.15b (entry `P1.15b`; GAPS2-B16-a, GAPS2-B16-e, REM-10-03, the WP-29 S10 `YRESCALE`/two-`style()` note) · Risk: yellow · Batch: 17 (merge order S48, S49, S50) · Depends on: 08, 28 · Blocks: 53, 56 · Tasks: 13, 1 commit · Case prefix: BYG

## Review amendments

- Fixed (major, Q-48.1 ruling): an unknown by() word is now refused in twoway's words and typed order with the capitals and repeats (TR-48.2, TR-48.4 step 5, BR-48.5, BYG-17, the CHANGELOG line and the Resolution); the residual and the open question are replaced by the ruling (Notes).
- Fixed (major, rule M5): refusing unknown words needs twoway's whole by() grammar, or valid twoway input (`graphregion()`, `t1title()`, `spacers()`, `bgcolor()`) would be refused. D-48g and TR-48.1 now transcribe stage 3 from bygraph_g.class:224-233 and graph_g.class:282-301/:340-345 (read at HEAD), not from S28's text table; `repeat_ok` follows new repeat probes; new `accepted` and `declared` fixture records, `TestTheGrammar::test_every_spelling_is_twoways` and BYG-18 prove nothing twoway accepts is refused.
- Fixed (minor): E6's model names the stage-3 readers and the final `FAKE_OPT_FOR_BETTER_MSG` check.
- Fixed (minor): a negative `imargin()` side had a note with no emitter; dash.ado's `_dash_by_check` prints it once (TR-48.4 step 7, `_byg_imargin_neg`), the renderer prints none.
- Fixed (minor): the size post-pass also scales Arrow heads (`ArrowHead` `size`, `line_width`), which a pc arrow layer draws in a panel.
- Fixed (minor): 48-01, 48-02 and 48-04 verifies, AC-48.4, the test plan and R1 name BYG-01..BYG-18.
- Kept (Q-48.2, ruling): the `iscale()` bound of 10,000, marked "Maintainer question (ratify)" with a recommendation.
- Checked at HEAD: `_dash_parse_by` (19941, `.lower()` at 19988), `_DASH_BY_SUPPORTED` 19856, `_DASH_BY_RESCALE_KEYS` 19872, `_dash_by_rescale` 20025, `_dash_reflow` 24465, `_dash_facet_cols` 24959, `_dash_layout_cell` 25001 (:25015-25020 quoted), `_ar_of` 25163, `apply_to_figure` 7376, copy-list `"_dash_by_rescale",` 33200, dash.ado byvarlist branch 2334-2423, `_dash_by_parts` end 3274, the by() rule loop 5345-5354, Mata `_dash_rep_value` 4546.
- Checked (batch 17): S48 shares no function with S49 (`_make_figure_body`, `_generate_app_source`, axis helpers, `_dash_process_segment`) or S50 (`SchemeParser._init_properties`, `_FALLBACK_PROPS`, refline functions, finishers); shared lines (`_needed`, the Mata header index, CORPUS) conflict in context only (Notes).
- Cross-file (notes file): index 17.0's expected list names `_dash_by_groups`, which S48 reads only, and omits `_dash_layout_cell` (CRITICAL); S53's TR-53.1 must add `margin by_indiv` to the scheme files (D-48e).
- The review pass applied both lenses.

**Binding readings applied in this file** (M1, M5, M6; register P1.15.1, P1.15.2, P1.15.4, P1.15.6; index A148, A149, A152, A153, A155, R1-R12, IR-17):
- **P1.15.1 (M1).** `xsize()`/`ysize()` size the whole by() array, not each panel.
- **P1.15.2 (M1, after P1.12).** twoway's default by() size multiplier and an explicit `iscale()` act on panel sizes in S08's Stata units.
- **P1.15.4 (M5) and the orchestrator's ruling on Q-48.1.** Refused in twoway's words and codes: `rows()` with `cols()` (r(198)); out-of-range or malformed `rows()`, `cols()`, `holes()` (r(121)/r(123)/r(125)/r(126), as twoway's own `syntax` reports them); a capitalised spelling of a by() sub-option, a repeated grid or style sub-option and an unknown by() word (r(198) `option X not allowed`). Measured order is reproduced (E6): every leftover of twoway's last stage is refused in typed order, whatever kind it is.
- **P1.15.6 / A54 (ratification item 9, pending).** `cols()` beyond the panel count is honoured up to the by_groups limit (default 100, ceiling 1,000); beyond it, clamped with one note. D-48c extends the same rule to `rows()`.
- **M6.** Nothing is printed where twoway prints nothing: honoured sub-options are no longer named; `rows()`, `holes()` and `iscale()` given empty are silent, as in twoway.
- **A152 / R11.** S48 regenerates no scheme file and edits no axis finisher (S50 is batch 17's regenerator and finisher editor).
- **R12.** S48 edits none of `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets` or an applier: every served hook is in a function the template already calls (`_dash_layout_cell`, `_dash_parse_by`, `SchemeParser.apply_to_figure`, `_dash_auto_bs_layout`).

**Section decisions.**
- **D-48a. Where the refusals run.** In dash.ado's `byvarlist` branch of `_dash_validate_value`, through a new program `_dash_by_check` and two Mata functions. Number checks run Stata's own `syntax` declarations, copied from `bygraph_g.class` (`Rows(numlist integer >0 min=0 max=1)`, `Cols(…)`, `HOLes(numlist integer >0 max=300)`), on argument text that first passes a strict numlist character set, so twoway's exact words come out and no user text is ever expanded.
- **D-48b. Where the grid is laid out.** `_dash_layout_cell` (both modes, unchanged signature) places panels by `_dash_by_positions`, a line-for-line port of `bygraph_g.class` `full_n`/`set_rows_cols`/`set_placement`, on the `gridplot()` S28 already re-positions (so the merged toolbar and `_dash_name_save` keep working), sets the spacing, scales each panel and sets each panel's aspect.
- **D-48c. `rows()` beyond the panels** is bounded exactly as `cols()` (A54's reason: an empty row is a layout track; rule 1).
- **D-48d. `iscale()` bounds.** twoway refuses a negative multiplier and one so large that a panel line width passes 10,000 (`gm_linewidth must be between 0.000 and  1.0e+04`, r(198), at draw time; measured: `iscale(1e4)` rc 0, `iscale(1e5)` r(198)). dash refuses `iscale(#)` and `iscale(*#)` when # < 0 or # > 10,000, in those words. The band 10,000 < m ≤ twoway's scheme-dependent bound is a documented over-refusal (Q-48.2, a maintainer question to ratify; Notes).
- **D-48g. The accepted-word set is twoway's whole by() grammar.** Because an unknown word is now refused (Q-48.1), `_DASH_BY_GRAMMAR` must hold every word twoway's by() accepts, or dash would refuse valid twoway input. It is transcribed from the four places bygraph_g.class reads the by() options (parse_make :74-81, parse_settings :266-285, the region, title, spacer and bgcolor parsers its parse_make calls at :224-233, and graph_g.class parse_and_log_titles :282-301 and parse_and_log_spacers :340-345), and every row's minimum spelling is confirmed accepted by the fixture's `accepted` probes (`TestTheGrammar::test_every_spelling_is_twoways`, BYG-18).
- **D-48e. The default panel margin** is the scheme's `margin by_indiv` (s2color `small`, stcolor/stmono1/stmono2 `allsides-ms`, economist `medium`). No shipped dash scheme file carries the key and S50 is batch 17's only regenerator (A152), so S48 reads `_props["margin by_indiv"]` when present and otherwise a table transcribed by its extractor from Stata's 26 scheme chains, keyed by `SchemeParser.name`. S53 (batch 18) adds the key to the extractor with its `by_*` keys; the table then only backs a missing key.
- **D-48f. Size scaling is a post-pass.** `_dash_by_scale_panel(fig, m)` multiplies every numeric size a panel draws (markers, line widths, text, tick lengths, label offsets, reference-line widths) once, after the panel is built, so no mapper or applier changes and both modes share one function. Field-valued sizes (per-row `mlabvposition` offsets) are left as they are and named as a residual.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:105-112 (P1.15) lists `rows`, `holes`, `colfirst` and `compact` as "named and ignored" and says faceted graphs "miss the automatic layout" (REM-10-03). WP-29 S10 adds: `YRESCALE` and two `style()` are accepted where twoway refuses them. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-15.md` §1, probe C):

```
by(foreign, total rows(1) holes(1) colfirst … compact iscale(.5) imargin(zero) …)
  both modes draw Domestic, Foreign, Total in the default grid and warn
  "dash: by() sub-option(s) not implemented and ignored: rows(1) holes(1) colfirst … compact iscale(.5) imargin(zero) …"
by(foreign, total cols(2) rows(2))   rc 0, note names rows(2) only     (twoway: r(198) may not specify both rows() and cols())
by(foreign, cols(0))                 rc 0, silent, automatic columns    (twoway: r(125) cols() invalid -- invalid number, outside of allowed range)
by(foreign, holes(0))                rc 0, noted                        (twoway: r(125) holes() invalid -- invalid numlist has elements outside of allowed range)
by(foreign, YRESCALE)                rc 0, silent, read as yrescale     (twoway: r(198) option YRESCALE not allowed)
by(foreign, style(compact) style(default))  rc 0, noted                 (twoway: r(198) option style() not allowed)
layout(bs), graph wide xsize(12) ysize(3) by(foreign): saved [[('wide', 6), ('sq1', 6)], [('sq2', 6)]]  (no by(): wide gets 12)
```

Every panel is drawn at the plain graph's text, marker and line size; twoway draws them at 0.85 of it for 2-4 panels and 0.6 for 10-16 (E5). Each panel takes the whole `xsize()/ysize()` ratio, where twoway sizes the whole array by it (research s01: both 8640x2160).

**After this section**, in the saved page and the served app (the layout is built once per page or session; filter moves never re-lay it out):
- `rows()`, `cols()`, `holes()` and `colfirst` place the panels in twoway's cells, holes and empty columns or rows included, with S28's head and foot cells around them;
- `compact`, `style(compact)` and `imargin()` set the space between panels in Stata units (s2color: 2.4 units between columns; `compact`: 0);
- panel text, markers, lines and ticks take twoway's by() multiplier, `iscale(#)` or `iscale(*#)`; overall text (S28's cells) does not;
- the array, not each panel, has the graph's `xsize()`/`ysize()` ratio, and `layout(bs)` sees a faceted graph's ratio;
- by() argument errors are refused in twoway's order, codes and words; honoured sub-options are no longer named.

**Why one section.** These are P1.15's grid and size parts (research §7 split 2; A138): one placement port, one spacing and size rule and one refusal program, all landing in `_dash_layout_cell` and dash.ado's `byvarlist` branch. The shared axes, legends and the compact edge-label effect are S53's; the text is S28's.

**Test order and commit rule (rule 7).** One cycle on `wp30-s48`: 48-01 and 48-02 write the fixture and every regression test and run them against the unmodified batch-17 base, saving `$S/48-P1.15b-failure.txt` (no commit); 48-03 to 48-12 fix, flip and document; 48-13 closes the entry and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — three CRITICAL layout symbols, a Stata-side parser that must speak twoway's words in twoway's order, and a size change on every by() dashboard

**Why.**
- `_dash_parse_by` CRITICAL (32 impacted, 9 direct, 16 processes); `_dash_layout_cell` CRITICAL (10 impacted, 3 direct, 8 processes); `_dash_reflow` CRITICAL (12 impacted, 4 direct) (research §5; re-run this pass: 32/10/12).
- `_dash_by_groups` CRITICAL (8): read only; the grid needs no grouping change (the manifest's warning is honoured by not editing it).
- `SchemeParser.apply_to_figure` LOW (3), `_dash_auto_bs_layout` LOW (3) (this pass).
- `ServerAppBuilder._glyph_layer_lines` HIGH (4): append at S48's anchor only.
- dash.ado `_dash_validate_value` and every Mata function: UNKNOWN (not indexed). `_dash_validate_value`'s by() call sites by grep: dash.ado:5345-5354 (the by() rule loop) and the segment rule loop (:5357-5366 skips by).

**Risk factors.**
1. Stata's own `syntax` sees only what dash puts on its line; user text holding a backtick, `$` or a quote must never reach a command line.
2. twoway's error order mixes three stages (E6); a wrong order turns a pasted do-file's error into a different one.
3. The post-pass could double-scale a panel laid out twice (tabs and grid) or miss a size kind.
4. Empty columns and rows need explicit tracks: a CSS grid's implicit tracks would collapse them.
5. `_dash_limit` is rclass and clobbers `r()`.
6. The copy loop skips a misspelt name silently (RK-9).

**Mitigation.**
1. `_dash_by_scan` reads the tail from a string scalar; only argument text matching `^[0-9 .eE+\-/(),:\[\]to]*$` is put on a `syntax` line; anything else is refused with twoway's non-numeric words (E6) without reaching Stata's parser. Every message goes out through `_dash_say`.
2. `_dash_by_check` follows E6's measured stages; BYG-01..BYG-18 compare rc and first error line with live twoway, including the order probes and the accepted words.
3. A `_dash_by_scaled` stamp makes the pass idempotent; `TestTheSizes::test_every_numeric_size_is_scaled` walks every property of every model of five panel types.
4. `grid.cols`/`grid.rows` are set to explicit track lists; an empty row gets one `Spacer` (E4 measured that GridPlot takes a track list).
5. `_dash_by_check` calls `_dash_limit` last, after every refusal; nothing after it in the `byvarlist` branch reads `r()` (checked in 48-04).
6. G4 guards in 48-08.

## Dependencies

- **Depends on: 08, 28.**
  - S08 (batch 3): `OptionTranslator.resolve_size`, `PT_PER_RS` (one Stata unit is 2.88 pt at dash's 4-inch reference) and `PX_PER_PT`; the panel sizes S48 multiplies are S08's.
  - S28 (batch 10): `_dash_by_frame_grid(grid, chrome, ncols)` (called after placement), `_dash_by_panel_label` (the label `Title` S48 scales), `_DASH_BY_TEXT_SPELLINGS` (the text keys in S48's grammar table), and S28's note that it re-positions `gridplot()`'s children.
  - Read, not depended on: S21's `_DASH_BY_GMETRIC = (3.0, 0.3, 1.0)` and its f(G) formula; S47's marginstyle reader for `imargin()` (D-48e); S10's sub-option table conventions; S06's note form; S01's entry, key, markers, stub `* ==== S48 P1.15b: by() grid and size ====` and anchors `# WP-30 S48 (P1.15b): by() grid and size (P1.15 part b)`.
- **Blocks: 53, 56.** S53 places the one legend in `legend(at(#))`'s hole through `_dash_by_positions(..., legend_at=)`, applies `compact`'s edge-label effect and adds `margin by_indiv` to the scheme files; S56 scales `text()` on panels with the same multiplier (`_dash_by_size_mult`).
- **Parallel batch: 17**, merge order S48, S49, S50.
- **Can run with:** S49 (edits `_make_figure_body`, `_generate_app_source`, the axis-variable and title helpers, dash.ado's plot validation) and S50 (the reference-line functions, `SchemeParser._init_properties`, `_FALLBACK_PROPS`, the finishers, the extractor and the 26 scheme files). None of S48's functions is theirs; S48 adds a SchemeParser method and one line to `apply_to_figure`, which neither partner edits.

## Evidence

Anchors at `c96facd` (dash_render.py 37,689 lines, dash.ado 8,487, dash_parse.mata 6,093, dash.sthlp 3,822). Batches 1-16 move many; re-find each by symbol at `batch-17-base`.

### E1. The parser names everything but cols/total/missing/rescale (dash_render.py `_dash_parse_by`, 19941-20022)

```python
19987    for tok in _dash_by_tokens(subopts.strip()):
19988        name = tok.split("(", 1)[0].strip().lower()
...
20004        elif name == "style" and arg.strip() in ("rescale", "combine"):
...
20012        else:
20013            unsupported.append(tok)
```
`_DASH_BY_SUPPORTED` (19856) holds cols, missing, total and the six rescale words; `.lower()` makes `YRESCALE` and `TOTAL` honoured. S28 adds a text-key branch before `style` (TR-28.3).

### E2. The grid is ceil(sqrt(n)) columns, row-major, clamped to the panels (`_dash_facet_cols` 24959, `_dash_layout_cell` 25001)

```python
24975    if n <= 0:
24976        n = min(n_panels, max(1, math.ceil(math.sqrt(n_panels))))
24977    return max(1, min(n, n_panels))
...
25015        cn = _dash_facet_cols(gopts_of(name) or {}, len(figs))
25016        rows = [figs[i:i + cn] for i in range(0, len(figs), cn)]
25019        return _dash_name_save(_dash_reflow(gridplot(rows, sizing_mode="stretch_width")))
```
Its four call sites (saved 30959, 31213, 32491; served 36250) pass `(name, figures, facet_map, kpi_divs, gopts_of)`. S28 frames the grid in this function (TR-28.7) and keeps the signature.

### E3. layout(bs) reads a faceted graph's ratio as 0 (`_dash_auto_bs_layout._ar_of`, 25163)

```python
        def _ar_of(nm):
            _f = (figures or {}).get(nm)
            _a = getattr(_f, "aspect_ratio", None) if _f else None
            return float(_a) if _a else 0.0
```
Panels are keyed `name__by__<k>` (dash_render.py:31541, :35623), so `figures.get("wide")` is None (REM-10-03).

### E4. `_dash_reflow` (24465) and the track list

`_dash_reflow` sets `grid.cols = _DASH_BS_TRACK` (`"minmax(0, 1fr)"`, :195) and a container query at `ncols × _DASH_MIN_COLUMN_PX` (240, :199), `ncols` taken from the children's highest column. Measured this pass under bokeh 3.9.0: `GridPlot.children = [(f0,0,0),(f1,0,1)]` with `cols = ['minmax(0, 1fr)']*5` serialises (`file_html` 10,991 bytes), so five tracks exist with two children. `GridPlot.spacing` defaults to 0 and takes an int or a (row, col) pair.

### E5. twoway truth (StataNow 19.5; research p1-15 §2 and this pass's `p48*.do`, SVGs read by a scratch reader)

Placement (bygraph_g.class:794-908, read as text): `full_n = n + words(holes) + (legend_hole>0) + (clegend_hole>0)`; `cols(#)` sets `rows = 1 + int((full_n−1)/cols)`, `rows(#)` the reverse, else `cols = int(sqrt(full_n)) + (frac > .01)`; cells filled from the top-left, row-major (`colfirst`: down the columns), a hole's index skipped. Research probes p07 (rows(1): 1x3), p08 (holes(3): 2x2, Total at (2,2)), p09 (colfirst), p40 (holes(1 2 3): 2x3), p28 (cols(5) with 2 panels: 1x5), p35 (holes(9): rc 0).

Sizes, s2color, two panels (`b_1`/`b_2` SVGs, 3960x2880 both): marker radius 22.03 → 18.69, label font 79.94 → 67.94, tick labels 99.99 → 85.02, strokes 8.64 → 7.34 and 5.76 → 4.90 (all ×0.85); the overall note stays 99.99. Ten panels (`by(g10)`): ×0.60 (48.02/79.94). `iscale(.5)` ×0.50; `iscale(*2)` ×1.70; `iscale(0)` every panel size 0; `iscale(abc)` ×0.85 with two notes. The space between columns (SVG units, min(W,H) = 2880): default 69.12 = 2.4 units (`margin by_indiv small`, 1.2 a side); `compact` 0; `imargin(large)` 460.8 = 16 units; with `iscale(.5)` still 69.1 (the space is not scaled). Whole array: `scatter mpg weight, by(foreign) xsize(12) ysize(3)` exports 8640x2160, as without by().

### E6. twoway's refusals and their order (this pass, `p48.do`, `p48c.do`, `p48d.do`; `bygraph_g.class` parse_make :73-90 and parse_settings :266-285)

```
rows(0) cols(0)                     r(125) rows() invalid -- invalid number, outside of allowed range
cols(0) rows(2)                     r(125) cols() invalid -- invalid number, outside of allowed range
rows(1.5) / rows(2 3) / rows(abc)   r(126) …noninteger value / r(123) …single number required / r(121) rows() invalid -- invalid number
rows(2) cols(2) YRESCALE            r(198) may not specify both rows() and cols()
rows(1) cols(1) holes(0)            r(198) may not specify both rows() and cols()
YRESCALE holes(0)                   r(125) holes() invalid -- invalid numlist has elements outside of allowed range
holes(1.5) / holes(abc) / holes(1/301)   r(126) …noninteger elements / r(121) holes() invalid -- invalid numlist / r(123) …too many elements
rows(2) rows(3)                     r(198) option rows() not allowed        rows(0) rows(2): r(125) (the first copy is checked)
cols(2) cols(0)                     r(198) option cols() not allowed        (the second copy is never range-checked)
colfirst colfirst rows(0)           r(125) rows() …                          (a repeat is reported after every number check)
holes(1) holes(2) style(compact) style(default)   r(198) option holes() not allowed (the first leftover in typed order)
style(compact) style(default) YRESCALE            r(198) option style() not allowed
TITLE("x") bogus                    r(198) option TITLE() not allowed;  bogus TITLE("x"): option bogus not allowed
COMPACT / Rows(2) / total TOTAL     r(198) option COMPACT not allowed / option Rows() not allowed / option TOTAL not allowed
compact compact / iscale(.5) iscale(2) / imargin(small) imargin(large) / yrescale yrescale / colfirst colfirst   r(198) option <name>[()] not allowed
iscale(-1) / iscale(*-1) / iscale(1e5)   r(198) gm_linewidth must be between 0.000 and  1.0e+04   (at draw; iscale(-1) rows(0) gives rows() first, iscale(-1) YRESCALE gives YRESCALE first)
iscale(1e4), iscale(0), iscale(100)      rc 0
iscale(abc) / iscale(.) / iscale(1 2)    rc 0, (note:  named style abc not found in class numstyle, default attributes used) and a second note naming "1"
imargin(bogus)                           rc 0, (note:  named style bogus not found in class margin, default attributes used)
rows() / holes() / iscale() / holes(301) / r(2) / c(1) colf / hol(2 2 9) / imargin(-1) / imargin(1 2 3 4) / imargin(l=5)   rc 0
```
The model: `syntax` takes the first copy of each declared option and checks its number in declaration order (rows, then cols); the rows/cols conflict follows; parse_settings checks `holes()`; graphregion(), plotregion(), the twelve titles (title, subtitle, note, caption, t1title, t2title, b1title, b2title, l1title, l2title, r1title, r2title), spacers() and bgcolor() are then read (bygraph_g.class:224-229; the title and region readers loop, so their copies repeat); every leftover (a second copy, a capitalised or unknown word) is refused at the end in typed order by `syntax [, FAKE_OPT_FOR_BETTER_MSG]` (:232-233); the `iscale()` bound is a draw-time error, after all of these.

### E7. Tests that pin today's behaviour (flip in place; re-measured by 48-09/48-10)

- `test/test_resource_limits.py::TestByColsCannotOutgrowThePanels::test_the_columns_are_at_most_the_panels` (:1058-1070; `cols(5)` of 4 panels → 4): becomes the D-48c rule on `_dash_by_positions` (cols 5 kept; 10^12 clamped to the ceiling). Its build-time and padding guards (:1072-) stay.
- `test/test_server_facets.py::TestAnUnimplementedBySuboptionIsNamed` (:491-570): rows(2), compact, holes(1 3) iscale(*.8), colfirst rows move to a still-unimplemented sub-option (`subtitleformat()`, `shrink`); as S28 left it.
- `test/test_by_scales.py::TestTheRescaleSubOptions::test_rescale_tokens_are_not_named` (`r(1)` is `rows(1)`, no longer named; `rows(2) yrescale` names nothing) and `::test_style_rescale_is_named_with_its_own_note` (`style(compact)` no longer named).
- `test/test_help_claims_5.py` :768-842 (rows/holes/compact named) and `test/test_help_claims_5.cscript` HC5-08 (:432-462).
- `test/test_mode_parity.py` :1576 and :1915 (`rows(2) compact` expected note).
- `test/test_by_suboptions.cscript` BYS-02..BYS-04, BYS-06 (rows/compact/holes as the unimplemented examples).
- `test/test_layout_facets.py` and `test/test_by_scales.py` aspect pins (grep `aspect_ratio` at the base).

## User stories

- **US-48.1** As a twoway user, I want `by(rep78, rows(2) holes(3) colfirst)` to place my panels in the cells twoway uses, so a pasted do-file lays out as in my Stata report, in the saved page and the served app.
- **US-48.2** As a twoway user, I want panel text and markers drawn at twoway's by() size and at `iscale()`, and `compact`/`imargin()` spacing, so a grid of ten panels reads as twoway's does.
- **US-48.3** As a dashboard publisher, I want `xsize(12) ysize(3)` to shape the whole faceted graph and `layout(bs)` to give it a full row, so wide facet strips are wide.
- **US-48.4** As a twoway user, I want a bad by() argument refused with twoway's words, so an error in a do-file is the error Stata gives.
- **US-48.5** As a dashboard publisher, I want an absurd `cols()` or `rows()` bounded with a note, so a typo cannot exhaust the page.

## Business requirements

- **BR-48.1** Panels occupy twoway's cells for any combination of `rows()`, `cols()`, `holes()`, `colfirst` and `total`, including holes beyond the panels (which still count in `full_n`) and empty trailing columns or rows; spellings `r(#)`, `c(#)`, `colf`, `hol()` as twoway's.
- **BR-48.2** Every panel size (markers, marker labels and their gaps, tick and axis-title text, the panel label, line widths, tick lengths, reference lines) is the plain graph's times m: f(k) with k = ceil(sqrt(full_n)) (1, .85, .8, .6, .48, .4, 2.4/k) by default, `#` for `iscale(#)`, f(k)×# for `iscale(*#)`; S28's overall title, subtitle, note and caption are not scaled.
- **BR-48.3** The space between panels is the panels' adjacent margins in Stata units (1% of min(W,H) each): the scheme's `margin by_indiv`, zero under `compact` or `style(compact)`, `imargin()` when given (any marginstyle name, `# # # #`, or `l=`/`r=`/`b=`/`t=`); not scaled by m; a negative `imargin()` side (twoway: rc 0, no note, panels overlap) is drawn as 0 with one note printed by dash.ado (TR-48.4 step 7), since dash draws it differently.
- **BR-48.4** Without `aspectratio()`, the array of R rows and C columns has the graph's W/H ratio: each panel's ratio is (W/H)×R/C; `layout(bs)` places a faceted graph by W/H.
- **BR-48.5** Refused in twoway's order, codes and words (E6): `rows()`/`cols()` numbers (r(121), r(123), r(125), r(126)); both given (r(198)); `holes()` numbers; the first leftover in typed order — a repeated sub-option that twoway reads once, a capitalised spelling of any by() sub-option, or a word that is no spelling of any by() sub-option (`bogus`) — `option <name as typed>[()] not allowed`, r(198); `iscale()` below 0 or above 10,000, r(198) `gm_linewidth must be between 0.000 and  1.0e+04`. Every word twoway's by() accepts (D-48g), including those dash names and does not draw (`graphregion()`, `t1title()`, `subtitleformat()`, the shrink words), is accepted.
- **BR-48.6** `iscale()` and `imargin()` text twoway cannot read is drawn at the default with twoway's first note, printed once by `dash` (both modes); `rows()`, `holes()`, `iscale()` given empty are silent.
- **BR-48.7** `cols()` or `rows()` above the by_groups limit is drawn at the limit with one note naming `$dash_max_by_groups`; a spec not written by dash.ado is clamped at the ceiling (1,000) silently.
- **BR-48.8** The layout is the same in the saved page, the served app, a tab and a `layout(bs)` cell, and is unchanged by filter moves.

## Technical requirements

- **TR-48.1 The grammar table** (Python and Mata twins, kept equal by a test).
  - `_DASH_BY_GRAMMAR` (dash_render.py, directly after `_DASH_BY_RESCALE_KEYS`, 19872): a dict, name → `(minimum, takes_args, stage, repeat_ok)`, transcribed from `bygraph_g.class` parse_make (:74-81, stage 1: `total tot`, `missing miss`, `rows r ()`, `colfirst colf`, `cols c ()`, `scale scale ()`, `iscale iscale ()`, `legend leg ()`, `legloc legloc ()`, `plegend pleg ()`, `plegloc plegloc ()`, `clegend cleg ()`, `clegloc clegloc ()`) and parse_settings (:266-285, stage 2: `compact com`, `style style ()`, the six rescale words with their minimums, `holes hol ()`, `noedgelabel noedge`, `edgelabel edge`, the i*/noi* axes, titles, labels and ticks words, `noindividual noind`, `individual ind`, `ilegends ileg`, `imargin im ()`, the six shrink words, `subtitleformat subtitleformat ()`; every name of :266-283 is a row, `NOXTitles XTitles NOYTitles YTitles` included), and stage 3, transcribed from the readers parse_make calls after parse_settings (D-48g): `graphregion graphr ()`, `plotregion plotr ()` (bygraph_g.class:224-225), the twelve titles of graph_g.class:286-299 with their capitals as minimums (`r1title r1 ()` … `b2title b2 ()`, `note note ()`, `caption cap ()`, `subtitle sub ()`, `title t ()`), `spacers space ()` (`SPACErs`, :345) and `bgcolor bgc ()` (bygraph_g.class:228). S28's `_DASH_BY_TEXT_SPELLINGS` is not this table's source (it lists only what S28 draws); where it and the fixture differ, the fixture wins and the difference goes to the notes file for S28. Values are tuples (literal_eval round-trip, so `_supply_missing_constants` carries it to the app). Where two declared names share a minimum (`ixt`: IXTicks and IXTitles), the first declared wins, as `syntax` does; 48-01's fixture probes `ixt` to confirm and the table follows the fixture. `repeat_ok` (the fourth element) is 1 exactly for the names the fixture's repeat probes show accepted twice (expected: the stage-3 titles, regions and bgcolor, whose readers loop).
  - Mata `_dash_by_grammar()` returns the same rows as a string matrix (dash_parse.mata part 5, directly after `_dash_rep_value`, 4543).
- **TR-48.2 Mata `_dash_by_scan(string scalar scname)`** (after `_dash_by_grammar`). Reads the tail with `st_strscalar(scname)`, splits it with `_dash_rep_toks(s, 0)` and names each word with `_dash_rep_optname`/`_dash_rep_value` (called, not edited). Sets locals: `_byg_rows`, `_byg_cols`, `_byg_holes`, `_byg_iscale`, `_byg_imargin` (the first copy's argument as typed; empty when absent or `()`), `_byg_rows_ok`, `_byg_cols_ok`, `_byg_holes_ok` (1 when the argument matches `^[0-9 .eE+\-/(),:\[\]to]*$`), `_byg_left` (the first leftover in typed order, as the message `option NAME not allowed` or `option NAME() not allowed`, NAME as typed, or ""), `_byg_iscale_kind` (`num`, `star`, `empty`, `bad`) and `_byg_iscale_val`, `_byg_imargin_bad` (1 when the text is no marginstyle name of S47's table, not 1-4 numbers and not `l|r|b|t=#` pairs), `_byg_imargin_neg` (1 when the text is numbers or `l|r|b|t=#` pairs and one of them is below 0). A word is a leftover when it is a second copy of a name whose row has `repeat_ok` 0 (48-01 probes `legend(off) legend(on)`, `clegend(on) clegend(off)`, `title("a") title("b")`, `graphregion() graphregion()`, `t1title(a) t1title(b)`, `spacers() spacers()` and `bgcolor(white) bgcolor(red)`), or when its name, exactly as typed (case-sensitive), is no valid spelling of any grammar row at any stage: a capitalised spelling (`YRESCALE`, `Rows()`) and an unknown word (`bogus`) alike (Q-48.1 ruling). The first leftover in typed order is reported. Linear in the tail's length; no `st_` call that executes text.
- **TR-48.3 Mata `_dash_by_clamp(string scalar scname, real scalar limit)`**: rewrites, in the scalar, the first copy of `rows()`/`cols()` whose integer exceeds `limit` to `limit`, and sets `_byg_clamped` to the sub-option names it changed ("" if none).
- **TR-48.4 dash.ado `_dash_by_check`** (new program, `version 19`, directly after `_dash_by_parts`'s `end`, 3274; not rclass). `args V` (a string scalar holding the tail). In order (E6):
  1. `mata: _dash_by_scan(st_local("V"))`.
  2. For `rows`, then `cols`: when the argument is not empty, if its `_ok` is 0, `mata: _dash_say("err", "", "<o>() invalid -- invalid number", "")` and `exit 121`; else `local 0 `", <o>(`_byg_<o>')"'` and `capture noisily syntax [, Rows(numlist integer >0 min=0 max=1) Cols(numlist integer >0 min=0 max=1)]`, exiting with its `_rc` when nonzero.
  3. Both arguments nonempty: `may not specify both rows() and cols()`, r(198).
  4. `holes`: as step 2 with `HOLes(numlist integer >0 max=300)` (non-matching text: `holes() invalid -- invalid numlist`, r(121)).
  5. `_byg_left` nonempty: print it through `_dash_say("err", …)`, r(198).
  6. `_byg_iscale_kind` `num` or `star` with a value below 0 or above 10000: `gm_linewidth must be between 0.000 and  1.0e+04` (two blanks before `1.0e+04`), r(198).
  7. Notes (twoway's first note only, `_dash_say("txt", …)`): `bad` iscale → `(note:  named style <text> not found in class numstyle, default attributes used)`; `_byg_imargin_bad` → `… in class margin, …`; `_byg_imargin_neg` (dash's own, since twoway draws overlapping panels silently and dash draws 0) → `(note: by(, imargin()) below 0 is drawn as 0)`. Each is printed once by `dash`; the renderer prints no by() spacing note.
  8. Last: `_dash_limit, name(by_groups)`; `mata: _dash_by_clamp(st_local("V"), <r(value)>)`; when `_byg_clamped` is not empty, one note `(note: by(, cols(#)) is above the by_groups limit of <n>; drawn with <n> columns; $dash_max_by_groups raises it)` (rows likewise), built in Mata with the dollar sign as `char(36)`, never typed in dash.ado's text, where Stata would expand it.
- **TR-48.5 The call** (`_dash_validate_value`, `byvarlist` branch, dash.ado:2334-2423): when `hastail`, after `unab` succeeds and before `local norm`, `tempname B`, `mata: st_strscalar(st_local("B"), st_local("tail"))`, `_dash_by_check `B'`, then `mata: st_local("tail", st_strscalar(st_local("B")))`. The tail never passes through a macro expansion other than these `st_local` reads (the block form JSE-69 requires).
- **TR-48.6 `_dash_parse_by`** (CRITICAL: warn). Matching becomes case-sensitive (drop `.lower()` at 19988; the existing branches compare the typed name); new branches, before S28's text branch: `rows` with parens (spellings `r`..`rows`), `colfirst`, `holes`, `compact`, `iscale`, `imargin`, and `style` with `compact` or `default` → `pass` with the comment "laid out by `_dash_layout_cell` (WP-30 P1.15b)". The 5-tuple, the injection check and every other branch are unchanged; `r` bare stays rescale. The docstring's "dash implements three" paragraph lists the drawn sub-options.
- **TR-48.7 `_dash_by_grid_options(by_raw) -> dict`** (after `_dash_by_rescale`, 20025): `{"rows": int, "cols": int, "holes": tuple, "colfirst": bool, "compact": bool, "style": str, "iscale": str, "imargin": str}`, first copies, case-sensitive; numbers through `_dash_expand_numlist(tokens, limit=300)` (CRITICAL, called not edited), non-positive or non-integer values dropped silently (dash.ado refused them); `cols`/`rows` from `_dash_parse_by`'s rule (`by_cols` key kept).
- **TR-48.8 `_dash_by_positions(n_panels, opts, legend_at=0, clegend_at=0, limit=None) -> (cells, nrows, ncols, extra)`**: E5's port; `cells[i]` is panel i's `(row_from_top, col)` (0-based; row_from_top = rows − r); `extra` maps "legend"/"clegend" to their cell for S53 and "full_n" to twoway's full_n; `cols`/`rows` clamped at `limit` (default `_DASH_LIMITS["by_groups"][1]`). Pure.
- **TR-48.9 `_dash_by_size_mult(by_raw, full_n) -> float`**: f(k) from S21's `_DASH_BY_GMETRIC` (`resz = 1 − (k−1)/k·b1 − [k > k1]·(b2−b1)(k−k1)/k`, k = ceil(sqrt(full_n))); `iscale(#)` → #, `iscale(*#)` → f×#, else f; clamped to [0, 10000]. Silent.
- **TR-48.10 Scheme margin.** `_DASH_BY_INDIV_MARGIN` (constant, from the fixture's `by_indiv` table: name → marginstyle) and `SchemeParser.by_indiv_margin(self) -> tuple` (l, r, b, t in Stata units: `_props["margin by_indiv"]` if present, else the table by `self.name`, else `small`, resolved through S47's marginstyle table). `apply_to_figure` (7376) gains one statement after S08's stamp: `fig._dash_by_indiv = self.by_indiv_margin()`.
- **TR-48.11 `_dash_by_spacing(fig0, opts) -> (row_px, col_px)`**: sides from `imargin` (S47's reader; unreadable → the default), else zero under `compact`/`style(compact)`, else `fig0._dash_by_indiv`; `col_px = round(max(0, l + r) × PT_PER_RS × PX_PER_PT)`, `row_px` from t + b.
- **TR-48.12 `_dash_by_scale_panel(fig, m)`**: when `getattr(fig, "_dash_by_scaled", None) is None`, multiplies by m every numeric value (int/float, finite) and every `"<n>px"`/`"<n>pt"` string of the properties in `_DASH_BY_SCALED_PROPS` on: each renderer's five glyph slots (`size`, `line_width`, `text_font_size`), `LabelSet`/`Label`/`Title` (`text_font_size`, `x_offset`, `y_offset`, `border_line_width`), `Span`/`Arrow` (`line_width`), every `ArrowHead` an Arrow carries in `start`/`end` (`size`, `line_width`), every axis (`major_label_text_font_size`, `axis_label_text_font_size`, `axis_line_width`, `major_tick_line_width`, `minor_tick_line_width`, `major_tick_in`, `major_tick_out`, `minor_tick_in`, `minor_tick_out`, `major_label_standoff`, `axis_label_standoff`), every grid (`grid_line_width`); then sets `fig._dash_by_scaled = m`. Field specs, `Legend` and `ColorBar` are untouched.
- **TR-48.13 `_dash_layout_cell`** (CRITICAL: warn). For a faceted name: `go = gopts_of(name) or {}`; `opts = _dash_by_grid_options(go.get("by"))`; `cells, R, C, _ = _dash_by_positions(len(figs), opts)`; stamp `_dash_array_ar` (the panel's current `aspect_ratio`) on every panel that lacks it; `m = _dash_by_size_mult(go.get("by"), extra["full_n"])`; `_dash_by_scale_panel(f, m)` for each panel; when `go` has no `aspectratio` and `_dash_array_ar` is set, each panel's `aspect_ratio = _dash_array_ar × R / C`; `grid = gridplot([figs], sizing_mode="stretch_width")`, then `grid.children = [(f, r, c) for …]` plus one `Spacer(sizing_mode="stretch_width", aspect_ratio=<panel ratio>)` at `(r, 0)` for each row holding no panel; `grid.spacing = _dash_by_spacing(figs[0], opts)`; `grid._dash_by_ncols = C`; then S28's `_dash_by_frame_grid(grid, chrome, C)`; then `_dash_name_save(_dash_reflow(grid))`. `_dash_facet_cols` is kept for its callers (grep at the base) and unchanged.
- **TR-48.14 `_dash_reflow`** (CRITICAL: warn): `ncols = max(<children's>, getattr(grid, "_dash_by_ncols", 0))`; when `_dash_by_ncols` is set, `grid.cols = [_DASH_BS_TRACK] * ncols` (else the single track, as today). Nothing else.
- **TR-48.15 `_dash_auto_bs_layout._ar_of`**: when `nm` is not in `figures`, the panel `figures[f"{nm}__by__{k}"]` of least k whose key matches `^<nm>__by__\d+$`; its `_dash_array_ar`, else its `aspect_ratio`.
- **TR-48.16 Both modes.** No template edit: the served app reaches every change through `_dash_layout_cell` (36250), `_dash_parse_by`, `apply_to_figure` (SchemeParser travels with its class) and `_dash_parse_bs_layout`. Copy list (R2 row S48), on new lines directly after `"_dash_by_rescale",` (33200) and before S28's names: the comment `# by() grid and size (WP-30 P1.15b).` and `"_dash_by_grid_options", "_dash_by_positions",`, `"_dash_by_size_mult", "_dash_by_spacing", "_dash_by_scale_panel",`. `_DASH_BY_GRAMMAR`, `_DASH_BY_INDIV_MARGIN` and `_DASH_BY_SCALED_PROPS` reach the app through `_supply_missing_constants` (tuples and dicts only).
- **TR-48.17 Registries.** `test/function_test_map.py` under `# WP-30 S48 (P1.15b): by() grid and size (P1.15 part b)`, alphabetical: `SchemeParser.by_indiv_margin`, `_dash_by_grid_options`, `_dash_by_positions`, `_dash_by_scale_panel`, `_dash_by_size_mult`, `_dash_by_spacing`, each naming its `test_by_grid.py` unit test. `test/program_coverage_map.py` under S48's `COVERAGE["dash.ado"]` anchor: `_dash_by_check`; under S48's `COVERAGE["dash_parse.mata"]` anchor: `_dash_by_clamp`, `_dash_by_grammar`, `_dash_by_scan`. dash.ado's `_needed` (237) gains `_dash_by_scan _dash_by_clamp`; dash_parse.mata's header index (1-303) gains the three entries.
- **TR-48.18 Security (rule 1).** User text reaches Stata's parser only after the character-set check; every message and note leaves through `_dash_say`; the Mata scan is linear and bounded by the tail's length; the renderer bounds rows/cols at the ceiling and `holes` at 300 elements; no new HTML or JS sink (the post-pass writes numbers and `px` strings built from numbers).

## Boundaries

- **Not edited:** `_dash_by_groups`, `_expand_by_groups`, `_plan_by_groups`, `_dash_share_by_scales`, `_dash_facet_label`, `_dash_by_tokens`, `_dash_rep_toks`, `_dash_rep_optname`, `_dash_rep_value`, `_dash_expand_numlist`, `_dash_plot_margin` and every finisher (R11, S50's), `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, the appliers, `SchemeParser._init_properties` and `_FALLBACK_PROPS` (S50's in this batch), any scheme file or the extractor (A152).
- **Batch partners:** S49 (horizontal: `_make_figure_body`, the template's layer loop, axis-variable and title helpers, `_dash_validate_opts`); S50 (reference lines, finishers, scheme keys).
- **Later sections:** S53 (outer axes, edge labels and `compact`'s/`noedgelabel`'s axis effect, the one legend in `legend(at())`'s hole through `_dash_by_positions`, i* options, `margin by_indiv` and the other `by_*` scheme keys, stacking with every panel's axes); S56 (`text()` scaled by `_dash_by_size_mult`).
- **Residuals named here (Notes for the closeout):** S21's plot-region margin under by() uses f(panels), not `iscale()` or `full_n`; per-row label offsets (field-valued) are not scaled; `subtitleformat()`, the shrink words and other bystyles stay named.

## Stata truth

New extractor `scripts/extract_by_grid_truth.do` in S02's path-free form (`DASH_REPO`, `adopath ++ "<repo>/"`, `global dash_nobrowser 1`), run with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_by_grid_truth.do"`; writes `test/fixtures/by_grid_truth.json` (`git add -f`) with the D12 `_meta` (`stata_version`, `born_date`, `dash_commit`, `extracted`; `dash_commit` from `git rev-parse HEAD` through `shell` into a local, read with `Macro.getLocal`; the python block never calls Stata, writes a backtick as `\x60`). Data: `sysuse auto`; `gen g10 = mod(_n, 10)`; `gen g3 = mod(_n, 3)`. Each probe runs `capture noisily twoway scatter mpg weight, mlabel(rep78) <opts>` and records rc, the first error line and every `(note:` line; a drawn probe is exported to SVG and read through `scripts/svg_truth.py`:
- **grid** (s2color): `by(foreign)`, `by(rep78)`, `by(rep78, total)`, `rows(1)`, `cols(1)`, `holes(3) total`, `colfirst total`, `holes(1 2 3)`, `cols(5)`, `holes(9)`, `rows(2) colfirst holes(1)`, `cols(3) holes(2) colfirst`, `total cols(5)`, `r(2)`, `c(1) colf`, `hol(2 2 9)`, `by(g10)`, `rows(5)` with g3: per panel its label and `(row, col)` from the SVG panel regions' distinct x and y (0-based from the top-left), and the grid's R and C.
- **sizes** (s2color, stcolor, economist): plain, `by(foreign)`, `by(g10)`, `iscale(.5)`, `iscale(*2)`, `iscale(0)`, `iscale(abc)`, `compact`, `style(compact)`, `imargin(large)`, `imargin(1 2 3 4)`, `imargin(l=5)`, `imargin(bogus)`, `imargin(zero) compact`: the multiplier (label font over the plain graph's), the column and row gaps in Stata units (SVG gap ÷ (min(W,H)/100)), viewBox; and `by(foreign) xsize(12) ysize(3)`'s viewBox.
- **refusals**: every row of E6, plus `cols(0) rows(0)`, `ixt`, `legend(off) legend(on)`, `clegend(on) clegend(off)`, `title("a") title("b")` (accepted: stage 3), `graphregion(color(white)) graphregion(color(red))`, `t1title(a) t1title(b)`, `spacers(ring(1)) spacers(ring(2))`, `bgcolor(white) bgcolor(red)`, `TOTAL rows(0)`, `bogus`, `bogus TITLE("x")`, `TITLE("x") bogus`, `bogus rows(0)` (a number error before the unknown word), `nolegend`.
- **accepted** (D-48g): for every row of `_DASH_BY_GRAMMAR` as 48-01 first writes it, the row's minimum spelling alone (with an argument the row takes: `rows(2)`, `holes(3)`, `iscale(.5)`, `imargin(small)`, `style(compact)`, `legend(off)`, `clegend(on)`, `legloc(6)`, `plegend(off)`, `plegloc(6)`, `clegloc(3)`, `scale(1)`, `graphr(color(white))`, `plotr(margin(zero))`, `t("a")`, `t1("a")` … `r2("a")`, `note("a")`, `cap("a")`, `sub("a")`, `space(ring(1))`, `bgc(white)`, `subtitleformat(%9s)`, a bare word otherwise) and the spelling one letter shorter (when that is no other row's spelling): rc and first error line each, recorded under `accepted["<name>:min"]` and `accepted["<name>:short"]`. A row whose minimum is refused, or whose shorter spelling is accepted, corrects the table before any test is written. The python block also records `declared`: every option name of the D-48g syntax lines and title calls, read from bygraph_g.class and graph_g.class as text (never executed), with its capitals.
- **by_indiv**: for each of Stata's 26 shipped schemes, `margin by_indiv` resolved through its `#include` chain (text read in the python block, as `scripts/extract_scheme_truth.py` resolves chains; never executed), and each marginstyle's four sides (`margin-<name>.style` → `gsize` keys → s2color's ladder).

Truth cases (Stata only through the driver, E5): BYG-01..BYG-18 in `test/test_by_suboptions.cscript` (area script, R1: one run at its end, before `display "All by() sub-option tests PASSED."`) compare live twoway's rc and first error line with dash's: BYG-01..BYG-15 the refusal rows of E6 and the order probes, BYG-16 `cols(500)` (dash: rc 0 and the limit note; twoway rc 0), BYG-17 the unknown-word rows (`bogus`, `bogus TITLE("x")`, `TITLE("x") bogus`, `bogus rows(0)`, `nolegend`), BYG-18 the accepted probes (every minimum spelling rc 0 in both, every refused shorter spelling refused alike). BYG-20..BYG-26 in S01's S48 block of `test/test_wp30_truth.cscript` build `dash … saving()` pages for six grid probes and `iscale(.5)`, read the panels' cells and label font sizes from the page with a python block, and compare them with twoway's SVG read in the same run.

## TDD test stubs

New `test/test_by_grid.py` (module helpers: `_T` the fixture, loaded lazily; `_both(spec)` through `test_mode_parity._standalone/_served`; `_cells(layout)` reading a by() grid's children as `(label, row, col)` through S28's find-panel-by-label helper). Red at `batch-17-base` unless marked guard.

- Test: `TestTheGrammar::test_python_equals_mata` — `_DASH_BY_GRAMMAR` equals the rows `_dash_by_grammar()` returns (parsed from dash_parse.mata's text). Red: NameError.
- Test: `TestTheGrammar::test_every_spelling_is_twoways` — for every row, the fixture's `accepted` probe of its minimum spelling has rc 0 and that of the shorter spelling is refused; every name of the fixture's `declared` list is a row; `repeat_ok` equals the fixture's repeat probes. Red: NameError.
- Test: `TestPositions::test_probe[<grid probe>]` — `_dash_by_positions` cells, R and C equal the fixture for every grid probe. Red: AttributeError.
- Test: `TestPositions::test_full_n_counts_holes_beyond_the_grid` (holes(9): 2x2) and `::test_limit_clamps` (cols 10^12 → 1,000). Red.
- Test: `TestTheGridIsDrawn::test_probe[<grid probe>-saved|served]` — the page's panels sit in the fixture's cells; `grid.cols` has C tracks; an empty row holds one Spacer. Red: default grid.
- Test: `TestTheSizes::test_multiplier[<sizes probe>]` — `_dash_by_size_mult` equals the fixture's ratio within 0.5%. Red.
- Test: `TestTheSizes::test_panels_are_scaled[saved|served]` — `by(foreign)`'s panel marker size, label and tick fonts, line widths are 0.85 × the plain graph's; S28's chrome cells unchanged; laying the graph out twice scales once. Red.
- Test: `TestTheSizes::test_every_numeric_size_is_scaled` — for scatter+mlabel, line, bar, rcap and a yline, every numeric property in `_DASH_BY_SCALED_PROPS` on every model is ×m and no other property changed. Red.
- Test: `TestSpacing::test_probe[<sizes probe>-saved|served]` — `grid.spacing` equals the fixture's gaps × `PT_PER_RS × PX_PER_PT` (rounded), per scheme. Red.
- Test: `TestTheArrayRatio::test_xsize12_ysize3[saved|served]` — two panels in one row: each `aspect_ratio == 2.0` (the array 4.0); with `aspectratio(.5)` added, each panel keeps `_dash_figure_aspect`'s per-panel 2.0 and is not divided. Red: 4.0.
- Test: `TestTheAutoLayoutSeesFacets::test_wide_facets_get_a_row[saved|served]` — REM-10-03: `wide` (by foreign, xsize 12 ysize 3) gets span 12. Red: 6.
- Test: `TestNamedNoMore::test_drawn_sub_options_are_not_named[<rows|r|holes|colfirst|compact|style(compact)|iscale|imargin>]` and `::test_capitals_are_named_by_the_renderer` (a hand-built `YRESCALE` is named, not honoured). Red.
- Test: `TestHostileInput::test_bounded` — a 10^6-character by() tail, `holes(1/1000000)`, `iscale(1e400)`, `imargin("</style>")` each lay out within 1 s with finite sizes and no text in any style string. Red: AttributeError.
- Test: `TestTheIndivTable::test_every_shipped_scheme` — `SchemeParser(name).by_indiv_margin()` equals the fixture's sides for all 26. Red.
- Guard: `TestLayoutHoldsAcrossAMove::test_saved_and_served` — after a dropdown move (saved through js_runner, served through `test_mode_parity._fire`) the grid's children, spacing and panel sizes are unchanged.
- Shared: `test/test_mode_parity.py` CORPUS `_case("by() grid and size (WP-30 P1.15b)", [_sc()], go={"by": "rep, rows(2) holes(1) colfirst iscale(.7) imargin(small)"})` (guard), with `_annotations`' layout profile extended to children positions, spacing and `cols` if it does not read them.
- Browser, new `test/test_by_grid_browser.py` (skips without Chrome, like `test_by_scales_chrome.py`): `TestInChrome::test_cols5_leaves_empty_columns` (two panels each about a fifth of the grid's width), `::test_no_horizontal_scroll_at_375`, `::test_save_button_still_writes_png`.
- cscript: BYG-01..BYG-18; BYG-20..BYG-26.

### Pinned tests to flip (R9; re-measured at the base, never trusted)

E7's list. Each flip gets a comment `Flipped (WP-30 P1.15b): <old> was wrong because twoway draws/refuses it (by_grid_truth.json <probe>)` and a `Flipped:` line in `$S/48-flips.txt`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Grammar twins, completeness, scan, clamp | pytest `TestTheGrammar`; cscript BYG-01..BYG-18 | dash_parse.mata, `accepted` | n/a |
| Refusals, order, notes, accepted words | cscript BYG-01..BYG-18 against live twoway | E6 rows, `accepted` | n/a (Stata) |
| Placement | pytest `TestPositions`, `TestTheGridIsDrawn`; BYG-20..BYG-24 | `by_grid_truth.json` | yes |
| Sizes and spacing | `TestTheSizes`, `TestSpacing`, `TestTheIndivTable`; BYG-25..26 | fixture | yes |
| Array ratio, layout(bs) | `TestTheArrayRatio`, `TestTheAutoLayoutSeesFacets` | fixture viewBox | yes |
| Moves | `TestLayoutHoldsAcrossAMove`; parity corpus | — | yes |
| Browser | `test_by_grid_browser.py` | — | saved |
| Registries, served names | maps, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` | — | served |

**Acceptance criteria.**
- **AC-48.1** (BR-48.1) every grid probe's cells match twoway in both modes; BYG-20..BYG-24 PASS.
- **AC-48.2** (BR-48.2, BR-48.3) multipliers within 0.5% and gaps within one pixel of the fixture for the three schemes; chrome cells unscaled.
- **AC-48.3** (BR-48.4) panel ratios (W/H)×R/C; REM-10-03's span 12.
- **AC-48.4** (BR-48.5, BR-48.6) BYG-01..BYG-18 PASS (rc and first line equal twoway's; notes as specified).
- **AC-48.5** (BR-48.7) `cols(500)` draws 100 columns with one note; `TestHostileInput` passes.
- **AC-48.6** (BR-48.8) the move guard, the parity corpus and the browser tests pass; no node skipped.
- **AC-48.7** every flip carries its reason; no test deleted; the full run is green; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 48-01 to 48-13 form the one commit of entry `P1.15b`, made by 48-13 on `wp30-s48` with the subject `Lay out and size by() panels as twoway does and refuse its bad by() arguments (WP-30 P1.15b)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s48`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S48 "$SLOT" "$S" "$S/run_<script>.do"`. Before the first edit of each CRITICAL or HIGH symbol (`_dash_parse_by`, `_dash_layout_cell`, `_dash_reflow`, `_glyph_layer_lines`) confirm `$S/batch-17-impact.txt` records the approval (E4).

<task type="auto" id="48-01">
  <name>Write the grid fixture and tests</name>
  <files>scripts/extract_by_grid_truth.do, test/test_by_grid.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-17-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s48`; stop otherwise. Create `scripts/extract_by_grid_truth.do` as "Stata truth" describes and run it through the slot; it writes `test/fixtures/by_grid_truth.json`. Create `test/test_by_grid.py` with every stub of "TDD test stubs", naming new symbols as `dr._dash_by_positions` and the others so they fail with AttributeError now. Append the CORPUS case to `test/test_mode_parity.py` before `CORPUS`'s closing bracket (after earlier sections' cases). Run `python3 -m pytest test/test_by_grid.py -q -n 6 -p no:cacheprovider -rf > "$S/48-new.log" 2>&1`. Write `$S/48-P1.15b-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/by_grid_truth.json')); m=d['_meta']; print(all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), d['sizes']['s2color']['by_foreign']['mult'], d['refusals']['rows(0) cols(0)']['rc'], len(d['by_indiv']), d['refusals']['bogus']['rc'], all(v['rc'] == 0 for k, v in d['accepted'].items() if k.endswith(':min')))"` prints `True 0.85 125 26 198 True` (the multiplier to two places); `grep -c FAILED "$S/48-new.log"` is at least 20; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway grid fixture existed and every pytest regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="48-02">
  <name>Write the refusal and truth cases</name>
  <files>test/test_by_suboptions.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    In `test/test_by_suboptions.cscript`, directly before `display ""` / `display "All by() sub-option tests PASSED."`, add one contiguous run headed `// BYG: by() arguments refused as twoway refuses them (WP-30 P1.15b)` with BYG-01..BYG-18: each runs `capture noisily twoway scatter mpg weight, by(foreign, <args>)` and the same through `dash scatter mpg weight, by(foreign, <args>) saving(...)` under `log` capture, and compares rc and the first error line (E6's rows, the order rows included; BYG-16 is `cols(500)`: twoway rc 0, dash rc 0 and the limit note; BYG-17 the unknown words; BYG-18 the accepted probes of "Stata truth"). Put the `_s48_*` helpers directly above S01's `* ==== S48 P1.15b: by() grid and size ====` header and BYG-20..BYG-26 between S01's S48 start and end lines in `test/test_wp30_truth.cscript`. Run both scripts through the driver on the unmodified tree; append every `BYG-nn FAIL` line, with the twoway line it quotes, to `$S/48-P1.15b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "BYG-(0[1-9]|1[0-8]) FAIL" "$S/run_test_by_suboptions.log"` is at least 14 (dash refuses no by() word at the base, so every refusal row and BYG-18's shorter spellings fail); `grep -cE "BYG-2[0-6] FAIL" "$S/run_test_wp30_truth.log"` is at least 5; `grep -c "BSC-10 PASS" "$S/run_test_by_suboptions.log"` prints 1.]]></verify>
  <done>The refusal cases and the twoway layout comparisons were in their scripts and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="48-03">
  <name>Add the Mata grammar, scan and clamp</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    In part 5, directly after `_dash_rep_value` (4543 at c96facd), add `_dash_by_grammar()`, `_dash_by_scan(string scalar scname)` and `_dash_by_clamp(string scalar scname, real scalar limit)` as TR-48.1-TR-48.3 define them, each with a header comment citing E6 and the bygraph_g.class lines. Call `_dash_rep_toks`, `_dash_rep_optname` and `_dash_rep_value`; edit none of them. Add the three entries to the header index (1-303) in its form. Read S47's marginstyle name list at the base (`grep -n "allsides-ms" dash_render.py`) and copy the names into `_dash_by_scan`'s imargin check with a comment naming the Python table.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_grid.py -q -n0 -p no:cacheprovider -k TestTheGrammar` passes; `python3 -m pytest test/test_file_headers.py test/test_no_orphans.py -q -n 6 -p no:cacheprovider` reports 0 failed except the orphan check for `_dash_by_scan`/`_dash_by_clamp` (called by 48-04).]]></verify>
  <done>The by() grammar, the first-copy scan with its leftover rule and the limit clamp existed in Mata, reading the tail only from a string scalar.</done>
</task>

<task type="auto" id="48-04">
  <name>Refuse bad by() arguments in Stata</name>
  <files>dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Add `_dash_by_check` after `_dash_by_parts`'s `end` (TR-48.4, `version 19`, header comment with E6's stage model) and the call in `_dash_validate_value`'s `byvarlist` branch (TR-48.5) as a block, never a one-line if. Add `_dash_by_scan _dash_by_clamp` to `_needed` (237). Confirm by reading the branch that no statement after the call reads `r()`; record the line numbers in `$S/48-notes.txt`. Add the program and the three Mata functions under S48's anchors of `test/program_coverage_map.py`, alphabetically. `_dash_validate_value` is UNKNOWN to the index; its by() callers are dash.ado:5345-5354 (grep).
  ]]></action>
  <verify><![CDATA[`test_by_suboptions.cscript` through the driver prints `BYG-01 PASS` to `BYG-18 PASS` and `All by() sub-option tests PASSED.` except BYS-02..BYS-04 and BYS-06 (flipped by 48-10); `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash refused by() argument errors in twoway's stages, codes and words, noted unreadable iscale() and imargin() text once, and bounded cols() and rows() at the by_groups limit with one note.</done>
</task>

<task type="auto" id="48-05">
  <name>Parse the grid sub-options case-sensitively</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_parse_by` is CRITICAL (32 impacted, 16 processes). Add `_DASH_BY_GRAMMAR` after `_DASH_BY_RESCALE_KEYS` (TR-48.1), make TR-48.6 in `_dash_parse_by` (case-sensitive names, the new pass branches before S28's text branch, the docstring) and add `_dash_by_grid_options` after `_dash_by_rescale` (TR-48.7). Touch no other branch and not the 5-tuple. Run every test file that names `_dash_parse_by` (`grep -l _dash_parse_by test/*.py`) with `-n 6`; failures that E7 lists are expected and fixed by 48-09.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_grid.py -q -n0 -p no:cacheprovider -k "NamedNoMore or TheGrammar"` passes; `python3 -c "import sys,warnings; sys.path.insert(0,'$WT'); import dash_render as d; warnings.simplefilter('error'); print(d._dash_parse_by('foreign, rows(2) holes(1 3) colfirst compact iscale(*.8) imargin(small) cols(2)')[1:])"` prints `(2, False, False, [])`.]]></verify>
  <done>The renderer read rows, holes, colfirst, compact, style(compact), iscale and imargin in twoway's spellings and case and stopped naming them.</done>
</task>

<task type="auto" id="48-06">
  <name>Port placement, multiplier and spacing</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_by_positions`, `_dash_by_size_mult` and `_dash_by_spacing` after `_dash_by_grid_options` (TR-48.8, TR-48.9, TR-48.11), each with a docstring citing E5. Add `_DASH_BY_INDIV_MARGIN` beside them, transcribed from the fixture's `by_indiv` table, and `SchemeParser.by_indiv_margin` (TR-48.10) beside `apply_to_figure`, plus its one stamp statement after S08's in `apply_to_figure` (7376). Read S21's `_DASH_BY_GMETRIC`, S08's `PT_PER_RS`/`PX_PER_PT` and S47's marginstyle reader by name at the base; edit none of them. Add the four map entries under S48's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_grid.py -q -n 6 -p no:cacheprovider -k "TestPositions or multiplier or TheIndivTable"` passes; `python3 -m pytest test/test_scheme_fidelity.py test/test_scheme_consumption.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>twoway's placement, by() multiplier and panel spacing were pure functions, and every figure carried its scheme's by() panel margin.</done>
</task>

<task type="auto" id="48-07">
  <name>Scale panel sizes once</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_DASH_BY_SCALED_PROPS` and `_dash_by_scale_panel` (TR-48.12) after `_dash_by_spacing`, with a docstring naming D-48f and the field-spec residual. Scale numbers and `<n>px`/`<n>pt` strings only, with a finite check; write `px` strings with `"%gpx"`. Add its map entry under S48's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_grid.py -q -n 6 -p no:cacheprovider -k "every_numeric_size or HostileInput"` passes.]]></verify>
  <done>One idempotent pass multiplied every numeric size a panel draws, leaving field specs, legends and colour keys alone.</done>
</task>

<task type="auto" id="48-08">
  <name>Lay out the grid in both modes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_layout_cell` (10 impacted) and `_dash_reflow` (12 impacted) are CRITICAL and `_glyph_layer_lines` HIGH. Make TR-48.13 in `_dash_layout_cell` (keeping S28's `_dash_by_frame_grid` call after placement, and its signature), TR-48.14 in `_dash_reflow`, TR-48.15 in `_dash_auto_bs_layout._ar_of`, and TR-48.16's copy-list lines directly after `"_dash_by_rescale",`. Do not edit `_generate_app_source`. Run test_layout_facets.py, test_layout_tabs.py, test_server_facets.py, test_by_scales.py, test_by_text.py and test_mode_parity.py with `-n 6`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_grid.py -q -n 6 -p no:cacheprovider` passes except the flips' tests; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Both modes placed, spaced, scaled and proportioned by() panels as twoway does, and layout(bs) saw a faceted graph's ratio.</done>
</task>

<task type="auto" id="48-09">
  <name>Flip the pytest pins</name>
  <files>test/test_resource_limits.py, test/test_server_facets.py, test/test_by_scales.py</files>
  <action><![CDATA[
    Re-measure E7's pytest pins on this tree and flip them in place with a `Flipped (WP-30 P1.15b)` comment each: `TestByColsCannotOutgrowThePanels::test_the_columns_are_at_most_the_panels` asserts `_dash_by_positions`' columns (cols(5) of 4 → 5; 10^12 → 1,000; cols(0)/cols(-7) → the automatic 2; `by_cols` kept); `TestAnUnimplementedBySuboptionIsNamed`'s rows use `subtitleformat(%9s)` and `shrink`; `test_rescale_tokens_are_not_named`'s `r(1)` and `rows(2) yrescale` rows name nothing; `test_style_rescale_is_named_with_its_own_note`'s last assertion is `[]` for `style(compact)`. Write one `Flipped:` line per node to `$S/48-flips.txt`. Delete no test; if `test_help_claims_5.py` :768-842 or `test_layout_facets.py` pins are also red, flip them the same way here and list them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_resource_limits.py test/test_server_facets.py test/test_by_scales.py test/test_help_claims_5.py test/test_layout_facets.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every pytest pin of the old grid, clamp or naming asserted twoway's layout, with the reason recorded.</done>
</task>

<task type="auto" id="48-10">
  <name>Flip the script and parity pins</name>
  <files>test/test_by_suboptions.cscript, test/test_help_claims_5.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
    In `test/test_by_suboptions.cscript` make BYS-02, BYS-03, BYS-04 and BYS-06 use `subtitleformat(%9s)` and `shrink` (still named) instead of rows(), compact and holes(), with their display texts; in `test/test_help_claims_5.cscript` HC5-08 asserts that rows(2) holes(1) compact colfirst are not named and the page holds a 2-row grid; in `test/test_mode_parity.py` the expected notes at :1576/:1915 (as S28 left them) drop `rows(2) compact`. Append the `Flipped:` lines to `$S/48-flips.txt`. Delete no case.
  ]]></action>
  <verify><![CDATA[Both scripts through the driver print `All by() sub-option tests PASSED.` and `HC5-08 PASS`; `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The scripts and the parity corpus asserted the drawn grid sub-options, with the reasons recorded.</done>
</task>

<task type="auto" id="48-11">
  <name>Check the grid in Chrome</name>
  <files>test/test_by_grid_browser.py</files>
  <action><![CDATA[
    Create `test/test_by_grid_browser.py` with the three browser stubs, using `responsive_probe.find_chrome()` and the skip form of `test_by_scales_chrome.py` (a skip under DASH_STRICT is a failure). Build the pages in `tmp_path` from Python specs (no Stata run).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_grid_browser.py -q -n0 -p no:cacheprovider -rs` reports 3 passed and no skip.]]></verify>
  <done>Chrome drew empty columns, kept the page within 375 px and saved the grid's PNG.</done>
</task>

<task type="auto" id="48-12">
  <name>Document the grid in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In "Faceting with by()" (2055-2137 at c96facd; find by text) add synopt entries for `rows(#)`, `holes(numlist)`, `colfirst`, `compact`, `iscale([*]#)` and `imargin(marginstyle)`; rewrite the arrangement paragraph (2102-2107: twoway's cells, empty columns up to the by_groups limit with a note) and the "implemented sub-options" sentence (as S28 left it) to name them and the refusals; add one sentence that panel sizes are twoway's by() size; in "Figure proportions" (3179-3227) one sentence that xsize()/ysize() size the whole by() array. Keep S28's sentences. Every new or changed line is at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_5.py test/test_by_grid.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -c "holes\|iscale\|imargin"` prints 0.]]></verify>
  <done>The help documented the grid and size sub-options, their refusals and the whole-array size.</done>
</task>

<task type="auto" id="48-13">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.15b"]` ("by() rows, holes, colfirst, compact, iscale and imargin are named and ignored, bad by() arguments are accepted, and faceted graphs miss the automatic layout"). Close that entry in place (`- [x]`) with "Notes: BUGS.md Resolution" and today's date; delete only the `"P1.15b"` line of `WP30_OPEN`; replace both `<!-- WP-30 P1.15b -->` markers in place with "Notes: CHANGELOG lines". Run test_tracking_documents.py, test_by_grid.py, test_fixtures_are_committed.py, test_cscript_hygiene.py, the maps' tests with `-n 6`, and both scripts through the driver. `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/48-full-1.log"` in the background, read when `exit=` appears (E6 for the known flaky tests). Stage exactly the files tasks 48-01 to 48-12 changed (listed in `$S/48-files.txt` as each task ends) plus these three, with `git add -f test/fixtures/by_grid_truth.json`; check `git -C "$WT" diff --cached --name-only` (G6); write `$S/48-message.txt` per Notes, check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/48-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.15b -->' "$WT/CHANGELOG.md"` prints 0; `python3 -c "import sys; sys.path.insert(0, '$WT/test'); import test_tracking_documents as t; print('P1.15b' in t.WP30_OPEN)"` prints `False`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.15b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.15b was closed naming existing tests, its markers carried the measured old and new behaviour, and one green commit on wp30-s48 was ready for the merger.</done>
</task>

## Section completion criteria

- Panels occupy twoway's cells for every fixture probe, with holes, colfirst, empty columns and rows, in both modes and unchanged by moves.
- Panel sizes take twoway's by() multiplier or `iscale()`; spacing follows `margin by_indiv`, `compact` and `imargin()`; the array has the graph's ratio; layout(bs) places faceted graphs by it.
- Every E6 refusal, unknown word included, matches twoway's rc, words and order, and every word twoway accepts is accepted (BYG-01..BYG-18); honoured sub-options are silent; limits bound cols/rows with one note.
- New functions mapped, served names copied, grammar twins equal, fixture committed with `-f`; every flip recorded; one green commit `(WP-30 P1.15b)`.

## Notes

- **Q-48.1, ruled (orchestrator, 06oct2026): refuse unknown by() words too.** M5 refuses "bad by() arguments" in twoway's words; twoway refuses an unknown word (`bogus`: `option bogus not allowed`, r(198)) in the same final stage as capitals and repeats, in typed order (`bogus TITLE("x")` names `bogus`, `TITLE("x") bogus` names `TITLE()`). `_dash_by_scan` therefore treats every word that is no spelling of a grammar row as a leftover (TR-48.2), BYG-17 compares those rows with live twoway, and the CHANGELOG line names the unknown word. Because the rule now refuses anything outside the table, the table is twoway's whole by() grammar (D-48g) and BYG-18 proves that nothing twoway accepts is refused.
- **Maintainer question (ratify) Q-48.2: the `iscale()` bound of 10,000.** D-48d refuses `iscale()` above 10,000, which over-refuses between 10,000 and twoway's scheme-dependent draw-time bound (measured: 10^4 accepted, 10^5 refused, s2color). Recommendation: ratify the 10,000 bound (a numeric limit; the ruling keeps it). The alternative, computing twoway's bound from the panel's widest line width, needs the scheme's line widths in Stata's gm units in dash.ado. Until ratified, S48 is written on the 10,000 bound.
- **`_dash_limit` and `r()`.** `_dash_by_check` calls it last; 48-04 records that nothing after the call reads `r()`.
- **S28's helpers.** If S28 named `_dash_by_frame_grid` or the find-panel-by-label test helper otherwise, use S28's names; never re-implement them.
- **Shared lines with S49 (conflicts in context only; the merger keeps both).** dash.ado's `local _needed` statement (237) gains S48's two names and S49's `_dash_hz_order`; dash_parse.mata's header index gains entries from both (S49's function sits after `_dash_rep_scan`, S48's after `_dash_rep_value`); `test/test_mode_parity.py` CORPUS gains cases from S48, S49 and S50.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; check it after each slot run; a SKIP is not a pass.
- **Merge rules.** R1: BYG-01..BYG-18 as one run at the end of `test_by_suboptions.cscript`; BYG-20..BYG-26 in S48's block. R2: S48's anchor after `"_dash_by_rescale",`; maps under S48's anchors. R3: "Faceting with by()" (S48's sentences; S28's kept) and "Figure proportions". R4/R5: the two `P1.15b` markers, the entry and its key. R6: one new program after `_dash_by_parts`, `version 19`, three Mata functions in part 5 with header entries and `_needed`. R7: one new fixture and extractor. R8: one CORPUS case. R9: E7's flips. R10: none of the combined pins move (re-check `test_unsupported_report_is_true.py` and the single-y digest; by() pages only). R11/R12: no finisher, template, figure-body or applier edit.
- **Landing (merger).** `gitnexus detect-changes` must name `_dash_parse_by`, `_dash_by_grid_options`, `_dash_by_positions`, `_dash_by_size_mult`, `_dash_by_spacing`, `_dash_by_scale_panel`, `SchemeParser.by_indiv_margin`, `SchemeParser.apply_to_figure`, `_dash_layout_cell`, `_dash_reflow`, `_dash_auto_bs_layout`, `_glyph_layer_lines` and test symbols.
- **Commit message.** Subject as in "Commit boundary". Body: `$S/48-P1.15b-failure.txt`; the measured defect (Overview's block); what changed (TR-48.1-TR-48.18, both modes); then `Regression: test/test_by_grid.py::<Class>::<test> -- failed at <base sha> with <text>` per node (cscripts as `test/test_by_suboptions.cscript BYG-01`, `test/test_wp30_truth.cscript BYG-20`); the `Flipped:` lines of `$S/48-flips.txt`; `Fixture: test/fixtures/by_grid_truth.json (scripts/extract_by_grid_truth.do)`; `BUGS.md: "by() rows, holes, colfirst, compact, iscale and imargin are named and ignored, bad by() arguments are accepted, and faceted graphs miss the automatic layout" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.15b). by() panels are placed in twoway's cells (_dash_by_positions, a port of bygraph_g.class full_n, set_rows_cols and set_placement: rows(), cols(), holes(), colfirst, empty columns and rows), spaced by the scheme's margin by_indiv, compact or imargin() in Stata units (_dash_by_spacing, SchemeParser.by_indiv_margin), sized by twoway's by() multiplier or iscale() (_dash_by_size_mult, _dash_by_scale_panel), and proportioned so the whole array has the graph's xsize()/ysize() ratio, which layout(bs) now reads (_dash_auto_bs_layout), through _dash_layout_cell and _dash_reflow in the saved page and the served app; dash.ado refuses by() argument errors in twoway's stages, codes and words (_dash_by_check with Mata _dash_by_scan: rows() and cols() numbers, both given, holes() numbers, a repeated, capitalised or unknown sub-option, in twoway's typed order, iscale() out of bounds; every word twoway's by() accepts is accepted) and bounds cols() and rows() at the by_groups limit with a note (_dash_by_clamp). Pinned by test/test_by_grid.py::TestTheGridIsDrawn::test_probe, test/test_by_grid.py::TestTheSizes::test_panels_are_scaled, test/test_by_grid.py::TestSpacing::test_probe, test/test_by_grid.py::TestTheAutoLayoutSeesFacets::test_wide_facets_get_a_row, test/test_by_grid.py::TestTheGrammar::test_every_spelling_is_twoways, test/test_by_suboptions.cscript BYG-01, test/test_by_suboptions.cscript BYG-17, test/test_wp30_truth.cscript BYG-20; fixture test/fixtures/by_grid_truth.json. Residual, deferred (WP-30): the plot-region margin of a panel ignores iscale() and holes (section 21's f(G)); per-row label offsets under by() are not scaled; subtitleformat(), the shrink options and other bystyles stay named.
  ```
- **CHANGELOG lines** (each replaces its marker in place):

  ```
  ### Results that change
  - by() graphs are laid out and sized as twoway does: `rows()`, `holes()`, `colfirst`, `compact`, `style(compact)` and `imargin()` place and space the panels (they were named and ignored); panel text, markers and lines are drawn at twoway's by() size, 0.85 of the plain graph's for 2 to 4 panels and 0.6 for 10 to 16 (they were full size), or at `iscale()`; `cols()` beyond the panel count leaves empty columns, as twoway does, up to the by_groups limit (it was clamped to the panels); `xsize()` and `ysize()` size the whole array (two panels of `xsize(12) ysize(3)` were 4:1 each and are now 2:1), and `layout(bs)` gives a wide faceted graph its own row. (WP-30, P1.15b)

  ### Changed behaviour (may need your do-files changed)
  - by() arguments twoway refuses are refused in its words (each was accepted, most with a note): `rows()` with `cols()` (`may not specify both rows() and cols()`, r(198)); a `rows()` or `cols()` that is not one positive integer and a `holes()` that is not a list of up to 300 positive integers (`rows() invalid -- invalid number, outside of allowed range`, r(125), and twoway's r(121), r(123), r(126) forms); a repeated `rows()`, `cols()`, `holes()`, `style()`, `compact`, `iscale()`, `imargin()`, `colfirst`, `total`, `missing` or rescale word, or a capitalised sub-option such as `YRESCALE` or `TITLE()` (`option YRESCALE not allowed`, r(198)); an unknown by() sub-option such as `bogus` (`option bogus not allowed`, r(198)); `iscale()` below 0 or above 10,000 (`gm_linewidth must be between 0.000 and  1.0e+04`, r(198)). (WP-30, P1.15b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B16** (:516-528): parts a (rows/holes/colfirst) and e (compact/iscale/imargin) closed by `<sha>`; B16 stays partly open for S53's parts until it lands.
  - **REMAINING.md:396** (REM-10-03): closed by `<sha>`.
  - **DROPIN-REMAINING.md:105-112**: the grid and size half "Closed by <sha> (WP-30 S48)".
  - **New P2 rows:** the plot-region margin of a by() panel uses f(panels) where twoway uses f(full_n) and `iscale()` (S21's `_dash_plot_margin`); per-row (field-valued) label offsets under by() are not scaled; twoway's second `iscale()` note ("named style 1") is not copied.
  - **AGENTS.md invariant:** "by() layout lives only in `_dash_layout_cell` (positions from `_dash_by_positions`, sizes from `_dash_by_scale_panel`, applied once per panel); dash.ado's `_dash_by_check` is the only place by() arguments are refused."
  - **Unverified:** twoway's `iscale()` bound under schemes with wider lines; Stata 14-18.5 (not run, M2).
