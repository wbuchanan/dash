# Section 05: Date computations in Stata units

> Part of: WP-29 · P0: P0.8, P0.20 · Sources: REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a, REM-08-04-C12 (P0.8); GAPS2-E1-residual (P0.20) · Risk: red · Batch: 1 · Depends on: 01 · Blocks: 10, 11, 12 · Case prefixes: DU (P0.8), KD (P0.20) · Tasks: 18, 2 commits (P0.8, then P0.20)

Conventions used below: `<wt>` is the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s05` (branch `wp29-s05`, cut from `wp29-p0` after step 0a); `<scratch>` is `/tmp/dash-wp29-s05`; `<base>` is the sha in `<scratch-of-orchestrator>/batch-1-base.txt` (the "failed at" sha). Line numbers are `7421d3d`'s (the batch-1 base changes only `test/test_packaging.py` and the audit file, so they hold in the worktree); symbols are authoritative.

## Review amendments (design review of u08, binding)

**Ratified 01oct2026:** the maintainer struck D05-1 ("Keep the date axis."); D05-2 … D05-7 stand. dash keeps its date axis when every layer is computed and the first is `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` over a date. Those layers are still COMPUTED in Stata units (the P0.8 fix stays) and drawn at their dates through `_on_axis`. Applied as index.md's "If struck" column says:
- TR-05.10 loses its D05-1 rule; `_DASH_UNIT_LABELLED_TYPES` is never created, and the served constants tuple gains nothing (TR-05.3).
- The 12 numeric-label cases leave `TestTheAxisRule::test_the_axis_is_twoways` (now 10 cases) and are pinned instead as the ratified divergence by `::test_a_unit_labelled_first_layer_keeps_the_date_axis`. `test_a_lone_fit_is_drawn_in_day_numbers` becomes `test_a_lone_fit_is_drawn_at_its_dates`.
- 05-07 keeps only the A10 half (lpoly/lpolyci with `bwidth(60)`). The `_UNITS` split and the lfit/qfit/lfitci/qfitci/kdensity flip are dropped, and those rows keep their ms window.
- Help (05-10), CHANGELOG/BUGS.md (05-11) and the closeout notes name lone `kdensity <date>` and the other six as one documented divergence, including the `range()` points before 01jan0100 that dash drops where twoway draws them.
- Kept and re-pinned: `_on_axis`'s marked-numeric branch, for a date layer on a mixed axis (Evidence §8, measured: twoway draws `(scatter close obs)(lfit close date)` on a numeric axis, and dash at HEAD draws the fit at 9.78e11 ms). Also kept: TR-05.11's marking of the served redraw's throwaway figure with the live figure's kinds, now pinned by `TestAfterAFilterMove::test_served_redraw_uses_the_live_figures_axis[mixed-numeric|lone-date]`.
- New parity cases (05-08) and a new residual (`xlabel(minmax)` on a mixed numeric axis, measured).

The reviewed design u08-date-units was "sound with amendments". Every amendment binds this section. Where it is carried out:

| Id | Amendment (short) | Where it is carried out |
|---|---|---|
| A1 | No non-finite number may reach `agg_configs_json`/`kpi_config_json`. Out-of-range bars and points follow one rule in both modes: they are dropped from the drawn source and from the config edges and grids, and one note names them. Tests: `JSON.parse` under node, a node filter move, a served draw. | TR-05.5, TR-05.6, TR-05.8; `TestOutOfRange` (05-02); tasks 05-04, 05-05 |
| A2 | The tick formatter, the log notes and the axis options read a univariate first layer's `var` as the x variable, in both modes (`%tdCCYY-NN-DD` reads `2001-01-01`, `%tmMon_CCYY` reads `Jan 2001`). | TR-05.9 (`_dash_axis_vars`); `TestAUnivariateDateIsOnX::test_the_axis_reads_the_variables_format`; task 05-06 |
| A3 | A date-formatted weight is converted the same way in Python and in the JS recount, or nowhere. | Decision D05-2: converted in both. TR-05.4 (`units=` reaches the weight), TR-05.7 (`ac.wdatekind`); `TestAfterAFilterMove::test_an_inert_move_changes_nothing[*-weighted]` |
| A4 | Rows are dropped jointly after conversion, before any estimator runs. `_histogram_counts` must never see a NaN. | Decision D05-3: the conversion happens inside `GlyphMapper._masked`, before its joint mask. `TestTheUnitHelpers::test_layer_units_drops_unconvertible_rows_jointly` |
| A5 | In JS, a value whose conversion returns `null` is dropped, both in the agg pair loop and in `dash_apply_kpis`. | TR-05.7, TR-05.14; `TestTheJsUnits::test_the_pair_loop_converts_and_drops_out_of_range`, `TestKpiOfADate::test_js_drops_out_of_range_values` |
| A6 | Flip `test_kpi_format.py::TestFirstPaint::test_every_kpi_row_of_the_fixture_saved`. It converts the statistic from ms at :195-197. Also flip `test_date_range.py:994` (`max == _MS[4]` becomes `2936549`). | Task 05-15 |
| A7 | Regression tests, in both modes, for what the axis move fixes: `yline(.002)`, `xline(15000)`, `xlabel(15000 15100)` and `yscale(log)` on `histogram date`. | `TestAUnivariateDateIsOnX` (05-02) |
| A8 | Name the nearby sites that stay out of scope, with their ids: `barwidth()` (GAPS2 A3); `function`/`scatteri`/`pci`/`pcarrowi` on a date axis (P1.23); the histogram tooltip in epoch ms (P1.23). Those fixes should reuse `_dash_units_to_axis`. | Boundaries; Notes for the closeout |
| A9 | Match twoway's first-plot axis-label rule where it is cheap: when every layer is computed and the first is `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci`, the axis is numeric and the layers are drawn in Stata units. | **Struck 01oct2026** (D05-1, "Keep the date axis."). Evidence §6 (with `qfitci` measured here) is kept as the measured basis of the documented divergence. `TestTheAxisRule::test_a_unit_labelled_first_layer_keeps_the_date_axis` pins dash's date axis; task 05-10 documents it. |
| A10 | The `_COMPUTED` flip's rationale: lpoly/lpolyci drew nothing on the twelve rows for two reasons, ms units and HEAD's default bandwidth. Flip with an explicit `bwidth(60)` and do not claim that the default draws. | Task 05-07; the `Flipped:` line text is given there |

### Decisions this section takes (each with its evidence; ratified 01oct2026, with D05-1 struck)

- **D05-1 (A9). STRUCK 01oct2026, maintainer's answer verbatim: "Keep the date axis."** twoway labels an axis by the first plot's own x (or y) variable.
  - The generated grids of `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` and `lpolyci` carry no date format, so with one of these first twoway's axis is numeric.
  - With `histogram`, `lowess`, `mspline`, `mband`, `fpfit`, `fpfitci`, `scatter`, `line` or `area` first, the axis shows dates.
  - Measured as SVG tick text (Evidence §6).
  - **dash does not adopt that rule.** Its axis rule is today's, plus the univariate x key (TR-05.10). An axis is a date axis when every layer's variable on it is a date of one kind (`_dash_figure_date_kind`'s all-agree test).
  - Every computed layer is still computed in the variable's Stata units (TR-05.4). It is drawn at the dates its Stata values denote (TR-05.5), so a lone `lfit close date` has twoway's fitted line, on a date axis where twoway's axis is numeric.
  - **The divergence.** twoway labels numbers in 12 measured cases: `kd_td lfit_td qfit_td lfitci_td qfitci_td lpoly_td lpolyci_td kd_then_hist lfit_then_scatter lfit_then_lowess kd_tm lfit_ydate`. dash keeps dates in all 12, and that is one documented divergence. It is pinned by `TestTheAxisRule::test_a_unit_labelled_first_layer_keeps_the_date_axis` and named in the help (05-10).
  - **A consequence, also documented.** For `kdensity date, range(-1000000 15400) n(5)`, twoway draws all 5 points on its numeric axis from -1000000 to 0 (Evidence §6). On a date axis, dash drops the 2 points before 01jan0100 with the off-dates note (D05-5).
  - **Applied as index.md's "If struck" column says:**
    1. TR-05.10's D05-1 rule and its constant `_DASH_UNIT_LABELLED_TYPES` are dropped, and nothing joins the served constants tuple;
    2. the A9 cases leave `test_the_axis_is_twoways`, and the A9 halves of the 05-07 flips are dropped;
    3. the help names lone `kdensity <date>` as a divergence;
    4. everything else stands. The marked-numeric branch of `_on_axis` and TR-05.11 still serve the mixed axis (D05-4, Evidence §8).
- **D05-2 (A3, option a).** A date-formatted weight is read in its Stata value in both languages, because twoway reads a weight in its Stata value. Python converts it inside `_masked` (D05-3), so `_layer_weights`' negative and non-integer checks see the Stata value, as `marksample` does. JS converts it in the pair loop through `ac.wdatekind` before its `!(w > 0)` test.
- **D05-3 (A4).** The single input gate is `GlyphMapper._masked(source, view, *varnames, units=None)`, with a keyword-only `units` map `{name: kind}`.
  - Each named column is converted by `_dash_date_units` before the joint NaN mask, so x, y and w are dropped together and nothing non-finite reaches an estimator.
  - `_layer_weights` gains the same keyword and passes it to each of its six `_masked` calls.
  - Both stay `@staticmethod`, so the static calls in the tests (`test_statistical_helpers.py:388`) keep working.
  - `GlyphMapper._layer_units(self, ...)` is the instance wrapper that passes `units=self.date_vars`.
  - This replaces the design's "convert after `_layer_weights`", which converted after the weight checks and could not satisfy A3 and A4 together.
- **D05-4.** `GlyphMapper._on_axis(fig, values, var, axis)` decides from the figure, not from the variable alone:
  - a variable that is no date is returned unchanged;
  - a figure marked by `_dash_mark_date_axes` converts with that axis's kind, or returns the values unchanged when the axis is not a date axis. With D05-1 struck that happens only on a mixed axis, where a date shares the axis with a non-date or with another date kind: `(scatter close obs)(lfit close date)`, Evidence §8. twoway draws the fit there at its Stata values.
  - an unmarked figure (a mapper used on its own) converts by the variable's kind.

  The served app redraws a layer on a throwaway `bokeh_figure()` (dash_render.py:30301). That figure is marked with the live figure's kinds (TR-05.11), so a served recompute draws on the axis the live figure drew. On a mixed numeric axis that is day numbers; unmarked, it would be epoch ms, because the fallback converts by the variable. On a date axis it is ms at the dates.
- **D05-5 (A1).** A position outside Stata's dates is NaN from `_dash_units_to_axis`. Each mapper drops it from the drawn source, and the histogram/kdensity config is built from the kept arrays only. `json.dumps` keeps its default `allow_nan=True`: making it raise would turn a future defect into a failed build, so the guarantee is by construction and is pinned by `TestOutOfRange` and `TestTheConfig::test_no_config_number_is_non_finite`.
- **D05-6.** The fixture is extracted (05-01) before the failing tests (05-02), because the failing tests assert Stata's numbers. Extraction reads Stata and changes no dash code, so rule 7's order still holds: no fix exists before its failing test.
- **D05-7.** `count` and `dcount` of a date keep today's millisecond floats; both are unit-free. `unitkind` is `""` for them.

## Overview

DROPIN-REMAINING.md §3 P0.8: "**Computed layers on a date variable run in milliseconds.** histogram/kdensity densities are per ms, and `width()`, `start()` and `bwidth()` are read as ms. lpoly/lpolyci draw nothing. histogram/kdensity put the date axis on Y." P0.20: "**KPI `sd`, `var`, `iqr`, `cv` and `sum` of a date are computed in epoch ms.** `sd` is 86,400,000× Stata's value on a %td variable."

The cause is one input gate. The loader holds a date as epoch milliseconds, the unit the Bokeh axis is drawn in, and every computed layer and every KPI statistic reads that column as it is held: `GlyphMapper._masked` → `_dash_float_values` (dash_render.py:8410-8432, :459-500), and `_dash_kpi_column` (:771-793). twoway computes in the variable's own Stata units: days for `%td`, ms after 01jan1960 for `%tc`, periods for `%tw/%tm/%tq/%th`, years for `%ty`. Measured on `sysuse sp500` (Evidence §1-§2):
- `width(30) start(14975)` gives twoway 13 bars and dash 15 bars, with every row in the last.
- A `%td` density is `.0029992` per day in twoway and `3.47e-11` per ms in dash.
- `lpoly close date, bwidth(30)` draws Stata's curve, and draws 0 points in dash.
- `sd(date)` is `105.3335` in twoway and `9.10e+09` in dash.

After this section:
- The computed-layer and KPI inputs are converted from ms to Stata units once, at the input gate (`_masked` with `units=`; `_dash_kpi_column` with `kind`).
- Every computed output is converted back to the axis's unit once, where each mapper builds its glyph source (`_on_axis`).
- User options are then read in Stata units with no option-specific code: `width()`, `start()`, `bin()`, `discrete`, `bwidth()`, `range()` and `n()`.
- Both renderers share the change, because the served app runs the same `GlyphMapper` and module helpers.
- The saved page's existing JS recounts (histogram, kdensity, KPI) convert their inputs with the existing JS twin `dash_stata_value_of`.
- histogram/kdensity draw their variable on x.
- A lone `lfit`/`kdensity`/... over a date keeps dash's date axis and is drawn at its dates. twoway labels day numbers there, which is the documented divergence (D05-1 struck 01oct2026). A date layer on a mixed numeric axis is drawn at its Stata values, as twoway draws it (Evidence §8).
- Out-of-range positions are dropped with one note, and no non-finite number reaches page JSON (A1).

Why one section: P0.8 and P0.20 share one defect, the date column read in ms, and one fix pattern, convert at the gate and draw on the axis. Both modes share the helpers.

**Test order and commit rule.** Two P0 entries, two cycles, two commits (index.md step 1).
1. Task 05-01 extracts the fixture and 05-02 writes every P0.8 regression test against the unmodified worktree. The failure text goes to `<scratch>/05-P0.8-failure.txt`, and nothing is committed.
2. Tasks 05-03 to 05-10 make P0.8 green, flip its pins, add its truth block and help text. Task 05-11 closes P0.8 and makes commit 1, `... (WP-29 P0.8)`.
3. Task 05-12 writes the P0.20 tests against the tree commit 1 leaves and saves `<scratch>/05-P0.20-failure.txt`.
4. Tasks 05-13 to 05-17 fix P0.20. Task 05-18 makes commit 2, `... (WP-29 P0.20)`.

No test-only commit exists, and no commit is red.

## Risk: [red] — thirteen mappers, two JS recounts, the KPI path and the axis rule change in both renderers at once, and a missed conversion draws a layer in the wrong unit with no error

**Why.** A layer converted on the way in but not on the way out lands near 1970, or near 15,000 ms. A JS recount that converts differently from Python changes the bars on the first filter move. A served redraw on an unmarked throwaway figure draws a date layer of a mixed numeric axis in ms (about 9.8e11 beside `obs` 1..248, Evidence §8) after the first move.

**Risk factors.**
1. Thirteen `map_*` methods each have their own output columns.
2. `_FILTER_JS`'s histogram/kdensity blocks are sliced by text markers in `test/js_runner.py:417-445`.
3. `dash_stata_value_of(null)` reads `Number(null)` as 0, a 1960 date.
4. The KPI value now has one unit in both writers; the date branch used to convert from ms.
5. A hostile `start()`/`range()` can put a bar before 01jan0100; JSON `NaN` kills the page's callback (`JSON.parse('[NaN]')` throws, review A1).
6. Adding lpoly/lpolyci to `_COMPUTED` (A10) adds parametrisations to `test_date_range.py` and, through its import, to `test_served_dates.py`. The univariate x key moves any pin of a histogram/kdensity date on y; 05-08's fallout run finds and flips such pins with `Flipped:` lines. With D05-1 struck, no lone-fit date-axis pin moves.
7. Merge conflicts with S07 (same `_make_figure_body`, merged first), S11 (rewrites `map_lpoly`/`map_lpolyci`, batch 2) and S12 (stale cue on the same recount, batch 2).

**Mitigation.**
1. One gate in, one gate out (`_masked(units=)`, `_on_axis`). A test per mapper type (`TestEveryComputedLayer`, `TestTheAxisRule`) and Stata truth for every non-affine estimator (histogram, kdensity, lpoly, fpfit, `%tm` lfit).
2. The JS markers `src.data = { x: xs, y: ys };`, `if (ac.type === 'histogram') {`, `} else if (ac.type === 'kdensity') {`, `// DASH_KDE_RULE` and `// agg_sources is a Bokeh model list` are kept verbatim.
3. Every JS conversion runs after the existing null/NaN test, and a `null` result is dropped (A5).
4. One rule for the KPI value: Stata units everywhere, pinned against summarize's display text in both modes, after a move and after a brush.
5. D05-5, with tests that parse the page JSON under node.
6. Flipped with `Flipped:` lines, never deleted; the collected-test count never falls (K3).
7. Merge order S07 → S05 (index.md batch 1). The anchor notes for S11/S12 are in Notes.

## Dependencies

- **Depends on:** section 01 (opens the two BUGS.md entries for P0.8 and P0.20, places `<!-- WP-29 P0.8 -->` and `<!-- WP-29 P0.20 -->` in the `**WP-29 (drop-in P0, 30sep2026)**` group at the end of CHANGELOG `### Results that change`, adds `WP29_OPEN["P0.8"]`/`["P0.20"]`, and creates `test/test_wp29_truth.cscript` with the marker line `* ==== append new blocks above this line ====`).
- **Blocks:**
  - 10 (axis(#)/by() scales need date axes in units);
  - 11 (the lpoly port's `%td`/`%tc` truth: Stata's default bandwidth 14.5456 days, and on `%tc` 32558842 ms with 3 of 5 grid points missing in Stata itself; that needs x in units);
  - 12 (the stale cue reads the same estimation sample and the same saved recount).
- **Parallel batch:** 1. It can run with 02, 03, 04, 06, 07, 08 and 09. The batch-1 merge order is `S01, S09, S03, S02, S04, S06, S07, S05, S08`, so S05 lands after S07 (both touch `_make_figure_body`; S07 changes no JS) and before S08 (the served template's launcher).
- **Why:** nothing in batch 1 depends on S05, and S05 needs only S01's tracking scaffolding.

## Evidence

GitNexus (rule R8). In the planning session, `gitnexus_impact` returned `Error: Repository "dash" not found. Available: TYME, PhotoShootPlannerPro`, so the blast radius was measured by grep at `7421d3d` (direct references in `dash_render.py` / test files that name the symbol):

| Symbol | refs in dash_render.py | test files | Expected risk |
|---|---|---|---|
| `GlyphMapper._masked` | 14 (map_area 8017, map_spike 8297, `_layer_weights` ×6, fpfit 10010, fpfitci 10080) | 2 | HIGH (shared reader) |
| `GlyphMapper._layer_weights` | 14 (13 computed mappers) | 3 | HIGH |
| `_dash_figure_date_kind` | 4 (def, `_figure_date_kind`, served template ×2) | 1 | MEDIUM |
| `DashRenderer._make_figure_body` | 3 | 1 | HIGH (index.md R8) |
| `_dash_kpi_column` / `_kpi_column` | 3 / 2 | 1 / 2 | MEDIUM |
| `_dash_format_kpi_value` | 3 | 3 | MEDIUM |
| `_kpi_callback_config` | 3 | 2 | MEDIUM |
| `map_histogram`, `map_kdensity`, the 11 fit/smooth mappers | 1 each (dispatch) | 6-10 each | MEDIUM |

The executor runs `gitnexus_impact({target, direction: "upstream"})` on each before editing (after `npx gitnexus analyze` if the index is stale), records the result in the commit body, and reports any HIGH/CRITICAL to the maintainer before the edit (CLAUDE.md).

### 1. Stata truth (StataNow 19.5 MP, `scripts/stata_slot.sh`, sysuse sp500: `date` %td, N=248, min 14977, max 15340)

Re-measured by the design review and in this planning pass. Quoted from the batch logs:

```
. twoway__histogram_gen date, density gen(h1 x1, replace) display
(bin=15, start=14977, width=24.2)
  h1: .0029992 .0024993 .0029992 ...            (per DAY)
. twoway__histogram_gen date, density width(30) start(14975) gen(h3 x3, replace)
TRUTH hist w30 s14975 bin=13 width=30 start=14975
  h3: .0025538 .0028226 .002957 .0025538 .0028226 .002957 .0026882 .0028226 .0022849 .002957 .0025538 .0028226 .0005376
. twoway__histogram_gen date, density bin(10) ...      bin=10 width=36.3 start=14977
discrete: bin=364 width=1 start=14977
%tm (m=mofd(date)): bin=15 width=.7333333333 start=492, first bar .1154692; width(2) start(492): bin 6, .0806452 .0846774 .0866935 .0887097 .0766129 .0826613
%tc (tc=cofd(date)+3600000*mod(_n,24)): bin=15 width=2092560000 start=1294016400000; start(1294012800000) width(604800000): bin=52
%tw: width 3.4 start 2132   %ty (yr=1950+mod(_n,40)): width 2.6 start 1950
kdensity date, nograph: r(bwidth)=31.47157681; m 1.029392267; q .3368726339; tc 2719279472; yr 3.4932545
twoway__kdensity_gen date, gen(kd kx) n(5) range(14900 15400): kd = 0 .00260856 .0028029 .00269729 .00003848
twoway__kdensity_gen m, gen(kd kx) n(5) bwidth(1) range(490 505): .00568033 .08179005 .08743657 .08035306 .00540984
lpoly close date, nograph gen(lx ly) n(5) bwidth(30): 1325.6916 1220.1454 1222.2587 1096.8882 1140.2131
lpoly close date (default): r(bwidth)=14.54557046 (S11's), %tc default 32558842.47 ms
fracpoly: regress close date   -> e(fp_pwrs) "3 3"; predict double: first=1329.538697227714 (14977), last=1106.957476610138
regress close date -> b=-.6154216803 cons=10522.03607 ; regress date close -> b=-.9063986130558567 cons=16239.25702302471
summarize date, detail: sd 105.3334549781108 var 11095.13673762570 sum 3758900 mean 15156.85483870968 p25 15065.5 p50 15154.5 p75 15250.5 skewness .0210125
display %9.0g: sd [ 105.3335] var [ 11095.14] sum [  3758900] cv [ .0069496] skew [ .0210125] iqr [      185]
m: sd 3.44531335951123 cv .0069254775 sum 123376 iqr 6.5 ; %9.0g sd [ 3.445313] cv [ .0069255]
tc: sd 9101263136.46 mean 1309592845161.29 sum 324779025600000 cv .0069496891
q sd 1.127492233 ; w sd 15.04588287 ; yr sd 11.69171053 sum 488316
start(15000) above the minimum: r(198)
```

`dash.ado` already registers KPI values in Stata units (log line `dash: KPI 'ksd' registered (sd(date) = 105.3334549781108).`). `dash.ado:3962-3975` already checks `start()` in Stata units, from above only. Neither needs a change.

### 2. dash at HEAD (this planning pass; `probe_saved.py`/`probe_kpi.py` harness: spec built in Python, saved through `DashRenderer`, served through `ServerAppBuilder`)

```
== saved hist             xaxis LinearAxis, yaxis DatetimeAxis, ytitle Density; Quad top max 3.47129654314405e-11 (per ms); left[0] 978393600000
== saved hist_w30         WARN 'dash: histogram option width(30) would need more than 1000 bins; deriving the width from the data instead.'
                          15 bars, left[0] 14975.0 (ms after 1970), top max 1.485506235011692e-11, all rows in the last bar
== saved kdens_bw10       yaxis DatetimeAxis; y max 0.00013524604702619695 (bwidth read as 10 ms)
== saved lpoly_bw30       x_lp: 0 points
== saved fpfit            y_fp[0] 1329.5112974409712   (Stata 1329.538697227714)
== saved hist_tm          bins cut in ms over unequal months, top 4.40e-11
SAVED first paint  {'k_sd': '9.10e+09', 'k_var': '8.28e+19', 'k_iqr': '1.60e+10', 'k_cv': '.0091564', 'k_sum': '2.46e+14', 'k_mean': '30jun2001', 'k_p50': '28jun2001', 'k_skewness': '.0210125'}
SAVED after move close>=1200 {'k_sd': '5.83e+09', 'k_cv': '.0058986', ...}   SERVED identical, first paint and after the move
histogram date, yline(.002):        Span width at -315619027200.0   (the density axis is marked %td)
histogram date, xline(15000):       Span height at 15000.0          (ms after 1970)
histogram date, xlabel(15000 15100): x ticks [15000.0, 15100.0]
histogram date, yscale(log):        "dash: yscale(log) is meaningless for the date variable ''; drawing a date axis instead."
histogram date with %tdCCYY-NN-DD:  the date-axis formatter's fmt is '%td' (xvar is '' for a univariate first layer)
lpoly on the twelve 30-day rows (test_date_range._spread_frame): bwidth(60) -> 0 points; default -> 0 points
```

Feeding the Stata values to dash's existing estimators gives Stata's numbers. The fix is the units alone:

```
hist w30 13 [0.0025538, 0.0028226, 0.002957, ..., 0.0005376]       hist def 15 14977.0 24.2 [0.0029992, 0.0024993, 0.0029992]
kde bw 31.47157680629159 [0.0, 0.00260856, 0.0028029, 0.00269729, 3.848e-05]
lpoly bw30 [1325.6916, 1220.1454, 1222.2587, 1096.8882, 1140.2131]
tm hist 15 492.0 0.7333 0.1154692 ; tm w2 6 [0.0806452, 0.0846774, 0.0866935, 0.0887097, 0.0766129, 0.0826613]
kde tm bw 1.0293922670450035 ; kde m bw1 [0.00568033, 0.08179005, 0.08743657, 0.08035306, 0.00540984]
fpfit on day numbers: first 1329.538697190932 (reldif 2.8e-11), last 1106.9574765725993 (reldif 3.4e-11)
lpoly twelve rows, bwidth 60 days: 12 of 12 finite ; default (HEAD ROT): 0 of 12 (S11's)
round trip: td 14977.5 -> 978436800000 -> 14977.5 ; tc 1294016400000 -> 978397200000 -> 1294016400000 ;
            tw 2132, 2183 / tm 492, 503 / tq 164 / th 82 / ty 2001 -> period start -> same number ; tm 492.5 -> 2001-01-16 12:00
            tw 2183 (2001w52) starts 2001-12-24, 2184 starts 2002-01-01
```

### 3. The input gate and the KPI column (dash_render.py)

`GlyphMapper._masked`, :8410-8432 (every computed mapper reaches it through `_layer_weights`, :8435):
```python
cols = [_dash_float_values(source.data[v]) for v in varnames]
n = len(cols[0]) if cols else 0
sel = GlyphMapper._view_mask(view, n)
if sel is not None:
    cols = [c[sel] for c in cols]
finite = ~np.isnan(cols[0])
for c in cols[1:]:
    finite &= ~np.isnan(c)
return tuple(c[finite] for c in cols)
```
`_dash_kpi_column`, :771-793:
```python
if not pd.api.types.is_datetime64_any_dtype(col):
    return col
if str(stat).lower().strip() == "sum":
    warnings.warn(f"dash: sum({varname}) adds up dates, which has no meaning. "
                  f"The result is shown as a number of milliseconds since 01jan1970.", UserWarning)
return (col.dropna().astype("datetime64[ms]").astype("int64").astype("float64"))
```
`_dash_format_kpi_value`, :23492-23529, date branch: `sv = _dash_stata_value_of(v, kind); return "." if sv is None else _dash_fmt_text(sv, fmt)`. The served `_compute_kpi(df, stat, varname)` (template :29952-29968) calls `_dash_kpi_column(series, stat, varname)` and swallows any exception as NaN. Its callers are :30905, :31253 and :31335.

### 4. The axis decision (both renderers)

`_dash_figure_date_kind`, :670-688, folds a univariate plot's `var` into the **y** key:
```python
name = plot.get(key, "") or (plot.get("var", "") if key == "yvar" else "") or fallback
```
- Saved: `_make_figure_body` takes `xvar = plots[0].get("xvar", "")` (:25931), which is `''` for a histogram (dash.ado:4109 writes only `"var"`). That `''` reaches `_figure_date_kind` (:25993), the log notes (:25996-26009), the formatter loop (:26028-26034) and `_dash_apply_axis_options` (:26116).
- Served: the template does the same with `xv` (:30341, :30379-30407, :30474).
- The served redraw draws on `_tfig = bokeh_figure()` (:30301), which is never marked.
- `_dash_mark_date_axes` (:691-695) stores `fig._dash_date_kinds`, and `_dash_axis_date_kind` (:698-701) reads it.

### 5. The saved page's recounts (`_FILTER_JS`)

- **Agg loop** (:16308-16495).
  - The pair loop (:16339-16357) pushes raw ms values and raw weights.
  - `dash_scale` (:16361-16374) takes widths from `edges` (ms).
  - The count (:16395-16405) uses `ac.start`/`ac.width`/`n_bins`.
  - The kdensity branch evaluates and draws at `ac.x_grid` (:16483-16493).
- **KPI loop.** `dash_apply_kpis` (:16076) filters `vals` (:16105-16109) and the date branch (:16175-16178) converts `result` from ms with `dash_stata_value_of`.
- **Converter.** `dash_stata_value_of` (:15528-15550, in `_DASH_FMT_JS`, which `_DASH_FILTER_MASK_JS` and therefore `_FILTER_JS` prepend) returns `null` outside Stata's range. `Number(null)` is 0.
- **Page JSON.** `agg_configs_json = json.dumps(_agg_cfgs_all)` (:27850) uses the default `allow_nan=True`. Verified by the review: `json.dumps` gives `{"x_grid": [NaN, 1.0]}` and node's `JSON.parse` throws `Unexpected token 'N'`.

### 6. twoway's axis-label rule (SVG tick text, graph export)

Since D05-1 was struck (01oct2026), this table is the measured basis of the documented divergence, not a rule dash adopts. In every row that shows numbers (`15000|...`, `490|...`, `-700000|...`, `-1000000 .. 0`), dash keeps a date axis.

```
histogram date        01jan2001|01apr2001|...        kdensity date          15000|15100|...|15400 (title x)
lfit close date       15000|...                       qfit close date        15000|...
lfitci close date     15000|...                       qfitci close date      15000|...   (measured in this pass)
lpoly / lpolyci       15000|...                       lowess/mspline/mband   01jan2001|...
fpfit close date      01jan2001|...                   fpfitci close date     01jan2001|... (measured in this pass)
(kdensity)(histogram) 15000|...                       (histogram)(kdensity)  01jan2001|...
(lfit)(scatter)       15000|...  <- dash keeps dates  (scatter)(lfit)        01jan2001|...
(lfit)(lowess)        15000|... (this pass)           lfit date close        y: 15000|...
(scatter date close)(lfit date close)  y: 01jan2001|...   kdensity m   490|495|500|505 (this pass)   histogram m  2001m1|...
twoway histogram date, start(-700000) width(100000):  bin=8, x ticks -700000|27oct0556|07mar1070|16jul1583|22nov2096, one populated bar
twoway kdensity date, range(-1000000 15400) n(5):  numeric axis -1000000 .. 0
```

### 7. Tests that pin today's behaviour (flip, never delete)

- `test/test_date_range.py` `_COMPUTED` (:703-709) excludes `lpoly`/`lpolyci`. `_plot_for` (:712-722) gives no bandwidth. Together these drive `TestAComputedLayerIsDrawnOnTheDateAxis::test_every_x_it_draws_lies_among_the_dates[*]`, which expects ms extents for every type. `test_served_dates.py` imports `_COMPUTED` (:51), so its `TestTheServedFigureReadsTheDateAsTheSavedOne::test_every_layer_is_drawn_where_the_saved_one_is[*]` (:200-213) gains rows with it. With D05-1 struck, only lpoly/lpolyci change here: they join `_COMPUTED` with `bwidth(60)` (A10). Every other row keeps its ms window, because a computed layer is drawn back at its dates on the date axis; on these single-variable figures the conversion is affine for `%td`. Counts measured at `7421d3d` (01oct2026): `python3 -m pytest test/test_date_range.py --collect-only -q -n0 -p no:cacheprovider | tail -1` gives `176 tests collected`, with 68 rows of `test_every_x_it_draws_lies_among_the_dates`. The same for `test/test_served_dates.py` gives `103 tests collected`, with 34 rows of `test_every_layer_is_drawn_where_the_saved_one_is`.
- `test/test_date_range.py::TestTheDateHelpers::test_a_kpi_sum_of_dates_neither_wraps_nor_names_the_wrong_epoch` (:982-994): `40_000 * _MS[4]`, the ms note, and `max == _MS[4]`.
- `test/test_date_range.py::TestTheDateHelpers::test_the_page_callback_writes_a_kpi_year_in_four_digits` (:1009-1030): feeds `result = -59011459200000` (ms).
- `test/test_server_layer_defects.py::TestTheKpiFormatHelpers::test_a_date_valued_statistic_is_shown_as_a_date` (:1105-1113): passes `_MS_02JAN2002` (ms).
- `test/test_kpi_format.py::TestFirstPaint::test_every_kpi_row_of_the_fixture_saved` (:186-198): converts `got` with `_dash_stata_value_of` at :195-197 (A6).
- Stay green and are run, not flipped:
  - `test_dates.py::TestDateFilterActuallyFilters::test_the_kpi_config_tells_the_callback_it_is_a_date` (:745);
  - `test_kpi_format.py::TestConfig::test_the_config_carries_fmt_and_storage_and_not_the_legacy_fields` (:373; `datekind` is kept);
  - `test_served_dates.py::TestTheServedKpiReadsTheDate::test_a_sum_of_dates_is_named_as_the_saved_page_names_it` (:266; the new note keeps "adds up dates");
  - `test_dates.py::TestDatetimeAxis::test_a_date_y_variable_gets_a_datetime_y_axis` and `test_served_dates.py:170` (line plots);
  - `test_statistical_helpers.py:388` (static `_layer_weights`);
  - `test/js_runner.py::run_filter_js_block` (:417-445) and its users (`test_js_runner.py:330`, `test_histogram_edge_rule.py`): their hand-built `ac` has no `unit_edges`/`bin_first`/`x_eval`, so the new fields default to today's behaviour.

### 8. A date layer on a mixed numeric axis, and `xlabel(minmax)` there (measured 01oct2026, after the ratification)

dash at the planning base (`7421d3d` plus untracked plan files). The probes `probe_axis.py` and `probe_minmax.py` are in `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp29r/s05/`. The frame has 12 rows: `date = 14977 + 30*i` (`%td`), `close`, and `obs = 1..12`. Pages are saved through `test_date_range._saved` and served through `_served`, read with `test_served_dates._served_fig`:
```
$ python3 probe_axis.py
kd_lone saved x ['LinearAxis'] y ['DatetimeAxis'] [('x', 978393600000.0, 1006905600000.0)]
kd_lone served x ['LinearAxis'] y ['DatetimeAxis'] [('x', 978393600000.0, 1006905600000.0)]
lfit_lone saved x ['DatetimeAxis'] y ['LinearAxis'] [('x', 978393600000.0, 1006905600000.0)]
lfit_lone served x ['DatetimeAxis'] y ['LinearAxis'] [('x', 978393600000.0, 1006905600000.0)]
mixed_obs_lfit saved x ['LinearAxis'] y ['LinearAxis'] [('x', 978393600000.0, 1006905600000.0)]
mixed_obs_lfit served x ['LinearAxis'] y ['LinearAxis'] [('x', 978393600000.0, 1006905600000.0)]
figkind mixed x: None
$ python3 probe_minmax.py          # graph_options {"xlabel": "minmax"}
lfit_first LinearAxis [978393600000.0, 1006905600000.0] []
obs_first LinearAxis [1.0, 12.0] []
```
(`mixed_obs_lfit` is `(scatter close obs)(lfit close date)`; `lfit_first` is `(lfit close date)(scatter close obs)`.)

twoway (`scripts/stata_slot.sh`, `mixed.do`: `sysuse sp500, clear`, `gen obs = _n`, `twoway (scatter close obs) (lfit close date)`, `graph export mixed.svg`) gives these SVG texts:
```
['1000', '1100', '1200', '1300', '1400', '0', '5000', '10000', '15000', 'Closing price', 'Fitted values']
summarize date: DMIN 14977 DMAX 15340
```
So twoway's x axis is numeric (0 to 15000) and the fit lies at the day numbers 14977-15340. Today dash draws it at 9.78e11 ms beside `obs`. After this section the live figure is marked `(None, None)`, so `_on_axis` returns day numbers, as twoway draws them. An unmarked served throwaway figure would convert by the variable's kind and redraw at ms after a move, so TR-05.11 is still required. `xlabel(minmax)` reads the first layer's variable column (`date`, in ms) even where the axis is numeric. That stays a residual (P1.23).

## User stories

- **US-05.1** As a twoway user with a daily date, I want `dash histogram date, width(7) start(14975)` to draw week-wide bars from 01jan2001 with densities per day, so that I get the bars `twoway histogram` draws.
- **US-05.2** As an analyst, I want `kdensity`, `lpoly`, `lpolyci`, `fpfit` and the other fits over a date to read `bwidth()`, `range()` and `n()` in the date's units and to equal Stata's curve, so that a published curve is Stata's.
- **US-05.3** As a twoway user, I want a histogram's or kdensity's date on the x axis, labelled in the variable's own picture (`2001-01-01`, `Jan 2001`). I want a date axis kept under a lone kdensity or lfit of a date, as the maintainer ratified on 01oct2026; twoway labels day numbers there, and the help names that difference. I want a date layer that shares an axis with a plain number drawn at its Stata values, as twoway draws it. I also want `yline()`, `xline()`, `xlabel()` and `yscale(log)` to mean what they mean in twoway.
- **US-05.4** As a dashboard reader, I want the saved page's histogram and kdensity, and the served app's every layer, to stay in the date's units after a filter move, so that the first move does not reshape the picture.
- **US-05.5** As an analyst, I want `dash kpi sd(date)` to read `105.3335` (days), and `var`, `iqr`, `cv`, `sum` and `skewness` to be `summarize`'s, with a `%tm` mean of 2001m1 and 2001m3 reading `2001m2`, at first paint, after a move and after a brush, in both modes.
- **US-05.6** As a dashboard publisher, I want a `start()` or `range()` that reaches before 01jan0100 to draw what it can and say what it did not, never to leave a page whose filters stop working.
- **US-05.7** As the maintainer, I want Stata's own `twoway__histogram_gen`, `twoway__kdensity_gen`, `lpoly`, `fracpoly` and `summarize` output pinned in a committed fixture and re-measured live in the truth script, so that the unit rule cannot regress silently.

## Business requirements

- **BR-05.1** A histogram, kdensity, lfit, qfit, lfitci, qfitci, lowess, lpoly, lpolyci, mspline, mband, fpfit or fpfitci of a date variable gives Stata's numbers in both modes.
  - **Inputs.** It reads the variable, its weight and every numeric option in the variable's Stata units, and computes from them.
  - **Histogram.** Bar count, edges and heights equal `twoway__histogram_gen` within 1e-9 relative.
  - **Kdensity.** The curve equals `twoway__kdensity_gen` within 1e-9.
  - **lpoly.** With an explicit `bwidth()`, the curve equals `lpoly ... gen()` within 1e-9.
  - **fpfit.** The curve equals `fracpoly` predictions within 1e-9.
- **BR-05.2** A computed layer is drawn where twoway draws it.
  - On a date axis it sits at the dates its Stata values denote.
  - On a mixed numeric axis, where a date shares the axis with a non-date or another date kind, it sits at the Stata values themselves, as twoway draws it (Evidence §8).
- **BR-05.3** A histogram's or kdensity's variable is on the x axis. An axis is a date axis exactly when every layer's variable on it is a date of one kind, so every axis twoway labels with dates (10 measured cases, Evidence §6) is a date axis. In the 12 measured cases where twoway labels numbers, because `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` is first, dash keeps its date axis. That is the one documented divergence (D05-1 struck 01oct2026).
- **BR-05.4** On a figure whose first layer is univariate, the date-axis ticks use the variable's own display format. `xscale(log)`/`yscale(log)` notes name the variable, and the density axis takes `yline()`, `ylabel()` and `yscale(log)` as numbers.
- **BR-05.5** After a filter move:
  - the saved page's histogram and kdensity, recounted from the kept rows in Stata units, equal Stata's on those rows (histogram on the build's grid; kdensity with Stata's bandwidth rule);
  - the served app's every layer equals Stata's on those rows;
  - a move that removes no row changes nothing, weighted or not.
- **BR-05.6** A KPI statistic of a date variable other than `count`/`dcount` is taken of the variable's Stata values. Its card equals `summarize`'s value under the card's effective format, at first paint, after a filter move and after a brush, saved and served. `sum` is named in one note that gives the units.
- **BR-05.7** A computed bar or point outside Stata's dates (01jan0100 to 31dec9999) is not drawn, and one note per layer names how many were dropped. The rule is the same in both modes and before and after a move. No `NaN` or `Infinity` reaches `agg_configs_json` or `kpi_config_json`. A hostile option never raises.
- **BR-05.8** Every changed result is a CHANGELOG "Results that change" line naming the command, the old value and the new value. The help states the unit rule, the axis rule and the one divergence.

## Technical requirements

All in `dash_render.py` unless named. "Both modes" holds by construction for everything in `GlyphMapper` and the module helpers, because the served app copies them. The served copy-list additions are named per TR. New functions are added to `test/function_test_map.py` in alphabetical place, each naming a test that fails when its body is skipped.

- **TR-05.1 `_dash_date_units(column, kind)`.** New, placed directly after `_dash_float_values` (:459-500).
  - It reads a datetime64 or epoch-ms column with `ms = _dash_float_values(column, coerce=True)` and masks `ok = isfinite(ms) & (ms >= _STATA_MS_MIN + _STATA_EPOCH_UNIX_MS) & (ms <= _STATA_MS_MAX + _STATA_EPOCH_UNIX_MS)`.
  - It returns a float64 array:

    | kind | returned value |
    |---|---|
    | `td` | `(ms - _STATA_EPOCH_UNIX_MS) / 86_400_000.0` (keeps the time of day) |
    | `tc`, `tC` | `ms - _STATA_EPOCH_UNIX_MS` |
    | `tw`, `tm`, `tq`, `th`, `ty` | `_dash_period_values(ms, kind)` (exact at period starts, :18227-18257) |
    | any other | `ms` unchanged |

  - Values outside `ok` are NaN. It never raises: numpy errors are silenced with `np.errstate(all="ignore")`.
- **TR-05.2 `_dash_units_to_axis(values, kind)`.** New, after TR-05.1. It turns Stata values (fractions allowed) into float epoch ms.
  - `td`: `v*86_400_000.0 + E`.
  - `tc`/`tC`: `v + E`.
  - Period kinds: `f = floor(v)`; `a` and `b` are `_dash_float_values(_stata_dates_to_datetime(pd.Series(f), kind))` and the same of `f + 1.0`; the result is `a` where `v == f`, else `a + (v - f)*(b - a)`.
  - Unknown kind: all NaN.
  - The result is NaN where it is non-finite or outside `[_STATA_MS_MIN + E, _STATA_MS_MAX + E]`, and where the input is non-finite or not a number (input read with `pd.to_numeric(..., errors="coerce")` when `np.asarray(values, float)` raises).
  - Every warning raised inside (the loader's range count, the `%tC` leap-second note) is caught with `warnings.catch_warnings(); simplefilter("ignore")`. `tC` never calls `_stata_dates_to_datetime`. It never raises.
  - E is `_STATA_EPOCH_UNIX_MS`.
- **TR-05.3 Copy lists (both modes).** In `ServerAppBuilder._glyph_layer_lines` (:28312):
  - the functions tuple gains `"_dash_date_units", "_dash_units_to_axis", "_dash_axis_vars"` directly after `"_dash_period_values"` (:28613, index.md R2);
  - the constants tuple gains nothing. With D05-1 struck, `_DASH_UNIT_LABELLED_TYPES` is never defined, and the axis rule does not read `_DASH_COMPUTED_ONLY_TYPES` (the served app does not need it). At `7421d3d` it is read only by `_dash_graph_computed_cells` (:1096) and `_dash_embedded_cells` (:1167), and `sed -n 28312,28900p dash_render.py | grep -c "_DASH_COMPUTED_ONLY\|_dash_graph_computed_cells\|_dash_embedded_cells"` prints 0, so the served copy list carries neither.
  - P0.20 adds `"_dash_kpi_unit_kind"` after `"_dash_kpi_date_valued"` (:28636).
  - `_dash_period_values`, `_stata_dates_to_datetime` and `_dash_unix_ms_to_unit` are already emitted.
- **TR-05.4 The input gate (D05-3).**
  - `GlyphMapper._masked(source, view, *varnames, units=None)`: after `cols = [_dash_float_values(...)]`, when `units`, replace `cols[i]` by `_dash_date_units(cols[i], units[name])` for each name with `units.get(name)` in `_STATA_DATE_KINDS`, before the view mask and the joint NaN mask.
  - `GlyphMapper._layer_weights(source, view, options, layer, *varnames, units=None)` passes `units=units` to all six `_masked` calls (:8464, :8472, :8483, :8493, :8500, :8501). The weight column is converted there when `units` names it, so the negative and non-integer checks see the Stata value (D05-2).
  - New instance method `GlyphMapper._layer_units(self, source, view, options, layer, *varnames)` returns `self._layer_weights(source, view, options, layer, *varnames, units=dict(self.date_vars or {}) or None)`.
  - The 13 computed mappers call `self._layer_units(...)` where they call `self._layer_weights(...)` today, at :8669, :8741, :8811, :8931, :9040, :9469, :9551, :9987, :10056, :10144, :10462, :12269 and :12401.
  - `map_fpfit`/`map_fpfitci`'s `self._masked(source, view, xvar, yvar)` (:10010, :10080) gain `units=dict(self.date_vars or {}) or None`.
  - `map_lowess`'s `adjust` reads `y_all = _dash_date_units(self.dataset[yvar], self.date_vars[yvar])` when `self.date_vars.get(yvar)`, else `_dash_float_values(...)` as now (:9082-9083).
- **TR-05.5 The output gate (D05-4, D05-5).**
  - New `GlyphMapper._on_axis(self, fig, values, var, axis)` returns `(drawn, off)`, two float/bool arrays the length of `values`:
    - `kind = (self.date_vars or {}).get(var)`. Not in `_STATA_DATE_KINDS` → `(float array, all False)`.
    - `marked = getattr(fig, "_dash_date_kinds", None)`. If `marked is not None`: `kind = _dash_axis_date_kind(fig, axis)`, and with no kind → `(float array, all False)`, because the axis is numeric and the layer is drawn in Stata units. With D05-1 struck, this branch is reached only on a mixed axis (Evidence §8).
    - Otherwise `drawn = _dash_units_to_axis(values, kind)` and `off = isfinite(values) & ~isfinite(drawn)`.
  - New `GlyphMapper._drop_off_dates(self, layer, what, off, *arrays)` returns the arrays with the `off` rows removed. When `off.any()` it calls `_dash_warn_once(("off-dates", layer, what), f"dash: {layer}: {n:,} {what} outside Stata's dates (01jan0100 to 31dec9999) not drawn.")`, where `what` is `"bar(s)"` or `"point(s)"`.
  - Each mapper converts every x output with `_on_axis(fig, ..., xvar, "x")` (the univariate types use their `yvar` argument, the variable) and every y output of a y date with `_on_axis(fig, ..., yvar, "y")`. Heights and densities are never converted. Then `_drop_off_dates` runs on the source's columns together:

    | Mapper | Line | x output(s) | y outputs when y is a date |
    |---|---|---|---|
    | lfit | :8705 | `x_fit` | `y_fit` |
    | qfit | :8777 | `x_fit` | `y_fit` |
    | lfitci | :8868-8870 | `x_fit` | fit, lower, upper |
    | qfitci | :8985-8987 | `x_fit` | fit, lower, upper |
    | lowess | :9109-9111 | `x_lw` | `y_lw` |
    | lpoly | :9508-9510 | `x_grid[valid]` | `y_fit` |
    | lpolyci | :9631-9635 | the `x_lp` grid | `y_lp`, `y_lower`, `y_upper` |
    | fpfit | :10015-10017 | `x_grid[valid]` | |
    | fpfitci | :10100-10104 | `x_grid[valid]` | band columns |
    | mspline | :12306 | `x_grid` | `y_grid` |
    | mband | :12423 | `x_mids` | `y_meds` |

    histogram and kdensity are TR-05.6.
- **TR-05.6 histogram and kdensity (both modes, saved config).**
  - **`map_histogram`.** `edges, ymode = self._histogram_grid(arr, options, w)` runs on unit `arr`, and counts and tops come from the unit edges (:10156-10165), unchanged.
    - Then `axis_edges, off_e = self._on_axis(fig, edges, yvar, "x")`. A bar is off when either of its edges is off. The kept bars form one contiguous run `[i0, i1)`, because edges are monotone and only the ends can leave Stata's range. Only that run is drawn: `top = tops[i0:i1]`, `left = axis_edges[i0:i1]`, `right = axis_edges[i0+1:i1+1]`, with the note through `_drop_off_dates("histogram", "bar(s)", ...)`.
    - The config keeps `start`, `width` and `bin` (the full grid, in units) and sets `bin_edges = axis_edges[i0:i1+1].tolist()`.
    - When `self.date_vars.get(yvar)` is a date kind it also sets `datekind`, `unit_edges = edges[i0:i1+1].tolist()` and `bin_first = int(i0)`.
    - When the weight variable is a date it sets `wdatekind`.
    - Every list is finite.
  - **`map_kdensity`.** `x_range = np.linspace(_lo, _hi, n)` is computed in units (so `range()` is units). `density = _kde_curve(arr, x_range, bw, ...)` (bandwidth in units). Then `x_draw, off = self._on_axis(fig, x_range, yvar, "x")` drops off points from `x_draw`, `x_range` and `density` together (note `"point(s)"`). The source is `{"x": x_draw, "y": density}` for the kept points. The config sets `x_grid = x_draw.tolist()`, and when the variable is a date also `datekind` and `x_eval = x_range_kept.tolist()`, plus `wdatekind` for a date weight. `bw_fixed` is in units.
  - **Config fields.** `datekind`/`wdatekind` are emitted only when the kind is in `_STATA_DATE_KINDS`. The caps already bound sizes: `unit_edges` ≤ 1001 numbers, `x_eval` ≤ 10000.
- **TR-05.7 The saved JS recount (`_FILTER_JS`, agg loop :16308-16495).**
  - **Weighted pair loop.** Each pair is read with `let v = raw_col[i], w = wcol[i];`. After the existing null/undefined/NaN tests on both:
    1. `if (ac.datekind) { v = dash_stata_value_of(v, ac.datekind); if (v === null) continue; }`
    2. `if (ac.wdatekind) { w = dash_stata_value_of(w, ac.wdatekind); if (w === null) continue; }`
    3. Then `if (!(w > 0)) continue;`, moved after the conversion.
  - **Unweighted branch.** After the existing filter, `if (ac.datekind) vals = vals.map(v => dash_stata_value_of(v, ac.datekind)).filter(v => v !== null);`.
  - **Histogram block.**
    - `const edges = ac.bin_edges; const n_bins = edges.length - 1; const uedges = ac.unit_edges || edges; const first = ac.bin_first || 0; const n_grid = ac.bin || n_bins;`.
    - Counts are `n_grid` long and clamped to `n_grid - 1`.
    - `dash_scale` totals over all `n_grid` counts and returns the `counts.slice(first, first + n_bins)` heights. Densities use `uedges[i+1] - uedges[i]`.
    - The empty branch is unchanged.
  - **Kdensity block.** `const xs = ac.x_grid; const xe = ac.x_eval || xs;`. The density is evaluated over `xe` (`const ys = xe.map(...)`). Keep the line `src.data = { x: xs, y: ys };` verbatim (it is a slice marker).
  - **Markers.** These marker strings stay unchanged: `// agg_sources is a Bokeh model list`, `if (ac.type === 'histogram') {`, `} else if (ac.type === 'kdensity') {`, `// DASH_KDE_RULE`.
- **TR-05.8 No non-finite page JSON (A1).** The configs are built only from the kept, finite arrays (TR-05.6). `TestTheConfig::test_no_config_number_is_non_finite` walks every agg and KPI config of a corpus of date specs and asserts `math.isfinite` on every float. `TestOutOfRange` parses `agg_configs_json` with `json.loads(..., parse_constant=<raise>)` and under node `JSON.parse`.
- **TR-05.9 Axis variables (A2, both modes).**
  - New module helper `_dash_axis_vars(plots)` → `(xv, yv)`, placed after `_dash_figure_date_kind` (:670-688). `p0 = (plots or [{}])[0] or {}`.
    - If `str(p0.get("type","")).lower() in _DASH_UNIVARIATE_TYPES`, return `(p0.get("var","") or p0.get("xvar","") or "", "")`.
    - Otherwise return `(p0.get("xvar","") or "", p0.get("yvar","") or "")`.
  - **Saved, `_make_figure_body`.** Add `_xa, _ya = _dash_axis_vars(plots)` after :25932 and use `_xa`/`_ya` in exactly four places:
    1. the `_figure_date_kind` fallback arguments (:25993-25994);
    2. the two log-note f-strings (:25999, :26006);
    3. the formatter loop's `_avar` (:26028-26029);
    4. `_dash_apply_axis_options(fig, graph_opts, _xa, _ya, ...)` (:26116).
  - The local `xvar`/`yvar` keep their other uses (`pxvar` fallback, hover, scale ranges).
  - **Served template (`_generate_app_source`).** The same four sites (:30379-30380, :30387/:30394, :30402-30403, :30474) read `_xa, _ya = _dash_axis_vars(plots)`, added after :30342.
- **TR-05.10 The axis rule (both modes).** `_dash_figure_date_kind(plots, key, fallback, date_vars)`:
  1. A plot whose type is in `_DASH_UNIVARIATE_TYPES` contributes `plot.get("var","") or fallback` on the `"xvar"` key and nothing on the `"yvar"` key. dash draws neither horizontal; P1.9 must read `horizontal` here.
  2. Every other plot contributes `plot.get(key,"") or fallback` as now.
  3. The all-agree test (`not kinds or len(kinds) > 1 or None in kinds` → None) is unchanged.

  D05-1's rule was struck on 01oct2026. It would have returned None for a computed-only figure whose first type is unit-labelled. No such rule is added, no `_DASH_UNIT_LABELLED_TYPES` constant is defined, and `_DASH_COMPUTED_ONLY_TYPES` is not read here. The docstring states rule 1. It also says that where twoway's first-plot rule labels the variable's numbers (an `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` first, WP-29 S05 Evidence §6), dash keeps its date axis, a documented divergence ratified 01oct2026.
- **TR-05.11 Served redraw marks its figure (D05-4).** In the template's `_dash_redraw_for(g, plot, pi, gname)` (:30264-30305), before `def _redraw(frame):` (:30288), add:
  - `_rax = _dash_axis_vars(g.get('plots', []))`;
  - `_rkinds = (_dash_figure_date_kind(g.get('plots', []), 'xvar', _rax[0], _date_vars), _dash_figure_date_kind(g.get('plots', []), 'yvar', _rax[1], _date_vars))`.

  After `_tfig = bokeh_figure()` (:30301) add `_dash_mark_date_axes(_tfig, *_rkinds)`. `_date_vars` is the closure's (`make_document`, :30053). `_rkinds` is computed by the same `_dash_axis_vars` and `_dash_figure_date_kind` calls the live figure uses (TR-05.9, :30379-30380 and :30401), so the throwaway figure carries the live figure's kinds. A date layer on a mixed numeric axis therefore redraws in day numbers, and one on a date axis redraws at its dates. This still holds with D05-1 struck (Evidence §8), and it is pinned by `test_served_redraw_uses_the_live_figures_axis`.
- **TR-05.12 KPI unit rule (P0.20).**
  - New `_dash_kpi_unit_kind(stat, kind)`, after `_dash_kpi_date_valued` (:23437): `k = str(kind or "")`; return `k` if `k in _STATA_DATE_KINDS and str(stat).lower().strip() not in ("count", "dcount")`, else `""`.
  - `_dash_kpi_column(col, stat, varname, kind=None)`:
    1. A non-datetime column is returned unchanged.
    2. For `count`/`dcount`, return today's ms floats (D05-7).
    3. If `kind not in _STATA_DATE_KINDS`, raise `ValueError(f"_dash_kpi_column: {varname!r} is a date column with no Stata date kind")`.
    4. For `sum`, warn `f"dash: sum({varname}) adds up dates, which has no meaning. The result is the sum of its Stata values ({units}), as summarize reports it."`. `{units}` comes from a dict literal inside the function: `td` days since 01jan1960, `tc`/`tC` milliseconds since 01jan1960, `tw` weeks since 1960w1, `tm` months since 1960m1, `tq` quarters since 1960q1, `th` half-years since 1960h1, `ty` years.
    5. Return `pd.Series(u[~np.isnan(u)], dtype="float64")` with `u = _dash_date_units(col.dropna(), kind)`.
- **TR-05.13 KPI callers (both modes).**
  - `DashRenderer._kpi_column` (:25231-25247) passes `(getattr(self, "date_vars", {}) or {}).get(varname)`.
  - `_dash_format_kpi_value` (:23492-23529): the date-valued branch returns `_dash_fmt_text(v, fmt)` (the statistic is already a Stata value). Rewrite the docstring sentence about ms.
  - Served template `_compute_kpi(df, stat, varname, date_vars=None)` (:29952-29968) passes `(date_vars or {}).get(varname)` to `_dash_kpi_column`. The three callers pass `_date_vars` as the fourth argument:
    - `_compute_kpi(_k_df, kstat, kvar, _date_vars)` (:30905);
    - `_compute_kpi(_k_fdf, ..., _date_vars)` (:31253);
    - `_compute_kpi(_k_sel, ..., _date_vars)` (:31335).
- **TR-05.14 KPI JS and config (P0.20).**
  - **Config.** `_kpi_callback_config` (:27360-27420) adds `"unitkind": _dash_kpi_unit_kind(kstat, getattr(self, "date_vars", {}).get(kvar, ""))`. It keeps `datekind`; data only, JSON-encoded.
  - **Values.** In `function dash_apply_kpis(` rename the filtered array to `_vals0` (:16105) and add `const vals = k.unitkind ? _vals0.map(v => dash_stata_value_of(v, k.unitkind)).filter(v => v !== null) : _vals0;` directly after it.
  - **Date branch.** It becomes `} else if (k.datekind) { text = dash_fmt_text(result, k.fmt); }` (:16175-16178).
  - **Scope.** Nothing else in the function changes, and the slice markers `// ---- KPI recompute, shared by`, `function dash_apply_kpis(`, `dash_apply_kpis(new_data,`, `    if (stat === 'count') {` and `        let text;` stay.
- **TR-05.15 Security (rule 1).**
  - No user text reaches a new path. New config fields are numbers and kind strings validated against `_STATA_DATE_KINDS`, encoded by `json.dumps` as data args and never interpolated into code.
  - Sizes are bounded by the existing caps: histogram ≤ 1000 bins and kdensity `n` ≤ 10000.
  - Conversions are vectorised O(n). A huge or non-finite `start()`/`range()` is refused by `_stat_option_float`/`_dash_range_pair` as today, and positions past Stata's range are dropped (A1).
  - Neither helper raises (TR-05.1, TR-05.2). The JS conversions drop `null` (A5).
- **TR-05.16 Maps.** `test/function_test_map.py` gains:
  - `_dash_date_units` → `test/test_date_units.py::TestTheUnitHelpers::test_date_units_reads_every_kind`
  - `_dash_units_to_axis` → `::TestTheUnitHelpers::test_units_to_axis_places_whole_and_fractional_periods`
  - `_dash_axis_vars` → `::TestTheUnitHelpers::test_axis_vars_reads_a_univariate_first_layer`
  - `GlyphMapper._layer_units` → `::TestTheUnitHelpers::test_layer_units_drops_unconvertible_rows_jointly`
  - `GlyphMapper._on_axis` → `::TestTheUnitHelpers::test_on_axis_follows_the_figures_axis`
  - `GlyphMapper._drop_off_dates` → `::TestOutOfRange::test_out_of_range_edges_never_reach_the_page_json`
  - (P0.20) `_dash_kpi_unit_kind` → `::TestTheKpiConfig::test_the_unit_kind_rule`

  Keep `_dash_figure_date_kind`'s entry. Point `GlyphMapper._masked` at `::TestTheUnitHelpers::test_layer_units_drops_unconvertible_rows_jointly` only if the existing entry's test no longer fails when the body is skipped (verify with `scripts/fncov/fncov_mutate.py --map` only if it is run; otherwise keep it).

## Boundaries

- **Other sections' symbols.** Do not touch:
  - `_default_lpoly_bwidth`, `_compute_lpoly_fit` or the lpolyci band (S11). This section only routes their inputs and outputs, and the lpoly default-bandwidth value stays S11's.
  - `_join_order`/`map_line` (S02), `_dash_axis_labels`/conftest labels (S03), `member_ids`/`_dash_colorvar_domain` (S07), the launcher/private root (S08), the stale cue (S12), the token (S13), the embed rows (S14).
- **Named out of scope (A8), with the sites and ids for S15's notes:**
  - `map_bar`/`map_rbar` `barwidth()` on a date axis read in ms (dash_render.py:8172-8180; twoway reads x units, `bar1.svg` vs `bar3.svg` rect widths 283.43 vs 786.48): GAPS2 A3.
  - `function` `range()`, `scatteri`, `pci`, `pcarrowi` on a date axis drawn at raw Stata values as ms: P1.23.
  - The histogram fallback tooltip `@{left}{0} to @{right}{0}` and the fit tooltips `@{x}{0}` showing epoch ms on a date axis (`_dash_build_hover`, :23997-24010): P1.23.

  Those fixes should reuse `_dash_units_to_axis`.
- **Ratified divergence, not a residual.** dash keeps its date axis where twoway labels the variable's numbers because an `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` is first. That covers the 12 Evidence §6 cases, `(lfit)(scatter)` among them, and the dropped pre-0100 `range()` points of a lone kdensity. D05-1 was struck on 01oct2026, so no follow-up is planned; the help documents it (05-10).
- **Other residuals.** `horizontal` (P1.9) is not added; `_dash_figure_date_kind` must read it when P1.9 lands. `xlabel(minmax)` on a mixed numeric axis whose first layer's variable is a date reads that column in epoch ms (Evidence §8: ticks `[978393600000.0, 1006905600000.0]`), while the date layer is drawn in day numbers (P1.23).
- **Files left alone.**
  - `dash.ado` and `dash_parse.mata` are unchanged: Stata-side KPI values are already in units, and `start()` is already checked in units.
  - No tracking document beyond BUGS.md and CHANGELOG.md is edited (A5 of index.md: GAPS2.md, REMAINING.md, ROADMAP.md, AGENTS.md and DROPIN are S15's; this section's text for them is in Notes for the closeout).
  - `test_gaps2_truth.cscript`, `test/run_all_cscripts.do` and `test/test_cscript_hygiene.py` are not edited (R1).
  - `ALLOWED`/`_MUST_WARN` in `test_mode_parity.py` are not edited (R6).
- **Silent when honoured.** No note is added except the off-dates note (BR-05.7) and the reworded sum note.
- **Membership pinned elsewhere.** `_DASH_COMPUTED_ONLY_TYPES`' membership is pinned equal to dash.ado's (`test_embedded_cells.py::TestTheTwoLanguagesAgree`). With D05-1 struck, this section neither reads nor changes it.

## Stata truth

**New fixture** `test/fixtures/date_units_truth.json`, written by the new `scripts/extract_date_units_truth.do`. It follows `scripts/extract_stat_truth.do`'s pattern:
- the `zq_s`/`zq_n`/`zq_a`/`zq_chunk` record writers (:80-118, copied);
- the `@@@` record file under `c(tmpdir)`;
- the `git rev-parse HEAD` capture into a local, refused unless 40 hex characters (:255-270);
- one trailing `python:` block that reads the record file, never calls back into Stata, writes a backtick as `\x60`, and uses no `shell=True`.

The script reads the repository from the environment: `local repo : env DASH_REPO`, refusing with `exit 198` when it is empty. It writes `${repo}/test/fixtures/date_units_truth.json`.

`_meta` has these keys:
- `generated_by: "scripts/extract_date_units_truth.do"`
- `stata_version`
- `born_date`
- `dash_commit`
- `extracted` (`c(current_date)`)
- `method` (one paragraph naming each probe's command)
- `precision` ("%21.0g; histogram heights compared at rel 1e-9")

Contents (every record carries its `cmd`):

| Block | Keys | Commands (on `sysuse sp500, clear`, `keep date close`, then `gen m = mofd(date)` %tm, `gen q = qofd(date)` %tq, `gen w = wofd(date)` %tw, `gen double tc = cofd(date) + 3600000*mod(_n,24)` %tc, `gen yr = 1950 + mod(_n,40)` %ty) |
|---|---|---|
| `data` | `date close m q w tc yr` (248 each, %21.0g), `formats`, `gen_cmds` | the generating commands above |
| `histogram` | `td:default`, `td:w30s14975`, `td:bin10`, `td:discrete`, `td:frequency`, `tm:default`, `tm:w2s492`, `tc:default`, `tc:w7d`, `tw:default`, `ty:default`, `td:default:if`, `td:w30s14975:if`, `td:default:fixedgrid:if` | `twoway__histogram_gen <v> [if close>=1200], density\|frequency [width() start() bin() discrete] gen(zh zx, replace)`. Records `bin width start min max` and `heights`, the full bar array of length `r(bin)`. `gen()` writes only populated bins, so the python block places each `(zx, zh)` pair at bar `round((zx - start)/width - 0.5)` and fills the rest with 0. `tc:w7d` is `start(1294012800000) width(604800000)`; `:fixedgrid:if` is `start(14977) width(24.2)` on `if close>=1200`. |
| `kdensity` | `bw:td`, `bw:tm`, `bw:tq`, `bw:tc`, `bw:ty` (r(bwidth) of `kdensity <v>, nograph`); curves `td:range:default`, `td:range:bw10`, `tm:range:bw1`, `td:range:default:if`, `td:range:bw10:if` | `twoway__kdensity_gen date [if close>=1200], gen(zd zx) n(5) range(14900 15400) [bwidth(10)]`; `twoway__kdensity_gen m, gen(zd zx) n(5) bwidth(1) range(490 505)`. Records `x`, `y`. |
| `lpoly` | `td:bw30`, `tm:bw2`, `tc:bw30d`, `td:bw30:if` | `lpoly close <v> [if close>=1200], nograph gen(zx zs) n(5) bwidth(30\|2\|2592000000)`. Records `x`, `y`, `bwidth`. (The default bandwidths, the `se()` and the `pwidth` belong to S11.) |
| `fits` | `fp:td` (`e(fp_pwrs)`, `predict double` at the first and last date), `lfit:tm` (`regress close m`, `_b`, predictions at m=492 and 503), `lfit:ydate` (`regress date close`, predictions at min/max close) | as named |
| `kpi` | scopes `all`, `if close>=1200`, `in 1/50`, `tm2`; per var `date m q w tc yr` (scope `tm2`: `m` only); per stat `sd var iqr cv sum skewness mean p50 p25 p75 min max count` | `summarize <v> [if] [in], detail`. Records `value` (%21.0g; iqr = r(p75)-r(p25), cv = r(sd)/r(mean)) and `display` (`strtrim` of `: display %9.0g` for sd/var/iqr/cv/sum/skewness/count, of `: display <the var's format>` for mean/p50/p25/p75/min/max). Scope `tm2` is `clear`, `set obs 2`, `gen m = 492 + 2*(_n-1)`, `format m %tm`. |
| `axis_labels` | `hist_td kd_td lfit_td qfit_td lfitci_td qfitci_td lpoly_td lpolyci_td lowess_td mspline_td mband_td fpfit_td fpfitci_td kd_then_hist hist_then_kd lfit_then_scatter scatter_then_lfit lfit_then_lowess kd_tm hist_tm lfit_ydate scatter_then_lfit_ydate` | `twoway <cmd>` then `graph export "<scratch>/<case>.svg", replace`. Records `cmd`, `date_axis` (`"x"` or `"y"`, the axis the date variable is on), the tick `texts`, and `dates_shown` (true iff a text matches `^[0-9]{2}[a-z]{3}[0-9]{4}$` for %td or `^[0-9]{4}m[0-9]{1,2}$` for %tm). The python block exits with an error when a case shows neither the expected date texts nor the number `15000`/`490`. |

**Runs (Stata only through the wrapper, CLAUDE.md rule 10).**
```sh
mkdir -p /tmp/dash-wp29-s05/extract
DASH_REPO=<wt> dash_nobrowser=1 <wt>/scripts/stata_slot.sh /tmp/dash-wp29-s05/extract <wt>/scripts/extract_date_units_truth.do
# log: /tmp/dash-wp29-s05/extract/extract_date_units_truth.log ; never relaunch to check, read the log
git -C <wt> add -f test/fixtures/date_units_truth.json scripts/extract_date_units_truth.do
```
The fixture is never patched by hand (R5). It is named by `test/test_date_units.py`, which satisfies `test_fixtures_are_committed.py` with no edit to that file.

**Truth blocks** in `test/test_wp29_truth.cscript`, each appended above `* ==== append new blocks above this line ====`. They are gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S05") {`, open and close with `display as text "S05 start/end `c(current_time)'"`, and use the scaffold's PASS/FAIL helper pair (S01 copies `_gt_expect`/`_gt_done` from `test_gaps2_truth.cscript:42-70`; read the script's head for the names). Each block reads pages with a Python helper that loads the page's document through `Document.from_json`, as in `test_gaps2_truth.cscript` HE-05's `_he5_read`. Served apps are `exec`'d with the curdoc attach replaced, as in KF-03.
- `* ==== S05 P0.8: computed layers on a date in Stata units ====`:
  - **DU-01** `dash histogram date, width(30) start(14975)`: 13 bars, heights equal live `twoway__histogram_gen` (reldif < 1e-9), first left equals 978220800000 exactly, x axis `DatetimeAxis`, y `LinearAxis`.
  - **DU-02** `dash histogram m`: non-empty bars equal live (HE-05's non-empty comparison); x `DatetimeAxis`.
  - **DU-03** `dash kdensity date, bwidth(10) range(14900 15400) n(5)`: y equals live `twoway__kdensity_gen`. x equals the epoch ms of the live grid `kx` (14900 … 15400), computed in the block as `(kx - td(01jan1970))*86400000` (reldif < 1e-12). x is a `DatetimeAxis` (D05-1 struck: dash keeps its date axis where twoway's is numeric).
  - **DU-04** `dash lpoly close date, bwidth(30) n(5)`: y equals live `lpoly ... gen()`. x equals the epoch ms of the same live grid, computed the same way, and x is a `DatetimeAxis`.
  - **DU-05** `dash fpfit close date`: first and last `y_fp` equal `fracpoly` `predict double` (reldif < 1e-9).
  - **DU-06** served app of DU-01 plus `dash lpoly close date, bwidth(30) n(5)` with `filter(close, type(slider))`: as opened and after the close slider moves to 1200, the bars equal live `twoway__histogram_gen date if close>=1200, density width(30) start(14975)` (the served app re-bins) and the curve equals live `lpoly close date if close>=1200, bwidth(30) n(5)`.
- `* ==== S05 P0.20: KPI statistics of a date in Stata units ====`:
  - **KD-01** saved page `sd var iqr cv sum skewness` of `date` and `mean p50` of `m`: each card equals `strtrim` of `: display %9.0g` (or `%tm`) of the live `summarize ..., detail` result.
  - **KD-02** served app of the same, opened and after the close slider moves to 1200, equals `summarize ... if close>=1200`.
  - **KD-03** a two-row `m` = {492, 494} dataset: `mean(m)` reads `2001m2` saved and served.

Driver:
```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<wt>" "<wt>" "test_wp29_truth.cscript" > /tmp/dash-wp29-s05/run_test_wp29_truth.do
dash_nobrowser=1 WP29_ONLY=S05 <wt>/scripts/stata_slot.sh /tmp/dash-wp29-s05 /tmp/dash-wp29-s05/run_test_wp29_truth.do
# log: /tmp/dash-wp29-s05/run_test_wp29_truth.log
```

## TDD test stubs

All tests are in the new **`test/test_date_units.py`** unless named otherwise.

**Module setup.**
- Load `test/fixtures/date_units_truth.json`. If it is missing, `pytest.fail("...run scripts/extract_date_units_truth.do (WP-29 S05)")`; never skip.
- Build `_DF` from `_TRUTH["data"]`: columns `date close m q w tc yr`, floats.
- `_FMT = {"date": "%td", "close": "%9.0g", "m": "%tm", "q": "%tq", "w": "%tw", "tc": "%tc", "yr": "%ty"}`.
- `_spec(plots, kpis=(), go=None, filters=({"varname": "close", "type": "slider"},))` returns `{"graphs": [{"plots": plots, "graph_options": dict({"name": "g1"}, **(go or {})), "if_expr": "", "in_expr": ""}], "kpis": list(kpis), "build_options": {"layout": "auto", "link": "", "theme": "", "title": "", "subtitle": "", "formats": _FMT, "filters": list(filters), "registry": " ".join(["g1"] + [k["name"] for k in kpis])}}`.

**Helpers** come from `test_help_claims_4` as `hc4`: `_saved`, `_saved_filter_move`, `_saved_brush`, `_served_app`, `_served_session`, `_served_widget`, `_served_filter_move`, `_served_brush`, `_run_js_full` and `_cards`. `js_runner.run_filter_js_block` and `js_runner.NODE` come from `js_runner`.

**Independent oracles:**
- `ms_td(v) = (v - 3653) * 86_400_000.0`;
- `ms_tm(v) = pd.Timestamp(year=1960 + v // 12, month=v % 12 + 1, day=1)` in ms;
- `ms_tm_frac(v) = ms_tm(f) + (v - f)*(ms_tm(f + 1) - ms_tm(f))` with `f = int(math.floor(v))`. This is the fractional-month position on a `%tm` date axis, needed since D05-1 was struck, because a lone `kdensity m` grid such as 490, 493.75, … is drawn on a date axis.

Never use the code under test to build an expected value.

**Conventions.**
- "saved|served" means both modes are parametrised.
- Node tests carry `@pytest.mark.skipif(js_runner.NODE is None, reason=...)`, plus a module test `test_the_node_tests_ran` (pattern `test_kpi_format.py:397`).
- No test asserts title or label text (A7 of index.md).

**P0.8, written by 05-02.** They fail at `<base>` unless marked *guard*.

- `TestTheUnitHelpers::test_date_units_reads_every_kind`: `_dash_date_units(_stata_dates_to_datetime(pd.Series([v]), k), k)` returns v for td 14977.5, tc 1294016400000, tw 2132, tm 492, tq 164, th 82 and ty 2001. NaT gives NaN, and an unknown kind leaves ms unchanged. (HEAD: AttributeError.)
- `TestTheUnitHelpers::test_units_to_axis_places_whole_and_fractional_periods`: tm `[492, 492.5, 493]` gives ms 2001-01-01, 2001-01-16 12:00 and 2001-02-01; td 14977.25 gives 2001-01-02 06:00; tw 2183.5 lies halfway between 2001-12-24 and 2002-01-01.
- `TestTheUnitHelpers::test_units_to_axis_never_raises_on_hostile_values`: `[1e300, -1e300, nan, inf, "x", 10000.0 (ty)]` all give NaN, with no warning escaping (`warnings.simplefilter("error")`) and no exception.
- `TestTheUnitHelpers::test_axis_vars_reads_a_univariate_first_layer`: histogram gives `("date", "")`; scatter gives `("date", "close")`; `[]` gives `("", "")`.
- `TestTheUnitHelpers::test_layer_units_drops_unconvertible_rows_jointly`: mapper `date_vars={"d": "tm"}` with source `d=[ms(2001m1), 1e18, ms(2001m3)]` and `w=[1.0, 2.0, nan]`. `_layer_units(src, None, {"weight": "fw", "wexp": "w"}, "histogram", "d")` returns `d=[492.0]` and `w=[1.0]`, and `map_histogram` raises nothing (A4).
- `TestTheUnitHelpers::test_on_axis_follows_the_figures_axis`: a figure marked `("td", None)` converts; one marked `(None, None)` gives identity; an unmarked figure converts by the variable; a non-date variable gives identity; `off` is True only where a finite value fell out.
- `TestAUnivariateDateIsOnX::test_the_date_axis_is_x[saved|served-histogram|kdensity]`: both have x `DatetimeAxis` and y not. For kdensity, D05-1 is struck and dash keeps its date axis. (HEAD: y `DatetimeAxis` and x `LinearAxis` for both; measured for kdensity in Evidence §8, `kd_lone`.)
- `TestAUnivariateDateIsOnX::test_the_axis_reads_the_variables_format[saved|served-%tdCCYY-NN-DD|%tmMon_CCYY]` (A2): `histogram date` / `histogram m` with that format. The x formatter's `args["fmt"]` equals the format. (HEAD: `%td`, and the formatter sits on y.) Also assert that twoway's measured first ticks are what the formatter's writer gives: `dr._dash_fmt_text(14976, "%tdCCYY-NN-DD") == "2001-01-01"` and `dr._dash_fmt_text(492, "%tmMon_CCYY") == "Jan 2001"` (both verified at `7421d3d`).
- `TestAUnivariateDateIsOnX::test_yline_is_a_density[saved|served]` (A7a): `go={"yline": ".002"}` gives a width `Span` at 0.002. (HEAD: -315619027200.0.)
- `TestAUnivariateDateIsOnX::test_xline_and_xlabel_are_days[saved|served]` (A7b,c): `xline(15000)` gives a height `Span` at `ms_td(15000)` = 980380800000; `xlabel(15000 15100)` gives ticks `[980380800000, 989020800000]`. (HEAD: 15000.0 and `[15000.0, 15100.0]`.)
- `TestAUnivariateDateIsOnX::test_yscale_log_is_honoured[saved|served]` (A7d): y is a `LogAxis`, and no warning contains `date variable ''`. (HEAD: refused.)
- `TestAUnivariateDateIsOnX::test_xscale_log_note_names_the_variable[saved|served]` (A2): the note reads `xscale(log) is meaningless for the date variable 'date'`. (HEAD: `''`, and on y.)
- **The axis rule (D05-1 struck 01oct2026).** Module constants:
  - `_TWOWAY_DATES = ("hist_td", "lowess_td", "mspline_td", "mband_td", "fpfit_td", "fpfitci_td", "hist_then_kd", "scatter_then_lfit", "hist_tm", "scatter_then_lfit_ydate")` (10);
  - `_DIVERGES = ("kd_td", "lfit_td", "qfit_td", "lfitci_td", "qfitci_td", "lpoly_td", "lpolyci_td", "kd_then_hist", "lfit_then_scatter", "lfit_then_lowess", "kd_tm", "lfit_ydate")` (12; twoway labels numbers, dash keeps dates).

  For each case the spec mirrors the twoway command, with lpoly/lpolyci given `bwidth(30)`.
- `TestTheAxisRule::test_the_cases_are_split_as_twoway_labels_them`: `{k for k, v in _TRUTH["axis_labels"].items() if v["dates_shown"]} == set(_TWOWAY_DATES)` and `{... if not v["dates_shown"]} == set(_DIVERGES)`. A re-extracted fixture that moves a case fails here. (Guard: passes at HEAD once the fixture exists.)
- `TestTheAxisRule::test_the_axis_is_twoways[saved|served-<10 _TWOWAY_DATES cases>]`: the axis on `date_axis` is a `DatetimeAxis`, and the other axis is never one. (HEAD: fails for the histogram cases, `hist_td`, `hist_then_kd` and `hist_tm`, whose date sits on y. The other seven are guards; the failure file records the measured split.)
- `TestTheAxisRule::test_a_unit_labelled_first_layer_keeps_the_date_axis[saved|served-<12 _DIVERGES cases>]` is the ratified divergence: the axis on `date_axis` is a `DatetimeAxis` where twoway's is numeric, and the other axis is never one. (HEAD: fails for `kd_td`, `kd_then_hist` and `kd_tm`, whose date sits on y. The rest are guards that pin the ratified decision against a later re-adoption of A9.)
- `TestTheAxisRule::test_a_lone_fit_is_drawn_at_its_dates[saved|served-lfit|qfit|lfitci|qfitci|kdensity|lpoly|lpolyci]`: x is a `DatetimeAxis`. Every drawn x lies in `[ms_td(14977), ms_td(15340)]`, and lpoly/lpolyci (with `bwidth(30)`) draw at least 2 points. (HEAD: kdensity's x is a `LinearAxis`; lpoly/lpolyci draw 0 points. lfit/qfit/lfitci/qfitci are guards.)
- `TestHistogramOnADate::test_bars_match_twoway[saved|served-<every non-":if" histogram key>]`:
  - bar count equals `bin`;
  - tops equal `heights` (rel 1e-9);
  - `left[0]` equals the independent ms of `start` (rel 1e-12) on a date axis.

  The options are `{"width": ..., "start": ..., "bin": ..., "discrete": "1", "frequency": "1"}` as the key needs (`_dash_histogram_ymode` reads a non-empty flag). Guards: `td:frequency`, `tc:default` (both affine-invariant in ms).
- `TestHistogramOnADate::test_width_and_start_raise_no_bin_limit_note[saved|served]`: no warning contains `1000 bins`.
- `TestKdensityOnADate::test_density_matches_twoway[saved|served-td:range:default|td:range:bw10|tm:range:bw1]`: y equals the fixture (rel 1e-9). x equals the independent ms of the fixture's `x`: `ms_td` for td, and `ms_tm_frac` for tm, whose grid 490, 493.75, … holds fractional months. The tolerance is 1 ms. The x axis is a `DatetimeAxis` (D05-1 struck).
- `TestKdensityOnADate::test_on_a_date_axis_it_is_drawn_at_the_dates[saved|served]`: `(histogram date)(kdensity date, range(14900 15400) n(5) bwidth(10))`. Kdensity x equals `ms_td` of 14900 … 15400, and y equals `td:range:bw10`.
- `TestLpolyOnADate::test_explicit_bwidth_draws_statas_curve[saved|served-td:bw30|tm:bw2|tc:bw30d]`: n(5) y equals the fixture (rel 1e-9). (HEAD: 0 points.)
- `TestLpolyOnADate::test_the_default_draws_a_curve[saved|served-lpoly|lpolyci]`: at least 2 finite points; the bandwidth value is S11's.
- `TestFpfitOnADate::test_the_curve_is_statas[saved|served]`: `y_fp` first and last equal `fits["fp:td"]` (rel 1e-9). (HEAD: 1329.5113.)
- `TestEveryComputedLayer::test_a_monthly_lfit_is_statas[saved|served]`: `(scatter close m)(lfit close m)`. The lfit y at its grid ends equals `fits["lfit:tm"]` predictions at 492 and 503 (rel 1e-9).
- `TestEveryComputedLayer::test_a_monthly_layer_lands_on_its_months[<13 types>]`: `(scatter close m)(<type> ...)`. Every drawn x lies within [ms_tm(492), ms_tm(503)] (guard for most; lpoly/lpolyci `bwidth(2)`).
- `TestEveryComputedLayer::test_a_date_y_is_fitted_in_its_units[saved|served]`: `(scatter date close)(lfit date close)`. The y ends equal `ms_td` of the `fits["lfit:ydate"]` predictions within 1 ms (guard: affine).
- `TestEveryComputedLayer::test_a_date_layer_on_a_numeric_axis_is_drawn_in_its_units[saved|served]` covers D05-4's mixed axis, kept after D05-1 was struck (Evidence §8). The frame is `_DF.assign(obs=np.arange(1.0, 249.0))` and the spec is `(scatter close obs)(lfit close date)`. x is a `LinearAxis`; the lfit's `x` lies in `[14977, 15340]`, and its smallest and largest x equal 14977 and 15340 within 1e-6 (the y values are affine-invariant here and are pinned elsewhere). (HEAD: x at 978393600000.0 and beyond, measured.)
- `TestOutOfRange::test_out_of_range_edges_never_reach_the_page_json[saved|served-hist_start-700000_w100000|kd_after_hist_range-1000000_15400|kd_lone_range-1000000_15400|lfit_after_scatter_range-700000_15340]` (A1). Cases:
  - `histogram date, start(-700000) width(100000)`: 7 bars drawn, note `1 bar(s)`;
  - `(histogram date)(kdensity date, range(-1000000 15400) n(5))`: 3 points, note `2 point(s)`;
  - `kdensity date, range(-1000000 15400) n(5)` alone: on dash's date axis (D05-1 struck), 3 points, note `2 point(s)`. twoway draws all 5 on a numeric axis (Evidence §6, last line); that is part of the documented divergence;
  - `(scatter close date)(lfit close date, range(-700000 15340))`: note `3 point(s)`.

  Saved: `json.loads(cb.args["agg_configs_json"], parse_constant=_raise)` succeeds, node `JSON.parse` of the same text succeeds, and `hc4._run_js_full` of a move to the slider's start completes. Served: draws with no exception, and gives the same note and the same drawn arrays as saved. (HEAD: the lfit case draws ms points; the hist case reads start as ms.)
- `TestAfterAFilterMove::test_saved_histogram_recount_is_per_day`: the close slider moves to 1200 under node. The tops of the first `bin` bars equal `histogram["td:default:fixedgrid:if"].heights` (rel 1e-9), and later bars are 0.
- `TestAfterAFilterMove::test_saved_kdensity_recompute_is_per_day`: `kdensity date, range(14900 15400) n(5)` after the move equals `kdensity["td:range:default:if"]` (the JS re-derives the bandwidth; rel 1e-9), and with `bwidth(10)` equals `td:range:bw10:if`.
- `TestAfterAFilterMove::test_served_layers_after_a_move`: the served slider moves to 1200. The histogram equals `td:default:if` (served re-bins); the kdensity equals `td:range:default:if`; `lpoly close date, bwidth(30) n(5)` equals `lpoly["td:bw30:if"]`.
- `TestAfterAFilterMove::test_an_inert_move_changes_nothing[histogram|kdensity|histogram-fw-date|kdensity-aw-date]` (A3): with the slider at its `start`, node tops/y equal first paint exactly. The weight is a `%td` variable `wd = date - 14900` formatted `%td`, added to the frame.
- `TestAfterAFilterMove::test_served_redraw_uses_the_live_figures_axis[mixed-numeric|lone-date]` (TR-05.11) runs served, before and after the close slider moves to 1200:
  - `mixed-numeric` is `(scatter close obs)(lfit close date)` on `_DF.assign(obs=np.arange(1.0, 249.0))`. The lfit's x stays in `[14977, 15340]` (day numbers on the `LinearAxis`, as the live figure drew it). An unmarked throwaway figure gives about 9.8e11 here.
  - `lone-date` is `lfit close date`. The lfit's x stays in `[ms_td(14977), ms_td(15340)]` on the `DatetimeAxis`.
- `TestTheJsUnits::test_the_pair_loop_converts_and_drops_out_of_range` (A3, A5): run `dr._DASH_FMT_JS` plus the `_FILTER_JS` text from `    let vals, wts = null;` up to `    if (ac.type === 'histogram') {`, with stubs `_ac_data`, `raw_col`, `_pick = c => c` and an `ac` carrying `datekind:'td', wvar:'w', wdatekind:'td'`. `vals`/`wts` are the Stata values, and the row with `1e18` ms or `null` is dropped.
- `TestTheJsUnits::test_the_kdensity_branch_evaluates_in_units_and_draws_on_the_axis`: `run_filter_js_block("kdensity", ac)` with `x_grid != x_eval` gives `x == x_grid` and y evaluated at `x_eval`.
- `TestTheJsUnits::test_the_histogram_branch_draws_its_slice`: `ac` with `bin=8, bin_first=1`, 7-bar `bin_edges`/`unit_edges` gives 7 tops, normalised over all 8 counts.
- `TestTheConfig::test_agg_config_carries_datekind_and_unit_grids`: a date histogram/kdensity has `datekind == "td"`, `unit_edges`/`x_eval` present and finite; a histogram of `close` has none of them.
- `TestTheConfig::test_no_config_number_is_non_finite`: walks every float in every `agg_configs_json`/`kpi_config_json` of the specs above.
- `TestTheFixture::test_meta_and_data`: `_meta` has `stata_version`, `born_date`, `dash_commit` (40 hex), `extracted` and `generated_by == "scripts/extract_date_units_truth.do"`; every `data` column has 248 values.
- `test_the_node_tests_ran`.

**P0.20, written by 05-12** (KPI spec: `[{"type": "scatter", "yvar": "close", "xvar": "date", "options": {}}]`):
- `TestKpiOfADate::test_first_paint[saved|served-<var>-<stat>]`, with var in `date m q w tc yr` and stat in `sd var iqr cv sum skewness mean p50 min max`: the card equals `kpi["all"][var][stat]["display"]`. Build one saved page and one served session holding all 60 cards (module-scoped fixtures) and parametrise only the assertion. The pass/fail split at the base is recorded in the failure file; the skewness rows and `tc` sd/var/iqr are guards.
- `TestKpiOfADate::test_a_monthly_mean_is_statas_month[saved|served]`: on the `tm2` frame `pd.DataFrame({"m": [492.0, 494.0], "close": [1.0, 2.0], "date": [14977.0, 15000.0]})`, `mean(m)` and `p50(m)` read `2001m2`. (HEAD: `2001m1`.)
- `TestKpiOfADate::test_after_a_move[saved|served]`: close slider at 1200; cards equal the `if close>=1200` displays (sd/var/iqr/cv/sum of date, mean/p50 of m).
- `TestKpiOfADate::test_after_a_brush[saved|served]`: KPIs with `"update": "brush"` on `g1`; indices 0..49 brushed; cards equal the `in 1/50` displays.
- `TestKpiOfADate::test_the_sum_note_names_the_units`: both modes give the identical note, containing `adds up dates` and `days since 01jan1960`.
- `TestKpiOfADate::test_js_drops_out_of_range_values`: node runs `dash_apply_kpis` (the `test_kpi_brush.py:250` slice plus `dr._DASH_FMT_JS`) on a `date` column of ms values plus `1e18`, with `unitkind 'td'` and `sd`. The card equals the sd of the in-range values, in days.
- `TestKpiOfADate::test_a_missing_kind_is_refused`: `dr._dash_kpi_column(<datetime col>, "sd", "date", None)` raises `ValueError`, and `"count"` with no kind returns floats.
- `TestTheKpiConfig::test_unitkind_reaches_every_statistic_but_counts`: in `kpi_config_json`, `sd(date)` has `unitkind 'td'`, `count(date)` has `''` and `mean(close)` has `''`; `datekind` is kept.
- `TestTheKpiConfig::test_the_unit_kind_rule`: `_dash_kpi_unit_kind` gives `("sd","td")` → `"td"`, `("count","td")` → `""`, `("DCOUNT","tm")` → `""`, `("sd","zz")` → `""` and `("sd",None)` → `""`.

**Mutation table** (each break must kill the named test):

| break this | test that must die |
|---|---|
| skip the `units=` conversion in `_masked` | `TestHistogramOnADate::test_bars_match_twoway`, `TestLpolyOnADate::test_explicit_bwidth_draws_statas_curve` |
| convert inputs but not outputs (`_on_axis` returns its input) | `TestKdensityOnADate::test_on_a_date_axis_it_is_drawn_at_the_dates`, `test_a_monthly_layer_lands_on_its_months` |
| re-adopt A9 (`_dash_figure_date_kind` returns None for a computed-only figure whose first type is lfit/qfit/lfitci/qfitci/kdensity/lpoly/lpolyci) | `TestTheAxisRule::test_a_unit_labelled_first_layer_keeps_the_date_axis[kd_td]`, `test_a_lone_fit_is_drawn_at_its_dates[lfit]` |
| `_on_axis` ignores the figure's marks (always converts by the variable) | `TestEveryComputedLayer::test_a_date_layer_on_a_numeric_axis_is_drawn_in_its_units`, `TestTheUnitHelpers::test_on_axis_follows_the_figures_axis` |
| forget `_dash_mark_date_axes(_tfig, ...)` | `TestAfterAFilterMove::test_served_redraw_uses_the_live_figures_axis[mixed-numeric]` |
| JS converts `v` before its null test | `TestTheJsUnits::test_the_pair_loop_converts_and_drops_out_of_range` |
| JS omits `wdatekind` | `test_an_inert_move_changes_nothing[histogram-fw-date]` |
| build `bin_edges` from un-dropped edges | `TestOutOfRange` (NaN in JSON) |
| leave the KPI date branch converting from ms | `TestKpiOfADate::test_first_paint[*-mean]` |
| served `_compute_kpi` without `_date_vars` | `TestKpiOfADate::test_first_paint[served-*]` (cards read `.`) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Unit helpers, both directions, hostile input | pytest | none (independent oracles) | n/a |
| Histogram bars per Stata grid, every kind | pytest | `histogram` | yes |
| kdensity curves, on numeric and date axes | pytest | `kdensity` | yes |
| lpoly explicit bwidth; default draws | pytest | `lpoly` | yes |
| fpfit, `%tm` lfit, date-y lfit | pytest | `fits` | yes |
| Axis rule: the 10 twoway date-label cases matched, the 12 numeric-label cases pinned as the ratified divergence (D05-1 struck), the fixture split checked, plus the formatter and yline/xline/xlabel/log | pytest | `axis_labels` | yes |
| A date layer on a mixed numeric axis (D05-4), first paint and served redraw | pytest | none (independent bounds) | yes |
| Out-of-range rule, JSON finiteness | pytest + node `JSON.parse` + node move | none | yes |
| Saved recount after a move, inert move, weights | pytest + node | `histogram`/`kdensity` `:if` keys | saved (served: re-bin test) |
| Served layers after a move; redraw axis | pytest | `:if` keys | served |
| JS pair loop, kdensity and histogram branches | node (sliced) | none | saved |
| KPI cards first paint / move / brush / tm2 / note | pytest + node | `kpi` | yes |
| Live Stata comparison | `test_wp29_truth.cscript` DU-01..DU-06, KD-01..KD-03 | none (Stata computes) | yes |
| Parity | `test_mode_parity.py` DATE_CORPUS additions (05-08, 05-16) | none | yes |

**Acceptance criteria.**
- **AC-05.1** `python3 -m pytest test/test_date_units.py test/test_date_range.py test/test_served_dates.py test/test_kpi_format.py test/test_server_layer_defects.py test/test_mode_parity.py -q` passes with no skips on a machine with node.
- **AC-05.2** Both blocks of `test_wp29_truth.cscript` print `DU-01..DU-06 PASS` and `KD-01..KD-03 PASS` under `WP29_ONLY=S05`, with no FAIL, no SKIP and no `r(`.
- **AC-05.3** The served-name guards (`test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`), `test_function_test_map.py`, `test_fixtures_are_committed.py` and `test_tracking_documents.py` pass.
- **AC-05.4** Two commits exist on `wp29-s05`, subjects ending `(WP-29 P0.8)` and `(WP-29 P0.20)`. Each body opens with its saved failure text and carries `Regression:`/`Flipped:`/`BUGS.md:` lines (and `Fixture:` on the first). The full suite was green before each.
- **AC-05.5** BUGS.md has both entries `- [x]` with `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.8|P0.20). … Pinned by test/test_date_units.py::…, test/test_wp29_truth.cscript DU-01|KD-01; fixture test/fixtures/date_units_truth.json.` `WP29_OPEN` has no `P0.8`/`P0.20` key. `grep -c '<!-- WP-29 P0.8 -->\|<!-- WP-29 P0.20 -->' CHANGELOG.md` prints 0.

## Tasks

**Commit boundary.**
- **Commit 1 (P0.8)** holds 05-01 … 05-11, subject `Compute date layers in the variable's Stata units (WP-29 P0.8)`.
- **Commit 2 (P0.20)** holds 05-12 … 05-18, subject `Take KPI statistics of a date in its Stata units (WP-29 P0.20)`.

Both are made on `wp29-s05` in `<wt>`, each after the section's full suite ran green once on that tree (`python3 -m pytest test/ -q`, rules 4 and 11). The merger lands them with the recorded messages (index.md step 1).

**Commit bodies.** Each body opens with the saved failure text, then:
- the measured defect;
- what changed, and where;
- `Regression: test/test_date_units.py::<Class>::<test> -- failed at <base> with <text>` (one per regression test);
- `Flipped: <node> -- <old expectation> was wrong because <why>`;
- `Fixture: test/fixtures/date_units_truth.json (scripts/extract_date_units_truth.do)` (commit 1 only);
- `BUGS.md: "<title>" (closed)`;
- the GitNexus impact lines.

No AI reference anywhere. Before and after each commit, `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0. `CLAUDE.md` and `.gitignore` are never staged.

<task type="auto" id="05-01">
  <name>Extract the date-units Stata truth fixture</name>
  <files>scripts/extract_date_units_truth.do, test/fixtures/date_units_truth.json</files>
  <action><![CDATA[
Create `scripts/extract_date_units_truth.do` exactly as "Stata truth" specifies: the header comment (purpose, run command, method); `local repo : env DASH_REPO` with `exit 198` when empty; the `zq_*` record writers copied from `scripts/extract_stat_truth.do:80-118`; the `git rev-parse HEAD` capture of :255-270; the data, histogram, kdensity, lpoly, fits, kpi and axis_labels probes with the keys and commands of the table; and one trailing `python:` block that rebuilds full histogram bar arrays from the `gen()` pairs, decides `dates_shown` from the exported SVG texts, writes `_meta` (generated_by, stata_version, born_date, dash_commit, extracted, method, precision) and `json.dump(..., indent=1, sort_keys=True)` to `${repo}/test/fixtures/date_units_truth.json`, writing a backtick as `\x60`, never calling back into Stata, never using `shell=True`. Run it once through the wrapper as "Stata truth" shows (`DASH_REPO=<wt>`), read the log, and `git add -f` both files (do not commit).
  ]]></action>
  <verify><![CDATA[`grep -c '^r([0-9]*);' /tmp/dash-wp29-s05/extract/extract_date_units_truth.log` prints 0; `python3 -c "import json;d=json.load(open('<wt>/test/fixtures/date_units_truth.json'));print(d['histogram']['td:w30s14975']['bin'], [round(h,7) for h in d['histogram']['td:w30s14975']['heights']][:3], d['kpi']['all']['date']['sd']['display'], d['kpi']['tm2']['m']['mean']['display'], d['fits']['fp:td']['pwrs'], d['axis_labels']['kd_td']['dates_shown'], len(d['data']['date']))"` prints `13 [0.0025538, 0.0028226, 0.002957] 105.3335 2001m2 3 3 False 248`; `git -C <wt> ls-files --error-unmatch test/fixtures/date_units_truth.json` succeeds.]]></verify>
  <done>Stata's own histogram, kdensity, lpoly, fracpoly, summarize and axis-label results for sp500's date variables were recorded in a committed-to-be fixture with its provenance stamp, with nothing committed.</done>
</task>

<task type="auto" id="05-02">
  <name>Write the failing P0.8 tests</name>
  <files>test/test_date_units.py</files>
  <action><![CDATA[
Create `test/test_date_units.py` with the module setup and every P0.8 test of "TDD test stubs" under exactly those class and test names (the P0.20 classes come in 05-12). Import `dash_render as dr`, `test_help_claims_4 as hc4`, `js_runner`; read only the fixture for Stata's numbers and the independent `ms_td`/`ms_tm` oracles for positions. The new helpers do not exist yet: reference them as `dr._dash_date_units` etc. inside test bodies (not at import), so collection succeeds and each test fails on its own. Run `python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider 2>&1 | tee /tmp/dash-wp29-s05/05-P0.8-run.txt` against the unmodified worktree. Do not commit. Write `/tmp/dash-wp29-s05/05-P0.8-failure.txt`: one line per failing test with its assertion text (at least: `top max 3.47e-11` vs `.0029992`, the `1000 bins` warning, `x_lp` 0 points, `1329.5113` vs `1329.5387`, y `DatetimeAxis`, `-315619027200.0`, `date variable ''`, fmt `%td`), then a "guards (pass at base)" list.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider --collect-only 2>&1 | tail -1` reports the collected count and no error; the run reports failures for every non-guard test and no collection error; `/tmp/dash-wp29-s05/05-P0.8-failure.txt` exists and names every failing test and the guard list.]]></verify>
  <done>Every P0.8 regression test existed and failed for its recorded reason against the unmodified tree, the guards were listed, and nothing was committed.</done>
</task>

<task type="auto" id="05-03">
  <name>Add the two unit helpers and axis vars</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Run `gitnexus_impact` upstream on `_dash_float_values` and `_dash_figure_date_kind` and record the result. Add `_dash_date_units` (TR-05.1) and `_dash_units_to_axis` (TR-05.2) directly after `_dash_float_values` (:459-500), and `_dash_axis_vars` (TR-05.9) directly after `_dash_figure_date_kind` (:670-688), each with a docstring that cites Stata's units and the measured round trip. In `ServerAppBuilder._glyph_layer_lines` add `"_dash_date_units", "_dash_units_to_axis", "_dash_axis_vars"` directly after `"_dash_period_values"` (:28613) with a one-line comment `# Stata units for computed layers (WP-29 P0.8)`. Add the three entries of TR-05.16 to `test/function_test_map.py` in alphabetical place.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider -k "date_units_reads or units_to_axis or axis_vars"` passes; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k CarriesEveryName` and `python3 -m pytest test/test_resource_limits.py -q -n0 -p no:cacheprovider -k DefinesEveryName` pass.]]></verify>
  <done>The two conversion helpers and the axis-variable reader existed in both renderers, never raised on hostile input, and were mapped to their tests.</done>
</task>

<task type="auto" id="05-04">
  <name>Read and draw the fits in units</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Run `gitnexus_impact` upstream on `GlyphMapper._masked`, `GlyphMapper._layer_weights` and each `map_*` named below; report HIGH/CRITICAL before editing. Apply TR-05.4: the keyword-only `units=None` on `_masked` (convert before the view and NaN masks) and on `_layer_weights` (pass it to all six `_masked` calls), the new `_layer_units` instance method, the 13 call-site swaps (:8669, :8741, :8811, :8931, :9040, :9469, :9551, :9987, :10056, :10144, :10462, :12269, :12401), the fpfit/fpfitci `_masked` calls (:10010, :10080) and lowess's adjust (:9082-9083). Apply TR-05.5: add `_on_axis` and `_drop_off_dates` beside `_layer_weights` and convert the outputs of lfit, qfit, lfitci, qfitci, lowess, lpoly, lpolyci, fpfit, fpfitci, mspline and mband at the lines TR-05.5 lists (histogram and kdensity are 05-05). Keep both `_masked` and `_layer_weights` `@staticmethod`. Add `GlyphMapper._layer_units`, `GlyphMapper._on_axis`, `GlyphMapper._drop_off_dates` to `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider -k "TestTheUnitHelpers or TestLpolyOnADate or TestFpfitOnADate or monthly_lfit or date_y"` passes; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k "LayerWeights or CarriesEveryName"` passes.]]></verify>
  <done>Every fit and smoother read a date and its weight in Stata units through one gate and drew its output on the figure's axis, dropping off-range points with one note.</done>
</task>

<task type="auto" id="05-05">
  <name>Convert histogram, kdensity and their JS recount</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-05.6 to `map_histogram` (:10144-10221) and `map_kdensity` (:10462-10551): grid, counts, tops and densities in units; drawn edges and x through `_on_axis`; the contiguous kept run for bars; config fields `datekind`, `wdatekind`, `unit_edges`, `bin_first`, `x_eval` only for dates, every list built from kept finite values. Apply TR-05.7 to `_FILTER_JS`'s agg loop: the pair-loop conversions after the existing null tests with `!(w > 0)` moved after them, the unweighted-branch conversion, the histogram block's `uedges`/`first`/`n_grid` and the sliced `dash_scale`, and the kdensity block's `xe` evaluation, keeping the five marker strings verbatim (TR-05.7). Then confirm `test/js_runner.py`'s slicing still finds its markers.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider -k "TestTheJsUnits or test_agg_config_carries or test_width_and_start or saved_histogram_recount or saved_kdensity_recompute or inert_move"` passes. Some position checks need the histogram's or kdensity's date on x, and pass only after 05-06: `test_bars_match_twoway`'s `left[0]`, `test_density_matches_twoway`'s ms x (until 05-06 a lone kdensity's x axis is unmarked for dates, so `_on_axis` leaves its grid in units), `TestOutOfRange`, and `test_on_a_date_axis_it_is_drawn_at_the_dates`. `python3 -m pytest test/test_js_runner.py test/test_histogram_edge_rule.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Histogram and kdensity counted and estimated in Stata units in Python and in the saved page's recount alike, and no non-finite number reached the page configuration.</done>
</task>

<task type="auto" id="05-06">
  <name>Move univariate dates to x, match twoway</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Run `gitnexus_impact` upstream on `_dash_figure_date_kind`, `DashRenderer._make_figure_body` and `ServerAppBuilder._generate_app_source`; report the expected HIGH on `_make_figure_body` before editing. Apply TR-05.10: the univariate x-key rule in `_dash_figure_date_kind`, with its all-agree test unchanged. D05-1 is struck (01oct2026), so add no unit-labelled rule, define no `_DASH_UNIT_LABELLED_TYPES`, and add nothing to the served constants tuple. Apply TR-05.9's four saved sites in `_make_figure_body` and the matching four template sites. Apply TR-05.11's marking of the throwaway `_tfig` in `_dash_redraw_for` with `_rkinds` from `_dash_axis_vars`/`_dash_figure_date_kind` over `g.get('plots', [])` and the closure's `_date_vars`, the same calls the live figure makes. Update `_dash_figure_date_kind`'s docstring for rule 1 and for the ratified divergence sentence of TR-05.10.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider` passes entirely, including `TestTheAxisRule`, `test_a_date_layer_on_a_numeric_axis_is_drawn_in_its_units` and `test_served_redraw_uses_the_live_figures_axis`. `python3 -m pytest test/test_statistical_helpers.py test/test_resource_limits.py -q -n0 -p no:cacheprovider -k "CarriesEveryName or DefinesEveryName"` passes. `grep -c "_DASH_UNIT_LABELLED_TYPES" dash_render.py` prints 0. `python3 -c "import sys;sys.path.insert(0,'.');import dash_render as d;print(d._dash_figure_date_kind([{'type':'lfit','yvar':'close','xvar':'date'}],'xvar','',{'date':'td'}), d._dash_figure_date_kind([{'type':'kdensity','var':'date'}],'xvar','',{'date':'td'}), d._dash_figure_date_kind([{'type':'scatter','yvar':'close','xvar':'obs'},{'type':'lfit','yvar':'close','xvar':'date'}],'xvar','',{'date':'td'}))"` prints `td td None`. At `7421d3d` the same command prints `td None None`, because the kdensity's date was read on y.]]></verify>
  <done>A histogram's or kdensity's date sat on x in the variable's own format. Every axis whose layers all carried a date of one kind stayed a date axis, the lone unit-labelled fits included (the ratified divergence). A date layer on a mixed axis was drawn at its Stata values, and the served redraw used the live figure's axis kinds.</done>
</task>

<task type="auto" id="05-07">
  <name>Flip the date-axis extent pins</name>
  <files>test/test_date_range.py</files>
  <action><![CDATA[
D05-1 is struck (01oct2026), so only the A10 half remains. Every other `_COMPUTED` row, lfit/qfit/lfitci/qfitci/kdensity included, keeps the existing ms window and is not edited, because a computed layer is drawn back at its dates on the date axis. In `test/test_date_range.py`, rewrite `_COMPUTED` (:706-709) to exclude only `scatteri`, `pci`, `pcarrowi` and `function`. Replace its comment (:703-705) with the A10 rationale and the marker `WP-29 P0.8 (section 05)`. Make `_plot_for` (:712-722) set `o.setdefault("bwidth", "60")` for `lpoly`/`lpolyci`, with the same marker comment. Do not edit `test/test_served_dates.py`: it imports `_COMPUTED` and `_plot_for` (:51), so `test_every_layer_is_drawn_where_the_saved_one_is` gains the two rows with no edit and keeps both `served == saved` and its ms window. Do not add `_UNITS`, `_LO_U` or `_HI_U`. Append one line to `/tmp/dash-wp29-s05/05-P0.8-flips.txt`: `Flipped: test/test_date_range.py::_COMPUTED (and through its import test/test_served_dates.py::TestTheServedFigureReadsTheDateAsTheSavedOne::test_every_layer_is_drawn_where_the_saved_one_is) -- lpoly and lpolyci were excluded because they drew nothing on the twelve 30-day rows, both with the default bandwidth and with any bwidth() read in ms; with bwidth(60) read in days they draw, at the dates on the date axis (the default bandwidth on these rows is section 11's to measure)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_range.py test/test_served_dates.py -q -n0 -p no:cacheprovider` passes. `python3 -m pytest test/test_date_range.py --collect-only -q -n0 -p no:cacheprovider | tail -1` prints `180 tests collected` and the same for `test/test_served_dates.py` prints `105 tests collected`. At `7421d3d` they print 176 and 103 (measured 01oct2026); if the worktree base differs, the counts are the base's +4 (2 types x 2 holes) and +2. `python3 -m pytest test/test_date_range.py --collect-only -q -n0 -p no:cacheprovider | grep -c "test_every_x_it_draws_lies_among_the_dates"` prints 72 (68 at the base). `git -C <wt> diff --name-only -- test/test_served_dates.py` prints nothing.]]></verify>
  <done>lpoly and lpolyci joined the pins that every computed layer over a date is drawn among the dates, both modes. No pin was deleted, the other rows kept their ms window (the date axis is kept), and the flip was recorded for the commit body.</done>
</task>

<task type="auto" id="05-08">
  <name>Add parity cases and absorb fallout</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
Append to `DATE_CORPUS` (test_mode_parity.py:1629-1675, after the last `_W` entry, before the WP-28 B2 entries) five cases: `_case("a histogram of a date, width() and start() in days", [plot_for("histogram", {"width": "3", "start": "15340"}, var="when")], _W)`, `_case("a kdensity of a monthly date", [plot_for("kdensity", {"bwidth": "1"}, var="when")], {"formats": {"when": "%tm"}})`, `_case("an lpoly over a date, bwidth() in days", [plot_for("scatter", yvar="mpg", xvar="when"), plot_for("lpoly", {"bwidth": "3"}, yvar="mpg", xvar="when")], _W)`, `_case("a lone lfit over a date keeps the date axis", [plot_for("lfit", yvar="mpg", xvar="when")], _W)` (D05-1 struck), `_case("a date fit on an axis shared with a number", [plot_for("scatter", yvar="mpg", xvar="weight"), plot_for("lfit", yvar="mpg", xvar="when")], _W)` (D05-4's mixed axis, Evidence §8) (`plot_for`, test_server_layer_defects.py:81, applies `**extra` with `p.update(extra)`, so `var="when"` replaces `"mpg"`). Edit neither `ALLOWED` nor `_MUST_WARN` (R6). Then run `python3 -m pytest test/test_mode_parity.py test/test_dates.py test/test_kpi_format.py test/test_statistical_helpers.py test/test_help_claims_4.py test/test_function_test_map.py test/test_embedded_cells.py -q`; any failure is either a pin of the ms defect (flip it in its file with a `Flipped:` line appended to the flips file, which may add that file to this task) or a regression (fix `dash_render.py`, never the test).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "date or lfit or kdensity or lpoly or histogram"` passes; the listed files pass with no new skips.]]></verify>
  <done>Both modes drew every new date case identically, and every other fallout was flipped with a recorded reason or fixed in the code.</done>
</task>

<task type="auto" id="05-09">
  <name>Certify the date layers against live Stata</name>
  <files>test/test_wp29_truth.cscript</files>
  <action><![CDATA[
Append the block `* ==== S05 P0.8: computed layers on a date in Stata units ====` … `* ==== end S05 P0.8 ====` above `* ==== append new blocks above this line ====` (after any lower-numbered section's block, R1), gated on `WP29_ONLY` as "Stata truth" shows, holding DU-01..DU-06 as specified there. Inside the `if`: `sysuse sp500, clear`, `gen m = mofd(date)`, `format m %tm`; `capture dash clear`; each dash page is built with `saving("<path>", replace)` under the script's work dir and read with a Python helper loading the page's document by `Document.from_json` (HE-05's `_he5_read` pattern, new name `_du_read`); the served app (DU-06) is built with `dash build, saving(<app>) server replace filter(close, type(slider))`, `exec`'d with the curdoc attach replaced by `pass`, and its slider fired as KF-03 does. Every expected number is computed live in the block (`twoway__histogram_gen`, `twoway__kdensity_gen`, `lpoly ... nograph gen()`, `fracpoly: regress` + `predict double`), never copied from the fixture. Each case ends with the scaffold's done-helper printing `DU-0n PASS: ...`; a failure never `exit`s. Header comment: add `S05  P0.8 / P0.20 date units (DU-01..DU-06, KD-01..KD-03)` to the script's block list. Run it through the driver of "Stata truth".
  ]]></action>
  <verify><![CDATA[`grep -c "DU-0[1-6] PASS" /tmp/dash-wp29-s05/run_test_wp29_truth.log` prints 6; `grep -c "FAIL\|SKIP" /tmp/dash-wp29-s05/run_test_wp29_truth.log` prints 0; `grep -c '^r([0-9]*);' /tmp/dash-wp29-s05/run_test_wp29_truth.log` prints 0.]]></verify>
  <done>Stata itself certified, in both modes and after a served filter move, that dash's date histograms, densities, smooths and fractional-polynomial fits were its own.</done>
</task>

<task type="auto" id="05-10">
  <name>Document the unit and axis rules</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
In `dash.sthlp` (1) the `bwidth(#)` synopt (:1915-1929): after "in the units of x" add ", days for a {cmd:%td} x and months for a {cmd:%tm} one,". (2) After the paragraph that ends "is named in a note and not drawn." (:2512-2519) add one `{pstd}` paragraph with exactly these claims, in SMCL: the 13 computed types compute from a date in its own units as twoway does; `width()`, `start()`, `bin()`, `bwidth()`, `range()` and `n()` read days for %td, milliseconds after 01jan1960 for %tc, and weeks, months, quarters, half-years or years for the others; a density is per day (per month for %tm), so `dash histogram date, width(7)` draws week-wide bars; a histogram's or kdensity's variable is on the x axis; an axis shows dates whenever every layer's variable on it is a date of one kind, and a date layer that shares an axis with a plain number is drawn at its Stata values, as twoway draws it; a bar or point computed outside 01jan0100 to 31dec9999 is not drawn and a note says how many. Then add, as its own sentences (D05-1 struck 01oct2026), the one difference from twoway, with each phrase quoted below kept whole on one source line so the verify greps find it: "{it:Difference from twoway:} twoway labels the axis with the variable's numbers (15000, 15100, ...) when the first layer is {cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}, {cmd:kdensity}, {cmd:lpoly} or {cmd:lpolyci}; dash keeps its date axis there and draws those layers at the dates their values denote." and "So {cmd:dash kdensity date} has a date axis where {cmd:twoway kdensity date} shows 15000 to 15400, and a {cmd:range()} that reaches before 01jan0100 loses those points, with a note, where twoway draws them." Grep `test/test_help_*.py` and `test/test_help_claims_*.cscript` for the changed sentences and update any pin in the same task (adding its file only if needed).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_examples.py test/test_help_claims_4.py -q -n0 -p no:cacheprovider` passes. `grep -c "dash keeps its date axis there" dash.sthlp` prints 1, `grep -c "{cmd:dash kdensity date} has a date axis" dash.sthlp` prints 1, and `grep -c "per day" dash.sthlp` prints at least 1. All three print 0 at `7421d3d` (measured 01oct2026).]]></verify>
  <done>The help stated the unit rule, the axis rule, the ratified difference from twoway (a lone lfit, qfit, lfitci, qfitci, kdensity, lpoly or lpolyci over a date keeps a date axis, and a lone kdensity's pre-0100 range() points are dropped) and the off-range note, in the paragraphs this section owns.
</task>

<task type="auto" id="05-11">
  <name>Close P0.8 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
BUGS.md: find the entry S01 opened for P0.8 (`grep -n "WP-29 section 05" BUGS.md`, the one about computed layers on a date); change `- [ ]` to `- [x]` in place and rewrite its Resolution: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.8). Every computed layer reads a date and its weight in the variable's Stata units through GlyphMapper._masked(units=) / _layer_units and draws through _on_axis / _dash_units_to_axis; histogram and kdensity configs carry datekind, unit_edges, x_eval, and the saved recount converts with dash_stata_value_of; histogram and kdensity draw their variable on x; a date layer on an axis shared with a non-date is drawn at its Stata values as twoway draws it; a lone lfit, qfit, lfitci, qfitci, kdensity, lpoly or lpolyci over a date keeps dash's date axis where twoway labels day numbers (ratified 01oct2026, a documented divergence in the help); positions outside Stata's dates are dropped with one note; both renderers (the served redraw marks its figure with the live figure's kinds). Pinned by test/test_date_units.py::TestHistogramOnADate::test_bars_match_twoway, ::TestLpolyOnADate::test_explicit_bwidth_draws_statas_curve, ::TestTheAxisRule::test_the_axis_is_twoways, ::TestTheAxisRule::test_a_unit_labelled_first_layer_keeps_the_date_axis, ::TestEveryComputedLayer::test_a_date_layer_on_a_numeric_axis_is_drawn_in_its_units, ::TestOutOfRange::test_out_of_range_edges_never_reach_the_page_json, test/test_wp29_truth.cscript DU-01; fixture test/fixtures/date_units_truth.json. Residual, deferred (WP-29): xlabel(minmax) on a mixed numeric axis whose first layer's variable is a date reads epoch ms (P1.23); barwidth() on a date axis (GAPS2 A3); function/scatteri/pci on a date axis and the histogram tooltip in epoch ms (P1.23); fractional period values are floored on load; horizontal (P1.9).` In `test/test_tracking_documents.py` delete only the `"P0.8": ...` line of `WP29_OPEN`. In CHANGELOG.md replace `<!-- WP-29 P0.8 -->` in place with lines each ending `(WP-29, P0.8)`, naming command, old value (from the failure file) and new: `dash histogram date, width(30) start(14975)` 15 bars with every row in the last and the note that width(30) needs over 1000 bins, densities per millisecond (3.47e-11), now 13 bars 30 days wide from 14975, densities per day (.0025538 …); `dash kdensity date, bwidth(10)` a curve of spikes to 1.35e-04, now Stata's curve per day; `dash lpoly close date, bwidth(30)` nothing drawn, now Stata's curve (1325.6916 at 02jan2001 with n(5)); `dash fpfit close date` 1329.5113 at 02jan2001, now 1329.5387; histogram/kdensity of a date: date axis on y with x drawn in ms on a numeric axis, now the date axis on x; `(scatter close obs) (lfit close date)`: the fit drawn at 978393600000 and beyond (epoch ms) beside obs 1..248, now at the day numbers 14977-15340 as twoway draws it. No line claims a lone lfit/qfit/lfitci/qfitci/kdensity/lpoly/lpolyci gets twoway's numeric axis: D05-1 was struck, and those keep dash's date axis. Run `gitnexus_detect_changes()`; then the full suite once (`python3 -m pytest test/ -q`; read its log, never relaunch); then 05-09's driver run; `git add` only this commit's paths (`git diff --cached --name-only` lists dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md, scripts/extract_date_units_truth.do and test/ files); commit with the subject and body of "Commit boundary".
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c '<!-- WP-29 P0.8 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-29, P0.8)' CHANGELOG.md BUGS.md` shows at least 1 in each; `git log -1 --format=%s` ends `(WP-29 P0.8)`; `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0; `git show --stat HEAD` lists no CLAUDE.md, .gitignore or *.html.]]></verify>
  <done>P0.8 was closed in BUGS.md naming existing tests, its CHANGELOG marker was replaced by the measured results, and one green commit on wp29-s05 carried the fix, its tests, flips, fixture and truth block.</done>
</task>

<task type="auto" id="05-12">
  <name>Write the failing P0.20 KPI tests</name>
  <files>test/test_date_units.py</files>
  <action><![CDATA[
On the tree commit 1 left, append the P0.20 classes of "TDD test stubs" (`TestKpiOfADate`, `TestTheKpiConfig`) to `test/test_date_units.py` under exactly those names, reading `kpi` displays from the fixture, KPI dicts in the form `{"name": "k_<stat>_<var>", "stat": s, "var": v, "fmt": "", "title": "T", "update": "filter", "if_expr": ""}` (`"update": "brush"` for the brush test), the node KPI slice built as `test/test_kpi_brush.py:250-253` builds it. Run `python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider -k "Kpi" 2>&1 | tee /tmp/dash-wp29-s05/05-P0.20-run.txt`. Do not commit. Write `/tmp/dash-wp29-s05/05-P0.20-failure.txt` with each failing test's assertion (at least `9.10e+09` vs `105.3335`, `8.28e+19`, `1.60e+10`, `.0091564`, `2.46e+14`, `2001m1` vs `2001m2`, the KeyError on `unitkind`, the ms note) and the guard list.
  ]]></action>
  <verify><![CDATA[The run reports failures for every non-guard KPI test and no collection error; `/tmp/dash-wp29-s05/05-P0.20-failure.txt` exists.]]></verify>
  <done>Every P0.20 regression test existed and failed for its recorded reason on the tree the P0.8 commit left, with nothing committed.</done>
</task>

<task type="auto" id="05-13">
  <name>Take Python KPI statistics in units</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Run `gitnexus_impact` upstream on `_dash_kpi_column`, `DashRenderer._kpi_column`, `_dash_format_kpi_value` and `ServerAppBuilder._generate_app_source`. Apply TR-05.12 (`_dash_kpi_unit_kind` after `_dash_kpi_date_valued` :23437; `_dash_kpi_column`'s `kind` parameter, the refusal, the per-kind sum note, the unit Series) and TR-05.13 (`_kpi_column` passes the kind; `_dash_format_kpi_value`'s date branch formats the Stata value and its docstring says so; the template's `_compute_kpi(df, stat, varname, date_vars=None)` and its three callers :30905, :31253, :31335). Add `"_dash_kpi_unit_kind"` after `"_dash_kpi_date_valued"` (:28636) in the functions tuple and `_dash_kpi_unit_kind` to `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider -k "first_paint or monthly_mean or sum_note or missing_kind or unit_kind_rule"` passes; `python3 -m pytest test/test_resource_limits.py -q -n0 -p no:cacheprovider -k DefinesEveryName` passes.]]></verify>
  <done>Every KPI statistic of a date but a count was taken of its Stata values at first paint in both modes, the sum note named the units, and a date column without a kind was refused.</done>
</task>

<task type="auto" id="05-14">
  <name>Take JS KPI statistics in units</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-05.14: `"unitkind"` in `_kpi_callback_config` (:27360-27420, beside `datekind`, with a comment that it is data only); in `function dash_apply_kpis(` rename the filtered array to `_vals0`, add the `vals` conversion line after it, and make the date branch `text = dash_fmt_text(result, k.fmt);`. Change nothing else in the function and keep the slice markers TR-05.14 names; confirm `test/test_kpi_values.py:343-346` and `test/test_kpi_brush.py:250-253` still slice cleanly.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_units.py -q -n0 -p no:cacheprovider -k "Kpi"` passes; `python3 -m pytest test/test_kpi_values.py test/test_kpi_brush.py test/test_filter_exclusion_sets.py -q -n0 -p no:cacheprovider` passes; `python3 -c "import sys;sys.path.insert(0,'.');import dash_render as d;s=d._FILTER_JS;assert s.index('// ---- KPI recompute, shared by') < s.index('function dash_apply_kpis(') < s.index('dash_apply_kpis(new_data,')"` prints nothing.]]></verify>
  <done>After a filter move and after a brush the saved page took each date KPI statistic of its Stata values, dropped what could not convert, and wrote date-valued results directly in their picture.</done>
</task>

<task type="auto" id="05-15">
  <name>Flip the KPI pins that assumed milliseconds</name>
  <files>test/test_date_range.py, test/test_server_layer_defects.py, test/test_kpi_format.py</files>
  <action><![CDATA[
Flip, each with a comment `WP-29 P0.20 (section 05)` and a `Flipped:` line appended to `/tmp/dash-wp29-s05/05-P0.20-flips.txt`: `test_date_range.py::TestTheDateHelpers::test_a_kpi_sum_of_dates_neither_wraps_nor_names_the_wrong_epoch` (:982-994) to call `dr._dash_kpi_column(col, "sum", "date", "td")` and expect `40_000 * 2936549.0` (rel 1e-12), a note containing `days since 01jan1960`, max `== 2936549.0`, keeping the no-wrap docstring point; `::test_the_page_callback_writes_a_kpi_year_in_four_digits` (:1009-1030) to set `const result = {td: -679350, ty: 100, tm: -22320, tc: -58695840000000}[kind];` with the same expected texts; `test_server_layer_defects.py::TestTheKpiFormatHelpers::test_a_date_valued_statistic_is_shown_as_a_date` (:1105-1113) to pass `15342.0` (keep `_MS_02JAN2002` only if another test uses it); `test_kpi_format.py::TestFirstPaint::test_every_kpi_row_of_the_fixture_saved` (:195-197) to compare `got` directly with no `_dash_stata_value_of` (A6). Reasons: the statistic is now summarize's own Stata value, so a sum is of day numbers and a date-valued statistic is a day number.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_range.py test/test_server_layer_defects.py test/test_kpi_format.py -q -n0 -p no:cacheprovider` passes; the flips file holds four `Flipped:` lines.]]></verify>
  <done>Every pin that read a date KPI in epoch milliseconds read it in Stata units, none was deleted, and each flip was recorded.</done>
</task>

<task type="auto" id="05-16">
  <name>Certify KPI cards and add parity</name>
  <files>test/test_wp29_truth.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
Append the block `* ==== S05 P0.20: KPI statistics of a date in Stata units ====` … `* ==== end S05 P0.20 ====` directly after 05-09's S05 block, gated identically, with KD-01..KD-03 as "Stata truth" specifies: `dash scatter close date, name(g1)`; `dash kpi sd(date)`, `var(date)`, `iqr(date)`, `cv(date)`, `sum(date)`, `skewness(date)`, `mean(m)`, `p50(m)`, each with `name(kd<i>) title("T")`; expected strings computed live with `summarize ..., detail` and `: display %9.0g` / `%tm`, and for KD-02 with `if close>=1200`; the saved card read as KF-01 reads it, the served cards and the slider move as KF-03 does them; KD-03 on a two-observation dataset. Append to `DATE_CORPUS` in `test/test_mode_parity.py` `_case("spreads and a sum of a date", [_sc()], _W, kpis=[_kpi(stat="sd", var="when"), _kpi(name="k2", stat="iqr", var="when"), _kpi(name="k3", stat="sum", var="when")])`. Run the cscript driver and the parity file.
  ]]></action>
  <verify><![CDATA[`grep -c "KD-0[1-3] PASS" /tmp/dash-wp29-s05/run_test_wp29_truth.log` prints 3 and `grep -c "DU-0[1-6] PASS" /tmp/dash-wp29-s05/run_test_wp29_truth.log` prints 6; `grep -c "FAIL\|SKIP" /tmp/dash-wp29-s05/run_test_wp29_truth.log` prints 0; `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "date"` passes.]]></verify>
  <done>Stata itself certified the date KPI cards in both modes and after a served move, and the parity corpus held a date-spread case.</done>
