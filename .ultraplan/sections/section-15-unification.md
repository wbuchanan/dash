# Section 15: Server/standalone unification

## Overview
`dash` implements the same 38 behaviours **107 times**.

Counted: 38 `map_*` methods in the standalone renderer; 37 `ptype` branches in the server main
loop; 16 more in the `by()` facet loop; 16 more in `by(total)`. **16 plot types are
implemented four times and 21 more twice.** KPI card HTML exists in 5 places, histogram
binning in 4, KPI statistics in 4 — one of them being Stata's `summarize`.

They have already drifted, and the drift is user-visible for identical commands:

| Behaviour | Standalone | Server |
|---|---|---|
| histogram bins | 10 | 20 |
| lowess `frac` | 0.8, `bwidth()` honoured | hardcoded 0.5, `bwidth()` ignored |
| lfit grid | 200 points with padding | 100 without |
| default series colour | scheme-derived | literal `#1f77b4` (`:8678`, `:9680`, `:9778`) |
| KPI card | 36px, bordered | 28px, borderless |
| `msize(large)` | 12px **or** 11px *within the same generated file* — 7 duplicated size maps on 2 incompatible scales |

`grep "scheme"` over lines >7738 returns **zero hits**: `ServerAppBuilder` ignores the scheme
entirely, so three scatters render identically blue.

Every parity fix in S06-S13 was written once, for the standalone path. Without this section
they have to be written again, and the next fix after that, forever.

## User story
> As a Stata user, the same command produces the same chart whether I build a standalone file
> or serve it — and when a bug is fixed, it is fixed in both.

## Business requirements
- BR-15.1 Identical input produces identical output in both modes, except where a documented
  capability difference applies (live aggregate recomputation under filtering).
- BR-15.2 A behaviour is implemented once.
- BR-15.3 The documented standalone-vs-server comparison table becomes true.

## Technical requirements
- TR-15.1 The generated app **imports and calls** shared functions instead of re-deriving
  behaviour in generated string literals.
- TR-15.2 The four glyph dispatch tables collapse to one.
- TR-15.3 The 5 KPI HTML builders, 4 histogram binners, 4 KPI statistic implementations and
  7 size maps each collapse to one.
- TR-15.4 A parity test asserts equivalence for a corpus of commands, so drift cannot recur
  silently.

## Risk: [red] — the largest refactor in the plan, on a 10,455-line file, in the half with the thinnest meaningful test coverage.

## Dependencies
- Depends on: S14
- Blocks: S16
- Parallel batch: 5

## TDD test stubs
- Test: for each command in a parity corpus, the figures built by both modes have equivalent
  glyph types, data and visual properties.
- Test: histogram bin counts are equal in both modes.
- Test: lowess `frac` and `bwidth()` handling are equal.
- Test: lfit grid size and range are equal.
- Test: default series colours are equal and scheme-derived in both.
- Test: KPI card markup is equal.
- Test: `msize(large)` resolves to one value everywhere in a generated file.
- Test: the generated app contains no glyph dispatch table of its own.
- Test: `scheme()` affects server output.
- Test: the capability differences that legitimately remain are exactly the documented ones.

## Tasks

<task type="auto" id="15-01">
  <name>Build the parity corpus and the failing equivalence test</name>
  <files>test/test_mode_parity.py, test/fixtures/parity_corpus.do</files>
  <action>
    Assemble a corpus covering every plot type, the `by()` and `by(total)` paths, KPIs,
    filters, linking, tabs and every layout — the four code paths that duplicate each other
    must all be represented, or the test will miss exactly what it is for.

    For each command, build both modes and compare the resulting Bokeh models structurally:
    glyph types, data values, and the visual properties that have drifted (colour, size, line
    width, alpha).

    Where a difference is legitimate — live aggregate recomputation — encode it as an explicit
    allowance with a comment, not as a loose comparison. A test that tolerates unknown
    differences would pass through the next drift too.

    Run. The known divergences must appear: bins 10 vs 20, lowess 0.8 vs 0.5, lfit 200 vs 100,
    colour scheme-derived vs `#1f77b4`, KPI 36px vs 28px. If a divergence in the audit does
    not appear, find out why before proceeding — the corpus is probably not reaching that
    path.
  </action>
  <verify>Every audited divergence is reproduced by the test, by name and by value.</verify>
  <done>Drift is measured, and the measurement is the acceptance criterion for this section.</done>
