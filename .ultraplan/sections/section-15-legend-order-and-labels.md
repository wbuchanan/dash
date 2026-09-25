# Section 15: Legend order and labels (B5)

> Part of: WP-28 · Gaps: B5 · Risk: yellow · Batch: 3 · Depends on: 02, 13 · Blocks: 19 · Tasks: 9, one commit (B5)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **3** · Depends on **02, 13** · Blocks **19** · Risk **yellow** · Commits: one commit (B5) → CHANGELOG `Results that change`

- D4/R5: this section extends S13's `scripts/extract_text_truth.do` and regenerates `text_truth.json` once.
- D11/C7 (replaces the earlier R1 line): the LO-01..LO-08 cases are a block `* ==== S15 B5: legend order and labels ====` appended to `test/test_gaps2_truth.cscript`, the one new certification script of WP-28, which S02 created and registered (runner block `// 67.`) in batch 1; this section adds no script and edits neither `test/run_all_cscripts.do` nor the hygiene pins. D12/C8: 15-05's regeneration re-stamps `_meta` and a test asserts its four keys. Stub: `label(0)` (F-22).
- AMEND-1 (A, B, H, I, J): the B5 CHANGELOG marker sits in the bold group `**WP-28 (GAPS2 audit, 25sep2026)**` at the end of the release's `### Results that change` list (CHANGELOG.md:10) and is replaced in place; a single cscript runs through a two-line driver do-file in the scratch directory (`cd "<repo>/test"` then `do`), with `GAPS2_ONLY=S15` in the environment to run this section's block alone; the block has the `* ==== S15 B5: … ====` / `GAPS2_ONLY` gate / `* ==== end S15 ====` form and is appended above `* ==== append new blocks above this line ====`; the regeneration is checked probe by probe (every pre-existing `title` probe unchanged, `_meta`'s existing keys kept); the closing task commits on the worktree branch `wp28-s15` and the merger lands it on `s3-bugs`.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

twoway's `legend(order())` takes key numbers each followed by optional text, and a `-` that inserts a text-only line; `label(# "text")` names key number # whatever `order()` does; `lastlabel()` overrides both (`legend_options.sthlp:104-119, 216-314`). GAPS2 B5 measures that dash gets all of it wrong with no warning: `order()` is read as `re.findall(r"\d+", ...)` applied to displayed positions, so `order(1 "Group 2" 3 "Three")` draws the keys `mpg` / `Fitted values` / `price` and ignores the texts; `label()` is applied by displayed position after the reorder, so `order(2 1) label(1 "Data")` relabels the fit instead of the scatter; `-` lines are dropped; and `lastlabel()` is only named. Both render modes, rc 0.

After this section a key is identified by Stata's plot number -- a `lfitci` layer counting as two, band then line, as `_dash_plot_style_indices` already numbers plots -- its text is resolved default → `label(#)` → `order()` text before anything is selected or moved, `order()` then selects, repeats and orders the keys and inserts its `-` rows as label-only `LegendItem`s (which Bokeh 3.8 and 3.9 draw as a text row with an empty glyph cell, research W §1a), and `lastlabel()` is applied last, by the key's drawn position, as the help says (D §5). A second `lastlabel()` in a repeated `legend()` no longer collapses into the first in dash.ado's merge. Everything honoured prints nothing (DISCOVERY Q22).

One gap, one function: `_dash_apply_legend` (`dash_render.py:15780-15983`), shared by both renderers, plus the key list it builds from and one Mata key. Truth comes from twoway's SVG legend text, isolated by the `legend(off)` companion diff `extract_axis_truth.do` already uses, recorded into `test/fixtures/text_truth.json` by the `scripts/extract_text_truth.do` that section 13 creates in batch 2; this section runs in batch 3, after 13 has merged, appends its probes in the script's marked region and regenerates the fixture once (rule R5).

**Test order (CLAUDE.md rule 7) and commit rule (D1): task 15-01 writes every regression test for this section**, runs it against the tree as batch 2 leaves it and saves the failure text to the scratch directory -- it does not commit (a red tree is never committed, rule 4); 15-02 appends the LO block to the shared truth script and runs it against the same tree; 15-03 and 15-04 extend the pinned tests; 15-05 records the truth; 15-06 to 15-08 turn the tests green; 15-09 closes the entry and makes the section's ONE commit (B5), subject ending `(GAPS2 B5)`, whose body opens with the saved failure text (S01 TR-01.9). The failing tests land in that commit, never alone.

## Risk: [yellow] — one function draws every legend in both modes, and a 100,000-key adversarial test constrains its shape

- **Why:** `_dash_apply_legend` is called once per figure in the saved renderer (`_rebuild_legend` 21794) and once per figure in the served template (26435); every graph with two or more keys goes through it.
- **Risk factors:** (1) key numbering must match twoway's with a CI layer counting two and a layer that drew nothing still consuming its number, or `order()` picks the wrong key on graphs with fits; (2) `test_adversarial_matrix.py::TestTextPlotOptionBounds::test_a_legend_order_of_a_hundred_thousand_keys_is_bounded` (2913-2943) requires repeated references to be the SAME `LegendItem` object (`len({it.id}) == 2`, two `LegendItem` models on the page) and the render under 30 s; (3) `lastlabel()`'s index rule (position after `order()`, D §5) is documented prose, not measured; (4) a `-` row is a new `LegendItem` shape that `test_label_sinks.py`'s inventory walks.
- **Mitigation:** keys are numbered by one helper (`_dash_legend_keys`) pinned by a CI-numbering fixture probe; one `LegendItem` per key is built once and referenced by the sequence, so repeats share it; the `lastlabel` rule is settled by the fixture probe `l_lastlabel_pos` and the executor follows the fixture; the `-` row uses the same `LegendItem.label` sink `test_label_sinks.py` already classifies, and the parity corpus gains four legend cases.

## Dependencies

- **Depends on:** section 02 (`test/cert_svg.do`, `scripts/svg_truth.py`, fixed names as S02 states them: `cert_svg_export` -> `r(rc)`/`r(file)`, `cert_svg_texts` -> `r(n)`/`r(list)`, `svg_texts` entries with `text`/`x`/`y`); section 13 (`scripts/extract_text_truth.do` with its `zp id group dataset body opts control` registration and its `python:` block, `test/fixtures/text_truth.json` group `title`).
- **Blocks:** section 19.
- **Parallel batch:** 3. **Can run with:** 11, 12, 18.
- Why: the cscript reads twoway's SVG through section 02's helper; this section's probes live in the extract script section 13 creates, and 13 is batch 2, so it has merged before this section starts; the fixture is regenerated once here (rule R5) and never hand-merged. No batch-3 section touches `_dash_apply_legend`, `_dash_legend_entries`, `_DASH_LEGEND_*` or dash_parse.mata 4751-4766. S18 and S11 (batch 3) append their own blocks to `test/test_gaps2_truth.cscript`; the merger orders the blocks by section number (R1), so the three appends never conflict on content.

## Evidence

Anchors are at `91d97be` (research report A §B5, W §1a/§1i, D §5).

### The keys, built without numbers

`_dash_apply_legend` (15780-15983) rebuilds the keys in place and returns early if `fig.legend` is empty (15819-15822):

```python
    if legend is not None and plot_renderers:
        live = [(plot, [r for r in rends if r in fig.renderers])
                for plot, rends in plot_renderers]
        items = [LegendItem(label={"value": lbl}, renderers=rends)
                 for lbl, rends in _dash_legend_entries(
                     live, var_labels or {}, default_level)]
        if items:
            legend.items = items
```

`_dash_legend_entries` (19754-19792) makes one key per layer and two for a CI type (band `"{lvl:g}% CI"` then `"Fitted values"`), and SKIPS a layer whose renderers are empty or all swatches (19772-19774), so a displayed position can drift from Stata's plot number. `_dash_plot_style_indices` (19513-19541) is Stata's numbering, a CI fit counting as two (band n, line n+1), pinned by `test/fixtures/ci_plot_index_truth.json`. Both renderers hand over EVERY layer in draw order: saved `_plot_renderers.append((plot, _layer_renderers))` (22277) and template `_leg_bounds.append((len(fig.renderers), plot))` per plot (26296) turned into `_plot_rends` (26423-26428). `_dash_legend_entries` is also called directly by `test/test_server_layer_defects.py:1038-1063`, which must keep passing.

### order(), label(), lastlabel()

Step 2, `order()` (15847-15852):

```python
    _order = _dash_legend_arg(_calls, ("order",))
    if _order is not None and legend is not None:
        wanted = [int(t) for t in re.findall(r"\d+", _order)]
        current = list(legend.items)
        legend.items = [current[i - 1] for i in wanted
                        if 1 <= i <= len(current)]
```

Step 5, `label()` by displayed position after the reorder (15929-15939):

```python
            lm = _DASH_LEGEND_LABEL_RE.fullmatch(_arg)
            idx = int(lm.group(1)) - 1
            if 0 <= idx < len(legend.items):
                legend.items[idx].label = {
                    "value": "\n".join(_textbox_lines(lm.group(2)))}
```

`_DASH_LEGEND_SUBOPTS` (18839-18841) lacks `lastlabel`, so `_dash_legend_unsupported` (18850) names it. `_dash_legend_parts` (15682-15703) gives `(words, calls)` through `_dash_by_tokens`; `_dash_legend_arg` (15706-15717) returns the FIRST matching call. `_DASH_LEGEND_LABEL_RE = re.compile(r"\s*(\d{1,6})(\s.*)", re.S)` (18847) bounds the key number to six digits. Step 8 (15966-15983) hides the series legend when `len(legend.items) < 2` unless `on`.

### Stata's rule (D §5, `legend_options.sthlp`)

`orderinfo` (`:104-111`): `{#|-} ["text" ["text" ...]]` repeated. "A dash specifies that text be inserted into the legend" (`:231-234`); `order(1 - "Predicted" 2 3)` adds a text-only line; `order(1 - " " "Predicted" 2 3)` a blank line then the text -- "we typed " " and not "". Typing "" would insert nothing" (`:254-267`); `order(1 "Observed 1992" ...)` overrides key 1's text (`:270-275`); `order(1 2 3)` with four keys drops key 4 (`:225-227`). `labelinfo` (`:113-119`): `# "text" ["text" ...]`, one key per `label()`, each string a line. `lastlabel()` (`:292-314`): "the last label to be applied and overrides any text specified in order() or label() ... If the text for a key is modified by the order() suboption, you cannot change the label with the label() suboption, but you can with lastlabel()"; it indexes by the key position on the graph after `order()` (`:305-309`). Default key text is the variable label, else the name (`:818-820`); a computed layer reads "Fitted values". Legend shown only with two or more keys unless `on`/`off` (`:698-703`). Repeated `legend()` options are merged-implicit: the last of each sub-option wins (`:34-35`).

### Bokeh (W §1a, §1i, measured on 3.8.0 and 3.9.0)

`LegendItem(label=value(text), renderers=[])` passes validation and BokehJS draws the label with an empty glyph cell; no placeholder glyph is needed. A bare string assigned to `item.label` AFTER construction is a field name, so any later rename must use `{"value": text}` or `value(text)`; dash builds labels as `{"value": ...}` (15838) already. `Legend.items` order is display order; reassigning the list is a document change.

### dash.ado's merge of a repeated legend()

`_dash_rep_subkey` (dash_parse.mata 4751-4766) keys `label(# ...)` by its number for category "I" so `legend(label(1 "A")) legend(label(2 "B"))` keeps both (TP-14a row r25); `lastlabel` is not keyed, so two `lastlabel()` calls across repeated `legend()` options collapse into the last:

```mata
    if (nm == "label" & cat == "I" & p) {
        v = strtrim(_dash_rep_value(tok))
        nm = nm + " " + (strpos(v, " ") ? substr(v, 1, strpos(v, " ") - 1) : v)
    }
```

`_dash_check_legend` (dash.ado 1750-1780) refuses only the bare words `top`/`bottom`/`left`/`right`; a `-` inside `order()` is inside parentheses and never seen by it.

### Fixtures on disk

`test/fixtures/axis_truth.json` `findings.legend_cases` already records `c_order21` (`order(2 1)`), `c_order1` (`order(1)`) and `c_order_relab` (`order(2 "FIT" 1 "RAW")`) with `keys_in_drawn_order`, measured by the `legend(off)` companion diff; no probe covers `-`, `label()` beside `order()`, `lastlabel()` or CI numbering. This section adds those to `text_truth.json`.

### Existing tests that pin today's behaviour (flip or extend, never delete)

- `test/test_axis_options.py::TestLegendOptions::test_order_reorders_the_keys` (399) and `test_order_can_drop_a_key` (407): pass on two keys; extend with `order(2 "FIT" 1 "RAW")` pinned to `axis_truth.json`'s `c_order_relab`.
- `test/test_graph_options.py::TestLegendLabels` (452-600): `label(1 ...)` on the first item passes; add `order(2 1) label(1 "Data")`.
- `test/test_server_legend.py::TestTheLegendOptionsNowReachIt::test_label_overrides_the_series_name` (169): add order text and a `-` row served.
- `test/test_mode_parity.py` `CORPUS` cases "legend(order(2 1))" (1203) and `legend(label(1 "Cars") cols(2))` (1207): add four cases.
- `test/test_ci_plot_index.py::TestALayerDrawsInItsPlotNumber::test_the_legend_keeps_its_keys_in_order` (276): a guard for the four-key order; add `order(4 1)`.
- `test/test_suboption_warnings.py::TestTheHonouredOnesStayQuiet` (100-119): `lastlabel` must now be quiet; `SUBOPTIONS` row "legend span stack holes" keeps naming `span`, `stack`, `holes(1)`.
- `test/test_adversarial_matrix.py::TestTextPlotOptionBounds::test_a_legend_order_of_a_hundred_thousand_keys_is_bounded` (2913): a guard for shared items and bounded time.
- `test/test_textbox_multiline.py::TestALegendLabelIsReadAsStataReadsIt` (800) and `TestALegendLabelAdversarial` (835): guards for `label()` text reading.
- `test/test_server_layer_defects.py` (1038-1063) direct `_dash_legend_entries` calls: guards.
- `test/test_help_claims_7.cscript` HC7-01 `order(2 1) cols(1) size(small)`: guard.
- `test/test_twoway_option_parity.cscript` TP-14a r24-r26, r31 (repeated `legend()`): guards; the new `lastlabel` pair is LO-08 in the `* ==== S15 B5: legend order and labels ====` block of `test/test_gaps2_truth.cscript` (D11).

## User stories

- **US-15.1** As the Stata user pasting twoway syntax, I want `legend(order(1 "Group 2" 3 "Three"))` to draw keys 1 and 3 with those texts, so that a reordered, retitled legend pastes unchanged.
- **US-15.2** As the Stata user, I want `label(1 "Data")` to name plot 1 wherever `order()` puts it, so that key numbers mean what they mean in twoway.
- **US-15.3** As the Stata user, I want `order(1 - "Note" 2)` to draw a text-only row between the keys, and `- " " "Note"` a blank line before it.
- **US-15.4** As the Stata user, I want `lastlabel(2 "L")` to be the last word, over `order()` text and `label()`, so that twoway's precedence holds.
- **US-15.5** As the Stata user, I want a `lfitci` layer's band and line to be keys n and n+1 as twoway numbers them, so that `order()` on a graph with a confidence band picks the right key.
- **US-15.6** As the dashboard viewer, I want the saved page and the served app to show the same legend rows in the same order.
- **US-15.7** As the maintainer, I want B5 closed by a test that failed at `91d97be`, recorded in BUGS.md and CHANGELOG.

## Business requirements

- **BR-15.1** `order()` selects and orders keys by Stata's plot number; a number listed twice draws the key twice; a number that is no key draws nothing; text after a number replaces that key's text.
- **BR-15.2** `-` followed by strings draws a text-only row at that position, one line per string; `- " "` draws a blank row; `- ""` draws nothing.
- **BR-15.3** `label(# "text" ...)` names plot #, one line per string, regardless of `order()`; `order()` text on the same key wins over `label()`.
- **BR-15.4** `lastlabel(# "text" ...)` is applied last and wins over both, indexed as `legend_options.sthlp:305-309` says and as `text_truth.json`'s `l_lastlabel_pos` measures.
- **BR-15.5** A CI layer's band is key n and its line key n+1; a layer that drew nothing still consumes its number.
- **BR-15.6** Repeated `legend()` options carrying `lastlabel()` for different keys keep every one, as `label()` already does.
- **BR-15.7** `order()`, `label()` and `lastlabel()` print nothing; sub-options still not drawn are named as today.
- **BR-15.8** Every drawn key text and order equals twoway's SVG legend for the same command, recorded in `test/fixtures/text_truth.json`; both render modes agree.

## Technical requirements

- **TR-15.1** New `_dash_parse_legend_order(arg)` beside `_dash_legend_parts` (15682): one linear pass over `arg` with `_textbox_string_end` for strings; returns a list of `(key, lines)` where `key` is an `int` (at most six digits, as `_DASH_LEGEND_LABEL_RE` bounds) or the string `"-"`, and `lines` is the list of strings that followed it (a compound string keeps what it holds; a bare word is a line, as `_textbox_lines` reads one), empty when none followed. An empty string `""` ends that entry's lines as `textbox.class` ends a textbox's. Any other token is skipped.
- **TR-15.2** New `_dash_legend_keys(plot_renderers, var_labels=None, default_level=None)` beside `_dash_legend_entries` (19754): returns `[(number, text, renderers)]` numbered by Stata's rule: `n` starts at 1; a layer of a `_DASH_CI_TYPES` type yields `(n, "{lvl:g}% CI", band_renderers)` and `(n + 1, "Fitted values", line_renderers)` for whichever of the two has renderers and advances `n` by 2; any other layer yields `(n, _dash_legend_key(plot, var_labels), renderers)` when it has non-swatch renderers and advances `n` by 1 either way. `_dash_legend_entries` becomes `[(t, r) for _, t, r in _dash_legend_keys(...)]` so its direct tests hold.
- **TR-15.3** `_dash_apply_legend` (15780) step 1 builds `texts = {n: [text]}` from `_dash_legend_keys`, applies every `label(#)` call in order (`_DASH_LEGEND_LABEL_RE`, `_textbox_lines`, last per number wins), then the LAST `order()` call's entries (text after a number replaces `texts[n]`), then builds ONE `LegendItem(label={"value": "\n".join(texts[n])}, renderers=rends)` per key in `items_by_n`. Step 2 builds the display sequence: with `order()`, each numbered entry that is a key appends `items_by_n[n]` (the same object on a repeat) and each `-` entry with lines appends a new `LegendItem(label={"value": "\n".join(lines)}, renderers=[])`; without `order()`, every key in number order. `lastlabel(#)` calls are applied last, per the fixture: by drawn position in the sequence (replacing that position's item with a new `LegendItem` carrying the same renderers and the new label so a shared object is not renamed elsewhere), or by key number before the items are built if `l_lastlabel_pos` measures that. `legend.items = sequence`; the visibility rule counts `len(sequence)`. A `label(#)` or `lastlabel(#)` whose `#` is no key (`0`, or beyond the count) is ignored silently, as twoway ignores it; an `order()` number that is no key draws nothing. Steps 3, 4, 6, 7 are unchanged.
- **TR-15.4** `_DASH_LEGEND_SUBOPTS` (18839) gains `"lastlabel"`; `_DASH_LEGEND_LABEL_RE` (18847) is reused for `lastlabel`.
- **TR-15.5** `_dash_parse_legend_order` and `_dash_legend_keys` are added to the function copy list (24466-24687) and to `test/function_test_map.py`; both call sites (`_rebuild_legend` 21794-21805; template 26435-26438) are unchanged in signature.
- **TR-15.6** dash_parse.mata `_dash_rep_subkey` (4751-4766): `if ((nm == "label" | nm == "lastlabel") & cat == "I" & p)` keys `lastlabel(# ...)` by its number. `test/program_coverage_map.py`'s `_dash_rep_subkey` entry (:451, today `("test_twoway_option_parity.cscript:TP-14",)`) gains `"test_gaps2_truth.cscript:LO-08"`.
- **TR-15.7** Security (rule 1): a `-` row's text and every key text reach `LegendItem.label` as a value, the DOM text-node sink `test_label_sinks.py` classifies, never HTML; the parser bounds numbers to six digits and is linear in the argument's length; no `eval`, no regex over the whole legend text.
- **TR-15.8** `scripts/extract_text_truth.do` gains the `legend` probes below in the marked region; `test/test_legend_order.py` pins them; the block `* ==== S15 B5: legend order and labels ====` (LO-01..LO-08) appended to `test/test_gaps2_truth.cscript` compares a live twoway export with dash's page (D11/C7).
- **TR-15.9** dash.sthlp 2290-2293 (`order()`), a new `lastlabel()` synopt, and the paragraph at 2307-2312; CHANGELOG (D2, AMEND-1 A): the B5 line replaces, in place, the marker `<!-- WP-28 B5 -->` that S01 put in the bold group `**WP-28 (GAPS2 audit, 25sep2026)**` at the end of the release's `### Results that change` list (CHANGELOG.md:10, after the `**Colours, schemes and appearance**` group, before `### Security`); the line ends `(WP-28, B5)` and nothing is added anywhere else; BUGS.md: one closed entry appended at the end of the file (S01 TR-01.8) with `- Resolution: Fixed <ddmonyyyy> (WP-28, B5). <what changed>. Pinned by test/<file>::<Class>::<test>.` and the residual as `Residual, deferred (WP-28): ...` at its end.
- **TR-15.10** The LO cases are a block appended to `test/test_gaps2_truth.cscript` (D11/C7), the one new certification script of WP-28: S02 created it (it opens with the standard Python gate, loads `cert_helpers.do` and `cert_svg.do`, and ends with the line `* ==== append new blocks above this line ====`), registered it as runner block `// 67.` in batch 1 and alone set `test/test_cscript_hygiene.py`'s pins (`len(_CSCRIPTS) == 66` at :292, `len(names) == 48` at :308). The block has AMEND-1 H's form: `* ==== S15 B5: legend order and labels ====`, then `local only : env GAPS2_ONLY` and `if inlist("`only'", "", "S15") { … }` holding `display as text "S15 start `c(current_time)'"`, the cases (each displaying `LO-0n PASS`) and `display as text "S15 end `c(current_time)'"`, closed by `* ==== end S15 ====`; it is inserted above the script's last line, in section order (R1: the merger places it). This section edits neither `test/run_all_cscripts.do` nor the pins. The case ids keep the `LO-` prefix so `program_coverage_map.py` and BUGS.md cite `test/test_gaps2_truth.cscript LO-08`.

