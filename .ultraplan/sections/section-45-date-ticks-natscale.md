# Section 45: Date #N ticks and natscale from Stata itself

> Part of: WP-31 · GAPS3 rows: D15 · Risk: red · Batch: 15 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U45

## Overview

**What is wrong today.** GAPS3 D15 (GAPS3.md:165): "Date `#N` ticks on %td-%th agree with `_tsnatscale` on 52-98% of ranges; three natscale misses on auto (strict xfails); `xtick(#N)`/`xlabel(minmax)` held after a move; margin a build-time fraction." Evidence test/test_date_axis_ticks.py:62 (`_AGREES`: "the model agrees with _tsnatscale on 52-98% of ranges"), test/test_natscale.py:64-78 (`_KNOWN = {("auto","price",4), ("auto","trunk",2), ("auto","trunk",3)}`, strict xfails), test/test_by_scales.py:426 (`style(rescale) noyrescale` x count, strict xfail). Task: "Fit more measured ranges or embed Stata's ticks at build time; re-place after a move." Register P2.19, P2.65.

At `6370ca4` a default axis carries `_dash_default_ticker(count)` (dash_render.py:29091-29106), a `FixedTicker` tagged `dash_count:N` filled at build and after every move by `_dash_place_count_ticks(e, lo, hi, common=False)` (:32940; it takes an axis ENTRY `e` from `_dash_count_axes` (:32852), and the per-axis loop that calls it is in `_dash_finish_count_ticks` (:33346, the call at :33403) -- REVIEW-3e F16) with `_dash_axis_count_ticks(lo, hi, n, kind)` (:30154), which is `_dash_natscale_ticks` (:28994-29090, "natscale is compiled ... fitted to test/fixtures/natscale_truth.json ... Where natscale's 32-bit step count overflows") for a number and `_dash_tsnatscale_ticks(lo, hi, n, unit)` (:30095-30153, "a model fitted to 12,000 of its answers ... Exact agreement with Stata over 2,000 random ranges each: %td 58%, %tw 58%, %tm 65%, %tq 60%, %th 66%, %ty 98%") for a date kind of `_DASH_TS_UNITS` (:29359-29363). The saved page ports both models (`_DASH_TSNATSCALE_JS`, :29447ff; `dash_natscale` :29650, `dash_tsnatscale` :29763) inside `_DASH_AXIS_FINISH_JS` (:30933), whose placer is the code inside the `dash_axis_finish` IIFE (:31430-31444; there is no JS function named `dash_place_count_ticks` -- REVIEW-3e F16), appended to `_FILTER_JS` by the module statement at :31459; the served app re-finishes through `_dash_refinish_axes` (:32271-32301). The models are guesses at compiled code; Stata itself offers the two routines to any program: `_natscale min max n` (`B/_/_natscale.sthlp`: r(min) r(max) r(delta)) and `_tsnatscale min max n, unit(d|w|m|q|h|y)` (`B/_/_tsnatscale.sthlp`: r(n), r(min), r(max), r(delta) or r(ticks) -- "`r(ticks)` is necessary when tick values are measured in days, but ticked on monthly boundaries").

**After this section**, both modes: at build, every default `#N` axis (number or date, primary and secondary, by() panels, mixed date-beside-number) takes the ticks Stata's own `_natscale`/`_tsnatscale` return over that axis's data range, computed by dash.ado at registration and embedded in the spec (D-45a) -- so the three auto misses and every date range agree with twoway exactly, with no model involved; after a filter move the saved page and the served app re-place the ticks with the models as today (the model is the move-time fallback; its agreement rate is documented), unless the kept rows' range equals a range the spec carries (then the embedded ticks are reused -- the full-data range always is, so a move back to "all" restores twoway's ticks); `xtick(#N)` and `xlabel(minmax)` are re-placed after a move like `#N` (D-45c); the plot margin is re-expressed as Stata's absolute margin on resize by the finish JS (D-45d) or documented with the measured bound. The three strict xfails in test_natscale.py are retargeted (D-45b): they keep pinning the model (still wrong on those ranges) but the drawn axes at build are pinned equal to twoway by new tests; test_by_scales.py:426 stays xfail (`style(rescale) noyrescale`'s count is not S45's -- S36 by-remainder owns by() grammar; S45 leaves a note).

**Why one section.** D15 is one row; it is batch 15's owner of `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS` (R11) and the only editor of the tick model files.

**Test order and commit rule.** One cycle, one commit `(WP-31 D15)`: 45-01 measures and writes red tests; 45-02 embeds Stata's ticks (dash.ado + renderer); 45-03 re-places `xtick(#N)`/`minmax` after a move, handles the margin, documents, closes, commits.

### Section decisions (binding on the executor)

