# Section 13: Linking, filters and KPI correctness

## Overview
The interactive layer — the reason `dash` exists rather than `twoway` — has a set of defects
that each produce a plausible-looking dashboard showing the wrong thing.

`link(_all)`, documented at `dash.sthlp:295`, **silently produces an unlinked dashboard**.
Two audits disagreed about this, so it was resolved directly: `_all` is expanded in three
places — `_setup_sources:6855`, `_build_figures:6983` and
`ServerAppBuilder._generate_app_source:7842` — but the first two are dead code (S12 deleted
them) and the third is the server path. The production standalone path is `render():7488`,
which derives `link_names` at `:7510-7512` with **no `_all` expansion**. The command returns
`rc=0`, which is why it looks implemented.

`dash kpi mean(mpg) if foreign==1` displays the **unconditional** mean. Measured: the card
shows **21.2973** where Stata's own `summarize` under the same qualifier reports **24.7727**.

And `filter()` combined with `by()` masks the wrong rows in faceted panels — present in the
flagship `examples/comprehensive_demo.do`, which uses ten `by()` graphs and three filters.

## User story
> As a Stata user, `link(_all)` links everything, a KPI with an `if` shows the conditional
> statistic, and a filter filters the rows it claims to.

## Business requirements
- BR-13.1 Every documented linking form works.
- BR-13.2 A filter selects the rows it says it does, in every panel.
- BR-13.3 A KPI shows the statistic the user asked for, before and after filtering.
- BR-13.4 A KPI's displayed precision does not change when a filter moves.

## The defect register

| # | Defect | Citation | Rating |
|---|---|---|---|
| 1 | `link(_all)` silently unlinked in the standalone path | `render():7510-7512` | SILENT |
| 2 | `filter()` + `by()` masks the wrong rows — the JS computes one row-mask from the primary source and applies it **by row index** to every source (`:4453-4471`), but a `by()` graph has one shorter source per facet (`:7649-7654`) and a qualified graph a pre-filtered one (`:7616-7617`) | `:4453-4471` | SILENT |
| 3 | `dash kpi ... if ...` shows the unfiltered statistic — Stata computes it and the JSON omits `if_expr` (`dash.ado:1421`), so `_build_kpi_html` recomputes from the full frame (`:7125-7133`) | **[measured]** 21.2973 vs 24.7727 | SILENT |
| 4 | `p25`/`p75` KPIs are absent from the JS recompute list (`:4504-4528`) and fall through to `result = 0` on the first filter interaction | `:4504-4528` | SILENT |
| 5 | KPI precision changes on first filter — initial render uses `fmt=""` (full float), the callback uses `"%9.0f"` (0 dp) | `:7118-7133` vs `:7277` | SILENT |
| 6 | `dcount` is always missing — `codebook` returns nothing in `r()` | `dash.ado:1110-1113` | SILENT |
| 7 | KPI colours bypass **both** `translate_mcolor` and `_sanitize_css_color` on the initial render — CSS-property injection, unlike the JS path at `:7292-7297` | `:6289-6290` | **SECURITY** |
| 8 | `update(brush)` is dead in the standalone path — no selection callback exists; `_kpi_update_modes` (`:5030`) is assigned and never read. `dash.sthlp:424` claims "Yes" | `:5030` | SILENT + doc |
| 9 | `filter(x, label("..."))` is read at `:7189` and nothing ever sets it | `:7189` | SILENT |
| 10 | Slider `vstep = (vmax-vmin)/100.0` gives a 0/1 dummy a step of 0.01 | `:4809`, `:4862` | MEDIUM |
| 11 | Unicode variable names rejected by ASCII-only regexes; the `filter()` one drops them **silently** | `dash.ado:1351` | SILENT |
| 12 | KPI stat list omits `var`, `cv`, `iqr`, `skewness`; `_pctile` frozen at `p(25 50 75)` | `dash.ado:1080`, `:1115` | GAP |
| 13 | `dash clear` drops `_dash_*`, not `dash_*` — orphan globals survive into the next build | `dash.ado:1024-1053` | SILENT |

## Risk: [yellow] — defect 2 touches the generated JavaScript's core assumption and needs care; the rest are well bounded.

## Dependencies
- Depends on: S12
- Blocks: S14
- Parallel batch: 4

## TDD test stubs
- Test: `link(_all)` links every graph — assert on shared source identity, not on `rc`.
- Test: `link(_all)` and an explicit name list produce equivalent linkage.
- Test: a filter over a dashboard containing a `by()` graph selects the correct rows **in each
  facet panel** — the test must check panels, not the dashboard.
