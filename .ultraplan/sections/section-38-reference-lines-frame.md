# Section 38: Reference lines beyond the frame

> Part of: WP-31 · GAPS3 rows: D12 · Risk: yellow · Batch: 13 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U38

## Overview

**What is wrong today.** GAPS3 D12 (GAPS3.md:162): "Reference lines: an out-of-range `xline()/yline()` is clipped to the frame (Bokeh Span); twoway draws it outside; an asymmetric extended end stays at the last frame on zoom-out." Evidence dash_render.py:39139 (`Span(location=v, dimension=dim, level="underlay", **kw)`). Register rows P2.54 ("clipped at the frame; twoway draws it outside the plot region") and P2.82 ("an asymmetric user scheme's extended end stays at the last re-finish's frame").

Measured at `6370ca4` (read from the code; re-measured by 38-01):
- `_dash_reference_lines` (:38859) draws every position of a copy whose ends both reach the frame as a `Span` (:39138-39141); a `Span`'s length is the frame, so a location outside the x range is not drawn at all, and the range is never widened for it (a Span is no renderer, so `DataRange1d` and `_dash_axis_hull` ignore it).
- A copy with an unextended end (scheme `yesno xyline_extend_low/high` no, or `noextend`) is a headless `Arrow` in data units (:39145-39157) whose perpendicular ends `_dash_refline_extents` (:39201) writes once every range is final, inset by the plot-region margin on the unextended side; the saved page's twin is `dash_refline_extent` (`_DASH_AXIS_FINISH_JS`, :31375-31400). Both run at the finish (build, and after a filter move). The ranges of counted axes already carry ONE zoom `CustomJS` (`_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS`, attached at :32566 on `start` and `end`, guarded by `cb_obj._dash_finishing` :31414, the flag `dash_axis_finish` sets on the RANGE at :31338) -- and that callback rewrites ticks only; it never calls `dash_refline_extent`, so after a wheel zoom or a pan the unextended end sits where the previous finish put it, no longer at the margin.

