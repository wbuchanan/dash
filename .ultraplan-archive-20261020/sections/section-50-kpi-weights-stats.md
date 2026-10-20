# Section 50: KPI weights and kurtosis, semean, range

> Part of: WP-31 · GAPS3 rows: H2k (H2 KPI part; E7 note) · Risk: green · Batch: 17 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U50

## Overview

**What is wrong today.** GAPS3 H2 (GAPS3.md:239): "KPI cards take no weights and lack kurtosis/semean/range". `_dash_kpi`'s `syntax` (dash.ado:9318-9326) is `syntax anything(name=statspec) [if] [in] , TItle(string) NAMe(string) [FMT(string) SUBtitle(string) COLOR(string) BGCOLOR(string) UPDate(string)]` -- no weight class -- and `local valid_stats "mean sum count dcount min max median sd var cv iqr skewness p25 p50 p75"` (:9350). The renderer's `_kpi_statistic` (dash_render.py:42830-42903) and the saved page's `dash_apply_kpis` (:24904-25010) compute the same list unweighted. `summarize mpg [aw=weight]` and `summarize mpg, detail` (r(kurtosis), r(se)? -- no: `semean` is `mean`'s/`tabstat`'s) are Stata's everyday answers a dashboard cannot show.

**After this section** `dash kpi mean(mpg) [aw=weight], title(...) name(...)` accepts `aweight`, `fweight` and `iweight` (`pweight` refused as `summarize` refuses it), writes `"weight":"aweight","wexp":"weight"` into the KPI spec, and every statistic is computed by `summarize`'s weighted formulas in Python and in JavaScript; three statistics are added, `kurtosis`, `semean` and `range`, unweighted and weighted. Every value is measured against Stata in the truth block (U50) and stored in a fixture by a new extract script.

