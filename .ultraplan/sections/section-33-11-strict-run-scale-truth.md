# Section 33-11: Strict run passes; scale() frame geometry truth

> Part of: WP-33 (Verification corpus and README gallery) · Items: TR-23, GW-11 · Risk: yellow · Batch: 33.3 · Depends on: 33-01, 33-10 (test/known_differences.py) · Blocks: WP-33 WE (the recorded strict run) · Tasks: 6, 2 commits · Case-id prefix: Q3311

## Overview

**What is wrong today.** TR-23 (audit :678-680, appendix :2655-2662): "No green strict batch-end run is recorded on HEAD; TestBounds (4 runs) always skips, so DASH_STRICT=1 cannot pass". `make test-all` runs pytest with `DASH_STRICT=1` (scripts/run_all_tests.sh:32), and `test/conftest.py:196-209` turns any skip into a failed session. The 19oct2026 gate recorded 11 skips (ROADMAP.md:5155). Measured here at `090d928` with targeted runs: 8 of them are in test/test_graph_text.py -- `TestBounds::test_dup_is_cut`, `::test_hline_is_cut`, `::test_note_once[saved|served]` (skipif `not _dup_expands()`, :1323-1338, because twoway draws `{dup 1000:x}` as typed: smcl_text_truth.json `smcl.dup_big.text == typed`) and `TestOtherSmclDirectives::test_each_directive[...-xlabel|legend-smcl.browse]` in both modes (runtime skip "a double quote ends a tick or legend label", :1292-1293) -- and 1 is test/test_mode_parity.py:6246-6247 `TestTheExportsAgree::test_the_moves_reach_the_exports[at build]` ("the build state has no move"). The other two were not reproduced by targeted runs of the 15 files with skip sites (scratch `skips.log`: 1,530 passed, 0 skipped).

GW-11 (audit :693-695, appendix :1709-1714): "scale() frame geometry is never compared with truth; the help wrongly says gaps are not scaled". twoway's plot region is linear in k: top = 100.86 + 174.49k and left = 100.8 + 289.94k (sizing_truth.json base, scale_15, scale_05; s2color, 5.5 x 4 in), so the title and label gaps scale and only the region margins stay. `_dash_apply_scale` (dash_render.py:27529-27606) already scales standoffs, paddings, tick lengths and the legend's spacing, but dash.sthlp:5686-5690 and the function's docstring (:27536-27537) say "the gaps between boxes are not scaled", and `test/test_sizing.py::TestScale` (:169-200) checks sizes only.

**After this section.** Every test that skipped on a measured false premise runs and asserts twoway's measured answer; a static guard proves no skip site is left in them; the batch 33.3 gate is the first strict run with no skip from them, and WP-33's WE.4 records the green strict run. A committed extract script measures the plot region and text boxes of twoway under scale(0.5, 0.75, 1, 1.5, 2) for two commands; a Chrome test (release tier, A-10) compares dash's frame insets with it (slopes, linearity, and intercepts with known differences keyed by GAPS4 ids), while the fixture's own check and the known table's hygiene run in the default tier; the help sentence says what twoway and dash do.

**Why one section.** Both are WP-33's coverage hygiene with no dash code change; GW-11's comparison is the strict tier's first frame-geometry truth.

**Test order and commit rule.** TR-23 first (tasks 01-02), then GW-11 (tasks 03-06) on the tree TR-23's commit leaves. Two commits.

### Section decisions (binding on the executor)

