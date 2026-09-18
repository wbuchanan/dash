# Section 10: Figure geometry and layout sizing

## Overview
There is currently **no way — by option, by scheme, or by data — for a user to influence plot
proportions.** Measured: neither generated dashboard contains a figure `width`, `height` or
`frame_width`; every figure is emitted with `sizing_mode="stretch_width"` (`:5643-5650`) and
Bokeh's default height, regardless of graph count, grid position or Bootstrap span.

Meanwhile `twoway` has `xsize()` and `ysize()` — both `r(198)` before S05 — and every Stata
scheme carries `graphsize 5`, `graphsize x 5.5`, `graphsize y 4`, which S03 now translates
and S03-04 now parses.

The layout thresholds are fixed too: `_compute_grid`'s `ceil(sqrt(n))`, and the Bootstrap
auto-layout's "4 KPIs per row", `span = 12 // per_row`, and 1→col-12 / 2-4→col-6 / ≥5→col-4.

## User story
> As a Stata user, `xsize()` and `ysize()` work, and when I pass neither my plots use my
> scheme's graph size — so a `dash` dashboard has the proportions of my other graphs.

## Business requirements
- BR-10.1 `xsize()`/`ysize()` control figure dimensions.
- BR-10.2 With neither given, dimensions come from the active scheme's `graphsize`.
- BR-10.3 Responsiveness — the abstract's headline feature — is preserved: a sized figure must
  still adapt to the viewport rather than becoming a fixed block.
- BR-10.4 Layout thresholds derive from content where a fixed number is arbitrary.

## Technical requirements
- TR-10.1 `xsize()`/`ysize()` (accepted in S05) are serialized and honoured.
- TR-10.2 Absent both, use `graphsize x` / `graphsize y` from the parsed scheme.
- TR-10.3 Reconcile sizing with `sizing_mode`. Stata's sizes are inches; Bokeh wants pixels
  and a sizing mode. Preserve the **aspect ratio** and let width flex, rather than pinning
  both dimensions — this satisfies BR-10.1 and BR-10.3 together. `aspectratio()` already maps
  to Bokeh's `aspect_ratio` (`:5620-5626`) and is the natural mechanism.
- TR-10.4 Bootstrap cell height must follow the span so a col-4 cell is not the same height
  as a col-12 one.
- TR-10.5 The `md`-only breakpoint (`:6567-6571`) gains at least an `lg` tier so a wide
  display is used.

## Risk: [yellow] — visual rather than logical, which makes it the section most likely to be reported "done" on the basis of a structural assertion. It is not done until someone has looked at it at three viewport widths.

## Dependencies
- Depends on: S09
- Blocks: S11
- Parallel batch: 3

## TDD test stubs
- Test: `xsize(6) ysize(4)` yields an aspect ratio of 1.5.
- Test: with neither, the ratio comes from the active scheme's `graphsize`.
- Test: two different schemes with different `graphsize` produce different ratios.
- Test: a sized figure still carries a responsive sizing mode.
- Test: `aspectratio()` and `xsize()`/`ysize()` together resolve by a documented precedence.
- Test: a col-4 Bootstrap cell and a col-12 cell get different heights.
- Test: the Bootstrap grid emits an `lg` class in addition to `md`.
- Test: a 1-graph, a 4-graph and a 9-graph dashboard each produce a sensible grid.
- Test: dashboards render without horizontal scroll at 375px, 768px and 1440px.

## Tasks

<task type="auto" id="10-01">
  <name>Write the geometry tests, including a real viewport check</name>
  <files>test/test_geometry.py, test/test_geometry_visual.md</files>
  <action>
    Structural tests first: assert on the emitted figure properties for each case above.

    Then the part that actually matters. Add a documented manual visual check — a short
    procedure, with a dashboard to build and three viewport widths to view it at — and record
    it as a file in `test/`. Every section that changes layout runs it.

    If the built-in browser can drive this, automate the three widths and capture what is
    rendered; if not, the written procedure is the deliverable and it must be followed rather
    than skipped.

    Run the structural tests. All sizing tests must fail — there is no width, height or
    ratio in the output today.
  </action>
  <verify>Structural sizing tests fail because no dimension is emitted; the visual procedure exists.</verify>
  <done>Both a structural and a visual check exist before any code changes.</done>