## Boundaries

- Do not touch `_dash_move_legend`, the chrome/placement/cols/rows/size steps, `_dash_legend_parts`, `_dash_legend_arg`'s first-match semantics for other callers, the colour-key legend (`_COLORVAR_LEGEND_NAME`, section 16), or `_dash_plot_style_indices`.
- Textbox sub-options inside `label()`/`order()` text (`label(1 "x", size(large))`) are not read here; they are named as today.
- `legend(all)`, `holes()`, `stack`, `textfirst`, `colfirst`, `symplacement()` and the other legend sub-options stay named.
- A layer that drew no renderers has no key; `order()` referencing its number draws nothing (twoway would draw the key). Recorded in the BUGS.md entry as a residual, not fixed.
- A key text's own textbox styling, `keygap()`, `symxsize()` and the legend's `title()` are out of scope.
- PRD §7 exclusions and DISCOVERY Q22 hold.

## Stata truth

Appended to `scripts/extract_text_truth.do` (section 13) in its `* ---- section 15: legend probes ----` region, using the sixth `control` argument for the `legend(off)` companion, exactly the pairing `extract_axis_truth.do:216-219` uses; the companion is registered as its own probe with an empty control. Two-plot body `P2` = `twoway (scatter mpg weight) (lfit mpg weight)`, three-plot `P3` = `twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight)`, CI body `PC` = `twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)`:

```
zp "l_two"               "legend" "auto" "<P2>" "" "l_two__off"
zp "l_two__off"          "legend" "auto" "<P2>" "legend(off)" ""
zp "l_order_text"        "legend" "auto" "<P3>" `"legend(order(1 "Group 2" 3 "Three"))"' "l_order_text__off"
zp "l_order_text__off"   "legend" "auto" "<P3>" "legend(off)" ""
zp "l_order_label"       "legend" "auto" "<P2>" `"legend(order(2 1) label(1 "Data"))"' "l_order_label__off"
zp "l_label_order"       "legend" "auto" "<P2>" `"legend(label(1 "Data") order(2 1))"' "l_label_order__off"
zp "l_order_beats_label" "legend" "auto" "<P2>" `"legend(order(1 "O") label(1 "L"))"' "l_order_beats_label__off"
zp "l_dash_text"         "legend" "auto" "<P2>" `"legend(order(1 - "Note" 2))"' "l_dash_text__off"
zp "l_dash_blank"        "legend" "auto" "<P2>" `"legend(order(1 - " " "Note" 2))"' "l_dash_blank__off"
zp "l_dash_empty"        "legend" "auto" "<P2>" `"legend(order(1 - "" 2))"' "l_dash_empty__off"
zp "l_dash_two_lines"    "legend" "auto" "<P2>" `"legend(order(1 - "Line 1" "Line 2" 2))"' "l_dash_two_lines__off"
zp "l_lastlabel_pos"     "legend" "auto" "<P2>" `"legend(order(2 1) lastlabel(2 "L"))"' "l_lastlabel_pos__off"
zp "l_lastlabel_all"     "legend" "auto" "<P2>" `"legend(order(2 "Y" 1) label(2 "X") lastlabel(2 "L"))"' "l_lastlabel_all__off"
zp "l_lastlabel_dash"    "legend" "auto" "<P2>" `"legend(order(1 - "Note" 2) lastlabel(3 "L"))"' "l_lastlabel_dash__off"
zp "l_lastlabel_two"     "legend" "auto" "<P2>" `"legend(lastlabel(1 "A") lastlabel(2 "B"))"' "l_lastlabel_two__off"
zp "l_lastlabel_repeat"  "legend" "auto" "<P2>" `"legend(lastlabel(1 "A")) legend(lastlabel(2 "B"))"' "l_lastlabel_repeat__off"
zp "l_label_two_lines"   "legend" "auto" "<P2>" `"legend(label(1 "A" "B"))"' "l_label_two_lines__off"
zp "l_order_repeat"      "legend" "auto" "<P2>" `"legend(order(1 2 1))"' "l_order_repeat__off"
zp "l_ci_default"        "legend" "auto" "<PC>" "" "l_ci_default__off"
zp "l_ci_order_last"     "legend" "auto" "<PC>" `"legend(order(4 1))"' "l_ci_order_last__off"
zp "l_ci_order_band"     "legend" "auto" "<PC>" `"legend(order(2 3))"' "l_ci_order_band__off"
zp "l_one_dash"          "legend" "auto" "twoway scatter mpg weight" `"legend(order(1 - "Only"))"' "l_one_dash__off"
```

