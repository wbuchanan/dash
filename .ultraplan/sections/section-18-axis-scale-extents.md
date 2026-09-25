# Section 18: Axis scale extents (B2)

> Part of: WP-28 · Gaps: B2 · Risk: red · Batch: 3 · Depends on: 02, 14 · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **3** · Depends on **02, 14** · Blocks **19** · Risk **red** · Commits: one commit (B2) → CHANGELOG `Results that change`

- D10: rewire `scripts/extract_axis_truth.do`'s private SVG code onto `scripts/svg_truth.py` when regenerating `axis_truth.json`; only this section edits `MUST_WARN`; the parity profile gains `renderers`/`reversed` fields; note Stata's 2.2% margin versus Bokeh's 5% pad (inner hulls are compared).
- D8: checkpoint 18-12 stays the last task. D7: split 18-02 and 18-05.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

**B2** (S1, silently wrong output). GAPS2 measured: "Explicit ticks only set a `FixedTicker`
(dash_render.py:16783-16786). With `ylabel(0(20)100)` on mpg 12-41, 60-100 are never shown";
"`_dash_apply_scale_ranges` (19017-19060) sets `Range1d(lo, hi)` exactly. `yscale(range(100))`
gives an inverted axis (100 to 41), `range(20 30)` hides data outside 20-30, and `range(0)` ends
exactly at the data maximum"; "`yscale(r(0 100))` is named and ignored". Stata's rules are the
opposite in every case: label and tick values widen the axis unless `norescale`
(axis_label_options.sthlp:344-350), and `range()` "never narrows the scale of an axis or causes
data to be omitted from the plot" (axis_scale_options.sthlp:336-341); `r()` is its abbreviation,
one value is one value to include, missing values are ignored.

The cause is where the extent is decided: before any layer is drawn, from the option alone, as
a bound. twoway decides it after: the axis is the hull of what is drawn, every tick and label
it places, and every `range()` value, then a margin. dash already has the place — `_dash_finish_count_ticks`
(17334-17352) runs after the layers in both modes (22335 saved, 26405 served), `_dash_count_axes`
(17210-17273) collects one entry per axis with the drawn minimum and maximum through each
renderer's view, and `_dash_place_count_ticks` (17276-17331) already widens a range to its
outermost `#N` ticks with Bokeh's 5% pad model. This section adds the hull step there, makes
`range()` a list of values to include, honours `norescale`, and writes a `Range1d` so the result
is the same number in both modes and pinnable against a fixture (report W §1g).

After this section: an axis with any explicit position or `range()` value spans the hull of its
drawn data, its label and tick positions (unless `norescale`) and its `range()` values, padded
5% a side (in log space on a log axis, in milliseconds on a date axis), reversed by `reverse`
or `rev`; an axis with no explicit value keeps Bokeh's autorange exactly as today; the second
axes follow the same rule; a by() graph's panels share one hull; and the saved page and the
served app limit their autoranges to the same renderers, which the parity profile now sees.
Nothing new is printed once honoured (DISCOVERY Q22); a `range()` value that is not a number is
named once.

**Test order (CLAUDE.md rule 7): task 18-01 writes every failing test**, runs it against the
tree as Sections 02 and 14 leave it, and the failures go into the B2 commit's message. This
section is one gap and one commit.

## Risk: [red] — every axis of every dashboard with a label, tick or range option changes extent, and the step must not fight count ticks, log and date axes, the by() common scale or the second axes

**Why.** PRD §10 risk 3. The hull runs in one place, but that place is shared by `#N` placement
(`_dash_place_count_ticks`), the by() common scale (`_dash_common_count_ticks`), the log and
date kinds (`_dash_count_axes`), and the second axes (`_dash_finish_secondary_axes`); the
saved renderer alone limits `DataRange1d.renderers` to primary-source renderers
(22314-22330), so a served figure autoranges over a fit's 10%-extended x grid while the saved
one does not — invisible to `test_mode_parity._axes`, which records a range only when its start
and end are numbers.

**Risk factors.** (1) Bokeh's `DataRange1d` autoranges over glyph bounds (a bar's half-width
included) while `_dash_secondary_values` reads coordinate columns: a `Range1d` from columns
alone would clip the outer half of an end bar. (2) A `Range1d` cannot be `flipped`; reverse is
start above end, and `_dash_place_count_ticks` must keep handling it. (3) Stata's margin is
2.2% of the canvas's shorter side (fixture `findings.axis_range_extension`), not 5% of the
span: the truth comparison must be of the *inner* hull, or it fails on every probe. (4) Count
ticks placed over the data alone would sit inside a `range()`-widened scale where twoway places
them over the whole scale. (5) `.Graph`'s scale members may be the data range, not the drawn
extent (report A surprise 4); which one, if any, equals the SVG is unknown until probed.

**Mitigation.** The hull reads bar widths; reverse is a swap and the existing Range1d branch;
pytest compares dash's inner hull with Stata's inner hull (SVG extent minus its measured
margin) and the finding's containment verdicts; count ticks are placed over data ∪ range
values before the hull; the extract script records all four `.Graph` candidates beside the
SVG extent and a verdict key, and the SVG stays the truth (DISCOVERY Q14 amendment).

## Dependencies

- **Depends on:** Section 02 (`scripts/svg_truth.py::svg_axis_extent(path, axis, tick_values)`,
  `test/cert_svg.do::cert_svg_export`, `cert_graph_scale, axis()` returning the four `.Graph`
  candidates) and Section 14 (the tick positions come from its parser: `FixedTicker.ticks`,
  `ax._dash_extra_ticks`, the CustomJSTicker `extra`; `norescale` joins its honoured tuple;
  `_dash_expand_numlist` expands a `range()` numlist).
- **Blocks:** Section 19.
- **Parallel batch:** 3, alone. It edits `_dash_finish_count_ticks`, `_dash_count_axes`,
  `_dash_place_count_ticks`, `_dash_common_count_ticks`, `_dash_apply_scale_ranges`,
  `_parse_scale_range`, `_dash_scale_spec`, `_dash_finish_secondary_axes`, the saved block at
  22314-22330 and the served template beside 26402 — regions no batch-2 section touches, but
  the parity profile change (TR-18.11) reaches every corpus case, so it runs after batch 2 is
  merged.

## Evidence

### Where the extent is decided today

`_dash_apply_scale_ranges` (19017-19065), called before any layer at 22102 (saved) and 26256
(served), replaces the range with an exact `Range1d`:

```python
19051        new_lo = lo if lo is not None else cur_lo
19052        new_hi = hi if hi is not None else cur_hi
19053        if new_lo is not None and new_hi is not None:
19054            setattr(fig, attr, Range1d(float(new_lo), float(new_hi)))
19055    for spec, attr in ((xspec, "x_range"), (yspec, "y_range")):
19056        if spec.get("reverse"):
19057            try:
19058                getattr(fig, attr).flipped = True
19059            except AttributeError:
19060                pass
```

so `range(100)` is `Range1d(100, 41)` (inverted), `range(20 30)` clips, `range(0)` ends at the
maximum, and `reverse` beside `range()` is dropped by the `except`. `_parse_scale_range`
(2409-2435) matches `\brange\s*\(` only and reads two tokens:

```python
2423    m = re.search(r"\brange\s*\(\s*([^)]*?)\s*\)", raw or "", re.I)
2424    if not m:
2425        return None, None
2426    parts = m.group(1).replace(",", " ").split()
2427    vals: list = []
2428    for tok in parts[:2]:
```

`_dash_scale_spec` (19001-19014) honours `_DASH_SCALE_SUBOPTS = {"log", "reverse", "range"}`
(18998) by exact name, so `r(0 100)` and `rev` are named through `_dash_report_suboptions`.
`norescale` is parsed nowhere (report A §B2). The second axes narrow the same way in
`_dash_finish_secondary_axes` (17158-17163):

```python
17158        if want_lo is not None:
17159            rng.start = float(want_lo)
17160        if want_hi is not None:
17161            rng.end = float(want_hi)
17162        if "reverse" in names:
17163            rng.start, rng.end = rng.end, rng.start
```

after it fitted the range to the drawn values with a 5% pad, in log space on a log axis
(17141-17157) — the padding model the hull reuses.

### The place for the hull, and the helpers already there

`_dash_finish_count_ticks(fig)` (17334-17352) runs after the layers and `_dash_keep_primary_ranges`
in both modes:

```python
17349    entries = _dash_count_axes(fig)
17350    fig._dash_count_entries = entries
17351    for e in entries:
17352        if e["lo"] is not None:
17353            _dash_place_count_ticks(e, e["lo"], e["hi"])
```

`_dash_count_axes` (17210-17273) walks every continuous axis on the four sides, finds its range
(`fig.y_range` or `extra_y_ranges[name]`), its kind (None, `"log"`, or the date kind from
`_dash_axis_date_kind`), and the drawn minimum and maximum through `_dash_secondary_values`
over a pool that is every renderer on y and the range's own renderers on x when limited
(17253-17262: "twoway's scale spans every layer on the axis. On x, a range limited to some
layers is read as it is limited: a fit's line is drawn 10% past the data there, which twoway's
is not") — but it returns only axes with a `#N` ticker. `_dash_place_count_ticks` widens:

```python
17313    if isinstance(rng, DataRange1d):
17314        if getattr(rng, "flipped", False):
17315            return
17316        if common:
17317            rng.start, rng.end = float(min(t_lo, d_lo)), float(max(t_hi, d_hi))
17318            return
17319        if t_lo < d_lo:
17320            rng.start = t_lo
17321        if t_hi > d_hi:
17322            rng.end = t_hi
17323    elif isinstance(rng, Range1d):
17324        a0, a1 = rng.start, rng.end
...
17327        if a0 <= a1:
17328            rng.start, rng.end = min(a0, t_lo), max(a1, t_hi)
17329        else:
17330            rng.start, rng.end = max(a0, t_hi), min(a1, t_lo)
```

with `d_lo/d_hi` the data padded 5% a side (log space on log). `_dash_common_count_ticks(figs)`
(17355-17377) re-ticks a by() graph's panels over all panels' data and sets each DataRange1d to
the common span. The explicit-label applier sets `FixedTicker(ticks=spec["ticks"])` (16783);
xtick positions travel as `CustomJSTicker(args={"extra": [...]})` (16893-16917); after Section
14, a count-mode list rides `ax._dash_extra_ticks`.

### The saved-only renderers block

`_make_figure_body`, 22314-22330, saved only:

```python
22322        _primary_renderers = [
22323            r for r in fig.renderers
22324            if hasattr(r, "data_source") and r.data_source is source
22325        ]
22326        if _primary_renderers:
22327            if isinstance(fig.x_range, DataRange1d):
22328                fig.x_range.renderers = _primary_renderers
22329            if isinstance(fig.y_range, DataRange1d):
22330                fig.y_range.renderers = _primary_renderers
```

The served template (26399-26405) goes from `_dash_finish_secondary_axes` to
`_dash_keep_primary_ranges(fig)` to `_dash_finish_count_ticks(fig)` with no such step; its
graph source is `src` (26122: `src = (_src_list[-1] if ... else shared_source)`).
`test_mode_parity._axes` (580-609) records `start`/`end` only when numeric and never
`renderers`, so the divergence is invisible.

### Stata's rules (report D §2, §3, §11)

- "By default, label options automatically rescale the axis and plot region to include the
  range of values in the new labels or ticks. norescale allows you to plot ticks or labels
  outside the normal bounds of an axis" (axis_label_options.sthlp:344-350).
- `range()` "specifies that the axis be expanded to include the numbers specified. Missing
  values, if specified, are ignored" (:144-148); `ysc(r(0))` extends 1-100 down to 0,
  `ysc(r(100))` extends 0-99 up to 100 (:314-334); "range() never narrows the scale of an axis
  or causes data to be omitted from the plot" (:336-341); it is a numlist, any count, any
  order; `r:ange`, `rev:erse` (:47-77).
- Bokeh (report W §1g): a narrow `Range1d` clips, it does not drop data; `DataRange1d` counts
  invisible renderers unless `only_visible=True`; the fixture-testable way is a Python-side
  `Range1d` with dash's own padding.
- `.Graph` has no `range_min`; candidates are `.Graph.plotregion1.yscale.{min,max,curmin,curmax}`
  ("permanent" and "temporary" in scale.class:19-27) and `.Graph.yaxis1.major.{min,max}`; the
  only committed reading (`natscale_axes_truth.json._meta`) gave the data range [12, 41] for a
  graph whose drawn extent is wider. The SVG-fitted extent is the truth (DISCOVERY Q14
  amendment); `.Graph` is probed once and used only where it matches.

### Truth already on disk

`test/fixtures/axis_truth.json` → `probes[id].y_axis.mapping.axis_low/axis_high` (SVG-fitted
drawn extent; `extract_axis_truth.do` 167-176, `axis_facts` 627-810):

| probe | option | axis_low | axis_high |
|---|---|---|---|
| `b_default` | none | 9.12 | 41.88 |
| `b_range_0` | `yscale(range(0))` | −1.16 | 42.16 |
| `b_range_60` | `yscale(range(60))` | 8.58 | 61.42 |
| `b_range_narrow` | `yscale(range(20 30))` | 9.12 | 41.88 (= default) |
| `b_range_0_50` | `yscale(range(0 50))` | −1.42 | 51.42 |
| `b_range_log` | `price, yscale(log range(1000 20000))` | 918.3 | 21775 (log10) |
| `b_xrange` | `xscale(range(0 6000))` | −92.7 | 6092.7 (x) |
| `b_reverse` | `yscale(reverse)` | 9.12 | 41.88, `reversed: True` |

`findings.axis_range_extension` records the margin: "Stata first widens the axis to include
every tick it decided to draw, then adds the margin", 71.2 px each side, 0.022 of the canvas's
shorter side (`margin_over_min_canvas_dimension_values`), so the **inner** hull is
`axis_low + m·span` to `axis_high − m·span` with `m = 71.2 / plotregion_px_extent` per axis.
No test reads any of these.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_axis_options.py::TestAxisScale::test_range_sets_the_axis_bounds` (start 0, end 50
  exactly), `::test_range_with_only_a_lower_bound` (start 0 exactly),
  `::test_range_combines_with_log` (`x_range.start == 1000`). Flip to hull assertions
  (TR-18.15). `::test_reverse_still_works` and `::test_unsupported_scale_suboptions_are_reported`
  stay.
- `test/test_html_output.py::TestXrangeYrange::test_xrange_embeds_unique_start_value`
  (`[("Range1d", -37.0, 99.0)]`), `::test_yrange_embeds_unique_end_value`
  (`[("Range1d", 0, 9999.0)]`). Flip: the document's Range1d start is below −37 / 0 and its end
  above 99 / 9999, and `_dash_range_hull` of it is the requested hull. `::test_xrange_invalid_ignores_gracefully`
  and `::test_yrange_invalid_ignores_gracefully` stay (DataRange1d kept) and gain "named once".
- `test/test_server.py::test_yscale_range_bounds_the_y_axis_in_both_modes` (about 1284-1305:
  `range(10 40)` → `(10.0, 40.0)`, `range(0)` → `(0.0, max)`). Flip: hull `(10, 41)` and
  `(0, 41)`, padded, identical in both modes.
- `test/test_served_dates.py::TestANumberOnADateAxisIsAStataDate::test_xscale_range_in_every_unit`
  (`(start, end) == (ms, ms)`), `::test_xscale_range_on_a_td_axis` (`== (_MS[0], _MS[3])`),
  `::test_one_range_bound_keeps_the_datas_other` (`start == _JAN4_2001`). Flip: a degenerate
  hull is widened by one unit then padded (`start < ms < end`); the td hull is `(_MS[0],
  _MS[3])` by `_dash_range_hull`; the one-bound case's hull low is `_JAN4_2001` only if it is
  below the data's first date — it is not (14979 is the third date), so the hull is the data's
  and the assertion becomes "the axis is not narrowed to 14979".
- `test/test_help_claims_7.py::test_yscale2_log_reverse_and_range` (about 1025-1035:
  `(rng.start, rng.end) == (0.0, 20000.0)` for `yscale2(range(0 20000))`). Flip: hull
  `(0, 20000)` padded; `reverse` still `start > end`.
- Verify, flip only if red: `test/test_graph_options.py::TestXscaleYscaleReverse` (no
  `range()` in any case, so `flipped` on a DataRange1d stays),
  `test/test_dual_axis.py::TestSecondaryAxisSetup::test_secondary_y_axis_range_covers_data`
  and `::TestSecondaryAxisOptions::test_ylabel2_custom_ticks` (still true under the hull),
  `test/test_natscale_axes.py::TestByPanelsShareOneScale` and `::TestBothModesTickLogAndDateAxes`
  (no explicit values: DataRange1d kept), `test/test_natscale.py::TestBothModesDrawTwowaysTicks`
  (`y_range.start <= 10`), `test/test_mode_parity.py` case "xscale(range()) and yscale with an
  unimplemented sub-option" (1163: both modes must agree on the new profile fields).

## User stories

- **US-18.1** As the Stata user pasting twoway syntax, I want `ylabel(0(20)100)` to draw the
  axis to 100 so that every label I asked for is on the graph, as in twoway.
- **US-18.2** As the Stata user, I want `yscale(range(100))` to extend the axis to 100 and
  never invert it, `range(20 30)` never to hide data, and `range(0)` to reach 0 with the usual
  margin at both ends, so that `range()` only ever widens.
- **US-18.3** As the Stata user, I want `yscale(r(0 100))`, `yscale(rev)`, `range(. 60)` and
  `range(100 0)` read as twoway reads them.
- **US-18.4** As the Stata user, I want `ylabel(0(20)100, norescale)` to draw the labels
  without widening the axis, as twoway does.
- **US-18.5** As the Stata user, I want log axes, date axes, `yaxis(2)` layers and `by()`
  panels to follow the same rule.
- **US-18.6** As the dashboard viewer, I want the saved page and the served app to show the
  same extent for the same graph.
- **US-18.7** As the maintainer, I want the extents pinned against twoway's own drawing, and
  the `.Graph` reading settled once.

## Business requirements

- **BR-18.1** An axis carrying explicit label or tick positions (`xlabel`, `ylabel`, `xtick`,
  `ytick`, `xlabel2`, `ylabel2`, a count rule's list) spans every one of them unless the
  option says `norescale`; with `norescale` the positions are drawn and the axis is not
  widened.
- **BR-18.2** `range()` widens the axis to include every value listed, in any order and any
  count; it never narrows; a single value is one value to include; a missing value (`.`) is
  ignored; `r()` and `rev` are the abbreviations; a value that is not a number is named once
  and ignored.
- **BR-18.3** An axis is never narrower than the data its layers draw, including a bar's
  full width and a fit or band's drawn values.
- **BR-18.4** The margin beyond the hull is 5% of the hull's span a side, in log space on a
  log axis, in the axis's own unit on a date axis; a degenerate hull is widened by one unit
  first. (Stata's margin is 2.2% of the canvas; that difference is B25 and stays.)
- **BR-18.5** `reverse` puts the high end first; with or without `range()`.
- **BR-18.6** `#N` ticks are placed over the widened scale, as twoway places them.
- **BR-18.7** `yscale2()`/`xscale2()` and `ylabel2()`/`xlabel2()` follow BR-18.1 to BR-18.5.
- **BR-18.8** A `by()` graph's panels share one extent, the hull over every panel.
- **BR-18.9** An axis with no explicit position and no `range()` value looks exactly as it did.
- **BR-18.10** The saved page and the served app give the same extent and limit their
  autoranges to the same renderers; the parity profile records both.
- **BR-18.11** Nothing is printed for an honoured option.

## Technical requirements

- **TR-18.1** `_parse_scale_range(raw) -> list[float]` (2409-2435): finds the rightmost
  `\b(r|ra|ran|rang|range)\s*\(([^)]*)\)` (case-insensitive; Stata's "rightmost sub-option
  wins"), expands its content with `_dash_expand_numlist` (Section 14, bounded by
  `_MAX_AXIS_TICKS`; commas as blanks), drops `.`, keeps every finite number, and names each
  other token once through `_dash_warn_once(("scale", "range", option, tok), …)`. Returns `[]`
  when absent. `_dash_scale_name(tok)` (new): the canonical name of a scale sub-option —
  `range` for any prefix of it of at least one letter `r`, `reverse` for `rev`…`reverse`,
  `log` — else `_dash_subopt_name(tok)`.
- **TR-18.2** `_dash_scale_spec(raw, option, seen, key)` compares canonical names against
  `_DASH_SCALE_SUBOPTS` and returns `{"log", "reverse", "values", "lo", "hi"}` with `values`
  the list and `lo`/`hi` its min/max or None (the keys `test_varlist_expansion.py` reads
  survive). `_DASH_SCALE2_SUBOPTS` (17037) and `_dash_finish_secondary_axes` use the same
  canonical names.
- **TR-18.3** `_dash_apply_scale_ranges(fig, xspec, yspec, frame, xvar, yvar)` never builds a
  `Range1d`: it converts the values on a date axis through `_dash_axis_positions` and names
  non-dates with `_dash_note_not_dates` (as at 19032-19046), stores
  `fig._dash_scale_values = {"x": [...], "y": [...]}` and `fig._dash_scale_reverse = {"x":
  bool, "y": bool}`, and sets `flipped = True` on a `DataRange1d` for `reverse` as today. The
  frame arguments stay in the signature (both call sites pass them) and are documented as
  unused.
- **TR-18.4** `norescale`: `_dash_parse_axis_spec`'s honoured tuple gains `norescale` (exact
  word, axis_label_options.sthlp:107-156 gives it no abbreviation) → `out["norescale"]`;
  `_dash_apply_axis_spec` sets `ax._dash_norescale = True` on each axis it tickers when set;
  `_dash_apply_tick_option` honours it likewise and sets `ax._dash_tick_norescale = True`.
  Both are underscore attributes on Bokeh models (allowed; `fig._dash_count_entries` already
  is one) and are not serialised.
