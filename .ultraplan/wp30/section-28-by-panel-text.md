# Section 28: by() panel labels and overall text (P1.15 part a)

> Part of: WP-30 · Items: P1.15 part a (entry `P1.15a`; GAPS2-B16-b, GAPS2-B31-a, GAPS2-B31-b, GAPS2-B31-d) · Risk: yellow · Batch: 10 (merge order S28, S29, S30) · Depends on: 15, 19 · Blocks: 48 · Tasks: 26, 1 commit · Case prefix: BP

## Review amendments

- Fixed (blocker): 28-19 added an eighth element to `range_probe._RANGES_JS` rows, which left `_MOVE_TIMED_JS` waiting for every plot's y range to agree, which a chrome cell's fixed 0-1 range never does, so `test_hundred_panels_settle` could not pass. Both scripts now skip the two chrome names; the row shape and every user (S21's `test_default_axes_chrome.py` too) are unchanged; `test_by_scales_chrome.py` is no longer edited.
- Fixed (major): earlier WP-30 sections' test files with by() cases (S15 `test_scheme_chrome.py`, S18 `test_axis_format_fallback.py`, S19 `test_series_labels.py`, S20 `test_value_lists.py`, S21 `test_default_axes.py`, S27 `test_bar_range_geometry.py`) had no task, and 28-11's rule would have stopped the section on any red node in them. New tasks 28-20 and 28-21 flip them; old 28-20..28-24 are now 28-22..28-26 (Tasks: 26).
- Fixed (minor): the tasks were inside an xml code fence; they are bare XML as BRIEF and every reviewed section has them.
- Resolved: Q-28.1 is a marked Maintainer question with the recommendation "P2 item", since S53 recorded the box as outside its scope (section-53, open-questions.md); the Resolution's residual and S53 bullet say so.
- Checked at `c96facd`: the saved join :31655-31656 and served join :35513-35520, `_dash_facet_label` :20107 (`" / "`, `"Missing"`), `_dash_by_groups` :3436/:3459, the frame lines :29986, :30029, :33898, :35569, :35580, `_dash_parse_by` :19941, `_dash_layout_cell` :25001-25020, copy-list anchor `"_dash_facet_label", "_dash_stata_date_text",` :33201, `range_probe._RANGES_JS`/`_MOVE_TIMED_JS`: as quoted. The BP needles are ASCII and match bokeh's page JSON (`"text":"Domestic, 1"`; `S\nDomestic` written as two characters), measured on bokeh 3.9.0.
- Checked: batch 10. S28 is the batch's only editor of `_build_sources_and_figures` and `_generate_app_source` (R12); it calls S09/S29's pass without editing it, reads `_textbox_color` and `SchemeParser.apply_to_figure` (S30 edits neither's callers' contract), and shares only append-only or distinct hunks of `test_mode_parity.py`, `test_label_sinks.py`, `test_html_output.py` and `test_help_claims_2.py`. M5: `TITLE()` stays named until S48 refuses it (register P1.15.4); M6: nothing new printed. Tracking forms match section-01.
- Rejected: "refuse `by(, TITLE())` now under M5" — register P1.15.4 gives the by() refusals to S48, in twoway's order.
- (cross-file pass) 28-26 verify: added the key-deletion check `grep -c '^    "P1.15a": "' "$WT/test/test_tracking_documents.py"` → 0 (S01 TR-01.10.1).
- (cross-file pass) Checked, no change (g08's S48 note): graph_g.class:299 (StataNow base) declares `Title`, minimum `t`, and bygraph_g.class:226 reads by()'s titles through it, so twoway accepts `by(foreign, t("X"))`; S28's probe a14 measured it rc 0 with no title drawn, so `_DASH_BY_TEXT_SPELLINGS["title"]` starting at `ti` (and `t("X")` → None in TestTheTextOptions) matches twoway; S48 accepts the spelling without drawing it.
- The review pass applied both lenses.
- Q-28.1 answered (ratification 06oct2026, row 36: "Add to S53"): S53 draws the panel label's filled box; D-28e, the S53 boundary bullet, the BUGS.md Resolution's residual list, the Maintainer question and the closeout's residual candidates now say so. S28's own drawing is unchanged (no fill), and it keeps the `dash_by_label` Title name S53 draws behind.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:105-112 (P1.15) reads, for this part: "Panel labels are appended to the graph title, and there is no "Graphs by" note. Composite and missing panels are titled differently from `twoway`." and names `title` and `note` among the by() sub-options "named in the note and ignored". GAPS2-B31 says "The panel label is appended to the figure title as "T — 0" … so `subtitle()` cannot reach it. There is no "Graphs by" note. … The missing panel reads "Missing" and joined labels read "Domestic / 3"". GAPS2-B16 says "`by(, title())` is stored but not drawn (JSE-46)". Measured at `c96facd`, the same in the saved page and the served app (research p1-15 §1 rows c, d, d2; critic correction 1; this section's probes, quoted under Evidence):
- `title("T") by(foreign)` titles the panels `T — Domestic` and `T — Foreign`; twoway draws `T` above each panel and the label `Domestic` below it.
- `subtitle("S") by(foreign)` draws a separate `S` row on every panel beside the label; twoway's `S` replaces the label.
- `by(foreign rep78, missing)` titles `Domestic / 1` … `Foreign / Missing`; twoway writes `Domestic, 1` … `Foreign, (missing)`.
- No `Graphs by Car origin` note is drawn; `by(foreign, title("X") subtitle("S") note("N") caption("C"))` draws none of the four and says `by() sub-option(s) not implemented and ignored: title("X") …`.
- A string by() variable's `""` group is drawn as an untitled panel: `by(s, total)` with `s` in {`D`, `F`, `""`} draws 4 panels (an untitled one, D, F, and a Total of all 74 rows); twoway draws 3 (D, F, and a Total of the 62 rows whose `s` is not `""`). `by(e, missing)` with every `e` equal to `""` draws one plain untitled figure; twoway draws one panel titled `(missing)` and the note `Graphs by e`.

**After this section**, in both modes and before and after any filter move:
- each panel's label is its own centred, unbolded `Title` row in the scheme's subtitle style, drawn below the graph's own `title()` (which every panel keeps, as twoway repeats it), and a graph-level `subtitle()` merges with it as twoway's does (replace, `prefix`, `suffix`, `""` removes it);
- labels of several variables are joined `", "`, a missing value reads `(missing)`, and a string `""` counts as missing in the group panels and in Total, as `markout …, strok` counts it;
- `by(, title() subtitle() note() caption())` are drawn once over the whole array, in the scheme's title, subtitle, note and caption styles, and the default note `Graphs by <label>` (twoway's SetByList: the label, else the name; `A and B`; `a, B, and C`) is drawn unless `by(, note(""))` removes it, with `prefix`/`suffix`/sub-option-only forms merged as twoway merges them;
- `note()` and `caption()` outside by() stay on every panel, as twoway draws them.

**Why one section.** These are the text parts of P1.15 (research §6 split, part 1; A138): the panel label (`_dash_facet_label`, both modes' title join), the missing-value rule that decides which panels exist (`_dash_by_groups` and the frame sites) and the overall text. They share one helper family, every new canvas sink, and one fixture. The grid (rows, holes, colfirst, sizes, refusals) is S48's and the shared axes and keys are S53's; both build on the chrome cells this section introduces.

**Decisions applied.**
- M1 (match twoway's look): the label is a centred, unbolded `Title` through S15's `_dash_textbox_place` and scheme subheading style; a CHANGELOG "Results that change" line.
- M5: nothing new is refused here. `TITLE("X")` and the other capitalised by() sub-options, which twoway refuses (`option TITLE() not allowed`, r(198), probe a12), stay named until S48 refuses them (register P1.15.4 is S48's); this section matches the four text sub-options case-sensitively so it never draws what twoway refuses.
- M6: nothing new is printed. A valid sub-option of these boxes that dash cannot draw (`ring(0)`, `pos(1)`, `nobexpand`) is named through `_dash_textbox`'s existing channel, once per graph.
- Register P1.15.5 (A53): date panel titles keep dash's date text. P1.15.7 (A55): twoway's splitting of a value label holding double quotes into two subtitle lines (q04) is not copied; the help says so.
- X.1 (A133): copy-list names appended at R2's S28 anchor. X.2 (A134): no new note text. X.4 (A136): the BP cases go in S28's block of `test/test_wp30_truth.cscript`. X.5 (A137): every new function is mapped in the same commit.

**Section decisions (this file).**
- **D-28a. Where the overall text lives.** Two "chrome cells" inside the panel `GridPlot`: a head cell spanning every column above the panels and a foot cell spanning them below. The grid is still made by `gridplot()` (so its one merged `SaveTool` and `_dash_name_save` work as today), and its children are then re-positioned. The cells are bare `bokeh.models.Plot` models, not `figure`s, so the many tests and helpers that collect `figure`s by type still see panels only. Measured on a scratch prototype (E10): `figure` cells turned 390 nodes red, `Plot` cells 147. A `column(head, grid, foot)` wrapper (131 red) was rejected: `_dash_name_save(cell, name)` at the layout(bs) call site (dash_render.py:30963) finds no toolbar on a column, so it would have to change, the overall text would be missing from the saved PNG, and S53's legend and axis-title cells must sit inside the grid anyway.
- **D-28b. How the layout finds the cells.** They are attached to the graph's first panel figure as the private attribute `_dash_by_chrome` (the pattern of `fig._dash_scale_values`), so `_dash_layout_cell`'s signature and its four call sites (saved 30959, 31213, 32491; served 36250) are unchanged. `_dash_by_chrome_figures(figures, facet_map)` reads them back for the canvas-text pass.
- **D-28c. One fixture of this part's own.** `test/fixtures/by_text_truth.json` by `scripts/extract_by_text_truth.do`. R7 lets no other section run this extractor, so S48 and S53 make their own fixtures; PLAN.md's `by_chrome_truth.json` name is left to S53.
- **D-28d. The three-variable note.** twoway's SetByList writes the first of three or more variables by its NAME (`Graphs by foreign, Repair record 1978, and Headroom (in.)`, p20, a quirk of bygraph_g.class:1439-1443). dash writes the same text (M1), and the help states it.
- **D-28e. The label's box is not drawn here.** twoway draws the panel label in a filled box spanning the plot region (stcolor `#F0F0F0` = gs15 with a gs15 outline: `textboxstyle subtitle subheading_gs`, `color bylabel_outline gs15`, scheme-stcolor.scheme:22-25; s2color bluishgray). Those keys are not in the 26 `dash-*.scheme` files, and only a scheme regenerator may add them (A152; S30 is batch 10's). The label is drawn without the box here; S53 (batch 18) draws the box (ratification row 36, 06oct2026: "Add to S53"); see Notes, Q-28.1.
- **D-28f. Help ownership.** R3 names S28's lines :2070 and :2096; the panel-title paragraph (:2106-2116) and the implemented-sub-options sentence (:2122-2125) state the old rule too (`"Domestic / 3"`, "A graph's own title() leads each of its panels' titles", title() named and ignored), so S28 rewrites those sentences as well. No batch-10 partner edits "Faceting with by()" (R3 table), and S48/S53 edit other sentences of it later.

**Test order and commit rule (rule 7, D1, A156).** One cycle, one commit, subject ending `(WP-30 P1.15a)`.
- **28-01** writes the regression module `test/test_by_text.py` (and the panel-finding helper `test/by_panel_probe.py`) and runs it on the unmodified tree, saving `<scratch>/28-P1.15a-failure.txt`. It never commits.
- **28-02 to 28-04** add the extractor and fixture, the fixture-driven tests and the BP truth block; each runs red-first on the unmodified renderer and appends its red lines to the failure file.
- **28-05 to 28-10** make the fix.
- **28-11 to 28-19** flip the 147 measured pinned nodes (E10), three files per task; 28-11 first re-measures them on the batch-10 base.
- **28-20 and 28-21** flip the by() pins of the test files earlier WP-30 sections wrote (S15, S18, S19, S20, S21, S27), which E10 could not measure.
- **28-22** registers the sinks and parity cases, **28-23** adds the browser check, **28-24** runs the cscripts and flips HC5-07, **28-25** writes the help.
- **28-26** closes the entry and makes the one commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every by() dashboard's panel text changes in both modes, through CRITICAL symbols

**Why yellow.** The change is visible on every faceted dashboard (labels move out of the title, a note row appears under every by() grid), touches five CRITICAL symbols (`_build_sources_and_figures`, `_dash_parse_by`, `_dash_by_groups`, `_expand_by_groups`, `_dash_layout_cell`) and the served template (HIGH), and flips 79 measured tests (147 parametrised nodes) in 26 files, most of which identify a panel by `fig.title.text` (E10). twoway's truth is fully measured, and a prototype of the design (quoted under Evidence E9) drew, stacked and saved correctly in headless Chrome.

**Risk factors.**
1. Tests that find a panel by its title text, count the plots of a document or unpack grid children as 3-tuples (research critic correction 5). Mitigation: one shared test helper (`test/by_panel_probe.py`) that finds a panel by its label `Title` and skips chrome cells; every flip uses it; the prototype run (E10) lists the 147 red nodes measured at `c96facd`, and 28-11 re-measures them on the batch-10 base.
2. Two partners (S09's canvas-text pass, S29's SMCL) must reach the new sinks. The pass is given `self.figures`, and chrome cells are not figures of the map. Mitigation: a second pass call over `_dash_by_chrome_figures(...)` right after S09's, in both modes; keys `<name>__by__head`/`<name>__by__foot` so S29's `<name>__by__<i>` split still names the graph; a sink test in `test_label_sinks.py` per new sink.
3. A `Plot` with no renderer logs Bokeh's `W-1000 (MISSING_RENDERERS)` (measured E9). Mitigation: each chrome cell carries one invisible `Span` in `center`, which satisfies Bokeh's check (`Plot._check_missing_renderers` counts an Annotation in `center`).
4. The panel grid gains rows: anything that reads `GridPlot.children` positions (`_dash_reflow`'s column count; tests) sees chrome cells. Mitigation: chrome cells are 5-tuples spanning every column at column 0, so `_dash_reflow`'s `ncols` is unchanged; the helper names them (`dash_by_head`, `dash_by_foot`) and the tests' grid reader skips them.
5. Stacking below the breakpoint must keep reading order. Measured (E9): at 375 px head, panels, foot stack top to bottom with no horizontal scroll.
6. The "no faceting" sentinel in `_build_sources_and_figures` (`len(by_groups) == 1 and by_groups[0][0] == ""`, :31584) reads an empty label as "no panels". After the fix a missing panel is `(missing)`, so `by(e, missing)` takes the facet path; a value label whose text is `""` still collides (Notes).

**Mitigation, overall.** Fixture-driven tests compare both modes with twoway probe by probe; the parity corpus gains two by() cases, and `_layout_tree` profiles a chrome cell (its texts, sizes, colours and alignment) so both modes' cells are compared; the browser test draws both modes' pages.

## Dependencies

- **Depends on: 15, 19.**
  - S15 (batch 5) gives `_dash_textbox_place(clock, just)`, the scheme's `text_clock`/`text_just`, the unbolded centred `Title` style in `apply_to_figure`, and `_dash_text_annotations` drawing subtitle, note and caption as `Title` rows by clock (TR-15.7, TR-15.8). The panel label and the chrome cells are drawn through them.
  - S19 (batch 7) settles twoway's default titles and keys and the rule that text is built raw for S29 (`_dash_layer_series`, `_dash_axis_default_titles`); this section's tests run on S19's titles, and its texts are built raw the same way.
  - S01's entry `P1.15a`, its `WP30_OPEN` key, its `<!-- WP-30 P1.15a -->` marker under `### Results that change`, the S28 stub block and the S28 map anchors. S09 (batch 3) gives `_dash_finish_graph_text`; S06 (batch 2) the note channel that `_dash_report_suboptions` uses.
- **Blocks: 48.** S48 places the panels (`_dash_by_positions` in place of `_dash_facet_cols`) and keeps calling `_dash_by_frame_grid(grid, chrome, ncols)` after it; its iscale scales the panel label, never the chrome text. S53 (through S48) adds the legend and outer-axis-title cells beside these.
- **Parallel batch (10):** S29 (SMCL in graph text) and S30 (Stata colour grammar). Merge order S28, S29, S30.
- **Can run with them because** S28 edits neither S09's pass function nor any colour reader; S29 edits neither `_build_sources_and_figures` nor `_generate_app_source` (index batch 10) and lands after S28 so its pass tests see S28's sinks; S30 edits `translate_mcolor`, the colour parsers, `SchemeParser`'s colour methods and the scheme files, which S28 only reads through `_textbox_color`.

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487). Earlier batches move them: locate each by its symbol and the quoted text, never by number alone. Research: `.ultraplan/wp30/research/p1-15.md` §1 rows c, d, d2, §2 "Panel labels" and "Overall text", §3C and critic corrections 1, 3, 5 and 6.

### E1. The panel label is appended to the graph's title, in both modes

Saved, `DashRenderer._build_sources_and_figures` (def 31389), the facet loop of "3. Build figures", dash_render.py:31652-31657:

```python
31652                        fig = self._make_figure(g_panel, src,
31653                                                facet_view=panel_view_r,
31654                                                rescale=_brs)
31655                        orig_title = fig.title.text if fig.title else ""
31656                        fig.title.text = f"{orig_title} — {label}" if orig_title else label
31657                        if name in link_names:
```

Served, the generated `_dash_figure_for` inside `ServerAppBuilder._generate_app_source` (def 33915), dash_render.py:35513-35520:

```python
35513            "        if _fac_label is not None:",
35514            "            # The panel title is the figure's OWN title text -- the",
...
35518            "            _own = fig.title.text if fig.title is not None else ''",
35519            "            fig.title.text = (f'{_own} \u2014 {_fac_label}' if _own",
35520            "                              else _fac_label)",
```

Both run after the figure is complete (saved: after `_make_figure` returns; served: at the end of `_dash_figure_for`), so a `Title` added at these two places is added after every axis and text box of the panel, in the same order in both modes. BokehJS pushes `fig.title` after every model of `fig.above` (`_compute_layout_panels`, bokeh.js 3.9.0:44765-44767: `get_side(title_location).push(this._title)`), so the graph's title is the outermost row and a `Title` in `fig.above` sits between it and the frame: twoway's order (r07: `T` at SVG y 459, `Domestic` at y 622).

The graph-level `subtitle()` is drawn per panel by `_dash_text_annotations` (def 25969, called at saved :30400 inside `_make_figure_body` and served :35261 inside `_dash_figure_for`), beside the label instead of merged with it. At HEAD it is a `Label`; after S15 it is a `Title` placed by clock (TR-15.8). Research probe_sub, `subtitle("S") note("N") by(foreign)`, both modes: `[('title','Domestic'), ('above','Label','S'), ('below','Label','N')]`.

### E2. Composite and missing labels: `_dash_facet_label` (def 20107)

dash_render.py:20150-20170:

```python
20150    keys = [key] if len(by_vars) == 1 else list(key)
20151    parts = []
20152    for var, val in zip(by_vars, keys):
20153        if isinstance(val, str):
20154            parts.append(val)
20155            continue
20156        if GlyphMapper._mlabel_missing(val):
20157            parts.append("Missing")
20158            continue
...
20170    return " / ".join(parts)
```

A string value `""` takes the first branch and titles its panel `""`. The docstring (:20113-20119) records twoway's `Domestic, 3` and `(missing)` as differences. `DashRenderer._facet_label` (def 30049) is a wrapper that passes the renderer's labels and formats; its docstring's example `"Domestic / 3"` changes, its code does not. The served app calls `_dash_facet_label` directly (:35604) and copies it by name (functions tuple, :33201).

### E3. Which panels exist: a string `""` is not treated as missing

The grouping, `_dash_by_groups` (def 3436), dash_render.py:3457-3460:

```python
3457    for gkey, gdf in gb:
3458        vals = (gkey,) if len(by_vars) == 1 else gkey
3459        if not by_missing and any(pd.isna(v) for v in vals):
3460            continue
```

The frames handed to it (critic correction 1: three sites, five lines):
- saved `DashRenderer._expand_by_groups` (def 29934), :29985-29986, the group frame, which is also the Total frame when the Total panel has no qualifier of its own (`t_df = work_df`, :30025):
  ```python
  29984        work_df = df.copy()
  29985        if not by_missing:
  29986            work_df = work_df.dropna(subset=valid_vars)
  ```
  and :30028-30029, the Total frame under its own qualifiers (`t_df = t_df.dropna(subset=valid_vars)`);
- served template :35569 `"        work_df = g_df if _bmissing else g_df.dropna(subset=by_vars)",` and :35580 `"                _t_df = _t_df.dropna(subset=by_vars)",`;
- the build-time count `ServerAppBuilder._plan_by_groups` (def 33855), :33898 `work = g_df if bmissing else g_df.dropna(subset=by_vars)`.

`dropna` keeps `""`. dash.ado already counts as twoway does: `_dash_by_panels` (dash.ado:3340) marks out with `markout `p' `varlist', strok` (:3346, and the Total panel at :3356), so `by(e)` with every value `""` is refused `nothing to graph` r(198) by dash.ado as by twoway, while the Python side draws the `""` group. The served app's Total redraw after a filter move reads `_owner_rows` (:35990-36000), which the build-time frame sets, so fixing the frame fixes the redraw (critic correction 1).

### E4. The four text sub-options are named and dropped

`_dash_parse_by` (def 19941) matches only `cols`, `total`, `missing`, the rescale words and `style(rescale|combine)`, lower-casing each name (:19988), and names everything else in one note (:20004-20020):

```python
20004        elif name == "style" and arg.strip() in ("rescale", "combine"):
...
20012        else:
20013            unsupported.append(tok)
20014    if unsupported and warn:
...
20018            "dash: by() sub-option(s) not implemented and ignored: "
```

`_DASH_BY_SUPPORTED` (:19856) holds those spellings. Research probe C (both modes) printed `dash: by() sub-option(s) not implemented and ignored: rows(1) holes(1) colfirst title("X") note("") legend(off) … caption("c") subtitle("s")`. The varlist alone is held to `_DASH_UNSAFE_BY` (:19847); the sub-options are user text (test_server_facets.py `TestAByTextHoldingMacroCharactersFacets` pins that title text holding a backtick, `$` or a backslash still draws two panels).

### E5. The panel grid

`_dash_layout_cell` (def 25001), dash_render.py:25012-25020, the one cell a faceted graph becomes in the grid, the tabs, layout(bs) and the served app:

```python
25012    if name in facet_map:
25013        figs = [figures[fk] for fk, _ in facet_map[name] if fk in figures]
25014        if not figs:
25015            return None
25016        cn = _dash_facet_cols(gopts_of(name) or {}, len(figs))
25017        rows = [figs[i:i + cn] for i in range(0, len(figs), cn)]
25018        while len(rows[-1]) < cn:
25019            rows[-1].append(None)
25020        return _dash_name_save(_dash_reflow(gridplot(rows, sizing_mode="stretch_width")))
```

`gridplot()` merges every panel's tools into one toolbar whose `SaveTool` `_dash_name_save` (def 24445) names (critic correction 4). `_dash_reflow` (def 24465) is the only code that reads a grid's children (:24509: `ncols = max(ncols, int(child[2]) + 1)`), and stacks the cells in DOM order below `n x _DASH_MIN_COLUMN_PX` (240) through a container query. No page script walks the document (`grep -n "roots()\|Bokeh.documents\|get_model_by" dash_render.py` finds nothing).

### E6. twoway's rule (StataNow 19.5; bygraph_g.class)

- The default note is put first among by()'s own options, so a typed `note()` inside by() supersedes or merges with it (bygraph_g.class:204-205):
  ```stata
  	.SetByList bylist : `varlist'				// title
  	local options `"note("Graphs by `bylist'") `options'"'
  ```
- SetByList (:1421-1446): one variable `LabOrName`; two `"A and B"`; three or more ``local list `1'`` (the NAME of the first), then `, <LabOrName>` per middle variable and `, and <LabOrName>` for the last. LabOrName (:1448-1456) is the variable label unless it is `""`, else the name: `_dash_var_label`'s rule (WP-29 S03).
- Each panel's label (RunGraph, :427-497): a string value `""` and a numeric `"."` read `(missing)`; several variables are joined `", "` (``local sep ", "``); the label is then given as the panel's `subtitle()` BEFORE the user's options (``local glob_op `"subtitle(`title') `glob_op'"'``, :497), so a graph-level `subtitle()` merges with it.
- Missing rows (:103-106): ``markout `missvar' `varlist' , strok`` unless `missing`.
- The label is drawn in the subtitle textbox with by()'s `special_options "subtitle(, astextbox box blcolor(scheme bylabel_outline))"` (bygraphstyle-default.style).

**Measured** (scratch `s28/probe28.do`, `probe28b.do`, `probe28c.do` through `scripts/stata_slot.sh`, with research `truth_by.do`/`truth_by2.do` records; `.Graph` members as recorded):

| Probe | twoway command (auto) | panels' `subtitle.text[1]` (`[2]`) | overall title / subtitle / note / caption |
|---|---|---|---|
| p01 | `scatter mpg weight, by(foreign)` | Domestic; Foreign | – / – / `Graphs by Car origin` / – |
| p14 | `…, title("T") by(foreign)` | Domestic; Foreign (each `title.text[1]` = `T`) | note as p01 |
| r01 | `…, subtitle("S") by(foreign)` | S; S | note as p01 |
| r02 | `…, subtitle("S", prefix) by(foreign)` | S (Domestic); S (Foreign) | note as p01 |
| p16 | `…, subtitle("Extra", suffix) by(foreign)` | Domestic (Extra); Foreign (Extra) | note as p01 |
| p15 | `…, subtitle("") by(foreign)` | (none); (none) | note as p01 |
| p17 | `…, subtitle(, ring(0) pos(1) nobexpand) by(foreign)` | Domestic; Foreign (moved inside: P2.4) | note as p01 |
| p18 | `…, by(foreign rep78)` | Domestic, 1; Domestic, 2; … | `Graphs by Car origin and Repair record 1978` |
| p19 | `…, by(rep78, missing)` | 1 … 5; (missing) | `Graphs by Repair record 1978` |
| p20 | `…, by(foreign rep78 headroom)` | Domestic, 1, 1.5; … | `Graphs by foreign, Repair record 1978, and Headroom (in.)` |
| p11 | `…, by(foreign, title("X") subtitle("S") note("N") caption("C"))` | Domestic; Foreign | X / S / N / C (SVG: X y 243, S y 434, N y 2929, C y 3073) |
| p12 | `…, by(foreign, note(""))` | Domestic; Foreign | no note |
| p13 | `…, by(foreign, note("My", suffix))` | as p01 | note lines `Graphs by Car origin`, `My` |
| a04 | `…, by(foreign, note("My", prefix))` | as p01 | note lines `My`, `Graphs by Car origin` |
| a03 | `…, by(foreign, note(, size(large)))` | as p01 | `Graphs by Car origin`, size 4.8611 (default 2.777) |
| a05 | `…, by(foreign, note("", suffix))` | as p01 | `Graphs by Car origin` |
| a06 | `…, by(foreign, ti("X") sub("S") cap("C"))` | as p01 | X / S / default note / C |
| a07 | `…, by(foreign, note("A") note("B"))` | as p01 | `B` |
| a08 | `…, by(foreign, note("A") note(, size(large)))` | as p01 | `A`, size 4.8611 |
| a13 | `…, by(foreign, title("X") title("Y"))` | as p01 | `Y` |
| a01 | `…, note("N") caption("C") by(foreign)` | as p01; each panel note `N`, caption `C` | default note |
| a02 | `…, subtitle("S") by(foreign, subtitle("O"))` | S; S | – / O / default note / – |
| r07 | `…, title("T") by(foreign, title("X"))` | Domestic; Foreign (each title T) | X / – / default note / – |
| a09 | `…, by(foreign, total)` | Domestic; Foreign; Total | default note |
| a10 | `… if foreign==1, by(foreign)` | Foreign | default note |
| a11 | `…, by(foreign rep78, missing)` | … Domestic, (missing); Foreign, 3; … Foreign, (missing) | two-variable note |
| q03 | unlabelled `foreign` (no value or variable label), `by(foreign)` | 0; 1 | `Graphs by foreign` |
| NB | `label variable foreign "   "`, `by(foreign)` | as p01 | `Graphs by    ` (blanks kept) |
| a17 | `s` = D (rows 1-40), F (foreign), `""` (rows 41-52); `by(s, total)` | D; F; Total; serset N 40, 22, 62 | `Graphs by s` |
| q01/a18 | `by(s, missing)` / `by(s, missing total)` | (missing); D; F (; Total) | `Graphs by s` |
| a19 | `e` = `""` everywhere, `by(e, missing)` | (missing) | `Graphs by e` |
| a20 | `by(e)` | — rc 198 `nothing to graph` | — |
| a12 | `…, by(foreign, TITLE("X"))` | — rc 198 `option TITLE() not allowed` | — |
| a14, a15 | `by(foreign, t("X"))`; `by(foreign, no("X"))` | rc 0, no title drawn; rc 198 `option no() not allowed` | — |

The minimum abbreviations are `ti`, `sub`, `note` (no shorter form: a15) and `cap` (a06), as dash.ado's own `TItle`/`SUBtitle`/`NOTE`/`CAPtion` (dash.ado:715-716). Repeated forms merge as twoway's textboxes do: the last occurrence that has text gives the text, and every occurrence's sub-options apply (a07, a08, a13). The SVG of p01 under stcolor draws the label at 105.13 px with `text-anchor="middle"` over a `#F0F0F0` rect spanning the plot region (x 553.33, width 2196.62), and the note `Graphs by Car origin` at 89.94 px, anchored left at x 245.36 (research `svg/p01.svg:572-578`). The label's size is the subheading size times the by() scale (.85 for two panels, research §2), which S48 applies.

### E7. dash at HEAD (the defect, measured)

- Python, both modes (research `probe_dash.py`, `probe_sub.py`, critic `crit_probe.py`): `title("T") by(foreign)` → `'T — Domestic'`, `'T — Foreign'`; `by(foreign rep78)` → `'Domestic / 1' … 'Foreign / 5'`; `by(rep78, missing)` → last `'Missing'`; `subtitle("S") note("N") by(foreign)` → each panel `[('title','Domestic'), ('above','Label','S'), ('below','Label','N')]`; `by(s, total)` on a frame of 30 D, 30 F, 14 `""` → panels `''`, D, F and `('Total', 74, …)` where twoway's Total holds 60.
- Stata, saved pages (scratch `s28/dash28.do`, then the page's JSON read in Python): `dash scatter mpg weight, by(e)` → `nothing to graph`, r(198) (dash.ado, as twoway); `by(e, missing)` → rc 0, one figure, no panel title and no note; `by(s, total)` → rc 0, 4 figures (`""`, D, F, Total); `title("T") by(foreign rep78, missing title("X") note("N"))` → titles `T — Domestic / 1` … `T — Foreign / Missing` and the warning `dash: by() sub-option(s) not implemented and ignored: title("X") note("N")`.
- Served (research `dash_srv.do`: `dash build, saving(app_s.py) replace server`, loaded, `make_document`): `by(s)` → 3 panels `''`, `'D'`, `'F'`.

### E8. The served copy lists (R2 row S28)

`ServerAppBuilder._glyph_layer_lines` (def 32834), functions tuple 33077-33425. S28's anchor: `"_dash_facet_label", "_dash_stata_date_text",` (:33201), directly after `"_dash_by_rescale",` (:33200). Already copied and edited in place: `"_dash_by_groups"` (:33313), `"_dash_facet_cols", "_dash_layout_cell",` (:33319), `"_dash_textbox_or_default",` (:33372), `"_dash_text_annotations", "_dash_scale_spec",` (:33375), `_dash_parse_by` (copied; edited in place). A module constant reaches the app through `_supply_missing_constants` (def 36619) when its `repr` round-trips through `ast.literal_eval` (a dict of tuples of strings does).

### E9. Prototype of the chrome cells (headless Chrome, bokeh 3.9.0; scratch `s28/proto28.py`)

Three panels `gridplot([[p0, p1], [p2, None]], sizing_mode="stretch_width")`, then `grid.children` rebuilt as `[(head, 0, 0, 1, 2)] + [(f, r + 1, c) …] + [(foot, 3, 0, 1, 2)]`; each cell a `figure(frame_height=1, height_policy="fit", width_policy="max", toolbar_location=None, tools="", outline_line_color=None, min_border=0, x_range=Range1d(0, 1), y_range=Range1d(0, 1))` with hidden axes and grid, one invisible `Span` in `center`, and `Title` rows (head: 16pt and 12pt above; foot: 9pt and 10pt below); `_dash_reflow(grid)` applied:
- `save tools on merged toolbar: 1`; children `[('figure', (0, 0, 1, 2)), ('figure', (1, 0)), ('figure', (1, 1)), ('figure', (2, 0)), ('figure', (3, 0, 1, 2))]`.
- Canvas rects `[x, y, w, h]` at 900 px: head `[0, 30, 900, 63]`, panels `[0, 93, 450, 250]`, `[450, 93, 450, 250]`, `[0, 343, 450, 250]`, foot `[0, 593, 900, 50]`.
- At 375 px (iframe, `responsive_probe`): `sw 375`, rects head `[0, 30, 375, 63]`, panels at y 93, 343, 593, foot `[0, 843, 375, 50]`: stacked in reading order, no horizontal scroll.
- Without the `Span`: `WARNING:bokeh.core.validation.check:W-1000 (MISSING_RENDERERS): Plot has no renderers` once per cell; with it, nothing.
- The same run with the cells as bare `Plot(...)` models (scratch `s28/proto28_plot.py`, the form TR-28.7 takes): children `[('Plot', (0, 0, 1, 2)), ('figure', (1, 0)), ('figure', (1, 1)), ('figure', (2, 0)), ('Plot', (3, 0, 1, 2))]`, one merged `SaveTool`, and the identical rects at 900 px and 375 px.

### E10. The tests that pin today's behaviour (measured; flipped in place, never deleted)

**Method.** `git archive c96facd` into scratch (`s28/proto`), the design of TR-28.1 to TR-28.7 patched in (`s28/patch28.py`), and every test file that names by() (`grep -l '"by"\|by(\|__by__\|facet' test/test_*.py`, 73 files) run with `-n 6`: 412 failed, 12,627 passed, 58 skipped with `figure` cells. The failing nodes rerun on an unpatched copy (`s28/proto0`): 22 fail there too, all in `test_responsive_layout.py` (`RuntimeError: the probe reported nothing at [375, 768, 1440] px` in that scratch copy), so they are not attributed and 28-11 re-measures them in the worktree. The other 390 rerun with the cells as `Plot` (`s28/protoC`, the design adopted): **147 nodes in 26 files**, below; with a column wrapper (`s28/protoB`): 131. Every one fails for one of these reasons: the panel found by `fig.title.text` (now the graph's title), the label text (`" / "`, `"Missing"`, `"T — label"`), a by() text sub-option expected in the "not implemented" note, a chrome cell counted among a document's plots or toolbars, or a grid child unpacked as a 3-tuple.

| Flip task | File::Class::test (parametrised nodes) |
|---|---|
| 28-11 | `test_help_claims_5.py`: `TestTheFacetLabelHelper::test_one_unlabelled_variable` (the `nan` case), `::test_two_variables_are_joined`; `TestThePanelTitles::test_a_date_is_titled_alike_in_both_modes`, `::test_a_display_format_plays_no_part`, `::test_a_fraction_is_written_without_its_leading_zero`, `::test_a_string_is_its_own_title`, `::test_an_unlabelled_value_is_written_as_stata_writes_it`, `::test_the_graphs_title_leads_each_panels`, `::test_the_helps_composite_example`, `::test_value_labels_are_used_whatever_the_display_format`; `TestTheOneLineFormHonoursCols::test_the_saved_page` (3); `TestTheSubOptionSplitterReadsStataQuotes::test_by_keeps_its_cols_after_an_apostrophe`, `::test_in_both_modes`; `TestTheSubOptionsDashDoesNotImplement::test_named_and_ignored`; `TestTheTotalAndMissingPanels::test_the_total_panel_is_one_more_than_the_group_limit`, `::test_total_with_missing_is_every_observation`, `::test_total_without_missing_is_the_groups_together`. `test_server_facets.py`: `TestAByTextHoldingMacroCharactersFacets::test_both_modes_draw_the_two_panels` (6); `TestAnUnimplementedBySuboptionIsNamed::test_each_unimplemented_sub_option_is_named` (the `title("By origin")` case); `TestEveryTypeFacetsTheSameWayInBothModes::test_the_missing_panel_agrees`, `::test_the_total_panel_agrees_too` (8). `test_by_scales.py`: `TestPanelsShareOneScale::test_a_linked_by_graph_shares` (2); `TestRescaleGivesEachPanelItsOwn::test_count_ticks_are_per_panel`, `::test_count_ticks_ignore_range_on_a_rescaled_axis`, `::test_range_is_not_applied_on_a_rescaled_axis` (2), `::test_yrescale_xrescale_rescale` (4) |
| 28-12 | `test_reserved_names.py`: `TestAGraphNamedLikeAPanel::test_the_saved_page` (4), `::test_the_served_app` (4); `TestAdversarialReservedNames::test_bypass_no_spelling_takes_a_panel_s_place` (12). `test_scheme_review_fixes.py::test_both_modes_title_a_by_panel_the_same` (3). `test_textbox_no_text.py::TestTrailingComma::test_facet_title_keeps_its_panel` (2) |
| 28-13 | `test_served_linked_views.py`: `TestBothModesShowTheSameRows::test_after_one_move` (6); `TestEachServedViewShowsItsOwnRows::test_a_per_layer_qualifier_keeps_its_panel`, `::test_after_one_move` (9); `TestEveryMoveStartsFromTheOwnedRows::test_the_saved_page_agrees`, `::test_the_served_rows` (2). `test_served_bs_layout.py`: `TestAByGraphsCellHonoursCols::test_the_cell_still_saves_under_the_graph_s_name`, `::test_the_saved_cell_is_the_served_cell` (6). `test_served_dates.py::TestTheServedFigureReadsTheDateAsTheSavedOne::test_a_by_graph_over_dates` |
| 28-14 | `test_server.py`: `TestServerByFaceting::test_by_creates_facet_figures`, `::test_by_doc_has_roots`, `::test_by_facet_labels_in_source`, `::test_the_by_total_key_adds_a_total_panel_in_both_modes` (2); `TestServerByTotalFullDispatch::test_by_total_source_in_generated_source`; `TestServerLpolyFpfit::test_fpfit_faceted_make_document_runs`, `::test_lpoly_faceted_make_document_runs`. `test_html_output.py::TestByFacetingHtmlOutput::test_by_cols_suboption_produces_html`, `::test_by_link_renders_valid_html`, `::test_by_total_adds_total_panel`. `test_toolbar.py`: `TestTheSavedPage::test_a_by_graph_s_panels_save_as_dashboard`, `::test_every_figure_has_the_nine_tools_in_order` (2); `TestTheServedApp::test_every_figure_has_the_nine_tools_in_order` (2); `TestWhatIsActiveWhenThePageOpens::test_every_toolbar_leaves_the_choice_to_bokeh` (2) |
| 28-15 | `test_qualifier_columns.py::TestATotalPanelReadsItsOwnColumn::test_a_served_filter_move_keeps_the_total_column`, `::test_a_total_panel_with_rows_when_no_group_has_one`, `::test_the_saved_page`, `::test_the_served_app`. `test_saved_stale_cue.py::TestTheCueFollowsEachTarget::test_by_panels`, `::test_by_with_total`; `TestTheFrozenTag::test_the_tag_of_each_kind`. `test_resource_limits.py::TestByColsCannotOutgrowThePanels::test_a_cols_past_the_panels_draws_one_row_as_it_always_did` (3) |
| 28-16 | `test_help_claims_4.py::TestTheSavedPageRecountsALayersOwnRows::test_after_a_filter_move` (2), `TestTheServedAppRedrawsFromTheFilteredRows::test_after_a_filter_move`. `test_help_claims_2.py::TestLabelsUsedAutomatically::test_by_panels_are_titled_by_the_value_labels`. `test_keyword_names.py::TestExcludeAByGraph::test_the_served_filter_leaves_its_panels_alone` (2) |
| 28-17 | `test_date_range.py::TestTheSavedPageHoldsThePlaceholder::test_a_by_panel_of_the_placeholder_is_titled_with_its_date`, `TestTheServedAppWritesThePlaceholder::test_a_by_panel_of_the_placeholder_is_titled_with_its_date`. `test_display_format_sites.py::TestFacetTitles::test_a_date_panel_is_titled_as_stata_in_both_modes` (2). `test_graph_options.py::TestByFaceting::test_facet_title_contains_group_label`, `TestByLinkIntegration::test_bl_09_facet_titles_contain_group_label` |
| 28-18 | `test_filter_exclude.py::TestTheSavedPageLeavesAnExcludedGraphAlone::test_a_graph_after_a_by_graph_is_left_alone`. `test_filter_exclusion_sets.py::TestAByPanelFollowsItsOwner::test_a_by_panel_follows_its_owner_across_moves` (2). `test_layout_tabs.py::TestTabsHoldFacetedGraphs::test_a_tabbed_graph_is_not_also_drawn_in_the_grid` |
| 28-19 | `test_phase5.py::TestByFacetingSecurity::test_by_xss_in_facet_label_is_canvas_text`. `test_by_scales_chrome.py::TestTheBrowserDrawsOneScale::test_auto_ranged_histogram_panels_share_after_a_move`, `::test_hundred_panels_settle`, `::test_saved_page_initial_and_after_a_move`, `::test_served_document_initial_and_after_a_move`, `::test_yrescale_panels_differ` (`range_probe`'s `_RANGES_JS` reports every model with ranges and renderers, chrome cells included: `assert 101 == 100`; and `_MOVE_TIMED_JS` waits for every plot's y range to agree, which a chrome cell's fixed 0-1 range never does. 28-19 fixes both in `range_probe.py`, so these five nodes are not edited) |

Not measurable at `c96facd` (the files do not exist yet) and re-measured by 28-11 on the batch-10 base: `test/test_canvas_tex.py::TestTheServedApp::test_make_document_runs_the_pass_after_the_panels_and_before_the_widgets` (S09: its anchor `fig.title.text = (f'{_own}` is the generated join this section deletes; flipped in 28-22), and the by() nodes of S15's `test_scheme_chrome.py`, S19's `test_series_labels.py`, S20's `test_value_lists.py` (flipped in 28-20), S21's `test_default_axes.py`, S18's `test_axis_format_fallback.py` and S27's `test_bar_range_geometry.py` (flipped in 28-21). S21's `test_default_axes_chrome.py` reads `range_probe`, which 28-19 teaches the chrome cells, so it needs no flip.

Certification scripts: `test/test_help_claims_5.cscript` HC5-07 (:388-426) pins `Domestic / 3` on the saved page (flipped, 28-24). HC5-06 (:385) reads twoway's `(missing)` only and stays. `test_by_suboptions.cscript` BYS-01..06 name `rows()`, `holes()` and `compact` (S48's to flip) and stay. `test_json_escaping.cscript` JSE-29/46/69/71 assert storage and row counts of by() titles and stay.

### E11. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`)

| Symbol | Edit | Risk |
|---|---|---|
| `DashRenderer._build_sources_and_figures` | label call, chrome attach, second pass call | CRITICAL (14 impacted, 2 direct, 7 processes): warn |
| `_dash_parse_by` | one branch for the text sub-options | CRITICAL (32, 9 direct, 16 processes): warn |
| `_dash_by_groups` | the missing test | CRITICAL (8, 2 direct, 12 processes): warn |
| `DashRenderer._expand_by_groups` | two frame lines | CRITICAL (8, 1 direct, 8 processes): warn |
| `_dash_layout_cell` | frame the grid | CRITICAL (10, 3 direct, 8 processes): warn |
| `DashRenderer._facet_label` | docstring only | CRITICAL (4, 1 direct, 9 processes): warn (no code change) |
| `ServerAppBuilder._generate_app_source` | the label call, chrome attach, frame lines, second pass call | HIGH (5, 1 direct, 3 processes): warn |
| `ServerAppBuilder._glyph_layer_lines` | ten names appended | HIGH (4, 1 direct, 4 processes): warn |
| `ServerAppBuilder._plan_by_groups` | one frame line | HIGH (5, 1 direct, 3 processes): warn |
| `_dash_facet_label` | `", "`, `(missing)` | LOW by graph (3), but called from the generated app (:35604) and copied by name: treat as MEDIUM |
| `_dash_text_annotations` | two keywords, the by() subtitle skip | LOW (3, 1 direct, 2 processes) |
| New: the ten functions of TR-28.10 and `_DASH_BY_TEXT_SPELLINGS` | added | no callers yet |
| Read only: `_dash_textbox_or_default`, `_dash_textbox`, `_dash_textbox_place` (S15), `_dash_figure_title`, `_dash_var_label`, `_dash_by_tokens`, `_textbox_split_point`, `_textbox_has_text`, `_dash_finish_graph_text` (S09) | — | — |

## User stories

- **US-28.1** As a twoway user, I want `scatter mpg weight, title("Mileage") by(foreign)` to keep `Mileage` above each panel and title the panels `Domestic` and `Foreign` on their own line, so my do-file's graph reads as Stata's does.
- **US-28.2** As a twoway user, I want `subtitle("S")`, `subtitle("S", prefix)`, `subtitle("S", suffix)` and `subtitle("")` outside by() to replace, extend or remove the panel labels as twoway's do, so I can relabel the panels the way I already do in Stata.
- **US-28.3** As a twoway user, I want `by(foreign rep78, missing)` panels titled `Domestic, 3` and `Foreign, (missing)`, so the labels match the graph a colleague made in Stata.
- **US-28.4** As a twoway user, I want a string by() variable's empty values left out of the panels and of the Total panel unless I give `missing`, and then shown as one `(missing)` panel, so the panels and counts are twoway's.
- **US-28.5** As a dashboard publisher, I want `by(, title() subtitle() note() caption())` drawn once over the panels and the `Graphs by <variable label>` note under them (removable with `by(, note(""))`), so a faceted dashboard explains itself as a Stata by() graph does.
- **US-28.6** As a dashboard publisher, I want the panel labels and the overall text the same on the saved page and in the served app, before and after a filter move, and stacked in reading order on a phone, so every reader sees the same graph.

## Business requirements

- **BR-28.1** Every by() panel is labelled with its value's text on a row of its own, centred and not bold, below the graph's own `title()`, which every panel keeps; the graph's title text never contains the label.
- **BR-28.2** A graph-level `subtitle()` combines with the panel label as twoway's does: its text replaces the label, `prefix` puts it before, `suffix` after, `""` removes the label, and sub-options alone keep the label (named where dash cannot draw them, once per graph).
- **BR-28.3** Several by() variables give `A, B[, C]`; a missing value gives `(missing)` in its place; date panels keep dash's date text (A53).
- **BR-28.4** A string by() value `""` is missing: without `missing` its rows are in no panel and not in Total; with `missing` they form one `(missing)` panel, placed first, and are in Total.
- **BR-28.5** `title()`, `subtitle()`, `note()` and `caption()` inside by(), with Stata's abbreviations `ti`, `sub`, `note`, `cap`, are drawn once over the whole panel array in the scheme's styles and positions, and are no longer named as ignored; repeated forms merge as twoway's do.
- **BR-28.6** The note `Graphs by <list>` is drawn under every by() graph: the list is twoway's (`label`, `A and B`, `name, B, and C`, each a variable label unless it is `""`, then the name); `by(, note(""))` removes it; `prefix`, `suffix` and sub-option-only forms behave as twoway's.
- **BR-28.7** `note()` and `caption()` outside by() are still drawn on every panel.
- **BR-28.8** Both modes draw the same labels and overall text, before and after a filter move; below the stacking width they stack head, panels, foot, with no sideways scroll; the grid's save button still saves the whole grid, now with its overall text.
- **BR-28.9** Capitalised by() sub-options (`TITLE()`) are not drawn: they stay named until S48 refuses them as twoway does.

## Technical requirements

- **TR-28.1 Missing by() values, both modes.** Add directly above `_dash_by_groups` (def 3436):
  - `_dash_by_value_missing(val) -> bool`: `True` for a `str` equal to `""`; for any other value `bool(pd.isna(val))` inside `try`, `False` on `TypeError`/`ValueError` (a non-scalar). Never raises. A string of blanks is not missing (Stata's `missing()`).
  - `_dash_by_nonmissing(df, by_vars) -> DataFrame`: the rows of `df` in which no variable of `by_vars` is missing in that sense, as `markout …, strok` keeps them: start from `pd.Series(True, index=df.index)`; per variable `keep &= col.notna()`, and for a column that is not numeric (`not pd.api.types.is_numeric_dtype(col)`) also `keep &= ~col.astype(object).eq("")`; return `df[keep]`. Vectorised, linear in rows x variables; a variable not in `df` is skipped (callers pass the valid ones).
  - Replace the five frame lines of E3 with it: saved :29986 `work_df = _dash_by_nonmissing(work_df, valid_vars)`, :30029 `t_df = _dash_by_nonmissing(t_df, valid_vars)`; `_plan_by_groups` :33898 `work = g_df if bmissing else _dash_by_nonmissing(g_df, by_vars)`; template :35569 and :35580 likewise (generated text).
  - In `_dash_by_groups` (:3459): `any(_dash_by_value_missing(v) for v in vals)` in place of `any(pd.isna(v) for v in vals)`.
  - Do not touch `GlyphMapper._mlabel_missing` (def 9634): an empty marker label is a label with no text, a different rule.
- **TR-28.2 The label text.** In `_dash_facet_label` (def 20107), the loop tests missing first: `if _dash_by_value_missing(val) or (not isinstance(val, str) and GlyphMapper._mlabel_missing(val)): parts.append("(missing)")`, then the string branch, then dates and numbers as today; return `", ".join(parts)`. Rewrite the docstring's twoway paragraph (twoway's rule now; the date difference kept, A53) and the Returns example (`"Domestic, 3"`). In `DashRenderer._facet_label` (def 30049) change only the docstring's example to `"Domestic, 3"`. The `"Total"` label (:30035, template `('Total', _t_df, None)`) is twoway's and stays.
- **TR-28.3 The text sub-options.** After `_DASH_BY_RESCALE_KEYS` (:19872) add the constant `_DASH_BY_TEXT_SPELLINGS = {"title": ("ti", "tit", "titl", "title"), "subtitle": ("sub", "subt", "subti", "subtit", "subtitl", "subtitle"), "note": ("note",), "caption": ("cap", "capt", "capti", "captio", "caption")}` with a comment citing probes a06, a12, a14, a15 (lower case only; `TITLE()` is refused by twoway and stays named until S48). After `_dash_by_rescale` (def 20025) add:
  - `_dash_by_text_key(tok) -> str | None`: for a token from `_dash_by_tokens` that contains `(` and ends with `)`, the key of `_DASH_BY_TEXT_SPELLINGS` whose tuple holds `tok.split("(", 1)[0].strip()` compared case-sensitively; else `None`.
  - `_dash_by_text_options(by_raw) -> dict`: `{"title", "subtitle", "note", "caption"}` each the merged raw value (`""` when not given), read from the sub-options after the first comma of `by_raw` through `_dash_by_tokens`. For each token with a key, `arg = tok[tok.index("(") + 1:-1]`; `cut = _textbox_split_point(arg)`; the text part is `arg[:cut]` (all of `arg` when `cut < 0`) and the sub-option part `arg[cut + 1:].strip()`. The merged text is the text part of the LAST occurrence for which `_textbox_has_text(text_part)` is true (a typed `""` counts); the merged sub-options are every occurrence's sub-option parts, in order, joined by one blank. The raw value is `text + (", " + subs if subs else "")`. Total; never raises; one pass.
  - `_dash_parse_by`: one new branch before the `style` branch (:20004): `elif _dash_by_text_key(tok) is not None: pass` with a comment "drawn by `_dash_by_chrome` (WP-30 P1.15a)". Its 5-tuple and every other branch are unchanged; its docstring's "dash implements three" paragraph names the text sub-options as drawn. A capitalised or bare form (`TITLE("X")`, `title`) is still named.
- **TR-28.4 The note's list.** After `_dash_by_text_options` add `_dash_by_note_list(by_vars, var_labels) -> str`: `[]` → `""`; one → `_dash_var_label(var_labels, v)`; two → `"%s and %s"`; three or more → the first variable's NAME, then `", " + _dash_var_label(…)` for each middle one, then `", and " + _dash_var_label(…)` for the last (SetByList, E6, D-28d). Labels are used as given (blanks kept: probe NB).
- **TR-28.5 `_dash_text_annotations` (S15's form) gains** keyword-only `defaults=None` and `sides=None`:
  - when `str((graph_opts or {}).get("by") or "").strip()` is non-blank the `"subtitle"` box is skipped: the panel label consumes it (TR-28.6). `note` and `caption` are drawn as today (probe a01);
  - with `sides`, each box's side is computed first (S15's `_dash_textbox_place` with the scheme's clock and justification, or `_DASH_TEXTBOX_DEFAULTS` without a scheme) and a box whose side is not in `sides` is skipped before its text is parsed;
  - with `defaults` holding the box's key, an empty raw value is not skipped and the text is `_dash_textbox_or_default(raw, ann_key, defaults[ann_key], seen, key)`; every other box keeps `_dash_textbox`.
  Both existing callers (saved :30400, served :35261) pass neither keyword. Docstring: the two keywords, the by() rule and its twoway truth (r01, a01).
- **TR-28.6 The panel label.** After `_dash_text_annotations` add `_dash_by_panel_label(fig, label, graph_opts, scheme=None, seen=None, key="") -> Title | None`:
  - `text, opts = _dash_textbox_or_default((graph_opts or {}).get("subtitle", ""), "subtitle", label, seen, key)` (twoway's replace/prefix/suffix/`""` rules, E6 r01, r02, p15, p16, p17); `None` when `text` is `""`;
  - `side, align = _dash_textbox_place(scheme.text_clock["subtitle"], scheme.text_just["subheading"])` with a scheme, else `("above", "center")`;
  - `Title(name="dash_by_label", text=text, align=align, text_font_style="normal", text_font_size=<_textbox_size(opts, None) as "Npx", else scheme.subheading_font_size, else "13px">, text_color=<_textbox_color(opts, None), else scheme.subheading_color, else "#444444">)`, added with `fig.add_layout(title, side)`; no fill (D-28e). Returns the Title.
  - Saved: replace :31655-31656 with `_dash_by_panel_label(fig, label, g.get("graph_options", {}), self.scheme, getattr(self, "_reported_subopts", None), name)`.
  - Served: replace the generated lines :35513-35520 (the `if _fac_label is not None:` block) with a two-line comment and `_dash_by_panel_label(fig, _fac_label, go, _DASH_SCHEME, _reported_subopts, go.get('name', '') or gname)`, so a refused sub-option is named for the graph, not per panel (as `_dash_note_hover_unreached` is, :35500-35505).
- **TR-28.7 The overall text (D-28a, D-28b).** After `_dash_by_panel_label` add:
  - `_dash_by_text_cell(scheme, name)`: the E9 cell, a bare `bokeh.models.Plot` (local import; D-28a: never a `figure`) built as `Plot(name=name, frame_height=1, height_policy="fit", width_policy="max", toolbar_location=None, outline_line_color=None, min_border=0, x_range=Range1d(0, 1), y_range=Range1d(0, 1))`: no axis, grid or tool exists on it; `scheme.apply_to_figure(cell)` when a scheme is given (measured on a bare Plot: it styles the title and fills and touches no axis); then `cell.outline_line_color = None`, `cell.background_fill_color = cell.border_fill_color`, and `cell.add_layout(Span(location=0, dimension="width", visible=False, name="dash_by_anchor"))` (E9: Bokeh's W-1000 otherwise).
  - `_dash_by_chrome(graph_opts, by_vars, var_labels, scheme=None, seen=None, key="") -> dict`: `o = _dash_by_text_options(graph_opts.get("by"))`; `boxes = {"subtitle": o["subtitle"], "note": o["note"], "caption": o["caption"]}`; `defaults = {"note": "Graphs by " + _dash_by_note_list(by_vars, var_labels)}`. The head cell (`"dash_by_head"`): when `o["title"]`, `cell.title.text` is `_dash_textbox(o["title"], "title", seen, key)[0]` and `_dash_figure_title(cell, {"title": o["title"]}, seen, key)` styles it; then `_dash_text_annotations(cell, boxes, seen, key, scheme, defaults=defaults, sides=("above",))`. The foot cell (`"dash_by_foot"`): `_dash_text_annotations(cell, boxes, seen, key, scheme, defaults=defaults, sides=("below",))`. A cell that holds no text (an empty `title.text` and no `Title` or `Label` but the anchor `Span`) is returned as `None`. Returns `{"head": …, "foot": …}`. Under economist the note's clock puts it above, in the title's band (S15's rule), so it lands in the head cell.
  - `_dash_by_frame_grid(grid, chrome, ncols) -> grid`: no-op without `chrome`; otherwise `grid.children` becomes `[(head, 0, 0, 1, ncols)]` (when head), then every existing child with its row increased by 1 when there is a head (tuples of 3 or 5 kept), then `(foot, last_row + 1 + offset, 0, 1, ncols)` (when foot). Total for an empty grid. Docstring: E9's measurements; S48 calls it after placing the panels.
  - `_dash_by_chrome_figures(figures, facet_map) -> dict`: for each name of `facet_map`, the first panel key present in `figures`; when that figure carries `_dash_by_chrome`, `{f"{name}__by__head": head, f"{name}__by__foot": foot}` for those that are not `None`.
  - Saved build: in the facet branch of "3. Build figures", after `_dash_share_by_scales(…)` (:31669-31671), compute `_bv = [v for v in _dash_parse_by(str(g.get("graph_options", {}).get("by", "") or ""), warn=False)[0].split() if v in self.df.columns]` and set `self.figures[<first present panel key>]._dash_by_chrome = _dash_by_chrome(g.get("graph_options", {}), _bv, self.variable_labels, self.scheme, getattr(self, "_reported_subopts", None), name)`.
  - Served build: after the generated `_dash_share_by_scales([figures[_f] for _f, _ in _entries` lines (:35653-35654), the same with `go`, `by_vars`, the make_document `var_labels` (:34770), `_DASH_SCHEME`, `_reported_subopts`, `gname`.
  - `_dash_layout_cell` (:25020): `grid = gridplot(rows, sizing_mode="stretch_width")`, then `_dash_by_frame_grid(grid, getattr(figs[0], "_dash_by_chrome", None), cn)`, then `return _dash_name_save(_dash_reflow(grid))`. Signature and callers unchanged.
  - The canvas-text pass: directly after S09's saved call `_dash_finish_graph_text(self.figures)` (TR-09.6) add `_dash_finish_graph_text(_dash_by_chrome_figures(self.figures, self._facet_map))`; directly after S09's generated `"    _dash_finish_graph_text(figures)",` (TR-09.7) add `"    _dash_finish_graph_text(_dash_by_chrome_figures(figures, _facet_map))",`. `_dash_finish_graph_text` itself is not edited (S29's).
- **TR-28.8 Served copy list** (R2 row S28, append only, X.1): in `_glyph_layer_lines`' functions tuple, on new lines directly after `"_dash_facet_label", "_dash_stata_date_text",` (:33201): the comment `# by() panel labels and overall text (WP-30 P1.15a).` and `"_dash_by_value_missing", "_dash_by_nonmissing",`, `"_dash_by_text_key", "_dash_by_text_options", "_dash_by_note_list",`, `"_dash_by_panel_label", "_dash_by_text_cell", "_dash_by_chrome",`, `"_dash_by_frame_grid", "_dash_by_chrome_figures",`. `_DASH_BY_TEXT_SPELLINGS` reaches the app through `_supply_missing_constants` (E8); no constants-tuple entry. `_dash_by_groups`, `_dash_facet_label`, `_dash_parse_by`, `_dash_layout_cell` and `_dash_text_annotations` are already copied and change in place.
- **TR-28.9 No JavaScript twin.** No page script reads or writes a panel label or a chrome cell: they are static canvas text, built before the document is serialised, and are in no `CustomJS`'s `args`. The saved filter move rebuilds sources and view filters only; the served move recomputes sources only (`make_document` builds chrome once per session). `_FILTER_JS` and every callback are not edited. A guard test checks both (TestAfterAFilterMove).
- **TR-28.10 Registries.** Under S01's anchor `# WP-30 S28 (P1.15a): by() panel labels and overall text (P1.15 part a)` in `test/function_test_map.py` `FUNCTIONS`, alphabetically: `_dash_by_chrome`, `_dash_by_chrome_figures`, `_dash_by_frame_grid`, `_dash_by_nonmissing`, `_dash_by_note_list`, `_dash_by_panel_label`, `_dash_by_text_cell`, `_dash_by_text_key`, `_dash_by_text_options`, `_dash_by_value_missing`, each mapped to its unit test in `test/test_by_text.py` (TDD stubs). The entries of the edited functions stay. `test/program_coverage_map.py`: no change (no Stata program is added or edited).
- **TR-28.11 Help** (R3, D-28f): see 28-25.
- **TR-28.12 Tracking** (R4, R5): close `P1.15a` in place in BUGS.md, delete its `WP30_OPEN` line, and replace `<!-- WP-30 P1.15a -->` in place under `### Results that change`. The texts are in 28-26.
- **TR-28.13 Security (rule 1).**
  - Every new text (labels, by() text options, the note's variable labels) reaches only `Title.text`/`Label.text`, canvas text that BokehJS draws with `fillText`: no new HTML or DOM sink. The sinks are registered in `test_label_sinks.py` (TestTextSinks: carried raw; S09's pass makes TeX inert on them; S29 later translates SMCL).
  - No user text is used as a model name, property name, regex or code: the Title and cell names are constants (`dash_by_label`, `dash_by_head`, `dash_by_foot`, `dash_by_anchor`); `_dash_by_text_key` compares a token's leading word with a constant table.
  - The varlist check (`_DASH_UNSAFE_BY`, Stata names) is unchanged; the sub-options stay text. `_dash_by_tokens` is linear (TestTheSubOptionSplitterReadsStataQuotes: 400,000 quotes under 2 s); `_dash_by_text_options` and `_dash_by_nonmissing` are single passes; a test bounds `_dash_by_text_options` on a 1 MB by() string under 2 s.
  - Echoed text is the existing `_dash_textbox` note (sub-option tokens as typed); no new echo. No `shell=True`, `eval`, `exec` or file access is added; the extractor's Python block reads files only, never calls Stata (D12).

## Boundaries

- **Batch partners (10).**
  - S29 owns `_dash_finish_graph_text`, `_dash_graph_text_models`, `_dash_graph_text_props`, `_dash_finish_text_value` (S09's pass, which it extends), `_dash_graph_text` and its tables, `_apply_mlabel_opts`, `_mlabel_column_kind`, `scripts/svg_truth.py`'s sibling reader, `graph_text_truth.json` and the help's "Text in graphs". S28 calls the pass on its chrome cells and edits none of them. Contract for S29: S28's texts are raw (SMCL untranslated), its chrome cells reach the pass under keys `<name>__by__head` and `<name>__by__foot` (so `key.split("__by__")[0]` is the graph), and its label `Title`s sit in each panel's `fig.above`/`fig.below`, where the pass walks.
  - S30 owns `OptionTranslator.stata_colour`, `translate_mcolor`, `parse_color_alpha`, `SchemeParser._color`/`_color_alpha`/`foreground_color`, `scripts/extract_scheme_truth.py`, the 26 scheme files and `scheme_truth.json` (batch 10's regenerator, A152). S28 reads colours only through `_textbox_color` and the scheme's existing attributes, and adds no scheme key (D-28e).
- **Later sections (do not do their part).**
  - S48 (P1.15b): `rows()`, `cols()`, `holes()`, `colfirst` positions (`_dash_by_positions` in place of `_dash_facet_cols`), the refusals of P1.15.4 (including `TITLE()` and the other capitals, `YRESCALE`, two `style()`), `iscale()` (which scales the panel label, never the chrome cells), `imargin()`, `compact`, the whole-array size and the layout(bs) facet ratio, help :2104-2105. S48 keeps calling `_dash_by_frame_grid` after placing panels.
  - S53 (P1.15c): outer axes and edge labels, axis titles once, no axis-2 title per panel, one legend (`by(, legend())`, `ilegends`, the scheme's `by_legend_position`), one colour key under `by(, clegend(on))`, the scheme's `by_*` keys, stacking with every panel's axes, and the label's filled box (Q-28.1, assigned to S53 by ratification row 36, 06oct2026). S53 draws it behind the `dash_by_label` Title S28 creates, so S28 keeps that Title's name and adds no fill of its own (D-28e).
  - P2.4: `subtitle(, ring(0) pos(1))` moving the label inside the plot region, and `title(, position() ring())` for the overall text. P2.18: `.a`-`.z` as their own panels. P2.53 / IR-9: `by(, graphregion() plotregion())`.
- **Not edited:** `_make_figure_body`, `_build_filter_widgets`, `_FILTER_JS`, the four appliers, `_dash_share_by_scales`, `_dash_by_rescale`, `_dash_by_tokens`, `_dash_facet_cols`, `_dash_reflow`, `_dash_name_save`, `_dash_textbox`, `_dash_textbox_or_default`, `_dash_textbox_place`, `_dash_figure_title`, `GlyphMapper` (`_mlabel_missing` included), `SchemeParser`, `_dash_by_panel_dropped`, `_dash_total_spec`, dash.ado (its `_dash_by_panels` already marks out with `strok`), dash_parse.mata, the scheme files and every tracking document but BUGS.md and CHANGELOG.md (A145).
- **Kept as documented differences:** date panel titles (A53); a value label holding double quotes is one label line, where twoway splits it (A55, probe q04); a one-panel graph whose only label text is `""` (a value label of empty text) is drawn without panel chrome (Notes).

## Stata truth

### The fixture `test/fixtures/by_text_truth.json` and its extractor

**`scripts/extract_by_text_truth.do`** (new; in `scripts/extract_unlabelled_truth.do`'s shape as S02 converted it). It opens with a header comment (what, why, output, run line `DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_text_truth.do`), `clear all`, `set graphics off`, `set more off`, `set linesize 255`, `version 19`, S02's root stanza (TR-02.9) with `<file>` = `extract_by_text_truth.do`, then ``adopath ++ "`repo'/"``, `global dash_nobrowser 1`, ``global BT_REPO "`repo'"``, ``global BT_OUT "`repo'/test/fixtures/by_text_truth.json"``, a work directory `` `c(tmpdir)'dash_by_text_probe `` (`capture mkdir`) in `$BT_WORK`, and `set scheme stcolor`. The stamp: `c(stata_version)`, `c(born_date)`, `c(current_date) c(current_time)` and `git -C "$BT_REPO" rev-parse HEAD` written by `shell` into a tempfile and read back by `file read`, with the 40-hex check and `exit 498` of extract_unlabelled_truth.do:66-80.

**Data.** `sysuse auto, clear`; `generate str4 s = cond(foreign, "F", "")`; `replace s = "D" in 1/40`; `generate str1 e = ""`; `generate double u = foreign` (no value label) and `label variable u ""`; `generate double fb = foreign`, `label values fb origin`, `label variable fb "   "`. Saved once to `$BT_WORK/bt.dta`, reloaded before every probe, and exported once through dash's own writer: a `python:` block with `sys.path` holding `$BT_REPO` (read by `Macro.getGlobal`) runs `dash_render._dash_write_stata_data(<work>/data.json, ["mpg", "weight", "foreign", "rep78", "headroom", "s", "e", "u", "fb"])`.

**Per probe** (`bt <id> "<if>" "<options>"`, registered in a table, run in a loop): `use "$BT_WORK/bt.dta", clear`; `serset clear`; a text log `$BT_WORK/<id>.log` around `capture noisily twoway scatter mpg weight <if>, <options> name(Graph, replace)`; the rc. When rc is 0, a record file `$BT_WORK/<id>.rec` written with `file write` (pipe-separated): `.Graph.graphs.arrnels`, `.Graph.title.text[1]`, `.Graph.subtitle.text[1]`, `.Graph.note.text[1]`, `.Graph.note.text[2]`, `.Graph.caption.text[1]`, `.Graph.note.style.size.val`; then one line per panel k with `subtitle.text[1]`, `subtitle.text[2]`, `title.text[1]`, `note.text[1]`, `caption.text[1]` of `.Graph.graphs[k]`, and the panel's observations from `serset set <k-1>` then `serset` (`r(N)`; probe28c: sersets come in panel order, `by(s, total)` → 40, 22, 62); then `graph export "$BT_WORK/<id>.svg", name(Graph) replace`. Nothing is echoed with `display`.

**The probes** (39; every command `twoway scatter mpg weight`):

```stata
bt bp01 "" "by(foreign)"
bt bp02 "" `"title("T") by(foreign)"'
bt bp03 "" `"subtitle("S") by(foreign)"'
bt bp04 "" `"subtitle("S", prefix) by(foreign)"'
bt bp05 "" `"subtitle("Extra", suffix) by(foreign)"'
bt bp06 "" `"subtitle("") by(foreign)"'
bt bp07 "" "subtitle(, ring(0) pos(1) nobexpand) by(foreign)"
bt bp08 "" "by(foreign rep78)"
bt bp09 "" "by(rep78, missing)"
bt bp10 "" "by(foreign rep78 headroom)"
bt bp11 "" `"by(foreign, title("X") subtitle("S") note("N") caption("C"))"'
bt bp12 "" `"by(foreign, note(""))"'
bt bp13 "" `"by(foreign, note("My", suffix))"'
bt bp14 "" `"by(foreign, note("My", prefix))"'
bt bp15 "" "by(foreign, note(, size(large)))"
bt bp16 "" `"by(foreign, note("", suffix))"'
bt bp17 "" `"by(foreign, ti("X") sub("S") cap("C"))"'
bt bp18 "" `"by(foreign, note("A") note("B"))"'
bt bp19 "" `"by(foreign, note("A") note(, size(large)))"'
bt bp20 "" `"by(foreign, title("X") title("Y"))"'
bt bp21 "" `"note("N") caption("C") by(foreign)"'
bt bp22 "" `"subtitle("S") by(foreign, subtitle("O"))"'
bt bp23 "" `"title("T") by(foreign, title("X"))"'
bt bp24 "" "by(foreign, total)"
bt bp25 "if foreign == 1" "by(foreign)"
bt bp26 "" "by(foreign rep78, missing)"
bt bp27 "" "by(s)"
bt bp28 "" "by(s, total)"
bt bp29 "" "by(s, missing)"
bt bp30 "" "by(s, missing total)"
bt bp31 "" "by(e, missing)"
bt bp32 "" "by(e)"
bt bp33 "" "by(u)"
bt bp34 "" "by(fb)"
bt bp35 "" `"by(foreign, TITLE("X"))"'
bt bp36 "" `"by(foreign, title("X", ring(0)))"'
bt bp37 "" "by(foreign) scheme(economist)"
bt bp38 "" `"by(foreign, title("X") note("N")) scheme(economist)"'
bt bp39 "" `"by(foreign, title("X") subtitle("S") note("N") caption("C")) scheme(s2color)"'
```

Expected from the measurements of E6: bp32 rc 198 `nothing to graph`; bp35 rc 198 `option TITLE() not allowed`; every other rc 0. If any recorded value differs from E6, stop and report before writing tests on it.

**The trailing `python:` block** reads files only (never calls Stata; a backtick written `\x60`) and writes `json.dump(…, ensure_ascii=False, indent=1, sort_keys=True)`:
- `_meta`: `stata_version`, `born_date`, `dash_commit`, `extracted` (D12), `scheme` (`stcolor`, the default; bp37-bp39 name theirs), `probes` (39), `method` ("`.Graph` members per probe; panel observations from the sersets; texts from the SVG through scripts/svg_truth.py").
- `data`: the parsed `data.json`.
- `probes[<id>]`: `if`, `options`, `rc`, `message` (the last non-blank line of the log above `r(<rc>);`, or `""`), and when rc is 0: `n`, `overall` = `{"title", "subtitle", "note": [line1, line2 without empties], "caption", "note_size"}`, `panels` = list of `{"sub": [lines without empties], "title", "note", "caption", "n"}`, `svg` = every non-numeric text of the export (`scripts/svg_truth.py` `svg_texts`: `text`, `x`, `y`, `anchor`, `size`), and `canvas` (the viewBox width).

`git add -f test/fixtures/by_text_truth.json`. The fixture is named by `test/test_by_text.py::TestTheFixture` (which also names the extractor, as `test_fixtures_are_committed.py::test_every_do_file_is_named_by_another_script_or_test` requires). It is regenerated only by this extractor, never patched by hand (R7).

**Run:** `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/s28" "$WT/scripts/extract_by_text_truth.do"` (log `$S/s28/extract_by_text_truth.log`).

### The S28 block of `test/test_wp30_truth.cscript`

It replaces S01's stub body between `* ==== S28 P1.15a: … ====` and `* ==== end S28 ====`, keeping S01's header line as S01 wrote it (shown below in S01's form) and its gate lines and S01's case helpers (read their names first: `grep -n 'program define _w30\|w30_work' test/test_wp30_truth.cscript`; below they are `_w30_expect`, `_w30_done` and `` `w30_work' ``). One helper goes directly above the S28 header: `_s28_count` (declares `version 19`; `syntax using/, needle(string)`; Mata `fileread` of the file and `(strlen(s) - strlen(subinstr(s, n, "", .))) / strlen(n)` as test_help_claims_5.cscript:119 does; returns `r(n)`). The needle is passed through `st_local`, never expanded inside Mata source.

```stata
* ==== S28 P1.15a: by() panel labels and overall text ====
local only : env WP30_ONLY
if inlist("`only'", "", "S28") {
    display as text "S28 start " c(current_date) " " c(current_time)
    local q = char(34)

    // BP-01 (guard, the truth): twoway's labels, repeated title and note.
    sysuse auto, clear
    quietly twoway scatter mpg weight, title("T") by(foreign rep78, missing) name(Graph, replace)
    local s28l1 `"`.Graph.graphs[1].subtitle.text[1]'"'
    local s28l6 `"`.Graph.graphs[6].subtitle.text[1]'"'
    local s28t1 `"`.Graph.graphs[1].title.text[1]'"'
    local s28nt `"`.Graph.note.text[1]'"'
    _w30_expect BP-01 `"(`"`s28l1'"' == "Domestic, 1")"' `"panel 1 label `s28l1'"'
    _w30_expect BP-01 `"(`"`s28l6'"' == "Domestic, (missing)")"' `"panel 6 label `s28l6'"'
    _w30_expect BP-01 `"(`"`s28t1'"' == "T")"' `"panel title `s28t1'"'
    _w30_expect BP-01 `"(`"`s28nt'"' == "Graphs by Car origin and Repair record 1978")"' `"note `s28nt'"'
    _w30_done BP-01 "twoway labels Domestic, 1 under T and notes Graphs by"

    // BP-02: dash draws the same texts; no em-dash join, no slash join.
    quietly dash scatter mpg weight, title("T") by(foreign rep78, missing) saving("`w30_work'/s28a.html", replace)
    foreach t in "Domestic, 1" "Domestic, (missing)" "Foreign, (missing)" "Graphs by Car origin and Repair record 1978" {
        cert_file_has "`w30_work'/s28a.html", needle(`"`q'text`q':`q'`t'`q'"')
        _w30_expect BP-02 "(r(found) == 1)" `"the page lacks `t'"'
    }
    foreach t in "Domestic / 1" "/ Missing" {
        cert_file_has "`w30_work'/s28a.html", needle(`"`t'"')
        _w30_expect BP-02 "(r(found) == 0)" `"the page still holds `t'"'
    }
    _s28_count using "`w30_work'/s28a.html", needle("dash_by_label")
    _w30_expect BP-02 "(r(n) == 10)" "panel labels: `r(n)'"
    _w30_done BP-02 "dash labels every panel and draws the note as twoway does"

    // BP-03: a string "" is missing in the panels and in Total.
    sysuse auto, clear
    generate str4 s = cond(foreign, "F", "")
    replace s = "D" in 1/40
    quietly dash scatter mpg weight, by(s, total) saving("`w30_work'/s28b.html", replace)
    _s28_count using "`w30_work'/s28b.html", needle("dash_by_label")
    _w30_expect BP-03 "(r(n) == 3)" "panels: `r(n)' (twoway: D, F, Total)"
    cert_file_has "`w30_work'/s28b.html", needle(`"`q'text`q':`q'Graphs by s`q'"')
    _w30_expect BP-03 "(r(found) == 1)" "no Graphs by s note"
    _w30_done BP-03 "by(s, total) draws D, F and Total, as twoway does"

    // BP-04: every value "" and missing: one (missing) panel.
    generate str1 e = ""
    quietly dash scatter mpg weight, by(e, missing) saving("`w30_work'/s28c.html", replace)
    cert_file_has "`w30_work'/s28c.html", needle(`"`q'text`q':`q'(missing)`q'"')
    _w30_expect BP-04 "(r(found) == 1)" "no (missing) panel"
    capture dash scatter mpg weight, by(e) saving("`w30_work'/s28d.html", replace)
    _w30_expect BP-04 "(_rc == 198)" "by(e) rc `_rc' (twoway: nothing to graph, 198)"
    _w30_done BP-04 "a string by() variable of empty values is one (missing) panel, or nothing to graph"

    // BP-05: by(, title subtitle note caption) once, and not named.
    sysuse auto, clear
    local s28log "`w30_work'/s28e.log"
    quietly log using "`s28log'", text replace name(s28e)
    dash scatter mpg weight, by(foreign, title("X") subtitle("S") note("N") caption("C")) saving("`w30_work'/s28e.html", replace)
    quietly log close s28e
    foreach t in X S N C {
        _s28_count using "`w30_work'/s28e.html", needle(`"`q'text`q':`q'`t'`q'"')
        _w30_expect BP-05 "(r(n) == 1)" `"`t' drawn `r(n)' times"'
    }
    cert_log_has "`s28log'", needle("by() sub-option")
    _w30_expect BP-05 "(r(count) == 0)" "a by() text sub-option was named"
    _w30_done BP-05 "by()'s title, subtitle, note and caption are drawn once"

    // BP-06: note("") removes the note; subtitle("S", prefix) merges.
    quietly dash scatter mpg weight, subtitle("S", prefix) by(foreign, note("")) saving("`w30_work'/s28f.html", replace)
    cert_file_has "`w30_work'/s28f.html", needle("Graphs by")
    _w30_expect BP-06 "(r(found) == 0)" "note() did not remove the note"
    cert_file_has "`w30_work'/s28f.html", needle(`"`q'text`q':`q'S\nDomestic`q'"')
    _w30_expect BP-06 "(r(found) == 1)" "subtitle(S, prefix) did not lead the label"
    _w30_done BP-06 "note() removes the note and subtitle() merges with the label"

    // BP-07: three variables: twoway's note names the first by its name.
    quietly twoway scatter mpg weight, by(foreign rep78 headroom) name(Graph, replace)
    local s28n `"`.Graph.note.text[1]'"'
    quietly dash scatter mpg weight, by(foreign rep78 headroom) saving("`w30_work'/s28g.html", replace)
    cert_file_has "`w30_work'/s28g.html", needle(`"`q'text`q':`q'`s28n'`q'"')
    _w30_expect BP-07 "(r(found) == 1)" `"dash's note is not twoway's `s28n'"'
    _w30_done BP-07 "the three-variable note is twoway's text"

    // BP-08 (guard, until S48): TITLE() is refused by twoway and never drawn.
    capture twoway scatter mpg weight, by(foreign, TITLE("Xq"))
    _w30_expect BP-08 "(_rc == 198)" "twoway rc `_rc'"
    capture dash scatter mpg weight, by(foreign, TITLE("Xq")) saving("`w30_work'/s28h.html", replace)
    if _rc == 0 {
        cert_file_has "`w30_work'/s28h.html", needle(`"`q'text`q':`q'Xq`q'"')
        _w30_expect BP-08 "(r(found) == 0)" "TITLE() was drawn"
    }
    _w30_done BP-08 "a capitalised by() title is never drawn"

    capture graph drop _all
    foreach f in s28a s28b s28c s28d s28e s28f s28g s28h {
        capture erase "`w30_work'/`f'.html"
    }
    capture erase "`s28log'"
    display as text "S28 end " c(current_date) " " c(current_time)
}
* ==== end S28 ====
```

Each `.Graph` member is copied into a local before it is compared, as the research probes read them; if S01's `_w30_expect` takes its condition in another form, keep the locals and adapt only the call. The JSON writes a newline in `S\nDomestic` as the two characters `\n`, which is the needle. Expected on the unmodified tree, from E6 and E7 (28-04 records the measured lines): BP-01 and BP-08 pass; BP-02 to BP-07 fail. Run it alone: `WP30_ONLY=S28` through the driver (index "The cscript driver"); log `$S/s28/run_test_wp30_truth.log`.

### Area cscripts

- `test/test_help_claims_5.cscript` HC5-07 (:388-426) is flipped in place (28-24): the dash half's `foreach` pairs become `"foreign rep78|Domestic, 3|Domestic / 3"`, `"r2|Three|3.00"`, `"r2|4|4.00"`, `"d|01jan2000|14610.0"`, and its PASS text says `Domestic, 3`. Header line :30 likewise.
- Run, unchanged, through the driver: `test_help_claims_5.cscript`, `test_json_escaping.cscript` (JSE-29, JSE-46, JSE-69 and JSE-71 build by() titles holding quotes, `$` and backslashes; they assert storage and row counts, which the chrome cells hold none of), `test_by_suboptions.cscript` (BYS-01..06 name `rows()`/`holes()`/`compact`, not text options) and `test_parser.cscript` (P1A-84's `by(foreign, title("total"))` must not read `total`).

## TDD test stubs

New module `test/test_by_text.py` (docstring: the defect of the Overview, twoway's rule of E6, the design of D-28a/D-28b). Helpers come from `test_by_scales` (`_plot`, `_graph`, `_spec`, `SC`), `test_mode_parity` (`_fire`, `_widgets_of`), `test_served_filter_move._move`, `test_server_layer_defects.plot_for`, and the new `test/by_panel_probe.py`. Its own `_write(spec, frame)`/`_both(spec, frame)` build the saved renderer (`DashRenderer(...).render()`, then `r._last_layout_root`) and the served document (`ServerAppBuilder(...).build`, the module loaded, `make_document(Document())`), as `test_by_scales._served_doc` does, with `make_data_json` and the fixture's data or a hand-built frame. "Both modes" means a `@pytest.mark.parametrize("mode", ("saved", "served"))`.

**`test/by_panel_probe.py`** (new test helper module; no test of its own beyond its users; docstring says why it exists, critic correction 5):
- `panel_label(fig)`: the text of the first `Title` named `"dash_by_label"` in `fig.above + fig.below`, else `""`.
- `panel_label_title(fig)`: that `Title`, or `None`.
- `is_chrome(model)`: `getattr(model, "name", None) in ("dash_by_head", "dash_by_foot")`.
- `chrome_texts(cell)`: the text rows of a chrome cell in reading order: the outermost `above` row first (its `title`, then its `above` Titles from the last to the first), then its `below` Titles from the first to the last; each `Title`/`Label` text with `""` skipped.
- `by_grid(root)`: the one `GridPlot` under `root` whose non-chrome children are all panels; returns `(panels, head, foot)` with `panels = [(row, col, fig)]` re-based so the first panel row is 0, sorted by place.
- `find_panel(figs, label)`: the one figure whose `panel_label` is `label`; raises `AssertionError` naming the labels it saw otherwise.

### Regression tests (28-01: fail on the unmodified tree)

- Test: `by(s)` on a frame whose `s` is `D`, `F` or `""` draws 2 panels, labelled `D` and `F`, both modes — `test/test_by_text.py::TestAStringMissingPanel::test_without_missing_the_empty_group_is_left_out[saved|served]`. Fails now: 3 panels.
- Test: `by(s, total)`'s Total panel holds the rows whose `s` is not `""` (62 of 74 on the fixture frame; a hand frame: 60 of 74), both modes — `…::TestAStringMissingPanel::test_the_total_panel_leaves_out_the_empty_group[…]`. Fails now: 74.
- Test: `by(s, missing)` labels its first panel `(missing)`; `by(e, missing)` with every `e` empty draws one panel labelled `(missing)` and the foot note `Graphs by e` — `…::test_with_missing_the_empty_group_is_one_missing_panel[…]`. Fails now: label `""`; one plain figure.
- Test: `ServerAppBuilder._plan_by_groups` counts `by(s)` as 2 groups under `$dash_max_by_groups` 2 (no over-limit note) — `…::TestAStringMissingPanel::test_the_build_time_count_leaves_it_out`. Fails now: 3 groups, the limit note.
- Test: `title("T") by(foreign)`: every panel's `fig.title.text` is `T` and its `panel_label` is `Domestic`/`Foreign`; no `Title.text` in the document contains `—` — `…::TestThePanelLabelIsItsOwnRow::test_the_title_stays_and_the_label_is_a_row[…]`. Fails now: `T — Domestic`, no label row.
- Test: the label `Title` is `text_font_style == "normal"`, `align == "center"` (stcolor) and sits in `fig.above` — `…::TestThePanelLabelIsItsOwnRow::test_the_label_row_is_centred_and_not_bold[…]`.
- Test: `subtitle("S")`, `subtitle("S", prefix)`, `subtitle("Extra", suffix)`, `subtitle("")` and `subtitle(, ring(0) pos(1) nobexpand)` give labels `S`, `S\nDomestic`, `Domestic\nExtra`, none, `Domestic` (r01, r02, p16, p15, p17), no separate subtitle row on any panel, and the last names `ring(0) pos(1) nobexpand` once — `…::TestTheSubtitleMergesWithTheLabel::test_each_form[…-<form>]`. Fails now: label unchanged, an extra `S` row.
- Test: `by(foreign rep, missing)` on a frame with a missing `rep` labels `Domestic, 3` … `Foreign, (missing)` — `…::TestCompositeAndMissingLabels::test_two_variables[…]`. Fails now: `Domestic / 3`, `Foreign / Missing`.
- Test: `by(foreign, title("X") subtitle("S") note("N") caption("C"))`: the head cell reads `["X", "S"]`, the foot `["N", "C"]`, and no `by() sub-option` note is raised — `…::TestTheOverallText::test_by_title_subtitle_note_caption[…]`. Fails now: no cells, the note names all four.
- Test: the default note: `by(foreign)` → `Graphs by Car origin`; `by(foreign rep)` → `Graphs by Car origin and Repair record 1978`; `by(foreign rep headroom)` → `Graphs by foreign, Repair record 1978, and Headroom (in.)`; an unlabelled `u` → `Graphs by u`; `by(foreign, note(""))` → no foot cell — `…::TestTheOverallText::test_the_graphs_by_note[…-<case>]`. Fails now: no note.
- Test: `note("N") caption("C") by(foreign)` still draws `N` and `C` on each panel and the foot reads `Graphs by Car origin` (a01) — `…::TestTheOverallText::test_a_graph_note_stays_on_each_panel[…]`. Fails now: no foot.
- Test: `by(foreign, TITLE("Xq"))` draws no `Xq` anywhere and its note still names `TITLE("Xq")` (guard until S48) — `…::TestTheOverallText::test_a_capitalised_title_is_not_drawn[…]`.
- Test: the panel grid holds the head cell at `(0, 0, 1, ncols)` and the foot at `(last + 1, 0, 1, ncols)`, the panels in between; the grid toolbar holds exactly one `SaveTool`; under `layout(bs)` its `filename` is `g1` — `…::TestTheGrid::test_cells_and_the_save_tool[…]`. Fails now: no cells.
- Test: a by() page's build logs no `W-1000` (`caplog` on `bokeh.core.validation`) — `…::TestTheGrid::test_no_missing_renderers_warning[…]`.
- Test: after a served filter move (`_move(doc, "Select", "Foreign")` on `filter(foreign, type(dropdown))`) and after `_fire` on a range, every `panel_label` and every `chrome_texts` is unchanged; on the saved page no `CustomJS.args` value is (or holds) a label `Title` or a chrome cell, and no `CustomJS.code` holds `dash_by_` — `…::TestAfterAFilterMove::test_the_text_is_unchanged[…]`.

### Fixture-driven tests (28-03: fail on the unmodified renderer, except where marked guard)

- Test: the fixture has `_meta` keys `stata_version`, `born_date`, `dash_commit`, `extracted`; 39 probes; names `scripts/extract_by_text_truth.do` in its docstring — `…::TestTheFixture::test_meta_and_probes` (guard).
- Test: for every probe with rc 0, dash's panel count, each panel's label (`"\n".join(sub)`), graph title, note and caption, in panel order, equal twoway's — `…::TestPanelsMatchTwoway::test_labels[<probe>-saved|served]`.
- Test: for bp24, bp28 and bp30, each panel's drawn rows equal twoway's serset `n` — `…::TestPanelsMatchTwoway::test_rows[<probe>-…]`.
- Test: for every probe with rc 0, the head cell's texts equal `[overall title, overall subtitle]` without empties and the foot's `note` lines joined by `\n` then `caption` — `…::TestOverallTextMatchesTwoway::test_texts[<probe>-…]`.
- Test: bp15 and bp19's foot note is drawn at `size(large)`'s size (`_textbox_size({"size": "large"}, None)`), other probes at the scheme's note size — `…::TestOverallTextMatchesTwoway::test_note_size[…]`.
- Test: under economist (bp37, bp38) and s2color (bp39), the label's `align` and each overall text's side and `align` match the SVG's `anchor` (`start` left, `middle` center, `end` right) and its y above or below the panels — `…::TestPlacementMatchesTwoway::test_sides_and_alignment[<probe>-…]`.
- Test: bp32's rc 198 is dash.ado's too (pytest reads the fixture; the BP-04 cscript case runs dash) — `…::TestPanelsMatchTwoway::test_an_all_missing_by_is_nothing_to_graph` (guard on the fixture).

### Unit tests (one per new function; `test/function_test_map.py` names these)

- `_dash_by_value_missing` — `…::TestTheMissingRule::test_values`: `""` True; `" "` False; `None`, `float("nan")`, `pd.NaT`, `np.nan` True; `0`, `"D"`, `[1]` False; never raises.
- `_dash_by_nonmissing` — `…::TestTheMissingRule::test_frames`: a numeric NaN row and a string `""` row are dropped, a `" "` row kept, an all-missing frame gives zero rows with its columns; 200,000 rows under 1 s.
- `_dash_by_text_key` — `…::TestTheTextOptions::test_keys`: `ti("X")` title, `sub("S")` subtitle, `note("N")` note, `no("N")` None, `cap("C")` caption, `TITLE("X")` None, `title` (no parens) None, `t("X")` None.
- `_dash_by_text_options` — `…::TestTheTextOptions::test_merge`: a07 `B`, a08 `"A", size(large)`, a13 `Y`, `note("")` → `""` text given, a compound-quoted `title(\`"a "b" c"')` kept whole, `title(Bob's cars) cols(2)` → `Bob's cars`; and `…::test_a_megabyte_is_read_at_once` (1 MB of `title("x") ` under 2 s).
- `_dash_by_note_list` — `…::TestTheNoteList::test_lists`: `[]` `""`; one labelled; one unlabelled (`""` label → name); a label of blanks kept; two; three (first by name).
- `_dash_by_panel_label` — `…::TestThePanelLabel::test_unit`: text `""` returns None and adds nothing; `size(large) color(red)` styles it; without a scheme `13px` `#444444`; the Title is named `dash_by_label`.
- `_dash_by_text_cell` — `…::TestTheChromeCells::test_a_cell_draws_no_frame_and_no_warning`: `type(cell).__name__ == "Plot"` (never `figure`), no axis or grid, `toolbar_location is None`, no tools, one invisible `Span`, the scheme's graph-region colour, no `W-1000` on `file_html`.
- `_dash_by_chrome` — `…::TestTheChromeCells::test_head_and_foot`: p11's four texts split head/foot; `note("")` and no title/subtitle/caption give `{"head": None, "foot": None}`; economist's note goes to the head.
- `_dash_by_frame_grid` — `…::TestTheChromeCells::test_frame_grid_positions`: head only, foot only, both, neither, an empty grid; 3- and 5-tuples kept.
- `_dash_by_chrome_figures` — `…::TestTheChromeCells::test_the_pass_sees_the_cells`: keys `g1__by__head`/`g1__by__foot`, none for a graph without cells; and in both modes a TeX pair in `by(, title("\(t\)"))` reaches the head cell inert (S09's pass ran on it).

### Pinned tests to flip (R9; measured list in E10, re-measured by 28-11)

Every flip edits the assertion in place, keeps the test's name, and adds a docstring or comment line `Flipped (WP-30 P1.15a): <old expectation> was wrong because <twoway's measured rule>`. The groups: panel identity by `fig.title.text` → `by_panel_probe.panel_label`; `" / "` → `", "`; `"Missing"` → `"(missing)"`; `"T — label"` → title `T` plus label; a by() text sub-option named as ignored → drawn, not named; the served figure list that now includes chrome cells → panels only (`is_chrome`); GridPlot children unpacked as 3-tuples → `by_grid`.

### Browser (28-23; headless Chrome, skips without it, as `test_by_scales_chrome.py` does)

`test/test_by_text_browser.py`:
- Test: the saved page and the served document (`file_html` of `doc.roots`) of `title("T") by(foreign rep78, total title("X") note("N"))` on the fixture's data at 900 px: the head canvas is above every panel canvas, the foot below, both as wide as the grid — `::TestInChrome::test_the_cells_frame_the_panels[saved|served]`.
- Test: at 375 px they stack head, panels, foot, top to bottom, and `scrollWidth == 375` — `::TestInChrome::test_stacked_in_reading_order[…]`.
The rectangles come from `responsive_probe.measure_many` with its `PROBE_JS` widened through `monkeypatch.setattr` to report every canvas rect of at least 20 x 20 px (E9's prototype form); `responsive_probe.py` is not edited.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Missing rule, frames, groups, build-time count | pytest `TestTheMissingRule`, `TestAStringMissingPanel` | hand frames; `by_text_truth.json` | yes |
| Labels, composite and missing text, subtitle merge | pytest `TestThePanelLabelIsItsOwnRow`, `TestTheSubtitleMergesWithTheLabel`, `TestCompositeAndMissingLabels`, `TestPanelsMatchTwoway` | `by_text_truth.json` (bp01-bp36) | yes |
| Overall text, note list, merging, sizes, placement | pytest `TestTheOverallText`, `TestTheTextOptions`, `TestTheNoteList`, `TestOverallTextMatchesTwoway`, `TestPlacementMatchesTwoway` | bp11-bp23, bp37-bp39 | yes |
| Grid cells, save tool, W-1000 | pytest `TestTheGrid`, `TestTheChromeCells` | inline | yes |
| After a filter move | pytest `TestAfterAFilterMove` | inline | yes (saved: callbacks never touch the text) |
| Parity | `test_mode_parity.py` with 2 new CORPUS cases and the chrome profile in `_layout_tree` (28-22) | inline | yes |
| Sinks (rule 1) | `test_label_sinks.py` new `Sink` rows (28-22) | inline | yes |
| Copy lists | `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` | — | served |
| Browser drawing and stacking | `test_by_text_browser.py` | inline | yes |
| twoway against dash in Stata | `test_wp30_truth.cscript` BP-01..BP-08 | live | saved (served covered by pytest) |
| Area cscripts | `test_help_claims_5.cscript` (HC5-07 flipped), `test_json_escaping.cscript`, `test_by_suboptions.cscript`, `test_parser.cscript` | live | saved |
| Registries, tracking | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | — |

**Acceptance criteria.**
- **AC-28.1** For every fixture probe with rc 0, both modes' panel count, labels, per-panel title, note and caption, head texts and foot texts equal twoway's (`TestPanelsMatchTwoway`, `TestOverallTextMatchesTwoway`); bp24, bp28 and bp30's panel rows equal twoway's serset counts.
- **AC-28.2** No `Title.text` of either document contains an em dash (U+2014) or `" / "` from a panel label; every panel keeps the graph's `title()` text unchanged.
- **AC-28.3** `by(, title() subtitle() note() caption())` (and `ti`/`sub`/`cap`) raise no `by() sub-option` note; `TITLE()` is still named and never drawn.
- **AC-28.4** The grid holds one `SaveTool`; under `layout(bs)` it saves `<name>.png`; no `W-1000` is logged.
- **AC-28.5** After a served move and on the saved page's callbacks, labels and overall text are unchanged (`TestAfterAFilterMove`).
- **AC-28.6** In Chrome, both modes draw head above and foot below the panels at 900 px and stack them in reading order at 375 px with no sideways scroll.
- **AC-28.7** BP-01 to BP-08 print PASS (`WP30_ONLY=S28`); HC5-07 passes flipped; `test_json_escaping`, `test_by_suboptions` and `test_parser` pass unchanged.
- **AC-28.8** `test_mode_parity.py` passes with the two new cases; `test_label_sinks.py` passes with the five new sinks in both modes.
- **AC-28.9** The ten new functions are mapped and copied; the full suite is green once through the queue.

## Tasks

**Commit boundary.** Tasks 28-01 to 28-26 form the one commit of entry `P1.15a`, made by 28-26 on `wp30-s28` with the subject `Draw by() panel labels and overall text as twoway does (WP-30 P1.15a)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s28`; every command uses `git -C "$WT"` or `$WT` paths, never the main checkout's tree (the plan files are read from the main checkout, which governs). Stata runs only through `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh` (E5). Before the first edit of each CRITICAL or HIGH symbol (`_build_sources_and_figures`, `_dash_parse_by`, `_dash_by_groups`, `_expand_by_groups`, `_dash_layout_cell`, `_plan_by_groups`, `_generate_app_source`, `_glyph_layer_lines`) the executor confirms that `$S/batch-10-impact.txt` records the maintainer's approval (E4); a symbol missing from it is run with `gitnexus impact <symbol> -d upstream -r dash` in the main checkout and reported before editing.

<task type="auto" id="28-01">
  <name>Write the failing regression tests</name>
  <files>test/by_panel_probe.py, test/test_by_text.py</files>
  <action><![CDATA[Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-10-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s28`; stop otherwise. Create `test/by_panel_probe.py` with the six helpers of "TDD test stubs" (module docstring: why panels are found by their label Title, critic correction 5). Create `test/test_by_text.py` with the module docstring and every stub under "Regression tests" and "Unit tests", naming new functions as `dr._dash_by_value_missing` etc. so they fail with AttributeError now; build frames by hand (auto-like: 74 rows, `s` D/F/"" as E6 a17, `e` all "", `u` unlabelled, labels `Car origin`, `Repair record 1978`, `Headroom (in.)`). Run `python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -rf > "$S/28-new-1.log" 2>&1`. Write `$S/28-P1.15a-failure.txt`: the base sha, one line per failing node from `28-new-1.log` with its assertion text, then "Guards (pass at the base)" naming `test_a_capitalised_title_is_not_drawn`. Edit no other file; do not commit.]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/28-new-1.log"` is at least 30 and `grep '^FAILED' "$S/28-new-1.log" | grep -c test_a_capitalised_title_is_not_drawn` prints 0; `git -C "$WT" status --porcelain` lists only `?? test/by_panel_probe.py` and `?? test/test_by_text.py`.]]></verify>
  <done>The regression tests existed, failed on the unmodified tree for the measured reasons, and their failure text was saved.</done>
</task>

<task type="auto" id="28-02">
  <name>Create the extractor and the fixture</name>
  <files>scripts/extract_by_text_truth.do, test/fixtures/by_text_truth.json</files>
  <action><![CDATA[Create `scripts/extract_by_text_truth.do` exactly as "Stata truth" describes: header comment, S02's root stanza (TR-02.9) with `<file>` = `extract_by_text_truth.do`, the stamp of extract_unlabelled_truth.do:66-80, the data block, the `bt` table with the 39 probes verbatim, the per-probe loop (log, rc, record file, sersets, SVG) and the trailing `python:` block (reads files only; `Macro.getGlobal` for paths; a backtick as `\x60`; `json.dump(..., ensure_ascii=False, indent=1, sort_keys=True)`). Run `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/s28" "$WT/scripts/extract_by_text_truth.do"`. Compare the recorded values with E6's table in a scratch script `$S/s28/check_fixture.py` (labels, overall texts, rc and messages, serset counts 40/22/62 for bp28); stop and report any difference. Run `git -C "$WT" add -f test/fixtures/by_text_truth.json`. Never edit the fixture by hand (R7).]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('$WT/test/fixtures/by_text_truth.json'));print(len(d['probes']), sorted(d['_meta'])[:4], d['probes']['bp32']['rc'], d['probes']['bp35']['rc'], [p['n'] for p in d['probes']['bp28']['panels']])"` prints `39 ['born_date', 'dash_commit', 'extracted', 'method']` then `198 198 [40, 22, 62]`; `python3 "$S/s28/check_fixture.py"` prints `all 39 probes match E6`.]]></verify>
  <done>twoway's labels, overall texts, panel counts and refusals for 39 probes were recorded with the D12 stamp.</done>
</task>

<task type="auto" id="28-03">
  <name>Add the fixture-driven tests, red first</name>
  <files>test/test_by_text.py</files>
  <action><![CDATA[Add the "Fixture-driven tests" stubs to `test/test_by_text.py`: `_FIXTURE` (path to `test/fixtures/by_text_truth.json`, read once), `_frame_of(fixture)` (the `data` key through `make_data_json`), `_probe_spec(probe)` (one scatter mpg weight graph with the probe's options split into graph options: `title`, `subtitle`, `note`, `caption`, `scheme` in `build_options`, `by` the whole by() argument, `if_expr` from `if`), and the classes `TestTheFixture`, `TestPanelsMatchTwoway`, `TestOverallTextMatchesTwoway`, `TestPlacementMatchesTwoway`, parametrised over the probes with rc 0 and both modes. Run them on the unmodified renderer: `python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -rf -k "Fixture or MatchTwoway or Placement" > "$S/28-new-2.log" 2>&1`, and append its FAILED lines and the passing guards to `$S/28-P1.15a-failure.txt`.]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/28-new-2.log"` is at least 40; `TestTheFixture` and `test_an_all_missing_by_is_nothing_to_graph` pass; `tail -1 "$S/28-P1.15a-failure.txt"` names a guard.]]></verify>
  <done>The tests that compare both modes with twoway probe by probe existed and failed for the measured reasons.</done>
</task>

<task type="auto" id="28-04">
  <name>Fill the BP truth block, red first</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[Read S01's helper names (`grep -n 'program define _w30\|w30_work' "$WT/test/test_wp30_truth.cscript"`). Put `_s28_count` directly above S01's `* ==== S28 P1.15a: ... ====` header and replace the S28 stub body between S01's start and end lines with the block of "Stata truth" (BP-01..BP-08), using S01's names. Write the driver `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/s28/run_test_wp30_truth.do"` and run `WP30_ONLY=S28 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/s28" "$S/s28/run_test_wp30_truth.do"`. Append every BP line of `$S/s28/run_test_wp30_truth.log` to `$S/28-P1.15a-failure.txt`. Do not edit the header, the gate, another section's block or the marker line.]]></action>
  <verify><![CDATA[`grep -E '^BP-0[18] PASS' "$S/s28/run_test_wp30_truth.log" | wc -l` prints 2 and the log stops at the first failing BP case among BP-02..BP-07 (its message is in the failure file); `python3 -m pytest "$WT/test/test_cscript_hygiene.py" -q -n0 -p no:cacheprovider -k Wp30` passes.]]></verify>
  <done>The twoway comparison in Stata existed and failed where dash differs from twoway.</done>
</task>

<task type="auto" id="28-05">
  <name>Count a string empty value as missing</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Make TR-28.1: add `_dash_by_value_missing` and `_dash_by_nonmissing` directly above `_dash_by_groups` (def 3436 at c96facd), each with a docstring citing bygraph_g.class:103-106 (`markout ..., strok`) and probes a17-a20; replace `any(pd.isna(v) for v in vals)` in `_dash_by_groups`; replace the five frame lines (saved `_expand_by_groups` :29986 and :30029, `_plan_by_groups` :33898, generated :35569 and :35580). Add both names to the served functions tuple after `"_dash_facet_label", "_dash_stata_date_text",` (:33201) under the comment `# by() panel labels and overall text (WP-30 P1.15a).` (TR-28.8; the other eight names join this line block in 28-07, 28-09 and 28-10). Add the two map keys under S28's anchor. Do not touch `GlyphMapper._mlabel_missing`.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -k "MissingRule or StringMissingPanel"` passes except `test_with_missing_the_empty_group_is_one_missing_panel` (needs 28-06 and 28-10); `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k TheServedAppCarriesEveryName` passes.]]></verify>
  <done>Both modes left a string by() variable's empty group out of the panels and of Total unless missing was given, and the build-time count agreed.</done>
</task>

<task type="auto" id="28-06">
  <name>Join labels and title missing panels</name>
  <files>dash_render.py</files>
  <action><![CDATA[Make TR-28.2 in `_dash_facet_label` (def 20107): the missing test first, `"(missing)"`, then the string branch, numbers and dates as before; `", ".join(parts)`. Rewrite its docstring's twoway paragraph and Returns example (`"Domestic, 3"`; the date difference kept, A53), and only the Returns example of `DashRenderer._facet_label` (def 30049). Nothing else.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -k "Composite"` passes; `python3 -c "import sys; sys.path.insert(0,'$WT'); import dash_render as d; print(d._dash_facet_label(['a','b'], (0.0, float('nan'))), '|', d._dash_facet_label(['s'], ''))"` prints `0, (missing) | (missing)`.]]></verify>
  <done>Panel labels of several variables were joined with ", " and a missing value read "(missing)" in both modes.</done>
</task>

<task type="auto" id="28-07">
  <name>Read by() title, subtitle, note and caption</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Make TR-28.3 and TR-28.4: `_DASH_BY_TEXT_SPELLINGS` after `_DASH_BY_RESCALE_KEYS` (:19872); `_dash_by_text_key`, `_dash_by_text_options` and `_dash_by_note_list` after `_dash_by_rescale` (def 20025), each with a docstring citing E6's probes; the new `elif _dash_by_text_key(tok) is not None: pass` branch in `_dash_parse_by` before the `style` branch (:20004) and its docstring paragraph. Append `"_dash_by_text_key", "_dash_by_text_options", "_dash_by_note_list",` to S28's copy-list block (after 28-05's line). Add the three map keys under S28's anchor.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -k "TextOptions or NoteList"` passes; `python3 -c "import sys,warnings; sys.path.insert(0,'$WT'); import dash_render as d; warnings.simplefilter('error'); print(d._dash_parse_by('foreign, ti(\"X\") note(\"N\") cols(2)'))"` prints `('foreign', 2, False, False, [])` and raises nothing.]]></verify>
  <done>The four text sub-options and their abbreviations were read and merged as twoway merges them, and no longer named as ignored.</done>
</task>

<task type="auto" id="28-08">
  <name>Let the text boxes skip and default</name>
  <files>dash_render.py</files>
  <action><![CDATA[Make TR-28.5 in `_dash_text_annotations` (S15's version; def 25969 at c96facd): keyword-only `defaults=None` and `sides=None`; the by() subtitle skip; the side computed before the text is parsed when `sides` is given; `_dash_textbox_or_default` for a key in `defaults`. Extend its docstring with both keywords and the twoway truth of r01 and a01. Leave the two existing call sites unchanged. The local import line stays S15's.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_chrome.py test/test_textbox_no_text.py -q -n 6 -p no:cacheprovider` passes except the by() nodes listed for 28-11; `python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -k "graph_note_stays"` still fails only on the missing foot cell.]]></verify>
  <done>The graph-level subtitle under by() was no longer drawn as a separate row, and the text-box helper could draw a default note on one side of a cell.</done>
</task>

<task type="auto" id="28-09">
  <name>Draw the panel label as its own row</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Make TR-28.6: add `_dash_by_panel_label` after `_dash_text_annotations`; replace the saved join (:31655-31656) with its call; replace the generated `if _fac_label is not None:` block (:35513-35520) with the two-line comment and the call. This is the batch's one edit of `_generate_app_source` and one of two edits of `_build_sources_and_figures` (both S28's, R12). Append `"_dash_by_panel_label",` to S28's copy-list block and its map key under S28's anchor.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider -k "PanelLabel or Subtitle or Composite or test_labels"` passes; `grep -n '_own} .u2014 {_fac_label' "$WT/dash_render.py"` prints nothing (the generated join, :35519 at `c96facd`) and `grep -n 'f"{orig_title} — {label}"' "$WT/dash_render.py"` prints nothing.]]></verify>
  <done>Every panel kept the graph's title and drew its label, merged with subtitle() as twoway merges it, as a centred unbolded row in both modes.</done>
</task>

<task type="auto" id="28-10">
  <name>Draw the overall text once</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Make TR-28.7: `_dash_by_text_cell`, `_dash_by_chrome`, `_dash_by_frame_grid` and `_dash_by_chrome_figures` after `_dash_by_panel_label`, each with a docstring (E9's measurements, D-28a, D-28b, the S48/S53 contract). In `_build_sources_and_figures` attach the cells after `_dash_share_by_scales` (:31669-31671) and add the second pass call after S09's `_dash_finish_graph_text(self.figures)`; in the template add the generated lines after `_dash_share_by_scales([figures[_f] ...` (:35653-35654) and after S09's `_dash_finish_graph_text(figures)`; in `_dash_layout_cell` (:25020) frame the grid. Append `"_dash_by_text_cell", "_dash_by_chrome",` and `"_dash_by_frame_grid", "_dash_by_chrome_figures",` to S28's copy-list block; four map keys under S28's anchor.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_text.py -q -n 6 -p no:cacheprovider` passes (browser module excluded); `python3 -m pytest test/test_statistical_helpers.py test/test_resource_limits.py test/test_function_test_map.py -q -n 6 -p no:cacheprovider -k "CarriesEveryName or DefinesEveryNameItReads or function_test_map"` passes.]]></verify>
  <done>by()'s own title, subtitle, note and caption and the Graphs by note were drawn once over the panels in both modes, framed in the panel grid and finished by the canvas-text pass.</done>
</task>

<task type="auto" id="28-11">
  <name>Re-measure and flip the first pins</name>
  <files>test/test_help_claims_5.py, test/test_server_facets.py, test/test_by_scales.py</files>
  <action><![CDATA[First re-measure: run the 26 files of E10 and every test file present at the batch-10 base that matches `grep -l '"by"\|by(\|__by__\|facet' test/test_*.py`, with `python3 -m pytest <files> -q -n 6 -p no:cacheprovider -rf > "$S/28-flips.log" 2>&1`, and write the FAILED nodes to `$S/28-red.txt`. A red node not in E10 but in a file 28-11 to 28-21 name is flipped by the same rules in that task; `test/test_canvas_tex.py`'s anchor node is 28-22's; a red node in any other file, or one that is not a panel-identity, label-text, chrome-count, grid-tuple or by()-text-note pin, stops the section for a plan amendment (R12, as S15 does). Then flip E10's 28-11 row in place, each with its R9 line: in `test_help_claims_5.py`, `_grid_panels` returns `by_panel_probe.by_grid` panels as `(row, col, panel_label)`, `_counts` keys on `panel_label`, `"Missing"` becomes `"(missing)"`, `"Domestic / 3"` becomes `"Domestic, 3"` (and the helper unit's `nan` case `"(missing)"`), `test_the_graphs_title_leads_each_panels` asserts title `Cars` and labels `Domestic`/`Foreign`, `test_by_keeps_its_cols_after_an_apostrophe` expects `[]` unsupported, `test_in_both_modes` expects no by() sub-option note and a head cell reading `Bob's cars`; in `test_server_facets.py`, `served()` skips models `by_panel_probe.is_chrome` names, `panel_profile`'s `"title"` is `panel_label(f)`, the missing panel is `"(missing)"`, `TestAByTextHoldingMacroCharactersFacets` expects no by() note (the text is drawn) and the head or foot cell to hold the typed text, and the `title("By origin")` case of `test_each_unimplemented_sub_option_is_named` becomes `'foreign, title("By origin") shrink'` naming `shrink` only (twoway's `SHRink`, implemented by no WP-30 section); in `test_by_scales.py`, `_title`, `_by_panels_of` and `_panels` key on `panel_label`.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_5.py test/test_server_facets.py test/test_by_scales.py -q -n 6 -p no:cacheprovider` passes; for each of the three files `grep -c 'def test_' <file>` equals its count at the base (`git -C "$WT" show HEAD:<file> | grep -c 'def test_'`).]]></verify>
  <done>The red list was re-measured on the batch base, and the first three files asserted twoway's panel text, found panels by their label row and kept every test.</done>
</task>

<task type="auto" id="28-12">
  <name>Flip the reserved-name and title pins</name>
  <files>test/test_reserved_names.py, test/test_scheme_review_fixes.py, test/test_textbox_no_text.py</files>
  <action><![CDATA[Flip E10's 28-12 row in place with the R9 line: `_PANELS` becomes the labels `["0", "1"]` read by `panel_label`, each panel's title asserted `g1`; `test_bypass_no_spelling_takes_a_panel_s_place` reads labels the same way; `test_both_modes_title_a_by_panel_the_same` asserts, in both modes and over panels only (`is_chrome` skipped), every `fig.title.text == want` and the labels `Domestic`, `Foreign`; `test_facet_title_keeps_its_panel` asserts title `A` and a non-empty label on each panel.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_reserved_names.py test/test_scheme_review_fixes.py test/test_textbox_no_text.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>These pins asserted the graph title on every panel and the label row beside it.</done>
</task>

<task type="auto" id="28-13">
  <name>Flip the served linked-view pins</name>
  <files>test/test_served_linked_views.py, test/test_served_bs_layout.py, test/test_served_dates.py</files>
  <action><![CDATA[Flip E10's 28-13 row in place with the R9 line: rows keyed by panel title (`"g1 — 0"`) are keyed by `"g1 " + panel_label` (or the label alone where the test keys a plain label); the bs-layout cell comparisons read panels through `by_grid` and compare the head and foot cells' `chrome_texts` in both modes; `test_the_cell_still_saves_under_the_graph_s_name` finds the grid's one `SaveTool` and asserts its filename `g1`; the date panel test reads `panel_label`.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_linked_views.py test/test_served_bs_layout.py test/test_served_dates.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>The served linked-view, bs-layout and date pins found panels by label and compared the overall text in both modes.</done>
</task>

<task type="auto" id="28-14">
  <name>Flip the server, page and toolbar pins</name>
  <files>test/test_server.py, test/test_html_output.py, test/test_toolbar.py</files>
  <action><![CDATA[Flip E10's 28-14 row in place with the R9 line: `TestServerByFaceting` and `TestServerLpolyFpfit` key panels on `panel_label`; `test_by_facet_labels_in_source` and `test_by_total_source_in_generated_source` assert the generated `_dash_by_panel_label(fig, _fac_label` call and the frame helper `_dash_by_nonmissing` in place of the deleted join and `dropna` text; the HTML tests read the label `Title` texts (`name == "dash_by_label"`) for `Group A`, `Group B` and `Total`; the toolbar tests skip chrome cells, which carry no tools by design (`is_chrome`), and `test_a_by_graph_s_panels_save_as_dashboard` counts panels through `by_grid`.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server.py test/test_html_output.py test/test_toolbar.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>The server, page-output and toolbar pins read the label rows and left the toolless chrome cells out.</done>
</task>

<task type="auto" id="28-15">
  <name>Flip the Total, cue and grid pins</name>
  <files>test/test_qualifier_columns.py, test/test_saved_stale_cue.py, test/test_resource_limits.py</files>
  <action><![CDATA[Flip E10's 28-15 row in place with the R9 line: `_by_label` reads `panel_label` (the split on the em dash goes); the stale-cue tests find `Domestic`, `Total` and the frozen tag's panel by `panel_label`; `TestByColsCannotOutgrowThePanels` reads the panel rows through `by_grid` (the foot row is not a panel row), its served half asserting gridplot is handed the panels alone as before.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_qualifier_columns.py test/test_saved_stale_cue.py test/test_resource_limits.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>The Total-column, stale-cue and column-limit pins found panels by label and counted panel rows only.</done>
</task>

<task type="auto" id="28-16">
  <name>Flip the help-claims and exclude pins</name>
  <files>test/test_help_claims_4.py, test/test_help_claims_2.py, test/test_keyword_names.py</files>
  <action><![CDATA[Flip E10's 28-16 row in place with the R9 line: the per-panel recount tests key on `panel_label`; `test_by_panels_are_titled_by_the_value_labels` asserts the value labels as label rows; `test_the_served_filter_leaves_its_panels_alone` finds the panels by label and skips chrome cells.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_4.py test/test_help_claims_2.py test/test_keyword_names.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>These pins asserted value labels as label rows and found panels by them.</done>
</task>

<task type="auto" id="28-17">
  <name>Flip the date and option pins</name>
  <files>test/test_date_range.py, test/test_display_format_sites.py, test/test_graph_options.py</files>
  <action><![CDATA[Flip E10's 28-17 row in place with the R9 line: the date-panel tests read `panel_label` (dash's date text kept, A53); `test_facet_title_contains_group_label` and `test_bl_09_facet_titles_contain_group_label` assert a non-empty label row naming the group.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_range.py test/test_display_format_sites.py test/test_graph_options.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>The date and graph-option pins read the label rows.</done>
</task>

<task type="auto" id="28-18">
  <name>Flip the filter and tab pins</name>
  <files>test/test_filter_exclude.py, test/test_filter_exclusion_sets.py, test/test_layout_tabs.py</files>
  <action><![CDATA[Flip E10's 28-18 row in place with the R9 line: the exclude tests find a by() panel by `panel_label`; `test_a_tabbed_graph_is_not_also_drawn_in_the_grid` lists model types with chrome cells left out (`is_chrome`), so the grid still holds no tabbed graph.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclude.py test/test_filter_exclusion_sets.py test/test_layout_tabs.py -q -n 6 -p no:cacheprovider` passes; no `def test_` count changed.]]></verify>
  <done>The filter and tab pins found panels by label and ignored the chrome cells.</done>
</task>

<task type="auto" id="28-19">
  <name>Teach the range probe the chrome cells</name>
  <files>test/range_probe.py, test/test_phase5.py</files>
  <action><![CDATA[In `test/range_probe.py`, in both `_RANGES_JS` and `_MOVE_TIMED_JS`, add `&& m.name !== "dash_by_head" && m.name !== "dash_by_foot"` to the test that collects a plot (the one requiring `x_range`, `y_range`, `renderers` and `toolbar`), with a comment: the chrome cells of a by() grid (WP-30 P1.15a) are bare Plots whose fixed 0-1 ranges are not a panel's, so counting them gave `assert 101 == 100` and kept `_MOVE_TIMED_JS`'s "every y range agrees" from ever resolving. Rows keep their seven places, so every user (`test_by_scales_chrome.py`, and S21's `test_default_axes_chrome.py`) reads them unchanged. `test_by_scales_chrome.py` is not edited: its five E10 nodes go green through this change, recorded as one `Flipped:` line naming the helper, the five nodes and the reason. In `test/test_phase5.py`, `test_by_xss_in_facet_label_is_canvas_text` reads the label `Title`'s text (`by_panel_probe.panel_label`), with its R9 line. Record every `Flipped:` line of 28-11 to 28-19 in `$S/28-flips.txt` (node, old expectation, why).]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_scales_chrome.py test/test_phase5.py -q -n0 -p no:cacheprovider` passes, `test_hundred_panels_settle` included and not skipped on this Mac; every test file that imports it (`grep -l range_probe test/test_*.py`) passes; `git -C "$WT" diff --name-only -- test/test_by_scales_chrome.py` prints nothing.]]></verify>
  <done>The browser range probe told panels from chrome cells, so the by() range and settle checks measured panels only, and the canvas-text pin read the label row.</done>
</task>

<task type="auto" id="28-20">
  <name>Flip earlier sections' by() pins, part one</name>
  <files>test/test_scheme_chrome.py, test/test_series_labels.py, test/test_value_lists.py</files>
  <action><![CDATA[These are S15's, S19's and S20's test files, written after `c96facd`, so E10 could not measure them. Take their red nodes from `$S/28-red.txt` (28-11's re-measure). Flip each in place by the rules of "Pinned tests to flip": a panel found by `by_panel_probe.panel_label`, `", "` and `(missing)` labels, `"T — label"` read as title `T` plus label, chrome cells skipped with `is_chrome`, the grid read through `by_grid`. Append each R9 line to `$S/28-flips.txt`. A file with no red node is left unchanged. A red node of any other kind stops the section for a plan amendment (R12).]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_chrome.py test/test_series_labels.py test/test_value_lists.py -q -n 6 -p no:cacheprovider` passes (a file absent at the base is reported, never created); for each file the section changed, `grep -c 'def test_'` equals its count at the base.]]></verify>
  <done>The by() pins of the earlier sections' chrome, key and value-list tests read the label rows, each flip with its reason.</done>
</task>

<task type="auto" id="28-21">
  <name>Flip earlier sections' by() pins, part two</name>
  <files>test/test_default_axes.py, test/test_axis_format_fallback.py, test/test_bar_range_geometry.py</files>
  <action><![CDATA[These are S21's, S18's and S27's test files (after `c96facd`). Flip their red nodes of `$S/28-red.txt` in place by the rules 28-20 states, each R9 line appended to `$S/28-flips.txt`; a file with no red node is left unchanged; a red node of any other kind stops the section for a plan amendment (R12). Then run the whole re-measured red list once more.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py test/test_axis_format_fallback.py test/test_bar_range_geometry.py -q -n 6 -p no:cacheprovider` passes; `python3 -m pytest $(cut -d: -f1 "$S/28-red.txt" | grep -v test_canvas_tex | sort -u | tr '\n' ' ') -q -n 6 -p no:cacheprovider` passes; `wc -l < "$S/28-flips.txt"` equals the number of flipped test functions of 28-11 to 28-21 plus 28-19's one range-probe line.]]></verify>
  <done>Every measured pin of today's panel text, in the original files and in the earlier sections' files, was flipped in place with its reason.</done>
</task>

<task type="auto" id="28-22">
  <name>Register the sinks and parity cases</name>
  <files>test/test_label_sinks.py, test/test_mode_parity.py, test/test_canvas_tex.py</files>
  <action><![CDATA[In `test/test_label_sinks.py`: g2's `by` becomes `'foreign, title("%s") subtitle("%s") note("%s") caption("%s")' % (quoted("btitle"), quoted("bsub"), quoted("bnote"), quoted("bcap"))`; add graph g9 `by="rep"` (scatter mpg weight; `rep` is in `_COLS`, :207, so its label is the tagged `vlrep`); add Sinks `by_title` (btitle), `by_subtitle` (bsub), `by_note` (bnote), `by_caption` (bcap) and `by_note_from_variable_label` (vlrep), each `("Title",)`, `"text"`, `"text"`; keep `facet_title_from_value_label`. In `test/test_mode_parity.py` append to `CORPUS` `_case("by() labels under a title and a prefixed subtitle (WP-30 P1.15a)", [_sc()], None, {"by": "foreign rep", "title": '"T"', "subtitle": '"S", prefix'})` and `_case("by() overall title, subtitle, note and caption (WP-30 P1.15a)", [_sc()], None, {"by": 'foreign, total title("X") subtitle("S") note("N", suffix) caption("C")'})`; `ALLOWED` and `_MUST_WARN` untouched (R8). In `_layout_tree` (test_mode_parity.py:862), before the final `kids` fallback, a `Plot` whose `name` is `dash_by_head` or `dash_by_foot` returns `("chrome", m.name, [(type(x).__name__, x.text, x.text_font_size, x.text_color, getattr(x, "align", None)) for x in <its title, then above, below and center Title/Label models>])`, so the chrome cells of both modes are compared, never skipped. In `test/test_canvas_tex.py` flip `TestTheServedApp::test_make_document_runs_the_pass_after_the_panels_and_before_the_widgets`: its anchor `fig.title.text = (f'{_own}` becomes `_dash_by_panel_label(fig, _fac_label`, with the R9 line.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_sinks.py test/test_mode_parity.py test/test_canvas_tex.py -q -n 6 -p no:cacheprovider` passes, and `-k "by_title or by_note or by_caption or by_subtitle"` selects 10 or more passing nodes.]]></verify>
  <done>The five new canvas sinks carried user text raw and inert in both modes, and both modes drew the by() text identically in the parity corpus.</done>
</task>

<task type="auto" id="28-23">
  <name>Add the browser check</name>
  <files>test/test_by_text_browser.py</files>
  <action><![CDATA[Create `test/test_by_text_browser.py` with the two "Browser" stubs: module skip without `responsive_probe.find_chrome()`; the saved page written by `DashRenderer`, the served one by `file_html(list(doc.roots), INLINE, ...)` (test_by_scales_chrome.py:48-53); `monkeypatch.setattr(responsive_probe, "PROBE_JS", <widened probe>)` reporting every canvas rect of at least 20 x 20 px. Identify the head, panel and foot canvases by order and width as E9 did.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_text_browser.py -q -n0 -p no:cacheprovider` passes (4 tests) on this Mac, which has Chrome; with `DASH_CHROME=/nonexistent` and no Chrome on PATH it skips, never fails.]]></verify>
  <done>Chrome drew the head above and the foot below the panels in both modes and stacked them in reading order at phone width.</done>
</task>

<task type="auto" id="28-24">
  <name>Run the cscripts and flip HC5-07</name>
  <files>test/test_help_claims_5.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[Flip HC5-07 in place (:388-426 and header line :30) as "Area cscripts" says, with a comment line `// Flipped (WP-30 P1.15a): dash wrote Domestic / 3; twoway writes Domestic, 3`. Run through the driver, each with its own driver file in `$S/s28/`: `test_wp30_truth.cscript` with `WP30_ONLY=S28`, `test_help_claims_5.cscript`, `test_json_escaping.cscript`, `test_by_suboptions.cscript`, `test_parser.cscript`. A failure in the last three is a defect of this section's code, never a flip.]]></action>
  <verify><![CDATA[`grep -c '^BP-0[1-8] PASS' "$S/s28/run_test_wp30_truth.log"` prints 8 and the log holds `ALL CHECKS PASSED`; each of the other four logs ends with its script's PASS summary and holds no `r(` error line; `ls -A "$S/s28/tmp"` prints nothing.]]></verify>
  <done>twoway and dash agreed in Stata on every BP case, HC5-07 asserted twoway's composite label, and the by() text cscripts stayed green.</done>
</task>

<task type="auto" id="28-25">
  <name>Rewrite the by() help sentences</name>
  <files>dash.sthlp, test/test_help_claims_5.py</files>
  <action><![CDATA[In "Faceting with by()" (dash.sthlp:2055-2137 at c96facd; find by text): :2070's synopt reads `include a panel, titled "(missing)", of the observations with a missing value (a string variable's "" included)`; add synopt rows for `by(varlist, title() subtitle() note() caption())` ("drawn once over the panels; abbreviations ti, sub, note, cap") and `by(varlist, note(""))` ("remove the Graphs by note"); :2096-2097 says the Total panel and the groups leave out a missing value, a string "" included, unless missing is given, and that the missing panel is titled (missing) as in twoway; :2106-2116 says the label is drawn as its own centred row under the graph's title(), that subtitle() replaces, leads (prefix) or follows (suffix) it and subtitle("") removes it, composite labels read "Domestic, 3", a value label holding double quotes stays one line (twoway splits it, A55), and the note is "Graphs by" with twoway's list (the first of three or more variables by its name); :2122-2125 lists title(), subtitle(), note() and caption() among the implemented sub-options and keeps rows(), holes() and compact as examples of the rest. Lines under 80 characters; SMCL as the paragraph uses it. In `test/test_help_claims_5.py` flip `TestTheHelpSaysSo::test_the_panel_title_rule_is_stated` (:1326-1329) to `'"Domestic, 3"'` with the R9 line.]]></action>
  <verify><![CDATA[`python3 -m pytest $(grep -l 'dash.sthlp' test/test_*.py | tr '\n' ' ') -q -n 6 -p no:cacheprovider` passes (every test file that reads the help; test_help_claims_5 is the one that reads "Faceting with by()"); `grep -c 'Domestic / 3\|titled "Missing"' "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help stated twoway's panel-label, missing-value and overall-text rules as dash now draws them.</done>
</task>

<task type="auto" id="28-26">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[In BUGS.md change the entry titled "by() panel labels are appended to the graph title, there is no Graphs by note, composite and missing panels are titled differently, and by(, title()) is ignored" in place to `- [x] Title:` and replace its Resolution line with: `  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.15a). Each by() panel is labelled on its own centred row under the graph's title(), merged with subtitle() as twoway merges it; labels of several variables are joined ", " and a missing value reads (missing); a string "" by() value is missing in the panels and in Total; by()'s title(), subtitle(), note() and caption() and the Graphs by note are drawn once over the panels, in _dash_facet_label, _dash_by_groups and the by() frames, _dash_by_panel_label, _dash_by_chrome and _dash_layout_cell, in the saved page and the served app and after a filter move. Pinned by test/test_by_text.py::TestPanelsMatchTwoway::test_labels, test/test_by_text.py::TestOverallTextMatchesTwoway::test_texts, test/test_by_text.py::TestAStringMissingPanel::test_the_total_panel_leaves_out_the_empty_group, test/test_by_text_browser.py::TestInChrome::test_stacked_in_reading_order, test/test_wp30_truth.cscript BP-02; fixture test/fixtures/by_text_truth.json. Residual, deferred (WP-30): the label's filled box (drawn by WP-30 section 53, entry P1.15c), subtitle(, ring(0) pos()) inside the plot region (P2.4), .a-.z panels (P2.18).` Delete only `P1.15a`'s line from `WP30_OPEN` in `test/test_tracking_documents.py`. Replace `<!-- WP-30 P1.15a -->` in place with the CHANGELOG line of Notes. Then: `python3 -m pytest test/test_tracking_documents.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider`; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/28-full-1.log"` waited for on its `exit=` line (E6 for the known flaky tests); `git -C "$WT" add` the named paths only (never `-A`; `-f` for the fixture); check `git -C "$WT" diff --cached --name-only` (G6) and the message (G7); commit with `-F "$S/28-message.txt"` (Notes: commit-message form).]]></action>
  <verify><![CDATA[`tail -1 "$S/28-full-1.log"` shows `exit=0` with 0 failed; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.15a)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git -C "$WT" show --name-only --format= HEAD | sort` lists exactly BUGS.md, CHANGELOG.md, dash.sthlp, dash_render.py, scripts/extract_by_text_truth.do, test/by_panel_probe.py, test/fixtures/by_text_truth.json, test/function_test_map.py, test/range_probe.py, test/test_by_text.py, test/test_by_text_browser.py, test/test_canvas_tex.py, test/test_help_claims_5.cscript, test/test_label_sinks.py, test/test_mode_parity.py, test/test_tracking_documents.py, test/test_wp30_truth.cscript, and the flipped test files of `$S/28-flips.txt`; `grep -c 'WP-30 P1.15a -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.15a": "' "$WT/test/test_tracking_documents.py"` prints 0.]]></verify>
  <done>Entry P1.15a was closed with its tests named, its marker and key were gone, and the section's one commit was made on wp30-s28 after a green full run.</done>
</task>

## Section completion criteria

- AC-28.1 to AC-28.9 hold.
- The ten new functions exist, are mapped under S28's anchor, and travel to the served app at R2's S28 anchor; `TestTheServedAppCarriesEveryName` and `TestTheServedAppDefinesEveryNameItReads` pass.
- `test/fixtures/by_text_truth.json` holds 39 probes with the D12 stamp, is force-added, and is named by `test_by_text.py`.
- Every pinned test of E10 (as re-measured in 28-11) is flipped in place with a `Flipped:` line; no test is deleted or renamed.
- BUGS.md's P1.15a entry is closed in place; its `WP30_OPEN` key and CHANGELOG marker are gone; the CHANGELOG line is under `### Results that change`.
- One commit on `wp30-s28`, subject ending `(WP-30 P1.15a)`, made after one green full run through the queue; no file outside the list of 28-26.

## Notes

**Traps for the executor.**
- **Order of models.** Both modes add the label after the panel figure is complete (saved: after `_make_figure` returns; served: at the end of `_dash_figure_for`), so the label is the outermost model of `fig.above` and BokehJS still draws `fig.title` outside it (E1). Never add the label inside `_make_figure_body` or before the second axis: the two modes add `xaxis(2)` at different moments (S15 E4).
- **The no-faceting sentinel.** `_build_sources_and_figures` treats `len(by_groups) == 1 and by_groups[0][0] == ""` (:31584) as "no panels". It is not changed. After 28-06 a missing panel is `(missing)`, so `by(e, missing)` is faceted; a one-panel graph whose only label is a value label of empty text still takes the plain path (Notes for the closeout).
- **Two missing rules.** `_dash_by_value_missing` is by()'s rule (`strok`: `""` is missing). `GlyphMapper._mlabel_missing` is the marker-label rule (`""` is a label with no text). Do not merge them.
- **Case.** `_dash_parse_by` lower-cases names for its own branches (:19988); `_dash_by_text_key` must not, or `TITLE("X")`, which twoway refuses, would be drawn (BP-08).
- **Sub-option notes once per graph.** The served label call passes `go.get('name', '') or gname` as the key, as `_dash_note_hover_unreached` does; passing the panel key would name a refused `subtitle()` sub-option once per panel when S23's trial relays session notes.
- **The pass.** S09's pass is given `figures`; chrome cells are not in it. The second call over `_dash_by_chrome_figures(...)` must follow S09's call in both modes, before the filter widgets (served) and before the method returns (saved), or TeX in a by() title reaches MathJax and S29's SMCL never reaches the note.
- **W-1000.** A cell without the invisible `Span` logs `MISSING_RENDERERS` once per cell (E9); `TestTheGrid::test_no_missing_renderers_warning` guards it.
- **Copy list and constants.** Append only, at S28's anchor (X.1). `_DASH_BY_TEXT_SPELLINGS` reaches the app through `_supply_missing_constants`: in the scratch prototype (E10) `_dash_parse_by` read it inside the generated app and every served by() test built its document, with no NameError. `TestTheServedAppDefinesEveryNameItReads` guards it.
- **The served scope.** The chrome call in the template uses `go`, `by_vars`, `gname` of the by() loop and the make_document-level `var_labels` (:34770) and `_reported_subopts` (:34920); the by() loop runs inside `make_document`, so all are in scope.
- **Fixture rows.** The fixture's frame is exported by `_dash_write_stata_data`, so `s` and `e` arrive as Stata's exporter writes them (`""`, not `None`); the hand frames of 28-01 must use `""` too, or `TestAStringMissingPanel` passes at the base for the wrong reason.
- **S15's names.** TR-28.5 to TR-28.7 use S15's `SchemeParser.text_clock`, `text_just` and `_dash_textbox_place` as TR-15.7/TR-15.8 name them. Read the landed names in the worktree (`grep -n 'text_clock\|text_just\|def _dash_textbox_place' dash_render.py`) before writing; if S15 landed other names, use them and say so in the commit body.
- **R12.** S28 is batch 10's only editor of `_build_sources_and_figures` and `_generate_app_source`; S29 and S30 edit neither. A need to edit `_make_figure_body` or an applier stops the section for a plan amendment.

**Merge rules for the shared files.** R1: the S28 block of `test_wp30_truth.cscript` between S01's start and end lines, `_s28_count` above S01's header; HC5-07 flipped in place only. R2: ten names at S28's copy-list anchor (after `"_dash_facet_label", "_dash_stata_date_text",`, :33201), no other row's anchor; ten map keys under S28's anchor; in-place edits of already-copied names. R3/A155 and D-28f: "Faceting with by()" only (:2070, :2096-2097, :2106-2116, :2122-2125); no batch-10 partner edits it. R4: the one `P1.15a` marker, under `### Results that change`, replaced in place. R5: the `P1.15a` entry and key only. R7: one new extractor and fixture, never hand-patched, force-added. R8: two CORPUS cases appended; `ALLOWED`/`_MUST_WARN` untouched. R9: every flip in place with its reason (E10). R10: no pin moves (the single-y digest page has no by()). R12: see above.

**CHANGELOG line** (replaces `<!-- WP-30 P1.15a -->` in place, under `### Results that change`):
`- dash scatter mpg weight, title("T") by(foreign rep78, missing) now labels each panel on its own row under T -- Domestic, 1 ... Foreign, (missing) -- where it titled them T — Domestic / 1 ... T — Foreign / Missing; subtitle() replaces, leads or follows the label as in twoway; by(, title() subtitle() note() caption()) are drawn once over the panels, where they were named and ignored, with twoway's note Graphs by Car origin and Repair record 1978 under them unless by(, note("")); and a string by() variable's "" values are left out of the panels and the Total panel unless missing is given, where they drew an untitled panel and were counted in Total (WP-30, P1.15a)`

**Commit message** (`$S/28-message.txt`). Subject: `Draw by() panel labels and overall text as twoway does (WP-30 P1.15a)`. Body, in order: the contents of `$S/28-P1.15a-failure.txt`; the measured defect (Overview, E7); what changed and where (TR-28.1 to TR-28.8, both modes, after a filter move); then one line each: `Regression: test/test_by_text.py::TestAStringMissingPanel::test_the_total_panel_leaves_out_the_empty_group -- failed at <batch-10 base> with <text>` (and one per regression class of 28-01), every `Flipped: <node> -- <old expectation> was wrong because <why>` line of `$S/28-flips.txt` and 28-22/28-25's, `Fixture: test/fixtures/by_text_truth.json (scripts/extract_by_text_truth.do)`, `BUGS.md: "by() panel labels are appended to the graph title, there is no Graphs by note, composite and missing panels are titled differently, and by(, title()) is ignored" (closed)`. No tool or vendor name (G7, A141).

**Maintainer question (answered).**
- **Q-28.1 (D-28e).** Answered 06oct2026 (ratification row 36), CHANGED: "Add to S53". S53 draws twoway's filled box behind each by() panel label (its scheme keys through batch 18's regenerator, S53); S58 files no P2 row. The original question and recommendation follow for the record. twoway draws each panel label in a filled box spanning the plot region (stcolor gs15 fill and outline; s2color bluishgray; scheme keys `textboxstyle subtitle` under by() and `color bylabel_outline`). The keys are not in dash's scheme files, and only a batch's regenerator may add them (A152; S30 regenerates in batch 10). S53's writer recorded the box as outside S53's manifest scope (section-53 Boundaries; open-questions.md), and no later section's scope covers it. **Recommendation: file it as a P2 item** (two scheme keys through a batch's regenerator, and the box drawn as a `BoxAnnotation` in screen units or a filled frame row, since a `Title`'s background spans only its text). If the maintainer assigns it to S53 instead, S53 re-plans it before `batch-18-base` is recorded (section-53 Notes). Until then the label is drawn without the box, and the help says so.

**Notes for the closeout** (S58 writes these; A145):
- GAPS2.md B16 Tracked line: add "title()/subtitle()/note()/caption() inside by() closed in WP-30 (P1.15a, commit <sha>)"; the rest of B16 stays with P1.15b and P1.15c.
- GAPS2.md B31 Tracked line: "panel labels, the Graphs by note and the missing/composite text closed in WP-30 (P1.15a, commit <sha>); repeated axes and legends: P1.15c".
- TWOWAY_COVERAGE_AUDIT.md:143 (Facets row): strike "panel label punctuation/date rendering can differ" down to "date panel titles are dash's date text (twoway writes the number)", and add "[WP-30 P1.15a, commit <sha>: panel labels, by() titles and notes, and string missing values as twoway draws them]".
- DROPIN-REMAINING.md P1.15: the text sub-bullets ("Panel labels are appended…", "Composite and missing panels…", and `title`, `note` in the first bullet) are closed by P1.15a.
- Residual candidates for the P2 list: a one-panel by() graph whose only value label is empty text is drawn without panel chrome (the sentinel); the label box is not a residual (Q-28.1: S53 draws it, ratification row 36). Existing items keep theirs: P2.4 (`subtitle(, ring(0) pos())`, `title(, position())`), P2.18 (`.a`-`.z` panels).
- AGENTS.md invariant (only if AGENTS.md has no uncommitted edits, E7): "a by() graph's panel label is the Title named dash_by_label, and its overall text lives in the chrome cells dash_by_head/dash_by_foot of the panel grid; find panels with test/by_panel_probe.py, never by fig.title".
