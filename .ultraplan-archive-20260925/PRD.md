# PRD — Phase 01: per-plot qualifiers on computed layers

> Product requirements for one implementation phase of the `dash` Stata package.
> Source of record: `phases/PHASE-01-per-plot-qualifiers-on-computed-layers.md` and
> `REMAINING.md`. Decisions: `.ultraplan/DISCOVERY.md`. Measurements: `.ultraplan/RESEARCH.md`.

---

## 1. What we're building

We are fixing a statistical command that returns a confidently wrong number and says nothing
about it.

In Stata, `twoway (scatter mpg weight) (lfit mpg weight if foreign==1)` draws a scatter of all
74 cars and a fitted line estimated on the 22 foreign ones. `dash` accepts the same command,
returns success, and draws the fitted line for **all 74** — a slope of `-.00600869` where the
user asked for `-.01042596`. Fourteen layer types behave this way, in both of the package's
renderers, and nothing warns.

This phase makes a qualifier written inside a plot's parentheses bind to that plot and to no
other: the layer is re-estimated on the qualified rows, every mark it draws respects the
restriction, and the restriction survives the viewer's first filter move, brush, link and
faceted panel. Where a layer structurally cannot carry a qualifier, it says so out loud
instead of quietly ignoring it.

## 2. The problem

`dash` advertises itself as a drop-in replacement for Stata's `twoway`. A user pastes a
working `twoway` command and expects the same numbers. For any layer that *computes*
something — a fit, a confidence band, a density, a set of bins — they do not get them.

The defect is structural, not incidental. The qualifier is implemented as a `CDSView` over the
graph's shared data source, which correctly restricts *which rows of that source a glyph
draws*. But every computed layer builds its own source from the unfiltered frame, and a view
over the graph's source never reaches it. The mechanism is sound for raw-data layers and
simply does not carry.

Three things make this the worst-shaped defect in the backlog:

- **It is silent.** Return code 0, no warning, a plausible-looking line on screen.
- **It is statistical.** The number is wrong, not the styling. A user drawing conclusions from
  a fitted line drawn on the wrong sample is being actively misled.
- **It is ordinary usage.** Multi-layer `twoway` commands with a per-layer `if` are common,
  and single-layer commands work today, so the failure appears only when a user does something
  slightly more sophisticated.

A related defect found during research widens it further: a **linked** `by()` graph gives
every panel the same source and differentiates them only by view — so every facet panel
already draws an identical `lfit`/`kdensity`/`histogram` computed from all rows, with no
qualifier involved at all. Adding `link()` silently changes a computed layer's values.

## 3. Who it's for

- **The Stata user pasting a `twoway` command.** They know Stata, not Bokeh. They expect
  dash's numbers to equal Stata's numbers, and they have no way to check short of exporting
  the data and re-running the regression by hand.
- **The dashboard viewer**, who may not be the author. They move a filter widget, drag a
  brush, click a facet — and every one of those interactions must leave the layer's meaning
  intact.
- **The package maintainer**, who needs each fix guarded by a test that fails before it and
  passes after, so this class of defect cannot return.
- **The `dash serve` operator**, who runs the server renderer and today gets none of this.

## 4. What it does

**Correctness on first paint.**

- A per-plot `if`/`in` re-estimates the layer on the qualified rows, for all 14 computed
  types: `lfit` `qfit` `lfitci` `qfitci` `lowess` `lpoly` `lpolyci` `fpfit` `fpfitci`
  `histogram` `kdensity` `mspline` `mband` `area`.
- A command-level qualifier still restricts every layer; both together intersect by logical
  AND, in either order, matching Stata exactly.
- `in` is absolute dataset observation numbers, never re-indexed into an outer subsample.
- Connected-topology layers (`line`, `tsline`, `rline`, and the line halves of `connected`
  and `rconnected`) draw the correct **gapped** shape rather than a line cutting across the
  excluded rows.
- Marker labels appear only on rows the layer drew. A `colorvar()` colour range is computed
  from the qualified rows.
- Under `by()`, each panel shows the intersection of panel rows and qualifier rows.

**Honesty where the restriction cannot apply.**

- `scatteri`, `pci` and `function` cannot be qualified. Their qualifier is still *validated* —
  a bad variable name or an out-of-range `in` is an error, as in Stata — and then reported in
  a named warning rather than silently discarded.
- When a qualifier leaves too few rows to compute (an `lfit` on one observation, a `kdensity`
  on none), the layer warns, names itself and the reason, and draws nothing. It never falls
  back to the unqualified computation, and it never aborts the build.

**Survival under interaction.**

- Moving a filter widget narrows what is shown without widening a qualified layer.
- Brushing, linking and faceting all preserve the intersection.
- `jitter()` composes with a qualifier without corrupting which rows are masked.
- Browser-side recomputation of bins and densities honours the row restriction — for
  per-plot **and** graph-level qualifiers, which share the defect.

**Proof for the renderer we are not fixing yet.**

