# Section 05: Histogram edge rule (C2)

> Part of: WP-28 · Gaps: C2 · Risk: yellow · Batch: 2 · Depends on: 03 · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **03** · Blocks **19** · Risk **yellow** · Commits: one commit (C2) → CHANGELOG `Results that change`

- D10: import `run_filter_js_block` from `test/js_runner.py` (S03 deletes `_NODE`/`_run_filter_js_block` from test_statistical_helpers.py).
- D3: append the C2 BUGS.md entry at the END of BUGS.md (no mid-file insertion); add a NaN-precondition stub for `_histogram_counts`.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

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
output for the five measured cases is pinned in `stat_truth.json`.

C2 is alone in this section because it touches one mapper, one JavaScript branch and one
extract script, none of which any other batch-1 section edits. S03's stateful node runner
(C2 "recount test" in the index) is optional here: the single-block runner at
`test/test_statistical_helpers.py:820` runs the histogram branch of the real `_FILTER_JS`
under node and is enough to prove the twin.

**Test order (CLAUDE.md rule 7): task 05-01 writes every regression test that needs no
Stata fixture, runs it against the unmodified tree and records the 2245/49 failures; task
05-02 records Stata's truth and pins it; tasks 05-03 onwards turn them green.**

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
  `cert_file_has` alone.
- **Mitigation.** The config carries the three numbers both counters use, so neither derives
  `h`; a seeded property test compares Python and node bar-for-bar; the spurious-bin file is
  revised (not deleted) to assert the new invariant through the mapper; the fixture diff is
  reviewed for additions only; the cscript decodes the page's JSON in a `python:` block, as
  `test/test_help_claims_4.cscript:421` already does.

## Dependencies

- **Depends on:** none. The fixture CSVs, the node runner and the served builder all exist.
- **Blocks:** 19 (closeout lifts the CHANGELOG line and the GAPS2 Tracked line).
- **Parallel batch:** 1.
- **Can run with:** every other batch-1 section. S05 edits `GlyphMapper.map_histogram`,
  `GlyphMapper._histogram_grid`, the histogram branch of `_FILTER_JS`,
  `scripts/extract_stat_truth.do` and `test/test_statistical_truth.py`; no other batch-1
  section names any of them (S12's date-axis work is batch 2 and touches neither).

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
served app never runs it.

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
  `nlsw88:{wage,hours}:*`; nothing for `ttl_exp`, `bin(27)` or `bin(75)`.
- `scripts/extract_stat_truth.do`: record helpers `zq_s`/`zq_n`/`zq_a` (:78-99), `zq_chunk`
  (:100-118), `zq_curve` (:120-176, **`maxn(41)`: a curve longer than 41 points is stored at
  11 sampled indices**), the dataset table (:238-241, `hvars(wage hours)` for nlsw88), layer 1
  (:276-380), the python reader (:1856-1913, `NEVER_NUM` :1898-1905), the section tuple the
  JSON is built from (:2779-2787) and `_meta.counts`/`self_checks` (about :2694-2760).

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
  asserts `ac.get("discrete") is True`: the key stays in the config (TR-05.4).
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
  measured cases pinned in a fixture, so that the rule can never drift back silently.

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
  Stata's own generator output bar for bar.

## Technical requirements

- **TR-05.1** Add `GlyphMapper._histogram_counts(arr, w, start, width, nb) -> np.ndarray`
  (a `@staticmethod` beside `_histogram_grid`): `idx = np.floor((arr - start)/width)`,
  `np.clip(idx, 0, nb-1).astype(np.int64)`, `np.bincount(idx, weights=w, minlength=nb)
  .astype(float)`. Both branches of `map_histogram` call it; the `if discrete ... else
  np.histogram` fork at :9559-9571 becomes one block. A static method on the class travels to
  the served app with the class copy (:24698-24700); no copy-list edit.
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
  `nlsw88:ttl_exp:bin27_density` (no `frequency`, for the y mode). The python block adds
  `"histogram_edge"` to the section tuple (:2779-2787), `histogram_edge_probes` to
  `_meta.counts`, and a self-check `histogram_edge_frequency_sums_equal_N` (every frequency
  record's `sum_height == N`). The block never calls Stata and writes no backtick (there is
  none to write). The fixture is re-added with `git add -f test/fixtures/stat_truth.json`.
- **TR-05.7** New test module `test/test_histogram_edge_rule.py` (TDD stubs below) covering:
  the CSV regressions, the seeded property test in Python and under node, the both-modes
  bar sums, the config keys, the unit test of `_histogram_counts`, and the `start()`
  tolerance fold. `test/test_statistical_truth.py` gains `TestHistogramEdgeAgainstStata`
  reading section `histogram_edge`.
- **TR-05.8** `test/function_test_map.py` gains
  `'GlyphMapper._histogram_counts': 'test/test_histogram_edge_rule.py::TestHistogramCounts::test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar'`.
- **TR-05.9** `test/test_histogram_spurious_bin.py`: rewrite the module docstring to state
  the new rule (the tolerance edge was removed by WP-28 C2; `bin(#)` gives # bars because the
  count folds, not because an edge is appended); rename `TestTheGuardStillGuards` to
  `TestEveryObservationIsCounted` and make its two tests count through
  `GM().map_histogram(..., {"frequency": "frequency", ...})` sums, keeping the same inputs.
- **TR-05.10** New `test/test_histogram_edge.cscript` (HE-01..HE-04) registered in
  `test/run_all_cscripts.do` as block 66 in the :1087-1109 pattern; it decodes the saved
  page's Bokeh JSON in a `python:` block (a `_column` reader as
  `test/test_html_output.py:164-183`, the script block found as
  `test/test_html_verification.py:105-113`) and asserts the histogram source's `top` sums to
  2246; `cert_file_has` asserts the page exists and carries the `top` column name;
  `cert_log_has` asserts twoway's refusal text for HE-04.
