# Section 34-05: Default area outline and key

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: PIC-1 (RH-14) · Risk: green · Batch: 34.1 · Depends on: none · Blocks: none · Tasks: 4, 1 commit · Case-id prefix: Q3405

## Overview

**What is wrong today.** A default `area` plot has no outline in any scheme, and neither has its legend key. twoway strokes the area's whole polygon -- "fill, baseline and closing edges" (audit PIC-1 appendix) -- in the `p#area` line style: colour `p#arealine` (falling back to `p#`), width `linewidth p#area`, drawn at twice the width and clipped to the inside, so one width shows. The audit measured it in every one of the ten schemes it ran: stcolor `#1a85ff` over the fill `#489dff`, s2color `#1a476f` over `#486c8c`, s1mono `#606060` over `#808080`, economist `#3e647d` over `#658397` (PIC-1, RH-14; gr_example #31 `twoway area d.gnp96 date`, tw31.svg `stroke:#1A85FF;stroke-width:19.44` clipped). dash draws only a `VArea`: `map_area` adds a border `Line` along the top only, and only `if any(k in options for k in _LINE_KEYS) or _named_ol:` (dash_render.py:18711), i.e. when `lcolor()`, `lwidth()`, `lpattern()` or a named line style is given; the key is a plain filled rectangle. The pin test even injects `lcolor(red)` to get an outline (test/test_scheme_linewidth.py:279), and dash.sthlp:6041 ("an area's outline width (linewidth parea)") is true only once an outline is asked for (HR-15). RH-14 is the same defect seen through `recast(area)` (audit :2988).

**After this section** (DECISIONS A-6: the full outline twoway draws, measured), in both modes and every scheme: every `area` layer draws its whole outline -- its top, its base and the two short closing edges at its first and last drawn point; under `nodropbase` the top and the chord that closes it -- as one stroked ring in the scheme's `p#area` line style (colour through `color p#arealine -> parealine -> p# -> p`, width `linewidth p#area`, pattern `linepattern p#area`), restyled by `color()`, `lcolor()`, `lwidth()`, `lpattern()` and the named line styles as today. A `cmissing(n)` gap breaks the ring where it breaks the fill (one closed ring per run). The ring follows the fill at build, after a served refit and after a saved move (a saved recount of a `kdensity` or `histogram` drawn with `recast(area)` included). The ring answers no hover: it carries no tooltip, as a ci band's outline carries none. The legend key is an outlined rectangle in the same fill and line; in a by() graph's legend, where a click hides a series, clicking the key hides the area and its outline in every panel; a plain legend stays static, as dash's legends are. `recast(area)` layers (RH-14) take the same outline and keep their WP-31 C16 recount; an area drawn by a ci fit's `fitplot(area)` or `ciplot(area)` keeps the ci layer's two keys. No difference is left to document.

**Why one section.** One item; `map_area`, one ring helper with its saved-page script, one rule in the auto-base helpers, the key rules in `_dash_legend_keys`, and one skip each in `_tag_recast` and `_dash_build_hover` so the new renderers break neither the recast recount nor the tooltips.

**Test order and commit rule.** 34-05-01 measures twoway's outline colours and stroked path per scheme into a fixture, writes every regression test and the cscript block, runs them on the unmodified tree, saves `<scratch>/34-05-01-failure.txt`, no commit. 34-05-02 adds the ring helper, its script and the auto-base rules; 34-05-03 draws the outline and the key and adds the recast and hover skips; 34-05-04 flips the pins, corrects the help and the tracking documents and commits `(WP-34 PIC-1)`.

### Section decisions

