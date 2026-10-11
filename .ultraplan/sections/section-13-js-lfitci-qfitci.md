# Section 13: lfitci and qfitci refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1b · Risk: yellow · Batch: 5 · Depends on: 10 · Blocks: 28 · Tasks: 3, 1 commit · Case-id prefix: U13

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): the saved page shows a stale cue for `lfitci` and `qfitci` after a filter move; the served app refits the line and its band. At `6370ca4` `map_lfitci` (dash_render.py:16421-16526) and `map_qfitci` (:16550-16654) build one `ColumnDataSource({"x_fit", "y_fit", "y_lower", "y_upper"})`, draw the band through `_render_ci_band` (:12473) and the line from the same source, and tag nothing; `_dash_stale_kind` returns `"fit"` for both. On `dash scatter mpg weight || lfitci mpg weight, filter(foreign, type(dropdown))` moved to Foreign, the band stays the 74-car band, dimmed, keyed "mpg (unfiltered)".

**After this section** both layers refit on the saved page: `regress y x [w]` on the kept rows (`dash_wls` from S10 on the centred design, or `_qfit_design`'s), `predict` with `stdp` (default), `stdf` or `stdr` (`dash_fitci_se`), the t quantile at `level()` with `df = N - rank` (`dash_t_ppf`), and twoway's rules at the edges: fewer than two rows draw nothing; two rows (lfitci) or three (qfitci) draw the line with a missing band (df 0); an aweight or pweight with `stdf`/`stdr` draws the line and no band (`_fitci_std_for` returns `"none"`). The stale cue stops marking the two types. The config schema is S10's with `level` and `std`.

**Why these rows share this section.** lfitci and qfitci are the two band layers that need only S10's solver and t quantile; they prove `dash_fitci_se` and the band write path (`dash_fit_write` with `more`) that S28 (fpfitci) reuses.

**Test order and commit rule.** One cycle, one commit `(WP-31 F1b)`: 13-01 writes the failing tests (never commits); 13-02 tags the mappers, adds the two JS branches, moves the two types into `_DASH_JS_REFIT_TYPES`; 13-03 flips, certifies, documents and commits.

### Section decisions (binding on the executor)

- **D-13.a. The band's missing values are dropped rows, not NaN cells.** Python writes `y_lower = y_fit - nan*se` as NaN columns of full length, and Bokeh skips NaN in a VArea/Patch. `dash_fit_write` (S10, D-10.e) drops a row when any column is non-finite -- which would drop the LINE too when the band is missing. So the ci branches write the source directly: line rows always, band columns `NaN` where undefined, through a local `dash_ci_write(src, ac, xs, ys, lo, hi)` (added here before `// DASH_FIT_HELPERS_END`) that places each column on its axis and keeps a row when x and y are finite, writing `NaN` into `y_lower`/`y_upper` where they are not. The saved page's JSON snapshot holds NaN as null; BokehJS reads a `NaN` written by a callback as a gap in the band, as the build's NaN columns are.
- **D-13.b. The weighted-std refusal is decided at build.** `std` in the config is `_fitci_std_for(options, wtype, layer)`'s answer (`"stdp"|"stdf"|"stdr"|"none"`), so the JS never re-derives twoway's refusal; a move does not change the weight type.
- **D-13.c. The near-singular rank cut (S10 D-10.c residual).** `_dash_wls` drops a nearly collinear column by lstsq's cutoff on the raw design (df N-2 on 5-minute `%tc` data). `dash_wls` has no such cut: on such data the JS keeps the column and the band differs. The parity corpus names the case (`qfitci on a 5-minute %tc x`) with tolerance 1e-6 on the LINE and the band compared only where Python's df equals the JS's; the residual is filed under M12 if it fails (BUGS.md open entry "qfitci band on a nearly collinear design differs between the saved page and the served app"), never silently widened.

## Risk: [yellow] -- the first band port, written against the tree S11 leaves

**Why.** S11 (fit-options, C4) edits `map_lfit`..`map_fpfitci`'s option reading in batch 4; S13 runs in batch 5 (DECISIONS A22 swapped S13 and S16 so no two sections of one batch edit `map_lfitci`/`map_qfitci`), so S13's tagging lines are written against S11's final text of the two mappers, including the `points` early return (S11 TR-11.6 b: a `points` layer returns before any tagging and carries no `_dash_agg_*` attribute).

**Risk factors.** (1) S11's `points` return in `map_lfitci`/`map_qfitci` must stay above S13's tagging block. (2) The band's NaN semantics (D-13.a). (3) `level()` outside (0,100) or `df` 0.

**Mitigation.** (1) S13's edit to each mapper is ONE contiguous block of three attribute assignments before the final `return [line_r, band_r]` and one `_std`/`_lvl` capture that reuses the locals the mapper already has (`std`, `_lvl`, `fit`); S11's edits (batch 4, landed) sit at the option-reading top and in the `points` early return, which S13 does not touch -- `TestTheConfig::test_a_points_layer_is_not_tagged` guards it. (2) `TestCiBranch::test_two_rows_draw_the_line_and_no_band`. (3) `level` travels as the float `_resolve_level` returned (already bounded); `df < 1` gives `t = NaN` and a missing band, as Python.

## Dependencies

- **Depends on: 10** (prelude, `dash_fit_rows`, `dash_fit_grid`, `dash_wls`, `dash_fitci_se`, `dash_t_ppf`, `dash_qfit_design`, `run_fit_js_block`, `_DASH_JS_REFIT_TYPES`, `GlyphMapper._fit_agg_config`).
- **Blocks: 28** (fpfitci reuses `dash_ci_write` and the band rule).
- **Parallel batch: 5** with S14 (`_dash_connect_opt`/`_dash_recast_opt`, `map_area`/`map_rarea`/`_dash_join_glyph` callers) and S15 (`_apply_colorvar`/`_dash_fold_typed` on non-fit mappers). Merge order 13, 14, 15. **Can run with S14 and S15**: neither edits `map_lfitci`/`map_qfitci`, `_FILTER_JS` or the stale-cue files. S13 is batch 5's `_FILTER_JS`/`js_runner.py`/`_dash_stale_kind`/`test_saved_stale_cue.py` editor (A2). S16 (lowess) took batch 4 (A22); S13 is written against the tree batch 4 leaves: S11's mapper text, S16's `lowess` in `_DASH_JS_REFIT_TYPES`, `_FROZEN` and the help table line.

## Evidence

- `map_lfitci` :16421-16526: `x_fit = _fit_grid(x, options, "lfitci")`; `X = [1, x - mean(x)]`; `fit = _dash_wls(X, y, w, wtype)`; `std = self._fitci_std_for(options, wtype, "lfitci")`; `se_band = _dash_fitci_se(Xg, fit, std)`; `_lvl = _resolve_level(options, self.default_level)`; `t_crit = _t_ppf(0.5 + _lvl/200, df=fit["df"]) if fit["df"] >= 1 else nan`; `y_lower/upper = y_fit -/+ t_crit*se_band`; `_on_axis` x, y, lower, upper; source columns `x_fit, y_fit, y_lower, y_upper`; `_render_ci_band` returns `(line_r, band_r)`. Empty layer (`n < 2`): `empty_ci_src` with the four columns, `_mark_unfit`.
- `map_qfitci` :16550-16654: the same with `_qfit_design(x, x_fit)`; the `LinAlgError` fallback is a bootstrap (unreachable when `_dash_wls` drops collinear columns; GAPS3 F5 notes the stale docstring); `n()` is read as given (qfitci `n(3)` plots 3).
- `_fitci_std_for` :16528-16548: `"none"` for stdf/stdr with aw/pw. `_dash_fitci_std` :22342, `_dash_fitci_se` :22352-22383.
- `_render_ci_band` :12473-12540: the band from `source` (or `band_source`), the line from `source`; `band_r._dash_ci_outline` is the outline renderer drawn from the SAME source.
- `_resolve_level` :21069; `_DEFAULT_LEVEL` 95.
- Fixture `test/fixtures/stat_truth.json`: `ci_bands` (lfitci/qfitci sersets on auto at level 95), `fitci_std` (stdp/stdf/stdr values at x=1760: .76500711, 3.522953, 3.3527192), `weighted_fit_check`.
- Pins to flip: `test_saved_stale_cue.py::_FROZEN` holds `"lfitci"`, `"qfitci"` (after S10 and S16: ten entries); `TestTheCueAppearsOnAMove::test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked` (:226) uses lfitci -- it must be re-pointed to `fpfitci` (still frozen until S28) with a `Flipped:` line; `test_mode_parity.py::_MOVED_LAYERS` comment.

## User stories

- **US-13.1** As a dashboard reader with the saved file, I want the confidence band to follow the filter so that the band's width reflects the rows I kept.
- **US-13.2** As a Stata user, I want `level(90)`, `stdf` and `stdr` honoured after a move exactly as at build.

## Business requirements

- **BR-13.1** After a move, the saved lfitci/qfitci line and band equal twoway's `regress`/`predict` on the kept rows (1e-8 relative to the served app's values).
- **BR-13.2** Two rows (lfitci) or three (qfitci) draw the line and no band; fewer than two draw nothing.
- **BR-13.3** No lfitci/qfitci is marked "(unfiltered)" on the saved page.
- **BR-13.4** The help names lfitci and qfitci among the refitted types.