- **TR-18.5** `_dash_count_axes(fig, every_axis=False)`: with `every_axis=True` an entry is
  returned for every continuous axis, `base`/`every` None when it carries no count ticker;
  each entry also records `"letter"` and `"name"`. Its pool rule (x: the range's own renderers
  when limited; y: every renderer; swatches skipped; log: positive values) is unchanged and is
  the hull's data rule.
- **TR-18.6** `_dash_axis_hull(fig, e)` (new) → `(lo, hi)` or None: collects (a) the entry's
  `lo`/`hi`; (b) for each renderer in the entry's pool whose glyph is a `VBar` (x) or `HBar`
  (y), `x ± width/2` / `y ± height/2` over the view's rows when `width`/`height` is a number
  or a column; (c) the tick positions: `FixedTicker.ticks`, a `CustomJSTicker`'s
  `args["base"]` ticks when it is a `FixedTicker`, and `ax._dash_extra_ticks`, all skipped when
  `ax._dash_norescale`; `args["extra"]` skipped when `ax._dash_tick_norescale`; (d) for the
  default range, `fig._dash_scale_values[letter]`; on a log axis every value ≤ 0 is dropped.
  Returns None when (c) and (d) are both empty — the axis is left to Bokeh — else the min and
  max over all collected values (never narrower than the data by construction).
- **TR-18.7** `_dash_padded_range(lo, hi, kind, reverse)` (new) → `Range1d`: a degenerate hull
  (`lo == hi`) becomes `lo − 1, hi + 1` (one decade in log10 space on `"log"`; one day,
  86,400,000 ms, on a `%tc`/`%tC`/`%td` axis and one period through
  `_dash_axis_positions([v − 1, v + 1], kind)` on the other date kinds); then 5% of the span a
  side, in log10 space when `kind == "log"`; `Range1d(start=hi_p, end=lo_p)` when `reverse`.
  `_dash_range_hull(rng, kind=None)` (new) inverts it: `(start + 0.05·s, end − 0.05·s)` with
  `s = (end − start) / 1.1`, in log10 space on log, ends swapped when reversed — the helper the
  tests and the cscript use. `_dash_range_reversed(rng)` (new): `flipped` on a DataRange1d,
  `start > end` on a Range1d.
- **TR-18.8** `_dash_hull_ranges(fig, entries, common=None)` (new): for each entry with a hull
  (or `common[key]` when given), replace the entry's range — `fig.x_range`/`fig.y_range` or
  the named extra range — with `_dash_padded_range(lo, hi, kind, reverse)` where `reverse` is
  `fig._dash_scale_reverse[letter]` for the default range, else `_dash_range_reversed(rng)`;
  record `fig._dash_hull_entries = [{"key", "letter", "name", "kind", "lo", "hi"}]`.
- **TR-18.9** `_dash_finish_count_ticks(fig)`: `entries = _dash_count_axes(fig,
  every_axis=True)`; `fig._dash_count_entries` = the counted subset (contract unchanged); for
  each counted entry widen `lo`/`hi` by the default range's `_dash_scale_values` before
  `_dash_place_count_ticks` (so `#N` is placed over the widened scale); then
  `_dash_hull_ranges(fig, entries)`. `_dash_place_count_ticks`'s Range1d common branch
  (17323-17330) widens to `d_lo`/`d_hi` as well as to the ticks.
