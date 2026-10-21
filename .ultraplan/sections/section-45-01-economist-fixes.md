# Section 45-01: economist: note painted; p#other and p#area widths

> Part of: WP-45 (Schemes, styles and figure geometry, audit package 10) · Items: PIC-4, PIC-7 (PIC-8) · Risk: yellow · Batch: 45.1 · Depends on: none · Blocks: none · Tasks: 4, 2 commits · Case-id prefix: Q4501

## Overview

**What is wrong today.**

- **PIC-4.** Under economist a graph's `note()` is never painted. `_dash_text_annotations`' in-band branch (dash_render.py:54510-54527) builds `Label(x=Node(target=title, symbol=align), y=Node(target=title, symbol="top"), anchor="top_" + align, ...)` and puts it in `fig.center`; the audit (PIC-4, verified in headless Chrome at 384, 424 and 1000 px): "BokehJS paints nothing: no note appears ... BokehJS evidently does not resolve a Node that targets a Title for a Label in fig.center." twoway draws the note "in the reverse_big box (white medlarge text on #7b92a8) at the top right of the title band". dash.sthlp:6202-6205 says the note "sits in its box in the title's band, at the top right" (Appendix B HR-15). Only economist takes the branch (note clock 1/11 beside an aligned title). Tests check only the model: test/test_scheme_chrome.py::TestTextboxesSitAtTheirClock::test_economists_note_is_in_the_title_band (:193-200), test/test_textbox_placement.py::TestEconomistBandUnchanged::test_band (:461).
- **PIC-7 (PIC-8).** economist widths: "rspike, rcap, rcapsym, rline, rconnected, spike, dropline, pcspike, pccapsym and the pcarrow/pcbarrow shafts take linestyle p#other: 0.8 rs (pother thick) under economist. The arrowheads are 1.2 and markers 3.63 rs. dash: Draws all of these lines at 1.2 rs (linewidth p)." Their widths follow `plot_line_width` (dash_render.py:12746; `linewidth p#<kind>` -> `p<kind>` -> `p#` -> `p`). The rarea outline is "0.8 rs centred where twoway draws parea 0.2 rs inside": `map_rarea` (:22977-23006) styles both bound Lines from `p_other_band_styles` (:12429-12446, `linewidth p#other` -> `pother` -> `p#`), whose premise "the p#other chain ends at the same values" (DECISIONS A34, comment :22982-22984) fails under economist. dash's own fixture says so: test/fixtures/linewidth_chain_truth.json `cases.lwt7` (`#include economist`) records `area_line` 0.8 for dropline and the range/pc types and 0.2 for area/rarea; test/test_scheme_linewidth.py's `_KIND` map (:64-79) reads `line` for them and `test_economist_draws_its_pc_lines_at_linewidth_p` (:398-409) pins the wrong key.

**After this section.** The economist note is painted in its reverse_big box at the top right of the title band, pinned by a pixel test in Chrome; the range, spike, dropline and paired-coordinate lines take `linewidth p#other` -> `pother` -> `p#` -> `p` (heads and markers keep `p#`); the rarea bound lines take the `p#area` chain (`linewidth p#area` -> `parea` -> `p#` -> `p`). Both modes.

**Why one section.** Both are economist's shipped look drawn wrong, in the scheme readers and the text annotations.

**Test order and commit rule.** PIC-4: 45-01-01 (extract script for both items, PIC-4 tests, failure saved, no commit), 45-01-02 (fix, close, commit `(WP-45 PIC-4)`). PIC-7: 45-01-03 (tests, no commit), 45-01-04 (fix, commit `(WP-45 PIC-7)`).

### Section decisions

