# Section 41-01: Contour under by(): one shared z axis

> Part of: WP-41 (by() fidelity, P6) · Items: BY-28 · Risk: yellow · Batch: 41.1 · Depends on: none (37-03 landed in WP-37) · Blocks: none · Tasks: 4, 1 commit · Case-id prefix: Q4101

## Overview

**What is wrong today.** The audit (package 6, BY-28; appendix "by-interactions" BY-28): "contour/contourline under by() cuts each panel at its own z ticks; twoway uses one shared z axis, so the same colour means a different z per panel". Measured by the audit: `contour price mpg weight, by(foreign)` -- "Domestic 3 levels (cuts 5000, 10000), Foreign 5 levels (cuts 6000(2000)12000)"; `by(rep78, total)` "4, 5, 3, 3, 4, 3 levels"; contourline the same. Cause: `GlyphMapper.map_contour` (dash_render.py:24368-24372) computes `zmin`/`zmax` from the panel's own rows and passes them to `_dash_contour_cuts`; `_dash_share_by_scales` (:47937) shares x and y only. The saved page's refit (`_FILTER_JS` contour branch, :35083-35097) recomputes each panel's cuts from its own kept rows too.

**The measured rule (this section's planning probe, 20oct2026, StataNow 19.5 console, `.Graph.graphs[i].plotregion1.plot1.lastcuts` read after `graph export ... .svg`).** twoway does NOT cut over the union of the panels: every panel, the Total panel included, is cut at the **first panel's** cuts, computed from the first panel's own z range. `by(foreign)`: both panels `5000 10000` (Domestic alone: `5000 10000`). With `nf = 1 - foreign` (Foreign first), `by(nf)`: both panels `6000 8000 10000 12000` (Foreign alone: the same). `by(rep78, total)`: all six panels `4400 4600 4800` (rep78==1 alone: `4400 4600 4800`). `levels(4) by(nf)`: both `6058.5 8369 10679.5` (the first panel's 3748..12990 in fourths). `by(nf, total)`, `by(nf, rescale)` and `by(nf, clegend(on))` keep the rule; contourline the same. The audit's "compute the cuts once over all panels" is superseded by this measurement (BRIEF: the measured truth is the requirement); 41-01-01 re-measures it into a committed fixture.