with a `<id>__off` line (`legend(off)` appended to the same body) for every id above. The trailing python block records for a `legend` probe, besides the common keys, `"keys_in_drawn_order"`: the `added_texts` (bare minus off) ordered by each `svg_texts` entry's `y` then `x` (top to bottom, then left to right), as `extract_axis_truth.do` orders `keys_in_drawn_order`. Section 13's block records `texts` in document order from the `text` field only; for group `legend` the block must keep the per-entry dicts of `svg_texts` (S02 TR-02.1: `text`, `x`, `y`, `size`, ...) until it has sorted them, and only then project to `text`. `l_dash_blank`'s blank row is invisible in the SVG; the fixture records the visible keys and the pytest asserts dash's rows minus its blank row equal them.

Run in batch 3, on a tree where section 13 has merged, through the slot wrapper (D6, `index.md` step 0; it takes one of three `mkdir` slots, `cd`s into the scratch directory, sets `STATATMP=/tmp/dash-s15/tmp/` with the trailing slash and runs the CLAUDE.md rule 10 console command `arch -arm64 /usr/local/bin/stata-mp -b do`; never the GUI):

```
scripts/stata_slot.sh /tmp/dash-s15 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_text_truth.do
```

(the extract script is given to the wrapper directly because, like `extract_axis_truth.do:85`, it sets `global ZA_REPO` itself and every path in it hangs off that global; a cscript is not run this way — see 15-02 for the driver do-file, AMEND-1 B). Then `git add -f test/fixtures/text_truth.json`. The fixture is named by `test_legend_order.py` (and read by the S15 block of `test/test_gaps2_truth.cscript`) as well as section 13's readers. Its `_meta` carries D12's four keys -- `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` and `extracted` -- written by section 13's mechanism (C8: the do-file captures `git rev-parse HEAD` into a tempfile with `shell`, reads it into a local, and the python block reads it through `Macro.getLocal`; never `shell=True`, never a Stata call from the python block); the regeneration here re-stamps them and `TestTheFixture::test_meta_carries_the_four_provenance_keys` asserts the four keys exist and compares nothing.

## TDD test stubs

New file `test/test_legend_order.py` with a `_legend(mode, plots, legend, wd)` helper modelled on `test_ci_plot_index._figure` (166-190) returning the one figure's `Legend` and a `truth()` fixture like `test_axis_options.py:40-47` that fails, never skips, on a missing fixture. Regression stubs that fail at `91d97be` first.