**After this section**, both renderers, ONE path (DECISIONS A17): every reference line, extended or not, is the headless `Arrow` in data units (D-38.a: Bokeh does not clip it; the Chrome check in 38-01 decides between this and the canvas-unit form), its location fixed and its perpendicular ends written by `_dash_refline_extents` from the flags (`low=high=True` for an extended copy: the range's ends; an unextended side: inset by the margin); so an `xline()`/`yline()` position outside the axis's final range is drawn beyond the plot region as twoway draws it; the range is not widened and the ticks do not change, as in twoway (D-38.c); the ends of every reference line follow a zoom or pan in both modes through ONE added statement at the end of the existing zoom callback `_DASH_AXIS_ZOOM_JS` (D-38.b), and that callback is attached to every range a `lines` entry names. Nothing is printed; no new option.

**Test order and commit rule (rule 7, M6).** One row, one commit `(WP-31 D12)`. 38-01 writes the extractor, the fixture, `test/test_refline_frame.py` and the U38 cases, runs them red and saves `<scratch>/38-01-failure.txt` (with the Chrome probe's result); 38-02 draws; 38-03 flips, help, BUGS, GAPS3, CHANGELOG, commit.

### Section decisions (this file; binding on the executor)

- **D-38.a Every reference line is the existing headless Arrow (one path, A17).** Bokeh clips glyph renderers (`Segment`) to the frame and a `Span` is as long as the frame, but an `Arrow` annotation in data units paints wherever its data coordinates fall (bokeh-web.md §5: "Arrow/Segment with start_units='canvas' are not clipped" -- the clipping is a property of the renderer kind, not the units). 38-01 verifies this in headless Chrome (`test_csp_browser.py`'s harness) with `xline(10000)` on `scatter mpg weight` and reads the pixels of the saved page's canvas at the arrow's x (a column of the xyline colour outside the frame). **If painted (the gate):** the `if low and high:` Span branch (:39138-39142) is deleted and every copy takes the Arrow form of :39145-39157 with its flags; `_dash_refline_extents` already writes both ends from `low`/`high` (an extended copy's ends are the range's ends), so no inside/outside decision exists anywhere, at build or after a zoom, and saved and served pages agree after any range change (M8). **If clipped:** the form is an Arrow with `start_units="canvas"`, `end_units="canvas"` whose px are written by `_DASH_REFLINE_CANVAS_JS`, a `CustomJS` on the figure's `inner_width`, `inner_height` and the two ranges, reading the frame's offset from `fig.frame_left`-style properties only if the installed BokehJS exposes them (`grep -c "inner_left\|frame_left" bokeh/server/static/js/bokeh.js`); failing that, the residual is filed (M12) and the range is widened to include the line with a note naming the difference (the cheaper route of bokeh-web.md §5). The chosen branch is written to `<scratch>/38-01-measured.txt` and the fixture's `_meta.arrow_unclipped`.
- **D-38.b One statement in `_DASH_AXIS_ZOOM_JS` (A17).** The ranges already carry the zoom callback (`_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS`, :32564-32577), whose code already contains `dash_refline_extent` (the finish JS is its prefix) and already returns under the range's `_dash_finishing` flag (:31414). S38 adds ONE statement at the end of `_DASH_AXIS_ZOOM_JS` (:31412; not an R11 constant -- R11 names `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes`, `_dash_finish_count_ticks`): `for (const grp of plan) for (const p of grp.panels) if (p.lines && p.lines.some(l => l.range === ri)) dash_refline_extent(p, models);` and widens `zoom_ranges` (:32548-32550) to include every range a `lines` entry names, so a figure whose axis is not `mode == "count"` (fixed `xlabel(0(10)50)` ticks) also gets the callback. No new constant, no new function, no sliced text, no second callback. The served Python side keeps `_dash_refinish_axes`'s call of `_dash_refline_extents` for moves; `_dash_axis_plan`'s re-attach (:32567-32577 removes the old `_dash_zoom_cb` before attaching) keeps one callback per range after a served move.
- **D-38.c No widening, no note.** twoway does not widen the axis for an out-of-range `xline()`; dash's hull (`_dash_axis_hull`, `dash_axis_hull`) keeps ignoring reference lines. The line is drawn as far as the graph region allows (the canvas); a position past the canvas is not visible, as in twoway.
- **D-38.d The horizontal transpose** (S49 of WP-30 landed): a `yline` under `horizontal` is already an `xline` by the time `_dash_reference_lines` runs; no change.

## Risk: [yellow] -- every reference line becomes an Arrow, and the existing zoom callback gains one statement and runs on every range a reference line names

**Why.** `_dash_reference_lines` runs on every figure in both modes; the zoom callback runs on every zoom.

**Risk factors.**
1. The Arrow's unclipped painting is a BokehJS behaviour, not a documented property (D-38.a's probe decides).
2. The zoom callback fires on `start` and `end` (twice per zoom) and once per finish write; `dash_axis_finish` writes ranges under `r._dash_finishing = true` (:31338) on the RANGE, and the callback already returns on `cb_obj._dash_finishing` (:31414) -- the new statement sits after that guard, so a finish write never re-enters it.
3. Pinned tests: test_reference_lines.py `TestDrawing`, test_refline_extent.py `TestTheEnds`/`TestAfterAFilterMove`, test_axis_options.py `TestReferenceLines` nodes that count `Span`s or assert an out-of-range line is a Span/absent.
4. Batch partners: S39 edits tabs/layout checks and legend label edges; S40 the symbol/pattern translators. None edits `_dash_reference_lines`, `_dash_axis_plan` or `_DASH_AXIS_ZOOM_JS`.

**Mitigation.**
1. The probe runs first; the fallback is written in D-38.a.
2. The statement runs after the existing `cb_obj._dash_finishing` and `_dash_done` returns of `_DASH_AXIS_ZOOM_JS` (:31414-31423) and is idempotent (`dash_refline_extent` writes only changed ends).
3. Flips in place with the reason (R9).
4. No shared function; no copy-list change (no new constant or function survives A17).

## Dependencies

- **Depends on: 01.** **Blocks:** none. S45 (batch 15) edits `_DASH_AXIS_FINISH_JS` next and must keep `dash_refline_extent`'s name and signature (its Notes are told so by this file's "For S45").
- **Parallel batch: 13**, merge order 38, 39, 40. **Can run with S39 and S40:** S39 edits `_dash_parse_tabs`, `_dash_layout_check`, `_dash_apply_legend`'s label regex, dash.ado's `_dash_check_legend`, dash_parse.mata's layout/legend functions, and is batch 13's sole `_generate_app_source` editor; S40 the symbol and pattern translators. S38 edits `_dash_reference_lines`, `_dash_axis_plan` (the `zoom_ranges` list) and `_DASH_AXIS_ZOOM_JS` (one statement). No template edit.

## Evidence

All anchors at `6370ca4`; re-read before editing.

### The Span and the Arrow

```python
39135    # Above the grid, below the glyphs, as twoway draws added lines; one
39136    # assignment for the copy (WP-30 P1.21a).
39137    low, high = _dash_refline_extent_flags(style, scheme)
39138    if low and high:
39139        spans = [Span(location=v, dimension=dim, level="underlay", **kw)
39140                 for v in values]
39141        fig.center = [*fig.center, *spans]
39142        return
39146    from bokeh.models import Arrow
39147    letter = "y" if dim == "height" else "x"
39149    for v in values:
39150        ends = ({"x_start": v, "x_end": v, "y_start": v, "y_end": v})
39151        a = Arrow(start=None, end=None, level="underlay", **ends, **kw)
39155    fig._dash_refline_arrows.extend((a, letter, low, high) for a in arrows)
39156    fig.center = [*fig.center, *arrows]
```

`_dash_refline_extents(fig)` (:39201-39237) writes `arrow.x_start/x_end` (or `y_*`) from `rng.start/end` and `_dash_refline_margin(rng)` (:39190), honouring the flags: an extended side gets the range's end, an unextended side the margin inset. "Called where every range is final: `_dash_axis_plan` (both modes, at build) and `_dash_refinish_axes` (served moves); the saved page's twin is `dash_refline_extent`." `_dash_axis_plan` (:32310) writes per figure `lines.append({"arrow": ai, "range": ri, "letter": letter, "kind": ..., "margin": [fm0, fm1], "low": int(bool(low)), "high": int(bool(high))})` (:32371-32377) -- indices into `models`, no user text -- and stores them as `panel["lines"]` (:32561-32562).

### The JS twin and the existing zoom callback

```js
31375 function dash_refline_extent(panel, models) {
31378     for (const ln of panel.lines) {
31379         const a = models[ln.arrow], r = models[ln.range];
31382         let s = r.start, e = r.end;
31385         let lo = ln.low ? s : s + ln.margin[0] * (e - s);
31386         let hi = ln.high ? e : e - ln.margin[1] * (e - s);
31401         if (typeof a.setv === "function") a.setv(at);
```

Called from `dash_axis_finish` (:31436-31437: "WP-30 P1.21b: the unextended reference lines follow the new ranges"), which sets `r._dash_finishing = true` (:31338) on each range it writes. `_DASH_AXIS_ZOOM_JS` (:31412-31445) is an IIFE: `if (!cb_obj || cb_obj._dash_finishing) return;` (:31414), `const plan = JSON.parse(plan_json); const ri = models.indexOf(cb_obj);`, the `_dash_done` return (:31421-31422), then the tick loop over `p.axes`; it never touches `p.lines`. It is attached at :32564-32577 as `CustomJS(args={"plan_json": plan_json, "models": models}, code=_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS)` to `start` and `end` of every range in `zoom_ranges`, which :32548-32550 fills only for `mode == "count"` axes.

### The range, the hull

`_dash_axis_hull` reads glyph renderers' extents (`_dash_hull_axes`); annotations are not read, so a reference line never widens a range (twoway's rule too, D-38.c).

