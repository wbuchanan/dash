# UltraPlan Discovery

## Project Idea
Review work phase **01** in `phases/` and develop a plan to implement it.

- **Phase 01** — Per-plot qualifiers on computed layers
  (10 work items, 3 epics, `dash_render.py` in both renderers)

**Scope note (2026-09-21):** an earlier run of this command scoped the idea to phases
01-03. The current invocation narrows it to **phase 01 only**. Phases 02 and 03 are
out of scope for this plan and remain specified in `phases/`.

Source of record: `REMAINING.md` (3,053 lines) and
`phases/PHASE-01-per-plot-qualifiers-on-computed-layers.md` (1,170 lines).
The previous ultraplan was archived to `.ultraplan-archive-20260921/`.

## Codebase Detection
- **Codebase found:** Yes — a mature Stata package, ~62 commits ahead of `main` on
  `feature/batch4-interactive-layer`.
- **Stack:** Stata ado/Mata (`dash.ado` ~2,600 lines, `dash_parse.mata`) + Python
  (`dash_render.py` ~16,000 lines) + Bokeh 3.9 / pandas / numpy. Two renderers:
  `DashRenderer` (standalone HTML) and `ServerAppBuilder` (emits source for `bokeh serve`).
- **Tests:** 82 pytest modules (~3,498 passing) + 25 Stata `.cscript` certification scripts,
  run with `arch -arm64 /usr/local/bin/stata-mp -b do`.
- **Conventions:** project rules in `CLAUDE.md` — notably rule 8 (failing regression test
  before every fix), rule 4 (unit test per function), rule 6 (never commit to `main`),
  rule 7 (no AI references in commit messages), rule 21 (user stories + BRs + TRs + test plan).
- **Note on discovery scope:** this is an implementation plan for 22 already-specified work
  items, not a greenfield product. The nine categories below are reinterpreted for that
  context; questions about monetization and visual design are re-aimed at release strategy
  and user-facing behaviour, which is where the equivalent decisions live here.

## Discovery Q&A

### Category 1 — Scope and approach (batch 1)

**Q1. How should Phase 1 discovery be run, given a 1,170-line spec already exists?**
**A:** *Focus on the open decisions.* Treat `phases/PHASE-01-*.md` and `REMAINING.md` as
the discovery record; ask only what the spec leaves genuinely open (~12-20 questions).
→ Consequence: DISCOVERY.md cites the spec rather than re-deriving it. The nine standard
categories are reinterpreted as: open decisions, edge cases, verification, rollout.

**Q2. Epic C (server-mode items 2, 5, 6) overlaps Phases 5-8's `_DASH_MAPPER` delegation.
What should Phase 01 do?**
**A:** *Parity test now, implement later.* Land Epics A and B (the wrong-numbers fix) plus
Epic C's failing parity test, so the server divergence is a visible red test rather than an
invisible defect. The ~20 emitted call sites are implemented with the delegation work.
→ Consequence: Phase 01's deliverable is **standalone-correct + server-divergence-proven**.
Items 2, 5 and 6 become "write the failing test; hand the implementation to Phase 5-8", and
the plan must state explicitly that the phase ships with a known-failing (xfail-marked or
skip-marked) server parity case rather than a silent gap. TR-01.11 and TR-01.12 travel with
the item so whoever lands it covers the by()-facet and callback paths too.

**Q3. How should `line` / `connected` / `tsline` / `rline` / `rconnected` behave, given
Bokeh rejects a CDSView on connected topology (E-1024)?**
**A:** *Private pre-filtered `ColumnDataSource`, with an explicit `link()` guard test.*
→ Consequence: the qualifier works and E-1024 disappears, at the cost of that layer sitting
outside `link()` and the filter callback. This is one of the two exceptions the Phase 01
document sanctions (TR-01.4 / TR-01.8). The guard test is mandatory, not optional: it must
assert what the layer does NOT participate in, so the trade-off is recorded in the suite.

**Q4. How tight should the ground-truth tolerance be on the `lfit` assertion?**
**A:** *Tight relative tolerance, ~1e-6.*
→ Consequence: the rendered endpoints must match Stata's `regress mpg weight if foreign==1`
coefficients (slope -.01042596, intercept 48.918297) to near floating-point agreement. The
unqualified fit (slope -.00600869) fails by a factor of 1.7, so the bound is far from the
decision boundary. State the tolerance in the test body, once.

