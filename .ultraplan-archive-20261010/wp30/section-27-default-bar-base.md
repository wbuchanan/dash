# Section 27: twoway's default base and axis extent (P1.17 part b)

> Part of: WP-30 · Items: P1.17 part b (entry P1.17b) · Risk: yellow · Batch: 9 · Depends on: 14, 21 · Blocks: 35, 57 · Tasks: 10, 1 commit · Case prefix: DB

## Review amendments

- Fixed (blocker): S27 was written before S21's text existed and bound the wrong forms. Now bound to section-21: `_dash_refinish_axes(figures, facet_map)` (not `(figs, rescale)`), which already reaches both Python hooks and is not edited; `_dash_hull_entries` keyed `(name, letter)` for every range; `_dash_share_by_scales` loses its y2/x2 block in S21. Evidence gains "S21's planned form".
- Fixed (blocker): the saved JS twin read renderer tags from a renderer list S21 never gives the JS (S21's `_dash_axis_plan` passes `layers` of source indexes and fields). The fill is now fed by two plan keys S27 adds to `_dash_axis_plan` (`autobase`, hull-only `bases`), built in Python from `_dash_base_spec`; the page parses no tag. TR-27.11, TR-27.14, TR-27.15, 27-05, 27-07 and AC-27.6 follow.
- Fixed (major): S21's D7 a marker is named (`_dash_auto_base`, stamped by `_dash_tag_hull_roles`, skipped by `_dash_layer_extent` and `_dash_secondary_values`); 27-05 retires it for the tag and flips S21's `TestTheHelpers::test_hull_roles` base ids in place (added to the pin list, 27-05's files and 27-10's staging).
- Checked at `c96facd`: the four mappers' base lines (:10223-10233, :10074-10081, :10339-10346, :13443-13444), `"base"` read only there, `_DASH_Y_COORDS` :23111, `_dash_secondary_values` :23117, `_dash_count_axes` :23345, `_dash_axis_hull` :23565, `_dash_hull_ranges` :23674 (`_dash_hull_entries`), `_dash_finish_count_ticks` :23732, `_dash_common_count_ticks` :23775 with its end :23829-23833, the y2 block :23903-23910, served call sites :35430/:35653, `_live.data` :36030, copy-list anchor :33251: all as quoted. Note `_dash_count_axes` entries already hold a `"base"` key (the axis option's); S27's new key is `"bases"`, distinct.
- Checked: batch 9. S27 is the batch's one finisher editor (R11); it edits no `_generate_app_source`, `_make_figure_body`, `map_function` or empty-layer helper, so it shares no function with S25 or S26. Parity cases append after S26's (R8). Tracking forms match section-01 (title, `Results that change`, stub header, subject).
- Rejected: "M6 forbids the base move" — the base is drawn, not noted; nothing is printed (BR-27.9).
- (cross-file pass) 27-10 verify: added the key-deletion check `grep -c '^    "P1.17b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:121-127 (P1.17) lists two bullets that are this section's: "bar's base is 0, not `twoway`'s rule" and "When 0 is outside the data, area, bar, spike and dropline draw from 0 and extend the axis to it." GAPS2 A3 (GAPS2.md:145-172) records it as: "With no `base()`, dash starts bars at 0, where twoway applies its own base rule." TWOWAY_COVERAGE_AUDIT.md says "default base differs" for area (:63), bar (:64), spike (:65) and dropline (:66), and "baseline behavior differs" under fill/bar styling (:115). dash.sthlp:2360-2362 documents the difference: "With no {cmd:base()}, when 0 lies outside the range of y, {cmd:twoway} draws them from the edge of the plot region and its axis does not reach 0; {cmd:dash} draws them from 0."

Measured at `c96facd` (this file's probes under Evidence; research `.ultraplan/wp30/research/p1-17.md` §2-§3 and "Critic additions"):
- With no `base()`, all four types draw from 0 in both modes. `bar` writes `bottom=0`; `spike` and `dropline` write a `y0` column of 0; `area` writes a `<y>_base` column of 0.
- The 0 extends the axis. For y from 10 to 14, the saved page's y range settles at [-0.7, 14.7] in Chrome for all four types. twoway draws from 10, on a scale of [10, 14].
- On a log axis the bars are drawn from 0, and the y range settles at [0.111, 17.625] in Chrome. twoway draws from 10, on [10, 14].
- On a date y axis the base is 0 ms, which is 01jan1970. twoway's 0 is 01jan1960, and twoway clamps it to the scale's low end anyway.
- An explicit `base(5)` is read as a tick input: `bar ypos x1, base(5) ylabel(#5)` ticks 4(2)14 in dash. twoway ticks 10(1)14 on a scale of [5, 14].

twoway's rule, measured on StataNow 19.5 from its own class values (`.plot#.drawn_base`, `.plotregion#.yscale.curmin/curmax`): with no `base()`, the base is 0 clamped into the axis's finished scale `[curmin, curmax]`. The scale is computed without the default base, from every layer's values, the natscale ticks and any `range()` or label values. An explicit `base(#)` is part of the scale but not of the tick input. Under `by()` the panels share the common scale's base; under `yrescale` each panel has its own. A `yaxis(2)` layer takes its base from the second axis.

**After this section** both modes draw every default base where twoway draws it, before and after any filter move. With no `base()`, `bar`, `spike`, `dropline` and `area` write their base into a data column, and their renderer carries a `dash_base:` tag marking it as the default. `_dash_finish_auto_bases` fills that column with 0 clamped into the axis's finished, unpadded scale. On a log axis that gives the scale's lower end, so 0 never reaches a log axis. On a date axis 0 is 01jan1960 (`_dash_units_to_axis(0, kind)`).

The fill runs at four points:
- at build, at the end of `_dash_finish_count_ticks`, for every figure in both modes;
- at build, at the end of `_dash_common_count_ticks`, for `by()` panels in both modes;
- after a served filter move, at the end of S21's `_dash_refinish_axes`;
- after a saved filter move, in S21's `_DASH_AXIS_FINISH_JS`.

Every value reader leaves a base out of the tick input, and a default base out of the hull. An explicit `base()` stays in the hull, so it widens the scale but places no tick. A 0 outside the data therefore no longer extends the axis.

**Why one section, and why now.** These are sub-claims c and f of P1.17 (GAPS2-A3-c, A3-f, AUDIT-42). They need the finished axis scale in both modes and after every move, which is the machinery S21 (P1.3 part a, batch 7) builds. Register P1.3.7 and P1.17.2 are one decision. S21 drops default bases from its tick input and hull (D7 a). This section clamps the drawn base into the scale S21 computes. Between batch 8 and this landing, default bases stay out of the scale but are still drawn from 0, beyond the axis (IR-12). That state exists only on `wp30-p1`. S14 (P1.17a, batch 5) owns the widths and caps of the same mappers and does not touch `base`.

**Test order and commit rule (rule 7, D1).** There is one cycle and one commit, `(WP-30 P1.17b)`:
- **27-01** checks S21's contract on the batch-9 tree. It writes and runs the twoway-only extractor, writes the regression classes, runs them on the unmodified tree, and saves `<scratch>/27-P1.17b-failure.txt`. It never commits.
- **27-02** writes the DB truth block and amends HC6-23b. Both are red.
- **27-03** flips the pinned tests in place and appends the parity cases.
- **27-04 to 27-07** fix the mappers, the readers, the Python fill and the JS fill.
- **27-08** certifies, **27-09** updates the help, and **27-10** closes the entry and makes the one commit.

No test-only commit exists, and no commit is red.

### Section decisions (this file; binding on the executor)

- **D-27a. A default base is a tagged data column.**
  - With no `base()`, `map_bar`'s `bottom` becomes the reserved column `__dash_base` (`GlyphMapper._BASE_COL`). `map_spike`'s and `map_dropline`'s `y0` and `map_area`'s `<y>_base` stay columns; they are already columns.
  - An explicit `base(#)` stays as it is today: a value on `bar`, the same columns on the other three.
  - Why a column: the only write path in both modes is then `source.data`. The saved derived-copy loop and the served redraw both already carry a source's columns. The fill is testable under node (`test/js_runner.py`), and no BokehJS property-spec setter is involved.
  - Size: a default-base bar layer carries one more float column (8 bytes a row) in the page. spike, dropline and area already carry theirs.
- **D-27b. The marker is a renderer tag, as a string.**
  - The tag is `dash_base:` followed by compact JSON `{"auto":…,"letter":"y","prop":…,"zero":…}`. `prop` is the glyph property that holds the base (`bottom`, `y0` or `y1`). `letter` is the axis it lies on. `zero` is Stata's 0 in that axis's units.
  - Renderer `tags` reach the saved page, the served document and the page's script; a Python attribute would not. A string is used, not a dict, because Bokeh 3 sends a dict to BokehJS as a Map (the `_FILTER_JS` Map rule).
  - Both an explicit and a default base are tagged (`auto` false and true), so one reader serves both rules.
- **D-27c. No base is a tick input, and only an explicit base is in the hull.**
  - Measured (Stata truth B3-B5, B12): `bar ypos x1, base(5)` ticks 10(1)14 on [5, 14]; `base(20)` ticks 10(1)14 on [10, 20]; `area y12 x1, base(5)` ticks 10(10)40 on [5, 41].
  - If S21 already removed explicit bases from the tick input, the tests that pin this are guards, and the reader edit for it is a no-op.
- **D-27d. The scale is read from the unpadded hull record, never from the padded Range1d.**
  - `_dash_axis_scale(fig, letter, name)` reads the record S21's finishers keep: at `c96facd`, `fig._dash_hull_entries` (keys `("default", letter)`, `lo`, `hi`) and `fig._dash_secondary_hulls[name]` (`(lo, hi, kind, reverse)`).
  - S21's plot-region margin (S47's later inner box) therefore never moves a base, and twoway's base sits at curmin, inside the margin (research critic correction 5).
- **D-27e. Where the fill runs. Neither `_make_figure_body` nor `_generate_app_source` is edited.**
  - The call sites are the ends of `_dash_finish_count_ticks` (LOW) and `_dash_common_count_ticks` (CRITICAL; a two-line addition), which S21's `_dash_refinish_axes` reaches on a served move, plus a JS twin inside `_DASH_AXIS_FINISH_JS` fed by `_dash_axis_plan`.
  - A fill only at the end of `_dash_finish_count_ticks` would give each `by()` panel its own base, because that function runs once per panel before the panels are shared (research critic correction 2).
  - S25 is batch 9's `_generate_app_source` editor (R12). Both template call sites already exist: `_dash_finish_count_ticks` (dash_render.py:35430) and `_dash_share_by_scales` (:35653), whose last step is `_dash_common_count_ticks` (:23910).
- **D-27f. One reading of `base()` on all four types.** `GlyphMapper._base_value(options, layer)` decides:
  - No `base` key, an empty value, or `.` means the default, silently. `.` is S20's missing element of a per-series `base()` list (research p1-01 "Critic additions": "A `.` element in `base(10 .)` means the default").
  - Anything else is read by `_stat_option_float(options, "base", None, layer)`. A text or non-finite value in a hand-written spec is named by its note and takes the default base. Today that already happens on dropline; bar, spike and area take 0 silently.
  - dash.ado validates `base=num` (dash.ado:2035), so only a hand-written spec reaches this path.
- **D-27g. No scale, no write.** When `_dash_axis_scale` returns None (the axis holds no finite value), the column keeps the mapper's provisional zero, as today. Such a layer draws nothing visible.
- **D-27h. Dates.**
  - `zero` is `_dash_units_to_axis([0.0], kind)[0]` for the y variable's kind (`self.date_vars.get(yvar)`, as S14's D-14d reads x), and 0.0 for a non-date y.
  - The clamp puts it at the scale's low end for every date Stata can hold, so no bar runs to 1960 or 1970.
  - It equals twoway's 14997 in the fixture's `%td` case only once S44 (batch 15) gives `%td`-`%ty` axes twoway's tsnatscale scale. Until then dash's scale starts at the data's 15000, and DB-08 compares with dash's own scale. This is a recorded residual handed to S44.

## Risk: [yellow] — every default bar, spike, dropline and area dashboard changes look, and the fill extends S21's freshly landed finishers in both modes

