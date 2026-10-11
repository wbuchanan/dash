# Section 05: Histogram edge rule (C2)

> Part of: WP-28 · Gaps: C2 · Risk: yellow · Batch: 2 · Depends on: 03 · Blocks: 19 · Tasks: 6, 1 commit (C2)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **03** · Blocks **19** · Risk **yellow** · Commits: one commit (C2) → CHANGELOG `Results that change`

- D10 (S03 TR-03.1's fixed names): `test/test_histogram_edge_rule.py` imports `from js_runner import run_filter_js_block, NODE`; its node tests carry `@pytest.mark.skipif(NODE is None, reason="node is not installed; set DASH_NODE")`; S03 deletes the private `_NODE`/`_run_filter_js_block` definitions from `test_statistical_helpers.py` (they stay there as aliases, but this module does not import them). Batch-2 merge order is S04, S05, S13, S17, S16, S14 (`sections/index.md` step 2). The histogram helper comes from the existing module: `from test_statistical_helpers import _hist`.
- D10/F-13: TR-05.1 states the NaN precondition of `_histogram_counts` -- the caller has already dropped missing rows through `_layer_weights` → `_masked` -- and `TestHistogramCounts` gains the two NaN cases.
- D3/F-07/consistency #29: the C2 BUGS.md entry is appended at the END of BUGS.md in the D3 form; its Description cites the entry at :1215 by title.
- D11 (`sections/BRIEF.md` "Certification scripts"; `sections/index.md` rule R1): no new cscript. The page-sum checks and the `start()` refusal (HE-01..HE-04) join `test/test_e2e_filters.cscript`; the bar-for-bar comparison with `twoway__histogram_gen` (HE-05, HE-06) is the block `* ==== S05 C2: histogram bars against twoway__histogram_gen ====` appended to `test/test_gaps2_truth.cscript`; the runner and the hygiene pins are untouched.
- D12 (`sections/BRIEF.md` "Fixtures"): the regenerated `stat_truth.json` gains the four provenance keys in `_meta` (its existing keys stay) and a test asserts they exist; the regeneration is verified record by record outside `_meta` and the new section (rule R5: one regeneration, by this section).
- D2 (`sections/index.md` rule R3; section-01 TR-01.7; consistency #1): 05-06 replaces the marker `<!-- WP-28 C2 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change` with one line ending `(WP-28, C2)` that quotes the failing tests' recorded counts (2245 of 2246; 49 of 50) as the old value (Q24).
- D1/F-01 (with the worktree-branch commit rule of `sections/index.md` step 1): 05-01 and 05-02 do not commit; the section's one commit is made by 05-06 on the worktree branch `wp28-s05`, subject ending `(GAPS2 C2)`; the merger lands it onto `s3-bugs`.
- feasibility #3: no `(new)` annotation in `<files>`.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

A continuous histogram in dash can lose its largest observation. GAPS2 C2 measured it: "On
nlsw88 ttl_exp, `bin(27|51|54|83)` counts 2245 of 2246 rows, census pop `bin(75)` counts 49 of
50, and about 4% of random rounded layers lose a row. No note is printed, and density bars are
rescaled to the rows that remain." The cause is one design choice made twice. Python builds the
edges as `start + width*arange(n+1)`, so the last edge is the maximum only in exact
arithmetic; when it lands a few ULPs below, `np.histogram` (dash_render.py:9577) drops the
maximum, and the tolerance-based extra edge at :9761-9766 does not fire because the shortfall
is smaller than its tolerance. The saved page's JavaScript recount (`_FILTER_JS`,
:14818-14826) makes the same choice with a hard range test. Stata never has this problem:
`twoway__histogram_gen.ado:200-203` counts every observation as `floor((v - min)/h)`, then
folds an index below 0 into bar 0 and an index equal to `bin` into bar `bin-1`, so a value at
or floating above the last edge is in the last bar and a value below `start()` (which dash.ado
admits within reldif 1e-5, as Stata does) is in the first.

After this section, `GlyphMapper.map_histogram` counts the continuous branch exactly as its
discrete branch already does (:9565-9575, Stata's rule since the BUGS.md "histogram, discrete"
fix): floor, clamp, `np.bincount`. The tolerance edge is gone; the last edge is
`start + h*bin`, which is Stata's `r(max)`. The aggregate config the recount reads carries
`start`, `width` and `bin`, and the JavaScript applies the same floor-and-clamp with those
numbers instead of rebuilding `h` from the edges. The served app needs no change beyond the
config: since `_compute_histogram` was deleted it redraws through the mapper
(`agg['redraw']`, :26919), so one mapper fix covers both renderers. Every frequency histogram
sums to N in Python, in the served app and under node, and Stata's own `twoway__histogram_gen`
output for the five measured cases is pinned in `stat_truth.json` and re-measured live in a
block of `test/test_gaps2_truth.cscript`.

C2 is alone in this section because it touches one mapper, one JavaScript branch and one
extract script, and no other batch-2 section edits the same lines: S04 prepends a constant to
`_DASH_FILTER_MASK_JS` (14110), S17 rewrites the aggregate block's reads of `active` above the
histogram branch (14725-14767), and the merge order S04, S05, S13, S17, S16, S14 lands this
section's hunk (14800-14826) before S17's. S03's `js_runner.run_filter_js_block` runs the
histogram branch of the real `_FILTER_JS` under node and is enough to prove the twin; this
section depends on S03 for that name (and for `NODE`).

**Test order (CLAUDE.md rule 7) and commit rule (D1): task 05-01 writes every regression
test that needs no Stata fixture**, runs it against the unmodified tree and saves the
2245/49 failure text to `<scratch>/05-01-failure.txt` -- it does not commit (a red tree is
never committed, rule 4); task 05-02 records Stata's truth, pins it and appends its failures
to the same file; tasks 05-03 to 05-05 turn the tests green; 05-06 closes the entry, runs the
full pytest suite once in the worktree and makes the section's ONE commit on the worktree
branch `wp28-s05`, subject ending `(GAPS2 C2)`, whose body opens with the saved failure text
(S01 TR-01.9); the merger lands that commit onto `s3-bugs` (`sections/index.md` step 1).

## Risk: [yellow] — one numeric rule in two languages, and every continuous histogram's bars can move by one count

- **Why.** The change is small and the rule is Stata's own, already implemented for the
  discrete branch. But it changes drawn numbers on any dataset whose maximum sits a few ULPs
  above the computed last edge, and it rewrites a JavaScript branch that only node tests
  exercise.
- **Risk factors.** (1) The Python count and the JavaScript count must agree exactly, or a
  filter move changes a bar that no filter touched. (2) `test/test_histogram_spurious_bin.py`
  was written around the tolerance edge this section deletes; its assertions still hold but
  its docstring and instrument (`np.histogram` on the returned edges) describe the old
  contract. (3) Regenerating `stat_truth.json` reruns every probe in
  `scripts/extract_stat_truth.do` (several minutes of Stata), and the whole file is rewritten.
  (4) Bokeh embeds the bar heights as a base64 ndarray, so the cscript cannot sum them with
  `cert_file_has` alone. (5) S17 edits `_FILTER_JS`'s aggregate block in the same batch, a
  few lines above this section's hunk.
- **Mitigation.** The config carries the three numbers both counters use, so neither derives
  `h`; a seeded property test compares Python and node bar-for-bar; the spurious-bin file is
  revised (not deleted) to assert the new invariant through the mapper; the regenerated
  fixture is checked record by record against the previous one outside `_meta` and the new
  section; the cscript decodes the page's JSON in a `python:` block, as
  `test/test_help_claims_4.cscript:421` already does; this section merges before S17 and a
  rejected hunk is applied by hand (rule R2).

## Dependencies

- **Depends on:** section 03 (`test/js_runner.py`: `run_filter_js_block` and `NODE`, S03
  TR-03.1). The fixture CSVs and the served builder exist at 91d97be.
- **Blocks:** 19 (closeout lifts the CHANGELOG line and the GAPS2 Tracked line).
- **Parallel batch:** 2. **Can run with:** S04, S13, S14, S16, S17. Merge order in the
  batch (`sections/index.md` step 2): S04, S05, S13, S17, S16, S14. S05 edits
  `GlyphMapper.map_histogram`, `GlyphMapper._histogram_grid`, the histogram branch of
  `_FILTER_JS`, `scripts/extract_stat_truth.do`, `test/test_statistical_truth.py`,
  `test/test_e2e_filters.cscript` and `test/test_gaps2_truth.cscript` (one appended block);
  no other batch-2 section names the mapper methods or the extract script; S17 appends its
  own block to the truth script after this section's (rule R1) and edits `_FILTER_JS` above
  the histogram branch.

Why: the recount twin is proved under node through S03's runner, whose predecessor S03
deleted; the block form and the truth script exist once S02 (batch 1) has landed.

## Evidence

### The Python count (`dash_render.py`, checked at 91d97be)

`GlyphMapper.map_histogram` :9519-9627. The discrete branch already applies Stata's rule:

```python
 9565            nb = len(edges) - 1
 9566            h = (float(edges[-1]) - float(edges[0])) / nb
 9567            idx = np.floor((arr - float(edges[0])) / h)
 9568            idx = np.clip(idx, 0, nb - 1).astype(np.int64)
 9569            counts = np.bincount(idx, weights=w, minlength=nb).astype(float)
 9570        else:
 9571            counts, _ = np.histogram(arr, bins=edges, weights=w)
```

(the `if discrete and len(arr):` fork opens at :9559; the `else` is the continuous branch).
The aggregate config at :9607-9623 carries `type`, `varname`, `bin_edges`, `ymode`, `wvar`,
`wtype`, `discrete`, and nothing the JavaScript could use to recover `h` without rebuilding it
from the edges. `r._dash_agg_rows` (:9626) is untouched by this section.

`arr` reaches the count through `_layer_weights` (:9551, `arr, w, wtype =
self._layer_weights(source, view, options, "histogram", yvar)`), which is `_masked` plus the
weight column: `_masked` (about :7810-7835) drops every row where any named column is NaN
(`finite = ~np.isnan(cols[0]) ...; return tuple(c[finite] for c in cols)`) and
`_layer_weights` (:7843) pulls the weight through "the SAME joint NaN drop as x and y". So
by the time the count runs, `arr` and `w` are finite; a NaN can reach `_histogram_counts`
only from a direct call, and F-13's precondition is stated for that caller.

`GlyphMapper._histogram_grid` :9629-9768 returns `(edges, ymode)`. The continuous tail:

```python
 9750        edges = start + width * np.arange(n_bins + 1, dtype=float)
 ...
 9761        _edge_tol = 1e-9 * max(abs(float(a_max)), abs(float(start)),
 9762                               float(width), 1.0)
 9763        if edges[-1] < a_max - _edge_tol:
 9764            edges = np.append(edges, a_max)
 9765
 9766        return edges, _dash_histogram_ymode(options)
```

The comment block above it (:9751-9760) explains the tolerance as a fix for a 1e-14-wide
spike bar; that fix is superseded here because with floor-and-clamp no extra edge is ever
needed. `start`, `width` and `n_bins` are all locals of this method at :9723-9748: `start`
from `start()` or `a_min` (:9704-9706), `n_bins` from `ceil(span/width)` for `width()`
(:9732) or from `bin()`/`_stata_bin_count` (:9734-9735), `width = span / n_bins` when derived
(:9748). `_histogram_heights` :12746-12776 divides by `np.diff(edges)`, so uniform edges give
Stata's `count/(N*h)`. `_stata_bin_count` :12778-12797 is Stata's `int(min(sqrt(N),
10*log10(N)))`.

### The JavaScript count (`_FILTER_JS`, :14177; histogram branch :14768-14834)

```js
14800        const bw = (edges[n_bins] - edges[0]) / n_bins;
...
14808            if (ac.discrete) {
14812                let b = Math.floor((v - edges[0]) / bw);
14813                if (b < 0) b = 0;
14814                if (b > n_bins - 1) b = n_bins - 1;
14815                counts[b] += wv;
14816                continue;
14817            }
14818            if (v < edges[0] || v > edges[edges.length - 1]) continue;
14819            if (v === edges[edges.length - 1]) {
14821                counts[n_bins - 1] += wv;
14822            } else {
14823                for (let b = 0; b < n_bins; b++) {
14824                    if (v >= edges[b] && v < edges[b + 1]) { counts[b] += wv; break; }
14825                }
14826            }
```

`dash_scale` (:14776-14789) is the twin of `_histogram_heights` and stays. `_FILTER_JS` is
the saved page's callback only: it is not in the served constants list (:24326-24428) and the
served app never runs it. The branch reads only `ac.*`, `v` and `wv`; the reads of `active`
that S17 rewrites are in the aggregate block's preamble above `if (ac.type === 'histogram')`.

### Where the config travels

Saved: `DashRenderer` collects `_r._dash_agg_config` into `agg_source_registry`
(:24130-24145, `_cfg = dict(_r._dash_agg_config)`), which the callback receives as `ac`.
Served: `_dash_redraw_for` (:26066) redraws the layer through the same `map_histogram` from
the filtered frame, `agg['redraw'](agg_fdf)` at :26919, registered at :26369-26375; the
comment at :25760-25769 records why `_compute_histogram` was deleted. `GlyphMapper` is copied
whole into the app (:24698-24700), so a new `@staticmethod` on it needs no copy-list entry.

### dash.ado's `start()` gate (:3823-3837)

```stata
3827        if "`ptype'" == "histogram" & `"`s(start)'"' != "" {
3830            quietly summarize `yvar' `macval(_hq)', meanonly
3831            if r(N) > 0 {
3832                if r(min) < `s(start)' & reldif(r(min), `s(start)') > 1e-5 {
3833                    display as error "option start() may not be larger than minimum of `yvar'"
3834                    exit 198
```

This is Stata's own test and Stata's own words, and it stays. A `start()` above the minimum by
less than reldif 1e-5 passes here as it passes Stata, and the rows below it must then be
counted in bar 0.

### Stata's rule (`/Applications/StataNow/ado/base/t/twoway__histogram_gen.ado`)

- `:102-111`: the reldif 1e-5 gate; in the continuous case `scalar min = start`.
- `:119-136`: `bin = max(1, int(min(sqrt(N), 10*log10(N))))`, `h = (max-min)/bin`; with
  `width()`: `h = width`, `bin = max(1, ceil((max-min)/h))`.
- `:200-203`, the whole of C2:

```stata
200    gen `midbin' = floor((`v'-`min')/`h') if `touse'
201    // fix edge problems between -float- and -double- precision
202    replace `midbin' = 0 if `touse' & `midbin' < 0
203    replace `midbin' = `bin'-1 if `touse' & `midbin' == `bin'
```

- `:166-185`: returns `max = min + h*bin`, `min`, `start`, `width`, `bin`, `N`.
- `:232-235`: with a user `start()` one extra observation with `x = start` and a missing
  height is appended (so the fixture's `bar_height` series for a `start()` case carries one
  `null`). GAPS2 and research report B cite these lines as 198-200; report D and the file
  itself say 200-203. The file is authoritative.

### Fixtures on disk

- `test/fixtures/data/nlsw88.csv`: columns `wage,ttl_exp`, 2246 rows; `census.csv`:
  `death,pop`, 50 rows. `test_statistical_truth.py`'s `datasets` fixture (:47-59) exposes
  ttl_exp as `datasets["nlsw88"][1]` and pop as `datasets["census"][1]`.
- `test/fixtures/stat_truth.json`: section `histogram` keyed `<ds>:<var>:<variant>` with
  `bin`, `start`, `width`, `xmin`, `xmax`, `N`, `n_x`, `n_points`, `bin_midpoint`,
  `bar_height`, `sample_index`, `cmd`, `rc`, `type`. Keys exist for `census:pop:*` and
  `nlsw88:{wage,hours}:*`; nothing for `ttl_exp`, `bin(27)` or `bin(75)`. Its `_meta` holds
  `run_date`, `counts` and `self_checks` today; those keys stay and the four provenance keys
  are added (D12).
- `scripts/extract_stat_truth.do`: the header globals `ZQ_REPO` (the absolute repository
  path), `ZQ_OUT`, `ZQ_WORK`, `ZQ_REC` (:67-73, so the script sets its own directories and is
  handed to `scripts/stata_slot.sh` directly), record helpers `zq_s`/`zq_n`/`zq_a` (:78-99),
  `zq_chunk` (:100-118), `zq_curve` (:120-176, **`maxn(41)`: a curve longer than 41 points is
  stored at 11 sampled indices**), the dataset table (:238-241, `hvars(wage hours)` for
  nlsw88), layer 1 (:276-380), the python reader (:1856-1913, `NEVER_NUM` :1898-1905), the
  section tuple the JSON is built from (:2779-2787) and `_meta.counts`/`self_checks` (about
  :2694-2760).

### The certification scripts this section extends (D11)

- `test/test_e2e_filters.cscript` (242 lines): `cscript "dash filter widget E2E" adodir ".."`
  (:11), the `c(python_exec)` gate with `exit 222` (:24-27), `sysuse auto`, `do "../dash_parse.mata"`,
  `do "../dash.ado"`, `do "cert_helpers.do"` (:39); cases P2-73..P2-75, FL-EX-1, FL-CP-1,
  FL-QT-1 and FL-QT-2, each ending in a `display "<ID> PASS: ..."` line after plain `assert`s;
  a `// Cleanup` section (`dash clear`) and the closing line `All filter widget E2E tests
  PASSED.` The HE-01..HE-04 block goes immediately before the `// Cleanup` section, in the
  same `assert` + `display` style, and restores `sysuse auto, clear` at its end.
- `test/test_gaps2_truth.cscript` (created by S02): the `GAPS2_ONLY`-gated block form of
  `sections/BRIEF.md` "Certification scripts", the tally helpers `_gt_expect`/`_gt_done`,
  `cert_helpers.do` and `cert_svg.do` loaded, the last line `* ==== append new blocks above
  this line ====`. This section's block is the first appended after S02's smoke block (section
  order, rule R1).

### Existing tests that pin today's behaviour

These are listed so the executor flips or revises them, never deletes them:

- `test/test_histogram_spurious_bin.py` (whole file): the module docstring documents the
  tolerance edge ("The guard is still needed ... kept, with a tolerance") and
  `TestTheGuardStillGuards::test_an_explicit_width_that_stops_short_still_covers_the_data`,
  `::test_width_alone_still_covers_the_data` count with `np.histogram` on the returned edges.
  No assertion inverts (with `ceil` the grid already covers those data), but the file states
  a contract this section replaces: revise the docstring and re-instrument the two tests
  through `map_histogram` frequency sums (TR-05.9).
- `test/test_statistical_helpers.py::TestFilterJavaScript::test_the_discrete_recount_folds_the_top_value_as_python_does`
  asserts `ac.get("discrete") is True`: the key stays in the config (TR-05.4). After S03 the
  class runs through `js_runner.run_filter_js_block` under `@requires_node`.
- `test/test_resource_limits.py::TestAHistogramWidthCannotOverflow::test_an_ordinary_width_still_works`
  asserts every bar is width 2.0: true before and after (no extra edge means no narrower last
  bar).
- `test/test_statistical_truth.py::TestHistogramAgainstStata::test_bin_option_reproduces_statas_bar_heights`
  (auto:mpg bin(20), non-empty bars): passes before and after; Stata folds the same way.
- `test/test_mode_parity.py` corpus cases `histogram, bin()` (:1053) and `histogram, percent`
  (:1054): both modes draw through the mapper, so parity holds.
- `test/function_test_map.py`: `GlyphMapper.map_histogram` :177, `GlyphMapper._histogram_grid`
  :129, `_histogram_heights` :510 stay; the new static method needs an entry.

## User stories

- **US-05.1** As the Stata user pasting twoway syntax, I want `dash histogram ttl_exp,
  bin(27)` to count all 2246 observations, so that the bars I publish are twoway's bars.
- **US-05.2** As the dashboard viewer, I want a histogram's bars after a filter move to be the
  same count the page drew for those rows at first paint, so that moving a slider never adds
  or drops an observation that the filter did not touch.
- **US-05.3** As the Stata user, I want `start()` to behave as twoway's does, refused above
  the minimum with twoway's message and, when tolerated, counting the rows below it in the
  first bar, so that a pasted command runs and draws the same picture.
- **US-05.4** As the maintainer, I want Stata's own `twoway__histogram_gen` output for the
  measured cases pinned in a fixture and re-measured by a certification block, so that the
  rule can never drift back silently.

## Business requirements

- **BR-05.1** Every observation in a histogram's sample is counted in exactly one bar, in the
  saved page, in the served app and after any filter move; a frequency histogram's bars sum
  to N (to the total weight under `[fw]`).
- **BR-05.2** The bar an observation falls in is Stata's: bar `floor((v - start)/h)`, with
  values below `start` in the first bar and values at or above the last edge in the last bar.
- **BR-05.3** A `bin(#)` histogram draws exactly # bars whose last right edge is
  `start + h*#`, Stata's `r(max)`.
- **BR-05.4** Density, fraction and percent heights follow from the corrected counts
  (density bars integrate to 1).
- **BR-05.5** A `start()` above the sample's minimum is refused with `option start() may not
  be larger than minimum of <var>`, r(198), exactly when twoway refuses it (reldif > 1e-5);
  within that tolerance it is accepted and no row is dropped.
- **BR-05.6** Nothing is printed when a histogram is drawn correctly (DISCOVERY Q22).
- **BR-05.7** The nlsw88 ttl_exp `bin(27|51|54|83)` and census pop `bin(75)` cases match
  Stata's own generator output bar for bar, in the fixture and live.
- **BR-05.8** A missing value never reaches the count: it is dropped with its row before
  counting, in both renderers, as `marksample` drops it in Stata.

## Technical requirements

- **TR-05.1** Add `GlyphMapper._histogram_counts(arr, w, start, width, nb) -> np.ndarray`
  (a `@staticmethod` beside `_histogram_grid`): `idx = np.floor((arr - start)/width)`,
  `np.clip(idx, 0, nb-1).astype(np.int64)`, `np.bincount(idx, weights=w, minlength=nb)
  .astype(float)`. Precondition (F-13): `arr` and `w` are finite -- the caller has dropped
  missing rows through `_layer_weights` → `_masked` (dash_render.py:9551, :7843), which
  drops every row where any named column is NaN before the count. The function states that
  in its docstring and enforces it: `if not np.isfinite(arr).all(): raise ValueError(
  "_histogram_counts: arr must be finite; the caller drops missing rows through
  _layer_weights")` (a NaN through `np.floor`/`astype(np.int64)` would otherwise become an
  undefined integer and `np.bincount` would raise a bare error or miscount). Both branches of
  `map_histogram` call it; the `if discrete ... else np.histogram` fork at :9559-9571 becomes
  one block. A static method on the class travels to the served app with the class copy
  (:24698-24700); no copy-list edit.
- **TR-05.2** `_histogram_grid` removes the tolerance edge (:9751-9764) and its comment;
  its `(edges, ymode)` return shape is unchanged (many tests unpack it). The continuous edges
  stay `start + width*arange(n_bins+1)`.
- **TR-05.3** In `map_histogram`, `nb = len(edges) - 1`, `start = float(edges[0])`,
  `h = (float(edges[-1]) - start)/nb` for both branches (the discrete branch's own
  expression), so the three numbers the JavaScript gets are the ones Python counted with.
- **TR-05.4** `r._dash_agg_config` gains `"start": start`, `"width": h`, `"bin": nb`
  (plain `float`/`int`, so Bokeh serialises them as numbers). `bin_edges`, `ymode`, `wvar`,
  `wtype`, `discrete` stay.
- **TR-05.5** The `_FILTER_JS` histogram branch (:14800-14826) counts every value as
  `let b = Math.floor((v - ac.start) / ac.width); if (b < 0) b = 0; if (b > n_bins - 1)
  b = n_bins - 1; counts[b] += wv;` for discrete and continuous alike; the `bw` line, the
  range test and the edge loop go. `n_bins = ac.bin`. If `!(ac.width > 0)` the branch leaves
  every count at zero (the page never generates such a config; the pytest in TR-05.7 proves
  the keys are present), never derives a width.
- **TR-05.6** `scripts/extract_stat_truth.do` gains a LAYER 1c block (after :380's layer 1)
  writing section `histogram_edge`: for each case `twoway__histogram_gen <var>,
  generate(zqh zqx) return frequency <opts>` on the loaded dataset, recording `cmd`,
  `equivalent_user_cmd`, `rc`, `bin`, `start`, `width`, `xmin`, `xmax`, `N`, `n_x`, `type`,
  `sum_height` (from `summarize zqh, meanonly`: `r(sum)`), and the curve through
  `zq_curve bin_midpoint bar_height, sec(histogram_edge) key(<key>) maxn(100)` so every bar
  is stored. Cases: `nlsw88:ttl_exp:bin27`, `bin51`, `bin54`, `bin83`, `census:pop:bin75`,
  `nlsw88:ttl_exp:bin27_start` (`start()` = `r(min)*(1+5e-6)` computed in the do-file after
  `summarize ttl_exp, meanonly`, recorded as `start_requested`), and
  `nlsw88:ttl_exp:bin27_density` (no `frequency`, for the y mode). The provenance stamp
  (D12; `sections/BRIEF.md` "Fixtures"): the do-file captures `tempfile gitrev`, `shell git -C
  "${ZQ_REPO}" rev-parse HEAD > "\`gitrev'"`, reads the first line into `local dash_commit`
  (40 hexadecimal characters, asserted with `ustrregexm`), and the python block reads it
  through `Macro.getLocal("dash_commit")` and writes `_meta.stata_version`
  (`c(stata_version)`), `_meta.born_date` (`c(born_date)`), `_meta.dash_commit` and
  `_meta.extracted` (`c(current_date)`) beside the existing `run_date`, `counts` and
  `self_checks` keys, which stay. The python block adds `"histogram_edge"` to the section
  tuple (:2779-2787), `histogram_edge_probes` to `_meta.counts`, and a self-check
  `histogram_edge_frequency_sums_equal_N` (every frequency record's `sum_height == N`). The
  block never calls Stata, never uses `shell=True`, and writes no backtick (there is none to
  write). The fixture is re-added with `git add -f test/fixtures/stat_truth.json`.
- **TR-05.7** New test module `test/test_histogram_edge_rule.py` (TDD stubs below) covering:
  the CSV regressions, the seeded property test in Python and under node, the both-modes
  bar sums, the config keys, the unit test of `_histogram_counts` (its NaN precondition
  included), the missing-row drop, and the `start()` tolerance fold. Its imports (S03
  TR-03.1): `from js_runner import run_filter_js_block, NODE` and `from
  test_statistical_helpers import _hist`; node tests carry `@pytest.mark.skipif(NODE is None,
  reason="node is not installed; set DASH_NODE")`. `test/test_statistical_truth.py` gains
  `TestHistogramEdgeAgainstStata` reading section `histogram_edge` and the `_meta` stamp test.
- **TR-05.8** `test/function_test_map.py` gains, in alphabetical place among the
  `GlyphMapper.` keys (rule R2),
  `'GlyphMapper._histogram_counts': 'test/test_histogram_edge_rule.py::TestHistogramCounts::test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar'`.
- **TR-05.9** `test/test_histogram_spurious_bin.py`: rewrite the module docstring to state
  the new rule (the tolerance edge was removed by WP-28 C2; `bin(#)` gives # bars because the
  count folds, not because an edge is appended); rename `TestTheGuardStillGuards` to
  `TestEveryObservationIsCounted` and make its two tests count through
  `GM().map_histogram(..., {"frequency": "frequency", ...})` sums, keeping the same inputs.
- **TR-05.10** Certification (D11; no new script, no runner or pin edit):
  - `test/test_e2e_filters.cscript` gains the block `// ---- WP-28 C2: histogram edge rule
    (HE-01..HE-04) ----` immediately before its `// Cleanup` section: `sysuse nlsw88, clear`,
    then in `c(tmpdir)` HE-01 `dash histogram ttl_exp, bin(27) frequency saving(he1.html,
    replace)` rc 0; HE-02 the same with `bin(83)`; HE-03 `start(\`s')` with `local s =
    r(min)*(1+5e-6)` after `quietly summarize ttl_exp, meanonly`, rc 0; HE-04 `start(\`s2')`
    with `local s2 = r(min)*1.01` under `log using`, `_rc == 198` and `cert_log_has` for
    `option start() may not be larger than minimum of ttl_exp`. For HE-01..03,
    `cert_file_has "<file>", needle("top")` must find the column name, and a `python:` block
    (Stata's Python: `import json, re, base64, gzip, numpy`; `from sfi import Macro`) reads the
    file, finds `<script type="application/json"` as `test_html_verification.py:105-113`,
    walks the document for a ColumnDataSource whose `data` entries hold `top`, `left` and
    `right` (Bokeh 3 writes `data` as `{"type": "map", "entries": [[name, value], ...]}`),
    decodes `top` as `test_html_output.py:164-183` (`list`, or `ndarray` with base64 `bytes`,
    gzipped when `raw[:2] == b"\x1f\x8b"`), and `Macro.setGlobal("he_sum",
    str(int(round(sum))))` and `he_nbar`; then `assert ${he_sum} == 2246` and `${he_nbar}`
    equal to the bin count. Each case ends in `display "HE-0n PASS: ..."`, the script's own
    style; the block ends with `sysuse auto, clear` so the Cleanup section finds what it
    expects; the header comment's `Tests:` line (:4) gains `HE-01 through HE-04`.
  - `test/test_gaps2_truth.cscript` gains, above its last line and after S02's block, the
    block (the form of `sections/BRIEF.md` "Certification scripts", verbatim):
    ```
    * ==== S05 C2: histogram bars against twoway__histogram_gen ====
    local only : env GAPS2_ONLY
    if inlist("`only'", "", "S05") {
        display as text "S05 start `c(current_time)'"
        ... HE-05, HE-06 ...
        display as text "S05 end `c(current_time)'"
    }
    * ==== end S05 ====
    ```
    HE-05: `sysuse nlsw88, clear`; `twoway__histogram_gen ttl_exp, generate(zqh zqx) return
    frequency bin(27)`; keep `r(bin)`, `r(max)`; `summarize zqh, meanonly` → `r(sum) == 2246`;
    `dash histogram ttl_exp, bin(27) frequency saving(he5.html, replace)` in `c(tmpdir)`; the
    same `python:` decoder as HE-01 also writes the non-empty `top` values, in bar order, to
    `${he_tops}` (space-separated integers) and the last `right` edge to `${he_right}`; Mata
    compares `${he_tops}` with the non-missing `zqh` values in `zqx` order (`_gt_expect HE-05
    "(\`same' == 1)" ...`) and `${he_right}` with `r(max)` at `reldif < 1e-9`. HE-06: the
    same on `sysuse census` `pop` with `bin(75)` (sum 50). Both through `_gt_expect`/`_gt_done`
    (`HE-05 PASS: ...`); `drop zqh zqx`, `graph drop _all`, `dash clear` at the end.
- **TR-05.11** BUGS.md: one closed entry for C2 appended at the END of the file (D3), whose
  Description says the entry titled "A histogram start() above the variable's minimum was
  accepted and the rows below it silently dropped" (BUGS.md:1215) left the within-tolerance
  rows dropped and that this entry closes that residual, with `- Resolution: Fixed
  <ddmonyyyy> (WP-28, C2). <what changed, in which functions, in both renderers>. Pinned by
  test/test_histogram_edge_rule.py::TestNlsw88AndCensusRegressions::test_ttl_exp_bin_27_51_54_83_count_every_row,
  ::TestEveryFrequencyHistogramSumsToN::test_seeded_cases_sum_to_n_in_python_and_under_node,
  ::TestTheJavaScriptRecountAgrees::test_ttl_exp_bin_27_under_node_sums_to_2246,
  test/test_statistical_truth.py::TestHistogramEdgeAgainstStata::test_bars_match_the_generator,
  test/test_e2e_filters.cscript HE-01..HE-04, test/test_gaps2_truth.cscript HE-05..HE-06;
  fixture test/fixtures/stat_truth.json.`; CHANGELOG: the marker `<!-- WP-28 C2 -->` (in the
  `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change`, placed
  by S01) is replaced in place by one line ending `(WP-28, C2)` naming the command, the old
  value (2245 of 2246 rows on nlsw88 ttl_exp `bin(27)`; 49 of 50 on census pop `bin(75)`, the
  counts 05-01 recorded) and the new (every row); dash.sthlp's histogram paragraph
  (:2040-2052) gains the continuous rule in one sentence.
- **TR-05.12** Security (rule 1): the config's three new values are Python numbers computed
  from the data, never user text; the JavaScript reads them as numbers; no new text reaches
  HTML; the cscript's `python:` block reads the page it built and sets only integer globals.

## Boundaries

- Do not touch the discrete grid (`_histogram_grid` :9679-9702) or the discrete count's
  semantics; only its code is shared through `_histogram_counts`.
- Do not change dash.ado's `start()` check (:3827-3837) or its message; it is Stata's.
- Do not add `histogram` re-estimation to `_FILTER_JS` for by() or fits: C4/E4 are out of
  scope (PRD §7).
- Do not change `_histogram_heights`, `_stata_bin_count`, `_dash_histogram_ymode` or the
  `_MAX_BINS` warnings.
- Do not change the served template (:25760-26925): the served app redraws through the
  mapper and receives the config through `map_histogram`.
- Do not edit `test/fixtures/data/*.csv`; do not add a fixture outside `stat_truth.json`.
- Do not change `zq_curve`'s default `maxn(41)`; the new block passes `maxn(100)`.
- Do not print anything when a histogram is drawn (DISCOVERY Q22).
- Do not create a `.cscript` file, and do not edit `test/run_all_cscripts.do` or
  `test/test_cscript_hygiene.py` (D11; rule R1); do not touch the existing cases of
  `test_e2e_filters.cscript` or any other section's block of `test_gaps2_truth.cscript`.
- kdensity, the KPI, filter and date code, and every other section's function are out of
  scope.

## Stata truth

This section extends `scripts/extract_stat_truth.do` (TR-05.6) and regenerates
`test/fixtures/stat_truth.json` once (rule R5). The twoway command lines recorded:

```
sysuse nlsw88, clear
twoway__histogram_gen ttl_exp, generate(zqh zqx) return frequency bin(27)
twoway__histogram_gen ttl_exp, generate(zqh zqx) return frequency bin(51)
twoway__histogram_gen ttl_exp, generate(zqh zqx) return frequency bin(54)
twoway__histogram_gen ttl_exp, generate(zqh zqx) return frequency bin(83)
twoway__histogram_gen ttl_exp, generate(zqh zqx) return bin(27)                 // density
quietly summarize ttl_exp, meanonly
twoway__histogram_gen ttl_exp, generate(zqh zqx) return frequency bin(27) start(`=r(min)*(1+5e-6)')
sysuse census, clear
twoway__histogram_gen pop, generate(zqh zqx) return frequency bin(75)
```

with `equivalent_user_cmd` `histogram ttl_exp, frequency bin(27)` and the same for the other
six. Invocation (D6; the wrapper implements CLAUDE.md rule 10, sets `STATATMP=<scratch-dir>/tmp/`
with the trailing slash and caps concurrent Stata sessions at three; the script sets its own
directories through `ZQ_REPO`, so it is handed to the wrapper directly):

```
scripts/stata_slot.sh /tmp/dash-s05 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_stat_truth.do
```

The log lands in `/tmp/dash-s05/extract_stat_truth.log`; read it, never relaunch to check. It
must end with `WROTE .../stat_truth.json` and print `SELFCHECK
histogram_edge_frequency_sums_equal_N True`. `.git/info/exclude` hides `*.json`, so the
fixture is staged with `git add -f test/fixtures/stat_truth.json`;
`test/test_fixtures_are_committed.py` already finds it named by `test_statistical_truth.py`.
The regeneration rewrites the whole file: verify it record by record, never as "additions
only" (rule R5): `python3 -c "import json,subprocess; old=json.loads(subprocess.run(['git','show','HEAD:test/fixtures/stat_truth.json'],capture_output=True,text=True).stdout); new=json.load(open('test/fixtures/stat_truth.json')); old.pop('_meta'); new.pop('_meta'); new.pop('histogram_edge'); assert old==new, [k for k in old if old[k]!=new.get(k)]"` must print nothing (every pre-existing record is unchanged; the old `_meta` keys are present in the new `_meta` beside the four provenance keys). A changed value in another section means Stata or its data changed and must be reported, not committed silently.

**The certification scripts** (05-05) run through the two-line driver of `sections/BRIEF.md`
"Running one cscript" (`<repo>` is the root of the tree under test: this section's worktree
`<path>/wp28-s05`, or the main checkout when the merger reruns the script):

```
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_e2e_filters.cscript" > /tmp/dash-s05/run_test_e2e_filters.do
scripts/stata_slot.sh /tmp/dash-s05 /tmp/dash-s05/run_test_e2e_filters.do
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_gaps2_truth.cscript" > /tmp/dash-s05/run_test_gaps2_truth.do
GAPS2_ONLY=S05 scripts/stata_slot.sh /tmp/dash-s05 /tmp/dash-s05/run_test_gaps2_truth.do
```

(logs `/tmp/dash-s05/run_test_e2e_filters.log` and `/tmp/dash-s05/run_test_gaps2_truth.log`;
`GAPS2_ONLY=S05` runs only this section's block of the truth script; the batch's merger runs
the whole script once after the batch).

## TDD test stubs

The first six are the regression tests that fail at 91d97be. All new pytest stubs live in
`test/test_histogram_edge_rule.py` unless a file is named. The module imports `from
js_runner import run_filter_js_block, NODE` and `from test_statistical_helpers import _hist`
(S03 TR-03.1).

- **Test: `TestNlsw88AndCensusRegressions::test_ttl_exp_bin_27_51_54_83_count_every_row`**
  (parametrised over 27, 51, 54, 83). `_hist(ttl_exp, {"bin": str(n), "frequency":
  "frequency"})` from the CSV; assert `tops.sum() == 2246` exactly and `len(tops) == n`.
  Pre-fix failure: 2245.0 (the recorded defect), not an exception.
- **Test: `TestNlsw88AndCensusRegressions::test_census_pop_bin_75_counts_every_row`**:
  sum 50 and 75 bars. Pre-fix: 49.0.
- **Test: `TestNlsw88AndCensusRegressions::test_density_bars_integrate_to_one_on_ttl_exp_bin_27`**:
  `sum(top * (right-left)) == approx(1.0, abs=1e-12)` and the last bar's density is
  `count/(2246*h)` for the fold-corrected count. Pre-fix: the bars integrate to 1 over 2245
  rows, so the last bar's height differs from `1/(2246*h)`; assert that height.
- **Test: `TestNlsw88AndCensusRegressions::test_a_missing_value_row_is_dropped_before_counting`**
  (F-13; the guarantee `_layer_weights` → `_masked` gives): `_hist([1.0, float("nan"), 2.0,
  3.0], {"bin": "3", "frequency": "frequency"})` sums to 3 and draws 3 bars, in the mapper;
  and a served build over the same four rows (the `TestBothModes` helpers) sums to 3.
  Pre-fix: passes (a guard for BR-05.8; its non-vacuity is the mutation table's).
- **Test: `TestTheJavaScriptRecountAgrees::test_ttl_exp_bin_27_under_node_sums_to_2246`**:
  `run_filter_js_block("histogram", r._dash_agg_config, ttl_exp)` (S03's runner); assert
  `sum(got["top"]) == 2246` and `got["top"] == tops`. Pre-fix: 2245 (the `v > edges[last]`
  skip). Skips only when node is absent (`NODE is None`), the reason naming `DASH_NODE`.
- **Test: `TestBothModes::test_the_served_app_draws_the_same_2246_bars`**: a spec with one
  `histogram ttl_exp, bin(27) frequency` over `conftest.make_data_json` of nlsw88; saved
  through `dr.DashRenderer(sp, dp).render()` and served through
  `dr.ServerAppBuilder(sp, dp).build(ap)` + `make_document(Document())` (the
  `test_mode_parity._standalone`/`_served` pattern :210-247); read each mode's histogram
  renderer (`"left" in data_source.data`, as `_served_bars` :2313-2332 finds it); assert both
  `top` arrays sum to 2246 and are equal. Pre-fix: 2245 in both.
- **Test: `TestStartTolerance::test_rows_below_a_tolerated_start_land_in_bar_zero`**:
  `start = ttl_exp.min()*(1+5e-6)` (reldif < 1e-5, what dash.ado admits); `bin(27)
  frequency`; assert the sum is 2246, `left[0] == start`, and bar 0 holds the rows with
  `v < start` plus those in `[start, start+h)`. Pre-fix: those rows are dropped.
- **Test: `TestEveryFrequencyHistogramSumsToN::test_seeded_cases_sum_to_n_in_python_and_under_node`**
  (the property test): `rng = np.random.RandomState(20260925)`; 40 cases; each draws
  `N in 1..500`, values `rng.normal(loc, scale)` rounded to `k in 0..3` decimals (ties on
  edges), options one of `bin(b)` with `b in 1..100`, `width(w)` with `w` a rounded fraction
  of the range, `start(min*(1+5e-6)) bin(b)`, `start(...) width(w)`, and every fifth case
  with fweights `rng.randint(1, 4, N)`; assert `tops.sum() == N` (or the weight total),
  `len(tops) == bin` when `bin()` was given, `right[-1] == approx(left[0] + h*len(tops))`,
  and the node run (`run_filter_js_block`) returns the same `top` array. Pre-fix: at least
  one case drops a row (GAPS2 measured about 4%); assert at the end that every case ran (no
  silent `continue`).
- **Test: `TestHistogramCounts::test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar`**
  (rule 3, the new function): `_histogram_counts(np.array([-0.5, 0, 0.5, 2.0, 2.0000000001]),
  None, 0.0, 1.0, 2)` gives `[3, 2]`; with weights `[1,1,1,2,3]` gives `[3, 5]`. Pre-fix:
  `AttributeError` (shape failure; its non-vacuity rests on the mutation table).
- **Test: `TestHistogramCounts::test_a_nan_in_arr_is_refused_not_miscounted`** (F-13):
  `_histogram_counts(np.array([0.5, float("nan")]), None, 0.0, 1.0, 2)` raises `ValueError`
  whose text names `_layer_weights`; the same with `w = np.array([1.0, float("nan")])` and a
  finite `arr` raises too. Pre-fix: `AttributeError`.
- **Test: `TestTheAggConfigCarriesTheRule::test_start_width_and_bin_are_numbers_the_page_can_read`**:
  after `map_histogram` the config has `start`, `width`, `bin` as `float`, `float`, `int`,
  `width > 0`, `bin == len(bin_edges) - 1`, and `discrete` is still present. Pre-fix:
  `KeyError`.
- **Test: `test/test_statistical_truth.py::TestHistogramEdgeAgainstStata::test_bars_match_the_generator`**
  (parametrised over the seven `histogram_edge` keys; written in 05-02): `_rec(truth,
  "histogram_edge", key)`; build the options from the key (`bin`, `frequency` unless
  `_density`, `start` = `rec["start_requested"]` for `_start`); assert `rec["rc"] == 0`,
  `len(tops) == rec["bin"]`, `left[0] == approx(rec["start"], rel=1e-12)`, `right[-1] ==
  approx(rec["xmax"], rel=1e-12)`, `tops[tops > 0]` equals `_series(rec, "bar_height")` with
  its trailing `null` (the `start()` row, :232-235) dropped, at `rtol=1e-9` for density and
  exactly for frequency, the drawn midpoints `(left+right)/2` at the non-empty bars equal
  `bin_midpoint`, and for the frequency keys `tops.sum() == rec["sum_height"] == rec["N"]`.
  Pre-fix (once the fixture exists): 2245 against Stata's 2246 for the four ttl_exp keys, 49
  against 50 for census.
- **Test: `test/test_statistical_truth.py::TestHistogramEdgeAgainstStata::test_the_fixture_holds_the_seven_edge_probes`**:
  the section has exactly the seven keys and every `rc` is 0, so a regenerated fixture that
  lost one fails rather than shrinking the parametrisation.
- **Test: `test/test_statistical_truth.py::TestHistogramEdgeAgainstStata::test_the_meta_stamp_holds_the_four_provenance_keys`**
  (D12): `truth["_meta"]` has `stata_version`, `born_date`, `dash_commit` (matching
  `[0-9a-f]{40}`) and `extracted`, each a non-empty string, and still has `run_date`,
  `counts` and `self_checks`; nothing is compared with the running Stata or the current
  commit.
- cscript cases: `test/test_e2e_filters.cscript` HE-01 (`bin(27)`, the page's decoded `top`
  sums to 2246 over 27 bars), HE-02 (`bin(83)`, 2246 over 83), HE-03 (a tolerated `start()`,
  rc 0, 2246), HE-04 (`start()` above the tolerance, r(198) with twoway's words);
  `test/test_gaps2_truth.cscript` block S05: HE-05 (nlsw88 ttl_exp `bin(27)`: the page's bars
  equal `twoway__histogram_gen`'s live, bar for bar, and the last right edge equals `r(max)`),
  HE-06 (census pop `bin(75)`: the same, sum 50).

**Pinned tests to revise (not delete):** `test/test_histogram_spurious_bin.py` module
docstring and `TestTheGuardStillGuards` (TR-05.9). No existing assertion inverts.

**Mutation table — proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| in `_histogram_counts`, drop the `np.clip` | `test_ttl_exp_bin_27_51_54_83_count_every_row` (bincount grows to 28 entries; the source columns disagree in length) |
| in `_histogram_counts`, clip to `0, nb` | `test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar` |
| in `_histogram_counts`, drop the finiteness check | `test_a_nan_in_arr_is_refused_not_miscounted` |
| in `_masked`, drop the joint NaN filter | `test_a_missing_value_row_is_dropped_before_counting` (the NaN reaches the count and `_histogram_counts` raises) |
| restore `np.histogram` in the continuous branch | every regression above; `test_the_discrete_recount_folds_the_top_value_as_python_does` stays green (discrete was already right) |
| restore the tolerance edge in `_histogram_grid` | `test_seeded_cases_sum_to_n_in_python_and_under_node` (`len(tops) == bin` on a case whose last edge lands below the maximum) and `test_bars_match_the_generator[nlsw88:ttl_exp:bin27]` (`right[-1]` ≠ `r(max)`) |
| in `_FILTER_JS`, keep `if (v < edges[0] \|\| v > edges[last]) continue;` | `test_ttl_exp_bin_27_under_node_sums_to_2246` |
| in `_FILTER_JS`, read `bw` from the edges instead of `ac.width` | `test_seeded_cases_sum_to_n_in_python_and_under_node` on a `start()` case where `(edges[n]-edges[0])/n` ≠ `ac.width` by an ULP |
| omit `"width"` from the config | `test_start_width_and_bin_are_numbers_the_page_can_read`, then every node test (zero counts) |
| in the extract script's python block, drop `dash_commit` | `test_the_meta_stamp_holds_the_four_provenance_keys` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| ttl_exp bin(27/51/54/83) sums to 2246; pop bin(75) to 50 | pytest | data/nlsw88.csv, data/census.csv | saved (mapper); served in `TestBothModes` |
| Density integrates to 1 over 2246 rows | pytest | data/nlsw88.csv | mapper |
| A missing row is dropped before the count | pytest | none | both |
| JS recount equals Python | pytest + node (`js_runner.run_filter_js_block`) | data/nlsw88.csv | saved page's JS |
| Seeded property, 40 cases, Python and node | pytest + node | none (seeded) | saved page's JS and mapper |
| `start()` within tolerance folds into bar 0 | pytest | data/nlsw88.csv | mapper |
| `_histogram_counts` contract and NaN precondition | pytest | none | n/a |
| Config carries start/width/bin | pytest | none | saved registry |
| Stata's generator output, seven keys; the `_meta` stamp | pytest | stat_truth.json `histogram_edge`, `_meta` | mapper |
| Fixture completeness | pytest | stat_truth.json | n/a |
| Page built by dash: decoded `top` sums to 2246; `start()` tolerated and refused | cscript block HE-01..HE-04 in `test_e2e_filters.cscript` (Stata's Python) | nlsw88 (sysuse) | saved page |
| Page bars equal `twoway__histogram_gen` live, bar for bar | cscript block S05 (HE-05, HE-06) in `test_gaps2_truth.cscript` | nlsw88, census (sysuse) | saved page |
| Served names | pytest `TestTheServedAppCarriesEveryName` | none | served |
| Full suite once in the worktree | `python3 -m pytest test/ -q` | all | both |

Acceptance criteria:

- **AC-05.1** The four ttl_exp cases and the census case sum to N in the mapper, in the
  served document and under node; before the fix they sum to N-1.
- **AC-05.2** 40 of 40 seeded cases sum to N (or the weight total), draw exactly `bin` bars
  when `bin()` is given, and agree bar for bar with node.
- **AC-05.3** `stat_truth.json` carries `histogram_edge` with seven keys, rc 0, the self-check
  `histogram_edge_frequency_sums_equal_N` true and the four `_meta` provenance keys beside
  its existing ones; every pre-existing record outside `_meta` is unchanged;
  `TestHistogramEdgeAgainstStata` is green.
- **AC-05.4** `test_e2e_filters.cscript` passes with HE-01 sum 2246 on the built page, HE-02
  `bin(83)` sum 2246, HE-03 `start()` within tolerance rc 0 and sum 2246, HE-04 `start()`
  above tolerance rc 198 with `option start() may not be larger than minimum of ttl_exp`;
  `test_gaps2_truth.cscript` block S05 passes HE-05 and HE-06 (run alone with
  `GAPS2_ONLY=S05`); no new script, runner block or pin.
- **AC-05.5** The full pytest suite is green once in the worktree before the section's one
  commit on `wp28-s05` (subject ending `(GAPS2 C2)`), with no skip attributable to this
  section (node is installed); `function_test_map` names `_histogram_counts`.
- **AC-05.6** BUGS.md holds the closed C2 entry at its end, `- Resolution: Fixed <ddmonyyyy>
  (WP-28, C2). ...`, naming its tests and closing the :1215 residual by reference; the
  `<!-- WP-28 C2 -->` marker is replaced in place by a line ending `(WP-28, C2)` and
  `grep -c '<!-- WP-28 C2 -->' CHANGELOG.md` prints 0; dash.sthlp updated.

## Tasks

Commit boundary: **one commit (C2)** holding 05-01 to 05-06, made by 05-06 on the worktree branch `wp28-s05`, subject ending `(GAPS2 C2)`, body per S01 TR-01.9 opening with the saved failure text; the full pytest suite runs green once in the worktree before it (CLAUDE.md rules 4 and 11); the merger lands the commit onto `s3-bugs` with that message (`sections/index.md` step 1). No task before 05-06 commits. Every Stata run goes through `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6); a cscript through the two-line driver under "Stata truth". No full cert-suite run here (S19). No AI references anywhere.

<task type="auto" id="05-01">
  <name>Write the failing histogram edge tests</name>
  <files>test/test_histogram_edge_rule.py</files>
  <action><![CDATA[
    Create `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_histogram_edge_rule.py` with tests only; do not touch `dash_render.py`. Module docstring: the defect in CHANGELOG terms (`dash histogram ttl_exp, bin(27)` drew 2245 of 2246 rows, `histogram pop, bin(75)` 49 of 50; Stata counts `floor((v - start)/h)` clamped to the grid, twoway__histogram_gen.ado:200-203). Header as `test/test_statistical_helpers.py:11-24` (`import dash_render as dr`, `GM = dr.GlyphMapper`), plus `from js_runner import run_filter_js_block, NODE` (S03 TR-03.1), `from test_statistical_helpers import _hist` and `from conftest import make_data_json`; load `test/fixtures/data/nlsw88.csv` and `census.csv` with pandas at module level. Write every stub named in "TDD test stubs" except the three `TestHistogramEdgeAgainstStata` tests (task 05-02): `TestNlsw88AndCensusRegressions` (four tests, the missing-row guard included), `TestTheJavaScriptRecountAgrees`, `TestBothModes` (helpers modelled on `test_mode_parity.py:200-247`, writing the spec and data JSON under `tmp_path`), `TestStartTolerance`, `TestEveryFrequencyHistogramSumsToN` (seeded with `np.random.RandomState(20260925)`, 40 cases, a module-level `_CASES` list so the coverage claim is visible, and a final assertion that 40 cases ran), `TestHistogramCounts` (both tests) and `TestTheAggConfigCarriesTheRule`. Node tests carry the `@pytest.mark.skipif(NODE is None, ...)` marker with the reason text of TR-05.7, and nothing else skips. Run the file against the unmodified tree. Do not commit: save the failure summary (the 2245/49 lines, the `AttributeError`/`KeyError` lines) to the scratch directory as `05-01-failure.txt`; it becomes the opening paragraph of the C2 commit (S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_histogram_edge_rule.py -q 2>&1 | tail -25` shows exactly one passed (`test_a_missing_value_row_is_dropped_before_counting`, the guard) and every other test failing; `python3 -m pytest test/test_histogram_edge_rule.py -q -k "bin_27_51_54_83" 2>&1 | grep -c "2245"` prints a non-zero count, and `-k census` shows `49`; `python3 -m pytest test/test_histogram_edge_rule.py -q -k HistogramCounts 2>&1 | grep -c AttributeError` is non-zero; `grep -c "from test_statistical_helpers import _hist$" test/test_histogram_edge_rule.py` prints 1; `<scratch>/05-01-failure.txt` exists.]]></verify>
  <done>The new module existed, collected cleanly through S03's runner names, and every regression test in it failed -- the behavioural tests with 2245 or 49 where 2246 or 50 was asserted, the API-shape tests with AttributeError or KeyError -- with dash_render.py unmodified and nothing committed.</done>
</task>

<task type="auto" id="05-02">
  <name>Record Stata's edge-case truth and pin it</name>
  <files>scripts/extract_stat_truth.do, test/fixtures/stat_truth.json, test/test_statistical_truth.py</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_stat_truth.do` add "LAYER 1c -- histogram edge rule (WP-28 C2)" after layer 1's closing brace (about :380, before the layer-2 banner), written per TR-05.6: a local list of seven cases `dataset|var|variant|opts`, each loaded with `sysuse`, run as `capture twoway__histogram_gen \`var', generate(zqh zqx) return \`opts'`, recording `rc` first and `continue`-ing on failure, then `bin start width xmin xmax N n_x` via `zq_n`, `type`, `cmd` and `equivalent_user_cmd` via `zq_s`, `sum_height` from `summarize zqh, meanonly` (`r(sum)`), `start_requested` for the `bin27_start` case (the local computed as `r(min)*(1+5e-6)` after `summarize ttl_exp, meanonly`), then `preserve`/`keep zqh zqx`/`drop if missing(zqx)`/rename to `bar_height bin_midpoint`/`zq_curve bin_midpoint bar_height, sec(histogram_edge) key(\`key') maxn(100)`/`restore`, exactly as :338-346 do for layer 1. Loop headers must not contain `${...}` (the file's own note at :56-58). Add the D12 provenance step to the header (`tempfile gitrev`, `shell git -C "${ZQ_REPO}" rev-parse HEAD`, `local dash_commit`, asserted 40 hexadecimal characters). In the trailing `python:` block add `"histogram_edge"` to the section tuple (:2779-2787), `histogram_edge_probes` to `_meta.counts`, the four `_meta` keys `stata_version`, `born_date`, `dash_commit` (through `Macro.getLocal("dash_commit")`), `extracted` beside the existing `run_date`/`counts`/`self_checks`, and the self-check `histogram_edge_frequency_sums_equal_N` beside `histogram_bin_rule_reproduces_stata` (about :2694): true when every `histogram_edge` record with `type == "frequency"` has `sum_height == N`; add `"start_requested"` nowhere in `NEVER_NUM` (it is numeric). Run `scripts/stata_slot.sh /tmp/dash-s05 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_stat_truth.do`, read the log's tail for `WROTE` and the SELFCHECK line, run the record-by-record comparison of "Stata truth" (it must print nothing), then `git add -f test/fixtures/stat_truth.json` (staging only). In `test/test_statistical_truth.py` add `TestHistogramEdgeAgainstStata` after `TestHistogramAgainstStata` (:177) with the three tests named in the stubs, using `_rec`, `_need`, `_series`, `mapper` and the `datasets` x columns (`datasets["nlsw88"][1]` is ttl_exp, `datasets["census"][1]` is pop). Run the file; the four ttl_exp keys and census fail with 2245/49 against the fixture's 2246/50; append that to `<scratch>/05-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`tail -40 /tmp/dash-s05/extract_stat_truth.log` shows `WROTE .../stat_truth.json` and `SELFCHECK histogram_edge_frequency_sums_equal_N True`; `python3 -c "import json;d=json.load(open('test/fixtures/stat_truth.json'));print(sorted(d['histogram_edge']), sorted(k for k in d['_meta'] if k in ('stata_version','born_date','dash_commit','extracted','run_date')))"` lists the seven keys and the five `_meta` names; the record-by-record comparison prints nothing; `git diff --stat` touches only the three files; `python3 -m pytest test/test_statistical_truth.py -q -k HistogramEdge 2>&1 | tail -12` shows `test_the_fixture_holds_the_seven_edge_probes` and `test_the_meta_stamp_holds_the_four_provenance_keys` passing and five `test_bars_match_the_generator` cases failing on the sum (2245 vs 2246, 49 vs 50) while the two `bin27_start`/`bin27_density` cases fail for the same missing row.]]></verify>
  <done>stat_truth.json carried a `histogram_edge` section of seven Stata-measured records whose frequency sums equalled N and the four provenance keys beside its old ones, every pre-existing record was unchanged, the extract script reproduced it, and test_statistical_truth.py pinned them with tests that failed on the unmodified mapper for the recorded reason, nothing committed.</done>
</task>

<task type="auto" id="05-03">
  <name>Count with Stata's floor-and-clamp in both languages</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py`: (1) add `@staticmethod def _histogram_counts(arr, w, start, width, nb)` immediately before `_histogram_grid` (:9629) with a docstring citing twoway__histogram_gen.ado:200-203 and the finiteness precondition of TR-05.1 (the `ValueError` naming `_layer_weights`), and the body of TR-05.1; (2) in `map_histogram` replace the `if discrete and len(arr): ... else: counts, _ = np.histogram(...)` fork (:9559-9571) with the one block of TR-05.3 calling `self._histogram_counts(arr, w, start, h, nb)`, keeping `discrete = bool(...)` for the config, and extend `r._dash_agg_config` (:9607-9623) with `"start": start`, `"width": h`, `"bin": nb` and a comment saying the page's recount reads these three rather than rebuilding `h` from the edges (TR-05.4); (3) in `_histogram_grid` delete :9751-9764 (the comment and the tolerance edge) and replace the comment with two lines: the last edge is `start + width*n_bins`, Stata's `r(max)`, and a value at or floating above it is folded into the last bar by `_histogram_counts`; update the method docstring's precedence paragraph to say so (TR-05.2); (4) in `_FILTER_JS` (:14768-14834) replace :14800 and :14808-14826 with the single floor-and-clamp of TR-05.5 reading `ac.start`, `ac.width`, `ac.bin`, guarded by `if (!(ac.width > 0)) { /* leave the counts at zero */ }` before the loop, and reword the comment to cite twoway__histogram_gen.ado:200-203 for both branches; touch no line above `if (ac.type === 'histogram')` (S17's region). Then add the function-map entry of TR-05.8 to `test/function_test_map.py` in alphabetical place among the `GlyphMapper.` keys (rule R2). Line numbers above are pre-edit; locate by symbol.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_histogram_edge_rule.py test/test_statistical_truth.py test/test_statistical_helpers.py test/test_histogram_spurious_bin.py test/test_resource_limits.py test/test_mode_parity.py test/test_function_test_map.py -q 2>&1 | tail -5` reports no failures; `grep -c "np.histogram(" dash_render.py` prints 0; `grep -n "v > edges\[edges.length - 1\]" dash_render.py` prints nothing; `python3 -c "import dash_render as d,numpy as np;print(d.GlyphMapper._histogram_counts(np.array([-0.5,0,0.5,2.0,2.0000000001]),None,0.0,1.0,2).tolist())"` prints `[3.0, 2.0]`; `python3 -c "import dash_render as d,numpy as np;d.GlyphMapper._histogram_counts(np.array([0.5,np.nan]),None,0.0,1.0,2)" 2>&1 | grep -c "_layer_weights"` prints 1.]]></verify>
  <done>Both branches of map_histogram counted through `_histogram_counts` with its finiteness precondition, the tolerance edge was gone, the config carried start/width/bin, the saved page's JavaScript applied the same rule from those numbers, and every test of 05-01 and 05-02 passed.</done>