### Category 2 — Behaviour decisions the spec left open (batch 2)

**Q5. `jitter()` (item 9): the glyph draws from a private copy while the view is registered
against the graph source, so after a widget move the mask lands on the wrong rows.**
**A:** *Register the view against the source the glyph really uses, and add that source to
`all_graph_sources` so the filter callback shortens it too.*
→ Consequence: `jitter()`'s visual behaviour is unchanged; one extra `ColumnDataSource` per
jittered layer persists. Per the spec's own risk note, source counts per graph must be
measured before and after (`test_jitter.py`, `test_linking.py`, `test_linking_filters.py`,
`test_filters.py`) and any change explained rather than waved through.

**Q6. `scatteri` / `pci` / `function` take no `view` parameter — there are no rows to
qualify. What should a per-plot `if` on one of them do?**
**A:** *Named warning; the layer still draws.* The warning names the layer number and type
and states that inline-coordinate / analytic layers cannot be qualified.
→ Consequence: satisfies US-A2's first acceptance criterion and preserves the "never lose
the layer" contract. Explicitly NOT an `r(198)` from `dash.ado` — `twoway` accepts the
command, so rejecting it would break the drop-in promise.

**Q7. The browser-side aggregate recompute drops row restrictions. The GRAPH-level
qualifier shares the defect. How wide should the fix go?**
**A:** *Fix both — it is one code path.* Thread the member row ids into `_dash_agg_config`
and intersect in JS for per-plot and graph-level qualifiers alike.
→ Consequence: Phase 01 grows slightly beyond its ten items. This is a deliberate, recorded
scope addition, not creep: the work already edits `_dash_agg_config` and `_FILTER_JS`, and
leaving the graph-level half broken would knowingly ship a defect the change touches.
Phase 5 VALIDATE must show this as an approved task-beyond-requirement.

**Q8. What happens when a qualifier leaves too few rows for the layer's computation
(`lfit` with 1 observation, `kdensity` with 0)?**
**A:** *Warn naming the layer and the reason; draw nothing for that layer.* e.g.
"dash: lfit on layer 2 needs at least 2 observations; the qualifier left 1".
→ Consequence: matches how dash already degrades `lowess` without statsmodels. Explicitly
NOT a fallback to the unqualified computation — that would put a wrong number on screen,
which is the exact failure this phase exists to remove. Never aborts the build.

### Category 3 — Verification, rollout and communication (batch 3)

**Q9. This changes rendered output users have already seen. How is that communicated?**
**A:** *CHANGELOG entry with before/after values*, in the style the archived plan used for
every changed default: the command, the old number, the new number, why the old one was
wrong. No runtime migration note.
→ Consequence: the plan carries a CHANGELOG deliverable. For the headline case that is
`dash (scatter mpg weight) (lfit mpg weight if foreign==1)`: was slope -.00600869 /
intercept 39.440284 (all 74 cars), now -.01042596 / 48.918297 (the 22 foreign cars).

**Q10. Rule 8 requires a failing test first. Which test languages?**
**A:** *pytest for every item, plus one end-to-end `.cscript`.* The cscript drives real
Stata — `dash lfit ... if foreign==1`, `dash build`, assert the rendered coefficients.
→ Consequence: catches spec-shape mismatches that pure-Python probes miss. This repo has a
documented history of exactly that failure (probes built against a spec shape `dash.ado`
never emits). Ten-plus pytest regressions + 1 new cscript = the phase's test deliverable.

**Q11. Commit shape?**
**A:** *One commit per work item, on the current branch* (`feature/batch4-interactive-layer`).
Each commit is a failing test plus its fix.
→ Consequence: ~10-12 commits, bisectable, individually revertible. Rule 6 holds — nothing
is committed to `main`, and the merge command is reported rather than run. Rule 7 holds —
no AI references in commit messages.

**Q12. What baseline should the plan assume?**
**A:** *Re-measure it as task 01.* Record today's pass/fail/skip counts for both suites and
commit them before touching any product code.
→ Consequence: every later claim is measured against a number taken today, not the audit's
`ca5fe35` figure (3,498 passed / 37 skipped / 25 cscripts). The archived plan did this and
it surfaced a stale-environment problem; repeating it is cheap insurance.

### Category 4 — Documentation, performance and interaction scope (batch 4)

