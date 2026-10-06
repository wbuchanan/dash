# Section 44: tsnatscale on %td-%ty default axes (P1.3 part b, M1)

> Part of: WP-30 · Items: P1.3 part b (entry `P1.3b`; GAPS2-B25-a for date axes; BUGS.md:2523, the open WP-27 tsnatscale entry) · Risk: red · Batch: 15 (merge order S42, S43, S44; lands last) · Depends on: 21, 35 · Blocks: 52, 57 · Tasks: 14, 1 commit · Case prefix: TN

## Review amendments

Extra scrutiny (red): the model, the ticker routing and S21's/S35's chain were re-read at `c96facd` and in their section files; D-44b was re-measured.

- Fixed (major): "prepended once at import" allowed a later rebinding of `_DASH_AXIS_FINISH_JS`. `_FILTER_JS` and the zoom callbacks copy the finisher's text when they are built (S21 TR-21.10/21.11), so the saved filter callback would have called an undefined `dash_tsnatscale` after every move. The port now goes into the one statement that assigns the finisher, and 44-07's verify and `TestTheServedCopy` assert `_FILTER_JS` carries it once.
- Fixed (major): the BUGS.md:2523 closure appended "Closed …" to a Resolution reading "Not fixed: it stays open because …", which leaves a closed entry saying it is open. The Resolution line is now replaced in place (TR-01.10 item 1's form), still without the `(WP-30, P1.3b)` token. This answers the orchestrator's open S44 item on the wording.
- Fixed (major): `$S` was shared with S42 and S43 (parallel, same log names); it is now `<scratch>/s44`.
- Fixed (minor): D-44b's measurement covered [-100,000, 100,000], but `_dash_ts_daily` iterates `{floor(lo), ceil(lo)}` over `%td` values up to 2,936,549. Re-measured over [-3,000,000, 3,000,000] (0 exceptions), and the pair test covers the `%td` range. The no-`document`/`window` check now targets `_DASH_TSNATSCALE_JS`, not S21's whole finisher. 44-10's Chrome node id is completed. 44-03's CORPUS case names `_DF`'s `%td` column `when`. The truth block states TR-01.10's form.
- Checked: `_dash_axis_count_ticks` (:22550) routes ts kinds to the model in epoch ms, and over P07's range gives 14976, 15066, 15157, 15249, 15341 (twoway's quarterly ticks); an `"su:"` kind falls to linear today, so TR-44.3's branch is the whole change. The four set sites (:22333, :22345, :22452, :22454) and `ks` (:22340) are as E1 says, and `ks` is ascending for n ≤ 62 (re-measured). The copy-list anchors (:32996-32998) and `_TS_FLOOR`/`_TS_SWEEP_FLOOR` (test_natscale_axes.py:144-147) hold. S21 defines the finisher after `_DASH_TICK_EVERY_JS` (:22878), below `_DASH_TS_LIMITS` (:22274). No function is shared with S42 or S43.
- Rejected: 44-13's `<files>none</files>`. It is a check-only step before the commit task and edits nothing.
- The review pass applied both lenses.

**Binding readings applied in this file** (M1; register P1.3.2, P1.3.3, P1.3.5, P1.3.8, X.1; index A8 (ratification item 2), A9 (item 3), A153, R2, R11, R12):
- **M1 / P1.3.5 / A8 (ratification item 2, pending).** `%td`, `%tw`, `%tm`, `%tq`, `%th` and `%ty` default axes take dash's fitted tsnatscale model, `_dash_tsnatscale_ticks`, which agrees with twoway on 52-66% of `%td`-`%th` ranges and 98% of `%ty`. The agreement floors are pinned; the rest stays P2.19. The help and BUGS.md state the rates. The model's weights are not refitted here.
- **P1.3.2.** Date axes, default and `#N`, re-tick over the kept rows after every filter move in both modes, y2/x2 included: S44 lifts S21's D-21e date hold.
- **P1.3.3 / A7.** A zoom on a date axis re-ticks by the same model over the visible range, through the same JS.
- **P1.3.8 / A9 (ratification item 3, pending).** The served re-finish keeps adding at most 0.2 s per figure per move at 500k rows; 100 saved by() panels settle within 1 s of the time measured at the batch-15 base.
- **A153 / R11.** S44 is batch 15's one finisher editor. It extends S21's `_dash_count_axes`, `_dash_axis_plan` and `_DASH_AXIS_FINISH_JS` on the date path only. S21's call sites cover dates, so S44 does not edit `_generate_app_source`, `_FILTER_JS` (except through `_DASH_AXIS_FINISH_JS`), `build_dropdown`/`build_slider`/`build_range` or `DashRenderer.render`. No BokehJS view internals.
- **S35's hand-off (section-35 "Notes for S44").** A mixed axis whose `_dash_axis_unit_format` is a `%td`-`%ty` format takes the model's ticks in Stata units, for the default ticker and `#N` alike; second date axes (`_dash_axis_date_kind(fig, "y2")`) take the default ticker too; S44's entry drops S35's residual sentence.
- **M5 / M6.** Nothing is refused and nothing is noted: a tick choice is drawn silently, as twoway draws it.
- **Lands last in batch 15** (manifest note). S52 (batch 18) then unions `add` with this ticker.

**Section decisions (this file).**
- **D-44a. One model, three callers.** The Python model stays the one source of truth. Build (both modes) and the served re-finish call `_dash_axis_count_ticks(lo, hi, n, kind)`, which already routes a date kind to `_dash_tsnatscale_ticks`. The saved re-finish and both modes' zoom call a line-for-line JS port, `dash_tsnatscale`, held in a new constant `_DASH_TSNATSCALE_JS` that is prepended once to `_DASH_AXIS_FINISH_JS` at import, as S35 prepended `_DASH_DATE_UNITS_JS`.
- **D-44b. Iteration order made explicit before porting.** The model iterates two-element integer sets (`{math.floor(x), math.ceil(x)}`, four sites) and the set `ks`; ties go to the first candidate. CPython orders a two-element set of consecutive integers `a, a + 1` as `a + 1, a` exactly when `(a + 1) & 7 == 0` (measured over every `a` in [-3,000,000, 3,000,000], which holds every `%td` value from 0100 to 9999 (-679,350 to 2,936,549) that `_dash_ts_daily`'s `{math.floor(lo), math.ceil(lo)}` can meet, including `hash(-1) == -2`; an int's hash is itself below 2**61, so the rule depends only on its low three bits), and `ks` is ascending for every `n` up to 62 and not beyond (measured). S44 replaces the sets with a new `_dash_ts_pair(x)` that returns that order, and `ks` with `sorted(ks)`. For every `n` the fixture holds (2-12) the answers are unchanged by construction; 44-01 proves it over the fixture and a seeded sweep against the unmodified code.
- **D-44c. Mixed date-labelled axes** carry a pseudo-kind `"su:<k>"` (Stata units of date kind `k`), stamped on the figure by `_dash_apply_axis_options`/`_dash_finish_secondary_axes` as `fig._dash_unit_kind[<axis name>]`. `_dash_axis_count_ticks` answers it with `_dash_tsnatscale_ticks(lo, hi, n, _DASH_TS_UNITS[k])` directly on the Stata values (no millisecond conversion); the JS does the same.
- **D-44d. Python floats.** `round()` is round-half-even and `"%.12g" % v` is twelve significant digits; the JS port uses `dash_round_half_even` and `Number(v.toPrecision(12))`, never `Math.round`.
- Row 12 bookkeeping (ratification 06oct2026): S35 now draws literals outside 0100-9999 on date axes and ticks such axes with its own off-date FixedTicker; the Dependencies list says S44 keeps that ticker and its `_dash_axis_count_ticks` branch and treats a JS null end as hold.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:77 (P1.3) and S01's entry `P1.3b`: "Default %td to %ty date axes keep Bokeh's DatetimeTicker, not twoway's tsnatscale ticks". GAPS2 B25-a for date axes; BUGS.md:2523 (open, WP-27): "#N ticks on a %td to %th date axis follow a fitted model that agrees with twoway's on about 60% of ranges, and three natscale ranges miss by a tick". Measured at `c96facd` (research `.ultraplan/wp30/research/p1-03.md` §2(a), §3; headless Chrome over the saved page):

```
dash  line close date (sp500, %td)   xticks 2001-01-01, -03-01, -05-01, -07-01, -09-01, -11-01, 2002-01-01   (DatetimeTicker)
twoway                              x 01jan2001 01apr2001 01jul2001 01oct2001 01jan2002, cur=[14976,15341]   (P07; tsnatscale #5)
dash's model _dash_tsnatscale_ticks over P07's data, n=5: the quarterly ticks twoway draws
```

