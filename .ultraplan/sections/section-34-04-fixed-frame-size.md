# Section 34-04: aspectratio() with xsize()/ysize(): exact frame, never 0 px

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: VF-3 (ST-12) · Risk: yellow · Batch: 34.1 · Depends on: none · Blocks: none · Tasks: 3, 1 commit · Case-id prefix: Q3404

## Overview

**What is wrong today.** `aspectratio()` with `xsize()` or `ysize()` is supposed to draw the figure at that size (96 px an inch) with the largest plot region of ratio # inside it (dash.sthlp:5670-5679). `_dash_frame_sizes` (dash_render.py:27650) sets `sizing_mode="fixed"`, `frame_width`/`frame_height` and `min_border_*`, but never `width`/`height`, and the figure keeps `min_height=160`/`max_height=560` from its constructor (dash_render.py:63428-63429) and the `aspect_ratio` `_dash_figure_aspect` gave it. The audit (VF-3, ST-12) measured: `aspectratio(1) xsize(4) ysize(4)` draws 600x560 with a 544x509 frame (ratio 1.07); `aspectratio(2) xsize(8) ysize(4)` draws a frame **0 px wide** -- no plot, only a y axis; and every such build prints `ERROR:bokeh.core.validation.check:E-1023 (MIN_PREFERRED_MAX_HEIGHT): Expected min_height <= height <= max_height` to the Stata console. [B] §4.6 traced the cause: with a fixed policy BokehJS takes the default height 600, `max_height` clamps it to 560, the CSS grid lays out `left | frame_width | right` against a host that disagrees, and the leftover `aspect_ratio=2` collapses the frame column.

**After this section**, in both modes: the figure's `width`/`height` are the xsize()/ysize() box (`_dash_frame_box`), `min_height`, `max_height` and `aspect_ratio` are cleared, the frame is drawn at ratio # within 1% (measured fix V1 in [B] §4.6: aspectratio(2) xsize(8) ysize(4) gives a 768x384 host with a 168x334 frame, ratio 1.99), no plot is 0 px in any case, and Bokeh logs no validation line. A fixed figure keeps its size in a narrow cell, which then scrolls sideways (D41 forbids only a 0 px plot; the help says so).

**The base for figure geometry (DECISIONS A-1).** A-1 rules that every graph keeps twoway's shape and that explicit xsize()/ysize() give the exact size, with this section's fix as the base. WP-45's 45-04 builds on it: it reuses `_dash_frame_sizes` as this section leaves it, removes the page height bound `k` from `_dash_apply_frame_aspect` (so the box is exact), extends the fixed box to xsize()/ysize() without aspectratio(), removes the 160-560 px band and extends test/test_sizing_browser.py. This section therefore keeps `k` (D-34-04.a) and writes no test that 45-04's removal of `k` would have to flip (D-34-04.d).

**Why one section.** One item, one function (`_dash_frame_sizes`) shared by both modes.

**Test order and commit rule.** 34-04-01 writes the model, validation and headless-Chrome tests and the cscript block, runs them on the unmodified tree, saves `<scratch>/34-04-01-failure.txt`, no commit. 34-04-02 makes the fix. 34-04-03 flips the pin, edits the help and the tracking documents and commits `(WP-34 VF-3)`.

### Section decisions