- **TR-18.10** `_dash_common_count_ticks(figs)`: after its tick loop, group every panel's
  `_dash_hull_entries` by `key`; for a key with two or more panels and at least one hull,
  union the hulls (and each panel's own data `lo`/`hi`) and call `_dash_hull_ranges(f,
  entries_of(f), common={key: (lo, hi)})` per panel, so every panel of a by() graph spans one
  extent.
- **TR-18.11** `_dash_limit_ranges_to_primary(fig, source)` (new): the block 22314-22330 as a
  module function; the saved renderer calls it in place of the block; the served template
  calls `_dash_limit_ranges_to_primary(fig, src)` immediately before
  `_dash_keep_primary_ranges(fig)` (26402). **Decision:** shared function, not a template
  transcription — the repo's rule for every twin ("the helper the generated app runs as well",
  22103, 22112, 26263), and a transcription would be a second text to keep in step, which is
  the defect class report A §0.1 warns of. `test_mode_parity._axes.rng` gains `"renderers":
  len(r.renderers) if isinstance(r.renderers, list) else "auto"` and `"reversed":
  dr._dash_range_reversed(r)`, so the profile sees both the limit and the direction; the whole
  corpus must agree on them.
- **TR-18.12** `_dash_finish_secondary_axes`: the hull is the drawn values (`all_vals`, log:
  positive) ∪ `_parse_scale_range(scale_raw)` ∪ the `{n}label2` positions unless its spec says
  `norescale`; the range is `_dash_padded_range(lo, hi, "log" if is_log else None,
  "reverse" in canonical names)`; the narrowing lines 17158-17163 and the inline pad
  17141-17157 go. The label positions are parsed before the range is set (move the
  `_dash_parse_axis_spec` call up; keep `_dash_apply_axis_spec` after).
- **TR-18.13** Copy lists: functions 24466-24687 gain `_dash_scale_name`, `_dash_axis_hull`,
  `_dash_padded_range`, `_dash_range_hull`, `_dash_range_reversed`, `_dash_hull_ranges`,
  `_dash_limit_ranges_to_primary`; `test/function_test_map.py` gains one entry each (no
  nested `def`). The changed functions are already copied.
- **TR-18.14** No option, value or text reaches JS, HTML or `exec`: the hull is numbers on
  Python-built models; the one note (`range()` non-number) goes through `_dash_display`.
- **TR-18.15** Flips: `test_axis_options.py::TestAxisScale` asserts, for `range(0 50)`, a
  `Range1d` whose `_dash_range_hull` is `(0, 50)` (mpg 12-41 inside) and, for `range(0)`,
  `(0, 41)`; `test_range_combines_with_log` asserts a `LogAxis`, `start < 1000` and hull
  `(1000, 5000)` in log space; `test_html_output.py`, `test_server.py`, `test_served_dates.py`,
  `test_help_claims_7.py` as listed under "Tests that pin today's behaviour".

## Boundaries

- Stata's margin (2.2% of the canvas's shorter side) and twoway's default tick choice are
  **B25** (S3, out of scope); the hull keeps Bokeh's 5% and the default `BasicTicker`. The
  fixture records the difference; pytest compares inner hulls.
- The parser of positions is **Section 14**'s: no change to `_dash_axis_tokens`,
  `_dash_expand_numlist`, `_dash_parse_axis_label_opt`; this section adds one word to the
  honoured tuple and reads what 14 leaves on the axes.
- `off`, `noextend`, `extend`, `fextend`, `alt`, `fill`, `noline`, `titlegap()` and the rest
  of `yscale()`'s sub-options are **B23**: still named. `range(datelist)` on `tscale()` is
  **B14**. `by(, yrescale/xrescale)` is **B16**.
- A `range()` on a categorical axis (none in dash's types) is not handled.
- The saved page's JS is untouched: a `Range1d` written at build time holds across filter
  moves (as `range()` already did); an axis with no explicit value keeps its `DataRange1d`
  and re-fits after a move as today. CHANGELOG names this.
- C4/E4 (re-estimation after a move) is out of scope; the y hull of a fit is what it drew at
  build.

## Stata truth

Extend `scripts/extract_axis_truth.do` (after Section 14's edits: `zp id group dataset body
opts ticks hull`; `hull` = the values the option asks the axis to include, `ticks` = the tick
positions for the SVG fit when known). Load Section 02's programs as its smoke script does —
`cd "${ZA_REPO}/test"`, `quietly do "cert_svg.do"`, `cd` back — because `cert_svg.do` computes
its scripts directory from `c(pwd)` (it also sets `$dash_nobrowser 1` and exits 222 when
`c(python_exec)` is empty, which the script's own `python:` block needs anyway). In the export
loop, immediately after a probe draws with rc 0 and before `graph export`, read the `.Graph`
candidates with `cert_graph_scale, axis(y)` (and `axis(x)` for x probes) into locals — `r(min)
r(max) r(curmin) r(curmax)` and `r(major_min) r(major_max) r(major_delta)`; the program clobbers
`r()`, so read all seven at once — and write them into the record line; for the by() probe read
`.Graph.graphs[1].plotregion1.yscale.{min,max,curmin,curmax}` and the same for `graphs[2]`
directly. Add `sp500` to the data-facts variable lists (`close date`). In the `python:` block,
for each `b2_*` probe: `axis_low/axis_high` from `svg_axis_extent(svg, axis, ticks)["low"]` /
`["high"]` (Section 02's keys; store them under the fixture's existing `axis_low`/`axis_high`
names, with its `space` and `reversed`) when `ticks` is given, else the existing numeric-label
fit. `tick_values` must hold one entry per tick pixel in axis order or the reader raises
`ValueError`, and the reader returns `None` when fewer than two ticks pair: catch both, record
the probe's axis under `unverified` with the reason, and fall back to the numeric-label fit —
expect this on `b2_ylab_0_100_nr`, whose labels sit outside the plotregion, where the
`graph_scale` candidates and `stata_inner` still answer;
`requested = (min(data_min, hull…), max(data_max, hull…))`; `drawn_ticks` = the numeric tick
values found; `stata_inner = (min(data_min, drawn_ticks…), max(…))` (the extension finding's
own method); `inner_from_margin` = the extent shrunk by `71.2 / plotregion_px_extent` a side
(the measured margin); `graph_scale = {min, max, curmin, curmax, major_min, major_max,
major_delta}` (the `major_*` triple is twoway's own tick rule and is what
`b2_hash5_range100`'s tick assertion reads); verdicts
`contains_requested`, `narrower_than_data`, `widened_vs_default` (against `b_default` or the
x/log twin), `stata_inner_is_requested` (within 1e-3 of the span). Write
`findings.range_rule = {"per_probe": …, "all_contain_requested": bool,
"none_narrower_than_data": bool, "norescale_not_widened": bool}` and
`findings.graph_scale_matches_svg = {"per_probe": {id: "min/max" | "curmin/curmax" | "both" |
"none"}, "verdict": the one answer shared by every probe, else "mixed"}`. The block never calls
Stata; a backtick is `\x60`.

Probes, group `b2_extent`, dataset `auto`, body `twoway scatter mpg weight` unless noted:

| id | option | hull | ticks |
|---|---|---|---|
| `b2_ylab_0_100` | `ylabel(0(20)100)` | y 0 100 | 0 20 40 60 80 100 |
| `b2_ylab_0_100_nr` | `ylabel(0(20)100, norescale)` | — | same |
| `b2_ylab_pair` | `ylabel(0 "zero" 60 "sixty")` | y 0 60 | 0 60 |
| `b2_ytick_50` | `ytick(50)` | y 50 | — |
| `b2_ytick_50_nr` | `ytick(50, norescale)` | — | — |
| `b2_range_100` | `yscale(range(100))` | y 100 | — |
| `b2_range_0` | `yscale(range(0))` | y 0 | — |
| `b2_range_20_30` | `yscale(range(20 30))` | y 20 30 | — |
| `b2_r_0_100` | `yscale(r(0 100))` | y 0 100 | — |
| `b2_range_dot_60` | `yscale(range(. 60))` | y 60 | — |
| `b2_range_60_dot` | `yscale(range(60 .))` | y 60 | — |
| `b2_range_unsorted` | `yscale(range(100 0))` | y 0 100 | — |
| `b2_range_three` | `yscale(range(0 50 100))` | y 0 50 100 | — |
| `b2_range_bad` | `yscale(range(abc))` | — | — (rc and message) |
| `b2_log_range` | `scatter price weight, yscale(log range(1000 20000))` | y 1000 20000 | — |
| `b2_log_r_one` | `scatter price weight, yscale(log r(100000))` | y 100000 | — |
| `b2_rev_range` | `yscale(reverse range(0 50))` | y 0 50 | — |
| `b2_rev_abbrev` | `yscale(rev)` | — | — |
| `b2_hash5_range100` | `ylabel(#5) yscale(range(100))` | y 100 | — |
| `b2_xlab_wide` | `xlabel(0(1000)6000)` | x 0 6000 | 0 1000 … 6000 |
| `b2_xtick_nr` | `xtick(0 6000, norescale)` | — | — |
| `b2_lfit_range0` | `(scatter mpg weight) (lfit mpg weight), yscale(range(0))` | y 0 | — |
| `b2_bar_xrange0` | `twoway bar mpg weight, xscale(range(0))` | x 0 | — |
| `b2_td_range` | `sp500`: `twoway scatter close date, xscale(range(14900 15400))` | x 14900 15400 | — |
| `b2_by_range0` | `scatter mpg weight, by(foreign) yscale(range(0))` | y 0 | — (`.Graph.graphs[k]` only; SVG per panel is `unverified`) |

Run from a scratch directory: `mkdir -p /tmp/dash-s18 && cd /tmp/dash-s18 && STATATMP=/tmp/dash-s18/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_axis_truth.do`
(trailing slash; never the GUI; at most three Stata sessions; one run regenerates the whole
fixture, Section 14's groups included). `git add -f test/fixtures/axis_truth.json`.
`test_fixtures_are_committed.py` requires a test to name the fixture: `test_axis_options.py`
and the new `test_axis_extents.py` do.

## TDD test stubs

All in **`test/test_axis_extents.py`** (new), both modes through a `_figures` helper copied from
`test_natscale_axes.py:312-339` (`_MODES` parametrisation), an auto-like frame (`_auto()` of
`test_axis_options.py:50-60`), a `truth()` fixture that `pytest.fail`s when the `b2_extent`
group is missing, and `hull = dr._dash_range_hull`. The first stubs fail at the pre-fix tree.

- Test: `TestLabelValuesWidenTheAxis::test_ylabel_0_20_100_reaches_100` — `Range1d`,
  `hull(fig.y_range) == (0, 100)` in both modes. Pre-fix: DataRange1d, end ≈ 42.
- Test: `TestLabelValuesWidenTheAxis::test_norescale_draws_the_labels_and_keeps_the_extent` —
  FixedTicker 0…100, `DataRange1d` kept (no explicit hull value), no note.
- Test: `TestLabelValuesWidenTheAxis::test_ytick_50_widens_and_norescale_does_not`.
- Test: `TestLabelValuesWidenTheAxis::test_a_labelled_pair_widens` — `ylabel(0 "zero" 60
  "sixty")` → hull `(0, 60)`.
- Test: `TestLabelValuesWidenTheAxis::test_xlabel_widens_x` — `xlabel(0(1000)6000)` → hull
  `(0, 6000)`.
- Test: `TestRangeOnlyWidens::test_range_100_widens_up_and_never_inverts` — hull `(12, 100)`,
  `start < end`. Pre-fix: start 100, end 41.
- Test: `TestRangeOnlyWidens::test_range_20_30_never_narrows` — hull `(12, 41)`. Pre-fix:
  `(20, 30)`.
- Test: `TestRangeOnlyWidens::test_range_0_reaches_0_and_keeps_the_top` — hull `(0, 41)` and
  `end > 41`. Pre-fix: end exactly 41.
- Test: `TestRangeOnlyWidens::test_r_is_range` — `r(0 100)`: hull `(0, 100)`, no note.
  Pre-fix: named, DataRange1d.
- Test: `TestRangeOnlyWidens::test_rev_is_reverse`, `::test_missing_values_are_ignored`
  (`range(. 60)`, `range(60 .)`), `::test_any_count_in_any_order` (`range(100 0)`, `range(0 50
  100)`), `::test_a_non_number_is_named_once_and_the_axis_left_alone` (`range(abc)`:
  DataRange1d kept, one note in both modes, identical text).
- Test: `TestTheReader::test_parse_scale_range_forms` — `range(0 100)`, `r(5)`, `ra(. 3)`,
  `range(1,2,3)`, `range(0(50)100)`, `range()` → lists; rightmost of two `range()` wins.
- Test: `TestLogAndDateAxes::test_a_log_hull_is_padded_in_log_space` — price with `log
  range(1000 20000)`: `LogAxis`, `hull(fig.y_range, "log") == (1000, 20000)`.
- Test: `TestLogAndDateAxes::test_a_td_range_is_in_milliseconds` — `_kind_frame`-style %td
  frame with `xscale(range(14900 15400))`: hull equals the two epoch-ms values.
- Test: `TestLogAndDateAxes::test_a_degenerate_hull_is_widened_by_one_unit` — one-row frame,
  `range(v v)`: `start < v < end`, both modes equal.
- Test: `TestReverse::test_reverse_with_a_range_is_start_above_end` — `reverse range(0 50)`:
  `Range1d`, `start > end`, `hull == (0, 50)`. Pre-fix: dropped by the `except`.
- Test: `TestReverse::test_reverse_alone_keeps_the_flipped_datarange`.
- Test: `TestCountTicksOverTheHull::test_hash5_with_range_100_ticks_over_the_widened_scale`
  — the FixedTicker equals `b2_hash5_range100`'s drawn ticks and the hull spans them.
- Test: `TestSecondAxes::test_yscale2_range_widens_only` (`range(0 20000)` beside price
  3291-15906: hull `(0, 20000)`; `range(5000 6000)`: hull the data's),
  `::test_ylabel2_positions_widen_y2`, `::test_norescale_on_ylabel2`,
  `::test_yscale2_reverse_swaps`.
- Test: `TestByPanels::test_by_with_range_0_gives_every_panel_one_hull` — `by(foreign)
  yscale(range(0))`: every panel `Range1d` with the same start and end, hull `(0, 41)`.
- Test: `TestComputedLayers::test_a_fit_beside_a_scatter_with_range_0` — y hull spans the
  fit's drawn values; the x range's renderers are the scatter's in both modes.
- Test: `TestBars::test_a_bar_keeps_its_outer_half_width` — `bar` with `xscale(range(0))`:
  the x hull's high end is the last bar's `x + width/2`, not `x`.
- Test: `TestPrimaryRenderersInBothModes::test_the_served_datarange_is_limited_like_the_saved_one`
  — `(scatter)(lfit)`, no scale option: `len(fig.x_range.renderers)` equal in both modes.
  Pre-fix: served `"auto"`.
- Test: `TestPrimaryRenderersInBothModes::test_the_parity_profile_records_renderers_and_direction`
  — `tp._axes(fig)["x_range"]` has `renderers` and `reversed`.
- Test: `TestTheHelpers::test_range_hull_inverts_padded_range[kind,reverse]`,
  `::test_range_reversed`, `::test_axis_hull_returns_none_without_an_explicit_value`.
- Test: `TestAgainstTwoway::test_every_probe_contains_its_requested_hull` — for each `b2_*`
  probe: `findings.range_rule.per_probe[id].contains_requested` is true and dash's hull for
  the same command equals the probe's `requested` (both modes).
- Test: `TestAgainstTwoway::test_dashs_hull_is_statas_inner_hull_where_ticks_stay_inside` —
  for probes with `stata_inner_is_requested`, dash's hull equals `stata_inner` within 1e-3 of
  the span.
- Test: `TestAgainstTwoway::test_norescale_probes_were_not_widened_by_twoway` and
  `::test_the_graph_scale_verdict_is_recorded` (the key exists and names one of the four
  answers; the test prints it so the answer is in the log).
- Flips: the list under "Tests that pin today's behaviour".

**Mutation table** (apply, see the named test fail, revert):

| break this | test that must die |
|---|---|
| in `_dash_axis_hull`, drop the data `lo`/`hi` | `test_range_20_30_never_narrows` |
| in `_dash_axis_hull`, ignore `_dash_norescale` | `test_norescale_draws_the_labels_and_keeps_the_extent` |
| in `_parse_scale_range`, keep `parts[:2]` | `test_any_count_in_any_order[range(0 50 100)]` |
| in `_dash_padded_range`, pad in linear space on log | `test_a_log_hull_is_padded_in_log_space` |
| in `_dash_finish_count_ticks`, place `#N` over data only | `test_hash5_with_range_100_ticks_over_the_widened_scale` |
| call `_dash_limit_ranges_to_primary` in the saved renderer only | `test_the_served_datarange_is_limited_like_the_saved_one` and the corpus |
| skip the bar half-width | `test_a_bar_keeps_its_outer_half_width` |
| drop the common hull in `_dash_common_count_ticks` | `test_by_with_range_0_gives_every_panel_one_hull` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| label/tick values widen; `norescale` | pytest `test_axis_extents.py` | `axis_truth.json` (`b2_extent`) | yes |
| `range()` widens only; `r()`, `rev`, `.`, order, count, bad value | pytest | same | yes |
| log, date, degenerate, reverse | pytest | same | yes |
| `#N` over the widened scale | pytest, `test_natscale*.py` | `natscale_truth.json`, `axis_truth.json` | yes |
| second axes | pytest, `test_dual_axis.py`, `test_help_claims_7.py` (flipped) | — | yes |
| by() common hull | pytest, `test_natscale_axes.py::TestByPanelsShareOneScale` | — | yes |
| primary-renderer limit and direction in the profile | pytest, `test_mode_parity.py` corpus | — | yes |
| twoway's extents live, five cases; `.Graph` verdict | cscript `test_axis_extents.cscript` AE-01..AE-06 | fixture cross-check | saved page |
| copy lists, function map | `TestTheServedAppCarriesEveryName`, `test_function_test_map.py` | — | served |

Acceptance criteria:

- **AC-18.1** `ylabel(0(20)100)` on mpg spans 0 to 100 (plus the pad) in both modes; with
  `norescale` the labels are drawn and the extent is the default's.
- **AC-18.2** `yscale(range(100))` runs 12 to 100 upward; `range(20 30)` equals the default;
  `range(0)` reaches 0 with the pad at both ends; `r(0 100)`, `rev`, `range(. 60)`, `range(100
  0)`, `range(0 50 100)` are honoured with no note; `range(abc)` is named once.
- **AC-18.3** Log axes hull in log space, date axes in milliseconds, a degenerate hull is
  widened, reverse is start above end; `#N` ticks sit over the widened scale.
- **AC-18.4** `yscale2`/`xscale2`/`ylabel2`/`xlabel2` follow the rule; by() panels share one
  hull.
- **AC-18.5** Every `b2_extent` probe's fixture verdict `contains_requested` is true; dash's
  hull equals Stata's inner hull wherever twoway's ticks stayed inside the requested hull; the
  `graph_scale_matches_svg` verdict is recorded.
- **AC-18.6** Both modes give the same extent, limit autoranges to the same renderers, and the
  parity corpus agrees on the two new profile fields.
- **AC-18.7** The cscript's five live cases pass with 0 SKIP; the full pytest suite is green
  under both interpreters; BUGS.md, dash.sthlp 2333-2335 and CHANGELOG are updated.

## Tasks

Commit boundary: **one commit (B2)** holding 18-01 to 18-11, with 18-01's failure summary in
the message; the full pytest suite runs green once before it (CLAUDE.md rules 4 and 11). No
AI references anywhere.

<task type="auto" id="18-01">
  <name>Write the failing tests for the extent rule</name>
  <files>test/test_axis_extents.py</files>
  <action>
    Create `test/test_axis_extents.py`. Module docstring in CHANGELOG terms: `ylabel(0(20)100)` on mpg 12-41 drew the axis to 42 and never showed 60-100; `yscale(range(100))` drew 100 down to 41; `range(20 30)` hid the data outside; `range(0)` ended at the maximum; `r()` and `rev` were named; `norescale` was named; the served app autoranged over a fit's extended grid where the saved page did not. Copy the header and `_figures` helper of `test_natscale_axes.py` (312-339), the `_auto()` frame of `test_axis_options.py`, `test_served_dates.py`'s %td frame builders for the date cases, and import `test_mode_parity as tp` for the profile test. Add the `truth()` fixture that `pytest.fail`s ("task 18-02 must land first") when `b2_extent` is absent. Write every stub of "TDD test stubs" with exactly those names; the hull assertions call `dr._dash_range_hull` (which does not exist yet — those tests fail with `AttributeError`, the behavioural ones with wrong numbers: keep both kinds). Do not edit `dash_render.py` or any existing test. Run the file and keep the summary.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_extents.py -q 2>&1 | tail -5` shows 0 passed and no collection error; `python3 -m pytest test/test_axis_extents.py -q -k "range_100_widens" 2>&1 | grep -c "100"` is non-zero (the inverted start is in the failure text).]]></verify>
  <done>`test/test_axis_extents.py` exists, collects, and every test in it fails for the reason its stub names.</done>
</task>

<task type="auto" id="18-02">
  <name>Record twoway's extents and the .Graph candidates</name>
  <files>scripts/extract_axis_truth.do, test/fixtures/axis_truth.json</files>
  <action><![CDATA[
    Register the 25 `b2_extent` probes of "Stata truth" (compound-quote the `ylabel(0 "zero" 60 "sixty")` option; `sp500` and `by()` as noted). Load Section 02's programs at the top as "Stata truth" says (`cd "${ZA_REPO}/test"`, `quietly do "cert_svg.do"`, `cd` back). In the export loop, after a probe draws with rc 0, call `cert_graph_scale, axis(y)` and, for x probes, `axis(x)`, read `r(min) r(max) r(curmin) r(curmax) r(major_min) r(major_max) r(major_delta)` into locals at once, and for `b2_by_range0` read `.Graph.graphs[1]`/`[2]`'s `plotregion1.yscale` members; append all of them to the PROBE record line as `gs_y_min|gs_y_max|gs_y_curmin|gs_y_curmax|gs_y_major_min|gs_y_major_max|gs_y_major_delta|gs_x_...` (blank where not read). Add `close date` to the data-facts list for `sp500`. In the `python:` block implement the per-probe fields and the two findings of "Stata truth" (`requested`, `drawn_ticks`, `stata_inner`, `inner_from_margin`, `graph_scale`, the four verdicts, `findings.range_rule`, `findings.graph_scale_matches_svg`); use `svg_axis_extent(svg, axis, ticks)` when `ticks` is given, mapping its `low`/`high` onto `axis_low`/`axis_high` and catching `ValueError`/`None` as "Stata truth" says. Run Stata from `/tmp/dash-s18` with `STATATMP=/tmp/dash-s18/tmp/`, read `probe <id> rc=` lines, then `git add -f test/fixtures/axis_truth.json`.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -c "import json; d=json.load(open('test/fixtures/axis_truth.json')); f=d['findings']; print(f['graph_scale_matches_svg']['verdict'], f['range_rule']['all_contain_requested'], f['range_rule']['norescale_not_widened'], d['probes']['b2_range_100']['y_axis']['mapping'])"` prints a verdict, `True True` and an extent reaching past 100; `git ls-files test/fixtures/axis_truth.json` prints the path; `python3 -m pytest test/test_axis_options.py -q 2>&1 | tail -2` stays green.]]></verify>
  <done>The fixture records twoway's drawn extent, inner hull, requested hull and the four .Graph candidates for every B2 case, with a verdict on which candidate matches the SVG, produced by Stata and committed.</done>
</task>

<task type="auto" id="18-03">
  <name>Read range() as values to include</name>
  <files>dash_render.py, test/function_test_map.py, test/test_html_output.py</files>
  <action>
    Implement TR-18.1 to TR-18.3: `_parse_scale_range` returns the expanded list (rightmost `range()`, prefixes of `range`, `.` ignored, non-numbers named once through `_dash_warn_once`); add `_dash_scale_name`; `_dash_scale_spec` matches canonical names and returns `values` beside `lo`/`hi`; `_DASH_SCALE_SUBOPTS` and `_DASH_SCALE2_SUBOPTS` are compared by canonical name; `_dash_apply_scale_ranges` stores `fig._dash_scale_values` and `fig._dash_scale_reverse` and keeps only the `flipped` write (document the unused frame arguments). Update the docstrings that describe the old behaviour (2409-2422, 19017-19024). Add `_dash_scale_name` to the copy list and the function map. Flip `test_html_output.py::TestXrangeYrange`: the two "embeds" tests assert a `Range1d` whose start is below −37 / 0 and end above 99 / 9999 and whose `_dash_range_hull` is `(−37, 99)` / `(0, 9999)` (read `start`/`end` from the attrs; `_figure_models` omits a default start of 0 — the padded start is never 0 here); the two "invalid" tests keep the `DataRange1d` assertion and add "one warning naming the value". Note: until 18-05 lands, a `range()` produces no `Range1d` at all — these flipped tests stay red until then.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_extents.py -k "TheReader or non_number" -q 2>&1 | tail -3` is green; `python3 -c "import dash_render as d; print(d._parse_scale_range('log r(100 . 0,50)'), d._dash_scale_spec('rev r(3)')['reverse'])"` prints `[100.0, 0.0, 50.0] True`.]]></verify>
  <done>`range()`, `r()`, `rev`, single values, missing values and any count are read as Stata reads them, recorded on the figure, and nothing narrows a range before the layers.</done>
</task>

<task type="auto" id="18-04">
  <name>Honour norescale on labels and ticks</name>
  <files>dash_render.py</files>
  <action>
    Implement TR-18.4: add `norescale` to `_dash_parse_axis_spec`'s honoured tuple (Section 14 already reads it through `_dash_axis_head_split`'s tail; keep the tuple in one place) with `out["norescale"]`; in `_dash_apply_axis_spec` set `_dash_norescale` on every axis the spec is applied to (iterate the splattable list or the single axis); in `_dash_apply_tick_option` honour `norescale` (it is neither named nor in `bad`) and set `_dash_tick_norescale` on each axis it tickers. Underscore attributes only; nothing serialised.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_suboption_warnings.py test/test_axis_options.py -k "Grammar or Honoured or Quiet" -q 2>&1 | tail -3` is green and `python3 -c "import dash_render as d; s=d._dash_parse_axis_spec('0(20)100, norescale'); print(s['norescale'], s['unsupported'])"` prints `True []`.]]></verify>
  <done>`norescale` is honoured in silence on xlabel/ylabel/xlabel2/ylabel2 and xtick/ytick, and the axes carry the flag the hull reads.</done>