## Technical requirements

- **TR-13.1 Tagging.** In `map_lfitci`, before `return [line_r, band_r]` (both the empty return and the drawn one): `line_r._dash_agg_source = ci_source` (or `empty_ci_src`), `line_r._dash_agg_config = dict(self._fit_agg_config("lfitci", xvar, yvar, wtype, w, fig, options, ["x_fit", "y_fit", "y_lower", "y_upper"], _n_used, _rng), level=float(_lvl), std=str(std))`, `line_r._dash_agg_rows = self._agg_member_ids(source, view)`. On the empty path `std = self._fitci_std_for(options, wtype, "lfitci")` and `_lvl = _resolve_level(options, self.default_level)` are computed first (they are pure reads). `_n_used`/`_rng` as S10 TR-10.1 (qfitci reads `n` as given, so `_n_used` is `_fit_grid`'s own count). Only the LINE renderer is tagged: step 3b registers one `(source, cfg)` per tagged renderer, and the band shares the source.
- **TR-13.2 `_DASH_JS_REFIT_TYPES`** gains `"lfitci", "qfitci"`.
- **TR-13.3 JS helper** before `// DASH_FIT_HELPERS_END`:
  ```js
  // A ci layer's columns (S13, D-13.a): line rows where x and y are finite,
  // the band NaN where its value is not (twoway's missing limits).
  function dash_ci_write(src, ac, xs, ys, lo, hi) {
      const [cx, cy, cl, cu] = ac.cols;
      const out = {}; for (const c of ac.cols) dash_own_col(out, c);
      for (let i = 0; i < xs.length; i++) {
          const xv = dash_axis_value_of(xs[i], ac.xaxiskind), yv = dash_axis_value_of(ys[i], ac.yaxiskind);
          if (!isFinite(xv) || !isFinite(yv)) continue;
          const l = dash_axis_value_of(lo[i], ac.yaxiskind), u = dash_axis_value_of(hi[i], ac.yaxiskind);
          out[cx].push(xv); out[cy].push(yv);
          out[cl].push(isFinite(l) ? l : NaN); out[cu].push(isFinite(u) ? u : NaN);
      }
      src.data = (ac.join) ? dash_join_rebuild(out, {x: cx, y: cy, style: ac.join.style, cmiss: "y"}, null) : out;
      src.change.emit();
  }
  ```
- **TR-13.4 Branches** before `// DASH_FIT_BRANCHES_END`:
  ```js
      } else if (ac.type === 'lfitci' || ac.type === 'qfitci') {
          const n = fx.length;
          const empty = () => dash_ci_write(src, ac, [], [], [], []);
          if (n < 2) { empty(); continue; }
          const xg = dash_fit_grid(fx, ac.n, ac.range);
          let X, Xg;
          if (ac.type === 'lfitci') {
              const ww = dash_weight_norm(fw, ac.wtype, n);
              const mu = dash_wmean(fx, ww);
              X = fx.map(v => [1, v - mu]); Xg = xg.map(v => [1, v - mu]);
          } else {
              const d = dash_qfit_design(fx, xg); X = d.X; Xg = d.Xg;
          }
          const fit = dash_wls(X, fy, fw, ac.wtype);
          if (fit === null) { empty(); continue; }
          const yg = Xg.map(r => { let s = 0; for (let j = 0; j < r.length; j++) s += r[j] * fit.beta[j]; return s; });
          const se = dash_fitci_se(Xg, fit, ac.std);
          const t = (fit.df >= 1) ? dash_t_ppf(0.5 + ac.level / 200, fit.df) : NaN;
          dash_ci_write(src, ac, xg, yg, yg.map((v, i) => v - t * se[i]), yg.map((v, i) => v + t * se[i]));
  ```
  (`fit.df` is `N - kk` with N the weight sum: for fw the frequency total, as `_dash_wls`.)
- **TR-13.5 js_runner**: `run_fit_js_block` already finds the branch by `"} else if (ac.type === 'lfitci' || ac.type === 'qfitci') {"`? No -- it searches `"} else if (ac.type === '%s') {" % type`. Change the runner (S13 owns js_runner this batch) to try `"} else if (ac.type === '%s') {"` first, then `"} else if (ac.type === '%s' || "` as a prefix match (`js.find`), then the `"|| ac.type === '%s') {"` suffix form, taking the first found; document in its docstring.
- **TR-13.6 Flips**: `_FROZEN` loses the two; `_REFIT` gains them; `test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked` (:226) re-pointed from lfitci to fpfitci (still frozen) with a `Flipped:` line.
- **TR-13.7 Help**: dash.sthlp:1946 column 2 (after S16: `lfit, qfit, lowess; others marked`) becomes `lfit, qfit, lfitci, qfitci, lowess; others marked`; the paragraph's "does not refit" list loses `{cmd:lfitci}, {cmd:qfitci},`; S16's lowess sentence stays where it is; the S10 sentence becomes `A straight or quadratic fit and its confidence band ({cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}) are refitted from the rows that pass the filter...`.
- **TR-13.8 Timing**: `TestTheJsTwinsAreBounded::test_lfitci_and_qfitci_under_node_on_1e5_rows` under 2 s each.
- **TR-13.9 Parity corpus**: `_move_case("lfitci, dropdown", _MOVES[0], [_sc(), plot_for("lfitci")])`, `_move_case("qfitci level(90), range", _MOVES[1], [_sc(), plot_for("qfitci", {"level": "90"})])`, `_move_case("lfitci stdf, slider", _MOVES[2], [plot_for("lfitci", {"stdf": "stdf"})])`, `_move_case("lfitci [fw=rep], dropdown", _MOVES[0], [plot_for("lfitci", {"weight": "fweight", "wexp": "rep"})])`, `_move_case("qfitci on a 5-minute %tc x, range", _MOVES[1], [plot_for("qfitci", yvar="mpg", xvar="when_tc")])` -- the last only if `_DF` carries a `%tc` column; otherwise record D-13.c's case in `test_js_fit_refit.py::TestCiBranch::test_nearly_collinear_design` with its own tolerance.

## Boundaries

Do not edit `map_lfit`/`map_qfit` (done), the option reading and the `points` early return at the top of `map_lfitci`/`map_qfitci` (S11's, landed in batch 4), S14's `_dash_connect_opt`/`_dash_recast_opt`, S15's colorvar code, `map_lowess` or the lowess branch (S16's), `_render_ci_band`, `_ci_band_glyphs`, `_dash_wls`/`_dash_fitci_se` in Python, the histogram/kdensity branches, `_BRUSH_JS`, the appliers, `_build_filter_widgets`.

## Stata truth

No new extractor. Truth block `* ==== S13 F1b: lfitci and qfitci ====` (S01's stub header), helpers `_u13_*`:
- **U13-01** `sysuse auto; dash scatter mpg weight || lfitci mpg weight, filter(foreign, type(dropdown)) name(zu13a)`; saved page moved to Foreign (JsSession); twoway `lfitci mpg weight if foreign == 1, n(100)` serset (`.t.plotregion1.plot1.serset` carries the band's lower/upper and the line); compare x, y, lower, upper to 1e-7 relative.
- **U13-02** `qfitci mpg weight, level(90) n(20)` with the range filter on price to 4500-11385 versus `twoway qfitci mpg weight if inrange(price,4500,11385), level(90) n(20)`.
- **U13-03** `lfitci mpg weight, stdf` dropdown to Domestic versus `twoway lfitci mpg weight if foreign == 0, stdf`.
- **U13-04** `lfitci mpg weight [fw=rep78]` dropdown to Foreign versus `twoway lfitci mpg weight [fw=rep78] if foreign == 1`.
- **U13-05** a move leaving two rows (`price` slider to 14500: 14500 and 15906): the saved lfitci source has two... rather `n()` points of line and all-missing limits; twoway's serset on `if price >= 14500` has the line and missing limits (`serset` values `.` read as NaN by the python block).

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (appended; red at the batch-5 base)

- Test: `map_lfitci`/`map_qfitci` tag the LINE renderer only, with S10's keys plus `level` (float) and `std` -- `TestTheConfig::test_lfitci_config_keys`, `::test_qfitci_config_keys`, `::test_the_band_renderer_is_not_tagged`, `::test_std_none_for_aw_stdf`.
- Test: `_dash_stale_kind("lfitci"|"qfitci")` is None -- `TestStaleKind::test_lfitci_and_qfitci_are_refit`.
- Test: the ci branch equals `map_lfitci`'s four columns on: default, level(90), stdf, stdr, aw, fw, pw, constant x (mean and its interval), two rows (band NaN), one row (empty), range(1000 6000) -- `TestCiBranch::test_lfitci_matches_python[case]` (`assert_allclose(rtol=1e-8, atol=1e-10, equal_nan=True)`).
- Test: qfitci: default, level(99), aw, three rows (band NaN), two-valued x (both rules), n(3) -- `::test_qfitci_matches_python[case]`.
- Test: `dash_ci_write` keeps a row with a NaN band and drops a row with a NaN y -- `TestCiWrite::test_rows`.
- Test: saved equals served after every `_MOVES` for both types -- `TestTheSavedPageRefits::test_saved_equals_served[lfitci|qfitci-move]` (band and line; the outline renderer's source is the same object).
- Test: the nearly collinear design (D-13.c) -- `TestCiBranch::test_nearly_collinear_design` (line rtol 1e-6; band compared only when `fit["df"]` equals the JS's).
- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked` over `_REFIT` now including lfitci/qfitci (red).

### Cases in cscripts

- `test_wp31_truth.cscript` U13-01..U13-05.

### Flips

- `_FROZEN` loses lfitci, qfitci; `test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked` uses fpfitci.
- Test: a `map_lfitci` call with `points` (S11) returns renderers without `_dash_agg_config` -- `TestTheConfig::test_a_points_layer_is_not_tagged` (guard).

### Parity corpus

TR-13.9's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Tagging and schema | pytest `TestTheConfig` | -- | saved |
| Branch vs Python | node `TestCiBranch` | `stat_truth.json` `fitci_std` values as a sanity pin (x=1760 se) | n/a |
| Saved vs served after a move | `TestTheSavedPageRefits`; `MOVE_CORPUS` | -- | yes |
| Stale cue | `TestARefitLayerIsNeverMarked`, `TestStaleKind` | -- | saved |
| Stata truth | U13-01..05 | live | saved vs twoway |
| Cost | `TestTheJsTwinsAreBounded` | -- | n/a |

**Acceptance criteria**
- **AC-13.1** Saved lfitci/qfitci line and band equal the served app's after every corpus move to 1e-8 relative (NaN equal NaN).
- **AC-13.2** Two rows (lfitci) and three (qfitci) draw the line and a NaN band; one row draws nothing; stdf/stdr under aw/pw draw no band.
- **AC-13.3** No lfitci/qfitci marked; the seven remaining fit types still marked.
- **AC-13.4** U13-01..05 pass; both twins under 2 s at 100,000 rows.

## Tasks

**Commit boundary.** 13-01 to 13-03 form the F1b commit, subject `Refit lfitci and qfitci with their bands on the saved page (WP-31 F1b)`, made by 13-03 on `wp31-s13`. Body: `<scratch>/13-01-failure.txt`; the measured defect (the band after the Foreign move is the build's); the change (tags in both mappers, `dash_ci_write`, the ci branch, `_DASH_JS_REFIT_TYPES`); `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[lfitci-dropdown to Foreign] -- failed at <base> with <text>`; `Regression: test/test_wp31_truth.cscript U13-01`; `Flipped: test/test_saved_stale_cue.py::_FROZEN -- lfitci and qfitci were frozen because the page did not refit them (F1b)`; `Flipped: test/test_saved_stale_cue.py::TestTheCueAppearsOnAMove::test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked -- used lfitci, now refitted; fpfitci is the ci layer still frozen (F1b)`; `Fixture: none`; `BUGS.md: "<F1b title>" (closed)`; `GAPS3: F1b Tracked`.

<task type="auto" id="13-01">
  <name>Write the failing ci refit tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Append the "TDD test stubs" classes to test/test_js_fit_refit.py under a comment `# ---- WP-31 F1b: lfitci and qfitci ----`. `TestCiBranch` builds the subset with `GM().map_lfitci(figure(), ColumnDataSource(df_subset), "y", "x", opts)` on `_DF`-derived frames (the `weighted_data` rows of test/fixtures/stat_truth.json for aw/fw/pw), reads the LINE renderer's `_dash_agg_config` and `data_source.data`, runs `run_fit_js_block(cfg, x_stata, y_stata, w)` and compares the four columns with `np.testing.assert_allclose(..., rtol=1e-8, atol=1e-10, equal_nan=True)`; the JS returns NaN as null, so map `None -> nan` first. For the two-row lfitci case assert every `y_lower` is NaN and `y_fit` has `cfg["n"]` finite values. In test_saved_stale_cue.py extend `_REFIT` with `"lfitci", "qfitci"` (the class is parametrised over it, so the new nodes are red). Run `python3 -m pytest test/test_js_fit_refit.py -k "lfitci or qfitci or CiWrite or Ci" test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked -q -n0 2>&1 | tee <scratch>/13-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/13-01-failure.txt is at least 20; `git status --porcelain | grep -c '^[AM]'` prints 0.]]></verify>
  <done>Every F1b regression test exists and fails against the batch-5 base with the text saved.</done>
</task>

<task type="auto" id="13-02">
  <name>Tag the ci mappers and add the ci branch</name>
  <files>dash_render.py, test/js_runner.py</files>
  <action><![CDATA[(1) `_DASH_JS_REFIT_TYPES = frozenset({"lfit", "qfit", "lfitci", "qfitci"})`. (2) In `map_lfitci` (:16421): on the `n < 2` path compute `std = self._fitci_std_for(options, wtype, "lfitci")`, `_lvl = _resolve_level(options, self.default_level)` before building the empty renderers, then before `return [line_r, band_r]` add the three TR-13.1 assignments on `line_r` with `empty_ci_src`, `n=_FIT_GRID`, `rng=None`; on the drawn path compute `_n_used = len(x_fit)` and `_rng = _dash_range_pair(options, "lfitci", "")` under silenced warnings (as S10 did), and add the three assignments on `line_r` after `_render_ci_band` returns. Repeat in `map_qfitci` (:16550) with layer "qfitci"; on its `except np.linalg.LinAlgError` bootstrap path tag with `std` and `_lvl` as well (the page will refit analytically; the bootstrap path is a fallback the config cannot express -- note this in the mapper comment). (3) Insert `dash_ci_write` (TR-13.3) before `// DASH_FIT_HELPERS_END` and the branch (TR-13.4) before `// DASH_FIT_BRANCHES_END`. (4) test/js_runner.py `run_fit_js_block`: TR-13.5's three-form head search:
```python
    t = ac["type"]
    heads = ["} else if (ac.type === '%s') {" % t,
             "} else if (ac.type === '%s' || " % t,
             "|| ac.type === '%s') {" % t]
    pos = [js.find(h) for h in heads]
    found = [(p, h) for p, h in zip(pos, heads) if p != -1]
    assert found, "no branch for %r in _FILTER_JS" % t
    p, h = min(found)
    lo = js.index("{", p) + 1 if not h.endswith("{") else p + len(h)
```
and keep the `nxt`/`end` cut as S10 wrote it (`nxt = js.find("} else if (ac.type === '", lo)`). Run `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py::TestFilterJavaScript test/test_saved_stale_cue.py -q`.]]></action>
  <verify><![CDATA[Green except the `_FROZEN` lfitci/qfitci nodes and :226 (flipped in 13-03); `python3 -c "import dash_render as d; print(sorted(d._DASH_JS_REFIT_TYPES))"` prints `['lfit', 'lfitci', 'lowess', 'qfit', 'qfitci']`; `grep -c "function dash_ci_write" dash_render.py` prints 1.]]></verify>
  <done>Both ci mappers tag their line renderer and the saved page refits line and band from the kept rows.</done>
</task>

<task type="auto" id="13-03">
  <name>Flip, certify, document and commit F1b</name>
  <files>test/test_saved_stale_cue.py, test/test_wp31_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Remove `"lfitci", "qfitci"` from `_FROZEN`; re-point :226's test from `lfitci` to `fpfitci` with the docstring reason. Append TR-13.9's `MOVE_CORPUS` entries (test/test_mode_parity.py, as S10's 10-04 did) under `# WP-31 F1b: lfitci and qfitci refit on the saved page`. Append the U13 block above the marker line in test/test_wp31_truth.cscript (helpers `_u13_move`, `_u13_serset_band` reading the serset's four variables through `serset use` into a python list, `_u13_close`); run `WP31_ONLY=S13 scripts/stata_slot.sh <scratch>/s13 <scratch>/run_test_wp31_truth.do`. dash.sthlp TR-13.7 (and the pin S10 flipped: update the expected text). Add `test_lfitci_and_qfitci_under_node_on_1e5_rows` to test_estimator_cost.py's `TestTheJsTwinsAreBounded`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_mode_parity.py -k "lfitci or qfitci or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q`. Close BUGS.md F1b (Resolution: fixed; `map_lfitci`, `map_qfitci` tag; `_FILTER_JS` ci branch; `_dash_stale_kind`; both renderers), rewrite the GAPS3 line to `- **F1b Tracked:** Closed in WP-31, BUGS.md "<F1b title>", commit pending.` (DECISIONS A11: the merger's step k.3b fills the sha; BUGS.md, GAPS3.md and CHANGELOG.md are the closing task's implied files, A13), replace the `<!-- WP-31 F1b -->` markers (Results: `lfitci and qfitci on a saved page after a filter move: the build's line and band (marked) -> regress/predict on the kept rows (WP-31, F1b)`). Grep the message for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; the slot log holds `U13-01 ok`..`U13-05 ok`; `git log -1 --format=%s` ends `(WP-31 F1b)`; `git log -1 --format=%B | grep -c "^Flipped:"` prints 2; `grep -c "F1b Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1.]]></verify>
  <done>F1b is one green commit: lfitci and qfitci refit with their bands on the saved page and are no longer marked.</done>
</task>

## Section completion criteria

- AC-13.1 to AC-13.4 hold; `_DASH_JS_REFIT_TYPES` has five members (lfit, qfit, lowess, lfitci, qfitci); `_FROZEN` has eight; `dash_ci_write` is defined once; the S10 markers are intact.
- BUGS.md F1b closed; GAPS3 Tracked rewritten (`commit pending`, A11); CHANGELOG marker replaced; help updated; one commit.

## Notes

- **Renderer order.** Only the line renderer is tagged (TR-13.1); the band and its outline share the source and follow. The served app refits through `_dash_redraw_for` as before.
- **R12.** S13 is the only `_FILTER_JS` editor in batch 5 (A22 moved it from batch 4 so it never shares S11's batch); S11's edits to the top of the same mappers landed in batch 4 -- S13's mapper edits are the last lines before each final `return`. S28 (batch 9) still depends on S13.
- **NaN transport.** node prints NaN as `null`; `JsSession` commits `None -> np.nan`; the browser's BokehJS keeps NaN. `dash_ci_write` writes `NaN` (the literal) into a JS array; `JSON.stringify` of the harness turns it to null -- the test maps it back.
- **Decisions for maintainer ratification.** D-13.a (band NaN kept as a cell, not a dropped row); D-13.c (the rank-cut residual is a named corpus case with its own tolerance, filed under M12 if red).
- **Cscript**: `serset use` after `serset set`/`serset dir`; read `.t.plotregion1.plot1.serset` (the number) then `serset set <n>`; missing values arrive as `.` -- the python block reads them through `Data.get` as `8.98846567431158e+307` (Stata's missing) and maps anything above 8.9e307 to NaN.