S21 (batch 7) gave date axes twoway's hull and margin but left the DatetimeTicker, and holds `%td`-`%ty` `#N` ticks after a move (S21 D-21e: "S44 lifts this"). S35 (batch 12) put dates on mixed axes in Stata units with natscale ticks (`0 5000 10000 15000` where twoway draws 01jan1960 01jan1970 … 01jan2000).

**After this section,** in the saved page and the served app:
- every default `%td`-`%ty` axis, primary or y2/x2, and every mixed axis labelled in such a format, is ticked by the model as `#N` with the scheme's N (5 in all 26 schemes), with no minor ticks;
- after every filter move, the date axes re-tick over the kept rows (served in Python, saved through the JS port), and a zoom re-ticks over the visible range;
- the saved and served pages give identical ticks on every one of the fixture's 12,000 answers, its 15,711 sweep answers and its 280 graphs, and the agreement with twoway is at least the pinned floors;
- BUGS.md:2523 is closed by disposition: the model is the default; its remainder is P2.19; natscale's three end misses stay strict xfails, as they are.

**Why one section.** The date half of P1.3 was split from S21 because it needs the ~350-line calendar port and S35's units (A138); it is one ticker on one finisher chain.

**Test order and commit rule (rule 7, D1).** One entry, one cycle, one commit `(WP-30 P1.3b)`. 44-01 to 44-03 write every regression test and the date-axis fixture and save `$S/44-P1.3b-failure.txt` (no commit); 44-04 to 44-13 fix, flip and document; 44-14 closes both BUGS.md entries, replaces the marker and commits after one full run.

## Risk: [red] — a 350-line calendar port that must equal the Python model, on every dashboard with a date axis

**Why.**
- `_DASH_AXIS_FINISH_JS` is UNKNOWN to the index (a string; `_FILTER_JS` reaches 27 test files) and is S21's; `_dash_refinish_axes` (S21's, served move path) is called, not edited.
- `_dash_axis_count_ticks` is HIGH (research §6); `_dash_count_axes` LOW; `_dash_apply_axis_options` LOW; `_dash_finish_secondary_axes` LOW; `ServerAppBuilder._glyph_layer_lines` HIGH; the `_dash_ts_*` model functions are on the copy list and reached through `_dash_axis_count_ticks`.
- Every saved page with a date axis and a filter carries the port in each filter callback's code.

**Risk factors.**
1. JS and Python disagree on a tie, a rounding or a calendar conversion, so the two modes draw different ticks after a move (RK-2).
2. Python's set iteration order decides ties (D-44b); a port that iterates in another order disagrees silently.
3. The re-finish exceeds A9's budgets on large data or 100 panels.
4. A mixed axis is re-ticked in milliseconds instead of Stata units.
5. Page size grows by the port's bytes per filter callback.

**Mitigation.**
1. Parity tests over all 12,000 + 15,711 + 280 fixture rows and 20,000 seeded ranges per unit (`TestJsTsnatscaleEqualsPython`), plus the calendar converters over every month boundary from 0100 to 9999; the Chrome test reads the drawn ticks after a move in both modes.
2. D-44b's explicit order, proved equal to the base's answers in 44-01 and pinned by `TestTheModelIsUnchanged`.
3. The timed tests of A9 (`TestTheBudgets`) at 500k rows and 100 panels.
4. D-44c's pseudo-kind; a mixed-axis case in every mode and after a move.
5. The port is minified by no tool; its size is measured in 44-12 and recorded in the commit body; S58.7 records page sizes.

## Dependencies

- **Depends on: 21, 35.**
  - S21 (batch 7): `_dash_default_ticker(n)` (a FixedTicker tagged `_DASH_COUNT_TAG + str(n)` and `_DASH_DEFAULT_TAG`), `fig._dash_numticks`, `_dash_count_axes(fig, every_axis=False)` with each entry's `default` and `hold` ("True on a re-finish for a `_DASH_TS_UNITS` kind"), `_dash_place_count_ticks`, `_dash_finish_count_ticks(fig, refinish=False)`, `_dash_common_count_ticks`, `_dash_refinish_axes(figures, facet_map)` (served, called from `_on_filter_change`), `_dash_axis_plan(figures, facet_map, zoom=True)` (per-axis `kind`, `mode`, `n`, `hold`), `_DASH_AXIS_FINISH_JS` (`dash_natscale`, `dash_axis_ticks` — "ts kinds return null" — `dash_axis_extent`, `dash_axis_pad`, `dash_axis_compute`, `dash_axis_finish`) and `_DASH_AXIS_ZOOM_JS` (TR-21.6-TR-21.14). S27 (batch 9) and S35 (batch 12) extended the same chain.
  - S35 (batch 12): Stata-unit date hulls (`_dash_spec_units`, `_DASH_DATE_UNITS_JS` prepended to `_DASH_AXIS_FINISH_JS`), y2/x2 `DatetimeAxis` with `#N` ticks in date units (`_dash_axis_date_kind(fig, "y2")`), `_dash_axis_unit_format(plots, axis, date_vars, formats)` for mixed axes, and a `CustomJSTickFormatter` on every date-labelled axis, so any tick position is labelled in the variable's format.
  - S35 (batch 12, ratification row 12, 06oct2026): a date axis reaching past Stata's dates (outside 0100-9999) is ticked by S35's off-date FixedTicker (`_dash_off_date_ticks`, `_dash_finish_off_date_axes`) through one branch of `_dash_axis_count_ticks` (where `_dash_unix_ms_to_unit` gives None). S44 keeps that ticker and that branch: its model answers only inside 0100-9999, and its JS port treats a null end as hold (no re-tick), never as a date.
  - S18 (read): the date formatters; S01 provides the open entry `P1.3b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.3b -->` in the WP-30 group of `### Results that change`, the S44 stub and the map anchor `# WP-30 S44 (P1.3b): tsnatscale on %td-%ty default axes (P1.3 part b, M1)`.
