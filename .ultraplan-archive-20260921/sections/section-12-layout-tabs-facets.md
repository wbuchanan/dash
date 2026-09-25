# Section 12: Layout, tabs and faceting correctness

## Overview
The package's two headline features destroy each other. Measured, on two dashboards identical
except for `layout()`:

| Marker in the generated HTML | `layout(bs)` | `layout(auto)` |
|---|---|---|
| the by-graph's title | **absent** | present |
| the ordinary graph's title | present | present |
| facet labels `Domestic` / `Foreign` | **absent** | present |

The Bootstrap grid checks `name in self.figures` (`:6546`), but a faceted graph is stored
under generated keys `name__by__0`, `name__by__1`, ... so the lookup misses and the graph is
**dropped from the dashboard entirely**, with no error and no warning.

The conference abstract sells Bootstrap responsiveness; `by()` is core `twoway`. Using both
loses one.

Around that sit four more layout defects of the same kind.

## User story
> As a Stata user, `by()` and `layout(bs)` work together, `tabs()` works whatever my layout,
> and a tab keeps the name I gave it.

## Business requirements
- BR-12.1 No graph may vanish from a dashboard without an error.
- BR-12.2 Every documented `layout()` form works.
- BR-12.3 `tabs()` is not silently conditional on another option.
- BR-12.4 User-supplied text is not silently rewritten.

## The five defects

| # | Defect | Citation | Rating |
|---|---|---|---|
| 1 | `layout(bs)` + `by()` drops the faceted graph entirely | `:6546` vs the `name__by__N` keys | **BLOCKER [measured]** |
| 2 | `layout(name:row,col ...)` validated in Stata (`dash.ado:1224-1227`) and documented (`dash.sthlp:271-275`) but never implemented — `_compute_grid` calls `int(parts[0])` on `"s1:1,1"`, raises `ValueError`, falls through to auto | `:6788-6800` | SILENT |
| 3 | `tabs()` is parsed, passed to Python, and **discarded unless `layout(bs...)`**, with no warning | `:7372` | SILENT |
| 4 | Tab labels are forcibly `.title()`-cased — `tabs(MPG stuff: u1)` renders "Mpg Stuff", with no way to suppress it | `:6692` | SILENT |
| 5 | `_NONSELECTION_ALPHA` (`:109`) is applied only in `_build_figures`, which `render()` never calls — **linked-brush dimming never ships** | `:109`, `:7037` | SILENT |

Also in scope: `_setup_sources` (`:6824`) and `_build_figures` (`:6955`) are dead duplicates
of `render()`'s phases that have already diverged — `_build_figures:6970` is the only caller
of `_setup_sources`, and nothing calls `_build_figures` outside tests. They are the reason
`link(_all)` *looks* implemented (S13) and the reason `_NONSELECTION_ALPHA` never ships.

## Risk: [yellow] — defect 1 is a small keying fix; removing the dead duplicates is the part that needs care, since tests reference them.

## Dependencies
- Depends on: S11
- Blocks: S13
- Parallel batch: 4

## TDD test stubs
- Test: a dashboard with a `by()` graph and a plain graph under `layout(bs)` contains both,
  and all facet panels — asserted by searching the HTML for the graph title and every facet
  label, which is how the defect was found.
- Test: the same under `layout(auto)` (regression).
- Test: a faceted graph under `layout(bs: spec)` honours its span.
- Test: `layout(s1:0,0 s2:0,1)` places graphs at those cells.
- Test: `tabs()` with `layout(auto)` either builds tabs or warns — never silently discards.
- Test: `tabs(MPG stuff: u1)` renders "MPG stuff".
- Test: linked brushing dims non-selected points at `_NONSELECTION_ALPHA`.
- Test: no production code path calls `_setup_sources` or `_build_figures`.

## Tasks

<task type="auto" id="12-01">
  <name>Write the faceted-layout regression test first</name>
  <files>test/test_layout_facets.py, test/test_layout_facets.cscript</files>
  <action>
    Encode the measurement that found the defect: build the two dashboards that differ only in
    `layout()`, and assert the HTML contains the by-graph's title and every facet label in
    **both**.

    Assert on the rendered HTML rather than on `self.figures`, because the defect is precisely
    that the figures exist and the layout omits them. A test against the internal dict would
    pass today.

    Add the `layout(bs: spec)` variant, where a faceted graph is given an explicit span.

    Run and confirm the `layout(bs)` case fails by absence.
  </action>
  <verify>The `layout(bs)` assertion fails on a missing title and missing facet labels; `layout(auto)` passes.</verify>
  <done>The blocker is pinned by a test that asserts what the user sees.</done>
</task>