### Stata rules

- `added_line_options.sthlp` (`/Applications/StataNow/ado/base/a/`, read by the executor): `xline()`/`yline()` "added lines ... extend across the plot region"; `noextend` "the line does not extend into the plot region's margin"; a position outside the axis's range is drawn where it falls (P2.54's measurement: outside the plot region).
- `gridlinestyle-default.style`: `yesno xyline_extend_low/high` yes (research/stata-ground-truth.md, cited at :39207-39209).

### Fixtures on disk

`test/fixtures/refline_truth.json`, `refline_extent_truth.json` (WP-30 P1.21a/b: the asymmetric scheme is `test/fixtures/schemes/`' extend-low-only file used by test_refline_extent.py; the executor reads `test_refline_extent.py:1-150` for its path). S38 adds `refline_frame_truth.json`.

### Tests that pin today's behaviour (flip in place, never delete)

- test/test_reference_lines.py::TestDrawing -- nodes asserting every position of an extended copy is a `Span` (every one becomes an Arrow).
- test/test_refline_extent.py::TestTheEnds, ::TestAfterAFilterMove -- nodes asserting the ends are written only at the finish, or asserting an extended copy has no entry in `fig._dash_refline_arrows` / `panel["lines"]`.
- test/test_axis_options.py::TestReferenceLines, ::TestRepeatedReferenceLines -- nodes counting `Span`s.
- test/test_axis_zoom*.py / test_refline_extent.py nodes that pin `_DASH_AXIS_ZOOM_JS`'s text or the `zoom_ranges` membership (only `mode == "count"` ranges today), if any (38-01's grep decides).
- test_help_claims_*.py nodes reading the help's "within the plot region" sentence for xline/yline, if any (38-01's grep decides).

The exact red list is measured by 38-01 into `<scratch>/38-flips.txt`.

## User stories

- **US-38.1** As a Stata user with `xline(10000)` on an axis that ends at 5,000, I want the line drawn beyond the plot region as twoway draws it, not dropped, so that my reference line is visible.
- **US-38.2** As a dashboard user zooming out, I want an unextended reference line's end to stay at the plot-region margin, as it was before the zoom.
- **US-38.3** As a Stata user, I want the axis unchanged by an out-of-range line, as in twoway.

## Business requirements

- **BR-38.1** An `xline()`/`yline()` position outside the axis's range is drawn beyond the frame, in both modes, and the range and ticks are those of the data alone.
- **BR-38.2** After a wheel zoom, a pan or a reset, an unextended end sits at the margin of the new range, in both modes.
- **BR-38.3** Nothing is printed for either behaviour.

## Technical requirements