</task>

<task type="auto" id="18-05">
  <name>Add the hull step after the layers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Implement TR-18.5 to TR-18.10: `_dash_count_axes(fig, every_axis=False)` with `letter`/`name` in each entry; `_dash_axis_hull`, `_dash_padded_range`, `_dash_range_hull`, `_dash_range_reversed`, `_dash_hull_ranges` (new, placed between `_dash_place_count_ticks` and `_dash_finish_count_ticks`); the new body of `_dash_finish_count_ticks` (count ticks over data ∪ scale values, then the hull); the Range1d common branch of `_dash_place_count_ticks` widened to `d_lo`/`d_hi`; the common hull in `_dash_common_count_ticks`. Bar half-widths: read `VBar.width`/`HBar.height` as a number or a column through the same view rows `_dash_secondary_values` uses. Add the five new functions to the copy list and the function map (tests from `test_axis_extents.py`). Rewrite the docstrings of `_dash_finish_count_ticks` and `_dash_place_count_ticks` to say what they do now.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_extents.py -k "Widen or RangeOnly or LogAndDate or Reverse or CountTicks or ByPanels or Computed or Bars or Helpers or Twoway" -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_natscale.py test/test_natscale_axes.py test/test_html_output.py -k "Ticks or Panels or Xrange" -q 2>&1 | tail -3` is green.]]></verify>
  <done>Every axis with an explicit position or range() value spans its hull with the 5% pad, in log and date units, reversed on request, shared across by() panels, in both modes; an axis without one is untouched.</done>
</task>

<task type="auto" id="18-06">
  <name>Apply the rule to the second axes</name>
  <files>dash_render.py, test/test_dual_axis.py, test/test_help_claims_7.py</files>
  <action>
    Implement TR-18.12 in `_dash_finish_secondary_axes`: parse the `{n}label2` spec before the range is set, build the hull from the drawn values, the `range()` values (`_parse_scale_range`) and the label positions unless `norescale`, write it with `_dash_padded_range` (log when the axis is a `LogAxis`; reverse from the canonical names), then apply the label spec as before. Flip `test_help_claims_7.py::test_yscale2_log_reverse_and_range`'s last assertion to `dr._dash_range_hull(rng) == (0.0, 20000.0)`; in `test_dual_axis.py` re-run `TestSecondaryAxisSetup` and `TestSecondaryAxisOptions` and adjust only an assertion that reads an exact bound (none is expected to; record "verified, no flip" in the commit message if so).
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_extents.py -k SecondAxes test/test_dual_axis.py test/test_help_claims_7.py -k "yscale2 or Second or Lone" -q 2>&1 | tail -3` is green.]]></verify>
  <done>`yscale2()`/`xscale2()` widen only and `ylabel2()`/`xlabel2()` positions widen the second axis unless norescale, padded and reversed by the shared helpers.</done>