**Why.**
- The base and the y extent change on every dashboard with one of these layers and no `base()` whose data stay on one side of 0. That is most bar charts of positive counts above the first tick (twoway draws mpg bars from 10, not 0).
- The fill must run after every scale change in both modes, or the saved page and the served app disagree after a move.
- The mappers are dispatched by name (`_dash_glyph_dispatch`, dash_render.py:28522-28537), so GitNexus resolves none of their callers.

**Risk factors.**
1. S21's finishers are being written in parallel with this plan, so their exact text is unknown here. This section depends on four of their properties (Evidence, "S21 contract").
2. `_dash_common_count_ticks` is CRITICAL (4 impacted), and `_dash_share_by_scales` (CRITICAL, 8) may need a three-line record (TR-27.10).
3. On the saved page, the derived-copy loop of `_FILTER_JS` brings back the build-time base on every move. In the served app, `_live.data = dict(_new.data)` (dash_render.py:36029-36030) brings back the redraw's provisional zero. Either becomes visible if the fill is skipped.
4. A 0 that reached a log axis would draw nothing, or break BokehJS's scale.
5. A tag read as code, or a property name taken from page JSON, would be an injection path.
6. Pinned tests assert 0 today: Evidence "Tests that pin today's behaviour".

**Mitigation.**
1. Task 27-01 checks the S21 contract with fixed greps and stops before any edit if it fails. The TRs bind the rule, not S21's line numbers.
2. Warn before editing (E4). The edits are appended calls only. `test_by_scales.py` and `test_by_scales_chrome.py` stay green.
3. `TestTheBaseAfterAMove` runs the page's own script under node and the served `_on_filter_change`. `TestTheSavedPageInChrome` reads the drawn base in a real browser after a slider move.
4. The clamp's lower bound is the hull's minimum, which S21 keeps above 0 on a log axis. `TestTheBaseOnALogAxis` asserts it in both modes.
5. `_dash_base_spec` accepts only `dash_base:` strings of at most 200 characters, holding a dict whose `prop` is one of six fixed names, whose `letter` is `x` or `y`, whose `zero` is finite and whose `auto` is a bool. The JS parses no tag: it writes only a column the build-time plan names, on a source in its own `axis_models`, after type and `hasOwnProperty` checks. Nothing is evaluated.
6. Each pinned test is flipped in place with a `Flipped:` line, and the red list is re-measured in 27-08 (R9).

## Dependencies

- **Depends on 14** (batch 5, landed).
  - S14 rewrote `map_bar`'s width code (`_bar_extent`, the `__dash_bar_xc`/`__dash_bar_w` columns on a period x) and moved `clean_source = ColumnDataSource(df)` below `_bar_extent`.
  - S27 adds its base column to the same `df` before that line and must not change `x` or `width` (S14 Notes, "For S27").
- **Depends on 21** (batch 7, landed). S21 provides:
  - `_dash_refinish_axes` (served, called from `_on_filter_change` after the live sources are written);
  - `_DASH_AXIS_FINISH_JS` (saved, run at the end of `_FILTER_JS`, with per-figure plans in the `build_dropdown`/`build_slider`/`build_range` CustomJS args);
  - every axis given a hull Range1d;
  - natscale ticks in the hull;
  - D7 a: default bases out of the tick input and hull.