</task>

<task type="auto" id="10-02">
  <name>Honour xsize()/ysize() and the scheme's graphsize</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    Serialize `xsize()`/`ysize()` from S05.

    In `_make_figure` (`:5643-5650`), resolve dimensions by precedence: explicit
    `xsize()`/`ysize()`, then `aspectratio()`, then the scheme's `graphsize x`/`graphsize y`
    (available from S03-04), then the current behaviour. Document the precedence in the help.

    Convert Stata inches to a Bokeh aspect ratio rather than to fixed pixels, and keep a
    responsive sizing mode. Pinning both dimensions would satisfy BR-10.1 and break BR-10.3,
    and BR-10.3 is the abstract's headline claim.

    Apply the same resolution to faceted panels, which currently inherit whatever
    `_make_figure` produced.
  </action>
  <verify>Ratios match for explicit sizes, for `aspectratio()`, and for two different schemes; figures remain responsive.</verify>
  <done>Figure proportions come from the user's option or the user's scheme.</done>
</task>

<task type="auto" id="10-03">
  <name>Derive layout thresholds from content</name>
  <files>dash_render.py</files>
  <action>
    `_compute_grid` (`:6767-6800`) uses `ceil(sqrt(n))`, which is a reasonable default and
    should stay — but it must yield to an explicit `layout(R C)`, which it already does, and
    to the figure aspect ratios now available: a dashboard of wide figures wants fewer
    columns than one of square figures. Make the default ratio-aware.

    In `_auto_bs_layout` (`:6319-6364`), the "4 KPIs per row" and the 1/2-4/≥5 graph
    thresholds are arbitrary. Derive the graph thresholds from the resolved aspect ratios,
    and keep the KPI rule but make the maximum a named constant with a comment, since 4 is a
    defensible design choice rather than a derivable quantity.

    Set Bootstrap cell heights from the span so a col-4 cell is not the height of a col-12
    cell (TR-10.4), and add an `lg` tier to the `db-col-12 db-col-sm-12 db-col-md-N` chain
    at `:6567-6571`.

    Note for S12, do not fix here: `layout(name:row,col ...)` is validated in Stata and
    documented but never implemented, because `_compute_grid` calls `int(parts[0])` on
    `"s1:1,1"` and falls through to auto.
  </action>
  <verify>Grids adapt to aspect ratio; cell heights follow spans; an `lg` class is emitted.</verify>
  <done>Layout decisions derive from content rather than from fixed thresholds.</done>
</task>

<task type="auto" id="10-04">
  <name>Visual verification at three widths, then commit</name>
  <files>examples/, .ultraplan/CHANGELOG.md</files>
  <action>
    Build a representative dashboard — KPIs, several graphs of different shapes, a faceted
    graph, under `layout(bs)` — and run the visual procedure from 10-01 at 375px, 768px and
    1440px.

    Confirm: no horizontal scroll at any width; no cell overlapping another; faceted panels
    sized consistently with unfaceted ones; and the whole dashboard usable on a phone, which
    is the specific claim the conference abstract makes.

    Regenerate every dashboard in `examples/`. Every one will change, because every figure
    now has a ratio it did not have. Record that in the CHANGELOG as a single expected class
    of change rather than file by file.

    Run all suites against the S01 baseline. Commit.
  </action>
  <verify>Clean rendering at all three widths, verified by looking; suites green against baseline.</verify>
  <done>Geometry is user- and scheme-driven, and the responsive claim has been checked rather than assumed.</done>
</task>