</task>

<task type="auto" id="18-07">
  <name>Share the primary-renderers limit and show it in the profile</name>
  <files>dash_render.py, test/test_mode_parity.py</files>
  <action>
    Implement TR-18.11: add `_dash_limit_ranges_to_primary(fig, source)` at module level beside `_dash_keep_primary_ranges` (17181), with the block's comment moved into its docstring; replace 22314-22330 with a call; in the served template insert `"        _dash_limit_ranges_to_primary(fig, src)",` immediately before the `_dash_keep_primary_ranges(fig)` line (26402) with a one-line comment; add the function to the copy list and the function map. In `test_mode_parity.py::_axes.rng` add `"renderers"` and `"reversed"` as TR-18.11 states, then run the whole corpus: every case must agree; a case that disagrees is a served/saved difference this task exists to remove — fix the code, never the profile.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_extents.py -k PrimaryRenderers test/test_mode_parity.py -k "same_axes" -q 2>&1 | tail -3` is green; `grep -n "_dash_limit_ranges_to_primary" dash_render.py | wc -l` prints at least 4 (definition, saved call, template line, copy list).]]></verify>
  <done>Both renderers limit their autoranges to the graph's primary-source renderers through one function, and the parity profile records the limit and the direction for every corpus case.</done>
</task>

