# Section 29: The saved page's contour refit in JavaScript (B4 part c)

> Part of: WP-31 · GAPS3 rows: B4c · Risk: red · Batch: 10 · Depends on: 26, 10 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U29

## Overview

**What is wrong today (after S26).** The saved page draws contour and contourline at build and marks them `(grid unfiltered)` after any filter move (S26 D-26j); the served app refits them. BokehJS has no contouring code (research/bokeh-web.md §1: "`contour` appears 4 times in bokeh.min.js, all the renderer class; `marching` 0"), so a saved page cannot call Bokeh to recompute; it must compute the polylines and the filled bands itself and write them into the two child sources (bokeh-web.md §1: "write `fill_renderer.data_source.data = {xs, ys, lower_levels, upper_levels, fill_color: <copied>}` and `line_renderer.data_source.data = {xs, ys, levels}`"; `xs/ys` for MultiPolygons are `[polygon][ring][points]`).

**After this section** `_FILTER_JS` carries named helpers `dash_contour_points`, `dash_tps_fit`, `dash_tps_eval`, `dash_shepard`, `dash_contour_grid`, `dash_contour_surface`, `dash_contour_segments`, `dash_contour_link`, `dash_contour_rings`, `dash_contour_lines`, `dash_contour_bands` (eleven; the solver is S10's `dash_solve`, DECISIONS A19) and a branch `else if (ac.type === 'contour' || ac.type === 'contourline')` inserted before `// DASH_FIT_BRANCHES_END`, which re-reads the kept rows' x, y, z jointly (A9's prelude generalisation from S10: `ac.xvar`, `ac.yvar`, plus `ac.zvar` here), rebuilds twoway's surface within the cap, cuts it at `ac.cuts`, and writes the fill and line sources. `_dash_stale_kind` returns None for the two types when the layer is within the cap, so the cue is gone there; above the cap the layer stays frozen and marked (M8). Parity: the JS level sets are compared with contourpy's (through Bokeh's `contour_data`) as rasterised masks and areas, not vertex order (bokeh-web.md §1 verdict).

**Decision for maintainer ratification (reported in the hand-back):** D-29a below writes the isoband routine in dash's own JavaScript rather than vendoring `d3-contour` 4.0.2 (ISC). Reason: d3-contour yields threshold regions `z >= t` as MultiPolygons, not bands, so a band still needs the ring-composition step written here, and vendoring adds ~14 KB (d3-contour 4.0.2 UMD ≈ 9 KB plus its `d3-array` slice ≈ 5 KB) to every saved page under the CSP hash path with a licence header to carry. The hand-written routine is ~170 lines, has no dependency, and is pinned to contourpy.

**Test order and commit rule (rule 7, BRIEF).** One cycle, one commit `(WP-31 B4c)`. 29-01 writes `test/test_contour_js.py` red (the helpers absent from `_FILTER_JS`; `_dash_stale_kind` still "grid"), saves `<scratch>/29-01-failure.txt`, never commits. 29-02 adds the helpers and the branch. 29-03 registers both child sources, flips the stale kind, adds the capped-contour mark case to test_saved_stale_cue.py (no `_FROZEN` edit: S28 owns that line in batch 9 and leaves `["histogram", "kdensity"]`, DECISIONS A20), extends js_runner, appends the truth block and parity cases. 29-04 updates the help, closes B4c with `commit pending` in its Tracked line (A11) and commits.

### Section decisions (binding on the executor)

- **D-29a. Own isobands, no vendoring.** Bands are composed from threshold rings: for cut list `c[0..k-1]`, `R_i` = rings of the region `{z >= c[i]}` over the drawn domain (valid cells only), traced with the region on the left; band `i` (between `c[i-1]` and `c[i]`, with band 0 below `c[0]` and band `k` above `c[k-1]`) is the polygon whose rings are `R_{i-1}`'s rings (as traced) plus `R_i`'s rings reversed; band 0's outer rings are the domain boundary rings (the region `{z >= -Infinity}`). Because `R_i ⊆ R_{i-1}`, the nonzero winding of a point in the band is +1 and of a point in `R_i` is 0, so the polygon is right under the nonzero rule and under even-odd alike (a point in `R_i` is inside an odd number of `R_{i-1}` rings and an odd number of `R_i` rings: even total). Each band is ONE MultiPolygons polygon `[[ring, ring, ...]]` -- Bokeh's `xs[i]` is a list of polygons each a list of rings; one polygon with all rings is valid and is what contourpy's "ChunkCombinedOffset" form reduces to for drawing.
- **D-29b. Marching squares for the rings.** Per valid cell (four finite corners after `interp(none)` masking; every cell when interpolated), corners classified `hi = z >= c`; the 16-case table with saddle disambiguation by the cell's mean `(z00+z10+z11+z01)/4` (the rule contourpy's `mpl2014` applies); crossing on an edge between nodes a (value za) and b (zb): `t = (c - za)/(zb - za)`, point `a + t*(b - a)`, computed from the SAME ordered node pair whichever cell asks (lower index first) so two cells sharing an edge get bit-identical vertices. Domain-boundary edges (a cell edge whose neighbour cell is void or outside the grid) emit their `z >= c` part as a segment with the region on the left. Segments are linked into rings by a hash of their start vertex (`x.toString() + "," + y.toString()`); at a vertex with more than one unused outgoing segment the one from the same cell as the incoming segment's exit is taken, else the first unused. **Orientation (DECISIONS A19, REVIEW-2 R2-01).** The 16-case table below lists each interior crossing pair with the HIGH region on the RIGHT of the direction `a -> b` (case 1 `L -> B`, case 3 `L -> R`: the left normal points into the low side), while the domain-boundary edges run counter-clockwise (bottom +x, right +y, top -x, left -y: region on the LEFT). Interior segments are therefore pushed REVERSED (`put(a, b)` stores `[b[0], b[1], a[0], a[1], cell]`) and boundary edges unreversed (`putB`), so every segment has the region on its left and rings chain: measured under node, 0 of 3,318 random rings open, the exterior ring of the one-high-corner 3x3 case has area +0.125 and the domain ring +4; with the table's raw orientation 14,879 of 16,101 rings were open.
- **D-29c. Contour lines** are the same marching-squares segments at each `c[i]` without the boundary segments, linked into polylines (open where they meet the domain boundary), one `MultiLine` entry per polyline with `levels[j] = c[i]`.
- **D-29d. The agg config** (written by S26's `map_contour`, read here): `{type: "contour"|"contourline", xvar, yvar, zvar, cuts: [..], interp, cap: 1000, capped, horizontal, fill_color: [..], lo, hi, part: "fill"|"line", use, member_ids?}`. Both child sources are registered (S26 Notes): `render()` step 3b (dash_render.py:46219-46237) adds `(fill_src, cfg|part=fill)` and `(line_src, cfg|part=line)` for a renderer carrying `_dash_contour_sources`. The branch computes the surface once per `(gname, pi)` move and caches it on a module-level `Map` under ONE key, the fill entry's index as a string (`String(ac.part === 'line' ? ac.fill_index : ai)`); the line entry reuses it (R2-04: a key that mixes `ai` and `fill_index` is never equal for the two parts and runs the O(n³) solve twice).
- **D-29e. The cap on the page.** When the kept rows' distinct `(x, y)` count exceeds `ac.cap`, the branch does NOT compute (an O(n³) solve in the browser past 1000 points is seconds and the Python side would have drawn the fallback grid, which the page cannot match): it leaves the sources as built and sets the stale mark. `_dash_stale_kind(ptype, options)` cannot see the row count; so `_make_figure_body` tags the layer frozen only when `cr._dash_contour_capped` is true (TR-29.4), and `_dash_stale_kind` returns None for the two types (the tag, not the kind, decides). The JS marking block (:25377ff) then marks a capped layer always, and an uncapped layer is refit instead. A layer that becomes capped only after a move cannot happen (a move keeps a subset of the rows).
- **D-29f. `interp(none)` and masking.** Nodes with no observed z are NaN; a cell with any NaN corner is void (contourpy's rule, bokeh-web.md §1 gotcha); the domain is the union of valid cells; boundary segments close the rings along void cells.
- **D-29g. Ties.** `hi = z >= c`; a node exactly equal to a cut yields a crossing at the node; the parity test uses cuts off the node values, and the help names ties as a difference (a vertex at a node may link rings differently from contourpy's).

## Risk: [red] -- a geometry algorithm written from scratch in the page script, pinned to a C library's output

**Why.** Isobands with holes and masked cells are the hard part bokeh-web.md §1 names. Errors show as missing or inverted fills on a moved filter, visible only in a browser or a raster comparison.

**Risk factors.**
1. Ring linking fails at saddles or ties: an open ring draws a wedge.
2. Orientation inconsistency between interior segments and boundary segments flips a band under nonzero fill.
3. Cost: 1000×1000 grid × k cuts in the browser; marching squares is O(cells·k) ≈ 10⁶·k operations -- seconds for k=7.
4. The prelude after S10 (section-10 TR-10.4) takes the `else if (ac.xvar && ac.yvar)` path for a config with `xvar` and `yvar` and `continue`s only when `dash_fit_rows` returns null (a missing column); `ac.zvar` is not read by the prelude, so the branch reads x, y, z itself through `_pick`. Setting `ac.varname` would send the config down the one-variable histogram path instead (R2-03): the config carries NO `varname`.
5. `js_runner.run_filter_js_block` slices the kdensity branch by `"src.data = { x: xs, y: ys };"` (:518-556); a new branch after it must not move those markers.

**Mitigation.**
1. `TestRings::test_every_ring_closes` on 200 random surfaces: every traced ring's last vertex equals its first, each segment used once; saddles tested on the four-corner checkerboard cell.
2. `TestOrientation::test_region_on_the_left`: signed area of every exterior ring positive, holes negative; the band's nonzero winding at the band's sample points is +1, at `R_i` points 0.
3. The branch caps the grid it evaluates at `ac.cap` distinct points (so at most 1000×1000 nodes), and the exact grid is twoway's; above `cap` nothing runs (D-29e). Measured in 29-03 and recorded in the commit body; contour is exempt from the 2 s bound (C2).
4. TR-29.2 reads `ac.xvar`, `ac.yvar`, `ac.zvar` through `_pick` inside the branch (bypassing the prelude's `fx`/`fy`); the prelude's fit path has already run `dash_fit_rows` on x and y and left `fx`/`fy` unused by this branch. No `varname` key is written.
5. The new branch is inserted directly before the `// DASH_FIT_BRANCHES_END` marker S10 placed (after the last fit branch, before the `}` that closes the `for (let ai ...)` loop); the helpers directly before `// DASH_FIT_HELPERS_END`; the kdensity markers stay; `run_filter_js_block` gains `kind == "contour"` slicing on `"} else if (ac.type === 'contour'"` to `// DASH_FIT_BRANCHES_END`.

## Dependencies

- **Depends on: 26** (mappers, config, sources, the frozen tag), **10** (the prelude generalisation `ac.xvar/ac.yvar`, the insertion markers `// DASH_FIT_HELPERS_END` and `// DASH_FIT_BRANCHES_END`, and `dash_solve` -- S10 TR-10.5's Gaussian elimination with partial pivoting and the non-finite check, reused here, never redefined (A9, DECISIONS A19; a second `function dash_solve` in `_FILTER_JS` would win silently)).
- **Blocks:** none.
- **Parallel batch: 10**, merge order S29, S30, S31. **Can run with S30 and S31**: S29 owns `_FILTER_JS`, `js_runner.py`, `_dash_stale_kind`, `test_saved_stale_cue.py` for batch 10 (A2); S30 edits textboxes, S31 legend builders. S29 edits `_make_figure_body` only at the frozen-tag lines (:44049-44060) -- S30/S31 do not edit it (their Boundaries say so); S29 is batch 10's `_make_figure_body` editor.

## Evidence

All anchors at `6370ca4`; S10, S23, S26 land first (names authoritative).

- `_FILTER_JS` starts :24612; `dash_kernel` :25124; `// agg_sources is a Bokeh model list` :25150; the prelude :25152-25211 (`raw_col = _pick(_ac_data[ac.varname]); if (!raw_col) continue;` :25174-25175); histogram branch :25213; kdensity branch :25285-25370 ending `src.change.emit(); }`; the stale marking block `// ---- Marks on the layers a saved page does not recompute` :25372ff. `js_runner.run_filter_js_block` :518-556 (helpers slice `function dash_pctl` .. `// agg_sources is a Bokeh model list`). `_dash_stale_kind` :1913-1929; `_FROZEN` test_saved_stale_cue.py:58; `_frozen_layer_tag` :43040; the tagging :44049-44060; `render()` step 3b :46219-46237; `_build_filter_widgets` :45427 (`agg_sources`, `agg_configs_json` :45706-45717). Bokeh's source shapes (probed 10oct2026): fill `{'xs': [[[array]], ...], 'ys': ..., 'lower_levels': ndarray, 'upper_levels': ndarray, 'fill_color': list}`; line `{'xs': [array, ...], 'ys': ..., 'levels': ndarray}`.
- Stata's rule: the surface (S23); the cut list (S26); the polygon cut is compiled and unknown (bokeh-web.md §2) -- parity here is with contourpy (what the Python side draws), the Stata comparison being S26's U26-2.

## User stories

- **US-29.1** As a saved-page viewer, I want the contour to follow the filter like every other layer so that the page I was sent is not frozen at build.
- **US-29.2** As the same viewer, when the layer cannot be recomputed (above the cap) I want to see that it was not.

## Business requirements

- **BR-29.1** After a filter move the saved page's contour and contourline show the surface of the kept rows, with the build's cuts and colours, within the cap.
- **BR-29.2** The JS level sets agree with the Python side's (contourpy) on the same rows: raster agreement ≥ 99% and per-band area within 1%.
- **BR-29.3** Above the cap the layer is marked, never silently stale.
- **BR-29.4** No new script tag, no CSP change: the code lives in `_FILTER_JS` (a `CustomJS`).

## Technical requirements

- **TR-29.1 helpers** inserted in `_FILTER_JS` directly before `// DASH_FIT_HELPERS_END` (S10's marker; it sits after every fit helper and before `// agg_sources is a Bokeh model list`, :25150 at base), as named functions (BRIEF: never between `dash_pctl` and "// Stata's kernels"). `dash_solve` is S10's and is NOT redefined here:

```js
// ---- twoway's contour surface and its cutting (WP-31 B4c) ----
// Twins of _dash_contour_points/_dash_tps_fit/_dash_tps_eval/_dash_shepard/
// _dash_contour_grid/_dash_contour_surface; pinned by test_contour_js.py.
// The linear solver is S10's dash_solve (declared above).
function dash_contour_points(x, y, z) {
    const rows = [];
    for (let i = 0; i < x.length; i++) {
        const a = x[i], b = y[i], c = z[i];
        if (Number.isFinite(a) && Number.isFinite(b) && Number.isFinite(c)) rows.push([a, b, c]);
    }
    rows.sort((p, q) => (p[1] - q[1]) || (p[0] - q[0]) || (p[2] - q[2]));   // by y, x, z
    const px = [], py = [], pz = [];
    for (let i = 0; i < rows.length; i++) {
        if (i > 0 && rows[i][0] === rows[i-1][0] && rows[i][1] === rows[i-1][1]) continue;
        px.push(rows[i][0]); py.push(rows[i][1]); pz.push(rows[i][2]);
    }
    return {x: px, y: py, z: pz};
}
function dash_tps_fit(x, y, z) {      // kernel r = hypot(dx, dy); trend 1, x, y
    const n = x.length, A = [];
    for (let i = 0; i < n + 3; i++) A.push(new Array(n + 3).fill(0));
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) A[i][j] = Math.hypot(x[i] - x[j], y[i] - y[j]);
        A[i][n] = 1; A[i][n+1] = x[i]; A[i][n+2] = y[i];
        A[n][i] = 1; A[n+1][i] = x[i]; A[n+2][i] = y[i];
    }
    return dash_solve(A, z.concat([0, 0, 0]));
}
function dash_tps_eval(w, x, y, gx, gy) {      // one node
    const n = x.length; let s = w[n] + w[n+1] * gx + w[n+2] * gy;
    for (let i = 0; i < n; i++) s += w[i] * Math.hypot(gx - x[i], gy - y[i]);
    return s;
}
function dash_shepard(x, y, z, gx, gy) {       // one node; a hit returns that z
    let num = 0, den = 0;
    for (let i = 0; i < x.length; i++) {
        const d2 = (gx - x[i]) * (gx - x[i]) + (gy - y[i]) * (gy - y[i]);
        if (d2 === 0) return z[i];
        num += z[i] / d2; den += 1 / d2;
    }
    return num / den;
}
function dash_contour_grid(v) {                // sorted distinct values
    return Array.from(new Set(v)).sort((a, b) => a - b);
}
// {gx, gy, gz (row-major, gz[iy*nx+ix]), nx, ny} or null above the cap
function dash_contour_surface(x, y, z, interp, cap) {
    const p = dash_contour_points(x, y, z);
    const n = p.x.length;
    if (n < 3 || n > cap) return null;
    const gx = dash_contour_grid(p.x), gy = dash_contour_grid(p.y), nx = gx.length, ny = gy.length;
    const gz = new Float64Array(nx * ny).fill(NaN);
    if (interp !== "none") {
        let w = null;
        if (interp !== "shepard") { w = dash_tps_fit(p.x, p.y, p.z); if (w === null) return null; }
        for (let iy = 0; iy < ny; iy++) for (let ix = 0; ix < nx; ix++) {
            gz[iy * nx + ix] = (interp === "shepard") ? dash_shepard(p.x, p.y, p.z, gx[ix], gy[iy])
                                                      : dash_tps_eval(w, p.x, p.y, gx[ix], gy[iy]);
        }
    }
    const xi = new Map(gx.map((v, i) => [v, i])), yi = new Map(gy.map((v, i) => [v, i]));
    for (let i = 0; i < n; i++) gz[yi.get(p.y[i]) * nx + xi.get(p.x[i])] = p.z[i];   // observed nodes exact
    return {gx: gx, gy: gy, gz: gz, nx: nx, ny: ny};
}
```

The cutter (same place, after the surface):

```js
// Segments of the region z >= c over the valid cells, region on the left;
// with_boundary adds the domain boundary's z >= c parts (for rings).  A
// vertex on an edge is computed from the ordered node pair (lower index
// first) so neighbouring cells share it bit for bit.
function dash_contour_segments(S, c, with_boundary) {
    const {gx, gy, gz, nx, ny} = S;
    const valid = (ix, iy) => ix >= 0 && iy >= 0 && ix < nx - 1 && iy < ny - 1 &&
        Number.isFinite(gz[iy*nx+ix]) && Number.isFinite(gz[iy*nx+ix+1]) &&
        Number.isFinite(gz[(iy+1)*nx+ix]) && Number.isFinite(gz[(iy+1)*nx+ix+1]);
    const cross = (ax, ay, az, bx, by, bz) => {        // point on a->b where z == c
        const t = (c - az) / (bz - az);
        return [ax + t * (bx - ax), ay + t * (by - ay)];
    };
    const segs = [];                                     // [x0,y0,x1,y1,cell]
    for (let iy = 0; iy < ny - 1; iy++) for (let ix = 0; ix < nx - 1; ix++) {
        if (!valid(ix, iy)) continue;
        const cell = iy * (nx - 1) + ix;
        const x0 = gx[ix], x1 = gx[ix+1], y0 = gy[iy], y1 = gy[iy+1];
        const z00 = gz[iy*nx+ix], z10 = gz[iy*nx+ix+1], z11 = gz[(iy+1)*nx+ix+1], z01 = gz[(iy+1)*nx+ix];
        const h00 = z00 >= c, h10 = z10 >= c, h11 = z11 >= c, h01 = z01 >= c;
        // edge crossings, each from the lower-index node to the higher
        const B = (h00 !== h10) ? cross(x0, y0, z00, x1, y0, z10) : null;   // bottom
        const R = (h10 !== h11) ? cross(x1, y0, z10, x1, y1, z11) : null;   // right
        const T = (h01 !== h11) ? cross(x0, y1, z01, x1, y1, z11) : null;   // top
        const L = (h00 !== h01) ? cross(x0, y0, z00, x0, y1, z01) : null;   // left
        const code = (h00 ? 1 : 0) | (h10 ? 2 : 0) | (h11 ? 4 : 0) | (h01 ? 8 : 0);
        // The table below lists each crossing pair a -> b with the HIGH
        // side on the RIGHT; put() stores it reversed so the region is on
        // the left, as the boundary edges (putB, unreversed) already have
        // it, and rings chain (DECISIONS A19, R2-01).
        const putB = (a, b) => segs.push([a[0], a[1], b[0], b[1], cell]);
        const put = (a, b) => segs.push([b[0], b[1], a[0], a[1], cell]);
        switch (code) {
            case 0: case 15: break;
            case 1:  put(L, B); break;            case 14: put(B, L); break;
            case 2:  put(B, R); break;            case 13: put(R, B); break;
            case 4:  put(R, T); break;            case 11: put(T, R); break;
            case 8:  put(T, L); break;            case 7:  put(L, T); break;
            case 3:  put(L, R); break;            case 12: put(R, L); break;
            case 6:  put(B, T); break;            case 9:  put(T, B); break;
            case 5: {                              // saddle: 00 and 11 high
                const mid = (z00 + z10 + z11 + z01) / 4 >= c;
                if (mid) { put(L, T); put(R, B); } else { put(L, B); put(R, T); }
                break; }
            case 10: {                             // saddle: 10 and 01 high
                const mid = (z00 + z10 + z11 + z01) / 4 >= c;
                if (mid) { put(B, R); put(T, L); } else { put(B, L); put(T, R); }
                break; }
        }
        if (!with_boundary) continue;
        // Domain-boundary edges: the z >= c part, region on the left
        // (bottom runs +x, right +y, top -x, left -y).
        const edge = (nb_ok, pa, ha, pb, hb, X) => {
            if (nb_ok) return;
            if (ha && hb) putB(pa, pb);
            else if (ha) putB(pa, X);
            else if (hb) putB(X, pb);
        };
        edge(valid(ix, iy-1), [x0, y0], h00, [x1, y0], h10, B);
        edge(valid(ix+1, iy), [x1, y0], h10, [x1, y1], h11, R);
        edge(valid(ix, iy+1), [x1, y1], h11, [x0, y1], h01, T);
        edge(valid(ix-1, iy), [x0, y1], h01, [x0, y0], h00, L);
    }
    return segs;
}
// Link segments into paths; closed when the last vertex is the first.
function dash_contour_link(segs) {
    const key = (x, y) => x + "," + y;
    const out = new Map();                   // start key -> [seg indices]
    segs.forEach((s, i) => { const k = key(s[0], s[1]); if (!out.has(k)) out.set(k, []); out.get(k).push(i); });
    const used = new Uint8Array(segs.length), paths = [];
    for (let i0 = 0; i0 < segs.length; i0++) {
        if (used[i0]) continue;
        const xs = [segs[i0][0]], ys = [segs[i0][1]];
        let cur = i0;
        while (cur !== -1) {
            used[cur] = 1;
            const s = segs[cur]; xs.push(s[2]); ys.push(s[3]);
            const cands = (out.get(key(s[2], s[3])) || []).filter(j => !used[j]);
            if (!cands.length) break;
            let nxt = cands.find(j => segs[j][4] !== s[4]);     // leave the cell
            if (nxt === undefined) nxt = cands[0];
            cur = nxt;
            if (xs[0] === segs[cur][2] && ys[0] === segs[cur][3]) { used[cur] = 1; xs.push(xs[0]); ys.push(ys[0]); break; }
        }
        paths.push({xs: xs, ys: ys, closed: xs[0] === xs[xs.length-1] && ys[0] === ys[ys.length-1]});
    }
    return paths;
}
function dash_contour_rings(S, c) {       // closed rings of the region z >= c
    return dash_contour_link(dash_contour_segments(S, c, true)).filter(p => p.closed);
}
function dash_contour_lines(S, cuts) {    // MultiLine data at the cuts
    const xs = [], ys = [], levels = [];
    for (const c of cuts) for (const p of dash_contour_link(dash_contour_segments(S, c, false))) {
        xs.push(p.xs); ys.push(p.ys); levels.push(c);
    }
    return {xs: xs, ys: ys, levels: levels};
}
// MultiPolygons data for the k+1 bands: band i is R_{i-1}'s rings plus
// R_i's rings reversed (R_0 is the domain boundary, R_{k+1} empty).
function dash_contour_bands(S, cuts, lo, hi) {
    const R = [dash_contour_rings(S, -Infinity)].concat(cuts.map(c => dash_contour_rings(S, c)), [[]]);
    const lv = [lo].concat(cuts, [hi]);
    const xs = [], ys = [], lower = [], upper = [];
    for (let i = 0; i < lv.length - 1; i++) {
        const rings = [];
        for (const r of R[i]) rings.push([r.xs.slice(), r.ys.slice()]);
        for (const r of R[i+1]) rings.push([r.xs.slice().reverse(), r.ys.slice().reverse()]);
        if (!rings.length) continue;
        xs.push([rings.map(r => r[0])]); ys.push([rings.map(r => r[1])]);
        lower.push(lv[i]); upper.push(lv[i+1]);
    }
    return {xs: xs, ys: ys, lower_levels: lower, upper_levels: upper};
}
```

- **TR-29.2 the branch**, inserted directly before `// DASH_FIT_BRANCHES_END` (S10's marker, the last line before the loop's closing `}`; by batch 10 the kdensity branch is followed by the lfit..fpfitci chain, so "after the kdensity branch" is NOT the place):

```js
    } else if (ac.type === 'contour' || ac.type === 'contourline') {
        // Both child sources are registered (ac.part); the surface is
        // computed once per move for the fill entry and reused.
        const _cx = _pick(_ac_data[ac.xvar]), _cy = _pick(_ac_data[ac.yvar]), _cz = _pick(_ac_data[ac.zvar]);
        if (!_cx || !_cy || !_cz) continue;
        const _ck = String(ac.part === 'line' ? ac.fill_index : ai);   // one key for fill and line
        let S = dash_contour_cache.get(_ck);
        if (S === undefined) {
            S = dash_contour_surface(_cx, _cy, _cz, ac.interp, ac.cap);
            if (S !== null && ac.horizontal) {    // swap roles: x <-> y, gz transposed
                const gz = new Float64Array(S.nx * S.ny);
                for (let iy = 0; iy < S.ny; iy++) for (let ix = 0; ix < S.nx; ix++) gz[ix * S.ny + iy] = S.gz[iy * S.nx + ix];
                S = {gx: S.gy, gy: S.gx, gz: gz, nx: S.ny, ny: S.nx};
            }
            dash_contour_cache.set(_ck, S);
        }
        if (S === null) continue;                 // above the cap or degenerate: left as built, marked
        if (ac.type === 'contour' && ac.part === 'fill') {
            const b = dash_contour_bands(S, ac.cuts, ac.lo, ac.hi);
            const fc = ac.fill_color;
            // colour i belongs to band lv[i]..lv[i+1]; an absent band drops its colour
            const cols = b.lower_levels.map(l => fc[[ac.lo].concat(ac.cuts).indexOf(l)]);
            src.data = {xs: b.xs, ys: b.ys, lower_levels: b.lower_levels, upper_levels: b.upper_levels, fill_color: cols};
        } else if (ac.part === 'line' || ac.type === 'contourline') {
            const l = dash_contour_lines(S, ac.cuts);
            src.data = {xs: l.xs, ys: l.ys, levels: l.levels};
        } else {
            src.data = {xs: [], ys: [], lower_levels: [], upper_levels: []};   // contourline's empty fill
        }
        src.change.emit();
    }
```
  with `const dash_contour_cache = new Map();` declared just before `for (let ai = 0; ...)` (after `const agg_configs = JSON.parse(agg_configs_json);`, :25152). `fill_color` is copied from the config, not read back from the source (Python's `set_data` copies the old source's non-geometry columns; a band that vanished after a move has no row to copy from). The joint drop of non-finite x, y, z is `dash_contour_points`'s.
- **TR-29.3 config and registration (Python).** In S26's `map_contour`: add `"part": "fill"` to `_dash_agg_config` (no `varname` key: the prelude's fit path reads `xvar`/`yvar`, risk factor 4); in `render()` step 3b (:46219-46237), for a renderer with `_dash_contour_sources`, register `(fill_src, cfg)` and then `(line_src, dict(cfg, part="line", fill_index=<index of the fill entry>))` (both with `member_ids` by the same rule). `_build_filter_widgets` passes the lists as today. For contourline the fill source is registered too (its data stays empty).
- **TR-29.4 stale kind and tag.** `_dash_stale_kind` (:1913): `if t in _DASH_CONTOUR_TYPES: return None` (delete S26's `return "grid"`). In `_make_figure_body` (:44049-44060) add, after the computed-only tagging: `for _fr in _layer_renderers: if getattr(_fr, "_dash_contour_capped", False): _fr._dash_frozen = {"type": ptype.lower(), "kind": "grid", "vars": [pzvar, pyvar, pxvar], "wvar": None, "wrule": None}` (plus `member_ids` by `_frozen_layer_tag`'s rule) so a capped contour is marked and an uncapped one is refit. `_DASH_STALE_STATUS_HTML` text gains nothing (the suffix `(grid unfiltered)` already exists); the help's stale-cue sentence names contour above the cap (TR-29.6).
- **TR-29.5 js_runner.** `run_filter_js_block(kind, ac, vals, wts=None, cols=None)`: for `kind == "contour"` slice from `"} else if (ac.type === 'contour'"` to the branch's `src.change.emit();\n    }` and define `_ac_data`, `_pick` (identity) and `dash_contour_cache` in the harness with `cols = {xvar: [...], yvar: [...], zvar: [...]}`; the helper slice already carries the new functions (they sit before `// agg_sources is a Bokeh model list`).
- **TR-29.6 help.** dash.sthlp Server Mode / saved-page paragraph (the sentence listing what a saved page recomputes): add contour and contourline within 1,000 distinct points; the `{ul:contour and contourline.}` paragraph (S26's) replaces "the saved page does not recompute the layer after a filter move (the served app does)" with "a saved page recomputes the layer after a filter move up to 1,000 distinct points; above that it is marked (grid unfiltered), as is any layer the page cannot recompute; polygon vertices are cut by dash's own routine, so they differ from twoway's while the level sets agree; a node exactly on a cut may join rings differently from the served app's".
- **TR-29.7 maps.** function_test_map.py: none new in Python apart from the step-3b registration (a nested change in `render`, no new function). `test/test_contour_js.py` is the JS twin's file.

## Boundaries

- Do not edit S23's or S26's Python helpers apart from the `part` config key (TR-29.3) and the frozen tag (TR-29.4).
- Do not redefine `dash_solve` or any other S10 helper; do not edit `test_saved_stale_cue.py::_FROZEN` (S28's line; A20).
- Do not vendor any library; no new `<script>`; no CSP change (M11).
- Do not touch the histogram/kdensity branches or the markers js_runner slices by.
- Do not change `_dash_redraw_for` or the served app (it refits already).

## Stata truth

None new: the JS twin is pinned to its Python twin and to contourpy; Stata's polygons are S26's truth (U26-2). The truth block below runs through the page's own `_FILTER_JS` under node against the fixture's inputs.

Truth block `* ==== S29 B4c: contour refit on the saved page ====`:
- **U29-1** `dash contour mpg weight length, filter(foreign, type(dropdown)) name(u291)`; a `python:` helper renders the saved page, runs the Select move to Foreign through `js_runner.JsSession`, and compares the fill source's band areas with `dash contour mpg weight length if foreign == 1`'s Python build (areas within 1%, raster agreement ≥ 99%); the stale status line is absent and no legend suffix `(grid unfiltered)`.
- **U29-2** the same for contourline (line level sets: every JS polyline vertex lies within 1e-9 of a contourpy segment of the same level, and counts per level agree).
- **U29-3** `interp(shepard)` and `interp(none)` moves agree with Python the same way.
- **U29-4** a 1001-distinct-point dataset: the saved page leaves the sources as built after the move and shows the `(grid unfiltered)` mark and status line (M8).
- **U29-5** `horizontal`: the refit surface's x is weight's range.

## TDD test stubs

### Regression tests, `test/test_contour_js.py` (new; red at the batch-10 base; node required: `requires_node`)

- Test: `dash_contour_points`, `dash_tps_fit`/`dash_tps_eval`, `dash_shepard`, `dash_contour_grid` equal their Python twins at 1e-9 on the fixture's three inputs -- `TestTwins::test_each_helper[name-ds]` (red: `ReferenceError: dash_contour_points is not defined`).
- Test: `dash_tps_fit` through S10's `dash_solve` solves the fixture's smallest system to 1e-12 and returns null on three collinear duplicate-free points -- `TestTwins::test_tps_singular` (red).
- Test: every ring closes and every segment is used once on 200 seeded random 8×8 surfaces × 3 cuts -- `TestRings::test_every_ring_closes` (red).
- Test: exterior rings have positive signed area, holes negative; band winding +1 inside, 0 in `R_i` -- `TestOrientation::test_region_on_the_left` (red).
- Test: the saddle cases (5 and 10) follow the cell mean -- `TestRings::test_saddles` (red).
- Test: masked cells (`interp(none)`) are excluded from every band and line and the rings close along them -- `TestMasking::test_void_cells` (red).
- Test: `dash_contour_bands` vs `bokeh.plotting.contour.contour_data(gx, gy, gz, lv)` on the fixture's surfaces: per-band area within 1%, 300×300 raster agreement ≥ 99% (point-in-polygon by even-odd ray casting in the test, points within 1e-6·range of a cut skipped) -- `TestParityWithContourpy::test_bands[ds-interp]` (red).
- Test: `dash_contour_lines` vs `contour_data(...).line_data`: per level, every JS vertex within 1e-9 of a contourpy vertex and equal vertex counts -- `TestParityWithContourpy::test_lines[ds-interp]` (red).
- Test: the branch, run through `run_filter_js_block("contour", cfg, ...)`, writes `xs/ys/lower_levels/upper_levels/fill_color` of the right shapes and `fill_color` from the config -- `TestTheBranch::test_fill_shapes` (red); for `part="line"` writes `xs/ys/levels` and, after both parts ran in one harness, `dash_contour_cache.size === 1` -- `::test_line_shapes` (red); above `cap` leaves `src.data` null -- `::test_cap_leaves_it` (red).
- Test: a whole-page move (`JsSession`) refits contour to the qualified Python build (areas 1%, raster 99%) -- `TestWholePage::test_move_refits[contour|contourline]` (red).
- Test: `_dash_stale_kind("contour", {})` is None; a capped layer is tagged frozen, an uncapped one not -- `TestStale::test_kind_and_tag` (red).
- Test: both child sources are registered in `agg_source_registry` with `part` fill/line -- `TestRegistration::test_two_entries` (red).
- Test: the help names the refit and the cap mark -- `TestHelp::test_sentences` (red).

### cscript cases: U29-1..U29-5.

### Pinned tests to flip (R9)

- test_saved_stale_cue.py: no `_FROZEN` flip (S28 left it `["histogram", "kdensity"]` in batch 9 and S26 did not add the contour names, DECISIONS A20); add a case in the same file: a capped contour is marked (`TestTheCueAppearsOnAMove::test_a_capped_contour_is_marked`), and the S26 case `test_contour_layers.py::TestMoves::test_saved_is_marked` is flipped to assert the uncapped layer is NOT marked, `Flipped: ... -- the saved page refits contour within the cap (WP-31 B4c)`.
- test_mode_parity.py MOVE_CORPUS: the S26 entry `_move_case("contour, dropdown to Foreign", ...)` keeps the Python oracle; add `_move_case("contourline, dropdown to Foreign", ...)`; no `ALLOWED` edit (R8).
- test_help_claims_*.py sentences about "a saved page does not recompute" that enumerate types: contour removed from the list (grep `grid unfiltered` in test/ and dash.sthlp).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| twins | pytest TestTwins (node) | contour_truth.json inputs | saved JS vs Python |
| rings, orientation, saddles, masks | pytest (node) | -- | n/a |
| bands/lines vs contourpy | pytest TestParityWithContourpy | contour_truth.json | n/a |
| page move | pytest TestWholePage; cscript U29-1..3,5 | -- | saved vs Python oracle |
| cap mark | pytest TestStale; cscript U29-4 | -- | saved |

Acceptance: **AC-29.1** twins at 1e-9; **AC-29.2** bands/lines agree with contourpy (1% area, 99% raster, line vertices 1e-9); **AC-29.3** the page refits on a move within the cap; **AC-29.4** above the cap marked; **AC-29.5** no CSP change (test_csp.py green); **AC-29.6** one green commit.

## Tasks

**Commit boundary.** 29-01..29-04 = one commit `Refit contour and contourline on the saved page within the cap (WP-31 B4c)`.

<task type="auto" id="29-01">
  <name>Write the failing JS twin tests</name>
  <files>test/test_contour_js.py, test/js_runner.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create test/test_contour_js.py with every stub (node harness through js_runner: a `_run_helpers(code)` that writes the `_FILTER_JS` helper slice plus `code` to a .mjs and runs node, as `run_filter_js_block` does at :518-556; the even-odd point-in-polygon and shoelace helpers in the test; `contour_data` from `bokeh.plotting.contour`). Add TR-29.5's `kind == "contour"` slicing and `cols` argument to js_runner.run_filter_js_block (the histogram/kdensity paths unchanged byte for byte). Append the S29 block (U29-1..U29-5) above the marker in test_wp31_truth.cscript. Run `python3 -m pytest test/test_contour_js.py -q -n0 -p no:cacheprovider 2>&1 | tee <scratch>/29-01-failure.txt` against the batch-10 base and the block through the driver (`WP31_ONLY=S29`), appending FAIL lines. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "ReferenceError: dash_contour\|FAILED" <scratch>/29-01-failure.txt` is at least 12; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k FilterJavaScript` reports 0 failed (js_runner's old paths intact); `grep -c "U29-[1-5] FAIL" <scratch>/s29/run_test_wp31_truth.log` is at least 1.]]></verify>
  <done>The JS contour tests and truth block failed against the batch-10 base with the text saved, and js_runner could slice the new branch.</done>
</task>

<task type="auto" id="29-02">
  <name>Add the JS helpers and the contour branch</name>
  <files>dash_render.py</files>
  <action><![CDATA[Insert TR-29.1's eleven functions verbatim directly before `// DASH_FIT_HELPERS_END` (S10's marker; do not add a `dash_solve`: S10's is in scope); add `const dash_contour_cache = new Map();` after `const agg_configs = JSON.parse(agg_configs_json);` (:25152 at base); insert TR-29.2's branch directly before `// DASH_FIT_BRANCHES_END`. Run `python3 -m pytest test/test_contour_js.py -q -n0 -p no:cacheprovider -k "Twins or Rings or Orientation or Masking or Parity or Branch"`, `test/test_statistical_helpers.py -k FilterJavaScript`, test_saved_filter_layers.py, test_csp.py.]]></action>
  <verify><![CDATA[Those runs report 0 failed; `grep -c "^function dash_contour_\|^function dash_tps_\|^function dash_shepard" dash_render.py` prints 11 and `grep -c "^function dash_solve" dash_render.py` prints 1 (S10's); `grep -c "ac.type === 'contour'" dash_render.py` prints 1; `python3 -c "import dash_render as dr; js=dr._FILTER_JS; assert js.index('function dash_contour_points') < js.index('// DASH_FIT_HELPERS_END') < js.index('// agg_sources is a Bokeh model list') and js.index(\"ac.type === 'contour'\") < js.index('// DASH_FIT_BRANCHES_END')"` exits 0.]]></verify>
  <done>The saved page's filter script carried twoway's surface, marching-squares rings, lines and bands, agreeing with contourpy's level sets, and a contour branch that rewrote the two child sources.</done>
</task>

<task type="auto" id="29-03">
  <name>Register both sources, flip the stale cue, add parity</name>
  <files>dash_render.py, test/test_saved_stale_cue.py, test/test_mode_parity.py</files>
  <action><![CDATA[Make TR-29.3 (config key `part`; step-3b registration of both child sources with `fill_index`) and TR-29.4 (`_dash_stale_kind` None for the family; the capped frozen tag in `_make_figure_body`; add `assert _DASH_COMPUTED_ONLY_TYPES - _DASH_JS_REFIT_TYPES - _DASH_CONTOUR_TYPES == {"histogram", "kdensity"}` as a module-level check in test_saved_stale_cue.py, DECISIONS A20). Do NOT edit `_FROZEN` (S28's line); add the capped-contour mark case to test_saved_stale_cue.py and flip test_contour_layers.py::TestMoves::test_saved_is_marked (uncapped: not marked; capped: marked); append the contourline MOVE_CORPUS entry. Run test_contour_js.py (all), test_saved_stale_cue.py, test_contour_layers.py, `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "contour"`, test_served_filter_move.py, and the S29 block through the driver. Time one whole-page move on auto (74 rows) and on a 1000-distinct-point synthetic set under node (the exact grid is up to 1000 x 1000 nodes x 1000 points, about 1e9 `hypot` calls on the page's main thread, R2-29) and record both in <scratch>/29-timing.txt for the commit body and the hand-back (no bound applies, C2). If the 1000-point move exceeds 10 s, report the number for ratification: the cap is Python's `_DASH_CONTOUR_EXACT_MAX` (S23) and the JS reads it as `ac.cap`, so lowering it is ONE edit in dash_render.py, not two.]]></action>
  <verify><![CDATA[Every run reports 0 failed; `grep -c "U29-[1-5] PASS" <scratch>/s29/run_test_wp31_truth.log` prints 5 and the log ends `ALL CHECKS PASSED`; `grep -c '"contour"' test/test_saved_stale_cue.py` prints the count of the capped-contour case only (`_FROZEN` is `["histogram", "kdensity"]`, unchanged); `python3 -c "import dash_render as dr; assert dr._dash_stale_kind('contour', {}) is None and dr._dash_stale_kind('kdensity', {}) == 'grid'"` exits 0.]]></verify>
  <done>Both contour sources were registered for the page script, the stale cue applied only above the cap, and the saved page's refit matched the Python oracle in the parity corpus and under Stata.</done>
</task>

<task type="auto" id="29-04">
  <name>Document, close B4c, commit</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Make TR-29.6's help edits. Close BUGS.md "B4c" (`Fixed <ddmonyyyy> (WP-31, B4c). _FILTER_JS gained dash_contour_points, dash_tps_fit, dash_tps_eval, dash_shepard, dash_contour_grid, dash_contour_surface, dash_contour_segments, dash_contour_link, dash_contour_rings, dash_contour_lines and dash_contour_bands and a contour/contourline branch that rewrites the fill and line sources after a filter move within _DASH_CONTOUR_EXACT_MAX distinct points; _dash_stale_kind returns None for the two types and a capped layer is tagged frozen in _make_figure_body. Pinned by test/test_contour_js.py::TestParityWithContourpy::test_bands, test/test_contour_js.py::TestWholePage::test_move_refits, test/test_wp31_truth.cscript U29-1. Above the cap the saved page marks the layer and the Python side draws the 100 x 100 grid from the seeded 1,000-point subsample (DECISIONS D4: confirmed, not a residual). Closes GAPS3 B4c (WP-31, B4c).`). Rewrite the B4c Tracked line to `- **B4c Tracked:** Closed in WP-31, BUGS.md "<B4c title>", commit pending.` (A11: the merger's step k.3b fills the sha; S23 and S26 own the B4a and B4b lines). No residual entry is opened: the above-the-cap behaviour is D4's decided design and index Residuals already names "contour above the cap" for S61. Replace `<!-- WP-31 B4c -->` under `### Fixed in WP-31` with `- A saved page recomputes contour and contourline after a filter move, as the served app does, up to 1,000 distinct points; above that the layer is marked (grid unfiltered). (WP-31, B4c)`. Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py $(grep -l "grid unfiltered" test/test_help_claims_*.py) -q -p no:cacheprovider`. Stage dash_render.py dash.sthlp test/test_contour_js.py test/js_runner.py test/test_saved_stale_cue.py test/test_contour_layers.py test/test_mode_parity.py test/test_wp31_truth.cscript BUGS.md GAPS3.md CHANGELOG.md; commit with BRIEF's body forms, the timing lines from <scratch>/29-timing.txt after the measured defect.]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -c '<!-- WP-31 B4c -->' CHANGELOG.md` prints 0; `git log -1 --format=%s` ends `(WP-31 B4c)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c "B4c Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1 and `grep -c "B4c Tracked:\*\* Open" GAPS3.md` prints 0.]]></verify>
  <done>The help described the saved page's contour refit and its cap, B4c was closed, and one green commit on wp31-s29 was ready for the merger.</done>
</task>

## Section completion criteria

- Eleven JS helpers (S10's `dash_solve` reused) and one branch in `_FILTER_JS`, inserted before the two S10 markers; twins at 1e-9; bands/lines agree with contourpy (1% area, 99% raster; line vertices 1e-9).
- A saved page refits contour/contourline on a move within the cap; above it the layer is marked; `_dash_stale_kind` None for the family; `_FROZEN` untouched (A20).
- No new script, CSP tests green; js_runner slices the branch; U29-1..U29-5 PASS; one green commit; B4c closed, its Tracked line `Closed in WP-31 ... commit pending`.

## Notes

- **Where the helpers go.** Directly before `// DASH_FIT_HELPERS_END` (between `dash_kernel` and `// agg_sources is a Bokeh model list`), the branch directly before `// DASH_FIT_BRANCHES_END`; never between `dash_pctl` and `// Stata's kernels` (the brush script copies that slice, :45374-45389). `dash_solve` is S10's: reuse, never redefine.
- **Row-major `gz`.** `gz[iy*nx+ix]` mirrors numpy's `(ny, nx)`; `dash_contour_surface` stores a `Float64Array`.
- **Cost.** `dash_tps_fit` is O(n³) with n ≤ 1000: ~0.3 s in V8 for n=1000 (dense 1003² elimination); the evaluation is O(nx·ny·n) -- up to 10⁹ `hypot` calls at n = nx = ny = 1000 on the browser's main thread: several seconds with the page frozen (R2-29; contour is exempt from M10, C2). Record the 1,000-point node timing in the hand-back (29-03); if it exceeds 10 s, lower `_DASH_CONTOUR_EXACT_MAX` -- the constant is Python's (S23) and the JS reads it from the config as `ac.cap`, so ONE edit in dash_render.py changes both twins -- and report the number for ratification; do not add a second constant. The one cache key (D-29d) keeps the solve to once per move.
- **Bokeh's fill rule.** Verify once in 29-02 with `grep -o "MultiPolygonsView[^;]*fill[^;]*" <site-packages>/bokeh/server/static/js/bokeh.js | head`; D-29a's orientation is correct under nonzero and even-odd alike, so the result does not change the code.
- **Ties (D-29g)** are a documented difference; the fixture's cuts avoid node values.
- **python_exec hazard**: check `~/.stata19/console/stata19.rc` after the driver runs.
- **Shared files (R1-R13).** R1: one S29 block. R2: no Python module function added (JS only; the `part` config key lives in S26's mapper). R3: the saved-page sentences in Server Mode and S26's contour paragraph (S29 owns them in batch 10). R4: one marker. R5: B4c entry closed, B4c Tracked rewritten (`commit pending`, A11). R8: one MOVE_CORPUS entry. R9: test_contour_layers.py::TestMoves::test_saved_is_marked flipped; `_FROZEN` untouched (A20). R12: S29 is batch 10's `_FILTER_JS` and `_make_figure_body` editor (frozen-tag lines only); S30/S31 edit neither.
- **For S61 (closeout).** "Contour above the cap" is in index Residuals and decided by D4 (subsample, 100x100 grid, cue, note); no BUGS.md residual entry is opened here. The hand-back note carries the measured node timing.
