# Section 23: Contour interpolation, grid rule, cap and Stata truth (B4 part a)

> Part of: WP-31 · GAPS3 rows: B4a · Risk: red · Batch: 8 · Depends on: 01 · Blocks: 26, 29 · Tasks: 4, 1 commit · Case-id prefix: U23

## Overview

**What is wrong today.** GAPS3 B4 (GAPS3.md:113): "`contour`, `contourline` refused by name." dash.ado:4891-4893 answers both with `dash: 'contour' is a twoway plot type dash does not draw: it needs a surface interpolated over a grid. Use Stata's own twoway contour, or dash scatter y x, colorvar(z) to colour each point by z.` r(198). Nothing in dash_render.py builds a grid from scattered (x, y, z) or interpolates a surface. twoway does (research/bokeh-web.md §2, §11; stata-ground-truth.md §3): `twoway__contour_gen z y x, cuts() gen() [line] interp()` calls the compiled Mata `_contour_filled`/`_contour_line`, whose grid is `unique(x) × unique(y)` of the data with nodes filled by a thin-plate spline (kernel `sqrt(x²+y²)` with a degree-1 trend) or Shepard's `1/d²`, duplicates `(y,x)` taking the smallest z, `interp(none)` drawing only observed cells.

**After this section** dash_render.py holds the shared, numpy-only interpolation and grid helpers (`_dash_contour_grid`, `_dash_tps_fit`, `_dash_tps_eval`, `_dash_shepard`, `_dash_contour_surface`) transcribed from research/bokeh-web.md §2 (verified exact at the data points to 1e-14 and equal to scipy's `RBFInterpolator(kernel="linear", degree=1)` to 2e-14), the module constant `_DASH_CONTOUR_EXACT_MAX = 1000` (unique (x,y) points; A8) and the bounded fallback `_dash_contour_fallback_grid` (a 100×100 grid over the data's range, A8), and a Stata truth extractor `scripts/extract_contour_truth.do` writing `test/fixtures/contour_truth.json` from `twoway__contour_gen ..., gen(gz gy gx glev)` output on auto and a synthetic dataset. No plot type is registered yet and nothing is drawn: S26 (batch 9) registers `contour`/`contourline`, maps options, colours and the key, and calls these helpers; S29 (batch 10) writes the JavaScript twins. The helpers are on the served copy list from this section so that S26's mappers find them in both renderers.

**Why this split (A1).** B4 is an L row: the interpolation (a numerical module with its own truth), the drawing (registration, options, colours, Bokeh calls) and the JS twin (marching squares, isobands) are three sessions' work and three different risk profiles. S23 lands first so S26 can be written against tested helpers and a committed fixture.

**Test order and commit rule (rule 7, BRIEF).** One cycle, one commit `(WP-31 B4a)`. 23-01 writes the extractor, runs it, writes `test/test_contour_interp.py` and runs it red (every helper absent: `AttributeError`), saves `<scratch>/23-01-failure.txt`, never commits. 23-02 adds the helpers and the constant. 23-03 appends the truth block U23-1..U23-6 and the copy-list entries. 23-04 closes B4a (its own BUGS.md entry and GAPS3 Tracked line; the drawing is B4b, S26's row, and the saved-page refit B4c, S29's), updates the help's Dependencies paragraph (no new dependency: C3) and commits.

### Section decisions (binding on the executor)