</task>

<task type="auto" id="05-17">
  <name>Document KPI statistics of a date</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
In `dash.sthlp` :1297-1304, after "shown in {cmd:%9.0g} unless {cmd:fmt()} says otherwise." add: "Each statistic is taken of the variable's Stata values, as {cmd:summarize} takes it: {cmd:sd()} of a {cmd:%td} variable is in days (105.3335 for {cmd:date} in {cmd:sysuse sp500}), {cmd:var()} in days squared, {cmd:iqr()} in days, {cmd:cv()} is the sd over the mean day number, and {cmd:sum()} adds up the day numbers, which a note says has no meaning; the mean of 2001m1 and 2001m3 is 2001m2." Grep the help-claims tests and cscripts for the changed paragraph and update any pin.
  ]]></action>
  <verify><![CDATA[`grep -c "105.3335" dash.sthlp` prints 1; `python3 -m pytest test/test_help_claims_4.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The help said that a KPI statistic of a date is taken in the variable's units, with sp500's sd as the example.</done>
</task>

<task type="auto" id="05-18">
  <name>Close P0.20 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
BUGS.md: find the P0.20 entry S01 opened (`grep -n "WP-29 section 05" BUGS.md`), change `- [ ]` to `- [x]` in place and rewrite: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.20). A KPI statistic of a date variable other than count and dcount is taken of its Stata values in _dash_kpi_column (kind from date_vars; refused without one), in the saved renderer, the served _compute_kpi (all three callers pass _date_vars) and the page's dash_apply_kpis (config unitkind, converted with dash_stata_value_of, null dropped); date-valued results are written directly in their picture; the sum note names the units. Pinned by test/test_date_units.py::TestKpiOfADate::test_first_paint, ::TestKpiOfADate::test_after_a_move, ::TestKpiOfADate::test_after_a_brush, ::TestTheKpiConfig::test_unitkind_reaches_every_statistic_but_counts, test/test_wp29_truth.cscript KD-01; fixture test/fixtures/date_units_truth.json.` Delete only `WP29_OPEN`'s `"P0.20"` line. Replace `<!-- WP-29 P0.20 -->` in place with lines ending `(WP-29, P0.20)`: `dash kpi sd(date)` on sp500 9.10e+09, now 105.3335; var 8.28e+19, now 11095.14; iqr 1.60e+10, now 185; cv .0091564, now .0069496; sum 2.46e+14, now 3758900, with the note now naming days since 01jan1960; the mean of a %tm 2001m1 and 2001m3 2001m1, now 2001m2. Run `gitnexus_detect_changes()`, the full suite once, the 05-16 driver run; stage only this commit's paths; commit with the P0.20 subject and body.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c '<!-- WP-29 P0.20 -->' CHANGELOG.md` prints 0; `git log -1 --format=%s` ends `(WP-29 P0.20)`; `git log -2 --format=%B | grep -ciE 'claude|anthropic'` prints 0; `git log --oneline -2` shows the P0.8 and P0.20 commits.]]></verify>
  <done>P0.20 was closed in BUGS.md naming existing tests, its CHANGELOG marker carried the measured old and new cards, and a second green commit on wp29-s05 completed the section.</done>
</task>

## Section completion criteria

- In both modes, before and after a filter move, every computed layer over a date equals Stata's numbers from the fixture and from live Stata in `test_wp29_truth.cscript`: histogram bars, kdensity curves, lpoly with an explicit bandwidth, fpfit, and `%tm` lfit. Each is drawn where twoway draws it.
- `dash kpi` spreads, sums and date-valued statistics of a date equal `summarize`'s display text, saved and served, at first paint, after a move and after a brush.
- histogram/kdensity dates are on x in the variable's own format. `yline`, `xline`, `xlabel` and `yscale(log)` behave as in twoway. Every axis twoway labels with dates is a date axis in dash (10 measured cases). The 12 measured cases where twoway labels numbers keep dash's date axis, which is the ratified divergence (D05-1 struck 01oct2026), pinned and documented. A date layer on a mixed numeric axis is drawn at its Stata values in both modes, after a served move as well.
- No non-finite number reaches page JSON. Off-range positions are dropped with one note per layer, in both modes.
- Two commits, `(WP-29 P0.8)` and `(WP-29 P0.20)`, each green on the full suite, each holding its failing tests, fix, flips and closed BUGS.md entry. The first also holds the fixture and the extract script. No test was deleted, and the collected-test count did not fall.
- BUGS.md: both entries `- [x]` naming existing tests. CHANGELOG: both markers replaced. `WP29_OPEN`: both keys gone. dash.sthlp: three paragraphs updated.

## Notes

- **Traps.**
  - `dash_stata_value_of(null)` reads `Number(null)` as 0, a 1960 date. Convert only after the existing null/NaN tests, and drop a `null` result (A5).
  - Keep the JS marker strings of TR-05.7 and TR-05.14 verbatim. `test/js_runner.py`, `test_kpi_values.py`, `test_kpi_brush.py`, `test_filter_exclusion_sets.py` and the brush wiring slice by them.
  - Compare round-tripped positions with a tolerance, never exactly: units → ms → units on %td is exact only to about 1e-8 day.
  - Period kinds are drawn piecewise-linear between period starts (invisible kinks).
- **Renderer order.**
  - The saved renderer marks its figure (:26023) before any layer is drawn.
  - The served live figure is marked at :30401.
  - The served redraw's throwaway figure must be marked by TR-05.11 with the live figure's kinds. Without it, a date layer on a mixed numeric axis redraws in ms after a move (`test_served_redraw_uses_the_live_figures_axis[mixed-numeric]`). This holds with D05-1 struck.
  - An unmarked figure falls back to the variable's kind, so a mapper used on its own (unit tests) still draws ms on a date.
- **Notes printed in a session.** The off-dates note is a mapper note. Like every mapper note (the existing "1000 bins" note included), the served app prints it in the session, and the parity guard compares both modes' merged lists (R6). It is not a build-time decision, so no `ServerAppBuilder` plan is added.
- **Fixture scope (R5).** One new fixture. The lpoly default bandwidths, `se()` and `pwidth` are recorded for S11 only as `r(bwidth)` values where listed; S11 extracts its own truth. Never patch the fixture by hand: re-run 05-01.
- **Shared files (R1-R8).**
  - R1: the two blocks go in `test_wp29_truth.cscript` only; the runner and the hygiene pins are untouched.
  - R2: the copy-list anchors are those of TR-05.3. With D05-1 struck, S05 adds nothing to the constants tuple, so index.md's R2 row for S05 must read "—" in its constants column (reported to the orchestrator; this section does not edit index.md).
  - R3: BUGS.md and CHANGELOG are edited in place only at this section's entries and markers, and `test_tracking_documents.py` loses only its two keys. The dash.sthlp paragraphs this section owns are :1297-1304, :1915-1929 and the new paragraph after :2519; S11 (batch 2) edits the lpoly paragraphs.
  - R5: one new fixture, `git add -f`.
  - R6: DATE_CORPUS additions only.
  - R7: flips are listed in the two flips files.
  - R8: run `gitnexus_impact` per symbol and `gitnexus_detect_changes()` before each commit.
- **For later sections.**
  - S11 rewrites `map_lpoly`/`map_lpolyci` and `_default_lpoly_bwidth` on this tree. Its inputs arrive in units through `_layer_units`, and its outputs must keep going through `_on_axis`/`_drop_off_dates`. Its rule-of-thumb bandwidth must stay stable for `%tc` x of about 1.3e12 (Stata itself leaves 3 of 5 grid points missing at its %tc default, 32558842 ms).
  - S12's stale cue reads the estimation sample as `_layer_weights` applies it, now with `units=`. The saved histogram/kdensity recount stays (PLAN.md non-goals) with this section's conversions.
  - P1.9 (`horizontal`) must teach `_dash_figure_date_kind` the univariate y case.
  - D05-1 struck: a lone `dash lpoly close date` draws `x_lp` in epoch ms on a date axis, not at Stata's grid values. S11's LW-05 (and any S11 pytest that compares a date lpoly's drawn x with `lpoly ... generate(gx gy)`) must compare x with `(gx - td(01jan1970))*86400000` for `%td`, or `gx - tc(01jan1970 00:00:00)` for `%tc`, never with `gx` itself. S10 and S12 re-derive any date-axis pin at their batch base (index.md's "If struck" column).
- **Stata invocation.** Every run goes through `scripts/stata_slot.sh <scratch> <file>.do`. It holds one of three slots and sets `STATATMP=<scratch>/tmp/`, with `dash_nobrowser=1`. Never use the GUI, a bare `stata-mp`, or the full cert suite inside the section. A cscript SKIP (exit 222 when `c(python_exec)` is empty under concurrency) is not a pass.
- **Notes for the closeout (A5 of index.md: S15 edits these, not this section).**
  - GAPS2.md: E1's "Residual, deferred" line (KPI spreads of a date in ms) becomes Closed in WP-29 P0.20, with the commit sha.
  - REMAINING.md: rows REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a and REM-08-04-C12 are marked closed by P0.8's commit.
  - DROPIN-REMAINING.md: P0.8 and P0.20 are annotated with their commits.
  - AGENTS.md "Invariants introduced by WP-29": "A computed layer and a KPI statistic of a date are computed in the variable's Stata units: inputs through `GlyphMapper._masked(units=)`/`_layer_units` and `_dash_kpi_column(kind)`, outputs through `_on_axis`/`_dash_units_to_axis`, which follows the figure's marked axis kinds (the served redraw's throwaway figure included). A computed position outside Stata's dates is dropped with one note, and no non-finite number reaches page JSON. dash keeps its date axis where twoway's first-plot rule labels numbers (ratified 01oct2026). Pinned by `test/test_date_units.py`."
  - Documented divergence, ratified 01oct2026, recorded as such and not as a residual: a lone or first `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` over a date keeps dash's date axis where twoway labels numbers (12 measured cases, `(lfit)(scatter)` among them). A lone kdensity's `range()` points before 01jan0100 are dropped where twoway draws them.
  - Residuals to record:
    - `xlabel(minmax)` on a mixed numeric axis whose first layer's variable is a date reads epoch ms (Evidence §8; P1.23);
    - `barwidth()` on a date axis (GAPS2 A3);
    - `function`/`scatteri`/`pci`/`pcarrowi` on a date axis (P1.23);
    - histogram and fit tooltips in epoch ms (P1.23);
    - fractional period values floored on load;
    - `horizontal` (P1.9).

    Each of the P1.23 fixes should reuse `_dash_units_to_axis`.