</task>

<task type="auto" id="05-04">
  <name>Revise the spurious-bin file's contract</name>
  <files>test/test_histogram_spurious_bin.py</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_histogram_spurious_bin.py` rewrite the module docstring per TR-05.9: keep the measured history (bin(6)/bin(12) drew a 7.105e-15-wide spike), state that WP-28 C2 removed the tolerance edge altogether because the count now folds a value at or above the last edge into the last bar (twoway__histogram_gen.ado:200-203), and that `bin(#)` therefore gives # bars by construction. Rename `TestTheGuardStillGuards` to `TestEveryObservationIsCounted`; keep its three inputs and turn the two coverage tests into frequency-sum assertions through `dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color")).map_histogram(figure(), ColumnDataSource({"v": arr.tolist()}), "v", {..., "frequency": "frequency"})` (imports as `test_statistical_helpers.py:18-19`), asserting `tops.sum() == len(arr)` and, for the `start(0) width(3)` case, `right[-1] == 12.0` (Stata's `r(max) = 0 + 3*4`). Leave `TestBinCountIsWhatWasAsked` as it is. Run this file and the histogram files only (the full suite is 05-06's one run); record the rename as a `Flipped:` line in the commit-message draft (old expectation: the instrument, not a value).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_histogram_spurious_bin.py test/test_histogram_edge_rule.py -q 2>&1 | tail -3` passes; `grep -c "np.histogram" test/test_histogram_spurious_bin.py` prints 1 or less (the one in `test_no_bar_is_a_degenerate_spike` may stay); `grep -c "TestEveryObservationIsCounted" test/test_histogram_spurious_bin.py` prints 1.]]></verify>
  <done>The spurious-bin file documented the floor-and-clamp contract and asserted it through the mapper, with the rename recorded for the commit message.</done>
</task>

<task type="auto" id="05-05">
  <name>Certify the built page against twoway's bars</name>
  <files>test/test_e2e_filters.cscript, test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_e2e_filters.cscript` insert, immediately before the `// Cleanup` section, the block `// ---- WP-28 C2: histogram edge rule (HE-01..HE-04) ----` of TR-05.10: `sysuse nlsw88, clear`, the four cases in `c(tmpdir)` in the script's own `assert` + `display "HE-0n PASS: ..."` style, the `python:` block that decodes `top` from the built page (as `test_html_verification.py:105-113` finds the script tag and `test_html_output.py:164-183` decodes the column) into `${he_sum}`/`${he_nbar}`, `cert_log_has` for HE-04's refusal text, and `sysuse auto, clear` at the block's end; extend the header's `Tests:` line (:4). No new script, no runner or pin edit, no new `SKIP ... Python` line (the script already gates at :24-27). In `test/test_gaps2_truth.cscript` append, above the line `* ==== append new blocks above this line ====` and after S02's block, the block of TR-05.10 (`* ==== S05 C2: histogram bars against twoway__histogram_gen ====` ... `* ==== end S05 ====`, the `GAPS2_ONLY` guard and the `S05 start`/`S05 end` lines verbatim) holding HE-05 and HE-06 through `_gt_expect`/`_gt_done`, comparing the page's decoded bars with `twoway__histogram_gen`'s `zqh`/`zqx` in Mata and the last right edge with `r(max)`, and add the block to the script's header list; the block ends with `drop zqh zqx`, `graph drop _all`, `dash clear`. Run both scripts through the drivers of "Stata truth" (`run_test_e2e_filters.do`; `run_test_gaps2_truth.do` with `GAPS2_ONLY=S05`) and read the two logs.
  ]]></action>
  <verify><![CDATA[`grep -c "HE-0[1-4] PASS" /tmp/dash-s05/run_test_e2e_filters.log` prints 4, the log shows `2246` for HE-01, HE-02 and HE-03, the r(198) text for HE-04 and ends with `All filter widget E2E tests PASSED.`; `/tmp/dash-s05/run_test_gaps2_truth.log` shows `S05 start`, `HE-05 PASS`, `HE-06 PASS`, `S05 end` and the script's ALL CHECKS PASSED line, with `grep -c '^r([0-9]*);' /tmp/dash-s05/run_test_gaps2_truth.log` printing 0; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -3` passes with its pins untouched; `git diff --stat -- test/run_all_cscripts.do test/test_cscript_hygiene.py` prints nothing.]]></verify>
  <done>Two existing certification scripts proved, from the page's own embedded data, that all 2246 rows were counted with bin(27), bin(83) and a tolerated start(), that a start() above the tolerance was refused with twoway's words, and that the page's bars equalled `twoway__histogram_gen`'s bar for bar, with no new script, runner block or pin.</done>
</task>

<task type="auto" id="05-06">
  <name>Close C2 in the tracking documents</name>
  <files>BUGS.md, CHANGELOG.md, dash.sthlp</files>
  <action><![CDATA[
    Append at the end of `/Users/billy/Desktop/Programs/StataPrograms/d/dash/BUGS.md` (S01 TR-01.8; never mid-file) the closed entry `- [x] Title: A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above` with File Names and Line Numbers (`dash_render.py GlyphMapper.map_histogram (np.histogram on the continuous edges), GlyphMapper._histogram_grid (the tolerance edge), _FILTER_JS (the range test)`), Description (GAPS2 C2's measured symptom: nlsw88 ttl_exp bin(27|51|54|83) 2245 of 2246, census pop bin(75) 49 of 50, the rows below a start() within reldif 1e-5 dropped; the residual of the entry titled "A histogram start() above the variable's minimum was accepted and the rows below it silently dropped" at BUGS.md:1215), Suggested fix (Stata's floor-and-clamp, twoway__histogram_gen.ado:200-203, in Python and in the page's recount), and the Resolution line of TR-05.11 verbatim: `- Resolution: Fixed <ddmonyyyy> (WP-28, C2). Every histogram counts each observation in bar floor((v - start)/width) clamped to the grid, in GlyphMapper._histogram_counts (both renderers redraw through the mapper) and in _FILTER_JS's recount from the config's start/width/bin; the tolerance edge is gone. Pinned by <the tests and cases TR-05.11 lists>; fixture test/fixtures/stat_truth.json.` (the title holds no `"`). In `CHANGELOG.md` replace the marker `<!-- WP-28 C2 -->` -- it sits in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change`, placed by S01 -- in place with one line ending `(WP-28, C2)`: a continuous `histogram` could drop the observation at its last bin edge when the computed edge fell a few units in the last place below the maximum, and the rows a tolerated `start()` lay above; `dash histogram ttl_exp, bin(27)` on nlsw88 counted 2245 of 2246 rows and `histogram pop, bin(75)` on census 49 of 50 (the counts 05-01 recorded), with the density bars scaled to the rows that remained; every observation is now counted as Stata counts it, bar `floor((v - start)/width)` clamped to the grid, in the page and after a filter move (2246 and 50). Add nothing anywhere else in CHANGELOG.md. In `dash.sthlp` extend the histogram paragraph (:2040-2052) with one sentence after "as Stata counts it.": on every histogram each observation is counted in bar floor((v - start)/width), a value at or past the last edge in the last bar and one below a tolerated start() in the first, as twoway__histogram_gen counts them. Run the full pytest suite once in the worktree, `python3 -m pytest test/ -q` (CLAUDE.md rules 4 and 11; the merger's `git merge --no-edit main` and pre-commit run are `sections/index.md` step 1); fix any regression in the code, never by weakening a test. Grep the three edits and the message draft for `claude` and `anthropic` (nothing may match). Commit the whole section as ONE commit on the worktree branch `wp28-s05`; the merger lands it onto `s3-bugs` with this message (`sections/index.md` step 1): subject ending `(GAPS2 C2)`, body opening with `<scratch>/05-01-failure.txt` and carrying the S01 TR-01.9 lines (`Regression:` per regression test with its 2245/49 text, `Flipped: test/test_histogram_spurious_bin.py::TestTheGuardStillGuards -- counted with np.histogram on the returned edges, which the removed tolerance edge made true; now TestEveryObservationIsCounted through the mapper`, `Fixture: test/fixtures/stat_truth.json (scripts/extract_stat_truth.do)`, `BUGS.md: "A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above" (closed)`). The merge command into `main` is S19's to report; do not run any merge.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q 2>&1 | tail -3` passes; `grep -n "dropped the observation at its last edge" BUGS.md CHANGELOG.md` finds both; `tail -12 BUGS.md | grep -c "Resolution: Fixed .* (WP-28, C2)"` prints 1; `grep -c '<!-- WP-28 C2 -->' CHANGELOG.md` prints 0 and `awk '/^### Results that change/{f=1;next} /^### /{f=0} f' CHANGELOG.md | grep -c '(WP-28, C2)'` prints 1; `grep -n "floor((v - start)/width)" dash.sthlp` finds the help sentence; `python3 -m pytest test/ -q 2>&1 | tail -5` reports no failures; `git log -1 --format=%s | grep -c '(GAPS2 C2)'` prints 1; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0; `git rev-parse --abbrev-ref HEAD` prints `wp28-s05`; `git status --short` prints nothing.]]></verify>
  <done>C2 was recorded closed at the end of BUGS.md naming its tests and closing the start() residual by reference, the C2 marker was replaced in place by the line quoting the old and new counts, the help stated the continuous counting rule, and one green commit on `wp28-s05` carried the whole section for the merger.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" exists and passes; the regression tests are recorded as
  failing at 91d97be in the C2 commit's message (from `<scratch>/05-01-failure.txt`).
- `grep -c "np.histogram(" dash_render.py` is 0; `_histogram_counts` exists with its
  finiteness precondition and is named in `test/function_test_map.py`.
- `stat_truth.json` holds the seven `histogram_edge` records with rc 0, the self-check true
  and the four `_meta` provenance keys beside its existing ones; every pre-existing record is
  unchanged; `git ls-files test/fixtures/stat_truth.json` lists it.
- `test_e2e_filters.cscript` (HE-01..HE-04) and the S05 block of `test_gaps2_truth.cscript`
  (HE-05, HE-06) pass through the driver and the wrapper; no `.cscript` was created and
  neither the runner nor the hygiene pins changed.
- One commit on `wp28-s05`, subject ending `(GAPS2 C2)`, holding the failing tests, the fix,
  the revision, the fixture, the cscript blocks and the closed BUGS.md entry; no test-only
  commit exists (D1); the full suite was green once in the worktree before it.
- BUGS.md (D3 form, at the end), CHANGELOG.md (the C2 marker replaced in place, ending
  `(WP-28, C2)`) and dash.sthlp carry the C2 closure; no AI reference anywhere.
- No file outside the six tasks' file lists is modified.

## Notes

- **The two counters must read the same numbers.** Python computes `h` from the edges it
  built; the config ships that `h`, `start` and `nb`; the JavaScript must not recompute
  anything from `bin_edges`. The property test's `start()` cases are where an
  edges-derived `bw` differs by an ULP and moves a value across a bar.
- **NaN never reaches the count.** `_layer_weights` → `_masked` drops every row where the
  plotted column or the weight is NaN (dash_render.py:9551, :7843); `_histogram_counts`
  refuses a NaN with a `ValueError` naming that guarantee, so a future caller that skips
  `_layer_weights` fails loudly instead of miscounting.
- **`zq_curve maxn(41)`.** Layer 1 records long curves at 11 sampled indices. The new block
  passes `maxn(100)` so the 83-bar case is stored whole; the record's `n_points` equals
  `n_x` and, for a `start()` case, `n_x + 1` (the appended `x = start` row with a `null`
  height, twoway__histogram_gen.ado:232-235). Drop the trailing `null` before comparing.
- **`start()` in the fixture.** Stata's `r(start)` is the value used; the do-file computes
  it from `r(min)` and records the literal it passed as `start_requested`; the pytest passes
  `start_requested` as the option and compares `left[0]` to `r(start)`.
- **Bokeh embeds arrays as base64.** In the saved page a ColumnDataSource column is
  `{"type": "ndarray", "array": {"type": "bytes", "data": "..."}, "dtype": "float64",
  "shape": [n], "order": "little"}`, gzipped when smaller. `cert_file_has` can find the
  column name `top` but cannot sum it; the cscript blocks decode in a `python:` block, the
  pattern of `test/test_help_claims_4.cscript:415-430` (`Macro.setGlobal`) and
  `test/test_html_output.py:164-183` (`_column`). Neither block uses a `capture python:`
  probe (the :315 pin; `TestTheAvailabilityGuardIsReliable`).
- **Shared registries (rules R1-R6).** R1: no cscript is created; HE-01..04 join
  `test_e2e_filters.cscript` and HE-05..06 are the S05 block of `test_gaps2_truth.cscript`,
  appended above its last line after S02's block and before S13's, S14's, S15's, S16's,
  S17's and S18's (section order); the runner and the pins are S02's. R2: the
  `function_test_map.py` key goes in alphabetical place; `_FILTER_JS` is shared with S04
  (a prefix on `_DASH_FILTER_MASK_JS`) and S17 (the aggregate block above the histogram
  branch): merge order S04, S05, S13, S17, S16, S14 (`sections/index.md` step 2); a rejected
  hunk is applied by hand keeping both edits. R3: the C2 marker only, the help paragraph
  2040-2052 only, the BUGS.md entry at the end. R5: `stat_truth.json` is regenerated once,
  here (S17 writes its own `filter_truth.json`); never patched by hand; checked record by
  record. R6: no parity corpus edit.
- **Commit body** uses S01 TR-01.9's line forms verbatim: `Regression: test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>` (one per regression test, with the 2245/49 numbers), `Flipped: <node> -- <old expectation> was wrong because <why>` (the spurious-bin rename), `Fixture: test/fixtures/stat_truth.json (scripts/extract_stat_truth.do)`, `BUGS.md: "<title>" (closed)`. The commit is made on `wp28-s05` and landed on `s3-bugs` by the merger (`sections/index.md` step 1).
- **Stata's Python.** The cscripts' `python:` blocks run under `c(python_exec)`
  (`/opt/anaconda3/bin/python3`, numpy available). Many concurrent Stata sessions can drop
  `python_exec` from `~/.stata19/console/stata19.rc`, after which every Python cscript
  SKIPs: the wrapper keeps to three sessions, and on a run of SKIPs check `c(python_exec)`
  before trusting them (`set python_exec /opt/anaconda3/bin/python3, permanently` restores
  it).
- **Stata invocation.** The extract script is handed to `scripts/stata_slot.sh` directly
  (it sets `ZQ_REPO` itself); each cscript runs through the two-line driver of "Stata
  truth" (`sections/BRIEF.md` "Running one cscript"); `GAPS2_ONLY=S05` limits the truth
  script to this section's block; never the GUI, never a bare `stata-mp`, never the full
  cert suite inside a section (S19).
- **Regenerating the fixture rewrites the whole file.** Expect only the new section and the
  `_meta` additions to change; the record-by-record comparison of "Stata truth" is the proof,
  and any other diff is a finding to report.
- **Renderer order.** Both renderers reach `map_histogram` with the same `options`; the
  served app's `_dash_redraw_for` passes the filtered frame, so the served recount is the
  mapper itself. There is no served JavaScript recount to edit.
- **A skip is not a pass.** The node tests skip only when `node` is absent (it is
  installed, v24; `DASH_NODE` overrides the lookup); `make test` runs strict and turns any
  other skip red.
- **Line numbers drift.** `_histogram_counts` adds about 30 lines before `_histogram_grid`,
  and S04's `_DASH_FMT_JS` shifts `_FILTER_JS` when it merges first; every anchor in 05-03 is
  also given as a symbol, and the symbol is authoritative.