- **D-23a. The kernel is `r = sqrt((x-xi)² + (y-yi)²)`, the trend `1 + x + y`.** Not `r² log r` (scipy's "thin_plate_spline", which does not match Stata: research/bokeh-web.md §2). The (n+3)×(n+3) system is `[[R, P],[Pᵀ, 0]] [w; a] = [z; 0]` solved with `numpy.linalg.solve`; a `LinAlgError` (duplicate points after de-duplication cannot occur; collinear data can) falls back to `numpy.linalg.lstsq` and sets `surface["note"] = "singular"`.
- **D-23b. The grid rule is twoway's, measured.** Nodes are `np.unique(x)` × `np.unique(y)` over the rows with finite x, y and z; duplicate `(y, x)` pairs keep the smallest z (bokeh-web.md §2 "Duplicate (y,x) -> smallest z (verified on the manual's 5-row example)"; stata-ground-truth.md §3 "duplicates (y,x): smallest z used (:91-94)"). Observed nodes keep their z; the rest are interpolated. Under `interp(none)` the rest are NaN and only cells whose four corners are observed draw (bokeh-web.md §1 gotcha: "ContourPy's NaN masking omits any cell touching a masked node").
- **D-23c. The cap and the fallback (A8, C1).** `n_unique = rows of the de-duplicated (x, y) set`. When `n_unique <= _DASH_CONTOUR_EXACT_MAX` (1000) the grid is exact (`unique(x) × unique(y)`, up to 10⁶ nodes evaluated in 4096-row chunks: n=1000 solve 0.01 s, eval of 10⁶ nodes ≈ 4 s worst case -- accepted: contour is exempt from timing tests, C2). Above the cap (confirmed by DECISIONS D4): the spline is fitted to a seeded random subsample of 1,000 de-duplicated points (`np.random.default_rng(20261010).choice(n_unique, _DASH_CONTOUR_EXACT_MAX, replace=False)`), evaluated on a 100×100 grid (`np.linspace(xmin, xmax, 100)` × `np.linspace(ymin, ymax, 100)`), and `surface["capped"] = True`. S26 reads `capped` to draw the stale cue on the saved page (the layer is tagged frozen) and a note naming the subsample (text fixed in S26); S29 reads it to skip the JS refit. Shepard above the cap uses the same subsample (n=1e5 × 100×100 is 4 s; bokeh-web.md §2).
- **D-23d. The surface object** returned by `_dash_contour_surface(x, y, z, interp, exact_max=_DASH_CONTOUR_EXACT_MAX)` is a plain dict, JSON-safe apart from the arrays: `{"gx": 1-D float array (nx), "gy": 1-D float array (ny), "gz": 2-D float array (ny, nx) with NaN where undrawn, "n_unique": int, "capped": bool, "interp": "thinplatespline"|"shepard"|"none", "zmin": float, "zmax": float (over the observed z), "note": ""|"singular"}`. Bokeh's `figure.contour(x=gx, y=gy, z=gz, ...)` takes exactly this (bokeh-web.md §1: `z` 2-D shape (ny, nx)).
- **D-23e. `interp()` spellings.** `thinplatespline` (default), `shepard`, `none`; twoway's abbreviations are measured by the extractor (`Interp(string asis)`, `zyx2view_parse:110-119`, class default `zyx2view_parse:30`); S26 owns the option parsing and passes the canonical word. An unknown word raises `ValueError` here; S26 turns it into the measured refusal.
- **D-23f. Truth is the generator's output, not the drawing.** The fixture records, per case, the de-duplicated input, the cuts, and `twoway__contour_gen`'s `gz gy gx glev` rows (polygon vertices with level ids for contour, line vertices for contourline) plus the heatmap form (`twoway__contour_gen ..., heatmap`, whose rectangles' edges expose the grid: midpoints of consecutive unique values and min/max, bokeh-web.md §2). The grid nodes' z values are read from the heatmap rectangles' level ids and, where the `.Graph` exposes them, from the serset; U23 compares dash's grid axes to the rectangle edges and dash's node levels to the heatmap's level per rectangle. Polygon-level comparisons are S26's (U26).

## Risk: [red] -- a numerical module whose truth lives in compiled Mata, with a cost cliff

**Why.** The grid-and-polygon rule is compiled (`_contour_filled`, bokeh-web.md §2 "Not verified: the exact marching rule"); only the generator's output can be compared. The TPS solve is O(n³) and the evaluation O(nodes × n); twoway itself did not finish n=3000 in ten minutes.

**Risk factors.**
1. A mismatch between Stata's kernel and the transcription (sign, trend, duplicate rule) only shows against the fixture.
2. Memory: an exact grid of 1000×1000 nodes is 8 MB per array, fine; the dense (n+3)² system at n=1000 is 8 MB; above the cap the subsample keeps both bounded.
3. Degenerate inputs: fewer than 3 distinct points (the system is singular), all x equal (one grid column: no cell), z constant (no cut).
4. The copy list: five new module functions and one constant must reach the served app or S26's served redraw fails with `NameError`.
5. Floating noise at the data points: the fixture's heatmap levels are integers per rectangle; node z within 1e-9 of a cut flips a level.

**Mitigation.**
1. U23-3 compares every observed-node z and every interpolated node's level against the heatmap fixture on three cases; `TestAgainstScipyFormula` (guard, skipped without scipy) pins the formula to `RBFInterpolator(kernel="linear", degree=1)` at 1e-10.
2. `_dash_tps_eval` evaluates in 4096-node chunks (bokeh-web.md §2 code); `TestTheCap` pins `capped` at 1001 and the 100×100 shape.
3. `_dash_contour_surface` returns `gz` all-NaN with `note="degenerate"` for `n_unique < 3`, and a 1-node axis yields `gz` of shape (ny, 1): S26 draws nothing and notes it (twoway's own answer is measured by the extractor, case `degenerate_*`).
4. R2 anchors below; `TestTheServedAppCarriesEveryName`.
5. Comparisons use `np.isclose(rtol=1e-6, atol=1e-9)` on z and compare levels only where `|z - cut| > 1e-6 * (zmax - zmin)`.

## Dependencies

- **Depends on: 01.** BUGS.md entry B4a, GAPS3 Tracked line, CHANGELOG marker, the truth script block `// 70.`.
- **Blocks: 26** (the mappers call these helpers; the fixture's polygon cases are U26's), **29** (the JS twins are transcriptions of these functions and are pinned to them).
- **Parallel batch: 8**, merge order S25, S23, S24. **Can run with S24 and S25**: S23 adds new module-level functions and one constant only (no existing function edited apart from the two copy tuples); S24 edits the axis ticker/LabelSet code; S25 edits `_FILTER_JS`.

## Evidence

All anchors at `6370ca4`.

### The refusal and the empty renderer

dash.ado:4891-4893 (quoted in S21 Evidence). `grep -n "contour\|thinplate\|shepard" dash_render.py` returns only the help-text constant for `coloruseplegend` and comments: no helper exists. Dependencies: both installed Bokehs require `contourpy>=1.2` (3.9.0 with contourpy 1.3.3 under python3; 3.8.0 with 1.3.3 under /opt/anaconda3; probed 10oct2026), so no new package (C3, M22). The served header's import comment (dash_render.py:48021-48026) says "No scipy and no statsmodels": the helpers use numpy only.

### The verified reference implementation (research/bokeh-web.md §2, lines 49-75)

```python
def tps_fit(x, y, z):
    x, y, z = (np.asarray(a, float) for a in (x, y, z)); n = x.size
    r = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
    P = np.column_stack([np.ones(n), x, y])
    A = np.zeros((n + 3, n + 3)); A[:n, :n] = r; A[:n, n:] = P; A[n:, :n] = P.T
    return np.linalg.solve(A, np.concatenate([z, np.zeros(3)]))
def tps_eval(w, x, y, gx, gy):
    ...  out[s:s+4096] = r @ w[:n] + w[n] + w[n+1] * gx[s:s+4096] + w[n+2] * gy[s:s+4096]
def shepard(x, y, z, gx, gy):
    ...  wgt = np.where(hit, 0.0, 1.0 / np.where(hit, 1.0, d2)); val = (wgt @ z) / wgt.sum(axis=1)
    ...  anyhit = hit.any(axis=1); val[anyhit] = z[hit.argmax(axis=1)[anyhit]]
```
Measured cost (same section): n=1000 solve 0.01 s / eval 0.04 s on a 100×100 grid; n=2000 0.06/0.08 s; Shepard n=1e5 -> 100×100: 4.05 s.

### Stata's rule (stata-ground-truth.md §3; bokeh-web.md §2, §11)

`twoway__contour_gen.ado:6-7` syntax `varlist(min=3 max=3 numeric) [if] [in], cuts(numlist) [gen(namelist min=4 max=4)] [line] [heatmap] [Interp(string)]`; `:33-46` calls `_contour_heatmap`/`_contour_filled`/`_contour_line(z, y, x, cuts, interp)`; `:47-64` `getmata (x y z lev)` renamed to `gen()`'s four names (default `z y x levels`). The manual's formulas: TPS `z = Σ wᵢ f(y-yᵢ, x-xᵢ) + w(n+1) + w(n+2) x + w(n+3) y`, `f(y,x) = sqrt(y² + x²)`; Shepard `z = Σ zᵢ fᵢ / Σ fᵢ`, `f = 1/(x² + y²)`; "regular grid" = every nonmissing (y,x) combination has a z; duplicates take the smallest z. Measured: grid `unique(x) × unique(y)`; heatmap rect edges at midpoints and min/max; n=3000 did not finish.

### Tests that pin today's behaviour

None pin the absence of these helpers. test_function_test_map.py requires an entry per new function (TR-23.5). test_dependency_guards.py:575 requires every unguarded top-level import to be the standard library: the helpers import nothing new.

## User stories

- **US-23.1** As a Stata user, I want dash's contour surface to be the one twoway computes (same kernel, same grid, same duplicate rule) so that the picture matches twoway's at every observed point and level.
- **US-23.2** As a user with many thousand points, I want dash to draw a contour anyway, bounded in time and memory, and to tell me it is approximate.
- **US-23.3** As a developer of S26/S29, I want one documented surface object and a committed fixture to test against.

## Business requirements

- **BR-23.1** The surface through observed points reproduces each observed z exactly (to 1e-9 relative) under thinplatespline and shepard.
- **BR-23.2** The grid axes are the distinct x and y values of the data; duplicates keep the smallest z; `interp(none)` leaves unobserved nodes undrawn.
- **BR-23.3** Up to 1000 distinct (x,y) points the computation is exact; above, it is bounded (100×100) and flagged.
- **BR-23.4** Interpolated node levels agree with twoway's heatmap levels on the fixture cases.
- **BR-23.5** Nothing a user runs changes in this section (no plot type is registered until S26).

## Technical requirements

- **TR-23.1 constant.** After `_MAX_MBANDS = 1000` (dash_render.py:11706) add:
  ```python
  # The largest number of distinct (x, y) points a contour surface is fitted
  # to exactly on twoway's own grid (unique(x) x unique(y)); above it the
  # surface is fitted to a fixed subsample and evaluated on a 100x100 grid,
  # and the layer is flagged (WP-31 B4a, decision A8).
  _DASH_CONTOUR_EXACT_MAX = 1000
  _DASH_CONTOUR_FALLBACK_N = 100
  _DASH_CONTOUR_INTERPS = ("thinplatespline", "shepard", "none")
  ```
- **TR-23.2 the helpers**, added as module-level functions after `_natural_cubic_spline` (:22385ff; before `_dash_note_no_second_y`), numpy only:
  ```python
  def _dash_contour_points(x, y, z):
      """De-duplicated finite (x, y, z): one row per distinct (y, x) pair,
      the smallest z kept, sorted by (y, x) (twoway's duplicate rule)."""
      x, y, z = (np.asarray(a, dtype=float).ravel() for a in (x, y, z))
      keep = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
      x, y, z = x[keep], y[keep], z[keep]
      if x.size == 0:
          return x, y, z
      order = np.lexsort((z, x, y))          # by y, then x, then z ascending
      x, y, z = x[order], y[order], z[order]
      first = np.ones(x.size, dtype=bool)
      first[1:] = (x[1:] != x[:-1]) | (y[1:] != y[:-1])
      return x[first], y[first], z[first]

  def _dash_tps_fit(x, y, z):
      """Weights of Stata's thin-plate spline: kernel sqrt(dx^2 + dy^2) with
      a degree-1 trend, from the (n+3)-square system.  Returns (w, note)."""
      x, y, z = (np.asarray(a, dtype=float) for a in (x, y, z))
      n = x.size
      r = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
      P = np.column_stack([np.ones(n), x, y])
      A = np.zeros((n + 3, n + 3))
      A[:n, :n] = r; A[:n, n:] = P; A[n:, :n] = P.T
      rhs = np.concatenate([z, np.zeros(3)])
      try:
          return np.linalg.solve(A, rhs), ""
      except np.linalg.LinAlgError:
          return np.linalg.lstsq(A, rhs, rcond=None)[0], "singular"

  def _dash_tps_eval(w, x, y, gx, gy):
      """The spline at (gx, gy), in 4096-node chunks (memory chunk x n)."""
      x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
      n = x.size
      gx, gy = np.asarray(gx, dtype=float).ravel(), np.asarray(gy, dtype=float).ravel()
      out = np.empty(gx.size)
      for s in range(0, gx.size, 4096):
          r = np.hypot(gx[s:s+4096, None] - x[None, :], gy[s:s+4096, None] - y[None, :])
          out[s:s+4096] = r @ w[:n] + w[n] + w[n+1] * gx[s:s+4096] + w[n+2] * gy[s:s+4096]
      return out

  def _dash_shepard(x, y, z, gx, gy):
      """Stata's shepard: 1/d^2 weights over every point; a node on a data
      point takes that point's z."""
      x, y, z = (np.asarray(a, dtype=float) for a in (x, y, z))
      gx, gy = np.asarray(gx, dtype=float).ravel(), np.asarray(gy, dtype=float).ravel()
      out = np.empty(gx.size)
      for s in range(0, gx.size, 4096):
          d2 = (gx[s:s+4096, None] - x[None, :])**2 + (gy[s:s+4096, None] - y[None, :])**2
          hit = d2 == 0
          wgt = np.where(hit, 0.0, 1.0 / np.where(hit, 1.0, d2))
          val = (wgt @ z) / wgt.sum(axis=1)
          anyhit = hit.any(axis=1)
          val[anyhit] = z[hit.argmax(axis=1)[anyhit]]
          out[s:s+4096] = val
      return out

  def _dash_contour_grid(x, y):
      """twoway's grid: the distinct x and the distinct y of the data."""
      return np.unique(np.asarray(x, dtype=float)), np.unique(np.asarray(y, dtype=float))

  def _dash_contour_fallback_grid(x, y, n=_DASH_CONTOUR_FALLBACK_N):
      """A bounded n x n grid over the data's range (A8), for a layer over
      _DASH_CONTOUR_EXACT_MAX distinct points."""
      x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
      return (np.linspace(x.min(), x.max(), n), np.linspace(y.min(), y.max(), n))

  def _dash_contour_surface(x, y, z, interp="thinplatespline",
                            exact_max=_DASH_CONTOUR_EXACT_MAX):
      """The surface twoway contour draws from (x, y, z): see D-23d."""
      interp = str(interp or "thinplatespline").strip().lower()
      if interp not in _DASH_CONTOUR_INTERPS:
          raise ValueError("interp(%s) is not thinplatespline, shepard or none" % interp)
      px, py, pz = _dash_contour_points(x, y, z)
      n = px.size
      out = {"n_unique": int(n), "capped": False, "interp": interp, "note": "",
             "zmin": float(pz.min()) if n else float("nan"),
             "zmax": float(pz.max()) if n else float("nan")}
      if n < 3:
          gx, gy = _dash_contour_grid(px, py) if n else (np.array([]), np.array([]))
          out.update(gx=gx, gy=gy, gz=np.full((gy.size, gx.size), np.nan), note="degenerate")
          return out
      if n > exact_max:
          rng = np.random.default_rng(20261010)
          pick = np.sort(rng.choice(n, exact_max, replace=False))
          fx, fy, fz = px[pick], py[pick], pz[pick]
          gx, gy = _dash_contour_fallback_grid(px, py)
          out["capped"] = True
      else:
          fx, fy, fz = px, py, pz
          gx, gy = _dash_contour_grid(px, py)
      GX, GY = np.meshgrid(gx, gy)                # shape (ny, nx)
      if interp == "none":
          gz = np.full(GX.shape, np.nan)
      elif interp == "shepard":
          gz = _dash_shepard(fx, fy, fz, GX, GY).reshape(GX.shape)
      else:
          w, note = _dash_tps_fit(fx, fy, fz)
          out["note"] = note
          gz = _dash_tps_eval(w, fx, fy, GX, GY).reshape(GX.shape)
      # Observed nodes keep their own z (exact under every method; the
      # only values interp(none) draws).
      if not out["capped"]:
          ix = np.searchsorted(gx, px); iy = np.searchsorted(gy, py)
          gz[iy, ix] = pz
      out.update(gx=gx, gy=gy, gz=gz)
      return out
  ```
  Under `capped`, the observed-node overwrite is skipped: the fallback grid's nodes are not the data's.
- **TR-23.3 served copy list (R2).** Append to the functions tuple (dash_render.py:46822-47270) after `"_dash_reference_lines",` (:47223): `"_dash_contour_points", "_dash_tps_fit", "_dash_tps_eval", "_dash_shepard", "_dash_contour_grid", "_dash_contour_fallback_grid", "_dash_contour_surface",`; append to the constants tuple after `_DASH_STALE_STATUS_HTML` (:46584-46784 region): `"_DASH_CONTOUR_EXACT_MAX", "_DASH_CONTOUR_FALLBACK_N", "_DASH_CONTOUR_INTERPS",`. (S24 appends after `_dash_reference_lines` too in batch 8: the merger lands S25, S23, S24 in that order; S24's Notes must name S23's last entry `_dash_contour_surface` as its anchor -- recorded for the index's R2 table.)
- **TR-23.4 the extractor** `scripts/extract_contour_truth.do` -- see Stata truth.
- **TR-23.5 maps.** function_test_map.py: `'_dash_contour_points': 'test/test_contour_interp.py::TestTheGridRule::test_duplicates_keep_the_smallest_z'`, `'_dash_tps_fit': 'test/test_contour_interp.py::TestTps::test_exact_at_the_data'`, `'_dash_tps_eval': ...::test_exact_at_the_data`, `'_dash_shepard': 'test/test_contour_interp.py::TestShepard::test_exact_at_the_data'`, `'_dash_contour_grid': 'test/test_contour_interp.py::TestTheGridRule::test_axes_are_the_distinct_values'`, `'_dash_contour_fallback_grid': 'test/test_contour_interp.py::TestTheCap::test_above_the_cap_is_a_100_grid'`, `'_dash_contour_surface': 'test/test_contour_interp.py::TestAgainstTheFixture::test_node_levels_match_twoways_heatmap'`. No Stata program or Mata function is added (program_coverage_map.py unchanged).
- **TR-23.6 dash.sthlp Dependencies** (:5136ff): no change in words ("optional -- none") -- the executor verifies `grep -c scipy dash_render.py` is unchanged; test_dependency_guards.py stays green.

## Boundaries

- No plot type is registered: do not touch `_dash_plottype_families`, `_dash_undrawn_plottype`, `_dash_glyph_dispatch`, `_make_figure_body`, `_dash_draw_layer`, dash.sthlp's Plot types or Not-drawn text (S26).
- No JavaScript, no `_FILTER_JS`, no `_dash_stale_kind` change (S25 owns `_FILTER_JS` in batch 8; S29 owns the contour JS).
- No scipy, no contourpy import here (contourpy is reached only through Bokeh's `figure.contour` in S26).
- Do not edit `_dash_reference_lines` or S24's axis code.

## Stata truth

`scripts/extract_contour_truth.do` (new). Header and guards as in scripts/extract_default_base_truth.do:1-60 (prefix `ZC_`); python block as :160-200 (`_meta` with `source: "scripts/extract_contour_truth.do"`). Datasets: (a) `sysuse auto`: z=`mpg`, y=`weight`, x=`length` (74 rows, duplicates in (weight,length) exist: the duplicate rule is exercised); (b) synthetic `set obs 60; set seed 20261010; gen x = runiform()*10; gen y = runiform()*5; gen z = sin(x)*cos(y) + rnormal(0,.05)` (no duplicates, 60×60 grid); (c) the manual's 5-row example with a duplicate pair (`twoway_contour.sthlp` interp remarks :91-94: rows `(y,x,z)` = (1,1,1) (1,2,2) (2,1,3) (2,2,4) (2,2,5)) -- the fixture records which z the duplicate keeps.

Per dataset and per `interp` in `thinplatespline shepard none`, with `cuts` = three fixed values at the 25/50/75 percentiles of z (`_pctile z, p(25 50 75)`), the probes:

| Key | Command | Recorded |
|---|---|---|
| `cases.<ds>.<interp>.input` | the de-duplicated rows (`bysort y x: keep if _n==1` after `sort y x z`) | `x y z` arrays, `n_rows`, `n_unique` |
| `cases.<ds>.<interp>.cuts` | | the three cuts |
| `cases.<ds>.<interp>.heatmap` | `preserve; twoway__contour_gen z y x, cuts(<cuts>) gen(gz gy gx glev) heatmap interp(<interp>)` | `gx gy gz glev` rows (rectangle corners and level ids), `n_rows` |
| `cases.<ds>.<interp>.filled` | `... gen(gz gy gx glev) interp(<interp>)` | polygon vertex rows `gx gy gz glev`, `n_rows` (U26's truth) |
| `cases.<ds>.<interp>.line` | `... gen(gz gy gx glev) line interp(<interp>)` | line vertex rows, `n_rows` (U26's truth) |
| `cases.<ds>.<interp>.rc` | each generator call | `rc` and error line when non-zero (e.g. `interp(none)` on auto) |
| `grid.<ds>` | from `heatmap`: `levelsof gx`, `levelsof gy` | the distinct rectangle-edge coordinates (expected: midpoints of consecutive distinct data x/y plus min and max) |
| `degenerate.two_points`, `degenerate.one_x` | `twoway contour z y x` on 2 rows; on rows with one distinct x | `rc`, error line |
| `interp_abbrev` | `twoway contour z y x, interp(thin)`, `interp(th)`, `interp(shep)`, `interp(no)`, `interp(bogus)` | rc, line (S26's refusal text) |
| `cost.n3000` | not run (bokeh-web.md §2: >10 min); recorded as a note | -- |

Generator rows are written with `%20.17g`. Output `test/fixtures/contour_truth.json`; `git add -f`; named by `test_contour_interp.py::TestTheFixture`. Run: `DASH_REPO=<wt> scripts/stata_slot.sh <scratch>/s23 <wt>/scripts/extract_contour_truth.do` (the auto thinplatespline run is 74 distinct-ish points: seconds; the 60-point synthetic: seconds).

Truth block in `test/test_wp31_truth.cscript` (`* ==== S23 B4a: contour interpolation ====`, WP31_ONLY gate, start/end lines):
- **U23-1** grid axes: a `python:` helper calls `dr._dash_contour_grid` on the fixture's input for auto; the midpoints of consecutive axis values plus min/max equal `grid.auto` edges (rtol 1e-6).
- **U23-2** duplicate rule: on the manual's 5-row case `_dash_contour_points` returns 4 rows with z=4 at (2,2); the fixture's heatmap level at that rectangle agrees with cutting z=4, not 5.
- **U23-3** node levels: for each of the three datasets under thinplatespline and shepard, `_dash_contour_surface(...)["gz"]` cut by the fixture's cuts (`np.searchsorted(cuts, gz, side="right")`) equals the heatmap's `glev` at each rectangle (levels compared where `|gz - cut| > 1e-6*(zmax-zmin)`), 100% agreement.
- **U23-4** `interp(none)`: dash's `gz` is finite exactly at the observed nodes; the heatmap writes rectangles only for those nodes (same count).
- **U23-5** cap: a 1001-point synthetic surface returns `capped=True`, `gz.shape == (100, 100)`; a 1000-point one `capped=False`.
- **U23-6** `interp(bogus)` raises `ValueError` whose text names the three words; the fixture's `interp_abbrev.bogus.rc` is 198 (S26 reuses the words).

## TDD test stubs

### Regression tests, `test/test_contour_interp.py` (new; red at 6370ca4: `AttributeError: module 'dash_render' has no attribute ...`)

- Test: `_dash_contour_points` keeps the smallest z of a duplicate pair and drops non-finite rows -- `TestTheGridRule::test_duplicates_keep_the_smallest_z` (red).
- Test: `_dash_contour_grid` returns the sorted distinct x and y -- `TestTheGridRule::test_axes_are_the_distinct_values` (red).
- Test: TPS reproduces each data z to 1e-9 on auto and the synthetic set; the trend is degree 1 (fitting `z = 2 + 3x - y` gives weights `w[:n] ≈ 0`, `w[n:] ≈ (2, 3, -1)`) -- `TestTps::test_exact_at_the_data`, `::test_a_plane_is_the_trend` (red).
- Test: Shepard reproduces each data z and gives the inverse-distance-squared mean elsewhere (hand case: two points, midpoint = mean) -- `TestShepard::test_exact_at_the_data`, `::test_midpoint_of_two` (red).
- Test: `interp("none")` leaves every unobserved node NaN -- `TestNone::test_only_observed_nodes` (red).
- Test: above the cap `capped` and a (100,100) grid; at the cap exact -- `TestTheCap::test_above_the_cap_is_a_100_grid`, `::test_at_the_cap_is_exact` (red).
- Test: `n_unique < 3` gives `note="degenerate"`, all-NaN -- `TestDegenerate::test_fewer_than_three` (red).
- Test: unknown interp raises `ValueError` -- `TestDegenerate::test_unknown_interp` (red).
- Test: node levels match the fixture's heatmap (U23-3 in Python, all datasets × interps) -- `TestAgainstTheFixture::test_node_levels_match_twoways_heatmap[ds-interp]` (red).
- Test: the grid edges match `grid.<ds>` -- `TestAgainstTheFixture::test_grid_edges_are_the_midpoints[ds]` (red).
- Test: the formula equals `scipy.interpolate.RBFInterpolator(kernel="linear", degree=1)` to 1e-10 -- `TestAgainstScipyFormula::test_linear_kernel_degree_one` (guard; `pytest.importorskip("scipy")`).
- Test: fixture `_meta` and keys -- `TestTheFixture::test_meta_and_cases` (guard after 23-01).
- Test: every new name is on the copy list and the served source defines it -- `TestServedCarries::test_names_copied` (red).
- Test: the module imports no new package (`grep` of `^import|^from` unchanged) -- `TestNoDependency::test_numpy_only` (guard).

### cscript cases: U23-1..U23-6 (truth block).

### Pinned tests to flip: none (no behaviour pinned today). Combined pins: function_test_map gains seven entries; no counts move.

### Parity corpus: none in S23 (nothing is drawn); S26 adds the entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| kernel, trend, Shepard, duplicates, grid | pytest test_contour_interp.py | contour_truth.json | n/a (shared helpers) |
| node levels vs twoway heatmap | pytest TestAgainstTheFixture; cscript U23-3 | contour_truth.json | n/a |
| cap and fallback | pytest TestTheCap; cscript U23-5 | -- | n/a |
| copy list | TestServedCarries, TestTheServedAppCarriesEveryName | -- | served |
| formula cross-check | TestAgainstScipyFormula (skips without scipy) | -- | n/a |

Acceptance: **AC-23.1** exact at the data (1e-9); **AC-23.2** levels agree with twoway's heatmap on every fixture case; **AC-23.3** grid edges are the midpoints; **AC-23.4** cap at 1001 with a (100,100) grid and `capped`; **AC-23.5** names copied; **AC-23.6** one green commit.

## Tasks

**Commit boundary.** 23-01..23-04 form the one commit `Add twoway's contour interpolation, grid rule and truth fixture (WP-31 B4a)`.

<task type="auto" id="23-01">
  <name>Write the extractor and failing tests</name>
  <files>scripts/extract_contour_truth.do, test/test_contour_interp.py, test/fixtures/contour_truth.json</files>
  <action><![CDATA[Create scripts/extract_contour_truth.do per "Stata truth" (copy the header, guards and the python block pattern from scripts/extract_default_base_truth.do:1-60 and :160-200, prefix ZC_; record each generator run under `preserve ... restore`; write rows with %20.17g to a record file and build the JSON in one trailing python block that never calls back into Stata, as scripts/extract_stat_truth.do:50-57 explains). Run `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s23 $WT/scripts/extract_contour_truth.do`; confirm the fixture holds `_meta`, three `cases.*` datasets x three interps, `grid.*`, `degenerate.*`, `interp_abbrev.*`. Create test/test_contour_interp.py with every stub under "TDD test stubs". Run `python3 -m pytest test/test_contour_interp.py -q -n0 -p no:cacheprovider 2>&1 | tee <scratch>/23-01-failure.txt` against the unmodified tree. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "AttributeError: module 'dash_render' has no attribute '_dash_contour" <scratch>/23-01-failure.txt` is at least 5; `python3 -c "import json;d=json.load(open('test/fixtures/contour_truth.json'));print(sorted(d['cases']), sorted(d['_meta']))"` prints `['auto', 'manual5', 'synthetic'] ['born_date', 'dash_commit', 'extracted', 'source', 'stata_version']`; `python3 -c "import json;d=json.load(open('test/fixtures/contour_truth.json'));print(d['cases']['manual5']['thinplatespline']['input']['n_unique'])"` prints 4.]]></verify>
  <done>The contour truth fixture was measured from twoway's generator and the interpolation tests failed against the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="23-02">
  <name>Add the interpolation helpers and constants</name>
  <files>dash_render.py</files>
  <action><![CDATA[Insert TR-23.1's three constants after `_MAX_MBANDS = 1000` (dash_render.py:11706) and TR-23.2's seven functions, verbatim, after `_natural_cubic_spline` (the function ending before `_dash_note_no_second_y`, :22385ff). Add no import. Run `python3 -m pytest test/test_contour_interp.py -q -n0 -p no:cacheprovider -k "not Served and not Fixture"` and `python3 -m pytest test/test_dependency_guards.py -q -p no:cacheprovider`.]]></action>
  <verify><![CDATA[The first run reports 0 failed (TestAgainstScipyFormula passes or is skipped); test_dependency_guards.py reports 0 failed; `grep -c "^def _dash_contour_\|^def _dash_tps_\|^def _dash_shepard" dash_render.py` prints 7; `grep -c "^_DASH_CONTOUR_EXACT_MAX = 1000" dash_render.py` prints 1.]]></verify>
  <done>dash_render.py held twoway's TPS and Shepard interpolation, the grid and duplicate rules, the cap and the bounded fallback, exact at the data and agreeing with twoway's heatmap levels.</done>
</task>

<task type="auto" id="23-03">
  <name>Copy the helpers to the served app and add the truth block</name>
  <files>dash_render.py, test/test_wp31_truth.cscript, test/function_test_map.py</files>
  <action><![CDATA[Make TR-23.3 (functions tuple entries after `"_dash_reference_lines",` at :47223; constants after `_DASH_STALE_STATUS_HTML`) and TR-23.5 (seven function_test_map.py entries under a `# WP-31 S23` comment). Append the S23 block with U23-1..U23-6 above `* ==== append new blocks above this line ====` in test/test_wp31_truth.cscript (its python helper imports dash_render from `..` as the S14 block of test_wp30_truth.cscript:2991-3010 does). Run `python3 -m pytest test/test_contour_interp.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" test/test_function_test_map.py "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` and the truth block through the driver (`WP31_ONLY=S23`).]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -c "U23-[1-6] PASS" <scratch>/s23/run_test_wp31_truth.log` prints 6 and the log ends `ALL CHECKS PASSED`; `grep -c '"_dash_contour_surface",' dash_render.py` prints 1; `grep -c "'_dash_contour_surface'" test/function_test_map.py` prints 1.]]></verify>
  <done>The served app carried the contour helpers, the function map named their tests, and Stata certified the grid, duplicate rule, node levels, interp(none) and the cap.</done>
</task>

<task type="auto" id="23-04">
  <name>Close B4a and commit</name>
  <files>BUGS.md, GAPS3.md, CHANGELOG.md</files>
  <action><![CDATA[BUGS.md: close the "B4a" entry in place (`- [x]`) with `- Resolution: Fixed <ddmonyyyy> (WP-31, B4a). dash_render.py gained twoway's contour interpolation as shared helpers (_dash_contour_points, _dash_tps_fit, _dash_tps_eval, _dash_shepard, _dash_contour_grid, _dash_contour_fallback_grid, _dash_contour_surface) with the kernel sqrt(x^2+y^2) and a degree-1 trend, Shepard's 1/d^2, twoway's unique(x) x unique(y) grid and smallest-z duplicate rule, exact up to _DASH_CONTOUR_EXACT_MAX = 1000 distinct points and a flagged 100x100 grid above, copied into the served app. Pinned by test/test_contour_interp.py::TestAgainstTheFixture::test_node_levels_match_twoways_heatmap, test/test_wp31_truth.cscript U23-3; fixture test/fixtures/contour_truth.json. Drawing is B4b (section 26) and the saved page's refit B4c (section 29), each its own GAPS3 row. Closes GAPS3 B4a (WP-31, B4a).`. GAPS3.md §9: rewrite the `- **B4a Tracked:**` line (S01 opens B4a, B4b and B4c as three lines; the tracking test's open set is keyed by those ids) to `- **B4a Tracked:** Closed in WP-31, BUGS.md "<B4a title>", commit pending.`; write `commit pending` literally: the merger's step k.3b fills the sha (DECISIONS A11). The B4b and B4c lines are untouched. CHANGELOG.md: replace `<!-- WP-31 B4a -->` under `### Fixed in WP-31` with `- The contour surface twoway computes (thin-plate spline with kernel sqrt(x^2+y^2) and a linear trend, Shepard 1/d^2, the unique(x) x unique(y) grid, smallest-z duplicates) is available to the renderers; no plot type uses it until B4b. (WP-31, B4a)`. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Stage dash_render.py scripts/extract_contour_truth.do test/test_contour_interp.py test/test_wp31_truth.cscript test/function_test_map.py BUGS.md GAPS3.md CHANGELOG.md and `git add -f test/fixtures/contour_truth.json`; commit `Add twoway's contour interpolation, grid rule and truth fixture (WP-31 B4a)` with the body in BRIEF's forms (the saved failure text first).]]></action>
  <verify><![CDATA[`git log -1 --format=%s` ends `(WP-31 B4a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 B4a -->' CHANGELOG.md` prints 0; `grep -c "B4a Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `grep -c "B4[bc] Tracked:\*\* Open" GAPS3.md` prints 2; test_tracking_documents.py reports 0 failed.]]></verify>
  <done>B4a was closed with its Tracked line rewritten, the CHANGELOG line named the surface, and one green commit on wp31-s23 was ready for the merger.</done>
</task>

## Section completion criteria

- Seven numpy-only helpers and three constants in dash_render.py, copied to the served app; no new dependency.
- Exact at the data, degree-1 trend, Shepard midpoint, duplicate and grid rules pinned; node levels agree with twoway's heatmap on three datasets × two interps; `interp(none)` observed-only.
- Cap at 1000 with the flagged 100×100 fallback.
- `contour_truth.json` stamped, named, holding the filled and line generator rows S26 needs.
- U23-1..U23-6 PASS; one green commit; B4a closed, its Tracked line in the Closed form with `commit pending`.

## Notes

- **Shape convention.** `gz` is `(ny, nx)` -- rows are y. `np.meshgrid(gx, gy)` without `indexing=` gives that. Bokeh's `figure.contour(x, y, z)` expects it (bokeh-web.md §1). The JS twin (S29) must flatten row-major with the same convention.
- **Chunk size 4096** keeps `r` at 4096 × n doubles (32 MB at n=1000).
- **Why the subsample is seeded, not "first 1000".** Rows arrive in dataset order; a seeded choice is deterministic across both renderers and a filter move, so the served redraw and the saved build pick the same points for the same rows. S29 cannot refit above the cap (it has no numpy); it marks the layer frozen (S26's tag) and leaves it.
- **Decisions for maintainer ratification.** D-23c (above the cap: a seeded random subsample of 1,000 de-duplicated points for the spline fit, a 100×100 evaluation grid, the stale cue on the saved page and a note naming the subsample) is confirmed by DECISIONS D4. D-23a, D-23b, D-23d, D-23e and D-23f stand as written.
- **Fixture size.** The synthetic 60×60 heatmap writes 3600 rectangles × 4 corners; auto's grid is up to 74×74. Store heatmap rows as four parallel arrays; the fixture stays under 2 MB. If larger, store the synthetic case at 40 points (`set obs 40`) and record `n` in the fixture.
- **python_exec hazard** (project memory): check `~/.stata19/console/stata19.rc` after the extractor and the driver run.
- **Shared files (R1-R13).** R1: one S23 block. R2: seven functions after `_dash_reference_lines`, three constants after `_DASH_STALE_STATUS_HTML`; S24 (same batch) must anchor after `_dash_contour_surface` -- tell the merger. R4: one marker. R5: one entry; the B4a Tracked line in the Closed form with `commit pending` (A11). R7: one fixture. R12: S23 edits none of the hot functions.
- **For S26.** Call `_dash_contour_surface(x, y, z, interp)`; pass `surface["gx"], surface["gy"], surface["gz"]` to `figure.contour`; read `capped` for the note and the frozen tag; `zmin`/`zmax` for `levels()`/`minmax` cuts; the fixture's `cases.*.filled`/`.line` rows are U26's polygon truth; `interp_abbrev.*` gives the refusal text.
- **For S29.** Transcribe `_dash_contour_points`, `_dash_tps_fit` (Gaussian elimination with partial pivoting replaces `np.linalg.solve`), `_dash_tps_eval`, `_dash_shepard`, `_dash_contour_grid` to JS as `dash_contour_*`; pin each to its Python twin at 1e-9 on the fixture's inputs.