- **TR-38.1** `_dash_reference_lines` (:38859): delete the `if low and high:` Span branch (:39138-39142) so every copy, extended or not, takes the Arrow route of :39145-39157 with its own `low`/`high` flags recorded in `fig._dash_refline_arrows` (D-38.a's painted branch); the `Span` import is dropped if nothing else in the function uses it. `_dash_refline_extents` (:39201) is unchanged: it already writes an extended side to the range's end. On D-38.a's clipped branch the Arrow has `start_units="canvas"`/`end_units="canvas"` and `_DASH_REFLINE_CANVAS_JS` writes its px.
- **TR-38.2** `_DASH_AXIS_ZOOM_JS` (:31412): one statement added directly before the closing `})();` (:31444, after the tick loop): `for (const grp of plan) for (const p of grp.panels) if (p.lines && p.lines.some(l => l.range === ri)) dash_refline_extent(p, models);`. It runs after the existing `cb_obj._dash_finishing` (:31414) and `_dash_done` (:31421-31422) returns; `plan`, `ri` and `models` are the IIFE's own locals; `dash_refline_extent` is defined in `_DASH_AXIS_FINISH_JS`, the callback's prefix (:32566).
- **TR-38.3** `_dash_axis_plan` (:32310): directly after `if lines: panel["lines"] = lines` (:32561-32562) add `for _ln in lines:` / `    _r = models[_ln["range"]]` / `    if zoom and _r not in zoom_ranges:` / `        zoom_ranges.append(_r)`, so every range a `lines` entry names is in `zoom_ranges` whatever the axis's `mode`; the attach loop at :32564-32577 is unchanged (one callback per range, the old `_dash_zoom_cb` removed first).
- **TR-38.4** The served app: `_dash_axis_plan` is already called by both modes at build (:39210-39212 docstring) and by `_dash_refinish_axes` after a move, so the callback exists in the served document too; `_dash_refinish_axes` keeps calling `_dash_refline_extents` after a move. No template edit, no `_generate_app_source` edit (S39 owns it in batch 13).
- **TR-38.5** Help (R3): the xline()/yline() paragraph in Axis and Display Options (the lines `grep -n "xline" dash.sthlp | sed -n 1,20p` points at within :3512-4140) gains: "A position outside the axis's range is drawn beyond the plot region, as twoway draws it, and does not widen the axis; the ends of a line the scheme or noextend stops at the plot-region margin follow a zoom or a pan." TWOWAY_COVERAGE_AUDIT.md :139 ("Reference lines") gains "positions beyond the frame".
- **TR-38.6** Parity (R8): `CORPUS` entry `"xline beyond the range"`; `MOVE_CORPUS` entry `"yline noextend, range move then zoom"` under `# WP-31 D12`.

### Code and verbatim texts (copy, do not paraphrase)

**The deletion in `_dash_reference_lines`** (:39138-39142 go; the comment at :39135-39136 stays and gains one line):

```python
    # Above the grid, below the glyphs, as twoway draws added lines; one
    # assignment for the copy (WP-30 P1.21a).
    # WP-31 D12 (D-38.a): every copy is a headless Arrow in data units, which
    # Bokeh does not clip; _dash_refline_extents writes an extended side to
    # the range's end, so a position outside the range is drawn beyond the
    # frame as twoway draws it.  A Span is as long as the frame and shows
    # nothing there.
    low, high = _dash_refline_extent_flags(style, scheme)
    from bokeh.models import Arrow
```

**The statement in `_DASH_AXIS_ZOOM_JS`** (directly before the closing `})();`):

```js
    // WP-31 D12 (D-38.b): the reference lines of every panel this range
    // belongs to follow the zoom or pan; an extended side stays at the
    // range's end, an unextended side at the margin.
    for (const grp of plan) for (const p of grp.panels) if (p.lines && p.lines.some(l => l.range === ri)) dash_refline_extent(p, models);
```

**The `zoom_ranges` widening** (in `_dash_axis_plan`, directly after :32562 `panel["lines"] = lines`):

```python
            # WP-31 D12 (D-38.b): the zoom callback also runs for every range
            # a reference line names, whatever the axis's tick mode.
            for _ln in lines:
                _r = models[_ln["range"]]
                if zoom and _r not in zoom_ranges:
                    zoom_ranges.append(_r)
```

**Help sentence** (Axis and Display Options, xline()/yline() paragraph): `A position outside the axis's range is drawn beyond the plot region, as {cmd:twoway} draws it, and does not widen the axis; a line the scheme or {cmd:noextend} stops at the plot-region margin keeps its ends at the margin through a zoom or a pan.`

**BUGS.md Resolution (D12):** `  - Resolution: Fixed <ddmonyyyy> (WP-31, D12). _dash_reference_lines draws every xline()/yline() as a headless Arrow in data units, which Bokeh paints beyond the frame (verified in headless Chrome), with _dash_refline_extents writing the ends from the extend flags and the range unchanged; _DASH_AXIS_ZOOM_JS ends with one statement calling dash_refline_extent for the panels whose lines name the zoomed range, and _dash_axis_plan attaches that callback to every range a reference line names, so the ends follow zooms and pans; in both renderers. Pinned by test/test_refline_frame.py::TestArrows::test_arrow_not_span, test/test_refline_frame.py::TestZoomCallback::test_zoom_out_follows, test/test_wp31_truth.cscript U38-01; fixture test/fixtures/refline_frame_truth.json. Closes GAPS3 D12 (WP-31, D12).`

**GAPS3 Tracked line (D12), written by 38-03:** `- **D12 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b replaces `pending` with the landed sha; DECISIONS A11).

**CHANGELOG Results line (D12):** `- Reference lines beyond the frame. dash scatter mpg weight, xline(10000) drew nothing (the Span was clipped to the frame), now a line beyond the plot region as twoway draws it, the axis unchanged; after a wheel zoom an unextended end stayed where the last finish put it, now at the margin of the new range. (WP-31, D12)`

**The Chrome probe script** (`<scratch>/s38/probe.py`): builds `figure(x_range=(1760, 4840), y_range=(12, 41))` with `Arrow(x_start=10000, x_end=10000, y_start=12, y_end=41, start=None, end=None, line_color="#c0362c", line_width=4)` in `center`, `output_file` to `<scratch>/s38/probe.html` with `min_border_right=400` so the canvas has room to the right of the frame, and the harness reads `canvas.getContext('2d').getImageData(x, y, 1, 1)` at the arrow's x (`frame_right + (10000 - 4840) / (4840 - 1760) * frame_width`, clamped to the canvas) and the frame's middle y; the line's colour at that pixel is `arrow_unclipped: true`.

### Both-mode call sites (grep first; anchors drift)

| Change | Saved renderer | Served app | Finder |
|---|---|---|---|
| every line an Arrow | `_dash_reference_lines` (copied) from `_make_figure_body` :43808 | the same function | `grep -n "_dash_reference_lines(" dash_render.py` |
| zoom statement | `_DASH_AXIS_ZOOM_JS` (:31412), already in the constants tuple (:46658) | copied | `grep -n "_DASH_AXIS_ZOOM_JS" dash_render.py` |
| `zoom_ranges` widening | `_dash_axis_plan` (both modes call it at build; `_dash_refinish_axes` after a move) | the same | `grep -n "zoom_ranges" dash_render.py` |

### The node harness for the zoom test (`TestZoomCallback`)

test_refline_extent.py::TestJsEqualsPython already runs `dash_refline_extent` under node against stub models (`{start, end}` ranges and `{x_start, ...}` arrows with a `setv` that assigns). `test_zoom_out_follows` builds the saved page of `scatter mpg weight, xline(3000)` under the asymmetric scheme, reads the figure's `x_range._dash_zoom_cb` (the one `CustomJS` `_dash_axis_plan` attached; it is also `x_range.js_property_callbacks["change:start"]`'s only entry), serialises its `args` the way the finisher tests serialise the plan (`plan_json` as is; the arrow and range models become `{x_start, x_end, y_start, y_end}` and `{start, end, _dash_finishing: false}` stubs; `cb_obj` is the x range's stub), prepends `const plan_json = <args.plan_json>; const models = <stubs>; const cb_obj = models[<ri>];`, appends the callback's `code`, sets `cb_obj.start -= 1000; cb_obj.end += 1000` before the call, runs it with `js_runner.run_js(code)` and compares the arrow stub's ends with `_dash_refline_extents` applied to a figure whose range was widened the same way (both to 1e-9). `test_zoom_in_follows` narrows instead. `test_finishing_guard` sets `cb_obj._dash_finishing = true` and asserts the arrow stub is untouched. The callback body is the finisher's own code plus one statement, so a divergence names the statement, not a second implementation.

### What twoway does, in one paragraph for the help author

twoway draws every added line on the graph region's canvas at the data position, clipped only by the canvas; with the default `fextend` the line runs the plot region's full height including the margin; `noextend` stops at the plot region's inner edge (the margin excluded); a position outside the axis is drawn wherever it falls, so `xline(10000)` on an axis ending at 4,840 appears to the right of the plot region when the graph region has room, and is simply off-canvas otherwise. The axis is never widened for it (added lines are not data). dash now matches the first two sentences exactly and the third as far as Bokeh's canvas reaches (the border is `min_border_*` wide; twoway's graph region is the scheme's `margin graph`, S37's `_dash_graph_margin` from batch 12).

### Measured red list procedure (38-01)

On a scratch copy, delete the Span branch and add the zoom statement; run `python3 -m pytest test/test_reference_lines.py test/test_refline_extent.py test/test_axis_options.py test/test_axis_zoom*.py test/test_help_claims_*.py -q -n0 -p no:cacheprovider -rf`; copy the failing ids with reasons into `<scratch>/38-flips.txt`; delete the copy.

### User-visible wording (Q36)

Nothing is printed for an out-of-range line, for the Arrow form, or for a zoom. The only text S38 adds is the help sentence and the CHANGELOG line. No `_dash_warn_once` is added; `_dash_report_suboptions` is not called.

## Boundaries

- Not `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes`, `_dash_finish_count_ticks` (R11; S45 is the next editor). `_DASH_AXIS_ZOOM_JS` is not an R11 constant: S38 adds one statement to it (A17).
- Not the hull or the ranges (D-38.c): no widening of any axis range.
- Not `_FILTER_JS`, the template, `_generate_app_source` (S39's in batch 13), `_make_figure_body`, the appliers (R12).
- Not the reference-line sub-options (WP-30 P1.21a/b landed; S33 draws `tlwidth` etc. on axes, not lines).
- No new option, no refusal, no scheme change, no new constant or function, no copy-list change.

## Stata truth

**New extractor** `scripts/extract_refline_frame_truth.do` (path-free form of scripts/extract_by_grid_truth.do :1-45), run as `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s38/x $WT/scripts/extract_refline_frame_truth.do`, writing `test/fixtures/refline_frame_truth.json` (`git add -f`; `_meta` five keys plus `arrow_unclipped` written by 38-01 from the Chrome probe). twoway only; `sysuse auto`; `set scheme s2color`; SVGs read by `scripts/svg_truth.py`.

| Key | twoway command | Recorded |
|---|---|---|
| `outside.x_10000`, `outside.x_neg` | `scatter mpg weight, xline(10000)`, `xline(-500)` | the axis's range (first and last labelled tick, `svg_axis_reading`), the plot-region box px, the added line's x px and its y extent (beyond the box or not), canvas px |
| `outside.y_60` | `scatter mpg weight, yline(60)` | the same for y |
| `outside.mixed` | `scatter mpg weight, xline(3000 10000)` | both lines' px; the range |
| `outside.noextend` | `scatter mpg weight, xline(10000, noextend)` | the line's y extent (inset or not) |
| `inside.control` | `scatter mpg weight, xline(3000)` | the line's px (guard: unchanged geometry) |
| `zoom.asym` | the asymmetric scheme (extend low only) `xline(3000)` | the line's y extent: top inset by the margin, bottom at the frame -- the geometry the zoom test preserves |

**Truth block** (R1; one row, so one block -- DECISIONS A14): `test/test_wp31_truth.cscript`, header `* ==== S38 D12: Reference lines beyond the frame ====`, helpers `_uf_*`, cases ending `_w31_done U38-0k`:
- **U38-01** `dash scatter mpg weight, xline(10000)`: saved and served figures hold one Arrow at x 10000 in `center`, no Span, and the x range's end equals the data's padded end (the fixture's range within the natscale tolerance); the log holds no note.
- **U38-02** `xline(3000 10000)`: two Arrows (3000 and 10000), no Span, both modes; the 3000 one's ends equal the y range's ends.
- **U38-03** `xline(3000)` under the asymmetric scheme, and `xline(3000) xlabel(0(1000)5000)` under s2color: in both the x range carries one `CustomJS` on `change:start` and `change:end` whose code contains `dash_refline_extent(p, models)` and `cb_obj._dash_finishing`, both modes (the second case has no counted x axis, so only TR-38.3 puts it in `zoom_ranges`).
- **U38-04** The saved page of U38-03 under node: set the x range's `start` to `start - 1000` and `end` to `end + 1000` through the callback's code with the page's models; the arrow's `y_start/y_end` equal `_dash_refline_extents`' values for the new range within 1e-9.

## TDD test stubs

### Regression tests, `test/test_refline_frame.py` (red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, spec)` as test_reference_lines.py; node runs through test_refline_extent.py's `TestJsEqualsPython` machinery; the fixture once.
- Test: fixture `_meta` (six keys) and table keys -- `TestTheFixture::test_meta`, `::test_keys` (guard).
- Test: twoway's out-of-range line is drawn beyond the plot box and the range is the data's (fixture only) -- `::test_twoway_draws_outside` (guard).
- Test: `xline(10000)` yields one Arrow in data units, no Span, in both modes; `xline(-500)`, `yline(60)` likewise -- `TestArrows::test_arrow_not_span[mode-case]` (red: a Span, or nothing).
- Test: `xline(3000 10000)` yields two Arrows and no Span, the in-range one's ends at the range's ends -- `::test_mixed[mode]` (red).
- Test: the range is not widened: `x_range.end` equals the `xline(3000)` control's -- `::test_range_unchanged[mode]` (red if today's Span changes nothing: then guard; the node is kept as a guard either way).
- Test: on the clipped branch (fixture `_meta.arrow_unclipped` false) the Arrow is in canvas units with the canvas callback -- `::test_canvas_branch[mode]` (skipped on the painted branch with the reason in the fixture).
- Test: the zoom callback on a reference-line range's `change:start` and `change:end` is one `CustomJS` whose code contains the TR-38.2 statement and `cb_obj._dash_finishing` -- `TestZoomCallback::test_statement_present[mode]` (red: statement absent).
- Test: a figure whose axis has fixed ticks (`xlabel(0(1000)5000)`, not `mode == "count"`) and a reference line carries the callback on that range; a figure with fixed ticks and no reference line carries none -- `::test_attached_without_count_axis[mode]`, `::test_absent_without_lines[mode]` (red: `zoom_ranges` holds only counted axes today).
- Test: under node, changing `start`/`end` through the callback moves the asymmetric end to the new margin, and a reverting change restores it; with `cb_obj._dash_finishing` set the arrow is untouched -- `::test_zoom_out_follows`, `::test_zoom_in_follows`, `::test_finishing_guard` (red).
- Test: the served document carries one callback per range after `_dash_refinish_axes` (the old `_dash_zoom_cb` replaced, not added to) -- `::test_served_after_move` (red).

