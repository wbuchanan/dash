# Section 41-03: by(): scale(), per-panel range(varname), zero-weight panels

> Part of: WP-41 (by() fidelity, P6) · Items: BY-2, BY-27, sil:SD-7 · Risk: yellow · Batch: 41.1 · Depends on: none · Blocks: none · Tasks: 7, 3 commits · Case-id prefix: Q4103

## Overview

**What is wrong today.**
- **BY-2 (with BY-29, BY-11).** "A scale() written outside by() scales every panel, where twoway ignores it on a by() graph; by(, scale()), which twoway applies, is named and ignored." Measured by the audit: `scatter mpg weight, scale(1.5) by(foreign)` exports an SVG identical to `by(foreign)` (marker r=14.34 in both); dash draws "panel tick labels 8.5pt to 12.75pt and markers from 3.4 to 5.1", no note. `by(foreign, scale(1.5))` in twoway "draws every text 1.5x larger (tick labels 95.68->143.44, panel labels 105.13->157.78, Graphs-by note 89.94->135.0)"; dash prints "by() sub-option(s) not implemented and ignored: scale(1.5)". Cause: `_dash_scale_factor` (dash_render.py:27487) reads the graph's `scale` with no by() check; `scale` in by() falls to `unsupported.append(tok)` in `_dash_parse_by` (:36404).
- **BY-27.** "function range(varname) under by() spans the whole data in every panel; twoway uses each panel's own range": `(scatter mpg weight) (function y=40-x/200, range(weight)), by(foreign)` -- twoway 1800-4840 (Domestic) and 1760-3420 (Foreign), dash 1760-4840 in both. Cause: `_dash_fold_range` (dash.ado:2401-2431) summarises the variable once over the plot's sample; the per-panel loop (dash.ado:8845-8873) reuses `_fn_lo_<m>`/`_fn_hi_<m>`. kdensity range(varname) has the same cause (twoway__kdensity_gen.ado:100,117 also summarises per panel).
- **sil:SD-7.** "A weighted layer under by() with a panel whose weights are all zero is drawn; twoway stops with r(198)". Measured again for this plan (20oct2026, drawn, not nodraw): `scatter mpg weight [aw=w], by(foreign)` with w = 0 for every foreign car -> rc 198; the same with `by(foreign, total)`, `by(rep78)` (w = 0 when rep78==3), `by(rep78, missing)` and a second unweighted layer -> 198; with `msymbol(none)` -> 0. Cause: dash.ado:6955 skips the check under by() (`& !\`: length local _ss_by'`).