**Q13. Phase 30 owns the `dash.sthlp` per-plot-qualifier item. Should Phase 01 write it?**
**A:** *Write it in Phase 01.* The semantics are being decided here — which layers can be
qualified, what `link()` does to a private-source layer, what each warning says.
→ Consequence: Phase 01 gains a `dash.sthlp` deliverable and discharges one of Phase 30's
nine items. Note that in the plan so the documentation phase does not re-plan it.

**Q14. Any data-size concern from re-running each qualified computation on a subset?**
**A:** *No special handling; measure and record.* A qualified layer computes on FEWER rows
than today, so per-layer cost falls; the only growth is one masked frame per qualified layer.
→ Consequence: the plan carries a measurement task (render time on the largest example,
before and after), not a cap. A cap is added only if a number justifies it.

**Q15. Item 8 scope — marker labels, colorvar range, or both?**
**A:** *Both.* A `LabelSet` has no `view` property, so labels must be masked in the data;
the `colorvar` range must be computed from the qualified rows or the colour scale is set by
rows the layer never drew. Both are US-A3 acceptance criteria.

**Q16. How should `by()` faceting interacting with a per-plot qualifier be treated?**
**A:** *First-class requirement with its own tests.* The layer shows the intersection of
panel rows ∩ qualifier rows, on first paint and after every widget move.
→ Consequence: item 7's intersection bug lives exactly here, and the emitted `by()`-facet
path is where the spec warns the server work is most likely to be under-scoped. Dedicated
tests, not incidental coverage.

---

## Discovery Summary

- **Total questions asked:** 16, in 4 batches
- **Mode:** focused on open decisions (Q1), with `phases/PHASE-01-*.md` (1,170 lines) and
  `REMAINING.md` (3,053 lines) standing as the discovery record for everything already
  specified — 10 work items, 3 epics, 7 user stories, BR-01.1-13, TR-01.1-15, and a test
  plan naming 13 existing test files.
- **Categories covered:** the nine standard categories reinterpreted for an implementation
  plan — (1) scope and approach, (2) behaviour decisions, (3) verification and rollout,
  (4) documentation, performance and interaction scope. Monetization and visual-design
  categories do not apply and were re-aimed at release strategy and user-facing behaviour.
- **Categories not applicable:** Users & Context and Integration Points are settled by the
  existing package and were not re-asked.

### Decisions that shape the plan

| # | Decision | Effect on the plan |
|---|---|---|
| 1 | Epic C: parity test now, implement with Phases 5-8 | Phase 01 ships standalone-correct with the server divergence proven by a red test, not hidden |
| 2 | Connected glyphs get a private pre-filtered source | Qualifier works, E-1024 disappears; mandatory `link()` guard test records the trade-off |
| 3 | Ground-truth tolerance ~1e-6 | The `lfit` assertion is meaningful, not decorative |
| 4 | jitter(): register against the real source | Visual behaviour unchanged; source counts measured before/after |
| 5 | Inline/analytic layers: named warning, still draw | Preserves "never lose the layer"; no `r(198)` from `dash.ado` |
| 6 | Aggregate recompute: fix per-plot AND graph-level | Deliberate scope addition, to be approved in VALIDATE |
| 7 | Degenerate subsets: warn and draw nothing | Never falls back to a wrong number |
| 8 | CHANGELOG entry with before/after values | Behaviour change is recorded, not silent |
| 9 | pytest per item + one end-to-end cscript | Catches spec-shape mismatches Python probes miss |
| 10 | One commit per item, current branch | Bisectable; rules 6 and 7 hold |
| 11 | Re-measure the baseline as task 01 | No claim rests on a figure from the audit |
| 12 | Write the `dash.sthlp` text here | Discharges one Phase 30 item while the reasoning is fresh |
| 13 | Performance: measure, do not cap | Cost falls; a guard needs a number to justify it |
| 14 | `by()` x qualifier is first-class | Dedicated tests on the path most likely to be under-scoped |

### Key themes

- **Wrong numbers, not missing features.** Every item exists because a statistical command
  returns a confidently wrong result with rc 0 and no warning.
- **Correct on first paint is half the job.** Items 7, 9 and 10 are all "right until the
  user touches a widget" defects.
- **The two renderers have diverged.** The fix threads through `GlyphMapper`, which reaches
  exactly one of the server's plot types; everything else in the emitted app duplicates it.
- **Every silent failure becomes a named warning.** The "never lose the layer" contract is
  preserved, but "drawn unfiltered" stops being the silent default.