- **D-45a. Stata's ticks are computed at registration by dash.ado and embedded per axis.** `_dash_plot` already knows each graph's x and y variables, their formats and the by() variable; a new program `_dash_axis_ticks_stata` (version 19) runs, per graph and per axis (x, y, x2, y2) whose label option is absent or a bare `#N`, `quietly summarize <var> if __dashq<k>, meanonly` for the axis's variables -- the segment's selection is the byte marker column `__dashq<k>` that `_dash_qual_gen` (dash.ado:6345) already materialises for segment k (and `_dash_qual_gen_by`'s per-panel variant, :6420, for a by() panel), so the qualifier TEXT is never re-substituted into a command line (DECISIONS A25, REVIEW-3e F15; `_dash_if_check` does not exist -- the qualifier programs are `_dash_qual_mark` :4680, `_dash_qual_gen` :6345, `_dash_qual_gen_by` :6420) -- the union over the graph's layers on that axis; per by() panel when the panel rescales, then `_natscale r(min) r(max) N` for a numeric or `%tc`/`%tC` variable and `_tsnatscale r(min) r(max) N, unit(<u>)` for `%td`-`%ty` (`u` from `_DASH_TS_UNITS`'s table: d w m q h y), and writes `graph_options["_stata_ticks"] = {"x": {"range": [lo, hi], "ticks": [...], "n": N}, "y": ..., "panels": {"<key>": {...}}}` -- the tick list is `r(ticks)` when present else `r(min) + k*r(delta)` for k in 0..r(n)-1 (the sthlp's rule). The key is the DRAWN axis word: under `horizontal` the layer's y variable is drawn on x, so its entry is written under `x` (and x's under `y`), exactly as the renderer swaps them (`_dash_is_horizontal`); `yaxis(2)` and axes 3-9 write `y2`, `y3` ... (S09's words) -- REVIEW-3e F17, A25. N is 5 unless the axis has `#N` (the scheme's `numticks_g *_major 5`; dash reads the count the same way `_dash_count_of` does). The renderer, when placing a count ticker (`_dash_place_count_ticks`), uses the embedded list if the axis's current data range (lo, hi over the drawn layers) equals the embedded `range` within 1e-9 relative; otherwise the model. The spec key is private (`_stata_ticks`); a spec without it (an older dash.ado, tests built from Python specs) behaves as today.
- **D-45b. The model stays as the move-time fallback and its three xfails stay honest.** `_dash_natscale_ticks`'s three `_KNOWN` cases are not fixable blind; test_natscale.py's xfail reasons become "natscale case the model does not reproduce; at build the drawn axis is Stata's own (WP-31 D15, test_stata_ticks.py)". A new test pins that the DRAWN axis for `auto price #4`, `trunk #2`, `trunk #3` equals the fixture's twoway ticks at build in both modes (red at base). The index's "flips incl. test_natscale.py:76 if S45 resolves it" is thus: not flipped; reason recorded. The maintainer may ratify a later section to extend the fitted model.
- **D-45c. `xtick(#N)` and `xlabel(minmax)` re-place after a move.** `_dash_place_count_ticks` (:32940, over the entries `_dash_count_axes` :32852 builds) and its JS twin (the placer inside the `dash_axis_finish` IIFE, :31430-31444) today read tickers tagged `dash_count:N`; `xtick(#N)`'s `CustomJSTicker` (:30910 region) and `minmax`'s two-tick FixedTicker (`_dash_axis_pieces`' head rule, dash.ado:3786-3800; the renderer's placement in `_dash_apply_axis_options` :31601 region -- REVIEW-3e F16) are tagged `dash_count_tick:N` and `dash_minmax` respectively, and the Python/JS placers handle the two new tags: `dash_count_tick:N` -> the count ticks with labels off (the ticker's own labels are empty: `major_label_overrides` to `""`? no -- xtick() ticks carry no labels because the axis's formatter is the label axis's; the existing xtick machinery already draws unlabelled ticks on a second ticker: keep its model, only re-place its `ticks`), `dash_minmax` -> `[lo, hi]` of the kept rows. twoway re-places both under `if` (P2.65: "twoway re-places under `if`").
- **D-45d. The margin.** P2.65: "the margin a build-time fraction, up to ~0.8% of the width off on resize (ratified A6)". Stata's plot margin is a `gsize` (absolute, scaled to the graph's smaller dimension); dash sets `DataRange1d.range_padding` as a fraction at build. The finish JS already runs on frame resize for the count placers? U45-03 measures: a saved page resized from 600 to 1200 px wide -- the padding in data units at both widths against Stata's `gsize` rule (`_dash_margin_sides`, :29107). If the fix is one line in the finish JS (recompute `range_padding` from `fig.inner_width`/`inner_height` and the stamped margin gsize), it is made; if it needs a new resize hook, the 0.8% bound is documented in the help with the measured example (M17) and left as the already-ratified A6 residual.
- **D-45e. One JS editor.** S45 edits `_DASH_AXIS_FINISH_JS` only (the literal at :30933 and its appended placer code), never `_FILTER_JS`'s own text (S46 is batch 15's `_FILTER_JS` editor for the recast branches, per index owner table "lpoly/function/stale-kind edges: 46"; R12). The module statement at :31459-31462 is unchanged.

## Risk: [red] -- dash.ado runs two Stata routines per axis at registration; the renderer's tick placer gains a second source of truth; the finish JS changes

**Why.** Registration time grows (two `summarize` + `_tsnatscale` per axis per panel); a wrong range comparison would draw Stata's ticks on a filtered axis; the JS placer runs on every move and resize.

**Risk factors.** 1. `summarize` over a `%tc` variable with 10^6 rows per axis per panel: measured cost. 2. The data range the renderer computes (over drawn layers, after `if`/`in`, per panel) must equal dash.ado's (same qualifier, same layers) or the embedded ticks are never used -- the comparison must use the same definition -- both sides select rows by the same `__dashq<k>` marker (A25); computed layers (lfit grid, histogram edges) extend the axis range beyond the data in dash's current placer (`_dash_axis_extents`?) -- `_dash_place_count_ticks` uses the drawn layers' extents (:14042 "natscale #5 over the plotted values"); dash.ado must mirror: for a computed-only layer the x range is the data's x; a histogram's edges are the bin edges (dash.ado knows `bin()`/`width()`? -- when the graph holds a histogram or kdensity layer, the embedded ticks are NOT written for that axis (fallback to the model), documented). 3. `_tsnatscale`'s `r(ticks)` vs `r(delta)` forms; `%tw` units of weeks. 4. Secondary axes (S35, batch 12) and axes 3-9 (S09): the embedded key per axis name must match `_dash_axis_number`'s words. 5. Resize hook (D-45d) in the saved page.