### Cases in cscripts
- `test_wp31_truth.cscript` U38-01..U38-04 (red at base).

### Flips (in place, each with a `Flipped:` line)
From `<scratch>/38-flips.txt`; docstrings gain "twoway draws an out-of-range xline()/yline() beyond the plot region, and an unextended end follows a zoom (WP-31 D12)".

### Parity corpus (R8; guards at base)
TR-38.6's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| every line an Arrow, out-of-range drawn | pytest `TestArrows`; U38-01, U38-02; Chrome probe in 38-01 | `outside.*` | yes |
| range unchanged | pytest `TestArrows::test_range_unchanged` | `outside.* inside.control` | yes |
| zoom statement and attachment | pytest `TestZoomCallback` (node); U38-03, U38-04 | `zoom.asym` | yes |
| parity | `python3 -m pytest test/test_mode_parity.py -q -n0` | -- | yes |

**Acceptance criteria**
- **AC-38.1** `xline(10000)` on `scatter mpg weight` is an Arrow in `center`, no Span, in both modes, and the saved page's canvas shows the line beyond the frame in headless Chrome (38-01's probe, repeated in 38-03 on the fixed tree).
- **AC-38.2** The x range's end is unchanged by the out-of-range line.
- **AC-38.3** Every range a reference line names carries the one zoom callback, whose code holds the TR-38.2 statement; under node a range change moves the unextended end to the new margin within 1e-9; the served document carries one callback per range after a move.
- **AC-38.4** `WP31_ONLY=S38` prints U38-01..U38-04 PASS, no SKIP; one green commit `(WP-31 D12)`.