- **TR-05.11** BUGS.md: one closed entry for C2 whose Description says the BUGS.md:1215
  entry ("A histogram start() above the variable's minimum was accepted and the rows below it
  silently dropped") left the within-tolerance rows dropped and that this entry closes that
  residual; CHANGELOG under `### Results that change` / `**Statistical layers and their
  rows**` with the command, 2245 and 2246, 49 and 50; dash.sthlp's histogram paragraph
  (:2040-2052) gains the continuous rule in one sentence.
- **TR-05.12** Security (rule 1): the config's three new values are Python numbers computed
  from the data, never user text; the JavaScript reads them as numbers; no new text reaches
  HTML.

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
- kdensity, the KPI, filter and date code, and every other section's function are out of
  scope.

## Stata truth

This section extends `scripts/extract_stat_truth.do` (TR-05.6) and regenerates
`test/fixtures/stat_truth.json`. The twoway command lines recorded:

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

with `equivalent_user_cmd` `histogram ttl_exp, frequency bin(27)` and so on. Invocation
(CLAUDE.md rule 10; at most three concurrent Stata sessions in the batch):

```
S="$(mktemp -d "${TMPDIR:-/tmp}/dash_s05.XXXXXX")"   # as scripts/run_cert_suite.sh does
mkdir -p "$S/tmp" && cd "$S" && STATATMP="$S/tmp/" arch -arm64 /usr/local/bin/stata-mp -b do \
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_stat_truth.do
```

`STATATMP` ends in `/` and is not the directory the log lands in (`$S/extract_stat_truth.log`).
The log must end with `WROTE .../stat_truth.json` and print `SELFCHECK
histogram_edge_frequency_sums_equal_N True`. `.git/info/exclude` hides `*.json`, so the
fixture is staged with `git add -f test/fixtures/stat_truth.json`;
`test/test_fixtures_are_committed.py` already finds it named by `test_statistical_truth.py`.
Review `git diff --stat` and `git diff test/fixtures/stat_truth.json | grep '^[-+]' | grep -v
histogram_edge | head`: the expected change is the new section plus `_meta` (`run_date`,
counts, the new self-check); a changed value in another section means Stata or its data
changed and must be reported, not committed silently.

## TDD test stubs

The first six are the regression tests that fail at 91d97be. All new pytest stubs live in
`test/test_histogram_edge_rule.py` unless a file is named.

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
- **Test: `TestTheJavaScriptRecountAgrees::test_ttl_exp_bin_27_under_node_sums_to_2246`**:
  `_run_filter_js_block("histogram", r._dash_agg_config, ttl_exp)` (import it from
  `test_statistical_helpers`); assert `sum(got["top"]) == 2246` and `got["top"] == tops`.
  Pre-fix: 2245 (the `v > edges[last]` skip). Skips only when node is absent, as its
  neighbours do.
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
  and the node run returns the same `top` array. Pre-fix: at least one case drops a row
  (GAPS2 measured about 4%); assert at the end that every case ran (no silent `continue`).
- **Test: `TestHistogramCounts::test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar`**
  (rule 3, the new function): `_histogram_counts(np.array([-0.5, 0, 0.5, 2.0, 2.0000000001]),
  None, 0.0, 1.0, 2)` gives `[3, 2]`; with weights `[1,1,1,2,3]` gives `[3, 5]`. Pre-fix:
  `AttributeError` (shape failure; its non-vacuity rests on the mutation table).
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

**Pinned tests to revise (not delete):** `test/test_histogram_spurious_bin.py` module
docstring and `TestTheGuardStillGuards` (TR-05.9). No existing assertion inverts.

**Mutation table — proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| in `_histogram_counts`, drop the `np.clip` | `test_ttl_exp_bin_27_51_54_83_count_every_row` (bincount grows to 28 entries; the source columns disagree in length) |
| in `_histogram_counts`, clip to `0, nb` | `test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar` |
| restore `np.histogram` in the continuous branch | every regression above; `test_the_discrete_recount_folds_the_top_value_as_python_does` stays green (discrete was already right) |
| restore the tolerance edge in `_histogram_grid` | `test_seeded_cases_sum_to_n_in_python_and_under_node` (`len(tops) == bin` on a case whose last edge lands below the maximum) and `test_bars_match_the_generator[nlsw88:ttl_exp:bin27]` (`right[-1]` ≠ `r(max)`) |
| in `_FILTER_JS`, keep `if (v < edges[0] \|\| v > edges[last]) continue;` | `test_ttl_exp_bin_27_under_node_sums_to_2246` |
| in `_FILTER_JS`, read `bw` from the edges instead of `ac.width` | `test_seeded_cases_sum_to_n_in_python_and_under_node` on a `start()` case where `(edges[n]-edges[0])/n` ≠ `ac.width` by an ULP |
| omit `"width"` from the config | `test_start_width_and_bin_are_numbers_the_page_can_read`, then every node test (zero counts) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| ttl_exp bin(27/51/54/83) sums to 2246; pop bin(75) to 50 | pytest | data/nlsw88.csv, data/census.csv | saved (mapper); served in `TestBothModes` |
| Density integrates to 1 over 2246 rows | pytest | data/nlsw88.csv | mapper |
| JS recount equals Python | pytest + node (`_run_filter_js_block`) | data/nlsw88.csv | saved page's JS |
| Seeded property, 40 cases, Python and node | pytest + node | none (seeded) | saved page's JS and mapper |
| `start()` within tolerance folds into bar 0 | pytest | data/nlsw88.csv | mapper |
| `_histogram_counts` contract | pytest | none | n/a |
| Config carries start/width/bin | pytest | none | saved registry |
| Stata's generator output, seven keys | pytest | stat_truth.json `histogram_edge` | mapper |
| Fixture completeness | pytest | stat_truth.json | n/a |
| Page built by dash: decoded `top` sums to 2246; `start()` tolerated and refused | cscript (Stata's Python) | nlsw88 (sysuse) | saved page |
| Served names | pytest `TestTheServedAppCarriesEveryName` | none | served |
| Full suite, both interpreters | `python3 -m pytest test/ -q` once; `make test` | all | both |

Acceptance criteria:

- **AC-05.1** The four ttl_exp cases and the census case sum to N in the mapper, in the
  served document and under node; before the fix they sum to N-1.
- **AC-05.2** 40 of 40 seeded cases sum to N (or the weight total), draw exactly `bin` bars
  when `bin()` is given, and agree bar for bar with node.
- **AC-05.3** `stat_truth.json` carries `histogram_edge` with seven keys, rc 0, and
  `histogram_edge_frequency_sums_equal_N` true; `TestHistogramEdgeAgainstStata` is green.
- **AC-05.4** `test_histogram_edge.cscript` passes: HE-01 sum 2246 on the built page, HE-02
  `bin(83)` sum 2246, HE-03 `start()` within tolerance rc 0 and sum 2246, HE-04 `start()`
  above tolerance rc 198 with `option start() may not be larger than minimum of ttl_exp`.
- **AC-05.5** Full pytest green under both interpreters with no skip attributable to this
  section (node is installed); `function_test_map` names `_histogram_counts`.
- **AC-05.6** BUGS.md holds the closed C2 entry naming its tests and closing the :1215
  residual by reference; CHANGELOG and dash.sthlp updated.

## Tasks

<task type="auto" id="05-01">
  <name>Write the failing histogram edge tests</name>
  <files>test/test_histogram_edge_rule.py (new)</files>
  <action>
    Create `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_histogram_edge_rule.py`
    with tests only; do not touch `dash_render.py`. Module docstring: the defect in CHANGELOG
    terms (`dash histogram ttl_exp, bin(27)` drew 2245 of 2246 rows, `histogram pop, bin(75)`
    49 of 50; Stata counts `floor((v - start)/h)` clamped to the grid,
    twoway__histogram_gen.ado:200-203). Header as `test/test_statistical_helpers.py:11-24`
    (`import dash_render as dr`, `GM = dr.GlyphMapper`), plus `from test_statistical_helpers
    import _hist, _run_filter_js_block, _NODE` and `from conftest import make_data_json`; load
    `test/fixtures/data/nlsw88.csv` and `census.csv` with pandas at module level. Write every
    stub named in "TDD test stubs" except the two `TestHistogramEdgeAgainstStata` tests (task
    05-02): `TestNlsw88AndCensusRegressions` (three tests), `TestTheJavaScriptRecountAgrees`,
    `TestBothModes` (helpers modelled on `test_mode_parity.py:200-247`, writing the spec and
    data JSON under `tmp_path`), `TestStartTolerance`, `TestEveryFrequencyHistogramSumsToN`
    (seeded with `np.random.RandomState(20260925)`, 40 cases, a module-level `_CASES` list so
    the coverage claim is visible, and a final assertion that 40 cases ran),
    `TestHistogramCounts` and `TestTheAggConfigCarriesTheRule`. Node tests carry
    `@pytest.mark.skipif(_NODE is None, reason="node is not installed")` exactly as
    `TestFilterJavaScript` does, and nothing else skips. Run the file against the unmodified
    tree and paste the failure summary (the 2245/49 lines) into the commit message.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_histogram_edge_rule.py -q 2>&1 | tail -25` shows 0 passed; `python3 -m pytest test/test_histogram_edge_rule.py -q -k "bin_27_51_54_83" 2>&1 | grep -c "2245"` prints a non-zero count, and `-k census` shows `49`. `python3 -m pytest test/test_histogram_edge_rule.py -q -k HistogramCounts 2>&1 | grep -c AttributeError` is non-zero.]]></verify>
  <done>The new module exists, collects cleanly, and every test in it fails: the behavioural tests with 2245 or 49 where 2246 or 50 is asserted, the API-shape tests with AttributeError or KeyError; dash_render.py is unmodified.</done>
</task>

<task type="auto" id="05-02">
  <name>Record Stata's edge-case truth and pin it</name>
  <files>scripts/extract_stat_truth.do, test/fixtures/stat_truth.json, test/test_statistical_truth.py</files>
  <action>
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_stat_truth.do`
    add "LAYER 1c -- histogram edge rule (WP-28 C2)" after layer 1's closing brace (about
    :380, before the layer-2 banner), written per TR-05.6: a local list of seven cases
    `dataset|var|variant|opts`, each loaded with `sysuse`, run as `capture
    twoway__histogram_gen \`var', generate(zqh zqx) return \`opts'`, recording `rc` first and
    `continue`-ing on failure, then `bin start width xmin xmax N n_x` via `zq_n`, `type`,
    `cmd` and `equivalent_user_cmd` via `zq_s`, `sum_height` from `summarize zqh, meanonly`
    (`r(sum)`), `start_requested` for the `bin27_start` case (the local computed as
    `r(min)*(1+5e-6)` after `summarize ttl_exp, meanonly`), then `preserve`/`keep zqh
    zqx`/`drop if missing(zqx)`/rename to `bar_height bin_midpoint`/`zq_curve bin_midpoint
    bar_height, sec(histogram_edge) key(\`key') maxn(100)`/`restore`, exactly as :338-346 do
    for layer 1. Loop headers must not contain `${...}` (the file's own note at :56-58). In the
    trailing `python:` block add `"histogram_edge"` to the section tuple (:2779-2787),
    `histogram_edge_probes` to `_meta.counts`, and the self-check
    `histogram_edge_frequency_sums_equal_N` beside `histogram_bin_rule_reproduces_stata`
    (about :2694): true when every `histogram_edge` record with `type == "frequency"` has
    `sum_height == N`; add `"start_requested"` nowhere in `NEVER_NUM` (it is numeric). Run
    Stata as the "Stata truth" section shows, from the scratch directory with `STATATMP`
    ending in `/`, read the log's tail for `WROTE` and the SELFCHECK line, then `git add -f
    test/fixtures/stat_truth.json` after reviewing the diff as that section requires. In
    `test/test_statistical_truth.py` add `TestHistogramEdgeAgainstStata` after
    `TestHistogramAgainstStata` (:177) with the two tests named in the stubs, using `_rec`,
    `_need`, `_series`, `mapper` and the `datasets` x columns (`datasets["nlsw88"][1]` is
    ttl_exp, `datasets["census"][1]` is pop). Run the file; the four ttl_exp keys and census
    fail with 2245/49 against the fixture's 2246/50; record that in the commit message.
  </action>
  <verify><![CDATA[`tail -40 <scratch>/extract_stat_truth.log` shows `WROTE .../stat_truth.json` and `SELFCHECK histogram_edge_frequency_sums_equal_N True`; `python3 -c "import json;d=json.load(open('test/fixtures/stat_truth.json'));print(sorted(d['histogram_edge']))"` lists the seven keys; `git diff --stat` touches only the three files; `python3 -m pytest test/test_statistical_truth.py -q -k HistogramEdge 2>&1 | tail -12` shows `test_the_fixture_holds_the_seven_edge_probes` passing and five `test_bars_match_the_generator` cases failing on the sum (2245 vs 2246, 49 vs 50) while the two `bin27_start`/`bin27_density` cases fail for the same missing row.]]></verify>
  <done>stat_truth.json carries a `histogram_edge` section of seven Stata-measured records whose frequency sums equal N, the extract script reproduces it, and test_statistical_truth.py pins them with tests that fail on the unmodified mapper for the recorded reason.</done>
</task>

<task type="auto" id="05-03">
  <name>Count with Stata's floor-and-clamp in both languages</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py`: (1) add
    `@staticmethod def _histogram_counts(arr, w, start, width, nb)` immediately before
    `_histogram_grid` (:9629) with a docstring citing twoway__histogram_gen.ado:200-203 and the
    body of TR-05.1; (2) in `map_histogram` replace the `if discrete and len(arr): ... else:
    counts, _ = np.histogram(...)` fork (:9559-9571) with the one block of TR-05.3 calling
    `self._histogram_counts(arr, w, start, h, nb)`, keeping `discrete = bool(...)` for the
    config, and extend `r._dash_agg_config` (:9607-9623) with `"start": start`, `"width": h`,
    `"bin": nb` and a comment saying the page's recount reads these three rather than
    rebuilding `h` from the edges (TR-05.4); (3) in `_histogram_grid` delete :9751-9764 (the
    comment and the tolerance edge) and replace the comment with two lines: the last edge is
    `start + width*n_bins`, Stata's `r(max)`, and a value at or floating above it is folded
    into the last bar by `_histogram_counts`; update the method docstring's precedence
    paragraph to say so (TR-05.2); (4) in `_FILTER_JS` (:14768-14834) replace :14800 and
    :14808-14826 with the single floor-and-clamp of TR-05.5 reading `ac.start`, `ac.width`,
    `ac.bin`, guarded by `if (!(ac.width > 0)) { /* leave the counts at zero */ }` before the
    loop, and reword the comment to cite twoway__histogram_gen.ado:200-203 for both branches.
    Then add the function-map entry of TR-05.8 to `test/function_test_map.py` in alphabetical
    place among the `GlyphMapper.` keys. Line numbers above are pre-edit; locate by symbol.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_histogram_edge_rule.py test/test_statistical_truth.py test/test_statistical_helpers.py test/test_histogram_spurious_bin.py test/test_resource_limits.py test/test_mode_parity.py test/test_function_test_map.py -q 2>&1 | tail -5` reports no failures; `grep -c "np.histogram(" dash_render.py` prints 0; `grep -n "v > edges\[edges.length - 1\]" dash_render.py` prints nothing; `python3 -c "import dash_render as d,numpy as np;print(d.GlyphMapper._histogram_counts(np.array([-0.5,0,0.5,2.0,2.0000000001]),None,0.0,1.0,2).tolist())"` prints `[3.0, 2.0]`.]]></verify>
  <done>Both branches of map_histogram count through `_histogram_counts`, the tolerance edge is gone, the config carries start/width/bin, the saved page's JavaScript applies the same rule from those numbers, and every test of 05-01 and 05-02 passes.</done>
</task>

<task type="auto" id="05-04">
  <name>Revise the spurious-bin file and run the suite</name>
  <files>test/test_histogram_spurious_bin.py</files>
  <action>
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_histogram_spurious_bin.py`
    rewrite the module docstring per TR-05.9: keep the measured history (bin(6)/bin(12) drew
    a 7.105e-15-wide spike), state that WP-28 C2 removed the tolerance edge altogether because
    the count now folds a value at or above the last edge into the last bar
    (twoway__histogram_gen.ado:200-203), and that `bin(#)` therefore gives # bars by
    construction. Rename `TestTheGuardStillGuards` to `TestEveryObservationIsCounted`; keep
    its three inputs and turn the two coverage tests into frequency-sum assertions through
    `dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color")).map_histogram(figure(),
    ColumnDataSource({"v": arr.tolist()}), "v", {..., "frequency": "frequency"})` (imports as
    `test_statistical_helpers.py:18-19`), asserting `tops.sum() == len(arr)` and, for the
    `start(0) width(3)` case, `right[-1] == 12.0` (Stata's `r(max) = 0 + 3*4`). Leave
    `TestBinCountIsWhatWasAsked` as it is. Then run the full suite once, `python3 -m pytest
    test/ -q`, and fix any regression in the code, never by weakening a test; record any
    re-baselined assertion in the commit message with old and new values (none is expected).
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_histogram_spurious_bin.py -q 2>&1 | tail -3` passes; `grep -c "np.histogram" test/test_histogram_spurious_bin.py` prints 1 or less (the one in `test_no_bar_is_a_degenerate_spike` may stay); `python3 -m pytest test/ -q 2>&1 | tail -5` reports no failures.]]></verify>
  <done>The spurious-bin file documents the floor-and-clamp contract and asserts it through the mapper, and the full pytest suite is green on the fixed tree.</done>
</task>

<task type="auto" id="05-05">
  <name>Certify the built page counts every row</name>
  <files>test/test_histogram_edge.cscript (new), test/run_all_cscripts.do</files>
  <action><![CDATA[
    Create `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_histogram_edge.cscript`
    with the header, `cscript "dash histogram edge rule" adodir ".."`, the `c(python_exec)`
    skip (`exit 222`), `do "cert_helpers.do"`, the two `qui do` lines and `global
    dash_nobrowser 1` copied from `test/test_custom_scheme.cscript:70-88`, then `sysuse
    nlsw88, clear` and four cases run in `c(tmpdir)`: HE-01 `dash histogram ttl_exp, bin(27)
    frequency saving(he1.html, replace)`, rc 0; HE-02 the same with `bin(83)`; HE-03
    `start(\`s')` with `local s = r(min)*(1+5e-6)` after `quietly summarize ttl_exp,
    meanonly`, rc 0; HE-04 `start(\`s2')` with `local s2 = r(min)*1.01` under `log using`,
    `_rc == 198` and `cert_log_has` for `option start() may not be larger than minimum of
    ttl_exp`. For HE-01..03, `cert_file_has "<file>", needle("top")` must find the column
    name, and a `python:` block (Stata's Python: `import json, re, base64, gzip, numpy`;
    `from sfi import Macro`) reads the file, finds `<script type="application/json"` as
    `test_html_verification.py:105-113`, walks the document for a ColumnDataSource whose
    `data` entries hold `top`, `left` and `right` (Bokeh 3 writes `data` as `{"type": "map",
    "entries": [[name, value], ...]}`), decodes `top` as `test_html_output.py:164-183`
    (`list`, or `ndarray` with base64 `bytes`, gzipped when `raw[:2] == b"\x1f\x8b"`), and
    `Macro.setGlobal("he_sum", str(int(round(sum))))` and `he_nbar`; then `assert ${he_sum}
    == 2246` and `${he_nbar}` equal to the bin count. Print `HE-0n PASS: ...` per case in
    the `_cs_expect`/`_cs_done` style or with plain `display`, and `exit 1` if any case
    failed. Register it in `test/run_all_cscripts.do` as block 66 by copying :1087-1109 with
    the new name (`test_cscript_hygiene.py::TestEveryCscriptIsWiredIntoTheRunner` requires
    it). Run it alone from a scratch directory with a two-line driver do-file (`cd
    ".../dash/test"` then `do "test_histogram_edge.cscript"`), `STATATMP=<scratch>/tmp/`,
    `arch -arm64 /usr/local/bin/stata-mp -b do run_one.do`, and read `run_one.log`.
  ]]></action>
  <verify><![CDATA[`grep -c "PASS" <scratch>/run_one.log` prints 4 and `grep -c "FAIL" <scratch>/run_one.log` prints 0; the log shows `2246` for HE-01, HE-02 and HE-03 and the r(198) text for HE-04; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -3` passes.]]></verify>
  <done>A registered certification script builds histogram pages through dash.ado and proves, from the page's own embedded data, that all 2246 rows are counted with bin(27), bin(83) and a tolerated start(), and that a start() above the tolerance is refused with twoway's words.</done>
</task>

<task type="auto" id="05-06">
  <name>Close C2 in BUGS.md, CHANGELOG and the help</name>
  <files>BUGS.md, CHANGELOG.md, dash.sthlp</files>
  <action>
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/BUGS.md` add, after the entry at
    :1215 ("A histogram start() above the variable's minimum ..."), a closed entry `- [x]
    Title: A continuous histogram dropped the observation at its last edge, and the rows a
    tolerated start() lies above` with File Names and Line Numbers (`dash_render.py
    GlyphMapper.map_histogram (np.histogram on the continuous edges), GlyphMapper._histogram_grid
    (the tolerance edge), _FILTER_JS (the range test)`), Description (GAPS2 C2's measured
    symptom: nlsw88 ttl_exp bin(27|51|54|83) 2245 of 2246, census pop bin(75) 49 of 50, the
    rows below a start() within reldif 1e-5 dropped; the residual of the entry above), Suggested
    fix (Stata's floor-and-clamp, twoway__histogram_gen.ado:200-203, in Python and in the
    page's recount), and Resolution "Fixed. Certified by
    test/test_histogram_edge_rule.py::TestNlsw88AndCensusRegressions,
    ::TestEveryFrequencyHistogramSumsToN, ::TestTheJavaScriptRecountAgrees,
    test/test_statistical_truth.py::TestHistogramEdgeAgainstStata (Stata's own generator
    output for the five cases) and test/test_histogram_edge.cscript HE-01..HE-04. Closes the
    residual of the start() entry above." In `CHANGELOG.md` under `### Results that change`
    (:10), `**Statistical layers and their rows**` (:16), add a bullet: a continuous
    `histogram` could drop the observation at its last bin edge when the computed edge fell a
    few units in the last place below the maximum; `dash histogram ttl_exp, bin(27)` on
    nlsw88 counted 2245 of 2246 and `histogram pop, bin(75)` on census 49 of 50, and the
    density bars were scaled to the rows that remained; every observation is now counted as
    Stata counts it, bar `floor((v - start)/width)` clamped to the grid, in the page and after
    a filter move (WP-28 C2). In `dash.sthlp` extend the histogram paragraph (:2040-2052)
    with one sentence after "as Stata counts it.": on every histogram each observation is
    counted in bar floor((v - start)/width), a value at or past the last edge in the last bar
    and one below a tolerated start() in the first, as twoway__histogram_gen counts them.
    grep the three edits and the commit message for `claude` and `anthropic` before and after
    committing (nothing may match).
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q 2>&1 | tail -3` passes; `grep -n "dropped the observation at its last edge" BUGS.md CHANGELOG.md` finds both; `grep -n "floor((v - start)/width)" dash.sthlp` finds the help sentence; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>C2 is recorded closed in BUGS.md naming its tests and closing the start() residual by reference, the changed numbers are listed under "Results that change", and the help states the continuous counting rule.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" exists and passes; the six regression tests are recorded as
  failing at 91d97be in 05-01's and 05-02's commit messages.
- `grep -c "np.histogram(" dash_render.py` is 0; `_histogram_counts` exists and is named in
  `test/function_test_map.py`.
- `stat_truth.json` holds the seven `histogram_edge` records with rc 0 and the self-check
  true; `git ls-files test/fixtures/stat_truth.json` lists it.
- `test/test_histogram_edge.cscript` is registered and passes under
  `arch -arm64 /usr/local/bin/stata-mp -b`; `scripts/run_cert_suite.sh` still reports no
  SKIP.
- `python3 -m pytest test/ -q` is green; `make test` (Stata's Python, `DASH_STRICT=1`) is
  green with no skip from this section.
- BUGS.md, CHANGELOG.md and dash.sthlp carry the C2 closure; no AI reference anywhere.
- No file outside the six tasks' file lists is modified.

## Notes

- **The two counters must read the same numbers.** Python computes `h` from the edges it
  built; the config ships that `h`, `start` and `nb`; the JavaScript must not recompute
  anything from `bin_edges`. The property test's `start()` cases are where an
  edges-derived `bw` differs by an ULP and moves a value across a bar.
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
  column name `top` but cannot sum it; the cscript decodes in a `python:` block, the pattern
  of `test/test_help_claims_4.cscript:415-430` (`Macro.setGlobal`) and
  `test/test_html_output.py:164-183` (`_column`).
- **Stata's Python.** The cscript's `python:` block runs under `c(python_exec)`
  (`/opt/anaconda3/bin/python3`, numpy available). Many concurrent Stata sessions can drop
  `python_exec` from `~/.stata19/console/stata19.rc`, after which every Python cscript
  SKIPs: keep to three sessions in the batch and, on a run of SKIPs, check
  `c(python_exec)` before trusting them (`set python_exec /opt/anaconda3/bin/python3,
  permanently` restores it).
- **Regenerating the fixture rewrites the whole file.** Expect only the new section and
  `_meta` to change; any other diff is a finding to report.
- **Renderer order.** Both renderers reach `map_histogram` with the same `options`; the
  served app's `_dash_redraw_for` passes the filtered frame, so the served recount is the
  mapper itself. There is no served JavaScript recount to edit.
- **A skip is not a pass.** The node tests skip only when `node` is absent (it is
  installed, v24); `make test` runs strict and turns any other skip red.
- **Line numbers drift.** `_histogram_counts` adds about 25 lines before `_histogram_grid`;
  every anchor in 05-03 is also given as a symbol, and the symbol is authoritative.