**After this section.** Under by() every contour and contourline layer, in every panel and the Total panel, is cut at the cuts its first drawn panel's z range gives (`ccuts()` and `levels()` rules included), coloured with one level list, and keyed over that panel's range, in the saved page and the served app; after a filter move both modes re-cut every panel at the first panel (in panel order) that keeps rows. This builds on WP-37's 37-03: a gridded by() layer (each panel a full grid, or `interp(none)`) already draws each panel from Stata's own `twoway__contour_gen` polygons at the cuts Stata computed by the same first-panel rule (D-37-03.b), so those panels are left as 37-03 draws them, and a panel of such a layer that dash still fits (one D-37-03.f's gate keeps out) takes those Stata cuts (D-41-01.e). What this section changes is every panel dash fits itself -- scattered data, as every probe below on auto is.

**Test order and commit rule.** 41-01-01 measures twoway into `by_contour_truth.json` and writes every failing test (saved failure, no commit). 41-01-02 adds the Python rule and the build in both modes; 41-01-03 adds the saved JS twin and the served after-move twin; 41-01-04 flips nothing it need not, updates help and tracking, and makes the one BY-28 commit `(WP-41 BY-28)`. No full suite inside the section.

### Section decisions

- **D-41-01.a -- the first panel's range, not the union.** The shared range is the z range (min, max over rows with x, y and z all non-missing, z in Stata units for a date) of the first panel in by() order that has such rows, read with the plot's own if/in. All cuts (`_dash_contour_cuts`), the fill levels (`_dash_contour_fill_levels`) and the key's ends use it; whether a panel is drawable stays the panel's own (a panel with no z draws nothing, as today).
- **D-41-01.b -- carried as an internal option.** The shared range rides into `map_contour` as the plot's options key `"_dash_by_zrange": [lo, hi]` with `"_dash_by_zshare": "<graph name>|<plot index>"` and `"_dash_by_zpanel": <panel index>`, written by a pure spec helper beside `_dash_fn_panel_spec`, so `_make_figure_body` (R12 hot) is not edited. No option table reads underscore keys (checked: no generic validator iterates the options dict).
- **D-41-01.c -- after a move.** Saved: a pre-pass in `_FILTER_JS` takes, per `zshare`, the kept-row z range of the config with the lowest `zpanel` that keeps rows. Served: `_dash_move_compute` and the inline redraw loop take the same range from each contour layer's qualified panel frame, through one module helper. A by() graph whose first panel keeps no rows takes the next panel's, as twoway's first drawn panel would be.
- **D-41-01.d -- served template ownership.** This section edits the served literal lines of the by() panel loop and the move compute (`ServerAppBuilder._generate_app_source_body`, R12) in batch 41.1; 41-03 and 41-06 must not edit that method in 41.1 (index R12; reported to the orchestrator).
- **D-41-01.e -- builds on 37-03: gridded panels already carry Stata's cuts.** After WP-37 a gridded by() layer's plot carries `options["contour_gen"]` = `{"panels": [{"key": ..., "grid": {..., "cuts": [...]}}, ...], "total": ...}` (TR-37-03.3), each panel's grid picked by `_dash_contour_panel_spec` (TR-37-03.5) and drawn by `map_contour`'s `cg` branch at the object's cuts -- Stata's, computed once over the first panel's rows (D-37-03.b). 41-01 does not re-cut those panels: the `cg` branch and 37-03's helpers are not edited, and `_dash_by_zrange`/`_dash_by_zcuts` are read only where `cg` is None (dash's own fit). So that one layer never mixes Stata's cuts with dash's, the layer's Stata cuts (the first `panels` entry's `cuts`, else `total`'s; `_dash_by_contour_gen_cuts`) ride beside the range as `"_dash_by_zcuts"` and a dash-fitted panel of that layer is cut at them; a layer with no such object (scattered data) is cut by the range rule of D-41-01.a. After a move the cuts follow the kept range (D-41-01.c): a served redraw drops `_dash_by_zcuts`. If 37-03's hand-back reports `first_panel_rule` 0 (each panel cut at its own rows), stop and report: it contradicts this section's measurement.

## Risk: [yellow] -- a JS twin and served literal lines on the filter path

**Why.** Contour's saved refit and the served redraw are the two most intricate refits on the page; the shared range must reach both and the build without changing a non-by() contour by a single cut.

**Risk factors.** 1. The saved refit's `_pick`/`_keep` logic must be reproduced exactly in the pre-pass, or a panel reads another panel's rows. 2. A date z is cut in Stata units (`units` in map_contour); the helper must convert with `_dash_date_units` as `GlyphMapper._masked` does. 3. The served redraw closure applies the graph's and the layer's qualifiers itself; the range must come from the same qualified frame. 4. Total is the last panel and never the first unless it is alone. 5. A gridded layer (37-03) reaches `map_contour` with a picked `contour_gen` object; re-cutting it, or cutting a dash-fitted panel of it at dash's cuts where Stata's differ, would mix two rules in one layer.

**Mitigation.** One Python rule (`_dash_contour_zrange_of`) used by the build helper and the served move; the JS pre-pass pinned to it through test/js_runner.py on the same rows; a non-by() parity guard (`_dash_by_zrange` absent changes nothing); the `cg` branch untouched and `TestGridPanels` pinning a gridded layer with one dash-fitted panel (D-41-01.e); the fixture covers ccuts(), levels(), total, rescale, contourline and a date-free and a first-panel-is-Foreign case.

## Dependencies

- **Depends on:** none in WP-41 (WP-41 W0 has created `test/test_wp41_truth.cscript` and `### Fixed in WP-41`). Earlier sections it builds on: **37-03** (WP-37 TR-13: a gridded by() contour layer carries 37-03's `options["contour_gen"]` object, picked per panel by `_dash_contour_panel_spec` and drawn by `map_contour`'s `cg` branch at Stata's cuts; D-41-01.e, TR-41-01.2's `_dash_by_contour_gen_cuts`, TestGridPanels and AC-41-01.5 read it), 37-01 and 37-02 (`map_contour`'s empty branch and key condition, which TR-41-01.1 matches), 37-04 (`_dash_fit_panel_spec`, whose saved and served lines TR-41-01.5 and TR-41-01.6 follow) and 33-12 (`BY_TYPES_KNOWN`'s BY-28 rows, D-33-12.d, which 41-01-04's step (2) deletes).
- **Blocks:** none.
- **Parallel batch:** 41.1 with 41-03 and 41-06. This section is the batch's one JS = yes section (`_FILTER_JS`) and the one editor of `_generate_app_source_body` (D-41-01.d).
- **Can run with:** 41-03 (edits `_dash_scale_factor`, dash.ado's per-panel loops) and 41-06 (panel labels): no shared function.

## Evidence

**Code at 090d928 (re-read before editing; anchors drift; `map_contour` was rewritten by WP-37 -- 37-01, 37-02, 37-03 -- before this batch).**
- `map_contour` dash_render.py:24309. The cut computation:
  ```
  24368        zmin = float(np.min(uz)) if uz.size else float("nan")
  24369        zmax = float(np.max(uz)) if uz.size else float("nan")
  24371        cuts, ticks = _dash_contour_cuts(options, zmin, zmax,
  24372                                         self.z_options)
  ```
  fill levels :24404-24405 `lv = _dash_contour_fill_levels(cuts, ticks, zmin, zmax) if math.isfinite(zmin) else ...`; the saved config `cr._dash_contour_config = {...}` :24428-24445 (its `"cuts"`, `"lo"`, `"hi"`); `cr._dash_agg_config = dict(cr._dash_contour_config, part=..., extra=..., **self._contour_refit_rule(...))` :24456-24462.
- `_dash_contour_cuts(options, zmin, zmax, zopts=None)` :29227; `_dash_contour_fill_levels(cuts, ticks, zmin, zmax)` :29466; JS twins `dash_contour_cuts` :34368, `dash_contour_fill_levels` :34386.
- Saved refit, `_FILTER_JS`: the loop head `for (let ai = 0; ai < agg_configs.length; ai++)` :34442, `_ac_data = dash_data_for(ac.use)` :34454, `_keep` from `ac.member_ids` :34455-34461, `_pick` :34462; the contour branch :35052, its own z range
  ```
  35083        let _zmin = Infinity, _zmax = -Infinity;
  35084        for (let i = 0; i < _zu.length; i++) {
  ...
  35090        let _cuts = ac.cuts, _ticks = null, _lo = ac.lo, _hi = ac.hi;
  35091        if (ac.rule && _zmin <= _zmax) {
  ```
- Saved by() build: `_dash_by_panel_dropped` (:5478) is the model for reading a plot's qualifier on a panel frame (`_dash_qual_mask`, `_dash_qualified_frame(frame, p_if, p_in, qual=qual, copy=False)`, :5530-5543). The panel groups are made in `_expand_by_groups` (:63056; the loop :63122-63141, Total :63151-63166); the figure loop calls `g_panel = _dash_fn_panel_spec(g_panel, panel_idx_r)` then `self._make_figure(g_panel, src, facet_view=panel_view_r, rescale=_brs)` (:65040-65043).
- Served build literal lines: `_panels` built :70780-70810; per panel `_g_pan = _dash_fn_panel_spec(g, _fi)` / `_dash_fn_panel_spec(_g_tot, _fi)` :70826-70834.
- Served move: `_dash_redraw_for(g, plot, pi, gname, cv_domain=None)` :70146 (its `_redraw(frame)` :70187-70205 qualifies with `_dash_layer_frame` twice); registration `agg_sources[(gname, pi)] = {'type', 'sources', 'redraw'}` :70517-70523; `_dash_agg_frame(plan, key)` :71147; `_dash_move_compute(plan)` :71193 (`fresh = {key: agg['redraw'](_dash_agg_frame(plan, key)) ...}` :71202); the inline loop `_fresh = (agg['redraw'](_dash_agg_frame(plan, key)) if res is None else res['fresh'][key])` :71353.
- Served copy list: `"_dash_fn_panel_spec",` :67800.
- `_dash_share_by_scales` :47937 (`letters = tuple(d for d in ("x", "y") ...)` :47955) -- not edited: the z rule is applied before the panels are drawn.
- After WP-37 (37-03, TR-13; re-read at the 41.1 base): `_dash_attach_function_points` puts each gridded layer's `contour_grids` object into `options["contour_gen"]` (TR-37-03.4); the saved figure loop calls, after `_dash_fn_panel_spec` and 37-04's `g_panel = _dash_fit_panel_spec(g_panel, self._facet_keys.get(fkey), fkey in self._facet_total_keys)`, `g_panel = _dash_contour_panel_spec(g_panel, self._facet_keys.get(fkey), fkey in self._facet_total_keys)`, and the served panel loop has the same literal after each of 37-04's (TR-37-03.5 (a)); `map_contour` reads `cg = _dash_contour_gen_of(options)`, uses it only when the layer's row count equals `cg["n"]`, and then draws the object's polygons at `cg["cuts"]` with no `_dash_agg_config` (stale tag "grid", TR-37-03.5 (b)); 37-03's note for 41-01 (its Notes) says the gridded panels arrive with twoway's cuts and that this section's rule meets them there. Fixture `test/fixtures/contour_gen_truth.json` (`sandstone.by`, `first_panel_rule`).

**twoway's rule.** `/Applications/StataNow/ado/base/z/zyx2view_g.class:255-276` (reset_dserset: cuts from the z axis's ticks); the measurement above shows by() gives every panel the first graph's.

**Fixtures on disk.** None for contour under by() (`contour_truth.json` and `contour_interp_truth.json` have no by() probe).

**Tests that pin today's behaviour.** No contour + by() test exists (audit; `grep -n "by" test/test_contour_layers.py test/test_contour_js.py` finds none on panels). Nothing to flip; the new tests are red at base.

## User stories

- US-41-01.1 As the Stata user with an existing twoway command, I want `contour z y x, by(g)` to colour every panel at the same cuts twoway draws, so that one colour means one z range across the panels.
- US-41-01.2 As the dashboard author, I want the panels to keep sharing their cuts after a filter move, in the saved page and the served app alike.

## Business requirements

- BR-41-01.1 Under by(), every panel's contour bands and contourline lines are drawn at the cuts twoway draws: the first panel's, for the default rule, `levels()`, `ccuts()` and `zlabel()` rules.
- BR-41-01.2 The Total panel takes the same cuts.
- BR-41-01.3 A graph without by() draws exactly as before.
- BR-41-01.4 After a filter move every panel is re-cut at the first panel that still has rows, identically in both modes.
- BR-41-01.5 A gridded by() layer keeps twoway's own polygons and cuts in every panel 37-03 draws from Stata's generator, and a panel of that layer that dash fits is cut at the same cuts.

## Technical requirements

- TR-41-01.1 New module function after `_dash_by_panel_dropped` (dash_render.py:5478); it must select exactly the rows `map_contour`'s `GlyphMapper._masked(..., units=units)` keeps for `uz` (re-read map_contour at the 41.1 base: 37-01's empty branch, 37-02's key condition and 37-03's `contour_gen` branch rewrote the block quoted in Evidence):
  `def _dash_contour_zrange_of(rows, plot, date_vars=None)` -> `[lo, hi]` or None. *rows* is a DataFrame already restricted to the layer's rows. `x = _dash_float_values(rows[plot["xvar"]])`, `y` likewise with `plot["yvar"]`, `z` with `plot["zvar"]`; for each of the three, when `(date_vars or {}).get(var) in _STATA_DATE_KINDS`, `col = _dash_date_units(col, date_vars[var])`; `ok = ~isnan(x) & ~isnan(y) & ~isnan(z)`; return `[float(z[ok].min()), float(z[ok].max())]` when `ok.any()`, else None. Missing columns or a non-dict plot: None. Never raises.
- TR-41-01.2 `def _dash_by_contour_zranges(gdf, frame, plots, masks=None, date_vars=None)` -> `{pi: [lo, hi]}` (pi 0-based) for each plot whose `type` lower-cased is in `_DASH_CONTOUR_TYPES`: rows = `gdf.index`, intersected with the plot's own qualifier exactly as `_dash_by_panel_dropped` does (:5530-5543, warnings ignored), then `_dash_contour_zrange_of(frame.loc[rows], plot, date_vars)`; a plot with None is left out. And `def _dash_by_contour_gen_cuts(plots)` -> `{pi: [c, ...]}` (D-41-01.e): for each plot whose `type` lower-cased is in `_DASH_CONTOUR_TYPES` and whose `(plot.get("options") or {}).get("contour_gen")` is a dict holding a `"panels"` list, the `cuts` of the first entry whose `grid` is a dict with a non-empty `cuts` list of finite numbers (not bools), else the `"total"` object's `cuts` by the same test, as sorted floats; a plot with none (a flat object, no object, a malformed one) is left out; never raises, never notes (37-03's `_dash_contour_gen_of` keeps the one malformed-object note).
- TR-41-01.3 `def _dash_by_zrange_spec(g, zranges, panel_idx, name, zcuts=None)` -> a copy of *g* whose plot `pi` (each key of *zranges*) has a copied options dict with `"_dash_by_zrange": [lo, hi]`, `"_dash_by_zshare": "%s|%d" % (name, pi)`, `"_dash_by_zpanel": int(panel_idx)`, and `"_dash_by_zcuts": list(zcuts[pi])` when *zcuts* holds `pi`; *g* itself when *zranges* is empty. Same copy discipline as `_dash_fn_panel_spec` (:60165).
- TR-41-01.4 `map_contour`: after :24369 add
  ```python
  _zr = options.get("_dash_by_zrange")
  zc_min, zc_max = zmin, zmax
  if (isinstance(_zr, (list, tuple)) and len(_zr) == 2
          and all(isinstance(v, (int, float)) and math.isfinite(v) for v in _zr)
          and _zr[0] <= _zr[1]):
      zc_min, zc_max = float(_zr[0]), float(_zr[1])
  ```
  and use `zc_min, zc_max` in the `_dash_contour_cuts(...)` call (:24371) and in `_dash_contour_fill_levels(cuts, ticks, zc_min, zc_max)` (:24404); `drawable` keeps `math.isfinite(zmin)`. Directly after that `_dash_contour_cuts(...)` call add (D-41-01.e)
  ```python
  _zk = options.get("_dash_by_zcuts")
  if (isinstance(_zk, (list, tuple)) and _zk
          and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                  and math.isfinite(v) for v in _zk)):
      _zk = sorted(float(v) for v in _zk)
      if not (len(_zk) == len(cuts) and all(
              abs(a - b) <= 1e-9 * max(1.0, abs(b)) for a, b in zip(cuts, _zk))):
          cuts, ticks = list(_zk), list(_zk)
  ```
  (Stata's cuts win where dash's differ, the key labelled at them, as 37-03's `cg` branch labels its key). All of this is on the dash-fit path only: where 37-03's `cg` is used (re-read the branch at the base), its lines stay exactly as 37-03 left them -- they keep the panel's own `zmin, zmax` and read neither key. The config (:24428) gains `"zshare": options.get("_dash_by_zshare") or None, "zpanel": int(options.get("_dash_by_zpanel") or 0)`. `GlyphMapper` is copied whole: no copy-list entry.
- TR-41-01.5 Saved build: in `_expand_by_groups` (:63056), after the groups list is complete (before :63167's `if not groups:`), compute `self._facet_zranges[_gname] = _dash_by_contour_zranges(groups[0][1], self.df, (_dash_total_spec(graph_spec) if groups[0][1].attrs.get("_dash_total") else graph_spec).get("plots", []), getattr(self, "qual_masks", None), getattr(self.mapper, "date_vars", None))` and `self._facet_zcuts[_gname] = _dash_by_contour_gen_cuts(graph_spec.get("plots", []))` (the unpicked plots, which carry 37-03's `{"panels": ...}` objects) when `groups` is non-empty (initialise `self._facet_zranges = {}` and `self._facet_zcuts = {}` beside `self._facet_map` at :62203). In the figure loop, directly after 37-03's `g_panel = _dash_contour_panel_spec(g_panel, ...)` line (which follows `g_panel = _dash_fn_panel_spec(g_panel, panel_idx_r)`, :65041, and 37-04's `_dash_fit_panel_spec` line): `g_panel = _dash_by_zrange_spec(g_panel, self._facet_zranges.get(name, {}), panel_idx_r, name, self._facet_zcuts.get(name, {}))`. The date kinds are the mapper's `self.mapper.date_vars` (GlyphMapper :14543); re-read what the builder holds before writing.
- TR-41-01.6 Served build literal lines: after the `_panels` list is final (after the "Every panel left out" block, :70810) add the literal lines `"        _zr_by = _dash_by_contour_zranges(_panels[0][1], df, (_g_tot if _t_idx == 0 else g).get('plots', []), _qual_masks, _date_vars)"` and `"        _zk_by = _dash_by_contour_gen_cuts(g.get('plots', []))"`; after each `_g_pan = ...` assignment (:70827 and :70830) -- and after the `_dash_contour_panel_spec` literal 37-03 added after each of them -- add `"            _g_pan = _dash_by_zrange_spec(_g_pan, _zr_by, _fi, gname, _zk_by)"`.
- TR-41-01.7 Served move: (a) in `_dash_redraw_for` factor the two `_dash_layer_frame` steps of `_redraw` into a local `def _qual(frame):` returning `_fr`; `_redraw(frame, zrange=None)`: when `zrange` is a 2-list, draw with `plot = dict(plot, options=dict(plot.get('options') or {}, _dash_by_zrange=list(zrange)))`, else with the options' `_dash_by_zrange` removed; either way the options' `_dash_by_zcuts` is removed (after a move the cuts follow the kept range, D-41-01.c/e); set `_redraw.zrange = lambda frame: _dash_contour_zrange_of(_qual(frame), plot, _date_vars)`. (b) the registration (:70517) adds `'zshare': (plot.get('options') or {}).get('_dash_by_zshare'), 'zpanel': (plot.get('options') or {}).get('_dash_by_zpanel', 0)`. (c) New module function `def _dash_by_first_zranges(aggs, frame_of)` -> `{zshare: [lo, hi]}`: for each `key, agg` with a truthy `agg.get('zshare')`, `r = agg['redraw'].zrange(frame_of(key))`; keep, per zshare, the r of the lowest `zpanel` with r not None. (d) `_dash_move_compute`: `_zf = _dash_by_first_zranges(_agg_srcs, lambda k: _dash_agg_frame(plan, k))` before `fresh`, and each call `agg['redraw'](_dash_agg_frame(plan, key), zrange=_zf.get(agg.get('zshare')))`; the inline loop (:71353) the same.
- TR-41-01.8 Saved JS twin (`_FILTER_JS`), three functions inserted directly before `// agg_sources is a Bokeh model list` (:34433). The first is the contour branch's own `_su` closure (:35059-35061) hoisted to a named function, so the twin and the branch convert z by one code (REVIEW R3-29); the branch's `const _su = (col, k) => ...` line becomes `const _su = dash_stata_units;`:
  ```js
  // A column in its Stata units under a date kind k (a value with no
  // Stata date is NaN); the column itself without one.  Hoisted from the
  // contour branch (WP-41 BY-28), which and dash_contour_kept_zrange use.
  function dash_stata_units(col, k) {
      return k ? col.map(v => {
          const u = (typeof v === "number" && isFinite(v)) ? dash_stata_value_of(v, k) : null;
          return u === null ? NaN : u; }) : col;
  }
  // WP-41 BY-28: the z range of a contour config's kept rows, exactly as
  // the contour branch's kept-range loop reads them (x and y finite as
  // stored, z finite in its Stata units).
  function dash_contour_kept_zrange(ac) {
      const d = dash_data_for(ac.use);
      let keep = null;
      if (ac.member_ids) {
          const m = new Set(ac.member_ids), rid = d[ROW_ID] || [];
          keep = [];
          for (let i = 0; i < rid.length; i++) if (m.has(rid[i])) keep.push(i);
      }
      const pick = (c) => (keep === null || !c) ? c : keep.map(i => c[i]);
      const cx = pick(d[ac.xvar]), cy = pick(d[ac.yvar]), cz0 = pick(d[ac.zvar]);
      if (!cx || !cy || !cz0) return null;
      const cz = dash_stata_units(cz0, ac.zdatekind);
      let lo = Infinity, hi = -Infinity;
      for (let i = 0; i < cz.length; i++) {
          if (!Number.isFinite(cx[i]) || !Number.isFinite(cy[i]) || !Number.isFinite(cz[i])) continue;
          if (cz[i] < lo) lo = cz[i];
          if (cz[i] > hi) hi = cz[i];
      }
      return lo <= hi ? [lo, hi] : null;
  }
  // Under by() twoway cuts every panel at its first panel's cuts: per
  // zshare, the range of the config with the lowest zpanel keeping rows.
  function dash_contour_zfirst(configs) {
      const best = {};
      for (const ac of configs) {
          if (!ac || !ac.zshare || (ac.type !== 'contour' && ac.type !== 'contourline')) continue;
          const r = dash_contour_kept_zrange(ac);
          if (r === null) continue;
          const b = best[ac.zshare];
          if (b === undefined || ac.zpanel < b.p) best[ac.zshare] = {p: ac.zpanel, r: r};
      }
      const out = {};
      for (const k of Object.keys(best)) out[k] = best[k].r;
      return out;
  }
  ```
  After `const agg_configs = JSON.parse(agg_configs_json);` (:34435): `const _dash_zfirst = dash_contour_zfirst(agg_configs);`. In the contour branch, the `_su` line as above, and after the kept-range loop (:35089): `if (ac.zshare && _dash_zfirst[ac.zshare]) { _zmin = _dash_zfirst[ac.zshare][0]; _zmax = _dash_zfirst[ac.zshare][1]; }`. Check that test/js_runner.py's helper slice still ends at the `// agg_sources` comment (the three functions are inside it).
- TR-41-01.9 Copy list (R2): append `"_dash_contour_zrange_of", "_dash_by_contour_zranges", "_dash_by_contour_gen_cuts", "_dash_by_zrange_spec", "_dash_by_first_zranges",` on the line after `"_dash_fn_panel_spec",` (:67800). test/function_test_map.py rows for the five functions (and their `<locals>` if any), naming the tests of "TDD test stubs".
- TR-41-01.10 Help (R3): dash.sthlp's contour paragraph on cuts (find `{marker contour}` / "cuts" near :596-620, re-read) gains: "Under {cmd:by()} every panel, the Total panel too, is cut at the first panel's cuts, as {cmd:twoway} cuts them (it reads one z axis, the first panel's); after a filter move, at the first panel that keeps rows."

## Boundaries

- Do not edit `_make_figure_body`, `_dash_share_by_scales`, `_dash_layout_cell`, `_dash_by_panel_label`, `_dash_scale_factor`, dash.ado or dash_parse.mata.
- No union-of-panels rule (D-41-01.a). No change to contour's surface, colours or key placement (WP-37, WP-42).
- Do not edit 37-03's code: `map_contour`'s `cg` branch, `_dash_contour_gen_of`, `_dash_contour_panel_spec`, `_dash_attach_function_points`, the Stata-side `_dash_contour_gen` and its served literals (D-41-01.e); they are called or read, never changed.
- Contour's own `heatmap` option is untouched.

## Stata truth

New `scripts/extract_by_contour_truth.do` -> `test/fixtures/by_contour_truth.json` (R7). Skeleton: scripts/extract_by_text_truth.do :1-90 (DASH_REPO guard, `set graphics off`, `version 19`, `set scheme stcolor` for the session only, `shell git -C ... rev-parse HEAD` into a file read by the python block through `Macro.getGlobal`, `_meta` = stata_version, born_date, dash_commit, extracted, source). Data: `sysuse auto`, `gen byte nf = 1 - foreign`. For each probe: `capture noisily twoway <cmd> name(G, replace)`, rc, then `graph export "<work>/<id>.svg", replace` (cuts are empty under nodraw), panel count `.G.graphs.arrnels`, and per panel `i` the string `` `.G.graphs[`i'].plotregion1.plot1.lastcuts' ``; also the cuts of the first panel drawn alone (`twoway contour ... if <first group>` and `` `.G.plotregion1.plot1.lastcuts' ``). Probes:

| id | command |
|---|---|
| C01 | `contour price mpg weight, by(foreign)` |
| C02 | `contour price mpg weight, by(nf)` |
| C03 | `contour price mpg weight, by(rep78, total)` |
| C04 | `contourline price mpg weight, by(nf)` |
| C05 | `contour price mpg weight, levels(4) by(nf)` |
| C06 | `contour price mpg weight, ccuts(5000 9000) by(nf)` |
| C07 | `contour price mpg weight, by(nf, total)` |
| C08 | `contour price mpg weight, by(nf, rescale)` |
| C09 | `contour price mpg weight, by(nf, clegend(on))` |
| C10 | `contour price mpg weight if rep78 > 2, by(rep78)` |

Record `{"cmd", "rc", "panels", "cuts": [[...] per panel], "first_alone": [...]}`. Run `DASH_REPO=<wt> sh <wt>/scripts/stata_slot.sh <scratch> <wt>/scripts/extract_by_contour_truth.do`; `git add -f test/fixtures/by_contour_truth.json`; name it in test/test_fixtures_are_committed.py's list. Expected (planning probe): C02 both `6000 8000 10000 12000`, C03 all six `4400 4600 4800`, C05 `6058.5 8369 10679.5`.

## TDD test stubs

New `test/test_by_contour_cuts.py` (render through the helpers test/test_contour_layers.py uses; `_MODES = ("saved", "served")`; levels read from each panel's ContourRenderer `levels`):
- Test: each probe's panels are cut at the fixture's cuts -- `TestByContourCuts::test_panels_share_the_first_panels_cuts[mode-C01..C10]` (red at base for C02, C03, C04, C05, C07, C08, C09, C10; C01 and C06 green guards).
- Test: the fixture's every panel equals its first panel and `first_alone` -- `TestTheFixture::test_first_panel_rule` (guard).
- Test: `_dash_contour_zrange_of` on rows with a NaN x, a date z and no rows -- `TestTheRule::test_zrange_of` (red: function missing).
- Test: `_dash_by_contour_zranges` reads the plot's qualifier column -- `TestTheRule::test_zranges_read_the_qualifier` (red).
- Test: `_dash_by_zrange_spec` copies, never mutates, returns g for `{}`, and writes `_dash_by_zcuts` only for a plot *zcuts* holds -- `TestTheRule::test_spec` (red).
- Test: `_dash_by_contour_gen_cuts` takes the first `panels` entry's cuts (else `total`'s) and leaves out a flat object, a non-contour plot and a malformed `cuts` -- `TestTheRule::test_gen_cuts` (red: function missing).
- Test: a gridded by() layer (37-03's `{"panels": ...}` object, built as test/test_contour_gen.py's by() parity entry builds it, with the last panel's entry removed so that panel is fitted by dash) draws the first panel from its object at the object's cuts and cuts the dash-fitted panel at the same cuts -- `TestGridPanels::test_gridded_panels_keep_statas_cuts[saved|served]` (red at base: the dash-fitted panel is cut at its own range).
- Test: a contour without by() carries no `zshare` and draws the same levels as before -- `TestTheRule::test_no_by_unchanged[mode]` (guard).
- Test: after a saved move (node, `js_runner.run_js` over `_FILTER_JS`'s helper slice with two panel configs) `dash_contour_zfirst` returns the lowest-zpanel kept range, equal to `_dash_contour_zrange_of` on the same rows, for a numeric z and for a `%td` z (`zdatekind` "td", the column as the page stores it) -- `TestTwins::test_zfirst_equals_python[numeric|td]` (red); `TestTwins::test_stata_units_is_the_branchs` (the hoisted `dash_stata_units` over a %td column equals `_dash_date_units` of the same column; red).
- Test: served move: build `by(nf)`, apply a filter keeping rep78 > 3, both panels' levels equal and equal the saved page's after the same move -- `TestAfterAMove::test_both_modes_share[saved|served]` (red).

cscript block (test/test_wp41_truth.cscript, `* ==== S01 BY-28: contour under by() cut at the first panel's cuts ====`, gate `WP41_ONLY`; the head adds S01 to `w41_run` from the header, so nothing else is edited):
- Q4101-1 for C02, C03, C05: `capture noisily twoway <cmd> name(G, replace)` + export, read the first panel's lastcuts; `capture dash <cmd> name(q1)` + `dash build, saving("<tmp>/q1.html", replace)`; `python:` read the page's ContourRenderer levels per panel with dash_render's page reader (re-use the reader test/cert_svg.do's companion uses) and assert every panel's inner cuts equal twoway's list to 1e-9.

Pinned tests to flip: none.

Parity (R8): append to `CORPUS` in test/test_mode_parity.py `_case("contour by() shared cuts", [plot_for("contour", {})], go={"by": "rep78, total"})` beside the contour entries (:1537-1545; re-read `_case`'s keywords at :1480).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| panels' cuts = twoway's | pytest TestByContourCuts; Q4101-1 | by_contour_truth C01-C10 | yes |
| rule helpers | pytest TestTheRule | -- | n/a |
| gridded panels keep Stata's cuts; a dash-fitted panel takes them (37-03) | pytest TestGridPanels | contour_gen_truth.json (37-03) | yes |
| saved JS twin | node TestTwins | -- | saved |
| after a move | pytest TestAfterAMove | -- | yes |
| no-by() unchanged | pytest test_no_by_unchanged; parity corpus | -- | yes |

- AC-41-01.1 Every red stub was red at the base (`<scratch>/41-01-01-failure.txt`) and is green after.
- AC-41-01.2 Q4101-1 PASS under the console binary, no SKIP.
- AC-41-01.3 test_mode_parity.py, test_contour_layers.py, test_contour_js.py, test_contour_key_moves.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName and test_function_test_map.py green.
- AC-41-01.4 GAPS4 BY-28 Tracked reads `Closed in WP-41, BUGS.md "<title>", commit pending.`
- AC-41-01.5 test/test_contour_gen.py (37-03) passes unchanged: no gridded panel is re-cut.
- AC-41-01.6 No plain `BY-28` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table; corpus_ledger.json is regenerated; the hygiene command and the S09 guard block pass.

## Tasks

**Commit boundary.** 41-01-01 to 41-01-04 form BY-28's one commit, subject `Cut every by() panel's contour at the first panel's cuts, as twoway does (WP-41 BY-28)`, made by 41-01-04 on `wp41-s01` in `$WT`, the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp41-s01` (BRIEF "Pull form": commands use this absolute path). Before the commit: run `git pull --ff-only . main` in $WT (CLAUDE.md rule 4; BRIEF "Pull form": `Already up to date.` when the batch base already contains main; if it refuses, stop and report to the orchestrator, never a merge commit on a section branch), run `gitnexus detect-changes --scope all --repo .` in $WT (the global CLI; `.gitnexus/` is git-ignored and absent from a worktree; re-run when it reports `partial` or `truncated`) and `python3 -m pytest test/test_cscript_hygiene.py -k "TestTheWpTruthScripts and wp41" -q -n0`.

<task type="auto" id="41-01-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_by_contour_truth.do, test/fixtures/by_contour_truth.json, test/test_by_contour_cuts.py</files>
  <action><![CDATA[Check the worktree branch is `wp41-s01` and HEAD equals the batch base. Create scripts/extract_by_contour_truth.do exactly as "Stata truth" lists (probes C01-C10, the lastcuts path `.G.graphs[i].plotregion1.plot1.lastcuts` read after `graph export`), run it through `scripts/stata_slot.sh`, `git add -f` the fixture and add it to test/test_fixtures_are_committed.py's list (41-03 and 41-06 append to the same list in 41.1: the merger needs that file in picks.sh's `addmerge.py ours-first` list -- name it in the hand-back). Create test/test_by_contour_cuts.py with every stub of "TDD test stubs". Append the Q4101-1 block to test/test_wp41_truth.cscript directly above the first `* ==== S` header numbered above 01, else above `* ==== append new blocks above this line ====` (the template's head computes the run list from the headers; never edit the head). Run `python3 -m pytest test/test_by_contour_cuts.py -q -n0 -rf > <scratch>/41-01-01-failure.txt 2>&1; true` and the block with `WP41_ONLY=S01` through a two-line driver; append the block's FAIL lines to the same file. Do not commit.]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/by_contour_truth.json'));p=d['probes'];print(p['C02']['cuts'][1], p['C03']['cuts'][5], sorted(d['_meta']))"` prints `[6000.0, 8000.0, 10000.0, 12000.0] [4400.0, 4600.0, 4800.0]` and a list holding born_date, dash_commit, extracted, source, stata_version; `grep -c FAILED <scratch>/41-01-01-failure.txt` is at least 15; no FAILED line names `TestTheFixture`; the file holds `Q4101-1 FAIL`.]]></verify>
  <done>twoway's by() contour cuts were recorded in a stamped fixture and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="41-01-02">
  <name>Share the first panel's range at build</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Run `gitnexus impact map_contour --direction upstream --repo dash`, and the same for `_expand_by_groups`, `_dash_fn_panel_spec` and `ServerAppBuilder._generate_app_source_body`; report HIGH or CRITICAL (an UNKNOWN result is confirmed with `grep -n`). Re-read `map_contour` as WP-37 (37-01..37-03) left it and match TR-41-01.1's rows to its `uz`; locate 37-03's `cg` branch and its `_dash_contour_panel_spec` lines (saved and served) and leave them unchanged (D-41-01.e). Apply TR-41-01.1 to TR-41-01.6 and TR-41-01.9 (the four build helpers' copy-list entries and function_test_map rows; `_dash_by_first_zranges` is added in 41-01-03). Re-read `_expand_by_groups` (:63056-63175) and the served `_panels` lines (:70780-70835) before inserting; the served lines are string literals in `_generate_app_source_body`, indented as their neighbours. Run `python3 -m pytest test/test_by_contour_cuts.py -k "TestByContourCuts or TestTheRule or TestTheFixture or TestGridPanels" -q -n0` and, with no `-k`, `python3 -m pytest test/test_contour_layers.py test/test_contour_interp.py test/test_contour_gen.py test/test_function_panels.py test/test_function_test_map.py -q -n0`.]]></action>
  <verify><![CDATA[Both runs report 0 failed; `grep -c "_dash_by_zrange_spec(" dash_render.py` is at least 3 (definition, saved call, served literal).]]></verify>
  <done>Every by() panel's contour was cut at its first panel's cuts at build, in the saved page and the served app.</done>
</task>

<task type="auto" id="41-01-03">
  <name>Share it after a filter move</name>
  <files>dash_render.py, test/js_runner.py, test/function_test_map.py</files>
  <action><![CDATA[Run `gitnexus impact _dash_redraw_for --direction upstream --repo dash` and the same for `_dash_move_compute`; report HIGH or CRITICAL. Apply TR-41-01.7 (served closure, registration, `_dash_by_first_zranges` with its copy-list entry after `"_dash_by_zrange_spec",`, the two redraw call sites) and TR-41-01.8 (the three JS functions before `// agg_sources is a Bokeh model list`, the branch's `_su` line, the `_dash_zfirst` line after `JSON.parse(agg_configs_json)`, the override after the kept-range loop). Check test/js_runner.py's helper slice still ends at that comment; edit it only if it is bounded by a function name. Run `python3 -m pytest test/test_by_contour_cuts.py test/test_contour_js.py test/test_contour_key_moves.py test/test_js_runner.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py -q -n0` (no `-k`).]]></action>
  <verify><![CDATA[That run reports 0 failed; `python3 -c "import dash_render as d;j=d._FILTER_JS;print(j.index('function dash_contour_zfirst') < j.index('// agg_sources is a Bokeh model list') < j.index('const _dash_zfirst'))"` prints True.]]></verify>
  <done>After a filter move both modes re-cut every panel at the first panel that keeps rows.</done>
</task>

<task type="auto" id="41-01-04">
  <name>Document, track and commit BY-28</name>
  <files>dash.sthlp, test/test_mode_parity.py, test/test_tracking_documents.py</files>
  <action><![CDATA[Apply TR-41-01.10. Append the parity entry to test/test_mode_parity.py's `CORPUS` (R8). Run `python3 -m pytest test/test_mode_parity.py -k contour -q -n0` on its own (a `-k` applies to every file on its command line), then, with no `-k`, `python3 -m pytest test/test_by_contour_cuts.py test/test_help_conformance.py test/test_function_test_map.py test/test_fixtures_are_committed.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName -q -n0`, and the S01 block (`WP41_ONLY=S01`). Close BY-28's BUGS.md entry (PD-4 closed form: "Fixed <date> (WP-41, BY-28). Under by() map_contour cuts every panel at the first panel's z range (_dash_by_contour_zranges, _dash_by_zrange_spec), saved and served at build, and after a move through dash_contour_zfirst and _dash_by_first_zranges. Pinned by test/test_by_contour_cuts.py::TestByContourCuts::test_panels_share_the_first_panels_cuts, Q4101-1; fixture test/fixtures/by_contour_truth.json. Closes GAPS4 BY-28 (WP-41, BY-28)."), flip `- [ ]` to `- [x]`, rewrite the GAPS4 Tracked line (`Closed in WP-41, BUGS.md "<title>", commit pending.`), delete `BY-28` from `GAPS4_OPEN` in test/test_tracking_documents.py, and add under `### Fixed in WP-41`: "contour and contourline under by() cut every panel at the first panel's cuts, as twoway does; by(rep78, total) drew 4, 5, 3, 3, 4 and 3 levels, now 4 in every panel (WP-41, BY-28)". Run test/test_tracking_documents.py. The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h), before the commit: (1) run `awk -F'\t' '$1 == "BY-28" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the plain rows; a `BY-28 (documented)` or `BY-28 (residual)` row stays, A-10) and `git add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py BY-28` and delete every `<file>:<line>` row it prints from its `*_KNOWN` table (staging each file it edits) -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion 33-10 names (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`; `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN`, e.g. `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `ABBREV_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (D-33-10.a; no ruling of this section keeps one, so none is expected: every panel is cut as twoway cuts it (D-41-01.a)) -- then rerun, with no `-k`, each test file whose table it edited (its comparison reads the table, so a deleted row whose difference remains fails there) and run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); both pass; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the driver) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`, D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes) and add its `Fixture:` line to the commit body. Then the Commit boundary's pre-commit checks: `git pull --ff-only . main` in $WT (BRIEF "Pull form"; `Already up to date.` at the batch base; a refusal stops the task and is reported), `gitnexus detect-changes --scope all --repo .` and, when a cscript changed, the hygiene test the Commit boundary names. Stage the files named in this section (scripts/corpus/ledger.tsv and the regenerated fixtures included) and commit with BRIEF's body lines; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[Both pytest runs report 0 failed; the log shows `Q4101-1 PASS` and no SKIP; `awk -F'\t' '$1 == "BY-28"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py BY-28` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s` ends `(WP-41 BY-28)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>BY-28 was closed in one green commit with its help sentence, BUGS entry, Tracked line and changelog line, and no ledger or known-differences row named BY-28 alone.</done>
</task>

## Section completion criteria

- Every stub green; Q4101-1 PASS; no test deleted or flipped.
- Five new helpers on the served copy tuple and in function_test_map.py; the JS twin pinned by node; 37-03's gridded panels drawn unchanged (test/test_contour_gen.py green).
- No plain `BY-28` row left in scripts/corpus/ledger.tsv or any `*_KNOWN` table; corpus_ledger.json regenerated; corpus_guard_truth.json regenerated if Q3309-1 reported any change for a guard example (an improved verdict or a changed field).
- dash.sthlp, BUGS.md, GAPS4.md, CHANGELOG.md and GAPS4_OPEN changed in the BY-28 commit.

## Notes

- **Help paragraph owned (R3):** dash.sthlp's contour cuts paragraph (one sentence added). No Differences entry: dash matches twoway.
- **Merge rules touched:** R1 (S01 block), R2 (five names), R3, R5, R7, R8, R12 (`_FILTER_JS`, `_generate_app_source_body` this batch).
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** Each closing task (41-01-04 for BY-28) deletes its item's plain rows of scripts/corpus/ledger.tsv, regenerates corpus_ledger.json (D-33-05.i), deletes every row `python3 test/known_differences.py <id>` prints and runs the hygiene command it prints (D-33-10.h) and regenerates corpus_guard_truth.json if Q3309-1 reports any change for a guard example (33-09, D-33-09.c), before its own commit.
- **Trap:** the Total panel is `groups[-1]` with `attrs["_dash_total"]`; the first panel is `groups[0]` and is Total only when it is alone -- take its plots from `_dash_total_spec` then.
- **Trap:** `_dash_by_panel_dropped` may leave a group out; the first panel is the first group kept, which is what `groups[0]` already is.
- **Trap:** a panel index in `zpanel` is the place in the drawn panels; `_dash_fn_panel_spec` uses the same index.
- **Trap:** the saved branch's kept-range loop tests x and y as stored and z in Stata units; `dash_contour_kept_zrange` keeps exactly that (it overrides that loop's result), while `_dash_contour_zrange_of` follows `GlyphMapper._masked` (the build). They agree on every fixture row; a date x or y with no Stata date is the one case where the two paths already differ, and is left as it is.
- **Trap (37-03).** 37-03's `contour_gen` output does reach by() panels at the base (gridded layers, D-41-01.e): those panels already carry Stata's first-panel cuts and are not re-cut; only dash-fitted panels read `_dash_by_zrange`/`_dash_by_zcuts`. After a move the saved page leaves a gridded panel at its build drawing, marked stale (37-03: no `_dash_agg_config`), so `dash_contour_zfirst` sees only the dash-fitted panels' configs, while the served redraw refits a gridded panel whose rows changed (37-03 drops its object) and takes part in `_dash_by_first_zranges`; that stale-versus-refit split is 37-03's, and TestAfterAMove's scattered-data case is where both modes must agree.
- **Functions edited** (for the manifest's Owns cell, which names `_dash_share_by_scales z` and `dash_contour_cuts`, neither edited here): `map_contour` (its dash-fit path only), `_expand_by_groups`, the saved figure loop, `_dash_redraw_for`, `_dash_move_compute`, `ServerAppBuilder._generate_app_source_body` (R12), `_FILTER_JS` (R12), and the five new helpers.
- **Commit-body lines:** `Regression: test/test_by_contour_cuts.py::TestByContourCuts::test_panels_share_the_first_panels_cuts -- failed at <base> with <text>`; `Fixture: test/fixtures/by_contour_truth.json (scripts/extract_by_contour_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: BY-28 Tracked`. Body notes that the measured rule (first panel's cuts) supersedes the audit's union sketch.