- Test: `order(1 "Group 2" 3 "Three")` on scatter+lfit+qfit draws two rows, `Group 2` (key 1's renderers) and `Three` (key 3's), in both modes, equal to `truth()['probes']['l_order_text']['keys_in_drawn_order']` — `test_legend_order.py::TestOrderText::test_text_after_a_number_retitles_that_key` (fails: three default keys).
- Test: `order(2 1) label(1 "Data")` draws `Fitted values` then `Data`, `Data`'s renderers being the scatter's — `::TestLabelByNumber::test_label_names_the_plot_not_the_position` (fails: `Data` on the fit).
- Test: `label(1 "Data") order(2 1)` gives the same — `::TestLabelByNumber::test_sub_option_order_does_not_matter`.
- Test: `order(1 "O") label(1 "L")` draws `O` — `::TestLabelByNumber::test_order_text_beats_label`.
- Test: `order(1 - "Note" 2)` draws three rows, the middle a `LegendItem` with `renderers == []` and label `Note`; `- " " "Note"` gives ` \nNote`; `- ""` gives two rows — `::TestTextOnlyRows::test_a_dash_inserts_a_text_row` (fails: two rows).
- Test: `lastlabel(2 "L")` beside `order(2 "Y" 1) label(2 "X")` draws what the fixture's `l_lastlabel_all` draws, and `order(2 1) lastlabel(2 "L")` what `l_lastlabel_pos` draws — `::TestLastLabel::test_lastlabel_wins_over_order_and_label` (fails: `lastlabel` named, not applied).
- Test: `lastlabel` is not named in either mode — `::TestLastLabel::test_lastlabel_is_quiet`.
- Test: `lastlabel(1 "A") lastlabel(2 "B")` relabels both — `::TestLastLabel::test_two_lastlabels`.
- Test: scatter+lfitci+scatter with `order(4 1)` draws the second scatter's key then the first's; `order(2 3)` the band then the fit — `::TestKeysAreNumberedByPlot::test_a_ci_layer_is_two_keys` (fails: key 4 does not exist by position).
- Test: `_dash_legend_keys` numbers `[(1, "mpg"), (2, "95% CI"), (3, "Fitted values"), (4, "price")]` for that graph and consumes a number for a layer with no renderers — `::TestKeysAreNumberedByPlot::test_numbers_unit`.
- Test: `_dash_parse_legend_order` unit cases: `'1 "Group 2" 3 "Three"'` → `[(1, ["Group 2"]), (3, ["Three"])]`; `'1 - "Note" 2'` → `[(1, []), ("-", ["Note"]), (2, [])]`; `'1 - " " "Note" 2'`; `'1 - "" 2'` → `[(1, []), ("-", []), (2, [])]`; `'0 "z"'` → `[(0, ["z"])]` (the parser keeps it; the applier ignores a key that does not exist); compound strings; `'2 "a" "b"'` two lines; a seven-digit number skipped; 100,000 tokens parsed under a second — `::TestTheParser::test_cases` (fails: `AttributeError`).
- Test: `label(9 "x")` and `label(0 "z")` on the two-key graph change nothing and print nothing in either mode; `order(0 1)` draws key 1 alone — `::TestLabelByNumber::test_a_label_for_no_key_is_ignored` (edge case, requirements review F-22).
- Test: `order(1 2 1)` draws three rows from two `LegendItem` objects — `::TestOrderText::test_repeats_share_one_item`.
- Test: `order(1 - "Only")` on a one-key graph draws whatever `l_one_dash` measures (two rows shown, or hidden) — `::TestTextOnlyRows::test_one_key_and_a_text_row`.
- Test: the saved page's embedded document lists the `LegendItem` labels in the same order as the served document for every case above — `::TestBothModes::test_the_page_and_the_app_agree`.
- Test: the served app source defines `_dash_parse_legend_order` and `_dash_legend_keys` — `::TestTheServedCopy::test_the_names_are_copied`.
- Test: `axis_truth.json`'s `c_order_relab` (`order(2 "FIT" 1 "RAW")`) equals dash's rows — `test_axis_options.py::TestLegendOptions::test_order_text_matches_the_measured_legend` (fails: default texts).
- Test: `test_graph_options.py::TestLegendLabels::test_label_names_the_key_number_not_the_position`.
- Test: `test_server_legend.py::TestTheLegendOptionsNowReachIt::test_order_text_and_a_text_only_row_are_served`.
- Test: `test_ci_plot_index.py::TestALayerDrawsInItsPlotNumber::test_order_counts_a_ci_layer_as_two_keys` (both modes).
- Guard (not a regression test: both modes are equally wrong before the fix, so the four cases may pass at `91d97be`): `test_mode_parity.py` `CORPUS` cases `legend(order(1 "Group 2" 3 "Three"))`, `legend(order(2 1) label(1 "Data"))`, `legend(order(1 - "Note" 2))`, `legend(order(2 1) lastlabel(2 "L"))` -- appended to `CORPUS` only; this section edits neither `ALLOWED` nor `_MUST_WARN` (rule R6).
- Test: `test_suboption_warnings.py::TestTheHonouredOnesStayQuiet` row `{"legend": 'order(1 - "Note" 2) lastlabel(2 "L")'}`.
- Guards that must keep passing: `test_adversarial_matrix.py` 2913 (two `LegendItem` models, 66,666 rows, under 30 s); `test_server_layer_defects.py` 1038-1063; `test_textbox_multiline.py` 800-900; HC7-01; TP-14a r24-r26, r31.
- Guard (D12/C8; passes before 15-05 because section 13's fixture already carries the stamp, and must still pass after the regeneration): `test/fixtures/text_truth.json` `_meta` holds the keys `stata_version`, `born_date`, `dash_commit` and `extracted`; nothing compares their values — `test_legend_order.py::TestTheFixture::test_meta_carries_the_four_provenance_keys` (reads the JSON directly, not through `truth()`).
- Truth-script block `* ==== S15 B5: legend order and labels ====` appended to `test/test_gaps2_truth.cscript` (D11/C7, form AMEND-1 H), cases LO-01..LO-08: for each of `order(1 "Group 2" 3 "Three")`, `order(2 1) label(1 "Data")`, `order(1 - "Note" 2)`, `order(2 1) lastlabel(2 "L")`, `order(4 1)` on the CI body, `order(1 2 1)`, `label(1 "A" "B")`: export twoway's graph bare and with `legend(off)` through `cert_svg_export` (two `name()`s), run `cert_svg_texts, file()` on each and read the two `r(list)` JSON-lines files in the cscript's `python:` block (each line's `text`), take the bare file's texts minus the off file's in the bare file's order, and compare them with the `LegendItem` labels of dash's built page, read in `Legend.items` order by a `python:` block over the page's embedded document (as `test_textbox_multiline.py::_page_legend_labels` reads it); LO-08 `legend(lastlabel(1 "A")) legend(lastlabel(2 "B"))`: the stored spec's `legend` value holds both calls and the page draws `A` and `B`.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| `order()` parser | pytest `TestTheParser` | none | n/a |
| Key numbering, CI as two | pytest `TestKeysAreNumberedByPlot`; cscript LO-05 | `text_truth.json` `l_ci_*` | yes |
| `order()` text and selection | pytest `TestOrderText`; cscript LO-01, LO-06 | `text_truth.json`, `axis_truth.json` `c_order_relab` | yes |
| `label()` by number | pytest `TestLabelByNumber`; cscript LO-02 | `text_truth.json` | yes |
| `-` rows | pytest `TestTextOnlyRows`; cscript LO-03 | `text_truth.json` | yes |
| `lastlabel()` | pytest `TestLastLabel`; cscript LO-04, LO-08 | `text_truth.json` | yes |
| Repeated `legend()` with `lastlabel()` | cscript LO-08 (Mata) | live twoway export | saved page |
| Both modes agree | pytest `TestBothModes`, `test_mode_parity` cases | none | yes |
| Served copy carries the names | pytest `TestTheServedCopy` | none | served |
| Bounded, shared items | `test_adversarial_matrix.py` 2913 (guard) | none | saved |
| Fixture committed and named | `test_fixtures_are_committed.py` | `text_truth.json` | n/a |
| Fixture provenance stamp (D12) | pytest `TestTheFixture` | `text_truth.json` `_meta` | n/a |

Acceptance criteria:
- **AC-15.1** Every stub passes; each regression stub failed on the pre-fix tree with the failure recorded as a `Regression:` line in the B5 commit's message (S01 TR-01.9).
- **AC-15.2** The full pytest suite (`python3 -m pytest test/ -q`, once, before the commit) is green under both interpreters with no skip added; `test/test_gaps2_truth.cscript` (its `* ==== S15 B5: legend order and labels ====` block LO-01..LO-08 among the blocks of the sections merged before it), `test_help_claims_7.cscript` and `test_twoway_option_parity.cscript` pass under Stata's Python, each run through its driver do-file.
- **AC-15.3** BUGS.md holds the closed B5 entry (appended at the end, `- Resolution: Fixed <ddmonyyyy> (WP-28, B5). ...`) naming its tests; dash.sthlp's legend synopts and paragraph updated; the `<!-- WP-28 B5 -->` marker in the `**WP-28 (GAPS2 audit, 25sep2026)**` group of `### Results that change` is replaced by the line listing the four changed legends and ending `(WP-28, B5)`, and `grep -c '<!-- WP-28 B5 -->' CHANGELOG.md` prints 0.
- **AC-15.4** No `dash:` note is printed for `order()`, `label()` or `lastlabel()` in either mode.

## Tasks

Commit boundary: **one commit (B5)** holding 15-01 to 15-09, subject ending `(GAPS2 B5)`, body per S01 TR-01.9 opening with the saved failure text; the full pytest suite runs green once before it (CLAUDE.md rules 4 and 11). Every Stata run goes through `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6, `index.md` step 0: three `mkdir` slots). No AI references anywhere.

<task type="auto" id="15-01">
  <name>Write the failing tests for the section</name>
  <files>test/test_legend_order.py</files>
  <action><![CDATA[
    Create `test/test_legend_order.py` with a module docstring stating GAPS2 B5's four measured symptoms and every class and test named in "TDD test stubs" under that file, with exactly those names (including `TestLabelByNumber::test_a_label_for_no_key_is_ignored` and `TestTheFixture::test_meta_carries_the_four_provenance_keys`, which reads the JSON directly and holds before 15-05). Build figures with a `_legend(mode, plots, legend, wd)` helper copied from `test_ci_plot_index._figure` (166-190) that returns the figure's one series `Legend` (skip `_COLORVAR_LEGEND_NAME`), read labels with `test_textbox_multiline._legend_text` and the saved page with `_page_legend_labels` (786-797), and the fixture through a `truth()` fixture that calls `pytest.fail("section 15 task 15-05 must land first: test/fixtures/text_truth.json has no legend group")`. Assert renderers by identity against the layers' renderers (`fig.renderers` order) so `Data` is proven to be the scatter's key. Run the file against the unmodified tree. Do not commit: save the failure output to the scratch directory as `15-01-failure.txt`; it becomes the opening paragraph of the B5 commit (S01 TR-01.9) and the texts it records are the CHANGELOG line's old values (Q24).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_legend_order.py -q 2>&1 | tail -5` reports no collection error, no regression stub passing (only the `_meta` guard `TestTheFixture::test_meta_carries_the_four_provenance_keys` passes, section 13's fixture already carrying the stamp), and the headline failure shows `['mpg', 'Fitted values', 'price']` where `['Group 2', 'Three']` was expected; `<scratch>/15-01-failure.txt` exists.]]></verify>
  <done>Every regression test for B5 existed and failed against the unmodified tree for the reason the gap describes, with no product file changed and nothing committed.</done>
</task>

<task type="auto" id="15-02">
  <name>Append the legend block to the truth script</name>
  <files>test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
    Insert into `test/test_gaps2_truth.cscript` (S02 created it in batch 1 and registered it as runner block `// 67.`; it opens with the standard Python gate, loads `cert_helpers.do` and `cert_svg.do` after its `cscript` line and ends with the line `* ==== append new blocks above this line ====`), above that last line and after the blocks of lower-numbered sections (R1), a block of AMEND-1 H's form: `* ==== S15 B5: legend order and labels ====`, `local only : env GAPS2_ONLY`, `if inlist("`only'", "", "S15") {`, `display as text "S15 start `c(current_time)'"`, the cases, `display as text "S15 end `c(current_time)'"`, `}`, `* ==== end S15 ====`. The cases are LO-01..LO-08 as "TDD test stubs" describes: for each, export twoway's graph twice (bare and with `legend(off)`) through `cert_svg_export` with two `name()`s, run `cert_svg_texts, file()` on both, read the two `r(list)` JSON-lines files in a `python:` block (each line's `text`), take the bare texts minus the off texts in the bare file's order, and compare them with the `LegendItem` labels of dash's built page, read in `Legend.items` order from the page's embedded document (as `test_textbox_multiline.py::_page_legend_labels` reads it: the `Legend` whose `name` is not `_dash_clegend`, each item's `label.value` and renderer count); LO-08 (`legend(lastlabel(1 "A")) legend(lastlabel(2 "B"))`) also asserts the stored spec's `legend` value holds both calls. Each case displays `LO-0n PASS` or `LO-0n FAIL: <why>` through the script's PASS/FAIL helper and never `exit`s on a failure, so the blocks after it still run. Edit neither `test/run_all_cscripts.do` nor `test/test_cscript_hygiene.py` (D11: S02 alone set the pins, 66 and 48, for this script). Run the block alone against the unmodified tree through the driver of AMEND-1 B: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_gaps2_truth.cscript > /tmp/dash-s15/run_test_gaps2_truth.do` then `GAPS2_ONLY=S15 scripts/stata_slot.sh /tmp/dash-s15 /tmp/dash-s15/run_test_gaps2_truth.do`, and append the LO lines of `/tmp/dash-s15/run_test_gaps2_truth.log` to `<scratch>/15-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^\* ==== S15 B5: legend order and labels ====' test/test_gaps2_truth.cscript` prints 1, `grep -c '^\* ==== end S15 ====' test/test_gaps2_truth.cscript` prints 1, the S15 block sits above `* ==== append new blocks above this line ====`, and `grep -c 'LO-0[1-8]' test/test_gaps2_truth.cscript` is at least 8; `/tmp/dash-s15/run_test_gaps2_truth.log` shows `S15 start`, `LO-01 FAIL` on the default texts `mpg` / `Fitted values` / `price`, `LO-04 FAIL` on `lastlabel` being named, and `S15 end`; `git diff --stat test/run_all_cscripts.do test/test_cscript_hygiene.py` prints nothing.]]></verify>
  <done>The eight legend cases were appended to the shared truth script as the S15 block and failed against the unmodified tree for the reasons the gap describes, with the runner and the hygiene pins untouched.</done>
</task>

<task type="auto" id="15-03">
  <name>Extend the pinned legend tests, first group</name>
  <files>test/test_axis_options.py, test/test_graph_options.py, test/test_server_legend.py</files>
  <action><![CDATA[
    In `test/test_axis_options.py::TestLegendOptions` add `test_order_text_matches_the_measured_legend`: `order(2 "FIT" 1 "RAW")` on `_TWO` draws `truth()['findings']['legend_cases']['c_order_relab']['keys_in_drawn_order']` (already in `axis_truth.json`), and leave `test_order_reorders_the_keys` and `test_order_can_drop_a_key` as they are. In `test/test_graph_options.py::TestLegendLabels` add `test_label_names_the_key_number_not_the_position` (`order(2 1) label(1 "Data")` -> `["Fitted values", "Data"]`, `Data`'s renderer being the scatter). In `test/test_server_legend.py::TestTheLegendOptionsNowReachIt` add `test_order_text_and_a_text_only_row_are_served` (`order(1 "Cars" - "Note" 2)` -> `["Cars", "Note", "Fitted values"]`, the middle item with no renderers) and `test_lastlabel_is_applied_not_named`. Run the three files and append the new failures to `<scratch>/15-01-failure.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_options.py test/test_graph_options.py test/test_server_legend.py -q -k "order_text or key_number or lastlabel or text_only" 2>&1 | tail -3` shows the four new tests failing and nothing else in those files changed.]]></verify>
  <done>The three files that pin legend behaviour each carried a case that failed on position-based `order()`/`label()` and on a named `lastlabel`.</done>
</task>

<task type="auto" id="15-04">
  <name>Extend the pinned legend tests, second group</name>
  <files>test/test_mode_parity.py, test/test_ci_plot_index.py, test/test_suboption_warnings.py</files>
  <action><![CDATA[
    In `test/test_mode_parity.py` `CORPUS` add, beside 1203-1208, four `_case(...)` entries on `[_sc(), plot_for("lfit")]` (the first on `[_sc(), plot_for("lfit"), plot_for("qfit")]`): `legend(order(1 "Group 2" 3 "Three"))`, `legend(order(2 1) label(1 "Data"))`, `legend(order(1 - "Note" 2))`, `legend(order(2 1) lastlabel(2 "L"))`; touch neither `ALLOWED` nor `_MUST_WARN` (rule R6). In `test/test_ci_plot_index.py::TestALayerDrawsInItsPlotNumber` add `test_order_counts_a_ci_layer_as_two_keys` (both modes: `order(4 1)` -> the second scatter's key then the first's, renderers checked by glyph colour as 276-296 does). In `test/test_suboption_warnings.py::TestTheHonouredOnesStayQuiet` add the row `({"legend": 'order(1 - "Note" 2) lastlabel(2 "L")'}, [plot_for("scatter"), plot_for("lfit")])`. Run the three files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ci_plot_index.py test/test_suboption_warnings.py -q -k "two_keys or lastlabel" 2>&1 | tail -3` shows both new tests failing (`lastlabel` named; key 4 absent); `python3 -m pytest test/test_mode_parity.py -q -k "Group 2 or Data or Note or lastlabel" 2>&1 | tail -3` collects the four guard cases (they may pass, both modes being equally wrong: they are guards, not regression tests, and the commit message says so).]]></verify>
  <done>The parity corpus, the CI plot-index file and the sub-option warnings file each carried the legend cases this section closes.</done>
</task>

<task type="auto" id="15-05">
  <name>Record twoway's legend truth into text_truth.json</name>
  <files>scripts/extract_text_truth.do, test/fixtures/text_truth.json</files>
  <action><![CDATA[
    In `scripts/extract_text_truth.do`'s `* ---- section 15: legend probes ----` region (section 13 created it in batch 2; it is on the tree) add every `zp` line under "Stata truth" with its `__off` companion (44 registrations). In the trailing python block add, for probes of group `legend`, `keys_in_drawn_order` as specified, keeping the per-entry `svg_texts` dicts until they are sorted by `y` then `x` and reusing the `added_texts` computation; touch nothing else in the block. Run `scripts/stata_slot.sh /tmp/dash-s15 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_text_truth.do`; check the log reports every legend probe measured with `rc` 0 and that `l_lastlabel_pos` recorded its keys; this is the ONE regeneration of the fixture (rule R5: never patched by hand) and section 13's `title` records must be unchanged by it, checked probe by probe (AMEND-1 I): `python3 -c "import json,subprocess;o=json.loads(subprocess.run(['git','show','HEAD:test/fixtures/text_truth.json'],capture_output=True,text=True,check=True).stdout)['probes'];n=json.load(open('test/fixtures/text_truth.json'))['probes'];bad=[k for k in o if n.get(k)!=o[k]];print(bad)"` prints `[]`; `git add -f test/fixtures/text_truth.json`. The regeneration re-stamps `_meta` (D12/C8) and keeps its existing keys: section 13's mechanism writes `stata_version`, `born_date`, `dash_commit` (the do-file captured `git rev-parse HEAD` into a tempfile with `shell`, read it into a local, and the python block reads it through `Macro.getLocal`; never `shell=True`, never a Stata call from the python block) and `extracted` -- touch nothing of that mechanism, and check the four keys are present in the regenerated file. Record in the commit message what `l_lastlabel_pos` and `l_lastlabel_dash` measured (position or number), since 15-07 follows it.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/text_truth.json'))['probes'];print(p['l_order_text']['keys_in_drawn_order'], p['l_dash_text']['keys_in_drawn_order'], p['l_lastlabel_pos']['keys_in_drawn_order'], p['l_ci_order_last']['keys_in_drawn_order'])"` prints `['Group 2', 'Three']`, `['mpg', 'Note', 'Fitted values']`, one of `['Fitted values', 'L']` / `['L', 'mpg']`, and `['price', 'mpg']` (or the variable labels twoway draws for them); `python3 -c "import json;m=json.load(open('test/fixtures/text_truth.json'))['_meta'];print(sorted(k for k in m if k in ('stata_version','born_date','dash_commit','extracted')))"` prints all four keys; the probe-by-probe comparison above prints `[]`; `python3 -m pytest test/test_fixtures_are_committed.py test/test_legend_order.py -q -k "committed or TheFixture"` passes.]]></verify>
  <done>twoway's drawn legend text and order for every `order()`, `label()`, `-` and `lastlabel()` case, including CI numbering, was committed in `test/fixtures/text_truth.json` by one regeneration.</done>
</task>

<task type="auto" id="15-06">
  <name>Add the order parser and key list</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Beside `_dash_legend_parts` (15682) add `_dash_parse_legend_order(arg)` per TR-15.1: walk `arg` with an index; on a `"` or `` `" `` take the string with `_textbox_string_end` (an empty string ends the current entry's lines); on `-` followed by a blank or the end start a `"-"` entry; on a run of one to six digits followed by a blank or the end start an `int` entry; on any other run of non-blank characters append it as a line of the current entry when one is open, else skip it; return the entries. Beside `_dash_legend_entries` (19754) add `_dash_legend_keys(plot_renderers, var_labels=None, default_level=None)` per TR-15.2, with the CI band detected as 19777-19781 does, and rewrite `_dash_legend_entries` as the pair projection of it. Add `"lastlabel"` to `_DASH_LEGEND_SUBOPTS` (18839). Add both new names to the function copy list (24466-24687) next to `_dash_legend_entries`, and to `test/function_test_map.py` naming `test/test_legend_order.py::TestTheParser::test_cases` and `::TestKeysAreNumberedByPlot::test_numbers_unit`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import dash_render as d;print(d._dash_parse_legend_order('1 \"Group 2\" - \"Note\" 3 \"\" 2'))"` prints `[(1, ['Group 2']), ('-', ['Note']), (3, []), (2, [])]`; `python3 -m pytest test/test_legend_order.py -q -k "TestTheParser or test_numbers_unit" test/test_server_layer_defects.py -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_function_test_map.py -q` passes.]]></verify>
  <done>`order()` text was parsed as twoway's `orderinfo` grammar in one linear pass and every key carried Stata's plot number in both renderers, with `_dash_legend_entries`'s direct tests still passing.</done>
</task>

<task type="auto" id="15-07">
  <name>Resolve, select, order and insert legend rows</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Rewrite steps 1, 2 and 5 of `_dash_apply_legend` (15834-15852, 15913-15939) per TR-15.3, keeping steps 3, 4, 6, 7 and 8 as they are: build `texts` from `_dash_legend_keys`, apply `label()` calls (all of them, last per number; a number that is no key is ignored silently), then the last `order()` call's entries through `_dash_parse_legend_order`, build one `LegendItem` per key in `items_by_n`, build the sequence (repeats share the object; `-` entries with lines become `LegendItem(label={"value": ...}, renderers=[])`; a number that is no key draws nothing), apply `lastlabel()` last by the rule 15-05 measured (position in the sequence, replacing that position's item with a fresh one, or by number before building if the fixture says so -- write a comment citing the probe), then `legend.items = sequence` and count `len(sequence)` in step 8. Replace the two-line docstring mention of `order()` with the rule and its citation. Run `test/test_legend_order.py`, the five extended files, `test/test_adversarial_matrix.py -k hundred_thousand`, `test/test_textbox_multiline.py -k Legend` and `test/test_label_sinks.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_legend_order.py test/test_axis_options.py test/test_graph_options.py test/test_server_legend.py test/test_ci_plot_index.py test/test_suboption_warnings.py test/test_mode_parity.py test/test_label_sinks.py test/test_textbox_multiline.py -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_adversarial_matrix.py -q -k hundred_thousand 2>&1 | tail -2` passes within its 30 s bound.]]></verify>
  <done>Keys were selected, repeated, ordered, retitled and interleaved with text-only rows by Stata's plot number and precedence in both render modes, with `lastlabel()` applied last and quietly, and the 100,000-key page still held two `LegendItem` models.</done>
