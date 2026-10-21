# Section 34-02: by(): x ticks at #4 and the shared y title painted

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: AX-2 (TR-3, BY-26), VF-2 (TR-24) · Risk: yellow · Batch: 34.3 · Depends on: 34-01 · Blocks: 34-09 · Tasks: 5, 2 commits · Case-id prefix: Q3402

## Overview

**What is wrong today -- AX-2.** twoway's by() styles set `xlabels(#4) ylabels(#4)` (bygraphstyle-default/compact/altleg/econ.style:39-40), so every by() graph ticks its first x axis with one fewer tick than the scheme's 5, as it does y. dash lowers only y: `_dash_by_numticks` (dash_render.py:40785) sets `out["y"] = max(1, ny - 1)` (:40799). Measured (AX-2, TR-3): `scatter mpg length, by(foreign)` -- twoway x 150 200 250, dash 140(20)240, in by(foreign), by(foreign, cols(1)), by(rep78) and xsize(10) alike; `scatter mpg displacement, by(foreign)` -- twoway 100(100)400, dash 100(100)500; `scatter mpg price, by(foreign)` -- twoway 5,000 10,000 15,000, dash 0(5000)15000; `tw histogram le, discrete by(region, total)` 50(10)80 against 55(5)80. Every x variable in by_scales_truth (weight, mpg, dates) gives the same ticks at #4 and #5, which is why it was never seen. The help says "a by() graph's panels take one fewer on y" (dash.sthlp:4679, HR-11).

**What is wrong today -- VF-2.** A by() graph's shared y title is never painted. The `dash_by_ytitle` cell holds its Title (visible) and lays out 28x560, but its canvas is 28x1 with 0 painted pixels (VF-2, measured in headless Chrome 155 at 760, 1200 and 1400 px; TR-24 settled by it). `_dash_by_text_cell` builds the cell `Plot(..., frame_height=1, height_policy="fit")` (:55040) and `_dash_by_cell` (:55386) with frame `(1, None)` sets `height_policy = "max"` (:55403) but never clears `frame_height`; deleting it from a scratch copy gives a 28x560 canvas with the title painted (295 dark pixels). The browser tests check bboxes and visibility only (test_legend_span_browser.py:519 `TestByPanelsFillTheirRow`, test_by_axes_keys_browser.py).