- **D-45-01.a The note is a canvas-anchored Label.** The in-band note becomes `Label(x=Node(target="canvas", symbol="right"), y=Node(target="canvas", symbol="top"), x_units/y_units default, anchor="top_right" (top_left for clock 11), x_offset=-<graph margin px>, y_offset=-<graph margin px>, ...)` -- the canvas Node already works in both Bokeh versions (B §4.5 GW-6 row; the frame/axis Node precedent dash_render.py:44788, test/test_axisn_minor.py:170). The box fill and text style stay `_dash_textbox_style`'s. The offsets put the box's top edge where twoway's is: from the extract script's `N_note` probe (box rect top and right in SVG units, converted at the figure's px per unit).
- **D-45-01.b A width kind `other`.** `SchemeParser._PLOT_LWIDTH_KINDS` gains `"other"`, whose chain is `linewidth p#other` -> `linewidth pother` -> `linewidth p#` -> `linewidth p` (as `_band_lwidth` reads it for bands). The mappers of rspike, rcap, rcapsym (spine), rline, rconnected (line), spike, dropline (stem), pcspike, pccapsym (shaft) and pcarrow/pcbarrow (shaft) ask `plot_line_width(idx, "other")`; arrowheads and markers keep their kinds. The list is confirmed per type by the extract script (`W_<type>`); a type twoway draws at `p#` stays.
- **D-45-01.c rarea's chain.** `map_rarea`'s bound lines take `line_width` from a new `SchemeParser.p_area_line_widths` list (chain `linewidth p#area` -> `parea` -> `p#` -> `p`), keeping `p_other_band_styles`' colour, alpha and pattern. The stroke stays centred here; twoway's inside alignment of area strokes is basic:PT-4 (section 47-03), which applies to rarea as to area.

## Risk: [yellow] -- shipped-scheme widths and a text placement change

**Why.** `plot_line_width` reaches every plot; the in-band note is the only Node-on-Title use.

**Risk factors.** 1. Schemes where `pother` differs from `p` other than economist: s2color/stcolor/meta measured equal (audit PIC-8) -- user schemes can differ (correctly now). 2. The canvas Node's offset at narrow widths. 3. The served app: SchemeParser and GlyphMapper methods are copied whole; `_dash_text_annotations` is module-level, already on the copy list.

**Mitigation.** 1. test_scheme_linewidth.py runs every shipped scheme. 2. The Chrome pixel test runs at 384, 600 and 1000 px. 3. A served render in each test.

## Dependencies

- **Depends on:** none.
- **Blocks:** none.
- **Parallel batch 45.1:** with 45-02 and 45-05. This section edits `_dash_text_annotations`' in-band branch, `SchemeParser.plot_line_width`/`p_other_band_styles`, and the line-width lines of the listed mappers; 45-02 edits the clock/ring readers (`_dash_textbox_position`, edge titles, legend regexes) and 45-05 the colour grammar and fonts -- no shared function.

## Evidence

- PIC-4 code: dash_render.py:54496-54532 (in-band test :54511-54516, Label :54517-54527); textbox style `_dash_textbox_style` (:54141); scheme note fill `scheme.note_box_fill_color`.
- PIC-7 code: `plot_line_width` :12746-12782; `_PLOT_LWIDTH_KINDS` (grep in SchemeParser); `p_other_band_styles` :12425-12446; `map_rarea` outlines :22975-23006. Each listed mapper: grep `plot_line_width(` in dash_render.py and note the call sites for those types.
- Fixtures: test/fixtures/linewidth_chain_truth.json (`cases.lwt7`, `schemes.lwt7` = `#include economist ...`); test/fixtures/colour_width_edges_truth.json (`ol.rarea`).
- Pins (flip, never delete): test/test_scheme_chrome.py::TestTextboxesSitAtTheirClock::test_economists_note_is_in_the_title_band; test/test_textbox_placement.py::TestEconomistBandUnchanged::test_band; test/test_scheme_linewidth.py::TestBothModesDrawEachPlotsWidth::test_economist_draws_its_pc_lines_at_linewidth_p and the `_KIND` rows for spike, dropline, rspike, rcap, rcapsym, rconnected, rline, pcspike, pccapsym, pcarrow, pcbarrow (`"line"` -> `"area_line"` where W_* shows pother); test/test_range_outlines.py::TestRareaOutline::test_two_outlines (:70-91).

## User stories

- US-45-01.1 As a Stata user drawing under economist, I want my note() painted in its box at the top right, as twoway draws it.
- US-45-01.2 As a Stata user under economist, I want range, spike, drop-line and arrow lines at twoway's thinner width and rarea outlines at parea's.

## Business requirements

- BR-45-01.1 Under economist a graph's note is visible in a #7b92a8 box at the top right of the title band, saved and served, at every page width tested.
- BR-45-01.2 The listed types' line widths equal twoway's under every shipped scheme; heads and markers unchanged.
- BR-45-01.3 rarea's outline width follows the p#area chain.

## Technical requirements

- TR-45-01.1 `_dash_text_annotations` in-band branch (:54517): replace the Title-target Nodes by canvas-target Nodes per D-45-01.a; keep `tags` and append `"dash_margin_offset"` to them (its offsets are a graph-margin gap, not a size: 45-04's unit post-pass leaves the offsets of a model with this tag unscaled), keep `_dash_textbox_style`, `fig.center = [band] + ...`. The offsets: `x_offset = -round(gm_r)`, `y_offset = -round(gm_t)` where `gm_r`, `gm_t` are the scheme's graph margin right/top in px at build (`scheme.graph_margin_sides`, units of min(W, H)/100 with W, H the figure's built width/height or the 4-inch reference when unknown); the fixture fixes the residual offset.
- TR-45-01.2 `SchemeParser`: `"other"` in `_PLOT_LWIDTH_KINDS`; `plot_line_width` builds keys for `k == "other"` as `[f"linewidth p{i}other", "linewidth pother", f"linewidth p{i}"]` then `default_line_width`; new attribute `self.p_area_line_widths = [self._band_lwidth((f"linewidth p{i}area", "linewidth parea", f"linewidth p{i}")) for i in 1..15]` set beside `p_other_band_styles` (:12429).
- TR-45-01.3 Mappers (D-45-01.b): each listed type's line `line_width` default from `self.scheme.plot_line_width(color_idx, "other")`; `map_rarea` (:22999-23005) `line_width=self.scheme.p_area_line_widths[color_idx % 15]`; the comment block :22978-22990 rewritten (A34's premise false under economist).
- TR-45-01.4 No new module-level function; no copy-list entry (methods are copied whole). function_test_map.py: none.

## Boundaries

- Not textbox placement for other clocks or rings (43-05), not clock/ring words (45-02), not outline alignment (47-03), not the area outline default (34-05).
- Help paragraphs owned (R3): dash.sthlp:6202-6205 (HR-15, economist note), the scheme-file width sentence :6359-6367 (the `other` stub added beside `area`, `arrowline`, `mark`).

## Stata truth

New `scripts/extract_economist_truth.do` writing `test/fixtures/economist_truth.json` (skeleton scripts/extract_scheme_visual_truth.do; widths in relative units = SVG stroke width / (min(SVG width, height) / 100)):
- `N_note` `sysuse auto`, `scatter mpg weight, title("T") note("The note") scheme(economist)`: the note box rect (x, y, w, h, fill), the text (x, y, size, fill), the title text position, the graph size; `N_note_s2` the same under s2color.
- `W_<type>` for rspike, rcap, rcapsym, rline, rconnected, spike, dropline, pcspike, pccapsym, pcarrow, pcbarrow, rarea, under economist and s2color: the plot line stroke widths, head and marker stroke widths (the command lines of scripts/extract_linewidth_chain_truth.do for each type, `scheme(economist)`).
- `_meta` (R7); `git add -f`; register.

Cscript blocks in test/test_wp45_truth.cscript: `* ==== S01 PIC-4: economist note painted ====` (Q4501-1: the saved page's note Label exists with canvas Nodes and twoway's text and fill; the Chrome pixel check runs in pytest's release tier), `* ==== S01 PIC-7: economist p#other and p#area widths ====` (Q4501-2: each W_* type's drawn width equals the fixture's, saved and served).

## TDD test stubs

New `test/test_economist_scheme.py`:
- Test (release tier, Chrome via `test/range_probe.RangeProbe`): the saved page under economist paints the note -- pixels of #7b92a8 within the expected box region at 384, 600 and 1000 px, and the note's text node rendered -- `TestTheNoteIsPainted::test_pixels[width]` (red: nothing painted).
- Test: the note Label's x/y are canvas Nodes, anchor top_right, text and fill as `N_note` -- `TestTheNoteIsPainted::test_model[mode]` (red).
- Test: each `W_<type>`: dash's line width in rs (px / 3.84) equals the fixture's within 0.05 rs, saved and served -- `TestEconomistWidths::test_type[type-mode]` (red for the listed types).
- Test: heads and markers unchanged -- `TestEconomistWidths::test_heads_and_markers[mode]` (guard).
- Test: `plot_line_width(i, "other")` follows the chain on a user scheme with only `linewidth pother vthick` -- `TestTheOtherChain::test_chain` (red).
- Pinned flips: Evidence list.
- Parity (R8): CORPUS `_case("economist note", graph options {"scheme": "economist", "title": "T", "note": "N"})` and `_case("economist rcap widths", ...)` beside the scheme entries (grep `economist` in test/test_mode_parity.py's CORPUS).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| note painted | Chrome pixel test (release tier); model test; Q4501-1 | economist_truth N_note | yes |
| widths | pytest TestEconomistWidths, TestTheOtherChain; Q4501-2 | W_*, linewidth_chain_truth lwt7 | yes |

AC-45-01.1 stubs red at base and green after (the Chrome test run with `DASH_TEST_TIER=release`); AC-45-01.2 Q4501-1..2 PASS; AC-45-01.3 HR-15's economist sentence true and pinned; AC-45-01.4 after each item's commit no plain row of its lead id is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py <id>` prints none), and test/test_corpus_ledger.py and every `test_every_known_difference_is_open` pass.

## Tasks

**Commit boundary.** 01+02 `Paint the economist note in its title-band box (WP-45 PIC-4)`; 03+04 `Draw range, spike and pc lines at p#other and rarea at p#area (WP-45 PIC-7)`; on `wp45-s01` in the worktree `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp45-s01` (BRIEF "Pull form": every command below runs in `$WT`, and a command that names the worktree names it `$WT`, this absolute path, never a `<wt>` placeholder or a relative path). Before editing a function, run `node .gitnexus/run.cjs impact <symbol> --direction upstream --repo .` and report a HIGH, CRITICAL or UNKNOWN risk in the hand-back. Before each commit: `git -C $WT pull --ff-only . main` (BRIEF "Pull form", CLAUDE.md rule 4: pulls local main into the worktree branch; it is a no-op, `Already up to date.`, when the batch base already contains main; if it fails, stop and report to the orchestrator without committing -- a section branch never takes a merge commit), then `git -C $WT merge-base --is-ancestor main HEAD` (exit 0; otherwise stop and report), then `node .gitnexus/run.cjs detect-changes --scope all --repo .` from `$WT` (re-run a `partial` or `truncated` result), and grep the message for claude|anthropic before and after.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", its steps (1)-(3), which every closing task takes whether its item is Fix, Document or Partly -- every item of this section is a Fix item; D-33-05.i, D-33-10.a, D-33-10.h, D-33-09.c). Each closing task (45-01-02 for `PIC-4`, 45-01-04 for `PIC-7`) takes them in `$WT` after its tracking edits and before the pull, for its item's lead id `<id>`: (1) **the ledger** -- delete every plain row of `scripts/corpus/ledger.tsv` (first column exactly `<id>`; PIC-8's rows are keyed `PIC-7`), keeping every `<id> (documented)` and `<id> (residual)` row (A-10: a Document item keeps its `<id> (documented)` rows); rerun `python3 scripts/corpus/ledger.py` (33-05; no `--run`, so the fixture's `_meta` is kept), stage scripts/corpus/ledger.tsv and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0`; (2) **the known-differences tables** -- run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints in whichever `*_KNOWN` table holds it; a difference the item's ruling keeps is not deleted but moved into that table's deliberate dict, the companion dict 33-10 names for that table -- `DELIBERATE` (test/value_truth_known.py) for `VALUE_KNOWN`, `ABBREV_DELIBERATE` (test/test_abbreviations.py) for `ABBREV_KNOWN`, `COLORVAR_DELIBERATE` (test/test_colorvar_truth.py) for `COLORVAR_KNOWN`, and `<NAME>_DELIBERATE` beside any other `<NAME>_KNOWN` table (33-11..33-13, e.g. `SCALE_FRAME_DELIBERATE` in test/scale_frame_known.py), as `"<key>": "<ruling id>: <what is kept>"`, where the ruling id is a DECISIONS or index id (P4-n, A-n, Q-n, M-n), never a section decision's id, and no key stays in both dicts (D-33-10.a rule 4); no item here has a ruling that keeps one; then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); (3) **the guard** -- run block S09 of `$WT/test/test_wp33_truth.cscript` alone (33-09's case Q3309-1): write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/run_test_wp33_truth.do` (BRIEF "Running one cscript") and run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`. If Q3309-1 reports any change for a guard example -- an improved verdict, `<example id> improved from <old verdict> (<old checks>) to <new verdict> (<new checks>): ...`, or a changed field, `<example id>: <field> was <old> now <new>` (D-33-09.c; `<example id>` is an id of scripts/corpus/guard_examples.txt, never the item's GAPS4 id) -- regenerate `test/fixtures/corpus_guard_truth.json` with its extract script, `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_corpus_guard_truth.do`, `git add -f` it, and run the S09 block again: the item is committed, with the regenerated fixture, only when that rerun's log shows `Q3309-1 PASS`. The commit body gains `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and, when regenerated, `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`.

<task type="auto" id="45-01-01">
  <name>Measure economist; failing note tests</name>
  <files>scripts/extract_economist_truth.do, test/test_economist_scheme.py, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_economist_truth.do with the probes of "Stata truth"; run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_economist_truth.do`; `git add -f test/fixtures/economist_truth.json`; register it in test/test_fixtures_are_committed.py. Create test/test_economist_scheme.py with PIC-4's class only, TestTheNoteIsPainted (the Chrome test marked as the release-tier tests are, see test/test_csp_browser.py's marker); TestEconomistWidths and TestTheOtherChain are added by 45-01-03 (BRIEF "Failing test first": this item's commit carries no later item's stub). Run `DASH_TEST_TIER=release python3 -m pytest test/test_economist_scheme.py -q -n0 -k Note > <scratch>/45-01-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/45-01-01-failure.txt` prints at least 4; the fixture's N_note box fill is #7b92a8 (case-insensitive).]]></verify>
  <done>twoway's economist note and widths are measured; the note tests fail at the base.</done>
</task>

<task type="auto" id="45-01-02">
  <name>Anchor the note on the canvas and commit</name>
  <files>dash_render.py, test/test_wp45_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Run `impact` on `_dash_text_annotations` (Commit boundary). Apply TR-45-01.1 (re-read :54496-54532). Flip test_scheme_chrome.py::TestTextboxesSitAtTheirClock::test_economists_note_is_in_the_title_band and test_textbox_placement.py::TestEconomistBandUnchanged::test_band to the canvas-Node model (reason: "a Label on Title Nodes is never painted by BokehJS; the canvas Node is"). Check dash.sthlp:6202-6205 against the painted page and keep it (HR-15 now true); add a help-claim pin of it in test/test_economist_scheme.py (`_between(_help(), ...)` pattern of test/test_help_claims_1.py). Append block S01 PIC-4 (Q4501-1) and run it: printf the driver for test_wp45_truth.cscript (BRIEF) and `WP45_ONLY=S01 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_wp45.do`. Add the `economist note` parity entry (TDD test stubs) to test/test_mode_parity.py's `CORPUS`. Close PIC-4 (BUGS PD-4 closed form pinned by test/test_economist_scheme.py::TestTheNoteIsPainted::test_pixels and Q4501-1, fixture; GAPS4 Closed pending; GAPS4_OPEN line deleted; CHANGELOG `### Fixed in WP-45`: `Under economist a graph's note() is painted in its box at the top right (was never drawn) (WP-45, PIC-4)`; TWOWAY_COVERAGE_AUDIT.md Schemes row (:147) gains `[WP-45 PIC-4: corrected -- the economist note painted in its title-band box]`). Run `DASH_TEST_TIER=release python3 -m pytest test/test_economist_scheme.py test/test_scheme_chrome.py test/test_textbox_placement.py test/test_scheme_rendered_output.py test/test_tracking_documents.py -q -n0`; take Closing steps (1)-(3) for `PIC-4`: (1) delete its plain rows of scripts/corpus/ledger.tsv, rerun `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py PIC-4`, delete the rows it prints from whichever `*_KNOWN` table file it names, and run the hygiene command it prints; (3) run block S09 of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json, `git add -f` it and rerun S09 until its log shows `Q3309-1 PASS`; then the pull, the merge-base check and detect-changes (Commit boundary); commit; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[pytest 0 failed; "Q4501-1 PASS"; `awk -F'\t' '$1 == "PIC-4"' scripts/corpus/ledger.tsv` prints nothing and `python3 test/known_differences.py PIC-4` prints no `<file>:<line>` row; test/test_corpus_ledger.py and the hygiene command pass; the last S09 driver log (the rerun's, after a regeneration) shows `Q3309-1 PASS`; `git log -1 --format=%s` ends "(WP-45 PIC-4)".]]></verify>
  <done>The economist note is painted in both modes, pinned by a pixel test, committed.</done>
</task>

<task type="auto" id="45-01-03">
  <name>Write failing economist width tests</name>
  <files>test/test_economist_scheme.py</files>
  <action><![CDATA[Add TestEconomistWidths and TestTheOtherChain (the stubs of TDD test stubs) to test/test_economist_scheme.py; run `python3 -m pytest test/test_economist_scheme.py -q -n0 -k "Widths or OtherChain" > <scratch>/45-01-03-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/45-01-03-failure.txt` prints at least 8.]]></verify>
  <done>The width tests fail at the PIC-4 commit.</done>
</task>

<task type="auto" id="45-01-04">
  <name>Route widths through p#other and p#area</name>
  <files>dash_render.py, test/test_scheme_linewidth.py, test/test_range_outlines.py</files>
  <action><![CDATA[Run `impact` on `SchemeParser.plot_line_width`, `p_other_band_styles` and `map_rarea` (Commit boundary). Apply TR-45-01.2 and TR-45-01.3 (re-read :12746-12782, :12425-12446, :22975-23006 and each listed mapper's `plot_line_width(` call). Flip test_scheme_linewidth.py's `_KIND` rows for the W_* types twoway draws at pother to `"area_line"` and `test_economist_draws_its_pc_lines_at_linewidth_p` to pother's width (reason: "linewidth_chain_truth lwt7 records area_line 0.8 for them; twoway draws linestyle p#other"), and test_range_outlines.py::TestRareaOutline::test_two_outlines to the p#area width. dash.sthlp scheme-file sentence (:6359-6367): add "other for the range, spike, drop-line and paired-coordinate lines". Append block S01 PIC-7 (Q4501-2) to test/test_wp45_truth.cscript, run it, and add the `economist rcap widths` parity entry (TDD test stubs) to test/test_mode_parity.py's `CORPUS`. Close PIC-7 with PIC-8 in its Item (BUGS -- and correct the wrong S3 resolution of the entry "A custom scheme's linewidth p#..." by appending a sentence to that closed entry's Resolution only if the tracking test allows edits there; otherwise name it in PIC-7's Resolution; GAPS4; GAPS4_OPEN; CHANGELOG Fixed: `Under economist range, spike, drop-line and arrow lines are drawn at pother (0.8, was 1.2) and rarea outlines at parea (WP-45, PIC-7)`; TWOWAY_COVERAGE_AUDIT.md Line styling row (:116) gains `[WP-45 PIC-7: corrected -- p#other and p#area line widths read]`). Run `python3 -m pytest test/test_economist_scheme.py test/test_scheme_linewidth.py test/test_range_outlines.py test/test_scheme_rendered_output.py test/test_tracking_documents.py -q -n0` and `python3 -m pytest test/test_mode_parity.py -q -n0 -k economist`; take Closing steps (1)-(3) for `PIC-7`: (1) delete its plain rows of scripts/corpus/ledger.tsv (PIC-8's rows are keyed `PIC-7`), rerun `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py PIC-7`, delete the rows it prints from whichever `*_KNOWN` table file it names, and run the hygiene command it prints; (3) run block S09 of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json, `git add -f` it and rerun S09 until its log shows `Q3309-1 PASS`; then the pull, the merge-base check and detect-changes (Commit boundary); commit; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[pytest 0 failed; "Q4501-2 PASS"; `awk -F'\t' '$1 == "PIC-7"' scripts/corpus/ledger.tsv` prints nothing and `python3 test/known_differences.py PIC-7` prints no `<file>:<line>` row; test/test_corpus_ledger.py and the hygiene command pass; the last S09 driver log (the rerun's, after a regeneration) shows `Q3309-1 PASS`; `git log -1 --format=%s` ends "(WP-45 PIC-7)".]]></verify>
  <done>economist's line widths follow twoway's p#other and p#area chains in both modes, committed.</done>
</task>

## Section completion criteria

- Two commits on `wp45-s01`; Q4501-1..2 PASS; the release-tier Chrome test green when run by hand.
- PIC-4 and PIC-7 tracked per PD-3 with `commit pending`; GAPS4_OPEN lines deleted; HR-15's economist sentence pinned.
- The closing steps taken in both commits: no plain PIC-4 or PIC-7 row left in scripts/corpus/ledger.tsv or a `*_KNOWN` table, corpus_ledger.json regenerated and staged, S09 run, and test/fixtures/corpus_guard_truth.json regenerated and staged whenever Q3309-1 reported a change for a guard example, the rerun PASS.

## Notes

- **Trap:** only the in-band branch changes; notes at other clocks go through `_dash_textbox_draw` unchanged.
- **Trap:** `plot_line_width`'s memo key must include the kind so `"other"` and `""` do not share a cached value (`_plot_lwidth_memo`).
- **Appendix B:** HR-15 (dash.sthlp:6202-6205 economist note) corrected and pinned here.
- **Help paragraphs owned (R3):** dash.sthlp:6202-6205, :6359-6367.
- **Merge rules:** R1, R3, R7, R8, R9, R13.
- **Functions this section edits (for the manifest's Owns cell):** `_dash_text_annotations` (in-band branch), `SchemeParser.plot_line_width`, `SchemeParser._PLOT_LWIDTH_KINDS`, `SchemeParser` beside `p_other_band_styles` (new `p_area_line_widths`), `GlyphMapper.map_rarea` and the line-width default of the listed range, spike, dropline and pc mappers. None is R12-hot; none is edited by 45-02 or 45-05.
- **For 45-04 (batch 45.3):** the in-band note's `x_offset`/`y_offset` are graph-margin gaps tagged `dash_margin_offset` (TR-45-01.1); 45-04 keeps them unscaled and recomputes them from the margin it draws.
- **Commit body lines:** `Regression: test/test_economist_scheme.py::TestTheNoteIsPainted::test_pixels[600] -- failed at <base> with <text>`; `Flipped: test/test_scheme_linewidth.py::TestBothModesDrawEachPlotsWidth::test_economist_draws_its_pc_lines_at_linewidth_p -- linewidth p was wrong because twoway draws p#other`; `Fixture: test/fixtures/economist_truth.json (scripts/extract_economist_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` (both commits; the guard fixture's line when S09 made it regenerate); `BUGS.md: "<title>" (closed)`; `GAPS4: PIC-4 Tracked` (and PIC-7).