- Test: the same for a graph with an `if` qualifier.
- Test: `dash kpi mean(mpg) if foreign==1` displays 24.7727, matching Stata.
- Test: `p25` and `p75` KPIs update under filtering and never display 0.
- Test: a KPI's decimal places are identical before and after a filter moves.
- Test: `dcount` returns a value.
- Test: a KPI colour containing a CSS injection payload is neutralised on the **initial**
  render, not only in the JS path.
- Test: `update(brush)` either works in standalone or the help says it does not.
- Test: `filter(x, label("My label"))` titles the widget.
- Test: an integer column's slider steps by 1.
- Test: a Unicode variable name works, or errors visibly — never silently drops.
- Test: `dash clear` removes every `dash_*` global.

## Tasks

<task type="auto" id="13-01">
  <name>Write the failing linking and filter-masking tests</name>
  <files>test/test_linking_filters.py</files>
  <action>
    `link(_all)`: assert the linked graphs share one `ColumnDataSource` instance. An `rc`
    assertion passes today and proves nothing — that is exactly how this defect stayed hidden.

    Filter masking: build a dashboard with a `by()` graph, a qualified graph and an
    unqualified graph, plus a filter. Drive the filter and assert the surviving row set **per
    panel**. This is the hardest test in the section and the most important; take the time to
    make it assert the actual rows rather than a count.

    While here, repair `test_linking.py:207-214`, which has **no assertion at all**.

    Run and confirm both fail: `link(_all)` on distinct sources, filter masking on wrong rows.
  </action>
  <verify>`link(_all)` fails on distinct sources; the facet-masking test fails with identifiably wrong rows.</verify>
  <done>Both silent defects are pinned by tests that assert behaviour, not return codes.</done>
</task>

<task type="auto" id="13-02">
  <name>Expand link(_all) in the production path</name>
  <files>dash_render.py</files>
  <action>
    Expand `_all` to the full registered-graph list in `render()` at `:7510-7512`, matching
    what the deleted `_setup_sources` did. S12 removed the dead duplicates, so this is now the
    only place it needs to exist.

    Validation already treats `_all` as a special token in Stata (`dash.ado:1240-1251`), so no
    Stata change is needed — confirm that rather than assuming.

    Note the limitation that remains and document it: exactly one link group is supported
    (`render()` builds a single `linked_source` at `:7573`). `link(_all)` is the whole-set
    case of that single group, not a second mechanism. `dash.sthlp:289` already says one
    group; make sure it still does.
  </action>
  <verify>`link(_all)` produces one shared source across every graph; explicit lists still work.</verify>
  <done>Every documented linking form works in the path users actually reach.</done>
</task>

<task type="auto" id="13-03">
  <name>Fix filter row-masking for faceted and qualified sources</name>
  <files>dash_render.py</files>
  <action>
    The generated JS (`:4453-4471`) computes one boolean row-mask from the primary source's
    snapshot and applies it **by row index** to every source in `all_graph_sources`
    (`:7308-7313`). Its inline comment claims all sources share a row universe. They do not: a
    `by()` graph gets one source per facet with only that facet's rows (`:7649-7654`), and an
    unlinked qualified graph gets a pre-filtered source (`:7616-7617`). Both are shorter than
    the primary, so the mask lands on the wrong rows.

    Fix by identity rather than by position. Carry a stable row identifier from the primary
    frame into every derived source and have the JS mask on that, so a shorter or reordered
    source masks correctly. This is more robust than index arithmetic and it is what makes the
    per-facet test in 13-01 pass.

    Watch the payload size: an extra column on every source costs bytes in a standalone file
    that is already over a megabyte. An integer index into the primary frame is enough; do not
    carry a string key.

    Verify against `examples/comprehensive_demo.do`, which has exactly this combination —
    ten `by()` graphs and three filters — and is the flagship example.
  </action>
  <verify>Per-panel row assertions pass for faceted, qualified and plain graphs; comprehensive_demo filters correctly.</verify>
  <done>A filter selects the rows it claims to, in every panel.</done>
</task>