**After this section**, in both modes: a by() graph's first x axes are ticked at the scheme's count less one, as y is (the second axes keep the scheme's count, by_scales_truth f02/c17); and the shared y title is painted at its full height. At build the x ticks come from the model at #4, which equals twoway for length and displacement; `price` at #4 is one of the model's known misses, made exact at build by 34-09 (which asks Stata for the by() count, AX-3).

**Why one section.** Both items are by()'s first drawing in the same family of functions (`_dash_by_numticks`, `_dash_by_cell`), neither with a JS twin.

**Test order and commit rule.** Two cycles, in the manifest's order. AX-2: 34-02-01 (failing tests, no commit), 34-02-02 (fix, flips, help, tracking, commit `(WP-34 AX-2)`). VF-2: 34-02-03 (failing pixel tests, no commit), 34-02-04 (fix), 34-02-05 (tracking, commit `(WP-34 VF-2)`).

### Section decisions

- **D-34-02.a. The count is the scheme's less one on x1 and y1.** `_dash_by_numticks` returns `{"x": nx-1, "y": ny-1, "x2": nx, "y2": ny}` under by() (both bounded below by 1). An explicit `#N` is N either way, as today.
- **D-34-02.b. Stata's answer at #4 is 34-09's.** The export's tick requests (`_dash_stata_tick_requests`, owned by 34-09) ask counts {5} plus `#N`; adding the by() count is AX-3's fix in batch 34.4. 34-02's truth rows are the ones the model draws exactly (length, displacement); 34-09 adds `price`.
- **D-34-02.c. A cell that fills its track's height has no frame height.** In `_dash_by_cell`, a `(width, None)` frame means "fill the track's height": `cell.frame_height = None`, with the `height_policy = "max"` the function already sets for it (:55403). The cells by frame (REVIEW R2-4): `(1, None)` is the left y title (`_dash_by_title_cell`, :55413), a vertical legend (:55656) and the default vertical colour key at 3 o'clock (`_dash_by_cell(scheme, "dash_by_clegend", (1, None) if vertical else (None, 1))`, :55924-55925): all three are cleared and fill the track. `(None, 1)` is the bottom title, a horizontal legend or colour key (the same calls with `vertical` false) and the ruler (:56595): unchanged, they keep `_dash_by_text_cell`'s `frame_height=1` and `height_policy="fit"`. `(None, None)` is the colour key at 6 or 12 o'clock or in an at() hole (:55889): untouched by the rule because its `fw` is None; that branch already sets its own height after building the cell -- `frame_height = None` with `height_policy = "fixed"` and `height = 200` (:55917-55919), or under at() `height_policy = "max"` with `min_height = 160` (:55898-55903) -- so it never falls back to Plot's default height of 600 px.

## Risk: [yellow] -- every by() graph's x ticks and side cells change

**Why.** The count reaches the saved plan (`n`) and the served refit; the cells reach every by() layout (legend, clegend, ruler).

**Risk factors.** 1. by() tests asserting 5 x ticks. 2. `_DASH_BY_FIT_JS` (:55541) and `_DASH_BY_STACK_JS` (:56167) resize and hide the cells. 3. A vertical `dash_by_legend` cell and the default vertical `dash_by_clegend` cell, both `(1, None)`, are cleared like the title and must still draw their key at the track's height; the 6/12 o'clock and at() `dash_by_clegend` cell, `(None, None)`, sets its own height and is untouched (D-34-02.c). 4. Virtual time renders no frames in headless Chrome (test_by_axes_keys_browser.py's docstring).

**Mitigation.** by_scales rows with #4 != #5; a Chrome test that reads each cell's canvas size and painted pixels after a forced layout (the measure probe of test/test_by_axes_keys_browser.py, which reads `v.canvas_view.primary.ctx`); the default colour key's cell (cleared) and the `clegend(on pos(6))` cell (its own 200 px) included.

## Dependencies

- **Depends on:** 34-01 (by() x ticks read the extent 34-01 changed).
- **Blocks:** 34-09 (adds the by() count to Stata's requests).
- **Parallel batch:** 34.3 with 34-07. **Can run with it:** 34-07 edits the export's requests and dash.ado's summaries; 34-02 edits `_dash_by_numticks` and `_dash_by_cell` only. Neither edits a JS literal; 34-07 is the batch's JS editor.

## Evidence

### Code at 090d928 (re-read before editing)

```python
40795     nx = getattr(scheme, "numticks_x", 5) or 5
40796     ny = getattr(scheme, "numticks_y", 5) or 5
40797     out = {"x": nx, "y": ny, "x2": nx, "y2": ny}
40798     if str((graph_opts or {}).get("by", "") or "").strip():
40799         out["y"] = max(1, ny - 1)
40800     return out
```
Set at :63474 (saved) and in the served literal :70342; read at :42018, :45318, :45334, :46948, :47007 (the placeholders' counts, so the saved plan's `n` follows).

```python
55399     fw, fh = frame
55400     if fw:
55401         cell.frame_width = int(fw)
55402         cell.width_policy = "fit"
55403         cell.height_policy = "max" if fh is None else "fit"
55404     if fh:
55405         cell.frame_height = int(fh)
```
`_dash_by_text_cell` sets `frame_height=1` (:55040). Callers: `_dash_by_title_cell` :55413 (`(1, None)` for the left title, `(None, 1)` for the bottom), the legend cell :55656 (`(1, None)` vertical, `(None, 1)` horizontal), `dash_by_clegend` :55889 `(None, None)` (6/12 o'clock or at(); it then sets `frame_height = None` and its own height, :55898-55919) and :55924-55925 (`(1, None)` vertical, the default 3 o'clock key; `(None, 1)` horizontal), the ruler :56595 `(None, 1)`. Single source, copied into the served app.

### twoway's truth

bygraphstyle-*.style:39-40 (`xlabels #4`, `ylabels #4`); the audit's probes p8 Y1/Y3/Y4 and p9 W1/W3/W4/W5 (AX-2 appendix): length x 150 200 250 in every layout; displacement 100(100)400; dash's model at #4 gives exactly those two (AX-2 verifier). test/fixtures/by_scales_truth.json from scripts/extract_by_scales_truth.do (`_bsc_run <id> <data> "<cmd>"`, :141-166).

### Tests pinning today's behaviour (flip, never delete)

- test/test_default_axes.py::TestTheHelpers::test_the_by_tick_count (:360-365) asserts `{"x": 5, "y": 4, "x2": 5, "y2": 5}` under by() -- flip to `{"x": 4, ...}`.
- test/test_by_axes_keys.py::TestTheUnitFunctions::test__dash_by_cell (:396) asserts `(None, 1).frame_height == 1` (stays) -- extend with `(1, None).frame_height is None` (an extension, not a flip).
- by() tests asserting 5 x ticks found in 34-02-01's runs (test/test_by_scales.py, test/test_by_*.py).

## User stories

- US-34-02.1 As a Stata user with an existing twoway command, I want `dash scatter mpg length, by(foreign)` to label x 150 200 250, as twoway does.
- US-34-02.2 As that user, I want the y title to the left of my by() panels, as twoway draws it.

## Business requirements

- BR-34-02.1 A by() graph's first x axes take one tick fewer than the scheme's count, as its y axes do, in both modes and after moves; second axes keep the scheme's count.
- BR-34-02.2 A by() graph's shared y title is painted, centred on the panel array, in both modes, at every page width the stacked layout does not hide it.
- BR-34-02.3 The legend and colour-key cells of a by() graph still draw: a vertical legend and the default colour key at the panels' height, a colour key at 6 or 12 o'clock at its own height.

## Technical requirements

- TR-34-02.1 `_dash_by_numticks`: under by() also `out["x"] = max(1, nx - 1)`; the docstring names AX-2 and the style files. No served literal change (the function is copied).
- TR-34-02.2 Stata truth for AX-2: scripts/extract_by_scales_truth.do gains, after the last `_bsc_run` line, `_bsc_run x01 auto \`"twoway scatter mpg length, by(foreign)"'`, `x02 ... by(foreign, cols(1))`, `x03 ... by(rep78)`, `x04 ... by(foreign) xsize(10)`, `x05 auto \`"twoway scatter mpg displacement, by(foreign)"'`; add `displacement` to the auto columns the script dumps into the fixture's `data.auto` (today foreign, length, mpg, price, rep78, turn, weight; find the column list in its python block), so test pages can draw x05; regenerate test/fixtures/by_scales_truth.json; `git add -f`.
- TR-34-02.3 `_dash_by_cell` (D-34-02.c): after the `if fw:` block (:55400-55403), `if fw and fh is None: cell.frame_height = None` (the fill-height case only); `(None, None)` and `(None, 1)` cells are left as `_dash_by_text_cell` builds them. The docstring states the rule: "a `(width, None)` cell fills its track's height with no frame height; every other cell keeps the 1-px frame its content fits".
- TR-34-02.4 Chrome test (release tier): for `scatter mpg weight, by(foreign) ytitle("Price")`, the same with `legend(on)` and a `colorvar(price)` layer (so a vertical legend cell and the default 3 o'clock `dash_by_clegend` cell exist), and the colorvar graph with `by(foreign, clegend(on pos(6)))`, at 1200 px, both modes: the `dash_by_ytitle` view's canvas (`v.canvas_view.primary.canvas`) is at least 100 px tall and holds at least 50 pixels darker than the background (read with `ctx.getImageData` over the cell); the legend cell's canvas is taller than 1 px; the default key's `dash_by_clegend` canvas height is within 2 px of the `dash_by_ytitle` canvas height (both fill the panels' track) and its ColorBar view (the view in the cell's `renderer_views` whose model is the ColorBar) has a `bbox.height` above 1 px; with `clegend(on pos(6))` the `dash_by_clegend` canvas is 200 px tall (within 1 px), the height its branch sets (REVIEW R2-4).

## Boundaries

- Do not touch `_dash_stata_tick_requests` (34-09, D-34-02.b), `_dash_common_count_ticks` or the finish JS (34-07 is batch 34.3's JS editor, R11/R12).
- Do not touch by() title text, positions or `_dash_by_chrome` (WP-41).
- PRD §7; R14.

## Stata truth

AX-2: TR-34-02.2, run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_by_scales_truth.do`. VF-2: none, and no truth block (BRIEF "Block order": an item with no Stata comparison adds none; twoway draws the outer y title, and the requirement that dash paints its own is pinned by test/test_by_axes_keys.py::TestTheUnitFunctions::test__dash_by_cell and test/test_by_cells_browser.py).

One truth block, inserted directly above the first block whose `S<MM>` is higher than S02 (BRIEF "Block order"; at the batch-34.3 base that is S03, which 34-03 landed in batch 34.2):
```
* ==== S02 AX-2: by() panels tick x at the scheme's count less one ====
local only : env WP34_ONLY
if inlist("`only'", "", "S02") & `: list posof "S02" in w34_run' {
    display as text "S02 start " c(current_date) " " c(current_time)
    ... Q3402-1 ...
    display as text "S02 end " c(current_date) " " c(current_time)
}
* ==== end S02 ====
```
- Q3402-1: for x01 and x05, twoway's panel-1 x ticks (`_q34_drawn .Graph.graphs[1] x1`) equal the saved page's x FixedTicker (`_q34_has`).

## TDD test stubs

AX-2 regression tests (red at the base):
- Test: `_dash_by_numticks` under by() is `{"x": 4, "y": 4, "x2": 5, "y2": 5}` (stcolor) -- test/test_by_tick_count.py::TestTheCount::test_the_rule
- Test: x01-x05 draw twoway's x ticks on every panel -- ::TestAgainstStata::test_rows[saved|served] (red: 140(20)240, 100(100)500)
- Test: after a saved move and a served refit x01's x ticks are the model's #4 over the kept data -- ::TestAfterAMove::test_saved, ::test_served
VF-2 regression tests (red at the base):
- Test: `_dash_by_cell(None, "dash_by_ytitle", (1, None)).frame_height is None` with `height_policy == "max"`, while `(None, None)` and `(None, 1)` keep `frame_height == 1` and `height_policy == "fit"` -- test/test_by_axes_keys.py::TestTheUnitFunctions::test__dash_by_cell (extended)
- Test: in Chrome the y title canvas is painted; the legend canvas is taller than 1 px; the default colour key's canvas is the y title canvas's height within 2 px with a ColorBar view taller than 1 px; under `clegend(on pos(6))` the colour key's canvas is 200 px tall -- test/test_by_cells_browser.py::TestTheTitleIsPainted::test_ytitle[saved|served] (new file, release tier)
cscript: Q3402-1 (AX-2). VF-2 adds no cscript case (no Stata comparison; BRIEF "Block order").
Pinned tests to flip: test/test_default_axes.py::TestTheHelpers::test_the_by_tick_count (AX-2).
Parity: append `_case("by foreign length x ticks", [plot_for("scatter", {}, yvar="mpg", xvar="length")], go={"by": "foreign"})` (`plot_for`, test/test_server_layer_defects.py:82, takes `yvar=`/`xvar=` keywords) and `_case("by ytitle cell", [_sc()], go={"by": "foreign", "ytitle": "Price"})` to `CORPUS`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| by() count rule | pytest unit | -- | n/a |
| x ticks vs twoway | pytest + Q3402-1 | by_scales_truth.json x01-x05 | yes |
| After a move | pytest + node through the saved plan | -- | yes |
| Cell frames | pytest unit | -- | yes |
| Title painted | Chrome (release) | -- | yes |
| Parity | CORPUS | -- | yes |

AC-34-02.1 x01-x05 match twoway in both modes; AC-34-02.2 the y title canvas is painted in both modes; AC-34-02.3 legend and clegend cells still draw; AC-34-02.4 two green commits.

## Tasks

**Commit boundary.** AX-2: 34-02-01 and 34-02-02 form commit 1, subject `Tick a by() graph's first x axes at the scheme's count less one (WP-34 AX-2)`, made by 34-02-02. VF-2: 34-02-03 to 34-02-05 form commit 2, subject `Paint a by() graph's shared y title at its full height (WP-34 VF-2)`, made by 34-02-05. Branch `wp34-s02` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s02`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). Each closing task (34-02-02 for AX-2, 34-02-05 for VF-2) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-02/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-02 <scratch>/34-02/run_test_wp33_truth.do` and read `<scratch>/34-02/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-02/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-02-01">
  <name>Measure by() x ticks and write failing tests</name>
  <files>scripts/extract_by_scales_truth.do, test/test_by_tick_count.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read _dash_by_numticks and its readers at the batch-34.3 base; run `node .gitnexus/run.cjs impact "_dash_by_numticks" --direction upstream --repo .` and the same for `_dash_by_cell`, writing callers to <scratch>/34-02/anchors.txt. Apply TR-34-02.2, run the extractor, `git add -f test/fixtures/by_scales_truth.json`. Create test/test_by_tick_count.py with the AX-2 stubs (pages through test/test_by_scales.py's _spec/_draw helpers). Insert the S02 AX-2 block (Q3402-1) where the Stata truth section says (above S03; not above the marker, REVIEW R2-20). Run `python3 -m pytest test/test_by_tick_count.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-02/01.log`, the S02 block with WP34_ONLY=S02, and save the failures to <scratch>/34-02-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/by_scales_truth.json'));print(sorted(k for k in d.get('probes', d) if k.startswith('x0')))"` lists x01-x05; `grep -c FAILED <scratch>/34-02/01.log` is at least 3; `test -s <scratch>/34-02-01-failure.txt`.]]></verify>
  <done>twoway's by() x ticks for five probes were recorded and the AX-2 tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-02-02">
  <name>Lower the by() x count and close AX-2</name>
  <files>dash_render.py, test/test_default_axes.py, dash.sthlp</files>
  <action><![CDATA[
Apply TR-34-02.1. Flip test_the_by_tick_count to `{"x": 4, "y": 4, "x2": 5, "y2": 5}` with `# Flipped (WP-34 AX-2): twoway's by() styles set xlabels(#4) as well as ylabels(#4).` Run test/test_by_tick_count.py, test/test_by_scales.py, test/test_by_*.py (not the browser files), test/test_default_axes.py, test/test_stata_ticks.py and test/test_mode_parity.py -k by; flip every node asserting a by() x axis at #5 with the same reason (a by() x axis whose ticks are equal at #4 and #5 needs no flip). Help (HR-11): in dash.sthlp:4679 replace "a {cmd:by()} graph's panels take one fewer on y, as {cmd:twoway} draws them" with "a {cmd:by()} graph's panels take one fewer on their first x and y axes, as {cmd:twoway}'s by() styles set them"; add test/test_by_tick_count.py::TestTheHelp::test_the_count_sentence (the `_between(_help(), ...)` pattern). Append the first CORPUS entry to test/test_mode_parity.py. Close the BUGS.md entry 33-01 registered for AX-2 (closed form: _dash_by_numticks lowers x1 as y1 under by(), both modes; at build the ticks at #4 are the model's, made Stata's by 34-09; pinned by test/test_by_tick_count.py::TestAgainstStata::test_rows and Q3402-1; fixture by_scales_truth.json); rewrite `- **AX-2 Tracked:**` to the Closed form with `commit pending`; delete AX-2's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- A by() graph's first x axes are ticked at the scheme's count less one, as twoway's by() styles set them (scatter mpg length, by(foreign): 140(20)240 -> 150 200 250) (WP-34, AX-2)` under `### Fixed in WP-34`. Run the Closing steps for AX-2 (Tasks; BRIEF steps (1)-(3)): (1) delete AX-2's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py AX-2`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-02) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run the files above, test/test_help_conformance.py, test/test_tracking_documents.py and the S02 AX-2 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_tick_count.py test/test_by_scales.py test/test_default_axes.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3402-1 PASS" <scratch>/34-02/run_test_wp34_truth.log` prints 1; `awk -F'\t' '$1 == "AX-2"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py AX-2` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-02/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 AX-2)`.]]></verify>
  <done>by() graphs tick their first x axes at the scheme's count less one in both modes, and AX-2 is closed in one commit.</done>
</task>

<task type="auto" id="34-02-03">
  <name>Write failing title-cell pixel tests</name>
  <files>test/test_by_axes_keys.py, test/test_by_cells_browser.py</files>
  <action><![CDATA[
Extend test/test_by_axes_keys.py's test__dash_by_cell per the VF-2 stubs. Create test/test_by_cells_browser.py per TR-34-02.4, copying test/test_by_axes_keys_browser.py's `_page`/`_measure` and its rgb/visit probe pattern (`Bokeh.index`, `v.canvas_view.primary`), forcing a layout before reading (`for (const v of Object.values(Bokeh.index)) v.resize_layout && v.resize_layout();` then a `requestAnimationFrame`-free read, as that file's widths loop does). Run `python3 -m pytest test/test_by_axes_keys.py -k by_cell test/test_by_cells_browser.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-02/03.log` and save the failures to <scratch>/34-02-03-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/34-02/03.log` is at least 2 (if Chrome is absent the browser tests skip: record that and rely on the model test); `test -s <scratch>/34-02-03-failure.txt`.]]></verify>
  <done>The title cell's 1-px canvas was shown by failing tests on the tree after commit 1.</done>
</task>

<task type="auto" id="34-02-04">
  <name>Clear the filling cell's frame height</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-34-02.3 in _dash_by_cell. Run test/test_by_axes_keys.py, test/test_by_cells_browser.py, test/test_by_axes_keys_browser.py, test/test_legend_span_browser.py -k By, test/test_by_remainder.py, test/test_by_grid.py, test/test_by_text.py and test/test_mode_parity.py -k by; a failure that asserts frame_height == 1 on a filling cell is flipped in 34-02-05 with its reason (write its file::Class::test name to <scratch>/34-02/flips.txt), any other is a regression to fix.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys.py test/test_by_cells_browser.py test/test_by_grid.py test/test_by_text.py -q -n0 -p no:cacheprovider` ends with 0 failed.]]></verify>
  <done>The shared y title, a vertical legend and the default vertical colour key fill their tracks and paint in both modes, and the 6/12 o'clock and at() colour keys keep the heights their branch sets.</done>
</task>

<task type="auto" id="34-02-05">
  <name>Record VF-2 in the tracking documents</name>
  <files>test/test_mode_parity.py, TWOWAY_COVERAGE_AUDIT.md, CHANGELOG.md</files>
  <action><![CDATA[
Flip, in place, each node of <scratch>/34-02/flips.txt (34-02-04's `frame_height == 1` asserts on a filling cell), with `# Flipped (WP-34 VF-2): a cell that fills its track takes the track's height; frame_height 1 left the title 1 px tall.` and a `Flipped:` body line each. Append the second CORPUS entry. Append `[WP-34 AX-2, VF-2: corrected -- by() x ticks at #4, the shared y title painted]` to the Facets row of TWOWAY_COVERAGE_AUDIT.md (:146). Close the BUGS.md entry 33-01 registered for VF-2 (closed form: _dash_by_cell clears frame_height on a cell that fills its track, both modes; pinned by test/test_by_cells_browser.py::TestTheTitleIsPainted::test_ytitle and test/test_by_axes_keys.py::TestTheUnitFunctions::test__dash_by_cell); rewrite `- **VF-2 Tracked:**` to the Closed form with `commit pending`; delete VF-2's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- A by() graph's shared y title is painted; its cell was 1 px tall (WP-34, VF-2)` under `### Fixed in WP-34`. Run the Closing steps for VF-2 (Tasks; BRIEF steps (1)-(3)): (1) delete VF-2's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py VF-2`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-02) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_by_axes_keys.py, test/test_by_cells_browser.py, test/test_mode_parity.py -k "ytitle cell" and test/test_tracking_documents.py; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_axes_keys.py test/test_by_cells_browser.py test/test_tracking_documents.py -q -p no:cacheprovider` ends with 0 failed; `awk -F'\t' '$1 == "VF-2"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py VF-2` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-02/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 VF-2)`.]]></verify>
  <done>The shared y title of every by() graph is painted and VF-2 is closed in its own commit.</done>
</task>

## Section completion criteria

- AX-2: x01-x05 match twoway in both modes; the count pin flipped; HR-11 corrected and pinned; commit 1 green.
- VF-2: the title canvas painted in Chrome in both modes; the legend and default colour-key cells fill the panels' height and the 6/12 o'clock key keeps its 200 px; commit 2 green.
- Both BUGS entries closed, both Tracked lines `commit pending`, both GAPS4_OPEN lines removed.

## Notes

- **Manifest note:** the audit's AX-2 fix also says "request n=4 from Stata's tick table"; that is in `_dash_stata_tick_requests`, which the index gives 34-09 (and 34-07 edits the same function in this batch for its row rule), so 34-09 adds the by() count (D-34-02.b) and the `price` row.
- **Help (R3, HR-11):** this section owns the clause of dash.sthlp:4679.
- **Trap:** the rule is on the frame, not the cell's name: only `(width, None)` cells are cleared (D-34-02.c) -- the y title, a vertical legend and the default vertical colour key. Do not add a clearing for `(None, None)` or `(None, 1)` cells: the `(None, None)` colour key's branch (:55889-55923) already sets `frame_height = None` with its own height (200 px fixed, or `max` with `min_height` 160 under at()), and a `(None, 1)` cell with `height_policy` "fit" and no frame height would fall back to Plot's default height (600 px). TR-34-02.4's two colour-key asserts and test/test_by_axes_keys.py's clegend tests (`test_the_colour_key_is_upright_below_the_panels`, :1162) guard it.
- **Commit body line forms:** `Regression: test/test_by_tick_count.py::TestAgainstStata::test_rows -- failed at <base sha> with <text>`; `Flipped: test/test_default_axes.py::TestTheHelpers::test_the_by_tick_count -- x 5 under by() was wrong because twoway's by() styles set xlabels(#4)`; `Fixture: test/fixtures/by_scales_truth.json (scripts/extract_by_scales_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: AX-2 Tracked` / `GAPS4: VF-2 Tracked`.
- Merge rules touched: R1, R3, R7, R8, R9.