## Tasks

**Commit boundary.** Tasks 38-01 to 38-03 form the one D12 commit, subject `Draw every reference line as an Arrow beyond the frame and follow zooms (WP-31 D12)`, made by 38-03 on `wp31-s38` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s38`. Body per BRIEF: `<scratch>/38-01-failure.txt`, the measured defect (the probe's result named), the change, `Regression:`, `Flipped:` lines, `Fixture: test/fixtures/refline_frame_truth.json (scripts/extract_refline_frame_truth.do)`, `BUGS.md: "<title>" (closed)`, `GAPS3: D12 Tracked`. The Tracked line reads `commit pending` (A11); no amend.

<task type="auto" id="38-01">
  <name>Probe Bokeh, measure twoway, write failing tests</name>
  <files>scripts/extract_refline_frame_truth.do, test/fixtures/refline_frame_truth.json, test/test_refline_frame.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals `<scratch>/batch-13-base.txt` and the branch is `wp31-s38`; `mkdir -p <scratch>/s38/x`. Probe (D-38.a): with a scratch Python script under `<scratch>/s38/` build a Bokeh figure of `scatter mpg weight`'s frame with a headless `Arrow(x_start=10000, x_end=10000, y_start=10, y_end=45)` in data units (and a second in canvas units), save it as a page, open it through test_csp_browser.py's DevTools harness and read the canvas pixels in the column where x=10000 maps (outside the frame): write `arrow_unclipped: true|false` to `<scratch>/38-01-measured.txt`. Create scripts/extract_refline_frame_truth.do by the "Stata truth" table (head from scripts/extract_by_grid_truth.do :1-45; the asymmetric scheme is the one test_refline_extent.py uses), run it through the slot, add `arrow_unclipped` to `_meta` through the extractor's python block reading `<scratch>/38-01-measured.txt` (path from the `DASH_PROBE` environment variable; absent -> `null`), and `git add -f test/fixtures/refline_frame_truth.json`. Create test/test_refline_frame.py with the classes of "TDD test stubs". Append the U38 block (`* ==== S38 D12: Reference lines beyond the frame ====`, U38-01..U38-04) to test/test_wp31_truth.cscript above the marker line. Run `python3 -m pytest test/test_refline_frame.py -q -n0 -p no:cacheprovider -rf > <scratch>/s38/38-01.log 2>&1` and the truth block through the driver (`WP31_ONLY=S38`); write `<scratch>/38-01-failure.txt`; list the pins a simulated fix turns red into `<scratch>/38-flips.txt` ("Measured red list procedure"). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/refline_frame_truth.json'));print(sorted(d['_meta']))"` prints `['arrow_unclipped', 'born_date', 'dash_commit', 'extracted', 'source', 'stata_version']`; `grep -c FAILED <scratch>/s38/38-01.log` is at least 10 and none names `TestTheFixture` or `test_twoway_draws_outside`; `grep -c "U38-0[1-4] FAIL" <scratch>/s38/run_test_wp31_truth.log` prints 4; no SKIP; `test -s <scratch>/38-01-measured.txt`.]]></verify>
  <done>Bokeh's painting of a data-unit Arrow beyond the frame was probed, twoway's out-of-range lines and asymmetric ends were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="38-02">
  <name>Draw every line as an Arrow and follow zooms</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In dash_render.py: in `_dash_reference_lines` (:38859) delete the `if low and high:` Span branch (:39138-39142) and add the comment of "Code and verbatim texts" so every copy takes the Arrow route of :39145-39157 with its flags (TR-38.1; the clipped branch per D-38.a if `_meta.arrow_unclipped` is false); in `_DASH_AXIS_ZOOM_JS` (:31412) add the one statement of TR-38.2 directly before the closing `})();` (:31444, after the tick loop); in `_dash_axis_plan` (:32310) add TR-38.3's four lines directly after `panel["lines"] = lines` (:32562) so every range a `lines` entry names is in `zoom_ranges`. No new constant, function or copy-list entry; `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes` and `_dash_refline_extents` are not edited. Run `python3 -m pytest test/test_refline_frame.py test/test_reference_lines.py test/test_refline_extent.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "not Flip"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_refline_frame.py -q -n0 -p no:cacheprovider` reports 0 failed; `python3 -c "import dash_render as d; print('dash_refline_extent(p, models)' in d._DASH_AXIS_ZOOM_JS, 'cb_obj._dash_finishing' in d._DASH_AXIS_ZOOM_JS)"` prints `True True`; `grep -c "Span(location=v" dash_render.py` prints 0; `git diff --stat` names dash_render.py only.]]></verify>
  <done>Every reference line was drawn as an unclipped Arrow and its ends followed range changes through one statement in the existing zoom callback attached to every range a line names, in both renderers.</done>