- **Blocks: 52, 57.** S52 unions `add` with this ticker and survives its re-finish; S57 audits the final served move path, this re-finish included.
- **Parallel batch: 15**, merge order S42, S43, S44; S44 lands last.
- **Can run with:** S42 (dash.ado, Mata, the data take-in, the CSV, the template) and S43 (the colour sites, including S31's `_dash_apply_axis_spec` and `_dash_apply_scale_look`) edit none of S44's functions; S44 edits no colour line and no template line.

## Evidence

Anchors are at `c96facd`, re-verified for this file; S21, S27, S35 and S18 move them and add the finisher chain. The executor re-finds each by symbol at `batch-15-base`.

### E1. The model (dash_render.py)

- `_DASH_TS_UNITS = {"td": "d", "tw": "w", "tm": "m", "tq": "q", "th": "h", "ty": "y"}` (:22199); `_dash_unix_ms_to_unit(ms, unit)` (:22203-22238, epoch ms → the unit's value with the elapsed fraction, None outside 0100-9999; weeks `min(51.999, …)`).
- `_DASH_TS_PARAMS` (:22243-22267: per unit 18 weights and five limits), `_DASH_TS_PER`, `_DASH_TS_SUB`, `_DASH_TS_GRIDS`, `_DASH_TS_YEARS`, `_DASH_TS_LIMITS` (:22268-22283).
- `_dash_ts_ladder` (:22286), `_dash_ts_cost` (:22299), `_dash_ts_candidates` (:22321), `_dash_ts_tiny` (:22357), `_dash_ts_calendar` (:22371), `_dash_ts_yearly` (:22386), `_dash_ts_frac_month` (:22398), `_dash_ts_month_day` (:22414), `_dash_ts_month_week` (:22423), `_dash_ts_week_day` (:22434), `_dash_ts_daily` (:22443), `_dash_tsnatscale_ticks(lo, hi, n, unit)` (:22491-22540), `_dash_axis_count_ticks(lo, hi, n, kind=None)` (:22543-22590).
- The iteration sites of D-44b:

  ```python
  22338         for t0 in ((fl, fl + g) if fl < lo else (fl,)):
  22340             for m in {math.floor(fh), math.ceil(fh)}:
  22347     ks = set(range(2, min(n + 1, 14) + 1)) | set(range(max(2, n - 10),
  22348                                                        n + 2))
  22349     for g in _DASH_TS_GRIDS[unit]:
  22350         for k in ks:
  22352             for mult in {math.floor(base), math.ceil(base)}:
  ...
  22458         for t0 in {math.floor(lo), math.ceil(lo)}:
  22460             for m in {math.floor(fh), math.ceil(fh)}:
  ```

  Ties: `cst < best[0] - 1e-12` (strict, first wins), in `_dash_ts_calendar` and `_dash_ts_daily`. Rounding: `int(round(hi - lo))` (:22360), `int(round(t0 + i * d))` (:22476); output `float("%.12g" % v)` (:22540).
- The CPython order (measured for this file, `python3`, 3.12/3.13 alike):

  ```
  every a in [-100000, 100000): list({a, a+1}) == ([a+1, a] if (a+1) & 7 == 0 else [a, a+1])   -> 0 exceptions
  every a in [-3000000, 3000000) (re-measured in review, python3 3.14): 0 exceptions; 200,000 seeded floats x, {floor(x), ceil(x)}: 0 exceptions
  list({-2,-1}) [-2, -1]   list({-1,0}) [0, -1]   list({7,8}) [8, 7]   list({-9,-8}) [-8, -9]
  ks ascending for n in 1..62; not ascending for n = 63..79, 127..129, …
  ```

  The fixture's `n` runs 2-12 (`tsnatscale`), 3-11 (sweeps), 2-12 (graphs).
- The copy list already carries every model name: constants `"_DASH_TS_UNITS", "_DASH_TS_PARAMS", "_DASH_TS_PER", "_DASH_TS_SUB", "_DASH_TS_GRIDS", "_DASH_TS_YEARS", "_DASH_TS_LIMITS"` (:32996-32998); functions `"_dash_unix_ms_to_unit", "_dash_tsnatscale_ticks", "_dash_axis_count_ticks", "_dash_ts_ladder", …, "_dash_ts_daily"` (:33261-33268).

### E2. The fixture and the floors

`test/fixtures/natscale_axes_truth.json` (WP-27, 24sep2026, StataNow 19.5): `tsnatscale` 12,000 rows `[unit, lo, hi, n, min, max, step, list]` (2,000 per unit), `tsnatscale_sweeps` 15,711, `date_graph` 280. `test/test_natscale_axes.py::TestDateAxisTicks` pins `_TS_FLOOR = {"d": 1042, "w": 1162, "m": 1298, "q": 1194, "h": 1320, "y": 1955}`, `_TS_SWEEP_FLOOR = {"d": 1939, "w": 1466, "m": 5314, "q": 1677, "h": 701}` and 163 of the 240 non-`%tc` graphs (:144-172), plus the model's parts and calendar conversions (:173-198). The fixture's `_meta` predates the D12 stamp; S44 reads it and does not regenerate it.

### E3. Where the date ticker is decided (S21's chain, as S21 TR-21.6/TR-21.8/TR-21.10/TR-21.11 define it)

- `_dash_apply_axis_options` installs `_dash_default_ticker` only when the axis's date kind is None, "tc" or "tC" (TR-21.6); `_dash_finish_secondary_axes` likewise for y2/x2.
- `_dash_count_axes` marks `hold: True on a re-finish for a _DASH_TS_UNITS kind` (TR-21.8); `_dash_finish_count_ticks(refinish=True)` keeps held ticks.
- `_DASH_AXIS_FINISH_JS`' `dash_axis_ticks` returns null for a ts kind (TR-21.11); `_DASH_AXIS_ZOOM_JS` calls it.
- `_dash_axis_plan` writes each axis's `kind` (None/"log"/"tc"/"tC"/a ts kind) (TR-21.10).
- S35 prepended `_DASH_DATE_UNITS_JS` (`dash_date_units(v, kind)`: ms → integer Stata periods) and made y2/x2 date axes and the mixed-axis formatter (TR-35.8-TR-35.10).

### E4. twoway's truth for default date axes

- P07 (research §3): `twoway line close date` on sp500 (`%td`): x 01jan2001 01apr2001 01jul2001 01oct2001 01jan2002, cur=[14976,15341]; `ylabel(#5) xlabel(#5)` equals the default (P01b, C06 = C07): the default is `#5`.
- `date_graph` (E2): every one of 280 graphs is `_tsnatscale`'s answer over its data.
- S35 (section-35 :41): `(scatter close date) (scatter close obs)` → 01jan1960 01jan1970 … 01jan2000, also under `xlabel(#5)`.
- Not yet measured, measured by 44-02's extractor: the default axis of each of `%tw`, `%tm`, `%tq`, `%th`, `%ty`; a y2 date axis; a by() date graph; the `if` subsets matching the tests' moves.

### E5. Tests that pin today's behaviour (written by S21 and S35; flipped, never deleted; re-measured by 44-01)

- S21's `test/test_default_axes.py` cases that assert a `%td`-`%ty` default axis keeps Bokeh's DatetimeTicker (S21 task text: "`%td`-`%ty` axes keep their DatetimeTicker") and the D-21e date hold after a move.
- S35's pytest twin of DA-05 in `test/test_date_axis_residuals.py`, which asserts dash's y2 `#5` rule (section-35 :483, :497). DA-05 itself sits in S35's block of `test/test_wp30_truth.cscript`, which R1 forbids S44 to edit: if it fails on the fixed tree, 44-11 stops and reports for an orchestrator amendment (it passes unchanged if it computes dash's rule live, as section-35 :483 says it asserts "dash's rule").
- `BUGS.md:2523`'s open form; `test/test_natscale.py`'s strict xfails for natscale's three end misses stay as they are.
No test at `c96facd` names `DatetimeTicker` (`grep -rn DatetimeTicker test/*.py` prints nothing).

### E6. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, re-run at 15.0)

| Symbol | Risk | Action |
|---|---|---|
| `_dash_axis_count_ticks` | HIGH | warn; one branch for `"su:"` kinds |
| `_dash_ts_candidates`, `_dash_ts_daily` | (research: reached through the above) | iteration order only |
| `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_count_axes`, `_dash_axis_plan` | LOW / LOW / LOW / (S21's) | the date conditions |
| `_DASH_AXIS_FINISH_JS` | UNKNOWN (constant) | the port prepended; `dash_axis_ticks`' ts branch |
| `ServerAppBuilder._glyph_layer_lines` | HIGH | names appended at S44's anchors |
| `_dash_refinish_axes`, `_generate_app_source`, `_FILTER_JS` | — | not edited |

## User stories

- **US-44.1** As a twoway user plotting a time series, I want `line close date` to tick 01jan2001, 01apr2001, … as twoway does, in the saved page and the served app.
- **US-44.2** As a dashboard reader, I want the date axis to re-tick over the rows a filter keeps, and on zoom, the same way in both modes.
- **US-44.3** As a twoway user, I want `%tw`, `%tm`, `%tq`, `%th` and `%ty` axes, a y2 date axis and a date beside a number to take twoway's calendar ticks.
- **US-44.4** As a maintainer, I want the JS and Python tickers proved equal on every measured answer, so the two modes cannot drift.

## Business requirements

- **BR-44.1** A `%td`, `%tw`, `%tm`, `%tq`, `%th` or `%ty` axis with no label rule (or a sub-option-only rule), primary or second, takes `#N` ticks from the model, N the scheme's `numticks_g` for that direction, over the axis's hull of drawn data, and draws no minor ticks.
- **BR-44.2** An axis that mixes a date layer with a number and is labelled in a `%td`-`%ty` format takes the model's ticks in Stata units, for the default and `#N` alike.
- **BR-44.3** After every filter move, every such axis, and every `#N` date axis, re-ticks over the kept rows; an axis whose kept rows draw nothing keeps its last ticks (S21's rule); a zoom re-ticks over the visible range.
- **BR-44.4** The saved page and the served app give the same ticks at build, after any move and on zoom.
- **BR-44.5** The model's agreement with twoway is at least the pinned floors (E2), and the help states the rates.
- **BR-44.6** A9's budgets hold.

## Technical requirements

- **TR-44.1 Explicit order (D-44b).** New `_dash_ts_pair(x) -> tuple[int, ...]`, directly above `_dash_ts_ladder`: `a, b = math.floor(x), math.ceil(x)`; `(a,)` when equal; else `(b, a)` when `b & 7 == 0`, else `(a, b)`. Docstring: why (CPython's set order decides ties; E1's measurement). `_dash_ts_candidates` and `_dash_ts_daily` iterate `_dash_ts_pair(fh)`, `_dash_ts_pair(base)` and `_dash_ts_pair(lo)` in place of the sets, and `sorted(ks)`. No other line of the model changes.
- **TR-44.2 Default ticker at build.**
  - `_dash_apply_axis_options`: S21's install condition (date kind None, "tc", "tC") gains every key of `_DASH_TS_UNITS`, so a default `%td`-`%ty` primary axis gets `_dash_default_ticker(fig._dash_numticks[letter])`. On an axis with no date kind whose S35 unit format `fb` is a `%td`-`%ty` format, it stamps `fig._dash_unit_kind = {**getattr(fig, "_dash_unit_kind", {}), <axis name>: "su:" + kind}` (kind from `_stata_date_kind(fb)`).
  - `_dash_finish_secondary_axes`: the same two rules for y2/x2 (a date kind through `_dash_axis_date_kind(fig, name)`; a mixed y2/x2 through S35's call there).
- **TR-44.3 The finisher chain (R11; S21's functions).**
  - `_dash_count_axes`: an entry's `kind` is `fig._dash_unit_kind.get(name)` when present, else today's; `hold` is no longer set for a `_DASH_TS_UNITS` kind (it stays for S21's other held cases: `xtick(#N)`, `minmax`, explicit lists).
  - `_dash_axis_count_ticks(lo, hi, n, kind=None)` (HIGH, warn): a kind `"su:<k>"` with `k` in `_DASH_TS_UNITS` returns `_dash_tsnatscale_ticks(lo, hi, n, _DASH_TS_UNITS[k])` (Stata values in, Stata values out); any other string starting `"su:"` is linear. Docstring extended.
  - `_dash_axis_plan`: each axis's `kind` carries the `"su:<k>"` kind and `hold` follows `_dash_count_axes`. Kinds stay from a fixed set (None, "log", "tc", "tC", the six ts kinds, the six `"su:"` kinds), never user text.
  - `_dash_refinish_axes` (served) needs no edit: it calls `_dash_finish_count_ticks(f, refinish=True)`, which now re-ticks date axes.
- **TR-44.4 `_DASH_TSNATSCALE_JS`** (new constant, directly after `_DASH_TS_LIMITS`; pure arithmetic; no DOM, `eval`, `Function`, `Date`-dependent locale or user text; at most 16,000 characters). It defines, each a line-for-line port of its Python twin, in the twin's order of operations:
  - `dash_round_half_even(x)`, `dash_g12(x)` (`Number(x.toPrecision(12))`), `dash_ts_pair(x)` (TR-44.1's rule);
  - `dash_days_from_civil(y, m, d)` and `dash_civil_from_days(z)` (proleptic Gregorian, integer arithmetic, years 0100-9999);
  - `dash_ms_to_ts_unit(ms, unit)` (`_dash_unix_ms_to_unit`, with `__DASH_MS_MIN__`, `__DASH_MS_MAX__`, `__DASH_EPOCH__` tokens);
  - `dash_ts_unit_to_ms(v, kind)` (`_stata_dates_to_datetime` for one value: a fraction floored to the period that holds it for `tw`-`ty`, a `%td` fraction kept as time of day; NaN past 0100-9999, so a tick past 31dec9999 is dropped as Python drops it);
  - `dash_ts_ladder`, `dash_ts_cost`, `dash_ts_candidates`, `dash_ts_tiny`, `dash_ts_calendar`, `dash_ts_yearly` (calling S21's `dash_natscale`), `dash_ts_frac_month`, `dash_ts_month_day`, `dash_ts_month_week`, `dash_ts_week_day`, `dash_ts_daily`, `dash_tsnatscale(lo, hi, n, unit)`;
  - the tokens `__DASH_TS_PARAMS__`, `__DASH_TS_PER__`, `__DASH_TS_SUB__`, `__DASH_TS_GRIDS__`, `__DASH_TS_YEARS__`, `__DASH_TS_LIMITS__`, `__DASH_MAX_AXIS_TICKS__`, `__DASH_YEAR_MIN__`, `__DASH_YEAR_MAX__` replaced at import by `json.dumps` of the Python constants (tuples as arrays), so the weights are never typed twice.
  - Sums run left to right as `sum(a * b for …)` does; candidate loops run in Python's order; `Math.floor`/`Math.ceil` match `math.floor`/`math.ceil` on finite doubles.
- **TR-44.5 `_DASH_AXIS_FINISH_JS`** (S21's constant): `_DASH_TSNATSCALE_JS` is prepended once, after S35's `_DASH_DATE_UNITS_JS`, inside the one statement that assigns `_DASH_AXIS_FINISH_JS` (S21 put it after `_DASH_TICK_EVERY_JS`, :22878 at `c96facd`, below `_DASH_TS_LIMITS`, so the new constant is already defined there). If at `batch-15-base` that assignment sits above `_DASH_TS_LIMITS` (for instance because S21 moved it above `_FILTER_JS`, :18562, to settle its own import order), 44-07 stops and reports: the port's tokens need the model's constants, so the orchestrator decides where the composition moves. Never as a later rebinding (`_DASH_AXIS_FINISH_JS = _DASH_TSNATSCALE_JS + _DASH_AXIS_FINISH_JS` further down): `_FILTER_JS` and the zoom callbacks copy the finisher's text when they are built, so a later rebinding would leave the saved filter callback calling an undefined `dash_tsnatscale`. 44-07 first greps where `_FILTER_JS` takes `_DASH_AXIS_FINISH_JS`'s text at `batch-15-base`, and `TestTheServedCopy` asserts `_FILTER_JS.count("function dash_tsnatscale(") == 1`. `dash_axis_ticks(lo, hi, n, kind)`: a ts kind → `dash_ms_to_ts_unit` both ends, `dash_tsnatscale`, `dash_ts_unit_to_ms` each tick, NaN dropped, null when none; an `"su:<k>"` kind → `dash_tsnatscale` on the values directly. No other function of the constant changes; `_DASH_AXIS_ZOOM_JS` is unchanged and gets the date path through `dash_axis_ticks`.
- **TR-44.6 Both modes, all paths.** Build: `_dash_finish_count_ticks` (saved `_make_figure_body`, served `_dash_figure_for`, both S21's call sites); by(): `_dash_common_count_ticks` passes the kind through; served move: `_dash_refinish_axes`; saved move: `dash_axis_finish` at the end of `_FILTER_JS`; zoom: S21's shared CustomJS. No call site is added.
- **TR-44.7 Copy lists (R2 row S44).** Constants, after `"_DASH_TS_GRIDS", "_DASH_TS_YEARS", "_DASH_TS_LIMITS",` (:32998): `"_DASH_TSNATSCALE_JS",`. Functions, after S27's names at S21's anchor (after `"_dash_finish_auto_bases",`, itself after `"_dash_refinish_axes",`): `"_dash_ts_pair",`. `_DASH_AXIS_FINISH_JS` stays copied by value as S21 listed it.
- **TR-44.8 Maps.** `test/function_test_map.py` under S44's anchor: `'_dash_ts_pair': 'test/test_date_axis_ticks.py::TestTheModelIsUnchanged::test_the_pair_is_cpythons_order'`.
- **TR-44.9 Help** (dash.sthlp "Axis and Display Options", R3, S44's row; the "Axis labels" paragraphs S21 rewrote): one paragraph: default `%td`-`%ty` axes and second date axes are `#5` (the scheme's N) by twoway's calendar rule as dash models it; it agrees with Stata on about 52-66% of daily-to-half-yearly ranges and 98% of yearly ones, otherwise choosing another calendar step or end tick; the axis re-ticks after a filter move and on zoom; a date beside a number is ticked on the date's calendar. Delete S21's sentence that `%td`-`%ty` default axes keep Bokeh's ticks and S35's residual sentence on mixed-axis tick positions (find both by text). Lines at most 79 characters.
- **TR-44.10 Security (rule 1).** The JS is a module constant with no user text; its tokens are replaced by `json.dumps` of numeric constants; the plan carries kinds from a fixed set; nothing is evaluated; every loop is bounded by `_MAX_AXIS_TICKS` and the ladder's length. A test asserts `_DASH_TSNATSCALE_JS` holds no `eval(`, `Function(`, `document` or `window`, and neither it nor `_DASH_AXIS_FINISH_JS` holds a `__DASH_` token after import.

## Boundaries

- **Batch 15 partners.** S42: dash.ado, dash_parse.mata, `_load_data`, `_dash_take_qual_columns`, `_dash_csv_meta`, `_DASH_CSV_JS`, `_dash_load_columns`, `_generate_app_source`. S43: the appliers, mappers and colour readers, `_dash_apply_axis_spec`, `_dash_apply_scale_look`. S44 edits none of them.
- **S21's and S35's functions** are extended only on the date path: no numeric, log or `%tc` behaviour changes (guarded by S21's and S35's tests running green).
- **Not this section's:** refitting the model (P2.19; BUGS.md:2523's remainder); natscale's three end misses (strict xfails in `test/test_natscale.py`, kept); `xlabel(minmax)` across layers (P2.20); `add` (S52); `tlabel()`/`ttick()` (S51); `plotregion(margin())` (S47).
- **Never:** `_generate_app_source`, `_make_figure_body`, `_FILTER_JS` outside `_DASH_AXIS_FINISH_JS`, `build_dropdown`/`build_slider`/`build_range`, `DashRenderer.render`, any BokehJS view internal, `_DASH_TS_PARAMS`' values.

## Stata truth

### `scripts/extract_date_axes_truth.do` → `test/fixtures/date_axes_truth.json`

S02's stanza (TR-02.9), `adopath ++ "`repo'/"`, `global dash_nobrowser 1`; `_meta` in S19's form (`stata_version`, `born_date`, `dash_commit`, `extracted`); the python block never calls Stata, no `shell=True`. Each probe reads `.Graph.xaxis1.major.min/max/delta` (and `yaxis1`, `xaxis2`/`yaxis2` where named), `.Graph.plotregion1.xscale.curmin/curmax`, and the tick label texts from an SVG through `scripts/svg_truth.py`.

- **Data:** `sysuse sp500` (`date` `%td`); from it `gen w = wofd(date)` `%tw`, `gen m = mofd(date)` `%tm`, `gen q = qofd(date)` `%tq`, `gen h = hofd(date)` `%th`; a 40-year yearly series `y` `%ty` (1961-2000) with a value column; `gen g = mod(_n, 2)`; `gen obs = _n`.
- **Probes:** `TD` `line close date`; `TW`, `TM`, `TQ`, `TH` `scatter close <var>`; `TY` `line val y`; `N5` `line close date, xlabel(#5)` (equal to `TD`); `Y2` `(line close date) (line volume date, xaxis(2))`; `MIX` `(scatter close date) (scatter close obs)` and `MIXN` with `xlabel(#5)`; `BY` `line close date, by(g)`; `IF1` `line close date if date <= 15100`, `IF2` `… if close > 1200`, `IF3` `scatter close m if m >= 492 & m <= 497` (the subsets the tests' moves produce).
- **Records:** per probe `cmd`, `rc`, per axis `major` `[min, max, delta]`, `labels` (texts), `cur` `[curmin, curmax]`, and `data_lo`/`data_hi` (the axis's data range in Stata units, from `summarize`).
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_date_axes_truth.do"`; `git add -f test/fixtures/date_axes_truth.json`.

### The S44 block of `test/test_wp30_truth.cscript` (R1)

Helpers `_s44_*` above S01's `* ==== S44 P1.3b: tsnatscale on %td-%ty default axes ====` header (S01 drops only the trailing parenthesis, "(P1.3 part b, M1)"): a `python:` reader of the saved page's and the served document's FixedTicker ticks per axis, converted to Stata units (any Stata helper declares `version 19`). Cases report through `_w30_expect`/`_w30_done`, write only under `` `w30_work' `` and erase their pages and SVGs before the `S44 end` line (TR-01.10 item 4); run alone (`WP30_ONLY=S44`) the block prints its PASS lines and `ALL CHECKS PASSED`.
- **TN-01:** `TD`: dash's saved and served x ticks equal twoway's `major` list.
- **TN-02:** `TW`..`TY`: each equals dash's model over `data_lo`/`data_hi` (n = 5), and twoway's list is printed beside it (agreement is the model's, A8).
- **TN-03:** `MIX`: dash's x ticks in Stata units equal twoway's (01jan1960 … 01jan2000).
- **TN-04:** `Y2`: dash's x2 ticks are the model's over the volume layer's dates.
- **TN-05:** `IF1`: the served document after a move to `date <= 15100` ticks as the model over the kept rows, and twoway's `IF1` list is printed beside it.

No area cscript gains a case: nothing is refused.

## TDD test stubs

### New `test/test_date_axis_ticks.py` (red at the batch-15 base unless marked guard; 44-01, 44-02)

`_T = json.load(test/fixtures/natscale_axes_truth.json)`; `_D = json.load(test/fixtures/date_axes_truth.json)`; `_both(spec)` through `test_mode_parity._render_pair`; `_ticks(fig, axis)` reads a FixedTicker's ticks; moves through `test_saved_filter_layers._move` (node) and `test_served_filter_move._move`.

- Test: `_dash_ts_pair` equals `tuple({math.floor(x), math.ceil(x)})` for 200,000 seeded values in [-700,000, 3,000,000] (the `%td` range of 0100-9999) and for `x` integral — `TestTheModelIsUnchanged::test_the_pair_is_cpythons_order`
- Test: the agreement with Stata over the 12,000, the sweeps and the 240 graphs equals exactly the counts 44-01 measured at the base (constants `_AT_BASE` in the file) — `TestTheModelIsUnchanged::test_the_agreement_is_the_bases`
- Guard: `test/test_natscale_axes.py::TestDateAxisTicks` (the floors) stays green — run, not copied.
- Test (both modes, `_D`): `TD`'s default x axis is a FixedTicker (no minor ticks) holding twoway's five quarterly positions in epoch ms — `TestDefaultDateAxes::test_td[saved|served]`
- Test (both modes): `TW`, `TM`, `TQ`, `TH`, `TY`: the ticks equal `_dash_axis_count_ticks(lo, hi, 5, kind)` over the hull's data — `TestDefaultDateAxes::test_unit[<unit>-saved|served]`
- Test (both modes): `N5` equals `TD` — `::test_default_is_hash5[saved|served]`
- Test (both modes): `Y2`'s x2 axis takes the model — `TestSecondDateAxes::test_x2[saved|served]`
- Test (both modes): `MIX` and `MIXN` tick 0, 3653, 7305, 10958, 14610 (01jan1960 … 01jan2000) in Stata units, labelled by S35's formatter — `TestMixedDateAxes::test_case[<probe>-saved|served]`
- Test (both modes): `BY`: both panels share the model's ticks over the union — `TestByDateAxes::test_common_ticks[saved|served]`
- Test (node, saved; served): after each of `IF1`, `IF2`, `IF3`'s moves the ticks equal the model over the kept rows, and saved equals served — `TestAfterAFilterMove::test_case[<probe>-saved|served]`
- Test (node): a zoom to half the range writes the model's ticks over the visible range; the reset extent writes the data's — `TestZoom::test_date_zoom`
- Test: a move that keeps no row holds the last ticks (S21's rule) on a date axis — `TestAfterAFilterMove::test_empty_holds[saved|served]`
- Test (timed): the served re-finish of a 500k-row `%td` line adds at most 0.2 s per move over the base's measured time; 100 by() `%td` panels settle within 1 s of the base (Chrome, `test_by_scales_chrome.py`'s harness) — `TestTheBudgets::test_served_500k`, `::test_saved_100_panels`
- Test: dash.sthlp states the rates and no longer says date axes keep Bokeh's ticks — `TestTheHelp::test_the_rule_is_documented`
- Test: the generated app defines `_dash_ts_pair` and `_DASH_TSNATSCALE_JS`; `_DASH_AXIS_FINISH_JS` and `_FILTER_JS` each contain `function dash_tsnatscale(` once and no `__DASH_` token; `_DASH_TSNATSCALE_JS` holds no `eval(`, `Function(`, `document` or `window` (S21's and S35's parts of the finisher are theirs to check) — `TestTheServedCopy::test_names_and_constant`
- Guard: a page with no date axis is byte for byte the base's (single-y digest unchanged) — `TestNoDateNoChange::test_unchanged`

### Extended `test/test_natscale_js.py` (S21's node file; 44-01)

- Test: `dash_tsnatscale(lo, hi, n, unit)` equals `_dash_tsnatscale_ticks` on every row of `tsnatscale`, `tsnatscale_sweeps` and `date_graph` — `TestJsTsnatscaleEqualsPython::test_the_fixture[<part>]`
- Test: 20,000 seeded ranges per unit, n 2-62, including ranges at 0100 and 9999 and of one period — `::test_random_ranges[<unit>]`
- Test: `dash_ms_to_ts_unit` and `dash_ts_unit_to_ms` equal `_dash_unix_ms_to_unit` and `_stata_dates_to_datetime` at every month's first day 0100-9999 and 10,000 seeded instants — `::test_the_calendar[<unit>]`
- Test: `dash_round_half_even` and `dash_g12` equal Python's `round` and `"%.12g"` on 10,000 seeded values with exact halves — `::test_the_float_helpers`
- Test: `dash_axis_ticks(lo, hi, 5, kind)` equals `_dash_axis_count_ticks` for the six ts kinds and the six `"su:"` kinds on 2,000 seeded ranges — `::test_the_axis_rule`

### Pinned tests to flip (R9)

E5's list, re-measured by 44-01 into `$S/44-flips.txt` (`python3 -m pytest test/test_default_axes.py test/test_date_axis_residuals.py -q -n 6 -p no:cacheprovider -rA` on the fixed tree, the nodes that fail, compared with the base) and flipped in place with `Flipped: <node> -- <a held or DatetimeTicker answer> was wrong because twoway ticks date axes by tsnatscale over the data (P1.3b, M1)`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Model unchanged, order explicit | `TestTheModelIsUnchanged`; `test_natscale_axes.py::TestDateAxisTicks` | `natscale_axes_truth.json` | n/a |
| JS = Python | node `TestJsTsnatscaleEqualsPython` (every row + 120,000 seeded + calendar) | same | saved JS |
| Default, second, mixed, by() axes | `TestDefaultDateAxes`, `TestSecondDateAxes`, `TestMixedDateAxes`, `TestByDateAxes`; TN-01..TN-04 | `date_axes_truth.json` | yes |
| After moves, zoom | `TestAfterAFilterMove` (node and served), `TestZoom`; TN-05; S21's Chrome test with date cases | fixture | yes |
| Budgets | `TestTheBudgets` | 500k rows, 100 panels | yes |
| Help, served copy, security | `TestTheHelp`, `TestTheServedCopy`, G4 guards | — | n/a |
| Parity | `test_mode_parity.py` one CORPUS case | `_DF` | yes |

**Acceptance criteria.**
- **AC-44.1** (BR-44.1, BR-44.2) `TestDefaultDateAxes`, `TestSecondDateAxes`, `TestMixedDateAxes`, `TestByDateAxes` pass in both modes; TN-01, TN-03 PASS; TN-02, TN-04 PASS on the model's rule.
- **AC-44.2** (BR-44.3, BR-44.4) `TestAfterAFilterMove`, `TestZoom` and S21's Chrome test with the date cases pass, none skipped; TN-05 PASS.
- **AC-44.3** (BR-44.4) every `TestJsTsnatscaleEqualsPython` case passes: 0 differences over 12,000 + 15,711 + 280 rows and the seeded ranges.
- **AC-44.4** (BR-44.5) `TestDateAxisTicks` (floors) and `TestTheModelIsUnchanged` pass; the help states the rates.
- **AC-44.5** (BR-44.6) `TestTheBudgets` passes.
- **AC-44.6** Every flip carries its `Flipped:` line; the full suite through the queue reports 0 failed; G7 prints 0 twice; S21's and S35's own test files pass unchanged except E5's flips.

## Tasks

**Commit boundary.** Tasks 44-01 to 44-14 form the one commit, made by 44-14 on `wp30-s44` with the subject `Tick default date axes with twoway's calendar model in both modes (WP-30 P1.3b)`. `$S` is `<scratch>/s44` (44-01 runs `mkdir -p "$S"`; S42, S43 and S44 run in parallel, so no log or slot directory is shared); `$SLOT` and the driver are as in section 42; `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s44`; the driver runs with `WP30_ONLY=S44`. Each task appends the files it changed to `$S/44-files.txt`.

<task type="auto" id="44-01">
  <name>Measure the base and write parity tests</name>
  <files>test/test_date_axis_ticks.py, test/test_natscale_js.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-15-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s44`; stop otherwise. `mkdir -p "$S"`. Write a scratch script `$S/44-base.py` (PYTHONPATH=$WT; a `--compare <file>` mode recomputes the same answers and prints `identical: <n>` or the first differing range) and record on the unmodified code: the model's agreement counts with Stata over `tsnatscale`, `tsnatscale_sweeps` and `date_graph` per unit, and the model's answers on a 20,000-range seeded sweep per unit (n 2-62) into `$S/44-base-answers.json`. Create `test/test_date_axis_ticks.py` with the `TestTheModelIsUnchanged`, `TestDefaultDateAxes` (TD only, from P07's literal ticks until 44-02), `TestAfterAFilterMove`, `TestZoom`, `TestTheBudgets`, `TestTheHelp`, `TestTheServedCopy` and `TestNoDateNoChange` stubs, `_AT_BASE` holding the measured counts. Add the `TestJsTsnatscaleEqualsPython` stubs to `test/test_natscale_js.py`. Measure the two A9 base times (`$S/44-budget-base.txt`). Run both files with `-n 6 -rf` into `$S/44-new.log`. Write `$S/44-P1.3b-failure.txt`: the base sha, each failing node, then "Guards". Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/44-new.log"` is at least 15; `python3 -c "import json; d=json.load(open('$S/44-base-answers.json')); print(sorted(d))"` lists the six units; `git -C "$WT" diff --name-only -- dash_render.py` prints nothing.]]></verify>
  <done>The base's agreement counts and answers were recorded and the parity, default-axis, move, zoom and budget tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="44-02">
  <name>Extract the date-axis truth</name>
  <files>scripts/extract_date_axes_truth.do, test/test_date_axis_ticks.py</files>
  <action><![CDATA[
    Create `scripts/extract_date_axes_truth.do` exactly as "Stata truth" describes and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_date_axes_truth.do"`; it writes `test/fixtures/date_axes_truth.json`. Add the fixture-driven stubs to `test/test_date_axis_ticks.py` (`TestDefaultDateAxes` per unit and `N5`, `TestSecondDateAxes`, `TestMixedDateAxes`, `TestByDateAxes`, the `IF` cases of `TestAfterAFilterMove`) and a `TestTheFixture::test_it_is_stamped`. Check that `TD`'s major list equals P07's quarterly ticks and `N5` equals `TD`; a difference is reported, never patched. Run the new classes and append their failures to `$S/44-P1.3b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/date_axes_truth.json')); p=d['probes']; print(p['TD']['x']['major'] == p['N5']['x']['major'], all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')))"` prints `True True`; the new classes fail on the unmodified tree.]]></verify>
  <done>twoway's default date axes for every unit, second and mixed axes, by() and the move subsets were in a stamped fixture, and the tests reading it were shown failing.</done>
</task>

<task type="auto" id="44-03">
  <name>Write the truth block and Chrome cases</name>
  <files>test/test_wp30_truth.cscript, test/test_default_axes_chrome.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Put the `_s44_*` helpers directly above S01's `* ==== S44 P1.3b: …` header and TN-01..TN-05 between S01's S44 start and end lines. In S21's `test/test_default_axes_chrome.py` add date cases (`line close date` ticks at build, after a range move and after a zoom, saved and served) to its existing parametrisation, never weakening its DASH_STRICT skip rule. Append `_case("Default date axis ticks (WP-30 P1.3b)", [plot_for("line", {"yvar": "price", "xvar": "when"})])` to `test/test_mode_parity.py`'s CORPUS before its closing bracket (`_DF`'s `when` is its `%td` column, test_mode_parity.py:95; re-check at the base). Run the block through the driver and the Chrome file; append the failures. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "TN-0[1-5] FAIL" "$S/run_test_wp30_truth.log"` is at least 3; `python3 -m pytest test/test_default_axes_chrome.py -q -n0 -p no:cacheprovider -k date` reports failures, not skips, when Chrome is present.]]></verify>
  <done>The live twoway comparisons, the browser cases and the parity case were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="44-04">
  <name>Make the model's iteration order explicit</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-44.1: `_dash_ts_pair` above `_dash_ts_ladder`, with the docstring citing E1's measurement; the four set sites of `_dash_ts_candidates` and `_dash_ts_daily` iterate it; `ks` is iterated as `sorted(ks)`. Change no weight, limit or other line. Then rerun `$S/44-base.py` against the worktree and compare with `$S/44-base-answers.json`: every answer must be identical; any difference stops the task and is reported.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_ticks.py::TestTheModelIsUnchanged test/test_natscale_axes.py -q -n 6 -p no:cacheprovider` reports 0 failed; `python3 "$S/44-base.py" --compare "$S/44-base-answers.json"` prints `identical: 120000`.]]></verify>
  <done>The model iterated in an explicit, portable order and gave exactly the base's answers.</done>
</task>

<task type="auto" id="44-05">
  <name>Install the default ticker on date axes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-44.2 in `_dash_apply_axis_options` and `_dash_finish_secondary_axes`: the install condition extended to every `_DASH_TS_UNITS` kind, and the `fig._dash_unit_kind` stamp for a mixed axis from S35's unit format. Both are LOW; record their callers by `gitnexus impact` in `$S/44-impact.txt` if 15.0 did not. Edit no other line of either (S31's look calls and S35's format lines stay).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_ticks.py -q -n 6 -p no:cacheprovider -k "Default and saved"` passes for `TD` (the build path is complete once 44-06 lands for mixed axes); `python3 -m pytest test/test_default_axes.py test/test_date_axis_residuals.py -q -n 6 -p no:cacheprovider` fails only on E5's pins.]]></verify>
  <done>Default primary and second date axes got the count placeholder at build, and mixed date-labelled axes were marked for the calendar rule.</done>
</task>

<task type="auto" id="44-06">
  <name>Re-tick date axes in Python</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `_dash_axis_count_ticks` is HIGH: warn first. Apply TR-44.3: `_dash_count_axes` reads `fig._dash_unit_kind` and stops holding ts kinds; `_dash_axis_count_ticks` answers `"su:<k>"`; `_dash_axis_plan` writes the kind and hold. Do not edit `_dash_refinish_axes`, `_dash_finish_count_ticks` or `_dash_common_count_ticks` (they pass the kind already); if one of them drops the kind at the base, stop and report.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_ticks.py -q -n 6 -p no:cacheprovider -k "served or Mixed or Second or ByDate"` passes; `python3 -m pytest test/test_default_axes.py test/test_by_scales.py test/test_served_filter_move.py -q -n 6 -p no:cacheprovider` fails only on E5's pins.]]></verify>
  <done>Build-time and served re-finish ticks of every date and mixed date axis came from the model, by() included.</done>
</task>

<task type="auto" id="44-07">
  <name>Port the model to JavaScript</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_DASH_TSNATSCALE_JS` after `_DASH_TS_LIMITS` exactly as TR-44.4 lists, each JS function a line-for-line port of its Python twin with the same loop order (D-44b), `dash_round_half_even` for every `round`, `dash_g12` for `"%.12g"`, integer civil arithmetic for every `datetime`/numpy date, and the tokens replaced at import by `json.dumps`. Prepend it once to `_DASH_AXIS_FINISH_JS` after `_DASH_DATE_UNITS_JS`, inside the statement that assigns `_DASH_AXIS_FINISH_JS` (TR-44.5; record `grep -n "_DASH_AXIS_FINISH_JS\|^_DASH_TS_LIMITS\|^_FILTER_JS" dash_render.py` before and after in `$S/44-sites.txt`, and stop and report if the finisher's assignment is above `_DASH_TS_LIMITS`), and give `dash_axis_ticks` the ts and `"su:"` branches (TR-44.5). Touch no other function of the constant and nothing of `_FILTER_JS` or `_DASH_AXIS_ZOOM_JS`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_natscale_js.py -q -n 6 -p no:cacheprovider` reports 0 failed, 0 skipped; `python3 -c "import dash_render as d; s=d._DASH_AXIS_FINISH_JS; print(s.count('function dash_tsnatscale('), '__DASH_' in s, 'eval(' in s, len(d._DASH_TSNATSCALE_JS) <= 16000)"` prints `1 False False True`; `python3 -c "import dash_render as d; print(d._FILTER_JS.count('function dash_tsnatscale('))"` prints `1`.]]></verify>
  <done>The saved page and both modes' zoom computed date ticks with a JS model equal to the Python model on every measured and seeded range.</done>
</task>

<task type="auto" id="44-08">
  <name>Add copy-list names and the map key</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    `ServerAppBuilder._glyph_layer_lines` is HIGH: warn first. Apply TR-44.7 at S44's two anchors (`"_DASH_TSNATSCALE_JS",` after `"_DASH_TS_GRIDS", "_DASH_TS_YEARS", "_DASH_TS_LIMITS",`; `"_dash_ts_pair",` after S27's `"_dash_finish_auto_bases",`) and TR-44.8's map key under S44's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads test/test_function_test_map.py "test/test_date_axis_ticks.py::TestTheServedCopy" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The served app carried the pair helper and the JS constant, and the helper named its test.</done>
</task>

<task type="auto" id="44-09">
  <name>Prove moves and zoom in both modes</name>
  <files>test/test_date_axis_ticks.py</files>
  <action><![CDATA[
    Complete `TestAfterAFilterMove` and `TestZoom` against the fixed tree (no stub is weakened): the saved page under node through `js_runner`, the served document through `_served_move`, each `IF` probe and the empty move, comparing saved with served and both with the model over the kept rows. Run the Chrome date cases of 44-03.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_ticks.py -q -n 6 -p no:cacheprovider -k "AfterAFilterMove or Zoom"` reports 0 failed, 0 skipped; `python3 -m pytest test/test_default_axes_chrome.py -q -n0 -p no:cacheprovider -k date` reports passed.]]></verify>
  <done>Date axes re-ticked identically in the saved page and the served app after every move and on zoom.</done>
</task>

<task type="auto" id="44-10">
  <name>Check the A9 budgets</name>
  <files>test/test_date_axis_ticks.py</files>
  <action><![CDATA[
    Run `TestTheBudgets` against `$S/44-budget-base.txt`'s base times: the served re-finish of a 500k-row `%td` line must add at most 0.2 s per move; 100 by() `%td` panels must settle within 1 s of the base. If either fails, profile (`python3 -m cProfile`) and make the model's caller cheaper (the hull is read once per axis; the model runs once per axis), never relaxing the bound; record the measurements in `$S/44-budgets.txt` for the commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_date_axis_ticks.py::TestTheBudgets" -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_by_scales_chrome.py::TestTheBrowserDrawsOneScale::test_hundred_panels_settle -q -n0 -s -p no:cacheprovider` passes.]]></verify>
  <done>The date re-finish stayed within the ratified budgets in both modes.</done>
</task>

<task type="auto" id="44-11">
  <name>Flip the pinned date-axis tests</name>
  <files>test/test_default_axes.py, test/test_date_axis_residuals.py</files>
  <action><![CDATA[
    Flip each node of `$S/44-flips.txt` in place, never deleting one: S21's DatetimeTicker and date-hold assertions to the model's ticks; S35's pytest twin of DA-05 to the model's x2/y2 ticks. Append one `Flipped:` line per node to `$S/44-flips-done.txt`. Edit only those cases. Run the truth script with `WP30_ONLY=S35`; if DA-05 fails, do not edit S35's block (R1): stop and report it to the orchestrator.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py test/test_date_axis_residuals.py -q -n 6 -p no:cacheprovider` reports 0 failed; the truth script with `WP30_ONLY=S35` prints `DA-05 PASS`; `wc -l < "$S/44-flips-done.txt"` equals `wc -l < "$S/44-flips.txt"`.]]></verify>
  <done>Every test that pinned Bokeh's date ticker or the date hold asserted the model's ticks, with the reason recorded.</done>
</task>

<task type="auto" id="44-12">
  <name>Document date ticks in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-44.9 in "Axis and Display Options": the date-tick paragraph with the agreement rates; delete S21's sentence that date axes keep Bokeh's ticks and S35's mixed-axis residual sentence, each found by its text. Edit no other paragraph (R3); lines at most 79 characters; no tool or vendor name. Measure the saved page size of `line close date` with one filter before and after (`$S/44-size.txt`) for the commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_date_axis_ticks.py::TestTheHelp" test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "DatetimeTicker" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help described twoway's date ticks as dash models them, with the agreement rates, and no stale sentence.</done>
</task>

<task type="auto" id="44-13">
  <name>Run the section's checks</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_date_axis_ticks.py`, `test_natscale_js.py`, `test_natscale_axes.py`, `test_natscale.py`, `test_default_axes.py`, `test_date_axis_residuals.py`, `test_by_scales.py`, `test_axis_extents.py`, `test_mode_parity.py`, `test_saved_filter_layers.py`, `test_served_filter_move.py`, `test_cscript_hygiene.py` and `test_fixtures_are_committed.py` with `-n 6`, the Chrome files with `-n0`, and the S44 and S35 blocks and S21's block (`WP30_ONLY=S21`) through the driver. Every one must pass with no new skip.
  ]]></action>
  <verify><![CDATA[Each pytest run reports 0 failed; `grep -cE "TN-0[1-5] PASS" "$S/run_test_wp30_truth.log"` prints 5; the S21 and S35 blocks print every case PASS.]]></verify>
  <done>Every test of the date path and of the finisher chain it extends passed on the section's tree.</done>
</task>

<task type="auto" id="44-14">
  <name>Close both entries and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.3b"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution (P1.3b)". Close BUGS.md:2523 ("#N ticks on a %td to %th date axis follow a fitted model …") in place: `- [ ]` becomes `- [x]` and its whole Resolution line is replaced by "Notes: BUGS.md:2523 closure" (TR-01.10 item 1's in-place form; its Title, File Names, Description and Suggested fix stay as written, so the measured rates and the misses remain on record). Delete the `"P1.3b"` key line of `WP30_OPEN`. Replace `<!-- WP-30 P1.3b -->` in place with "Notes: CHANGELOG line". Run `test_tracking_documents.py` and `test_date_axis_ticks.py` with `-n 6`; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/44-full.log"` in the background, read when `exit=` appears. Stage exactly `$S/44-files.txt`, these three and `test/fixtures/date_axes_truth.json` (`git add -f`); G6; G7 before and after; commit.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/44-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.3b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.3b": "' "$WT/test/test_tracking_documents.py"` prints 0; `grep -c '^- \[ \] Title: #N ticks on a %td' "$WT/BUGS.md"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.3b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.3b and BUGS.md:2523 were closed naming existing tests, the marker carried the measured old and new ticks, and one green commit on wp30-s44 was ready to land last in batch 15.</done>
</task>

## Section completion criteria

- Every default and `#N` `%td`-`%ty` axis, second date axis and mixed date-labelled axis is ticked by the model at build, after every saved and served move and on zoom, identically in both modes (fixture probes; TN-01..TN-05).
- The JS port equals the Python model on all 12,000 + 15,711 + 280 fixture rows and 120,000 seeded ranges; the agreement floors and the base's counts hold.
- A9's budgets hold.
- `_dash_ts_pair` and `_DASH_TSNATSCALE_JS` exist, travel to the served app and are mapped; S21's and S35's tests pass except E5's flips.
- The date-axis fixture is generated, stamped, committed with `-f` and read by tests.
- One green commit `(WP-30 P1.3b)` on `wp30-s44` closes the entry and BUGS.md:2523, deletes the key and replaces the marker.

## Notes

- **The port's traps** (each pinned by a parity case): CPython's two-element set order (D-44b), round-half-even, `"%.12g"`, the `1e-12` strict tie, `min(51.999, …)` for weeks, `datetime.date(9999, 12, …)` (`_dash_ts_frac_month`'s `dim = 31` branch), `hash(-1) == -2` (covered by the pair rule), a tick past 31dec9999 dropped not clamped, `_dash_ts_yearly` reusing natscale (S21's `dash_natscale`, unchanged). Do not "simplify" the port; it is a transcription.
- **No refit.** `_DASH_TS_PARAMS`' values are copied, never changed; a better fit is P2.19's.
- **Merge order.** S44 lands last in batch 15 (manifest). On a conflict with S42's or S43's hunks in `dash_render.py` (different functions), the merger keeps both by hand (R2's adjacent-anchor rule) and re-runs the registry tests.
- **python_exec hazard.** As section 42's Notes.
- **Merge rules for the shared files.**
  - R1: the S44 block and helpers only; S35's block (DA-05) is never edited (44-11 stops and reports if it fails).
  - R2: S44's two anchors; the map key under S44's anchor.
  - R3: "Axis and Display Options" (S44's row): the date-tick paragraph and two stale sentences.
  - R4/R5: the `P1.3b` marker, entry and key; BUGS.md:2523 closed in place.
  - R7: one new extractor and fixture; `natscale_axes_truth.json` read, never regenerated.
  - R8: one CORPUS case at most.
  - R9: E5's flips. R10: the single-y digest is unchanged (no date on that page).
  - R11: S44 is batch 15's one finisher editor; A9 kept.
  - R12: S44 edits neither `_make_figure_body` nor `_generate_app_source`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `_dash_ts_pair`, `_dash_ts_candidates`, `_dash_ts_daily`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_count_axes`, `_dash_axis_count_ticks`, `_dash_axis_plan`, `_glyph_layer_lines` and the two constants, plus test symbols.
- **Commit message.** Subject as in "Commit boundary". Body: the failure file; the measured defect (Overview's block); what changed and where (TR-44.1-TR-44.9, both modes); the base-answer identity (`identical: 120000`), the parity counts, the budget measurements (`$S/44-budgets.txt`) and the page-size delta (`$S/44-size.txt`); one `Regression: test/test_date_axis_ticks.py::<Class>::<test> -- failed at <base sha> with <text>` per node, `test/test_natscale_js.py::TestJsTsnatscaleEqualsPython::<test>` likewise, `test/test_wp30_truth.cscript TN-01` style; the `Flipped:` lines; `Fixture: test/fixtures/date_axes_truth.json (scripts/extract_date_axes_truth.do)`; `BUGS.md: "Default %td to %ty date axes keep Bokeh's DatetimeTicker, not twoway's tsnatscale ticks" (closed)` and `BUGS.md: "#N ticks on a %td to %th date axis follow a fitted model that agrees with twoway's on about 60% of ranges, and three natscale ranges miss by a tick" (closed by disposition)`.
- **BUGS.md Resolution (P1.3b)** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.3b). Default %td, %tw, %tm, %tq, %th and %ty axes, second date axes and axes that place a date beside a number in Stata units are ticked as #N (the scheme's N) by the fitted tsnatscale model, at build and after every filter move in both modes and on zoom: the default placeholder is installed on date axes (_dash_apply_axis_options, _dash_finish_secondary_axes), the date hold after a move is lifted (_dash_count_axes), mixed axes tick in Stata units (_dash_axis_count_ticks' su: kinds), the model iterates in an explicit order (_dash_ts_pair) and the saved re-finish and zoom run a JavaScript port of it (_DASH_TSNATSCALE_JS inside _DASH_AXIS_FINISH_JS) equal to the Python model on all 12,000 fixture answers, the 15,711 sweep answers, the 280 graphs and 120,000 seeded ranges. The model agrees with twoway on 52-66% of %td-%th ranges and 98% of %ty (floors pinned). Pinned by test/test_date_axis_ticks.py::TestDefaultDateAxes::test_td, ::TestMixedDateAxes::test_case, ::TestAfterAFilterMove::test_case, ::TestTheModelIsUnchanged::test_the_agreement_is_the_bases, test/test_natscale_js.py::TestJsTsnatscaleEqualsPython::test_the_fixture, test/test_wp30_truth.cscript TN-01..TN-05; fixture test/fixtures/date_axes_truth.json. Residual, deferred (WP-30): the model's remaining disagreements with twoway's calendar step and end ticks (P2.19).
  ```
- **BUGS.md:2523 closure** (its Resolution line replaced in place; the old line said "Not fixed: it stays open because …", which a closed entry must not keep. The `(WP-30, P1.3b)` token is left to the P1.3b entry alone, so S01's closure readers see one entry per id; "WP-30 section 44 (entry P1.3b)" names the closer in words. This answers the orchestrator's S44 item on this wording):

  ```
  - Resolution: Closed <ddmonyyyy> by disposition, by WP-30 section 44 (entry P1.3b). The fitted model is adopted as the default for every %td-%ty axis under the maintainer's decision to match Stata (M1; ratification item 2, A8), not refitted: its agreement floors stay pinned by test/test_natscale_axes.py::TestDateAxisTicks, and the saved page computes the same ticks through a JavaScript port (test/test_natscale_js.py::TestJsTsnatscaleEqualsPython::test_the_fixture). Recovering _tsnatscale's exact calendar-step rule is tracked as P2.19; natscale's three end misses stay strict xfails in test/test_natscale.py.
  ```
- **CHANGELOG line** (replaces `<!-- WP-30 P1.3b -->` in place):

  ```
  - Default date axes take twoway's calendar ticks: `dash line close date` on sp500 drew Bokeh's monthly ticks (2001-01-01, 2001-03-01, … 2002-01-01) and now draws twoway's 01jan2001 01apr2001 01jul2001 01oct2001 01jan2002; every %td-%ty axis, second date axis and date-beside-number axis is #5 by dash's model of twoway's calendar rule (it agrees with Stata on 52-66% of daily to half-yearly ranges and 98% of yearly ones) and re-ticks after a filter move and on zoom in both modes. (WP-30, P1.3b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B25** (:635): B25 is carried by P1.2a (S15), P1.3a (S21) and P1.3b (S44); with this commit it is Closed: `- **Tracked:** Closed in WP-30, BUGS.md "<P1.3b title>", commit <S44 sha>`, naming S21's commit for B25-a on numeric, log and %tc axes and B25-b (section-21 :1060).
  - **DROPIN-REMAINING.md:77** (P1.3): "Closed by <S21 sha>, <S44 sha> (WP-30 S21, S44)."
  - **P2.19** keeps the calendar-step refit and gains this commit as its baseline.
  - **AGENTS.md invariant:** "date ticks come only from `_dash_tsnatscale_ticks` (Python) and its line-for-line port `dash_tsnatscale` (JS); a change to either changes both, proved by `TestJsTsnatscaleEqualsPython`."
  - **Unverified:** Stata 14-18.5 (M2); Windows and Linux (M4); browsers other than Chrome for the zoom path.