- The generated `bokeh serve` app does not get the fix in this phase. It gets a parity test
  that fails, so the divergence is a visible red test rather than an invisible defect.

## 5. How it should feel

Invisible. A user who pastes a `twoway` command should notice nothing except that the number
is now right. There is no new syntax, no new option, no new concept to learn — the feature
already appeared to work.

The one place the user *should* notice something is when dash cannot do what was asked. Those
warnings must name the layer by number and type, state plainly what could not be applied and
why, and never be the only sign that something is wrong. A warning is a conversation, not an
error code.

## 6. What it connects to

- **`dash.ado` / `dash_parse.mata`** — emit `if_expr` and `in_expr` per plot segment. Already
  correct; this phase reads what they already write, and probes one scoping rule.
- **`dash_render.py: DashRenderer`** — the standalone HTML renderer. Where the work lands.
- **`dash_render.py: ServerAppBuilder`** — emits source for `bokeh serve`. Receives a failing
  parity test in this phase; the implementation travels with Phases 5-8.
- **Bokeh 3.9** — `CDSView`/`BooleanFilter` for marker and bar glyphs, NaN columns for
  connected glyphs, the `text` glyph for labels, `LinearColorMapper.domain` for colour.
- **The test suites** — 82 pytest modules and 25 Stata `.cscript` certification scripts.

## 7. What it does NOT do

- **It does not implement the server-mode fix.** Items 2, 5 and 6 become a failing parity
  test. The ~43 emitted call sites belong to the delegation work in Phases 5-8.
- **It does not reproduce Stata's inconsistent degenerate-subset behaviour.** Stata aborts the
  whole graph for some layer types and not others; dash is uniformly graceful, and the
  divergence is documented.
- **It does not reproduce Stata's `by()` panel deletion.** Stata silently drops a whole panel
  when one layer's qualifier leaves too few rows; dash keeps the panel.
- **It does not fix the qualifier translator's own defects** — `in 1/l` and friends being
  silently discarded, or `mpg>20` excluding missing where Stata includes it. Both are
  recorded for a later phase.
- **It does not make every private source reachable by the filter callback.** That is a
  broader defect the NaN decision reduces but does not close.
- **It does not add new syntax, options or user-facing surface.**

## 8. How we'll know it works

- `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` renders a fit whose endpoints
  imply slope `-.010425957587798849` and intercept `48.918297231743246`, to a relative
  tolerance of 1e-6, while the scatter still draws 74 points.
- Every one of the 14 computed types, given a per-plot qualifier, produces data equal to the
  same computation run on the qualified subsample.
- A `line` layer with a qualifier draws the correct number of gapped subpaths and the document
  carries no Bokeh E-1024 validation error.
- After a filter widget moves, a brush is dragged, and inside a `by()` panel, every assertion
  above still holds.
- Each of the ten work items has a regression test that **fails before its fix and passes
  after**, and each has been shown to fail by mutation.
- One end-to-end `.cscript` proves the headline case through real Stata, from command to
  rendered coefficients.
- Both suites are green against the baseline measured at the start of the phase.

## 9. Release strategy

This is not a product with a business model; the equivalent decisions are about release.

- **One commit per work item**, on `feature/batch4-interactive-layer`, each a failing test plus
  its fix. Bisectable and individually revertible.
- **Never on `main`** (project rule 6); the merge command is reported, not run.
- **No AI references in commit messages** (rule 7).
- **A CHANGELOG entry recording the behaviour change** with before-and-after values, in the
  style the archived plan used for every changed default. Users have seen the old numbers.
- **`dash.sthlp` updated in this phase**, while the semantics are being decided, discharging
  one of Phase 30's documentation items.

## 10. Risks and concerns

1. **The server overlap.** Items 2, 5 and 6 touch emitted code that Phases 5-8 delete.
   Mitigated by shipping a failing parity test instead of an implementation — but whoever
   lands the implementation must cover the `by()`-facet and callback paths, not just the plot
   loop, or the phase's guarantee is only two-thirds true.
2. **The NaN mechanism changes what a layer's source looks like.** One extra column per
   qualified connected layer, and isolated single rows need a paired scatter to be visible at
   all. Column growth is measured on the largest example rather than assumed harmless.
3. **Replacing `LabelSet` with a `text` glyph changes which Bokeh model carries labels.**
   Every existing `mlabel` assertion needs re-baselining, and a re-baselining pass is where
   a real regression can hide.
4. **`jitter()` changes a shared invariant** — how many `ColumnDataSource` objects exist per
   graph. Source counts are measured before and after, and any change is explained rather
   than waved through.
5. **Existing coverage is scatter-only and structurally cannot catch this class of bug.** The
   helper the current tests rely on reads a renderer's view filter, which reports a computed
   layer as fully visible no matter what. New assertions must compare computed **values**
   against an independently computed subsample.
6. **Items 7 and 10 are latent until item 1 lands.** Both are "correct on first paint, wrong
   after the first interaction". Deferring them would make the phase look finished in a
   screenshot and fail the moment a user touches a widget.