</task>

<task type="auto" id="38-03">
  <name>Flip pins, update help and commit D12</name>
  <files>dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
    Flip every node of `<scratch>/38-flips.txt` in place with the reason (R9); append TR-38.6's parity entries under `# WP-31 D12: reference lines beyond the frame`. Repeat 38-01's Chrome probe on the fixed tree with `dash scatter mpg weight, xline(10000)`'s saved page and record the pixel result in `<scratch>/s38/38-03-probe.txt`. Help (R3, TR-38.5) and TWOWAY_COVERAGE_AUDIT.md :139. Close the D12 BUGS.md entry with the Resolution of "Code and verbatim texts" (naming `_dash_reference_lines`, `_dash_refline_extents`, `_DASH_AXIS_ZOOM_JS`'s statement, `_dash_axis_plan`'s `zoom_ranges`, both renderers; a `Residual, deferred (WP-31)` clause only on the clipped branch's fallback), rewrite the D12 Tracked line to `- **D12 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (A11; the merger writes the sha), replace the `<!-- WP-31 D12 -->` marker with the Results line of "Code and verbatim texts". Run `python3 -m pytest test/test_refline_frame.py test/test_reference_lines.py test/test_refline_extent.py test/test_axis_options.py test/test_mode_parity.py test/test_help_conformance.py test/test_tracking_documents.py test/test_statistical_helpers.py -q -p no:cacheprovider` plus the files `<scratch>/38-flips.txt` names, and the truth block through the driver. Stage dash_render.py dash.sthlp TWOWAY_COVERAGE_AUDIT.md BUGS.md CHANGELOG.md GAPS3.md scripts/extract_refline_frame_truth.do test/test_refline_frame.py test/test_wp31_truth.cscript test/test_mode_parity.py and the flipped files; `git add -f test/fixtures/refline_frame_truth.json`; commit once (no amend); grep the message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; the driver log shows `U38-01 PASS` through `U38-04 PASS`, no SKIP; `grep -c "true" <scratch>/s38/38-03-probe.txt` prints 1 on the painted branch; `git log -1 --format=%s` ends `(WP-31 D12)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D12 -->' CHANGELOG.md` prints 0; `grep -c "D12 Tracked:\*\* Closed in WP-31, BUGS.md .*, commit pending\." GAPS3.md` prints 1.]]></verify>
  <done>D12 was closed in BUGS.md naming tests that exist, its Tracked line rewritten with commit pending, its marker replaced, the help described lines beyond the frame and zoom-following ends, and one green commit on wp31-s38 was ready for the merger.</done>