- **D-33-11.a Convert, never delete (CLAUDE.md, R9).** A test that skips because its premise is measured false is rewritten in place to assert the measured truth, its skip removed, its name changed only when the old name states the false premise; the commit body carries `Flipped: <old node> -> <new node> -- <reason>`. Here: `test_dup_is_cut` -> `test_dup_past_its_bound_is_drawn_as_typed`, `test_hline_is_cut` -> `test_hline_past_its_bound_is_drawn_as_typed`, `test_note_once` -> `test_no_cut_note_past_a_bound` (same class, same place). `test_each_directive` keeps its name: the quoted keys are written with compound double quotes in the xlabel and legend sinks (measured here: `xlabel(2000 \`"a {browse "https://www.stata.com":xy} b"')` and `legend(label(1 \`"..."'))` draw `a xy b` in both modes, the fixture's text). `test_the_moves_reach_the_exports` keeps its name; at the build state it asserts that two saved exports of the build are equal (the state the guard compares against is deterministic).
- **D-33-11.b Skips found later.** Any other skip the batch 33.3 gate's strict verdict names (`strict mode (DASH_STRICT=1): <n> test(s) skipped` lines in `$out/pytest.log`) is converted on s3-bugs in step k.5 by D-33-11.a, its node added to `_STANDING_SKIP_NODES` (TR-33-11.1) so the guard covers it, and its conversion named in the batch's tracking commit. An environment skip (Chrome or node missing) is not converted: the gate machine has both.
- **D-33-11.c TR-23 closes Fixed** in this section's commit; its resolution says the strict whole-suite run is recorded in ROADMAP's WP-33 section by WE.4 (the index's WE step), and the batch 33.3 gate is its first run.
- **D-33-11.d GW-11 truth.** A new script, not an edit of extract_sizing_truth.do (whose fixture other tests pin): `scripts/extract_scale_frame_truth.do` -> `test/fixtures/scale_frame_truth.json`, scheme s2color (the shape dash's default figure has at 528 px, 1.375), sentinels `plotregion(lcolor("1 2 3")) graphregion(lcolor("4 5 6"))`, k in 0.5 0.75 1 1.5 2, commands A `twoway scatter mpg weight, title("T")` and B `twoway (scatter mpg weight) (lfit mpg weight), title("T") subtitle("S") ytitle("Y") xtitle("X") note("N")` (legend at the bottom, a note under it).
- **D-33-11.e The comparison.** In Chrome at a 528 px wide page (dash's lone figure fills the width; s2color's 1.375 ratio gives 384 px, inside the 160-560 band), dash's frame insets (top, left, bottom, right, in CSS px, from the figure view's `frame.bbox` against the figure's own bbox) are fitted against k by least squares per side. Twoway's insets are converted at 96 px per inch (SVG units / 720 * 96). Per side and command: (1) linearity -- dash's residuals within 1.5 px; (2) slope -- within 15 % of twoway's or 2 px per unit k, whichever is larger; (3) intercept -- within 3 px. A failing comparison is a known difference only when listed in `SCALE_FRAME_KNOWN = {"<command>:<side>:<slope|intercept|linear>": "<GAPS4 id>"}` (D-33-10.a's three value forms), kept in its own module `test/scale_frame_known.py` so the default-tier hygiene test and the release-tier comparison read one table: intercepts by the graph margin -> `GW-6` (45-04); slopes by relative text sizes -> `VF-4` (45-04); the bottom side of B by the legend's box -> `LT-6` (43-03). A failure that none of these explains stops the section at task 05's checkpoint.
- **D-33-11.f Help.** The scale() paragraph (dash.sthlp:5686-5690) becomes: "... reference lines -- by {it:#}, as in {helpb twoway}, and with them the gaps around titles, labels, keys and added text; only the graph region's margins stay as they are." This is true of twoway (the fixture) and of dash (the comparison's slopes); if the checkpoint finds dash's slopes listed as differences, the sentence adds "dash's differences are listed under {help dash##differences:Differences from twoway}" -- no new Differences entry (the item is Fix, not Document).
- **D-33-11.g The docstring** of `_dash_apply_scale` (:27536-27537) is left as it is: the index makes the function read-only here. 45-04 (figure geometry) corrects it; this section names it in its hand-back.
- **D-33-11.h Tiers (A-10; REVIEW-1 R1-34).** The Chrome comparison stays in the release tier (A-10: Chrome scale and position comparisons stay there). Everything that needs no Chrome runs in the default tier, so `make test` and every gate run it: twoway's fixture check (`test_twoway_scales_the_gaps`) and the table's hygiene (`test_every_known_difference_is_open`, `dead_rows(SCALE_FRAME_KNOWN, "scale_frame") == []`, D-33-10.a's rule 3) live in test/test_sizing.py's new class `TestScaleFrameTruth` (test_sizing.py already has a `TestTheFixture`, :140, for sizing_truth.json). A WP-45 fix that closes GW-6 or VF-4 and leaves a plain row therefore fails at its own gate.
- **D-33-11.i The strict guard is static (REVIEW-1 R1-36).** Strict mode already fails any skip at the gate (conftest.py:196-209); a nested pytest of the same nodes would test that again and add about 70 tests to every `make test`. The guard instead reads the converted nodes' source with `ast` and fails on any skip site left in them.

## Risk: [yellow] -- a strict skip found only by the gate; a Chrome geometry test with tolerances

**Risk factors.** (1) The two unreproduced skips. (2) Converting a test can turn it red if dash differs from twoway. (3) Chrome layout varies by a pixel between runs. (4) Tolerances chosen too loose hide a difference, too tight flap.

**Mitigation.** (1) D-33-11.b. (2) Measured before writing: dash already draws `{dup 1000:x}` and `{hline 100000}` as typed with no `cut` flag (`dr._dash_graph_text_parts(...)[3] == ()`), and the compound-quoted sinks draw the fixture text. (3) Integer-rounded bboxes and the least-squares fit over five k values. (4) D-33-11.e's three thresholds are stated; the checkpoint shows the measured numbers to the maintainer.

## Dependencies

- **Depends on: 33-01** (GAPS4.md, the BUGS entries, test_wp33_truth.cscript) and **33-10** (batch 33.2: `test/known_differences.py`, the known-differences rule D-33-10.a).
- **Blocks:** WP-33's WE.4 (the recorded strict run).
- **Parallel batch 33.3:** with 33-03 (scripts/corpus/ twoway runner) and 33-07 (graph frames: `_dash_register_graph`, `_dash_prepare_spec`, `_dash_write_data`, `_dash_build`). Disjoint: this section edits test files, dash.sthlp's scale() paragraph, one new extract script and its fixture.

## Evidence

**TR-23.** test/test_graph_text.py:1311-1338:

```python
def _dup_expands():
    ...
    rec = _smcl_truth()["smcl.dup_big"]
    return rec.get("text") != rec["typed"]
_NO_CUT = "twoway draws {dup 1000:x} as typed: no count is cut (D-42b)"
class TestBounds:
    @pytest.mark.skipif(not _dup_expands(), reason=_NO_CUT)
    def test_dup_is_cut(self):
        flags = dr._dash_graph_text_parts("{dup 1000:x}")[3]
        assert "cut" in flags
```

`test_total_budget` (:1340) and `test_cut_note_once` (:1355) run unconditionally and stay. smcl_text_truth.json: `smcl.dup_big` `typed == text == "{dup 1000:x}"`; `smcl.hline` variants `h256`, `h300` drawn as typed (`{hline 256}`, `{hline 300}`); `smcl.browse` typed `a {browse "https://www.stata.com":xy} b`, text `a xy b`. The class fixture `smcl_sinks` (:1255-1284) writes only unquoted keys into the xlabel and legend sinks (`plain`); the runtime skip at :1292-1293. test/test_mode_parity.py:6118-6123 `_EXPORT_STATES` ("at build", []) and :6243-6250. conftest.py:196-209 (`_strict_verdict` :735-743). BUGS.md:3693 names `TestBounds::test_total_budget` (kept).

**GW-11.** sizing_truth.json `plot` boxes (SVG units, 3960 x 2880 canvas): base top 275.35 left 390.8 bottom 2489.18 right 3859.02; scale_15 362.6 / 535.71 / 2344.27 / 3859.02; scale_05 188.11 / 245.77 / 2634.23 / 3859.02 (right fixed: no right-side text). `_dash_apply_scale` scales Axis font sizes, tick lengths, `axis_label_standoff`, `major_label_standoff`; Title/Label `padding`, `standoff`, `offset`; Legend `spacing`, `padding`, `margin`, glyph sizes; it does not touch the figure's `min_border*`. Help dash.sthlp:5686-5690 (quoted in Overview). Chrome access: `test/range_probe.py::RangeProbe` (`_eval` :241, `_wait_for` :251), the pattern of `test/test_default_axes_chrome.py:49-50` reading views through `Bokeh.index`.

## User stories

- **US-33-11.1** As the maintainer, I want a strict batch-end run to be able to pass, so that a skip is never mistaken for a pass.
- **US-33-11.2** As the Stata user, I want `scale()` to move the plot region as twoway moves it, and the help to say so truly.

## Business requirements

- **BR-33-11.1** No test skips because a measured truth contradicts its premise; such a test asserts the truth instead.
- **BR-33-11.2** WP-33's closeout records a strict whole-suite run with no skip.
- **BR-33-11.3** dash's plot-region insets under scale() are compared with twoway's measured ones; every difference is listed under the item that fixes it.
- **BR-33-11.4** The help's scale() sentence is true of twoway and dash.

## Technical requirements

- **TR-33-11.1 (TR-23 guard)** In test/test_strict_mode.py append `class TestNoStandingSkip` with module constant `_STANDING_SKIP_NODES = ("test/test_graph_text.py::TestBounds", "test/test_graph_text.py::TestOtherSmclDirectives::test_each_directive", "test/test_mode_parity.py::TestTheExportsAgree::test_the_moves_reach_the_exports")`, a helper `_skip_sites(node) -> list[str]` and `test_none_of_them_can_skip(self)` (D-33-11.i). `_skip_sites` splits the node at `::`, parses the file with `ast.parse`, finds the class and, when named, the method (every method of the class otherwise), and returns `"<file>:<line>: <what>"` for each skip site in them: a decorator whose dotted name ends `mark.skip` or `mark.skipif` (bare or called), and a call whose dotted name is `pytest.skip`, `pytest.importorskip` or `pytest.xfail`; a node that names no class or method is a site too (`"<node> not found"`). The test asserts `[s for n in _STANDING_SKIP_NODES for s in _skip_sites(n)] == []`. No subprocess, no nested pytest; default tier.
- **TR-33-11.2 (TR-23 conversions)** test/test_graph_text.py: `test_dup_past_its_bound_is_drawn_as_typed` -- `text, flags = dr._dash_graph_text_parts(t)[0], dr._dash_graph_text_parts(t)[3]` for `t = _smcl_truth()["smcl.dup_big"]["typed"]`: `"cut" not in flags` and `dr._dash_graph_text(t)[0] == _smcl_truth()["smcl.dup_big"]["text"]`; `test_hline_past_its_bound_is_drawn_as_typed` -- the same over the `smcl.hline` variants `h256` and `h300`; `test_no_cut_note_past_a_bound[mode]` -- the old build, assert no note holds "was cut". `smcl_sinks`: for the quoted keys build a second xlabel spec `" ".join('%d \`"%s"\'' % (...))` and legend spec with `label(%d \`"%s"\')`, store under `out[(mode, "xlabel_q")]` / `"legend_q"`; `test_each_directive` reads the `_q` entry for a quoted key instead of skipping. test/test_mode_parity.py:6246-6247: replace the skip with `assert _saved_exports(_EXPORT_SPEC, []) == _saved_exports(_EXPORT_SPEC, []); return`, a `# Flipped (WP-33 TR-23): ...` comment above it.
- **TR-33-11.3 (GW-11 extract)** Create `scripts/extract_scale_frame_truth.do` on the form of scripts/extract_sizing_truth.do (re-read its root guards, `_zs_run`, the export and the python block; copy them with the prefix `zf`): for command in A B and k in 0.5 0.75 1 1.5 2 run `<cmd> scale(<k>) <sentinels> name(zf1, replace)` under `set scheme s2color`, export SVG, and in the python block read with scripts/svg_truth.py (`svg_document`, `svg_rects`, `svg_texts`) and scripts/svg_chrome.py (`svg_region` with the two sentinels) the graph and plot region rects and each text's x, y and anchor. Fixture keys `"A:0.5"` ... `"B:2"`, each `{"rc", "canvas": {w,h}, "graph": box, "plot": box, "texts": [{text,x,y,anchor,size}]}`; `_meta` five keys (`git rev-parse HEAD` through `shell` into a local, read with `Macro.getLocal`, a backtick written `\x60`); `"rules"`: the least-squares slope and intercept of each plot side against k, per command. Add `"scale_frame_truth.json": "scripts/extract_scale_frame_truth.do"` to `GENERATORS` (test/test_fixtures_are_committed.py:257, alphabetical, after `"scale_..."` or before `"scheme_..."` as the sort puts it).
- **TR-33-11.4 (GW-11 comparison)** Create `test/scale_frame_known.py` holding `SCALE_FRAME_KNOWN = {}` (filled at task 06, one `"<command>:<side>:<check>": "<id>",  # twoway <x> / dash <y>` per line, sorted) and `SCALE_FRAME_DELIBERATE = {}` (D-33-10.a's companion dict for a difference a ruling keeps; empty). Create `test/test_scale_frame.py` (`pytestmark = pytest.mark.release`, Chrome via `responsive_probe.find_chrome`, skip when absent as the other release files do), holding only the Chrome comparison: `TestDashAgainstTwoway::test_the_insets[A|B]` builds each command's saved page with `DashRenderer` (spec: scatter, and scatter + lfit with title/subtitle/ytitle/xtitle/note graph options, `scale` = k, scheme s2color, auto's columns from `conftest.auto_df`), opens them with a local `_ScaleProbe(RangeProbe)` whose `viewport(w, h)` sends `Emulation.setDeviceMetricsOverride {width: w, height: h, deviceScaleFactor: 1, mobile: false}` through `self._send`, evaluates `window.__dashOld = true`, sends `Page.reload` and waits with `self._wait_for("!window.__dashOld && (" + _READY_JS + ")")` (RangeProbe hard-codes `--window-size=1200,900`, range_probe.py:158, and is read-only here; 33-04's `CorpusProbe.viewport` lands a batch later; REVIEW-1 R1-35), sets 528 x 900, then evaluates `const v = Object.values(Bokeh.index).find(v => v.model.type === "Plot" || v.model.type === "Figure"); JSON.stringify([v.bbox.top, v.bbox.left, v.bbox.bottom, v.bbox.right, v.frame.bbox.top, v.frame.bbox.left, v.frame.bbox.bottom, v.frame.bbox.right].map(Math.round))` (the `Object.values(Bokeh.index)` access `_TICKS_JS` uses, test_default_axes_chrome.py:66), and applies D-33-11.e through `known_problems(<results>, scale_frame_known.SCALE_FRAME_KNOWN, "scale_frame", deliberate=scale_frame_known.SCALE_FRAME_DELIBERATE)`. The served app draws the same figure model (GlyphMapper and the figure body are shared); a served-mode run of the same check is `TestDashAgainstTwoway::test_the_insets_served[A|B]` through `ServerAppBuilder` and `load_app` into a `Document`, serialised with `bokeh.embed.file_html` for the probe. In test/test_sizing.py (default tier) add `class TestScaleFrameTruth` after `TestScaleBounds` (:218): `test_twoway_scales_the_gaps` (every side but right has |slope| > 10 units per k and residuals < 1 unit in scale_frame_truth.json -- twoway's gaps scale) and `test_every_known_difference_is_open` (`dead_rows(SCALE_FRAME_KNOWN, "scale_frame") == []`, D-33-10.a's rule 3, every key of the form `<A|B>:<top|left|bottom|right>:<slope|intercept|linear>`; D-33-11.h).
- **TR-33-11.5 (GW-11 block)** In test_wp33_truth.cscript, directly above the marker (after S10's two blocks, batch 33.2): one top-level `python:` block holding the helper, directly above the block header (as WP-31 places its helpers; `_u32_plot`, test_wp31_truth.cscript:7386-7398, is the pattern), then `* ==== S11 GW-11: scale() frame geometry ====` in BRIEF's block form (gate `WP33_ONLY`, `S11 start`/`S11 end` lines). One method reads the plot region; `cert_graph_scale` (test/cert_svg.do:295-330) is not used, since it returns `.Graph` axis-scale members (min, max, curmin, major_*), not the region's box.
  - `_w33s11_plot()`: reads the locals `svg` and `key` with `Macro.getLocal` (no macro is expanded into Python text, as test/cert_svg.do's helpers do); inserts `<repo>/scripts` (`os.path.abspath("..")`, the cscript's parent) at `sys.path[0]`; reads twoway's plot region with `svg_chrome.svg_region(svg, "#010203")`, the `plotregion(lcolor("1 2 3"))` sentinel, exactly as extract_scale_frame_truth.do reads it (TR-33-11.3, copied from extract_sizing_truth.do:166, `box(svg_chrome.svg_region(path, "#010203"))`); sets the locals `top` and `left` to `"%.3f"` of the region's `top` and `left` (`.` when no sentinel rect is drawn) with `Macro.setLocal`, and `ftop` and `fleft` to the fixture's `json.load(open("fixtures/scale_frame_truth.json"))[key]["plot"]` `top` and `left` (the cscript runs in test/); removes the path in a `finally`.
  - The block: `local s11_scheme "\`c(scheme)'"`; `set scheme s2color`; `local d "\`w33_work'/s11"`; `capture mkdir "\`d'"`; for `k` in 0.5 1.5: `sysuse auto, clear`; `twoway scatter mpg weight, title("T") scale(\`k') plotregion(lcolor("1 2 3")) graphregion(lcolor("4 5 6")) name(zf1, replace)`; `cert_svg_export, name(zf1) file("\`d'/zf1_\`k'.svg")`; `local svg "\`r(file)'"`; `local key "A:\`k'"`; `python: __import__("__main__")._w33s11_plot()`; `_w33_expect Q3311-1 "(abs(\`top' - \`ftop') <= 0.5 & abs(\`left' - \`fleft') <= 0.5)" "scale(\`k'): twoway's plot region top \`top' left \`left', the fixture's \`ftop' \`fleft'"` (a missing `top` fails: missing is above every number); then `_w33_done Q3311-1 "twoway's plot region under scale() is the committed truth"`; `capture graph drop zf1`; `set scheme \`s11_scheme'` (never `permanently`), so later blocks keep the session's scheme. TR-23 adds no block (it has no Stata content).
- **TR-33-11.6 Maps.** No dash_render.py function or program added; function_test_map.py and program_coverage_map.py unchanged.

## Boundaries

- No edit of `_dash_apply_scale` or any dash_render.py code (read only, index); no new Differences entry; only dash.sthlp:5686-5690 changes (R3).
- Never delete a test (CLAUDE.md); `ALLOWED` in test_mode_parity.py untouched (R8).
- No `graph set` or permanent preference; the scheme is set per command.

## Stata truth

`scripts/extract_scale_frame_truth.do` (new): run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s11 $WT/scripts/extract_scale_frame_truth.do`; `git add -f test/fixtures/scale_frame_truth.json`; ten probes (two commands x five k). Live case Q3311-1.

## TDD test stubs

TR-23 (red at the base):
- Test: `test/test_strict_mode.py::TestNoStandingSkip::test_none_of_them_can_skip` -- red: five skip sites (three `skipif` decorators in TestBounds, the `pytest.skip` calls in `test_each_directive` and `test_the_moves_reach_the_exports`).
- Test: `test/test_graph_text.py::TestBounds::test_dup_past_its_bound_is_drawn_as_typed`, `::test_hline_past_its_bound_is_drawn_as_typed`, `::test_no_cut_note_past_a_bound[saved|served]` -- the converted tests (green once written: dash already matches; they replace skips).

GW-11 (red after TR-23's commit):
- Test: `test/test_sizing.py::TestScaleFrameTruth::test_twoway_scales_the_gaps` -- red: fixture missing.
- Test: `test/test_sizing.py::TestScaleFrameTruth::test_every_known_difference_is_open` -- red: `scale_frame_known` missing (default tier, D-33-11.h).
- Test: `test/test_sizing.py::TestScaleHelp::test_the_sentence_says_the_gaps_scale` -- reads the scale() paragraph with the `_between(_help(), ...)` pattern of test/test_help_claims_1.py; asserts "gaps between boxes are not scaled" absent and "the gaps around titles, labels, keys and added text" present -- red.
- Test: `test/test_scale_frame.py::TestDashAgainstTwoway::test_the_insets[A|B]`, `::test_the_insets_served[A|B]` (release tier, Chrome).
- cscript: `Q3311-1`.

Flips: TR-23's four nodes (D-33-11.a) and the parity node.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| no standing skip | pytest, static `ast` read of the nodes | -- | both (the nodes are) |
| converted bounds and sinks | pytest | smcl_text_truth.json | yes |
| twoway's gaps scale; known-table hygiene | pytest, default tier (test_sizing.py) | scale_frame_truth.json, scale_frame_known.py | -- |
| dash's insets vs twoway | pytest release, Chrome | scale_frame_truth.json | yes |
| help sentence | pytest help claim | dash.sthlp | -- |
| Stata drift | cscript Q3311-1 | scale_frame_truth.json | -- |

- **AC-33-11.1** `python3 -m pytest test/test_strict_mode.py::TestNoStandingSkip -q` passes; the batch 33.3 gate's strict verdict names none of `_STANDING_SKIP_NODES`; `python3 -m pytest test/test_sizing.py -q` runs `TestScaleFrameTruth` in the default tier and passes.
- **AC-33-11.2** `DASH_TEST_TIER=release python3 -m pytest test/test_scale_frame.py -q` passes with every difference listed under a live row.
- **AC-33-11.3** Two commits ending `(WP-33 TR-23)` and `(WP-33 GW-11)`.

## Tasks

**Commit boundary.** 33-11-01..02: TR-23, subject `Turn the tests that skipped on a measured false premise into checks of the truth (WP-33 TR-23)`, made by 33-11-02. 33-11-03..06: GW-11, subject `Compare the plot region under scale() with twoway's, and say the gaps scale (WP-33 GW-11)`, made by 33-11-06. Branch `wp33-s11` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s11`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-10.h). Each closing task (33-11-02 for TR-23, 33-11-06 for GW-11) runs them in `$WT` before staging. Batch 33.3 lands before the corpus ledger (scripts/corpus/ledger.tsv and ledger.py, 33-05, batch 33.5) and the guard (Q3309-1, 33-09, batch 33.6) exist, so steps (1) and (3) have nothing to run on yet (BRIEF applies them from WP-34 on; 33-14 runs all three for TR-2 in batch 33.7); step (2) runs for the item's lead id `<id>`: run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed. No row keyed to the closing item's own id is expected: SCALE_FRAME_KNOWN keys each difference to the item that fixes it (GW-6, VF-4, LT-6; D-33-11.e), so they stay live when this item closes. Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` and commits.

<task type="auto" id="33-11-01">
  <name>Write the standing-skip guard red</name>
  <files>test/test_strict_mode.py</files>
  <action><![CDATA[In worktree $WT (wp33-s11) append TR-33-11.1's class and helper to test/test_strict_mode.py (read its imports first; add `import ast` beside them). Run `python3 -m pytest test/test_strict_mode.py::TestNoStandingSkip -q -n0 -p no:cacheprovider > <scratch>/s11/01.log 2>&1` on the unmodified tree; save the failure (it lists the five skip sites) to <scratch>/33-11-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s11/01.log` prints 1; `grep -c "skip" <scratch>/33-11-01-failure.txt` is at least 5.]]></verify>
  <done>The guard existed and failed on the five standing skip sites.</done>
</task>

<task type="auto" id="33-11-02">
  <name>Convert the skipping tests; commit TR-23</name>
  <files>test/test_graph_text.py, test/test_mode_parity.py</files>
  <action><![CDATA[Run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` for each test function and fixture edited (`test_dup_is_cut`, `test_hline_is_cut`, `test_note_once`, `test_each_directive`, `smcl_sinks`, `test_the_moves_reach_the_exports`) and note the results (an UNKNOWN is unresolved: confirm with `grep -rn "<name>" test/`). Apply TR-33-11.2 (re-read test_graph_text.py:1255-1338 and test_mode_parity.py:6220-6250 first). Each converted test carries `# Flipped (WP-33 TR-23): <old> -- twoway draws {dup 1000:x} and {hline 300} as typed (smcl_text_truth.json), so there is nothing to cut` or, for the sinks, `-- a compound-quoted label carries the double quote`. Run `python3 -m pytest test/test_graph_text.py -q -n 8 -p no:cacheprovider -rs`, `DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k "TestTheExportsAgree" -q -rs -n0 -p no:cacheprovider` and test/test_strict_mode.py::TestNoStandingSkip: no skip, all pass. Close the TR-23 BUGS entry (title `GAPS4_OPEN["TR-23"]`): `Fixed <ddmonyyyy> (WP-33, TR-23). The nine tests that skipped because a measured truth contradicts their premise assert that truth instead (TestBounds: {dup}/{hline} past their bounds drawn as typed, no cut note; TestOtherSmclDirectives: quoted keys through compound quotes in the xlabel and legend sinks; TestTheExportsAgree at build: the build's exports are deterministic); the strict whole-suite run is the batch 33.3 gate's and is recorded in ROADMAP's WP-33 section by WE.4. Pinned by test/test_strict_mode.py::TestNoStandingSkip::test_none_of_them_can_skip, test/test_graph_text.py::TestBounds. Closes GAPS4 TR-23 (WP-33, TR-23).`; `- [x]`; Tracked line Closed `commit pending`; delete `"TR-23"` from `GAPS4_OPEN` in test/test_tracking_documents.py; CHANGELOG `### Fixed in WP-33`: `- No test skips on a premise twoway's measurements contradict, so a strict run can pass (WP-33, TR-23)`. Run the Closing steps for TR-23 (Tasks): steps (1) and (3) have nothing to run on at batch 33.3 (no ledger, no guard yet); (2) run `python3 test/known_differences.py TR-23`, delete every row it prints (none expected; nothing moves to a deliberate dict) and run the hygiene command it prints. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .`; commit on wp33-s11 with one `Flipped:` line per converted node.]]></action>
  <verify><![CDATA[The three pytest runs pass with `0 skipped`/no SKIPPED line; `python3 test/known_differences.py TR-23` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `git log -1 --format=%s` ends `(WP-33 TR-23)`; the claude|anthropic grep prints 0.]]></verify>
  <done>No test skips on a false premise and TR-23 was committed.</done>
</task>

<task type="auto" id="33-11-03">
  <name>Write GW-11's failing tests</name>
  <files>test/test_scale_frame.py, test/scale_frame_known.py, test/test_sizing.py</files>
  <action><![CDATA[Create test/scale_frame_known.py and test/test_scale_frame.py (TR-33-11.4) and append `class TestScaleFrameTruth` (TR-33-11.4) and `class TestScaleHelp` (TDD stub) to test/test_sizing.py after `TestScaleBounds` (:218). Run `DASH_TEST_TIER=release python3 -m pytest test/test_scale_frame.py "test/test_sizing.py::TestScaleFrameTruth" "test/test_sizing.py::TestScaleHelp" -q -n0 -p no:cacheprovider > <scratch>/s11/03.log 2>&1`; save the failures (fixture missing, help sentence) to <scratch>/33-11-03-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "FAILED\|ERROR" <scratch>/s11/03.log` is at least 2; `test -s <scratch>/33-11-03-failure.txt`.]]></verify>
  <done>GW-11's tests existed and failed for the missing truth and the false sentence.</done>
</task>

<task type="auto" id="33-11-04">
  <name>Measure twoway's frame under scale()</name>
  <files>scripts/extract_scale_frame_truth.do, test/fixtures/scale_frame_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_scale_frame_truth.do (TR-33-11.3), add its GENERATORS row, run it through the slot, `git add -f test/fixtures/scale_frame_truth.json`. Append the S11 GW-11 block (TR-33-11.5) to test/test_wp33_truth.cscript directly above the marker and run it with `WP33_ONLY=S11` (Q3311-1 PASS; note its seconds from the `S11 start`/`S11 end` lines for the hand-back, D-33-01.i). Run `python3 -m pytest test/test_fixtures_are_committed.py "test/test_sizing.py::TestScaleFrameTruth::test_twoway_scales_the_gaps" -q -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/scale_frame_truth.json'));print(len([k for k in d if ':' in k]), sorted(d['_meta']))"` prints 10 and the five keys; the two pytest targets pass; the driver log shows `Q3311-1 PASS`.]]></verify>
  <done>twoway's plot region and text boxes under five scale factors were committed truth.</done>
</task>

<task type="checkpoint" id="33-11-05">
  <name>Approve the measured scale() differences</name>
  <files>none</files>
  <action><![CDATA[Run `DASH_TEST_TIER=release python3 -m pytest test/test_scale_frame.py -q -n0 -p no:cacheprovider -rf` and show the maintainer, per command and side, twoway's and dash's slope and intercept and the residuals, with the GAPS4 id D-33-11.e assigns to each failing comparison. Ask for approval of those rows. If the maintainer rules a difference has no item, stop: it needs a new GAPS4 row, which this section does not add.]]></action>
  <verify><![CDATA[The maintainer approved the rows (or named the ones to change) in chat.]]></verify>
  <done>The maintainer approved the measured scale() differences and their owners.</done>
</task>

<task type="auto" id="33-11-06">
  <name>List the differences; correct help; commit</name>
  <files>test/scale_frame_known.py, dash.sthlp</files>
  <action><![CDATA[Fill SCALE_FRAME_KNOWN in test/scale_frame_known.py with the approved rows, rewrite dash.sthlp:5686-5690 per D-33-11.f (re-read the paragraph first), run test/test_scale_frame.py (release tier), test/test_sizing.py and the test/test_help_claims_*.py files that read the scale() paragraph (grep `scale(#)` in them). Close the GW-11 BUGS entry: `Fixed <ddmonyyyy> (WP-33, GW-11). scripts/extract_scale_frame_truth.do measures twoway's plot region under scale(0.5..2) for two commands (gaps scale, region margins stay); test/test_scale_frame.py compares dash's frame insets in Chrome in both modes, differences listed under <ids>; the help says the gaps scale. Pinned by test/test_scale_frame.py::TestDashAgainstTwoway, test/test_sizing.py::TestScaleFrameTruth, test/test_sizing.py::TestScaleHelp, test/test_wp33_truth.cscript Q3311-1; fixture test/fixtures/scale_frame_truth.json. Closes GAPS4 GW-11 (WP-33, GW-11).`; `- [x]`; Tracked Closed `commit pending`; delete `"GW-11"` from `GAPS4_OPEN` in test/test_tracking_documents.py; CHANGELOG `- The help no longer says scale() leaves the gaps between boxes unscaled; twoway's frame under scale() is measured and compared (WP-33, GW-11)`; no existing function is edited in this commit (new classes, files and help text), so no impact run is needed. Run the Closing steps for GW-11 (Tasks): steps (1) and (3) have nothing to run on at batch 33.3 (no ledger, no guard yet); (2) run `python3 test/known_differences.py GW-11`, delete every row it prints (none expected; nothing moves to a deliberate dict) and run the hygiene command it prints. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .`; commit on wp33-s11 (body adds `Seconds: S11 <n>`).]]></action>
  <verify><![CDATA[`DASH_TEST_TIER=release python3 -m pytest test/test_scale_frame.py -q` and `python3 -m pytest test/test_sizing.py -q` pass; `python3 test/known_differences.py GW-11` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `git log -1 --format=%s` ends `(WP-33 GW-11)`; the claude|anthropic grep prints 0.]]></verify>
  <done>scale()'s frame geometry was compared with twoway's, its differences listed, the help corrected, and GW-11 committed.</done>
</task>

## Section completion criteria

- Two commits on wp33-s11 (TR-23, GW-11); the standing-skip guard and the converted tests green; scale_frame_truth.json committed by its script; test_scale_frame.py (release) and TestScaleFrameTruth (default tier) green with approved known rows; Q3311-1 PASS; help sentence corrected.

## Notes

- **The recorded run.** This section does not run the full suite (CLAUDE.md rule 2). The batch 33.3 gate (k.4) is the first strict run after the conversions; WE.4 of WP-33 records the green run in ROADMAP's WP-33 Measurements line (`pytest <n> passed, 0 skipped` under `DASH_STRICT=1`).
- **Help paragraph owned (R3):** dash.sthlp:5686-5690 (scale()) only; Appendix B HR-19's last sentence ("gaps not scaled") is this section's.
- **Chrome.** RangeProbe starts Chrome at `--window-size=1200,900` (range_probe.py:158, read-only); `_ScaleProbe.viewport(528, 900)` sets the page size by DevTools and reloads (TR-33-11.4); `--disable-gpu` as the other probes; wait for `Bokeh.documents[0]` idle before reading bboxes; read integers (`Math.round`).
- **For the closing sections (WP-43, WP-45; R1-33).** `SCALE_FRAME_KNOWN` (test/scale_frame_known.py; hygiene test `test/test_sizing.py::TestScaleFrameTruth::test_every_known_difference_is_open`, default tier) lists rows keyed GW-6, VF-4 and LT-6; their closing commits follow D-33-10.h (`python3 test/known_differences.py <lead id>`, delete the plain rows -- or move a difference a ruling keeps into `SCALE_FRAME_DELIBERATE` with the ruling id, D-33-10.a -- and run the hygiene command), and 45-04's commit also reruns the release-tier comparison, since its sizing change moves the measured slopes and intercepts.
- **Commit body lines:** `Regression: test/test_strict_mode.py::TestNoStandingSkip::test_none_of_them_can_skip -- failed at <base> with 5 skip sites`; `Flipped: test/test_graph_text.py::TestBounds::test_dup_is_cut -> ::test_dup_past_its_bound_is_drawn_as_typed -- twoway draws {dup 1000:x} as typed`; `Fixture: test/fixtures/scale_frame_truth.json (scripts/extract_scale_frame_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: GW-11 Tracked`.
- **Hand-back:** name `_dash_apply_scale`'s docstring sentence (:27536-27537) for 45-04 (D-33-11.g).