</task>

<task type="auto" id="15-08">
  <name>Key lastlabel by number in the repeat merge</name>
  <files>dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    In `dash_parse.mata` `_dash_rep_subkey` (4751-4766) change the condition to `if ((nm == "label" | nm == "lastlabel") & cat == "I" & p)` and extend the comment ("and label(# ...) and lastlabel(# ...) keyed by their number"). No library rebuild exists or is needed: dash_parse.mata is `run` from dash.ado. In `test/program_coverage_map.py` add `"test_gaps2_truth.cscript:LO-08"` to the `_dash_rep_subkey` entry (:451). Run the S15 block through the driver of 15-02 (`GAPS2_ONLY=S15 scripts/stata_slot.sh /tmp/dash-s15 /tmp/dash-s15/run_test_gaps2_truth.do`) and `test/test_twoway_option_parity.cscript` through its own driver (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_twoway_option_parity.cscript > /tmp/dash-s15/run_test_twoway_option_parity.do` then `scripts/stata_slot.sh /tmp/dash-s15 /tmp/dash-s15/run_test_twoway_option_parity.do`).
  ]]></action>
  <verify><![CDATA[`/tmp/dash-s15/run_test_gaps2_truth.log` shows `LO-08 PASS` (the stored `legend` value of `legend(lastlabel(1 "A")) legend(lastlabel(2 "B"))` holds both calls and the page draws `A` and `B`) and every other LO case passing, with `grep -c '^r([0-9]*);' /tmp/dash-s15/run_test_gaps2_truth.log` printing 0; `/tmp/dash-s15/run_test_twoway_option_parity.log` still reports TP-14 PASS; `python3 -m pytest test/test_program_coverage_map.py -q` passes.]]></verify>
  <done>A repeated `legend()` kept every `lastlabel()` for a distinct key, as it keeps every `label()`.</done>
</task>

<task type="auto" id="15-09">
  <name>Close B5 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md (S01 TR-01.8; never mid-file) the closed entry `- [x] Title: legend order() text and label() after order() are applied to the wrong keys` with File Names and Line Numbers (`dash_render.py` `_dash_apply_legend`, `_dash_legend_entries`; `dash_parse.mata` `_dash_rep_subkey`), Description (the four symptoms), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, B5). Keys are numbered by Stata's plot number (a CI layer counting two), order() text and label() resolve by number before selection, - rows are LegendItems with no renderers, lastlabel() is applied last, in both renderers; a repeated legend() keeps every lastlabel(). Pinned by test/test_legend_order.py::TestOrderText::test_text_after_a_number_retitles_that_key, ::TestLabelByNumber::test_label_names_the_plot_not_the_position, ::TestTextOnlyRows::test_a_dash_inserts_a_text_row, ::TestLastLabel::test_lastlabel_wins_over_order_and_label, test/test_gaps2_truth.cscript LO-01..LO-08; fixture test/fixtures/text_truth.json. Residual, deferred (WP-28): a layer that drew nothing has no key, so order() naming its number draws nothing where twoway draws the key.` -- the title holds no `"`. Update dash.sthlp: 2290-2293 `order()` becomes `order({#|-} ["text" ...] ...)` "select and order the keys by plot number, retitle one with text after its number, or insert a text-only line after `-`"; add `{synopt:{cmdab:leg:end(lastlabel(}{it:#} {it:"text"}{cmd:))}}` "the last label applied, over order() and label()"; extend the paragraph at 2307-2312 with the precedence and the CI numbering (band n, line n+1). Grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed lines and update any pin. In `CHANGELOG.md`, replace in place the marker `<!-- WP-28 B5 -->` that S01 put in the bold group `**WP-28 (GAPS2 audit, 25sep2026)**` at the end of the release's `### Results that change` list (CHANGELOG.md:10; D2, AMEND-1 A) with one line ending `(WP-28, B5)` that names each command, the old value as `<scratch>/15-01-failure.txt` recorded it (Q24) and the new value: `legend(order(1 "Group 2" 3 "Three"))` (keys 1, 2, 3 with default text -> keys 1 and 3 titled as given), `legend(order(2 1) label(1 "Data"))` (the fit relabelled -> the scatter), `legend(order(1 - "Note" 2))` (the line dropped -> drawn), `legend(lastlabel(2 "L"))` (named -> applied); add nothing anywhere else in the file. Run the full pytest suite once in the worktree (rule 11: `python3 -m pytest test/ -q`, the section's one full run), then the S15 block through the driver of 15-02; grep the three files and the message for `claude|anthropic`; commit the whole section as ONE commit on the worktree branch `wp28-s15`, subject ending `(GAPS2 B5)`, body opening with `<scratch>/15-01-failure.txt` and carrying the `Regression:` / `Flipped:` / `Fixture: test/fixtures/text_truth.json (scripts/extract_text_truth.do)` / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (`index.md` step 1, AMEND-1 J), after its own `git merge --no-edit main` and the batch's full run.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_examples.py -q` passes; `grep -c '<!-- WP-28 B5 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, B5)' CHANGELOG.md BUGS.md` prints 2; `grep -n 'Group 2\|lastlabel' CHANGELOG.md dash.sthlp BUGS.md | wc -l` is at least 6; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0 and `git log -1 --format=%s | grep -c '(GAPS2 B5)'` prints 1.]]></verify>
  <done>B5 was closed in BUGS.md naming its regression tests, the help documented `order()`'s grammar and `lastlabel()`, the B5 CHANGELOG marker was replaced, and one green commit on the worktree branch `wp28-s15` carried the section for the merger.</done>