<task type="auto" id="18-08">
  <name>Flip the pinned range tests</name>
  <files>test/test_axis_options.py, test/test_graph_options.py, test/test_server.py</files>
  <action><![CDATA[
    `test_axis_options.py::TestAxisScale`: rewrite the three narrowing assertions as TR-18.15 says, each with a one-line docstring citing axis_scale_options.sthlp:336-341 ("range() never narrows"); `test_server.py::test_yscale_range_bounds_the_y_axis_in_both_modes`: `bounds` become `lambda df: (10.0, float(df["mpg"].max()))` and `(0.0, float(df["mpg"].max()))`, compared through `dr_module._dash_range_hull(fig.y_range)` at `pytest.approx`, and the two modes' `(start, end)` asserted equal to each other; `test_graph_options.py::TestXscaleYscaleReverse`: run it — if green, add `test_reverse_with_a_range_is_start_above_end` beside it (a `_get_figure({"yscale": "reverse range(0 50)"})` whose range is a Range1d with `start > end`); if any case is red, flip it to `dr._dash_range_reversed`.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_options.py test/test_graph_options.py test/test_server.py -k "Scale or Reverse or yscale_range" -q 2>&1 | tail -3` is green.]]></verify>
  <done>The tests that pinned exact narrowing now pin the widening rule, and reverse beside range() is pinned.</done>
</task>

<task type="auto" id="18-09">
  <name>Flip the date-range tests and verify the tick suites</name>
  <files>test/test_served_dates.py, test/test_natscale_axes.py</files>
  <action><![CDATA[
    `test_served_dates.py`: `test_xscale_range_in_every_unit` asserts `Range1d`, `start < ms < end` and both modes equal; `test_xscale_range_on_a_td_axis` asserts `dr._dash_range_hull(fig.x_range) == (_MS[0], _MS[3])` at `pytest.approx(abs=1)`; `test_one_range_bound_keeps_the_datas_other` asserts the hull's low end is the data's first date (14979 lies inside the four dates) and that the axis was not narrowed to it — rename it `test_one_range_value_inside_the_data_changes_nothing`, keeping the old name in its docstring. Run `test_natscale_axes.py` and `test_natscale.py` whole; they should be green unchanged (no explicit values); if a case is red, the hull touched an axis without an explicit value — fix `_dash_axis_hull`, not the test.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_served_dates.py test/test_natscale_axes.py test/test_natscale.py -q 2>&1 | tail -3` is green.]]></verify>
  <done>Date-axis range() tests pin the widening rule in milliseconds, and the natscale suites pass unchanged.</done>
</task>

<task type="auto" id="18-10">
  <name>Certify five extents against twoway live</name>
  <files>test/test_axis_extents.cscript, test/run_all_cscripts.do</files>
  <action><![CDATA[
    Create `test/test_axis_extents.cscript` (`*!` index; `cscript`; `global dash_nobrowser 1`; `quietly do "cert_helpers.do"` and `quietly do "cert_svg.do"` from `test/` before any `cd`, as Section 02 prescribes — `cert_svg.do` exits 222 itself when `c(python_exec)` is empty; `_ae_ok` PASS/FAIL helper). AE-01..AE-05, for `ylabel(0(20)100)`, `yscale(range(100))`, `yscale(range(20 30))`, `yscale(r(0 100))`, `ylabel(0(20)100, norescale)` on `sysuse auto` `scatter mpg weight`: `cert_svg_export, file()` the twoway graph, then `cert_svg_extent, file() axis(y) [values(0 20 40 60 80 100)]` and assert `r(low)`/`r(high)` equal the fixture's `axis_low`/`axis_high` at rtol 1e-3 (the fixture is not stale; AE-05 may return `r(reason)` — then compare `cert_graph_scale`'s candidate the fixture verdict names), then `dash scatter mpg weight, <option> name(aeN)` + `dash build, saving()` and one `python:` block that reads every `Range1d`'s `start`/`end` from the page's embedded document JSON with a regex (measure the spelling once on AE-01: `"name":"Range1d"` … `"attributes":{"start":…,"end":…}`), computes the hull as `_dash_range_hull` does, and asserts it equals the fixture's `requested` (AE-05: no `Range1d` on y at all). AE-06: `cert_graph_scale, axis(y)` on AE-02's graph equals the fixture's `graph_scale` and the recorded verdict names the matching candidate. Register in `run_all_cscripts.do`.
  ]]></action>
  <verify><![CDATA[`cd /tmp/dash-s18 && STATATMP=/tmp/dash-s18/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_axis_extents.cscript && grep -c " PASS" test_axis_extents.log` prints 6 and `grep -c " FAIL\| SKIP" test_axis_extents.log` prints 0; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -2` is green.]]></verify>
  <done>A registered certification script proves live that twoway's extents match the fixture and that dash's page spans the requested hull for five cases, and records the .Graph verdict.</done>
</task>

<task type="auto" id="18-11">
  <name>Close B2 in BUGS.md, help and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append a closed BUGS.md entry `- [x] Title: Label/tick values do not widen the axis; xscale/yscale(range()) narrows or inverts it (GAPS2 B2)` naming `test/test_axis_extents.py::TestRangeOnlyWidens::test_range_100_widens_up_and_never_inverts` and `test/test_axis_extents.cscript` AE-02, and stating the `.Graph` verdict the fixture recorded. Rewrite dash.sthlp 2333-2335: label and tick values widen the axis unless `norescale`; `xscale(range())`/`yscale(range())` widen the axis to include every value listed and never narrow it, `r()` is the abbreviation, one value is one value, missing values are ignored; and 2431-2432 for `yscale2()`/`xscale2()` (`rev`, `r()`, widen only). In CHANGELOG.md under `### Results that change` add the B2 item with before and after for each measured command (`yscale(range(100))`: 100 to 41, now 12 to 100 with the margin; `range(20 30)`: 20 to 30, now the data's; `ylabel(0(20)100)`: 12 to 41, now 0 to 100; `range(0)`: ended at 41, now padded; `r()`, `rev`, `norescale`: named, now drawn) and one sentence that an axis with an explicit label, tick or range value is now a fixed range that holds across filter moves; note under `### Fixed` that the served app now limits its autoranges as the saved page does (WP-28). Grep the three files and the message for `claude|anthropic`; pull local main; run the full suite once (`python3 -m pytest test/ -q`); commit the whole section on `s3-bugs`; report `git checkout main && git merge s3-bugs` without running it.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_7.py -q 2>&1 | tail -2` is green; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>B2 is closed in BUGS.md naming its tests, the help states twoway's rule, CHANGELOG lists every changed picture, and one commit on s3-bugs carries the section with a green full suite.</done>
</task>

<task type="checkpoint" id="18-12">
  <name>Verify extents in both modes and both interpreters</name>
  <files>none</files>
  <action>
    Run the full pytest suite under the development Python and under Stata's (`make test`), then the certification suite (`make cert`, scratch directory, `STATATMP`), and confirm 0 failed, 0 skipped, `test_axis_extents.cscript` 6 PASS. Open the saved page and the served app for `dash scatter mpg weight, ylabel(0(20)100) yscale(range(. 120))` and for `(scatter mpg weight)(lfit mpg weight), by(foreign) yscale(range(0))`; read the y extents. Present the commit hash, the `.Graph` verdict from the fixture, and the merge command.
  </action>
  <verify>Both suite runs report 0 failed and 0 skipped; the maintainer confirms the axes read 0 to 120 and 0 to the common maximum in both modes.</verify>
  <done>Section 18 is verified end to end, its commit is ready to merge, and the .Graph question is answered in the fixture.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" passes in both modes; every listed pinned test is flipped or
  recorded as "verified, no flip" in the commit message; none deleted.
- `axis_truth.json` holds the `b2_extent` group with `findings.range_rule` and
  `findings.graph_scale_matches_svg`, produced by Stata and committed;
  `test_axis_extents.py::TestAgainstTwoway` reads them.
- `test_axis_extents.cscript` is registered and passes with 6 PASS, 0 SKIP.
- `_dash_scale_name`, `_dash_axis_hull`, `_dash_padded_range`, `_dash_range_hull`,
  `_dash_range_reversed`, `_dash_hull_ranges`, `_dash_limit_ranges_to_primary` are in the copy
  list and `function_test_map.py`; the served template calls the limit and the parity profile
  records `renderers` and `reversed`.
- The full pytest suite is green under both interpreters with no skip; the cert suite passes.
- BUGS.md has the closed B2 entry; dash.sthlp 2333-2335 and 2431-2432 and CHANGELOG are
  updated; one commit on `s3-bugs`, no AI references.

## Notes

- **Order inside `_dash_finish_count_ticks` is the whole design:** count ticks over data ∪
  range values first, the hull last; `_dash_common_count_ticks` repeats both for by() panels.
  Putting the hull first would place `#N` over the data alone (mutation row 5).
- **Renderer order differs** (report A §0.2): the saved renderer adds second axes after the
  title styling, the served template before; both call `_dash_finish_secondary_axes`,
  `_dash_keep_primary_ranges` and `_dash_finish_count_ticks` in the same order after the
  layers, and the new limit call goes immediately before `_dash_keep_primary_ranges` in both.
- **Line numbers drift.** Section 14 adds about 150 lines near 16041 and 200 near 18745; every
  anchor here is also a symbol. Locate by `def`.
- **A Range1d has no `flipped`.** Reverse is start above end; `_dash_place_count_ticks` already
  handles `a0 > a1`; `_dash_range_reversed` is the one reader.
- **Bar widths.** `_dash_secondary_values` reads coordinate columns only; without the half-width
  the last bar is cut in half under `xscale(range(0))`. `Quad` (histograms) already gives
  `left`/`right`.
- **The margin is not Stata's.** Compare inner hulls, never extents; the fixture's
  `inner_from_margin` is there for the cscript's sanity check, `stata_inner` for the rule.
- **`.Graph` is probed once.** Whatever `graph_scale_matches_svg` says, the SVG is the truth;
  the verdict goes into the BUGS.md entry so nobody probes again.
- **Copy lists.** A new module-level name used inside a copied function is a `NameError` in
  the served app at draw time (`TestTheServedAppCarriesEveryName`).
- **Parity profile.** Adding `renderers`/`reversed` makes every corpus case compare them; the
  only legitimate way to green is the shared limit (18-07). Do not add an `ALLOWED` entry.
- **Fixture and Stata rules.** `git add -f` the JSON; the `python:` block never calls Stata;
  `\x60` for a backtick; `STATATMP=<dir>/tmp/` with the trailing slash; at most three Stata
  sessions; a run of skips means `python_exec` was dropped from `~/.stata19/console/stata19.rc`
  — restore with `set python_exec /opt/anaconda3/bin/python3, permanently`; a skip is not a
  pass. `global dash_nobrowser 1` right after the `cscript` line.
- **`range()` names its junk once.** `test_xrange_invalid_ignores_gracefully` asserted only
  the range type; one warning is new and deliberate (an unhonoured value is named, Q22).