- **D-34-05.a. The style chain is a SchemeParser method.** `SchemeParser.area_line_style(index)` returns `{"line": hex, "line_alpha": float|None, "line_width": px, "line_dash": list}` from `self._stub_color_alpha(i, "arealine")` (the p#stub -> pstub -> p# -> p chain, dash_render.py:11107), `self.plot_line_width(index, "area")` (:12746) and `self._lpattern_chain((f"linepattern p{i}area", "linepattern parea", f"linepattern p{i}", "linepattern p"))` (:11273), with `i = index % 15 + 1`. A method, not an `__init__` list, so it reads directives parsed after construction. SchemeParser methods are copied whole into the served app (BRIEF): no copy-list entry.
- **D-34-05.b. The whole outline is one ring (A-6).** The outline is one `Line` renderer over a source of its own (the ring) whose vertices `_dash_area_ring` makes from the fill's own source: for each run of drawn rows, the tops in order, then the bases in reverse order, then the run's first top again (under `nodropbase`: the tops, then the first top, which is the closing chord); runs are separated by one `(nan, nan)` vertex. It replaces today's optional top-edge Line through `_dash_join_glyph`: one renderer, so one dash pattern runs round the polygon and the corners join, as twoway's one stroked path does (twoway strokes the same path it fills: the `<use>` of the fill's path, TR-34-05.5 measures it). The stroke is centred at the `p#area` width (twoway's doubled, clipped stroke shows that width), as rarea's outline is (WP-31 E8).
- **D-34-05.c. The ring follows the fill's source.** The fill's source (`area_source`, :18634) holds at every moment what the ring needs: its x, its top, its base column (filled by `_dash_finish_auto_bases` once the scale is known, :46020) and its zero-height gap vertices (a null row id: `_dash_fill_rebuild` :59916 and its saved twin `dash_fill_rebuild_kept` write None/null in every carried column there). So: (1) at build, and after every served finish, `_dash_finish_auto_bases` rewrites the ring right after it rewrites a base column (`_dash_area_ring_write`); (2) on every area fill source, a `CustomJS` hung on `area_source.js_on_change("data", ...)` runs `_DASH_AREA_RING_JS`, the JS twin of `_dash_area_ring`, on the saved page and in the served browser, after every assignment of the fill's data (the filter's derived-source rewrite :32179-32183, the recast recount's `src.data = dash_recast_data(...)` :34615/:34657/:34668/:34759, `dash_fill_auto_bases`' `src.data = nd` :43268). This is the arrowheads' pattern (`_DASH_ARROW_HEAD_JS` :43847, hung on `pc_source.js_on_change("data", cb)` :25352). The script's `rid` arg is `_ROW_ID_COLUMN` when the fill's source carries that column (every page dash.ado's export builds for a plain area; 34-05-01 confirms it for both modes) and `""` when it does not: a `recast(area)` layer's fill is drawn over `_dash_draw_xy_as`'s fresh `x`/`y` source (:26573), which has no row id and which the saved recount rewrites after every move (WP-31 C16), and a hand-written spec may predate the row identity. With `rid` `""` a row breaks the ring where a value is not finite or at the build's pin rows (`pins`, the cmissing(n) gap vertices of D-14a): such a source is re-split by no filter path (`_dash_join` is hung only with a row id, :18650-18654), and a recast source has no pins (its computed points are finite), so the build's pin rows stay valid on every reassignment that keeps its rows. No edit to `_FILTER_JS`, `_DASH_AXIS_FINISH_JS` or `_DASH_CVAR_RELEVEL_JS` (34-01 is batch 34.1's editor of them, R12). The ring source carries no `_ROW_ID_COLUMN`, so the saved filter's derived-source loop never rewrites it (`if (!_did) continue;`, :32164), and the in-place `dash_fill_repin` (:32006) does not matter: the ring breaks at null-row-id rows whatever their values.
- **D-34-05.d. The ring is no tick or hull input.** Its base vertices hold the default base, which twoway's scale leaves out (WP-30 P1.17b). `_dash_auto_base_props(r, letter)` (:45984) returns `(letter,)` for a renderer tagged `dash_area_outline`, so every reader that already skips a default base skips the ring's coordinates: `_dash_secondary_values` (:45907), `_dash_layer_extent` (:46127) and `_dash_axis_plan` (:46559); the fill (VArea `x`, `y2`) still gives the layer's extent. `_dash_finish_auto_bases` reads `_dash_base_spec`, not `_dash_auto_base_props`, and the ring has no `dash_base:` tag, so the finish never fills the ring's y with the base. The ring's columns are named with the layer's x and y variable names, so `_dash_layer_in_axis_units` (:2149, which keys on field names) gives the ring the fill's date transform. The ring is never named with `_DASH_SWATCH_PREFIX` (that would skip the date transform at :2149).
- **D-34-05.e. The key is a swatch that hides the layer.** `map_area` adds one swatch renderer -- `fig.quad` over one NaN row, named `_DASH_SWATCH_PREFIX + "area_key_<n>"` so every filter, brush, extent and redraw path skips it (`_dash_is_swatch`, :53423) -- in the area's final fill and the ring's final line, stamped `_dash_key_glyph = True`, with `key.js_link("visible", r, "visible")` and `key.js_link("visible", ring_r, "visible")`. `_dash_legend_keys` keys a layer by its `_dash_key_glyph` renderers alone when it has any (for a ci layer, per part: TR-34-05.7), so a by() legend click toggles the swatch and the links hide the fill and the ring; the by() legend item holds each panel's own swatch (`_dash_by_panel_matches`, :55484, matches by position), whose links hide that panel's area (REVIEW R2-5). Only a by() legend is clickable (`click_policy="hide" if panels else "none"`, :55680); a plain legend stays static, as `_dash_apply_legend` deliberately leaves it (:39327-39328), so there the links are inert and nothing changes. `colorvar()` on an area draws nothing, as in twoway: `map_area` never calls `_apply_colorvar`, the VArea's fill is a scalar, and twoway takes the option silently (`cv_silent` of test/fixtures/colorvar_types_truth.json holds `area`; test/test_colorvar_coverage.py). The swatch's colours are therefore literals in every case; the rule that a fill or line colour that is a field or transform spec is replaced on the swatch by `_fill_base` (else `self.scheme.default_color(color_idx, "area")`) for the fill and `area_line_style(color_idx)["line"]` for the line stays only as a guard (REVIEW R2-44). The precedents are the colorvar swatch (`_swatch`, :16581-16594) and the by() clones (`_dash_by_clone_renderers`, :55447).
- **D-34-05.f. The new renderers are neither recounted nor hovered.** The ring (2n+1 rows) and the swatch (one row) join every `kdensity`/`histogram` `recast(area)` layer's renderers. `GlyphMapper._tag_recast` (:22367) returns, tagging nothing, as soon as any added renderer has a column not n long (the loop :22386, its `return` :22396-22397), so it skips both (TR-34-05.10) and tags the fill alone; the ring then follows the recounted fill through its script (D-34-05.c). `_dash_build_hover` (:58731) gives every renderer with a source the layer's tooltip except those it filters (:58803-58809); the ring carries the layer's x and y columns, so at its base vertices a tooltip would show the base as the y value: it is filtered as a ci band's outline is (TR-34-05.4a).

## Risk: [green] -- one ring renderer and one swatch per area layer, a small saved-page script and one rule in the auto-base helpers

**Why.** The ring is derived from a source whose every path (finish, served refit, saved move, gap re-split) already exists and is tested; the script is the arrowheads' pattern; the swatch is the colorvar pattern.

**Risk factors.** 1. Tests that count an area layer's renderers, read the old border Line's source or assume no Line. 2. The legend: the swatch must be the key in `legend()`'s `order()`/`label()` handling and in by()'s legend clones, and must still hide the layer in a by() legend; a ci layer whose band or fit is drawn as an area (`ciplot(area)`, `fitplot(area)`) must keep its band key `n` and its fit key `n + 1`. 3. `nodropbase` (`fig.patch`) areas and `horizontal` areas (`_dash_transpose_layer` turns the ring with the fill). 4. The ring must never reach a tick or hull reader, and never a tooltip. 5. The script and the Python twin must agree (pinned by a node test). 6. A `kdensity` or `histogram` `recast(area)` layer must keep its saved recount (WP-31 C16): `_tag_recast` gives up on a renderer whose columns are not n long.

**Mitigation.** The renderer-count and border-source tests are found by running the area test files (34-05-03) and flipped with reasons; a legend test with `order(2 1)`, a by() legend test, a click test and a ci `fitplot(area)`/`ciplot(area)` key test; `nodropbase`, `horizontal` and `recast(area)` rows; an extent test and a hover test; a node test of `_DASH_AREA_RING_JS` against `_dash_area_ring` over the same vectors; a recount test of `kdensity mpg, recast(area) range(10 45)` after a node move, test/test_recast_refit.py and the WP-31 C16 parity entries in 34-05-03's runs; parity CORPUS and MOVE_CORPUS entries.

## Dependencies

- **Depends on:** none.
- **Blocks:** none. (43-04 later owns legend key shapes; its composites may replace this swatch.)
- **Parallel batch:** 34.1 with 34-01 and 34-04: disjoint. This section edits `map_area`, one new SchemeParser method, `_dash_auto_base_props` (one rule), `_dash_finish_auto_bases` (one call after its write), `_dash_legend_keys` (the key rules of TR-34-05.7), `GlyphMapper._tag_recast` (one `continue`, TR-34-05.10) and `_dash_build_hover` (one filter clause, TR-34-05.4a), and adds `_dash_area_ring`, `_dash_area_ring_write` and `_DASH_AREA_RING_JS`. 34-01 edits `map_histogram`'s Quad branch, `_dash_layer_extent`, `_dash_transpose_layer`, `_dash_axis_plan` and the two JS literals, which call `_dash_auto_base_props` without changing it; `map_histogram`'s recast branch calls `_tag_recast` (:22263) without either section changing that call; 34-04 edits `_dash_frame_sizes`. No JS literal of R12 is touched here.
- **Manifest note:** `_dash_legend_keys` is listed as 34-06's (batch 34.2). 34-05 adds its key rules in batch 34.1 (TR-34-05.7: the `keyed` list as the loop's first statement, the ci branch's part keys, and `if keyed and rends: rends = keyed` immediately before `if ptype in _DASH_CONTOUR_TYPES:`); 34-06 edits its counter one batch later and must keep all three where they are.

## Evidence

### Code at 090d928 (re-read before editing)

```python
18704         _LINE_KEYS = ("lcolor", "lwidth", "lpattern")
18709         _named_ol = any(str(options.get(k, "") or "").strip()
18710                         for k in ("lstyle", "alstyle", "blstyle"))
18711         if any(k in options for k in _LINE_KEYS) or _named_ol:
18712             # Default border color = the fill's resolved colour, unblended
18713             border_color = _fill_base or "#aec7e8"
 ...
18722             _dash_join_glyph(
18723                 self, fig, {k: v for k, v in options.items()
18724                             if k != "connect"},
18725                 dict(x=xvar, y=yvar, source=border_source,
18726                      line_color=border_color,
18727                      line_width=self.scheme.plot_line_width(color_idx,
18728                                                             "area")),
18729                 role="aline" if _named_ol else None)
```
(`map_area` def :18567; `_y1_col = f"{yvar}_base"` :18631; `area_source` :18634; the gap rebuild and `_pin_rows` :18640-18656; `_fill_base` :18658; fill `fig.patch(...)` under nodropbase :18680 or `fig.varea(...)` :18687; `self._tag_base(r, "y1", _base is None, _zero)` :18694; `return r` :18732.) `_dash_join_glyph` (re-read) applies `mapper._apply_line_opts(r, options)` or `(..., role=role)` after `fig.line(**line_kwargs)`. `_dash_legend_keys` (:58213) starts its loop with `rends = [r for r in rends if not _dash_is_swatch(r) and "dash_dots" not in ...]` (:58236-58237). Both modes collect a layer's renderers as a slice of `fig.renderers` (saved :63800, served literal :70623-70625), so the ring and the swatch reach the key code, the date conversion and the served redraw's source pairing in both. `_dash_finish_auto_bases` (:46020) writes `data[field] = new` (:46063) and `n += 1` for each default base column that changed. `_dash_auto_base_props` (:45984):
```python
    bs = _dash_base_spec(r)
    return (bs["prop"],) if bs and bs["auto"] and bs["letter"] == letter \
        else ()
```
`GlyphMapper._tag_recast(added, xs, ys, cfg, rows)` (:22367; called for `histogram` at :22263 and `kdensity` at :22765 with `list(fig.renderers[_before:])`, everything `_dash_draw_xy_as` drew) -- its first loop, which gives up on the whole layer:
```python
22386         for g in added:
22387             ds = getattr(g, "data_source", None)
22388             if not isinstance(ds, ColumnDataSource) or not ds.data:
22389                 return
 ...
22396                 if a.ndim != 1 or len(a) != n:
22397                     return
```
`_dash_build_hover` (:58731), the renderers it gives a tooltip:
```python
58803     _rends = [r for r in fig.renderers if getattr(r, "data_source", None)
58804               is not None
58805               and "dash_ci_outline" not in (getattr(r, "tags", None) or [])
58806               and "dash_join_none" not in (getattr(r, "tags", None) or [])
58807               # WP-31 B5b: dot's rows answer for nothing; the marker does.
58808               and "dash_dots" not in (getattr(r, "tags", None) or [])]
```
`_dash_legend_keys`' ci branch (:58239-58256): `band = [r for r in rends if getattr(r, "_dash_ci_band", False) or type(getattr(r, "glyph", None)).__name__ in ("VArea", "Band", "Patch")]`, `line = [r for r in rends if r not in band and not getattr(r, "_dash_nofit", False)]`, keys `(n, band)` and `(n + 1, line)`, `n += 2; continue`; then `if ptype in _DASH_CONTOUR_TYPES:` (:58258). A ci layer's `fitplot(area)` fit is drawn by `_dash_draw_xy_as` -> `map_area` (:14934-14937; `"area"` is in `_RECAST_DRAWN`, :26543), and `ciplot(area)` draws its band the same way through `_dash_draw_range_as`, every renderer of it stamped `_dash_ci_band = True` (:14927-14928). Only a by() legend is clickable: `click_policy="hide" if panels else "none"` (:55680); `_dash_apply_legend` leaves a plain legend static on purpose (:39327-39328).

### twoway's rule and truth

`linestyle p#area` = width `p#area`, colour `p#arealine`, pattern `p#area` (dash's own style table, dash_render.py:9927-9931). Measured by the audit (PIC-1 appendix, picture/corpus c2 `area le_wm year` in s1mono, s1color, s2mono, sj, economist, meta, stmono1, stgcolor, stcolor, s2color): the polygon -- "fill, baseline and closing edges" -- is stroked and clipped inside; the key rectangle is outlined. RH-14: `qfit recast(area)`, `function recast(area) horizontal` and `rarea recast(area)` draw the same stroke (tw_P11.svg:381-382). TR-34-05.5 records the colours and the stroked path's shape per probe.

### Fixtures on disk

None for area outlines. test/fixtures/colour_width_edges_truth.json `ol.rarea` holds the rarea precedent.

### Tests pinning today's behaviour (flip, never delete)

- test/test_scheme_linewidth.py:279 `opts = {"lcolor": "red"} if ptype == "area" else {}` -- flip to `{}` for area with the reason "the area's outline is drawn by default (WP-34 PIC-1)"; :468 `test_economists_area_outline_is_parea` stays green.
- Tests asserting an area layer has one renderer or no Line, or reading the old border Line's source (its `border_source` columns or its `_dash_join` spec), e.g. in test/test_area_cmissing.py, test/test_named_styles.py and test/test_saved_filter_layers.py -- found in 34-05-03's runs and flipped there with the reason "the outline is the area's whole polygon, one ring rebuilt from the fill's source (WP-34 PIC-1, A-6)".
- test/test_recast_refit.py `_recast_renderers` (:68-70) returns every non-swatch renderer of g2, and `TestRecastRefit::test_tagged` / `test_js_equals_python` require each to carry `_dash_agg_config`; for target `area` the ring is now among them and is deliberately untagged (it follows the fill through its script, D-34-05.f). Flip the helper in place to leave out renderers tagged `dash_area_outline` too, with `# Flipped (WP-34 PIC-1): an area's outline ring is drawn from its fill's source by its own script; the fill is the recounted renderer.`

## User stories

- US-34-05.1 As a Stata user with an existing twoway command, I want `dash area le_wm year` outlined all round as twoway outlines it, in my scheme, so that the picture matches.
- US-34-05.2 As that user, I want the area's legend key outlined too.
- US-34-05.3 As a dashboard author, I want the outline to follow cmissing() gaps and filter moves as the fill does, and, in a by() graph's legend, a click on the key to hide the area with its outline in every panel.

## Business requirements

- BR-34-05.1 Every area layer is outlined all round -- top, base and the closing edges at its first and last drawn point, or under nodropbase the chord that closes it -- in the scheme's area line colour, width and pattern, in both modes and every shipped scheme.
- BR-34-05.2 The area's legend key is a rectangle in the area's fill with that outline; in a by() graph's legend, where a click hides a series, clicking the key hides the area and its outline in every panel; a plain legend stays static, as dash's legends are.
- BR-34-05.3 color(), lcolor(), lwidth(), lpattern() and the named line styles restyle the outline as they do today.
- BR-34-05.4 The outline breaks where cmissing(n) breaks the fill and follows filter moves in both modes, a recast layer's recount included.
- BR-34-05.5 The outline changes no axis: the ticks and span of an area's axes are what they are today.
- BR-34-05.6 A `kdensity` or `histogram` drawn with `recast(area)` is still recounted after a saved filter move, and its outline follows the recounted area; a ci fit whose fit or band is drawn as an area keeps its two legend keys, the band's and the fit's.
- BR-34-05.7 Hovering over the outline shows no tooltip; the area's own tooltip is unchanged.

## Technical requirements

- TR-34-05.1 `SchemeParser.area_line_style(self, index)` per D-34-05.a, placed beside `plot_line_width` (:12746; any position inside the class, methods are copied whole). `line_alpha` is `_stub_color_alpha`'s opacity (None when the scheme declares none).
- TR-34-05.2 New module function after `_dash_fill_rebuild` (re-read; it follows `_dash_fill_vertices`):
```python
def _dash_area_ring(xs, y1s, y2s, breaks=None, drop=True):
    """An area's whole outline as one ring of vertices (WP-34 PIC-1,
    DECISIONS A-6): twoway strokes the polygon it fills, so each run of
    drawn rows is the run's tops (*y2s*) in order, then with *drop* its
    bases (*y1s*) in reverse, then its first top again; without *drop*
    (nodropbase) the tops and then the first top, the closing chord.  A
    run is a maximal sequence of rows whose x and top (and with *drop* its
    base) are finite and that *breaks* does not mark (map_area's zero-height
    gap vertices); runs are separated by one (nan, nan) vertex.  Returns two
    float arrays.  Pure, O(n); the twin of _DASH_AREA_RING_JS."""
    x = _dash_float_values(xs)
    t = _dash_float_values(y2s)
    b = _dash_float_values(y1s) if drop else None
    n = min(len(x), len(t), len(b) if drop else len(t))
    brk = (np.zeros(n, dtype=bool) if breaks is None
           else np.asarray(list(breaks)[:n], dtype=bool))
    ok = np.isfinite(x[:n]) & np.isfinite(t[:n]) & ~brk
    if drop:
        ok &= np.isfinite(b[:n])
    ox, oy = [], []
    i = 0
    while i < n:
        if not ok[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and ok[j + 1]:
            j += 1
        if ox:
            ox.append(np.nan)
            oy.append(np.nan)
        ox.extend(x[i:j + 1])
        oy.extend(t[i:j + 1])
        if drop:
            ox.extend(x[i:j + 1][::-1])
            oy.extend(b[i:j + 1][::-1])
        ox.append(x[i])
        oy.append(t[i])
        i = j + 1
    return np.asarray(ox, dtype=float), np.asarray(oy, dtype=float)
```
  and after it:
```python
def _dash_area_ring_write(r):
    """Rewrite the outline ring map_area hung on area renderer *r*
    (``r._dash_area_ring``) from *r*'s own source (WP-34 PIC-1): a row
    breaks the ring where its _ROW_ID_COLUMN value is None (the fill's
    zero-height gap vertices), or, on a source without that column, where
    its index is one of the build's pin rows.  True when it wrote; never
    raises."""
    spec = getattr(r, "_dash_area_ring", None)
    if not spec:
        return False
    try:
        d = r.data_source.data
        x, y1, y2 = spec["x"], spec["y1"], spec["y2"]
        rid = d.get(_ROW_ID_COLUMN)
        n = len(d[y2])
        if rid is not None:
            brk = [v is None for v in list(rid)[:n]]
        else:
            pins = set(int(i) for i in spec.get("pins") or ())
            brk = [i in pins for i in range(n)]
        rx, ry = _dash_area_ring(d[x], d[y1] if y1 else None, d[y2], brk,
                                 drop=bool(y1))
        spec["ring"].data = {x: rx, y2: ry}
        return True
    except Exception:  # noqa: BLE001 -- never raises
        return False
```
- TR-34-05.3 New module constant `_DASH_AREA_RING_JS` beside `_DASH_ARROW_HEAD_JS` (:43847), with a `#:` comment naming WP-34 PIC-1, A-6 and `_dash_area_ring` as its twin. Args (all data, read with `hasOwnProperty` only): `src` (the fill's source), `ring`, `x`, `y1` (`""` under nodropbase), `y2`, `rid` (`_ROW_ID_COLUMN` when the fill's source has that column, else `""`, TR-34-05.4), `pins` (the build's pin rows, a list of ints, read only when `rid` is `""`; `_dash_area_ring_write`'s pins branch is its Python side). Body:
```js
const d = src.data, has = (c) => !!c && Object.prototype.hasOwnProperty.call(d, c);
if (!has(x) || !has(y2) || (rid && !has(rid)) || (y1 && !has(y1))) return;
const X = d[x], T = d[y2], B = y1 ? d[y1] : null, R = rid ? d[rid] : null;
const P = new Set((pins || []).map(Number));
const n = Math.min(X.length, T.length, R ? R.length : T.length, B ? B.length : T.length);
const num = (v) => (v === null || v === undefined || v === "") ? NaN : Number(v);
const ok = [];
for (let i = 0; i < n; i++) {
    const brk = R ? (R[i] === null || R[i] === undefined) : P.has(i);
    ok.push(!brk && isFinite(num(X[i])) && isFinite(num(T[i])) && (!B || isFinite(num(B[i]))));
}
const ox = [], oy = [];
for (let i = 0; i < n; ) {
    if (!ok[i]) { i++; continue; }
    let j = i;
    while (j + 1 < n && ok[j + 1]) j++;
    if (ox.length) { ox.push(NaN); oy.push(NaN); }
    for (let k = i; k <= j; k++) { ox.push(num(X[k])); oy.push(num(T[k])); }
    if (B) for (let k = j; k >= i; k--) { ox.push(num(X[k])); oy.push(num(B[k])); }
    ox.push(num(X[i])); oy.push(num(T[i]));
    i = j + 1;
}
const nd = {};
nd[x] = ox;
nd[y2] = oy;
ring.data = nd;
```
  No user text reaches the script: column names arrive as args (they are Stata variable names and dash's reserved names) and are used only as keys. With `rid` `""` and no pins (a `recast(area)` layer's fill) `brk` is false on every row, so the ring breaks only where a value is not finite, which is `_dash_area_ring(xs, y1s, y2s, None)`.
- TR-34-05.4 `map_area`: replace the block from `_LINE_KEYS = ...` (:18704) to the `_dash_join_glyph(...)` call's end (:18729) with an unconditional outline. Keep `_named_ol` (:18709-18710). Then: `_als = self.scheme.area_line_style(color_idx)`; `_oa_c = "color" in _oa` (twoway: `color()` sets the outline too); `_drop = not _nodrop`; `_rx, _ry = _dash_area_ring(area_source.data[xvar], area_source.data[_y1_col] if _drop else None, area_source.data[yvar], [v is None for v in area_source.data[_ROW_ID_COLUMN]] if _ROW_ID_COLUMN in area_source.data else [i in set(_pin_rows if _pin_rows is not None else ()) for i in range(len(area_source.data[yvar]))], drop=_drop)`; `ring = ColumnDataSource({xvar: _rx, yvar: _ry})`; `ring_r = fig.line(x=xvar, y=yvar, source=ring, line_color=(_fill_base if _oa_c else _als["line"]) or "#aec7e8", line_width=_als["line_width"], line_dash=list(_als["line_dash"]), line_alpha=1.0 if _als["line_alpha"] is None else _als["line_alpha"])`; `ring_r.tags = ["dash_area_outline"]`; then `_opts = {k: v for k, v in options.items() if k != "connect"}` and `self._apply_line_opts(ring_r, _opts, role="aline") if _named_ol else self._apply_line_opts(ring_r, _opts)` (exactly what `_dash_join_glyph` applied to the old border Line); `r._dash_area_ring = {"ring": ring, "x": xvar, "y1": _y1_col if _drop else "", "y2": yvar, "pins": [int(i) for i in (_pin_rows if _pin_rows is not None else ())]}`; then, on every area fill source (D-34-05.c), `area_source.js_on_change("data", CustomJS(args=dict(src=area_source, ring=ring, x=xvar, y1=_y1_col if _drop else "", y2=yvar, rid=_ROW_ID_COLUMN if _ROW_ID_COLUMN in area_source.data else "", pins=list(r._dash_area_ring["pins"])), code=_DASH_AREA_RING_JS, name="dash_area_ring"))` (`CustomJS` imported inside the function, as `_CJS` is at :25323). Under nodropbase the same ring is drawn over the Patch's rows (`_drop` False). The ring's tooltip is filtered by TR-34-05.4a. The `_area_ids` lines (:18619-18623) fed only the old border source: delete them with it (the fill's source keeps its row id through `_carry_cols`).
- TR-34-05.4a `_dash_build_hover` (:58731): in the `_rends` filter (:58803-58808), after the `"dash_ci_outline"` clause, add `and "dash_area_outline" not in (getattr(r, "tags", None) or [])`, and extend the comment above it (:58798-58802) with "An area's outline ring (WP-34 PIC-1) is its polygon too: like a ci band's outline, its vertices answer for nothing; the fill does." Both modes call it (the served app copies it by name, the function tuple :67420): no copy-list change.
- TR-34-05.5 Stata truth: create `scripts/extract_area_outline_truth.do` (header, root and `_meta` pattern of scripts/extract_ts_operator_truth.do:1-90, git commit through `shell` into a file, read back; the python block reads globals by `Macro.getGlobal`; a backtick written `\x60`). (a) Colours, for each of s1mono s1color s2mono s2color sj economist meta stmono1 stgcolor stcolor: `sysuse uslifeexp, clear`; `twoway (area le_wm year) (area le_bm year) (area le_wf year), scheme(<s>) nodraw`; record for plot k = 1..3 `.Graph.plotregion1.plot<k>.style.area.linestyle.color.rgb`, `.style.area.linestyle.width.val` (read the class path that test_scheme_linewidth.py's extractor reads; re-read scripts/extract_scheme_truth.py for the width key) and `.style.area.shadestyle.color.rgb`, plus the same with `lcolor(red)` on plot 1. (b) The stroked path, under stcolor, for probe `plain` `twoway area le_wm year`, probe `nodrop` `twoway area le_wm year, nodropbase` and probe `gap` (`replace le_wm = . in 40/45` on a fresh `sysuse uslifeexp`) `twoway area le_wm year, cmissing(n)`: `graph export` to `a_<probe>.svg` in the script's own work folder (a global set at its top, as scripts/extract_ts_operator_truth.do's `ZT_WORK` is, :303), `as(svg) replace`; in the python block, find each element (`<use ...>` or `<path ...>`) whose style strokes the plot-1 line colour of (a), resolve a `<use>`'s `href`/`xlink:href` to the `<path id=...>` it names, split its `d` into subpaths at each `M`/`m`, and record per subpath `{"closed": <it ends with Z/z or its last point equals its first within 0.01 units>, "base_corners": <it has a vertex at the subpath's largest SVG y, within 0.5 units, at both its smallest and its largest x, within 0.5 units>}`. (c) The data: the 100 rows of `year` and `le_wm`. Output `test/fixtures/area_outline_truth.json` `{"_meta": {...}, "schemes": {"<s>": [{"line": "#rrggbb", "fill": "#rrggbb", "width": <val>}, ...]}, "paths": {"plain": [...], "nodrop": [...], "gap": [...]}, "data": {"year": [...], "le_wm": [...]}}`; `git add -f`. Expected (the audit's reading): `plain` one subpath, closed, with base corners; `gap` two such subpaths; `nodrop` one closed subpath without base corners. If the fixture differs, the fixture wins and the ring rule is changed to match it before 34-05-03 (record it in the handback).
- TR-34-05.6 The key swatch (D-34-05.e), after the ring is styled: `_kf = r.glyph.fill_color if isinstance(r.glyph.fill_color, str) else (_fill_base or self.scheme.default_color(color_idx, "area"))`; `_kl = ring_r.glyph.line_color if isinstance(ring_r.glyph.line_color, str) else _als["line"]`; `key = fig.quad(left=[float("nan")], right=[float("nan")], top=[float("nan")], bottom=[float("nan")], fill_color=_kf, fill_alpha=r.glyph.fill_alpha, line_color=_kl, line_width=ring_r.glyph.line_width, line_dash=ring_r.glyph.line_dash, line_alpha=ring_r.glyph.line_alpha, name="%sarea_key_%d" % (_DASH_SWATCH_PREFIX, len(fig.renderers)))`; `key._dash_key_glyph = True`; `key.js_link("visible", r, "visible")`; `key.js_link("visible", ring_r, "visible")`. A hidden outline (`lcolor(none)`, alpha 0) gives a key with line alpha 0. No `legend_label`.
- TR-34-05.7 `_dash_legend_keys` (:58213), three edits, every layer with no `_dash_key_glyph` renderer keyed exactly as today: (1) as the loop's first statement, `keyed = [r for r in rends if getattr(r, "_dash_key_glyph", False)]` (before the swatch filter, which drops the swatches, :58236-58237); (2) in the ci branch (:58239-58256), `band = [r for r in rends if getattr(r, "_dash_ci_band", False) or (type(getattr(r, "glyph", None)).__name__ in ("VArea", "Band", "Patch") and getattr(r, "_dash_area_ring", None) is None)]` -- a `fitplot(area)` fit's VArea carries `_dash_area_ring` and no `_dash_ci_band`, so it is the fit, not the band; `line` stays `[r for r in rends if r not in band and not getattr(r, "_dash_nofit", False)]`; then `bkey = [k for k in keyed if getattr(k, "_dash_ci_band", False)]` (a `ciplot(area)` band's swatch) and `lkey = [k for k in keyed if not getattr(k, "_dash_ci_band", False) and not getattr(k, "_dash_nofit", False)]` (a `fitplot(area)` fit's swatch; under nofit the fit's swatch is `_dash_nofit` with the rest of the fit, :14961-14965, so `lkey` is empty and the line part is all hidden); the keys become `out.append((n, ser[0][0], bkey or band))` and `out.append((n + 1, ser[-1][0], lkey or line))`, each under its existing `if band:` / `if line:`; (3) after the ci branch, immediately before `if ptype in _DASH_CONTOUR_TYPES:` (:58258), `if keyed and rends: rends = keyed`. Placed there, a ci layer's `rends` are never replaced by its swatches before the band test, which would then find no band and drop key `n` of a `fitplot(area)` layer. The served app copies `_dash_legend_keys` by name (the function tuple, :67429): no copy-list change.
- TR-34-05.8 `_dash_auto_base_props` (:45984): first statement `if "dash_area_outline" in (getattr(r, "tags", None) or ()): return (letter,)`; the docstring gains "an area's outline ring (WP-34 PIC-1) is no tick or hull input on either axis: its base vertices are the default base". `_dash_finish_auto_bases` (:46020): right after `data[field] = new` (:46063), `_dash_area_ring_write(r)`. The docstring gains one sentence naming the ring.
- TR-34-05.10 `GlyphMapper._tag_recast` (:22367): in its first loop, `for g in added:` (:22386), as the loop's first statement, `if "dash_area_outline" in (getattr(g, "tags", None) or ()) or _dash_is_swatch(g): continue` -- the ring and the key swatch are drawn from the fill and are not recount targets (D-34-05.f) -- and the docstring gains "An area's outline ring and its key swatch (WP-34 PIC-1) are skipped: the ring follows the recounted fill through its own script." The second loop tags only `plans`, so the fill alone gets `_dash_agg_source`, `_dash_agg_config` and `_dash_agg_rows`. A staticmethod of GlyphMapper, copied whole into the served app; `_dash_is_swatch` is a module function both modes have (the function tuple, :67735).
- TR-34-05.9 Copy lists (R2; re-read the anchors): `"_dash_area_ring", "_dash_area_ring_write",` after `"_dash_axis_scale", "_dash_finish_auto_bases",` (:67557); `"_DASH_AREA_RING_JS",` after `"_DASH_ARROW_HEAD_JS", "_DASH_ARROW_ANGLE_DEG"` in the constants tuple (:67259). test/function_test_map.py: `'_dash_area_ring': 'test/test_area_outline.py::TestTheRing::test_the_helper',`, `'_dash_area_ring_write': 'test/test_area_outline.py::TestTheRing::test_the_finish_rewrites_the_ring',`.

## Boundaries

- Do not touch `map_rarea`, `map_bar` or the colorvar swatches; do not touch `_dash_layer_extent`, `_dash_axis_plan`, `_dash_secondary_values`, `_FILTER_JS`, `_DASH_AXIS_FINISH_JS` or `_DASH_CVAR_RELEVEL_JS` (34-01's in this batch, R11/R12): D-34-05.d works through `_dash_auto_base_props` alone.
- `_dash_legend_keys`: only TR-34-05.7's three edits; its counter (`n += 2`) is 34-06's.
- `GlyphMapper._tag_recast`: only TR-34-05.10's `continue` and docstring sentence; `_dash_build_hover`: only TR-34-05.4a's clause and comment. Do not edit `map_histogram` (34-01's in this batch) or its `_bin_tag` helper.
- No change to `_dash_apply_legend` (34-06's in batch 34.2, R12), `_make_figure_body`, `_dash_by_panel_matches` or `GlyphMapper._apply_colorvar` (R12).
- No `_ROW_ID_COLUMN` on the ring source (D-34-05.c); no new option or syntax.

## Stata truth

`scripts/extract_area_outline_truth.do` -> `test/fixtures/area_outline_truth.json` (TR-34-05.5), run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_area_outline_truth.do`. Truth block, inserted directly above the first block whose `S<MM>` is higher than S05 (BRIEF "Block order"), or above `* ==== append new blocks above this line ====` if there is none. Its cases are live twoway-against-dash comparisons only (REVIEW R2-47; the page model is pytest's); a python helper above the block reads twoway's SVG (TR-34-05.5 (b)'s reader) and the dash page's JSON (the Line renderer tagged `dash_area_outline` and its ring source):

```
* ==== S05 PIC-1: the default area outline ====
local only : env WP34_ONLY
if inlist("`only'", "", "S05") & `: list posof "S05" in w34_run' {
    display as text "S05 start " c(current_date) " " c(current_time)
    ...
    display as text "S05 end " c(current_date) " " c(current_time)
}
* ==== end S05 ====
```
- Q3405-1: for stcolor, s2color and economist, twoway's stroked outline colour for `twoway area le_wm year, scheme(<s>)` (its exported SVG) equals the line colour of the outline of `dash area le_wm year, scheme(<s>) saving(<dir>/a_<s>.html, replace)`.
- Q3405-2: for the `plain` and `gap` probes (stcolor), the number of closed subpaths twoway strokes equals the number of runs of the dash page's ring (NaN-separated, each closed: its first vertex equals its last), and each run visits the base at its first and last x exactly where twoway's subpath has base corners.

## TDD test stubs

Regression tests (red at the base), in test/test_area_outline.py (pages built with test/test_mode_parity.py's `_spec`/`plot_for` and the saved/served helpers test/test_scheme_linewidth.py uses; the uslifeexp rows from the fixture's `data`):
- Test: `area_line_style(k)` equals the fixture's outline colour for plots 1-3 in all ten schemes -- ::TestTheStyle::test_matches_twoway
- Test: `_dash_area_ring` over a plain run, a run with a NaN row, two runs split by `breaks`, nodrop, a one-row run and no rows -- ::TestTheRing::test_the_helper (red: NameError)
- Test: `_DASH_AREA_RING_JS` run under node through test/js_runner.py with stub `src`/`ring` objects over the helper's vectors (a row-id column holding null at the gap rows) writes exactly `_dash_area_ring`'s vertices; with `rid` `""` (a source with no row-id column) and `pins` holding the gap rows it writes `_dash_area_ring(..., breaks=<those rows>)`, with `rid` `""` and no pins `_dash_area_ring(..., None)`; and with `rid` naming a column the source lacks it writes nothing -- ::TestTheRing::test_js_twin
- Test: `_dash_finish_auto_bases` on a built area figure rewrites the ring with the finished base, and `_dash_auto_base_props(ring_r, "y")` is `("y",)` -- ::TestTheRing::test_the_finish_rewrites_the_ring
- Test: a default area layer draws one Line tagged `dash_area_outline` (and no other Line) in `area_line_style`'s colour, width and pattern, in both modes and ten schemes -- ::TestTheOutline::test_default_outline[saved|served]
- Test: the ring of the fixture's `plain`, `gap` and `nodrop` probes has twoway's subpaths: as many runs, each closed, with base visits where twoway has base corners -- ::TestTheOutline::test_ring_matches_twoway[saved|served]
- Test: `lcolor(red)`, `lwidth(thick)`, `lpattern(dash)`, `color(green)` and `lstyle(p3)` restyle the ring as they restyled the old optional outline -- ::TestTheOutline::test_restyle[saved|served]
- Test: a saved move (the node harness test/test_saved_filter_layers.py uses, then the ring script on the moved fill source) and a served refit rebuild the ring from the kept rows, its base the finished base -- ::TestTheOutline::test_gap_and_move[saved|served]
- Test: `nodropbase` closes the ring along the chord over the Patch's rows -- ::TestTheOutline::test_nodropbase[saved|served]
- Test: `line le_wm year, recast(area)` is outlined in the area line style (RH-14, REVIEW R2-45) -- ::TestTheOutline::test_recast_area[saved|served]
- Test: `kdensity mpg, recast(area) range(10 45)` (`plot_for("kdensity", {"recast": "area", "range": "10 45"})` under test/test_saved_filter_layers.py's `_MOVES[1]` filter, built with its `_spec`/`_render`): the fill (the VArea carrying `_dash_area_ring`) keeps `_dash_agg_config` and the ring and swatch carry none; after `_move(r, _MOVES[1][2])` and the fill source's `dash_area_ring` CustomJS (its `js_property_callbacks["change:data"]` entry, run with that file's `_run(cb.code, cb.args)`, as the browser runs it on the recount's assignment), the ring's columns equal `_dash_area_ring(d["x"], d["y_base"], d["y"], None)` over the recounted fill's data `d` -- ::TestTheOutline::test_recast_area_after_a_move[saved] (red at the base: no ring, NameError)
- Test: no HoverTool of the figure lists the ring in its `renderers` (plain area, `cmissing(n)` and `recast(area)`), while the fill keeps its tooltip -- ::TestTheOutline::test_no_hover_on_the_ring[saved|served]
- Test: `area le_wm year, horizontal` turns the ring with the fill -- ::TestTheOutline::test_horizontal[saved|served]
- Test: the area's y and x ticks and hull are those of today's tree (the ring is no tick or hull input; `_dash_layer_extent` over the layer equals its value without the ring) -- ::TestTheOutline::test_no_tick_input[saved|served]
- Test: the key item of an area layer holds exactly the swatch Quad, with the area's fill and the ring's line -- ::TestTheKey::test_key_is_outlined[saved|served]
- Test: `legend(order(2 1))` over two areas keys each by its swatch; a by(foreign) legend clones the swatch -- ::TestTheKey::test_order_and_by[saved|served]
- Test: under `by(foreign)` the legend's `click_policy` is `"hide"`, its item's renderers are the panels' swatches, and each swatch's `js_property_callbacks["change:visible"]` holds links whose targets are its own panel's VArea and ring, so a click hides the area and its outline in every panel; a plain legend's item is the swatch and its `click_policy` stays `"none"` (static, as `_dash_apply_legend` leaves it) (REVIEW R2-5) -- ::TestTheKey::test_click_hides_the_area[saved|served]
- Test: `area le_wm year, colorvar(le_wf)` gives a swatch whose fill and line colours are strings, and the swatch's fill and line and the ring's line colour are exactly those of `area le_wm year` without colorvar() (`_fill_base` and `area_line_style(0)["line"]`): colorvar() on an area draws nothing, as in twoway (`cv_silent`) (REVIEW R2-44) -- ::TestTheKey::test_colorvar_swatch[saved|served]
- Test: `lfitci mpg weight, fitplot(area)` (`plot_for("lfitci", {"fitplot": "area"})`) keys its band as `n` (the band's VArea, no swatch) and its fit as `n + 1` by the fit's swatch alone; `lfitci mpg weight, ciplot(area)` keys its band as `n` by the band's swatch and its fit line as `n + 1`; with `nofit` added to the first, only key `n` remains -- ::TestTheKey::test_ci_fitplot_area[saved|served]
- Test: the help's area sentence states the whole outline -- ::TestTheHelp::test_sentences (the `_between(_help(), ...)` pattern of test/test_help_claims_1.py)
cscript: Q3405-1, Q3405-2.
Pinned tests to flip: test/test_scheme_linewidth.py:279; test/test_recast_refit.py's `_recast_renderers` (Evidence); the old-picture nodes 34-05-03 lists.
Parity: append `_case("area default outline", [plot_for("area")])`, `_case("area cmissing outline", [plot_for("area", {"cmissing": "n"})])` and `_case("area nodropbase outline", [plot_for("area", {"nodropbase": "nodropbase"})])` to `CORPUS`, and one `_move_case("area outline after a range move", <an existing range-slider move>, [plot_for("area")])` to `MOVE_CORPUS` (`ALLOWED` is never edited, R8).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Style chain per scheme | pytest | area_outline_truth.json | n/a |
| Ring helper and its JS twin | pytest + node | -- | n/a |
| Whole outline vs twoway's stroked path | pytest | area_outline_truth.json paths | yes |
| Restyle, gaps, moves, nodropbase, recast, horizontal | pytest | same | yes |
| recast(area) recount after a saved move (WP-31 C16 kept) | pytest + node; the recast refit file; parity's C16 entries | -- | yes |
| No tick or hull input; no tooltip on the ring | pytest | -- | yes |
| Key outlined, order(), by(), by() click hides, plain legend static, colorvar, ci fitplot/ciplot(area) keys | pytest | same | yes |
| Live twoway vs dash | cscript Q3405-1/2 | -- | saved |
| Help sentence | pytest help-claim | -- | n/a |
| Parity | test_mode_parity CORPUS, MOVE_CORPUS | -- | yes |

AC-34-05.1 every default area is outlined all round in twoway's colour and width in ten schemes, both modes; AC-34-05.2 its key is outlined and, in a by() legend, hides the area; AC-34-05.3 cmissing, nodropbase and moves keep twoway's polygon, a recast(area) recount included; AC-34-05.4 no axis changes and no tooltip on the ring; AC-34-05.5 a ci layer drawn with an area keeps keys n and n+1; AC-34-05.6 one green commit.

## Tasks

**Commit boundary.** 34-05-01 to 34-05-04 form one commit, subject `Outline every area plot all round, and its key, in the scheme's area line style (WP-34 PIC-1)`, made by 34-05-04 on branch `wp34-s05` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s05`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (34-05-04 for PIC-1) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-05/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-05 <scratch>/34-05/run_test_wp33_truth.do` and read `<scratch>/34-05/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-05/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-05-01">
  <name>Measure area outlines and write failing tests</name>
  <files>scripts/extract_area_outline_truth.do, test/test_area_outline.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read map_area, _dash_legend_keys, _dash_auto_base_props, _dash_finish_auto_bases, GlyphMapper._tag_recast, _dash_build_hover, _stub_color_alpha, _lpattern_chain and the arrowheads' script hook (:25323-25352) at the batch base; run `node .gitnexus/run.cjs impact "map_area" --direction upstream --repo .` and the same for `_dash_legend_keys`, `_dash_auto_base_props`, `_dash_finish_auto_bases`, `_tag_recast` and `_dash_build_hover`, writing callers, risk and anchors to <scratch>/34-05/anchors.txt (HIGH/CRITICAL or UNKNOWN named in the handback); record there whether a saved and a served area source carry `_ROW_ID_COLUMN` (print `sorted(area_source.data)` for a cmissing(n) probe in each mode). Create the extractor per TR-34-05.5, run it through scripts/stata_slot.sh and `git add -f test/fixtures/area_outline_truth.json`. Create test/test_area_outline.py with the TDD stubs. Insert the S05 block and its python helper where the Stata truth section says. Run `python3 -m pytest test/test_area_outline.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-05/01.log`, run the S05 block with WP34_ONLY=S05, and save the failures to <scratch>/34-05-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/area_outline_truth.json'));print(len(d['schemes']), d['schemes']['stcolor'][0]['line'], len(d['paths']['plain']), d['paths']['plain'][0]['base_corners'], len(d['paths']['gap']))"` prints `10 #1a85ff 1 True 2` (case-insensitive hex; if the paths differ, the handback records the fixture's answer per TR-34-05.5); `grep -c FAILED <scratch>/34-05/01.log` is at least 8; `grep -c "Q3405-[12] FAIL" <scratch>/34-05/run_test_wp34_truth.log` prints 2; `test -s <scratch>/34-05-01-failure.txt`.]]></verify>
  <done>twoway's area outline colours and stroked polygon were recorded and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-05-02">
  <name>Add the ring helper and its script</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Add `_dash_area_ring` and `_dash_area_ring_write` (TR-34-05.2), the constant `_DASH_AREA_RING_JS` (TR-34-05.3), the `dash_area_outline` rule in `_dash_auto_base_props` and the `_dash_area_ring_write(r)` call in `_dash_finish_auto_bases` (TR-34-05.8), the copy-list entries and the function-map rows (TR-34-05.9). If the fixture's paths differed from the expected ones (34-05-01's handback note), change `_dash_area_ring` and its twin to the fixture's shape first. Run test/test_area_outline.py -k TheRing, test/test_bar_range_geometry.py (the auto-base tests), test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test/test_function_test_map.py and test/test_csp.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_area_outline.py -k TheRing test/test_bar_range_geometry.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py test/test_csp.py -q -n0 -p no:cacheprovider` ends with 0 failed.]]></verify>
  <done>The ring helper, its JS twin and the auto-base rules exist, agree with each other and change no current picture.</done>
</task>

<task type="auto" id="34-05-03">
  <name>Draw the whole outline and its key</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-34-05.1 (SchemeParser.area_line_style), TR-34-05.4 (the ring outline in map_area, replacing the optional top-edge Line, and its script on every fill source), TR-34-05.4a (the ring left out of `_dash_build_hover`), TR-34-05.6 (the key swatch and its visibility links), TR-34-05.7 (the three key edits in _dash_legend_keys) and TR-34-05.10 (the ring and swatch skipped by `_tag_recast`). Flip test/test_recast_refit.py's `_recast_renderers` in place as the Evidence says (it is the one flip this task's verify needs; 34-05-04 names it in the commit body). Run test/test_area_outline.py, test/test_recast_refit.py, test/test_mode_parity.py -k C16, test/test_scheme_linewidth.py, test/test_named_styles.py, test/test_area_cmissing.py, test/test_saved_filter_layers.py -k area, test/test_legend*.py -k "area or key", test/test_ci_plot_index.py, test/test_ciplot_colours.py, test/test_fit_options.py -k "fitplot or ciplot", test/test_hover_export.py, test/test_hover_merge.py, test/test_series_labels.py, test/test_by_axes_keys.py, test/test_by_remainder.py -k Legend, test/test_default_axes.py and test/test_mode_parity.py -k area; write to <scratch>/34-05/flips.txt every failure that asserts the old picture (no outline, a top-edge-only border Line, its border source or `_dash_join`, one renderer per area layer, a ci `fitplot(area)` fit's VArea keyed with the band) with its file::Class::test name; any other failure is a regression to fix in the code.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_area_outline.py test/test_recast_refit.py -k "not TheHelp" -q -n0 -p no:cacheprovider` ends with 0 failed; `python3 -m pytest test/test_mode_parity.py -k C16 -q -p no:cacheprovider` ends with 0 failed; `test -f <scratch>/34-05/flips.txt`.]]></verify>
  <done>Every area layer is outlined all round and keyed as twoway outlines it, in both modes, at build and after moves, with recast(area) layers still recounted, no tooltip on the ring and a ci layer's two keys kept.</done>
</task>

<task type="auto" id="34-05-04">
  <name>Flip pins, correct the help, close PIC-1</name>
  <files>test/test_scheme_linewidth.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
Flip test/test_scheme_linewidth.py:279 to `opts = {}` with `# Flipped (WP-34 PIC-1): an area is outlined by default, as twoway outlines it; lcolor(red) only forced the outline.` and every node in <scratch>/34-05/flips.txt in place with `# Flipped (WP-34 PIC-1): the outline is the area's whole polygon, one ring rebuilt from the fill's source (A-6).`. Help: in dash.sthlp:6040-6042 (the clause wraps over three lines; match it across the line breaks) change "a bar's and an area's outline width ({cmd:linewidth pbar} and {cmd:linewidth parea})" to "a bar's and an area's outline width ({cmd:linewidth pbar} and {cmd:linewidth parea}; an area is outlined by default, as {cmd:twoway} outlines it)"; after the rarea sentence ending "are not drawn." (dash.sthlp:454) add "An {cmd:area} is outlined whole, as {cmd:twoway} strokes its polygon: along its top, its base and the two short edges at its first and last points (under {cmd:nodropbase}, along the chord that closes it), in the scheme's area line colour, width and pattern, which {cmd:color()}, {cmd:lcolor()}, {cmd:lwidth()}, {cmd:lpattern()} and the named line styles restyle; a {cmd:cmissing(n)} gap breaks it where it breaks the fill, and its legend key is the outlined fill." (no Differences line: nothing is left undrawn). Write the new sentences into test/test_area_outline.py::TestTheHelp::test_sentences's expected text. Append the parity entries to test/test_mode_parity.py. Append `[WP-34 PIC-1: corrected -- the default area outline (the whole polygon) and key drawn]` to the `area` row of TWOWAY_COVERAGE_AUDIT.md (:64). Close the BUGS.md entry 33-01 registered for PIC-1 with PD-4's closed form (what changed: map_area always draws the area's whole polygon as one ring Line in SchemeParser.area_line_style, rebuilt from the fill's source by _dash_finish_auto_bases and _DASH_AREA_RING_JS, no tick or hull input; the key is a swatch Quad keyed through _dash_legend_keys' _dash_key_glyph rules (a ci layer's band and fit keyed per part) whose visibility hides the area and ring from a by() legend; the ring and swatch are skipped by _tag_recast, so a recast(area) kdensity or histogram keeps its saved recount, and by _dash_build_hover; recast(area) included (RH-14); both modes; pinned by test/test_area_outline.py::TestTheOutline::test_ring_matches_twoway and Q3405-2; fixture area_outline_truth.json); rewrite `- **PIC-1 Tracked:**` to the Closed form with `commit pending`; delete PIC-1's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- A default area plot and its legend key are outlined as twoway outlines them -- the whole polygon, top, base and end edges -- in the scheme's area line style (WP-34, PIC-1)` under `### Fixed in WP-34`. Run the Closing steps for PIC-1 (Tasks; BRIEF steps (1)-(3)): (1) delete PIC-1's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py PIC-1`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-05) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_area_outline.py, test/test_scheme_linewidth.py, test/test_recast_refit.py, the flipped nodes, test/test_mode_parity.py -k "area or C16", test/test_help_conformance.py, test/test_tracking_documents.py, test/test_fixtures_are_committed.py and the S05 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines and a line naming DECISIONS A-6; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_area_outline.py test/test_scheme_linewidth.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3405-[12] PASS" <scratch>/34-05/run_test_wp34_truth.log` prints 2; `awk -F'\t' '$1 == "PIC-1"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py PIC-1` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-05/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 PIC-1)`; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>Every default area plot and key is outlined all round as twoway draws it, and PIC-1 is closed in one commit.</done>
</task>

## Section completion criteria

- Ten schemes' outline colours matched in both modes; the ring equal to twoway's stroked polygon for the plain, gap and nodropbase probes; the key outlined and hiding the layer from a by() legend (a plain legend static); cmissing, nodropbase, recast(area) (its WP-31 C16 recount kept), horizontal and moves kept; no tooltip on the ring; a ci layer drawn with an area keeps keys n and n+1; no axis changed; the pins flipped with their reasons; the help (HR-15's :6041) corrected and the area sentence pinned; one green commit.

## Notes

- **DECISIONS A-6** supersedes REVIEW-2's Q-7 and this section's earlier top-edge-only decision: the base and closing edges are drawn, so there is no area residual and no Differences line. rarea's undrawn closing edges (WP-31 E8, dash.sthlp:449-454) are not this section's.
- **Help (R3, HR-15):** this section owns dash.sthlp:6041's clause and the new area sentence after :454. HR-15's :6069 (V/v chevron) is 47-06's, :6202-6205 (economist note) 45-01's.
- **Trap:** never give the ring a `_ROW_ID_COLUMN`: the saved filter would then keep its rows by id and break the closing edges after a move (D-34-05.c). Never name it with `_DASH_SWATCH_PREFIX`: the date conversion skips swatches (:2149).
- **Trap:** `_DASH_SWATCH_PREFIX` names are skipped by `_dash_layer_extent` and the hull, so the NaN swatch never reaches an axis; do not give it a `legend_label` (Bokeh would add an auto item).
- **Trap:** Bokeh's `legend_label=yvar` on the VArea creates an automatic item; `_dash_apply_legend` replaces the figure's legend from `_dash_legend_keys` -- confirm the auto item does not survive (the key test reads the final Legend's items).
- **Trap:** `ring.data = nd` inside the script assigns the ring, not the fill's source, so the script never triggers itself.
- **Trap:** the node harness (test/js_runner.py) runs a filter callback, not the `change:data` callbacks an assignment fires in the browser; a test of the ring after a saved move runs the fill source's `dash_area_ring` CustomJS itself after the move (TestTheOutline::test_gap_and_move, ::test_recast_area_after_a_move).
- **Trap:** `_bin_tag` inside `map_histogram` (:22209, 34-01's function in this batch) gives `__dash_bin_rows` to every renderer whose source has one row per bar, so a one-bar `histogram ..., recast(area)` gives it to the key swatch too; harmless (the swatch draws nothing and every filter, brush and redraw path skips a swatch), and `map_histogram` is not this section's to edit.
- **For 34-06 (batch 34.2):** keep TR-34-05.7's three edits where they are when changing the counter: the `keyed` list as the loop's first statement, the ci branch's `band`/`bkey`/`lkey` rules, and `if keyed and rends: rends = keyed` immediately before `if ptype in _DASH_CONTOUR_TYPES:` (after the ci branch, never before it).
- **Manifest note (REVIEW R2-25; the index's Owns cell is the orchestrator's to correct):** the cell lists `map_area`; to draw A-6's whole outline this section also adds `SchemeParser.area_line_style`, `_dash_area_ring`, `_dash_area_ring_write` and `_DASH_AREA_RING_JS`, edits one line each of `_dash_auto_base_props` and `_dash_finish_auto_bases`, three places of `_dash_legend_keys` (TR-34-05.7), one `continue` in `GlyphMapper._tag_recast` (TR-34-05.10) and one filter clause of `_dash_build_hover` (TR-34-05.4a). None is an R11/R12 hot function, and no other batch-34.1 section edits them (34-01 calls `_dash_auto_base_props` from `_dash_layer_extent` and `_dash_axis_plan` without changing it, and leaves `map_histogram`'s `_tag_recast` call as it is).
- **GitNexus:** `impact` on every function named in Owns before editing (34-05-01), `detect-changes --scope all` before committing (34-05-04).
- **Commit body line forms:** `Regression: test/test_area_outline.py::TestTheOutline::test_default_outline -- failed at <base sha> with <text>`; `Flipped: test/test_scheme_linewidth.py::<class>::<test> -- lcolor(red) was injected because no default outline was drawn, which was wrong because twoway outlines every area`; `Flipped: test/test_recast_refit.py::_recast_renderers (TestRecastRefit::test_tagged, ::test_js_equals_python) -- every non-swatch renderer was a recount target, which was wrong once the area's outline ring is drawn from the fill by its own script`; `Fixture: test/fixtures/area_outline_truth.json (scripts/extract_area_outline_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: PIC-1 Tracked`; `DECISIONS A-6: the whole polygon is stroked, as twoway strokes it`.
- Merge rules touched: R1, R2, R3, R6 (function map), R7, R8, R9.