- **Reads S20** (batch 7): per-series `base()` lists, whose `.` element is the default (D-27f).
- **Blocks 35** (batch 12): S35 reads an explicit `base(#)` in date units in the same four mappers, and draws a mixed date axis through a transform. It keeps S27's tag and `zero`.
- **Blocks 57** (batch 20): the served worker applies a redraw on the next tick. `_dash_finish_auto_bases` must run in that same tick, after the data copy (S57's audit names it).
- **Parallel batch 9:** merge order S25, S26, S27; S27 lands last (index Batch 9).
  - **Can run with S25:** its guard is in `_generate_app_source`'s header and in dash.ado and dash_setup. S27 edits none of these.
  - **Can run with S26:** S26 edits `map_function`, the `map_function` fallback mark read by `_dash_note_empty_layer`, and dash.sthlp:413-418. S27 edits none of these.
  - The three sections share no function, no copy-list anchor (S26's is `"_dash_function_points",` at 33126; S27's is S21's anchor after 33251) and no help paragraph.

## Evidence

All anchors are `c96facd`'s: dash_render.py has 37,689 lines and dash.sthlp 3,822. S01-S26 land first and shift the numbers; the symbols and the quoted text are authoritative.

### The four mappers write 0

`GlyphMapper.map_bar` (def :10122), dash_render.py:10223-10233:

```python
10223        # base() option sets the bar bottom; default 0
10224        base_val = 0.0
10225        if "base" in options:
10226            try:
10227                base_val = float(options["base"])
10228            except (ValueError, TypeError):
10229                pass
10232        _vbar_kwargs: dict = dict(
10233            x=xvar, top=yvar, bottom=base_val, source=clean_source,
```

`map_area` (def :10029), :10074-10081, then `fig.varea(x=xvar, y1=_y1_col, y2=yvar, …)` at :10087:

```python
10074        # base() option sets the lower boundary; default 0
10075        base_val = 0.0
10076        if "base" in options:
10077            try:
10078                base_val = float(options["base"])
10079            except (ValueError, TypeError):
10080                pass
10081        y1_base = np.full_like(y_arr, base_val)
```

`map_spike` (def :10311), :10339-10346; the Segment reads `y0="y0"` at :10355:

```python
10340        base_val = 0.0
10341        if "base" in options:
10342            try:
10343                base_val = float(options["base"])
10344            except (ValueError, TypeError):
10345                pass
10346        y0_base = np.full_like(x_arr, base_val)
```

`map_dropline` (def :13398), :13443-13444; its Segment reads `"y0": zeros`:

```python
13443        _base = _stat_option_float(options, "base", 0.0, "dropline")
13444        zeros = np.full_like(x_arr, 0.0 if _base is None else float(_base))
```

No other mapper reads `base`: `grep -n '"base"' dash_render.py` gives :10076, :10225, :10341 and :13443 only. The histogram's `bottom=0` (:12429) is not a `base()`. The mappers are dispatched at :28522 (area), :28523 (bar), :28524 (spike) and :28537 (dropline).

### The readers take the base as a drawn value

`_dash_secondary_values(fig, range_attr, name)` (:23117) reads every coordinate property in `_DASH_Y_COORDS = ("y", "y0", "y1", "y2", "top", "bottom")` (:23111). A field's values go to `column_values` (:23152-23161), and a constant goes to `all_values` (:23162-23168). So `spike`'s `y0`, `dropline`'s `y0` and `area`'s `<y>_base` are drawn values, and `bar`'s `bottom` is a constant:

```python
23149            field = (v if isinstance(v, str)
23150                     else v.get("field") if isinstance(v, dict)
23151                     else getattr(v, "field", None))
23152            if field:
23158                col = _dash_float_values(data[field], coerce=True)
23159                sel = col[list(rows)] if len(col) else col
23160                cols.extend(float(x) for x in sel if np.isfinite(x))
23161                continue
```

The other readers:
- `_dash_count_axes` (:23345) uses `all_values` as each axis entry's `lo`/`hi` (:23406-23415). Those values are the `#N` tick input (`_dash_finish_count_ticks`, :23757-23771) and the data part of `_dash_axis_hull` (:23565).
- `_dash_finish_secondary_axes` uses `all_vals` for the y2/x2 hull (:23250-23261) and records it in `fig._dash_secondary_hulls[name] = (lo, hi, kind, reverse)` (:23266-23271).
- `_dash_hull_ranges` records each primary hull in `fig._dash_hull_entries` (`key`, `letter`, `name`, `kind`, `lo`, `hi`; :23674-23729), also when `by()` passes `common=`.

### The finishers and their call sites

`_dash_finish_count_ticks(fig)` (:23732) ends with the hull. This is S27's first hook:

```python
23769        e["tick_lo"], e["tick_hi"] = lo, hi
23770        if lo is not None:
23771            _dash_place_count_ticks(e, lo, hi)
23772    _dash_hull_ranges(fig, entries)
```

It is called once per figure, after `_dash_finish_secondary_axes`, in both modes: saved at :30660 then :30679 (inside `_make_figure_body`); served at :35417 then :35430 (generated by `_generate_app_source`).

`_dash_common_count_ticks(figs, letters)` (:23775) ends with the shared hull (S27's second hook):

```python
23829        lo = min([h[0] for h in hulls] + data)
23830        hi = max([h[1] for h in hulls] + data)
23831        made: dict = {}
23832        for f, es in per.values():
23833            _dash_hull_ranges(f, es, common={hkey: (lo, hi)}, made=made)
```

It is the last statement of `_dash_share_by_scales` (:23910). That function is called by the saved `by()` path (:31669, in `_build_sources_and_figures`) and by the served template (:35653). Its second-axis block (:23897-23909) pads one Range1d over the panels' y2 hulls but does not write the union back to each panel's `_dash_secondary_hulls`:

```python
23903            if hulls:
23904                new = _dash_padded_range(min(h[0] for h in hulls),
23905                                         max(h[1] for h in hulls),
23906                                         hulls[0][2], hulls[0][3])
23907                for f in figs:
23908                    setattr(f, extra, {**getattr(f, extra), name: new})
```

The served redraw copies the redraw's data onto the live source (:36029-36030, `_live.data = _dash_keep_jitter(dict(_new.data), …)`), which brings the mapper's provisional value back. The saved page's derived-copy loop (`_FILTER_JS`, :18756-18781) rebuilds each derived source from its build-time snapshot.

The served functions tuple: `"_dash_count_of", "_dash_finish_count_ticks",` at dash_render.py:33251. S21 adds `"_dash_default_ticker", "_dash_plot_margin", "_dash_refinish_axes"` after it (R2), and S27's names go after S21's. The generated app imports `json` and `math` (`_generate_app_source`, :34044-34046).

### The S21 contract (checked by 27-01 at the batch-9 base)

S21's file is written in parallel with this one, so its text is not quoted here. S27 relies on four properties, all named in S21's manifest scope and in `index.md` A153/R11:
1. `_dash_refinish_axes(figures, facet_map)` exists, is copied into the served app, and runs from `_on_filter_change` after the live sources are written. It re-ticks, re-hulls and re-shares `by()` panels, including y2/x2.
2. `_DASH_AXIS_FINISH_JS` exists and runs at the end of `_FILTER_JS`. Each axis has a JS value reader (a port of `_dash_secondary_values`), a computed unpadded scale and a `by()` union, and the JS can reach every renderer drawn on that axis.
3. Every continuous axis's unpadded twoway scale is recorded per figure in both modes: at build, after a `by()` share, and after a served move. At `c96facd` this is `_dash_hull_entries` and `_dash_secondary_hulls`.
4. D7 a: default bases are out of the tick input and the hull.

If S21 recorded the scale elsewhere, or identified default bases by its own marker, 27-05 and 27-06 point S27's helpers at S21's form and replace S21's marker with the `dash_base:` tag. The rules of the TRs bind; the `c96facd` line numbers do not.

**S21's planned form (section-21 TR-21.7-TR-21.11, D-21g; binding unless 27-01 finds otherwise).**
- `_dash_tag_hull_roles(renderers, ptype, options)` stamps the Python attribute `_dash_auto_base` (the default base's glyph property) in both build loops; `_dash_layer_extent(renderers, range_attr, name, kind=None)` (the vectorised reader) and `_dash_secondary_values` skip those properties. That attribute is S21's D7 a marker.
- `_dash_finish_count_ticks(fig, refinish=False)`; `_dash_common_count_ticks(figs, letters)` covers every range name (keys `(name, letter)`); `_dash_share_by_scales` loses its y2/x2 block (`_dash_common_count_ticks` covers it); `_dash_hull_ranges` records every name.
- `_dash_refinish_axes(figures, facet_map)` runs `_dash_finish_count_ticks(f, refinish=True)` per figure, then `_dash_common_count_ticks(group, letters)`, so it already reaches both of S27's Python hooks.
- The saved JS gets no renderer list: `_dash_axis_plan(figures, facet_map, zoom=True)` (a module function, not inside `_build_filter_widgets`) writes, per panel per axis, `layers: [{"src", "filt", "fields", "consts"}]` with model indexes into `axis_models`; `_DASH_AXIS_FINISH_JS`'s `dash_axis_extent` reads those fields and consts. So the JS twin works from the plan (TR-27.11), and the plan builder is where the default bases are left out and the explicit ones become hull-only.

### Measured at `c96facd` (this file's probes, 03oct2026)

dash, both modes (`<scratch>/s27/head.py`: `test_date_range._spec`, `_saved`, `_served`; frame x1 = 1..5, ypos = 10..14, y12 = {12,25,33,41,18}, d = 15000 + 7k as `%td`):

```
bar ypos {}  | saved [('bottom', 0)] ('DataRange1d', nan, nan) | served [('bottom', 0)] ('DataRange1d', nan, nan)
bar y12 {}  | saved [('bottom', 0)] ('DataRange1d', nan, nan) | served [('bottom', 0)] ('DataRange1d', nan, nan)
spike y12 {}  | saved [('y0', 0.0)] ... | served [('y0', 0.0)] ...
dropline y12 {}  | saved [('y0', 0.0)] ... | served [('y0', 0.0)] ...
area y12 {}  | saved [('y1', 0.0)] ... | served [('y1', 0.0)] ...
bar ypos {'base': '5'}  | saved [('bottom', 5.0)] ... | served [('bottom', 5.0)] ...
bar ypos {} {'yscale': 'log'} | saved [('bottom', 0)] ... | served [('bottom', 0)] ...
bar d {}  {'d': '%td'}| saved [('bottom', 0)] ... | served [('bottom', 0)] ...
```

Ticks with `ylabel(#5)` (`<scratch>/s27/ticks.py`, saved renderer):

```
bar y12 {} FixedTicker [0.0, 10.0, 20.0, 30.0, 40.0]          (twoway 10(10)40)
spike y12 {} FixedTicker [0.0, 10.0, 20.0, 30.0, 40.0]        (twoway 10(10)40)
area y12 {} FixedTicker [0.0, 10.0, 20.0, 30.0, 40.0]         (twoway 10(10)40)
bar ypos {'base': '5'} FixedTicker [4.0, 6.0, 8.0, 10.0, 12.0, 14.0] 4.0 nan   (twoway 10(1)14 on [5,14])
bar ypos {} FixedTicker [0.0, 5.0, 10.0, 15.0] nan 15.0       (twoway 10(1)14 on [10,14])
```

The saved page in headless Chrome (research p1-17 §2, `test/range_probe.RangeProbe`): `bar`, `area`, `spike` and `dropline` of ypos 10..14 settle at y [-0.7, 14.7]. `bar ypos x1, yscale(log)` settles at [0.111, 17.625] (critic `py/logprobe.py`).

### Tests that pin today's behaviour

Re-measured at `c96facd` by reading each test; the batch-9 base is re-measured in 27-01 and 27-08 (R9).

| Node | Today's assertion | After (flip or amend, in place) |
|---|---|---|
| test/test_glyphs.py::TestBarOptions::test_base_default_is_zero | `r.glyph.bottom == 0` (the mapper alone) | `bottom` is the field `__dash_base`, the column holds the provisional 0.0 for every row, and `_dash_base_spec(r) == {"prop": "bottom", "letter": "y", "zero": 0.0, "auto": True}` (red at base) |
| test/test_glyphs.py::TestAreaBase::test_base_default_is_zero | 74 zeros in `<y>_base` (the mapper alone) | the same zeros, plus the auto tag on prop `y1` (amended; red at base) |
| test/test_glyphs.py::TestSpikeBase::test_base_default_is_zero | 74 zeros in `y0` (the mapper alone) | the same zeros, plus the auto tag on prop `y0` (amended; red at base) |
| test/test_help_claims_6.py::TestDroplineBase::test_the_default_is_zero[saved], [served] | `y0 == 0.0` after a full render of `dropline mpg weight` | `y0 == 10.0`, twoway's `drawn_base` (fixture `auto.dropline`); node name kept |
| test/test_help_claims_6.py::TestBaseOnTheBarPlots::test_the_base_is_drawn_and_defaults_to_zero[<mode>-<layer>-] (the six `base=""` ids) | `want = 0.0` | `want = 10.0` (fixture `auto.<layer>`). `_bases` reads `bar`'s `bottom` field from the source when it is a field. The six `base="10"` ids stay green. |
| test/test_help_claims_6.cscript HC6-23b (:685-701) | twoway side only; its comment says "dash draws them from 0" | the comment is rewritten, and a dash-side check is added: dash's base equals twoway's curmin (17) for each of the four types `in 1/3` (27-02) |

Guards that stay green and are not edited:
- test_glyphs.py::TestMapDropline::test_dropline_segment_drops_to_zero (:799). The mapper alone writes the provisional 0.
- test_help_claims_6.py::TestDroplineBase::test_an_unusable_base_draws_from_zero (:405-414). The mapper alone gives the provisional 0, with warnings ignored.
- test_html_output.py::TestNewOptionHtml::test_bar_default_base_zero (:2020-2032). y = 1..20, so twoway's scale reaches 0 (natscale 0(5)20) and the base stays 0. `_values` reads a field (:264-280).
- test_glyphs.py's explicit-base tests (`test_base_changes_bar_bottom` and its area and spike siblings) and TestDroplineBase::test_the_drops_start_at_base.

S21's own tests pin the hull rule, not the drawing (IR-12). Any of them found asserting a drawn 0 is flipped by 27-03 with a `Flipped:` line. `test/test_default_axes.py::TestTheHelpers::test_hull_roles` (ids `bar`, `bar_base`, `area`, `spike`, `dropline`) reads S21's `_dash_auto_base` stamp, which S27 replaces; 27-05 flips those five ids in place to read `_dash_base_spec` (TR-27.7). `TestDefaultBasesStayOut` and `test_an_explicit_base_widens` stay green as guards.

### Blast radius (E4; recorded in `<scratch>/batch-9-impact.txt` at 9.0)

`gitnexus impact <symbol> -d upstream -r dash`, 03oct2026 at `c96facd`:

| Symbol | Risk | Note |
|---|---|---|
| `_dash_common_count_ticks` | **CRITICAL** (4 impacted, 1 direct) | Two appended lines at its end (TR-27.10). Warn before editing. |
| `_dash_share_by_scales` | **CRITICAL** (8) | Edited only if S21's tree does not record the shared y2/x2 hull per panel (TR-27.10): three lines in its second-axis block. Warn first. |
| `_dash_units_to_axis` | **CRITICAL** (15) | Called, not edited |
| `_stat_option_float` | CRITICAL (36; S14's measurement) | Called, not edited |
| `_dash_finish_count_ticks` | LOW (3) | One appended line. index Batch 9 lists it as expected HIGH/CRITICAL; re-run at 9.0. |
| `_dash_secondary_values` | LOW (5) | Skip of the tagged property |
| `_dash_count_axes` | LOW (3) | One new entry key |
| `_dash_axis_hull` | LOW (6) | Explicit bases joined to the hull |
| `_dash_finish_secondary_axes` | LOW (3) | Explicit bases joined to the y2/x2 hull |
| `GlyphMapper.map_bar`, `map_area`, `map_spike`, `map_dropline` | UNKNOWN (0 resolved) | Dispatched by name (:28522-28537) through `_dash_add_glyph`. Treat them as every bar, area, spike and dropline layer in both modes. |
| S21's `_dash_refinish_axes` (expected unedited), `_DASH_AXIS_FINISH_JS`, `_dash_layer_extent`, `_dash_axis_plan` and `_dash_tag_hull_roles` | measured at 9.0 | Not in the `c96facd` index; run impact at the batch-9 base and report |
| `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets`, the four appliers | — | **Not edited** (R12). If S21's plan builder lives inside `_build_filter_widgets` and needs an edit (TR-27.11), stop and report first. |

## User stories

- **US-27.1** As a twoway user, I want `dash bar mpg weight` to draw its bars up from 10, on an axis that stops at 10, as `twoway bar mpg weight` does, so the dashboard looks like my report.
- **US-27.2** As a twoway user, I want `dash spike`, `dropline` and `area` to start where twoway starts them when 0 is outside the data, so no empty band of axis reaches down to 0.
- **US-27.3** As a twoway user, I want `base(5)` to reach the axis without adding a tick, as twoway draws it.
- **US-27.4** As a dashboard publisher, I want a bar chart on a log axis, or of dates, to stand on the axis's lower end, never on 0 or 1970, so it draws at all.
- **US-27.5** As a dashboard publisher, I want `by()` panels to share one base on a common scale and have their own under `yrescale`, and a `yaxis(2)` bar to stand on its own axis, as in Stata.
- **US-27.6** As a dashboard reader, I want the bars' base to follow the axis when I move a filter, on the saved page and in the served app, as twoway's `if` would draw it, and to come back when I move the filter back.

## Business requirements

- **BR-27.1** With no `base()`, a `bar`, `spike`, `dropline` or `area` layer is drawn from 0 when its axis's scale contains 0. Otherwise it is drawn from the end of the scale nearest 0: twoway's `drawn_base`, in both modes (fixture `bases.*`, `auto.*`).
- **BR-27.2** A default base never widens the axis or places a tick. The y scale equals twoway's `[curmin, curmax]`, so a 0 outside the data no longer extends the axis.
- **BR-27.3** An explicit `base(#)` is drawn at #, is inside the scale, and is not a tick input: the ticks are twoway's.
- **BR-27.4** On a log axis the default base is the scale's lower end; no layer is ever drawn from 0.
- **BR-27.5** On a date y axis the default base is Stata's 0 (01jan1960) clamped into the scale. It is never 01jan1970, and never outside the scale.
- **BR-27.6** A layer on `yaxis(2)` takes its base from the second axis's scale.
- **BR-27.7** Under `by()` the panels' bases come from the common scale (a shared second axis included). Under `yrescale` each panel's base comes from its own scale.
- **BR-27.8** After any filter move, saved or served, the base and the axis are twoway's for the kept rows, as `if` gives them (fixture `bases.bar_ydown_if`: 12). Moving back restores them. Zoom and pan do not change the base.
- **BR-27.9** Nothing new is printed (M6). The tooltips of the four types are unchanged.
- **BR-27.10** The saved page and the served app draw identical bases and scales, before and after moves (G3).

## Technical requirements

- **TR-27.1 Class attributes on `GlyphMapper`**, placed after S14's `_BAR_XC`/`_BAR_W`:
  - `_BASE_COL = "__dash_base"`;
  - `_BASE_PROPS = ("bottom", "y0", "y1", "left", "x0", "x1")`. The last three are reserved for S49's horizontal layers.

  Class members travel with the class (R2: the class loop at :33436), so they need no copy-list entry.
- **TR-27.2 `GlyphMapper._base_value(self, options, layer)`** returns a float or None (None means the default base).

  ```python
  raw = options.get("base")
  if raw is None or str(raw).strip() in ("", "."):
      return None
  return _stat_option_float(options, "base", None, layer)
  ```

  It never raises.
- **TR-27.3 `GlyphMapper._base_zero(self, yvar)`** gives Stata's 0 in the axis's units:
  - with `kind = (self.date_vars or {}).get(yvar)` in `("td", "tc", "tC", "tw", "tm", "tq", "th", "ty")`, it returns `float(_dash_units_to_axis(np.array([0.0]), kind)[0])`; for `td`, `tc` and `tC` that is -315619200000.0;
  - otherwise it returns 0.0.

  A NaN result (never expected) gives 0.0.
- **TR-27.4 `GlyphMapper._tag_base(r, prop, auto, zero, letter="y")`** (staticmethod):
  - It asserts `prop in GlyphMapper._BASE_PROPS` and `letter in ("x", "y")`.
  - It builds `"dash_base:" + json.dumps({"auto": bool(auto), "letter": letter, "prop": prop, "zero": float(zero)}, sort_keys=True, separators=(",", ":"), allow_nan=False)`.
  - It sets `r.tags = [t for t in (r.tags or []) if not str(t).startswith("dash_base:")] + [tag]`.
  - The tag is at most 120 characters and holds no user text.
- **TR-27.5 The mappers** (the default base is provisional until filled):
  - **`map_bar`.** Replace the `base_val` block (:10223-10229) with `_base = self._base_value(options, "bar")` and `_zero = self._base_zero(yvar)`. These two lines move above S14's `clean_source = ColumnDataSource(df)`. When `_base is None`, set `df = df.assign(**{self._BASE_COL: _zero})` before that line, and `bottom=self._BASE_COL`. Otherwise `bottom=_base`.

    After `r = fig.vbar(**_vbar_kwargs)`, call `self._tag_base(r, "bottom", _base is None, _zero)`. The empty layer takes the same path (an empty column).

    The docstring says: "with no base(), drawn from a tagged column that _dash_finish_auto_bases fills with twoway's base (0 clamped into the axis's scale)". `x`, `width`, the colours and the appliers are unchanged.
  - **`map_area`.** `_base = self._base_value(options, "area")`; `_zero = self._base_zero(yvar)`; `y1_base = np.full_like(y_arr, _zero if _base is None else _base)`. After `fig.varea(...)`, call `self._tag_base(r, "y1", _base is None, _zero)`. The border line (a separate Line) is untagged.
  - **`map_spike`.** The same, with `y0_base`; tag prop `"y0"` on the Segment.
  - **`map_dropline`.** :13443-13444 become `_base = self._base_value(options, "dropline")` and `zeros = np.full_like(x_arr, _zero if _base is None else float(_base))`. Tag the Segment `"y0"`. The dots are untagged. Rewrite the comment at :13436-13442 ("drawn from 0 rather than raised" becomes "drawn from the default base rather than raised").
- **TR-27.6 `_dash_base_spec(r)`** (new module function, placed after `_dash_secondary_values`) returns a dict `{"prop", "letter", "zero", "auto"}` or None.
  - Over `getattr(r, "tags", None) or ()`, the first `str` tag starting with `dash_base:` and at most 200 characters long is parsed with `json.loads`.
  - The result must be a dict with `prop in GlyphMapper._BASE_PROPS`, `letter in ("x", "y")`, `auto` a bool and `zero` a finite int or float (not bool). Anything else returns None.
  - It never raises.
- **TR-27.7 The value readers** (every one S21's tree uses, in both modes):
  - **`_dash_secondary_values`.** In the renderer loop, `_bs = _dash_base_spec(r)`. In the `fields` loop, skip `attr == _bs["prop"]` when `_bs` is set and `_bs["letter"]` is the reader's letter (`y` for `y_range_name`). No base, default or explicit, is a coordinate value any more. The docstring's "a coordinate given as a number, such as a bar's base" becomes "… a coordinate given as a number; a bar's, spike's, dropline's or area's base is never one (twoway: base(5) is no tick input, B3)".
  - **`_dash_explicit_base_values(renderers, range_attr, name)`** (new, after `_dash_base_spec`). It reads the renderers on range `name` (`getattr(r, range_attr, "default") == name`; swatches skipped) whose spec has `auto` False and whose letter matches. It returns the finite values of the tagged property: a value spec's number, or a field column's finite values through `_dash_float_values(…, coerce=True)`. It never raises.
  - **`_dash_count_axes`.** Each entry gains `"bases": _dash_explicit_base_values(pool, range_attr, name)`, with only values > 0 kept on a log axis. `lo`/`hi` are unchanged; they are the tick input.
  - **`_dash_axis_hull`.** Next to the `lo`/`hi` addition, add `vals += [float(v) for v in e.get("bases") or () if ok(v)]`.
  - **`_dash_finish_secondary_axes`.** `vals = list(all_vals) + list(want) + _dash_explicit_base_values(fig.renderers, kw, name)`.
  - **S21's vectorised reader `_dash_layer_extent`** (P1.3.8) skips the tagged property of every renderer `_dash_base_spec` reads (default or explicit) in place of its `_dash_auto_base` skip; the explicit values reach the hull through `bases` above.
  - **S21's plan builder `_dash_axis_plan`** leaves each tagged property out of a layer's `fields`/`consts`, and gives each panel axis two new keys: `bases` (the explicit values, numbers or `{"src": i, "filt": j, "field": f}`, hull only) and `autobase` (`[{"src": i, "field": f, "zero": z}]` for each renderer on that axis whose spec has `auto` True; `src` is the renderer's own source's index in `models`). Its JS reader `dash_axis_extent` adds `bases` to the hull and never to the tick input.
  - **S21's D7 a marker** `_dash_auto_base`: `_dash_tag_hull_roles` stops stamping it (its `_dash_raw_sif` stamp stays), and every reader of it reads `_dash_base_spec(r)` instead. S21's `test/test_default_axes.py::TestTheHelpers::test_hull_roles` ids `bar`, `bar_base`, `area`, `spike` and `dropline` are flipped in place to read `_dash_base_spec` (`Flipped: … -- the default base's role is now the renderer's dash_base: tag, read by _dash_base_spec, one marker for both modes and the page (P1.17b)`). If 27-01 finds S21 used another marker, the same rule applies to it.
- **TR-27.8 `_dash_axis_scale(fig, letter, name)`** (new) returns the unpadded `(lo, hi)` of that axis's finished scale, or None.
  - The entry of `getattr(fig, "_dash_hull_entries", None) or ()` whose `key == (name, letter)` (S21 records every range name there; at `c96facd` only `("default", letter)` existed).
  - If there is none and `name != "default"`: `(getattr(fig, "_dash_secondary_hulls", None) or {}).get(name)[:2]` (the `c96facd` form, kept for a tree where S21 left it).
  - Both values must be finite and `lo <= hi`, or it returns None.
  - If S21 records the scale elsewhere (S21 contract 3), this helper reads that record and nothing else does.
- **TR-27.9 `_dash_finish_auto_bases(fig)`** (new) returns the number of columns written. For each renderer `r` in `fig.renderers` whose `_dash_base_spec(r)` has `auto` True:
  1. `name = getattr(r, spec["letter"] + "_range_name", "default") or "default"`.
  2. `sc = _dash_axis_scale(fig, spec["letter"], name)`; continue when it is None.
  3. Read the field of `getattr(r.glyph, spec["prop"])` (string, dict or spec object, as `_dash_secondary_values` reads it). Continue when there is no field or it is not in `r.data_source.data`.
  4. `v = min(max(spec["zero"], sc[0]), sc[1])`; `new = np.full(len(col), v, dtype=float)`.
  5. Continue when `np.array_equal(np.asarray(col, dtype=float), new)`, so an unchanged column sends no change event in the served app.
  6. Otherwise `r.data_source.data[field] = new` and count it.

  It never raises: a renderer it cannot read is skipped.
- **TR-27.10 The Python fill points.**
  - The last statement of `_dash_finish_count_ticks` becomes `_dash_finish_auto_bases(fig)`, after `_dash_hull_ranges(fig, entries)`.
  - After the panels loop of `_dash_common_count_ticks`, at function level, add `for f in figs or (): _dash_finish_auto_bases(f)`.
  - S21's `_dash_refinish_axes(figures, facet_map)` reaches both hooks above (it calls `_dash_finish_count_ticks(f, refinish=True)` and `_dash_common_count_ticks`), so it is not edited. Only if 27-01 finds it does not, add `for f in figures: _dash_finish_auto_bases(f)` at its end (idempotent).
  - Only if S21's `_dash_share_by_scales` still has its y2/x2 block (S21 removes it, TR-21.8) and does not already record the shared second-axis hull on each panel: after `new` is made in its y2/x2 block, add
    ```python
    for f in figs:
        f._dash_secondary_hulls = {**(getattr(f, "_dash_secondary_hulls", None) or {}),
                                   name: (lo2, hi2, hulls[0][2], hulls[0][3])}
    ```
    where `lo2, hi2` are the min and max already computed. Warn CRITICAL first.
  - `_make_figure_body` and `_generate_app_source` are not edited.
- **TR-27.11 The JS twin**, inside S21's `_DASH_AXIS_FINISH_JS`, working from the plan (S21 gives the JS no renderer list):
  - `function dash_fill_auto_bases(ax, models, lo, hi)`: it returns at once unless `lo` and `hi` are finite with `lo <= hi` and `Array.isArray(ax.autobase)`. For each `a` of `ax.autobase` with `Number.isInteger(a.src)`, `typeof a.field === "string"`, `Number.isFinite(a.zero)`, a model at `models[a.src]` that has `data` and `Object.prototype.hasOwnProperty.call(models[a.src].data, a.field)`:
    - `v = Math.min(Math.max(a.zero, lo), hi)`;
    - skip if every element of the column already equals `v`;
    - otherwise `const nd = Object.assign({}, src.data); nd[a.field] = new Array(n).fill(v); src.data = nd; src.change.emit();`.
  - `dash_axis_extent` adds `ax.bases` to the hull only (TR-27.7).
  - `dash_fill_auto_bases` is called once per axis inside `dash_axis_finish`, after that axis's final unpadded scale is known (after the `by()` union for a shared axis), with that scale.
  - The plan's `autobase` entries are built in Python by `_dash_axis_plan` from `_dash_base_spec` (TR-27.7), so the page's script parses no tag and takes no property name from the page: it writes only a column S21's plan already names, on a source in `axis_models`.

- **TR-27.12 Served copy lists (R2).** Functions tuple, after S21's `"_dash_refinish_axes"`: `"_dash_base_spec", "_dash_explicit_base_values", "_dash_axis_scale", "_dash_finish_auto_bases",`. The R2 table names `_dash_finish_auto_bases`; the other three are S27's at the same anchor, and S44 adds after S27's names. No constant is added: `_DASH_AXIS_FINISH_JS` is S21's, already listed, and edited in place. The registry tests stay green: `TestTheServedAppCarriesEveryName`, `test_every_listed_name_exists` and `TestTheServedAppDefinesEveryNameItReads`.
- **TR-27.13 Maps (A148).** In `test/function_test_map.py`, under `# WP-30 S27 (P1.17b): twoway's default base and axis extent (P1.17 part b)`, alphabetical:
  - `'GlyphMapper._base_value': 'test/test_bar_range_geometry.py::TestTheMappersMarkTheirBase::test_base_value'`
  - `'GlyphMapper._base_zero': 'test/test_bar_range_geometry.py::TestTheMappersMarkTheirBase::test_base_zero'`
  - `'GlyphMapper._tag_base': 'test/test_bar_range_geometry.py::TestTheMappersMarkTheirBase::test_each_mapper_tags_its_base'`
  - `'_dash_axis_scale': 'test/test_bar_range_geometry.py::TestTheFill::test_the_axis_scale'`
  - `'_dash_base_spec': 'test/test_bar_range_geometry.py::TestTheBaseSpec::test_reads_only_well_formed_tags'`
  - `'_dash_explicit_base_values': 'test/test_bar_range_geometry.py::TestAnExplicitBaseStaysInTheScale::test_the_reader'`
  - `'_dash_finish_auto_bases': 'test/test_bar_range_geometry.py::TestTheFill::test_clamps_zero_into_the_scale'`

  `test/program_coverage_map.py` is not changed: no Stata program or Mata function is added.
- **TR-27.14 The node harness.** The JS twin reads the plan, not renderer tags, so `test/js_runner.py` needs no change. Only if a node test of 27-01 must read a tag through S21's harness and the `GlyphRenderer` stand-in (`stand_in`, :149-176 at `c96facd`) carries no `tags`, add `"tags": [str(t) for t in (m.tags or [])]` to it, and nothing else.
- **TR-27.15 Security (rule 1).**
  - The tag is built by `json.dumps(..., allow_nan=False)` from fixed keys and a float, never from user text.
  - The Python reader bounds the tag's length, checks `prop` against the fixed list before indexing a glyph, and parses with `json.loads`. The JS parses no tag; it checks each plan entry's types and writes a column only when the source owns it (`hasOwnProperty`). There is no `eval`, `new Function` or `exec`.
  - The JS writes only the column the plan names for that renderer's own source.
  - No text reaches the page.
  - The extractor runs `git rev-parse` through Stata's `shell` into a file, and its python block never uses `shell=True`.

## Boundaries

- **S25 (same batch)** owns `_generate_app_source`'s header guard (`_dash_dep_fail`, `_DASH_MIN_PYTHON`), dash.ado's `_dash_require_deps`, dash_setup, and the dependency paragraphs of the help. S27 edits none of them, and does not edit `_generate_app_source` at all.
- **S26 (same batch)** owns `map_function`, its fallback mark read by `_dash_note_empty_layer`, and dash.sthlp:413-418. S27 edits none of them.
- **S14 (landed)** owns widths and caps (`_bar_extent`, `_BAR_XC`/`_BAR_W`, `map_rbar`, `map_rcap`, `map_rcapsym`, the `dash_cap` tag, the `{ul:Bars and range caps.}` help paragraph). S27 must not change `x`, `width` or any cap.
- **S21 (landed)** owns natscale, the margin (`_dash_plot_margin`), `_dash_default_ticker`, the zoom ticker and the re-finish plumbing. S27 adds only the fill call, the skip and the explicit-base hull values to S21's `_dash_refinish_axes`, its reader and `_DASH_AXIS_FINISH_JS` (R11: S27 is batch 9's one finisher editor).
- **S35 (batch 12)** owns an explicit `base(#)` read in date units, mixed date and numeric axes, and every date-axis decision (`_dash_axis_date_kind`, `_on_axis`). S27's `_base_zero` reads only `date_vars`.
- **S44 (batch 15)** owns the `%td`-`%ty` scale (tsnatscale). DB-08's twoway equality waits for it.
- **S47 (batch 16)** owns the margin and inner box; the base reads the unpadded scale, so S47 needs no change here.
- **S49/S55 (batches 17, 19)** own `horizontal`: a horizontal layer's tag has `letter "x"` and prop `left`/`x0`/`x1`. S27 writes only `letter "y"`.
- **S45 (batch 16)** owns `recast()`. A layer recast to bar, spike, dropline or area goes through these mappers and is tagged.
- **S20 (landed)** owns per-series `base()` lists and their validation. S27 only reads a `.` element as the default.
- **P2.7** owns `nodropbase` and `baroffset`. `base()` on `dot` and on `function` stays undrawn (dash.sthlp:2363-2365).
- Not touched: `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, the four appliers, dash.ado, dash_parse.mata, the scheme files, the histogram's `bottom=0`, `_dash_padded_range`, and the tracking documents (A145).

## Stata truth

**New extractor** `scripts/extract_default_base_truth.do`, in S02's path-free form: copy the head of an extractor S02 converted, e.g. `scripts/extract_emptied_layer_truth.do`, taking the tree from `DASH_REPO`, else `c(pwd)` when it holds dash.ado. It opens with `adopath ++ "<repo>/"` and `global dash_nobrowser 1`, and is run only as:

```sh
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s27/x $WT/scripts/extract_default_base_truth.do
```

It writes `test/fixtures/default_base_truth.json` (added with `git add -f`).
- `_meta` holds `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` and `extracted` (`c(current_date) c(current_time)`). `dash_commit` is `git rev-parse HEAD` written by `shell` to a file in the work directory and read by the python block, never with `shell=True`.
- It runs twoway only, so it is the same before and after the fix.
- Every graph uses `set scheme s2color`, is drawn with `name(g, replace)` and is dropped at the end. Each case's values are read from twoway's class members into locals right after the graph is drawn: `.g.plotregion1.plot#.drawn_base`, `.g.plotregion1.yscale.curmin/curmax`, `.g.yaxis1.major.min/delta/max`, `.g.plotregion2.*` for a second axis and `.g.graphs[i].*` under `by()`. A trailing `python:` block reads the locals through `Macro.getLocal` and writes the JSON. A backtick is written as `\x60`.

Data (typed with `input`):

```
x1 ypos y12 yneg ys g d(%td) ymix ydown
1  10   12  -10  1  1 15000  -3   14
2  11   25  -11  2  1 15007   5   13
3  12   33  -12  3  2 15014   8   12
4  13   41  -13  4  2 15021   2   11
5  14   18  -14  5  2 15028  -1   10
```

`sysuse auto, clear` is used for the `auto.*` keys.

| Key | twoway command | Recorded | Measured 03oct2026 |
|---|---|---|---|
| `bases.bar_ypos` | `bar ypos x1` | drawn_base, curmin, curmax, ticks | 10, [10, 14], 10(1)14 |
| `bases.bar_y12`, `spike_y12`, `dropline_y12`, `area_y12` | `<t> y12 x1` | the same | 10, [10, 41], 10(10)40 |
| `bases.bar_yneg` | `bar yneg x1` | the same | -10, [-14, -10] |
| `bases.bar_ymix` | `bar ymix x1` | the same | 0, [-5, 10] |
| `bases.bar_scatter` | `(bar y12 x1) (scatter ys x1)` | plot1's | 0, [0, 41] |
| `bases.bar_base5`, `spike_base5` | `<t> ypos x1, base(5)` | the same | 5, [5, 14], 10(1)14 |
| `bases.area_base5` | `area y12 x1, base(5)` | the same | 5, [5, 41], 10(10)40 |
| `bases.bar_base20` | `bar ypos x1, base(20)` | the same | 20, [10, 20], 10(1)14 |
| `bases.two_bars` | `(bar y12 x1) (bar ypos x1, base(30))` | plot1's and plot2's | 10 and 30, [10, 41] |
| `bases.auto_explicit0` | `(bar ypos x1) (bar y12 x1, base(0))` | plot1's | 0, [0, 41] |
| `bases.bar_log`, `area_log` | `<t> ypos x1, yscale(log)` | the same | 10, [10, 14] |
| `bases.bar_range0` | `bar ypos x1, yscale(range(0))` | the same | 0, [0, 14] |
| `bases.bar_ylabel5` | `bar ypos x1, ylabel(5(5)15)` | the same | 5, [5, 15] |
| `bases.bar_reverse` | `bar ypos x1, yscale(reverse)` | the same | 10, [10, 14] |
| `bases.bar_if` | `bar ypos x1 if x1>=3` | the same | 12, [12, 14], 12(.5)14 |
| `bases.bar_ydown`, `bar_ydown_if` | `bar ydown x1`; `… if x1<=3` | the same | 10, [10, 14]; 12, [12, 14] |
| `bases.bar_y2` | `(scatter y12 x1) (bar ypos x1, yaxis(2))` | `.plotregion2.plot2.drawn_base`, `.plotregion2.yscale`, `.plotregion1.yscale` | 10, y2 [10, 14], y [10, 41] |
| `bases.bar_by`, `bar_by_yrescale` | `bar y12 x1, by(g)`; `by(g, yrescale)` | per panel `.graphs[i]` | 10/10 on [10, 41]; 10 on [10, 25] and 18 on [18, 41] |
| `bases.bar_by_y2` | `(scatter y12 x1) (bar ypos x1, yaxis(2)), by(g)` | per panel `.plotregion2` | 10/10, y2 [10, 14] both |
| `bases.bar_td`, `dropline_td` | `<t> d x1` | the same | 14997, [14997, 15028] |
| `auto.<t>` for t in bar, spike, dropline, area | `<t> mpg weight` (auto) | the same | 10, [10, 41], 10(10)40 |
| `auto3.<t>` | `<t> mpg weight in 1/3` | the same | 17, [17, 22] |

The measured column comes from this file's probes `<scratch>/s27/p1.do`-`p7.do`, run through the slot. Representative lines from the logs:

```
PRB B3 bar ypos base(5): base=[5] cur=[5,14] ticks=10(1)14
PRB B6 bar ypos log: base=[10] cur=[10,14] ticks=10(1)14
PRB B7 bar d(%td): base=[14997] cur=[14997,15028] ticks=14997(0)15025
PRB B12 bar ypos base(20): base=[20] cur=[10,20] ticks=10(1)14
PRB B15 by yrescale[2] base=[18] cur=[18,41]
PRB B17 by y2[2] base=[10] y2cur=[10,14] y1cur=[10,41]
PRB B18 auto+explicit0: p1 base=[0] cur=[0,41]
PRB B21 mixed sign: base=[0] cur=[-5,10]
PRB B24 ydown if x1<=3: base=[12] cur=[12,14]
PRB auto3 bar: base=[17] cur=[17,22]
```

The rule: a default base is `min(max(0, curmin), curmax)`, with the scale computed without default bases; an explicit base is in `[curmin, curmax]` but not in the ticks. The help's sentence "the value of yvar closest to 0" (twoway_bar.sthlp:125-127) is wrong for y12 (twoway draws from 10, not 12), and dash.sthlp:2360-2362's "from the edge of the plot region" is wrong too: twoway's bar ends at curmin, and the axis line sits a margin lower (research critic correction 5).

**Truth block (R1).** In `test/test_wp30_truth.cscript`, between S01's `S27 start` and `S27 end` lines, under `* ==== S27 P1.17b: twoway's default base and axis extent ====`.
- Its python helpers sit directly above that header, at top level, with no brace inside the gate: `_db_bases(sp, dp)` gives `{"saved": [...], "served": [...]}` of `(range name, base value, scale lo, hi, y ticks)` for every renderer `_dash_base_spec` tags, read from the saved renderer and from the generated app's `make_document`; `_db_move(sp, dp, app)` gives the served values after a range move.
- Each case runs twoway, then `dash ..., name(zdbK)`, then `_dash_serve_spec, specpath() datapath()`, and compares with twoway's own values from the same run, through `_w30_expect` and `_w30_done`.

The cases:
- **DB-01** `bar`, `spike`, `dropline` and `area` of `y12 x1`: dash's base equals `.plot1.drawn_base` (10), and dash's scale (`_dash_axis_scale`) equals `[curmin, curmax]` within 1e-9 of the span, in both modes.
- **DB-02** `bar ypos x1`, `bar yneg x1`, `bar ymix x1`, `(bar y12 x1) (scatter ys x1)`: bases 10, -10, 0 and 0, in both modes.
- **DB-03** `bar ypos x1, base(5)`, `base(20)`, `spike ypos x1, base(5)`, and `(bar ypos x1) (bar y12 x1, base(0))`: the bases and the scale equal twoway's, and dash's y ticks equal `.yaxis1.major` (10(1)14 for the first three), in both modes.
- **DB-04** `bar` and `area` of `ypos x1, yscale(log)`: base 10, and no base value ≤ 0, in both modes.
- **DB-05** `(scatter y12 x1) (bar ypos x1, yaxis(2))`: the y2 base equals `.plotregion2.plot2.drawn_base` (10), and the y scale is `[10, 41]`.
- **DB-06** `bar y12 x1, by(g)`, `by(g, yrescale)` and `(scatter y12 x1) (bar ypos x1, yaxis(2)), by(g)`: the per-panel bases equal twoway's `.graphs[i]` values, in both modes.
- **DB-07** served move: `dash bar ydown x1` with a range filter on `x1`, its upper handle set to 3 and the generated app's `_on_filter_change` fired (as `test_mode_parity._served_after_move` fires it). The base is 10 before and 12 after, equal to twoway's `bar ydown x1 if x1<=3` (`drawn_base` 12) and to `bar ydown x1` (10).
- **DB-08** `bar d x1` with `d` `%td`: dash's base equals dash's own scale low end, is greater than `_dash_units_to_axis(0, "td")` and is not 0 ms. twoway's 14997 is printed beside it, not asserted (S44's residual).

**HC6-23b**, `test/test_help_claims_6.cscript` :685-701, is amended in place (R1). The comment's last sentence becomes "dash draws them from the same place, in both modes". Inside the `foreach`, after the twoway reads, the case runs `dash \`t' mpg weight in 1/3, name(hc6b)`, writes the spec with `_dash_serve_spec`, and checks through a one-line `python:` call that the saved renderer's tagged base equals `\`m0'` (17). A mismatch sets `bad`. The tally text becomes "twoway's default base: the axis stops at the data (17), not 0, on bar spike dropline area, and dash draws from 17".

## TDD test stubs

### Regression tests, appended to `test/test_bar_range_geometry.py` (S14's file, PLAN's P1.17 test file)

The tests go under a banner `# P1.17b (WP-30 S27): twoway's default base and axis extent`, reading `test/fixtures/default_base_truth.json` once at module level. The module docstring gains a P1.17b paragraph: the defect, the probe commands and the rule.

Helpers:
- `_db_frame()`: the extractor's data, with `d` given format `%td`;
- `_db_figs(mode, plots, graph_options=None, if_expr="", filters=None)`: saved `DashRenderer(...).render()` figures, or served `ServerAppBuilder.build` then `make_document` (test_date_range's `_saved`/`_served`);
- `_db_base(r)`: the drawn base value of a tagged renderer (the field's unique value, or the value spec);
- `_db_cases`: case key to (plots, graph_options, if_expr), mirroring the extractor's commands.

Every class that draws is parametrized over `mode in ("saved", "served")`. Every class is red at the batch-9 base unless marked guard; at `c96facd` every drawn base is 0.

- Test: the fixture exists, carries the four `_meta` keys, and holds every key of the Stata truth table — `TestTheBaseFixture::test_meta_is_stamped`, `::test_every_case_was_measured` (guard after 27-01).
- Test: the default base equals twoway's `drawn_base` for `bar_ypos`, `bar_y12`, `spike_y12`, `dropline_y12`, `area_y12`, `bar_yneg`, `bar_ymix`, `bar_scatter`, `bar_range0`, `bar_ylabel5`, `bar_reverse`, `bar_if`, `bar_ydown`, `auto3.*` — `TestTheDefaultBaseIsTwoways::test_the_base_is_twoways[mode-case]`.
- Test: dash's y scale (`_dash_axis_scale`) equals `[curmin, curmax]` within 1e-9 × span, and the y Range1d's start is above 0 for `bar_ypos` — `::test_the_scale_is_twoways[mode-case]`, `::test_the_axis_does_not_reach_zero[mode]` (the second is a guard after S21).
- Test: `bar_base5`, `spike_base5`, `area_base5`, `bar_base20`, `two_bars` and `auto_explicit0` draw at twoway's bases with twoway's scale and twoway's ticks — `TestAnExplicitBaseStaysInTheScale::test_base_and_scale[mode-case]`, `::test_the_ticks_are_twoways[mode-case]`. The ticks test is red at `c96facd` (4(2)14); at the batch-9 base it is a guard if S21 already left explicit bases out of the tick input.
- Test: `_dash_explicit_base_values` returns 5.0 for `bar ypos, base(5)`, nothing for a default base, and nothing for a renderer on another range — `::test_the_reader`.
- Test: `bar_log` and `area_log` (and spike, dropline on ypos log) are drawn from 10 and never from a value ≤ 0 — `TestTheBaseOnALogAxis::test_never_zero[mode-type]`.
- Test: on `%td`, the tag's `zero` is -315619200000.0, the drawn base equals the scale's low end, and it is above the tag's zero and not 0 ms — `TestTheBaseOnADateAxis::test_the_default_base_is_1960_clamped[mode-type]` (bar, spike, dropline, area).
- Test: `bar_y2`: the y2 bar's base is 10, and the scatter's y scale is `[10, 41]` — `TestTheBaseOnASecondAxis::test_y2[mode]`.
- Test: `bar_by` gives (10, 10), `bar_by_yrescale` gives (10, 18) and `bar_by_y2` gives (10, 10) — `TestTheBaseUnderBy::test_a_common_scale_gives_a_common_base[mode]`, `::test_yrescale_gives_each_panel_its_own[mode]`, `::test_a_shared_second_axis_gives_a_common_base[mode]`.
- Test: a saved move (the page's own `_FILTER_JS`, with S21's finisher, under node through S21's saved re-finish harness; at `c96facd`, test_saved_filter_layers `_render`/`_move`) of a range filter on `x1` to x1 ≤ 3 makes the `bar ydown x1` base 12, and moving back makes it 10 — `TestTheBaseAfterAMove::test_saved[type]` (bar, spike, dropline, area), `::test_saved_back`.
- Test: the same move through the served `_on_filter_change` — `::test_served[type]`, `::test_served_back`. After the move, the saved and served bases and y ticks are equal — `::test_both_modes_agree`.
- Test: in headless Chrome, `bar ydown x1` with a RangeSlider on `x1`. Before the move, the base is 10 and y start > 9. After `move_range_slider(0.5)` and `wait_settled`, the base is 12, y start > 11, and `js_errors() == []`. The base is read with `p._eval` over `Bokeh.documents[0]`'s renderers whose tags start with `dash_base:` — `TestTheSavedPageInChrome::test_the_base_follows_the_slider` (the module skips only when `responsive_probe.find_chrome()` is None, as test_by_scales_chrome.py does).
- Test: each mapper tags its renderer (`bottom`, `y1`, `y0`, `y0`) with `auto` True with no `base()` and False with `base(5)`; bar's `bottom` is `__dash_base` only when auto — `TestTheMappersMarkTheirBase::test_each_mapper_tags_its_base[type-explicit]`.
- Test: `_base_value` gives None for absent, `""` and `"."`; 5.0 for `"5"`; and None with one note for `"abc"`, `"inf"` and `"nan"` — `::test_base_value`. `_base_zero` gives 0.0 for a number and `_dash_units_to_axis(0, k)` for each date kind — `::test_base_zero`.
- Test: `_dash_base_spec` reads a well-formed tag, and returns None for: no tag, `dash_base:` with bad JSON, a JSON list, prop `__proto__`, letter `z`, zero `"0"` or NaN-by-text, auto `1`, and a tag over 200 characters — `TestTheBaseSpec::test_reads_only_well_formed_tags`.
- Test: `_dash_finish_auto_bases` writes 10 for scale [10, 14], -10 for [-14, -10] and 0 for [-5, 5]; writes nothing when there is no scale or the column already holds the value (returns 0, the column object unchanged); and never touches an explicit base — `TestTheFill::test_clamps_zero_into_the_scale`, `::test_an_unchanged_column_is_not_rewritten`, `::test_an_explicit_base_is_left_alone`. `_dash_axis_scale` reads the primary hull entry, the y2 record, and None for a missing or non-finite one — `::test_the_axis_scale`.
- Test: a fill over a 500,000-row bar takes under 0.05 s — `TestTheFillIsCheap::test_500k_rows` (A9: S21's budget is kept).
- Test: the tooltips of bar, spike, dropline and area name the same fields as before, and no tooltip names `__dash_base` — `TestTheTooltipsAreUnchanged::test_the_fields[mode-type]` (guard).

### Cases in cscripts

- `test_wp30_truth.cscript`: DB-01 to DB-08, all red at the batch-9 base.
- `test_help_claims_6.cscript`: HC6-23b amended (red at base: dash's base is 0).

### Flips (in place; each gets a `Flipped:` line and stays red at base after the flip)

Listed under Evidence "Tests that pin today's behaviour". Each flipped or amended docstring gains: "twoway draws a default base as 0 clamped into the axis's scale (P1.17b)".

### Parity corpus (R8; appended; guards at base)

In `test/test_mode_parity.py`, under `# WP-30 P1.17b: twoway's default base`:
- `CORPUS` cases: "bar with 0 below the data" (`plot_for("bar")`; mpg 14-30 on `_DF`), "spike base(5)", "area on a log y" (`{"yscale": "log"}`), "dropline on yaxis(2)" (a scatter of mpg plus `plot_for("dropline", {"yaxis": "2"}, yvar="price")`);
- `MOVE_CORPUS` cases: "bar with 0 below the data, dropdown" (`_MOVES[0]`) and "area under by(), range" (`_MOVES[1]`, `{"by": "foreign"}`).

`_DF`, `ALLOWED` and `_MUST_WARN` are not edited.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Default base on four types and four sign cases | pytest `TestTheDefaultBaseIsTwoways`; cscript DB-01, DB-02 | `bases.*`, `auto3.*` | yes |
| The scale has no default base | pytest `::test_the_scale_is_twoways`, `::test_the_axis_does_not_reach_zero` | `bases.*` curmin/curmax | yes |
| Explicit base: in the scale, not the ticks | pytest `TestAnExplicitBaseStaysInTheScale`; DB-03 | `bases.*base*`, `two_bars`, `auto_explicit0` | yes |
| Log and date axes | pytest `TestTheBaseOnALogAxis`, `TestTheBaseOnADateAxis`; DB-04, DB-08 | `bases.bar_log`, `area_log`, `bar_td` | yes |
| Second axis, by(), yrescale, shared y2 | pytest `TestTheBaseOnASecondAxis`, `TestTheBaseUnderBy`; DB-05, DB-06 | `bases.bar_y2`, `bar_by*` | yes |
| After a move and back | pytest `TestTheBaseAfterAMove` (node and served), `TestTheSavedPageInChrome`; DB-07; `MOVE_CORPUS` | `bases.bar_ydown*` | yes |
| Mapper tags, spec reader, fill, budget | pytest `TestTheMappersMarkTheirBase`, `TestTheBaseSpec`, `TestTheFill`, `TestTheFillIsCheap` | — | n/a (units) |
| Tooltips | pytest `TestTheTooltipsAreUnchanged` | — | yes |
| Help claim | cscript HC6-23b | `auto3.*` | saved |
| Parity | `python3 -m pytest test/test_mode_parity.py -q -n0` (G3) | — | yes |
| Registry | `test_function_test_map.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` | — | — |

**Acceptance criteria**
- **AC-27.1** For every `bases.*` and `auto*` record but the two `%td` ones, dash's drawn base equals twoway's `drawn_base` and dash's unpadded y scale equals `[curmin, curmax]`, within 1e-9 × span, in the saved page and the served app.
- **AC-27.2** With an explicit `base()`, dash's y ticks equal twoway's major ticks in both modes (10(1)14 for `bar ypos x1, base(5)`).
- **AC-27.3** No default base is ≤ 0 on a log axis, or outside the scale on a date axis, in either mode.
- **AC-27.4** After a saved move (node and Chrome) and after a served move, the `bar ydown x1` base is 12, and after moving back it is 10. The two modes agree.
- **AC-27.5** `test_wp30_truth.cscript` under `WP30_ONLY=S27` prints DB-01 to DB-08 PASS and `ALL CHECKS PASSED`. `test_help_claims_6.cscript` prints HC6-23b PASS. There is no SKIP and no `r(` error.
- **AC-27.6** `grep -c "dash_base:" dash_render.py` is at least 2 (the tag writer and the Python reader; the JS reads the plan). `grep -n "bottom=base_val" dash_render.py` prints nothing. The registry tests are green.
- **AC-27.7** One full run through the queue is green before the commit.

## Tasks

**Commit boundary.** Tasks 27-01 to 27-10 form the one P1.17b commit, made by 27-10 on `wp30-s27` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s27` after one full run through the queue. Subject: `Draw bars, spikes, droplines and areas from twoway's default base (WP-30 P1.17b)`.
- The body opens with `<scratch>/27-P1.17b-failure.txt`, then the measured defect, then what changed and where: the four mappers, the readers, the four fill points, both modes.
- Then one line each of:
  - `Regression: test/test_bar_range_geometry.py::<Class>::<test> -- failed at <batch-9 base sha> with <text>`, plus `Regression: test/test_wp30_truth.cscript DB-0k` and `Regression: test/test_help_claims_6.cscript HC6-23b`;
  - `Flipped: <node> -- <old expectation> was wrong because twoway draws a default base as 0 clamped into the axis's scale (P1.17b)` (one per flip, from `<scratch>/s27/27-flips.txt`);
  - `Fixture: test/fixtures/default_base_truth.json (scripts/extract_default_base_truth.do)`;
  - `BUGS.md: "<title>" (closed)`.

Every command runs from `$WT`. No body, BUGS, CHANGELOG or help line names a tool or vendor (G7). `<scratch>` is the orchestrator's WP-30 scratch directory (index.md, "Deltas from BRIEF.md"); the probes this file quotes ran in its `s27/` subdirectory.

<task type="auto" id="27-01">
  <name>Check S21, measure twoway, write failing tests</name>
  <files>scripts/extract_default_base_truth.do, test/fixtures/default_base_truth.json, test/test_bar_range_geometry.py</files>
  <action><![CDATA[
    1. Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-9-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s27`. Run `mkdir -p <scratch>/s27/x`. Confirm that `<scratch>/batch-9-impact.txt` holds Evidence "Blast radius" with the maintainer's approval of the CRITICAL rows.
    2. Check the S21 contract (Evidence) and write what you find, with file:line, to `<scratch>/s27/s21-contract.txt`:
       - `grep -n "def _dash_refinish_axes" dash_render.py` prints 1 line;
       - `grep -n "^_DASH_AXIS_FINISH_JS" dash_render.py` prints 1 line;
       - `grep -c '"_dash_refinish_axes"' dash_render.py` prints 1;
       - the call in `_on_filter_change` after the live sources are written;
       - the JS call at the end of `_FILTER_JS`;
       - where each axis's unpadded scale is recorded (primary, y2/x2, by()-shared, after a served move) and where the JS holds it;
       - S21's value readers (Python, vectorised, JS) and how they leave default bases out (D7 a);
       - whether explicit bases are in the tick input.
       If any of the first five is missing, stop and report to the orchestrator without editing anything.
    3. Create scripts/extract_default_base_truth.do by "Stata truth", run it through the slot, and run `git add -f test/fixtures/default_base_truth.json`. Its values must match the table's "Measured" column; a mismatch stops the task.
    4. Append to test/test_bar_range_geometry.py exactly the banner, helpers, classes and tests of "TDD test stubs / Regression tests".
    5. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -rf -k "Base or Fill or Explicit or Mappers or Tooltips" > <scratch>/s27/27-01.log 2>&1`. Write `<scratch>/27-P1.17b-failure.txt`: the base sha, each failing node with its one-line reason, then the guards that passed. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/default_base_truth.json'));print(sorted(d['_meta']), d['bases']['bar_y12']['drawn_base'], d['bases']['bar_by_yrescale'])"` prints the four `_meta` keys, 10 and panel bases 10 and 18; `grep -c FAILED <scratch>/s27/27-01.log` is at least 50; no `TestTheBaseFixture` or `TestTheTooltipsAreUnchanged` node is FAILED; `test -s <scratch>/27-P1.17b-failure.txt && test -s <scratch>/s27/s21-contract.txt`.]]></verify>
  <done>S21's contract was confirmed and recorded, twoway's bases were stored in a stamped fixture, and every regression test was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="27-02">
  <name>Write the DB truth block and HC6-23b</name>
  <files>test/test_wp30_truth.cscript, test/test_help_claims_6.cscript</files>
  <action><![CDATA[
    In test_wp30_truth.cscript, add the `_db_` python helpers directly above `* ==== S27 P1.17b:` (top level, no brace inside the gate). Write DB-01 to DB-08 of "Stata truth / Truth block" between S01's `S27 start` and `S27 end` lines; each case ends with `_w30_done DB-0k "<what>"` and has its expectations through `_w30_expect`. Every file goes under the scaffold's work directory and is erased; `dash clear` and `set scheme` are restored. Amend HC6-23b in test_help_claims_6.cscript in place, as "Stata truth" says, touching no other case. Run both through the driver (`WP30_ONLY=S27` for the truth script) on the unmodified renderer and append their FAIL lines to `<scratch>/27-P1.17b-failure.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c "DB-0[1-8] FAIL" <scratch>/s27/run_test_wp30_truth.log` prints 8; `grep -c "HC6-23b FAIL" <scratch>/s27/run_test_help_claims_6.log` is at least 1; `grep -c "SKIP" <scratch>/s27/run_test_wp30_truth.log` prints 0.]]></verify>
  <done>Live twoway was compared with dash's saved page and served app in eight cases and the amended help claim, and all of them failed on the unmodified tree.</done>
</task>

<task type="auto" id="27-03">
  <name>Flip base pins and add parity cases</name>
  <files>test/test_glyphs.py, test/test_help_claims_6.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Flip or amend in place, keeping every node name, the nodes of Evidence "Tests that pin today's behaviour":
    - three in test_glyphs.py (`TestBarOptions`, `TestAreaBase`, `TestSpikeBase` `::test_base_default_is_zero`);
    - `TestDroplineBase::test_the_default_is_zero` and `TestBaseOnTheBarPlots::test_the_base_is_drawn_and_defaults_to_zero` in test_help_claims_6.py; its `_bases` reads `bar`'s `bottom` field from `r.data_source.data` when `bottom` is a field.
    Use the fixture's `auto.<t>` drawn_base (10) for the expected value, not a literal. Add the docstring reason. Append one `Flipped:` line per node (parametrized ids each) to `<scratch>/s27/27-flips.txt`. Append the parity cases of "TDD test stubs / Parity corpus" to test_mode_parity.py and nothing else. Run the three files on the unmodified renderer, and append the red nodes under `Pinned, red at base after the flip` to `<scratch>/27-P1.17b-failure.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_glyphs.py test/test_help_claims_6.py -q -p no:cacheprovider` fails exactly the flipped and amended nodes (3 + 2 + 6 = 11 ids); `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "P1.17b or base or log y or yaxis(2)"` reports 0 failed; `grep -c "WP-30 P1.17b" test/test_mode_parity.py` is at least 2.]]></verify>
  <done>Every test that pinned a 0 base asserted twoway's base instead, keeping its name, and the parity corpus held the new cases in both modes.</done>
</task>

<task type="auto" id="27-04">
  <name>Mark each base in the mappers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add TR-27.1 to TR-27.4 (`_BASE_COL`, `_BASE_PROPS`, `_base_value`, `_base_zero`, `_tag_base`) to GlyphMapper after S14's `_BAR_XC`/`_BAR_W`. Make TR-27.5 in map_bar, map_area, map_spike and map_dropline: replace only the base lines named there, add the tag call after the glyph is made, and touch no width, x, colour, applier or label line. Add `_dash_base_spec` (TR-27.6) after `_dash_secondary_values`. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -k "Mappers or BaseSpec"`, the 27-03 files, and test_internal_column_names.py.
  ]]></action>
  <verify><![CDATA[Those classes pass, and test_internal_column_names.py passes; `grep -n "bottom=base_val\|base_val = 0.0" dash_render.py` prints nothing; `grep -c "_tag_base(r" dash_render.py` prints 4.]]></verify>
  <done>Every bar, spike, dropline and area renderer carried a tag naming its base and whether it was the default, with the default written as a provisional zero in a data column.</done>
</task>

<task type="auto" id="27-05">
  <name>Keep bases out of ticks and hull</name>
  <files>dash_render.py, test/test_default_axes.py</files>
  <action><![CDATA[
    Make TR-27.7: the skip in `_dash_secondary_values`; `_dash_explicit_base_values` after `_dash_base_spec`; the `bases` key in `_dash_count_axes`; the hull addition in `_dash_axis_hull` and in `_dash_finish_secondary_axes`. Then apply the same rule to `_dash_layer_extent`, `_dash_axis_plan` (`fields`/`consts` without tagged properties; the `bases` and `autobase` keys) and `dash_axis_extent` in `_DASH_AXIS_FINISH_JS`, as recorded in `<scratch>/s27/s21-contract.txt`. Stop `_dash_tag_hull_roles` stamping `_dash_auto_base` and re-point every reader of it to `_dash_base_spec`; flip `test/test_default_axes.py::TestTheHelpers::test_hull_roles`'s five base ids in place (TR-27.7) and append their `Flipped:` lines to `<scratch>/s27/27-flips.txt`. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -k "Explicit or the_scale or reach_zero"`, test_axis_extents.py, test_by_scales.py and S21's own test file(s) named in the contract.
  ]]></action>
  <verify><![CDATA[`TestAnExplicitBaseStaysInTheScale` and `::test_the_scale_is_twoways` pass; test_axis_extents.py, test_by_scales.py and S21's files report 0 failed.]]></verify>
  <done>No base was a tick input in either mode, a default base stayed out of every hull, and an explicit base widened the scale as twoway's does.</done>
</task>

<task type="auto" id="27-06">
  <name>Fill bases at build and served moves</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Warn before editing `_dash_common_count_ticks` (CRITICAL). Warn also before `_dash_share_by_scales` (CRITICAL), and before S21's `_dash_refinish_axes` at the risk 9.0 recorded, if they need edits. Add `_dash_axis_scale` (TR-27.8) and `_dash_finish_auto_bases` (TR-27.9) after `_dash_explicit_base_values`. Make the TR-27.10 calls, and the y2/x2 record only if the contract file says S21 does not keep one. Add the four names of TR-27.12 after S21's `"_dash_refinish_axes"` in the functions tuple, and the seven map entries of TR-27.13 under S27's anchor. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -k "not saved and not Chrome"`, test_function_test_map.py, `"test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName"`, `"test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads"` and S21's timed served re-finish test.
  ]]></action>
  <verify><![CDATA[Every run above reports 0 failed; `grep -c "_dash_finish_auto_bases(" dash_render.py` is at least 4 (the def and three calls); `grep -c '"_dash_finish_auto_bases"' dash_render.py` prints 1.]]></verify>
  <done>Both modes drew every default base at twoway's clamp at build, under by() and after a served move, through module functions the served app carries.</done>
</task>

<task type="auto" id="27-07">
  <name>Fill bases after saved moves</name>
  <files>dash_render.py, test/js_runner.py</files>
  <action><![CDATA[
    Inside S21's `_DASH_AXIS_FINISH_JS`, add `dash_fill_auto_bases` (TR-27.11) beside `dash_axis_extent`, and call it once per axis inside `dash_axis_finish`, after the final unpadded scale is known (after the by() union for shared axes), with that axis's plan entry. The `autobase` key it reads was added to `_dash_axis_plan` in 27-05; if 27-01 found the plan builder inside `_build_filter_widgets`, stop and report instead (R12). Touch no other line of the constant and none of `_FILTER_JS`. Touch js_runner.py only under TR-27.14's condition. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -k "saved or Chrome or agree"`, test_saved_filter_layers.py, test_js_runner.py and test_by_scales_chrome.py (S21's 100-panel bound).
  ]]></action>
  <verify><![CDATA[Every run reports 0 failed, and `TestTheSavedPageInChrome` reports passed, not skipped; `python3 -c "import dash_render as d; s=d._DASH_AXIS_FINISH_JS; print(s.count('dash_fill_auto_bases('), 'eval(' in s, 'new Function' in s, 'JSON.parse(t' in s)"` prints a count of at least 2, then False False False.]]></verify>
  <done>The saved page's own script re-drew every default base at the moved axis's clamp, matching the served app, under node and in a real browser.</done>
</task>

<task type="auto" id="27-08">
  <name>Certify against Stata in both modes</name>
  <files>none</files>
  <action><![CDATA[
    Run every test file changed in 27-01 to 27-07, plus every test file that names bar, spike, dropline, area, `base` or `VBar` (`grep -l`), plus test_axis_extents.py, test_by_scales.py, test_date_range.py, test_served_filter_move.py and test_html_output.py: `python3 -m pytest <those files> -q -p no:cacheprovider`. A failure outside the flipped list is a pin the list missed. Flip it in place with a `Flipped:` line (R9), never delete it, and re-run. Then run G3 `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider` and `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (expected unchanged: a page with no bar). Through the driver, run `test_wp30_truth.cscript` (`WP30_ONLY=S27`) and `test_help_claims_6.cscript`. Afterwards check that `~/.stata19/console/stata19.rc` still holds `python_exec`.
  ]]></action>
  <verify><![CDATA[All pytest runs report 0 failed; `grep -c "DB-0[1-8] PASS" <scratch>/s27/run_test_wp30_truth.log` prints 8; `grep -c "HC6-23b PASS" <scratch>/s27/run_test_help_claims_6.log` prints 1; `grep -c " FAIL\|SKIP" <scratch>/s27/run_test_wp30_truth.log <scratch>/s27/run_test_help_claims_6.log` prints 0 for each.]]></verify>
  <done>Stata certified the default and explicit bases, the scale and the after-move base, and both modes drew them alike.</done>
</task>

<task type="auto" id="27-09">
  <name>Describe twoway's default base in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Rewrite the `base(#)` entry (:2358-2362) through "draws them from 0." as follows: "{cmd:bar}, {cmd:spike}, {cmd:dropline} and {cmd:area}: the value the bars, spikes, drops and area are drawn from; any number. The axis reaches it, but no tick is placed for it, as in {cmd:twoway}. With no {cmd:base()} they are drawn from 0 when the y axis's scale holds 0, and otherwise from the end of the scale nearest 0, so the axis does not reach 0: {cmd:dash bar mpg weight}, like {cmd:twoway bar mpg weight}, draws its bars up from 10. On a log axis that is the scale's lower end, and on a date axis 0 is 01jan1960. Under {cmd:by()} the panels share one base unless {cmd:yrescale} gives each its own scale, and a {cmd:yaxis(2)} layer takes its base from that axis. The base follows the axis when a filter moves." Keep the sentences from "{cmd:twoway} also takes {cmd:base()} on {cmd:dot}" to the end. In Plot types, after S14's `{ul:Bars and range caps.}` paragraph, add `{ul:Where bars stand.}  {cmd:bar}, {cmd:spike}, {cmd:dropline} and {cmd:area} stand where {cmd:twoway} stands them: on 0 when the axis holds it, otherwise on the end of the axis nearest 0; see {opt base(#)} under Statistical Layer Options.` Touch nothing else. Run `python3 -m pytest test/test_help_conformance.py $(grep -l "base()\|base(#)\|draws them from 0" test/test_help_claims_*.py) -q -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "dash} draws them from 0\|edge of the plot region" dash.sthlp` prints 0; `grep -c "Where bars stand" dash.sthlp` prints 1.]]></verify>
  <done>The help stated twoway's default-base rule, its log, date, by() and second-axis forms and the behaviour after a move, and no longer said dash draws from 0.</done>
</task>

<task type="auto" id="27-10">
  <name>Close P1.17b and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. The title is `WP30_OPEN["P1.17b"]`. Close that BUGS.md entry in place (`- [x]`) and replace its Resolution with: `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.17b). With no base(), GlyphMapper.map_bar, map_spike, map_dropline and map_area draw from a base column whose renderer is tagged as the default (bar's bottom becomes the reserved __dash_base column), and _dash_finish_auto_bases fills it with twoway's base, 0 clamped into the axis's finished scale: 0 when the scale holds it, else the scale's end nearest 0; the lower end on a log axis; 01jan1960 on a date axis; the common scale under by(), each panel's under yrescale, the second axis's for a yaxis(2) layer. It runs at build (the ends of _dash_finish_count_ticks and _dash_common_count_ticks), after a served filter move (_dash_refinish_axes) and after a saved one (_DASH_AXIS_FINISH_JS). The value readers leave every base out of the tick input and a default base out of the hull, so a 0 outside the data no longer extends the axis, and an explicit base() widens the scale without placing a tick (_dash_explicit_base_values). Both renderers draw alike. Pinned by test/test_bar_range_geometry.py::TestTheDefaultBaseIsTwoways::test_the_base_is_twoways, test/test_bar_range_geometry.py::TestTheBaseAfterAMove::test_served, test/test_bar_range_geometry.py::TestTheBaseAfterAMove::test_saved, test/test_wp30_truth.cscript DB-01; fixture test/fixtures/default_base_truth.json. Residual, deferred (WP-30): on a %td to %ty axis the base is the low end of a scale that starts at the data until section 44 gives those axes twoway's tsnatscale scale (twoway 14997 against dash 15000 in the fixture's case); an explicit base(#) on a date axis is read in date units by section 35; a horizontal layer's base is section 49's.`
    2. Delete the `"P1.17b"` key line from `WP30_OPEN`. `WP30_LISTS["P1.17b"]` stays `("Results that change",)`.
    3. In CHANGELOG.md, replace `<!-- WP-30 P1.17b -->` in place with one line, taking the old values from `<scratch>/27-P1.17b-failure.txt`: `- Bars, spikes, droplines and areas stand where twoway stands them. With no base(), dash drew them from 0 and stretched the y axis to 0: bar, spike, dropline and area of a y from 10 to 14 were drawn up from 0 on a y axis from -0.7 to 14.7; they are now drawn from 10, the end of twoway's scale (10 to 14) nearest 0, and the axis stops there, as twoway draws them (dash bar mpg weight now stands on 10). 0 is still used when the scale holds it (yscale(range(0)), ylabel(0(10)40), a layer reaching 0); on a log axis the base is the scale's lower end, where dash drew from 0; on a date axis 0 is 01jan1960 (dash used 01jan1970); under by() the panels share the base of their common scale, each its own with yrescale; a yaxis(2) layer takes its own axis's. An explicit base() widens the axis but places no tick (bar of a y from 10 to 14 with base(5) and ylabel(#5) ticked 4(2)14, now 10(1)14 as twoway). The base follows the axis when a filter moves, in both modes. (WP-30, P1.17b)`
    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, then `git -C $WT merge --no-edit main` (expect `Already up to date.`), then one full run `<scratch>/full_suite_queue.sh $WT <scratch>/27-full-1.log`, launched in the background and waited for on its `exit=` line (E1, E6).
    5. Stage only: `dash_render.py dash.sthlp BUGS.md CHANGELOG.md scripts/extract_default_base_truth.do`, the test files 27-01 to 27-08 changed (`test/test_bar_range_geometry.py test/test_glyphs.py test/test_help_claims_6.py test/test_mode_parity.py test/function_test_map.py test/test_tracking_documents.py test/test_wp30_truth.cscript test/test_help_claims_6.cscript test/test_default_axes.py`, `test/js_runner.py` if changed, and any file 27-08 flipped), and `git add -f test/fixtures/default_base_truth.json`. Check `git diff --cached --name-only` (G6: never CLAUDE.md, .gitignore, AGENTS.md, .ultraplan/ or *.html). Write the message to `<scratch>/s27/msg.txt` in the boundary's form. Run G7 before and after `git commit -F <scratch>/s27/msg.txt`, and report the sha and the message.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/27-full-1.log` prints `exit=0`, and the summary line above it names no `failed` or `error`; `git log -1 --format=%s` ends `(WP-30 P1.17b)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.17b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.17b": "' test/test_tracking_documents.py` prints 0; `grep -c "(WP-30, P1.17b)" CHANGELOG.md` prints 1; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.17b was closed in BUGS.md naming tests that exist, its key was removed, its CHANGELOG marker became the measured Results line, and one green commit on wp30-s27 was ready for the merger.</done>
</task>

## Section completion criteria

- With no `base()`, `bar`, `spike`, `dropline` and `area` are drawn from twoway's `drawn_base` in both modes, on every fixture case but `%td`. On `%td` the base is the low end of dash's scale (S44's residual).
- No default base is in the tick input or the hull. An explicit base is in the hull and not the ticks. A log axis never gets a 0 base.
- `by()`, `yrescale`, `yaxis(2)` and a shared second axis follow twoway's values.
- After a saved move (node and Chrome) and a served move the base is twoway's `if` value, and moving back restores it.
- `default_base_truth.json` is stamped and named by `test_bar_range_geometry.py`. DB-01 to DB-08 and HC6-23b PASS through the driver. Every flip is recorded with its reason.
- The registry tests and G3 parity are green, and S21's time budgets hold.
- There is one green commit `(WP-30 P1.17b)` on `wp30-s27`: the BUGS.md entry closed in place, its `WP30_OPEN` key deleted, and the marker replaced.

## Notes

- **The finisher's order is the design.** The fill must run after the scale is final: after the `by()` union, and after S21's re-finish in both modes. A fill placed before the share gives each `by()` panel its own base, a wrong answer that shows only under `by()` (`TestTheBaseUnderBy`).
- **Two paths bring the provisional value back.** On the saved page, `_FILTER_JS`'s derived-copy loop restores each derived source from its build-time snapshot. In the served app, the redraw's `_live.data = dict(_new.data)` brings the mapper's zero. Both are expected: the fill that follows rewrites them. Never "fix" this by editing the copy loop or the template.
- **Unchanged columns send nothing.** `_dash_finish_auto_bases` compares before writing, so the served app sends no patch when a move leaves the scale as it was. `TestTheFill::test_an_unchanged_column_is_not_rewritten` pins it.
- **Explicit bases stay as they were drawn.** `bar`'s explicit `bottom` stays a value. S35 converts it to date units later through `_base_value`'s call sites. The tag's `zero` is unchanged by S35.
- **Log axes.** The clamp's lower bound is the hull's minimum, which S21 keeps above 0 on a log axis (`_dash_axis_hull` drops values ≤ 0). Never write `zero` itself to a log axis's column.
- **`area`'s `<y>_base` column name** is today's and is not renamed: S27 changes its values, not its name.
- **python_exec hazard** (project memory): concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then exits 222, and a SKIP is not a pass. Check after 27-02 and 27-08.
- **Demo pages** in the repository root are ignored by `.gitignore` (`git ls-files '*.html'` prints nothing), so nothing is regenerated or committed.
- **Shared files (R1-R13).**
  - **R1:** only the S27 block, with its helpers above its header; HC6-23b amended in place in test_help_claims_6.cscript, which no other batch-9 section edits.
  - **R2:** four names after S21's `"_dash_refinish_axes"`. S26's anchor (`"_dash_function_points",`, 33126) is not adjacent. Map entries go under S27's anchor.
  - **R3:** Plot types (one new paragraph after S14's), and the `base(#)` entry in Statistical Layer Options. No batch-9 section edits that title: S19, S32 and S45 are batches 7, 11 and 16.
  - **R4:** the one Results marker is replaced; `WP30_LISTS` is unchanged.
  - **R5:** the one entry and its key line.
  - **R7:** the new extractor is run only by S27; the fixture is never hand-patched.
  - **R8:** `CORPUS` and `MOVE_CORPUS` are appended to.
  - **R9:** flips in place, recorded.
  - **R10:** no combined pin moves. The single-y digest is unchanged (no bar on that page); 27-08 checks it.
  - **R11:** S27 is batch 9's one finisher editor: `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS`. It keeps A9's budgets.
  - **R12:** S27 edits no one-editor symbol: not `_generate_app_source` (S25's in batch 9), not `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets` or the appliers.
- **Commit body line forms** are BRIEF's, with WP-30 ids. `failed at` is `batch-9-base.txt`'s sha.
- **For S35 (batch 12).** Read an explicit `base(#)` in the y variable's date units at the four `_base_value` call sites (`_dash_units_to_axis(_base, kind)`). Keep the tag and `zero`. A mixed date and numeric axis's transform must leave the base column in axis units, or route the clamp through S35's Python twin.
- **For S44 (batch 15).** Once `%td`-`%ty` axes take the tsnatscale scale, tighten DB-08 and `TestTheBaseOnADateAxis` to the fixture's `bases.bar_td` (14997) and drop the residual sentence from the help and BUGS text through S44's own entry.
- **For S49/S55 (batches 17, 19).** A horizontal layer tags `letter "x"` and prop `left` (HBar), `x0` (Segment) or `x1` (HArea). `_dash_finish_auto_bases` and `_dash_axis_plan`'s `autobase` read the letter, so no other change is needed.
- **For S57 (batch 20).** The fill belongs to the same tick as the redraw's data copy and `_dash_refinish_axes`. Name `_dash_finish_auto_bases` in the thread-safety audit.
- **Notes for the closeout (S58).**
  - **DROPIN P1.17:** bullets 3 ("bar's base is 0, not twoway's rule") and 5 ("When 0 is outside the data ...") are closed by P1.17b, commit `<sha>`. With S14's P1.17a, every bullet of P1.17 is closed.
  - **GAPS2-A3:** sub-claims c and f are closed by P1.17b. With P1.17a's a, b, d and e, both entries carrying A3 are closed, so its Tracked line becomes Closed, and `(WP-30, GAPS2-A3)` is appended to P1.17b's Resolution (index BUGS.md row).
  - **AUDIT-42** (TWOWAY_COVERAGE_AUDIT.md rows :63 area "default base is 0 rather than the plot-region edge when zero is outside the data", :64 bar, :65 spike and :66 dropline "default base differs", and :115 fill/bar styling "baseline behavior differs"): tag as corrected by WP-30 P1.17b. The audit's rows are unnumbered, so AUDIT-42 maps to these rows by content.
  - **P1.23 sub-claim 5** ("Base 0 is 1970, not 1960"): its default-base half is closed by P1.17b (01jan1960 clamped); its explicit `base(#)` half is S35's.
  - **dash.sthlp:2358-2368** has been rewritten; HC6-23b now checks dash too.
  - **Residuals to file:** none new. The `%td` equality is S44's, and the explicit date base is S35's. `nodropbase` (P2.7) and `base()` on `dot`/`function` (undrawn; P2.21's surface) are unchanged.
  - **ROADMAP:** the WP-30 entry lists P1.17b and its commit.
  - **AGENTS.md invariant** (E7): "A default base of bar, spike, dropline and area is a tagged data column (renderer tag dash_base:) that only _dash_finish_auto_bases and its JS twin write, from the finished unpadded scale; no value reader counts a base as data."
- **Line numbers** are `c96facd`'s; S01-S26 land first. Symbols and the quoted excerpts are authoritative.