</task>

## Section completion criteria

- An out-of-range `xline()`/`yline()` is drawn beyond the frame in both modes with the range unchanged; the Chrome probe on the fixed tree shows the line.
- Every reference line's ends follow a zoom or pan through the one statement in `_DASH_AXIS_ZOOM_JS` in both modes; node equals Python within 1e-9.
- `refline_frame_truth.json` stamped and named; U38-01..U38-04 PASS; flips recorded; one green commit `(WP-31 D12)` with the Tracked line at `commit pending`; BUGS, GAPS3, CHANGELOG, help, audit, corpus updated.

## Notes

- **R11.** S38 does not edit `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes` or `_dash_finish_count_ticks`. `_DASH_AXIS_ZOOM_JS` is not an R11 constant (A17); S38's one statement there calls the finisher's `dash_refline_extent`, which is already in the same callback's code (the finish JS is its prefix at :32566).
- **The finishing guard** lives on the RANGE: `dash_axis_finish` sets `r._dash_finishing = true` (:31338) while it writes, and `_DASH_AXIS_ZOOM_JS` returns at :31414 on `cb_obj._dash_finishing`; the new statement sits after that return. `dash_refline_extent` only writes changed ends, so a double call is harmless.
- **CustomJS args** are the existing `plan_json` and `models` (indices and model references, never names or user text); CSP tests unaffected (model callbacks are not inline scripts).
- **Both modes without a template edit.** `_dash_axis_plan` runs at build in both modes and after a served move; the callback therefore exists in the served document and is replaced, not duplicated, on a move (:32567-32577). Do not add a template line; `_generate_app_source` is S39's in batch 13.
- **Dropped by A17** (REVIEW-3d F1-F4): the inside/outside split, the Span branch, `_dash_refline_outside`, `_dash_refline_draw_arrows`, `_DASH_REFLINE_ZOOM_JS`, `_dash_refline_extent_js_body`, their copy-list entries, `test_code_is_the_finishers`, `TestServedCopy` and the template route. Nothing of them is written.
- **python_exec hazard** (project memory) after each cscript run; a SKIP is not a pass.
- **Shared files.** R1: the U38 block only; R2: none (no new constant or function); R3: the xline()/yline() paragraph only; R4: one marker; R5: one entry, one Tracked line (`commit pending`); R7: one extractor; R8: corpus; R9: flips; R10: none; R12: no hot function.
- **Commit-body line forms** are BRIEF's; `failed at` is `batch-13-base.txt`'s sha.
- **For S45 (batch 15).** Keep `function dash_refline_extent(panel, models)` as one function with that exact header and keep `_DASH_AXIS_FINISH_JS` as the zoom callback's prefix; S38's statement depends on both.
- **Decisions for maintainer ratification.** D-38.a (every reference line a data-unit Arrow, the Chrome probe as the gate, with the canvas-unit fallback and the widening-with-note last resort), D-38.b (one statement in `_DASH_AXIS_ZOOM_JS` (A17) and `zoom_ranges` holding every range a line names), D-38.c (no widening of any axis range).