</task>

<task type="auto" id="15-02">
  <name>Extract the shared primitives</name>
  <files>dash_render.py</files>
  <action>
    Work outward from the smallest and least risky, verifying the parity test after each:

    1. **The size and colour maps.** 7 duplicated size maps on 2 incompatible scales, where
       `msize(large)` is 12px in one and 11px in another *in the same file*. One map.
    2. **Histogram binning.** 4 implementations. One function, with S07's data-driven rule.
    3. **KPI statistics.** 4 implementations, one of which is Stata's `summarize`. One
       function. Keep the Stata-side computation as the source for the *initial* value where
       that is deliberate (S13 made it honour `if`/`in`), but the recompute logic is shared.
    4. **KPI card HTML.** 5 builders. One.

    Each extraction is its own commit. After each, run the parity test and the full suite.
    That cadence is what makes a refactor this size recoverable — a failure identifies the
    extraction that caused it.
  </action>
  <verify>The parity test's divergence count falls after each extraction; the full suite stays green throughout.</verify>
  <done>The small duplications are gone and the parity test is measurably closer to passing.</done>
</task>

<task type="auto" id="15-03">
  <name>Collapse the four glyph dispatch tables to one</name>
  <files>dash_render.py</files>
  <action>
    This is the core of the section: 38 `map_*` methods, 37 server `ptype` branches, 16 in the
    `by()` facet loop, 16 in `by(total)`.

    The generated app currently re-derives everything in string literals. Have it **import**
    `GlyphMapper` and call it, exactly as the standalone path does. The generated file becomes
    a thin document-construction shim over the same rendering code rather than a second
    renderer.

    Two constraints to design around. First, the generated app must remain runnable in an
    environment where `dash_render.py` is importable — that is the same install `dash.ado`
    already resolves, so record how the app locates it and test the packaged-install case
    against S02's cscript. Second, the app embeds its data base64-encoded; keep that, and keep
    S14's cleanup of the file that carries it.

    The `by()` and `by(total)` facet loops should become the same facet-expansion code the
    standalone path uses (`_expand_by_groups`, `:5417-5499`), not a third and fourth copy.

    Wire the scheme through while doing it: `grep "scheme"` over lines >7738 returns zero hits
    today, which is why server output is uniformly `#1f77b4`. After this, S11's scheme
    consumption applies to both modes for free — which is the point of the section.
  </action>
  <verify>The parity test passes except for documented capability differences; the generated app contains no dispatch table of its own.</verify>
  <done>A plot type is implemented once, and both modes render it identically.</done>
</task>

<task type="auto" id="15-04">
  <name>Lock the parity in, correct the comparison table, commit</name>
  <files>test/, dash.sthlp, .ultraplan/CHANGELOG.md</files>
  <action>
    Add the parity test to the standard suite so any future divergence fails CI. This is the
    deliverable that outlives the section.

    Correct `dash.sthlp`'s standalone-vs-server comparison table, which has three known
    errors: `:424` claims brush/lasso KPI update works in standalone (S13 settled it);
    `:422` *understates* the standalone histogram, which does recompute bin counts
    (`:4566-4630`); and the remaining rows should be re-derived from the parity test's
    allowance list rather than edited by hand, so the table and the test agree by construction.

    Record in the CHANGELOG that server-mode output changes substantially — different bin
    counts, different smoother parameters, different colours, different KPI cards — because
    it is now correct rather than a drifted copy.

    Run all suites, the S05 conformance corpus and the parity corpus against the S01 baseline.
    Commit.
  </action>
  <verify>The parity test is in the standard suite; the help's table is generated from the same allowance list; suites green.</verify>
  <done>The two modes cannot drift again without a test failing.</done>
</task>