<task type="auto" id="12-02">
  <name>Fix the Bootstrap grid's faceted-graph lookup</name>
  <files>dash_render.py</files>
  <action>
    At `:6546` the grid checks `name in self.figures`, which misses the `name__by__N` keys a
    faceted graph produces.

    Resolve a registered name to its facet panels the way `_build_tabs_widget` already does —
    it checks `self._facet_map` first (`:6724-6738`) and handles this correctly. Reuse that
    resolution rather than writing a second one; two implementations is how this diverged.

    Decide and document how a faceted graph occupies a Bootstrap cell: all panels inside one
    cell as a sub-grid, or one cell per panel. The sub-grid preserves the user's span
    arithmetic and is the better default. Say which in the help.

    Then add the general guard this defect should never have survived: at the end of layout
    assembly, assert every registered graph name appears somewhere in the output, and raise a
    clear error naming any that does not. **This is the fix that matters** — defect 1 is one
    instance of a class, and the guard catches the rest.
  </action>
  <verify>All 12-01 tests pass; the guard fires when a graph is deliberately removed from the layout.</verify>
  <done>No graph can silently vanish from any layout.</done>
</task>

<task type="auto" id="12-03">
  <name>Implement layout(name:row,col) and unconditional tabs()</name>
  <files>dash_render.py</files>
  <action>
    Implement the placement form. `_compute_grid` (`:6788-6800`) splits on whitespace and
    calls `int(parts[0])`, which raises on `"s1:1,1"` and falls through to auto. Parse
    `name:row,col` properly, place each named graph at its cell, and decide what happens to a
    graph the spec omits — the Bootstrap path appends omitted names as full-width rows
    (`:6432-6434`), so match that.

    Tighten the Stata-side validation at `dash.ado:1224-1227` while here: the regexes require
    exactly one space, are case-inconsistent, allow `0` in the placement form, and are not
    end-anchored.

    Make `tabs()` work with any layout (`:7372`). Tabs are purely a layout mechanism over
    already-built figures (`:6703-6761`); nothing about that requires Bootstrap. If there is a
    genuine reason the plain gridplot path cannot host a `Tabs` widget, then warn loudly
    instead — but establish which it is rather than preserving the silent discard.

    Stop force-title-casing tab labels (`:6692`). Use the user's text.

    Also here, same family: `filterposition(left)` only takes effect in Bootstrap mode
    (`:7387`, `:6603`); in the plain path filters always go in a row above the grid
    (`:7456-7458`) regardless. Honour it in both, or report it in the plain path.
  </action>
  <verify>Placement layouts position graphs correctly; `tabs()` works under `layout(auto)`; labels keep their casing; `filterposition(left)` behaves or reports.</verify>
  <done>Every documented layout and tab form works, and nothing is silently conditional.</done>
</task>

<task type="auto" id="12-04">
  <name>Remove the dead duplicate render path</name>
  <files>dash_render.py, test/</files>
  <action>
    `_setup_sources` (`:6824`) and `_build_figures` (`:6955`) are dead: `_build_figures:6970`
    is the only caller of `_setup_sources`, and nothing calls `_build_figures` outside tests.
    They duplicate `render()`'s phases and have already diverged — they expand `link(_all)`
    where `render()` does not, and they apply `_NONSELECTION_ALPHA` where `render()` does not.

    They are actively harmful. They make `link(_all)` look implemented to anyone reading the
    file, and the tests that exercise them (`test/test_dual_axis.py:103`,
    `test/test_graph_options.py:84`) assert behaviour no user can reach.

    Before deleting, harvest: `render()` is missing two behaviours these contain —
    `link(_all)` expansion (S13 implements it there) and `_NONSELECTION_ALPHA` (task 12-05).
    Move the behaviour, then delete the functions.

    Repoint the tests that call them at `render()`. A test that cannot be repointed was
    testing something unreachable and should be deleted with a note saying so.

    Add a test asserting no production path calls either name, so they cannot come back.
  </action>
  <verify>Both functions are gone; the repointed tests pass against `render()`; the no-caller test passes.</verify>
  <done>There is one render path, so the two cannot diverge again.</done>
</task>

<task type="auto" id="12-05">
  <name>Ship linked-brush dimming, then commit</name>
  <files>dash_render.py, .ultraplan/CHANGELOG.md</files>
  <action>
    `_NONSELECTION_ALPHA = 0.15` (`:109`) is applied only in the now-deleted `_build_figures`,
    so brushing a linked graph has never dimmed the non-selected points in shipped output.
    Apply it in `render()`.

    Verify by hand: build a linked dashboard, box-select in one graph, and confirm the other
    graph's non-selected points dim. Structural assertion is not enough for a visual effect
    that has never once worked.

    Consider whether 0.15 should be user-controllable. `twoway` has no analogue, so a named
    constant with a comment is defensible — but it must be in one place, and S15 will find the
    server's copy of it.

    Run all suites against the S01 baseline. Record in the CHANGELOG that brushing now dims,
    since anyone who has used linked dashboards will see a change. Commit as single-issue
    commits.
  </action>
  <verify>Brushing visibly dims non-selected points, confirmed by looking; suites green.</verify>
  <done>Linked brushing looks like linked brushing.</done>
</task>