<task type="auto" id="13-04">
  <name>Make KPIs show the number the user asked for</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    Defect 3: serialize the KPI's `if_expr`/`in_expr` (omitted at `dash.ado:1421`) and have
    `_build_kpi_html` apply it before recomputing (`:7125-7133`). Stata already computes the
    right value and stores it — the renderer overwrites it. The measured target is 24.7727 for
    `mean(mpg) if foreign==1`, where the card currently shows 21.2973.

    Defect 4: add `p25` and `p75` to the JS recompute list (`:4504-4528`). They are accepted
    by `dash kpi` (`dash.ado:1080`) and computed correctly for the initial render
    (`:5134-5137`), then fall through to `result = 0` on the first filter interaction.

    Defect 5: unify the format default between the initial render (`fmt=""`, full float) and
    the callback (`"%9.0f"`, 0 dp) so precision does not change when a filter moves. With S08
    done, the default should be the variable's Stata display format.

    Defect 6: `dcount` is always missing because `codebook` returns nothing in `r()`
    (`dash.ado:1110-1113`). Use a method that does — `levelsof` or `egen group()`.

    Defect 12: add `var`, `cv`, `iqr` and `skewness`, and stop freezing `_pctile` at
    `p(25 50 75)` (`:1115`) so an arbitrary percentile is possible. Add each to the JS
    recompute list at the same time — adding a statistic that silently reads 0 under filtering
    is defect 4 all over again.

    Defect 8: `update(brush)` has no standalone selection callback at all; `_kpi_update_modes`
    (`:5030`) is assigned and never read. Either implement a selection callback or correct
    `dash.sthlp:424`, which claims it works. Decide explicitly — implementing it is preferable
    since brushing is a headline feature, but a corrected help beats a false claim.
  </action>
  <verify>The measured KPI matches Stata; p25/p75 update; precision is stable; dcount works; every new statistic updates under filtering.</verify>
  <done>Every KPI shows the statistic requested, at a stable precision, before and after filtering.</done>
</task>

<task type="auto" id="13-05">
  <name>Close the KPI colour injection hole and the filter widget gaps</name>
  <files>dash_render.py, dash.ado</files>
  <action>
    Defect 7 is a security fix and takes priority in this task. KPI `color()`/`bgcolor()`
    bypass **both** `translate_mcolor` and `_sanitize_css_color` on the initial render
    (`:6289-6290`), while the JS path sanitises correctly (`:7292-7297`). Route the initial
    path through the same sanitiser. Write the adversarial tests first, per project rule 18:
    CSS property injection, style-attribute breakout, and a payload that is benign in the JS
    path but not in the initial one.

    Defect 9: `filter(x, label("..."))` is read at `:7189` and nothing sets it. Parse `label()`
    in `_parse_filter_raw` (`:5354-5415`), which today extracts only `varname`, `type` and
    `exclude`. Keep the existing fallback chain — Stata variable label, then variable name.

    Defect 10: derive the slider step from the data (`:4809`, `:4862`). An integer column
    should step by 1, not by `(max-min)/100`.

    Defect 11: the ASCII-only name regexes reject Stata 14+ Unicode variable names, and the
    `filter()` one (`dash.ado:1351`) drops them **silently**. Widen the regexes to Stata's own
    name rules, and make any remaining rejection visible.

    Defect 13: `dash clear` (`dash.ado:1024-1053`) drops `_dash_*` but the globals are
    `dash_*`, so orphans survive into the next build and silently add stale graphs. Fix the
    pattern and add a test that a second build after `dash clear` contains only the new
    graphs.
  </action>
  <verify>Adversarial colour payloads are neutralised on both paths; `label()` titles the widget; integer sliders step by 1; Unicode names work; `dash clear` leaves nothing behind.</verify>
  <done>The interactive surface is hardened and its remaining silent drops are gone.</done>
</task>

<task type="auto" id="13-06">
  <name>Regression sweep and commit</name>
  <files>test/, examples/, .ultraplan/CHANGELOG.md</files>
  <action>
    Repair the remaining landmine tests found in the audit: `test_kpi.py:276` and `:287` are
    tautologies; `test_server.py:2225`, `:2238` and `:2250` accept two opposite security
    outcomes. A test that passes either way is worse than no test.

    Regenerate every dashboard in `examples/`. `comprehensive_demo.do` will change materially
    because its filters were masking the wrong rows in ten faceted graphs — record what it
    looked like before and after.

    Run all suites and the S05 conformance corpus against the S01 baseline. Commit as
    single-issue commits, with the security fix in its own commit.
  </action>
  <verify>No tautological or both-ways tests remain in the touched files; suites green against baseline.</verify>
  <done>Linking, filtering and KPIs do what they say, and the tests can tell.</done>
</task>