**Mitigation.** 1. U45-02 times registration on 1,000,000 rows (bound: under 1 s added, else the embedding is limited to axes whose variables have under 10^6 rows, documented). 2. `_stata_ticks` carries the `range`; the renderer compares; `TestTheRangeRule` pins equality for scatter/line and the fallback for histogram. 3. Both forms covered by the fixture's `%tm` and `%td` probes (`r(ticks)` appears for %td ticked monthly). 4. `TestSecondaryAxes` and `TestAxes3to9` (if S09 landed) use the axis words. 5. D-45d's branch.

## Dependencies

- **Depends on: 01.** S09 (axes 3-9, batch 3), S24 (minor ticks, batch 8), S33 (axis sub-options, batch 11), S35 (second-axis moves, batch 12) have landed: S45 is the fourth editor of `_dash_refinish_axes`/`_DASH_AXIS_FINISH_JS` (R11) and must re-read them at the batch-15 base.
- **Blocks: none.**
- **Parallel batch: 15**, merge order S44, S45, S46. **Can run with S44 and S46**: S44 edits `SchemeParser` only; S46 edits lpoly, function points, recast tagging, `_dash_stale_kind` and `_FILTER_JS`'s histogram/kdensity branches. dash.ado: S45 adds `_dash_axis_ticks_stata` and one call in `_dash_plot`'s graph-JSON block (:7335-7415 region, beside `graph_options`); S46 edits `_dash_fn_points` (:8280) and its call (:7052); disjoint lines, both in `_dash_plot` -- merge order S45 before S46 with `patch -p1`.

## Evidence

### The placers

```python
29091 def _dash_default_ticker(count):
29092     """The placeholder a DEFAULT axis carries (WP-30 P1.3a): a FixedTicker
29093     with no ticks and no minor ticks, tagged as a ``#count`` placeholder
29094     (:func:`_dash_count_of` reads it) and as a default.  Its ticks are
29095     written in place by :func:`_dash_place_count_ticks` -- twoway's
29096     natscale ticks over every drawn layer -- at build and after every
29097     filter move.
28977 _DASH_COUNT_TAG = "dash_count:"
28981 _DASH_DEFAULT_TAG = "dash_default"
29348 def _dash_count_of(ticker):
30154 def _dash_axis_count_ticks(lo, hi, n, kind=None):
30095 def _dash_tsnatscale_ticks(lo, hi, n, unit):
28994 def _dash_natscale_ticks(lo, hi, n):
32271 def _dash_refinish_axes(figures, facet_map):
30933 _DASH_AXIS_FINISH_JS = _DASH_DATE_UNITS_JS + _DASH_TSNATSCALE_JS + r"""
31459 _FILTER_JS = (_FILTER_JS + _DASH_AXIS_FINISH_JS
```
`_DASH_TS_UNITS = {"td": "d", "tw": "w", "tm": "m", "tq": "q", "th": "h", "ty": "y"}` (:29362-29363); `_DASH_TS_PARAMS` (:29401ff) the fitted weights; `_MAX_AXIS_TICKS = 2000` (:28962). `xtick()`: :31468-31484 ("ticks WITHOUT labels, beside whatever labels the axis has ... #N"); the CustomJSTicker code at :30910; `xlabel()/xtick()` applier at :31606; `minmax` head rule dash.ado:3786-3800 (`_dash_axis_expand`).

### The tests and fixtures