</task>

## Section completion criteria

- All 15-01 stubs and the extended cases pass in both modes; each regression stub failed on the pre-fix tree for its recorded reason.
- One commit on the worktree branch `wp28-s15` (landed on `s3-bugs` by the merger), subject ending `(GAPS2 B5)`, holding the failing tests, the fix, the flips, the fixture and the closed BUGS.md entry; no test-only commit exists (D1).
- `test/fixtures/text_truth.json` carries the 22 legend probes with `keys_in_drawn_order` and a `_meta` holding `stata_version`, `born_date`, `dash_commit` and `extracted` (D12) beside its existing keys, was regenerated once with every pre-existing probe unchanged, and is committed.
- The `* ==== S15 B5: legend order and labels ====` … `* ==== end S15 ====` block (LO-01..LO-08, gated by `GAPS2_ONLY`) is in `test/test_gaps2_truth.cscript` above its last line; `test/run_all_cscripts.do` and `test/test_cscript_hygiene.py` are untouched (D11).
- The full pytest suite is green under both interpreters; `test/test_gaps2_truth.cscript`, `test_help_claims_7.cscript` and `test_twoway_option_parity.cscript` pass under Stata's Python with no skip.
- `_dash_parse_legend_order` and `_dash_legend_keys` are in the served copy list and `function_test_map.py`; `_dash_rep_subkey`'s coverage entry names LO-08.
- One closed BUGS.md entry appended at the end with `- Resolution: Fixed <ddmonyyyy> (WP-28, B5). ...`; dash.sthlp updated; the `<!-- WP-28 B5 -->` marker replaced; `order()`, `label()`, `lastlabel()` print nothing.