- **D-34-04.a. Fix V1 of [B] §4.6, exactly.** In `_dash_frame_sizes`: `fig.width, fig.height = int(round(width)), int(round(height))`; `fig.min_height = None`; `fig.max_height = None`; `fig.aspect_ratio = None`. The page height bound is already applied to the box by `_dash_apply_frame_aspect` (`k = min(1.0, _MAX_FIGURE_HEIGHT / (h_in * 96.0))`, :27696-27699), so the figure never exceeds it; `k` stays in this section (A-1 gives its removal to 45-04, D-34-04.d).
- **D-34-04.b. No responsive shrink.** A fixed figure does not shrink on a phone; the help sentence says a narrow cell scrolls sideways. Shrinking would need a resize hook and is not this section's (WP-45 45-04 owns figure geometry). This is A-1's "explicit xsize()/ysize() give the exact size".
- **D-34-04.c. HR-12 split.** This section corrects dash.sthlp:5670-5679 (the aspectratio() paragraph). The `xsize(9)` "exactly as twoway does" sentence at :5653-5655 (xsize() alone, no aspectratio()) is 45-04's (VF-4: xsize()/ysize() alone change nothing today).
- **D-34-04.d. Written as A-1's base.** Every test this section adds compares the figure with `fig._dash_frame_box` (never with a 560 px number), and every probe's box is under 560 px tall (768x384; 768 by the scheme's graphsize y, 384 or 432 px in the shipped schemes; 576x288), so 45-04 removing `k` leaves them green. The clause "held to the page's height bound" of dash.sthlp:5673-5674 stays as it is here; 45-04 rewrites it with `k`. test/test_sizing_browser.py is created here for 45-04 to extend (its `TestTheThreeCasesInChrome`), so its probe JS is a module-level helper, `_frame_probe(page, name)`, returning `[host_w, host_h, frame_w, frame_h]`.

## Risk: [yellow] -- a figure leaves the responsive layout in every route that sizes it this way

**Why.** `sizing_mode="fixed"` with explicit width/height changes how the figure sits in a grid cell, a tab and a `layout()` cell; by() is not affected (the served call is under `if _fac_label is None`, :70703, and the saved call at :64007 is in the same non-faceted branch).

**Risk factors.** 1. A layout/tab cell narrower than the box. 2. `_DASH_GRAPH_MARGIN_JS` and the span hooks resize figures on page resize. 3. Tests that assert `aspect_ratio` on these figures. 4. Bokeh 3.8 and 3.9 both ([B] measured both identical).

**Mitigation.** Chrome tests at 1400 and 375 px, alone and in a two-cell `layout()`; `check_integrity` and a bokeh-logger capture assert no E-/W- line; the one pin is flipped with its reason.

## Dependencies

- **Depends on:** none.
- **Blocks:** none in WP-34. Across WPs, 45-04 (WP-45) builds on this section's `_dash_frame_sizes` and test/test_sizing_browser.py (DECISIONS A-1).
- **Parallel batch:** 34.1 with 34-01 and 34-05; disjoint functions (`_dash_frame_sizes` only).

## Evidence

### Code at 090d928 (re-read before editing)

```python
27650 def _dash_frame_sizes(fig, ar, placement, width, height):
 ...
27672     fig.sizing_mode = "fixed"
27673     fig.frame_width, fig.frame_height = fw, fh
27674     fig.min_border_left = int(round(b["left"] + xl))
27675     fig.min_border_right = int(round(b["right"] + sx - xl))
27676     fig.min_border_top = int(round(b["above"] + yt))
27677     fig.min_border_bottom = int(round(b["below"] + sy - yt))
```
Caller `_dash_apply_frame_aspect` (:27680; the bound `k` :27696, `fig._dash_frame_box = (int(round(width)), int(round(height)))` :27699) at :64007 (saved) and in the served literal :70704 (`_dash_apply_frame_aspect(fig, go, _SCHEME_GRAPHSIZE_X, _SCHEME_GRAPHSIZE_Y)`). Constructor kwargs `max_height=_MAX_FIGURE_HEIGHT, min_height=_MIN_FIGURE_HEIGHT` (:63428-63429). Both functions are copied into the served app by name (the function tuple holding `_dash_apply_frame_aspect, _dash_overhangs, _dash_fxy_size`, :68113); confirm `_dash_frame_sizes` is in the copy lists with `grep -n '"_dash_frame_sizes"\|_dash_frame_sizes,' dash_render.py` -- it must be (the served app calls it today).

### twoway's truth

[S] §7 (720 SVG units an inch): `scatter mpg weight, aspectratio(2) xsize(8) ysize(4)` draws an 8x4 in page with a 1.726x3.276 in plot region (ratio 1.898; with the plot region's own margin m = 63.4 units the inner ratio is 2); `aspectratio(1) xsize(5) ysize(5)` a 4.018x4.018 in region. test/fixtures/sizing_truth.json `ar_place_*` holds the placement rows (`e` right, `w` left, `n` top, `s` bottom, `c` centred). [B] §4.6 measured dash's fix V1 on both bokeh versions: ar 2 xsize 8 ysize 4 host 768x384 frame 168x334; ar 1 xsize 8 host 768x384 frame 334x334; ar .5 xsize 6 ysize 3 host 576x288 frame 476x238; no message.

### Tests pinning today's behaviour

- test/test_sizing.py:268-275 `TestAspect::test_survives_sizes` asserts `f.aspect_ratio == pytest.approx(2.0)` -- flip to `f.aspect_ratio is None` and add `(f.width, f.height) == f._dash_frame_box` and `f.min_height is None and f.max_height is None`.
- test/test_sizing.py `TestAspect::test_placement_borders` (:277) stays green (borders unchanged).
- Pattern for "no validation output": test/test_responsive_layout.py:691 `test_no_validation_warning` (`bokeh.core.validation.check_integrity` over every model).

## User stories

- US-34-04.1 As a Stata user with an existing twoway command, I want `aspectratio(2) xsize(8) ysize(4)` to draw an 8x4 in graph with a tall plot region, so that my graph is never an empty frame.
- US-34-04.2 As that user, I want no Bokeh error line in my Results window when I give these options.
- US-34-04.3 As a dashboard author, I want such a figure to keep its size in a narrow cell rather than collapse.

## Business requirements

- BR-34-04.1 With aspectratio() and xsize() or ysize() the figure is drawn at the xsize()/ysize() box (96 px an inch, held to the page's height bound) and its plot region at ratio # within 1%, placed as placement() says, in both modes.
- BR-34-04.2 No plot region is ever 0 px wide or tall.
- BR-34-04.3 Building such a graph prints no Bokeh validation message.
- BR-34-04.4 Without xsize()/ysize() nothing changes.

## Technical requirements

- TR-34-04.1 `_dash_frame_sizes` (dash_render.py:27650): after `fig.sizing_mode = "fixed"` (:27672) add, in this order, `fig.width = int(round(float(width)))`, `fig.height = int(round(float(height)))`, `fig.min_height = None`, `fig.max_height = None`, `fig.aspect_ratio = None`. Nothing else changes; the docstring gains one sentence: "The figure's width and height are the box and its height bounds and aspect ratio are cleared (WP-34 VF-3): with a fixed policy BokehJS sizes the host from them, and Bokeh's default 600 against max_height 560 drew a 0 px frame."
- TR-34-04.2 Served mode: no literal change -- the served app calls the copied `_dash_apply_frame_aspect`/`_dash_frame_sizes`. No new function or constant: no copy-list or function_test_map.py entry.
- TR-34-04.3 Validation test: build each probe in both modes, collect every model of the root(s), run `bokeh.core.validation.check_integrity(models)` and assert no error and no warning code; also attach a `logging.Handler` to the `bokeh` logger around `render()` (saved) / document creation (served) and assert no record whose message contains `E-10` or `W-10`.
- TR-34-04.4 Chrome test (release tier, `pytestmark = pytest.mark.release`, skipped without Chrome as test/test_by_axes_keys_browser.py:29-30 skips): with `responsive_probe.measure_many(page, widths)` and the module-level helper `_frame_probe(page, name)` (D-34-04.d), whose JS finds the Plot view of the figure (`Bokeh.index` views whose `model.name` is the graph's name) and posts `[view.el.offsetWidth, view.el.offsetHeight, view.frame.bbox.width, view.frame.bbox.height]`; for each probe at 1400 px and 375 px: host equals `_dash_frame_box` within 2 px, frame width and height both above 0, frame height/width within 1% of #; in a `layout()` of two cells the same.

## Boundaries

- Do not touch `_dash_apply_frame_aspect`'s box arithmetic (its bound `k` is 45-04's to remove, A-1), `_dash_frame_borders`, `_dash_overhangs`, `_make_figure_body` (R12) or the by() path.
- No resize hook (D-34-04.b); no change to xsize()/ysize() without aspectratio(), to the 160-560 px band or to relative sizes (45-04, A-1).
- R14 banned topics; Chrome is the only browser.

## Stata truth

None new: [S] §7 and test/fixtures/sizing_truth.json are the truth. Truth block in test/test_wp34_truth.cscript, inserted directly above the first block whose `S<MM>` is higher than S04 (BRIEF "Block order"), or above `* ==== append new blocks above this line ====` if there is none (at the batch-34.1 base there is none; 34-01's S01 and 34-05's S05 land beside it in merge order). The cscript keeps only live twoway-against-dash comparisons and what no pytest can see (REVIEW R2-47): the page model is TestFixedFrame's.

```
* ==== S04 VF-3: aspectratio() with xsize()/ysize() draws its frame ====
local only : env WP34_ONLY
if inlist("`only'", "", "S04") & `: list posof "S04" in w34_run' {
    display as text "S04 start " c(current_date) " " c(current_time)
    ...
    display as text "S04 end " c(current_date) " " c(current_time)
}
* ==== end S04 ====
```
- Q3404-1 (twoway against dash, live): for `scatter mpg weight, aspectratio(2) xsize(8) ysize(4)`, `aspectratio(1) xsize(5) ysize(5)` and `aspectratio(.5) xsize(6) ysize(3)`: twoway's plot-region ratio, read from its SVG (`cert_svg_export`, then a python helper defined above the S04 block that calls `scripts/svg_truth.py`'s `svg_plotregion` and returns (bottom - top - 2m)/(right - left - 2m), m = 63.4 SVG units, the [S] §7 rule), and the ratio dash draws for the same command (`dash scatter ..., <same options> saving(<dir>/arN.html, replace)`; the same helper reads the page's figure `frame_height`/`frame_width` from its JSON, as test_wp31_truth.cscript's `_u45_has` (:12425-12443) reads the page JSON; 34-01's `_q34_has` is not yet on this worktree's base) agree within 2%, and both are within 2% of #; and twoway's graph size, read from the same SVG's `viewBox` (its width/720 and height/720 inches, times 96 px), equals the width and height of the page JSON's figure within 1 px: 768x384, 480x480 and 576x288. The ratio part passes at the base: `_dash_frame_sizes` already writes `frame_width`/`frame_height` at ratio # (`fw = min(iw, ih / ar)`, `fh = fw * ar`, dash_render.py:27665-27673), and the 0 px plot is BokehJS's layout, which never reaches the page JSON. The size part fails there: at the base the figure's `width`/`height` are never set (TR-34-04.1 sets them to the box), so the page JSON carries none and the case fails.
- Q3404-2 (what no pytest sees): each `dash scatter ...` of Q3404-1 runs under `log using <dir>/arN.log, text replace`; the log holds no `E-1023` and no `E-10`/`W-10` line from bokeh's validator (`cert_file_has`; it clobbers r(), so save r() first). The width/height/bounds model checks are TestFixedFrame's and are not repeated here (REVIEW R2-47).

## TDD test stubs

Regression tests (red at the base):
- Test: for the three [B] §4.6 probes, `(f.width, f.height) == f._dash_frame_box`, min/max height and aspect ratio None, `f.frame_height / f.frame_width` within 1% of # -- test/test_sizing.py::TestFixedFrame::test_box_and_ratio[saved|served-probe]
- Test: no validation error or warning and no `E-10`/`W-10` bokeh log record -- test/test_sizing.py::TestFixedFrame::test_no_validation_message[saved|served-probe]
- Test: in Chrome, host = box, frame above 0 px and at ratio #, at 1400 and 375 px, alone and in a two-cell layout() -- test/test_sizing_browser.py::TestFixedFrameInChrome::test_frame[saved|served] (new file, release tier)
- Test: placement(e) puts the frame against the host's right edge (frame right within 2 px of host right less the right axis estimate) in Chrome -- ::TestFixedFrameInChrome::test_placement_e[saved|served]
cscript: Q3404-1, Q3404-2.
Pinned test to flip: test/test_sizing.py::TestAspect::test_survives_sizes.
Parity: append to `CORPUS` `_case("aspectratio 2 xsize 8 ysize 4", [_sc()], go={"aspectratio": "2", "xsize": "8", "ysize": "4"})`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Model: box, cleared bounds, ratio | pytest TestFixedFrame | -- | yes |
| No validation message | pytest (check_integrity + logger) | -- | yes |
| Drawn frame, never 0 px | Chrome (release) | -- | yes |
| twoway's region ratio against dash's frame ratio, and twoway's graph size against dash's figure size, live | cscript Q3404-1 | sizing_truth.json | saved |
| No Bokeh validation line in Stata's log | cscript Q3404-2 | -- | saved |
| Parity | test_mode_parity CORPUS | -- | yes |

AC-34-04.1 the three probes draw a frame of ratio # within 1% at the box size in both modes; AC-34-04.2 no plot is 0 px at 1400 or 375 px; AC-34-04.3 no E-1023 in the build log; AC-34-04.4 one green commit.

## Tasks

**Commit boundary.** 34-04-01 to 34-04-03 form one commit, subject `Draw aspectratio()'s frame at the xsize()/ysize() box with no height bounds left (WP-34 VF-3)`, made by 34-04-03 on branch `wp34-s04` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s04`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (34-04-03 for VF-3) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-04/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-04 <scratch>/34-04/run_test_wp33_truth.do` and read `<scratch>/34-04/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-04/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-04-01">
  <name>Write failing frame and validation tests</name>
  <files>test/test_sizing.py, test/test_sizing_browser.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read _dash_frame_sizes, _dash_apply_frame_aspect and the served call (:70703-70705) at the batch base; run `node .gitnexus/run.cjs impact "_dash_frame_sizes" --direction upstream --repo .` and write callers and anchors to <scratch>/34-04/anchors.txt. Add class TestFixedFrame to test/test_sizing.py (reuse its `_figure(mode, tmp_path, go)` helper; probes {"aspectratio": "2", "xsize": "8", "ysize": "4"}, {"aspectratio": "1", "xsize": "8"}, {"aspectratio": ".5", "xsize": "6", "ysize": "3"}). Create test/test_sizing_browser.py per TR-34-04.4, copying test/test_by_axes_keys_browser.py's `_page`/`_measure` pattern, with `_frame_probe(page, name)` at module level (D-34-04.d). Insert the S04 block (Q3404-1, Q3404-2) and its python helper above it, at the place the Stata truth section names. Run `python3 -m pytest test/test_sizing.py test/test_sizing_browser.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-04/01.log`, run the S04 block with WP34_ONLY=S04 through the driver, and save the failure lines to <scratch>/34-04-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/34-04/01.log` is at least 6 (the Chrome tests fail rather than skip when Chrome is present; if they skip, record that in the failure file); `grep -c "Q3404-[12] FAIL" <scratch>/34-04/run_test_wp34_truth.log` is 2; `test -s <scratch>/34-04-01-failure.txt`.]]></verify>
  <done>The model, validation, Chrome and live-Stata tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-04-02">
  <name>Size the fixed figure at its box</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-34-04.1 in _dash_frame_sizes. Run test/test_sizing.py, test/test_sizing_browser.py, test/test_responsive_layout.py, test/test_layout*.py -k "aspect or size", test/test_overhang*.py if present, and test/test_csp.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_sizing.py -k "FixedFrame" test/test_sizing_browser.py test/test_responsive_layout.py -q -n0 -p no:cacheprovider` ends with 0 failed; `test_survives_sizes` is the only failure in test/test_sizing.py before its flip.]]></verify>
  <done>Every aspectratio() figure with xsize() or ysize() is drawn at its box with a frame of ratio # and no validation message.</done>
</task>

<task type="auto" id="34-04-03">
  <name>Flip the pin, correct the help, close VF-3</name>
  <files>test/test_sizing.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
Flip TestAspect::test_survives_sizes as the Evidence says, with the comment `# Flipped (WP-34 VF-3): aspect_ratio 2 was the leftover that collapsed the frame; the box is the figure's width and height now.` Append the CORPUS entry to test/test_mode_parity.py. In dash.sthlp's aspectratio() paragraph (:5670-5679) replace "The room the axes and titles take is estimated, so the figure's size can differ from {cmd:xsize()} by a few pixels." with "The figure is drawn at that size; the room the axes and titles take is estimated, so the plot region can differ from the largest fit by a few pixels.  Such a figure keeps its size in a cell narrower than it, which then scrolls sideways." (the clause "held to the page's height bound" before it stays; 45-04 rewrites it when it removes the bound, A-1) Add a help-claim test test/test_sizing.py::TestFixedFrameHelp::test_the_size_sentence that reads the new sentence with the `_between(_help(), ...)` pattern of test/test_help_claims_1.py (import its helpers). Append `[WP-34 VF-3: corrected -- aspectratio() with xsize()/ysize() drawn at that size, never a 0 px frame]` to the Proportions row of TWOWAY_COVERAGE_AUDIT.md (:145). Close the BUGS.md entry 33-01 registered for VF-3 with PD-4's closed form (what changed: _dash_frame_sizes sets width/height to the box and clears min_height, max_height and aspect_ratio, both modes; pinned by test/test_sizing.py::TestFixedFrame::test_box_and_ratio, test/test_sizing_browser.py::TestFixedFrameInChrome::test_frame and Q3404-2), rewrite `- **VF-3 Tracked:**` to the Closed form with `commit pending`, delete VF-3's line from `GAPS4_OPEN` in test/test_tracking_documents.py, and add `- aspectratio() with xsize()/ysize() draws its plot region at that size and ratio; aspectratio(2) xsize(8) ysize(4) drew a 0 px plot and printed Bokeh's E-1023 (WP-34, VF-3)` under `### Fixed in WP-34`. Run the Closing steps for VF-3 (Tasks; BRIEF steps (1)-(3)): (1) delete VF-3's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py VF-3`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-04) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_sizing.py, test/test_sizing_browser.py, test/test_mode_parity.py -k aspectratio, test/test_help_conformance.py, test/test_tracking_documents.py and the S04 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_sizing.py test/test_sizing_browser.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3404-[12] PASS" <scratch>/34-04/run_test_wp34_truth.log` prints 2; `awk -F'\t' '$1 == "VF-3"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py VF-3` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-04/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 VF-3)`.]]></verify>
  <done>aspectratio() with xsize()/ysize() draws its frame exactly and silently in both modes, and VF-3 is closed in one commit.</done>
</task>

## Section completion criteria

- Three probes at ratio # within 1% in both modes, never 0 px, no Bokeh validation line; the pin flipped; the help sentence corrected and pinned; tracking documents updated; one green commit.

## Notes

- **Help (R3, HR-12):** this section owns the one sentence of dash.sthlp:5670-5679 named in 34-04-03; :5653-5655 and the "held to the page's height bound" clause are 45-04's.
- **DECISIONS A-1:** this section is the base of WP-45's figure geometry. Keep `_dash_frame_sizes`' new lines in one block after `fig.sizing_mode = "fixed"` and keep `_frame_probe` a reusable module-level helper, so 45-04 calls the first and extends the second without rewriting them; name A-1 in the commit body.
- **Help-claim test** lives in test/test_sizing.py (no shared new file, so no same-batch file conflict with 34-01 or 34-05).
- **GitNexus:** run `impact` on `_dash_frame_sizes` before editing (34-04-01) and `detect-changes --scope all` before committing; report HIGH/CRITICAL or UNKNOWN risk in the handback.
- **Trap:** `fig.width`/`fig.height` must be ints; Bokeh refuses floats on some versions.
- **Trap:** the served app's figure is created by `figure(...)` in the template with the same kwargs; the clearing happens after, in the copied function -- verify the served model too (TestFixedFrame runs both modes).
- **Commit body line forms:** `Regression: test/test_sizing.py::TestFixedFrame::test_box_and_ratio -- failed at <base sha> with <text>`; `Flipped: test/test_sizing.py::TestAspect::test_survives_sizes -- aspect_ratio 2.0 was wrong because the leftover ratio collapsed the frame`; `BUGS.md: "<title>" (closed)`; `GAPS4: VF-3 Tracked`.
- Merge rules touched: R1, R3, R8, R9.