test/test_date_axis_ticks.py (module docstring :1-14; `_BUILD` :41-56; `_AGREES` :59-61; `TestDefaultDateAxes` :74; `TestTheRangeOption` :91) over `test/fixtures/date_axes_truth.json` from scripts/extract_date_axes_truth.do (`_dt_axis`, :90-105: reads `.Graph.xaxis1.major.dlg_tickpos[i]`, `.major.min/.max/.delta`, the scale's `curmin/curmax`). test/test_natscale.py (`_KNOWN` :64, `_drawn_cases` xfail marks :72-78, `TestTheRuleAgainstStata` :81) over `test/fixtures/natscale_truth.json` (264 axes) and `natscale_axes_truth.json` (the 12,000 random ranges). test/test_natscale_js.py proves the JS port equals the Python model. test/test_by_scales.py:420-432 (`e01` xfail).

### Stata's routines

`B/_/_natscale.sthlp`: `_natscale min max n` -> `r(min)`, `r(max)`, `r(delta)` ("nice" values, approximately n steps). `B/_/_tsnatscale.sthlp`: `_tsnatscale min max n, unit(d|w|m|q|h|y)` -> `r(n)`, `r(min)`, `r(max)`, `r(delta)` or `r(ticks)` ("you will either be presented with r(delta) ... or with r(ticks), which is a list of tick values ... when tick values are measured in days, but ticked on monthly boundaries"). The graph's own record equals `_natscale min max N` in all 264 axes measured (dash_render.py:29001-29003) and `_tsnatscale` in all 280 date graphs (:30102-30103) -- so the embedded values ARE the drawn ticks.

### Tests pinning today's behaviour

test_date_axis_ticks.py::TestDefaultDateAxes nodes for probes outside `_AGREES` (TH, IF2 ...: "dash draws the model's ticks and the test prints twoway's beside them") -- after S45 the build equals twoway for every probe, so those nodes' expectations flip to equality (red at base after the flip); test_default_axes.py nodes pinning the model's ticks at build for a Stata-built spec (if any use a fixture spec with data ranges where the model misses); test_natscale.py xfails: reasons retargeted, not flipped (D-45b).

## User stories

- US-45.1 As a Stata user, I want my date axis ticked exactly where twoway ticks it, every time, not 58% of the time.
- US-45.2 As a user who filters, I want `xtick(#5)` and `xlabel(minmax)` to follow the kept rows as `#5` does.
- US-45.3 As a user of `auto`, I want `price` and `trunk` axes to match twoway's.
- US-45.4 As a maintainer, I want the model's role (move-time fallback) and its agreement rate written down.

## Business requirements

- BR-45.1 At build, every default or `#N` axis of a Stata-registered graph carries the ticks Stata's `_natscale`/`_tsnatscale` give over that axis's data range, both modes, including by() panels, secondary axes and date-beside-number axes; computed-only axes are documented exceptions.
- BR-45.2 After a move the ticks are re-placed (model), and a move back to the full range restores the embedded ticks.
- BR-45.3 `xtick(#N)` and `xlabel(minmax)` re-place after a move in both modes.
- BR-45.4 The margin follows D-45d's branch; the bound is documented when not fixed.
- BR-45.5 Registration time grows under 1 s on 10^6 rows (or the embedding is bounded and documented).
- BR-45.6 Specs without `_stata_ticks` render as today.

## Technical requirements

- TR-45.1 dash.ado: `program define _dash_axis_ticks_stata, rclass` (version 19): args graph index, axis word (the DRAWN word: x/y swapped under `horizontal`, `y2`.. for the secondary axes), varlist, the segment's marker column name (`__dashq<k>`, or the by()-ordered panel marker; read by value through `_dash_text_args`; NO qualifier text -- A25), format kind, N; runs `quietly summarize <v> if <marker>, meanonly` over the union (min of mins, max of maxs), then `_natscale`/`_tsnatscale` (`capture`; on rc or missing r() the axis is skipped), returns `r(json)` = `{"range":[lo,hi],"ticks":[...],"n":N}` written through `_dash_json_number17`-style numbers (Mata `_dash_axis_ticks_json(lo, hi, ticks)` for exact doubles; header index, `_needed` alphabetical, program_coverage_map.py). Called from `_dash_plot`'s graph-JSON block, after `_dash_qual_gen` has written the markers, for each axis whose label option is absent or `#N` (read with `_dash_axis_pieces`' head rule) and not for a graph holding a histogram or kdensity layer on that axis; per by() panel when `rescale`/`xrescale`/`yrescale` applies (S36's grammar: the panel key is the by value as `_dash_by_groups` keys it; the per-panel marker is `_dash_qual_gen_by`'s). Writes `graph_options["_stata_ticks"]` under the drawn axis words (REVIEW-3e F17).
- TR-45.2 dash_render.py: `_dash_count_axes(fig, ...)` (:32852) stamps each axis entry `e` with `e["stata"] = fig._dash_stata_ticks.get(<the entry's drawn axis word>)` (the per-figure dict stamped by `_make_figure_body`/the served `_dash_figure_for` from `graph_options["_stata_ticks"]`, both modes; the panel's entry for a by() figure); `_dash_place_count_ticks(e, lo, hi, common=False)` (:32940), before calling `_dash_axis_count_ticks`, reads `e.get("stata")`; if present and `abs(lo - r[0]) <= 1e-9 * max(1, abs(r[0]))` and the same for hi, `ticks = r["ticks"]` (converted to axis units: epoch ms for a date axis through `_dash_units_to_axis(values, kind)`); else the model (REVIEW-3e F16: the placer takes an entry, not the figure). JS twin: the same comparison inside the `dash_axis_finish` IIFE's placer (:31430-31444) against the plan entry's `stata` field (`_dash_axis_plan` copies `e["stata"]` into the axis entry; numbers only, bounded 64 KB per figure, else omitted).
- TR-45.3 (D-45c) tags `dash_count_tick:N` on the xtick(#N) ticker and `dash_minmax` on the minmax FixedTicker where they are built (:31468ff, and `_dash_apply_axis_options` :31601ff); `_dash_count_axes` (:32852) enumerates tickers with the two new tags as entries beside `dash_count:N`, `_dash_place_count_ticks` (:32940) and the IIFE placer handle the three tags; `_dash_refinish_axes` (served) already calls `_dash_finish_count_ticks(f, refinish=True)` (:33346, the loop at :33403) -- extend that loop to the two new tags.
- TR-45.4 (D-45d) per branch: one line in the finish JS recomputing `range_padding` from the stamped margin gsize and `inner_width`, hooked on `fig.inner_width` change (`fig.js_on_change("inner_width", CustomJS(...))` built in `_make_figure_body`'s finish step through the nonce path -- CustomJS is a Bokeh model, allowed), or the help sentence.
- TR-45.5 Both renderers: `_dash_place_count_ticks`, `_dash_finish_count_ticks`, `_dash_axis_count_ticks` are already in the functions tuple (confirm by grep); any new helper (`_dash_stata_ticks_for(fig, word)`) goes after `"_dash_reference_lines",` (R2). `_DASH_AXIS_FINISH_JS` is shared by construction. function_test_map.py entries for new functions; program_coverage_map.py for `_dash_axis_ticks_stata` and the Mata helper (`test_wp31_truth.cscript:U45-02`).
- TR-45.6 Tests and docs: test_natscale.py xfail reasons retargeted (D-45b); test_date_axis_ticks.py `_AGREES` becomes every probe at build (the model's set kept for the move tests under a new name `_MODEL_AGREES`); help: the axis paragraph ("default ticks are Stata's own at build; after a filter move the saved page and served app place twoway's rule by a fitted model that agrees with Stata on 58-98% of ranges (measured)"), the `xtick()`/`minmax` sentence, the margin sentence per D-45d. TWOWAY_COVERAGE_AUDIT.md's axis row gains `[WP-31 D15: corrected -- build ticks are Stata's]`.


### Reference TR-45.A: `_dash_axis_ticks_stata` (TR-45.1)

```
// ================================================================
// _dash_axis_ticks_stata -- the ticks Stata's own _natscale/_tsnatscale
//                            give over an axis's data range (WP-31 D15)
// ================================================================
// Called by _dash_plot per graph and axis whose label option is absent or
// a bare #N, after _dash_qual_gen has written the segment's marker column.
// Reads by value (_dash_text_args): the axis variables, the marker column
// name (__dashq<k>, or the by() panel's marker; never qualifier text --
// WP-31 DECISIONS A25), the date kind ("" for a number or %tc/%tC; d w m
// q h y for %td-%ty) and N.  Returns r(json) =
// {"range":[lo,hi],"ticks":[...],"n":N} through _dash_axis_ticks_json, or
// an empty r(json) when summarize finds no finite value or the routine
// fails (the renderer then uses its model).  r(ticks) is taken when
// present, else r(min) + k*r(delta), k = 0..r(n)-1 (_tsnatscale.sthlp).
program define _dash_axis_ticks_stata, rclass
    version 19
    mata: _dash_text_args(4, 0, 0)
    local vars  : copy local _dash_a1
    local mark  : copy local _dash_a2
    local kind  : copy local _dash_a3
    local n     : copy local _dash_a4
    confirm variable `mark'
    local lo .
    local hi .
    foreach v of local vars {
        capture quietly summarize `v' if `mark', meanonly
        if _rc | r(N) == 0 continue
        if `lo' >= . | r(min) < `lo' local lo = r(min)
        if `hi' >= . | r(max) > `hi' local hi = r(max)
    }
    if `lo' >= . | `hi' >= . {
        return local json ""
        exit
    }
    if "`kind'" == "" capture _natscale `lo' `hi' `n'
    else              capture _tsnatscale `lo' `hi' `n', unit(`kind')
    if _rc {
        return local json ""
        exit
    }
    if "`r(ticks)'" != "" local ticks `r(ticks)'
    else {
        local ticks ""
        local kmax = cond("`r(n)'" != "", r(n), floor((r(max) - r(min)) / r(delta) + 0.5) + 1)
        forvalues k = 0/`=`kmax' - 1' {
            local ticks `ticks' `=r(min) + `k' * r(delta)'
        }
    }
    mata: st_local("json", _dash_axis_ticks_json(`lo', `hi', "`ticks'", `n'))
    return local json `"`json'"'
end
```
`_dash_axis_ticks_json(lo, hi, ticks, n)` (Mata, after `_dash_fn_points_json` in the header index) writes each number with the `%24.17g` rule `_dash_json_number17` uses. The `_natscale` call's own `r(n)`: `_natscale` returns min/max/delta only, so the delta branch counts; `_tsnatscale` returns `r(n)` and either form.

### Reference TR-45.B: the spec key and the placer (TR-45.2)

Spec: `"graph_options": {..., "_stata_ticks": {"x": {"range": [1760, 4840], "ticks": [2000, 3000, 4000, 5000], "n": 5}, "y": {...}, "x2": {...}, "panels": {"0": {"x": {...}}, "1": {...}}}}` (keys are the DRAWN axis words: under `horizontal` the y variable's ticks sit under `x`). Python placer, at the top of `_dash_place_count_ticks(e, lo, hi, common=False)` (:32940; `e` is the axis entry, stamped `e["stata"]` by `_dash_count_axes` from `fig._dash_stata_ticks` -- re-read at the base):

```python
        _emb = e.get("stata")
        if _emb is not None and _dash_same_range(lo_units, hi_units, _emb["range"]):
            ticks = list(_emb["ticks"])
        else:
            ticks = _dash_axis_count_ticks(lo_units, hi_units, n, kind)
```
with `_dash_same_range(lo, hi, r)`: `abs(lo - r[0]) <= 1e-9 * max(1.0, abs(r[0])) and abs(hi - r[1]) <= 1e-9 * max(1.0, abs(r[1]))`, a module function after `"_dash_reference_lines",` in the functions tuple (with `_dash_stata_ticks_for(fig, word, panel_key)`, the reader `_dash_count_axes` uses to stamp `e["stata"]`), and `fig._dash_stata_ticks` the per-figure dict stamped from the spec (the panel's entry for a by() figure). JS twin inside the `dash_axis_finish` IIFE's placer (:31430-31444): `dash_same_range(lo, hi, r)` as a named function in `_DASH_AXIS_FINISH_JS` beside `dash_refline_extent`, reading the plan entry's `a.stata` (numbers the plan already carries; no tag parsing, no user text).

### Reference TR-45.C: the probe set and units

| probe | variable / format | unit for `_tsnatscale` | expected agreement at base (model) |
|---|---|---|---|
| TD, N5, IF1, IF2, IF3, Y2, BY | `%td` | d | TD/N5/Y2/BY/IF1/IF3 agree; IF2 not |
| TW | `%tw` | w | agrees |
| TM | `%tm` | m | agrees |
| TQ | `%tq` | q | agrees |
| TH | `%th` | h | not |
| TY | `%ty` | y | agrees |
| MIX, MIXN | `%td` beside a number | d (the date's units) | agree |
| auto price #4, trunk #2, trunk #3 | number | `_natscale` | the three `_KNOWN` misses |
| auto price default, mpg if foreign | number | `_natscale` | agree |
| `%tc` axis | `%tc` | `_natscale` on ms (tickset_g: %tc takes natscale) | model |
| by(foreign, xrescale) price weight | number, two panels | `_natscale` per panel | model |

The extractor records `model_agrees` per probe by calling dash's model in its python block, so `TestBuildTicksAreStatas` knows which nodes are red at base without a literal list.

### Verbatim TR-45.D

- test_natscale.py:72-78 xfail reason text: `"natscale case the model does not reproduce; at build the drawn axis is Stata's own (WP-31 D15, test_stata_ticks.py::TestBuildTicksAreStatas::test_auto_misses)"`.
- test_date_axis_ticks.py:59-61: `_AGREES` renamed `_MODEL_AGREES` with the comment `#: The probes where dash's MOVE-TIME model draws twoway's ticks; at build every probe is Stata's own (WP-31 D15).`
- dash.sthlp axis paragraph sentence: `A default axis, or one labelled {cmd:#N}, is ticked where Stata's own {cmd:_natscale} and {cmd:_tsnatscale} tick it, computed when the graph is registered; after a filter move the saved page and the served app place {cmd:twoway}'s rule with a fitted model that agrees with Stata on 58-98% of ranges (measured), and a move back to all the data restores Stata's ticks. {cmd:xtick(#N)} and {cmd:xlabel(minmax)} follow a move the same way.`
- CHANGELOG Results line: `- default date axes and auto's price #4 and trunk #2/#3 axes took a fitted model's ticks (58-98% agreement); at build they take Stata's own natscale and tsnatscale ticks (WP-31, D15)`.
- program_coverage_map.py: `"_dash_axis_ticks_stata": ("test_wp31_truth.cscript:U45-02",),` under `"dash.ado"`; `"_dash_axis_ticks_json": ("test_wp31_truth.cscript:U45-03",),` under `"dash_parse.mata"`.

## Boundaries

- No change to `_dash_natscale_ticks`/`_dash_tsnatscale_ticks`'s arithmetic or `_DASH_TS_PARAMS` (the model is the fallback; refitting is not S45's).
- `_FILTER_JS`'s own text untouched (S46's); the module statement :31459 unchanged.
- by() grammar (`style(rescale) noyrescale`, test_by_scales.py:426) stays S36's residual; S45 adds a Notes line.
- No new dependency; no `shell=True`; no qualifier text reaches `summarize`: the selection is the `__dashq<k>` marker column `_dash_qual_gen`/`_dash_qual_gen_by` already materialise (A25).

## Stata truth

Script `scripts/extract_stata_ticks_truth.do` -> `test/fixtures/stata_ticks_truth.json`: for each of the 11 `_BUILD` probes of test_date_axis_ticks.py (re-using scripts/extract_date_axes_truth.do's `_dt_data`/`_dt_axis` programs by `include`) plus `auto price #4`, `auto trunk #2`, `auto trunk #3`, `auto price` default, `auto mpg if foreign` (#5 under a qualifier), `by(foreign, xrescale)` on `auto price weight`, a `%tc` axis and a mixed axis: record (a) `summarize`'s min/max, (b) `_natscale`/`_tsnatscale`'s r() (`r(ticks)` or the delta form), (c) the drawn `.Graph` ticks (`_dt_axis`) and (d) their equality; plus `time.reg_1e6`: seconds for `_dash_axis_ticks_stata` on a 10^6-row `%tc` variable (`timer`); plus `horizontal.y2`: `scatter mpg weight, horizontal` and `..., horizontal yaxis(2)` -- the drawn x axis's ticks (mpg's) and the y axis's (weight's); plus `margin.svg_600`/`margin.svg_1200`: twoway's plot-region margin in data units at `xsize(3)` and `xsize(6)` (SVG plotregion rect vs the axis range).

Truth block `* ==== S45 D15: Stata's own ticks at build ====`: U45-01 fixture stamped; U45-02 for every probe `_dash_axis_ticks_stata`'s r(json) ticks equal `.Graph`'s drawn ticks (same session); U45-03 the registered spec's `_stata_ticks` equals (b) and dash's saved and served axes draw them (python helper over `_dash_serve_spec` output, `_major_ticks(ax)` as test_by_scales does); U45-04 `auto price #4`, `trunk #2`, `trunk #3` drawn equal to twoway in both modes; U45-05 registration of the 10^6-row frame adds under 1 s (`timer list`); U45-06 after `dash ... if foreign` the drawn ticks equal twoway's `if foreign` ticks (the embedded range is the one `__dashq<k>` selects); U45-07 `dash scatter mpg weight, horizontal` writes mpg's ticks under `_stata_ticks.x` and both modes draw them on the x axis (`horizontal.y2`).

## TDD test stubs

### `test/test_stata_ticks.py` (new)

- Test: fixture stamped; every probe's embedded ticks equal its drawn ticks (the fixture's own claim) -- `TestTheFixture::test_meta`, `::test_stata_agrees_with_itself` (guard).
- Test: a spec carrying `_stata_ticks` draws exactly those ticks at build, both modes, for every probe (synthetic data spanning the probe's range) -- `TestBuildTicksAreStatas::test_probe[mode-probe]` (red: the model's ticks on the non-`_AGREES` probes; green by chance on others -- mark those as guards from the fixture's `model_agrees` flag computed in the test by calling the model).
- Test: the three auto misses draw twoway's ticks -- `::test_auto_misses[mode-case]` (red).
- Test: a spec without `_stata_ticks` draws the model's -- `TestTheFallback::test_no_key_is_the_model` (guard).
- Test: after a saved move the axis takes the model; a move back to all restores the embedded list; the served app the same -- `TestAfterAMove::test_saved_move_then_back`, `::test_served_move_then_back` (red: never restored).
- Test: the range comparison refuses a range off by more than 1e-9 relative -- `TestTheRangeRule::test_mismatch_falls_to_model`, `::test_histogram_axis_has_no_key` (red/guard).
- Test: `xtick(#4)` and `xlabel(minmax)` re-place after saved and served moves -- `TestCountTickAndMinmaxMove::test_xtick[mode]`, `::test_minmax[mode]` (red: held).
- Test: by(, xrescale) panels each take their own embedded ticks -- `TestPanels::test_each_panel[mode]` (red).
- Test: secondary axis (`yaxis(2)`) takes its embedded ticks -- `TestSecondaryAxes::test_y2[mode]` (red).
- Test: under `horizontal` the spec's `x` entry holds the y variable's ticks and the drawn x axis takes them; `horizontal yaxis(2)` likewise under `x` -- `TestHorizontal::test_swapped_words[mode]` (red; REVIEW-3e F17).
- Test: `_dash_axis_ticks_stata`'s source holds no `if \`cond'`-style substitution: it reads one marker name and `summarize ... if <marker>, meanonly` (source scan) -- `TestNoQualifierText::test_marker_only` (red; A25).
- Test: margin per D-45d -- `TestMargin::test_resize_keeps_statas_margin` (red) or `::test_bound_is_documented`.
- Test: `_DASH_AXIS_FINISH_JS` placer equals the Python placer on the fixture (node) -- `TestTheJsPlacer::test_equal` (red).

### Flips

test_date_axis_ticks.py::TestDefaultDateAxes (every probe equals twoway at build; `_AGREES` renamed `_MODEL_AGREES` and used by the move tests only); reasons "build ticks are Stata's own (D15)". test_natscale.py: xfail REASONS retargeted (not flips; a `Flipped:`-style line `Retargeted: test/test_natscale.py:76 -- the xfail now says the drawn axis is Stata's at build` in the body).

### cscript: U45-01..U45-07. Parity: `CORPUS` "auto price #4 default", "%tm default axis"; `MOVE_CORPUS` "xtick(#4), dropdown to Foreign", "xlabel(minmax), range".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Embedded ticks at build | pytest + U45-02/03/04 | stata_ticks_truth.json | yes |
| Fallback and move-back | pytest | same | yes |
| xtick/minmax moves | pytest + parity | -- | yes |
| Panels, secondary axes | pytest | same | yes |
| Registration cost | U45-05 | same | n/a |
| Margin | pytest + fixture | same | saved |

AC-45.1 every probe equal at build; AC-45.2 the three auto misses equal; AC-45.3 moves re-place and restore; AC-45.4 cost bound; AC-45.5 one green commit; AC-45.6 xfail reasons retargeted, documented.

## Tasks

**Commit boundary.** 45-01..45-03 form the one D15 commit, subject `Embed Stata's own natscale and tsnatscale ticks at build and re-place count ticks and minmax after a move (WP-31 D15)`, made by 45-03; the Tracked line reads `commit pending` (DECISIONS A11; the merger's step k.3b fills the sha; no amend). `$WT=<worktrees>/wp31-s45`.

<task type="auto" id="45-01">
  <name>Measure Stata's tick routines and write failing tests</name>
  <files>scripts/extract_stata_ticks_truth.do, test/fixtures/stata_ticks_truth.json, test/test_stata_ticks.py</files>
  <action><![CDATA[
    Check the worktree (wp31-s45 at the batch-15 base); re-read `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS` (the placer inside the `dash_axis_finish` IIFE), `_dash_count_axes`, `_dash_place_count_ticks(e, lo, hi, common=False)` and `_dash_finish_count_ticks` at this base (S09/S24/S33/S35 moved them; at 6370ca4 :32852, :32940, :33346 -- REVIEW-3e F16) and `_dash_qual_gen`/`_dash_qual_gen_by`'s marker column names (dash.ado:6345, :6420; A25), and write their current anchors into `<scratch>/s45/anchors.txt`. Create the extractor (reuse `_dt_data`/`_dt_axis` from scripts/extract_date_axes_truth.do by `include`; the `_natscale`/`_tsnatscale` calls per probe; the timing probe; the margin SVGs; `_meta`); run through the slot; `git add -f`. Create test/test_stata_ticks.py with the stub classes (specs built with `_stata_ticks` from the fixture's (b) values). Run it `-q -n0 -p no:cacheprovider -rf > <scratch>/s45/45-01.log`; write `<scratch>/45-01-failure.txt`. Write U45-01..U45-07 in the S45 block; run (`WP31_ONLY=S45`); append FAIL lines. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/stata_ticks_truth.json'));print(sorted(d['_meta']), len(d['probes']), all(p['stata_ticks']==p['drawn_ticks'] for p in d['probes'].values()))"` prints the five keys, at least 19 and True; `grep -c FAILED <scratch>/s45/45-01.log` is at least 10; `grep -c "U45-0[3-7] FAIL" <scratch>/s45/run_test_wp31_truth.log` is at least 4; `test -s <scratch>/45-01-failure.txt`.]]></verify>
  <done>Stata's _natscale/_tsnatscale answers were shown equal to the drawn axes for every probe and recorded with the registration cost and margins, and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="45-02">
  <name>Embed Stata's ticks at registration and draw them at build</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[
    Apply TR-45.1 (`_dash_axis_ticks_stata` over the `__dashq<k>` markers, A25; `_dash_axis_ticks_json`; the `_dash_plot` call after `_dash_qual_gen`, under the drawn axis words; header index, `_needed`, program_coverage_map.py) and TR-45.2 (`_dash_count_axes` stamping `e["stata"]`, `_dash_place_count_ticks(e, ...)`'s embedded-first rule and the JS twin inside the `dash_axis_finish` IIFE; the figure stamp in both `_make_figure_body` and the served `_dash_figure_for`); copy-list entry for any new module helper after `"_dash_reference_lines",`; function_test_map.py entries. Flip test_date_axis_ticks.py's `_AGREES` nodes (`_MODEL_AGREES` for moves). Run test_stata_ticks.py (TestBuildTicksAreStatas, TestTheFallback, TestAfterAMove, TestTheRangeRule, TestPanels, TestSecondaryAxes, TestHorizontal, TestNoQualifierText, TestTheJsPlacer green), test_date_axis_ticks.py, test_natscale.py, test_natscale_js.py, test_default_axes.py, test_by_scales.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_function_test_map.py, test_program_coverage_map.py, test_csp.py, and U45-02..U45-07 through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_stata_ticks.py -k "not CountTickAndMinmax and not Margin" test/test_date_axis_ticks.py test/test_natscale.py test/test_natscale_js.py test/test_default_axes.py test/test_by_scales.py test/test_csp.py -q -p no:cacheprovider` ends 0 failed (xfails counted as xfailed); `grep -c "U45-0[2-7] PASS" <scratch>/s45/run_test_wp31_truth.log` prints 6; `grep -c "if \`mark', meanonly" dash.ado` prints 1.]]></verify>
  <done>Every default and #N axis of a Stata-registered graph draws Stata's own ticks at build in both modes, falls to the model after a move and restores them on a move back, within the measured registration cost.</done>
</task>

<task type="auto" id="45-03">
  <name>Re-place xtick and minmax after moves, settle the margin, close D15</name>
  <files>dash_render.py, dash.sthlp, BUGS.md</files>
  <action><![CDATA[
    Apply TR-45.3 (tags and the three-tag placers in Python and the finish JS; `_dash_finish_count_ticks` extended) and TR-45.4 per `margin.*` (D-45d). Retarget test_natscale.py's xfail reasons (D-45b). Apply TR-45.6's help and audit edits; append the parity entries. Run test_stata_ticks.py whole, test_mode_parity.py -k "xtick or minmax or natscale", test_saved_filter_layers.py -k axis, test_second_axis*.py, test_help_conformance.py, and the S45 block once more. Close BUGS.md D15 (Resolution names D-45a/D-45b/D-45d; a Residual clause only if the margin is documented: "Residual, deferred (WP-31): the plot margin is a build-time fraction, up to 0.8% of the width on resize (GAPS3 D15 Tracked, ratified A6)"), rewrite `D15 Tracked` to `- **D15 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (or the Partly form `Partly closed in WP-31 (section 45, commit pending): ...; open: the resize margin (BUGS.md "<title>")` naming the margin when D-45d documents it; A11: the merger's step k.3b writes the sha), replace the marker (Results line: "default date and auto price/trunk axes: the fitted model's ticks -> Stata's own"). Commit `(WP-31 D15)`; no tooling names. Write `<scratch>/s45/handback.txt` (sha; D-45b for ratification; D-45d's branch; the note that test_by_scales.py:426 stays S36's).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_stata_ticks.py test/test_mode_parity.py -k "xtick or minmax or natscale" test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` ends 0 failed; `grep -c FAIL <scratch>/s45/run_test_wp31_truth.log` prints 0; `git log -1 --format=%s` ends `(WP-31 D15)`; `grep -c "D15 Tracked:\*\*.*commit pending" GAPS3.md` prints 1; `grep -c "WP-31 D15" test/test_natscale.py` prints at least 1.]]></verify>
  <done>xtick(#N) and xlabel(minmax) follow filter moves in both modes, the margin is fixed or documented with its measured bound, the natscale xfails say what they now mean, and the D15 commit landed green.</done>
</task>

## Section completion criteria

- Every probe's axis equals Stata's at build in both modes; moves fall to the model and restore on move-back; xtick/minmax re-place; margin settled per D-45d; registration cost within bound.
- One green commit; BUGS.md D15 closed (or closed with the margin residual); Tracked line reading `commit pending` (A11); marker; fixture stamped and named; xfail reasons retargeted; no qualifier text in `_dash_axis_ticks_stata` (A25).

## Notes

- **R11:** S45 is batch 15's one editor of `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS`; re-read both at the batch-15 base (S35 moved them in batch 12).
- **R12:** `_FILTER_JS`'s literal is S46's this batch; S45 touches only `_DASH_AXIS_FINISH_JS` (appended by the module statement, which is not edited).
- **Renderer order:** the figure stamp (`_dash_stata_ticks`) must be set before `_dash_finish_count_ticks` (and so `_dash_count_axes` and `_dash_place_count_ticks`) runs in BOTH `_make_figure_body` and the served `_dash_figure_for`; the served redraw after a move rebuilds figures -- the stamp is re-read from the spec there too. Under `horizontal` the stamp's keys are already the drawn words (dash.ado wrote them so); the renderer does not swap them again.
- **Copy lists (R2):** new helpers after `"_dash_reference_lines",`; constants (a tag string) after `_DASH_STALE_STATUS_HTML`'s group.
- **R6:** `version 19`; `_needed` alphabetical; the seven graph key lists unchanged (`_stata_ticks` is written inside `graph_options` by the JSON writer directly, not parsed as an option -- confirm the writer accepts an extra key: :7339's list is for parsed options; add the key where `graph_options` is assembled, :7335-7415).
- **For S36 (by-remainder, landed):** the `style(rescale) noyrescale` x count (test_by_scales.py:426) is a by() grammar matter; with D-45a the panel's x range under that style is what dash.ado summarizes -- if S36 made the range right, the xfail may now pass (strict xfail would then FAIL: 45-02 checks and, if so, flips it with `Flipped:` and the reason "the panel's ticks are Stata's own at build").
- **python_exec hazard** as S40.
- **Decisions for ratification:** D-45b (model kept as fallback; xfails retargeted), D-45d's branch.