## Notes

- **Section 13 precedes this section (batch 2 -> batch 3).** Its `scripts/extract_text_truth.do` and `text_truth.json` (group `title`) are on the tree when this section starts; this section's edits are `zp` lines inside the marked region plus the `keys_in_drawn_order` lines in the python block, and 15-05 regenerates the fixture ONCE (rule R5). A regenerated fixture is never patched by hand; every pre-existing `title` probe must be unchanged, checked probe by probe, and `_meta` keeps its existing keys (AMEND-1 I).
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression: test/<file>.py::<Class>::<test> -- failed at <pre-fix tree> with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>` (one per flip), `Fixture: test/fixtures/text_truth.json (scripts/extract_text_truth.do)`, `BUGS.md: "<title>" (closed)`.
- **Shared registries (rules R1-R6).** R1: the LO cases are a block of `test/test_gaps2_truth.cscript` in AMEND-1 H's form (`* ==== S15 B5: … ====`, the `GAPS2_ONLY` gate, `S15 start`/`S15 end` lines that S19 reads for wall time, `* ==== end S15 ====`), inserted above the script's last line in section order; no runner block and no hygiene-pin edit (D11). R2: copy-list entries go after `"_dash_legend_entries"` (24544, C6) and `function_test_map.py`/`program_coverage_map.py` keys in alphabetical place; the merger resolves append conflicts by hand. R3: this section edits dash.sthlp 2290-2312 only, replaces only its `<!-- WP-28 B5 -->` marker and appends its one BUGS.md entry at the end. R5: `text_truth.json` is regenerated once here, never patched. R6: `CORPUS` gains four cases; `ALLOWED` and `_MUST_WARN` are never edited here (S10 and S18 own them). dash_parse.mata 4751-4766: no `.mlib` exists (dash_parse.mata is `run` from dash.ado); a rejected hunk is applied by hand.
- **`lastlabel` index.** The help says position after `order()`; the section brief for B5 says "by key number". The fixture probes `l_lastlabel_pos` and `l_lastlabel_dash` are the arbiter: follow them in 15-06 and cite the probe in the code comment. If they show position, a `-` row counts as a position.
- **Shared items.** The adversarial test at 2913 asserts `len({it.id for it in items}) == 2` for 66,666 rows: never build a new `LegendItem` per `order()` entry for a repeated key. A `lastlabel` by position on a repeated key must replace that position with a fresh item rather than rename the shared one.
- **Renaming after construction** is a field, not a value, on a bare string (W §1a): always `{"value": text}`.
- **`_dash_legend_arg` returns the first match**; this section reads the LAST `order()` and the last `label(#)`/`lastlabel(#)` per number, as `_dash_rep_subkey` keeps the last of each. Do not change `_dash_legend_arg` for the placement/cols/rows/size callers.
- **Served template.** `_plot_rends` (26423-26428) already lists every layer in order; no template edit is needed for numbering. `_dash_apply_legend`'s signature is unchanged, so neither call site changes.
- **`legend(off)` under `by()`.** `extract_axis_truth.do` records that `by(..., legend(off))` is the form that switches the legend off inside `by()`; none of this section's probes use `by()`, so the plain companion works. Do not add a `by()` probe without that form.
- **Blank rows.** `- " "` is invisible in the SVG; the fixture records the visible keys, and the pytest compares dash's rows with the blank one removed.
- **Copy lists and the function map.** A new module-level function missing from 24466-24687 raises `NameError` only when the served app draws a legend -- `TestTheServedCopy` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` catch it.
- **Stata invocation.** Every run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6, `index.md` step 0): the wrapper takes one of three `mkdir` slots, sets `STATATMP=<scratch-dir>/tmp/` (trailing slash) and runs the CLAUDE.md rule 10 console command; never the GUI, never a bare `stata-mp`, never `make cert` inside a section (S19 runs the cert suite and records its wall time). A cscript is never given to the wrapper directly (it opens `cscript … adodir ".."` and `do "cert_helpers.do"` relative to `test/`): write the two-line driver `cd "<repo>/test"` / `do "<repo>/test/<script>.cscript"` into the scratch directory and run that (AMEND-1 B); `GAPS2_ONLY=S15` in the environment runs only this section's block of the truth script. The extract script sets `${ZA_REPO}` itself and runs directly.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, turning every Python cscript into a skip, and a skip is not a pass: check `c(python_exec)` before trusting skips.
- **Line numbers drift** by what 15-06 adds (about +40 at 15682 and +35 at 19754) and by batch 2's merges. Symbols are authoritative.