**After this section.** Under by() the outer scale() changes nothing and by(, scale(#)) scales the whole by() graph (panels, panel labels, overall texts, legend and key cells) by #; function and kdensity range(varname) span each panel's own range of the variable (Total: the whole sample); a weighted marker layer with a panel whose weights are all zero or missing is refused r(198) in silence, as twoway refuses it.

**Why together.** Three per-panel rules of the by() graph that are computed outside the panel layout: scale() in the shared size helpers, range() and the weight check in dash.ado's segment code.

**Test order and commit rule.** Per item in the manifest's order (BY-2, BY-27, sil:SD-7): a test task saves the failure text without committing, then a fix task commits `(WP-41 <id>)`. 41-03-01 measures all three items once into one fixture. No full suite inside the section.

### Section decisions

- **D-41-03.a -- by(, scale()) folds into by()'s size multiplier.** `_dash_by_size_mult` returns f(k) x iscale x shrink x s, s = by()'s scale(#); `_dash_by_scale_panel` therefore scales each panel's contents and its label by s, and the panel margin (`_dash_share_by_scales` :47971) takes s too. The overall cells (by()'s title/subtitle/note/caption, the outer axis titles, the legend and colour-key cells) are scaled by s once, in `_dash_layout_cell`'s by() branch, with `_dash_apply_scale`. `_dash_scale_factor` returns None for a graph whose by() names a variable, so the outer scale() is ignored silently there.
- **D-41-03.b -- an unreadable by(, scale())** (a word, a negative number) stays in the "not implemented and ignored" note and draws at 1; twoway's named-style words for it are 49-02's (LT-25 carries BY-8).
- **D-41-03.c -- per-panel range in Stata.** `_dash_fold_range` computes, under by(), each panel's range of the variable over the plot's sample and the panel's rows, in by() panel order (groups of the graph's sample in sort order, Total last), and returns it as `s(range_panels)` "lo hi|lo hi|..." (". ." for a panel with none). The function per-panel loop evaluates panel p over its pair; kdensity carries it as the option `range_panels`, which `_dash_fn_panel_spec` swaps into `options["range"]` per panel. The build's per-panel range is kept after a filter move, as the non-by() range is (folded at build).
- **D-41-03.d -- zero weights per panel.** The check runs per group of the by() variables over the plot's sample (and, as today, only when the markers are drawn and not labelled); any panel with no weight above zero -> `exit 198`, no message. The Total panel needs no own test (it is all-zero only when every group is).
- **D-41-03.e -- `_dash_layout_cell`.** This section edits one block of `_dash_layout_cell`'s by() branch (R12 hot) in batch 41.1; neither 41-01 nor 41-06 edits it (reported to the orchestrator).

## Risk: [yellow] -- every by() graph's sizes and two dash.ado paths change

**Why.** The size multiplier reaches every by() panel; the range and weight rules add Stata code to every by() segment.

**Risk factors.** 1. Folding s into `_dash_by_size_mult` must not double-scale: the panels must no longer receive `_dash_apply_scale` from `_dash_scale_factor` (D-41-03.a). 2. Panel order: Stata's `egen group()` order must equal `_dash_by_groups`' sort order (dash_render.py:5418, "in sort order"); a panel twoway leaves out (`_dash_by_panel_dropped`) shifts later indices, as it does for C12's function points today. 3. The served redraw multiplies weighted marker columns by `_dash_scale_factor(_go)` (:70207): under by() that is now None, as on the saved page.

**Mitigation.** Fixture rows for scale(1.5) outside and inside by(), with and without iscale(1); per-panel serset-equivalent ranges for function and kdensity under by(foreign) and by(rep78, total); zero-weight probes for five by() forms plus msymbol(none).

## Dependencies

- **Depends on:** none (W0 done).
- **Blocks:** none.
- **Parallel batch:** 41.1 with 41-01 (owns `_FILTER_JS` and the served template this batch) and 41-06 (panel label row).
- **Can run with:** both: this section edits no served literal line and no JS.

## Evidence

- `_dash_scale_factor` dash_render.py:27487-27501 (reads `graph_opts["scale"]`, returns None for absent/1/unusable); applied `_dash_apply_scale(fig, _dash_scale_factor(graph_opts))` in `_make_figure_body` :64004, served literal :70701; served `_dash_scale_columns(_out, _dash_scale_factor(_go))` :70207. `_dash_apply_scale(fig, factor)` :27529 (post-pass over `fig.references()`, idempotent through `fig._dash_scaled`).
- `_dash_by_size_mult(by_raw, full_n)` :36704-36732 (f(k), iscale, shrink; callers :47971, :51568, :56567); `_dash_by_scale_panel(fig, m)` :36855 (scales titles, the panel label too; legends and colour bars left alone).
- `_dash_layout_cell` :51524; by() branch :51535-51616; `_dash_by_frame_grid(grid, getattr(figs[0], "_dash_by_chrome", None), cn)` :51609-51610.
- `_DASH_BY_GRAMMAR` row `"scale": ("scale", 1, 1, 0)` :36149; `_dash_parse_by` :36289 (else branch :36403-36404).
- dash.ado `_dash_fold_range` :2401-2431 (args `ptype qual`; `summarize \`name' \`macval(_fr_q)', meanonly`); called :6789-6791; function's range read `mata: st_local("_fn_rnorm", st_global("s(range)"))` :6794; carried by `c_local _seg_fnlo_out` :7206 (reset :8571) into `_fn_lo_<m>`/`_fn_hi_<m>` :8669-8670; per-panel loop :8845-8873 (`_dash_fn_points \`_fx_raw' \`_fn_lo_\`_m'' \`_fn_hi_\`_m'' ... \`=\`_p'-1'` :8871). The graph's by() at segment level: `mata: st_local("_ss_by", st_global("s(g_by)") + st_global("dash__g_by"))` :6862; the graph's qualifier `$dash__gq_if`/`$dash__gq_in` :6372.
- kdensity options list for JSON: dash.ado:5429 (`... sort range range_var colorlist jitterseed ///`); `map_kdensity`'s range_var branch dash_render.py:22655-22661; `_dash_fn_panel_spec(g, idx)` :60165.
- Zero weights: dash.ado:6948-6968 (the `_ss_by` gate :6955, `exit 198` :6966).
- twoway: bygraph_g.class:78,160-161 (scale() only from by()'s own options); twoway__function_gen.ado:101-102 and twoway__kdensity_gen.ado:100,117 (`sum range if touse`); `_draw_weighted_points` per panel.
- Fixtures: sizing_truth.json `scale_15` (non-by() scale); no by() scale, by() range or by() weight fixture.
- Pinned tests: test/test_sizing.py:152-214 (scale() without by(), stays green); test_wp31_truth.cscript:4033-4059 (zero weights without by(), green); `test/test_by_grid.py::TestNamedNoMore` and test/test_note_channel.py name only bgcolor (unchanged here). Any test asserting `scale(1.5)` is named under by(): `grep -rn "scale(1.5)" test/ | grep "by"` before 41-03-02 and flip those in place.

## User stories

- US-41-03.1 As the Stata user with an existing twoway command, I want `scale()` beside `by()` to change nothing and `by(, scale())` to scale the whole graph, so that my by() graph has twoway's sizes.
- US-41-03.2 As the Stata user, I want `function ..., range(x)` and `kdensity ..., range(x)` under by() to span each panel's own x, as twoway draws them.
- US-41-03.3 As the Stata user, I want a weighted scatter whose panel has only zero weights refused as twoway refuses it, so that the same do-file fails in both.

## Business requirements

- BR-41-03.1 Outer scale() on a by() graph draws the same sizes as without it, with no note.
- BR-41-03.2 by(, scale(#)) multiplies every text, marker and line size of the by() graph by #, overall texts and keys included; with iscale(1) as well.
- BR-41-03.3 Under by(), function and kdensity range(varname) span each panel's minimum to maximum of the variable; the Total panel spans the whole sample.
- BR-41-03.4 Under by(), a weighted marker layer with drawn, unlabelled markers and a panel with no weight above zero is refused r(198) with no message.

## Technical requirements

- TR-41-03.1 `def _dash_by_scale_mult(by_raw)` after `_dash_by_shrink_factor` (:36745): the by() sub-option row `scale` (through `_dash_by_tokens` and `_dash_by_word`, the last copy), its argument read with the number regex of `_dash_by_size_mult` (:36722); returns the value when finite and above 0, else 1.0; never raises.
- TR-41-03.2 `_dash_by_size_mult`: after `f *= _dash_by_shrink_factor(by_raw)` (:36731) add `f *= _dash_by_scale_mult(by_raw)`.
- TR-41-03.3 `_dash_scale_factor(graph_opts)`: first line of the body, `if _dash_parse_by(str((graph_opts or {}).get("by", "") or ""), warn=False)[0]: return None`.
- TR-41-03.4 `_dash_layout_cell`: directly after the `_dash_by_frame_grid(...)` call (:51609-51610) add
  ```python
  _bys = _dash_by_scale_mult((gopts_of(name) or {}).get("by"))
  if _bys != 1.0:
      _panel_ids = {id(f) for f in figs}
      for _ch in list(grid.children):
          if id(_ch[0]) not in _panel_ids:
              _dash_apply_scale(_ch[0], _bys)
  ```
- TR-41-03.5 `_dash_parse_by`: a `scale(...)` token whose `_dash_by_scale_mult` reads a value (the argument parses as a positive number) passes silently (a new `elif` before the final `else`); otherwise it stays in `unsupported`.
- TR-41-03.6 Copy list (R2): `"_dash_by_scale_mult",` after `"_dash_by_positions", "_dash_by_size_mult",` (:67456). function_test_map.py row.
- TR-41-03.7 dash.ado `_dash_fold_range`: after the whole-sample `summarize` (:2412), when `` mata: st_local("_fr_by", st_global("s(g_by)") + st_global("dash__g_by")) `` holds a varlist before its comma: parse the by() variables (`gettoken` up to ","), `missing` (`mis` to `missing` in the sub-options, the regex of `_dash_fn_panel_count`, dash_parse.mata:12258) and `total` (`tot`..`total`); `tempvar _fr_t _fr_g`; `generate byte \`_fr_t' = 0`; `replace \`_fr_t' = 1` under the graph qualifier (`$dash__gq_if`, `$dash__gq_in`, as :6372-6380 build it); without `missing`, `replace \`_fr_t' = 0 if missing(<each by var>)` (`== ""` for a string); `egen long \`_fr_g' = group(<by vars>) if \`_fr_t', missing`; for `p = 1/r(max)` of `_fr_g`: `summarize \`name' \`macval(_fr_q)' & \`_fr_g' == p` -- written as a tempvar mark `\`_fr_m' = 1 \`macval(_fr_q)'` then `summarize \`name' if \`_fr_m' & \`_fr_g' == \`p', meanonly` -- appending `"lo hi|"` (`%21.0g`, as :2426-2427) or `". .|"` when r(N)==0; with `total`, one more pair over `\`_fr_m' & \`_fr_t'`. `sreturn local range_panels` holds the string (trailing `|` dropped). Without by(): `sreturn local range_panels ""`.
- TR-41-03.8 dash.ado: add `range_panels` after `range_var` in the option-name list (:5429). Function: after :6794 `mata: st_local("_fn_rpan", st_global("s(range_panels)"))`; `c_local _seg_fnrp_out \`_fn_rpan'` beside :7206; `local _seg_fnrp_out ""` beside :8571; `local _fn_rp_\`_fn_m' : copy local _seg_fnrp_out` after :8670; in the per-panel loop (:8869-8872), when `_fn_rp_<m>` is non-empty, `mata: st_local("_fp_lohi", _dash_range_panel(st_local("_fn_rp_\`_m'"), \`_p'))` and pass its two words in place of `_fn_lo_<m>`/`_fn_hi_<m>`. A pair ". ." (the panel holds no value of the variable) skips the `_dash_fn_points` call for that panel, so its key is absent from `{"panels": ...}` and `_dash_fn_panel_spec` gives the layer `points = None`, which draws it empty in that panel (its docstring, :60172-60174).
- TR-41-03.9 New Mata function after `_dash_fn_panel_count` (dash_parse.mata:12247): `string scalar _dash_range_panel(string scalar rp, real scalar p)` -> the p-th (1-based) `|`-separated pair, trimmed, or "" when p is out of range. Header index line (dash_parse.mata:341 area), `_dash_require_mata`'s `_needed` list, test/program_coverage_map.py row (R6).
- TR-41-03.10 Python `_dash_fn_panel_spec(g, idx)` (:60165): also treat a plot whose `options["range_panels"]` is a non-empty string: split on `|`, take element `idx` (0-based); two finite numbers -> `options["range"] = "lo hi"`; ". ." -> `options["range"] = ""` (map_kdensity then draws the empty curve, :22655); out of range -> unchanged. The copy discipline is the function branch's; docstring names both.
- TR-41-03.11 dash.ado zero weights (:6955): drop `& !\`: length local _ss_by'` and, inside, when `_ss_by` holds a varlist: build the group as TR-41-03.7 does (graph qualifier, `missing`), restricted to the plot's sample (`_ps_if`, `_ps_in`); `tempvar _wm_g _wm_p`; `egen long \`_wm_g' = group(<by vars>) if <sample>, missing`; `egen byte \`_wm_p' = max(!missing(\`_seg_wexp') & (\`_seg_wexp') > 0), by(\`_wm_g')`; `quietly count if !missing(\`_wm_g') & \`_wm_p' == 0`; `if r(N) > 0 exit 198`. Without by() the existing count stays.
- TR-41-03.12 Help (R3): dash.sthlp by() sizing paragraph (:3264-3270) gains, inside :3264-3270 and with no reflow past :3271 (41-06 edits :3278-3287 in the same batch, eight lines below; REVIEW R3-38), "{cmd:by(, scale(}{it:#}{cmd:))} multiplies every size of the by() graph, its overall text and keys too, as {cmd:twoway} does; a {cmd:scale()} outside {cmd:by()} changes nothing on a by() graph, as in {cmd:twoway}."; the scale() paragraph (:5686-5691) gains "On a {cmd:by()} graph only {cmd:by(, scale())} acts."; the function/kdensity range(varname) sentence (grep `range(}{it:varname}` in dash.sthlp) gains "under {cmd:by()}, each panel's own"; the weights paragraph (:4192-4197) gains "under {cmd:by()} the rule is applied to each panel, as {cmd:twoway} applies it". Remove `scale()` from any by() "named" list if it is there.

## Boundaries

- Do not edit `_make_figure_body`, `_generate_app_source_body` (41-01 owns it this batch), `_FILTER_JS`, `_dash_by_panel_label` (41-06), `_dash_by_chrome` (41-02), `_dash_by_keys` (41-04).
- BY-8's note words for unreadable by() values are 49-02's.
- No change to scale() without by() (sizing_truth scale_15 stays green).

## Stata truth

New `scripts/extract_by_scale_range_truth.do` -> `test/fixtures/by_scale_range_truth.json` (skeleton of scripts/extract_by_text_truth.do :1-90; `set scheme stcolor` for the session; `_meta` complete). Probes (each `capture noisily twoway ...`, rc, and when rc 0 `graph export` to SVG read with scripts/svg_truth.py: every text's font size and string, the first marker circle's r, the panel plot-region rects):

| id | command | records |
|---|---|---|
| S01 | `scatter mpg weight, by(foreign)` | sizes |
| S02 | `scatter mpg weight, scale(1.5) by(foreign)` | sizes (expect = S01) |
| S03 | `scatter mpg weight, by(foreign, scale(1.5))` | sizes |
| S04 | `scatter mpg weight, by(foreign, scale(1.5) iscale(1))` | sizes |
| S05 | `(scatter mpg weight) (lfit mpg weight), legend(on) by(foreign, scale(1.5) title("T"))` | sizes incl. legend and title |
| R01 | `(scatter mpg weight) (function y=40-x/200, range(weight)), by(foreign)` | per panel: `summarize weight if foreign==k` min/max, and the function path's x extent in data units |
| R02 | R01 with `by(rep78, total)` | the same, Total = all rows with rep78 non-missing |
| R03 | `(scatter mpg weight) (kdensity weight, range(weight)), by(foreign)` | the same for the density curve |
| W01-W05 | the five zero-weight commands of the Overview, drawn | rc |
| W06 | `scatter mpg weight [aw=w], by(foreign) msymbol(none)` | rc (0) |

`git add -f` the fixture; add it to test/test_fixtures_are_committed.py.

## TDD test stubs

New `test/test_by_scale_range_weights.py` (`_MODES = ("saved", "served")`; build helpers of test/test_by_grid.py):
- BY-2: `TestByScale::test_outer_scale_changes_nothing[mode]` (panel tick label and marker sizes equal S01's ratio to S02's = 1; red), `::test_by_scale_scales_everything[mode]` (tick labels, panel label, by() title and note, legend label = 1.5 x the no-scale build, within 0.01; red), `::test_by_scale_with_iscale1[mode]` (red), `::test_no_note_for_a_number` (red), `::test_a_word_is_still_named` (guard), `::test_scale_mult` unit test of `_dash_by_scale_mult` (red).
- BY-27: `TestPerPanelRange::test_function_spans_each_panel[mode-R01|R02]` (each panel's function x min/max = fixture's summarize pair within 1e-9; red), `::test_kdensity_spans_each_panel[mode]` (R03; red), `::test_range_panel_mata` (Mata `_dash_range_panel` through a Stata cert case, see below), `::test_panel_spec_swaps_the_range` (unit, red).
- sil:SD-7: covered by cscript cases (Stata-side refusal).

cscript cases (test/test_wp41_truth.cscript, blocks `* ==== S03 BY-2: by() scale() ====` and `* ==== S03 BY-27: per-panel range(varname) ====`; sil:SD-7 is a refusal, so its cases go in test/test_option_validation.cscript and it adds no truth block, BRIEF R1):
- Q4103-1 `dash clear`; `dash scatter mpg weight, by(foreign, scale(1.5)) name(q1)` rc 0; then -- the "by() sub-option(s) not implemented and ignored: scale(1.5)" note is printed by Python at build (dash_render.py:36409), which registration never runs -- `quietly log using "<tmp>/q1.log", text replace name(_q4103)`, `capture noisily dash build, saving("<tmp>/q1.html", replace) nobrowser` rc 0, `quietly log close _q4103`, and `cert_log_has "<tmp>/q1.log", needle("not implemented and ignored")` (test/cert_helpers.do:182) with `r(found) == 0`. Red at base: the build names scale(1.5).
- Q4103-2 R01 under dash: rc 0; the spec's function points per panel span `summarize weight if foreign==k` (read from the registered JSON with Mata).
- Q4103-3 `mata: _dash_range_panel("1 2|3 4|. .", 2)` = "3 4"; p=3 = ". ."; p=4 = "".
- Q4103-4..8 (test/test_option_validation.cscript, the weights area) W01-W05: `capture dash <cmd>` rc 198 and twoway's measured rc 198 with no message; Q4103-9 W06 rc 0.

Pinned tests to flip: whichever the grep in Evidence finds naming by(, scale()) as not implemented.

Parity (R8): `_case("by() scale(1.5)", [plot_for("scatter", {})], go={"by": "foreign, scale(1.5)"})` and `_case("by() function range(var)", [plot_for("scatter", {}), plot_for("function", {...})], go={"by": "foreign"})` (copy an existing function entry's points form).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| outer scale ignored, by(scale) applied | pytest TestByScale; Q4103-1 | S01-S05 | yes |
| per-panel range | pytest TestPerPanelRange; Q4103-2/3 | R01-R03 | yes |
| zero-weight panels | Q4103-4..9 | W01-W06 | n/a (Stata) |
| parity | test_mode_parity CORPUS | -- | yes |

- AC-41-03.1 Every red stub was red at its base and is green after; failure texts saved per item.
- AC-41-03.2 Q4103-1..9 PASS, no SKIP.
- AC-41-03.3 test_sizing.py, test_by_grid.py, test_function_panels.py, test_weighted_markers.py green.
- AC-41-03.4 GAPS4 BY-2, BY-27, sil:SD-7 Tracked lines in the Closed form.

## Tasks

**Commit boundary.** 41-03-01..03 form BY-2's commit `Ignore scale() beside by() and draw by(, scale()) over the whole graph (WP-41 BY-2)`; 41-03-04..05 BY-27's `Span function and kdensity range(varname) per by() panel (WP-41 BY-27)`; 41-03-06..07 sil:SD-7's `Refuse a by() panel whose weights are all zero, as twoway does (WP-41 sil:SD-7)`. Branch `wp41-s03`; `$WT` is the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp41-s03` (BRIEF "Pull form": commands use this absolute path). Before each commit: run `git pull --ff-only . main` in $WT (CLAUDE.md rule 4; BRIEF "Pull form": `Already up to date.` when the batch base already contains main; if it refuses, stop and report to the orchestrator, never a merge commit on a section branch), run `gitnexus detect-changes --scope all --repo .` in $WT (the global CLI; `.gitnexus/` is git-ignored and absent from a worktree; re-run when it reports `partial` or `truncated`) and `python3 -m pytest test/test_cscript_hygiene.py -k "TestTheWpTruthScripts and wp41" -q -n0`.

<task type="auto" id="41-03-01">
  <name>Measure twoway for all three items</name>
  <files>scripts/extract_by_scale_range_truth.do, test/fixtures/by_scale_range_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_by_scale_range_truth.do with the probes of "Stata truth" (drawn graphs: no nodraw, `set graphics off`; R01-R03's per-panel pairs from `summarize ... if <group>` and the SVG path extents), run it through `scripts/stata_slot.sh`, `git add -f` the fixture and name it in test/test_fixtures_are_committed.py's list (41-01 and 41-06 append to the same list in 41.1: the merger needs that file in picks.sh's `addmerge.py ours-first` list -- name it in the hand-back). Record in `<scratch>/41-03-measured.txt` the S02/S01 size ratio, the S03/S01 ratios and the W rc list. Do not commit.]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/by_scale_range_truth.json'))['probes'];print([p[k]['rc'] for k in ('W01','W02','W03','W04','W05','W06')], p['R01']['panels'])"` prints `[198, 198, 198, 198, 198, 0]` and two pairs equal to 1800/4840 and 1760/3420; `test -s <scratch>/41-03-measured.txt`.]]></verify>
  <done>twoway's by() scale, per-panel range and zero-weight answers were recorded in a stamped fixture.</done>
</task>

<task type="auto" id="41-03-02">
  <name>Write the failing scale tests</name>
  <files>test/test_by_scale_range_weights.py, test/test_wp41_truth.cscript</files>
  <action><![CDATA[Create test/test_by_scale_range_weights.py with the TestByScale stubs reading the fixture's S rows. Append the S03 BY-2 block with Q4103-1 directly above the first `* ==== S` header numbered above 03, else above the append marker (the head computes the run list from the headers; never edit the head). Run `python3 -m pytest test/test_by_scale_range_weights.py::TestByScale -q -n0 -rf > <scratch>/41-03-02-failure.txt 2>&1; true` and the block (`WP41_ONLY=S03`), appending its FAIL line. Run the grep of Evidence and list the pins to flip in `<scratch>/41-03-flips.txt`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/41-03-02-failure.txt` is at least 4; the file holds `Q4103-1 FAIL`.]]></verify>
  <done>BY-2's regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="41-03-03">
  <name>Fix scale under by() and commit</name>
  <files>dash_render.py, dash.sthlp, test/function_test_map.py</files>
  <action><![CDATA[Run `gitnexus impact _dash_scale_factor --direction upstream --repo dash`, the same for `_dash_by_size_mult`, `_dash_parse_by` and `_dash_layout_cell`; report HIGH or CRITICAL (an UNKNOWN result is confirmed with `grep -n`). Apply TR-41-03.1 to TR-41-03.6 and the scale sentences of TR-41-03.12. Flip the pins in `<scratch>/41-03-flips.txt` in place with the reason. Append the parity entry to test/test_mode_parity.py's `CORPUS` (R8). Run `python3 -m pytest test/test_mode_parity.py -k "scale or by" -q -n0` on its own (a `-k` applies to every file on its command line), then, with no `-k`, `python3 -m pytest test/test_by_scale_range_weights.py::TestByScale test/test_sizing.py test/test_by_grid.py test/test_by_scales.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py -q -n0` (the copy-list entry and the function_test_map row of `_dash_by_scale_mult`, TR-41-03.6), and the S03 block. Close BY-2's BUGS entry (PD-4), its Tracked line, its GAPS4_OPEN line, and add the CHANGELOG line under `### Fixed in WP-41`: "scale() beside by() no longer scales the panels and by(, scale()) scales the whole graph, as twoway does; scatter mpg weight, scale(1.5) by(foreign) drew 12.75pt tick labels, now 8.5pt (WP-41, BY-2)". The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h), before the commit: (1) run `awk -F'\t' '$1 == "BY-2" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the plain rows; a `BY-2 (documented)` or `BY-2 (residual)` row stays, A-10) and `git add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py BY-2` and delete every `<file>:<line>` row it prints from its `*_KNOWN` table (staging each file it edits) -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion 33-10 names (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`; `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN`, e.g. `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `ABBREV_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (D-33-10.a; no ruling of this section keeps one, so none is expected; an unreadable by(, scale()) still differs, D-41-03.b, but that difference is LT-25's (49-02, via BY-8): a row for it keyed `LT-25` is not printed here, and one keyed `BY-2` is re-keyed to `LT-25`, not deleted) -- then rerun, with no `-k`, each test file whose table it edited (its comparison reads the table, so a deleted row whose difference remains fails there) and run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); both pass; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the driver) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`, D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes) and add its `Fixture:` line to the commit body. Then the Commit boundary's pre-commit checks: `git pull --ff-only . main` in $WT (BRIEF "Pull form"; `Already up to date.` at the batch base; a refusal stops the task and is reported), `gitnexus detect-changes --scope all --repo .` and, when a cscript changed, the hygiene test the Commit boundary names. Commit per BRIEF; grep the message.]]></action>
  <verify><![CDATA[Both pytest runs report 0 failed; `Q4103-1 PASS`; `awk -F'\t' '$1 == "BY-2"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py BY-2` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s` ends `(WP-41 BY-2)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>scale() follows twoway's by() rule in both modes, no ledger or known-differences row names BY-2 alone, and BY-2 is closed in one commit.</done>
</task>

<task type="auto" id="41-03-04">
  <name>Write the failing range tests</name>
  <files>test/test_by_scale_range_weights.py, test/test_wp41_truth.cscript</files>
  <action><![CDATA[Add the TestPerPanelRange stubs (function R01/R02, kdensity R03, the panel-spec unit test) and the S03 BY-27 block with Q4103-2 and Q4103-3. Run `python3 -m pytest test/test_by_scale_range_weights.py::TestPerPanelRange -q -n0 -rf > <scratch>/41-03-04-failure.txt 2>&1; true` and the block, appending its FAIL lines. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/41-03-04-failure.txt` is at least 4; the file holds `Q4103-2 FAIL` and `Q4103-3 FAIL` (the Mata function is missing).]]></verify>
  <done>BY-27's regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="41-03-05">
  <name>Fold the range per panel and commit</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[Run `gitnexus impact _dash_fold_range --direction upstream --repo dash` and the same for `_dash_fn_panel_spec`, `_dash_plot` and `_dash_process_segment` (TR-41-03.8 edits it after :6794 and beside :7206); report HIGH or CRITICAL (UNKNOWN confirmed with `grep -n`). Apply TR-41-03.7 to TR-41-03.10 and the range sentence of TR-41-03.12 in dash.sthlp (R6: Mata header index, `_needed`, program_coverage_map.py). Run `python3 -m pytest test/test_by_scale_range_weights.py::TestPerPanelRange test/test_function_panels.py test/test_computed_layer_rows.py test/test_distribution_odds.py test/test_program_coverage_map.py -q -n0`, the S03 block, and test/test_parser.cscript once (its function and kdensity range cases). Append the parity entry to test/test_mode_parity.py's `CORPUS` (R8). Close BY-27 (BUGS, Tracked, GAPS4_OPEN, CHANGELOG "function and kdensity range(varname) under by() span each panel's own range, as twoway does; Domestic and Foreign both drew 1760-4840, now 1800-4840 and 1760-3420 (WP-41, BY-27)"). The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h), before the commit: (1) run `awk -F'\t' '$1 == "BY-27" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the plain rows; a `BY-27 (documented)` or `BY-27 (residual)` row stays, A-10) and `git add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py BY-27` and delete every `<file>:<line>` row it prints from its `*_KNOWN` table (staging each file it edits) -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion 33-10 names (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`; `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN`, e.g. `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `ABBREV_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (D-33-10.a; no ruling of this section keeps one, so none is expected: each panel spans its own range, as twoway's does (D-41-03.c)) -- then rerun, with no `-k`, each test file whose table it edited (its comparison reads the table, so a deleted row whose difference remains fails there) and run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); both pass; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the driver) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`, D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes) and add its `Fixture:` line to the commit body. Then the Commit boundary's pre-commit checks: `git pull --ff-only . main` in $WT (BRIEF "Pull form"; `Already up to date.` at the batch base; a refusal stops the task and is reported), `gitnexus detect-changes --scope all --repo .` and, when a cscript changed, the hygiene test the Commit boundary names. Commit.]]></action>
  <verify><![CDATA[pytest 0 failed; `Q4103-2 PASS`, `Q4103-3 PASS`; test_parser.cscript's success line; `awk -F'\t' '$1 == "BY-27"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py BY-27` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s` ends `(WP-41 BY-27)`.]]></verify>
  <done>Each by() panel's function and kdensity range(varname) spans its own rows in both modes, no ledger or known-differences row names BY-27 alone, and BY-27 is closed.</done>
</task>

<task type="auto" id="41-03-06">
  <name>Write the failing weight cases</name>
  <files>test/test_option_validation.cscript</files>
  <action><![CDATA[Add cases Q4103-4..9 to test/test_option_validation.cscript after the last weighted-marker case (grep `aw=` there; re-read), each comparing `capture dash <cmd> name(qN)` with the fixture's W rc. Run the script once through BRIEF's two-line driver (`<scratch>/run_test_option_validation.do`, log `<scratch>/run_test_option_validation.log`); copy its FAIL lines (Q4103-4..8 FAIL: dash rc 0) to `<scratch>/41-03-06-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "Q4103-[4-8] FAIL" <scratch>/run_test_option_validation.log` prints 5 and `grep -c "Q4103-9 PASS" <scratch>/run_test_option_validation.log` prints 1; `test -s <scratch>/41-03-06-failure.txt`.]]></verify>
  <done>The zero-weight panel cases were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="41-03-07">
  <name>Check weights per panel and commit</name>
  <files>dash.ado, dash.sthlp</files>
  <action><![CDATA[Run `gitnexus impact _dash_process_segment --direction upstream --repo dash`; report HIGH or CRITICAL (UNKNOWN confirmed with `grep -n`). Apply TR-41-03.11 and the weights sentence of TR-41-03.12; delete the comment line "Under by() twoway answers panel by panel; that is not judged here." (dash.ado:6954) and write instead "Under by() it is judged per panel (WP-41 sil:SD-7)". Run test/test_option_validation.cscript and test/test_wp31_truth.cscript's weighted-marker cases (`WP31_ONLY` of their block; re-read its id) once each, and `python3 -m pytest test/test_weighted_markers.py -q -n0`. Close sil:SD-7 (BUGS, Tracked, GAPS4_OPEN; CHANGELOG under `### Changed behaviour (may need your do-files changed)`: "a weighted marker layer under by() with a panel whose weights are all zero is refused r(198), as twoway refuses it; it was drawn (WP-41, sil:SD-7)"). The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h), before the commit: (1) run `awk -F'\t' '$1 == "sil:SD-7" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the plain rows; a `sil:SD-7 (documented)` or `sil:SD-7 (residual)` row stays, A-10) and `git add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py sil:SD-7` and delete every `<file>:<line>` row it prints from its `*_KNOWN` table (staging each file it edits) -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion 33-10 names (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`; `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN`, e.g. `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `ABBREV_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (D-33-10.a; no ruling of this section keeps one, so none is expected: the panel is refused as twoway refuses it (D-41-03.d)) -- then rerun, with no `-k`, each test file whose table it edited (its comparison reads the table, so a deleted row whose difference remains fails there) and run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); both pass; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the driver) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`, D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes) and add its `Fixture:` line to the commit body. Then the Commit boundary's pre-commit checks: `git pull --ff-only . main` in $WT (BRIEF "Pull form"; `Already up to date.` at the batch base; a refusal stops the task and is reported), `gitnexus detect-changes --scope all --repo .` and, when a cscript changed, the hygiene test the Commit boundary names. Commit.]]></action>
  <verify><![CDATA[Both cscripts print their success line; `grep -c "Q4103-[4-9] PASS" <scratch>/run_test_option_validation.log` prints 6; pytest 0 failed; `awk -F'\t' '$1 == "sil:SD-7"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py sil:SD-7` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s` ends `(WP-41 sil:SD-7)`.]]></verify>
  <done>A zero-weight by() panel is refused as twoway refuses it, no ledger or known-differences row names sil:SD-7 alone, and sil:SD-7 is closed.</done>
</task>

## Section completion criteria

- Three commits, each with its failing tests first, fixture lines and tracking edits; Q4103-1..9 PASS; no test deleted.
- `_dash_by_scale_mult` on the served copy tuple; `_dash_range_panel` in the Mata header, `_needed` and program_coverage_map.py.
- No plain `BY-2`, `BY-27` or `sil:SD-7` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table; corpus_ledger.json is regenerated by `scripts/corpus/ledger.py`; the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script if Q3309-1 reported any change for a guard example (an improved verdict or a changed field).

## Notes

- **Help paragraphs owned (R3):** dash.sthlp :3264-3270 (by() sizing), :5686-5691 (scale()), the range(varname) sentence, :4192-4197 (weights). The scale() "gaps are not scaled" sentence is 33-11's (GW-11).
- **Merge rules:** R1, R2, R3, R5, R6, R7, R8, R9, R12 (`_dash_layout_cell` this batch).
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** Each closing task (41-03-03 for BY-2, 41-03-05 for BY-27, 41-03-07 for sil:SD-7) deletes its item's plain rows of scripts/corpus/ledger.tsv, regenerates corpus_ledger.json (D-33-05.i), deletes every row `python3 test/known_differences.py <id>` prints and runs the hygiene command it prints (D-33-10.h) and regenerates corpus_guard_truth.json if Q3309-1 reports any change for a guard example (33-09, D-33-09.c), before its own commit.
- **Functions edited** (for the manifest's Owns cell): `_dash_scale_factor`, `_dash_by_size_mult`, `_dash_parse_by`, `_dash_layout_cell` (R12, one block of its by() branch), `_dash_fn_panel_spec`, dash.ado `_dash_fold_range`, `_dash_plot`'s per-panel loop, `_dash_process_segment`'s zero-weight gate (:6948-6968, not the per-type check block R12 names), new `_dash_by_scale_mult` and Mata `_dash_range_panel`.
- **Task count.** Three items in seven tasks: one measuring task, then two per item (BRIEF "Task counts").
- **Trap:** `_dash_apply_scale` is idempotent per model (`_dash_scaled`); a chrome cell scaled by TR-41-03.4 must not be scaled again by a later layout of the same graph -- the stamp already prevents it.
- **Trap:** dash's own zero-weight check runs whether or not the graph is drawn (DT-28 ruled that nodraw needs no change); twoway accepts under nodraw. Do not add a nodraw branch.
- **Trap:** egen group() order must match `_dash_by_groups`; for a string by() variable both are byte order; confirm on `by(make)` in the R probes if the executor adds one.
- **Commit-body lines:** `Regression: test/test_by_scale_range_weights.py::TestByScale::test_outer_scale_changes_nothing -- failed at <base> with <text>` (and the per-item equivalents); `Fixture: test/fixtures/by_scale_range_truth.json (scripts/extract_by_scale_range_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: <id> Tracked`.
