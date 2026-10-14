# Section 35: Second-axis ranges after a move, the first-used axis, horizontal titles

> Part of: WP-31 · GAPS3 rows: D9 · Risk: yellow · Batch: 12 · Depends on: 09 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U35

## Overview

**What is wrong today.** GAPS3 D9 (4.D, S2): "Secondary axis: the y2/x2 range is built once and never follows a filter move in either mode; the first-used axis is not drawn left/bottom; `horizontal` with `yaxis(2)` titles no x axis." Evidence dash_render.py:31764 (`_dash_add_secondary_axes` builds `Range1d(lo, hi)` from `_compute_secondary_range` over the build frame), :31723-33579 (the second-axis helpers), "no y2 in `_DASH_AXIS_FINISH_JS`/`_FILTER_JS`" -- verified by grep at 6370ca4: between the start of `_DASH_AXIS_FINISH_JS` (:30933) and its end (:31462) the strings `extra_y_ranges`, `"y2"` and `y_range_name` do not occur; `_dash_refinish_axes` (:32271-32301) calls `_dash_finish_count_ticks(f, refinish=True)`, which re-ticks and re-ranges the axes `_dash_count_axes` enumerates, and `_dash_count_axes` does enumerate an axis whose `y_range_name` is `y2` (def +52: `name = getattr(ax, range_attr, "default") or "default"; rng = ... getattr(fig, extra_attr).get(name)`) -- so where exactly y2 is left behind (the plan's `ri` for a Range1d the finisher never registered, empty `layers` for the extra axis, or the padded-range overwrite) is measured in 35-01 with a Python probe before anything is written; the call order is NOT a candidate: count-ticks already runs after the secondary axes in both modes (saved :44108 then :44136; served :49640 then :49657). research/codebase-mechanics.md §4: "Neither `_dash_refinish_axes` nor `_DASH_AXIS_FINISH_JS` touches y2/x2 after a move (GAPS3 D9)." GAPS3 H6 adds the missing parity entry: "second-axis range after a slider move".

The two smaller parts: twoway draws the FIRST axis it uses on the left (axis_choice_options.sthlp:76-77 "The first y axis appears on the left, and the second (if there is a second) appears on the right", measured by S09's fixture `sides.y23_no1` for a graph whose layers use axes 2 and 3 only); and under `horizontal` a layer on `yaxis(2)` gives no x-axis title because `_dash_axis_default_titles` (dash_render.py:28538-28575) swaps each series' labels through `_dash_is_horizontal` and then collects x labels only from layers whose `xaxis` list holds the axis asked for -- measured in 35-01 (`twoway scatter mpg weight, horizontal yaxis(2)` has an x title: the fixture says which).

**After this section.** After a filter move, in both modes, every extra range `y<n>`/`x<n>` (S09's names; `y2`/`x2` at least) is recomputed over the rows kept by exactly the rule that built it, so a move that keeps every row leaves `start`/`end` unchanged and a move that drops the layer's high values shrinks the range as the primary axes shrink. The saved page does it in `_DASH_AXIS_FINISH_JS` through the axis plan (the extra ranges are planned axes with their Range1d indexed), the served app in `_dash_refinish_axes`. When no layer uses axis 1 of a letter, the first axis used (in layer order) is drawn on the first side (left/below) and numbered as twoway numbers it. `horizontal` with `yaxis(2)` titles the x axis as twoway does.

**Test order and commit rule.** One row, one commit `(WP-31 D9)`: 35-01 probes, measures, writes failing tests; 35-02 fixes; 35-03 certifies, documents, closes and commits.

### Section decisions (binding on the executor)

- **D-35.a One rule builds and re-fits an extra range.** `_dash_finish_secondary_axes` stops setting `rng.start/end` from its own `_dash_padded_range` call and instead registers each extra axis with the hull machinery: it appends (or completes) the axis's entry in `fig._dash_hull_axes` (the entries `_dash_count_axes` makes; the extra axis is already enumerated there when its `y_range_name` is set, and `_dash_finish_count_ticks` already runs after the extra axes exist in both modes, so the fix is to carry the extra axis's `range()`, `norescale` and label positions into its entry's `explicit`/`scale` lists, as the primary axes do, and to stop `_dash_finish_secondary_axes` overwriting the padded range). Then `_dash_hull_ranges` (called by `_dash_finish_count_ticks`) sets the extent at build, `_dash_refinish_axes` re-sets it on a served move, and `_dash_axis_plan` indexes the Range1d so `dash_axis_compute` re-sets it on a saved move -- one rule, three callers. If the probe (35-01) shows the extra axes are already in the plan but the plan's `layers` for them are empty (because `_dash_tag_hull_roles`/`_dash_layer_extent` filter renderers by `range_attr == name` and the layers were assigned `y_range_name` AFTER tagging), the fix is the ordering of the range-name assignment (the S09 helpers, names per S09's hand-back) before the tagging; the probe decides between the two candidates -- empty `layers` or the padded-range overwrite -- and both are the same TR-35.1.
- **D-35.b The padding rule is twoway's, not 5%.** `_compute_secondary_range`'s 5% padding (dash_render.py:11840-11875) is the first estimate only; the final extent is `_dash_hull_ranges`' twoway plot-region margin, as for the primary axes (WP-30 P1.3a). If a pinned test asserts the 5% value for y2 (test_dual_axis.py `test_secondary_y_axis_range_covers_data`, :154: reads "covers"; test_axis2_suboptions.py `test_extents` :303), it is flipped to the hull rule with the reason.
- **D-35.c The first-used axis.** For a letter whose layers use no axis 1: the axes used, in order of first use among the layers, are renumbered 1, 2, 3 ... for drawing (axis 1 = first used, drawn on the first side; 2 the other side; ≥3 stacked, S09's rule), while every option written for the typed number (`ylabel(, axis(3))`) still reaches the layer it was written for. Implemented in `_dash_lone_second_axes` (:4000; the name S09 gives it after D-09.c -- S09's text calls it `_dash_lone_axis_rewrite`, a name that does not exist at HEAD): the rewrite maps typed numbers to drawn numbers through a per-graph dict `{typed: drawn}` applied to every layer's `yaxis` option and to the `*2` keys/`axisn` object's names. When a layer does use axis 1 nothing is renumbered (twoway: axis 1 is the left one). Measured by S09's `sides.y23_no1` and 35-01's `first_used.*` cases.
- **D-35.d The horizontal x title.** The fixture decides the text; the hypothesis is that twoway titles the x axis of a horizontal layer on `yaxis(2)` with the layer's y variable label (the horizontal swap puts the y variable on x, and the x axis is axis 1 for every layer). The fix is in `_dash_axis_default_titles`: after the horizontal swap, the x label joins `xs` when `str(xaxis)` is in the layer's `xaxis` option list (it is, "1"), so the probe must show why it is empty today (likely the y-side filter excludes the layer and a later guard drops `xs`); fix where the probe points, inside `_dash_axis_default_titles` or `_dash_add_secondary_axes`'s default-title call (:31778-31781: `_dash_axis_default_titles(plots, var_labels, yaxis=2 ...)[0 if n == "x" else 1]`).

## Risk: [yellow] -- the axis finishers are shared by every figure; one editor per batch (R11)

**Why.** `_dash_refinish_axes`, `_dash_finish_count_ticks`, `_dash_axis_plan` and `_DASH_AXIS_FINISH_JS` run for every saved page with a filter and every served move; a wrong hull entry re-ranges a primary axis. R11 names S35 as batch 12's one editor of the finishers. Risk factors: (1) the plan's JSON grows an entry per extra axis -- `js_runner` tests of the plan shape (test_axis_plan*.py, test_saved_axis_finish*.py: `ls test/ | grep -i "axis_plan\|axis_finish"`) may pin counts; (2) renumbering typed axes must not change where options land; (3) the horizontal title's cause is unknown until probed; (4) partners S36 (by() appliers) and S37 (region appliers) do not touch the finishers.

**Mitigation.** (1) 35-01's probe records the plan before/after; the count pins are flipped with reasons; (2) `TestFirstUsed::test_options_follow_their_layer` pins `ylabel(, axis(3))` landing on the renumbered axis; (3) the probe in 35-01 writes `<scratch>/s35/probe.txt` naming the line; (4) Boundaries.

## Dependencies

- **Depends on: 09** (the `y<n>` names, `_dash_axisn_value`, `axis_side(which, n, count)`, `fig._dash_extra_axes`; S09's fixture `sides.y23_no1`). **Blocks: --.**
- **Parallel batch: 12** with S36 and S37. S35 owns `_dash_add_secondary_axes`, `_dash_finish_secondary_axes`, `_dash_refinish_axes`, `_dash_finish_count_ticks`, `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS`, `_dash_lone_second_axes`, `_dash_axis_default_titles` for this batch. S36 edits the by() grammar appliers only; `_dash_common_count_ticks` is a finisher (R11) that S36's emptied-panel rule must not edit (S36 Boundaries). S36 owns `_generate_app_source` in batch 12 (index owner table); S35 makes no template edit. S37 edits region appliers only.

## Evidence

### The build (dash_render.py:31764-31770, :32581-32700) and the finish order (saved :44108 then :44136; served :49640 then :49657)

```python
31771        lo, hi = _compute_secondary_range(frame, plots, axis_key, var_key, 2)
31772        getattr(fig, rng_attr)[name] = Range1d(lo, hi)
```

`_dash_finish_secondary_axes` docstring (:32600-32612): "The range is the hull of the drawn values, every range() value and the ylabel2()/xlabel2() positions (unless `norescale`), padded by `_dash_padded_range` -- range() only ever widens." It is called after the layers at saved :44108 and served :49640, and `_dash_finish_count_ticks` runs AFTER it in both modes (saved :44136 in `_make_figure_body`'s tail; served :49657 in `_dash_figure_for`'s): count-ticks already runs after the secondary axes in both modes, so no call-order move and no second count-ticks call is needed (35-01 re-greps the four lines).

### The move paths

- Served: template :50355-50363, step 3b `_dash_refinish_axes(_axis_figs, _axis_fmap)` after step 3's data copy; `_dash_refinish_axes` (:32271-32301) → `_dash_finish_count_ticks(f, refinish=True)` → `_dash_count_axes(fig, every_axis=True, refinish=True)` → `_dash_hull_ranges`.
- Saved: `_dash_axis_plan(self.figures, ...)` at :46253 → plan JSON + models; `_FILTER_JS = (_FILTER_JS + _DASH_AXIS_FINISH_JS ...)` (:31459-31462); `dash_axis_finish(plan, models)` (:~31380) sets `r.start/end/reset_start/reset_end` for each planned range index via `dash_axis_compute`. The plan entry per axis holds `range` (model index, -1 for none), `layers` (source, filter, fields) and `scale`/`explicit`/`margin`/`reverse`; `_dash_axis_plan` builds it from `fig._dash_hull_axes` (:32382ff) with `rng = getattr(f, letter + "_range") if name == "default" else getattr(f, "extra_%s_ranges" % letter).get(name)`.

### The lone rewrite and the default titles

`_dash_lone_second_axes` (:4000; S09 generalises it to one number k, D-09.c, under the name its hand-back gives). `_dash_axis_default_titles` (:28538-28575): series swapped under `_dash_is_horizontal`; `ys`/`xs` filtered by `str(yaxis) in (opts.get("yaxis") ...)`. `_dash_add_secondary_axes` default title call :31778-31781.

### Pinned tests (flip, never delete; the probe confirms which are red)

| Node | Today | After |
|---|---|---|
| test/test_dual_axis.py::TestSecondaryAxisSetup::test_secondary_y_axis_range_covers_data (:154) | 5% padding (if asserted numerically) | the hull rule's extent (D-35.b) |
| test/test_axis2_suboptions.py::TestTheSecondAxisOptionsReachTheSecondAxis::test_extents (:303) | today's extents | the hull rule's |
| test/test_axis2_suboptions.py::TestAfterAFilterMove::test_served_move_keeps_routing (:398) | profile equal before/after (types, ticks, span) | unchanged (guard) -- extend with the range |
| test_mode_parity.py MOVE_CORPUS cases with `yaxis(2)` (:1935-1971 CORPUS; MOVE: grep) | move profile excludes y2 range (H6) | the move profile compares extra ranges |
| any test pinning y2 `start/end` after a saved move (`grep -rn "extra_y_ranges" test/*.py | grep -i "move\|filter"`) | unchanged after move | recomputed |

## User stories

- **US-35.1** As a dashboard reader, I want the right-hand axis to re-scale when I move a filter, as the left one does, on the saved page and in the served app.
- **US-35.2** As a twoway user, I want a graph whose layers use `yaxis(2)` and `yaxis(3)` only to draw the first-used axis on the left, as twoway does.
- **US-35.3** As a twoway user, I want `scatter mpg weight, horizontal yaxis(2)` to title its x axis as twoway titles it.

## Business requirements

- **BR-35.1** After any filter move, each extra range's `start`/`end` equals what a fresh build over the kept rows gives (the move oracle `_saved_with_qualifier`, test_mode_parity.py:2802), both modes, to 1e-9; a move keeping every row changes nothing.
- **BR-35.2** At build, an extra range's extent follows the hull rule the primary axes follow (twoway's margin), with `range()`, label positions and `norescale` honoured as today.
- **BR-35.3** With no layer on axis 1 of a letter, the first-used axis is drawn on the first side and every `axis(#)` option reaches the layer it was typed for; with a layer on axis 1 nothing is renumbered.
- **BR-35.4** `horizontal` with `yaxis(2)` draws the x title twoway draws (fixture).
- **BR-35.5** One- and two-axis graphs without a filter are unchanged except where D-35.b changes the padding (flipped tests name it).

## Technical requirements

- **TR-35.1 Register the extra axes with the hull (D-35.a).** In `_dash_finish_secondary_axes`: after the axis's `range()`/label/tick/line reading (the part that computes `want`, the label positions and `norescale`), instead of `rng.start, rng.end = _dash_padded_range(...)`, write the axis's inputs where `_dash_count_axes` reads them for a primary axis: `fig._dash_scale_values2[name] = <range() values>` (exists), `ax._dash_hull_ticks`/`ax._dash_hull_tick_extra` (label and tick positions), `ax._dash_norescale`/`_dash_tick_norescale`, `fig._dash_scale_reverse2[name]`, `fig._dash_margin` for the letter -- the same attributes `_dash_apply_axis_spec` writes for ylabel()/ytick() on axis 1 (grep `_dash_hull_ticks =` to find the writer and call the same helper). The build's `_dash_finish_count_ticks(fig)` call already runs AFTER `_dash_finish_secondary_axes` in both modes (saved :44108 then :44136; served :49640 then :49657), so no call-order move and no second `_dash_finish_count_ticks(fig, refinish=True)` call is made (a second call would re-tick every axis twice per figure at build); the probe decides only between the two candidates -- the extra axis's plan `layers` are empty (fix: the range names are assigned before `_dash_tag_hull_roles` tags, through the S09 helpers) or the padded-range overwrite is the culprit (fix: delete it). Delete the `_dash_padded_range` extent write for extra axes (the function stays for other callers). If TR-35.1's in-function registration cannot carry the extra ranges without a template edit, stop, open residual D9b and hand back (Boundaries).
- **TR-35.2 The plan carries the extra axes.** `_dash_axis_plan` (:32308-32420): confirm (probe) that an extra axis's entry gets `ri` (its Range1d is a `Range1d`: yes, built at :31772) and a non-empty `layers` list (from `_dash_tag_hull_roles`/`_dash_layer_extent` filtering by `range_attr == name`). Fix whichever the probe shows empty. `_DASH_AXIS_FINISH_JS`: `dash_axis_compute` reads `a.layers` and `a.range` with no letter/name test (`grep -n '"default"' dash_render.py` inside 30933-31462 in 35-01: if a branch skips non-default names, generalise it). The one JS section of batch 12 is S35's (R11/R12 note: `_DASH_AXIS_FINISH_JS` is not `_FILTER_JS`; S35 edits only the axis finish literal).
- **TR-35.3 Served re-finish.** `_dash_refinish_axes` needs no change once TR-35.1 holds: `_dash_finish_count_ticks(f, refinish=True)` enumerates every axis. Confirm with the served move test; if `_dash_count_axes(refinish=True)` skips entries whose `base is None and every is None` for ranging (it keeps them in `entries`; `_dash_hull_ranges(fig, entries)` ranges all), nothing to do.
- **TR-35.4 First-used axis (D-35.c).** `_dash_lone_second_axes`: for each letter, `used = [n for layer in order, first occurrence]`; if `1 in used`: no change; else `mapping = {typed: i+1 for i, typed in enumerate(used)}`; rewrite each layer's option (`"1"` for the first → delete the key, as today), the `*2` graph keys → the first-axis keys when mapped to 1 (today's code) or to `*2` when mapped to 2, and `axisn[<letter><typed>]` → `axisn[<letter><drawn>]` or the `*2`/first keys. The orphan note (`_DASH_AXIS2_KEYS` loop, :3986) runs after the rewrite (confirm order; both loaders call the rewrite "before the spec is drawn or embedded", docstring :4014-4016).
- **TR-35.5 Horizontal title (D-35.d).** Per the probe: fix in `_dash_axis_default_titles` or `_dash_add_secondary_axes`'s default-title call so the fixture's `horizontal.y2.xtitle` text is drawn; the control case `scatter mpg weight, horizontal` keeps its titles.
- **TR-35.6 Parity (H6).** test_mode_parity.py: the static `_figure_profile` (:837-838) already carries `extra_x`/`extra_y` and is not duplicated; the gap is the MOVE comparison built on `_own` (:2888ff) -- it gains every figure's `extra_y_ranges`/`extra_x_ranges` `start`/`end` (rounded to 9 places) in the saved-vs-served and oracle comparison of a move; `MOVE_CORPUS` gains `_move_case("yaxis(2) line, range slider", _MOVES[<range move>], [_sc(), plot_for("line", {"yaxis": "2"}, yvar="price")])`, `"by(foreign) yaxis(2), dropdown"` (F9: the per-panel re-finish) and the S09 three-axis move. `ALLOWED` is not edited (R8).
- **TR-35.7 Registries.** No new module function expected (TR-35.1 reuses writers); if a helper is factored out (e.g. `_dash_register_hull_inputs(fig, ax, name, ...)`), it goes on the functions copy tuple after `"_dash_reference_lines",` (R2) and in function_test_map.py under `# WP-31 S35 (D9)`.
- **TR-35.8 Security.** The plan holds numbers, letters, kinds and column names only (docstring :32322-32323); extra-axis entries add nothing else. No new JS beyond generalising a name test; no HTML.

### Code to insert and the probe (verbatim where marked)

**35-01's probe `<scratch>/s35/probe.py` (run with the repo's test directory on `sys.path`; prints the facts D-35.a and D-35.d need):**

```python
import sys, os
HERE = "/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s35"
sys.path[:0] = [HERE, os.path.join(HERE, "test")]
import warnings; warnings.simplefilter("ignore")
import dash_render as dr
import test_mode_parity as mp
import js_runner

plots = [mp._sc(), mp.plot_for("line", {"yaxis": "2"}, yvar="price")]
spec = mp._spec(plots, None, filt="foreign, type(dropdown)")
r = mp._saved_renderer(spec)          # the helper test_mode_parity uses for the saved page
fig = mp._figures_of(r)[0]
y2 = fig.extra_y_ranges["y2"]
print("build y2", y2.start, y2.end)
for e in getattr(fig, "_dash_hull_axes", ()):
    print("hull entry", e.get("letter"), e.get("name"), type(e["rng"]).__name__)
plan, models = dr._dash_axis_plan(r.figures, r.facet_map, zoom=False)
import json
for g in plan:
    for p in g["panels"]:
        for a in p["axes"]:
            if a.get("name") != "default":
                print("planned extra axis", a["letter"], a["name"], "range", a["range"],
                      "layers", len(a.get("layers", [])))
sess = js_runner.JsSession(r.filter_callbacks)
sess.select("Foreign")                 # the Select move as test_saved_filter_layers drives it
moved = sess.range_of(y2)              # start/end the page's JS left
oracle = mp._saved_with_qualifier(spec, "foreign == 1")
of = mp._figures_of(oracle)[0].extra_y_ranges["y2"]
print("saved y2 after move", moved, "oracle", (of.start, of.end))
print("y2 after move == oracle:", abs(moved[0] - of.start) < 1e-9 and abs(moved[1] - of.end) < 1e-9)
sv = mp._served_after_move(spec, ("Select", "Foreign"))
s2 = mp._figures_of(sv)[0].extra_y_ranges["y2"]
print("served y2 after move", s2.start, s2.end)
hz = mp._spec([mp.plot_for("scatter", {"horizontal": "1", "yaxis": "2"})])
hf = mp._figures_of(mp._saved_renderer(hz))[0]
print("horizontal titles", [a.axis_label for a in hf.below], [a.axis_label for a in hf.left + hf.right])
```

(The helper names `_saved_renderer`, `_figures_of`, `_saved_with_qualifier`, `_served_after_move`, `JsSession.select`/`range_of` are to be checked against test_mode_parity.py:2756-2802 and js_runner.py:302-439 and replaced by the real names before running; the probe is a scratch file, never committed.)

**TR-35.4 the typed-to-drawn mapping (`_dash_lone_second_axes`, replaces the `lone` logic of :4028-4036 for each letter; `_dash_axis_no` is the S09 reader, name per S09's hand-back):**

```python
        for side in ("y", "x"):
            used = []
            for p in plots:
                n = _dash_axis_no(p.get("options"), side)
                if n not in used:
                    used.append(n)
            if 1 in used or not used:
                continue                       # twoway: axis 1 is the first side
            # No layer on axis 1 (WP-31 D9, D-35.c): the first axis used is
            # drawn first, the second second, and so on; every option typed
            # for an axis number follows the layer it was written for.
            mapping = {typed: drawn + 1 for drawn, typed in enumerate(used)}
            remap[side] = mapping
```

followed by the rewrite of each layer's `<side>axis` option through `mapping` (drawn 1 → the key deleted), the `*2` graph keys and `axisn` names through the same mapping (`_dash_axisn_value`'s inverse: a value for typed k lands under the drawn number's key).

**TR-35.6 the move comparison (test_mode_parity.py, in the figure digest the `_own` move cases (:2888ff) compare before and after a move -- not in the static `_figure_profile`, which already has `extra_x`/`extra_y` at :837-838):**

```python
        "extra_ranges": {name: (round(rg.start, 9), round(rg.end, 9))
                         for name, rg in list(fig.extra_y_ranges.items())
                         + list(fig.extra_x_ranges.items())},
```

## Boundaries

- Not S35's: building axes 3-9 and routing `axisn` (S09, landed); `_FILTER_JS`'s filter body (the JS sections); by() panel emptying and `_dash_common_count_ticks`' letters (S36 -- but S36 must not edit the finishers: R11); region appliers (S37); the date-axis ticks after a move (S45, batch 15, the next finisher editor); `_dash_option_rules`; `_make_figure_body`. Not `_generate_app_source` (S36's this batch). If TR-35.1's in-function re-finish cannot carry the extra ranges, stop, open residual D9b and hand back.

## Stata truth

**New extractor** `scripts/extract_axis2_move_truth.do` → `test/fixtures/axis2_move_truth.json` (path-free; `_meta` five keys; `git add -f`). `sysuse auto`. twoway has no filter: the truth for a move is twoway drawn under the same `if` (the move oracle's own definition, test_mode_parity.py:2802), so the fixture records twoway's y2 axis range before and under `if foreign == 1`, and the first-used/horizontal cases.

| Key | twoway command | Recorded |
|---|---|---|
| `move.full`, `move.foreign` | `(scatter mpg weight) (line price weight, yaxis(2))` [+ `if foreign == 1`] | `.Graph.yaxis2.major.ticks` or the SVG tick labels of the right axis; `.Graph.plotregion1.yscale2` min/max if readable (the class value names are probed: `.Graph.yaxis2.` members) |
| `move.x2_full`, `move.x2_foreign` | `(scatter mpg weight) (scatter mpg price, xaxis(2))` [+ `if`] | the top axis's tick labels |
| `first_used.y23`, `y32` | `(scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3))`; the two layers swapped | side of each axis (SVG label x positions), its label range (which variable) |
| `first_used.y2_opts` | the y23 graph plus `ylabel(0(10)50, axis(2)) ytitle("Two", axis(2))` | which drawn axis carries 0..50 and "Two" (expected the left one) |
| `horizontal.y2`, `horizontal.ctrl` | `scatter mpg weight, horizontal yaxis(2)`; `scatter mpg weight, horizontal` | `.Graph.xaxis1.title.text`, `.Graph.yaxis1.title.text` / `.yaxis2.title.text` |

**Truth block** (R1) `* ==== S35 D9: Second-axis ranges after a move, the first-used axis, horizontal titles ====`, helpers `_u35_*`:
- **U35-1** `dash (scatter mpg weight) (line price weight, yaxis(2)), filter(foreign, type(dropdown)) name(u351)`: saved page's `_FILTER_JS` run under node (js_runner.JsSession) with the Select at Foreign: `extra_y_ranges["y2"].start/end` equal the saved renderer re-run with `if foreign == 1` (the move oracle) to 1e-9; served `make_document` + `_fire` the same; the tick labels of the right axis after the move equal twoway's `move.foreign` labels.
- **U35-2** the same with `xaxis(2)` and a range-slider move (`filter(weight, type(range))`) to 2000-3000.
- **U35-3** a move that keeps every row: `start/end` unchanged to the bit, both modes.
- **U35-4** `first_used.*`: dash draws the first-used axis on the side twoway does, both modes; `ylabel(0(10)50, axis(2))` lands on the axis twoway labels.
- **U35-5** `horizontal.*`: dash's axis titles equal twoway's.

**Block skeleton** (WP-30 form):

```stata
// S35 helpers (WP-31 D9).  _u35_move: for a registered dash graph with a
// filter, the extra ranges' start/end before and after a Select or
// RangeSlider move, saved (node) and served, and the oracle's (the saved
// renderer under the move's qualifier); through globals u35_b, u35_s,
// u35_v, u35_o.
python:
(helpers, top level, built on test/js_runner.py's JsSession and
 test/test_mode_parity.py's _served_after_move and _saved_with_qualifier)
end
* ==== S35 D9: Second-axis ranges after a move, the first-used axis, horizontal titles ====
local only : env WP31_ONLY
if inlist("`only'", "", "S35") & `: list posof "S35" in w31_run' {
display as text "S35 start"
sysuse auto, clear
dash clear
// U35-1
capture noisily dash (scatter mpg weight) (line price weight, yaxis(2)), ///
    filter(foreign, type(dropdown)) name(u351)
_w31_expect U35-1 (_rc == 0) "yaxis(2) with a filter rc `=_rc'"
tempfile sp dp
_dash_serve_spec, specpath("`sp'") datapath("`dp'")
python: _u35_move("`sp'", "`dp'", "Select", "Foreign", "foreign == 1")
_w31_expect U35-1 ("${u35_s}" == "${u35_o}") "saved y2 after move ${u35_s}, oracle ${u35_o}"
_w31_expect U35-1 ("${u35_v}" == "${u35_o}") "served y2 after move ${u35_v}, oracle ${u35_o}"
_w31_done U35-1 "the second axis re-fits over the rows a move keeps, both modes"
// U35-2 .. U35-5 likewise
dash clear
display as text "S35 end"
}
* ==== end S35 ====
```

**Area script:** none (no refusal changes).

## TDD test stubs

### Regression tests, `test/test_second_axis_moves.py` (new; red at 6370ca4 unless guard)

Helpers: saved moves through `js_runner.JsSession(r.filter_callbacks)` (js_runner.py:302-439) as test_saved_filter_layers.py does; served through `test_mode_parity._served_after_move`; oracle `_saved_with_qualifier`.

- Test: fixture stamped and complete -- `TestTheFixture::test_meta`, `::test_keys` (guard after 35-01).
- Test: after a dropdown move the y2 range equals the oracle's, saved (node) and served -- `TestTheRangeFollowsAMove::test_y2_saved`, `::test_y2_served` (red); x2 with a range move -- `::test_x2_saved`, `::test_x2_served` (red); a three-axis graph (S09) -- `::test_y3[mode]` (red); `by(foreign)` panels each with a `yaxis(2)` layer after a dropdown move, every panel's y2 equal to its oracle (`_dash_refinish_axes(figures, facet_map)` and the JS plan are per panel) -- `::test_by_panels[mode]` (red).
- Test: a move keeping every row leaves every extra range unchanged -- `::test_identity_move[mode]` (red if the build padding differs from the re-finish rule; else guard -- record).
- Test: the axis plan carries an entry per extra axis with `range >= 0` and non-empty `layers` -- `TestThePlan::test_extra_axes_are_planned` (red).
- Test: at build an extra range's extent equals the hull rule's over its layers (compare with a primary axis given the same data) -- `TestTheBuildRule::test_hull_not_five_percent[mode]` (red).
- Test: layers on 2 and 3 only: first-used left, second right; options follow their layer -- `TestFirstUsed::test_sides[mode-order]`, `::test_options_follow_their_layer[mode]` (red); with a layer on 1 nothing is renumbered -- `::test_axis_one_present_is_unchanged[mode]` (guard).
- Test: horizontal with yaxis(2) titles x as the fixture says; the control is unchanged -- `TestHorizontalTitle::test_y2[mode]` (red), `::test_control[mode]` (guard).
- Test: `_DASH_AXIS_FINISH_JS` and `_dash_refinish_axes` have no name test that skips extra ranges (source read) -- `TestNoSkip::test_js_and_python` (red if such a test exists; the probe decides).

### Cases in cscripts

- `test_wp31_truth.cscript` U35-1..U35-5 (red; U35-3 red or guard per the probe).

### Flips

From Evidence; recorded in `<scratch>/s35/35-flips.txt` with `Flipped (WP-31 D9): the second axis follows a move and takes the hull rule`.

### Parity corpus (R8)

TR-35.6's three MOVE_CORPUS entries and the extended `_own` move comparison.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| y2/x2/y3 after a move, by() panels | pytest `TestTheRangeFollowsAMove` (incl. `test_by_panels`); cscript U35-1, U35-2; MOVE_CORPUS (incl. "by(foreign) yaxis(2), dropdown") | `move.*` | yes |
| Identity move | pytest `::test_identity_move`; U35-3 | -- | yes |
| Build rule | pytest `TestTheBuildRule`; flips | -- | yes |
| Plan shape | pytest `TestThePlan`, test_axis_plan*/js_runner tests | -- | saved |
| First-used axis | pytest `TestFirstUsed`; U35-4 | `first_used.*`, S09's `sides.y23_no1` | yes |
| Horizontal title | pytest `TestHorizontalTitle`; U35-5 | `horizontal.*` | yes |

**Acceptance criteria**
- **AC-35.1** After the dropdown and range moves, every extra range equals the oracle's to 1e-9 in both modes; the identity move changes nothing.
- **AC-35.2** The plan has one entry per extra axis with a range index and layers.
- **AC-35.3** First-used sides equal the fixture's; `axis(2)` options land where twoway lands them.
- **AC-35.4** Horizontal titles equal the fixture's.
- **AC-35.5** test_dual_axis.py, test_axis2_suboptions.py, test_axes_three_to_nine.py (S09) green after the flips; parity green with the extended profile; U35-1..U35-5 PASS; no SKIP.

## Tasks

**Commit boundary.** One commit on `wp31-s35` (`$WT=.../dash-wt/wp31-s35`), subject `Re-fit the second axes after a filter move and draw the first-used axis first (WP-31 D9)`, made by 35-03; body in BRIEF's forms with `Fixture: test/fixtures/axis2_move_truth.json (scripts/extract_axis2_move_truth.do)`, `BUGS.md: "<D9 title>" (closed)`, `GAPS3: D9 Tracked`.

<task type="auto" id="35-01">
  <name>Probe, measure twoway, write failing tests</name>
  <files>scripts/extract_axis2_move_truth.do, test/fixtures/axis2_move_truth.json, test/test_second_axis_moves.py</files>
  <action><![CDATA[
    Check the cut (`<scratch>/batch-12-base.txt`, branch `wp31-s35`); `mkdir -p <scratch>/s35/x`. Probe first (Python only, no pytest, no Stata): a script `<scratch>/s35/probe.py` imports dash_render, builds the saved renderer for the spec `(scatter mpg weight) (line price weight, yaxis(2)), filter(foreign, type(dropdown))` on test_mode_parity's `_DF` (`import test_mode_parity as mp`; `mp._spec`), and prints: `fig.extra_y_ranges["y2"].start/end`; the entries of `fig._dash_hull_axes` (name, `rng` type, `ax` type); the plan from `dr._dash_axis_plan(r.figures, r.facet_map)` filtered to the y2 entry (its `range`, `layers`); the `start/end` after a `js_runner.JsSession` move to Foreign versus `mp._saved_with_qualifier`; the served `start/end` after `mp._served_after_move`; and the call order of `_dash_finish_count_ticks` vs `_dash_finish_secondary_axes` in both modes (`grep -n "_dash_finish_count_ticks(\|_dash_finish_secondary_axes(" dash_render.py`; expected saved :44108 then :44136 and served :49640 then :49657 -- count-ticks already runs after the secondary axes, so the order is not a candidate). Also `scatter mpg weight, horizontal yaxis(2)`'s axis titles. Write the findings to `<scratch>/s35/probe.txt` naming the line where y2 is left behind (D-35.a's two candidates: empty plan `layers` or the padded-range overwrite) and the title's cause (D-35.d). Create scripts/extract_axis2_move_truth.do per "Stata truth" (path-free head; the `.Graph.yaxis2.` member names probed with `classutil describe` and recorded), run it through the slot, `git add -f` the fixture. Create test/test_second_axis_moves.py with the classes of "TDD test stubs"; append U35-1..U35-5 to test/test_wp31_truth.cscript above the marker (helpers `_u35_*`). Flip the Evidence pins that the probe confirms are wrong (record in `<scratch>/s35/35-flips.txt`). Run the pytest file (`-rf > <scratch>/s35/35-01.log`) and the truth script (`WP31_ONLY=S35`) on the unmodified tree; write `<scratch>/35-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`test -s <scratch>/s35/probe.txt` and it contains the words `y2` and `plan`; `python3 -c "import json;d=json.load(open('test/fixtures/axis2_move_truth.json'));print(sorted(d['_meta']), sorted(d))"` prints the five `_meta` keys and `_meta first_used horizontal move`; `grep -c FAILED <scratch>/s35/35-01.log` is at least 8 and no FAILED line names TestTheFixture, test_control or test_axis_one_present_is_unchanged; `grep -c "U35-[1245] FAIL" <scratch>/s35/run_truth.log` is at least 3; `grep -c SKIP <scratch>/s35/run_truth.log` prints 0; `test -s <scratch>/35-01-failure.txt`.]]></verify>
  <done>The exact point where the second axis is left behind by a move was found by probe, twoway's ranges under the move's qualifier, first-used sides and horizontal titles were recorded, and every regression test and case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="35-02">
  <name>Re-fit extra ranges, renumber first-used axes, title horizontal</name>
  <files>dash_render.py, test/test_mode_parity.py, test/function_test_map.py</files>
  <action><![CDATA[
    Following `<scratch>/s35/probe.txt`: make TR-35.1 (register each extra axis's inputs with the hull writers; no second `_dash_finish_count_ticks` call and no template call-order move -- count-ticks already runs after the secondary axes; delete the `_dash_padded_range` extent write for extra axes; if the extra ranges cannot be carried without a template edit, stop, open residual D9b and hand back), TR-35.2 (the plan's `range`/`layers` for extra axes; generalise any `"default"`-only test in `_DASH_AXIS_FINISH_JS` -- the only JS edited is that literal), TR-35.3 (confirm; no change expected), TR-35.4 (`_dash_lone_second_axes`'s typed→drawn mapping), TR-35.5 (the horizontal title where the probe points), TR-35.6 (the extra ranges in `_own`'s move comparison and the three MOVE_CORPUS entries, including "by(foreign) yaxis(2), dropdown"). Any factored helper goes on the copy tuple after `"_dash_reference_lines",` and in function_test_map.py under `# WP-31 S35 (D9)`. Run `python3 -m pytest test/test_second_axis_moves.py test/test_dual_axis.py test/test_axis2_suboptions.py test/test_axes_three_to_nine.py test/test_saved_filter_layers.py test/test_served_filter_move.py test/test_function_test_map.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -n0 -p no:cacheprovider`, then `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "yaxis or axes or Move"`, then the truth script (`WP31_ONLY=S35`). A failure in a file 35-01 did not edit is a missed pin: flip it in place with its reason if it asserts the 5% padding or a frozen y2; otherwise stop and report.
  ]]></action>
  <verify><![CDATA[Every pytest run reports 0 failed; `grep -c "U35-[1-5] PASS" <scratch>/s35/run_truth.log` prints 5 and `grep -c " FAIL\|SKIP"` prints 0; `python3 <scratch>/s35/probe.py | grep -c "y2 after move == oracle: True"` prints 1 (add that line to the probe's output in 35-01).]]></verify>
  <done>Every extra range followed a filter move in both modes by the rule that built it, layers using no first axis drew their first-used axis first with their options intact, and the horizontal second-axis graph took twoway's x title.</done>
</task>

<task type="auto" id="35-03">
  <name>Certify, document and commit D9</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
    Run every test file touched in 35-01/35-02 plus `python3 -m pytest test/test_saved_stale_cue.py test/test_axis*.py test/test_natscale.py test/test_by_scales.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` (globs by ls) and the truth script (`WP31_ONLY=S35`). dash.sthlp (R3; S35's paragraphs): the Secondary axes section's sentence on filters (`grep -n "second axis\|Secondary axes" dash.sthlp`) says the second axis re-scales with the rows a filter keeps in both modes, that with no layer on the first axis the first axis used is drawn on the left (below), and the horizontal title rule; the Server Mode / Linking sentence listing what a move recomputes (`grep -n "recomput" dash.sthlp`) adds "the second axes' ranges". Close D9: BUGS.md Resolution in BRIEF's closed form naming test/test_second_axis_moves.py::TestTheRangeFollowsAMove::test_y2_saved, ::test_y2_served, test/test_wp31_truth.cscript U35-1 and the fixture, with `Flipped:` reasons; GAPS3 `- **D9 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (DECISIONS A11: the merger's step k.3b fills the sha; never amend); CHANGELOG `<!-- WP-31 D9 -->` under Results → "A second axis kept its build-time range after a filter move in both modes (y2 12..41 stayed when Foreign kept 14..41); it re-fits over the rows kept, as the first axes do; its build extent takes twoway's plot-region margin instead of 5%; layers using no first axis draw their first-used axis on the left; horizontal with yaxis(2) titles the x axis (WP-31, D9)" with the measured numbers from the fixture. Stage dash_render.py dash.sthlp BUGS.md CHANGELOG.md GAPS3.md scripts/extract_axis2_move_truth.do test/test_second_axis_moves.py test/test_wp31_truth.cscript test/test_mode_parity.py test/function_test_map.py and the flipped files; `git add -f test/fixtures/axis2_move_truth.json`; `git diff --cached --name-only` names no CLAUDE.md/.ultraplan/*.html; commit once (no amend).
  ]]></action>
  <verify><![CDATA[Every pytest run reports 0 failed; the truth log holds `U35-1 PASS` .. `U35-5 PASS` and no FAIL or SKIP; `git log -1 --format=%s` ends `(WP-31 D9)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D9 -->' CHANGELOG.md` prints 0; `grep -c "re-scales\|re-fits" dash.sthlp` is at least 1; `grep -c "D9 Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 1; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The second axes' move behaviour, first-used placement and horizontal title were certified in both modes, documented, and D9 was closed in one green commit on wp31-s35.</done>
</task>

## Section completion criteria

- Every extra range follows dropdown and range moves in both modes to the oracle; identity moves change nothing; the build extent is the hull rule's.
- The plan carries every extra axis; `_DASH_AXIS_FINISH_JS` re-fits them; `_dash_refinish_axes` re-fits them served.
- First-used axis drawn first when no layer is on axis 1; options follow their layer.
- Horizontal `yaxis(2)` x title as twoway's.
- `axis2_move_truth.json` stamped and named; U35-1..U35-5 PASS; flips recorded; one green commit; D9 closed with a `commit pending` Tracked line.

## Notes

- **R11:** S35 is batch 12's only editor of `_dash_refinish_axes`, `_dash_finish_count_ticks`, `_dash_common_count_ticks`, `_dash_axis_plan` and `_DASH_AXIS_FINISH_JS`; S36 (by() emptied panels) must route its panel hiding through visibility, not the finishers, and S45 (batch 15) is the next finisher editor.
- **R12:** the axis-finish literal is appended to `_FILTER_JS` by the module statement at :31459-31462 (WP-30 A153): never edit inside `_FILTER_JS` itself; S35 edits only `_DASH_AXIS_FINISH_JS`'s text.
- **The identity move** is the sharpest test of D-35.a: if the build extent and the re-finished extent come from different rules, `start/end` jump on a move that keeps every row. Build and re-finish must share `_dash_hull_ranges`.
- **No template edit.** S36 owns `_generate_app_source` in batch 12 (index owner table); S35 makes no template edit, and none is needed: count-ticks already runs after the secondary axes in both modes. If TR-35.1 cannot carry the extra ranges in-function, residual D9b is opened and the section hands back.
- **Decision for ratification:** D-35.b (the second axis's build padding changes from 5% to twoway's margin -- a visible change on every two-axis dashboard; the flipped tests name it).
- **python_exec hazard**; **a skip is not a pass**; **cscript drops globals**.
- **Shared files.** R1: the S35 block. R2: a helper only if factored. R3: the Secondary axes and the recompute sentences. R4: one marker. R5: one entry. R7: one fixture. R8: profile extension and two MOVE entries; `ALLOWED` untouched. R9: flips. R13: the merger re-indexes.
- **For S09 (landed before batch 12):** S09's text names `_dash_lone_axis_rewrite`, `_dash_axis_no` and `_dash_assign_range_names` (":33578"); at HEAD the function is `_dash_lone_second_axes` (:4000) and the other two do not exist -- S35 uses the names S09's hand-back records.
- **For S45 (date ticks after a move):** the extra axes are planned axes now; a `%t` second axis re-ticks through the same `hold` placeholder rule (WP-30 P1.3b) once S45 generalises it.
- **For S60 (test harness, H6):** the saved-JS move oracle S60 adds should compare extra ranges too; the profile extension here is the Python oracle's.

## Addendum (14oct2026, DECISIONS D14): batch 1-4 gaps added to this section

### C10e: Axes 3 to 9 on a date variable are labelled in Stata numbers, and t-options with axis(3) to axis(9) are left as typed

**Gap.** S09 drew axes 3-9, but date kinds (`_dash_axis_date_kind`, the DatetimeAxis loop, the date `_convert`) are decided for axes 1 and 2 only, so an axis 3-9 on a %t variable shows Stata numbers; and `_dash_route_axis2` routes x and y options only, so tlabel()/tscale()/ttitle()/ttick() with axis(3)-(9) are left as typed (found by S09).

**Requirement.** Measure twoway with a %td/%tm variable on yaxis(3) and xaxis(3), and t options with axis(3); decide the date kind per axis number in both renderers (the saved page's axis plan and the served template), and route the t options for axes 3-9 as S09 routes x/y. Uses S09's `_dash_axis_groups`/`axis_side(which, n, used)`.

**Tests.** pytest (both modes) in test/test_axes_three_to_nine.py and a `* ==== S35 C10e: ... ====` truth block. Fits S35 because S35 owns the secondary/extra axes and their re-finish in batch 12.

**Process (binding, as for every row).** Task 1 of this row writes the failing tests and saves `<scratch>/35-C10e-failure.txt`; then the fix; then ONE commit with subject ending `(WP-31 C10e)`. The closing task flips the BUGS.md entry "Axes 3 to 9 on a date variable are labelled in Stata numbers, and t-options with axis(3) to axis(9) are left as typed" to `- [x]` with a Resolution in the BRIEF's closed form ending `Closes GAPS3 C10 (WP-31, C10e).`, deletes the `"C10e":` line from `WP31_OPEN` in test/test_tracking_documents.py, rewrites GAPS3.md's `- **C10e Tracked:**` line to `Closed in WP-31, BUGS.md "Axes 3 to 9 on a date variable are labelled in Stata numbers, and t-options with axis(3) to axis(9) are left as typed", commit pending.`, and replaces `<!-- WP-31 C10e -->` in place under `### Results that change` with a line ending `(WP-31, C10e)`. Measure twoway first (an extract script or a live probe in the cscript); where the measurement contradicts this addendum, the measurement wins and the deviation is recorded. Refusal/message cases go to the area cscript under the `U35` prefix; drawing comparisons go to a `* ==== S35 C10e: ... ====` block in test/test_wp31_truth.cscript. dash replaces twoway (DECISIONS D13): never use `dash twoway` in a probe.