**Why one section.** One statistic table, three twins (Stata's truth, Python, JS), one spec key pair. S50 is batch 17's KPI-statistics owner; S51 (same batch) owns the link/brush machinery and S52 the `_FILTER_JS` wrapper.

**Test order and commit rule.** One cycle, one commit `(WP-31 H2k)`: 50-01 extractor and fixture, regression tests red; 50-02 dash.ado, Python and JS twins; 50-03 served path, help, close, commit.

### Section decisions (binding on the executor)

- **D-50a. Weight classes follow `summarize`.** `aweight`, `fweight`, `iweight` accepted; `pweight` refused with r(101) and `summarize`'s text (measured in the extract script: `capture summarize mpg [pw=weight]` → `_rc` and the log line, expected `pweights not allowed`). Formulas ([R] summarize, Methods and formulas): let w_i be the weights of the N non-missing observations and W = Σ w_i. For `fweight`/`iweight`: mean = Σ w_i x_i / W; Var = Σ w_i (x_i − mean)² / (W − 1); sd = sqrt(Var); count = W (for fweight; for iweight also W, as summarize reports N = Σw); sum = Σ w_i x_i; min/max unweighted over observations with w_i ≠ 0; skewness = m3 / m2^1.5 and kurtosis = m4 / m2² with m_k = Σ w_i (x_i − mean)^k / W; semean = sd / sqrt(W); cv = sd / mean; range = max − min; percentiles: sort x ascending, cumulative weight W_i = Σ_{j≤i} w_j, P = p/100 · W; the p-th percentile is x_i for the first i with W_i > P, and (x_i + x_{i+1})/2 when W_i = P exactly (the rule Stata states for `summarize, detail` with weights). For `aweight`: the weights are first normalised, w_i* = w_i · N / W, then the fweight formulas apply with W = N (so Var's denominator is N − 1 and count = N, the unweighted observation count). `dcount` ignores weights (distinct values). An observation with missing or zero weight is dropped (negative weights are refused by Stata; dash's `syntax` weight class refuses them too).
- **D-50b. The weight is a variable name.** `[aw=weight]` with a variable; an expression (`[aw=weight/2]`) is refused r(198) `dash kpi: the weight must be a variable name; dash does not evaluate '<text>'` (bounded to 40 characters). The variable name is written as `wexp`, the class as `weight` (the plot-layer convention, `_DASH_OPT_VAR_KEYS` carries `wexp` into sources). A KPI's weight variable joins the dataset columns the page embeds (it is a dataset variable, always embedded).
- **D-50c. New statistics.** `kurtosis` (m4/m2², Stata's biased form, `summarize, detail` r(kurtosis)), `semean` (sd/sqrt(N) or sd/sqrt(W); `tabstat, statistics(semean)` and `mean`'s standard error for fw; truth from `summarize`'s r(sd)/sqrt(r(N)) for the unweighted case and `mean [aw=]`'s `_se` for aw -- measured, not derived, in the extractor) and `range` (r(max) − r(min)). On fewer than 2 observations sd-based statistics are missing; kurtosis needs m2 > 0.
- **D-50d. One arithmetic each.** Python: `_kpi_statistic(col, stat, weights=None)` gains an optional weight Series aligned with `col`; the unweighted path is the weighted one with w = 1 (so one body). JS: `dash_apply_kpis` reads `k.wvar` and takes `data_obj[k.wvar]` as weights, computes `dash_wstats(vals, w, kind)` -- a new named function placed between `dash_kernel` and the "agg_sources" comment (BRIEF: new estimator helpers go there) so `js_runner`'s helper slice carries it.

## Risk: [green] -- additive statistics, measured truth, both twins pinned

**Why.** The formulas are standard and measured; the surfaces are the KPI syntax, the two twins and the spec.

**Risk factors.** (1) aweight normalisation differences between `summarize` and `summarize, detail` percentiles; (2) the saved page's `kpi_config` must carry `wvar` and the brush path (`_BRUSH_JS`) passes the same `data_obj` so weights ride along; (3) S51 edits the brush machinery in the same batch -- the weight column must be in `_need` (:45400-45401) for brushable copies.

**Mitigation.** (1) truth measured per statistic × weight class in the fixture; (2) `kpi_config` built at :45313 gains `"wvar"`; `_need` adds the weight variables (a two-line edit at :45400-45401 inside `_wire_brush_callbacks` (:45345; REVIEW-4 R4-18: the function is `_wire_brush_callbacks`, not `_wire_brush`), whose other lines S51 (new args, the state CDS) and S52 (the `CustomJS(code=...)` call) edit -- three disjoint hunks, recorded in the three files and the index owner table, DECISIONS A28); (3) merge order 50 → 51 → 52.

## Dependencies

- **Depends on: 01.** **Blocks: none.**
- **Parallel batch: 17** with S51 (link/brush) and S52 (`_FILTER_JS` wrapper, slider throttle). **Recorded R12 exception (DECISIONS A28, REVIEW-4 R4-11; the index owner table carries it):** `_FILTER_JS`: 52 (the wrapper at the :31459 assembly), 50 (the `dash_apply_kpis` body :24916-25040 and the `dash_wstats`/`dash_wpctl` insertion between `dash_kernel` and the agg_sources comment ONLY); template (`_generate_app_source`): 50 (`_compute_kpi`, `_dash_kpi_value`), 51 (the link/brush block), 52 (the three `document_ready` lines :50764-50766); `_wire_brush_callbacks`: 50 (the two `_need` lines :45400-45401), 51 (args, state CDS), 52 (the `CustomJS(code=...)` construction only). Merge order 50 → 51 → 52; the merger checks each hunk's lines are disjoint before `patch -p1`. S50 is not moved to batch 18 (it would collide with S55 on the template).

## Evidence

### dash.ado

```
9318    syntax anything(name=statspec) [if] [in] , ///
9319        TItle(string)           ///
9320        NAMe(string)            ///
9321        [ FMT(string)           ///
...
9350    local valid_stats "mean sum count dcount min max median sd var cv iqr skewness p25 p50 p75"
```

The KPI JSON row (:10447): `{"name":"...","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"...","fmt":"...","title":"...","subtitle":"...","color":"...","bgcolor":"...","update":"`kupdate'","if_expr":"","in_expr":"","qual_col":"`_kqc'"}`. The registry globals that feed it are set near :9480-9530 (`dash_kpi_<name>_stat` and friends; the executor greps `kupdate` to find the pattern).

### Python

`_kpi_statistic` (:42830-42903): `sd` → `col.std(ddof=1)`, `skewness` biased `m3/m2**1.5`, percentiles via `_stata_percentile(srt, p)`. Called by `_compute_kpi_stat_on_df` (:42905) in the saved renderer and by the served `_compute_kpi` (template :48654-48672, "Delegates to _kpi_statistic, which is the standalone renderer's own function copied in verbatim above").

### JavaScript

`dash_apply_kpis(data_obj, kpi_config, kpi_divs, ROW_ID)` (:24904-25040): `const col = data_obj[k.varname]`; filters `_vals0`; the branch chain `count/dcount/sum/mean/min/max/sd/var/cv/skewness/else percentiles`. `kpi_config` entries are written at :45313 (`"has_qual": qual_ids is not None`, beside `varname`, `stat`, `fmt`, `storage`, `unitkind`, `datekind`).

### Fixtures

test/fixtures/kpi_truth.json (`kpi_stats.all`, `kpi_stats.foreign1`, `moment_definitions`) has NO committed generator (GAPS3 K3 list; S60 K3 adds `scripts/extract_kpi_truth.do` for the EXISTING keys). S50 writes its own fixture `test/fixtures/kpi_weights_truth.json` from `scripts/extract_kpi_weights_truth.do` so the two generators do not collide.

### Existing tests that pin today's behaviour

- test/test_kpi_values.py::TestEveryStatisticMatchesStata::test_the_statistics_the_command_does_not_yet_accept (:283-292) -- `var cv iqr skewness` ARE accepted today by dash.ado (:9350) and the renderer; the docstring is stale, the test passes; S50 renames it in place to `test_var_cv_iqr_skewness` and adds `kurtosis semean range` to `test_unconditional`'s parametrisation once the fixture has them (R9: a flip with a reason, no deletion).
- test/test_kpi_brush.py::TestTheArithmeticIsNotDuplicated::test_the_statistic_is_defined_exactly_once (:191) -- pins one definition per statistic marker in the JS; the new `dash_wstats` must keep each statistic's marker string unique (define the new branches inside `dash_apply_kpis` by calling `dash_wstats`, and give `dash_wstats` no `stat === '...'` literals that the pin counts -- read the pin's marker list first).
- test/test_help_claims_4.cscript / test_help_claims_4.py (every statistic the help lists is Stata's) -- the help's statistic list grows by three; the cscript's loop over the list picks them up (verify the loop reads the help, else add three cases U50-9..11 there).

## User stories

- **US-50.1** As an analyst I want `dash kpi mean(price) [fw=rep78]` so that a card shows the frequency-weighted mean Stata shows.
- **US-50.2** As an analyst I want kurtosis, the standard error of the mean and the range as cards so that distribution summaries need no extra graph.
- **US-50.3** As a reader I want weighted cards to stay weighted after a filter or brush so that the page agrees with Stata on the kept rows.

## Business requirements

- **BR-50.1** `[aw= fw= iw=]` on `dash kpi` give `summarize`'s weighted statistics for every statistic; `[pw=]` is refused as `summarize` refuses it.
- **BR-50.2** `kurtosis(var)`, `semean(var)`, `range(var)` are accepted and equal Stata's `summarize, detail` kurtosis, sd/sqrt(N) and max − min.
- **BR-50.3** A weighted card recomputes weighted after a filter move and a brush in both modes.
- **BR-50.4** A weight expression that is not a variable, and a string weight variable, are refused in one sentence each.

## Technical requirements

- **TR-50.1 dash.ado syntax.** `syntax anything(name=statspec) [if] [in] [aweight fweight iweight pweight], ...` then: `if "`weight'" == "pweight" { display as error "pweights not allowed"; exit 101 }` (text measured by the extractor, U50-7 compares); `if "`weight'" != "" { local _kw = strtrim(subinstr("`exp'", "=", "", 1))` (`syntax` returns `exp` as `= weight` with a blank after `=`, so `substr(..., 2, .)` would leave a leading blank and `confirm numeric variable` would fail on a valid name -- REVIEW-4 R4-32); `capture confirm numeric variable `_kw'`; a failure → D-50b's refusal (r(198)) or `dash kpi: weight variable '<v>' is a string` r(109) }`. Store `dash_kpi_<name>_weight` and `_wexp` globals beside `_stat`; the JSON row (:10447) gains `,"weight":"`kweight'","wexp":"`kwexp'"` after `"update":"`kupdate'"`.
- **TR-50.2 valid_stats.** `local valid_stats "mean sum count dcount min max median sd var cv iqr skewness kurtosis semean range p25 p50 p75"`.
- **TR-50.3 Python.** `_kpi_statistic(col, stat, weights=None)`: `w = np.ones(len(col)) if weights is None else np.asarray(weights, dtype=float)`; drop rows where `w` is NaN or 0 (and the matching `col` rows); `kind` (`"aweight"` normalises `w = w * len(w) / w.sum()`); `W = w.sum()`; `mean = (w*x).sum()/W`; `var = (w*(x-mean)**2).sum()/(W-1)` when `W > 1`; `count = W` for fweight/iweight, `len(x)` for aweight and unweighted; `sum = (w*x).sum()`; `skewness/kurtosis` from `m_k = (w*(x-mean)**k).sum()/W`; `semean = sqrt(var/W)`; `range = x.max()-x.min()`; `dcount` unweighted; percentiles via new `_stata_wpercentile(x_sorted, w_sorted, p)` implementing D-50a's rule (the unweighted `_stata_percentile` is the special case w = 1 -- `test_the_weighted_rule_reduces_to_the_unweighted` pins this). Signature change: callers `_compute_kpi_stat_on_df(df, stat, varname, weight=None, wkind="")` pass `df[wexp]` when the KPI spec has `wexp`. The served `_compute_kpi(df, stat, varname, date_vars=None, wexp="", wkind="")` (template :48654) forwards them; `_dash_kpi_value(plan, kpi)` (:50168) passes `kpi.get('wexp', '')`, `kpi.get('weight', '')`.
- **TR-50.4 JS.** New `function dash_wstats(vals, w, stat, kind)` between `dash_kernel` and the agg_sources comment: the same arithmetic as TR-50.3 (normalise for `aweight`; sort pairs for percentiles; `dash_wpctl(xs, ws, p)` beside it). `dash_apply_kpis`: after `src_col`, `const wcol = k.wvar ? data_obj[k.wvar] : null;` build `vals` and `ws` together (a row is kept when its value passes today's test AND, with `wcol`, its weight is a finite non-zero number); replace the branch chain's arithmetic with `result = dash_wstats(vals, ws, stat, k.wkind)` for every statistic but `count`/`dcount`/`sum` (keep those branches, weighted as D-50a says) -- keep the `stat === '...'` marker literals exactly as they are so test_kpi_brush.py:191's pin still counts one each. `kpi_config` (:45313) gains `"wvar": wexp, "wkind": weight`.
- **TR-50.5 Brushable copies.** `_wire_brush_callbacks`' `_need` (:45400-45401) adds every KPI's `wvar` (two lines; S50's only edit in that function, A28).
- **TR-50.6 Extract script.** `scripts/extract_kpi_weights_truth.do` → `test/fixtures/kpi_weights_truth.json`: `sysuse auto`; for each class in `aw fw iw` (fw needs integer weights: use `rep78` with missing dropped, and `gear_ratio` rounded into `gen int wfw = round(weight/100)`), `summarize mpg [<class>=<w>], detail` → `r(N) r(sum_w) r(mean) r(Var) r(sd) r(min) r(max) r(sum) r(skewness) r(kurtosis) r(p25) r(p50) r(p75)`; `mean mpg [aw=weight]` → `_se[mpg]` as `semean_aw`; the unweighted `summarize mpg, detail` block (kurtosis, semean = r(sd)/sqrt(r(N)), range); `capture summarize mpg [pw=weight]` → `pw_rc`, `pw_text` (from the log through `cert_log_has`-style reading in the do-file); the `foreign1` scope (`if foreign`) for each. `_meta` per BRIEF; `git add -f`.
- **TR-50.7 Maps.** function_test_map: `_stata_wpercentile`; program_coverage_map: none new (no new program).
- **TR-50.8 Help.** dash.sthlp `{title:KPI Cards}` (:1793ff): the weight clause in the syntax line, the three statistics in the list, one sentence on `summarize`'s formulas and the `pweight` refusal.

## Boundaries

- No change to `_BRUSH_JS`, `_dash_link_names`, `_DASH_FIGURE_TOOLS`, `_dash_dim_nonselection` (S51).
- No `_FILTER_JS` edit outside `dash_apply_kpis` and the new helpers; no slider wiring (S52).
- No plot-layer weight change (S07 A5, S20 C9 landed earlier).
- No `pweight` support (refused).

## Stata truth

`scripts/extract_kpi_weights_truth.do` (TR-50.6), run as `DASH_REPO=<repo> scripts/stata_slot.sh <scratch> <repo>/scripts/extract_kpi_weights_truth.do`; fixture `test/fixtures/kpi_weights_truth.json`, keys `{"_meta":..., "unweighted": {all, foreign1}, "aweight": {...}, "fweight": {...}, "iweight": {...}, "pweight_refusal": {"rc": 101, "text": "pweights not allowed"}}`, each scope `{N, sum_w, mean, Var, sd, min, max, sum, skewness, kurtosis, p25, p50, p75, semean, range}`. Truth block `* ==== S50 H2k: KPI weights ====`: `U50-1` `dash kpi mean(mpg) [aw=weight], ...` spec holds `"weight":"aweight","wexp":"weight"`; `U50-2..U50-5` for each of mean, sd, p75, kurtosis the rendered card text equals `summarize [aw=weight], detail` measured live in the block (`%12.6f`); `U50-6` fw and iw cards (mean, Var); `U50-7` `[pw=]` r(101) with Stata's text; `U50-8` `[aw=weight/2]` r(198); `U50-9` `semean(mpg)` equals r(sd)/sqrt(r(N)); `U50-10` `range(mpg)`; `U50-11` a string weight r(109).

## TDD test stubs

Regression (red at 6370ca4), file `test/test_kpi_weights.py`:
- `TestTheFixture::test_meta_and_scopes` (fixture committed, keys present).
- `TestWeightedStatistics::test_python_matches_stata[stat x class]` (parametrised over the 15 statistics × aw/fw/iw; `_kpi_statistic(col, stat, weights, kind)` to 1e-9 relative).
- `TestWeightedStatistics::test_the_weighted_rule_reduces_to_the_unweighted` (w = 1 equals `_stata_percentile` for p in 1..99 on auto `price`).
- `TestNewStatistics::test_kurtosis_semean_range_unweighted` (against `unweighted.all`).
- `TestTheJavaScriptTwin::test_dash_wstats_matches_python[stat x class]` (node via `js_runner.run_filter_js_block` helper slice; same tolerances).
- `TestTheCardsRender::test_saved_card_text_is_statas` (spec with `weight`/`wexp`, `%12.6f`), `::test_served_card_text_is_statas`, `::test_a_filter_move_keeps_the_weights` (node: `dash_apply_kpis` over the masked rows vs Python on the same rows), `::test_a_brush_keeps_the_weights` (the brush code string as `_wire_brush_callbacks` assembles it).
- `TestKpiConfig::test_wvar_and_wkind_are_written`, `::test_wvar_joins_the_brushable_need`.
- Flip: test_kpi_values.py:283 renamed to `test_var_cv_iqr_skewness` (`Flipped:` line: the docstring claimed a capability gap that closed earlier); `test_unconditional` parametrisation gains `kurtosis semean range` reading `kpi_weights_truth.json`'s unweighted scope.

cscript cases U50-1..U50-11 (above), the weighted ones measured live against `summarize [aw=] , detail`.

Parity: `_case("weighted kpi", [plot_for("scatter")], kpis=[kpi_for("mean", "mpg", weight="aweight", wexp="weight")])` (extend the `kpi_for` helper with the two keys) and `_move_case("weighted kpi, dropdown to Foreign", _MOVES[0], [plot_for("scatter")], kpis=[...])` -- the card oracle `_saved_with_qualifier` carries the weight automatically (it re-runs the saved renderer).

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| weight syntax, refusals, spec | cscript U50-1, 7, 8, 11 | none (live) | n/a |
| card values vs Stata | cscript U50-2..6, 9, 10; pytest TestTheCardsRender | kpi_weights_truth.json | yes |
| Python twin | pytest | kpi_weights_truth.json | -- |
| JS twin | node | kpi_weights_truth.json | saved |
| moves and brushes keep weights | node + served doc | none | yes |
| parity | test_mode_parity entries | none | yes |

**AC-50.1** every stub green; **AC-50.2** U50-1..11 pass; **AC-50.3** test_kpi_values.py, test_kpi_brush.py, test_help_claims_4.py green; **AC-50.4** `TestTheServedAppCarriesEveryName` green (`_stata_wpercentile` on the statistical-helpers copy list after `_natural_cubic_spline`, R2).

## Tasks

**Commit boundary.** 50-01..50-03 form the one commit `Take aweight, fweight and iweight on dash kpi and add kurtosis, semean and range (WP-31 H2k)`.

<task type="auto" id="50-01">
  <name>Extract the weighted truth and write failing tests</name>
  <files>scripts/extract_kpi_weights_truth.do, test/test_kpi_weights.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create scripts/extract_kpi_weights_truth.do on the pattern of scripts/extract_default_base_truth.do (DASH_REPO guard, adopath, mata/ado load, global dash_nobrowser 1, `shell git rev-parse HEAD > file' into a local, a python: block writing the JSON with _meta through Macro.getLocal, sort_keys) measuring TR-50.6's values; run it through scripts/stata_slot.sh and `git add -f test/fixtures/kpi_weights_truth.json`. Create test/test_kpi_weights.py with the classes above (the node tests through test/js_runner.py's helper slice). Append the S50 block with U50-1..U50-11 to test/test_wp31_truth.cscript. Run `python3 -m pytest test/test_kpi_weights.py -q` on the unmodified tree; save to <scratch>/50-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[python3 -c "import json;d=json.load(open('test/fixtures/kpi_weights_truth.json'));print(sorted(d))" prints ['_meta', 'aweight', 'fweight', 'iweight', 'pweight_refusal', 'unweighted']; the pytest tail shows failures (TypeError: _kpi_statistic() got an unexpected keyword argument 'weights'); test -s <scratch>/50-01-failure.txt]]></verify>
  <done>The fixture exists with its _meta, and the regression tests fail at 6370ca4.</done>
</task>

<task type="auto" id="50-02">
  <name>Weight the statistics in Stata, Python and JavaScript</name>
  <files>dash.ado, dash_render.py, test/test_kpi_values.py</files>
  <action><![CDATA[Apply TR-50.1 and TR-50.2 in dash.ado (syntax weight classes, the pweight refusal with the measured text, the variable-only rule, the two globals and the two JSON keys after "update"). In dash_render.py apply TR-50.3 (_kpi_statistic with weights and kind; _stata_wpercentile after _stata_percentile; _compute_kpi_stat_on_df forwarding from the KPI spec's wexp/weight; its copy-list entry after _natural_cubic_spline), TR-50.4 (dash_wstats and dash_wpctl between dash_kernel and the agg_sources comment; dash_apply_kpis reads k.wvar/k.wkind; kpi_config at :45313 gains wvar and wkind) and TR-50.5. Flip test_kpi_values.py:283 per the stubs. Run test/test_kpi_weights.py (not the served class), test/test_kpi_values.py, test/test_kpi_brush.py, test/test_statistical_helpers.py -k CarriesEveryName, and the S50 truth block driver through scripts/stata_slot.sh.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_kpi_weights.py test/test_kpi_values.py test/test_kpi_brush.py -q -k "not served" prints all passed; the truth-block log shows U50-1..U50-11 PASS]]></verify>
  <done>Weighted and new statistics compute identically in Stata's truth, Python and the saved page's script.</done>
</task>

<task type="auto" id="50-03">
  <name>Serve the weights, document and commit H2k</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[Edit the served template's _compute_kpi (:48654-48672) to take wexp and wkind and pass df[wexp] to _kpi_statistic, and _dash_kpi_value (:50168) to forward kpi.get('wexp',''), kpi.get('weight',''); add the parity entries (extend kpi_for). Run test/test_kpi_weights.py -k served, test/test_server_kpi_statistics.py, DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k weighted. Edit the KPI Cards help paragraphs (TR-50.8). Replace the <!-- WP-31 H2k --> marker under "### Fixed in WP-31" with "dash kpi takes [aweight fweight iweight] with summarize's formulas and adds kurtosis, semean and range, in both modes (WP-31, H2k)"; close BUGS.md "Dashboard extensions: KPI weights and statistics"; rewrite the GAPS3 H2k Tracked line. The H2k Tracked line takes the Closed form with `commit pending` (DECISIONS A11). Commit on wp31-s50 with the body forms (Fixture: test/fixtures/kpi_weights_truth.json (scripts/extract_kpi_weights_truth.do)).]]></action>
  <verify><![CDATA[git log -1 --format=%s ends "(WP-31 H2k)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0; python3 -m pytest test/test_fixtures_are_committed.py test/test_tracking_documents.py -q passes]]></verify>
  <done>H2k is committed: weighted KPI cards serve and save alike, with help, CHANGELOG, BUGS.md and GAPS3 updated.</done>
</task>

## Section completion criteria

- Every statistic × weight class equals Stata's measured value in Python, JS and both rendered modes; `pweight` and expression weights are refused with the measured/stated texts.
- U50-1..11 pass; the flip carries its reason; the fixture is committed with `_meta`; one commit `(WP-31 H2k)`.

## Notes

- **JS placement (BRIEF).** `dash_wstats`/`dash_wpctl` go between `dash_kernel` and the "// agg_sources is a Bokeh model list" comment, never between `dash_pctl` and "// Stata's kernels", or `js_runner`'s slice misses them. The brush code (`_wire_brush_callbacks`, :45389-45392) slices `_pctl` from `dash_pctl` to the kernels comment and `_helpers` separately -- confirm `dash_wstats` is inside the `_helpers` slice the brush concatenates; if not, report it to the merger rather than widening the slice (the `code = (...)` statement is S51's hunk and its `CustomJS(...)` construction S52's, A28).
- **R12 and the template (A28).** S50's template edit is confined to `_compute_kpi` and `_dash_kpi_value`; S51's to the link block; S52's to the `document_ready` lines. Batch-17 hunk note for the merger: S50 = `dash_apply_kpis` body + `dash_wstats`/`dash_wpctl` insertion + `_need` two lines + `_compute_kpi`/`_dash_kpi_value`; apply S50 first.
- **Copy lists (R2):** `_stata_wpercentile` after `_natural_cubic_spline` (statistical helpers tuple :47446-47503).
- **Security:** the weight name passes `confirm numeric variable` in Stata and `_dash_is_stata_name` before becoming a column key; no user text reaches JS.
- **python_exec hazard:** every Stata run through `scripts/stata_slot.sh`; `global dash_nobrowser 1`.
- **Commit body forms:** `Regression: test/test_kpi_weights.py::TestWeightedStatistics::test_python_matches_stata[mean-aweight] -- failed at 6370ca4 with TypeError: _kpi_statistic() got an unexpected keyword argument 'weights'`; `Flipped: test/test_kpi_values.py::TestEveryStatisticMatchesStata::test_the_statistics_the_command_does_not_yet_accept -- renamed test_var_cv_iqr_skewness because the four are accepted since WP-28`; `Fixture: test/fixtures/kpi_weights_truth.json (scripts/extract_kpi_weights_truth.do)`; `BUGS.md: "Dashboard extensions: KPI weights and statistics" (closed)`; `GAPS3: H2k Tracked`.
- **Decisions for ratification:** weight classes per `summarize` with `pweight` refused (D-50a); variable-only weights (D-50b). **Decided:** the batch-17 R12 exception with recorded disjoint hunks and merge order 50 → 51 → 52 (DECISIONS A28).
- **Tracked line (A11):** `commit pending`; no amend. **A14:** 50-01 appends the one H2k block.
