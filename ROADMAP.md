# ROADMAP.md — closing the gaps in `dash`

Companion to [`GAPS.md`](GAPS.md). Every finding in that audit — 70 gaps
across 14 areas — is assigned to exactly one work package here, and the
[traceability matrix](#traceability-matrix) proves the coverage.

Baseline: `187a786` (`feature/batch4-interactive-layer`, 62 commits ahead of
`main`). Written 2026-09-21.

---

## How to use this document

Each work package (WP) is self-contained and carries:

- **Gaps closed** — the `GAPS.md` finding IDs it retires
- **User story** — who wants this and why
- **BR** — business requirements (what must become true)
- **TR** — technical requirements (how, with file:line and the actual approach)
- **AC** — acceptance criteria (how we know it is done)
- **Test plan** — unit, certification, integration and regression coverage

A WP is done when every AC passes *and* its tests are committed and green in
both suites. Nothing is "done" on the strength of a code change alone
(CLAUDE.md rules 2 and 4).

`phases/` holds an earlier 31-phase breakdown derived from `REMAINING.md`.
Where the two overlap, **this document wins** — it is built on measured
findings at `187a786`, and it corrects two technical assumptions that
breakdown made (see [Corrections](#corrections-to-earlier-plans)).

---

## Sequencing principle

Three facts drive the order:

1. **Wrong numbers outrank everything.** A dashboard that renders beautifully
   from the wrong rows is worse than one that fails, because nothing tells the
   user.
2. **Two fixes are near-free and stop silent data loss** (WP-01). They are
   four `&& depth == 0` clauses and one missing quote-tracker. They go first
   because nothing else in the list has that ratio.
3. **WP-09 is the lever.** Six of the eight server defects exist because the
   server re-implements what `GlyphMapper` already does. Once a plot type
   delegates, it inherits every standalone fix for free. Doing the
   server-dependent packages before WP-09 means doing that work twice.

### Dependency graph

```
M1 ─ WP-01 ──┐
     WP-02 ──┤
     WP-03 ──┤
     WP-04 ──┼──► M2 ─ WP-09 ──┬──► WP-10 ──┐
     WP-05 ──┤                 ├──► WP-11 ──┼──► WP-12
     WP-06 ──┤                 └──► WP-16 ──┘      │
     WP-07 ──┤                                     │
     WP-08 ──┘                                     ▼
                                    M3 ─ WP-13 ─ WP-14 ─ WP-15
                                         WP-17   WP-18   WP-19   WP-20
                                                          │
                                                          ▼
                                    M4 ─ WP-21  WP-22  WP-24  WP-25  WP-26
                                                          │
                                                          ▼
                                    M5 ─ WP-23 ─ WP-27  (need all above)
```

### Milestones

| | Milestone | Packages | Exit gate |
|---|---|---|---|
| **M1** | **Correct and installable** | WP-01 … WP-08 | No command produces silently wrong output or silently loses user input. A `net install` renders correctly. |
| **M2** | **One renderer** | WP-09 … WP-12 | Standalone and server agree on all 38 plot types plus `by()`, `link()`, `tabs()`, KPIs, hover. |
| **M3** | **An honest surface** | WP-13 … WP-20 | Every accepted option is honoured or reported. Schemes are consumed as declared. Resources are bounded. |
| **M4** | **Complete and covered** | WP-21 … WP-26 | Documented capabilities exist; the suite cannot pass vacuously; CI runs both suites. |
| **M5** | **Shippable** | WP-23, WP-27 | Help matches code; `net install` + every example passes; package is versioned and merge-ready. |

---

# Milestone 1 — Correct and installable

## WP-01 · Parser integrity — DONE

**Gaps closed:** A6, A7, A8 · **Severity:** S1 · **Effort:** S · **Depends on:** —

> **DONE** (24sep2026, on WP-24's mapping).  Every acceptance criterion holds
> on `a2c7502`, each by a test that goes red when the criterion is broken on
> a copy of the tree (WP-24's mutation campaign):
>
> * **AC-01.1** P1B-01..08, and P1B-35 end to end (two layers drawn, no
>   "ignoring" note).  **TR-01.1**'s comma half had no test that could fail
>   -- P1B-09..12 find the comma before any quote -- and has P1B-31, P1B-32
>   and P1B-38.
> * **AC-01.2** P1B-19..22e, P1B-33, P1B-34, and test_e2e_filters.cscript
>   FL-QT-1/2 (the title drawn as written, no widget).
> * **AC-01.3** P1B-13, test_help_claims_1.cscript HC1-21, and P1B-36 (r(198)
>   and "unbalanced parentheses"); **AC-01.4** P1B-15..17, HC1-04/06/21, and
>   P1B-37 (the criterion's own input, twoway's return code and message).
> * **AC-01.5** test_tokenizer.cscript P1A-20..28; **TR-01.5** P1B-23..25.
>
> With all of 9c7dbf7 reverted at once, P1B-02, HC1-04/06/21, every new P1B
> case and FL-QT-1 fail.

> **User story.** As a Stata user, when I write a perfectly legal `twoway`
> command, I want every plot I asked for to be drawn and my title text left
> alone — and if `dash` cannot parse something, I want it to say so rather
> than quietly do something else.

### Business requirements

- **BR-01.1** No legal `twoway` command may lose a plot layer silently.
- **BR-01.2** No user-supplied text may be modified by the parser.
- **BR-01.3** Input the parser cannot represent must raise an error, not
  produce a partial result.

### Technical requirements

- **TR-01.1** Delete the `& depth == 0` guard from the double-quote and
  compound-quote branches of `_dash_split_segs` at `dash_parse.mata:468` and
  `:473`, and from `_first_comma_pos` at `:303` and `:308`. Paren mode
  (`:410, 415`) already tracks quotes at any depth and is the reference
  implementation — flat mode must match it exactly.
- **TR-01.2** Add quote tracking to `_dash_extract_filters`
  (`dash_parse.mata:752-828`). It currently scans the lower-cased raw command
  for `filt|filte|filter` with only a preceding-character word-boundary test
  at `:787`. It must skip any match that falls inside a double-quoted or
  compound-quoted run, reusing the same `in_dq` / `in_cq` state machine the
  splitter uses. Factor that state machine into one helper rather than
  writing a third copy.
- **TR-01.3** Add an end-of-scan balance check to `_dash_split_segs`: on
  exit, `depth != 0` or `in_dq != 0` must `exit(198)` naming the unbalanced
  construct. Today both conditions silently yield one segment.
- **TR-01.4** Reject the malformed paren-mode forms `twoway` rejects — stray
  text between groups (`(a) junk (b)`), an unmatched `)`, and a group after a
  top-level comma. `dash_parse.mata:439` currently `break`s at the first
  top-level comma and treats everything after it as graph options.
- **TR-01.5** Fix `_dash_option_names` (`:945`), which toggles its in-quote
  flag on every `"` with no compound-quote handling, so an odd quote count
  drops trailing options.

### Acceptance criteria

- **AC-01.1** `dash scatter mpg weight, title("a ( b") name(g) || line mpg weight`
  registers a graph with **two** plot layers and prints no
  "ignoring unsupported option(s)" message.
- **AC-01.2** `dash build, title("Q1 filter(foreign) report")` renders the
  title **`Q1 filter(foreign) report`** and creates **no** filter widget.
- **AC-01.3** `dash scatter y x, legend(off || line y2 x` exits 198 with a
  message naming the unclosed parenthesis.
- **AC-01.4** `dash (scatter y x) junk (line y2 x)` exits 198, matching
  `twoway`'s `r(198)`.
- **AC-01.5** Every case in `test/test_tokenizer.cscript` still passes.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | `test_tokenizer.cscript` — new group T-21…T-30 | Segment count for a paren inside `title()`, `legend(label(1 "a ( b"))`, `note()`; nested quotes; a `)` inside a quoted value |
| Cert | `test_tokenizer.cscript` — T-31…T-34 | Unbalanced `(`, unterminated `"`, stray text between groups, group after top-level comma all exit 198 |
| Cert | new `test_filter_extraction.cscript` | `filter(` inside `title()`, `note()`, `subtitle()`, and in mixed case, is not harvested; a real `filter()` next to a quoted one still is |
| Integration | new `test_parser_integrity.py` | Build from a spec whose title contains `filter(`; assert the rendered title is verbatim and `filter_widgets` is empty |
| Regression | `BUGS.md` entries for A6 and A7 | Per CLAUDE.md rule 8: written **before** the fix, failing against `187a786` |

---

## WP-02 · Computed layers must honour their rows — DONE

**Gaps closed:** A1, A2 · **Severity:** S1 · **Effort:** M · **Depends on:** —

> **DONE** (24sep2026, on WP-24's mapping).  Every acceptance criterion holds
> on `a2c7502`, each by a test that goes red when the criterion is broken on
> a copy of the tree (WP-24's mutation campaign):
>
> * **AC-02.1, AC-02.2** test_computed_layer_rows.py's mapper-level tests and
>   its spec-level `TestAQualifiedSpecComputesFromItsRows` (fourteen layers,
>   saved and served) and `test_ac_02_1`, with test_help_claims_6's kdensity
>   and lpoly `if` cases.  A dispatch that handed computed layers no view left
>   every mapper-level test green; the spec-level tests catch it, in each
>   mode.
> * **AC-02.3** `TestLinkedFacetsComputeSeparately`, `test_ac_02_3`
>   (`link(_all)' on auto) and `TestLinkAll`.
> * **AC-02.4** `test_ac_02_4`, saved and served, against the fixture's
>   `regress`, and test_e2e_single.cscript P1C-19, end to end through Stata
>   against a live `regress` -- the test_qualified_layers GAPS.md A1 said was
>   never written.
> * **TR-02.1, TR-02.4** `TestTheMaskHelperDegradesSafely`; the follow-up
>   fixes 9179359 and 7c6a2fe, test_view_alignment.py.

> **User story.** As an analyst, when I write `(lfit mpg weight if foreign==1)`
> or facet a histogram with `by(foreign) link(_all)`, I want the fit and the
> bins computed from **those** rows — because I will read the number off the
> chart and put it in a paper.

### Business requirements

- **BR-02.1** Every statistical layer computes from exactly the rows its
  qualifier, facet or graph filter selects.
- **BR-02.2** If a filter cannot be applied, the layer must warn — never
  silently fall back to all rows.

### Technical requirements

The audit established the shape of this fix, and it is **not** the obvious
one. The 13 affected mappers do not draw from the shared source: they compute
a grid and build their **own** `ColumnDataSource` (e.g. `map_lfit` at
`dash_render.py:3865`, `fit_source = ColumnDataSource({"x": x_fit, "y": y_fit})`).
Attaching the `CDSView` to the returned renderer would therefore do nothing.
**The input arrays must be masked before the computation.**

- **TR-02.1** Add two helpers to `GlyphMapper`:

  ```python
  @staticmethod
  def _view_mask(view, n: int) -> "np.ndarray | None":
      """Boolean row mask a CDSView selects, or None for 'all rows'.

      Handles BooleanFilter (.booleans) and IndexFilter (.indices).
      Returns None when the view is absent or its length does not match,
      so a mismatch degrades to today's behaviour rather than crashing.
      """

  def _xy(self, source, yvar, xvar, view):
      """The (x, y) float arrays this layer should compute from."""
  ```

  `_view_mask` reads `getattr(view, "filter", None)` then `.booleans` /
  `.indices`. The per-plot path already builds exactly this shape — a
  `BooleanFilter` aligned to source rows, intersected with any facet view
  (`dash_render.py:9979-9989`), so the mask is ready to consume.

- **TR-02.2** Replace the direct `source.data[...]` reads in all 13 mappers
  with `self._xy(...)`: `map_lfit` (3821), `map_qfit` (3873), `map_lfitci`
  (3918), `map_qfitci` (3998), `map_lowess` (4091), `map_lpoly` (4272),
  `map_lpolyci` (4344), `map_fpfit` (4517), `map_fpfitci` (4569),
  `map_histogram` (4636), `map_kdensity` (4806), `map_mspline` (5912),
  `map_mband` (5983). `map_area` (3592) reads the source the same way and
  takes the same fix.
- **TR-02.3** `_linked_graph_views` (`:11502`) and the facet view builder
  (`:11466-11480`) already produce correct masks — no change needed there once
  the mappers consume them. Verify by test rather than by edit.
- **TR-02.4** Warn when a mask is present but its length does not match the
  source, rather than ignoring it silently.
- **TR-02.5** **Scope note.** This fix is for render-time filtering (per-plot
  `if`/`in`, facets, graph-level filters). It does not change the documented
  standalone-versus-server difference on *interactive* filter widgets
  (standalone rescales in JS; the server recomputes) — that distinction is in
  `dash.sthlp:516-533` and is intentional.

### Acceptance criteria

- **AC-02.1** With `y = x` for `g==0` and `y ≈ 50 + 2x` for `g==1`, a spec
  with `{"type":"lfit","if_expr":"g==0"}` produces fitted endpoints
  **1.0 → 4.0**, not the full-data 25.5 → 30.0.
- **AC-02.2** The same holds for `qfit`, `lowess`, `lpoly`, `mband`,
  `kdensity`, `histogram` and the four `*ci` variants.
- **AC-02.3** `histogram mpg, by(foreign) link(_all)` produces **different**
  bar heights in the two panels, matching the unlinked `by()` result.
- **AC-02.4** `dash (scatter mpg weight) (lfit mpg weight if foreign==1)`
  draws a fit whose coefficients equal Stata's
  `regress mpg weight if foreign==1`.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Unit | new `test_computed_layer_filtering.py`, parametrized over all 14 mappers | Rendered output with a qualifier differs from without, and equals the same mapper run on the pre-filtered frame |
| Unit | same file | `_view_mask` handles `BooleanFilter`, `IndexFilter`, `None`, and a length mismatch (warns, does not crash) |
| Truth | extend `test/fixtures/stat_truth.json` | Add `if`-qualified ground truth from Stata for `lfit`, `qfit`, `lowess`, `lpoly`, `kdensity`, `histogram` — computed by `scripts/extract_stat_truth.do` |
| Integration | `test_linking_filters.py` | Linked `by()` facets produce per-panel statistics |
| Cert | new `test_qualified_layers.cscript` | End-to-end: `dash (lfit mpg weight if foreign==1)` vs `regress`, compared in Stata |
| Regression | `BUGS.md` entries for A1 and A2 | Written first, failing at `187a786` |

---

## WP-03 · `dash serve` accepts its own options — DONE

**Gaps closed:** C1, C2, C3 · **Severity:** S1 · **Effort:** S · **Depends on:** —

> **DONE** (24sep2026, on WP-24's mapping).  Every acceptance criterion holds
> on `a2c7502`, each by a test that goes red when the criterion is broken on
> a copy of the tree (WP-24's mutation campaign):
>
> * **AC-03.1** test_serve_launch.cscript SRV-01..04; test_help_claims_4
>   HC4-17 (stub) and HC4-19/20/21 (a real launch); and, in
>   test_server.py, `TestTheOutputPathRule` and `TestTheRealHandoffServes`.
> * **AC-03.2** SRV-18 (a graph registered, r(198) and the range message);
>   P20-26 and P4-75 check the return code only, and SRV-09/10 passed with
>   the range check removed, because an empty registry exits 198 on its own.
> * **AC-03.3** SRV-17 (a build with a filter, then a bare `dash serve': the
>   spec carries the filter and the served document has the dropdown),
>   test_serve_options' inherit cases and HC2-26b/c.
> * **AC-03.4** test_bug_regressions.cscript BR-02 (`dash build', the
>   immediate route and `dash serve' up to its launch, each under its own
>   log).  **TR-03.4** SRV-13..15.

> **User story.** As a user following the help, I want `dash serve, port(5006)`
> to start a server on port 5006.

### Business requirements

- **BR-03.1** Every option `dash serve` documents must work.
- **BR-03.2** The happy path must be covered by a test that exercises the
  real subcommand.

### Technical requirements

- **TR-03.1** At `dash.ado:2601`, strip the leading comma from `` `0' `` before
  forwarding, exactly as `_dash_build` does at `:2440`:
  `local _fwd : copy local 0` then `local _fwd : subinstr local _fwd "," ""`.
  Use the extended-function form, which operates on the macro's *value* and
  therefore does not re-expand the user's `title()` text.
- **TR-03.2** `_dash_serve_spec` (`:2530-2589`) is correct and complete —
  it validates the port range, the timeout, and inherits build options. Do not
  touch it.
- **TR-03.3** Trace and fix the `(file … not found)` diagnostic that surfaces
  under `capture noisily` on both `dash serve` and `dash build` (C3). It
  indicates a `capture confirm file` failing in the spec path; the three
  candidates are `dash.ado:50`, `:1710` and `:2268`.
- **TR-03.4** Either honour or reject `saving()`, `replace` and `server` on
  `dash serve` — they are declared in `_dash_prepare_spec` (`:2009, 2019,
  2020`), never referenced in its body, and reach it through the trailing `*`.

### Acceptance criteria

- **AC-03.1** `dash serve, port(5099) timeout(1) nobrowser` starts a server on
  5099 and exits after 1 minute.
- **AC-03.2** `dash serve, port(80)` still exits 198 with the range message.
- **AC-03.3** A `dash build, filter(...)` followed by a bare `dash serve`
  serves a dashboard carrying that filter.
- **AC-03.4** Under `capture noisily`, neither `dash build` nor `dash serve`
  emits a "file not found" diagnostic.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | new `test_serve_launch.cscript` | `dash serve, port(N) timeout(1) nobrowser` returns rc 0 and the server exits on its own timeout. Must invoke `dash serve`, **not** `_dash_serve_spec` — bypassing the subcommand is what hid this defect |
| Cert | `test_serve_options.cscript` | Keep existing coverage; add one case that goes through `dash serve` |
| Integration | `test_server_serves.py` | Poll the port, pull a session, assert the document has the expected figure |
| Regression | `BUGS.md` entry for C1 | Written first, failing at `187a786` |

---

## WP-04 · Registry integrity — DONE

**Gaps closed:** K1, K2, K3 · **Severity:** S1 · **Effort:** S · **Depends on:** —

> **DONE** (24sep2026, on WP-24's mapping).  Every acceptance criterion holds
> on `a2c7502`, each by a test that goes red when the criterion is broken on
> a copy of the tree (WP-24's mutation campaign):
>
> * **AC-04.1** test_registry_collision.cscript REG-01, REG-02 and REG-35
>   (the message).
> * **AC-04.2** REG-04..06, REG-12, and REG-42 (the build draws the KPI card
>   and no orphaned graph, and says nothing about "both").
> * **AC-04.3** REG-15, REG-27, REG-28, and REG-43 (the warning names the
>   entry: with its name dropped from the warning, REG-15 stayed green).
> * **TR-04.2** REG-11; **TR-04.4** (K3) GOS-01..10 and HC1-20.  A second
>   name() in one command, refused as twoway refuses it since `a17c552`, is
>   held by REG-33, REG-37, REG-38 and REG-41.

> **User story.** As a user building a multi-graph dashboard, if I reuse a
> name by mistake I want to be told — not to have a graph vanish from the
> output with `rc=0`.

### Business requirements

- **BR-04.1** Graphs and KPIs share one namespace and one collision policy.
- **BR-04.2** No registered item may be dropped from a build without a message.

### Technical requirements

- **TR-04.1** Give `_dash_kpi` (`dash.ado:1928-1956`) the collision check
  `_dash_register_graph` has at `:1556-1575`: refuse a name already in
  `${dash_graph_registry}` unless `replace` is given. Support
  `name(k1, replace)` with the same sub-option split (`:1530-1534`).
- **TR-04.2** When a KPI replaces a graph of the same name (or vice versa),
  drop the superseded item's globals so the registry cannot hold both a
  `dash_json_<n>` and a `dash_kpi_<n>`.
- **TR-04.3** Make the skip at `_dash_prepare_spec:2280` defensive: if a name
  carries both a graph JSON and a KPI marker, warn rather than silently
  `continue`.
- **TR-04.4** — DONE, and its premise was half wrong. The policy is now
  measured against `twoway` rather than read off the propagation loop
  (see K3). Last-write-wins across segments was correct and matches `twoway`;
  "never clear" was not — `title("")` blanks. The defect actually present was
  precedence: an option after the top-level comma lost to one inside a
  segment, where `twoway` has it win. Fixed in `_dash_plot`, documented in
  `dash.sthlp`, covered by `test/test_graph_option_scope.cscript`.
- **TR-04.5** (K2) Document in `dash.sthlp` that the registry lives in Stata
  globals and that overwriting `dash_*` globals by hand is unsupported. A
  deeper fix — moving session state out of globals — is out of scope here and
  recorded as a known limitation.

### Acceptance criteria

- **AC-04.1** `dash scatter mpg weight, name(g1)` then
  `dash kpi mean(mpg), name(g1)` exits 198 telling the user to use
  `name(g1, replace)`.
- **AC-04.2** With `replace`, the build contains the KPI and **no** orphaned
  graph JSON.
- **AC-04.3** A build that skips a registry entry for any reason emits a
  warning naming it.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | `test_clear_registry.cscript` — new cases | Graph→KPI collision exits 198; KPI→graph collision exits 198; `replace` succeeds and leaves exactly one item |
| Integration | new `test_registry_collision.py` | A built dashboard from a collided registry contains every item the user registered — count figures **and** KPI cards |
| Regression | `BUGS.md` entry for K1 | Written first, failing at `187a786`; assert the built HTML contains a figure |

---

## WP-05 · Packaged install and scheme reachability — DONE

**Gaps closed:** B1, B2, B3, B4 · **Severity:** S1 · **Effort:** M · **Depends on:** —

> **DONE.** Delivered against a real `net install`, not a model of one. What
> shipped, and where this plan was wrong:
>
> * **TR-05.1** landed, but *not* as written. Appending the install root and
>   its letter subdirectories to `allowed` was built and measured to be
>   exploitable: `allowed` also governs the caller-controlled CWD candidate,
>   so a symlink named `s2color.scheme` in the working directory would reach
>   any file in `PLUS/s` — reopening BUG-51 for exactly the fourteen names the
>   change was meant to help. The shipped version adds no directory to
>   `allowed` at all; it checks one computed path against its own realpath'd
>   directory, after the candidate loop.
> * **TR-05.2 was NOT built, deliberately.** Passing a `findfile`-resolved
>   absolute path into the spec looked robust and is not: `findfile` returns
>   only the *first* adopath hit and `.` precedes `PLUS`, so a stray
>   `s2color.scheme` in the working directory would silently win for every
>   graph; and it would have the renderer accept an arbitrary absolute path
>   from the spec, bypassing the containment checks entirely. The renderer-side
>   fix needs no `dash.ado` change and keeps every guard.
> * **TR-05.3** landed, with its premise corrected: `findfile` *does* search
>   `PLUS/py`, so the wrong hardcoded paths were never reached by a real user.
>   They were removed for the failure mode they produced when reached — an
>   unguarded path handed to `runpy`.
> * **TR-05.4**'s mechanism was wrong (the literal suppresses nothing; the
>   parent has already warned) and its conclusion right (the generated app is
>   silent). Fixed by emitting the provenance and a notice naming the
>   *requested* scheme. A second, unrecorded defect was found and fixed here:
>   `_FALLBACK_PROPS` differed from s2color in twelve public attributes while
>   claiming to mirror it.
> * **TR-05.5** is left to WP-17, which owns the `scheme()` policy. Escalating
>   to an error now would have made every installed build fail outright, since
>   the *default* scheme was among the fourteen that could not resolve. The
>   crux question was measured: Python `UserWarning`s **do** reach the Stata
>   console (and survive `quietly`, though not `capture`), so the current
>   behaviour is loud — just raw. [WP-30 P1.26a, commit dd7c165: notes now take twoway's `(note: …)` channel; UserWarnings no longer reach the console raw]
> * **TR-05.6** landed with its premise corrected — see GAPS B4. `v 2` was
>   wrong twice over.
> * **TR-05.7** closed as a documented limitation, with its rationale
>   corrected: the shipped schemes are *shadowed*, not invisible, because
>   `scheme.class` falls back to a bare `<name>.scheme`.
> * **Not in this plan at all:** `theme()` was the one user string interpolated
>   into the master spec unescaped, giving `r(7102)` and a Python traceback for
>   a Windows-style path. Fixed under rule 16.
>
> New tests: `test/test_installed_layout.py` (52 cases), `test_pkg_metadata.py`
> (13), `test_scheme_fallback_provenance.py` (9), `test_render_locate.cscript`
> (LOC-01..09, runner #31), `test_theme_escaping.cscript` (THM-01..09,
> runner #32).

> **Mutation-checked by WP-24** (24sep2026, `a2c7502`).  Each fix was
> reverted on a copy of the tree; nine reverts left the committed suite
> green and each now fails a new test: the tamper warning removed
> (test_installed_layout.py INST-07, strengthened), the locator's failure
> branch silenced or its beside-dash.ado candidate returned unconfirmed
> (test_render_locate.cscript LOC-10, LOC-11), `dash serve` announcing a
> server before it failed (LOC-12, test_env_guards.cscript ENV-17), the
> served app's fallback notice removed or naming s2color
> (test_scheme_fallback_provenance.py FBP-10/11, FBP-06), and B3's
> limitation paragraph deleted (INST-18).  AC-05.1 had only a model of an
> install: LOC-13..16 run a real `net install` into a scratch PLUS, and
> INST-01/02/12 cover all twenty shipped schemes, not fourteen.  AC-05.4
> (adoupdate) is held only by reading dash.pkg.

> **User story.** As a user who installed `dash` with `net install`, I want
> `scheme(stcolor)` to give me stcolor — not a fallback that looks like
> nothing Stata ships.

### Business requirements

- **BR-05.1** A `net install`ed package resolves all 14 schemes.
- **BR-05.2** A scheme that cannot be resolved must fail loudly, in both
  render modes.
- **BR-05.3** The package must be discoverable by `adoupdate`.

### Technical requirements

Stata routes `f schemes/<name>.scheme` to `<root>/<first letter>/<name>.scheme`
and `f dash_render.py` to `<root>/py/dash_render.py`. Two fixes, and both
should land:

- **TR-05.1 (minimal, self-contained).** Extend `SchemeParser._resolve_path`
  (`dash_render.py:1690-1752`) to try the installed letter layout: from
  `<root>/py/dash_render.py`, compute `root = dirname(dirname(__file__))` and
  add the candidate `<root>/<name[0]>/<name>.scheme`. Add `<root>` and its
  letter subdirectories to the `allowed` list so the existing abspath and
  realpath containment checks (`:1719-1751`) still apply — **do not weaken
  them**; they are correct and were verified against symlink escape.
- **TR-05.2 (robust).** Have `dash.ado` resolve the scheme with `findfile`
  (which already locates `plus/s/s2color.scheme` successfully) and pass the
  resolved absolute path into the spec as `build_options.scheme_path`. The
  renderer prefers that path when present. This removes the dependency on
  guessing Stata's layout.
- **TR-05.3** Correct the three hardcoded renderer fallbacks at
  `dash.ado:1747`, `:2480` and `:2621` — they compute
  `` `c(sysdir_plus)'d/dash_render.py `` but the file installs to `py/`.
- **TR-05.4** Stop the server path from swallowing the fallback warning:
  `is_fallback` is hardcoded `False` at `dash_render.py:12412-12431`, so a
  served dashboard built on the fallback says nothing at all.
- **TR-05.5** Escalate an unresolvable scheme from `UserWarning` to an error
  when the name was explicitly requested (see WP-17 for the full `scheme()`
  policy).
- **TR-05.6** Add `v 2` and `d Distribution-Date: <date>` to `dash.pkg`, and
  sync its version line — it says `1.0.0 25mar2026` while `dash.ado` and
  `dash_parse.mata` declare `2.0 27mar2026`.
- **TR-05.7** (B3) Record as a known limitation that schemes install as bare
  `<name>.scheme` into shared PLUS letter directories: they are invisible to
  Stata's own `set scheme` and can collide with other packages. A rename to
  `dash_<name>.scheme` would fix both but breaks `scheme()` name compatibility
  — decide explicitly and document the decision.

### Acceptance criteria

- **AC-05.1** After a real `net install` into a clean directory,
  `dash scatter mpg weight, name(g1) scheme(s1color)` then `dash build`
  produces a dashboard whose colours are s1color's, with **no** fallback
  warning.
- **AC-05.2** All 14 schemes resolve from the installed copy.
- **AC-05.3** `scheme(nosuchscheme)` fails loudly in both modes.
- **AC-05.4** `adoupdate` detects a newer package.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Integration | new `test_net_install.py` — **the gate this package exists for** | Build a package from `stata.toc`+`dash.pkg`, `net install` into a temp PLUS, then load the installed `dash_render.py` and assert `resolve_or_fallback(n).is_fallback is False` for all 14 |
| Cert | new `test_installed_render.cscript` | From the installed copy, render one dashboard per scheme and assert no fallback warning in the log |
| Unit | `test_scheme.py` | `_resolve_path` finds a scheme in the letter layout; still rejects `../../../etc/passwd.scheme`, an absolute path outside the allowed set, and a symlink escape |
| Unit | `test_server.py` | `is_fallback` is propagated, not hardcoded |
| Regression | `BUGS.md` entry for B1 | Written first, failing at `187a786` |

---

## WP-06 · `dash_setup` tells the truth — DONE

**Gaps closed:** J1, J2, J6 (all but rollback) · **Severity:** S1 · **Effort:** S · **Depends on:** —

> **DONE**, and the plan understated it. TR-06.1's premise — "prints an error
> and does not exit" — is true, but the branch was never reached:
> `_dash_pyver_ok` returned 1 for every input when called under the
> `version 16.0` that `dash_setup` declares, because `return scalar` plus
> `exit` inside its `forvalues` took effect there. The comparator was correct
> from a cscript, which is why fourteen existing cases passed while the
> production path was broken. Fixed by deciding once and returning after the
> loop, plus seven cases in the calling context the tests were missing.
>
> * **TR-06.1** landed as a failure/warning accumulator and a separate
>   `_dash_setup_summary`. Separate on purpose: while the banner was four
>   inline `display` lines the requirement could not be tested without
>   pip-installing into the user's environment.
> * **TR-06.2** landed for the install path. The upgrade path was declined on
>   purpose — an importable package below its minimum is reported as unmet
>   with the exact command, not upgraded behind the user's back. AC-06.2
>   allows either.
> * **TR-06.3** landed as `_dash_setup_gate`, four verdicts instead of two.
>   `_dash_pyver_ok` is the fallback, not a replacement: measured against
>   `packaging` it disagrees on every pre/post-release form, so it may report
>   `below` but never `ok`.
> * **TR-06.4..TR-06.7, TR-06.9** landed. Measured: a bare `syntax` gives
>   r(101), not r(198).
> * **TR-06.8** landed, and asks the RENDERER rather than `findfile` —
>   `findfile s2color.scheme` succeeds on exactly the install where the
>   renderer can read none, so a findfile check would have passed on the tree
>   it exists to catch.
> * **Not addressed:** rollback (J6). Still open.
>
> New: `test/test_setup_honesty.cscript` (HON-01..18, runner #33), plus seven
> version-context cases in `test_setup_python_gate.cscript`.

> **Mutation-checked by WP-24** (24sep2026, `a2c7502`).  Nine reverts
> left the committed suite green -- nothing ran `dash_setup` itself -- and
> each now fails a case of test_setup_honesty.cscript HON-19..25, which run
> it with pip replaced by a recorder: a Python below the minimum counted
> (HON-19), a package below its minimum reported (HON-20), pip's output
> shown and nothing called OK without packaging (HON-21), `pkg>=min` and
> the `--user` retry handed to pip (HON-22), and the check of its own files
> (HON-23..25).  test_program_coverage.cscript PC-15..26 run it end to end,
> in a sandbox that starts no process.  TR-06.9 is comments only.

> **User story.** As a new user, if setup did not fully succeed I want to be
> told that — not to see "All dependencies are satisfied" and discover the
> problem later inside a Python traceback.

### Business requirements

- **BR-06.1** The summary must reflect what actually happened.
- **BR-06.2** A dependency below its declared minimum must be upgraded or
  reported as unmet.

### Technical requirements

- **TR-06.1** Introduce a failure accumulator (`local _setup_failed`) set by
  every failing branch, and branch the summary at `dash_setup.ado:198-201` on
  it. Today the below-minimum Python branch at `:53-57` prints an error and
  **does not exit**, so control falls through to the success banner.
- **TR-06.2** Pass the version specifier to pip. `:123` issues
  `pip install bokeh`; the minimums declared at `:106-110` never reach it, and
  no `--upgrade` is ever attempted. A package present but below minimum is
  warned about and left in place.
- **TR-06.3** Fix the "OK (version unknown)" masking at `:169-171`: when
  `packaging` is unavailable the code prints OK for every package even though
  `_dash_pkg_version` already retrieved the real version. Compare
  lexicographically as a fallback, or report "unverified" — never "OK".
- **TR-06.4** Wrap the `Version(...)` call at `:155-159` in `capture`; an
  unparseable version string currently kills `dash_setup` with `r(7102)`.
- **TR-06.5** Add a `syntax` line (the program has none at `:15-17`, so
  `dash_setup, garbage(1)` runs silently).
- **TR-06.6** Retry a permission-denied install with `--user` (`:120-127`).
- **TR-06.7** Surface pip's own output on failure — it is discarded by
  `capture_output=True` at `:72-73`, so a `packaging` failure gives no reason.
- **TR-06.8** Have `dash_setup` verify that `dash_render.py` and the schemes
  are installed and findable — this is why WP-05's defect survived a
  "successful" setup.
- **TR-06.9** Renumber the two sections both labelled "3" (`:90`, `:175`).

### Acceptance criteria

- **AC-06.1** With Python below 3.8, `dash_setup` exits non-zero and never
  prints "All dependencies are satisfied".
- **AC-06.2** With `bokeh 2.4` pre-installed, setup upgrades it or reports it
  as unmet.
- **AC-06.3** With `packaging` unavailable, no package is reported "OK".
- **AC-06.4** `dash_setup` reports a missing `dash_render.py` or unreachable
  schemes directory.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | `test_setup_python_gate.cscript` — extend | Below-minimum Python sets the failure flag and suppresses the success banner |
| Unit | new `test_setup_logic.py` | `_dash_pyver_ok` truth table (already correct — lock it in); the failure accumulator; the version-specifier string handed to pip |
| Integration | new `test_setup_scenarios.py`, venv-based | Below-minimum package upgraded; `packaging` absent → no false OK; unparseable version does not abort |
| Regression | `BUGS.md` entry for J1 | Written first |

---

## WP-07 · Environment verification at entry — DONE

**Gaps closed:** J3, J4, J5 · **Severity:** S2 · **Effort:** S · **Depends on:** —

> **DONE**, with one technical requirement measured to be wrong.
>
> * **TR-07.1, TR-07.2, TR-07.3, TR-07.5** landed as written.
> * **TR-07.4 was NOT implemented as written, because it is a regression.**
>   The return code of the Mata `run` does not carry the question: a benign
>   second load returns r(3000), the same code as a total compile failure, so
>   refusing to run on a non-zero code breaks every user — and every cscript
>   here — that loads `dash_parse.mata` before `dash.ado`. What landed instead
>   checks whether the functions dash calls are present and, on a miss, loads
>   the library itself before re-checking and reporting.
> * A first attempt that checked presence and *vetoed* also failed, against
>   `test_examples_run.cscript`: the library is routinely absent at the entry
>   to a command through no fault of the install. Both wrong turns are
>   recorded in BUGS.md, with the measurements.
> * **AC-07.3** is met by the repair path: all three staged broken trees now
>   give a dash-authored message and r(198) instead of `_dash_check_utf8() not
>   found` — or, for the partial break, rc 0 and "graph registered".
> * The test-plan row "extend `test_mata_autoload.cscript` — a failed compile
>   is reported at load time" is deliberately not done: reporting at load time
>   is what the rc check would have been, and it is wrong for the reason
>   above. The reporting happens at entry, covered by ENV-08..11.
>
> New: `test/test_env_guards.cscript` (ENV-01..16, runner #34), plus a new
> class in `test_cscript_hygiene.py` covering the two shipped `.ado` files.

> **Mutation-checked by WP-24** (24sep2026, `a2c7502`).  Three reverts
> left the committed suite green and each now fails a new case: the Python
> guard moved after the renderer (test_env_guards.cscript ENV-19), an
> unrepairable library not reported (ENV-20), and the library check cut to
> one function (ENV-21); ENV-17 also catches WP-05's revert, `dash serve`
> announcing a server before the guard stops it.  AC-07.3 held only in a
> fresh session: a partly compiled library already in memory passed the
> check, which asked for one function, and its list lacked
> `_dash_path_badchar`.  WP-24 fixed both -- every function dash.ado calls
> is checked, a part library is repaired from the file, and one that cannot
> be is refused by name (ENV-22, ENV-23, test_mata_library_guard.cscript
> MLG-01..06, test_program_coverage.cscript PC-30).

> **User story.** As a user without Python linked, I want `dash` to tell me to
> run `dash_setup` — the way it already does for `jsonio` — instead of
> handing me a raw Stata Python error.

### Business requirements

- **BR-07.1** Every external dependency is verified before use, with a
  message naming the remedy (CLAUDE.md rule 15). [WP-30 P1.32, commit 9dc17da: met for the Python version and numpy, pandas and bokeh; BR-07.2 still holds]
- **BR-07.2** Python availability is probed without running Python.

### Technical requirements

- **TR-07.1** Add a `_dash_require_python` helper that probes `c(python_exec)`
  and errors with "run dash_setup" guidance. `c(python_exec)` appears
  **nowhere** in `dash.ado` or `dash_setup.ado` today.
- **TR-07.2** Call it from `_dash_do_render` (`dash.ado:141`), `_dash_build`
  and `_dash_serve` (`:2651`), which all reach `python:` cold. Model the
  message on the existing `jsonio` check at `:1684` / `:2245`, which is good.
- **TR-07.3** Replace `capture python query` at `dash_setup.ado:32` with the
  `c(python_exec)` probe. Keep `python query` only for *reporting* the version
  after availability is established.
- **TR-07.4** Check the return code of the Mata `run` at `dash.ado:55`, which
  is currently discarded. A failed compile surfaces much later as
  `_dash_split_segs() not found`, r(3499) — a message naming an internal
  function.
- **TR-07.5** Extend `test_cscript_hygiene.py:12-14` — which enforces the
  `c(python_exec)` rule for `.cscript` files only — to cover `dash.ado` and
  `dash_setup.ado`, so this cannot regress.

### Acceptance criteria

- **AC-07.1** With no Python linked, `dash scatter mpg weight` exits 198
  naming `dash_setup`.
- **AC-07.2** No `python query` or `python: import` is used as an availability
  probe anywhere.
- **AC-07.3** A deliberately broken `dash_parse.mata` produces a clear
  load-time error.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | new `test_env_guards.cscript` | The Python guard fires with the right message and rc |
| Static | `test_cscript_hygiene.py` extension | No `python query` / `python: import` availability probe in either `.ado` |
| Cert | `test_mata_autoload.cscript` — extend | A failed Mata compile is reported at load time |

---

## WP-08 · Input hardening — UTF-8, JSON escaping, paths — DONE

**Gaps closed:** A9, E6, E7 · **Severity:** S2 · **Effort:** M · **Depends on:** —

> **DONE.** All eight technical requirements, with two deviations stated.
>
> * **TR-08.1** rewritten to RFC 3629 s.4 and verified by DIFFERENTIAL TEST
>   against Python's own decoder — 41,976 sequences, zero mismatches — rather
>   than against a hand-written table, which would only check that two
>   readings of the RFC agree. 2,245 of those are committed as
>   `test/fixtures/utf8_cases.txt`.
> * **TR-08.2** decided: C0 bytes are **well-formed UTF-8 and stay accepted**
>   at the gate, and are escaped by TR-08.3 instead. Rejecting them would
>   refuse a title with a control character pasted from a web page, where the
>   user story asks for a correct dashboard. `char(0)` is unreachable — a
>   Stata string cannot carry one.
> * **TR-08.3** done, and **AC-08.2 is met by the other half of its own
>   sentence**: the build now *succeeds* with the character escaped, rather
>   than giving a `dash` error. The user story allows either; this one keeps
>   the value.
> * **TR-08.4, TR-08.6, TR-08.7, TR-08.8** done as written. TR-08.6 was the
>   sharpest: `saving("…a\b.html")` returned rc 0 and wrote to `a\\b.html`,
>   so the command reported success and put the file somewhere else.
> * **TR-08.5** was already done, under WP-05 — `theme()` is escaped.
> * A detail worth keeping: `_dash_validate_path` cannot write through its
>   argument (they are values, not macro names), so it publishes the
>   normalised path as `_dash_vpath` and the three call sites read it back.
>
> New: `test/test_utf8_validation.cscript` (UTF-01..12, runner #35),
> `test/test_json_escaping.cscript` (JSE-01..10, runner #36),
> `test_path_validation.cscript` PV-13..19, `test_adversarial.cscript`
> P8-86..89, `test/fixtures/utf8_cases.txt` and `scripts/gen_utf8_cases.py`.
>
> *Correction, found by WP-23:* TR-08.8's `.py` requirement for server-mode
> output (7ddbc08) also caught `_dash_serve`'s deliberately extension-less
> tempfile, so every `dash serve` aborted with r(7102) until WP-23 fixed the
> launch route (GAPS.md C1, C2; BUGS.md).

> **Mutation-checked by WP-24** (24sep2026, `a2c7502`).  Five reverts left
> the committed suite green and each now fails a new case: a wrong escape
> digit for 0x10 (test_json_escaping.cscript JSE-38, all 31 control bytes
> round-tripped through Python's json), a caller that does not read the
> validated path back (JSE-39..41, one per route), and the refusal's
> message changed (test_utf8_validation.cscript UTF-13).  JSE-03/04 could
> never fail -- their needles were control bytes Stata drops from a
> do-file -- and compare the whole escaped text now.  Two things did not
> hold, and WP-24 fixed both: `dash build, saving() server` still refused
> any `..` in the path, so `my..report.py` was refused where
> `my..report.html` was built (test_path_validation.cscript PV-20), and a
> double quote in saving() gave r(132) instead of dash's message (PV-21).

> **User story.** As a user pasting text from the web into `title()`, I want
> either a clean `dash` error or a correct dashboard — never a raw Python
> traceback.

### Business requirements

- **BR-08.1** All text input is validated as well-formed UTF-8 before it
  leaves Stata (CLAUDE.md rule 16).
- **BR-08.2** The spec document is always valid JSON.
- **BR-08.3** Path validation is applied consistently and does not reject
  legitimate paths.

### Technical requirements

- **TR-08.1** Tighten `_is_utf8` (`dash_parse.mata:90-109`) to enforce the
  RFC 3629 second-byte ranges per lead byte. It currently checks only the
  lead-byte range and that continuations are `0x80-0xBF`, so overlong
  encodings (`E0 80 AF`, `E0 9F BF`, `F0 80 80 80`), UTF-16 surrogates
  (`ED A0 80`, `ED B0 80`) and codepoints above U+10FFFF (`F4 90 80 80`) all
  pass — and then crash the renderer with `r(7102)`.
- **TR-08.2** Decide and enforce a policy for NUL and C0 control bytes, which
  also pass today.
- **TR-08.3** Complete `_dash_json_str` (`dash.ado:224-232`): it escapes only
  `\`, `"`, TAB, LF, CR. `\b` (8), `\f` (12) and every other C0 byte must be
  `\uXXXX`-escaped — they are illegal raw in JSON and currently produce a
  `JSONDecodeError` instead of a Stata diagnostic.
- **TR-08.4** Call `_dash_check_utf8` from `_dash_kpi`, `_dash_build`,
  `_dash_prepare_spec`, `_dash_serve` and `_dash_serve_spec`. It is called
  once today, at `dash.ado:1385`, so KPI titles, build titles/subtitles,
  `tabs()` and filter labels have no UTF-8 gate at all.
- **TR-08.5** Escape `theme()` at `dash.ado:2343` — the one build option
  written to JSON raw while `title`, `subtitle`, `tabs`, `scheme` and `filter`
  all go through `_dash_json_str`.
- **TR-08.6** Un-escape the `saving()` path extracted at `dash.ado:1602-1607`.
  `_dash_json_str` doubles backslashes and the extractor slices the raw JSON
  text and uses it as a filesystem path — **this breaks every Windows
  `saving()` path on the immediate-render route**.
- **TR-08.7** Tighten `_dash_validate_path` (`:157`): reject a leading `-`
  (`shell open "-e.html"` parses the target as a flag), expand or reject `~`,
  and narrow the `..` rule so a legitimate `my..report.html` is accepted.
  Consider an opt-in directory confinement — any absolute path is writable
  today.
- **TR-08.8** Validate `output_path` in `dash_render.py:main()`
  (`:16121-16157`), which has no validation when the renderer is invoked
  directly.

### Acceptance criteria

- **AC-08.1** Every encoding in the GAPS A9 table is rejected with a clean
  `r(198)` naming the problem.
- **AC-08.2** `title("bad" + char(1) + "title")` gives a `dash` error, not
  `r(7102)`.
- **AC-08.3** A Windows-style `saving("C:\dir\out.html")` writes to that path.
- **AC-08.4** `saving("my..report.html")` is accepted; `saving("-e.html")` is
  rejected.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Unit | new `test_utf8_validation.cscript` — **the gap L3 names** | Every byte sequence in the A9 table, positive and negative. Today's only two callers pass `""` |
| Unit | new `test_json_escaping.cscript` | All C0 bytes round-trip through `_dash_json_str` into parseable JSON |
| Cert | `test_path_validation.cscript` — extend | Leading `-`, `~`, `my..report.html`, absolute paths |
| Adversarial | `test_adversarial.cscript` — extend | Malformed UTF-8 and control bytes through `title()`, KPI `title()`, `tabs()`, filter `label()` |
| Regression | `BUGS.md` entries for A9, E6 | Written first |

---

# Milestone 2 — One renderer

## WP-09 · Server unification — table-driven dispatch — DONE

**Gaps closed:** D1, D7 · **Severity:** S1 · **Effort:** L · **Depends on:** WP-02

> **DONE.** All 38 plot types now dispatch through `GlyphMapper`; the
> `if/elif ptype` chain no longer draws anything itself.
>
> **TR-09.1's premise was measurably wrong**, and that shaped the work. This
> plan calls the job "cheaper than it looks ... the server simply does not
> call 37 of them". The second half was right — `grep` returned one name,
> `map_scatter`. The first was not. Comparing every branch against its mapper,
> and adversarially re-checking each claimed difference, found **132
> non-cosmetic differences across 37 types, 28 of them S1**. Calling the
> mappers was not a substitution: in several types the SERVER did something
> the mapper did not, and swapping would have lost it.
>
> Those became mapper fixes, which is the point — each is a bug in the SAVED
> dashboard that the comparison surfaced:
>
> * `map_area`, `map_rline`, `map_rarea` and `map_tsrline` joined their
>   points in dataset order. Bokeh connects points as given and Stata draws
>   along x, so every one of them drew a self-intersecting shape on unsorted
>   data. `map_line` and `map_connected` had always sorted.
> * `map_lowess`, `map_mspline`, `map_mband` and `map_fpfit` dropped the
>   plot's line options on their bail-out path, so `lwidth(thick)` was lost
>   whenever the curve could not be computed — which, with `statsmodels`
>   optional, is EVERY lowess layer on a machine without it.
> * `map_rbar` never called `_apply_line_opts` and ignored `bfcolor()`,
>   `blcolor()`, `lwidth()` and `lcolor()` entirely.
> * Server-mode `pci` read four variable names that `pci 20 3000 30 4000`
>   never sets, so it drew nothing at all. It now uses `map_pci_literal`,
>   as standalone always has.
>
> **TR-09.2** landed as three source builders — `_dash_layer_source`,
> `_dash_range_source`, `_dash_pc_source` — each de-duplicating its column
> list in the helper, so the `pc*` crash and the `pcscatter` no-draw are
> structurally impossible. **TR-09.3** and **TR-09.5** come free: the chain
> lower-cases through `_dash_add_glyph`, and the per-branch style literals
> went with the branches. **TR-09.4** warns on an unknown type.
> **AC-09.1**, **AC-09.2** and **AC-09.3** are met.
>
> Two things worth knowing for the next change here:
>
> * `graph_sources` feeds the filter snapshot AND the brush-to-KPI wiring,
>   and the latter skips any source without an `index` column — which a
>   mapper-built one has not got. Each swapped branch registers the layer
>   source as well as the mapper's, or those layers stop driving a brush.
>   `rscatter` and `pcscatter` additionally keep their `agg_sources` entry,
>   or their points freeze at the unfiltered values.
> * The three security tests that guarded the served `function` validator
>   read `ServerAppBuilder`'s own source, because the validator used to be
>   written there as string literals. It now lives in `map_function` and is
>   copied into the app whole, so those assertions found nothing and failed
>   on a change that removed no protection. They were repointed at the shared
>   implementation and at behaviour: six integer-power-bomb forms were
>   measured returning in under a second and drawing nothing, and the
>   keyword-argument escape test — which writes a marker file if the sandbox
>   is breached — still passes.
>
> Still divergent, pre-existing and unchanged by this work: `mlabel()` draws
> in the saved dashboard and not the served one for the common plot types.
> Measured identical at the previous commit and at this one, so it is not a
> regression; it stays on the inventory for WP-12's parity corpus.

## WP-10 · Server layer defects — DONE

**Gaps closed:** D2, D3, D5, D6 · **Severity:** S1 · **Effort:** M · **Depends on:** WP-09

> **DONE.** A sweep of all 38 plot types — bare, with `mlabel(foreign)` and
> with `hover(foreign)`, 114 comparisons — now reports **zero** differences
> between the two modes in glyphs, tooltips, marker labels and legend keys.
> It reported 114 before this work, and the roadmap's own account of which
> ones was out of date in both directions.
>
> **Four of the eight technical requirements were already met by WP-09.**
> Measured, not assumed: `pci` draws `[Segment]` in both modes (TR-10.1),
> `fpfitci` draws `[VArea, Line]` in both (TR-10.2), all four `pc*` types
> agree with a repeated y or x variable (TR-10.3), and `_MAX_EXPR_CHARS` is
> a single module constant (part of TR-10.8). They are pinned by
> `TestTheUnificationKeepsD2Closed`, so the next hand-written branch fails
> there rather than on a user's page.
>
> **WP-09 left a regression this found.** Once every type went through the
> mapper, the mapper drew each layer's `mlabel()` itself — and the generated
> app still ran its own "common mlabel block" over the top. Measured:
> `line`, `connected`, `dot`, `dropline` and `tsline` carried TWO LabelSets
> at the same coordinates when served; `lpoly`, `lpolyci`, `fpfit`,
> `fpfitci` and `mband` carried one where the saved dashboard carries none.
> The block is deleted, not narrowed. **This also corrects WP-09's closing
> note**, which carried forward an inventory item reading "`mlabel()` draws
> in the saved dashboard and not the served one". At WP-09's final commit
> the served dashboard drew MORE labels than the saved one, not fewer.
>
> **The defects that were real, and what each cost.**
>
> * **D3 — per-plot qualifiers (TR-10.5).** `plot.get('if_expr')` appeared
>   nowhere in the generated app. `dash.ado` promotes only a single
>   segment's qualifier to the graph level, so in
>   `dash (scatter mpg weight) (scatter mpg weight if foreign==1)` the
>   second layer's `if` was discarded: ten points served where five are
>   saved, no warning, nothing visibly wrong. A served KPI's own `if`/`in`
>   was ignored at all three computation sites — the initial build and both
>   recompute paths — so the card showed the unconditional number.
> * **D6 — the silent failures (TR-10.7).** The served app had no
>   equivalent of the saved renderer's empty-layer report. That is why every
>   D2 divergence was silent.
> * **D2 — hover (TR-10.4).** `HoverTool` was imported into the app and
>   never instantiated: the only tooltips a served figure had were the two
>   that `map_scatter` and `map_line` add for themselves. Bar, histogram,
>   area, dropline, every fit and every range type had none, and `hover()`
>   was ignored entirely. **The saved renderer had its own defect at the
>   same spot**: it built a comprehensive tool but cleared the per-layer
>   ones only when `hover()` was given, so a plain `dash scatter mpg weight`
>   carried two HoverTools with identical tooltips — and
>   `dash line mpg weight, hover(foreign)` carried NONE, because clearing
>   them then failed to find a renderer whose source held `foreign`.
> * **The legend, which the plan does not mention.** The served app keyed
>   every layer with the y-variable name. A served `lfitci` read "mpg"
>   twice where the saved one reads "95% CI" and "Fitted values" — there was
>   no way to tell the band from the line. It also built a Legend model for
>   `lowess`, `scatteri` and `pci` where the saved dashboard builds none.
>   Both now run `_dash_legend_key` / `_dash_legend_entries`.
> * **TR-10.8's remainder.** `layout(g1:0,0)` placed when saved and was
>   discarded when served — one spec, two parsers, one of which rejected a
>   zero index. A KPI's `fmt(%12.0fc)` was identical to `fmt(%12.0f)` when
>   served, and a card with no `fmt()` showed a different number of digits.
>   The legend used the scheme's tick-label size, 10pt, against the saved
>   dashboard's text size, 11pt; those differ for 13 of the 14 shipped
>   schemes. Under `layout(bs)` an item `tabs()` does not name was drawn
>   ABOVE the tabs, where `dash.sthlp` says below and where the other two
>   layouts put it.
>
> **Every fix is one implementation, not two.** Eleven module-level helpers
> are now copied into the generated app and called by the saved renderer as
> well: `_dash_qualified_frame`, `_validate_if_expr` (which replaces the
> app's own `_safe_g` whitelist), `_dash_layer_drew_anything`,
> `_dash_report_empty_layer`, `_dash_build_hover`, `_dash_hover_row`,
> `_dash_legend_key`, `_dash_legend_entries`, `_dash_placement_map`,
> `_dash_effective_kpi_fmt` and `_dash_format_kpi_value`. `GlyphMapper`
> gained `_carry_cols` and `_masked_index` so `map_bar`, `map_spike`,
> `map_dropline` and `map_rcap` carry the caller's other columns through
> their derived sources — which is what lets `hover()` reach them, in both
> modes.
>
> **AC-10.1 through AC-10.5 are met.** `test/test_server_layer_defects.py`
> holds 378 cases: 306 comparing the two modes, most parametrised over all
> 38 plot types, and 72 exercising the shared helpers directly, so a failure
> says which helper rather than which plot type.
>
> Two existing tests asserted the defects rather than the behaviour, and
> were corrected with the reason recorded in place:
> `test_server_legend.py::test_the_labels_name_the_series` required every
> legend key to contain "mpg" — true only while the app keyed all 38 types
> with the y variable, which is the very thing that file's opening
> paragraph calls "no way to tell the fit from the points"; and
> `test_varlist_expansion.py`'s golden hash for the saved dashboard moved,
> because the duplicate HoverTool is gone. That second change was diffed
> token by token against HEAD before re-baselining: the whole normalised
> difference is one `HoverTool` object and its id in the figure's tools
> list, and nothing else.
>
> **Found and NOT fixed here, because it is a feature and not a divergence
> in this package's sense:** the generated server app has no date handling
> at all. `_load_spec_and_data` coerces every non-string column with
> `pd.to_numeric`, so a `%td` variable is served as a raw Stata day number
> on a linear axis where the saved dashboard draws a `DatetimeAxis` and
> formats the tooltip as a date. Measured on a four-row `%td` fixture. It is
> in no GAPS.md entry; `REMAINING.md` has it under "08-04 ... Remaining,
> item 1", whose companion complaint — `numeric_formats 0` — WP-10 DID
> close: the dataset's numeric display formats are resolved into the app as
> `_NUM_FORMATS` and the served tooltip uses them. The date half is
> recorded in `BUGS.md` and belongs to a package of its own.
>
> **One behaviour change outside the server:** routing
> `_apply_graph_filter` through the shared reader means the saved renderer
> now accepts Stata's `~=` in a qualifier, which the served one always did.
>
> **User story.** As a user of `dash serve`, I want the served dashboard to be
> the dashboard I would have got from `dash build`.

### Business requirements

- **BR-10.1** A served dashboard is model-for-model equivalent to the saved
  one, except where `dash.sthlp` documents a difference.
- **BR-10.2** Any layer that draws nothing must say so, in both modes.

### Technical requirements

Most of these dissolve once WP-09 lands; the rest are explicit work:

- **TR-10.1** `pci` (D2) — the server reads `y1var/x1var/y2var/x2var` at
  `:14781-14796` while `dash.ado:1164-1212` emits a literal `"values"` array,
  so the gate is never true. Delegating to `map_pci_literal` fixes it.
  Note `map_pci` (`:5516`) is **dead** and must not be the delegation target
  (see WP-26).
- **TR-10.2** `fpfitci` (D2) — `:14253-14263` is a verbatim copy of the
  `fpfit` branch and draws no band. Delegating to `map_fpfitci` fixes it.
- **TR-10.3** `pc*` shared-variable cases (D2) — fixed by TR-09.2's shared
  column helper.
- **TR-10.4** Hover (D2) — build the comprehensive `HoverTool` the standalone
  path builds at `:10192-10304`, honouring `graph_options["hover"]`, Stata
  display formats and variable labels. `HoverTool` is imported at `:12879` and
  never instantiated.
- **TR-10.5** Per-plot and KPI qualifiers (D3) — there is no
  `plot.get('if_expr')` past `:12700`. Read them, and apply KPI `if`/`in` at
  `:15331, 15645, 15694`. Then correct the now-stale comment at
  `dash.ado:1484`.
- **TR-10.6** `mlabel()` on range types (D5) — `:14897-14901` skips the mlabel
  block for every range type and 15 others; the standalone path wires all 13
  claimed types.
- **TR-10.7** "Drew nothing" warning (D6) — port the standalone guard at
  `:10078-10091` into the generated app. This is what made D2 silent.
- **TR-10.8** Align the remaining D7 divergences: `layout()` indexing
  (0-based standalone at `:11126-11128`, 1-based server at `:15795`), KPI
  `fmt()` (`:13665-13682` ignores the `c` suffix and the `%9.0g` default),
  legend text size (`text_font_size` vs `tick_label_font_size` at `:9067`
  / `:12660`), tabs placement under `layout(bs)` (`:10888-10889`), and the
  duplicated `_MAX_EXPR_CHARS` literal at `:14872`.

### Acceptance criteria

- **AC-10.1** `pci`, `fpfitci`, and all four `pc*` types with a repeated
  variable produce identical models in both modes.
- **AC-10.2** `hover(foreign)` adds `foreign` to the served tooltip.
- **AC-10.3** `bar`, `histogram` and `area` have hover tools in server mode.
- **AC-10.4** A served KPI with `if foreign==1` shows the conditional value.
- **AC-10.5** A served layer that draws nothing emits a warning.

### Test plan

Covered by WP-12's expanded parity corpus plus targeted regression tests in
`test_server.py` for each of D2's four measured divergences. Each gets a
`BUGS.md` entry written first.

---

## WP-11 · Server facets — DONE

**Gaps closed:** D4 · **Severity:** S1 · **Effort:** M · **Depends on:** WP-09

> **DONE.** All 38 plot types under `by(foreign)` — every panel compared,
> glyph for glyph, row for row, hover, labels and legend — report **zero**
> differences between the modes. Before this work every one of the 38
> differed: the twenty D4 names served empty panels, and the eighteen that
> drew had no hover tool, a visible Bokeh-default legend at 13px keyed
> "lfit mpg", no band for `lpolyci` or `fpfitci`, and `fpfit` at 200 points
> where the saved dashboard draws five.
>
> **TR-11.1 went further than deleting the two chains.** The per-graph loop
> body is now one emitted function, `_dash_figure_for`, called once per
> graph or once per panel; and the 38 per-type branches WP-09 left standing
> — each the same eleven lines with a different name in them, measured by
> normalising the bodies: ten distinct texts, all by family — are one
> dispatch, `_dash_draw_layer`, in the saved renderer's order. The old
> facet block is deleted, not narrowed.
>
> **Three defects the plan does not mention were found by measuring along
> the way, and fixed here because facets ride the same code.**
>
> * **The saved dashboard grouped the unqualified frame.** The reverse of
>   D3: `if price > 4500, by(foreign)` faceted every observation when saved
>   and the qualified ones when served (BUG-36 had fixed the server). Both
>   `_expand_by_groups` call sites now group `_apply_graph_filter(g)`.
> * **WP-09 broke live recompute for every computed layer.** Once fits went
>   through the mapper, nothing registered them for recompute; their
>   mapper-built sources sat in `graph_sources`, where the raw-source refresh
>   "restored" `x`/`y` by the filtered row index. Measured after one filter
>   move: a 100-point `lfit` became ten points of the OLD line; a served
>   `line` and `area` were drawn in dataset order, crossing themselves. A
>   read-only audit of the fifteen `_compute_<type>` twins the old recompute
>   dispatched to found `lowess` returning `x`/`y` for a glyph bound to
>   `x_lw`/`y_lw`, `lfitci`/`qfitci` ignoring `n()`, no registration site
>   writing the plot options, and five branches unreachable. Rather than
>   repair fifteen twins, a mapper-built layer is now **redrawn by the same
>   mapper on the filtered frame** and the fresh data copied onto the live
>   sources — one text, so nothing can drift. Verified for seventeen types,
>   per facet, and for a qualified layer against the saved renderer run on
>   the filtered rows. The twins stay emitted, uncalled, for WP-26.
> * **A served `histogram` ignored its qualifier**: the univariate path of
>   `_dash_layer_source` handed it the graph's initial, unqualified source.
>   Three bars where the saved dashboard draws two.
>
> **TR-11.2:** `_dash_parse_by` is one parser for both modes (it also holds
> the one copy of the injection check both had), tokenises respecting
> parentheses and quotes so `holes(1 3)` is one option, accepts Stata's
> abbreviations for the three it implements, and names every other
> sub-option in one warning. `cols(#)` was also **inert when served** — the
> grid read a `by_cols` graph option nothing writes and never the value it
> had just parsed; it uses it now, with the saved renderer's fallback rule.
> `dash.sthlp` says which sub-options are implemented and what happens to
> the rest.
>
> **AC-11.1 and AC-11.2 are met.** `test/test_server_facets.py`: 124 cases
> (every type under `by()`, total, two variables, missing, linked, qualifier
> in both modes, recompute against the saved-on-filtered-rows oracle, the
> parser, one-dispatch source guards, `cols()`); six `by()` entries in the
> standing parity corpus; `test/test_by_suboptions.cscript` (BYS-01..06)
> reads the warning back out of the Stata log. Fourteen existing tests
> asserted the emitted TEXT of the old chains (`_compute_lfitci`,
> `atype == 'lfitci'`, `_by_q_df`, `opts.get('bwidth'`, `elif ptype ==
> 'dot':`) and were restated as behaviour in place, each with the reason.
>
> **A fourth, found by the certification suite itself:** `dash_setup`'s
> scheme probe installed `warnings.simplefilter("ignore")` in Stata's
> embedded interpreter and never removed it, so a user who ran `dash_setup`
> and then `dash` in one session saw none of dash's reports. Measured: two
> warning lines from one render before, zero after. The new cert script
> could not see the warning it was written to read because
> `test_setup_honesty.cscript` runs the probe four scripts earlier in the
> same session. The filters are now saved and restored around the probe;
> BYS-06 pins it.
>
> **Not fixed, recorded:** a `by()` panel of an integer-valued float is
> titled "3.0" in both modes where Stata says 3 (BUGS.md).
>
> **User story.** As a user, I want `by(foreign)` to work in server mode for
> every plot type it works for in a saved dashboard.

### Business requirements

- **BR-11.1** `by()` works for every plot type in both render modes.
- **BR-11.2** A `by()` sub-option that is not implemented is named, not
  discarded.

### Technical requirements

- **TR-11.1** Delete the two near-duplicate reduced chains at
  `dash_render.py:15144-15212` and `:15245-15315` and route facet and "Total"
  panels through WP-09's single dispatch. They handle 18 of 38 types today;
  the other 20 fall off the end of the `elif` with no `else` and no warning.
- **TR-11.2** Extend `_parse_by_raw` (`:8669-8701`) to warn on `by()`
  sub-options it does not implement. It regex-matches `cols()`, `total` and
  `missing` and silently discards everything else — Stata's `by()` also takes
  `rows()`, `holes()`, `iscale()`, `compact`, `colfirst`, `norescale`,
  `yrescale`, `xrescale`, `noixlabel`, `noiylabel`, `noixtick`, `noiytick`,
  `imargin()`, `ixaxes`, `iyaxes`, `altshowyvars` and its own
  `title()`/`note()`/`legend()`. (Implementing them is WP-14/WP-22; warning is
  here.)

### Acceptance criteria

- **AC-11.1** All 38 plot types render under `by()` in server mode.
- **AC-11.2** An unimplemented `by()` sub-option produces a named warning.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Parity | `test_mode_parity.py` | A `by()` corpus entry for every plot type |
| Unit | `test_server.py` | Only one facet dispatch exists in the generated source |
| Cert | new `test_by_suboptions.cscript` | Unimplemented sub-options are named |

---

## WP-12 · The parity guard earns its name — DONE

**Gaps closed:** D8 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-09, WP-10, WP-11

> **User story.** As a maintainer, I want the next divergence between the two
> renderers to fail a test rather than reach a user.

### What was measured before any code changed

The plan's premise was that the corpus covered 17 of 38 types. On this
branch it covered 21 (WP-11 had added six `by()` entries); the 17 missing
were `fpfit fpfitci lowess pcarrow pcbarrow pci pcscatter qfit qfitci rbar
rcap rconnected rline rscatter rspike tsline tsrline`. No entry set
`link()`, `filter()`, `tabs()` or a KPI. The profile collected seven glyph
style properties, a few annotation fields and the figure chrome -- not the
rows a glyph draws, its coordinates, the tools, the tooltips, the legend,
the axes, the widgets, the KPI cards, or where anything sits.

A profile that collects all of that, run over all 38 types bare and over
every cross-cutting feature, found **twelve divergences the four earlier
packages had not**, on the day it was written:

| Divergence | Saved | Served |
|---|---|---|
| Legend click policy (36 of 38 types) | Bokeh default | `hide` |
| `legend(position(6) rows(1))` | below, horizontal | top-right, vertical; `order()`, `size()`, `ring(0)`, one-series `on` ignored |
| Histogram / kdensity y-axis title | none | the variable (Stata: "Density" / "kdensity mpg") |
| `xlabel(2000(1000)4000)` | FixedTicker | ignored (a 14-line parser) |
| `yaxis(2)` | second axis | none |
| `colorvar(foreign)` | coloured by the variable | scheme colour |
| `lfitci` under `set level 90` | 90% band | 95% band keyed "90% CI" |
| Dropdown option values | `0`, `1` | `0.0`, `1.0` |
| Threshold slider title | `price ≥` | `price` |
| Filter widget bounds under `by()` | first facet's five rows | whole dataset |
| KPI card position | before every graph | registry order |
| Title header | two classed Divs | one classless Div |
| Faceted graph in `tabs()` | panels flattened | nested, honouring `cols()` |

Every one was fixed as one implementation with two callers (BUGS.md has an
entry per row). The saved renderer was wrong in four of them: the widget
bounds and categories and the JavaScript snapshot came from the first
graph's source (one facet under `by()`), KPIs were forced before graphs
whatever the registry said, facets in tabs ignored `cols()`, and neither
mode titled a histogram's axes as Stata does (measured by SVG export:
"Density"/"Percent"/"Frequency"/"Fraction" and the variable's label).

### Technical requirements, as delivered

- **TR-12.1** The corpus has a bare entry for every plot type, and
  `TestTheCorpusIsComplete` derives the list from the code
  (`_dash_plot_type_names`, over the dispatch tables and the new
  `_DASH_LITERAL_TYPES`) and cross-checks it against `dash.ado`'s
  Supported: text and the Mata abbreviation table. `ALL_TYPES` in
  `test_server_layer_defects.py` is derived from the same function.
- **TR-12.2** Entries for `by()` (total, cols, two variables, an unimplemented
  sub-option, a graph-level `if`, mlabel and hover per panel), `link()` (a
  pair, `_all`, a faceted member, hover and mlabel on a linked graph),
  `filter()` (all three types, `label()`, `filterposition(left)`, on a
  linked pair, on a faceted graph), `tabs()` (two tabs, an unassigned item, a
  faceted graph, a KPI), KPIs (fmt, no fmt, `if`, `in`, brush, a percentile,
  a styled count, on a facet, registered before or between graphs), plus
  `layout()` placement in both index bases, `layout(bs)`, qualifiers at
  every level, `legend()` sub-options, `xlabel()` grammar, `yaxis(2)` and
  `xaxis(2)`, `colorvar()`, `level()`, schemes, titles, and the immediate
  path's own unnamed-graph spec written exactly as `dash.ado` writes it.
- **TR-12.3** The profile is the document: layout tree (figures, KPI cards,
  widgets, tabs, containers), every widget's title/options/bounds/step, every
  KPI card's value, and per figure the glyphs (type, style, visibility,
  rows drawn through any view, every coordinate drawn), annotations
  (LabelSet, Label, Span, Legend items/font/visibility/location/
  orientation/click policy, BoxAnnotation), tools with tooltips, formatters
  and renderer scope, axes (type, label, ticker, ticks, formatter, fonts,
  ranges, extra ranges, scales) and chrome; and the warnings each mode
  raises. A second class, `TestAFilterMoveAgrees`, fires a widget in the
  served document and compares glyphs, labels and KPI cards to the saved
  renderer given the equivalent qualifier: eleven layer types × three
  widget types, facets, KPIs with their own `if`, a linked pair, a graph
  with its own `if`.
- **TR-12.4** `TestTheCorpusIsComplete` fails naming the type when a
  dispatched type has no bare entry, and `test_every_cross_cutting_feature_
  has_an_entry` names the feature when none exercises it.

### Legitimate differences

Three, each looked up by name with `_allowed()` where it is tolerated, and a
test that the list and the code agree: live recompute (initial values
compared, and the move class compares the rest), one source per dashboard
versus per graph (rows through the view are compared, identity is not), and
`layout(bs)`, which the help documents as falling back to a grid when served
(figures compared in registry order; the tree and the per-figure toolbar
location are not). The two date entries are in their own class and are
asserted to STILL fail on the comparisons the gap breaks, by hand rather
than with an `xfail` mark, so the day they pass the class fails and the
entries move into the corpus.

### Acceptance

- **AC-12.1** 38/38 types; every cross-cutting feature the package has.
- **AC-12.2** Verified by mutation. Each WP-10, WP-11 and WP-12 fix was
  reintroduced, one at a time, in a copy of the final tree, and the guard
  run in full (1966 cases). Every mutation fails it; the count and the
  comparison that caught it:

  | Defect reintroduced | Failures | Caught by |
  |---|---|---|
  | WP-10: served mlabel drawn twice | 8 | annotations, labels after a move |
  | WP-10: served per-plot `if` not read | 4 | glyphs, tools |
  | WP-10: served KPI `if` not read | 4 | KPI cards, tree |
  | WP-10: served empty layer says nothing | 1 | warnings |
  | WP-10: served no hover tool | 46 | tools |
  | WP-10: served legend keys not rebuilt | 48 | annotations |
  | WP-10: served zero-index placement dropped | 3 | glyphs, annotations, tools (the figures pair differently) |
  | WP-10: served KPI fmt drops the `c` suffix | 2 | KPI cards, tree |
  | WP-11: served by() panels empty | 21 | glyphs |
  | WP-11: saved by() groups the unqualified frame | 3 | glyphs, glyphs after a move |
  | WP-11: served computed layer not refit after a move | 56 | glyphs after a move |
  | WP-11: served histogram ignores its qualifier | 14 | glyphs after a move |
  | WP-11: served by() sub-option not named | 1 | warnings |
  | WP-11: served by(cols()) ignored | 0, then 1 | **not caught on the first run**: the layout tree recorded a grid's children without their positions, so 3×1 and 2×2 compared equal. The tree now records `(row, col)`; re-run, the mutation fails the tree comparison |
  | WP-12: served legend clickable | 156 | annotations |
  | WP-12: served histogram y titled with the variable | 9 | axes |
  | WP-12: served session level ignored | 8 | glyphs, annotations |
  | WP-12: served dropdown carries 0.0 | 8 | widgets, tree |
  | WP-12: served slider title without the inequality | 2 | widgets, tree |
  | WP-12: served KPIs first whatever the registry | 11 | tree |
  | WP-12: served header as one classless Div | 3 | tree |
  | WP-12: served faceted graph not nested in its cell | 121 | tree, figure count |
  | WP-12: served colorvar column not carried | 8 | glyphs, annotations |
  | WP-12: served no second axis | 4 | axes |
  | WP-12: served xlabel() ticks ignored | 6 | axes |
  | WP-12: served shared source without hover columns | 2 | tools |
  | WP-12: saved widget reads the first graph's source | 2 | widgets, tree |

  Two WP-10/WP-11 fixes are outside this file's reach and are pinned
  elsewhere: the `layout(bs)` tabs order (Bootstrap markup, no Bokeh tree;
  `test_server_layer_defects.py::TestTabsAreWhereTheHelpSaysTheyAre`) and
  `dash_setup`'s warning silencing (Stata-side; `test_by_suboptions.cscript`
  BYS-06).
- **AC-12.3** Removing any bare entry fails `test_every_dispatched_type_has_a_bare_entry` naming it.

### Found and not fixed

- The served app has no date handling (BUGS.md, open since WP-10). The port
  is scoped: seven consumers of `date_vars` in the saved renderer, all
  liftable into `_dash_*` helpers; one measured trap, that the saved
  renderer converts BEFORE it qualifies, so `if when > 15345` on a date
  variable selects Stata's rows served and every row saved -- the shared
  qualifier must translate the literal before the port lands.
- `layout(bs)` served draws the auto grid without a warning (WP-21).
  *Since fixed by 31e76e0: the served app draws the saved page's 12-column
  grid (test_served_bs_layout.py), as WP-23's reconciliation measured.*
- `scheme` legend_position/legend_cols are parsed and consumed by nothing in
  either mode; not activated here, since that would move every s2color
  legend in both modes without a Stata measurement.  *Since consumed: both
  modes place and wrap the legend by the scheme when the user gives
  neither (dash_render.py's legend chrome; test_scheme_rendered_output.py
  `TestTheLegend`, `TestNamedLegendPlacements`), as WP-23 measured.*

**Verification.** Certification 37/37 passed, 0 failed, 0 skipped.  pytest 6102 passed, 58 skipped, 6 xfailed -- five of the six are the date-gap comparisons this package pins so their fix is noticed, the sixth predates it.

---

# Milestone 3 — An honest surface

## WP-13 · Options: honour or report, never silence — DONE

**Gaps closed:** A3, E1 (nodraw), E2, E4 · **Severity:** S2 · **Effort:** M · **Depends on:** —

> **User story.** As a user, I want to be told when `dash` ignores something
> I wrote — and never to be told it ignored something it actually used.

### What was measured before any code changed

Every premise held, at the process boundary in Stata:

| Command | Before |
|---|---|
| `dash scatter mpg weight [aw=price], name(w1)` | rc 0, registered, no note |
| `dash scatter mpg weight, name(g1) link(g1)` then `dash build` | rc 0, one source, no widget, no note; `build_options.link` empty |
| `dash scatter mpg weight, name(g2) filter(foreign, type(dropdown))` then `dash build` | no widget, the variable not even serialised, no note |
| `dash scatter mpg weight, name(g3) saving(named.html)` | registered, file not written (rc 601), no note |
| `dash scatter mpg weight, nodraw saving(x.html)` | `ignoring unsupported option(s): nodraw()`, and the browser kept shut |
| `dash (lpoly mpg weight, bw(400))` | spec `{"barwidth":"400"}`, the same 193-point default curve as with no bandwidth, no note; `bwidth(400)` gives a different 200-point curve |
| `twoway lpoly mpg weight, bw(400)` / `twoway bar mpg weight, bw(100)` | rc 0 / r(198) |

Two things the plan did not know. `nodraw` on a registered graph was also
ignored by `dash build`, although the help said it had nobrowser's effect
there. And the help's own Unsupported entry for `nodraw` argued, in six
lines, for naming it in the note while admitting it was honoured -- the
contradiction was documented, not accidental.

### Technical requirements, as delivered

- **TR-13.1** `link()` and `filter()` written on a graph are on both pending
  lists and named in the note; the help's Unsupported section says they
  belong to `dash build`. `saving()` on a named graph is named at the route
  decision in `_dash_plot`, not from a list, because the immediate route
  honours it and the note must not say otherwise there. Reported, not
  honoured: `twoway` rejects both `link()` and `filter()`, and a per-graph
  filter would be a feature with an `exclude()` semantics to decide.
- **TR-13.2** The weight type is saved before the `sreturn clear` that
  destroyed it and appended to the segment's ignored list; the reporter
  prints a bracketed token without the `()` suffix, so the note reads
  `dash: ignoring unsupported option(s): [aweight]` -- by type, never by
  variable, once per distinct type per command.
- **TR-13.3** `nodraw` is off both pending lists. The launch decision is
  `_dash_browser_wanted`, a program a certification script can call without
  launching anything, and `dash build` now reads the registry for a graph's
  `nodraw` (`_dash_registry_nodraw`), which makes the help's claim true. The
  fixture disposition and the generator's inventory follow, so neither can
  reinstate the lines.
- **TR-13.4** `_dash_fold_bw` resolves `bw()` once the plot type is known:
  `bwidth()` on the bandwidth types, `barwidth()` on the bar family (dash's
  documented superset), named in the note elsewhere, and twoway's r(198)
  when written beside `bwidth()`.
- **TR-13.5** `test_unsupported_report_is_true.py` now classifies every
  option the two syntax blocks declare -- pending, alias, route, or live --
  and renders every live option twice to prove it changes the document.
  Measured on the day: 86 live options, all live; the only unclassified
  names were `link` and `filter`, which the run named.

### Acceptance

- **AC-13.1** `[aw=price]` reports `[aweight]`, once; `test_option_surface.cscript` AC-13.1a-c.
- **AC-13.2** graph-level `link()` and `filter()` are named once each; O2-08.
- **AC-13.3** `nodraw` prints no note, keeps the window shut on both routes; `test_nodraw_honoured.cscript` ND-01 to ND-05.
- **AC-13.4** `bw(400)` on lpoly sets `bwidth`; `test_alias_semantics.cscript` measures twoway's rc per type in the same run.

### Found on the way

- `test_option_surface.cscript`'s O2-02 ("no options, no note") counted the
  corpus control `scatter mpg weight [aweight=price]` as a zero-option
  command; its premise is now "no options and no weight".
- The standalone run of a certification script that renders needs the
  dash directory on the ado-path (`cscript ... adodir ".."` is not enough
  for `findfile dash_render.py`); the runner sets it. Pre-existing.

**Verification.** Certification 39/39 passed, 0 failed, 0 skipped (two new scripts).  pytest 6199 passed, 62 skipped, 6 xfailed, 0 failed; the four new skips are the cscript-hygiene checks the two new scripts do not need, as for the 37 before them.

---

## WP-14 · Sub-options stop vanishing — DONE

**Gaps closed:** E3 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-13

> **User story.** As a user writing `legend(span stack)`, I want to know those
> sub-options did nothing — `dash.sthlp:162` promises "nothing is ever dropped
> without being named".

### What was measured before any code changed

Every E3 premise held, in both render modes: `legend(span stack holes(1)
keygap(2))`, `xlabel(, valuelabel)`, `ylabel(, labcolor(red))`,
`yscale(reverse noline titlegap(2))`, `xline(3000, lstyle(foreground))`,
`filter(price, type(bogus))` and `filter(nosuchvar, ...)` all rendered with
rc 0 and no warning; `filter(price, type(range) label("R&D __ spend"))`
and `label("open the door")` produced no widget; `xtitle("Weight",
orientation(vertical))` titled the axis with the sub-option text. One E3
claim was stale: `xline(3000, lcolor() lpattern())` is honoured (WP-10's
corpus pins it), so it is not named.

The sink analysis for the filter text: the label reaches only a Bokeh
widget title (entity-escaped into the page) and, served, a `repr` Python
literal; the filter JavaScript carries varname, type and sentinel only.
Nothing in the label is evaluated anywhere. The old `_UNSAFE_F` gate
protected nothing and refused real labels.

### Technical requirements, as delivered

- **TR-14.1** One reporter, `_dash_report_suboptions`, in by()'s words
  (`dash: legend() sub-option(s) not implemented and ignored: span
  stack`), once per graph per render, from shared code: legend
  (`_dash_legend_unsupported`), the axis grammar (`_dash_parse_axis_spec`
  records what it does not honour; `_dash_apply_axis_options` names it),
  the scales (`_dash_scale_spec`, which subsumes the old five-token
  warning), the textboxes (`_dash_textbox`: title, subtitle, note,
  caption, xtitle, ytitle -- size() and color() honoured, the rest named;
  the text split from its sub-options), and the reference lines
  (`_dash_reference_lines`).
- **TR-14.2** by(): WP-11.
- **TR-14.3** `_dash_parse_filter_raw` is the one parser for both modes. It
  refuses a group only for a variable or exclude() name that is not a
  name, or a type() it does not build, and says so; a stray token is
  named; the label may be any text but a semicolon (the group separator,
  on the Stata side too -- documented).
- **TR-14.4** An unknown `type()` is named with the three accepted types, in
  the parser and in both widget loops; a variable not in the data is named
  too.

### Acceptance

- **AC-14.1** every E3 sub-option: `test_suboption_warnings.py` (both modes,
  13 named cases, 7 honoured-only cases) and `test_suboption_reporting.cscript`
  SR-01 to SR-09.
- **AC-14.2** `filter(x, label("R&D __ spend"))` produces the widget, in
  both modes and from Stata (SR-07).
- **AC-14.3** `filter(x, type(bogus))` warns, naming the accepted types.

### Found on the way

- `ylabel(#5, grid)` was silently ignored: the stripped sub-option left its
  comma behind and `#5,` matched no keyword form. Fixed.
- Three served divergences the parity corpus lacked: `title()` size() and
  color() (15px red saved, 13px grey served), `xscale(range())` (dropped
  served), and the caption at y = -12 served, where the saved renderer's
  own comment says a Label is clipped. All three now run one text, the
  parity profile records a Label's position, and the corpus carries each.
- Not covered, and said so: `plotregion()`, `graphregion()`, the `*2` axis
  options, `colorcuts()` and `tabs()` still drop their sub-options in
  silence. [WP-30 P1.20a, commit 2207ddb: plotregion()/graphregion() sub-options are drawn or named; margins by P1.20b, commit 6e2af0c]

### Verification, measured 22sep2026

| Suite | Result |
|---|---|
| `test_suboption_warnings.py` (both modes) | 39 passed |
| `test_suboption_reporting.cscript` SR-01 to SR-09 | ALL CHECKS PASSED |
| Parity guard `test_mode_parity.py`, corpus + 8 | 2048 passed, 1 skipped (layout(bs), stated), 5 xfailed |
| Full Python suite (`-n auto`) | 6357 passed, 54 skipped (stated reasons), 6 xfailed, 0 failed |
| Full certification suite | 40 passed, 0 failed, 0 skipped |

Four `test_server.py` xscale tests grepped the generated source for the
old emitted text (`x_range.flipped`, `_xs_toks`); they now assert on the
served document (flipped ranges, `LogScale`), and BUG-21e's
comma-separated `filter(foreign, type(dropdown), exclude(g1))` caught
the shared parser reading `type(dropdown),` as an empty type -- fixed,
and pinned in `test_suboption_warnings.py`.

---

## WP-15 · Systematic option validation — DONE

**Gaps closed:** E5 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-13

> **User story.** As a user who typed a bad value, I want a clear `dash` error
> naming the option — the way `level()` already does.

### What was measured before any code changed

The E5 premise held: `level()` was the only value dash checked
(`dash.ado:830-842`, not the 549-558 the gap cited), and every other plot
and graph value went to JSON verbatim. Forty probes through Stata,
22sep2026: two hard errors, both `level()`; two `r(111)` from `fmt()`
(`fmt(bogus)`, `fmt("HACKED" %9.2f)`, the `HACKED not found` case);
thirteen Python warnings then rc 0 with a substituted value (`degree(x)`,
`bwidth(-1)`, `bin(0|abc)`, `width(-1)`, `kernel(bogus)`, `n(-5)`,
`xsize(abc)`, `ysize(-2)`, `aspectratio(abc)`, `scheme(nonsense)`,
`xscale(bogus)`, `barwidth(abc)`); one note (`connect(bogus)`, pending); [WP-30 P1.8a, commit fa52891: connect() is drawn; connect(bogus) is refused as twoway refuses it]
twenty-one silent rc 0, four of them good values rightly silent
(`msize(huge)`, `malpha(2)`, `fmt(%9.2f)`, `fmt(%-12.0gc)`) and seventeen
bad (`msize(abc)`, `msymbol(nonsense)`, `mcolor(notacolour)`,
`jitter(-3|abc)`, `lwidth(abc)`, `lpattern(bogus)`, `mlabposition(99)`,
`yaxis(3)`, `colornlevels(0)`, `bgcolor(notacolour)`, `hover(bogus)`,
`fintensity(abc)`, `mlabsize(abc)`, `msangle(abc)`, `bands(0)`,
`jitterseed(abc)`); and one silent and wrong (`fmt(%tc)` on `mpg` prints `01jan1960 00:00:00`).
Read, not run: `map_scatteri` called `translate_msize` and
`translate_msymbol` bare, so `scatteri ..., msize(abc)` aborted the render;
`map_dropline` did the same with a bare `float()` on `jitter()`; a negative
`jitterseed()` reached `numpy.random.default_rng` and aborted in both modes.

The oracle, twoway itself, 248 probes: 60 refused, 188 accepted, 36 of the
accepted with `(note: named style X not found in class Y, default
attributes used)`. twoway never refuses a style name. It refuses a number
outside a range it has: `msangle(400)`, `lwidth(-1)`, `yaxis(0|10|abc|1.5)`,
`xsize(0|101)`, `bin(0|abc|2.5)`, `bands(0|abc|2000)`, `degree(-1|x|1.5)`,
`n(0|abc|2.5)`, `bwidth(0|-1)` on lpoly and `bwidth(-1|abc)` on kdensity
(kdensity accepts `bwidth(0)` itself; dash's positive rule is its own
there), `kernel(bogus)`, `aspectratio(abc)`, `barwidth(abc)`, lfitci
`level(abc)`; and it answers
`mlabel(nosuchvar)` and `by(nosuchvar)` with r(111). It silently accepts
what dash cannot use: `jitter(abc|-3|31)`, `jitterseed(abc|-1|2.5)`,
`level(150|0|-5)`, lowess `bwidth(5|0|-0.5)`, `msize(-1|0)`, `degree(5)`,
`n(1)`, `yaxis(3..9)`. `confirm numeric format`, 26 probes: rc 0 for
`%9.2f %9.0gc %-12.3e %09.2f %9,2fc %12.0fc %tdCCYY-NN-DD %tcHH:MM:SS %21x
%16H %tc %td %tm %9.2fc %-9.2f %10.0g %8.0e`, rc 7 for `%12s bogus 9.2f
%9.2 %9.2f_n %9.2f%9.2f %c % %%9.2f`; and two `strofreal()` probes showing
it returns "" for `bogus` with rc 0, which is why it is not the validator.

The corpus inventory (`twoway_corpus.do`, 299 commands;
`conformance_corpus.txt`; the help examples; `examples/*.do`; every cert
script): 1015 values across 205 options and 70 sub-option keys, every one a
plain number, keyword, variable or quoted RGB triplet. The table below was
checked against all of them before it was written down.

### Technical requirements, as delivered

- **TR-15.1** One declarative table, `_dash_option_rules`, between
  `_dash_fold_bw` and `_dash_plot_opts_to_json` under sentinel comments.
  Token grammar `option=kind[,p1[,p2[,p3]]][@type1|type2]`; a token with
  `@` applies to those plot types only, one without to every type that has
  no `@` token for that option. Kinds: `num` (finite; optional inclusive
  bounds, `x` makes both exclusive), `int`, `pos`, `style` (a name passes
  untouched, a number must lie in the range if the token has one;
  `mlabposition()` and `fintensity()` have none, as `msize()` has none,
  and a token that only looks like a number, `msize(1e400)`, is refused
  rather than passed as a name), `istyle` (a name or an integer in the
  range), `enum` (case-insensitive, normalised to lower case), `numlist`
  (a count range), `var`, `varlist`, `byvarlist` (the head before the
  first top-level comma is a varlist, expanded with `unab` and normalised;
  the rest kept verbatim) and `format`. The variable kinds use `unab`
  alone: `tsunab` and `fvunab` are sclass and their `sreturn clear` wiped
  the segment's s() from inside the validator; a head `unab` cannot expand
  but `capture tsrevar ..., list` (rclass) can is a time-series expression
  dash cannot draw and is refused, `dash: colorvar() must name a variable,
  not a time-series expression (got: L.price)`, r(198), and otherwise the
  first token failing `confirm variable` is `dash: colorvar(): variable X
  not found`, r(111). `_dash_validate_opts` also snapshots every s() macro
  before each value and restores any that came back empty. A value that
  passes is written back normalised: `int` as `string(x, "%21.0f")`
  (`yaxis(2.0)`, `yaxis(02)`, `yaxis(+2)`, `n(1E3)` reach the renderer as
  2, 2, 2, 1000); `num` as written when Python can parse it, else as
  `%21.0g`; `numlist` as `r(numlist)` (`colorcuts(1(1)5)` as `1 2 3 4 5`,
  `range(0,10)` as `0 10`); every value `ustrtrim()`ed first, so a
  tab-padded `jitter(5)` passes as it does in twoway.
  `_dash_validate_value` (`prefix opt spec value ptype`) judges one value
  and c_locals the normalised form; `_dash_validate_opts` (sclass) applies
  the plot rules once per segment, right after `_dash_fold_bw`, reading
  `s()` and sreturning the normalised values, and the graph rules against
  the segment's own `s(g_<opt>)`, so `(scatter mpg weight, xsize(500)) ,
  xsize(5)` and `(scatter, by(nosuch)) , by(foreign)` are refused as
  twoway refuses them (the first cut checked only the after-comma winner);
  `_dash_plot` applies the graph rules (`xsize`, `ysize`, `aspectratio`,
  `hover`, `by`) once per graph, after the after-comma restore loop and
  before the saving()/report block. The hand-written `level()` block left
  `_dash_parse_plot_opts` for the row `level=num,0,100,x`. A refusal is
  one `display as error` line in the house shape, `dash: opt() must be
  ... (got: V)`, then `exit 198` (`exit 111` for a variable that does not
  exist); the value is echoed through `macval()`; for five bounds that are
  dash's own a second sentence says so, `yaxis()`/`xaxis()` (`dash draws
  two axes.`), `degree()`, `bin()`, `n()` and the lowess `bwidth()`; the
  other dash-own bounds (`colornlevels()`, `jitter()`, `level()`,
  `barwidth()`, `aspectratio()`, `jitterseed()`/`jseed()`, kdensity
  `bwidth()`) carry none. Two deliberate supersets stay: `kernel(GAUSSIAN)`
  is normalised where twoway refuses it, and `lwidth(())` passes as a name
  that the renderer then reports.
- **TR-15.2** KPI `fmt()`, in `_dash_kpi` beside the `update()` check,
  both of them above the `name(k, replace)` block and before any
  computation, so nothing is destroyed until every value is proven (as
  first placed, `name(k, replace) fmt(bogus)` refused correctly but had
  already dropped the old KPI's globals while the registry still listed
  the name, and the next `dash build` died in a JSON traceback): a
  character gate (a single leading `%`, then only `[A-Za-z0-9_.,:!/+-]`,
  at most 60 characters) then `confirm numeric format`; failure is `dash
  kpi: fmt() must be a numeric display format such as %9.2f or %12.0fc
  (got: V)`, r(198). `: display` stays the formatter, on a proven token,
  and its `if` is compound-quoted.
- **TR-15.3** The renderer, both modes: `_dash_style_note(option, value,
  what)` is module-level and copied into the served app beside
  `_stat_option_float`, and says each thing once: a module-level
  `_DASH_NOTED` set keyed on (option, value, what), cleared by
  `_dash_reset_notes()` at the start of `DashRenderer.render()` and of
  the served `make_document` (both names are emitted into the app), so
  `connected`'s line and marker border, `rcapsym`'s spine and dot and
  every `by()` panel print one note, not two or four; `parse_color_alpha`
  takes the option name and notes an unknown colour; every `except
  ValueError: pass` around
  `translate_msymbol`/`translate_msize`/`translate_lwidth`/
  `translate_lpattern` in `_apply_line_opts`, `_apply_marker_opts`,
  `_apply_fill_opts` and `_apply_mlabel_opts` notes and then defaults;
  `msangle`, `fintensity` and `mlabposition` note a value they cannot read
  (`mlabposition(13)` draws at 3 o'clock with the note, as twoway does);
  `translate_msize` and `translate_lwidth` raise `ValueError` on a
  non-finite number (`msize(1e400)` reached `int(inf)` and aborted both
  modes with `OverflowError`); `_extract_region_lwidth` notes
  `plotregion(lwidth(abc))` and returns None where it raised out of the
  standalone figure body and was silent when served; `map_area`'s
  `color()`, `map_bar`/`map_histogram`'s `color()` beside `blcolor()`,
  `bgcolor()`, `plotbgcolor()`, `plotregion(color|lcolor)`,
  `graphregion(color)`, `xline()`/`yline()` `lpattern()` and `lwidth()`,
  `legend(size())` and the KPI `color()` (prefix `dash kpi`) all note the
  option as written; `map_scatteri` warns and defaults instead of raising;
  `map_dropline`, `map_scatter` and `map_scatteri` read `jitter` through
  `_stat_option_float(..., lo=0.0, hi=100.0)`; the served figure strings
  read `aspectratio`, `xsize` and `ysize` through the same
  `_stat_option_float(..., "graph")` as the standalone body, which emits
  one aspectratio message rather than two; `_jitter_seed` warns and draws
  unseeded on a negative or non-integer seed; an `mlabel()` with several
  names uses the first and names the extras once, and one naming a column
  the source lacks notes once; every echoed value goes through
  `_dash_display`. `_stat_option_float`'s signature and the raising
  `translate_*` are unchanged (`test_options.py` pins them).

### Acceptance

- **AC-15.1** every table option, one good and one bad value, through
  Stata: `test/test_option_validation.cscript` (OV-nn); the table's
  structure, every rule against a declared option, the renderer notes in
  both modes and the three abort fixes: `test/test_option_validation.py`;
  hostile values per option: `test/test_adversarial.cscript` P9-nn.
- **AC-15.2** `dash kpi mean(mpg), name(k) title(T) fmt(bogus)` is the
  `fmt()` message with r(198), not r(111): OV-nn and P9-nn.
- **AC-15.3** no documented example regresses: `test/test_conformance.cscript`
  C-05 runs `test/fixtures/help_examples.txt`, and
  `test/fixtures/value_truth.json` (curated from the oracle) records
  twoway's own rc per value; `test/test_option_validation.py` checks each
  rule's kind against it (a style kind rests on a twoway note, a refusing
  kind on a twoway refusal, the format verdicts on the confirm probes),
  not each bound against each value.

### Found on the way

- `scatteri ..., msize(abc)` and `msymbol(nonsense)` raised out of the
  mapper and lost the whole render; `dropline ..., jitter(abc)` the same
  through a bare `float()`; `jitterseed(-1)` the same through
  `numpy.random.default_rng`. The `ValueError` is pinned by
  `test_option_validation.py`; the r(7102) it would have ended in is read
  off dash.ado's bare `runpy` call, not run. Fixed in both modes; the
  Stata table refuses `jitter(abc)` and the negative seed before Python
  runs, and the `scatteri` names take the note-and-default path every
  other layer had.
- `mlabel(make foreign)` named no column and labelled nothing; `by(for)`
  reached the renderer unexpanded and took the measured `by(nosuchvar)`
  path, one unfaceted panel with no message; `hover(bogus)` was split on
  whitespace and every unknown name dropped without a word. The `var`,
  `byvarlist` and `varlist` kinds expand and confirm them in Stata, as
  twoway does.
- A style name twoway notes was silent in dash on every marker layer
  (`mcolor(notacolour)`, `msymbol(nonsense)`, `msize(abc)`, `lwidth(abc)`,
  `lpattern(bogus)`, `msangle(abc)`, `fintensity(abc)`,
  `mlabposition(99)`). One note each now, in both modes.
- The old `level()` pair and the bwidth()-repeated message
  (`dash.ado:1151`, `option bwidth() may not be repeated`) were the only
  unprefixed errors in `dash.ado`; the table's messages carry the `dash:`
  prefix like every other (the bwidth one still does not).
- Stale line references, in E5 and in this package as first written, at
  the WP-15 baseline (cc3c4ac): `level()` was at `dash.ado:830-842` (not
  549-558), the `: display` at `:2410` (not 1918), `_stat_option_float`
  at `dash_render.py:7050` (not 9228) and `_resolve_kpi_color` at `:7486`
  (not 10484). The table moved them again.
- Found by the adversarial review of the first cut and closed in the same
  package. `tsunab`, tried after `unab` for a time-series name, is sclass
  and its `sreturn clear` wiped every option of the segment, so `(scatter
  mpg weight, colorvar(L.price) jitter(5) msize(large))` on tsset data
  registered with an empty options object and rc 0 (the same through
  `mlabel(L.mpg)`); the validator now uses `unab` alone, refuses a
  time-series expression by name (`must name a variable, not a
  time-series expression`), and `_dash_validate_opts` restores any s()
  macro a value check emptied. `dash kpi ..., name(k, replace) fmt(bogus)`
  refused correctly but had already destroyed the old KPI's globals with
  the name still in the registry, and the next `dash build` died in a
  JSON traceback (`update(bogus)` did the same before WP-15); both checks
  now run before the replace. A graph option inside a layer escaped the
  check whenever a later value won (`(scatter mpg weight, xsize(500)) ,
  xsize(5)` rc 0 where twoway is r(198); `(scatter, by(nosuch)) ,
  by(foreign)` rc 0 where twoway is r(111)); the graph rules now run per
  segment too. `colorcuts(1(1)5)`, `range(0,10)`, `yaxis(2.0)`,
  `yaxis(02)`, `yaxis(+2)` and `n(1E3)` reached the renderer as written;
  numlists are expanded and integers made canonical. A tab-padded
  `jitter(5)` was refused where twoway takes it; values are
  `ustrtrim()`ed. `mlabposition(13)` and `fintensity(150)` were refused
  where twoway draws (with a note, and in silence); both are unbounded
  style kinds now and the renderer notes them.
- On the renderer side the same review found `plotregion(lwidth(abc))`
  aborting the standalone render (bare `translate_lwidth` in
  `_extract_region_lwidth`) while the served app was silent;
  `msize(1e400)` aborting both modes with `OverflowError`
  (`int(float("1e400"))`); one bad option noted twice per layer and again
  per panel (`connected lcolor(notacolour) by(foreign)` printed four
  lines, `rcapsym mcolor(notacolour)` two); `area color()`,
  `bar`/`histogram` `color()` beside `blcolor()`, `bgcolor()`,
  `plotbgcolor()`, `plotregion(color)`, `graphregion(color)`,
  `xline(lpattern())`, `legend(size())` and the KPI `color()` replaced in
  silence; and the served figure reading `aspectratio`/`xsize`/`ysize`
  with a bare `float()` where the standalone body warned, twice for
  aspectratio. All closed as TR-15.3 says.
- Not fixed here, follow-ups: `dash (scatter mpg weight, level(95))` is
  accepted and `level` lands in the JSON where twoway's `scatter` refuses
  `level()` as not allowed; the table judges values, not which plot type
  takes the option, which is E1's territory. `by(a) by(b)` prints
  `dash: ignoring unsupported option(s): by()`, a misleading note for a
  repeated option twoway accepts with rc 0.

### Verification, measured 22sep2026

| Suite | Result |
|---|---|
| `test_option_validation.cscript` OV-01 to OV-134 plus the 58-line corpus arbiter | ALL CHECKS PASSED (203 checks) |
| `test_option_validation.py` (table vs parsers vs twoway fixture; every style note in both modes; the abort fixes) | 218 passed |
| `test_adversarial.cscript` P9-01 to P9-14 (injection and exhaustion payloads, KPI fmt payloads) | all pass (P9-05 is a note: a `$` payload cannot reach dash) |
| `test_conformance.cscript` C-05, 27 documented examples | rc 0, no drop note |
| Parity guard `test_mode_parity.py` | 2048 passed, 1 skipped (layout(bs), stated), 5 xfailed |
| Full Python suite (`-n auto`) | 6580 passed, 56 skipped (stated reasons), 6 xfailed, 0 failed |
| Full certification suite | 41 passed, 0 failed, 0 skipped |

An adversarial review between the first implementation and this commit
found and fixed: a helper (`tsunab`) that cleared every parsed option of
a segment; the KPI replace path destroying the old KPI before the new
value was proven; a graph option inside a layer escaping validation
when a later value won; two pre-existing render aborts
(`plotregion(lwidth(abc))`, `msize(1e400)`); repeated notes on
`connected`, `rcapsym` and by() panels; and silent graph-level colours,
reference-line and legend sub-options.

---

## WP-16 · Schemes reach the page — DONE

**Gaps closed:** G3, G4, G5, G6 · **Severity:** S1/S2 · **Effort:** M · **Depends on:** WP-09

> **User story.** As a user who chose `scheme(s1color)`, I want the dashboard
> to look like s1color — including *not* drawing gridlines s1color does not
> draw.

### What was measured before any code changed

The rendered baseline, 22sep2026: every one of the 14 shipped schemes in
both modes, four cases each (a scatter with a line and title, subtitle,
note and caption; a bar; a scatter with a KPI; a scatter with
`xlabel(, grid)`), read off the Bokeh models. Every scheme drew a minor
grid on both axes (`#505050` in twelve, `#808080` s1rcolor, `#ffffff`
economist) at alpha 1.0, the four that draw no major grid included
(s1color, s1mono, s1rcolor, stmono1). `fig.title` was Bokeh's
`#444444`/`13px` under all 14, dark grey on s1rcolor's black plot; the
subtitle, note and caption Labels were the literals 13px `#444444`, 11px
`#555555` and 12px `#555555` under all 14; axis titles and tick labels
`#444444` under all 14. The legend sat `top_right`, vertical, `ncols` auto
under all 14 while the schemes say 6 o'clock in two columns (nine of
them), 3 o'clock in one (stcolor, stgcolor, stmono1, stmono2) and 12
o'clock in three (economist). Every KPI card was inline `#f8f9fa` on
`#dee2e6` under all 14, and no card Div carried a stylesheet. economist's
heading was 7pt under an 11pt subtitle (`int(6.0 * 1.2)`) and its lines
1.2px against every other scheme's 1.5px. `xlabel(, grid)` drew `#e5e5e5`
on the ten schemes whose x grid is off. Markers were 8.0px medium, 5.82px
small, 10.18px large. Warnings: none. The two modes agreed on every figure
value; their one disagreement was the whitespace of the KPI Div.

The Stata truth, read from `scheme-*.scheme` and `style/*.style` with no
Stata run: minor grids off on both axes in all 14 chains, economist's y
axis through `vertical_nolinetick` and `draw_minor_nlt_vgrid`; the bare
`draw_minor_grid` and `draw_major_grid` keys are read by no style file.
The textbox mapping: `title()` is `heading`, `subtitle()` `subheading`,
`caption()` `body`, `note()` `small_body` (not `gsize note`, which every
scheme declares and no textbox reads), legend entries `key_label`, axis
titles `axis_title`, tick labels `tick_label`; a KPI card's nearest Stata
object is the legend box (`color legend`, `color legend_line`, text `color
text`). Units: every `gsize-*`, `symbolsize-*` and `linewidth-*` style is
`sztype relative`, 100 is the graph's smaller dimension, 2.88pt per unit
at the four-inch reference (medium 3.8194 = 11pt; the style files' own
comments say so, and `test/fixtures/scheme_visual/truth.json` measures it);
the symbolsize ladder is not the gsize ladder (large over medium 1.59
against 1.27); economist's `gsize heading 6.0` is 17.28pt and its
`linewidth p 1.2` four times medium. Every value dash's translated files
already carried agreed with the chains; what they lacked was every
`draw_minor_*`, `color
subheading/body/small_body/text/axis_title/tick_label/key_label/foreground`,
`gsize subheading/body/small_body/key_label`, `linewidth
minor_grid/axisline` and `numstyle legend_rows`.

Three claims in this package as first written were stale at the WP-16
baseline (`52c473c`): the major grid was already per axis from
`draw_major_hgrid`/`draw_major_vgrid`, so G3 was the minor grid alone; the
served legend already ran the shared `_dash_apply_legend`, so the
`lg.location = 6` `ValueError` of the old TR-16.4 no longer existed and
the two attributes were simply unread in both modes; and the served app
already built a real `SchemeParser` from `_SCHEME_PROPS`, so glyph
colours, symbols, patterns, alphas and marker sizes were already in
parity. The test side explained why all of it passed: `test_scheme_fidelity.py`
compares parsed attributes to the fixture and by its own docstring refuses
the pt/px conversion; nothing read `minor_grid_line_color`, a Label's
font, the legend's placement or a card's style off a figure; and the
parity profile recorded neither the minor grid nor the card's style, so a
one-mode change there would have been invisible.

### Technical requirements, as delivered

- **TR-16.1 (G3)** `scripts/extract_scheme_truth.py` extracts `yesno
  draw_minor_grid/draw_minor_hgrid/draw_minor_vgrid`, `color
  subheading/body/text/small_body/axis_title/tick_label/key_label/foreground`,
  `gsize subheading/body/small_body/key_label`, `linewidth
  minor_grid/axisline` and `numstyle legend_rows`, writes the EFFECTIVE
  per-axis flags through the axisstyle indirection (economist's y axis
  from `draw_major_nlt_vgrid`/`draw_minor_nlt_vgrid`), and records
  `_meta.units` with the three ladders and the pt formula;
  `test/fixtures/scheme_truth.json` and the 14 `schemes/*.scheme` are
  regenerated from it, additions only. `SchemeParser` gains
  `draw_minor_hgrid`/`draw_minor_vgrid` (default no),
  `subheading_font_size`, `body_font_size`, `small_body_font_size`,
  `key_label_font_size`, `subheading_color`, `body_color`,
  `small_body_color`, `text_color`, `axis_title_color`, `tick_label_color`,
  `key_label_color`, `minor_grid_line_width` and `legend_rows`, each with
  its s2color value in `_FALLBACK_PROPS`. `apply_to_figure` colours a minor
  grid only where the axis's flag is yes, else `None`, at
  `minor_grid_line_width`. After the review: `axis_line_width` (`linewidth
  axisline`, through `_lwidth` with a thin default) is parsed too and
  `apply_to_figure` sets each axis's `axis_line_width` from it; `color
  foreground` is carried in the files and the fixture with no parser
  attribute, because no Bokeh property answers to it.
- **TR-16.2 (G5)** `_gsize` numeric is `val * 2.88` pt, formatted `%g`, no
  `max(6, ...)` floor, no `int()`; `_GSIZE_PT` minuscule 1pt and vhuge 28pt;
  `_lwidth` numeric is `val * 5.0` px, so keyword medium .30 and numeric
  .30 are both 1.5px and economist's 1.2 is 6.0px; a `_SYMBOLSIZE_PT`
  ladder (zero 0, vtiny 0.29, tiny 1.0, vsmall 1.5, small 3.0, medsmall 3.6,
  medium 4.4, medlarge 5.6, large 7.0, vlarge 9.0, huge 14.0, vhuge 16.0,
  ehuge 32.0) with `_markersize_px` anchored at medium 4.4pt = 8px. The
  linewidth keyword ladder `_LWIDTH_MAP` is untouched (a follow-up, below).
- **TR-16.3 (G4)** `apply_to_figure` sets `fig.title.text_color` and
  `text_font_size` from `color heading`/`gsize heading` and each axis's
  `axis_label_text_color`/`major_label_text_color` from `color
  axis_title`/`color tick_label`; `_dash_figure_title` still runs after it,
  so `title(, size() color())` wins. `_dash_text_annotations(fig,
  graph_opts, seen, key, scheme=None)` draws `subtitle()` at subheading
  size and colour, `note()` at small_body size and colour and
  `caption()` at body size and colour, falling back to
  `_DASH_TEXTBOX_DEFAULTS` only when no scheme is passed; both call sites
  pass one. `note_font_size` stays parsed for the fidelity check and is
  read for nothing.
- **TR-16.4 (G4)** One module-level `_dash_scheme_chrome(scheme)` builds
  the legend chrome for `_rebuild_legend` and the served call: background,
  border, label size and colour from `key_label`, `legend_position`,
  `legend_cols`, `legend_rows`. `_dash_apply_legend` applies the scheme's
  placement only when the user gave no `position()`, `pos()`, `ring()` or
  keyword: 6 is below and horizontal in `legend_cols` columns, 12 above and
  horizontal, 3 right and vertical, 9 left, the other clock values through
  `_DASH_CLOCK_SIDE`; user `cols()`/`rows()` win. After the review: a
  legend the scheme or a user `position()` puts in a side panel is inserted
  nearest the plot (after the axis in `fig.below`/`fig.above`, before every Label, Stata's
  `legend_ring 3` inside note, caption, subtitle and title) and centred
  (`location = "center"`); a user `rows()` alone sets `ncols` to `"auto"`
  and `cols()` alone `nrows` to `"auto"`, so the scheme's columns never
  survive a user `rows()`; a `clockdir legend_position` outside 1-12 or a
  negative `legend_cols`/`legend_rows` is refused with the `dash scheme:`
  warning and the default used.
- **TR-16.5 (G4)** `default_color(index, plot_type)` reads `p_mark_colors`
  for the marker types (scatter, scatteri, dot, dropline, connected's
  markers, rscatter, pcscatter). Equal to `p_colors` in every shipped
  scheme, so no rendered change; a user scheme declaring `color p1mark`
  now works. After the review the lookup is gated on the glyph, not on the
  plot type's "scatter" alias: the marker glyphs of scatter, scatteri, dot,
  rscatter, pcscatter, dropline and rcapsym read `p#mark`; the Segments of
  spike, rcap, rspike, pcspike and pcarrow and the line halves of dropline
  and rcapsym read `p#`, as Stata's `p#mark`/`p#line`/`p#other` split
  intends.
- **TR-16.6 (G6)** One module-level `_dash_kpi_card_html(title, value,
  subtitle, color, bgcolor, name, scheme)` writes the card for
  `_make_kpi_div`, the served `_dash_kpi_card` and, mirrored, the JS
  rebuild in `_FILTER_JS`: class `db-kpi-card`, the layout-only inline
  properties, no inline background or border unless `bgcolor()` was given
  (then `background:<explicit>` inline, and it wins; the JS config sends
  "" when it is not explicit), value colour `color()` or the scheme's
  `text_color`, title and subtitle `text_color` plain. Every card Div in
  both modes gets `stylesheets=[InlineStyleSheet(scheme.css_block())]`,
  because a Bokeh 3 Div renders in a shadow root; `css_block` emits
  `.db-kpi-card { background-color: <legend>; border: 1px solid
  <legend_line>; color: <text>; }`, `.db-title` at heading colour and size
  and `.db-subtitle` at subheading colour and size.
- **TR-16.7 (G6)** `_dash_apply_axis_options(..., grid_color=None)`: the
  `xlabel(, grid)` branch colours the grid it turns on with the scheme's
  grid colour, not `"#e5e5e5"`; both callers pass `scheme.grid_color`.
- **TR-16.8** Served app: `_dash_apply_scheme(fig)` is
  `_DASH_SCHEME.apply_to_figure(fig)` and its hand-copied body is gone; the
  unread served constants (`_SCHEME_NAME`, `_SCHEME_MARKER_SIZE`,
  `_SCHEME_FILL_ALPHA`, `_SCHEME_BAR_ALPHA`, `_SCHEME_AREA_ALPHA`,
  `_SCHEME_LINE_WIDTH`, `_SCHEME_COLORS`, `_SCHEME_SYMBOLS`,
  `_SCHEME_LINE_PATTERNS`, `_SCHEME_CONNECT_PATTERNS`, `_SCHEME_CHROME`) and
  the helpers `_dash_scheme_color/_symbol/_dash` are deleted;
  `_SCHEME_GRAPHSIZE_X/Y` stay, and the served figure takes the standalone
  aspect fallback to the scheme's graphsize ratio.
- **TR-16.9** `test_scheme_fidelity.py` checks every new directive
  parsed-against-truth for all 14 schemes; the new
  `test_scheme_rendered_output.py` reads the values above off real figures
  for all 14 schemes in both modes and asserts the two modes' profiles
  equal; `test_mode_parity.py`'s profile records the minor grid and its
  width, the axis line and text colours, the title style, the legend's
  `ncols`/`nrows`/label colour, and a card's class, inline background and
  stylesheet text, with four new corpus entries (s1color with a legend and
  a KPI; economist with the four texts and a legend; stcolor's default
  legend placement; an explicit `bgcolor()` under economist). Wrong-value
  pins restated: `test_scheme_coercion.py` (numeric linewidth is Stata's
  unit; no 6pt floor), `test_kpi.py`, `test_kpi_security.py` and
  `test_option_validation.py` (no inline background, the class rule
  carries it; the KPI value's default colour is the scheme's `color text`,
  not `#212529`); and `test_scheme.py` `TestApplyToFigure` gains a
  minor-grid test (`None` under s2color). After the review: the parity
  `_chrome` profile also records `aspect_ratio`, `min_height`,
  `max_height`, the minor grid's width and the axis line width, and
  `_kpi_card` the value and title colours; the corpus gains "by() with a
  graph title" and "legend(rows(1)) with three series under s2color"; the
  note Label is checked against the fixture's `small_body_color`; and the
  new `test_scheme_review_fixes.py` pins each renderer fix listed under
  "Found on the way".
- **TR-16.10** `BUGS.md`: the G3 entry written first, then G4, G5 and G6;
  `GAPS.md` G3-G6 closed with the measured before and after; `dash.sthlp`'s
  scheme section says what a scheme governs on the page, on which unit
  scale, how an `#include` in a user `.scheme` file is resolved, and that
  an explicit option wins.

### Acceptance

- **AC-16.1** minor grid `None` on both axes under all 14 schemes in both
  modes, and major `None` too under s1color, s1mono, s1rcolor and stmono1:
  `test_scheme_rendered_output.py`.
- **AC-16.2** economist's title 17.28pt over its 11pt subtitle Label, and
  its line 6.0 over s2color's 1.5, in both modes: `test_scheme_rendered_output.py`.
- **AC-16.3** a KPI card under economist carries no inline background and
  an `InlineStyleSheet` whose `.db-kpi-card` rule is `#c6d3df` on
  `#c6d3df`; `bgcolor(#ecf0f1)` is still inline: `test_scheme_rendered_output.py`.
- **AC-16.4** every parsed attribute has a consumer, with one stated
  exception: `note_font_size` (`gsize note`) is kept parsed for the
  fidelity check and read for nothing, because Stata's note textbox reads
  `small_body`; `graphsize x/y` stays ratio-only, as the figure-proportions
  help documents.
- **AC-16.5** both modes agree on every value above: the per-scheme
  profiles are asserted equal in `test_scheme_rendered_output.py`, and the
  widened parity guard stays green.

### Found on the way

- `gsize note` is declared by every scheme and read by no Stata textbox;
  the note textbox is `small_body`. dash's `note_font_size` read the wrong
  key, and any fix that wired it would have drawn economist's notes at
  14pt where Stata draws 8pt.  *Corrected by WP-25 (24sep2026):* Stata's
  own drawing (`test/fixtures/scheme_visual/truth.json`) has economist's
  note at medlarge, 4.1660% of the graph height, in white: economist routes
  `note()` through `textboxstyle note reverse_big`, a filled box (BUGS.md,
  "economist's note() is drawn as a small black body note").
- economist's y axis is `axisstyle vertical_default vertical_nolinetick`,
  whose style file reads `draw_major_nlt_vgrid`/`draw_minor_nlt_vgrid`, not
  `draw_major_vgrid`; the same yes/no by coincidence, so the fixture now
  records the effective per-axis flag rather than the bare key.
- `SchemeParser._parse_file` takes `tokens[-1]` as the value, so a quoted
  RGB triple in a user scheme (`color major_grid "200 200 200"`, which
  Stata documents) is misread; the shipped files write hex and avoid it.
  Not fixed here; WP-17's territory. A `#include` in a user file is
  resolved against dash's own search path -- the working directory, then
  the fourteen translations -- never Stata's ado tree; an unresolvable one
  is skipped in silence. The help as first written said the file had to be
  self-contained and could include only a shipped name; the review
  corrected it to the resolution order above.
- The linewidth keyword ladder `_LWIDTH_MAP` keeps ratios that are not
  Stata's (dash thin .533 of medium, Stata .667; dash vthick 2.33, Stata
  4.667). Not fixed here; recorded as a follow-up. [WP-30 P1.12b, commit 37e9fa4: closed: line widths use Stata's ladder in Stata's units]
- s1rcolor's bar alpha 0.8 is scheme-driven (`intensity bar inten80`), not
  a defect; `p_mark_colors` equals `p_colors` in all 14 shipped schemes,
  so TR-16.5 exists for user schemes only. [WP-30 P1.2b, commit 870e778: s1rcolor's bar intensity (`intensity p#bar` through the p chain, inten80) is drawn as twoway draws it, an opaque blend towards black (`#cccc00`); the former alpha 0.8 read graph bar's `intensity bar`, which twoway's bar ignores, and compounded where bars overlap]
- The visual delta the risk table asks to state: every dashboard loses
  its minor grid; s1color, s1mono, s1rcolor and stmono1 lose every grid
  line; economist's title grows from 7pt to 17.28pt and its lines from
  1.2px to 6px; KPI cards take the scheme's legend colours (black with
  white text under s1rcolor, `#c6d3df` under economist); legends move to
  the scheme's clock position and columns; markers under the st* schemes
  shrink from 5.82px to 5.45px and economist's grow from 10.18px to
  12.73px; every text under s1rcolor turns white; figure titles take the
  scheme's heading colour and size.
- Stale line references, in G3-G6 and in this package as first written,
  were measured at `187a786`; at `52c473c` the minor-grid assignment was
  at `dash_render.py:2365` (served `:14617`), `_gsize` at `:2024`, `_lwidth`
  at `:2083`, the parser rows at `:2145-2268`, `default_color` at `:2274`,
  the `"#e5e5e5"` literal at `:9379`, the textbox literals at `:10018`, the
  card markup at `:12362` (served `:14910`, JS `:8163`).
- The adversarial review of this package (22sep2026) found, and the same
  package fixed before commit, each with its test written first in the new
  `test/test_scheme_review_fixes.py` unless said otherwise, and each an
  entry in `BUGS.md`:
  `layout(bs)` with a KPI or a filter widget was a blank page, pre-existing
  and S1: `_render_bootstrap_html` scraped the head of Bokeh's `file_html`
  with a non-greedy `<head>(.*?)</head>`, and Bokeh 3.9's inlined
  `bokeh-widgets.min.js` contains the literal `<head></head>` 189,588
  characters into the 378,283-character bundle, so the widgets script was
  cut there and never closed -- 3 `<script` opens against 2 `</script>`
  closes, no `/* END bokeh-widgets.min.js */` marker, `Uncaught
  SyntaxError` in the browser and a white page, at HEAD as well; the same
  page without a KPI rendered, and the checked-in sample pages were made
  with a bundle that lacked the string. Fixed by taking the head up to the
  last `</head>` (`rfind`); pinned by the open/close count and the END
  marker.
- Review: the scheme-placed legend was the outermost item on its side
  (under s2color `fig.below = [axis, note, caption, legend]`; under
  economist Bokeh's reversed `fig.above` put it between the title and the
  subtitle) where Stata's rings put it nearest the plot (`legend_ring 3`,
  note 4, caption 5, subtitle 6, title 7), and right-aligned (Bokeh's
  `top_right` default) where Stata centres a 6 or 12 o'clock legend; and a
  user `legend(rows(1))` with three series drew a 2x2 grid because the
  scheme's `ncols` 2 survived beside `nrows` 1. Fixed: inserted after the panel's axis, before every Label
  of the panel, `location = "center"`, and `rows()` alone sets `ncols`
  "auto" (`cols()` alone `nrows` "auto"); both modes; the parity corpus
  gains "legend(rows(1)) with three series under s2color".
- Review: `color p#mark` reached the Segments of spike, rcap, rspike,
  pcspike and pcarrow and the line halves of dropline and rcapsym, because
  those mappers asked `default_color` for "scatter"; invisible under the
  14 shipped schemes (`p#mark == p#`), a regression for a user scheme
  declaring `color p1mark`. Fixed: the lookup is gated on the glyph, marker
  glyphs only; the test writes a scheme with `color p1 #111111` and `color
  p1mark #22aa22` and reads each mapper's glyphs in both modes.
- Review: `_gsize` numeric formatted with `%g`, so `gsize body 0.00001`
  became `2.88e-05pt`, which Bokeh's FontSize validator rejects, and the
  whole figure aborted where HEAD floored to 6pt and drew. Fixed: fixed
  decimals, and a point size outside (0, 1000] falls back to the default
  with the `dash scheme:` warning. TR-16.2's "formatted `%g`" is therefore
  superseded.
- Review: `linewidth axisline` and `color foreground` were extracted,
  carried in all 14 files and the fallback dict, and read by nothing.
  Fixed for the axis line: `axis_line_width` is parsed and applied to each
  axis in `apply_to_figure`, and the parity `_chrome` profile records it.
  `color foreground` stays a carried directive with no consumer,
  deliberately, the second stated exception beside `note_font_size`
  (AC-16.4).
- Review: a user scheme's hostile placement values passed in silence --
  `clockdir legend_position 99` became "right", `numstyle legend_rows
  1000` a thousand rows, `linewidth major_grid -4` a zero-width, invisible
  grid -- while a bad colour warned. Fixed: `_init_properties` range-checks
  the clock (1-12), cols/rows (>= 0) and every linewidth (>= 0) with the
  `_color` warning shape; the hostile file in the test draws three warnings
  and the defaults.
- Review: after a filter move the JS-rebuilt KPI card lost its value div's
  `id="kpi_val_<name>"` (pre-existing; every other byte matched
  `_dash_kpi_card_html` over 18 scheme-by-option combinations). Fixed: the
  escaped name rides in `kpi_config` and the template emits the id; the
  test diffs the Python card against a JS-template rendering with the same
  config.
- Review: the served by() panel title was `html.escape(go["title"])`, so
  `title("By") by(foreign)` served `&quot;By&quot; -- Domestic` where the
  saved page showed `By -- Domestic` (pre-existing; the parity corpus had
  no by() case with a title). Fixed: the served template uses the parsed
  title text, as `_dash_figure_title` does; the parity corpus gains "by()
  with a graph title".
- Review, Stata side: `dash bar price` and `dash scatter mpg` (and `line`,
  `lfit`, `dot`, `spike` with one variable) registered with rc 0 and a
  `dash build` died with a Python `KeyError: ''` in `map_bar`, r(7102),
  where `twoway bar price` and `twoway scatter mpg` refuse at parse time
  with r(102) (`twoway bar` with no variable: `varlist required`, r(100)),
  measured with the console binary. Fixed in `dash.ado`: a two-variable
  plot type given one variable is refused at registration with `dash:
  <type> requires a y and an x variable (got: <varlist>)` and twoway's own
  r(102); the one-variable types (histogram, kdensity, tsline, function and
  the rest) are untouched; cert cases OV-135 to OV-141 in
  `test_option_validation.cscript` (bar, scatter, a short segment inside a
  multi-segment command, `line price if foreign`, and histogram and
  kdensity as the one-variable controls).
- Review, docs: seven statements in this package, `BUGS.md`, `GAPS.md` and
  the help were corrected: the `#include` resolution order (the bullet
  above), `test_kpi_security.py`'s seven `#212529` pins that no owner had
  restated (7 failed, 25 passed against the tree), the note colour (`color
  small_body`, not `color body`), the full list of eighteen directives the
  shipped files lacked, the helper's name (`_dash_apply_axis_spec`; no
  `_dash_apply_one_axis` exists), `test_scheme.py`'s minor-grid test being
  new rather than restated, and five line ranges in BUGS G4/G5 that were
  off by two or three at `52c473c`.
- Not fixed here, two follow-ups from the review, both resolved by WP-17.
  `s2color8`, the session scheme `cscript` sets (`c(scheme_cscript)`,
  cscript.ado:35), was not among the 14 translations, so every unschemed
  `dash build` under the certification runner wrote `dash: 's2color8' is
  not a known theme or scheme; using s2color` into the Stata log -- 41
  occurrences across 11 of the 12 certification logs the review read, at
  HEAD as well, because `dash.ado` forwards `c(scheme)` as the session
  scheme; WP-17 ships s2color8 as one of its six new translations
  (TR-17.3), so the line is gone (`test_custom_scheme.cscript` CS-11: `set
  scheme s2color8` then a build, rc 0 and no warning). And
  `test_render_log_clean.cscript` asserted only on `__builtins__`,
  `DashRenderer`, `GlyphMapper` and a line count, so it tolerated a
  `UserWarning` line; it now asserts that none appears, so a
  session-scheme warning is caught rather than tolerated.

### Verification, measured 22sep2026

| Suite | Result |
|---|---|
| `test_scheme_rendered_output.py`, all 14 schemes, both modes | 826 passed |
| `test_scheme_review_fixes.py` (the review's ten items, written first) | 102 passed |
| `test_scheme_fidelity.py`, 132 property units per scheme against Stata's files | 90 passed |
| Parity guard `test_mode_parity.py`, profile widened, corpus + 6 | 2114 passed, 1 skipped (layout(bs), stated), 5 xfailed |
| `test_option_validation.cscript` OV-01 to OV-141 plus the corpus arbiter | ALL CHECKS PASSED (210 checks) |
| Full Python suite | 7578 passed, 56 skipped (stated reasons), 6 xfailed, 0 failed |
| Full certification suite | 41 passed, 0 failed, 0 skipped |

Between the first implementation and this commit an adversarial review
found and fixed: the scheme-placed legend sitting outside the note and
caption and flush right (Stata keeps it nearest the plot, centred); a
user rows() fighting the scheme's columns; the marker colour reaching
the spike-family segments; a tiny numeric gsize aborting the figure; a
served by() panel title carrying html entities; and, older than this
package, every Bootstrap page holding a KPI or a filter widget blank in
the browser, and a one-variable bar or scatter registering with rc 0
and dying at build.

---

## WP-17 · Scheme coverage and custom schemes — DONE

**Gaps closed:** G1, G2, G8, F4's bare-name row, WP-05's AC-05.3 · **Severity:** S2/S3 · **Effort:** M · **Depends on:** WP-05

> **User story.** As a user with a house scheme, I want to point `dash` at it
> the way the help says I can.

### What was measured before any code changed

The baseline, 22sep2026 at `0112221`, with the console binary, a
`mytheme.scheme` in the working directory that is a copy of s1rcolor
(black background, white heading) and the session scheme read back from
`c(scheme)` (scratchpad `wp17/probe/probe.log`, `probe2.log` and the
rendered pages):

| entry point | value | at `0112221` |
|---|---|---|
| `dash scatter ..., scheme(mytheme)` (immediate) | bare name, file in the CWD | rc 0; `dash: 'mytheme' is not a known theme or scheme; using s2color`; the figure drawn with mytheme (`background_fill_color` `#000000`) under s2color page chrome (`.db-title { color: #1e2d53 }`, `#eaf2f3`): half applied |
| `dash scatter ..., scheme(mytheme.scheme)` | file name | works throughout (`.db-title { color: #ffffff }`, no s2color colour on the page) |
| `dash build, scheme(mytheme)` | bare name | rc 0, the warning, s2color throughout |
| `dash build, scheme(mytheme.scheme)` | file name | works |
| graph registered with `scheme(mytheme)`, then `dash build` | bare name | half applied, as the immediate route |
| `scheme(nosuchthing)` / `theme(nosuchtheme)`, either entry point | a typo | rc 0, the warning, s2color; two warnings on the immediate route, the gate's and the per-graph swap's (`scheme 'nosuchthing' was not found for graph (unnamed); using s2color`), each a raw Python block naming `dash_render.py` and a line |
| `scheme(d3colors)` | one of 129 third-party `scheme-*.scheme` files in `PLUS/s` | rc 0, the warning, s2color: dash reads its own translations and the working directory only, by design (WP-05) |
| `set scheme s2color8`, then any unschemed dash | inherited `c(scheme)` | rc 0, `'s2color8' is not a known theme or scheme; using s2color`; `cscript` sets s2color8 (`c(scheme_cscript)`, cscript.ado:35) for every session, so the runner's log of the WP-16 verification run (`test/run_all_cscripts.log`, 41 passed) carried the line 49 times across 13 of the 41 scripts |
| `set scheme d3colors`, then any unschemed dash | inherited third-party | the same line with that name |

`twoway scatter mpg weight, scheme(nosuchthing)` is rc 0 with `(note:
scheme nosuchthing not found, using s2color)`, `set scheme nosuchthing` is
r(111) `scheme nosuchthing not found`, and `twoway ..., scheme(s2color8)`
draws it: dash had copied twoway's note for the explicit case where a saved
dashboard wants `set scheme`'s refusal, and could not draw a scheme Stata
draws.

The cause, read at `0112221`: `_resolve_scheme_name` (`dash_render.py:8941`)
takes `scheme()`, then `theme()`, then a graph's `scheme()`, then
`session_scheme`, and its unknown-name branch (`:9018-9029`) rejected any
name that was neither a `_THEME_SCHEME_MAP` alias (`:8926-8938`) nor one of
the fourteen `_BUILTIN_NAMES` (`:1624-1631`) unless it ended in `.scheme`,
blanking the name and warning, before `SchemeParser._resolve_path` (`:1910`,
whose bare-name branch at `:1930-1931` tries `<cwd>/<name>.scheme` first and
was added for exactly this route) could run. The per-graph swap in
`_make_figure` (`:12317-12325`) calls `resolve_or_fallback` directly, so a
graph-level name reached the file for the figure while the page chrome had
already fallen back. On the Stata side `_dash_prepare_spec` (`dash.ado:2969`)
validated `layout()`, `link()` and `filterposition()` and only escaped
`scheme()` and `theme()` (`:3357-3369`); a graph-level `scheme()` was one of
the keys written verbatim (`:1669`); WP-15's `_dash_validate_value` (`:1257`)
had no kind for either. The session scheme took the same branch and the same
words as an explicit one, so a user who typed no `scheme()` read a warning
about a name they never typed.

For G2: dash's `s2color.scheme` carried 136 directives (118 at `187a786`;
WP-16's eighteen) against Stata's 2060, 135 to 166 across the fourteen
files, every `color` line hex, no `#include` directive in any file, and the
`sources` map of `test/fixtures/scheme_truth.json` the only record of which
directives were transcribed and which inferred. For G1: s2gmanual and
s2mono are the only two StataCorp schemes that declare a `lineplot`
directive at all (s2mono `color plineplot` and fifteen `linepattern
p#lineplot`; s2gmanual fifteen `color p#lineplot` and fifteen `linepattern
p#lineplot`), so s2gmanual is the one scheme whose `p_lineplot_colors` must
come from a declared directive rather than the `p#stub` fallback. The six
files to add: s2manual and s2gmanual `#include s2mono`, s1manual `#include
s1mono`, s2color8 and sttrans `#include s2color`, stgcolor_alt `#include
stcolor_alt`.

### Technical requirements, as delivered

- **TR-17.1 (G8/F4)** `SchemeParser._BUILTIN_NAMES` is the twenty, and
  every "fourteen" comment in `dash_render.py` says twenty. A new classmethod
  `SchemeParser.can_resolve(name)` says whether `_resolve_path(name)` would
  succeed, with no warning and no exception (a name that fails containment
  is False). The unknown-name branch of `_resolve_scheme_name` asks it
  first, so a bare working-directory name, a `.scheme` file name and a
  shipped name pass untouched and only a name that resolves to nothing
  warns. The warning keeps the substring `is not a known theme or scheme`
  and now says why the name can be one the user never typed, in one line:
  `dash: 's2color8' is not a known theme or scheme; it was inherited from
  the session (c(scheme)) because no scheme() or theme() was given, or came
  from a spec built without dash.ado; using s2color. Themes: ... Schemes:
  ...`. The per-graph swap and the served builder are unchanged; with the
  gate agreeing, a working-directory bare name gives the same page chrome
  (`css_block()` colours) and the same figure in both modes.
- **TR-17.2 (G8)** One list in one place: `_dash_shipped_schemes`, between
  `// BEGIN shipped schemes (WP-17)` and `// END shipped schemes (WP-17)`,
  hands back `_dash_schemes` (the twenty, lower case) and `_dash_themes`
  (`default clean mono dark economist sj`). WP-15's table gains the kind
  `scheme`: accepted when the lower-cased value is a shipped name or a
  theme, with or without the `.scheme` extension (`scheme(s2color.scheme)`
  needs no file in the working directory); else when it carries no `/`,
  `\` or `..` and `confirm file` finds it in the working directory, as
  written if it ends in `.scheme` or with `.scheme` appended (nothing
  normalised, the value passed through); else
  refused, `P: scheme() must be a shipped scheme, a theme, or a .scheme file
  in the working directory (got: V)`, r(198). The graph rule token
  `scheme=scheme` puts the immediate route, a registered graph and a
  per-segment `scheme()` through the existing validation loops;
  `_dash_prepare_spec` validates `scheme` with the same kind and `theme` as
  an `enum` of the six themes beside its `layout()`/`filterposition()`
  checks, for `dash build` and `dash serve` alike, before anything is
  written. The session's `c(scheme)` is inherited when nothing is requested
  and stays warn-and-fall-back, never fatal (129 third-party schemes on this
  machine alone). Third-party schemes in `PLUS/s` are deliberately not read;
  the help says so.
- **TR-17.3 (G1)** `scripts/extract_scheme_truth.py`'s `SCHEMES` is the
  twenty; the fixture is regenerated and the six files created by the same
  writer (the `update_scheme_file` "created" path: the same header, the
  include chain stated, every colour hex), the fourteen re-run reporting no
  changed value. `test_scheme_fidelity.py`'s `EXPECTED_SCHEMES` is the
  twenty, and an anchor test reads the fixture's `lineplot_declared` and
  `sources` to check that s2gmanual's `p_lineplot_colors` and patterns come
  from its declared directive, not the inference. The grid truth tables in
  `test_scheme_grids.py` / `test_scheme_grid_measured.py` are extended to
  twenty from the fixture's effective flags where they enumerated the
  fourteen.
- **TR-17.4 (G2)** The fixture's per-scheme `sources` map is written into
  every shipped file as a `* provenance:` block, one line per directive,
  `transcribed from scheme-X.scheme:<directive>` or `inferred: <rule>`, by
  the same writer, so a re-run is a no-op. `dash.sthlp` says what the
  shipped files are (dash-format translations, about 135 directives,
  flattened, every colour hex, sttrans's with its `%20` opacity kept,
  provenance comments; not drop-in Stata scheme
  files, never read by `graph`), lists the twenty with one-line descriptions
  taken from Stata's own file headers, documents the custom-scheme rule on
  every entry point, the refusal, the inherited-session warning, and that
  third-party schemes in `PLUS` are not read; the WP-16 sentence that named
  `s2color8` as an `#include` dash would skip is corrected, since it ships.
- **TR-17.5** Tests and records. New `test/test_scheme_resolution.py`,
  written first: in a temporary working directory holding `mytheme.scheme`
  (s1rcolor with `color background #123456`), build-level `scheme(mytheme)`
  and `scheme(mytheme.scheme)` and graph-level `scheme(mytheme)` in both
  modes give a figure with `border_fill_color` `#123456` and a
  `css_block()` containing it, with no warning; `scheme(nosuchthing)` from
  a spec dict gives exactly one warning carrying the inherited-session
  sentence; `_BUILTIN_NAMES` equals the extractor's `SCHEMES`,
  `test_scheme_fidelity.EXPECTED_SCHEMES` and the Stata list parsed from
  between the sentinels; every one of the twenty resolves with no warning
  in both modes; `can_resolve("../x")` is False and `can_resolve("mytheme")`
  True there. New `test/test_custom_scheme.cscript`, CS-01 to CS-13 (runner
  block 42), in a temporary directory it `cd`s into with `mytheme.scheme`
  and a `scheme-zzdashtest.scheme` (`#include s2color`, so `set scheme
  zzdashtest` finds it). `test_theme_escaping.cscript` THM-01 to THM-06
  restated to r(198) at the gate. `BUGS.md`: the silent typo (G8) written
  first, then the half-applied bare name, the s2color8 warning in the
  certification logs, and `theme()`'s hostile strings; `GAPS.md` G1, G2 and
  G8 closed with the table above and F4's bare-name row cross-referenced.

### Acceptance

- **AC-17.1** a `mytheme.scheme` in the working directory is found by
  `scheme(mytheme)` on `dash scatter` and on `dash build`, and by a
  graph-level `scheme(mytheme)`, the page and the figure from the same
  file: `test_custom_scheme.cscript` CS-01 to CS-05 (`#123456` present,
  s2color's `#1e2d53` absent, no warning) and `test_scheme_resolution.py`
  in both modes.
- **AC-17.2** `scheme(nosuchthing)` is r(198) naming `scheme()` on the
  immediate route (CS-06), on `dash build` (CS-07) and on the `dash serve`
  spec path (CS-13); `theme(nosuchtheme)` r(198) naming `theme()` (CS-08);
  `scheme(../mytheme)` r(198) (CS-09); an untranslatable session scheme is
  rc 0 with exactly one warning that mentions the session and an s2color
  page (CS-10); `set scheme s2color8` then a build is rc 0 with no warning
  (CS-11); the hostile `theme()` values of THM-01 to THM-06 are refused
  with no traceback and nothing written; `test_scheme_resolution.py` pins
  the one warning from a spec dict.
- **AC-17.3** all twenty ship, translate faithfully and render:
  `test_scheme_fidelity.py` over the twenty against Stata's files with the
  s2gmanual anchor; `test_scheme_rendered_output.py` over the twenty in both
  modes; CS-12, every shipped name on `dash build, scheme()` with rc 0 and
  no warning; the WP-05 containment tests in `test_scheme.py` still pass.

### Found on the way

- The refusal is stricter than `twoway`, whose `scheme(nosuchthing)` is rc
  0 with a note, and matches `set scheme`, which is r(111); the help says so
  and why (a saved dashboard in the wrong scheme is not a note the user
  sees). `theme()` was the one option whose hostile values WP-05 had made
  survive the trip to Python (THM-01 to THM-06 asserted rc 0); an alias
  table of six names has no arbitrary values, so those cases are refused at
  the gate now, and the escaping helper stays for the values that pass.
- The immediate route warned twice for one typo, once from the gate and
  once from the per-graph swap; both go with the Stata refusal.
- s2color8 is not s2color: Stata's file is `#include s2color` with the "8"
  colour variants substituted (`ltbluishgray8` `225 230 240` for the
  background and grid against `ltbluishgray` `234 242 243`, `navy8` `39 63
  111` for p1 against `navy` `26 71 111`, `bluishgray8` for the boxes and
  p15), so the fallback under `cscript` was a near miss, not the scheme.
- sttrans declares every `color p#` with a `%20` opacity suffix (`"26 71
  111 %20"`, Paul Tol's muted palette), and Stata draws it so: `twoway
  scatter mpg weight, scheme(sttrans)` exported to SVG carries its markers
  at fill-opacity 0.20 (scratchpad `wp17/ownerA/`). At `0112221` the
  extractor stripped the suffix, recorded `opacity suffix %20 ... not
  folded into hex` in `unresolved` and wrote the opaque hex; once the
  extractor kept it, the shipped `sttrans.scheme` wrote `color p1
  #1a476f%20` (with its line, bar, mark and lineplot twins) and the
  renderer dropped it, because `SchemeParser._color` resolved a scheme
  colour through `translate_mcolor`, which discards a `%NN` suffix, so the
  figure drew sttrans opaque in both modes while the file was faithful.
  Now the declared opacity is carried into the glyphs in both modes for
  the layers that take a scheme alpha (scatter and connected markers,
  line, connected, bar, area, histogram): a colour opacity the scheme
  declares wins over the intensity approximation, and a user's
  `mcolor(x%NN)` or `malpha()` still wins over the scheme. The range,
  spike, fit, band, density, function, scatteri, pci, dot and rscatter
  layers still draw sttrans opaque (they apply no scheme alpha); routing
  them through `default_alpha` is a follow-up. The fixture records it in `p_colors_opacity` and its twins,
  the help's sttrans row says dash carries it, and `BUGS.md` has the entry
  ("sttrans's twenty-percent colour opacity ...").
- "About 118 keys" in this package as first written was stale by one
  package: 136 at `0112221` for s2color, WP-16 having added eighteen.
- `test_render_log_clean.cscript` tolerated a `UserWarning` line (it
  asserted on `__builtins__`, `DashRenderer`, `GlyphMapper` and a line
  count), as the WP-16 review recorded; with s2color8 shipped the line it
  tolerated is gone, and it now asserts that no `UserWarning` line
  appears, closing that follow-up.
- Stale line references: this package as first written cited `187a786`
  (`_resolve_scheme_name`'s gate at `dash_render.py:7967-7970`, the CWD
  bare-name branch at `:1704-1716`, the swap at `:9484-9487`); at `0112221`
  they are `:8941` (the gate `:9018-9029`), `:1910` (the bare-name branch
  `:1930-1931`) and `:12317-12325`, with `_BUILTIN_NAMES` at `:1624-1631`
  and `_THEME_SCHEME_MAP` at `:8926-8938`; `dash.ado`'s pass-through at
  `:3357-3369` and `_dash_validate_value` at `:1257`.
- Not fixed here, one follow-up seen in the certification log once the
  session-scheme warning was gone: three example files
  (`examples/bootstrap_stacked.do`, `multi_graph_dashboard.do`,
  `kelly22ex_categorical.do`) ask for `ms(inverted_triangle)`, a Bokeh
  marker name that neither Stata's symbolstyle list nor dash's translator
  knows, so those layers draw the scheme's default symbol with a note in
  both modes. Either the examples take a Stata symbol or dash's marker
  map admits the Bokeh names as a documented superset; the examples pass
  (WP-27) decides.

### Verification, measured 22sep2026

| Suite | Result |
|---|---|
| `test_custom_scheme.cscript` CS-01 to CS-14 (both entry points, refusals, the session scheme, all twenty names) | ALL CHECKS PASSED |
| `test_scheme_resolution.py` (both modes; one shipped list in dash.ado, the extractor and the fixture; the carried opacity) | 266 passed |
| `test_scheme_fidelity.py`, twenty schemes against Stata's files | 175 passed |
| `test_scheme_rendered_output.py`, twenty schemes, both modes | 1162 passed |
| `test_render_log_clean.cscript`, now asserting no warning line | ALL PASS |
| Parity guard `test_mode_parity.py` | 2114 passed, 1 skipped (layout(bs), stated), 5 xfailed |
| Full Python suite | 8307 passed, 58 skipped (stated reasons), 6 xfailed, 0 failed |
| Full certification suite | 42 passed, 0 failed, 0 skipped; no session-scheme warning in any log |

---

## WP-18 · Statistical fidelity — DONE

**Gaps closed:** A4, A5, and A3 finished (weights honoured, not only named) · **Severity:** S2 · **Effort:** L · **Depends on:** WP-02

> **User story.** As a researcher, I want `mspline` and `fpfit` to be the
> estimators Stata documents, and weights to be honoured.

### What was measured before any code changed

The baseline, 23sep2026 at `fe3b12a`, with the console binary
(`scratchpad/wp18/measure_result.json`: keys `truth`, `estimators`,
`fidelity`, `ado`; `scratchpad/wp18/probe/fidelity.json`), dash's mappers
called exactly as `test_statistical_truth.py` calls them and every error
a fraction of the raw y range (auto 29, census 184824, sp500 407.93,
nlsw88 39.74; for kdensity, Stata's density range). The truth is the
serset of the saved `.gph`, read back into the regenerated
`test/fixtures/stat_truth.json` (26 to 52 sections; the 25 pre-existing
sections byte-identical by serialisation; `_meta.self_checks` 14 of 14
true; every probe rc 0, nothing skipped):

| layer | at `fe3b12a` | Stata's rule (source) | measured gap |
|---|---|---|---|
| `mspline` | PCHIP through every distinct-x/mean-y point on a 200-point grid; `bands()`/`n()` in the options dict and read by nothing (`dash_render.py:6985-7057`) | `as_median_bands, bands(B)` then `as_spline, splinepts(n)`: cross medians of B equal-width bands (K non-empty), a cubic spline through the K knots at the knots plus n equally spaced points between each pair, (K-1)n + K points; B default `round(min(10 log10 N, sqrt N))` raised to `min(N, 2)` (`_gs_default_bands.ado:5-17`); n default 10 (`twoway_mspline_parse.class:34`); the spline is serset 2 of the `.gph`, serset 1 dropped by `derived_serset.class` | 14.0 mpg max error on auto default; 9.2 bands(8), 11.5 bands(8) n(5), 5.3 bands(4); auto default 89 points, nlsw88 342 (K 32 of 34), census bands(20) 122 (K 12); a natural cubic spline through the knots reproduces all 20 probes to 4.1e-6 (auto) and 9.65e-6 (nlsw88) abs against float32 sersets; not-a-knot 2.76, clamped 1.62, PCHIP-through-knots 0.96, Akima 1.02 |
| `fpfit` | `_fit_fp2` loops pairs including (p, p) but the design has no repeated-power column, so `[1, z, z]` is rank 2 of 3 and collapses to FP1; x <= 0 dropped to NaN; no scaling; `_fp_grid` capped at 1000 (`:5357-5408`, `:7520-7550`) | `fracpoly regress y x [w]` then `fracpred` at every distinct sorted x; powers -2 -1 -.5 0 .5 1 2 3, degree 2 by deviance over all 36 pairs p1 <= p2; (p, p) is `x^p` and `x^p ln x` (`ln^2 x` at 0) (`fracgen.ado:193-212`); `frac_xo.ado:81-106`: if min(x) <= 0 shift by (smallest positive spacing of sorted x) - min(x), then ALWAYS scale by `10^(sign(log10 s) int(abs(log10 s)))`, s the range | auto (-2,-1) vs Stata (-2,-2): 9.0e-3; census (0,.5) vs (1,3): 3.9e-2 (cond 3.6e21 unscaled; RSS at (1,3) 7.39e10 raw, 1.67e9 scaled by 1e7); nlsw88 (1,3) vs (2,2): 2.7e-2, and 1000 grid points where Stata has 1546; sp500 (-.5,0) both, 1.5e-7; with the repeated-power column and the scaling, 1.5e-7 on all four; `xs = weight - 3000` (35 non-positive): shift 1250, scale 1000, (0,0), twoway rc 0; `xz = mpg - 12`: shift 1, scale 10, (-2,-2) |
| `fpfitci` | bootstrap percentile band, 200 resamples, seed 42 (`:5531-5535`, `_bootstrap_ci` `:3282`) | `fracpred, stdp` t band, `invttail(df_r, (100 - level)/200)`, df_r = N - 3 (`twoway__fpfit_serset.ado:31-50`); stdf/stdr refused r(198) | band off by 1.1e-1 (auto), 2.3e-1 (census), 1.17 (sp500: past the y range at the first sample), 1.1e-1 (nlsw88); width ratio 0.67 to 4.72; analytic stdp reproduces auto to 6.3e-8 |
| `lowess` | statsmodels `lowess(frac=bw, it=3)`: nearest-by-distance window, three robustness iterations, tied x identical; `mean`/`noweight`/`adjust`/`logit` unread (`:4986-5061`) | [R] lowess: stable sort by x; k = int((N bw - .5)/2); window by INDEX; tricube on d/(1.0001 max d); local line at x_i (weighted mean with `mean`; unit weights with `noweight`); no iterations; `adjust` = smooth x mean(y)/mean(smooth) (`lowess.ado:203-209`); `logit` clamps to 1/N, 1 - 1/N under the .0001 rule then ln(s/(1 - s)) (`:213-221`), adjust before logit; bwidth outside (0, 1) -> .8 (`:75-78`); ties in dataset order after a stable sort | 1.08e-1 (auto, 3.13 mpg), 1.19e-1 (census), 1.92e-1 (sp500), 3.67e-2 (nlsw88) on the default; `mean` drawn as the default 1.46e-1 (auto), 4.36e-1 (census); it = 0 alone leaves 0.62 mpg; the rule reproduces all 20 probes to 1.5e-10 abs |
| `lfitci`/`qfitci` | stdp band only | stdp (default), stdf = sqrt(stdp^2 + s^2), stdr = sqrt(s^2 - stdp^2) (missing where negative); two together r(198) `may not combine` | stdp exact today (2.7e-7, 2.8e-7); stdf/stdr absent (auto lfitci at x = 1760: stdp [27.34, 30.39], stdf [21.84, 35.89], stdr [22.18, 35.55]) |
| `lpoly` | `np.polyfit(w=K)`, which squares the kernel weight; a point drawn with one positive-weight observation; 200-point grid, `n()` unread (`:5108-5172`) | weighted least squares needs w = sqrt(K); a grid point is missing when fewer than 2 observations have positive kernel weight; `n()` points over the observed range, default min(N, 50); aw normalised to mean 1, fw raw, local weight K_i w_i (`lpoly.ado:295-303`) | degree(1) at Stata's own bandwidth 2.8e-2 (auto), 2.9e-2 (sp500), 3.5e-2 (nlsw88), 1.3e-15 with sqrt(K); degree(0) exact (5.6e-15); dash finite at 5 of 11 samples where Stata is null (auto bwidth(5)); as drawn 1.58e-2 (auto default); the ROT bandwidth -9.7% (auto), +14.2% (census), +5.7% (sp500), +6.8% (nlsw88) against `r(bwidth)`, in compiled Mata, not changed |
| `histogram` | no `discrete`; no weights | `discrete`: each distinct value its own bin, width = `width()` or the smallest positive spacing of the distinct values (1 if a single value), start = min - width/2 (`twoway__histogram_gen.ado:109-164, 200-231`); `discrete` + `bin()` r(198); fweight only (aw/pw/iw r(101)); N = sum fw | absent: auto rep78 discrete 5 bins of width 1 from .5, densities .02899 .11594 .43478 .26087 .15942; auto mpg 30 bins, 21 occupied; `[fw=int(price/1000)]` N 417, 20 bins of width 1.45 |
| `kdensity` | grid [min - 3h, max + 3h] x 300; no weights (`:5717-5828`) | twoway: [min, max] x n() (default 300); aw/fw honoured (weighted sd and percentiles in the bandwidth, N = sum fw; density = sum w K / (sum w h)); pw/iw r(101) | estimator exact (2.7e-12; bandwidth 3.4e-16) but as drawn 1.0 on census bwidth(2), grid step 617 against a kernel support of 4.5; 1.0e-2 sp500 bwidth(2); else below 1.2e-3 |
| `lfit`/`qfit` | unweighted | aw normalised to sum N (df_r = N - 2), fw replicated (N = sum w), pw = aw point estimates with HC1 robust stdp for a band | exact unweighted; auto `[aw=price]` lfit -0.0054960, 37.6987 in `weighted` |
| `mband` | exact (1.5e-7) | weights accepted and inert (aw/fw/pw rc 0, iw r(101)) | none |
| weights | parsed, type named in the note, expression discarded (`dash.ado:1059-1110`, `:1976-1996`; `dash_parse.mata:768-772`; `dash_render.py:10438`) | accepted by lfit qfit lfitci qfitci fpfit fpfitci lpoly lpolyci kdensity histogram mspline mband, each with twoway's own type list; twoway accepts an expression (`[aw=price+1]` rc 0) | not applied; `[iw=price]` on scatter and `[pw=price]` on histogram rc 0 with the note where twoway is r(101) |

Three premises of this package as first written were false, measured in
the 18 x 4 grid of `weight_acceptance` (72 probes, `weight_acceptance_table`):
**`lowess` takes no weights in Stata** (`twoway lowess` and `lowess` r(101)
`weights not allowed` for aw, fw, pw and iw; `lowess.ado:9`,
`twoway_lowess_parse.class:35`); **`histogram` takes `fweight` only**
(aw/pw/iw r(101) on `histogram`, `twoway histogram` and
`twoway__histogram_gen`); **`iweight` is refused by every twoway
statistical type**, and `pweight` by `kdensity`, `lpoly` and `lpolyci`.
TR-18.5's list is corrected below. Two more things the measurement
corrected: the old fixture's `unverified` block said the default
band-count rule was in no `.ado` -- it is `_gs_default_bands.ado:5-17`,
which both `mband` and `mspline` call (`rules_wp18.mspline.bands_default`);
and the help's "`bands()` 1 to 200 is twoway's own limit" was false --
twoway has no cap, the cap is dash's (`dash.ado:1251`). **Corrected by
the coordinator's review:** the help was right. twoway mband and mspline
refuse `bands(0)` and `bands(250)`, "bands must be between 1 and 200",
r(198); the cap is twoway's (see "Found by the coordinator's review").

### Technical requirements, as delivered

The contract is `scratchpad/wp18/DESIGN.md`; the owners were disjoint
(Stata side, renderer, Python tests, docs) and the coordinator's
verification run below is the record of what landed. Principle: every
statistical layer is the estimator Stata documents, checked against
Stata's own plotted points in both render modes through the one
`GlyphMapper`; an option that changes an estimate is honoured or refused,
never accepted and ignored; what already matched Stata was locked by the
fixture before it was touched.

- **TR-18.1 (A4)** `map_mspline` is Stata's estimator: the cross medians
  of `bands()` equal-width bands (the loop factored out of `map_mband`
  into a shared helper; non-empty bands only; default count by
  `_gs_default_bands`'s rule, the one `_mband_default_bands` already
  had), a numpy cubic spline through the K knots -- the end condition
  MEASURED against the fixture's curves, natural first, not-a-knot
  second, shipping the one that matches to better than 1e-6 relative or
  the closest with its residual recorded in the help -- evaluated at
  (K-1)n + K points with `n()` honoured (default 10; `n(1)` accepted, the
  rule token `n=int,1,10000@mspline`) and nothing drawn when K < 2. scipy
  is no longer needed for it. `bands()` keeps dash's 1..200 cap, now
  documented as dash's own. *Review corrections: `n()` is 1..300, as
  twoway (`n=int,1,300@mspline`); one or two knots draw the knots alone;
  the 1..200 `bands()` cap is twoway's.*
- **TR-18.2 (A4)** `_fit_fp2` builds the repeated-power design (`x^p`,
  `x^p ln x`; `ln x`, `ln^2 x` at p = 0), searches all 36 pairs by RSS
  (weighted RSS under a weight) and predicts at every distinct sorted x,
  the 1000-point cap removed or raised past 1546 (delivered:
  `_FP_GRID_MAX` 20000), its reason (the bootstrap) gone. `_fp_report_unsupported` keeps refusing `bwidth()` and
  `degree()`.
- **TR-18.3 (A4)** `_fp_prepare` applies `frac_xo`'s shift when
  min(x) <= 0 and its power-of-ten scaling on every fit; no row is
  dropped for its sign. `map_fpfitci` draws the t band on the analytic
  stdp of the FP design with N - 3 degrees of freedom (HC1 under
  pweights; *review correction: N minus the rank the design supports,
  and no band at df 0*); `_bootstrap_ci` remains for `lpolyci` and the `qfitci`
  LinAlgError fallback only.
- **TR-18.4 (A5)** The seven sub-options are declared in `dash.ado`
  as twoway declares them (`DISCrete`; `STDP STDF STDR` with no
  abbreviation; `NOWeight Adjust LOgit`; and `MEan`, one letter longer
  than twoway's `m` because the same parser declares `Msymbol()` and
  `test_abbreviations.py` refuses a prefix two options could claim --
  `dash.ado:774-776` and the comment at `:997-1004`), sreturned,
  carried as flags in the plot JSON (`"discrete":"discrete"`), mirrored
  in `scripts/regen_option_surface.py`'s lists, honoured by the renderer
  in both modes, and refused outside their plot type with twoway's r(198)
  `option X not allowed` through a flag-applicability list in
  `_dash_option_rules` (`discrete@histogram`,
  `stdp|stdf|stdr@lfitci|qfitci`, `mean|noweight|adjust|logit@lowess`)
  checked in `_dash_validate_opts`; `stdp`, `stdf`, `stdr` are mutually
  exclusive (r(198) `may not combine`); `discrete` with `bin()`/`bins()`
  is r(198). With them: `map_lowess` is Stata's smoother
  (`GlyphMapper._stata_lowess`: stable sort, index window, tricube on
  1.0001 max d, local line or `mean`, `noweight`, `adjust`, `logit`,
  ties in dataset order), statsmodels no longer imported for it;
  `map_lfitci`/`map_qfitci` draw stdp, stdf or stdr from the values they
  already had; `_histogram_grid` has the discrete branch and the
  standalone page's JavaScript recompute keeps working on its edges;
  `_compute_lpoly_fit` weights by sqrt(K), leaves a grid point missing
  below two positive-weight observations, and evaluates on `n()` points
  with Stata's default min(N, 50) (*review correction: 50, capped at the
  DATASET's _N, and _N whenever the dataset has fewer than 50 rows --
  `twoway_lpoly_parse.class:56`*); `map_kdensity` uses twoway's grid
  [min, max] x n().
- **TR-18.5 (A3)** Weights are honoured on lfit qfit lfitci qfitci fpfit
  fpfitci lpoly lpolyci kdensity histogram mspline mband with twoway's
  own acceptance per type, and refused in Stata where twoway refuses
  them, with rc 101 and twoway's wording (`iweights not allowed`
  everywhere; `weights not allowed` on lowess; `aweights not allowed` and
  `pweights not allowed` on histogram; `pweights not allowed` on
  kdensity, lpoly, lpolyci); on scatter and the other glyph layers the
  WP-13 note stays. The parsers sreturn the expression (stripping the
  leading `= `); `_dash_process_segment` saves it across `sreturn clear`,
  expands and confirms it as ONE existing variable (anything else:
  `dash: [aweight=price+1] must name one variable; dash cannot evaluate
  a weight expression. Generate it first: generate double w = price+1`,
  r(198)), checks fweight integrality (r(401)), runs the option
  validation also for a weight-only segment, makes the note conditional
  on the type not honouring weights, and splices
  `"weight":"<type>","wexp":"<var>"` into the plot's options ONLY when a
  weight is present (the unweighted JSON is pinned byte for byte by
  `test_varlist_expansion.cscript` and `test_pipeline_integration.py`);
  `_dash_extract_vars` gains `"wexp":`, one edit for both export routes;
  `_DASH_OPT_VAR_KEYS` gains `"wexp"`, one line for both modes' sources;
  `_layer_weights` hands each mapper (w, type): aweights normalised to
  sum N, fweights replicated where a closed form needs counts (N = sum
  w, df from it), pweights the aweight estimates with HC1 for the bands;
  `_masked` returns w with a joint NaN drop and drops w <= 0 with a note.
  Weights on mspline and mband are accepted and inert, as in Stata.
- **TR-18.6** What already matched Stata was locked first: the fixture
  regenerated by `scripts/extract_stat_truth.do` (1485 to 2815 lines;
  curves written in 100-value chunks because a record line longer than
  about 5,300 characters came back from Stata with a space inserted
  every ~5,290 characters, 117 corrupted tokens on the first run, 0
  after chunking), 26 to 52 sections, the 25 pre-existing ones
  byte-identical, so `_fit_grid`'s observed-range rule,
  `_stata_bin_count`, `_stata_kde_bandwidth`, the ROT bandwidths,
  `_t_ppf`, `_stata_percentile`, `mband`'s cross medians and the stdp
  bands are pinned as they were. The served app's dead textual copies
  of `_compute_kdensity/_lowess/_lpoly/_lpolyci/_mband/_lfitci/_qfitci`
  and the second `_FP_POWERS/_fp_transform/_fit_fp2` (`dash_render.py`
  ~15695-16128) are deleted after a grep for call sites; every new
  module-level helper is in `_shared_stat_lines` or a `GlyphMapper`
  staticmethod, so both modes run one text.
- **TR-18.7** Records. `BUGS.md`, written first: eleven entries (mspline;
  the repeated-power FP2; the missing shift and scale; lowess; lpoly's
  squared kernel weight; lpoly's null rule; lpoly's grid and `n()`; the
  fpfitci band; kdensity's grid; the seven sub-options; weights), each
  with the measured numbers and the fixture sections that pin it.
  `GAPS.md` A3 finished, A4 and A5 closed. `dash.sthlp`: `{weight}` in
  the syntax diagrams; a Weights section with the per-type table, the
  one-variable rule and the refusals with twoway's rc; `bands()`/`n()`
  and the cross-median spline under mspline; `mean`, `noweight`,
  `adjust`, `logit` under lowess and that statsmodels is no longer
  needed; stdp/stdf/stdr under lfitci/qfitci; `discrete` under
  histogram; fpfit's "require positive x values" replaced by the shift
  rule; lpoly's `n()` and null rule and its bandwidth tolerance in the
  measured numbers; kdensity's grid; the dependency section corrected.

### Acceptance

- **AC-18.1** `mspline` equals `twoway mspline` for two `bands()` values
  and more: `test_statistical_truth.py::TestMsplineAgainstStata` over all
  20 probes (4 datasets x default, bands(5), bands(20), n(20),
  bands(5) n(4)) -- point count (K-1)n + K, knots equal the `mband`
  cross medians, curve rtol 1e-6 or the documented residual; the parity
  corpus `mspline bands(5) n(4)` in both modes;
  `test_statistical_options.cscript` `mspline, n(1)` rc 0.
- **AC-18.2** `fpfit` selects a repeated-power model where Stata does:
  `TestFpfitRepeatedPowers` over the 7 fits (auto price~mpg, weight~mpg,
  mpg~weight, census death~pop, sp500 close~volume, nlsw88 wage~ttl_exp,
  the synthetic `y = 3 x^2 ln x + N(0, .5^2)` from `fpfit_repeated_data`),
  chosen powers equal to `e(fp_powers)`, curve rtol 1e-6.
- **AC-18.3** `fpfit` on data with x <= 0 uses every observation:
  `TestFpfitShift` on `xs = weight - 3000` and `xz = mpg - 12` (powers,
  the 64- and 21-point curves) and the fpfitci stdp band.
- **AC-18.4** Each A5 option changes the output in the documented
  direction: `TestFitciBandTypes` (24 probes), `TestHistogramDiscrete`
  (12), `TestLowessIsStatasSmoother` (full-resolution default, mean,
  noweight on 4 datasets at rtol 1e-8 of the y range; logit and adjust on
  auto foreign~weight and nlsw88 union~wage); `TestLpolyDegreeOne`,
  `TestLpolyNullRule` and `TestKdensityAsDrawn` for the findings beside
  them; `test_unsupported_report_is_true.py` renders each flag present
  against absent (stdp against its stdf sibling); the parity corpus
  `lowess mean`, `lowess noweight logit adjust`, `lfitci stdf`, `qfitci
  stdr`, `histogram discrete`; `test_statistical_options.cscript` SO-nn:
  each flag accepted on its type with no note and refused elsewhere with
  r(198) `not allowed`, `stdf stdr` together r(198), `discrete bin(5)`
  r(198).
- **AC-18.5** Weighted fits match Stata's weighted estimates:
  `TestWeightedLayers` over every weighted probe (lfit, qfit, lfitci
  coefficients and curves; lpoly; fpfit powers and curve; histogram
  fweight heights; kdensity bandwidth and curve); the parity corpus's
  weighted lfit and weighted kdensity; `test_statistical_options.cscript`
  SO-nn: each type accepted per the table with no note and the JSON
  carrying `weight`/`wexp`, every refusal of the table with r(101) (iw
  everywhere, lowess any, histogram aw/pw, kdensity/lpoly/lpolyci pw),
  `[aw=price+1]` r(198) with the hint, `[aw=pri]` expanded to price,
  `[fw=mpg]` on histogram accepted and `[fw=gear_ratio]` r(401), a
  weighted immediate render rc 0 with `"price"` in the data JSON.

### Found on the way

- The lpoly weighting defect was outside A4/A5's text and inside
  "statistical fidelity": `numpy.polyfit`'s `w` multiplies the unsquared
  residual, so passing the kernel weight minimised sum K^2 r^2.
  degree(0) has no polyfit, which is why the existing fixture test was
  green.
- Stata's positive-weight cutoff for the gaussian kernel at extreme z is
  not pinned: census `kernel(gaussian)` (|z| up to 3e5) has 8 Stata nulls
  against 5 predicted by double underflow (|z| < 38.6); the rule
  reproduces the other 15 probes.
- The spline serset is index 2 of a `.gph`, not 1: `derived_serset.reset`
  creates the cross-median serset, builds the spline from it and drops
  it, so `serset set 1` is r(111) on an mspline graph (recorded per probe
  under `serset_dir`). `mband` keeps index 1, which is why LAYER 7 of the
  extractor reads `set(1)`.
- `lowess` tie order is the dataset order after a stable sort by x: a
  fresh `sysuse` run equals a run after `sort x obs, stable` point for
  point and differs from `gsort x -obs` on 23 of 74 (auto) and 1352 of
  2246 (nlsw88) observations; 14 tied-x groups on auto carry unequal
  values, so `obs_index` is recorded beside every full-resolution point.
- The `adjust` factor uses `mean(y)` over ALL observations, not the
  estimation sample (`lowess.ado:203-209`); both means are recorded.
- `lowess bwidth(1)`: Stata resets a bandwidth outside (0, 1) to .8;
  dash's table refuses more than 1 (`bwidth=pos,1@lowess`) and passes
  exactly 1 through -- unchanged, and the help keeps saying "at most 1".
- The help credited scipy to `qfitci` and `kdensity`; at `fe3b12a` only
  `map_lfitci` (`linregress`) and `map_mspline` (`PchipInterpolator`)
  imported it, and `map_qfitci` and `_t_ppf` were written to run without
  it. The weighted rewrite of `map_lfitci` removes the first import and
  the numpy spline the second, and `map_lowess` no longer imports
  statsmodels, so the help's dependency section now says no optional
  package is needed by any statistical layer. Written from the contract
  while the renderer was still being edited (at the docs owner's last
  read `map_lfitci` and `map_lowess` had lost their imports and
  `map_mspline` still called `_optional_import("scipy.interpolate",
  "PchipInterpolator")`): the coordinator verifies that sentence against
  the merged renderer. `dash_setup.ado:134-150` and
  `dash_setup.sthlp:76-78, 91` still declare scipy and statsmodels as
  optional with the old per-layer attribution, and `dash_render.py`'s
  module docstring (`:47-48`, `:500-501`) still lists both; none of the
  three is in this package's files. Follow-up. **Done by the
  coordinator:** the merged renderer imports neither (an AST scan of an
  app built with every statistical layer, `test_server_optional_deps.py`),
  the served app's guarded `from scipy import stats` -- read by nothing --
  is deleted, and `dash_setup` neither installs nor checks either package
  (`dash_setup.ado`, its help, `dash.pkg`, HON-05 of
  `test_setup_honesty.cscript`); the help's sentence is now true.
- `lpolyci` keeps its bootstrap band: Stata's is `invnormal` times a
  Mata standard error (`lpoly.ado:319-324`), outside A4/A5. Follow-up.
- A weight EXPRESSION is refused, not evaluated: supporting it would mean
  generating a variable on both export routes, rewriting the spec, and
  keeping a temporary name out of the served app's column list. Out of
  scope; the refusal says how to do it by hand.
- `scripts/regen_option_surface.py` is stale (no `hover`, none of the
  alias declarations), so the syntax block is hand-edited and the
  generator's lists kept in step for the record, as the last three
  packages did.
- Stale line references: this package as first written cited `187a786`
  (`map_mspline` at `dash_render.py:5912-5980`, `_fp_transform`
  `:4452-4459`, `_fit_fp2` `:4483`); at `fe3b12a` they are `:6985-7057`,
  `:5357-5365` and `:5367-5408`, with `map_lowess` at `:4986-5061`,
  `map_fpfitci` `:5479-5546`, `_compute_lpoly_fit` `:5108-5172`,
  `map_kdensity` `:5717-5828` and the option rules at `dash.ado:1241-1253`.

### Found by the coordinator's review

The package landed in the working tree without its verification run, and
the DESIGN.md contract and the scratchpad measurements it cites were
gone. The coordinator re-ran both suites (Python: 11 failures, every one
a test pinning behaviour the package replaced -- the 200-point PCHIP
mspline, the served app's deleted `_compute_*` copies, lpoly curves the
null rule now empties -- each restated to Stata's rule; Stata: 43 of 43)
and had four independent reviews read the diff against Stata's own
`.ado` sources and probe Stata where they doubted it. Everything below
was measured with the console binary on 23sep2026 and is fixed with a
test written from Stata's output; each has a `BUGS.md` entry with the
numbers.

- **The weight clause.** `unab` read `[aw=price-price]` as the range
  price (twoway weights by zero); `confirm name` first. stdf/stdr under
  an aweight (r(135) "not possible with weighted data") or a pweight
  (r(198)) were drawn; refused. A negative aweight on kdensity, lpoly and
  lpolyci is r(402) in twoway; refused, over the plot's own if/in sample
  (a bad weight on a row whose y is missing still refuses -- measured).
  In the renderer the value rules are twoway's per layer: lfit, qfit,
  lfitci and qfitci leave a negative weight's row out; fpfit/fpfitci draw
  nothing for any negative weight, and qfit/qfitci/fpfit/fpfitci nothing
  for a non-integer fweight ("could not fit model"). A string weight in a
  hand-written spec is named, not fatal.
- **mband and mspline.** An observation on a band edge belongs to the
  band above (`floor((x - min) B / range)`; linspace's edges put it
  below: 8 knots for Stata's 10 on tenths, 6 of 20 knots moved on
  hundredths). The default band count is at least min(N, 2); mband draws
  from two observations; one or two knots draw the knots alone. mspline
  `n()` is 1..300 and `bands()` 1..200, both twoway's own bounds (this
  section's measured table said otherwise; corrected above).
- **histogram and kdensity.** `discrete` folds a value past its last edge
  into the last bar (twoway__histogram_gen.ado:200-203), in Python and in
  the page's recount; a single repeated value is one bar of width 1; a
  `start()` above the sample's minimum is r(198), as in twoway. The
  weighted percentile's tie needed dash_wpctl's tolerance (kdensity's
  bandwidth 9% off on a tie the float sum lands just below). The page's
  kdensity recount clears a curve it cannot smooth instead of leaving the
  old one.
- **lowess.** adjust divides by the mean of y over every observation in
  memory (lowess.ado:207, `summ y, mean`, no if), not the smoothed
  sample: 4.13 mpg on `if foreign, adjust`. The running line is missing
  where its window has no x spread (495 of 2244 on nlsw88 wage~grade);
  logit turns a missing smooth into 1 - 1/N; N >= 3 and a range of 1e-30
  gate the smooth; a zero-mean smooth has no adjusted value. The mapper
  now holds the data in memory (`GlyphMapper.dataset`, set by both modes)
  for this and for lpoly's grid.
- **lpoly and lpolyci.** The grid follows the dataset's _N
  (`twoway_lpoly_parse.class:56`, `lpoly.ado:283-290`), not the sample:
  50 points on `if foreign==1`, n(100) capped at 74. A window with fewer
  distinct x than the degree fits the degree it supports. lpolyci's
  bootstrap evaluates every resample on the drawn grid (it mixed grids;
  the band is still a bootstrap -- follow-up).
- **The fitted lines' regression.** `_dash_wls` omits an exactly
  collinear later column (qfit/qfitci on a two-valued x are the line, as
  regress fits them), decides the rank on the raw design as lstsq does
  (Stata's regress omits a nearly collinear term on date-time data, and
  so must dash), and keeps the covariance in SVD form -- on a centred,
  scaled copy of the column space when full rank. fpfitci's band on
  hourly %tc was 0.09 to 1.2 of Stata's; fpfit draws from two
  observations and nothing for a constant y; qfitci with three rows no
  longer takes the dashboard down (df 0: the fit, no band); qfit draws
  qfitci's own regression.
- **Dead code.** The served `_compute_histogram`, `_compute_lfit` and
  `_compute_qfit` (called by nothing, weight-blind) are deleted with their
  tests restated against the served layers; a test now checks that the
  served app defines every module-level name GlyphMapper reads (it caught
  three during the review). `_compute_rscatter`/`_compute_pcscatter` are
  left for WP-26.

Recorded, not fixed (outside WP-18; `BUGS.md`): linked graphs with
`by()` under a served filter move overwrite the shared source per panel;
a weight on `function`/`scatteri` answers with a different rc from
twoway's, and twoway's `kernel()` abbreviations are refused; lowess costs
116 s at 100k rows (no slower than statsmodels was) and fpfit ~2 s at
1e6, rerun unthrottled on every served filter move (WP-19). On a
date-time or offset x, Stata's choice between two nearly equal FP models
rests on its own rounding and can differ from dash's (on the offset x
the residual sums of squares, to 60 digits, rank dash's choice first);
the curves then agree to 5e-4 of their span, and the fixture test carries
that tolerance.  *Since then (WP-23's reconciliation): the linked by()
filter move is fixed by 7c2c918; function and the immediate types answer a
weight as twoway does (WP-23), while kernel() abbreviations are still
refused; the served recompute is throttled (WP-19), and lowess and fpfit
still cost what they did -- both open in BUGS.md.*

### Verification, measured

23sep2026, the coordinator, on the tree committed with this record
(branch `feature/batch4-interactive-layer`, `main` merged first: already
an ancestor), both suites run once on the final code:

- `python3 -m pytest test/ -q`: **8846 passed, 0 failed**, 6 xfailed
  (unchanged), 58 skipped, 1:52.  Every skip is structural, none a
  missing dependency: 37 and 20 `test_cscript_hygiene.py` checks that do
  not apply to a given script, and the `layout(bs)` parity entry whose
  document tree cannot be compared (WP-21).  scipy and statsmodels were
  installed, and no test needs either.
- `test/run_all_cscripts.do` with the console binary: **43 passed, 0
  failed, 0 skipped** -- `test_statistical_options.cscript` (151 checks)
  among them, `test_conformance.cscript` rendering the corpus with lowess
  and WP-18's options and weights, `test_setup_honesty.cscript` against
  the setup that no longer installs scipy or statsmodels.

Acceptance, each certified by the tests named (all green in those runs):

- **AC-18.1** `TestMsplineAgainstStata` (20 probes), the parity entry
  `mspline, bands(5) n(4)`, SO-67/70/87/88; the review's knots and band
  edges in `test_statistical_helpers.py`.
- **AC-18.2** `TestFpfitRepeatedPowers` (7 fits: powers equal
  `e(fp_powers)`, curves rtol 1e-6).
- **AC-18.3** `TestFpfitShift` and the fpfitci stdp band; the edge
  cases of `fp_edge_truth.json` (14, fit and band against Stata).
- **AC-18.4** `TestFitciBandTypes`, `TestHistogramDiscrete`,
  `TestLowessIsStatasSmoother`, `TestLpolyDegreeOne`, `TestLpolyNullRule`,
  `TestKdensityAsDrawn`; `test_unsupported_report_is_true.py` for each
  flag; the parity corpus; SO-45..66.
- **AC-18.5** `TestWeightedLayers` (every weighted probe), the parity
  corpus's weighted lfit and kdensity, SO-01..44 and SO-71..86.

---

## WP-19 · Resource limits — DONE

**Gaps closed:** I2 · **Severity:** S2 · **Effort:** M · **Depends on:** —

> **User story.** As a user who pointed a filter at a continuous variable, I
> want a warning and a sane widget — not a 200 001-option dropdown.

### What was measured before any code changed

23sep2026 at `f1321c6`, the standalone renderer unless marked, dash's own
classes driven directly (`scratchpad/wp19/measure.py`, `limiter.py`):

| Input | Measured |
|---|---|
| `filter(v, type(dropdown))`, 20,000 distinct values | 0.5 s; served app 2.0 MB, 20,001 options |
| the same, 200,000 distinct values | 4.4 s, 38.8 MB page; served app 14.8 MB, 200,001 options; 954 MB RSS |
| `by(id)`, 300 groups | 8.4 s, 300 figures |
| `by(id)`, 1,000 groups | 29.2 s, 7.3 MB, 1,000 figures |
| 300 registered graphs | 7.9 s, 4.0 MB |
| `tabs()` with 3,000 tabs | 14.4 s, 3.9 MB |
| 1,000,000 rows x 2 | 4.0 s, 47.6 MB, 1.0 GB RSS; the warning estimated 68 MB |
| 2,000,000 rows x 2 | 7.9 s, 94.9 MB, 2.1 GB RSS, rc 0 |
| the served limiter, one machine cycling 10,000 forged `X-Forwarded-For` keys in 60 s | peer-address default: 60 granted; `--trust-forwarded-for`: 10,120 granted, and the real client's key flushed -- 120 of 120 in one window |

### Business requirements

- **BR-19.1** No user input can produce unbounded output or memory use
  (CLAUDE.md rule 3).
- **BR-19.2** Every clamp warns, naming the limit and the option that would
  raise it.

### Technical requirements, as delivered

One table in each language -- `_DASH_LIMITS` in `dash_render.py`,
`_dash_limit_table` in `dash.ado`, held equal by
`test_resource_limits.py::TestTheTwoLanguagesAgree` -- gives every limit a
default, a hard ceiling nothing moves, and a global macro that moves the
default for the session.  `_dash_limit` validates a set global (digits
only, at most nine, 1 to the ceiling, read through `st_global()` and never
by a regular expression; anything else is r(198) naming the global, the
range and the value reduced to safe characters), and `_dash_limits_json`
writes the set ones into `build_options["limits"]` on both routes.  The
renderer's `_dash_limits` re-validates them, so a hand-edited spec cannot
lift a ceiling.  `dash clear` leaves the globals alone: they are settings,
not registry.  Documented in `dash.sthlp`, "Resource limits".

| Limit | Global | Default | Ceiling | At the limit |
|---|---|---|---|---|
| values embedded (observations x variables used) | `dash_max_cells` | 5,000,000 | 20,000,000 | refused, r(134), before the export |
| graphs and KPI cards registered | `dash_max_graphs` | 100 | 1,000 | a new name refused, r(134) |
| plots in one graph (one per y variable) | `dash_max_plots` | 100 | 1,000 | refused, r(134) |
| values one dropdown lists | `dash_max_filter_options` | 1,000 | 100,000 | numeric or date → `type(range)`; string → its first values |
| panels one `by()` graph draws | `dash_max_by_groups` | 100 | 1,000 | the first groups in sort order |
| tabs | `dash_max_tabs` | 50 | 500 | the first tabs |
| filter widgets | `dash_max_filters` | 20 | 200 | the first filters |

- **TR-19.1** `_dash_filter_effective_type` plans a dropdown under the
  option limit in both modes -- in the saved renderer's filter loop, and at
  build time in `ServerAppBuilder` so the served user is told where they
  are.  Over the limit a numeric or date variable is drawn as `type(range)`
  and the page's filter spec says so too; a string variable keeps its
  dropdown and `_dash_filter_widget(max_options=)` lists its first values.
  The distinct count is `nunique` first and the exact option count only
  past the limit.
- **TR-19.2** `_dash_by_groups`, one helper both modes group through,
  counts the groups before it copies any and stops after the first
  `by_groups` in sort order; the served build names the clamp at build
  time (`_plan_by_groups`, on the graph's qualified rows).  KPI facet cards
  follow the capped panels.
- **TR-19.3** Graphs and KPI cards: `_dash_graph_cap` in both registrars,
  before any global is set or retired, never counting a replace.  Plots:
  `_dash_process_segment` refuses a single segment whose y variables pass
  the limit before building their JSON, and `_dash_plot` keeps a running
  total.  Tabs and filters: `_dash_parse_tabs(limit)` and
  `_dash_cap_filters`.  The renderer also holds graphs and plots
  (`_dash_cap_spec`) for a spec that did not come through dash.ado.
- **TR-19.4** `_dash_cell_cap` refuses before the date-format swap and the
  export, on both routes, leaving the data and formats untouched; the
  message says `if`/`in` do not help (dash exports every observation and
  applies qualifiers itself) and names keep/drop/sample/collapse.  Both
  renderers refuse too (`_dash_refuse_oversized`, `DashLimitError`).  The
  large-dataset note keeps its threshold, gets the measured 24 bytes a
  cell (was 34), and stops advising a qualifier.
- **TR-19.5** The served `_RateLimiter` is rewritten: per client
  (`--sessions-per-client`, 60), a shared first-contact window for keys it
  is not tracking (`--new-clients-per-minute`, 60), all sessions together
  (`--sessions-per-minute`, 600); stale keys swept, a live key never
  evicted; refusals logged once a minute per bound, naming the flag.  The
  flags parse through `_dash_arg_parser`/`_dash_apply_limits`, each 1 to
  1,000,000.  Health keeps a separate budget.
- **TR-19.6** The bounds that held are pinned in both modes
  (`TestTheBoundsThatAlreadyWorkedAreKept`): `_MAX_BINS`, `_MAX_MBANDS`,
  `_MAX_EXPR_CHARS`, `_FP_GRID_MAX`, the function point clamp,
  `_WEBGL_THRESHOLD`, the port clamp.
- **The served recompute** (the WP-18 entry in `BUGS.md` assigned here): a
  slider recomputes when its drag ends (`value_throttled`), and every filter
  and brush callback runs through `_dash_event_throttle`, a token bucket per
  callback per session (10 at once, 2 a second, the rest folded into one
  trailing recompute with the latest values).  The estimators' own cost is
  left recorded: lowess is O(N x window) by definition, as Stata's is.

### Acceptance

- **AC-19.1** `TestADropdownOnAContinuousVariable` (both modes, the page's
  filter spec, the build-time note), RL-01..04.
- **AC-19.2** `TestByOnAHighCardinalityVariable` (both modes, the qualified
  count, two by-variables), RL-06..08 and RL-11.
- **AC-19.3** `TestAnOversizedDatasetIsRefused` (both renderers), P19-11..13
  (both routes: r(134), no file, no `dash_opts_*`, data and `%td` format
  unchanged) and P19-23 (the default at scale: 5,200,000 values refused,
  exactly 5,000,000 admitted).  The graph and plot refusals: P19-01..10.
- **AC-19.4** `test_server_rate_limit.py::TestTheForwardedKeyCycleIsHeldToTheNominalRate`:
  with the header trusted the same attack now gets 59 sessions (it got
  10,000) and the real client its 60, not a second 60; with the default
  peer-address key it gets none, as before.  Key reuse is held to the
  total (`TestReusedKeysAreHeldToTheTotal`).

### Found on the way

Each with a failing test first, fixed, and recorded in `BUGS.md`:

- A do-file beginning `version 16` or `version 17` could not name a graph
  or KPI card: the name check used `{0,31}`, which Stata's old regex engine
  -- the one a caller below 18 gets -- does not know.  The whole
  certification suite was then run with the caller at `version 16`: 44 of
  44 passed.
- A 23- to 32-character graph name, or a 19- to 32-character KPI name,
  passed the check and failed on Stata's 32-character global limit; the
  limits are now 22 and 18, in dash's own words.
- A refused filter, graph or KPI name was echoed as SMCL: `{bf:}`, `{hline}`
  -- and SMCL's `{browse}` and `{stata}` links -- were drawn from the
  user's text.  Every unsafe character is now neutralised (P19-24..26).
- With the header trusted, a forwarded IPv6 zone of any length was a bucket
  key, and one address spelled two ways was two clients; keys are now the
  canonical address, at most 45 characters.
- A graph of literal values (`function`, `scatteri`, `pci`) exported every
  observation of a placeholder variable it never reads, and under the cell
  limit was refused for it; it now exports one (RL-13..14).
- Recorded here and fixed straight after, in its own commit: `cscript`
  drops every global, so the runner's `$dash_nobrowser` never reached the
  scripts, and 13 of them built dashboards with it unset (under the
  console binary nothing opened).  `cert_helpers.do` now sets it, the six
  scripts that build without loading it set it after `cscript`, and
  `test_cscript_hygiene.py` fails any build that runs while it is unset.

### Verification, measured

23sep2026, on the tree committed with this record (branch
`feature/batch4-interactive-layer`, `main` already an ancestor), both
suites run once on the final code:

- `python3 -m pytest test/ -q`: **9012 passed, 0 failed**, 6 xfailed
  (unchanged), 60 skipped, 2:13.  Every skip is structural: 39 and 20
  `test_cscript_hygiene.py` checks that do not apply to a given script --
  one more for each new script than WP-18's 58 -- and the `layout(bs)`
  parity entry (WP-21).  Tests: `test_resource_limits.py` 84 (19 before,
  all kept), `test_server_rate_limit.py` 73 (11 before, two restated for
  the new contract), `test_served_throttle.py` 31 (new).
- `test/run_all_cscripts.do` with the console binary: **45 passed, 0
  failed, 0 skipped** -- the new `test_caller_version.cscript` (11 checks)
  and `test_resource_limits.cscript` (14) among them, and
  `test_adversarial.cscript` with P19-01..26.
- Once, after the name-check fix and before the rest of WP-19, the 44
  scripts of the runner were run with the caller at `version 16` (the
  runner with `version 16` after `clear all`): 44 passed.

---

## WP-20 · Security hardening — DONE

**Gaps closed:** I3 · **Severity:** S2/S3 · **Effort:** S · **Depends on:** WP-09

> **User story.** As someone deploying a served dashboard on a shared
> machine, I want the same protections the saved file already has.

### Business requirements

- **BR-20.1** Security controls apply equally in both render modes.
- **BR-20.2** Every input surface has adversarial coverage for auth bypass,
  injection and resource exhaustion (CLAUDE.md rule 18).
- **BR-20.3** Defences that depend on a third-party library's behaviour are
  pinned by a test, not assumed.

### What was measured before any code changed

23sep2026 at `e932446`, in Chromium (the browser pane) on pages built by
dash's own classes, with bokeh 3.9.0 (the test suite's Python) and 3.8.0
(Stata's configured Python) read at source:

| Question | Measured |
|---|---|
| Served app, `/` and `/health` | `Server`, `Content-Type`, `Date`, `Etag` only: no CSP, no `X-Content-Type-Options`, `X-Frame-Options` or `Referrer-Policy` |
| Saved page under `default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'` | renders; no violation; the dropdown's CustomJS ran (KPI -0.07 → 0.04); hover drawn.  The same for `layout(bs)` |
| Served policy on a minimal Bokeh server (template meta + Tornado transform) | headers on `/`; the websocket opens under `connect-src 'self'`; a server callback round-trips; CustomJS runs; no violation |
| Variable label `<img src=x onerror="document.title='PWNED'">` on y | axis title, legend and tooltip show the text; no `<img>` in the document or any shadow root; title unchanged -- saved and served |
| The BokehJS sink walk | text nodes and canvas text everywhere except a slider-family title holding a TeX pair (`innerHTML` after `process_tex`, which copies the text around the TeX raw), a Div's MathJax pass (`\href{javascript:}` a live link), and a tooltip field `@{name}` (parsed as HTML after filling) [WP-30 P1.11a, commit 3bdffb5: canvas text sinks carry TeX pairs inert in both modes (`_dash_finish_graph_text`), so the saved page no longer loads MathJax for user text] |
| `dash_setup` | a crafted version string reached `Version("...")` as code and created a marker file; a renderer directory whose name closed `r"..."` ran `sfi.Macro.setGlobal` |

### Technical requirements, as delivered

- **TR-20.1 / TR-20.2** Two policies, both `default-src 'none'`:
  `_DASH_CSP_STANDALONE` (scripts and styles inline only, images and fonts
  from `data:`, `connect-src 'none'`, `object-src 'none'`, `base-uri 'none'`,
  `form-action 'none'`) and `_DASH_CSP_SERVED` (the same with `'self'` and
  `connect-src 'self'` for the websocket).  `_dash_csp_meta` refuses any
  character a policy does not need.  The meta comes before every script
  and style in `<head>`: first on both saved pages (the `layout(bs)` page
  had it after the inlined BokehJS -- `BUGS.md`), and on the served page,
  through a Bokeh document template (`_dash_served_template`, set in
  `make_document`), after only `<meta charset>` and `<title>`.  The
  served app's own launcher adds a Tornado transform (`_DashSecurityHeaders`
  through `_dash_server_transforms`, which keeps Tornado's gzip rule) that
  sends the policy with `frame-ancestors 'none'`, `X-Content-Type-Options:
  nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer` on
  every response, `/health` included; `bokeh serve app.py` sends none, and
  `dash.sthlp` says so.  `unsafe-eval` stays: BokehJS's `CustomJS` needs it.
- **TR-20.3** The hover label is safe (a text node) and pinned.  Every sink a
  label or value reaches is classified in `test_label_sinks.py`, pinned to the
  Bokeh versions it was verified on (3.9.0 walked; 3.8.0 compared at source
  and identical).  The three unsafe sinks are closed: `_dash_inert_tex` breaks
  every `$$`, `\(`, `\)`, `\[`, `\]` in a slider, range or date filter title
  with a WORD JOINER; every Div dash writes sets `disable_math`; a tooltip
  field is built only for a plain Stata name.  The text sinks -- legend
  labels, dropdown options, facet titles, tick labels, colour-bar titles --
  get the raw text, which they had shown as entities, and tick labels travel
  in the formatter's `args`, not its code. [WP-30 P1.11a, commit 3bdffb5: the same sinks now finish TeX inert]
- **TR-20.4** `dash_setup` reads every value inside Python with
  `sfi.Macro.getLocal` (the version gate, the scheme probe, the metadata
  query), and keeps a version read back only when it is made of version
  characters; `test_cscript_hygiene.py` forbids a macro inside a Python
  string literal on any `python:` line of either ado file.
- **TR-20.5** Pinned in `test_security_surface.py`: the function whitelist in
  both modes (whose literal check let strings and `True` towers through --
  now refused, `BUGS.md`), the qualifier whitelist, scheme containment
  (abspath + realpath, symlinks, includes), `_sanitize_css_color`, the filter
  name check and loopback binding at run time.
- **AC-20.3** `test_adversarial_matrix.py` registers 24 input surfaces --
  every command-line token and option family, the data, the files dash
  reads, the renderer's own command line and every request the served app
  answers -- with at least one auth-bypass, one injection and one exhaustion
  test each, 196 entries in all; meta-tests prove that every entry is a
  collected test or a certification case its script displays as passing.
  "Auth bypass" is getting past a surface's own guard: dash has no accounts
  (L10, and the standing note below).  The gaps the registry exposed were
  fixed, each with a failing test first and a `BUGS.md` entry:
  - every echo of the user's text in `dash.ado` -- 23 of them -- drew it as
    SMCL, and the `.gph` note ran a quoted name as display directives; the
    Mata `_dash_say` now prints the text by value, as written, with control
    characters shown as `?`;
  - `port()` and `timeout()` took digits followed by a newline (StataNow's
    `regexm` matches `$` before it), and `timeout()` 400 digits; both are
    now proven byte by byte (`_dash_is_digits`), `timeout()` nine digits at
    most;
  - a backslash at the end of `layout()` broke the spec (it went in raw);
    `EXCLUDE()` in upper case skipped the registry check;
  - a `layout()` grid of any size was built cell by cell (4000 x 4000 peaked
    at 1.5 GB); dash.ado refuses a grid larger than the graphs limit and the
    renderer draws one as `layout(auto)`, with one ASCII reading of the
    layout in the count and in both grid readers (`_dash_grid_dims`), which
    the Mata and Python counts share (`test_echo_text.cscript` ECH-09);
  - the renderer recursed or allocated without bound on a 1,500-file
    `#include` chain, a 490-operator `if`, `xlabel(0(0.000001)1000000)`, a
    billion-decimal format, a limit in non-ASCII digits and an infinite
    function `n`; each is bounded.

### Acceptance

- **AC-20.1** `test_csp.py` (65 tests): both policies and their placement,
  the meta ahead of every script and style on every page, and nine against
  a live served app on a free port -- the headers on `/` and `/health`, the
  meta in the document, a session and its websocket.  Checked in Chromium on
  a served app launched by its own launcher: headers and meta present, the
  websocket open, and both filters round-tripping through the server under
  `connect-src 'self'` -- the dropdown moved the KPI card from -0.07 to
  -0.01, 0.04 and back, the range slider to -0.21 and back -- with no
  violation and no console error.
- **AC-20.2** `test_label_sinks.py` (918 tests): a hostile label through
  every sink in both modes, the TeX and MathJax paths, the tooltip field,
  the served app's source; checked in Chromium in both modes (text shown, no
  `<img>`), and again in the served app after the filter round trips (no
  `<img>` in the document or its 60 shadow roots).  `test_kpi_security.py`,
  as the test plan asked, pins the KPI card's title, subtitle and name as
  inert HTML with maths off in both modes -- in the saved page's rebuild
  config and in the served card after a filter moves -- and a hand-edited
  `fmt` as bounded there too (23 new tests; 58 in the file).
- **AC-20.3** `test_adversarial_matrix.py` (233 tests: the registry and its
  gap tests), `test_adversarial.cscript` P20-01..30,
  `test_setup_injection.cscript` INJ-01..11, `test_echo_text.cscript`
  ECH-01..11.

### Standing note: CLAUDE.md rule 19 is not applicable, by design

dash has no accounts, no administrators and no administrative component;
every dashboard is built by the Stata user who runs the command, and the
served app binds loopback by default and offers no privileged route.  Rule
19 therefore does not apply, by design and not by omission (GAPS.md L10; the
module docstring of `test_adversarial_matrix.py`).  If dash ever gains
accounts or an administrative surface, it does.

### Found on the way

- In the new P20 cases, a second `cert_file_has` in a row read an emptied
  `r(log)` (each call replaces `r()`), and three "no file was written"
  checks could be answered by a file an earlier run had left behind; the
  cases keep the log path in a local and erase first.
- Stata's own parser refuses a brace in a weight expression, so that echo
  cannot carry SMCL; it goes through `_dash_say` all the same.
- Closing WP-20's last gaps (a second commit): `layout()` was checked only
  at its start, so a value the renderer could not read -- `layout(g1:1,1
  junk)`, `layout(bs\)` -- was drawn as auto in silence, a placement naming
  no registered item made the modes disagree (`layout(nosuch:1,1)` was
  3 x 1 saved and 1 x 2 served), and a Bootstrap spec dropped an unknown
  name and clamped a span of 13 without a word.  dash build now refuses
  each (P20-30, `_dash_layout_refusal`), and the renderer's
  `_dash_layout_check` reports and corrects it for a spec that did not come
  through dash.ado, identically in both modes.  P20-17's first case, which
  built `layout("bs\")`, is restated to the refusal; the spec's escaping of
  `layout()` is pinned statically instead.

### Verification, measured

23sep2026, branch `feature/batch4-interactive-layer` (`main` already an
ancestor, so nothing to pull).  Both suites were run on the working tree,
which also carries test-infrastructure changes from other work that are not
part of this commit (`pyproject.toml`'s parallel default, `test/conftest.py`'s
per-test document reset and session lock, and the two tests that pin them);
the commit's own tree was then run on its own, last below.

- `test/run_all_cscripts.do` with the console binary: **48 passed, 0
  failed, 0 skipped**, in 43 s -- the new `test_echo_text.cscript`
  (ECH-01..09) and `test_setup_injection.cscript` (INJ-01..11) among them,
  and `test_adversarial.cscript` with P20-01..29.  After it the help's
  `timeout()` entry was reflowed (below), and `test_abbreviations.cscript`,
  the one script that parses the help, was run again: passed.
- `python3 -m pytest test/ -q`, first run: 10,410 passed, **2 failed**.
  `test_server.py`'s BUG-49 check reads the help's `timeout()` entry as two
  lines, and the new wording ran to three: reflowed.
  `test_option_validation.py` forbade any `mata:` in the three validator
  programs, a WP-15 constraint that keeps validation in Stata; the refusals
  now echo through the Mata display helper `_dash_say`, so the check allows
  that call alone and a new test asserts it is the only Mata there.
- Second run: **10,413 passed, 0 failed**, 61 skipped, 6 xfailed
  (unchanged), 2:01.  Every skip is structural: 60 `test_cscript_hygiene.py`
  checks that do not apply to a given script, and the `layout(bs)` parity
  entry (WP-21).
- The commit's own tree -- `HEAD` with only the staged WP-20 diff applied,
  in a separate worktree, with `HEAD`'s `conftest.py` and no
  `pyproject.toml` -- run whole with `-n auto`: **10,395 passed, 0
  failed**, 61 skipped, 6 xfailed, 3:39.  The 18 fewer are the two
  uncommitted infrastructure test files.  The certification scripts were
  not rerun there: every WP-20 file in that tree is byte-identical to the
  one they ran, and the files left out are pytest infrastructure and
  documents, which no script reads.

The second commit (closing WP-20's gaps), 23sep2026, the same way:

- `test/run_all_cscripts.do` with the console binary: **48 passed, 0
  failed, 0 skipped**, in 45 s -- `test_adversarial.cscript` with P20-30
  and the restated P20-17, `test_echo_text.cscript` with ECH-10..11.  P20-30
  was first run against the committed code (`f2ecdd4`): all 15 refused
  values built with rc 0 there, and the 8 valid ones passed.
- `python3 -m pytest test/ -q`: **10,468 passed, 0 failed**, 61 skipped,
  6 xfailed, 2:11.  Two tests were written after that run had started
  (`TestALayoutThatCannotBeReadIsReported::test_an_item_the_graphs_limit_dropped_is_left_out_quietly`
  and `::test_the_checks_read_what_their_readers_read`) and were run on
  their own: both pass, after the first had its own assertion corrected (the
  report quotes the whole layout, which holds the name it looked for).
- The commit's own tree -- the first commit with only this diff applied, in
  a separate worktree, with `HEAD`'s `conftest.py` and no `pyproject.toml`
  -- ran the three test files this commit changes and the 22 that read or
  set `layout()`, with `-n auto`: **5,104 passed, 0 failed**.

---


# Milestone 4 — Complete and covered

## WP-21 · Export — DONE

**Gaps closed:** H1, H3 · **Severity:** S2 · **Effort:** S · **Depends on:** WP-09

> **User story.** As a user, I want to save the chart as an image and the
> filtered rows as CSV, so the dashboard can feed a paper or a deck.

### Business requirements

- **BR-21.1** A user can get the chart out as an image and the data out as
  CSV, in both modes.
- **BR-21.2** Exported data reflects the filters the user has applied.

### What was measured before any code changed

23sep2026 at `ed41e8a`:

| Question | Measured |
|---|---|
| Tools on a figure | saved `pan,wheel_zoom,box_select,lasso_select,reset`; served the same five as ONE list of instances handed to every figure, so all figures shared each tool object |
| Save, CSV, download, export | none, in either mode |
| What `gridplot` does with save tools | merges every figure's into one new `SaveTool` on the grid's toolbar, whose BokehJS view exports its parent -- the whole grid -- as one PNG, and which, having no file name, stops to `prompt()` with `bokeh_plot` filled in (BokehJS 3.9 source) |
| Stata's `export delimited` | dates in their display format (`16jan2020`, `2020m1`), value labels, 16 significant digits without a leading zero (`.3333333333333333`), RFC quoting, no byte-order mark, and a cell `=SUM(A1)` written as it is |
| Stata's `import delimited` on UTF-8 with a BOM and CRLF | variable names clean, `é` intact, quoted commas intact |
| `layout(bs)` served | read by the placement parser, nothing found, the automatic grid drawn without a word: `bs` of two graphs and four KPI cards a 2 x 3 grid in registry order where the saved page draws the cards in one row at span 3 and the graphs under them at span 6; `bs:` spans and rows ignored |

### Technical requirements, as delivered

- **TR-21.1 / TR-21.2** Every figure, in both modes, carries
  `pan, wheel_zoom, box_zoom, box_select, lasso_select, undo, redo, reset,
  save` (`_DASH_FIGURE_TOOLS`), and in the served app each figure owns its
  own tools.  What is active when the page opens is unchanged -- pan is the
  drag, the wheel scrolls the page until wheel zoom is chosen (read from
  BokehJS's own `default_order`, and pinned).  No crosshair: in a toolbar a
  grid shares it draws across every figure at once, and the tooltip already
  reads values.  Every grid's one save button -- the dashboard's, a tab's, a
  `by()` graph's panels -- writes `dashboard.png` (`_dash_name_save`); under
  `layout(bs)`, where each item keeps its own toolbar, it writes the item
  under its own name, in both modes.  The parity guard's `_tools` compared a
  sorted list and so never saw an order change; it now compares the order,
  and the document tree carries each grid's save and its name.
- **TR-21.3** `dash build, csv` (and `dash serve`, which inherits it) adds a
  **Download CSV** button beside the filters, or in a bar of its own when
  there are none, in both modes.  Opt-in, because it hands any viewer every
  row of every variable the dashboard uses: a served dashboard otherwise
  sends the browser only what it plots, and a variable only a KPI card
  summarises stays on the server (dash.sthlp, Exporting).  One formatter,
  written in JavaScript (`_DASH_CSV_JS`), writes the file in both modes, so
  the two cannot disagree on a number or a date:
  - saved: the button's CustomJS masks the filter callbacks' own snapshot
    with their own function (`dash_filter_mask`) and writes the rows that
    pass; string columns travel once more, raw, because the snapshot holds
    "007" as 7 (its dropdown matches through that);
  - served: the button's click reaches the server, which masks its frame
    with the recompute's own rule (`_dash_frame_filter_mask`, moved out of
    the app template so the two share it), puts the rows in a source
    (`_dash_csv_payload`, converting the frame's Stata dates as the saved
    loader does), and bumps the button's tags, whose CustomJS writes the
    file -- a new tag each click, so the same rows twice are two files, and
    the source rides in that callback's args, which is what puts it in the
    document.  A token bucket (`_DASH_CSV_RATE`, `_DASH_CSV_BURST`: two at
    once, then one every five seconds) holds each session.
  - the file: variable names, then the rows in the data's order; numbers as
    JavaScript spells them (the shortest decimal that reads back as the same
    double); a value-labelled number as its label; dates in ISO 8601 (the
    fraction of a `%tc` second only when not zero; the year for `%ty`; the
    period's first day for `%tw %tm %tq %th`); a text cell beginning
    `= + - @`, a tab or a carriage return after an apostrophe (OWASP, "CSV
    injection"); RFC 4180 quoting, CRLF, UTF-8 with a byte-order mark --
    which Excel needs and Stata's `import delimited` reads through
    (measured).  Stata's own `export delimited` was measured first: it
    writes dates in their display format, value labels, 16 significant
    digits without a leading zero, no BOM and no formula guard.
- **TR-21.4** `layout(bs)` is served with the saved page's rows and spans, on
  a 12-column `GridBox` (`_dash_bs_grid`): each item takes its span, a row
  wraps where Bootstrap wraps at wide widths, a name the spec leaves out is
  appended full width, tabs() takes its items out of the grid as on the
  saved page, and each figure keeps its own toolbar.  One reader for both
  modes -- `_dash_parse_bs_layout` and `_dash_auto_bs_layout`, moved out of
  `DashRenderer` (whose methods now wrap them) and copied into the app.  The
  served grid does not reflow as the window narrows, as the saved page
  does; dash.sthlp says so.  The parity corpus's `layout(bs)` entry, skipped
  until now, compares the saved page's grid, read from its HTML, with the
  served `GridBox` cell by cell.
- **TR-21.5** dash.sthlp: "The toolbar" (every tool, the save files, why no
  crosshair, one toolbar per grid), "Exporting" (the save button and
  `csv`: what a file holds and how it differs from `export delimited`, why
  it is opt-in, the served pace), `csv` in the options tables, the mode
  table's toolbar and `layout(bs)` rows.

### Acceptance

- **AC-21.1** Both modes offer PNG save and CSV download: `test_toolbar.py`
  (107 tests), `test_export.py` (84), `test_export.cscript` EXP-01..06.
  Checked in Chromium on pages built from the tree: the saved page's grid
  save wrote a 2560 x 990 PNG (97.7 KB) named `dashboard`, the served one an
  85 KB PNG; each page's Download CSV wrote `dashboard.csv`, UTF-8 with a
  BOM, the two files identical, with no policy violation under either
  page's `default-src 'none'`.
- **AC-21.2** The CSV reflects the active filters:
  `TestTheFileHoldsTheFilteredRows`, which runs both modes' downloads on the
  same filter states through the shipped JavaScript and requires identical
  files; in the browser the saved and served files held the same two rows
  after the same dropdown and range moves (checked before the toolbar
  merge) and the same six before any move (checked again after it).
- **AC-21.3** `layout(bs)` in server mode is specified (dash.sthlp) and
  tested: `test_served_bs_layout.py` (103 tests, each served grid checked
  against a written expectation and against the saved page's HTML), and the
  parity entry.

### Found on the way

Each with a failing test first and a `BUGS.md` entry:

- A saved page's range and slider filters compared a missing value as
  JavaScript compares null, as 0, while the served app drops it: the modes'
  KPI cards disagreed.  One mask function now, failing a missing value.
- An untouched range filter dropped every missing value as soon as any
  filter moved; a range at its full extent, or a slider at its start, now
  restricts nothing, as a dropdown at "All" restricts nothing.
- A saved dashboard with a filter failed to render at all when a date
  variable held a missing value (`NaT` in a list, which JSON refuses).
- Under plain `layout(bs)`, a KPI card placed in tabs() was drawn twice on
  the saved page.
- A name repeated in `layout()` was placed once per repeat (100,000
  repeats: an 18.1 MB page) or kept its last place, in silence; dash.ado
  refuses it now (P20-31).
- The parity corpus's `tabs()` entry wrote `"A: g1; B: g2"`, which tabs()
  reads as ONE tab holding g2, so no two-tab dashboard was ever compared;
  fixed in its own commit (`4f6a314`) with a test that it builds two tabs.

Not done here, recorded for later: the saved `layout(bs)` page puts the
filters above the title where every other layout puts them below; the
served grid does not copy the saved KPI cells' minimum heights.  A third,
that under a saved `layout(bs)` a `by()` graph's panels ignored `cols()`
where the served grid honoured it, was fixed in the commit after this one,
with an unbounded `cols()` found on the way (both in BUGS.md).

### Verification, measured

23sep2026, branch `feature/batch4-interactive-layer` (`main` already an
ancestor, so nothing to pull).  As for WP-20, both suites ran on the working
tree, which also carries test-infrastructure changes from other work that
are not part of this commit; the commit's own tree was then run on its own,
last below.

- `test/run_all_cscripts.do` with the console binary: **49 passed, 0
  failed, 0 skipped**, in 47 s -- the new `test_export.cscript`
  (EXP-01..06) among them, `test_adversarial.cscript` with P20-31 (a name
  repeated in `layout()` refused) and `test_echo_text.cscript` with the
  repeated-name refusals echoed as typed.  No file a script reads changed
  after it.
- `python3 -m pytest test/ -q`, first run: 10,793 passed, **1 failed**,
  2:15.  `test_varlist_expansion.py`'s single-y golden hash: the page
  carries the new tools.  Diffed token by token against `HEAD`, whose
  output gives the recorded `5e1c3a24`: four chunks, all insertions -- the
  grid toolbar's box zoom (with its default overlay), undo, redo and its
  save named `dashboard`, and the figure's own four new tools.
  Re-baselined to `20a7cb46`, with that reason beside the constant.
- Second run: **10,794 passed, 0 failed**, 61 skipped, 6 xfailed, 2:15.
  Every skip is structural: `test_cscript_hygiene.py` checks that do not
  apply to a given script.  The `layout(bs)` parity entry, the one other
  skip until now, is compared.
- The commit's own tree -- `HEAD` with only the staged WP-21 diff applied,
  in a separate worktree, with `HEAD`'s `conftest.py` and no
  `pyproject.toml` -- run whole with `-n auto`: **10,776 passed, 0
  failed**, 61 skipped, 6 xfailed, 4:08.  The 18 fewer are the two
  uncommitted infrastructure test files.  The certification scripts were
  not rerun there: the files they read are byte-identical to the ones they
  ran against, and what changed after them -- this record and the golden
  hash -- no script reads.

---

## WP-22 · `twoway` parity — DONE

**Gaps closed:** F1, F2, F3 · **Severity:** S2/S3 · **Effort:** L · **Depends on:** WP-09

> **User story.** As a Stata user, I want `dash.sthlp`'s drop-in claim to hold
> — or to be told precisely where it does not.

### Business requirements

- **BR-22.1** Every `twoway` plot type either renders or is documented as
  unsupported — the user is never surprised at the command line.
- **BR-22.2** Options that are aliases of implemented ones behave as `twoway`
  does.
- **BR-22.3** No implementation limit may silently cap future growth.

### What was measured before any code changed

23sep2026 at `9f48cf7`, StataNow 19.5 with the console binary:

| Question | Measured |
|---|---|
| `contour`, `contourline`, `pcarrowi`, `pccapsym` | `twoway` draws all four (rc 0) and takes no abbreviation of any; dash refused each with "unrecognised plot type", r(198), and its Supported: list |
| Every `twoway` plot type | `graph_twoway.sthlp` links 41; beyond the four above, `rpcap` and `rpspike` (y ylow yhigh x) are new in StataNow 19.5, run with rc 0, take no abbreviation, and were "unrecognised" to dash |
| Plot types in the help | dash drew 38; `dash.sthlp` listed none of them anywhere, and nine were not named at all: `pcarrow pcbarrow pci pcscatter pcspike rconnected rscatter tsline tsrline` |
| F3's options | `clcolor() clpattern() clwidth()` are not plain aliases: `twoway_yxview_parse.class` applies them after the l-options whatever the order, to the connecting line only (lcolor() also outlines areas and bars); `mlabangle()`, `mlabformat()`, `sort(varlist)`, `mlabvposition()`, `mlabtextstyle()` and `xoverhangs`/`yoverhangs` are real `twoway` options; `xreverse`, `yreverse`, `xalternate`, `yalternate`, `xcommon`, `ycommon`, `lockaspect`, `zoom()`, `ddensity`, `altaxis`, `addplot()`, `margin()` and `region()` are refused by `twoway` at the level they were written (r(198)) -- sub-options of `xscale()`, `plotregion()`, `legend()`, `clegend()`, or options of `graph combine`, `histogram` or no command at all |
| The `inlist()` ceiling | ten plot-type tests in dash.ado were string `inlist()` calls; the range types' held nine literals and `ptype`, Stata's limit of ten, so a tenth range type could not be added |

### Technical requirements, as delivered

- **TR-22.1** `pcarrowi` and `pccapsym` are drawn, in both modes.
  `pccapsym` is a spike with the same marker at each end -- line options
  style the spike, marker options the markers, `mlabel()` labels the first
  point (`map_pccapsym`).  `pcarrowi` reads its values as `twoway` does
  (`#y1 #x1 #y2 #x2 [(#clockpos)] ["label"]`, a Mata reader in
  dash_parse.mata that runs in linear time), refuses with r(198) what
  `twoway` refuses, drops an incomplete last arrow with a note, and draws
  through pcarrow's own mapper with its labels at the tails
  (`map_pcarrowi`).  Four `twoway` plot types dash does not draw --
  `contour`, `contourline`, `rpcap`, `rpspike` -- are refused by
  name, r(198), each with what to use instead (`_dash_undrawn_plottype`),
  instead of as "unrecognised plot type".
- **TR-22.2** `dash.sthlp` has a Plot types section: every type dash draws,
  in `twoway`'s groups, the five it refuses and why, and the notes on
  `pccapsym` and `pcarrowi`.  The syntax line and Differences item 5 point to
  it; item 5 no longer claims that a copy-pasted command always runs.
  `test_help_plot_types.py` holds the section to the code in both
  directions.
- **TR-22.3** The triage, measured against `twoway`: `clcolor()`,
  `clpattern()` and `clwidth()` are honoured as `twoway` defines them -- on
  the connecting line of the plot types that draw one, over the l-options
  whatever the order, never on markers (`_dash_fold_cl` in dash.ado, the
  shared `_apply_line_opts`); `mlabangle()` (Stata's anglestyles or
  degrees) and `mlabformat()` (%f and %e) are honoured; `sort(varlist)`,
  `mlabvposition()`, `mlabtextstyle()` and `xoverhangs`/`yoverhangs` are
  declared, listed in the help's Unsupported section and named in the note
  as declared; the names that are not `twoway` options where they were
  written stay unknown, named in the note, and the help gives `twoway`'s own
  spelling for each.  The help's claim that `twoway` sorts line plots by x
  was wrong and is corrected.
- **TR-22.4** Every plot-type test in dash.ado is `: list ptype in <family>`
  over family lists defined once (`_dash_plottype_families`), equal to the
  renderer's own sets; no string `inlist()` is left on a plot-type macro.

### Acceptance

- **AC-22.1** Every plot type `graph_twoway.sthlp` links in StataNow 19.5 is
  drawn by dash or refused by name and documented:
  `test_help_plot_types.py`, `test_parser.cscript` P1A-49..59,
  `test_pccapsym_pcarrowi.py` (45 tests), `test_conformance.cscript` C-06,
  and the mode-parity corpus's bare and labelled entries for both new types.
- **AC-22.2** `clcolor()`/`clpattern()`/`clwidth()` work as `twoway` does:
  `test_twoway_option_parity.py` (134 tests) and
  `test_twoway_option_parity.cscript` (47 checks, among them every plot type
  against a live `twoway` run), OV-149..156.
- **AC-22.3** A tenth range type compiles: `test_plottype_families.py`, and
  `test_parser.cscript` P1A-56, where a tenth and eleventh range member are
  found by `: list` while `inlist()` of the same list is r(130).

### Found on the way

- `map_pcarrow`, which pcarrowi draws through, added one arrowhead per
  `add_layout()` call, each copying the annotation list: 8,000 arrows took
  85 s.  They are added in one change now, linearly (BUGS.md).
- dash_parse.mata's `_json_escape` was dead code, and wrong -- it wrote
  four backslashes for one; the pcarrowi reader uses a rewritten one that
  escapes every control character and the characters that would break a
  Stata macro.
- Recorded for later, each measured: `pcbarrow` still adds its arrowheads
  one at a time; `scatteri` and `pci` pass their tokens into the spec
  unchecked, so a malformed one fails the build with a JSON traceback;
  dash draws marker labels on plot types `twoway` never labels, shows a
  value-labelled `mlabel()` as codes, and styles marker borders with line
  options; `dash build` of immediate graphs alone fails; `rpcap` and
  `rpspike` could be drawn later (they are siblings of `rcap` and
  `rspike`).  Separate tasks carry the first several.

### Verification, measured

23sep2026, branch `feature/batch4-interactive-layer`, on top of the four
fixes committed after WP-21 (`f92ef65`, `dbe24bc`, `0744eb6`, `99d5bed`;
`main` already an ancestor, so nothing to pull).  Two agents did the work
in worktrees cut from `9f48cf7`, each writing its tests first against that
code; their diffs were merged by three-way apply, with one conflict --
`test_adversarial.cscript`'s P20-33 beside P22-01..03, both kept.  The
refusals of `rpcap` and `rpspike` came after: P1A-58's new
checks failed on the merged code without them (r(3498)).

- `test/run_all_cscripts.do` with the console binary: **50 passed, 0
  failed, 0 skipped** -- the new `test_twoway_option_parity.cscript` among
  them, `test_parser.cscript` with P1A-49..59, `test_adversarial.cscript`
  with P22-01..03, `test_conformance.cscript` with C-06 and
  `test_option_validation.cscript` with OV-149..156.
- `python3 -m pytest test/ -q`: **11,375 passed, 0 failed**, 63 skipped,
  6 xfailed, 2:34.  The two new skips are `test_cscript_hygiene.py` checks
  that do not apply to the new script.
- The commit's own tree -- `HEAD` with only the staged WP-22 diff applied,
  in a separate worktree, with `HEAD`'s `conftest.py` and no
  `pyproject.toml` -- ran the fourteen test files WP-22 adds or changes,
  with `-n auto`: **4,245 passed, 0 failed**, 63 skipped, 5 xfailed.

---

## WP-23 · Documentation reconciliation — DONE

**Gaps closed:** F4, F5, M1, M4, M5, C1, C2 · **Severity:** S2/S3 · **Effort:** M (delivered as L) · **Depends on:** all feature packages

> **User story.** As a user, I want the help file to describe the command I
> actually have.

### Business requirements

- **BR-23.1** Every claim in `dash.sthlp` is true of the shipped code.
- **BR-23.2** Every supported capability is documented.
- **BR-23.3** No tracking document in the repository claims work that is not
  done.

### What was measured before any code changed

23sep2026 at `4ede074`, StataNow 19.5 with the console binary, `twoway` as
the oracle for every claim about `twoway`, both render modes for every
claim about a dashboard:

| Question | Measured |
|---|---|
| F4's nine rows | Two had been fixed (the bare-name scheme, WP-17; the scipy text, WP-18) and one was true (`nodraw` on `dash build`).  Six were still false: `dash kpi p97.5(price)` was r(198); repeated `filter()` groups were joined with `\|\|`, not a semicolon, and a label holding `;`, `\|\|`, `exclude(` or an apostrophe broke the build or dropped an `exclude()`; `xtick()`, recorded as fixed by WP-14/15, still replaced the labels when alone and was dropped beside `xlabel()`; `colorvar()` was drawn on four plot types and dropped in silence on the other thirty-six; `legend(top)` and its three siblings were drawn inside the plot where `twoway` refuses them; `ylabel2()`/`xlabel2()` drew no ticks for anything but a numlist |
| The rest of the help | Eight parallel audits read every claim of every section against the code, each keeping a ledger of the claim, the test that holds it and any correction: 56 claims were false because of a code defect, and the others that were false or imprecise were corrected in the help |
| TR-23.3's names | `hover()`, `marker()` and `mlg()` had no entry at all -- the old conformance test passed `hover()` on the words "hover tooltips" and `marker()` on SMCL's own `{marker}` tags; `bands()`, `n()`, `range()` and `base()` named some of their plot types; `$dash_nobrowser` was a mention in two rows; 37 plot-type spellings and a dozen option spellings dash accepts and `twoway` refuses were written nowhere |
| TR-23.4, Server Mode | the comparison table did not render as a table (Stata collapsed its spaces), several rows were false, and `dash serve` aborted on every launch with r(7102) -- 7ddbc08 (WP-08's TR-08.8) had made the renderer refuse the extension-less tempfile `_dash_serve` hands it on purpose, and no test ran a real launch (GAPS C1, C2) |
| TR-23.5 | `TODO.md` (555 items, all checked) and `PLAN.md` described the plan overtaken in September; `BUGS.md` held 260 entries, 7 open -- 2 of them already fixed -- and 26 closed entries named no test that exists; 28 gaps that a finished work package or a commit had closed were still marked open in GAPS.md |
| TR-23.6, TR-23.7 | the generator NOTE was there four times and the t/b/l/r fold three times; the explicit `T() B() L() R()` were reached only by a third spelling after `t1title()` and `t2title()`, which the fold then dropped without a word at graph level; the `inlist()` ceiling was gone (WP-22) |
| The rendered help | from the Faceting example to the end of the file, Stata's own renderer showed raw SMCL: a paragraph left open before an example cascades; beside it a directive split over two lines, five `{opt name(` rows in the Region table and an `{in}` |
| The help's examples | nothing ran them: an `lpoly` example drew one point of its curve (a bandwidth written as a fraction), a refused weighted command left its weight in `s()` for the next command to use, three `dash build` examples needed graphs no earlier line registered, and one used variables no shipped dataset has |

### Technical requirements, as delivered

- **TR-23.1** Every F4 claim is true, by making the code do what the help
  says where that is `twoway`'s behaviour or an intended feature, and
  otherwise by correcting the help: a KPI percentile is any p strictly
  between 0 and 100 with `_pctile`'s value in both modes -- and both
  renderers' percentile rule, which disagreed with Stata at large n, is
  Stata's; filter groups are split only outside quotes and parentheses, in
  Mata and in the renderer, so a label may hold any character; `xtick()`
  draws ticks without labels beside the labels, and `grid` as `twoway`
  draws it; `colorvar()` is named in the note where it is not drawn;
  `legend(top|bottom|left|right)` is refused with r(198), naming the
  `position()` meant; `ylabel2()`/`xlabel2()` take `ylabel()`'s grammar;
  `nodraw` and the scipy text are pinned.  The whole help was audited the
  same way, section by section: 56 defects fixed test-first, each with a
  BUGS.md entry -- among them `dash serve`, a second axis drawn on a
  0-to-1 range for eighteen plot types, a qualifier after the plot groups
  dropped in silence, `tsline` drawn against a variable where `twoway`
  draws against the time, seventeen plot types with no tooltip, a saved
  page's brush that never updated a KPI card, and marker labels anchored at
  their corner at every clock position.  One false claim is corrected
  rather than fixed: an option dash honours on some plot types, given on
  one that does not take it, is ignored where `twoway` refuses it -- the
  help now says so, and a test pins it.
- **TR-23.2** The Plot types section (WP-22) gains a Synonyms table: the
  37 spellings only dash accepts, beside `twoway`'s own abbreviations
  (`sc`, `li`, `con`, `hist`, `rsc`, `rl`, `rcon`, `fun`, `mbands`, `fn` --
  the last two refused by dash until now).
- **TR-23.3** `hover()`, `marker()`, `color()`, `bands()`, `n()`,
  `range()` and `base()` have definition entries naming the plot types that
  take them; `mlg()`, `bw()`, `bins()`, `colv()`, `cv()`, `pbgc()`, the
  twelve second-axis synonyms and `jit()` are written beside their options;
  `$dash_nobrowser` is defined under Dashboard Options
  (`{marker nobrowser_global}`).
- **TR-23.4** The Server Mode section is rewritten against both modes: the
  comparison table renders, every row is measured, and a limitations block
  says what the served app does not do (dates, a phone viewport, the
  dimming of an unselected point).  `dash serve` launches again: on the
  `--launch` route the renderer takes a `.py` name or one no file holds
  yet, never overwriting another file, and the app stays a Stata tempfile
  erased on exit, error or Ctrl+C (C1); a real launch runs in the
  certification suite (C2).
- **TR-23.5** Retired rather than reconciled: `TODO.md` and `PLAN.md` are
  deleted (the last commit that holds them is `4ede074`).  `BUGS.md` is
  reconciled: every open entry is measured and says why it is open, the two
  already fixed are closed with their commits, and every closed entry names
  a test that exists -- three name none and say so (WP-24).  GAPS.md and
  ROADMAP.md agree both ways on every gap a DONE package closes (WP-06's J6
  is qualified to what it did).  `test/test_tracking_documents.py` holds the
  three documents to all of it.  `.ultraplan/`, `REMAINING.md` and
  `phases/` are the user's records and are left to them.
- **TR-23.6** Every duplicate is gone, and with `T() B() L() R()` goes the
  one thing they did: a third t(), b(), l() or r() at graph level is named
  like any other unsupported spelling (BUGS.md).  The helper the
  abbreviation tests share uses the measured rule (a digit ends the run of
  capitals).
- **TR-23.7** Verified: no string `inlist()` of ten or more arguments is
  left (WP-22's TR-22.4).

### Acceptance

- **AC-23.1** Every claim in `dash.sthlp` is verified by a test or
  corrected: each audit kept a claims ledger, and the claims are pinned by
  `test/test_help_claims_1.py` to `_8.py` and their `.cscript` twins (by
  section), `test/test_help_examples.cscript` (every example command run
  from a fresh session and held to the return code and output the help
  shows; both help files rendered by Stata and held to no SMCL left as
  text) and `test/test_help_examples.py`.
- **AC-23.2** Every supported plot type and honoured option is documented:
  `test_help_plot_types.py`, and `test_help_conformance.py`, which now
  derives dash's alias spellings from `dash.ado`'s own folds and its
  plot-type expander, measures them against `twoway`
  (`test/fixtures/alias_spelling_truth.json`), and requires every spelling
  `twoway` refuses to be written in the help and every dash-only option to
  have a definition entry.
- **AC-23.3** No tracking document claims work that is not done:
  `test_tracking_documents.py`.

### Found on the way, not fixed

Each measured; follow-up tasks carry them.  An option given on a plot type
that does not take it is ignored where `twoway` refuses it (documented);
after a served filter move a raw layer of an unlinked graph loses its own
`in` and draws every row the filter keeps (its fit and a KPI card's `in`
are counted over observations since WP-23);
`exclude()` holds only while its own filter moves; a per-graph `scheme()`
is drawn differently by the two modes; a title or qualifier that opens with
an apostrophe is refused; user text is macro-expanded a second time; the
renderer refuses `~x` on a numeric column; a repeated option lands in its
`*2` twin; `bwi()` is ignored; `xline()` positions and `colordiscrete`
levels are unbounded and cost quadratic time; Bokeh's minor ticks are drawn
by default (documented).  WP-01, WP-02 and WP-04 meet their acceptance
criteria (measured by this package; WP-01's and WP-04's re-run on the
WP-23 tree), but several of the tests their plans name were written under
other names or not at all, so heading them DONE waits on WP-24's
AC-to-test mapping; WP-03's C1 and C2 are closed here, and its AC-03.4 has
no regression test (BUGS.md, the "file not found" entry).  *Since then:*
WP-24 mapped every acceptance criterion of WP-01 to WP-04 to a test that
goes red when the criterion is broken, and all four are DONE; AC-03.4 is
held by `test/test_bug_regressions.cscript` BR-02.  A title or qualifier
holding an apostrophe after a double quote is stored as typed, and user
text is expanded once, where the user typed it, since 24sep2026 (BUGS.md,
"Any dash command holding a double quote followed by an apostrophe
stopped at the entry" and "dash expanded macros in user text a second
time"; `test/test_json_escaping.cscript` JSE-42 to JSE-70).  A served
filter move keeps a raw layer's own `if` and `in`, and clears a brushed
selection as the saved page does, since 24sep2026 (BUGS.md, "The served
app dropped a layer's own if() and in() at the first filter move";
`test/test_mode_parity.py` TestALayersOwnQualifierAfterAMove).  The
renderer reads `!x` and `~x` on a numeric column as Stata does, and a
qualifier is stored with its abbreviations written out, since 24sep2026
(BUGS.md, "The renderer skipped `if !x' and `if ~x' on a numeric column"
and "A qualifier that abbreviates a variable is skipped by the renderer";
`test/test_qualifier_literals.cscript` QL-16 to QL-22).

### Verification, measured

Certification 59/59 passed, 0 failed, 0 skipped (nine new scripts: test_help_claims_1 to _8 and test_help_examples, among them a real `dash serve` of one minute).  pytest 14173 passed, 72 skipped, 6 xfailed, 0 failed -- the six xfails are the served date gap this package narrows (five) and one that predates it.  Each part ran its new tests against `4ede074` first; every test that pins a fix failed there.

---

## WP-24 · Test integrity — DONE

**Gaps closed:** L3, L4, L5, L6, L7, L9 · **Severity:** S1/S2 · **Effort:** M (delivered as L) · **Depends on:** —

> **User story.** As a maintainer, I want a green suite to mean the code
> works.

### Business requirements

- **BR-24.1** Every test fails when its subject is broken.
- **BR-24.2** Every function of every feature has a behavioural test
  (CLAUDE.md rule 4).
- **BR-24.3** Every fixed defect has a regression test (CLAUDE.md rule 8).

### What was measured before any test changed

24sep2026, at `68327a8` and `a2c7502`, StataNow 19.5 with the console binary.
A test was judged by breaking what it names -- the product behaviour, on a
copy of the tree -- and running it:

| Question | Measured |
|---|---|
| Tests that verify nothing (TR-24.2, TR-24.3, L5) | 23 of 4367 test functions at `a2c7502` (GAPS.md counted 19 of 2340 when written); the three TR-24.2 names could not fail, and `test_options.py`'s claim was false -- nothing clamps an out-of-range RGB, Stata notes it and draws the default.  A scan for AC-24.2's shapes found 30: 23 with no verification, 5 handlers that swallow a failure, 1 refusal never asserted, 1 AssertionError caught.  Four more returned green when a precondition failed; BUG-33's regression test had never asserted anything (its data lacked the variable it filtered on) and BUG-32's re-filtered on "All" |
| Source-text tests (TR-24.5, L4) | 481 reviewed: 46 were the only coverage of their behaviour, 89 deliberate structural guards, 205 duplicated by a behavioural test, 141 not source tests.  `_dash_json_get_str`'s regression test asserted only that its name was in the source |
| Vacuous pass conditions (TR-24.4, L6) | C-03's "drew nothing" line scan passed with the report reworded, and with a layer drawing nothing and its report silenced; `test_every_plot_type_draws.py`, parametrized by a regex over a display string, passed with rscatter drawn blank and dropped from that string.  `cert_file_has` searched 32,768-character pieces alone, so each of its 423 calls in 37 scripts could miss a needle across a piece boundary, and log searches failed from a 212-character checkout path.  The same shapes -- floors, needles the inlined BokehJS carries on every page, absence checks with no control, loops that could run zero times, a skip where a failure belonged -- were found throughout the certification scripts and pytest files |
| Untested programs and functions (TR-24.6, L7) | Instrumented, the certification suite entered 61 of 63 ado programs (`dash_setup`'s body never: HON-14/15 stop at its syntax line) and 52 of 55 Mata functions; pytest executed 434 of 440 renderer functions, and skipping each function's body was caught for 436 of 453 -- 5 were genuinely unchecked.  The existence loop GAPS L7 cites listed 22 of 56 programs, not all but three |
| Bug regressions (TR-24.7, L9) | Three closed BUGS.md entries had no test that could fail: the fills of `comprehensive_demo.do`, the "file not found" note, `ylabel(#5, grid)` |
| The fixes of WP-01..WP-08 (the test plan) | WP-01..04: nine fix parts no committed test caught.  WP-05..08: of 108 mutations, 78 caught, 4 equivalent, 26 missed |

### Technical requirements, as delivered

- **TR-24.1** Delivered by WP-08 (`test_utf8_validation.cscript` UTF-01..12)
  and tightened here: UTF-13 runs every sequence of GAPS A9's table through
  the gate for r(198) and "non-UTF-8" (with the message reduced to "invalid
  input", UTF-01..12 had passed); UTF-10 holds exactly 2,245 fixture
  sequences and exits 601 on a missing fixture, which was a skip; UTF-11
  names the program each of the six gates sits in.
- **TR-24.2 / TR-24.3** All 23 tests with no verification, and the three
  that could not fail, assert what they name.  `test_rgb_clamps_at_255` was
  replaced by three tests of what Stata does.  `test/test_test_integrity.py`
  enforces AC-24.2 over every test file: an AssertionError caught; a broad
  handler that returns, passes or continues; a handler that skips a try's
  assertions; no verification; a return before verifying; an assert that
  cannot be false.  Each rule is tested against its own examples; the
  allowlist is empty.
- **TR-24.4** C-03 and C-04 read the saved page's document; C-01's corpus
  is the renderer's own list of plot types; C-00 tests the readers.
  `test_every_plot_type_draws.py` is parametrized by `_dash_plot_type_names()`,
  held equal to the Mata table.  `cert_helpers.do` reads files whole, and
  `cert_log_has` searches a log with its wrapped lines re-joined, as the
  four scripts that keep a log reader of their own now do too.  Beyond the two the
  plan named, every vacuous condition found was replaced, in two rounds,
  each change shown red under a break its old form passed: in
  `test_server.py` five loops that never ran, 24 `roots > 0` and
  `len(html) > 100` floors and six product-state skips; in
  `test_html_output.py` checks of canvas text that is never in a page, of
  escaped markup, of pages with no document, and some forty needles BokehJS
  carries on every page; floors, one-letter needles and value checks in the
  filter, KPI, glyph, layout, scheme, security, resource-limit, serve and
  help files, read now from what the page or the app draws; and skips over a
  missing committed fixture made failures.
- **TR-24.5** Every source-text test that was the only coverage of its
  behaviour runs the code: `_dash_json_get_str` has 43 behavioural cases
  and `test_qualifier_literals.cscript` QL-01..15; the paired-coordinate
  checks are P1A-56; `test_serve_options.cscript` [6/7] and [7/7] run
  `_dash_serve_spec`; the Windows browser commands, which ran only on
  Windows, go through one opener, `_dash_open_page`, that returns its
  command without running it (`test_serve_browser.cscript` SB-13..20);
  `dash_setup`'s eight are held by runs of `dash_setup` itself; the layout
  and websocket-origin checks drive both modes and a live server.  The
  structural guards that remain say so in their docstrings.
- **TR-24.6** `test_program_coverage.cscript` PC-01..11 and PC-31 test the
  three programs L7 names with ordinary, edge, hostile and abbreviated input
  on both routes; PC-15..26 run `dash_setup` end to end in a sandbox that
  starts no process (`test/setup_sandbox.py`, itself tested), as do
  `test_setup_honesty.cscript` HON-19..28.  All three programs are in the
  existence loop.
- **TR-24.7** `test_bug_regressions.cscript` BR-01..03 and
  `test_bug_regressions.py`; `CLOSED_WITHOUT_A_TEST` is empty.

Defects found on the way and fixed test-first, each with a BUGS.md entry
naming its test: `inrange()` with a missing bound selected no rows, in both
modes; both renderers read a qualifier's string literals as Python source,
and the served filter callback re-applied a graph's qualifier with a private
copy of that code; the Mata library check named 22 of the 23 functions
dash.ado called, checked one while the library was in memory, and could not
repair a partly loaded library; a date format holding a quote, backtick or
dollar sign was lost or refused on every render, a failing jsonio left dates
`%12.0g`, and a variable a qualifier abbreviates is read by its stored name;
`saving()` refused a `..` inside a file name on the server route, and a
double quote gave r(132); `BOKEH_ALLOW_WS_ORIGIN` replaced the served app's
origin list without a word -- the launcher now says so, and warns when it
admits every site.  The browser opener, rewritten to be testable, now hands
the shell a single-quoted path it no longer expands.  In the tests
themselves, `cert_file_has` missed a needle across a 32,768-character piece;
log checks depended on the checkout's path; `test_security_surface.py` failed
when run alone; the `dash_setup` sandbox blocked a package but not its cached
submodules, so PC-18 could not see BUG-50's own break; and an absence check
read a page an earlier script had left under a reused tempfile name.

### Acceptance

- **AC-24.1** Every test this package changed or added was run against a
  break of its subject and failed there, each recorded with the old test's
  result under the same break (WP-01..08's are summarised in their own
  records above).
- **AC-24.2** `test/test_test_integrity.py`, empty allowlist.
- **AC-24.3** `test/program_coverage_map.py` names the behavioural test of
  each of the 123 ado programs and Mata functions, and
  `test/function_test_map.py` that of each of the 467 renderer
  functions, every one measured to fail when its function's body is
  skipped; their guards fail on a unit with no test, a stale entry, a
  missing test, or dead code becoming reachable.  One unit has no test by
  design: `_dash_graph_opts_to_json`, uncalled and broken, which WP-26
  removes.
- **AC-24.4** Every closed BUGS.md entry names a test that exists
  (`test_tracking_documents.py`); none is listed as without one.

### Found on the way, not fixed

Each measured and recorded as an open BUGS.md entry saying why it stays
open (a product change outside test integrity): a saved page's filter
leaves line, tsline, area, bar, spike, dropline and connected layers as
they were; the one-line form overwrites an existing file named by
`saving()` without `replace`, and ignores `replace` -- the one to fix first;
a qualifier that abbreviates a variable, or holds a subscript or a function
call, is skipped by the renderer and every row drawn; a function layer
naming an unknown function draws nothing where twoway refuses it; nested
compound quotes are refused; an lfit of a variable with no spread draws a
sloped segment; an empty dataset is reported as missing its variables;
`xline()`/`yline()` ignore the scheme; `filterposition(left)` prints Bokeh's
W-1005; the one-line form ignores `by()`'s `cols()`; `#N` ticks fall where
Bokeh puts them; `gsize text` is read by nothing (a strict xfail); a linked
`by()` graph with a line layer logs Bokeh's E-1024; a column name holding
markup gets no tooltip; a lone `yaxis(2)` draws two axes; a range layer with
no second y variable is misreported.  Whether dash should refuse
`BOKEH_ALLOW_WS_ORIGIN=*` outright, or treat its origins as additions, is a
policy choice left to the maintainer (WP-20 pinned the variable as the
operator's).  Concurrent Stata sessions (up to eighteen) once rewrote the
console binary's settings file without its Python lines, and every script
then skipped: the runner counts skips, and no more than three sessions now
run at once.

Left in the tests, deliberately: a few checks in `test_html_output.py` look
in the page for a colour or title no default carries, which fails when the
option is ignored but not when it lands on the wrong property; four floors
that sit beside an exact check of the same scan.  Noted, not measured
further: `%tb` business-calendar formats are not treated as dates by either
side; the uncalled `_dash_kv_json` refuses a backtick (WP-26 removes it);
`DashRenderer._kpi_update_modes` is written and never read.

### Verification, measured

Certification 63/63 passed, 0 failed, 0 skipped, in one session (four new
scripts: test_bug_regressions, test_program_coverage, test_qualifier_literals
and test_mata_library_guard).  pytest 14804 passed, 8 xfailed, 0 failed, 0
skipped -- the 68 skips before were per-script checks run over scripts they
do not apply to, which are no longer generated.  The eight xfails are the
open BUGS.md entries they name: the served app's date gap (five), the saved
page's line filter, the constant-x lfit and `gsize text`.  Each part ran its
new tests against its base first; every test that pins a fix failed there.
The first part was committed at `7c28802` after its own full runs
(certification 63/63, pytest 14753 passed).

---

## WP-25 · Test infrastructure — DONE

**Gaps closed:** L1, L2, L8 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-24

> **Changed by the maintainer's decisions and by measurement (24sep2026).**
> The maintainer chose **local CI**: `make check` and a versioned pre-push
> hook run both suites under both interpreters; no hosted workflow, because
> GitHub's runners have no Stata and `wbuchanan/dash` is private and has
> never been pushed to (no branch on the remote, measured).  The maintainer
> also chose to commit the uncommitted test infrastructure already on the
> working tree -- `pyproject.toml` (the pytest configuration, parallel by
> default), `test/conftest.py`'s full-suite lock, parity grouping and
> Bokeh-document clearing, `test/test_suite_lock.py` and
> `test/test_bokeh_document_hygiene.py` -- so TR-25.3's configuration is
> `pyproject.toml`, which `.git/info/exclude` does not drop, and no
> `pytest.ini` is added (one would override it).  Measured before this
> package: `packaging` is installed under both interpreters, so TR-25.6's
> seven `lowess` skips no longer occur (0 skipped under the development
> interpreter); Stata's `c(python_exec)`, `/opt/anaconda3/bin/python3`
> 3.13.9 (bokeh 3.8.0, pandas 2.3.3), already carries pytest 8.4.2 and
> pytest-xdist 3.8.0; `test/fixtures/scheme_visual/` holds 8 PNGs and
> `truth.json`, and the one high-severity disagreement `truth.json` records
> (s1mono's line colours) is fixed.  The maintainer then asked for the
> Python Stata ships to be the reference: `make test` runs it first, and the
> development interpreter follows in `make check`.
>
> **What running under Stata's Python found (24sep2026).**  The first full
> pytest run under `/opt/anaconda3/bin/python3` gave 6 failed, 15220
> passed, 0 skipped -- failures the development interpreter never showed.
> Two were a security hole: under bokeh 3.8 the served app admitted a
> websocket origin whose host only begins with an allowed one
> (`localhost.evil.example`, `127.0.0.1.nip.io`), fixed in dash whatever
> Bokeh it runs under.  One was a defect: under pandas 2.3 one far-future
> date blanked a whole date column.  Three were the tests' own: a page hash
> that recorded the Bokeh version, a time bound measured inside tracemalloc,
> and a text-sink safety gate that needed its browser checks run on bokeh
> 3.8.0, which were run.  BUGS.md records each.

#### The plan in detail

**US-25.1** As a maintainer, I run one command and learn whether both
suites pass under both interpreters, and a push cannot leave with either
red.  **US-25.2** As the next auditor, every test asset I find is read by a
test, and every fixture says what it is.

**TR-25.1 (L1), local CI.**  A `Makefile` at the package root:
`make test` (pytest under Stata's `c(python_exec)`, read from Stata itself
by `scripts/stata_python_exec.sh` through the console binary), `make
test-dev` (pytest under the development interpreter), `make cert`
(`scripts/run_cert_suite.sh`: the certification runner from a scratch
directory with its own `STATATMP`, judged from its log by
`scripts/cert_verdict.py`, which passes only when every script the runner
registers passed and none skipped, since Stata's batch mode returns no exit
status), `make check` (all three, in that order), and `make hooks` (points
`core.hooksPath` at `scripts/git-hooks`, whose `pre-push` runs `make
check`; opt-in, since it changes the clone's git configuration).  Both
pytest targets set `DASH_STRICT=1`.

**TR-25.2 (L2), both interpreters, strict.**  Under `DASH_STRICT=1`,
`test/conftest.py` (a) refuses to start, `pytest.UsageError`, when the
interpreter or its libraries differ from the baseline `DASH_BASELINE`
names -- `dev` (Python 3.14, bokeh 3.9, pandas 3.0, numpy 2.4, scipy 1.17)
or `stata` (the versions Stata's interpreter carries, measured) -- and (b)
turns the run red when any test skips, naming each skip and its reason.
Without `DASH_STRICT` both stay warnings, as today.  The baselines live in
conftest.py itself; its pointer to `.ultraplan/BASELINE.md`, a file no
longer in the tree, goes.

**TR-25.3** `pyproject.toml` is committed as the pytest configuration.

**TR-25.4 (L8).**  The 15 unreferenced `.do` files in `test/` are deleted:
March 2026 diagnostics with hard-coded paths and no assertion, for a
defect the certification suite covers.  `scheme_visual/truth.json` is
wired into `test/test_scheme_visual_truth.py`, which holds the scheme
parser's colours, symbols and patterns for each of the four schemes to what
Stata drew, and each PNG to the graph size the record gives it.  A guard
in `test/test_fixtures_are_committed.py` requires every file under
`test/fixtures` to be named by a test and every `.do` file in `test/` to be
named by the runner or a script, and its message no longer claims every
fixture is read.

**TR-25.5 (L8)** `abbrev_truth.json`'s `_meta` gains a `status` note: its
`dash` fields and `dash_*` lists record dash on 18 Sep 2026, before BR-04's
fix, and `test_abbreviations.py` holds today's declarations to its Stata
fields.

**TR-25.6** Measured resolved; recorded.

**TR-25.7** The two mislabels are corrected.

#### Test plan

- Each strict rule has a unit test on its helper (drift, skips), and a
  subprocess test running a throwaway suite: a skip turns it red under
  `DASH_STRICT=1` and not without it; a drifted baseline refuses to start.
- `scripts/run_cert_suite.sh`'s verdict is unit-tested on runner logs: all
  passed, one failed, one skipped, a truncated log, a missing script.
- The self-verifying run of this package's own plan: `make check` on the
  clean tree is green; on a scratch copy with a deliberately failing
  pytest test, a deliberately skipping one, and a deliberately failing
  certification case, each is red.
- `test/test_scheme_visual_truth.py` fails when a scheme colour, symbol or
  pattern is changed from what Stata drew (mutation in a scratch copy).

> **User story.** As a maintainer, I want both suites to run automatically,
> under the interpreter that actually ships.

### Business requirements

- **BR-25.1** Both suites run automatically, and a failure or an unexpected
  skip blocks the change.
- **BR-25.2** The suites run under the interpreter that actually ships.
- **BR-25.3** No test asset is unreferenced, and no fixture describes itself
  falsely.

### Technical requirements

- **TR-25.1 (L1).** Add a CI configuration running both suites. There is no
  `.github`, `.gitlab`, `travis` or `circle` config, no Makefile, and no
  `pytest.ini`/`pyproject.toml`/`setup.cfg` — **nothing enforces that either
  suite runs before a commit.**
- **TR-25.2 (L2).** Run pytest under Stata's `c(python_exec)` as well as the
  development interpreter, and make `conftest.py`'s drift warning
  (`:41-52`) a **failure** in CI. Today pytest runs on bokeh 3.9/pandas 3.0
  and Stata on bokeh 3.8/pandas 2.3, so a green pytest does not prove the
  shipped path works.
- **TR-25.3** Add a `pytest.ini` — note `.git/info/exclude` carries `*.ini`,
  which is why one was avoided; fix the exclude rather than working around it.
- **TR-25.4 (L8).** Delete or wire up the 15 unreferenced `.do` files in
  `test/`. Either wire up `test/fixtures/scheme_visual/` (9 PNGs, referenced
  by no test) or fix `test_fixtures_are_committed.py:83-90`, whose docstring
  falsely claims they are "read by the test suite".
- **TR-25.5 (L8).** Annotate `test/fixtures/abbrev_truth.json` as a **pre-fix
  record**. All 25 historical mis-mappings it documents were verified fixed;
  without a note, the next auditor re-reports 25 resolved items as live gaps.
- **TR-25.6** Fix the `packaging` import in the development interpreter to
  recover the 7 skipped `lowess` tests.
- **TR-25.7** Correct the overstated comment at `test_scheme_coercion.py:371`
  ("all fourteen"; the parametrization lists four) and the mislabelled cases
  at `test_tokenizer.cscript:102-122` (they name `_dash_first_comma_pos`,
  which does not exist).

### Acceptance criteria

- **AC-25.1** CI runs both suites on every push and fails on any failure or
  unexpected skip.
- **AC-25.2** CI runs pytest under both interpreters.
- **AC-25.3** No unreferenced test asset remains, and no fixture docstring is
  false.

### Test plan

Self-verifying: CI's first green run on a branch with a deliberately broken
test must be red.

### Acceptance, measured (24sep2026)

- **AC-25.1**, local as the maintainer chose.  `make check` on the finished
  tree: pytest under Stata's Python 15690 passed, 13 xfailed, 0 skipped;
  under the development interpreter 15690 passed, 13 xfailed, 0 skipped;
  the certification suite 61 of 63 -- the two red scripts,
  `test_setup_honesty` (HON-21, HON-22) and `test_program_coverage`
  (PC-18), pinned the pandas minimum this package raised to 2.0; corrected,
  they pass, 28 and 31 cases.  The self-verification: on a trimmed copy
  with the same Makefile, scripts and conftest.py, `make test` and `make
  test-dev` went red (exit 2) on a failing test and on a skipped one, and
  `make cert` on a failing and on a skipping script, green otherwise.
  `make hooks` is left to the maintainer: it changes the clone's git
  configuration.
- **AC-25.2** Both pytest targets run the whole suite, strict, and the
  first run under Stata's Python is what found the defects recorded above.
- **AC-25.3** `test/test_fixtures_are_committed.py` fails any fixture no
  test names and any `.do` file nothing runs; no fixture docstring is
  false.
- TR-25.6 was resolved before this package (`packaging` under both
  interpreters); TR-25.7's comment is at `test_scheme_coercion.py:449` now.

---

## WP-26 · Dead code removal — DONE

**Gaps closed:** N, N1, M3 · **Severity:** S3 · **Effort:** S · **Depends on:** WP-09, WP-10

> **Changed by WP-24** (24sep2026).  `_json_escape` is no longer dead:
> `_dash_formats_json` escapes each display format with it, and
> `_dash_require_mata` checks for it, so TR-26.3 must leave it (its
> `_html_escape` half still has no caller).  `_dash_graph_opts_to_json` is
> broken as well as dead -- it reads its own empty `g_*` locals and returns
> `{}` whatever its caller holds.  `test/function_test_map.py` lists the
> renderer functions nothing reaches (`DEAD`, 10) and those only tests
> reach (`TEST_ONLY`, 13); its guard fails when one becomes reachable, and
> each is this package's to delete or keep.  TR-26.4's `map_pci` is reached
> only by tests too, although the static call graph counts the `"pci"`
> entry of the dispatch table and the list leaves it out.

> **User story.** As the next person to audit this codebase, I want what I
> read to be what runs.

### Business requirements

- **BR-26.1** Every definition in the codebase has a caller or a test.
- **BR-26.2** No comment or header describes code that is not there.

### Technical requirements

- **TR-26.1** Delete `_dash_graph_opts_to_json` (`dash.ado:891-913`) — zero
  callers, and a **trap**: graph JSON is assembled inline at `:1462-1480` over
  a larger key set, so an auditor reading the dead helper would report ~26
  false inert options.
- **TR-26.2** Delete `_dash_kv_json` (`dash.ado:242-251`) — zero callers.
- **TR-26.3** Delete `_json_escape`, `_html_escape`, `_dash_json_esc`,
  `_dash_html_esc` (`dash_parse.mata:53, 71, 82, 85`) — the last two have zero
  callers anywhere, making the first two transitively dead. `dash.ado` escapes
  in `_dash_json_str` instead.
- **TR-26.4** Delete `map_pci` (`dash_render.py:5516`) — unreachable; the live
  path is `map_pci_literal` (`:5548`). Remove it from `pc_dispatch` (`:10454`).
  **Do this before WP-10's delegation**, so the wrong target cannot be wired.
- **TR-26.5** Remove the unreachable `"sc"`, `"li"`, `"hist"` dispatch aliases
  (`:10362, 10365, 10379`) — `_expand_plottype_str` always writes the full
  name — or keep them deliberately and say so.
- **TR-26.6** Remove the unreachable ambiguity branch in
  `_expand_plottype_str` (`dash_parse.mata:225`). Brute-forcing every prefix
  of all 38 names gives a maximum hit count of 1: the
  `strlen(name) >= strlen(minab)` gate at `:218` structurally suppresses the
  longer candidate in every colliding pair. Either remove it, or fix the gate
  so genuine ambiguity is detectable.
- **TR-26.7** Decide on the unused scheme-parser branches (`color plineplot`,
  `linepattern p1`–`p15`, bare `graphsize`) and `#include` support
  (`:1786-1800`) — no shipped scheme uses `#include`, though 25 of Stata's 26
  do, so this one is worth **keeping** for WP-17's custom schemes.
- **TR-26.8 (N1).** Fix the stale headers. `dash_parse.mata` lists
  `_dash_json_esc`/`_dash_html_esc` as "Public API (called from dash.ado)" at
  lines 34-35 — both dead; claims at line 8 that Mata does option-key
  abbreviation expansion — removed at `:239-268`; and omits four functions
  that *are* called. `dash.ado:14-16` repeats the same stale claim.
- **TR-26.9 (M3).** Move `regen_*.py` and the eight generated `*.html` files
  (~13 MB) out of the package root into `examples/` or `scripts/`, or
  gitignore them. They do not ship but they dominate the repository.

### Acceptance criteria

- **AC-26.1** Every function in `dash.ado` and `dash_parse.mata` has a caller
  or a test.
- **AC-26.2** No file header describes code that is not there.
- **AC-26.3** The full suite passes after removal.

### Test plan

Add a static test asserting zero orphaned `program define` / Mata function
definitions, so this cannot re-accumulate.

### Done, measured (24sep2026)

- **TR-26.1, TR-26.2** `_dash_graph_opts_to_json` and `_dash_kv_json`
  deleted: named only at their own definitions in every source.  PC-29,
  which tested nothing but `_dash_kv_json`, went with it.
- **TR-26.3** `_dash_json_esc`, `_dash_html_esc` and `_html_escape`
  deleted, `_json_escape` kept (WP-24's note); PC-27 went, PC-28 now tests
  `_json_escape` itself.  Beyond the list, `_dash_imm_gettoken` (a test
  wrapper since c036fb6) and `_dash_pc_immediate` (pcarrowi's entry until
  c036fb6) had no production caller; deleted, their tests pointed at
  `_dash_imm_next` and `_dash_immediate`, the paths production runs.
- **TR-26.4, TR-26.5** `map_pci` and the `"sc"`, `"li"`, `"hist"` aliases
  deleted in both modes; a hand-written spec naming an alias now draws
  nothing with the same note in both (`TestAnAliasIsNotAPlotType`).
- **TR-26.6** Removed.  Measured in Stata: of the 186 distinct prefixes of
  the table's 40 rows none reaches two, and twoway has no notion of an
  ambiguous plot type (209 prefixes of 45 names: 127 refused as "not a
  twoway plot type", 82 resolved to one).  P1A-76 and
  `TestNoPlotTypePrefixReachesTwoRows` fail if a prefix ever reaches two.
- **TR-26.7** All four kept and each tested through a custom scheme file
  against Stata's drawing; `color plineplot` and `linepattern p#` agree,
  and a bare `graphsize` and `#include` show four defects, pinned as strict
  xfails (BUGS.md).
- **TR-26.8** dash_parse.mata's header lists exactly the 27 functions
  dash.ado calls -- it omitted eight, not four, and named two it does not
  call -- and neither header claims the option-key expansion; three caller
  notes and a duplicated section number are corrected, and dash.ado's two
  identity copies of the option text (`opts_exp`, `gopts_exp`) are gone.
- **TR-26.9** The `regen_*.py` scripts are in `scripts/`; the generated
  pages were never tracked (`.gitignore`'s `*.html`).
- The renderer's DEAD list is deleted and TEST_ONLY holds four test seams
  kept on purpose: `_build_figures`, `_setup_sources` and
  `_dash_plot_type_names` with its probe.  The wrappers only tests called
  are deleted and their tests call the production functions; two tests
  whose expected values were never Stata's (a non-positive `x`, a constant
  `x` under fpfit) were measured and corrected.
- **Test plan** `test/test_no_orphans.py` (every program and Mata function
  has a caller and is reachable from `dash` or `dash_setup`),
  `test/test_file_headers.py`, and test_function_test_map.py's new checks
  (whatever nothing runs is listed as kept, and nothing is listed dead).

---

# Milestone 5 — Shippable

## WP-27 · Release closeout — DONE

**Gaps closed:** M2, B4 (verification) · **Severity:** S3 · **Effort:** S · **Depends on:** all

> **User story.** As the maintainer, I want one command sequence that proves
> the package is ready, and a merge command I can run myself.

### Business requirements

- **BR-27.1** The release gate is executed end to end from an installed
  package, not from the repository working tree.
- **BR-27.2** No S1 or S2 finding remains open at release.
- **BR-27.3** The merge is reported, never performed (CLAUDE.md rule 6).

### Technical requirements

- **TR-27.1** Run the full gate: `net install` into a clean PLUS, then run
  **every** file in `examples/` and assert rc 0 with no fallback warning and
  no ignored-option note the example did not intend.
- **TR-27.2** Re-verify responsive layout at 375 / 768 / 1440 px.
- **TR-27.3** Run the adversarial suite (CLAUDE.md rule 18): three cases per
  API endpoint and input surface, targeting auth bypass, injection and
  resource exhaustion.
- **TR-27.4** Reconcile `BUGS.md` so every defect this roadmap fixes is
  recorded with its regression test.
- **TR-27.5** Verify `dash.pkg` carries `v 2` and a current
  `Distribution-Date:`, and that `adoupdate` sees it.
- **TR-27.6** (M2) Resolve the branch state: 62 commits ahead of `main` with
  53 uncommitted working-tree entries. Commit or discard the `.ultraplan`
  reorganisation, then **report the merge command — do not run it**
  (CLAUDE.md rule 6).

### Acceptance criteria — release gate

- **AC-27.1** Both suites fully green, zero unexplained skips, under both
  interpreters.
- **AC-27.2** `net install` + every example: rc 0, correct schemes.
- **AC-27.3** Every `GAPS.md` finding is closed or explicitly deferred with a
  recorded rationale.
- **AC-27.4** No S1 or S2 finding remains open.
- **AC-27.5** Working tree clean; merge command reported to the user.

### Test plan

This package *is* the test plan: AC-27.1 … AC-27.5 are the release gate, run
against an installed package rather than the working tree. Record the run —
commands, output and the resolved state of every `GAPS.md` finding — in
`BUGS.md` and the CHANGELOG so the gate is auditable after the fact.

### Done, measured (24sep2026)

- **BR-27.2 / AC-27.4.** At the start, 36 BUGS.md entries were open, and
  graded on GAPS.md's scale 20 were S1 or S2.  The maintainer chose to fix
  them all here, and to have Stata evaluate qualifiers rather than mend the
  renderer's translation of them.  All 20 are fixed, test first, and the
  work found eight more, fixed as well: the jsonio export that stopped on
  a quote-holding string (dash now writes its data from Stata's own Python
  and needs no jsonio), a byte cap for the strL values that export then
  carries, pcarrow heads, linked selection on a scatter with a missing
  value, with and without jitter(), a served re-jitter, each layer's own
  tooltip, and the phone-width overflow TR-27.2 found.  Every open entry
  now carries "Graded S<n> (WP-27): <why>", and
  test/test_tracking_documents.py::TestNoOpenEntryBlocksARelease fails on
  an open S1 or S2: 19 remained open, all S3, at WP-27's closeout (3 at 6370ca4; see BUGS.md).
- **AC-27.1.** `make check`: pytest under Stata's Python and under the
  development interpreter, both strict, 16,693 passed, 11 xfailed and the
  same 5 failed in each -- three stale expectations (a layer that now
  draws its own rows with no view, the help's entry count after the
  $dash_max_bytes row, the single-y page's hash after the reflow's
  column track, each diffed before its test was changed) -- which pass
  under both after the fix; no skip.  The certification suite: 64 of 64
  scripts passed.
- **TR-27.1 / AC-27.2, BR-27.1.** `make gate` (scripts/run_release_gate.sh,
  scripts/release_gate.do, judged by scripts/release_verdict.py, whose
  verdict test/test_release_verdict.py holds to failing on each way a
  release can be wrong) net installs exactly what dash.pkg ships into a
  scratch PLUS, narrows the ado-path to BASE;SITE;PLUS, confirms dash.ado,
  dash_setup.ado, dash_parse.mata, the renderer and the locator's renderer
  are the installed copies, and runs every example and one page per
  shipped scheme from it.  Its first runs found two defects of its own
  script (a `/*' in a comment swallowed the file; a wrapped log line cut
  its paths) and three examples asking for a symbol Stata does not have,
  `ms(inverted_triangle)' -- twoway notes "named style inverted_triangle
  not found in class symbol" and draws the default, as dash did; they now
  ask for `V'.  Final run: 12 of 12 examples and 20 of 20 scheme pages rc 0
  with no fallback, ignored-option note or Python or Bokeh diagnostic.
- **TR-27.2.** Measured in headless Chrome through an iframe of exact
  width: at 375 px geometry_responsive (545 px wide) and full_dashboard
  (440) overflowed; now every page fits at 375, 768 and 1440 px, and
  test/test_responsive_layout.py measures 11 saved and 6 served layout
  families the same way.
- **AC-27.3.** Of GAPS.md's findings 70 are closed and 4 are no gap; two
  are closed in part and the rest deferred with the reason recorded -- E1's
  38 twoway options dash documents as unsupported and names when given,
  and J6's rollback of a failed pip install.
- **TR-27.3.** Every surface of test/test_adversarial_matrix.py has its
  three categories; WP-27's new surfaces are registered, and a new one,
  `qualifier_columns', is required.
- **TR-27.4.** Every closed entry names a test that exists
  (TestEveryClosedEntryNamesATestThatExists).
- **TR-27.5.** dash.pkg carries `v 3' -- the manifest format usersite.sthlp
  specifies, not the `v 2' this plan named (PKG-04) -- and Distribution-Date
  20260924, the version lines 2.0 24sep2026.  The gate's adoupdate reported
  nothing to update against the installed source and reported dash against
  a copy one day newer.
- **TR-27.6 / AC-27.5.** The maintainer chose to leave their planning
  files -- the .ultraplan reorganisation and its archive, phases/,
  REMAINING.md and CLAUDE.md -- uncommitted, so the working tree is clean
  of this package's work but not of theirs.  The merge is reported, not run.

---

## WP-28 · Close the GAPS2 audit's 22 gaps — DONE

**GAPS2 closed:** B1, B2, B3, B5, B6, B7, C2, D1, E1, E2, E3, E14, F1, G1, G2, G3, G5, G6, G16, K2, X1, X2 · **Severity:** S1 (14), S2 (5), S3 (3) · **Effort:** L · **Depends on:** WP-27

> **User story.** As the Stata user pasting twoway syntax, I want the
> numbers, text and colours twoway draws, and twoway's refusals; as the
> maintainer, I want each of the 22 audited defects closed by a regression
> test that failed before its fix.

### Business requirements

- **BR-28.1** Every number, date and float a KPI card, dropdown, slider,
  tooltip, date axis, marker label or CSV shows is written in the
  variable's Stata display format or the card's `fmt()`, in both
  renderers (E1, E3, G6).
- **BR-28.2** `xlabel`/`ylabel`/`xtick`/`ytick` read numlists and
  quoted-value pairs as Stata's own axis-label grammar does, and
  label/tick values widen the axis unless `norescale`; `range()` only
  widens (B1, B2). Value labels reach the axis and `hover()` (G16).
- **BR-28.3** Every textbox sub-option abbreviation Stata accepts is
  honoured or named, never drawn as literal text; `xtitle("")`/
  `ytitle("")` remove the title; `ytitle2()`/`xtitle2()` follow textbox
  grammar (B3, B6, B7).
- **BR-28.4** `legend`'s `order()` text, `label()`-after-`order()` and
  `lastlabel()` apply to the key Stata's own plot numbering names (B5).
- **BR-28.5** A histogram counts every observation Stata counts, with
  Stata's floor-and-clamp rule, in both the Python mapper and the saved
  page's JavaScript recount (C2).
- **BR-28.6** A scheme file's quoted RGB and %opacity values are read the
  way Stata's own scheme reader reads them (D1).
- **BR-28.7** `colorvar()` under `colordiscrete` with `colorcuts()` treats
  the listed values as levels, drops cuts below the column minimum, and
  honours `colorlevels()`, `colorvarminmax`, `zlabel()`, `ztitle()` and
  `zscale()` (X2).
- **BR-28.8** Every graph and card is masked by exactly the filters whose
  `exclude()` does not name it, on every move, in both modes; dropdown
  values compare as numbers for numeric columns and as exact text for
  string columns (E2, X1).
- **BR-28.9** The saved and served pages present one dashboard: the same
  viewport tag, dimming, range-selection wiring and responsive
  breakpoints; the saved `layout(bs)` filter bar sits below the header as
  the served app's already does (E14).
- **BR-28.10** `dash serve` returns a non-zero exit code and a message
  naming the reason when no server starts, and refuses a `--port` outside
  1024-65535 instead of clamping it; the declared Python/Bokeh/pandas/
  numpy floor is the version the suites actually run under (F1, K2).
- **BR-28.11** An internal column name can never silently overwrite a
  user variable; string variables are refused as plot variables with
  twoway's r(109); Unicode variable names work in `filter()`, `dash kpi`,
  `by()`, `hover()` and `colorvar()`; the saved page's data-limit count
  matches what it actually embeds (G1, G2, G3, G5).
- **BR-28.12** An option dash newly honours prints nothing extra, exactly
  as twoway prints nothing; only an option dash still cannot draw is
  named in the note (DISCOVERY Q22).
- **BR-28.13** Every refusal this package adds uses twoway's own return
  code (r(109), r(110), r(198)) and, where twoway has one, twoway's
  wording.

### Technical requirements

- **TR-28.1** One display-format module reached by all 14 number-to-text
  sites, with a JavaScript twin the node runner tests against it; the
  writer takes the full Stata format string and the variable's storage
  type (RESEARCH.md "Key architecture decisions" 1).
- **TR-28.2** Axis extents are computed in Python after the layers are
  drawn, as the hull of drawn data, label/tick positions and `range()`
  values, into a `Range1d` a fixture can pin in both modes (decision 2).
- **TR-28.3** Legend keys are built by Stata's own plot number, with text
  resolved default -> `label(#)` -> `order()` text -> `lastlabel()`; a
  `-` row is a label-only `LegendItem` (decision 3).
- **TR-28.4** Per-target filter masks are computed once per distinct
  exclusion set, in JavaScript and pandas from one shared rule; `Select`
  widgets carry numeric values for numeric columns (decision 4).
- **TR-28.5** Truth comes from Stata once, through a shared SVG/`.Graph`
  certification helper and per-family `scripts/extract_*_truth.do`
  scripts; every new or regenerated fixture carries the `_meta`
  provenance stamp (decision 5, D12).
- **TR-28.6** The declared floor is the measured `stata` pytest baseline
  (Python 3.13, Bokeh 3.8, pandas 2.3, numpy 2.3), not a modelled one
  (decision 5; K2).
- **TR-28.7** The served app's copy lists (`dash_render.py` constants
  24326-24428, functions 24466-24687) carry every new module-level name
  the served template reads; `test/function_test_map.py` and
  `test/program_coverage_map.py` name every new function and Stata
  program.
- **TR-28.8** Every gap's regression test fails against the unmodified
  tree at `91d97be`, is recorded in that gap's fix commit, and turns
  green in the same commit as its fix; no test-only commit exists (D1).
- **TR-28.9** Every gap's BUGS.md entry lands closed, in its fix commit,
  in the form this file's section 01 records (TR-01.8); every CHANGELOG
  line replaces the marker section 01 placed (TR-01.7); every closing
  task updates the dash.sthlp paragraph GAPS2 cites for its gap.
- **TR-28.10** `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree`
  (added by S01) is the mechanical reader that resolves this package's
  `**GAPS2 closed:**` field against GAPS2.md's headings, and, once this
  package is headed DONE, against each id's Tracked line, a closed
  BUGS.md entry and a commit that exists.
- **TR-28.11** Stata is invoked only through
  `scripts/stata_slot.sh <scratch-dir> <file>.do` (never the GUI, never a
  bare `stata-mp -b do`), holding concurrent Stata sessions at three
  across every parallel section.

### Acceptance criteria

- **AC-28.1** Each of the 22 gaps has a regression test that failed at
  `91d97be` and passes after its fix, asserted in both the saved and
  served modes wherever the gap has a page.
- **AC-28.2** The Stata-measured fixtures RESEARCH.md and the section
  files name are on disk, `git add -f`'d, and carry the `_meta`
  provenance stamp.
- **AC-28.3** The full pytest suite (`python3 -m pytest test/ -q`) is
  green under both interpreters with no skips.
- **AC-28.4** The certification suite (the 65 scripts of the audit commit
  plus `test/test_gaps2_truth.cscript`) passes with no skips, and grows
  by at most about five minutes of wall time over the step-0b baseline.
- **AC-28.5** BUGS.md has no open S1 or S2 entry; 22 entries are closed,
  each naming a test that exists.
- **AC-28.6** Every GAPS2.md entry in scope carries a Tracked line naming
  WP-28, a closed BUGS.md title and a commit that exists;
  `test_tracking_documents.py::TestGaps2AndRoadmapAgree` passes both
  directions.
- **AC-28.7** CHANGELOG.md holds no `<!-- WP-28 ` marker; every changed
  number, text or picture is listed under its line ending
  `(WP-28, <ID>)`.
- **AC-28.8** The WP-27 release gate passes from an installed package
  with every example at return code 0.

### Test plan

| What | How |
|---|---|
| Each gap's own regression test, both modes where the gap has a page | pytest, per section |
| Twoway's own drawn truth (SVG text/fill, `.Graph` extents, `display` text) | the shared SVG/`.Graph` cert helper and `scripts/extract_*_truth.do`, per section |
| The saved page's JavaScript twins | the stateful node runner (`test/js_runner.py`), per section |
| twoway/Stata comparisons that are new certification work | `test/test_gaps2_truth.cscript`, one block per section |
| Refusals, messages, return codes, setup checks | the existing cscript for each area |
| This package's own closure | `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree` |
| No tracking-document regression | `python3 -m pytest test/ -q` before every commit |
| The per-gap plan | the section file that closes it (`.ultraplan/sections/section-NN-*.md`) |

#### GAPS2 traceability

| Gap | Title | Sev | Effort | Closable | Section |
|---|---|---|---|---|---|
| B1 | Axis-label rules misread quoted numeric text, multi-line labels and numlist forms | S1 | M | yes | S14 |
| B2 | Label/tick values do not widen the axis; xscale/yscale(range()) narrows or inverts it | S1 | M | yes | S18 |
| B3 | Textbox sub-option abbreviations are drawn as part of the title/axis-title text | S1 | S | yes | S13 |
| B5 | legend order() text and label()-after-order() are applied to the wrong keys | S1 | M | yes | S15 |
| B6 | xtitle("")/ytitle("") do not remove the axis title | S1 | S | yes | S13 |
| B7 | ytitle2()/xtitle2() draw their quote marks and ignore textbox grammar | S1 | S | yes | S13 |
| C2 | histogram silently drops the maximum observation when the last bin edge falls short | S1 | S | yes | S05 |
| D1 | A user or third-party scheme's quoted values are dropped without a warning | S1 | S | yes | S06 |
| E1 | KPI fmt() accepts formats the card then does not apply, and %w.0g over-rounds | S1 | M | yes | S04+S11 |
| E2 | exclude() leaves excluded graphs and cards showing a stale filter state | S1 | M | yes | S17 |
| E3 | Dates and formatted numbers ignore the variable's Stata display format | S2 | L | yes | S04+S11+S12 |
| E14 | The saved page and the served app still present the dashboard differently | S3 | M | yes | S10 |
| F1 | dash serve returns rc 0 when no server ran; --port is clamped, not refused | S1 | S | yes | S09 |
| G1 | Internal column names can overwrite a user variable | S1 | M | yes | S07 |
| G2 | String variables are accepted as plot variables; twoway refuses them | S2 | S | yes | S08 |
| G3 | The data limit counts exported values, refusing pages that would be small | S2 | M | partly | S08 |
| G5 | Unicode variable names are refused by filter() and dash kpi | S2 | S | yes | S07 |
| G6 | %g formats and float storage are not reproduced | S3 | M | yes | S04+S12 |
| G16 | Value labels are never drawn on axes or in tooltips | S3 | S | yes | S14 |
| K2 | The declared Python/Bokeh minimums are false | S2 | S | yes | S09 |
| X1 | Dropdown filters rewrite numeric-looking string codes and drop categories | S1 | S | yes | S17 |
| X2 | colorvar() explicit forms (colorcuts, colorlevels, z-axis) are not drawn | S1 | M | partly | S16 |

### Done, measured (30sep2026)

- **BR-28 / GAPS2.** The 22 gaps in scope are closed, each test first,
  each by a commit whose subject names it and a closed BUGS.md entry
  whose Resolution reads (WP-28, <ID>); GAPS2.md's Tracked line of each
  names that entry and commit.  C4 and its duplicate E4 are deferred by
  decision (DISCOVERY Q3).  Residuals deferred, as BUGS.md records them
  and the maintainer approved: B1, B2, B5, D1, E1, E14, G1, G3, G16, K2
  and X2.
- **Fixtures.** test/fixtures gained or regrew ten files, the Stata-
  measured truth of text_truth.json and value_truth.json among them.
- **Tests flipped.** 99 pinned expectations were flipped, each named
  with its reason in its fix commit's Flipped: line.
- **Runs (30sep2026, on the dated tree).** make test, under Stata's
  Python (/opt/anaconda3/bin/python3, 3.13): 20,771 passed, 3 xfailed,
  0 skipped.  make test-dev (python3, 3.14): 20,771 passed, 3 xfailed,
  0 skipped.  Their first runs found nine stale pins the batch-3 merge
  left in files no section owned and a node guard that skipped under
  xdist; each was fixed under its gap's id.  make cert: 66 of 66
  scripts, 0 skipped, after six scripts were fixed under B3, X1, X2,
  E3 and G6 (stale needles, and a colour count that read only the
  first 32,768 bytes of a line); wall time 575 s before WP-28 and
  699 s after, a growth of about 2.1 minutes, within the five-minute
  budget.  make gate: 12 of 12 examples and 20 of 20 scheme pages
  clean from a net-installed copy.  No S1 or S2 entry is open, and the
  22 closed WP-28 entries name tests that exist
  (TestEveryClosedEntryNamesATestThatExists).
- **Demo pages.** scatter (1.3 MB), dashboard (1.8), full_dashboard
  (2.0), kelly22ex_dashboard (1.8), comprehensive_demo (2.4),
  bs_equal_cols (1.7), bs_kpi_hero (1.7), bs_stacked (1.7) and
  bs_responsive (1.7); regenerated and left untracked (.gitignore
  holds *.html).
- **AGENTS.md** carries "Invariants introduced by WP-28", each with its
  guarding test.
- **Merge.** `git checkout main && git merge s3-bugs` -- reported, not run.

---

## WP-29 · Close the drop-in P0 gaps — DONE

**GAPS2 closed:** A1, A6, A9, B4, C7, F2, F4, H7, I2, I3, X3 · **Severity:** S1 (19), S2 (2) · **Effort:** XL · **Depends on:** WP-28

> **User story.** As the Stata user pasting twoway syntax, I want dash to
> draw what twoway draws -- joins, scales, titles, axes, functions,
> smooths, bands and dates -- with nothing I named dropped; as the
> dashboard publisher, I want the page and the served app to carry only
> the rows a reader may see, to admit only me, and to stop with my Stata
> session; as the installer, I want dash_setup to work on an externally
> managed Python; as the maintainer, I want each of the 20 P0 items of the
> drop-in re-audit (`.ultraplan/handoff/DROPIN-REMAINING.md` section 3, P0,
> verified at 357c368) closed by a regression test that failed before its
> fix.

### Business requirements

- **BR-29.1** Join order: data order by default, x order under `sort`,
  varlist order under `sort(varlist)` (the rightmost copy wins), time
  order for the ts types, ties stable; in both modes and after a move; an
  invalid `sort()` name is refused with twoway's message and r(198) (P0.1).
- **BR-29.2** by() axes: one shared scale per axis by default (x, y, y2,
  x2, the Total panel included), the union of the drawn data after any
  move; the rescale forms and their abbreviations give per-panel scales; a
  `range()` twoway ignores on a rescaled axis is named once, at build
  time, in both modes (P0.2).
- **BR-29.3** Text: a variable's label when it is non-empty, else its
  name; a title sub-option with no text keeps the default text; a typed
  `""` empties the title; wherever a title, key or tooltip names a
  variable (P0.3, P0.4).
- **BR-29.4** axis(#): every routed option draws on the axis it names; an
  axis number no layer uses is refused with twoway's rc and message;
  axis-number parsing follows twoway's integer bounds; nothing is dropped
  unnamed (P0.5).
- **BR-29.5** function: the points are Stata's own
  (`twoway__function_gen`), written to round-trip exactly (`%24.17g`); an
  expression Stata refuses is refused with Stata's rc, before graph-level
  options are checked; the RNG state matches twoway's (P0.6).
- **BR-29.6** lpoly: the default bandwidth equals Stata's `r(bwidth)`
  within 1e-7 relative on exact rows (degree 0/1, x centred within three
  half-ranges of 0) and within 5e-5 relative on noisy rows (degree 2/3,
  or an offset x such as years, dates or `weight+20000`), where Stata's
  own float64 arithmetic varies; a missing or zero `r(bwidth)` draws y=0
  on every grid point, as twoway does; the lpolyci band at a given
  `bwidth()` and `pwidth()` or `var()` equals Stata's `lpoly, ci` band
  within 1e-8 times max(1,|y|), and at the default bandwidths within the
  bandwidth's tier; for every kernel, degrees 0-3 (the only degrees dash
  draws; the degree 4-7 constants are unit-tested, not drawn),
  `pwidth()`, `var()`, weights and the small-x scales where Stata drops
  pivots, in served recomputes too, with the option checks in twoway's
  order; the divergences D1-D9 that section 11 measures are documented
  and pinned (P0.7, P0.9).
- **BR-29.7** Dates: computed layers and KPI statistics run in Stata units
  and draw on the date axis; out-of-range bins or points are dropped and
  named in one note, alike in both modes; no non-finite number reaches page
  JSON; when every layer is computed and the first is lfit, qfit, lfitci,
  qfitci, kdensity, lpoly or lpolyci over a date, dash keeps its date axis
  where twoway labels numbers, a documented divergence (P0.8, P0.20).
- **BR-29.8** hover(): every named variable is exported, and counted
  against the data limits, when some layer can show it; a name that is not
  a variable is refused before any Stata command text is built (P0.10).
- **BR-29.9** Embedding: the saved page holds a cell only when a layer, a
  recomputed KPI card, a filter or the csv export reads that variable on
  that observation; Stata-computed results still use the whole data; both
  modes number the rows they send 0..m-1 in data order (the saved page's
  row ids and the served sources' `index`), so no row number reveals an
  excluded observation; the help discloses the rule (P0.11).
- **BR-29.10** Served access: without the per-launch token no session,
  page, autoload, metadata or row reaches a client, under `dash serve`,
  `python app.py` and `bokeh serve app.py`; the app never runs without a
  token: started with none, it makes its own, writes its link to a 0600
  file and prints only that file's path; the key is never printed, except
  when no link file can be written in any folder dash tries: then one
  warning line and the link alone are printed once, to the output of
  whoever started the server, which keeps serving; `/health` and BokehJS
  static files stay open; tokens are compared in constant time (P0.12a).
- **BR-29.11** Private files: every temporary copy of the data lives in a
  per-user directory dash makes 0700, and every file is created 0600; a
  location that cannot be kept private (a `c(tmpdir)` other accounts can
  change, a disk that keeps no permissions, a `dash-<uid>` that is not the
  user's own folder) is never refused: dash proceeds, leaves a planted
  `dash-<uid>` alone for a 0700 fallback, and prints one note naming the
  location; as an anti-hijack guard, not for privacy, no write goes
  through a symbolic link, into a FIFO or device, or over a hard-linked or
  another account's file, and no replaced app file is started, each ending
  r(7102); dash starts its served app only from the bytes it wrote, read
  through a descriptor it opened and verified, never by path, so an app
  file swapped in after that check never runs; one-line preview pages are
  private and bounded (unique names, 0600 in a 0700 folder; a session
  keeps its newest five; `dash clear` removes the session's pages except
  one a browser was asked to open in the last 60 s; another session's
  pages are removed only once that session is dead or the page is more
  than 24 h old; all sessions together keep at most 25); a server app the
  user names is written 0600 into the folder the user names, which is
  never refused or re-moded, and pages the user names keep twoway's umask
  semantics (P0.12b, P0.14).
- **BR-29.12** Lifecycle: the served app stops within the grace period
  after its parent Stata dies; no data file stays on disk while it serves;
  Break stops `dash serve` from every front end and ends it with r(1); the
  messages name Break, not Ctrl+C, in the GUI (P0.13).
- **BR-29.13** Saved filters: a linked or by() layer's view stays inside
  its panel or graph qualifier after any move; a colorvar's domain, levels
  and bins come from the layer's drawn rows, in both modes, for numeric,
  string and date colorvars (P0.15, P0.16).
- **BR-29.14** Stale and redraw: after a move that removed a row of a
  frozen layer's estimation sample the layer shows a visible cue, cleared
  when the move is undone; the served app recomputes bar and rbar widths
  and an emptied layer's style as the saved build does (P0.17, P0.18). [WP-30 P1.17a, commit 624837e: spacing machinery removed: a bar is one x unit or barwidth(), never derived from the rows a filter keeps]
- **BR-29.15** Setup: on a PEP 668 Python `dash_setup` starts no pip
  process, names the reason and the `venv()` route, never suggests
  `--break-system-packages` and ends r(198); `venv(path)` creates,
  installs into and verifies a private environment and prints how to link
  Stata to it; printed commands run as printed in cmd.exe and POSIX
  shells (P0.19).
- **BR-29.16** Every P0 BUGS.md entry is closed with a Resolution naming
  tests that exist, every CHANGELOG marker is replaced, and the GAPS2 ids
  this package lists are closed with commits that exist.

### Technical requirements

- **TR-29.1** The plan is `.ultraplan/wp29/`: `PLAN.md` (context, goals,
  risks, exit gates) and `index.md` (the 15 sections, the four batches and
  their merge order, merge rules R1-R8, the cscript driver and gates
  G0-G11); each section file carries its own TR-NN.k and test plan.
- **TR-29.2** Tracking (section 01): 21 BUGS.md entries opened in the
  WP-29 form, the `WP29_OPEN` allowance and `TestWp29Tracking` in
  `test/test_tracking_documents.py`, 26 CHANGELOG markers in five lists,
  and the one truth script `test/test_wp29_truth.cscript` (runner block
  68, gated by `WP29_ONLY=S<NN>`).
- **TR-29.3** One commit per P0 entry (P0.13 two), subject ending
  `(WP-29 P0.<n>)`, each on a tree that was never red, its body opening
  with the failing tests' saved output.
- **TR-29.4** Both renderers every time: a helper the served app needs is
  added to the served copy lists and named in `test/function_test_map.py`;
  `test/test_mode_parity.py` gains each section's corpus cases and its
  `ALLOWED` set is unchanged.

### Acceptance criteria

- **AC-29.1** The 21 BUGS.md entries section 01 opened are closed; each
  Resolution holds `(WP-29, P0.<n>)` and names tests that exist;
  `WP29_OPEN` is empty.
- **AC-29.2** Each P0 entry's fix commit body opens with its saved failure
  text, with a `Regression:` line per regression test.
- **AC-29.3** `test/test_wp29_truth.cscript` runs every section block with
  every case PASS and no SKIP on a machine with Python; its fixtures carry
  the `_meta` stamp and are committed.
- **AC-29.4** `test/test_mode_parity.py` is green with every section's
  corpus cases, and `ALLOWED` is unchanged.
- **AC-29.5** Both served-name guards are green, the `__main__` block
  included.
- **AC-29.6** The security tests are green: no session, page or data
  without the token, and an app started without one makes its own and
  prints only its link file's path, or, when no link file can be written
  anywhere, prints the link once after a warning line and keeps serving;
  0600 files in a 0700 root wherever the disk keeps permissions; a
  location that is not private proceeds with one note, never an error; a
  link, FIFO or device, hard-linked or foreign file at a target, or a
  replaced app, refused r(7102); an app path swapped after the launch's
  check runs nothing but the verified bytes; every preview page 0600 in a
  0700 folder, at most five per session and 25 in all, removed by `dash
  clear` (except a page a browser was asked to open in the last 60 s) and
  once its session is dead; the app exits within the grace period after
  its parent dies; Break ends `dash serve` with r(1); no non-finite number
  in page JSON; no saved-page cell outside BR-29.9, and no served `index`
  value that is an original observation number.
- **AC-29.7** CHANGELOG.md holds no WP-29 marker; every WP-29 line ends
  `(WP-29, P0.<n>)`, and each Results line names the command, the old
  value and the new.
- **AC-29.8** WP-29 is headed DONE here; each id its `GAPS2 closed` field
  lists has a GAPS2.md Tracked line `Closed in WP-29, ...` naming a commit
  that exists; `test/test_tracking_documents.py` is green.
- **AC-29.9** `make test`, `make test-dev`, `make cert` and `make gate`
  are green once each on `wp29-p0`, and the cert wall time is reported
  against the baseline recorded before batch 1.
- **AC-29.10** No WP-29 commit message names an AI tool or vendor, and no
  WP-29 commit holds `CLAUDE.md` or `.gitignore`.
- **AC-29.11** Each commit's change detection showed only its section's
  symbols, and every HIGH or CRITICAL impact was reported before its edit.
- **AC-29.12** The merge into `main` is reported, not run, and the
  worktrees are removed.

### Test plan

`test/test_tracking_documents.py::TestWp29Tracking` checks the entries,
the allowance and the CHANGELOG markers at every commit; each section's
regression tests, truth block and parity corpus cases are listed in its
section file; the closeout runs the full suites, the certification suite
and the release gate once each.

#### P0 traceability

| P0 | Entry (BUGS.md) | Grade | Section | Commit |
|---|---|---|---|---|
| P0.1 | line types joined in x order; sort(varlist) ignored | S1 | 02 | b0d170d |
| P0.2 | by() panels independently scaled | S1 | 10 | ab53f25 |
| P0.3 | unlabelled variables: blank titles, type-named keys, blank tooltips | S1 | 03 | 8d3593e |
| P0.4 | a title sub-option with no text deletes the title | S1 | 03 | e908b78 |
| P0.5 | axis(2) on ylabel/yscale/yline/xtick applied to axis 1 | S1 | 10 | 3208b2b |
| P0.6 | function: ^ right-associative, pi and e accepted | S1 | 04 | 96aa267 |
| P0.7 | lpoly/lpolyci default bandwidth wrong | S1 | 11 | 758cf59 |
| P0.8 | computed layers on a date run in ms | S1 | 05 | cd210ea |
| P0.9 | lpolyci band a bootstrap, not Stata's | S1 | 11 | e32be3a |
| P0.10 | hover()-only variable never exported | S1 | 06 | 735c534 |
| P0.11 | saved page embeds rows if/in exclude | S1 | 14 | cbeef4e |
| P0.12a | served app has no credential | S1 | 13 | 7f5c8f5 |
| P0.12b | served app files readable by other accounts | S1 | 08 | fd51038 |
| P0.13 | served app outlives Stata; Break cannot stop serve | S1 | 08 | F2 ece0752, F4 c595259 |
| P0.14 | one-line preview pages never deleted, 0644 | S2 | 08 | fd51038 |
| P0.15 | saved filter registers per-plot rows, not the intersection | S1 | 07 | 3cff164 |
| P0.16 | colorvar range ignores qualifiers | S1 | 07 | 85dc7d2 |
| P0.17 | saved fits stale after a filter move, no cue | S1 | 12 | b242b99 |
| P0.18 | served redraw keeps build-time bar widths | S1 | 12 | 2d52fbe [WP-30 P1.17a, commit 624837e: spacing machinery removed] |
| P0.19 | dash_setup fails on PEP 668 Pythons | S2 | 09 | 4d74922 |
| P0.20 | KPI sd/var/iqr/cv/sum of a date in ms | S1 | 05 | 529875d |

### Done, measured (02oct2026)

- **P0 entries.** The 21 BUGS.md entries section 01 opened are closed,
  each test first, by a commit whose subject names it (P0.13 by two, F2
  then F4); each Resolution reads (WP-29, P0.<n>) and names tests that
  exist. WP29_OPEN is {} and test_no_wp29_entry_remains_open keeps it so.
  No CHANGELOG marker is left; the 39 WP-29 lines sit in the lists
  WP29_LISTS names (P0.8, P0.10, P0.19 and P0.20 keep several items each,
  accepted at the closeout on 02oct2026).
- **Per P0.** P0.1 (b0d170d): the six joining types join in the data's
  order unless sort or sort(varlist) is given; tsline and tsrline in time
  order. P0.2 (ab53f25): by() panels share one scale per axis and
  yrescale/xrescale are honoured; 100 panels settle 7.98 s after a move
  in headless Chrome (the plan's 3 s not met; the maintainer accepted a
  30 s bound, 1.5 times the per-panel control's 19.28 s, left for a later
  performance task). P0.3 (8d3593e): unlabelled variables are named by
  their names in titles, keys, tooltips and widgets. P0.4 (e908b78): a
  title option of sub-options only keeps the default title. P0.5
  (3208b2b): axis(#) options are drawn on the axis they name, and refused
  as twoway refuses them. P0.6 (96aa267): function layers are evaluated
  by Stata's own generator. P0.7 (758cf59): lpoly's default bandwidth is
  Stata's rule of thumb for every kernel and degree. P0.8 (cd210ea):
  computed layers of a date run in the variable's Stata units. P0.9
  (e32be3a): lpolyci draws Stata's analytic band with pwidth() and var();
  at N=20000 the band costs 0.066 s, where the bootstrap took 4.23 s.
  P0.10 (735c534): every variable hover() names is exported, saved and
  served. P0.11 (cbeef4e): a page embeds only the rows its graphs, cards
  and filters read (a range filter under if price > 4500 spans 4749-11385,
  was 3799; a brushed card 25.66667, was 23.4); served row numbers are the
  page's ranks (index 0-5, was 1, 3, 4, 6, 7, 9). P0.12a (7f5c8f5): the
  served app requires a per-launch key and makes its own when started
  without one. P0.12b (fd51038): dash's temporary copies are private.
  P0.13 (ece0752 F2, c595259 F4): the served app stops when Stata ends,
  keeps no copy of the data on disk while it serves, and Break ends dash
  serve with r(1). P0.14 (fd51038): previews are private and pruned to
  five per session. P0.15 (3cff164): a linked layer's own if holds inside
  its panel after a saved move. P0.16 (85dc7d2): the colour key is drawn
  from the rows each colorvar layer draws. P0.17 (b242b99): the saved page
  marks layers it does not recompute after a move. P0.18 (2d52fbe): the
  served redraw follows bar widths and keeps an emptied layer's style. [WP-30 P1.17a, commit 624837e: spacing machinery removed]
  P0.19 (4d74922): dash_setup works on externally managed Pythons and
  adds venv(). P0.20 (529875d): KPI statistics of a date are taken in its
  Stata units.
- **GAPS2.** Closed: A1, A6, A9, B4, C7, F2, F4, H7, I2, I3, X3. Partly
  closed, each Tracked line saying what is open: A4, A13, B12, B15, B16,
  B22, C12, F9 and C4. WP-28 residuals closed or narrowed: E1 (P0.20),
  G16 (P0.10), G3 (P0.10). C4: partly closed by the stale cue; the saved
  page does not re-estimate, by decision M3.
- **Residuals.** 19 deferred clauses, as BUGS.md records them and the
  maintainer approved; filed in DROPIN-REMAINING.md as P2.30-P2.41, with
  notes on P1.3, P1.4, P1.8, P1.9, P1.15-P1.18, P1.22, P1.23, P1.26,
  P1.30, P1.34, P2.2, P2.7, P2.14, P2.18, P2.21, P2.24, P2.28, P3.2 and
  P3.12. lpoly's tolerance rulings (a 1e-4 tier for four offset rows, the
  exact-fit threshold 1e-6 of var(y), the drawn-curve exclusion at
  x=4405.71) are recorded in section 11's commit.
- **Fixtures.** test/fixtures: 13 files changed, 74,657 insertions and 315
  deletions.
- **Tests flipped.** 160 Flipped: lines name each pinned expectation and
  its reason in its fix commit; every pytest node named collects under
  its current name.
- **Security (AC-29.6).** The per-launch key (TestTheServedAppRequiresItsToken,
  TestTheSessionGate, the self-made key included), the once-printed link
  (TestTheLauncherPassesTheToken), the private files and the location that
  is not private (TestTheDataFileIsPrivate), the anti-hijack refusals
  r(7102), the launch from the open file (TestTheLaunchFromTheOpenFile),
  the previews (PF-01 to PF-05), the parent watch
  (TestTheServerDiesWithItsLauncher), Break (LC-03) and the embedded rows
  (TestTheSavedPageHoldsOnlySelectedRows, TestTheServedIndexIsARank), all
  green in both runs below.
- **Runs (02oct2026).** make test, under Stata's Python
  (/opt/anaconda3/bin/python3, 3.13.9): 24,574 passed, 3 xfailed, 0
  skipped. make test-dev (python3, 3.14.5): 24,574 passed, 3 xfailed, 0
  skipped. make cert: 67 of 67 scripts, 0 skipped; wall time 1,178 s
  before WP-29 (step 0b, measured under load) and 907 s after, about 4.5
  minutes less; the 10 timed blocks of test_wp29_truth.cscript took 97 s,
  the slowest S02 (48 s) and S10 (18 s). make gate: 12 of 12 examples and
  20 of 20 scheme pages clean from a net-installed copy, venv-linked
  sessions clean. The closeout's runs found, and fixed under their P0
  ids, a cost bound Stata's Python could not meet (P0.1), a lost filter
  cap note on a saved build after a served one (P0.11), a note on every
  one-line saving() about function points the graph did not have (P0.6),
  three certification pins and one case P0.3, P0.11 and P0.14 had left
  stale or unisolated, and the gate reading the venv logs under the wrong
  name (P0.19). The last of those touched only the gate's runner and its
  test; the full suite on the final tree: 24,575 passed, 3 xfailed. No S1
  or S2 entry is open.
- **Not measured.** Windows, Linux and Stata before 19 (the package's
  non-goals): the commands dash_setup prints were tested in the sandbox
  for cmd.exe and POSIX shells only; GUI Break was verified through a
  patched pollstd only. Commits cd210ea (P0.8) and 529875d (P0.20) open
  with their failure text but carry no Regression: line in the formal
  form (recorded, history not rewritten). [WP-30 P1.35, commit 1f05b63: Stata before 19 is refused]
- **AGENTS.md** carries "Invariants introduced by WP-29", 20 paragraphs,
  each with its guarding test.
- **Merge.** `git checkout main && git merge --no-ff wp29-p0` -- reported,
  not run.

---

## WP-30 · Close the drop-in P1 gaps — DONE

**GAPS2 closed:** A3, A13, B12, B14, B16, B18, B20, B22, B23, B25, B31, D2, D3, D7, D8, D9, D10, D11, D12, D18, D19, F3, F5, G4, G10, H4, H6, I12, I14, K1, X4, X5 · **Severity:** S1 (9), S2 (38), S3 (9) · **Effort:** XL · **Depends on:** WP-29

As a Stata user who pastes a twoway command or do-file into dash, I want the common twoway options, the default look of every shipped scheme, twoway's errors and silences, and a served app and installation that hold under real use, so that a dashboard reads as the Stata graph it came from (US-30.1 to US-30.26, .ultraplan/wp30/PLAN.md section 5).

### Business requirements

Each requirement holds in **both modes** and **after any filter move** unless it says otherwise (BR-30.38). "Refused as twoway" means: with twoway's return code and message text as measured in StataNow 19.5, in twoway's order where the order was measured. "Noted" means one `(note: …)` line (BR-30.26).

- **BR-30.1** Stylelists and value lists (P1.1):
  - A style option given a list over an expanded varlist styles the k-th y with the k-th element. A lone value or a short list styles only the leading series; the rest keep their defaults, silently (twoway's padding).
  - The shorthands `.`, `=`, `..` and `...` resolve as twoway resolves them. A misplaced `..` is refused r(198) `<opt>(<value>):  invalid syntax`. A used quoted element of only blanks (`" "`) is refused r(198) `dash: <opt>() element <j> is blank; use . for the default (got: <value>)`; an unused one is not checked, and an empty `""` element is `.`, as in twoway.
  - A quoted or compound element is one element (`"hsv 240 1 1"`, `*.5`, `navy*.5%50`); an unquoted `255 0 0` is three elements. Single-y types take the first element. An unknown element draws twoway's default attributes, noted with the element named.
  - `malpha()`, `lalpha()`, `falpha()` and `jseed()` stay scalars applied to every series, as documented.
  - `mlabel(varlist)` is positional; `.` omits that series' labels; `..` is refused r(198) `.. not allowed in option mlabel()` and `=` r(101) `=exp not allowed`; every named variable must exist (r(111)).
  - `jitter()`, `base()`, `barwidth()` and `mlabposition()` are checked per element after the shorthands resolve, so `jitter(2 ..)` and `base(10 =)` draw. Elements past the number of y are ignored silently. rbar `barwidth()` lists and lowess `bwidth()` lists stay refused as twoway refuses them.
- **BR-30.2** Scheme chrome and intensity (P1.2), for each of the 26 shipped schemes:
  - the title is centred and not bold (economist: left); axis titles are upright; subtitle, note and caption are placed by the scheme's justification; economist's note sits in the title band;
  - no minor ticks unless asked; tick length, side, colour and width come from the scheme in Stata units; s2color's y labels are vertical (`ylabel(, angle(0))` is the escape); stcolor's grid is dashed; s1rcolor's ticks are visible; economist's axis sides, lines and ticks are the scheme's;
  - markers are opaque unless `%NN`, `sttrans` or `malpha()` asks otherwise (rconnected's markers included);
  - bar, area and histogram fills and the CI band blend the scheme's p#bar/p#area intensity opaquely, user colours included; `fintensity()` is an opaque blend; above 1 it darkens with twoway's measured clamp (navy at 6000 and above is #010304); it is never refused; negatives read as 0;
  - a user scheme's `intensity bar` and `intensity area` are not read, silently (twoway ignores both).
- **BR-30.3** Default ticks and padding (P1.3):
  - Default numeric, log and `%tc` axes, and y2/x2 axes without their own labels, take twoway's natscale choice with the scheme's tick count, and draw no minor ticks.
  - An axis range is the hull of every drawn layer, fits included, plus twoway's plot-region margin (r × min(W,H), r = 0.022; economist 0.006), placed within about 0.8% of the width of twoway's. Shared by() panels share one range over the union hull.
  - After every filter move, default and `#N` axes re-tick and re-range over the kept rows, y2/x2 included. An explicit-value axis re-hulls its data part and keeps its label positions (the help's "holds across filter moves" is rewritten). Zoom and pan re-tick by natscale over the visible range.
  - Budget: the served re-finish adds at most 0.2 s per figure per move at 500k rows; 100 saved by() panels settle within 1 s of WP-29's measured time.
  - `%td`, `%tw`, `%tm`, `%tq`, `%th` and `%ty` default axes take the fitted tsnatscale model. Its agreement with twoway is pinned at the measured floors (52-66% of `%td`-`%th` ranges, 98% of `%ty`) and stated in the help. The saved page and the served app give the same ticks on every one of the fixture's 12,000 answers.
- **BR-30.4** Scheme keys on every layer (P1.4):
  - `sttrans` opacity reaches fits, spikes, ranges, pc types and immediates; rarea follows area's rule (opaque; 0.2 under `sttrans`).
  - Histograms take the scheme's histogram colour, intensity, line colour and line width, and so does an empty histogram's key.
  - The scheme's hollow and `sm*` p# symbols are drawn hollow and at 0.707 size, and so is a user's `msymbol(sm*)`, after `msize()` (IR-4). The p# symbol cycle reaches scatteri, rscatter, pcscatter, dropline and rcapsym. Markers read p#markfill/p#markline, not p#mark. `msymbol(Oh)` with `malpha()` stays hollow.
  - The default marker-label size and colour come from the scheme's label keys in Stata text units, the same in both modes. The colour key's title, labels and ticks come from the scheme.
  - Every directive of a user, PLUS, third-party or shipped scheme is kept in the parsed scheme (none discarded), so later versions can draw it; a directive dash does not draw is not noted, in either mode.
- **BR-30.5** Axis formats (P1.5):
  - Default tick labels use the axis variable's display format (`weight` `%9.0fc` writes `2,000`), with twoway's `%g`/`%gc` fallback, on second axes, on range and pc first layers and in the text-label formatter. `xvarformat()`/`yvarformat()` are read.
  - Narrow `%g`, `%e` and `%f` fallbacks write what Stata writes (its own entry, P1.5.7).
  - `xlabel(, format(%td…))` is honoured. A numeric `format()` on a date axis writes the stored value.
  - `format(bogus)` is refused r(198) `invalid format, bogus`. A format twoway accepts but dash cannot write exactly (such as `%12s` on a numeric axis) draws `%9.0g`, noted. The help's log example is corrected.
- **BR-30.6** The `t*` options (P1.6):
  - `tlabel()`, `ttick()`, `tmlabel()`, `tmtick()`, `ttitle()`, `tscale()` and `tline()` are accepted on every twoway graph and apply to x axis 1 under twoway's base-format rule, with date literals in Stata units. The `axis(2)` forms route to the second axis. `tmlabel()`/`tmtick()` are accepted and named as not drawn until minor ticks are (P2.2). `tline()` is drawn under BR-30.21.
  - Refused as twoway: date literals where twoway's x axis is numeric (r(198), r(198), r(121) as measured), and where the first plot is lfit, kdensity or another type twoway refuses them for; a too-short `tm()` or `ts()` (r(198)); the left-aligned `%-t` form in `tline()` and `tscale(range())` (it is accepted in `tlabel()`/`ttick()`). A `format()` given with date literals is accepted or refused exactly as twoway's tickset format rules decide.
  - A date token is evaluated without ever running user text as a Stata command. `tscale(log)` on a date axis stays noted. The help lists every option.
- **BR-30.7** Time-series operators (P1.7):
  - `L.`, `F.`, `D.`, `S.` and their combinations, including `L(1/2).x`, are accepted in plot varlists on every type twoway accepts them on (measured; the line family, tsline and the lfit family), and drawn.
  - Titles, keys, notes and the CSV header show the expression as typed (`D.close`). `D.`/`S.` of a `%t` variable carry its format.
  - Refused as twoway: no `tsset` r(111) `time variable not set`; a string variable r(109); a factor variable r(101) `factor-variable operators not allowed`; operators on types twoway refuses them on r(101); `by()` with an operated variable r(5) `not sorted` (one hint line may follow); a bare `sort` with an operated x r(198).
  - Weights with operators stay refused (P2.14).
- **BR-30.8** `connect()`, `cmissing()` and `recast()` (P1.8):
  - `connect()` (`l`, `L`, `J`, `stairstep`, `stepstair`, `i`/`none`) and `cmissing()` are drawn on scatter, the line family, scatteri and the fits, per the measured truth: scatter `c(l)` draws the line; `J`, `stairstep` and `stepstair` draw stairs and keep today's tooltips (IR-3); `L` breaks where x drops; `cmissing(n)` breaks at missing values. `function` bridges interior missing regions by default and breaks under `cmissing(n)`.
  - Per-y lists follow BR-30.1; `cmissings()` is accepted; an unknown connect name is drawn direct, noted as twoway notes it; an unknown `cmissing()` value is refused r(101) in twoway's words.
  - `recast()` redraws base and range types as the target, with twoway's out-of-group fallbacks and notes (a yx type falls back to scatter, a range type to rspike, a pc type to pcspike; a range type cast to a yx name draws its first bound; `function` and `dot` ignore it). A derived type (fit, kdensity, function, histogram) keeps its computation and is drawn as the target. The key keeps the original series label. `recast(bar)` uses the one-x-unit width (BR-30.17).
  - `recast()` on lfitci, qfitci, lpolyci and fpfitci is refused r(198) `recastas() option not allowed`. Where twoway draws the same picture, dash is silent.
  - `cmissing(n)` on area/rarea and `connect()` on rarea stay noted (P2.42).
- **BR-30.9** `horizontal` (P1.9):
  - It is drawn on bar, rbar, spike, rspike, rcap, rcapsym, dropline, area, rarea, histogram, kdensity and function, with the axis variables, default titles, date kinds and y2 swapped and rcap caps perpendicular. Mixed orientation with a date axis matches twoway's truth.
  - `horizontal vertical` together is refused r(198) `may not combine options horizontal and vertical`. `horizontal` or `vertical` on a type twoway refuses them for is refused r(198) in twoway's words, judged on the type after `recast()` (`recast(bar) horizontal` is rc 0). `vertical` alone is accepted silently. The unsupported-option list and notes stop naming them.
  - After saved and served moves, turned layers keep their geometry; hover fields and the hover line follow the orientation; by() and `yaxis(2)` hold.
- **BR-30.10** `text()` and `ttext()` (P1.10):
  - Each copy is drawn at its position with its placement, orientation, size (Stata units), colour (BR-30.13), box and axis, on numeric and date axes (Stata units), on every by() panel with `iscale()`, after a move. Labels never extend the axis. Repeated copies keep their own sub-options. The scheme's text defaults apply. SMCL in the text follows BR-30.11.
  - Refused r(198) in twoway's words: a malformed point (`invalid point, BAD 30`), a missing axis pair, an unknown sub-option. A textbox sub-option that cannot be drawn is noted and listed in the help. Notes are raised once, in Stata, for both modes.
  - `ttext()` converts date literals under the first-plot or `xlabel()` format rule, with twoway's date refusals.
  - Limit `added_text`: default 1,000, ceiling 100,000, `$dash_max_added_text`; it counts texts × by() panels over the dashboard, and beyond it the command is refused r(134).
- **BR-30.11** SMCL and TeX (P1.11):
  - TeX delimiters (`$$…$$`, `\(…\)`) in any user text on the canvas are drawn as typed, never interpreted. The saved page ships no MathJax (a TeX title's page drops from about 3.1 MB to about 1.3 MB), and no user text reaches a TeX parser.
  - The graph-text tags `{bf:}`, `{it:}`, `{sup:}`, `{sub:}`, `{&name}`, `{c #}`, `{c name}` and the font tags (`{stSans}`, `{stSerif}`, `{stMono}`, `{stSymbol}`, `{fontface}`) are drawn as twoway draws them, in Unicode, with whole-string style and font set only where SMCL asks, at every canvas sink (titles, axis titles, tick labels, keys, panel labels, colour key) and in marker labels. A run Unicode cannot express gives one note per graph and sink kind. Other SMCL is drawn as typed and listed in the help (P2.47).
  - `{c 0}` empties the text and C0/C1 control codes are kept, as twoway does; every sink carries them escaped (`\uXXXX` in JSON/JS, HTML-escaped where HTML is written). dash-only page text translates characters and symbols and strips style tags; KPI and dashboard titles, `tabs()` and data-borne text (string tooltips, value-label columns, the CSV) stay raw, as the help states.
  - Hostile text (100,000 `{`, deep nesting) is handled in under one second.
- **BR-30.12** Size units (P1.12):
  - Numbers and keywords are Stata's relative units: one unit for every class at the 4-inch reference (rs = 2.88 pt; IR-1). The default marker goes from 8 to 5.87 px and the default line from 1.5 to 1.15 px.
  - `#pt`, `#in`, `#cm` and `#rs` convert at min(xsize, ysize) (graphsize when given); `*#` is relative; the full keyword ladder holds, `vhuge` included. Line widths follow Stata's linear ladder, `vvvthin` and `none` included, with a 0.3 pt hairline floor.
  - This holds for `msize()`, textbox `size()`, `labsize()`, `mlabsize()`, legend `size()`, title and axis-title sizes, colour-key label sizes and every line width (`lwidth()`, `mlwidth()`, `clwidth()`, `alwidth()`, region and reference-line widths, colour-key lines). `mlabgap()` is measured from the marker's edge.
  - An unknown size name draws the class's medium, noted as twoway notes it. Negative unit and multiplier forms are refused as twoway refuses them.
  - Brushed-away (nonselection) and muted copies of a glyph follow the option appliers: their size, width, colour, marker and dash are the drawn glyph's, with dash's nonselection alpha kept, in both modes (S08; later appliers reach them through S08's sync). P2.49 is not filed.
- **BR-30.13** Colour grammar (P1.13):
  - `colour*#` (with the clamp above 1), CMYK, HSV, quoted forms with intensity, `%` and `*` in either order, and `bg`/`fg`/`background`/`foreground` from the scheme are read in options and in scheme files. Invalid multipliers are ignored as twoway ignores them.
  - A bare `*#` or `%#` at any colour site (markers, lines, fills, CI bands, marker labels, titles, subtitles, notes, captions, axis titles, label and axis-line colours, graph and plot regions, the KPI, reference lines, `colormissing()`) takes the site's own base colour before intensity, composed with the intensity blend and a named style's base colour.
  - Colour names are case-sensitive, in options and in scheme files. An unknown or out-of-range colour draws black (bars #333333), noted, at every site. `grey`, `dimgrey`, `bluishgrey` and `ltbluishgrey` become unknown names (IR-6). `"255,0,128"` is refused r(198) in twoway's words. A short or invalid hex draws the default, silently. An unreadable scheme value draws #000000 for that key where twoway does.
  - The KPI keeps its case-insensitive Stata lookup ahead of CSS colour names.
- **BR-30.14** Named styles (P1.14):
  - `pstyle()` (and its `p()` alias: its own key, the first copy wins, applied last), `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` take `p1`-`p15` on every type, in twoway's factor order: explicit options win.
  - Every linestyle name of Stata's 76 shipped linestyle files resolves, and a table of the other Stata names (ci, ci2, histogram, foreground, background, grid, major_grid, minor_grid, refline, none and the p#line/bar/area/other/mark/box/dot/arrow forms) resolves (IR-14). `pstyle(ci)` and `ci2` work on non-CI types.
  - An unknown name draws twoway's default attributes for its class, noted once per layer.
  - `dstyle()`, `dlstyle()` and `bmlinestyle()` are accepted, kept in the spec and named as not drawn (P2.9, P2.8). Area and rarea outlines and pc arrowheads stay noted (P2.12, P2.8).
- **BR-30.15** by() (P1.15):
  - Panel labels are drawn as a centred panel title, not appended to the graph title. Composite labels are joined with ", ". Missing panels read "(missing)", and a string `""` group counts as missing in group panels and in Total. Date panel titles keep dash's date text.
  - `by(, title() subtitle() note() caption())` are drawn once over the array. The "Graphs by <label>" note uses the variable's label, else its name, and `by(, note(""))` removes it. `by(, graphregion() plotregion())` stay named, not drawn (IR-9).
  - `rows()`, `cols()`, `holes()` and `colfirst` place panels as twoway does. `cols()` beyond the panel count is honoured up to the by() groups limit (100, ceiling 1,000), then clamped, noted. `iscale()`, `imargin()` and `compact` act in Stata units; `xsize()`/`ysize()` size the whole array.
  - Refused as twoway: `rows()` with `cols()` r(198) `may not specify both rows() and cols()`; out-of-range `rows()`, `cols()` or `holes()` r(125); capitalised forms (`YRESCALE`) and a repeated `style()` r(198).
  - Shared panels show outer axes and edge labels only, with the `i*`/`noi*` options and `noedgelabel`. Axis titles are drawn once, and no panel draws an axis-2 title. There is one legend, governed by `by(, legend())` (with `at()`) and the scheme's by-legend position. There is one colour key, only under `by(, clegend(on))`, showing panel 1's mapping, silently; a level has the same colour in every panel.
  - Each panel label is drawn in twoway's filled box from the scheme (S53, Q-28.1; ratification row 36, changed).
  - On a narrow screen the panels stack and every panel's axis labels show. Forms twoway ignores under by() are silent.
- **BR-30.16** Keys and default titles (P1.16):
  - lowess, lpoly, mband, mspline and function layers are keyed in twoway's text (for example "lowess mpg weight", "Median bands"); the pc family, scatteri and pci are keyed as twoway keys them; a function name may be any Unicode identifier of at most 32 characters.
  - Default axis titles follow twoway's first-equals-last rule per axis: no title when the layers' labels differ. Range types get a y title. `yaxis(2)` is titled by its own layers' variables. There is no opt-out.
  - Merged keys, histogram-only legends and first-used-axis placement stay open (P2.50-P2.52).
- **BR-30.17** Bar and range geometry (P1.17):
  - bar and rbar default to one x unit wide (in the variable's units on a date axis); rbar honours `barwidth()`; widths do not change after a move.
  - rcap's cap length follows `msize()`, defaulting to the scheme's p# symbol size; rcapsym draws no caps and sizes its end markers from the scheme. rcap `barwidth()` is refused r(198) `option barwidth() not allowed`.
  - The default base of bar, area, spike and dropline is twoway's: clamped into the axis scale (under by() the common minimum; per panel under `yrescale`; never 0 on a log axis), so a 0 outside the data no longer extends the axis. An explicit `base()` stays inside the range. On a date axis the default base is 01jan1960.
- **BR-30.18** Axis sub-options (P1.18):
  - `nolabels`/`labels`, `noticks`, `labcolor()`, `tlength()`, `tposition()`, the anglestyle names (`rvertical`, `stacked`, …), `xscale(off)`/`on`, `noline`/`line`, the axis line's colour, width and pattern, `alt` and `titlegap()` are drawn on every axis, second axes included. Tick-only positions honour `noticks`, `tlength()` and `tposition()`.
  - An anglestyle name is matched case-sensitively: `angle(Vertical)` is noted and drawn at 0, as twoway does (IR-5). Out-of-bound angles (`angle(400)`) and capitalised `NOLABELS`, `OFF` and `Alt` are refused r(198) in twoway's words. Under by() the `scale(off)`, `nolabels`, `noticks` and `titlegap()` that twoway ignores are silent.
  - `add` adds to the default ticks (date ticks included) and survives every re-tick after a move; an `axis(2)` label with `add` is drawn; a repeated `add` is kept; `a(b)c` rules and `norescale` on a lone rule draw as twoway draws them.
- **BR-30.19** Sub-option abbreviations (P1.19):
  - Legend, axis-label and tick, `xline`/`yline` and textbox sub-options accept twoway's abbreviations (`c()`, `r()`, `lab()`, `posi()`; `labs()`, `glc()`, `ang()`, `for()`, `g`, `nog`, `val`, `labc()`, `tl()`, `tp()`, `nolab`, `noli`, `titleg()`; `lc()`, `lp()`, `lw()`, `lst()`, `noex`, `la()`, `st()`; textbox `s()` is size).
  - Names match in lower case only. Capitalised names and spellings twoway refuses are refused r(198) in twoway's words. A sub-option dash honours, given a bad value, is refused with twoway's code (`legend(c(red))` r(121) `cols() invalid`).
  - Repeated copies merge by full name, the last copy winning; `rows()` beats `cols()`; quoted label text is never read as a sub-option. A note names the sub-option as the user typed it.
- **BR-30.20** `plotregion()` and `graphregion()` (P1.20):
  - Their sub-options and abbreviations (`fc()`, `lc()`, `c()`, `lw()`, `lp()`, `ls()`, `sty()`, `col()`, `fcol()`, `mar()`) are drawn: `color()` sets fill and outline; `none` paints nothing; `%NN` opacity; `style(none)`, `lstyle(none)` and the area-style names; `lpattern()`; the graph outline; widths on Stata's ladder. Repeated copies merge and margins add up.
  - Typos and a sub-option repeated within one copy are refused r(198) in twoway's words. Valid forms dash cannot draw (`lalign()`, `ilalign()`, `graphregion(margin())`, the graphregion `i*` options) are named in one note.
  - `bgcolor()` paints under the graph region, as twoway does: a region `none` shows `bgcolor()` if given, else the scheme's background, and a lone `bgcolor(red)` no longer shows (IR-2).
  - `plotregion(margin())` sets the plot-region margin (exact for zero; within BR-30.3's tolerance otherwise). The plotregion `i*` inner box is drawn at the finished range and follows it after a move.
  - Region styling writes only computed numbers and sanitised colours into the page.

- **BR-30.21** `xline()` and `yline()` (P1.21):
  - Numlist positions (`2000(500)3000`, `a/b`) are drawn; duplicates are dropped.
  - Refused as twoway, in twoway's order, r(198)/r(100)/r(123): invalid positions (including `nan`, `inf`, `1e400` and `1_000`, `invalid line argument`), more than 2,500 positions in one copy, and unknown, short, repeated or capitalised sub-options (`NOEXTEND`, `LSTYLE()`).
  - Abbreviations follow BR-30.19. `lstyle()` takes every linestyle name (BR-30.14). `lalign()` is accepted silently. Lines are drawn above the grid and below the glyphs, and never extend the axis.
  - `extend`/`noextend` and `style()` follow the scheme's xyline extend keys, over the finished axis and again after every move; under `margin(zero)`, `noextend` equals `extend`.
  - Limit `reflines`: default 10,000, ceiling 100,000, `$dash_max_reflines`; it counts positions × by() panels over the dashboard, and beyond it the command is refused r(134).
  - A line outside the range is clipped at the frame (P2.54).
- **BR-30.22** `function` without Stata's points (P1.22, closed by disposition under M12):
  - A Stata-built spec draws Stata's own points (WP-29 P0.6, unchanged).
  - The points-free fallback keeps its ten functions. Any other function draws nothing and gives one neutral note, in both modes, that reaches Stata: it says the layer needs Stata's points, lists what the fallback knows and names the function it met (true for `pi`, `e` and `sin (x)`).
  - The help states the rule and no longer promises a draw from the expression.
- **BR-30.23** Dates on every axis (P1.23):
  - Range and pc plots with a date y (or a pc date x) get a date axis. An `axis(2)` layer keeps the primary date axis. y2/x2 date axes show dates, take their own options and `#N` ticks, and range in date units.
  - scatteri, pci and pcarrowi coordinates, `function range()` and an explicit `base(#)` are placed in date units. A literal outside 0100-9999 on a date axis is drawn at its number as twoway draws it, with no note; only one past the browser's dates (|ms| > 8.64e15) is left out with one note.
  - A date layer beside a numeric layer on one axis is drawn in Stata units, labelled in the first layer's date format, and `xlabel(minmax)` reads Stata units there. The mixed axis renders under the page's CSP.
  - A date colour variable's key, ticks and `colorcuts()`/levels boundaries are in Stata units; key text uses twoway's comma general format; `zlabel(, format(%t*))` is honoured.
  - Fallback tooltips (histogram, fits, kdensity) use the variable's display format. The histogram tooltip names its measure (Density, Frequency, Fraction or Percent), not "Count".
- **BR-30.24** `mlabvposition()` and `mlabtextstyle()` (P1.24):
  - `mlabvposition(varname)` places each row's label in both modes and after saved and served moves. One variable applies to every y and is never split. Offsets stay physical under `horizontal`.
  - A repeated `mlabvposition()` and the types twoway refuses it on are refused r(103) in twoway's words (naming the label variable when `mlabel()` is given), judged on the type after `recast()`.
  - `mlabtextstyle()` is a per-y list (BR-30.1) resolved from Stata's 37 shipped textboxstyle names on the scheme's marker-label defaults. A user textboxstyle file is noted (P2.55).
  - No declared plot option is silently dropped: each reaches the spec or the list of options named as not drawn.
- **BR-30.25** Scheme resolution (P1.25):
  - The six StataCorp schemes dash refused (meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta, stgcolor_mv) are shipped and drawn as twoway draws them: 26 schemes in all. stcoloralias draws as stcolor (its `zyx2rule` is unread, documented).
  - `scheme(NAME)` and an inherited `c(scheme)` resolve along Stata's whole ado-path in Stata's order, as `scheme-NAME.scheme` then `NAME.scheme`, with the shipped StataCorp names first, so a working-directory `s2color.scheme` no longer overrides the shipped one. `#include` follows the same walk. An inherited `c(scheme)` always walks; an explicit theme alias loses to a file of that name and works when none exists.
  - A path, separator, `..` or quote in `scheme()` is refused. A file that is not regular, that resolves outside its directory, or that exceeds the size limit is refused. A scheme file is read as data and never run. The refusal lists the 26 names and the themes, and the help's remedy is corrected.
  - A served dashboard whose graphs use different schemes draws each graph with its own scheme, as the saved page does (its own entry, P1.25.6).
- **BR-30.26** Notes (P1.26):
  - A note is one `(note: …)` line in text colour, shown under `quietly` and `set output error`, hidden by `capture`, SMCL-escaped, and free of internal paths and source lines. A session `warnings` filter neither hides a note nor turns it into an error (no r(7102)). A repeated note prints once.
  - `dash build, server` prints the saved build's option and empty-layer notes, from one trial render. `dash serve` relays the child's notes, ERROR lines and tracebacks (redacted, at most 200 lines, de-duplicated against the build's), from the child's warm-up, never rendering twice. A trial that raises stops `dash serve` with r(198) and is noted under `dash build, server`. Access-log lines stay out.
  - A layer whose own if/in keeps no row is silent in both modes, as in twoway.
- **BR-30.27** Command form and `saving()` (P1.27):
  - Batch mode and `set graphics off` open no browser and print the path; interactive console Stata still opens one. A temporary preview is still written, and its line says it is temporary and names `saving()`.
  - A `twoway`, `tw`, `two` or `graph twoway` prefix is accepted. `twow`, `twowa`, `gra` and `grap` are refused r(199) `command X is unrecognized`, as twoway refuses them.
  - `saving(f, replace)` and `saving(f, asis)` are read as twoway reads them, on the one-line form, `dash build` (HTML and server) included. An unknown `saving()` sub-option is refused r(198) `option X not allowed`; an unquoted `saving(my file.html)` is refused as twoway refuses it.
  - Under M11 `saving()` accepts `..` and `; & | < >`, and keeps refusing a double quote, backquote, `$`, control characters and a leading `-`. The served "To launch" line is single-quoted on Mac and Unix.
  - `dash twoway` with nothing after it stays refused (P2.56).
- **BR-30.28** Export (P1.28):
  - dash returns `r(filename)`: the absolute path of what it wrote, set last, never holding the served key, empty when the command is refused, and documented as transient for previews. No other internal `r()` leaks from any subcommand.
  - One note per dash command, only when Stata holds a graph in memory, says that `graph export` would write that graph. A `saving()` name with an image extension writes `.html`, noted.
  - The help documents the export limit and that printing prints the active tab.
  - Every grid toolbar in both modes gains a "Save as SVG" action that runs under the page's CSP. There is no SVG backend, so the PNG save keeps working.
- **BR-30.29** Page security (P1.29):
  - The saved page's script policy lists a hash for every inline script and no `'unsafe-inline'`. An inline script without its hash stops the build with a named error and writes nothing.
  - The served page carries a per-document nonce: nonce-only if the browser test is clean, otherwise also `'self'` with the reason recorded. The `python app.py` header keeps its policy and the page's own policy governs. `'unsafe-eval'` and inline styles stay (BokehJS needs them) and are documented. The empty and redirect pages carry `default-src 'none'`.
  - In a browser, in both modes, an injected inline script or handler is blocked, and the page still renders, filters and exports. A browser that supports only CSP level 1 shows a blank page.
  - On Windows a path holding a cmd metacharacter (`% ! ^ & | < > ;`) is written but never opened through the shell: the path is printed, `r(opened)` is 0, `r(why)` says why, and the command ends rc 0 (tested as a pure function and a dry run).
  - The help states the `saving()` character rule and what the CSP does and does not protect.
- **BR-30.30** The bokeh window (P1.30):
  - `dash_setup` installs `bokeh>=3.8,<3.10` (`<3.11` only if bokeh 3.10 is verified inside WP-30) into an environment dash created. A Python or environment dash did not create is never downgraded: above the window it is reported "outside the verified range" with rc 0; a managed Python gets the managed guidance, never a pip line.
  - At run time, in both modes: above the window one note and the run continues; below 3.8 the command is refused, and so is the served app at start (`python app.py`, `bokeh serve`). "Verified" means major.minor.
  - The text-sink injection checks run for every version in the window.
  - If a Bokeh release changes an internal dash relies on (host matching, the page template's blocks, the origin check, the auth hook, the BokehJS calls the ticker, the date transform and Save as SVG use), the server refuses to start with a named error.
- **BR-30.31** Served capacity (P1.31):
  - The dataset is decoded once per app process. At most `maxsessions()` sessions run at once (default 20; 0 refused) under `dash serve`, `python app.py` and `bokeh serve`. Beyond the cap a static busy page answers (HTTP 503 with Retry-After, no auto-refresh).
  - A session with no filter, brush or CSV activity closes after `idletimeout()` minutes (default 60; 0 never), with a reload message.
  - The app warms up before it listens and first prints "preparing the dashboard (N rows, …)".
  - Per-session memory growth stays at or below 80 MB at 200k rows × 3 layers (60.7 MB today, so the test is a regression guard). The estimator memo holds at most 64 MB per process and never runs in Stata's process. [WP-30 follow-up, 09oct2026: the bound is removed by the maintainer's decision; dash sets no per-session memory bound, since the rows a reader serves are not known]
  - A filter-move recompute never blocks other sessions or `/health`: one worker; the latest request per session wins; stale results are dropped; the session shows an "updating" cue. The worst wait (about 3 min at 20 × 8.7 s for lowess at 100k) is documented.
  - Opening a session still runs on the event loop (P2.57).
- **BR-30.32** Dependency guards (P1.32):
  - A missing or unimportable numpy, pandas or bokeh, or a Python below the floor, gives one message naming `dash_setup`, from `dash` and from the generated app, never a bare `ModuleNotFoundError` or `SyntaxError`. bokeh below 3.8 is refused (BR-30.30). numpy or pandas below `dash_setup`'s minimums is noted, not refused.
  - dash checks availability without running Python as a program, before it renders.
  - `dash_setup`'s first Python call is captured and summarised with the architecture hint.
  - `dash clear` still prunes with the packages missing.
- **BR-30.33** The Python floor (P1.33):
  - The declared floor is the lowest of 3.11 and 3.12 at which both pytest suites (with the dev pins and with the Stata pins), a fresh resolve as `dash_setup` installs, the Stata venv-link leg and one full certification run pass. `dash.pkg`, both help files, `dash_setup` and the version messages state it, and code that needs a newer Python has a fallback or guard.
  - `dash_setup` with a Python below the floor says to link Python <floor> or later and never suggests `venv()`.
  - The floor is measured once, in WP-30, by S05; the release gate gains no floor-Python leg, and the manual re-measure procedure is written in `scripts/floor_matrix.sh`'s header. Downloads go only into scratch environments (M10).
- **BR-30.34** Portable runners (P1.34, closed under M4):
  - Every runner (`scripts/stata_slot.sh`, `run_cert_suite.sh`, `run_release_gate.sh`, `stata_python_exec.sh`, the Makefile, the header of `test/run_all_cscripts.do`, `measure_stata_coverage.py`, every extractor, `test/fixtures/twoway_corpus.do`) uses `STATA_BIN` if set, else `/usr/local/bin/stata-mp`, with an architecture prefix only when the binary's own architecture needs one (right under Rosetta). No runner selects a Stata 14-18.5 binary.
  - The repository root is `DASH_REPO`, else the current folder when it holds `dash.ado` and `test/run_all_cscripts.do`, else r(601).
  - No file under `scripts/`, `test/` or the Makefile holds `arch -arm64` or the maintainer's path (a guard test, no exemption list). The two option generators are retired and refuse to run.
  - On this Mac the effective command is unchanged (the console binary in batch mode).
- **BR-30.35** The Stata floor (P1.35, closed under M2):
  - `dash` and `dash_setup` refuse a Stata below 19 as their first act, with `dash requires Stata 19 or later; this is Stata X.Y` and r(9).
  - Every program declares `version 19`; no `version 16.0` remains in dash.ado, dash_setup.ado or the generators that write one.
  - `dash.pkg` and both help files say "Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64" and "Measured on MP only".
  - Function points are unchanged by the new language level, and a full certification run is green after the sweep.
- **BR-30.36** Refusals (M5): every form WP-30 newly refuses (the register's 26 M5 rows and those of IR-17) is refused with twoway's return code and message text as measured in StataNow 19.5, has a test asserting both, and has a CHANGELOG line under "Changed behaviour (may need your do-files changed)". A valid twoway option dash cannot draw is noted, never refused. Outside the areas WP-30 touches, nothing is newly refused.
- **BR-30.37** Silence (M6): where twoway draws the same picture and prints nothing (the register's 11 M6 rows, among them a layer whose own if/in keeps no row, the by()-ignored axis forms, a lone style value over several y, the levels the single by() colour key leaves out, a user scheme's `intensity bar`/`intensity area`, and a short or invalid hex), dash prints nothing in either mode.
- **BR-30.38** Both modes: every behaviour in BR-30.1 to BR-30.35 that concerns drawing holds on the saved page and in the served app, before and after a filter move, and the two modes draw the same. No saved/served difference is allowed for in the parity test.
- **BR-30.39** Announced changes (M1, M5): every look change has a CHANGELOG line under "Results that change" naming the command, the old value and the new; every newly refused form has one under "Changed behaviour"; every new capability under "New"; the floors and the bokeh window under "Requirements"; every closed threat under "Security".
- **BR-30.40** Tracking: every WP-30 BUGS.md entry is closed with a Resolution naming tests that exist; every CHANGELOG marker is replaced; ROADMAP WP-30 is DONE; the GAPS2 ids it closes are marked with commits that exist; the manifest's residuals and P2.42-P2.57 are filed.

### Technical requirements

The technical requirements of each entry are its section's TR-NN.k in .ultraplan/wp30/index.md and the section files it lists (plain text, not a link).

### Acceptance criteria

- **AC-30.1** The 56 entries S01 opened are closed, each with a Resolution `(WP-30, P1.<n>[abc])` naming tests that exist; `WP30_OPEN` is empty and pinned so. The extra entries are in place: P1.5.7 and P1.25.6 closed in their sections' fix commits; P2.49 is not filed, because S08 fixes it under P1.12a. BUGS.md holds exactly 3 open entries.
- **AC-30.2** Red first: each fix commit body opens with its saved failure text and a `Regression:` line per regression test (G1); every flipped test has a `Flipped:` line; guard tests are listed apart; there is no test-only commit; the collected test count never falls.
- **AC-30.3** Truth: `test/test_wp30_truth.cscript` runs all 57 blocks with every case `PASS` and no SKIP on a machine with Python; every new fixture carries the D12 `_meta` stamp with `stata_version` and is committed; no fixture is hand-patched.
- **AC-30.4** Parity: `test/test_mode_parity.py` is green with every drawing section's CORPUS cases; `ALLOWED` is unchanged; `_MUST_WARN` entries were edited only by the sections whose fixes silenced them.
- **AC-30.5** Served names: `TestTheServedAppCarriesEveryName` (with `test_every_listed_name_exists`) and `TestTheServedAppDefinesEveryNameItReads` are green.
- **AC-30.6** Refusals and silences: every M5 refusal row has a test asserting twoway's return code and message text as measured in 19.5, and a CHANGELOG "Changed behaviour" line; every M6 row has a test asserting no note in either mode.
- **AC-30.7** Look: each shipped scheme's look truth passes (BR-30.2, BR-30.4); the size defaults are pinned (markers 5.87 px, lines 1.15 px); the tsnatscale floors and the 12,000-answer parity hold; the timed budgets of pass.
- **AC-30.8** Security (G9): green, each named in its commit body:
  - the browser test of both modes (an injected inline script or handler is blocked; the page renders, filters, exports and saves as SVG); an unhashed inline script fails the build; `default-src 'none'` on the empty and redirect pages;
  - the Windows opener runs nothing for a path with a cmd metacharacter;
  - notes SMCL-escaped with no internal paths; relayed child output redacted and bounded;
  - TeX never interpreted; hostile SMCL handled in under one second; control codes kept as twoway keeps them and escaped at every HTML/JS sink;
  - the scheme lookup's name, containment, regular-file and size guards, with symlink, oversized, traversal and hostile-directive tests; scheme files never run;
  - region styling writes only computed numbers and sanitised colours;
  - the `reflines` and `added_text` limits refuse r(134);
  - date tokens never run as Stata code (no `_stata()` call takes user text);
  - Bokeh internals fail closed; below bokeh 3.8 refused at app start;
  - the session cap, idle close and busy page; the turned-bar redraw never reads a property name from page data; the worker's thread safety.
- **AC-30.9** Floors: `grep -c 'version 16.0' dash.ado dash_setup.ado` prints 0 and 0; the Stata guard's refusal and the guard order are pinned; the declared Python floor equals the matrix's lowest pass; the bokeh window is declared once and checked at run time; the dependency guards are green; the runner path guard is green with no exemption list.
- **AC-30.10** CHANGELOG.md holds no `<!-- WP-30` marker; every WP-30 line ends `(WP-30, P1.<n>[abc])`; each Results line names the command, the old value and the new.
- **AC-30.11** Tracking documents: ROADMAP's WP-30 is headed DONE with §6's requirements and these criteria; every id in its `**GAPS2 closed:**` has a `Closed in WP-30` Tracked line with a commit that exists; partly closed ids say what is open; the 22 residuals (as amended) and P2.42-P2.57 are filed; DROPIN-REMAINING.md's P1 rows carry their commits; `test_tracking_documents.py` is green.
- **AC-30.12** Release: `make test`, `make test-dev`, `make cert` and `make gate` are each green once on `wp30-p1`, through the queue; the certification time and its change from the step-0b baseline, the page sizes, render times and served memory and latency are recorded (S58.7).
- **AC-30.13** Messages and scope: index G7's message check prints 0 on every commit message in `main..wp30-p1` and on the added lines of BUGS.md, CHANGELOG.md, dash.sthlp and dash_setup.sthlp; no commit, entry, CHANGELOG line or help line names a tool or vendor; the project instructions file, `.gitignore` and (outside index E7's rule) `AGENTS.md` are in no WP-30 commit.
- **AC-30.14** GitNexus: impact ran at every batch base, every HIGH or CRITICAL result was reported before its edit and the approval recorded, every `UNKNOWN` was confirmed by grep; `detect-changes` at every landing named only the section's symbols; the final compare against `main` is recorded.
- **AC-30.15** The merge command into `main` is reported and not run; every worktree and `wp30-s<NN>` branch is removed.

#### P1 traceability

| P1 | Entry (BUGS.md) | Grade | Section | Commit |
|---|---|---|---|---|
| P1.1a | A style list over several y variables, such as mcolor(red blue), is given whole to ... | S2 | S11 | e8953d4, a001fd6, 099a242 |
| P1.1b | Per-series value lists such as mlabel(make rep78), jitter(2 3), base(10 20) and ... | S2 | S20 | 8bd6b5a |
| P1.2a | The default chrome differs from every scheme: a bold left-aligned title, italic axis ... | S3 | S15 | 6a777a3 |
| P1.2b | Markers are drawn at alpha 0.8, and fintensity() and the schemes' bar and area ... | S3 | S16 | 870e778 |
| P1.3a | Default numeric axes use Bokeh's ticker and 10 percent padding, not twoway's natscale ... | S3 | S21 | bde085e, 90ad393 |
| P1.3b | Default %td to %ty date axes keep Bokeh's DatetimeTicker, not twoway's tsnatscale ticks | S3 | S44 | 8573347 |
| P1.4a | The scheme's opacity, histogram colour, intensity and width, and its hollow and sm ... | S3 | S24 | 638970a |
| P1.4b | Marker-label size and colour are fixed, the colour key has no scheme chrome, and ... | S3 | S33 | c0518a7 |
| P1.5 | Default tick labels ignore the variable's display format, xlabel(, format(%td)) is ... | S1 | S18 | 34832ad |
| P1.6 | The tsline time-axis options tlabel, ttick, tmlabel, tmtick, ttitle, tscale and tline ... | S2 | S51 | 9a72553, c565897 |
| P1.7 | Time-series operators in plot varlists, such as line D.close date and lfit y L.x, are ... | S2 | S42 | d69005d, acd868f |
| P1.8a | connect() and cmissing() are not honoured: scatter y x, c(l) draws no line, stairsteps ... | S2 | S40 | fa52891 |
| P1.8b | recast() is not honoured, and recast() on lfitci, qfitci, lpolyci and fpfitci is ... | S2 | S45 | f20751d |
| P1.9a | horizontal is not drawn on any plot type, and vertical is named as unsupported | S2 | S49 | 7229a0c, 169130d |
| P1.9b | The filter-move redraws of both modes write vertical geometry only, so a horizontal ... | S2 | S55 | a5e3757 |
| P1.10 | text() and ttext() annotations are not drawn | S2 | S56 | 1a5edf1, 56b3597 |
| P1.11a | TeX delimiters in titles, labels and keys are typeset as mathematics through MathJax ... | S2 | S09 | 3bdffb5 |
| P1.11b | SMCL in graph text, such as {bf:}, {it:}, {sup:}, {&beta} and {c #}, is drawn literally | S2 | S29 | a0224b5, 66c51ca |
| P1.12a | Marker, text and gap sizes are read as pixels on a private ladder, and #pt, *# and ... | S2 | S08 | a1dcb2f |
| P1.12b | Line widths use a private ladder without vvvthin or none and read numbers as pixels, ... | S2 | S13 | 37e9fa4 |
| P1.13a | Stata colour forms such as navy*.5, CMYK, HSV, bg and fg are refused, and an unknown ... | S2 | S30 | d680274 |
| P1.13b | A bare *# or %# colour, such as mcolor(*.5), is refused or loses the site's default ... | S2 | S43 | f3a0403 |
| P1.14a | pstyle() works only on the four CI fits, and lstyle, mstyle, mlstyle, astyle, alstyle, ... | S2 | S32 | f4216a8 |
| P1.14b | Style names other than p1-p15, such as ci, histogram, refline and p1bar, are not read ... | S2 | S36 | 38bbb05, 98109fc |
| P1.15a | by() panel labels are appended to the graph title, there is no Graphs by note, ... | S2 | S28 | e7c6ed3 |
| P1.15b | by() rows, holes, colfirst, compact, iscale and imargin are named and ignored, bad ... | S2 | S48 | 1326b97 |
| P1.15c | Under by() every panel draws a legend and repeats both axes, and by(, legend()) and ... | S2 | S53 | 52d5b6a, 2f51a50 |
| P1.16 | Legend keys and default axis titles do not follow twoway: fits are keyed Fitted ... | S1 | S19 | 3f172a9, ace9c19 |
| P1.17a | bar and rbar default to 0.8 of the smallest x gap, rbar ignores barwidth() without a ... | S1 | S14 | 624837e |
| P1.17b | bar, area, spike and dropline draw from 0 rather than twoway's default base, and a 0 ... | S1 | S27 | b3fc476 |
| P1.18a | The axis look sub-options nolabels, noticks, off, noline, line colour, width and ... | S2 | S31 | ebde0e9 |
| P1.18b | The add sub-option replaces the default ticks instead of adding to them, and an ... | S1 | S52 | a34192b |
| P1.19 | Sub-option abbreviations such as legend(c(2) posi(6)), ylabel(, labs(small)) and ... | S2 | S10 | ecb8aec, 4ab91c7, e64c136 |
| P1.20a | plotregion() and graphregion() styling sub-options such as style(none), lcolor(), ... | S1 | S38 | 2207ddb |
| P1.20b | plotregion(margin()) and graphregion(margin()) have no effect and no note, and the ... | S1 | S47 | 6e2af0c |
| P1.21a | xline() and yline() numlists such as xline(2000(500)3000) draw nothing, and lstyle() ... | S2 | S39 | 78f9045 |
| P1.21b | xline() and yline() noextend, extend and style() are only named, so every line spans ... | S2 | S50 | 10ab4ce |
| P1.22 | The points-free function fallback knows ten functions and draws any other in silence | S3 | S26 | 47677f8 |
| P1.23a | Dates on range, pc, immediate and second axes are drawn at raw or millisecond ... | S1 | S35 | 7aa8875 |
| P1.23b | A date colour key shows epoch milliseconds, fallback tooltips ignore display formats, ... | S1 | S17 | cc3c900 |
| P1.24 | mlabvposition(varname) and mlabtextstyle() are declared and pending but never ... | S2 | S37 | b79db35, 390d964 |
| P1.25a | Six StataCorp schemes, among them meta and stcolor_mv, are refused r(198) where twoway ... | S2 | S07 | 438d27e |
| P1.25b | scheme(NAME) is looked for in two places only, never along Stata's ado-path or under ... | S2 | S34 | 15c4f7b |
| P1.26a | Notes print as raw Python warnings with internal paths, a warnings filter of ignore ... | S2 | S06 | dd7c165 |
| P1.26b | dash build, server and dash serve report no option or empty-layer notes, and the ... | S2 | S23 | 824e0be |
| P1.27 | The drop-in command form fails: a twoway prefix is refused, saving(name, asis) writes ... | S2 | S12 | 6906236, 8346679, 10f1c58 |
| P1.28a | dash returns no r(filename), and graph export after dash fails r(601) or silently ... | S2 | S22 | eea99ce |
| P1.28b | Neither mode offers a vector export: the toolbar saves only a PNG at the screen's ... | S3 | S54 | fd4fff0 |
| P1.29 | Both content security policies allow inline scripts, and percent and exclamation signs ... | S2 | S04 | 0e8fbaf |
| P1.30 | The bokeh dependency has no ceiling or run-time version check, and the Bokeh internals ... | S2 | S41 | 621c477, 61f5c21 |
| P1.31a | The served app has no session cap or idle lifetime and decodes the whole dataset again ... | S2 | S46 | 842e1d9 |
| P1.31b | One reader's filter-move recompute blocks the served event loop for every other reader | S2 | S57 | e371f8d |
| P1.32 | A missing numpy, pandas or bokeh or an old Python fails with a bare ... | S2 | S25 | 9dc17da |
| P1.33 | The Python floor of 3.13 turns away 3.11 and 3.12 users, and dash_setup reports ... | S2 | S05 | b3153d0, dcbca5d |
| P1.34 | The certification runners hard-code arch -arm64 and the maintainer's paths, so they ... | S3 | S02 | 44f8ab0 |
| P1.35 | dash declares Stata 16.0, but only StataNow 19.5 has ever run it or made its truth ... | S2 | S03 | 1f05b63 |

### Deferred: the platform package (P1.34.6)

- Linux, Windows (the `/e` batch flag, cmd.exe, `Scripts\python.exe` venvs), Intel macOS and GUI Stata, with WP-29's private-file, lifecycle, served-key and PEP 668 paths there (M4; manifest item 34; S02).
- Stata 16-18.5 certified (version-parametrised runners, version-keyed truth, a Break fallback below 18.5, version-dependent rpcap/rpspike advice), and Stata 19.0, BE and SE measured (M2; manifest item 35; S03).
- A scripted image export: `dash export using file.png|pdf|svg` driven by a browser found on the machine, at a chosen size, `r(filename)` its output (P1.28 B3, GAPS2-E10c; M8; manifest item 28; S22, S54).
- Python 3.10 and older, and Windows patch levels of 3.11 without CPython's os.mkdir 0o700 fix (CVE-2024-4030; dash_render.py relies on it) (manifest item 33; S05).
- S02's critic list: `release_gate_venv.do`'s `gatevenv/bin/python`, the `/tmp/dash-stata-slot-N.d` locks, the Makefile's `STATA_BIN` default, the `W29_REPO` extractors' POSIX `capture shell cd … && git rev-parse`.
- S04: whether cmd.exe expands `%` and `!` in a page path; opening such a page without cmd.exe (option B, `os.startfile`); Firefox and Safari runs of the CSP browser test.
- S12: `c(mode)`/`c(graphics)` under Windows `/e`, `/b` and GUI Stata, and the Windows `To launch:` line.
- S25: the processor hint off Apple Silicon. S34: Windows and Linux path and case rules for the scheme walk.
- S41, S44, S46, S54, S57: Linux, Windows and Intel runs of the bokeh window, date-tick zoom, session lifetimes and 503 path, the Save as SVG action and the recompute worker; browsers other than Chrome.
- Every section's "Stata 14-18.5 not run (M2)".

### Scope changes of existing items

- P2.11: the sm* sizes closed by P1.4a for the scheme and `msymbol()` (IR-4); the `x`/`smx`, `v`/`smv` geometry measured; the lower-case shorthands stay.
- P2.12: `lwidth(none)` closed by P1.12b; `mlabtextstyle` closed by P1.24.
- P2.13: the graphsize reference closed by P1.12a; `xsize()`/`ysize()` stay (S08 Q1).
- P2.14: gains `fintensity(1e400)` (S16), `[aw=L.x]` reusing `_dash_tsop_gen` (S42), and S20's value-list bounds.
- P3.2 loses `xvarformat()`/`yvarformat()` (P1.5). P3.7 loses its extractor-path part (IR-8, P1.34). P3.9 gains the two requirements files and the bokeh window comment (P1.33, P1.30). P3.11 gains the beforeprint layout and the SVG's omissions (P1.28).

### Done, measured (09oct2026)

- **Entries.** 56 P1 entries closed test first (S1 9, S2 38, S3 9), with P1.5.7 and P1.25.6 closed in their sections' commits; P2.49 not filed (S08 fixed it under P1.12a, ratification row 27). BUGS.md holds 3 open entries (none S1 or S2). `WP30_OPEN = {}` behind `TestWp30Tracking::test_no_wp30_entry_remains_open` (S58.1).
- **Per entry.** One clause each from the traceability table.
- **GAPS2.** Closed: A3, A13, B12, B14, B16, B18, B20, B22, B23, B25, B31, D2, D3, D7, D8, D9, D10, D11, D12, D18, D19, F3, F5, G4, G10, H4, H6, I12, I14, K1, X4, X5. Partly closed: A4, B11, B17, B21, B26, B27, D5, D16, D17, E10, G14, J7, J8, K3, K5. Annotated: A6, E3, K2. The H intro (platforms, GUI, Stata version), the I summary and the C intro served-cost sentence are recorded on the DROPIN rows (R58-6).
- **Residuals.** DROPIN P2.42-P2.92 (P2.46 and P2.49 written closed), the notes on existing items, and the platform package above.
- **Documented differences.** tsnatscale floors; the plot-margin tolerance (a build-time fraction, up to ~0.8%% of the width); date panel titles in dash's date text; the CSP level 1 blank page; date literals and bases past the browser's dates (|ms| > 8.64e15) left out with a note (those outside 0100-9999 are drawn, ratification row 12; control codes mirror twoway, row 8); zyx2rule drawn as stcolor; twoway's split of quoted value labels into lines; S12's three error-code differences; S34's `scheme(NAME.scheme)`, cwd-only `dash-` names, refused paths, unfollowed links.
- **Python floor (K15) and bokeh window.** Python 3.11 (measured by the floor matrix, S05; no gate leg, ratification row 25); bokeh 3.8 to <3.10, verified on 3.8 and 3.9 (3.10 not verified, S41). The floor certification run (S05's AC-05.4, deferred at closeout) passed 09oct2026 at fad7f4c: `make cert` under arm64 Python 3.11.17 with the stata pins, 68 of 68 scripts in 688 s, no SKIP, PYF-03 and PYF-04 PASS.
- **Fixtures.** 49 files changed, 699,687 insertions, 21,859 deletions under test/fixtures (c96facd..HEAD).
- **Tests flipped.** 565 `Flipped:` lines; every node, or its renamed successor, collects.
- **Security.** G9 is held by `test/test_csp_browser.py` and `test/test_csp.py` (both modes block an injected inline script; hashes and nonce), the Windows opener cases SB-21..SB-30 of `test/test_serve_browser.cscript`, `test/test_note_channel.py` and `test/test_served_notes.py` (escaped notes, no internal paths, bounded relay), `test/test_label_sinks.py` and `test/test_graph_text.py` (TeX inert, hostile SMCL bounded, control codes escaped), `test/test_scheme_lookup.py` (name, containment, regular-file and size guards), `test/test_region_truth.py`, `test/test_ts_operators.py` (no user text reaches `_stata()`), `test/test_bokeh_internals.py` (internals fail closed), `test/test_served_resources.py` (session cap, idle close, busy page) and `test/test_served_worker.py` (the worker's thread safety).
- **Runs.** make test under Stata's Python (/opt/anaconda3/bin/python3): 21,120 passed, 5 xfailed, 0 failed, 459 s, after ab21a4d fixed the test side for pytest 8.4 and bokeh 3.8 (the first run: 3 failed, 113 errors, all test-side); make test-dev: 21,120 passed, 5 xfailed, 423 s; the release tier: 207 passed. make cert: 68 of 68 registered scripts passed on three sessions, no SKIP and no FAIL, verdict PASS, 410 s wall (WP-29: 907 s for 67 scripts on one session; the WP-30 baseline was not measured). The 57 WP-30 truth blocks, sharded across the sessions, all closed and passed: 399 s summed; slowest S21 53 s, S11 28 s, S19 25 s, S30 21 s, S07 20 s. No raw `dash_render.py:<n>: UserWarning` line in the certification logs (X4-d; 87 in WP-29's). make gate: 12 of 12 examples and 26 of 26 scheme pages clean, verdict PASS. Logs: .ultraplan/handoff/wp30-*.log.
- **Measurements** (StataNow 19.5, auto.dta; c96facd → HEAD): a saved page with `$$x^2$$` in its title 3,087,235 → 1,437,796 bytes, no longer shipping bokeh-mathjax (2 → 0 references; 10 bytes over its plain-word page, 1,437,786); the plain-word page 1,301,201 → 1,437,786; by(rep78) 1,331,043 → 1,485,775; 100,000 rows of scatter plus lowess 7,215,975 → 7,307,470. Render times: TeX title 1.73 → 2.11 s (each run's first build, so it carries Python's start), plain 0.24 → 0.08 s, by(rep78) 0.38 → 0.25 s, 100k scatter plus lowess 27.4 → 27.0 s. Served: `/health` answers within 1.0 s during a 100k-row recompute (test_served_worker.py::TestTheLoopAnswersDuringARecompute, passed; the value is asserted, not printed). Per-session RSS growth has no bound (removed 09oct2026 by the maintainer's decision; P2.57 note).
- **Compare against main.** main..wp30-p1 changes 605 files, 2,346 symbols and 505 processes (risk critical, as a whole package is); the path guard, the version pin (`version 16.0` 0 and 0), the floors and the tracking readers pass; the inventory prints 56 of 56, 2 extra closed, 3 open, 0 problems; the message check prints 0 apart from 8a874b1, and 0 on the added lines of BUGS.md, CHANGELOG.md and both help files.
- **Not measured.** Linux, Windows, Intel Mac and GUI Stata (M4); Stata below 19 (M2).
- **AGENTS.md.** 38 invariants under "Invariants introduced by WP-30".
- **Excluded from the message check.** Commit 8a874b1 ("Updated CLAUDE.md to try to deal with the test suite issues.") is the maintainer's own commit on wp30-p1; it stages CLAUDE.md and names it, and the maintainer accepted it, so the E13 check excludes it. History is not rewritten.
- **Merge.** `git checkout main && git merge --no-ff wp30-p1` -- reported, not run.

## WP-31 · Close the GAPS3 drop-in gaps — DONE

**GAPS3 closed:** A1, A2, A3, A4, A5, A6, A7, A8, B1, B2, B3, B4, B5, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17, C18, D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14, D15, D16, E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12, E13, F1, F2, F3, F4, F5, G1, G2, G4, G5, G6, G7, H1, H2, H4, H7, I2, I4, I5, I6, I7, J1, J2, J3, J4, J5, J6, K6; partly: G3, H3, H6, I3, K2, K3, K4 · **Severity:** S1 (3), S2 (27), S3 (64) · **Effort:** XL · **Depends on:** WP-30

As a Stata user who pastes a twoway command or do-file into dash, I want every twoway plot type, option and default the drop-in audit of 10oct2026 (GAPS3.md) found missing or different to draw as twoway draws it, or be refused or noted in twoway's words, in the saved page and the served app and after any filter move, and the package to install, document and test itself as a release, so that a dashboard reads as the Stata graph it came from (.ultraplan/sections/index.md).

### Business requirements

Summarised from the decision record of .ultraplan/sections/index.md (M1-M25) and .ultraplan/review/DECISIONS.md (D1-D38, A11-A34), which hold them in full.

- **Scope (M1, M2).** Every twoway-facing GAPS3 row, the documents, the tests, packaging basics, accessibility (K6) and the dashboard extensions (H2); the platform package stays deferred and the renderer is not split. Done means every in-scope row is closed with a BUGS.md entry and a pinning test, and the full pytest suite, `make cert` and `make gate` are green at the closeout.
- **contour and contourline (M3, D4, D26, D27).** twoway's interpolation and grid rule, exact up to 1,000 unique points with a live refit in both modes; above the cap a seeded 1,000-point subsample on a 100x100 grid with the stale cue and a note.
- **Refusals (M4, M5, D5, D13, D23).** sunflower and matamatrix() refused by name; options on types that do not take them, the abbreviation superset and misplaced date literals refused with twoway's return code and words, measured; `dash twoway ...` refused as `twoway twoway` is; each newly refused form has a CHANGELOG Changed behaviour line.
- **Tests and truth (M6, M9, M13, M24, M25).** Pinned pictures are flipped with the reason, never deleted; one truth script with a block per section; Stata truth only from committed extract scripts; both twins for computed work against one fixture, with a parity entry.
- **Modes (M8, M14, M16).** A difference the saved page cannot avoid shows a visible cue; new drawing code lives in the shared glyph layer the server copies; all eleven estimators have a JavaScript twin pinned to Python.
- **Cost and security (M10, M11, M22).** New computed layers under 2 s for 100,000 rows (lowess measured at 10,000, D11); no security guard weakened, new HTML and JS through the nonce and hash paths; no new Python dependency.
- **Fidelity (M7, M15, M17, M21).** Scheme files in RGB and Stata's RGBA syntax; a drawn option leaves the pending list, the help's Unsupported section and TWOWAY_COVERAGE_AUDIT.md in the same commit; what Bokeh cannot express is documented with a measured example; minor-tick labels drawn.
- **Release (M18, D8, D38).** Version 0.1.0 dated at the closeout is the release; distribution from GitHub (`net install` from https://wbuchanan.github.io/dash), with Author, Support and KW lines in dash.pkg.
- **Accessibility and extensions (M19, M20).** Keyboard-reachable widgets, ARIA names on every filter, KPI card, tab and figure, scheme contrast checks, axe-core over the pages; per-graph data tables, KPI weights and statistics, multi-select, "(missing)", slider direction, reset, link groups, brush-as-filter, a print stylesheet.
- **Tracking (M12, M23).** GAPS3.md section 9 carries one Tracked line per entry; GAPS2.md and DROPIN-REMAINING.md stay read-only; a residual is an open BUGS.md entry, a GAPS3 Tracked line in the Partly form and a hand-back note.

### Measurements

Measured at the closeout, 18oct2026, on s3-bugs (StataNow 19.5 MP, macOS arm64).

- **Entries.** 143 WP-31 entries (110 at the plan, A12, and 33 added by D14-D36); 87 GAPS3 rows closed and 7 partly closed; `WP31_OPEN = {}` behind `TestWp31Tracking::test_no_wp31_entry_remains_open` and `::test_no_gaps3_line_is_open`. BUGS.md holds 10 open entries, none S1 or S2: the 8 WP-31 residuals below and 2 older S3 entries.
- **Full pytest suite** (`python3 -m pytest test/ -q`, 8 workers, the development interpreter): 27,473 passed, 8 skipped, 5 xfailed, 0 failed, 2,469 subtests, 898 s (15 min 7 s wall).
- **Certification** (`make cert`, three sessions): 69 of 69 registered scripts passed, no SKIP, verdict PASS, 804 s wall (13 min 24 s); the shards' scripts summed 802 s, 640 s and 685 s (test_wp30_truth's parts 200-203 s each, test_wp31_truth's 126 s, 156 s and 174 s). The shard table and test_wp31_truth's block seconds (`w31_secs`, 54 blocks, 458 s) are written from this run.
- **Release gate** (`make gate`): 14 of 14 examples and 26 of 26 scheme pages clean, the venv-linked sessions clean, verdict PASS, 105 s.
- **Accessibility.** axe-core 4.12.1 reports 0 violations on the 14 example pages the gate built (`DASH_STRICT=1 DASH_TEST_TIER=release python3 -m pytest test/test_accessibility_axe.py -k examples`: 14 passed), after S61.4 fixed the fetch race the first run hit (12 passed, 2 errors, no violation).
- **Contour at the cap** (S23, S29): 1,000 unique points solve in 0.01 s and evaluate on a 100x100 grid in 0.04 s; the exact grid of up to 10^6 nodes takes about 4 s at worst; a saved-page move at the cap takes about 13 s (D26).
- **Whole batch-end run.** 1,807 s for the full suite, `make cert` and the gate in turn (batch 20: 957 s and 802 s, 1,769 s); CLAUDE.md rule 11's five minutes is a residual below.

### Residuals

- **The axes of degenerate or emptied layers after a move** (GAPS3 H6; BUGS.md "Found by the move-parity extension: axes of degenerate or emptied layers after a move").
- **The parity guard's uncompared surfaces** (H6; "Parity guard: the surfaces it does not compare"): multi-move, bs under 992 px, runtime notes, PNG/SVG/CSV bytes, ado-path schemes, launched-process behaviour.
- **A renderer without its source file** (K2; "A renderer without its source file cannot write a served app").
- **Truth fixtures awaiting regeneration** (K3): 50 PENDING_META fixtures and the scheme visual truth.
- **Harness guards** (K4): the dispatch count, the scheme-key enumeration, the CSS guard's served arm, the tracking counts and two strict xfails.
- **Served build on the event loop** (H3).
- **The binary data file** (G3b, past WP-31 by D36; "The data file embeds numbers as JSON text (about 0.5 GB per million values)").
- **Hash-pinned installs** (I3, D38; "dash_setup installs by version, not by hash").
- **The suite's five-minute target** (CLAUDE.md rule 11): pytest's critical path is a few served-mode probes that each run alone on one worker -- test_size_units.py's TestStataRatios label offsets and sizes (212 s and 192 s), test_bare_intensity.py (93 s), test_by_text.py's three served probes (66-67 s each), test_added_text.py (62 s), test_intensity_blend.py (59 s), test_by_axes_keys.py (40 s each); the certification run is bound by test_wp30_truth.cscript (567 s over three parts) and test_wp31_truth.cscript (456 s); splitting the served probes per case and trimming the truth scripts' repeated renders are the candidates.
- **Expected by the index.** Legend text before its symbol (M17); contour above the cap (subsample, D4); the platform package (I1); the module split (K5); the served-key and private-file design residuals (H5).

---

## WP-32 · The D39 follow-ups — DONE

**Ruling:** DECISIONS D39 (18oct2026): fix every WP-31 leftover that can be fixed, and change D-15f, D-53d, D-53e, D-30.c, D-31.a and D-37.a to twoway's behaviour.

- **Drawn as twoway draws them.** Legend keys at symxsize() by symysize(); framed title boxes padded by their margin; colorvar() on a line split into twoway's levels (continuous and zscale(log)); graphregion(margin()) follows a resize and insets a by() array; axes of empty layers and of fits that draw no point; the colour key's ring, text() alignment(), the scheme's minor tick count and by_legend_ring; meta's legend without an outline.
- **Exports and serving.** Open data tables in the whole-dashboard PNG/SVG; printing prints every tab fitted to the page; a .pyc-only renderer writes a served app; a served session is built off the event loop with library warning filters serialised and a brush kept through a waiting move; the served page shows the stale cue for a fit drawn from Stata's points.
- **Guards and truth.** The parity guard compares multi-move sequences, runtime notes, layout(bs), export bytes, ado-path schemes and the launched app; the 50 pending fixtures are regenerated by `make truth`; the scheme visual truth covers all 26 schemes and a histogram; the K4 harness guards are in.
- **Second round (19oct2026, the maintainer's "fix the remaining bugs"):** legend_span and legend(span), spanned titles and by()'s legend, titles, colour key and panel sizes placed as twoway places them; the binary data file (G3b) and a hash-pinned dash_setup lock at the tested versions (I3); bokeh serve documented as on the loop, dash serve the supported path; the pre-WP-31 "drew nothing" notes and mixed-list naming; every option twoway refuses refused, every option twoway draws drawn (sort order, contour heatmap/outlines, mwidth, baroffset, named styles), every option twoway takes silently taken silently; play() and a bare replace refused as twoway refuses them (saving(f, replace) instead, maintainer ruling); colour keys, levels and bins re-levelled over the kept rows after a move (overriding WP-29 BR-07.4).
- **Left open (BUGS.md, with reasons):** three natscale misses of 264 axes after a move (Stata's natscale is a compiled built-in; open after a filter move only -- at build every axis is asked of Stata since WP-34 AX-3).
- **Gate (18oct2026):** `make test-all` -- pytest 37,557 passed, 5 failed, 9 skipped (995 s); cert 68 of 69 (test_wp31_truth U39-08). The five pytest failures and U39-08 were merge interactions fixed and re-run green; one was a sub-second timing test that passes alone.
- **Gate (19oct2026):** `make test-all` -- pytest 38,224 passed, 6 failed, 11 skipped (1,562 s); cert 68 of 69 (test_wp31_truth U29-4). The six pytest failures and U29-4 were merge interactions (guards, a pin, an orphan scan that missed `_dash_pend` dispatch, the node harness writing sources back as lists), fixed and re-run green; test_dual_axis's one-pass timing passes alone. The suite now takes about 40 minutes wall, past CLAUDE.md's five-minute target.

## WP-33 · Verification corpus and README gallery (P13) — DONE

**GAPS4 closed:** TR-2, TR-11, TR-23, BY-23, BY-24, stat:PT-23, CV-16, syn:SD-20, GW-11

As the maintainer, I want every twoway example in the help files, the graphics manual, examples/ and the drop-in audit compared with dash's picture by geometry and colour, each difference explained by a known item or counted as unexplained, so that later work packages are measured against a recorded baseline and the closing gallery can show twoway's picture beside dash's.

### Business requirements

Summarised from .ultraplan/sections/index.md (M1-M14, PD-1..PD-18) and .ultraplan/review/DECISIONS.md (P4-1..P4-10, A-1..A-28, P5-1..P5-3, D42-D54), which hold them in full.

- **Tracking (M4, PD-1..PD-6).** GAPS4.md registers the audit's items (221 at the start; 231 after the rows the batches measured: syn:SD-20a..e, BY-24a, BY-32, MS-15, syn:SD-22, CV-17), each with a BUGS.md entry; one truth script per work package from a shared template.
- **No size cap (P4-3).** The embedded-cell and page-bytes caps are removed in both modes; every count cap stays and is documented.
- **The corpus (M5, P4-2, D52).** One example per combination of plot types and option names; each run on the data its variables come from; only what twoway accepts is compared, and fragments whose variables no shipped dataset holds are dropped and listed.
- **Verdicts (PD-14, A-4, A-25, D46-D51).** Geometry decides: axes and their scale, ticks, labels, titles, legend, glyphs, colours, text size, margins, marker size, line width, marker labels and outlines; the maintainer labelled the 32 calibration pairs (D49: no pair is Same, every one differs in text size, margins and marker or line size, owned by VF-4 and GW-6); the ledger keys each known difference by its GAPS4 item.
- **Gallery (P4-1, P4-8, PD-12, PD-13).** dash image panels and graphs registered under Stata's frame prefix make the per-plot-type gallery pages possible; the gallery and the README block are built only at WP-50's closeout.
- **Guard (M5).** Twenty-one corpus examples are compared in every certification run (Q3309-1).
- **Suite speed (22oct2026, the maintainer).** The gate records where its time goes (timing.txt); heavy served comparisons check a representative subset at the gate and every probe in the release tier; long probe loops are split; the closed WP-29/30/31 truth scripts run in the release tier and at each work package's closeout (`make cert-all`). The gate went from 2,062 s to about 1,260-1,560 s, still past the five-minute target.

- **Baseline (Q12, approved 24oct2026 after D56-D58).** test/fixtures/corpus_baseline.json: the run of 23oct2026 at e8cf4e4, 339 examples compared, 0 Same, 284 Close, 55 Differs, 0 skipped as approved, 285 Close and 54 Differs once CV-17's ledger rows explain ex-feature_tour-eaf70b99 (first recorded 22oct2026: 0 Same, 235 Close, 104 Differs); 87 fragments dropped for want of a dataset; dash refuses 3 that twoway draws.
- **Entries.** 9 WP-33 entries; 9 closed, 0 documented, 0 partly closed; BUGS.md holds 222 open entries.
- **Left open:** none of WP-33's items. The batches registered nine measured differences for later work packages (D42, D44, D48, D50, D54).
- **Gate (22oct2026):** `make test-all` -- pytest 39,112 passed, 1 failed (1,051 s; a two-second timing bound under a loaded machine, converted to a ratio check in 6d07e30 and re-run green); cert 67 of 67 (506 s). `make cert-all` -- 70 of 70 passed.

## WP-34 · Default drawing of common graphs (P1) — DONE

**GAPS4 closed:** AX-4, AX-2, AX-1, VF-2, VF-3, PIC-1, PIC-3, TR-4, DG-3, AX-3; **partly closed:** plot:PT-13

As a Stata user who pastes a common twoway graph into dash, I want its axes, ticks, labels, frame and default outlines drawn as twoway draws them, in the saved page and the served app and after a filter move, so that the everyday graphs look like Stata's without any option.

### Business requirements

Summarised from .ultraplan/sections/index.md (M6) and .ultraplan/review/DECISIONS.md (A-1, A-6, A-16, A-18, A-19, D41, D55), which hold them in full.

- **Ticks (M6, A-16, A-19).** Every count axis is asked of Stata as the page is built, in both modes: by() panels at their own count, histogram bin axes over their bin midpoints, range() widening an axis but not its ticks, a date axis over the rows each series draws, colour keys included; the zero label is `0`. dash's natscale model draws only after a filter move or for a page rendered outside Stata (D41 keeps those misses open).
- **Frame (M6, A-1, D55).** aspectratio() with xsize()/ysize() draws the exact frame, never 0 px, counting the graph's title; a by() graph's shared y title is painted at its full height.
- **Defaults (A-6).** An area plot is outlined all round as twoway outlines it, with its key; a ci fit with nofit counts as one plot, so the layers after it take twoway's colours.
- **Time-series operators (PD-16, D41).** Re-measured first: all 99 earlier probes gave twoway's 18oct2026 answers and the 22 new ones the expected codes.

- **Entries.** 11 WP-34 entries; 10 closed, 0 documented, 1 partly closed; BUGS.md holds 215 open entries.
- **Left open:** the natscale model's after-move misses, the residual of plot:PT-13 (BUGS.md "The natscale model misses three of the 264 axes twoway drew"). The batches also registered AX-19, AX-20 and PIC-17 (34-07's measured rows rules) for WP-44 and WP-47.
- **Gate (26oct2026):** `make test-all` -- pytest 39,625 passed, 2 failed, 1 skipped (902 s; two help pins 34-09's wording moved, fixed in 767b4e0 and re-run green; the skip was ruff missing from a changed PATH, run green with ruff found); cert 68 of 68 (461 s). `make cert-all` -- 69 of 71 (the closed WP-29/31 truth readers counted 34-05's area outline ring; fixed in 2de7cc9 and those blocks re-run green).

## WP-35 · Accepted syntax and refusals (P11, with P4's remaining items) — DONE

**GAPS4 closed:** MS-1, syn:SD-3, stat:PT-7, syn:SD-5, stat:PT-13, syn:SD-20a, syn:SD-20b, syn:SD-20c, syn:SD-20d, syn:SD-20e, stat:PT-6, stat:PT-9, syn:SD-7, basic:PT-8, syn:SD-8, GW-2, GW-3, GW-4, sil:SD-8, stat:PT-1, stat:PT-2, stat:PT-5, stat:PT-8, stat:PT-14, basic:PT-9, basic:PT-13, DT-15, DT-19, plot:PT-3, plot:PT-4, syn:SD-1, syn:SD-13; **documented:** syn:SD-22

As a Stata user who writes a twoway command into dash, I want dash to accept exactly what twoway accepts and to refuse what twoway refuses with twoway's return code and words, so that a do-file behaves the same under either command and a mistake is caught as Stata catches it.

### Business requirements

Summarised from .ultraplan/sections/index.md (M7) and .ultraplan/review/DECISIONS.md (P4-7, P4-9, PD-10, PD-18, A-17, A-20, D42-D45, D53, D54, D59-D63), which hold them in full.

- **Repeated and p#() options (M7).** Options twoway takes rightmost are read rightmost; p1()..p20() are read as twoway reads them, marker() inside them as mstyle() (D62).
- **Statistical types (M7).** The spellings twoway documents are taken; histogram's exclusive options, the scale words off histogram, contour levels() above 500, lowess noweight with weight and bw() off the bandwidth types are refused in twoway's words (bw() with a `use barwidth()` line, P4-9).
- **Values (M7, D59-D61).** A bad value fails with twoway's rc and first line, from a table generated from Stata's answers; dash's own bounds are lifted where twoway draws the value, and widths and angles are bounded only on the types where twoway draws them. aspectratio() at or below 0 stays refused (D59).
- **Dash-only words (P4-7, P4-9, D53).** Every dash-only spelling of a twoway option is refused with twoway's words and a line naming twoway's spelling; hover() and table are kept and listed in one help paragraph.
- **Graph options and grammar (M7, PD-10, D54).** Graph-option refusals, omit pairs, maxaxes and the command grammar copy twoway; contour levels() leniency is documented (syn:SD-22).
- **Working columns (A-17, A-20).** dash's working columns take a prefix no variable of the data uses, and are made in a frame when c(maxvar) leaves no room; the in-place export keeps e(sample).

- **Entries.** 33 WP-35 entries; 32 closed, 1 documented, 0 partly closed; BUGS.md holds 182 open entries.
- **Left open:** none of WP-35's rows. barwidth(-2) is drawn at the default width (Bokeh draws no negative width; twoway draws bars outside the axis), and `histogram ..., bin(0) width(2)` gives the pair's r(198) before twoway's r(125); both are named in their BUGS.md Resolutions.
- **Gate (27oct2026):** `make test-all` -- pytest 39,766 passed (814 s), cert 69 of 69 (467 s), 1,291 s in all. `make cert-all` -- 80 of 82 script runs (both failures were parts of the closed test_wp30_truth: PS-31 held jitter(2 200) and LN-27 held scatter lwidth(*-1) and line lwidth(*40000) to dash's answers before basic:PT-13; flipped in 06a9531 and ea04f24, blocks S20 and S13 re-run green).

## WP-36 · Python discovery and environment (P2) — DONE

**GAPS4 closed:** plat:PT-1, plat:PT-4, DG-14; **documented:** plat:PT-5, plat:PT-2, plat:PT-11, plat:PT-12, plat:PT-6, plat:PT-16, plat:PT-14

As a Stata user installing and running dash, I want it to use the Python Stata already runs, to draw large and dashed graphs correctly, and to say plainly where it has been tested and what it needs, so that a working Stata setup is enough and I know the limits before I meet them.

### Business requirements

Summarised from .ultraplan/sections/index.md (M8) and .ultraplan/review/DECISIONS.md (A-2, A-7, A-8), which hold them in full.

- **Python discovery (M8, A-8).** No pre-check of Python: with c(python_exec) empty, dash and dash_setup run the normal python: path, so Stata picks its own Python, and a Python that cannot start shows Stata's message followed by dash's advice. No script in the harness skips for want of a Python setting; a release-tier test starts Stata with a fresh HOME to prove it.
- **WebGL (M8).** A dashed line keeps its figure on the canvas backend, and the switch to WebGL counts the rows the graph draws, not the dataset's.
- **Function points (A-7).** A named graph's function points are kept in a private file under dash's temp folder, keyed by graph name, so c(macrolen) no longer caps them.
- **Environment, documented (M8, A-2).** The help, README and package description state the tested platform (macOS arm64, StataNow 19.5, run from the console), that the drop-in claim is for Stata 19 and later, the full dependency list, the lock's Python and platform coverage, saving()'s tilde rule, Chrome as the tested browser, and the measured large-data cost (about 8 s cold, 6 s warm, 1.5 GB of Stata memory and a 48 MB page per million rows). The existing tested-release sentences are unchanged.

- **Entries.** 10 WP-36 entries; 3 closed, 7 documented, 0 partly closed; BUGS.md holds 172 open entries.
- **Left open:** none of WP-36's rows. Registering a graph with a function layer now starts Python (36-03 accepts this).
- **Gate (29oct2026):** `make test-all` -- pytest 39,783 passed (842 s), cert 70 of 70 (495 s), 1,347 s in all. `make cert-all` -- 73 of 73 registered scripts passed (3 sessions, all tier).

## WP-37 · Statistical and computed layers (P12) — DONE

**GAPS4 closed:** DG-1, DG-5, DG-8, TR-13, TR-13a, stat:PT-12; **documented:** stat:PT-16, DT-26, stat:PT-21

As a Stata user drawing fits, areas and contours, I want dash to compute them as twoway does -- an empty sample answered as twoway answers it, a fit on the transformed x, a gridded contour from twoway's own generator -- and to say plainly where its numbers part from twoway's, so that a twoway command draws the same picture in dash.

### Business requirements

Summarised from .ultraplan/sections/index.md (M9) and .ultraplan/review/DECISIONS.md (A-12, A-26, P5-1, P5-2, D45, D64, D65), which hold them in full.

- **Zero observations (M9, PD-15, P5-2).** One check runs on every export route, after the working columns and before Python, and answers each plot type and empty-sample case as twoway does (400 measured probes); a contour over no rows draws an empty plot with its key's title instead of a Python traceback.
- **Fits on a transformed x (A-12, P5-1).** lfit and lfitci with xlog or xtransform() draw twoway's own fit (twoway__lfit_serset with xtrans()), once per by() panel; every Stata-computed fit under by() is fitted per panel.
- **Areas and contour keys.** rarea's outlines break where cmissing(n) breaks its fill, in both modes and after a filter move; a contour with no surface still draws its colour key.
- **Contours from Stata's grid (M9, A-26).** A gridded contour or contourline, or one with interp(none), is cut by twoway__contour_gen at export, flat, per by() panel and for the Total panel; after a filter move that drops rows the layer is refitted by dash and marked stale.
- **outlines (D64).** contour's outlines option reaches the renderer and draws as twoway draws it: the colour key's boxes outlined, the plot region unchanged (TR-13a, filed during the WP).
- **Option removed (D65).** contour and contourline refuse the option the maintainer removed, r(198), as any option they do not take; the two-contour refusal reads "multiple contour or patch plots not allowed".
- **Documented (D45).** lpolyci's band where the pilot has no residual degrees of freedom, the estimators' numeric limits (lpoly's bandwidth at degree 2-3 within 5e-6, 6-7 and above 7, exact-polynomial cases, fpfit on dates, the 2,000,000-dot limit) and tied sort keys keeping the data's order each have a help sentence with its measured numbers and a Differences entry.

- **Entries.** 9 WP-37 entries; 6 closed, 3 documented, 0 partly closed; BUGS.md holds 164 open entries.
- **Left open:** none of WP-37's rows.
- **Gate (30oct2026):** `make test-all` on dc758d6 -- pytest 40,026 passed and 1 failed (a timing ratio under load, made best-of-three in a31c6d9 and green alone), cert 71 of 71 (511 s), 1,445 s in all. `make cert-all` on a16b0d6 -- 74 of 74 registered scripts passed (3 sessions, all tier).

## WP-38 · Stata graph integration, documented (P3) — DONE

**GAPS4 closed:** none; **documented:** syn:SD-17, GW-12, ECO-1, ECO-4, GW-13, GW-14, GW-15, GW-16, GW-9, ECO-5, ECO-15, ECO-7

As a Stata user who builds dashboards beside twoway's graphs, I want the help to say plainly that a dashboard is not a Stata graph, and to give each return code and message where dash's registry answers differently from twoway's graph memory, so that a do-file written for twoway does not surprise me in dash.

### Business requirements

Summarised from .ultraplan/sections/index.md (M10) and .ultraplan/review/DECISIONS.md (A-17), which hold them in full.

- **A dashboard is not a Stata graph (M10, 38-01).** A new help topic says what name() and saving() do in dash, that graph export/save/display/combine, putdocx, putpdf, putexcel, dyndoc and markdown cannot use a dashboard, that a registered graph draws the data in memory at dash build, how dash build's layout() stands in for graph combine, which s() macros dash leaves, and when a browser page opens; each has a Differences entry.
- **The registry's answers (M10, 38-02).** A second topic sets out name()'s limits, saving() onto a file that exists, nodraw with saving(, asis), play(), name()'s sub-options and dash clear, each beside twoway's measured rc and words, with a sub-point under Differences item 2.
- **Measured, not assumed.** twoway's answer to nodraw with saving(, asis) depends on what the session drew before; the help gives the fresh-session answer, measured by scripts/extract_graph_export_truth.do, and the case after a drawn graph is dropped.
- **No code change.** Every row is resolved by help text and the tests that read it.

- **Entries.** 12 WP-38 entries; 0 closed, 12 documented, 0 partly closed; BUGS.md holds 152 open entries.
- **Left open:** none of WP-38's rows.
- **Gate (30oct2026):** `make test-all` on 4b24ca7 -- pytest 40,069 passed, cert 72 of 72 (503 s), 1,376 s in all. `make cert-all` on 4b24ca7 -- 75 of 75 registered scripts passed (3 sessions, all tier).

## WP-40 · Resource limits (P5) — DONE

**GAPS4 closed:** plat:PT-7; **documented:** plat:PT-8, plat:PT-9, plat:PT-10, stat:PT-15, sil:SD-1, AX-16, sil:SD-11, sil:SD-12, sil:SD-13

As a Stata user with large or wide data, I want a subset of my data to build as quickly as twoway draws it, and every limit dash keeps to be stated beside twoway's answer, so that a refusal, a trimmed graph or a slow build is never a surprise.

### Business requirements

Summarised from .ultraplan/sections/index.md (M10, Q44, Q45) and .ultraplan/review/DECISIONS.md (P4-3, A-12, A-18), which hold them in full.

- **Only the drawn rows are exported (Q45, P4-3, A-12).** On the one-line form and on a saved `dash build` with no filter(), link(), brush(), csv or KPI card, dash evaluates the qualifiers first and exports only the rows some graph draws (`dash scatter y x in 1/100` on 200,000 observations exports 100); the user's frame is never reduced, every graph draws what it drew before, and a served app or any other build exports every row. Each graph's JSON carries its frame's `_N` as `"n_obs"`, so lpoly's grid keeps twoway's count (50 points over 22 cars) at build and after a served filter move; a by() graph keeps every row of its own sample, so each by() group keeps its panel; a lowess layer with adjust keeps every row; a frame stack with no room for the selection column exports every row.
- **No size limit, count limits documented (M10, Q44, P4-3).** The help says that dash, like twoway, sets no limit on the size of the data or of the page, and that no image is limited by its file size; a new Differences item lists every count limit with its default and global, and Resource limits states twoway's answer beside each.
- **Fixed limits (A-18).** A new Fixed limits paragraph states n() and bin() bounds by type (mspline 300, as twoway refuses it; 10,000 on the other bounded types; lfit, qfit, lfitci, qfitci and fpfitci take any n()), lpoly's fit degree of at most 30, histogram rebinning above 1,000 bins, the 2,000-tick limit and the 256 axis ranges a build asks Stata's tick routine for, the 1,000-unit marker size, fpfit's 20,000-point grid and the 4,000-character text limit, each beside twoway's measured answer; the msize "any number" and discrete "one bar per distinct value" sentences are corrected.

- **Entries.** 10 WP-40 entries; 1 closed, 9 documented, 0 partly closed; BUGS.md holds 142 open entries.
- **Left open:** none of WP-40's rows.
- **Gate (30oct2026):** `make test-all` on cc50c88 -- pytest 40,233 passed, cert 73 of 73 (514 s), 1,431 s in all. `make cert-all` on cc50c88 -- 75 of 76 registered scripts passed (3 sessions, all tier): test_wp29_truth ER-02 found a by() graph losing the panel of a group no plot had a row in under the selected-row export; fixed in 17ea7fd (a by() graph marks its own rows), and test_wp29_truth and the S01 block pass on it.

## WP-41 · by() fidelity (P6) — DONE

**GAPS4 closed:** BY-28, BY-1, BY-24a, BY-2, BY-27, BY-3, BY-4, BY-5, BY-6, BY-32, BY-12, BY-13, BY-14, BY-16, BY-18, VF-6, GW-5, sil:SD-7, PIC-13, BY-7, TR-19; **partly closed:** BY-10; **brought forward from WP-45 and partly closed there:** VF-4, GW-6

As a Stata user who draws by() graphs, I want each panel, its labels, its shared axes, keys and titles laid out as twoway lays them, and every by() option twoway honours honoured or refused in twoway's words, so that a by() dashboard reads as the graph twoway draws.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-41) and .ultraplan/review/DECISIONS.md (A-1, D48, D66, D67), which hold them in full.

- **Panels share what twoway shares (41-01, 41-03).** contour under by() takes one z axis across panels; a scale() outside by() is ignored and by(, scale()) applied; function range(varname) and a weighted layer read each panel's own rows, a panel whose weights are all zero stopping with r(198) as in twoway.
- **Titles, notes and keys where twoway puts them (41-02, 41-04).** ring(0) note(), caption() and subtitle() are drawn, l1title() and b1title() replace the shared axis titles, at() holes are kept for undrawn keys, legloc()/clegloc()/plegend()/plegloc() place their keys, a legend in a hole takes by()'s 0.85 text, and coloruseplegend with plegend(at(#)) is refused r(4019) as twoway refuses it.
- **Panel labels (41-06).** justification(), nobexpand, lwidth(), lpattern(), span, alignment(), linegap(), bmargin() and placement() are drawn; dates are written as twoway writes them.
- **Layout and shape (41-05, with WP-45's VF-4 and GW-6 brought forward, D66, D67).** Every graph keeps twoway's shape with no height band; every size scales with the drawn width as one picture; a page has one toolbar laid over the graph; the scheme's graph margin surrounds the graph; a row's y axis is drawn once, at the panels' size, so every panel in a row has the same plot width; compact panels touch and are outlined; style(combine) draws graph combine's regions, ticks and titles; x labels are drawn only on panels with none below, as twoway draws them.

- **Entries.** 22 WP-41 entries; 21 closed, 0 documented, 1 partly closed; BUGS.md holds 127 open entries.
- **Left open:** BY-10's orientation() (BUGS.md "A by() panel label's orientation() is named, not drawn"); by(, subtitle(, position(3))) label placement and plot widths (BUGS.md "by(, subtitle(, position(3))) panel labels sit right of their strips and the two plot regions are narrower and unequal"), deferred by the maintainer on accepting the 41-05 screenshot pairs (01nov2026); VF-4's and GW-6's residuals, filed under WP-45, among them the corpus guard's help-added_text_options-0a48288d plot region (BUGS.md "A line graph with a title, subtitle, note and a boxed text() has a wider plot region than twoway's", measured 02nov2026).
- **Gate (01nov2026):** `make test-all` on a3d132d -- pytest 40,766 passed and 9 failed (626 s; the suite was cut from 2,344 s by 09c369f..9243eb4), cert 74 of 74 (531 s), 1,157 s in all; the nine were fixed in 041d05a (a copied conftest runs without the new memory guard), 776708a (an unused import) and 37caf94 (a fake Popen counted another test's thread), and their files pass. `make cert-all` on a3d132d -- 76 of 77 registered scripts passed (3 sessions, all tier): test_wp31_truth U39-08 read margin(large)'s inset against the whole padding GW-6 now draws; fixed in 2a39b77, and block S39 passes on it.

## WP-42 · Colour variables (P7) — DONE

**GAPS4 closed:** CV-8, sil:SD-4, CV-17, CV-1, CV-6, CV-7, CV-2, CV-9, CV-10, CV-14, CV-3, CV-15, LT-12, AX-12, LT-22, CV-8a, CV-4, CV-5, CV-11

As a Stata user who colours a graph by a variable, I want the levels, their colours and the colour key drawn as twoway draws them -- binned at twoway's cuts, keyed on twoway's axis-style key, and every colour option twoway honours honoured or refused in twoway's words -- so that a colorvar() or contour dashboard reads as the graph twoway draws.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-42) and .ultraplan/review/DECISIONS.md (D68, M11), which hold them in full.

- **Levels and colours (42-01, 42-05).** An unbinned numeric colorvar() is binned at twoway's z ticks on every type twoway colours, mono schemes starting near white; colordiscrete colorlevels(k) cuts at range/(k+1); the key is as thick as the scheme's clegend_width; a colorlist() or ccolors() of quoted RGB colours takes each colour whole (CV-17, registered by WP-33's corpus run).
- **Line parts and layers (42-02).** colorfillonly keeps the level colours on lines, spikes, caps and arrows; two colorvar() layers draw the last layer's key and a plot legend; a colorvar layer's plot-legend key is drawn in its series colour.
- **twoway's axis-style key (42-03, M11).** The colour key is swatches beside a z axis, highest at the top, ticked at the natscale ticks or the cuts, its title up its side, no missing entry and no frame; zlabel(), zscale(), the z tick family and clegend()'s sub-options are drawn on it; clegend(title()) is drawn above it; a by() contour draws twoway's one key (D68); contourline keys its levels and follows a filter move.
- **The plot legend and the key (42-04).** coloruseplegend keys the levels highest first, then Other, untitled, in the display format; legend()'s size(), rows() and cols() leave every colour key; colorkeysreverse reverses the key's colours only; colorlevels() over one value cuts at zero width.
- **Refusals (42-05).** colorvar(), colorcuts(), colorlevels() and malformed clegend()/plegend()/zlabel()/zscale() are refused with twoway's rc and words; the documented acceptances are answered as twoway answers them.

- **Entries.** 19 WP-42 entries; 19 closed, 0 documented, 0 partly closed; BUGS.md holds 110 open entries.
- **Left open:** a colorlist() shorter than the levels that starts with a quoted colour (BUGS.md "A colorlist() shorter than the levels that starts with a quoted colour repeats its last colour; twoway gives the unlisted levels the hue rule's colours", measured 03nov2026, S3).
- **Gate (03nov2026):** `make test-all` on 0fdf722 -- pytest 41,412 passed (511 s), cert 68 of 75 (537 s), 1,057 s in all; the seven were readers that predated CV-3's key cell and d088459's graph region box (test_conformance, test_e2e_multi, test_gaps2_truth, test_wp34_truth, test_wp37_truth, test_wp41_truth, test_wp42_truth), fixed in 6757e2c, each passing under the runner. `make cert-all` -- first on 6757e2c, 75 of 78 (test_wp29_truth, test_wp30_truth and test_wp31_truth read the same old models; fixed in 4f51cf0); then on 4f51cf0, 78 of 78 registered scripts passed (3 sessions, all tier, 1,082 s). Before the gate, the full pytest suite on 1491225 had 22 failures, fixed in 9f4ab08.

## WP-43 · Legend, titles and added text (P8) — DONE

**GAPS4 closed:** LT-1, LT-13, LT-15, LT-4, LT-5, LT-17, LT-2, LT-3, PIC-11, MS-10, RH-13, LT-8, LT-9, LT-14, LT-16, LT-19, LT-24, LT-11 · **documented:** LT-7, LT-20, LT-21, ST-14 · **partly closed:** LT-6, LT-10, LT-18

As a Stata user who titles, annotates and keys a graph, I want the legend, the title family and added text drawn as twoway draws them -- the legend's title, place, box, layout and keys, the title boxes and edge titles, and text() -- and every difference dash keeps named in its note and documented in the help, so that a dashboard's text and keys read as the graph twoway draws.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-43) and .ultraplan/review/DECISIONS.md (D69, D70, D71, D72, M11), which hold them in full.

- **The legend's title (43-01, D69).** legend(title()) and subtitle() are drawn in the scheme's leg_title and leg_subtitle styles with their position(), justification() and box through the Legend's own stylesheet (no overlay, D69); the edge titles inside legend() are refused as twoway refuses them.
- **The legend's place (43-02).** ring(0) bplacement() and its abbreviations, legend(all), draw and nodraw, and holes() in a one-column or one-row legend are drawn as twoway draws them.
- **The legend's box and layout (43-03).** nobox is the key texts' option; the key texts' textbox options, style(), width(), height(), xoffset(), yoffset(), showindex, region() styles and every marginstyle form are drawn; bexpand is named and documented (D72).
- **The legend's keys (43-04).** Marker keys at the plot's marker size, angle and width, each key in its column's width, textfirst, stacked and symplacement() drawn, twoway's seven key shapes, keys merged by plot type and pstyle, a turned kdensity keyed by its grid; a long-texted legend kept inside the graph; a legend's own note() and caption() named, not drawn (D70).
- **Title boxes (43-05).** Each scheme's textbox fill and line, real-valued rings, ring(x) refused as twoway refuses it, placement() at ring(0), orientation(), width(), height(), the frame styles, edge titles' boxes, and option text with a stray quote refused as twoway refuses it.
- **Added text (43-06).** text()'s alignment(), fixed boxes, line gaps and frame styles drawn; a global's =exp evaluated only through the listed functions (documented).
- **Markup on part of a text (43-07, D71).** No route ruling D69 allows draws twoway's runs, so a text keeps one style with one note per graph and kind of text, documented as Differences item 15.

- **Entries.** 25 WP-43 entries; 18 closed, 4 documented, 3 partly closed; BUGS.md holds 97 open entries.
- **Left open:** legend(style(zyx2)) (BUGS.md "legend(style(zyx2)) is named; twoway lays the keys in one column at the scheme's zyx2 gaps and key size", LT-6, S3); bmargin() per side (BUGS.md "legend(bmargin()) and a title's bmargin() keep only the largest side; twoway reserves each side", LT-10, S3); angle() with box (BUGS.md "title(..., angle() box) turns twoway's text inside its level box; dash keeps the title level", LT-18, S3); and eight S3 entries filed during the WP, among them the 1.13-text-size key rows, legend(title(, box)) height, by(, legend(pos(0))) and scale() on a title box's padding.
- **Gate (05nov2026):** `make test-all` -- first on 776c193, pytest 2 failed of 42,827 (the help's split bold lead and the Differences items' order) and cert 69 of 76 (readers that predated the LT-21 key proxies, SR-01's stack, Q3307-5's digest after LT-8's scheme textbox colour, and the LT-24 sentence's literal braces), fixed in 1a11e90; then on 1a11e90, pytest 42,827 passed (553 s), cert 76 of 76 (620 s), 1,186 s in all. `make cert-all` -- first on 1a11e90, 77 of 79 (test_wp29_truth and test_wp30_truth read the key proxies as series; fixed in e34bf80 and 90452a8); then on 90452a8, 79 of 79 registered scripts passed (3 sessions, all tier, about 1,197 s).

## WP-44 · Axes (P9) — DONE

**GAPS4 closed:** AX-13, MS-11, MS-13, PIC-12, AX-6, AX-8, AX-14, AX-7, AX-9, AX-10, MS-14, DG-13, AX-19, AX-18, DG-6, DG-4, AX-20, MS-12, DG-9 · **documented:** AX-5, AX-11, AX-15

As a Stata user who titles, labels and scales a graph's axes, I want every axis drawn as twoway draws it -- its titles, its label and tick sub-options, its scale's look and transform, its date labels, and the rows its range reads -- and every difference dash keeps named in its note and documented in the help, so that a dashboard's axes read as the graph twoway draws.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-44) and .ultraplan/review/DECISIONS.md (D73, D74, D75, D76, M11), which hold them in full.

- **Axis titles (44-01).** A title's orientation(), justification(), placement(), box and margin() drawn; a right-hand y title reads upward; a suffix or prefix copy draws a second line; an axis shared by plot regions titled differently takes twoway's "<first title>..." title.
- **Label and tick sub-options (44-02, D73, D74).** Tick-option gridlines in the major grid's look; labelminlen(), showlabels, pgmgrid and style() drawn; tstyle(), labstyle(), gstyle(), tlstyle(), glstyle() and nogextend read from Stata's style files; xtick() and xmtick() at their own lengths and the %21x, %16H and %#s formats drawn; custom's grid edits dropped and its look on every label (D73), reference lines past the scale and the margin after a resize documented (D74).
- **Scales (44-03, D75).** off fill keeps the axis's space; atanh, logit and log1m refused r(199) as twoway's graph fails on them, no transform but log drawn (D75); two transform words in one copy refused r(198); style() read from Stata's axis style file; a log axis ticked over every finite value (documented); range() on a log axis adds no end tick; minmax on an empty scale writes twoway's labels and a span past the largest double is refused r(199).
- **Date axes (44-04).** A date axis kept only where twoway labels dates, a lone fit's in Stata numbers; %tC ticked in raw milliseconds; parenthesised dates with blanks read.
- **Lone second axes and label lists (44-05).** A graph whose every layer is on a second axis draws no gridlines; a non-number in a label list refused as twoway refuses it.
- **The rows an axis reads (WE, D76).** Each variable of a layer read over the layer's own rows, a row its partner misses included, in both modes and in the export's requests for Stata's ticks (AX-19, re-scoped from the registration after measurement); a baroffset() bar ticked over its x and its scale widened half a bar and |baroffset()| bars each way (AX-20).

- **Entries.** 22 WP-44 entries; 19 closed, 3 documented, 0 partly closed; BUGS.md holds 79 open entries.
- **Left open:** an axis title's margin() (BUGS.md "An axis title's margin() widens its slot but leaves the plot where it is; twoway moves the plot by the margin", AX-13, S3); minmax after a filter move to no row (BUGS.md "ylabel(minmax) writes no label after a filter move leaves no row; twoway writes 1.e+300 and -1.e+300", DG-13, S3); gridlines with the first layer on yaxis(2) (BUGS.md "With the first layer on yaxis(2) and a later one on axis 1, the y gridlines follow axis 2's ticks; twoway draws them at axis 1's", MS-12, S3); a bar row whose y is missing (BUGS.md "A bar row whose y is missing joins the x scale without its half bar; twoway spans x plus or minus half a bar over every row", AX-19, S3).
- **Gate (07nov2026):** `make test-all` -- first on 0c888ae, pytest 8 failed of 43,585 (627 s) and cert 75 of 77 (655 s), 1,282 s in all: tests and readers WP-44's batches left stale (the single-y page digest after AX-11's finish JS, the graph-key-list count after 44-03's scale-word loop, the scale look's fill key, the Differences items' numbers, SR-04's logit, Q3307-5's style rows) and the closeout's own (two ruff findings, the served worker's audited names, the new cert blocks' form), fixed in 33c7669; then on 33c7669, pytest 43,579 passed and 6 failed, each a time limit in a run the machine stalled (7,813 s wall against 627 s), each passing alone (9 of 9 in 6 s), and cert 77 of 77 (640 s). `make cert-all` -- on 33c7669, 79 of 80 registered scripts passed (3 sessions, all tier): test_wp29_truth read a lone kdensity and lpoly of a date in epoch ms on a date axis, stale since AX-18; fixed in 1b74868, the whole script then passing alone (107 checks). The suite runs about 21 minutes, over the 5-minute rule (CLAUDE.md 11); the cuts are proposed as their own work.

## WP-45 · Schemes, styles and figure geometry (P10) — DONE

**GAPS4 closed:** PIC-4, PIC-7, ST-1, ST-22, GW-10, ST-7, ST-15, ST-10, ST-17, ST-16, GW-1, ST-21 · **partly closed:** VF-4, GW-6

As a Stata user who draws a graph under a scheme, my own style files and a graph size, I want every scheme directive, style file and style word twoway reads read the same way, and the graph drawn at twoway's proportions with its graph region, margins and outlines, so that a dashboard's graph is the picture twoway draws.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-45) and .ultraplan/review/DECISIONS.md (D66, D67, D69, D74, D77, M11), which hold them in full.

- **economist (45-01).** A graph's note() painted; range, spike, dropline and pc lines at linewidth pother, the rarea outline at parea, inside.
- **Style words (45-02).** compass2dir, tb_orientstyle, clockdir, gridringstyle, anglestyle and connectstyle names and abbreviations read as twoway reads them, refused where twoway refuses them, in twoway's words.
- **Style files and schemes (45-03).** Leaf style files on the ado-path (linepattern, linewidth, symbolsize, gsize, intensity, anglestyle, margin), color and textboxstyle files read; a shipped-name scheme placed before BASE used; clockdir, title textboxstyle, legend_col_gap and the title side clocks drawn; an unknown scheme() noted and drawn as s2color.
- **Colour edges and fonts (45-05).** twoway's intensity rule at its edges; a blank stylelist word read as twoway reads it; graph set's plain-text font face read.
- **Figure geometry (45-04, D66, D67, D69, D74, D77).** Each graph at twoway's shape, xsize()/ysize() in every unit twoway takes, fxsize()/fysize() at the scheme's reference side; the scheme's graph margin drawn round every graph and Bokeh's own border dropped; the graph region's outline stroked unasked, its inner box and lalign() drawn; the plot-region margin a share of the graph's smaller side, fixed at build (D74); plotregion(lalign(inside)) drawn inside the edge and lalign(outside) documented (D77); each title box's room under scale() as twoway's.

- **Entries.** 14 WP-45 entries; 12 closed, 0 documented, 2 partly closed; BUGS.md holds 68 open entries.
- **Left open:** sizes in five corpus guard examples (BUGS.md "Five corpus guard examples draw text, marker or line sizes unlike twoway's", VF-4, S3); an axis's room under scale() (BUGS.md "An axis's room under scale() keeps about 5 px that twoway's does not", GW-6, S3); the margin estimate beside a second axis or a legend (BUGS.md "A lone graph's plot-region margin leaves out a second axis's and a legend's room", ST-21, S3); the economist note's row (BUGS.md "The economist note's row deepens the title band by the box's height; twoway's band holds the title and the note side by side", PIC-4, S3).
- **Gate (09nov2026):** `make test-all` -- first on 5855ea9, pytest 5 failed of 44,500 (583 s) and cert 74 of 78 (679 s), 1,262 s in all; `make cert-all` on 5855ea9, 76 of 81: pins and fixtures WP-45's batches left stale (VF-4's residual ledger rows, the Differences items' order and a sub-point's link, the value refusal table after GW-1, HC8-12 after ST-16, U39-09's comparer after GW-6, Q3307-5's spec digest after GW-10) and one test bug (Q4503-1/2: twoway sees a style file added after a session's first graph only past discard), fixed in 41a4f05; then on 41a4f05, pytest 44,500 passed (682 s), cert 78 of 78 (718 s), 1,400 s in all, and `make cert-all` 81 of 81 registered scripts passed (3 sessions, all tier, 1,233 s). The suite runs about 23 minutes, over the 5-minute rule (CLAUDE.md 11); the cuts are proposed as their own work.

## WP-46 · recast() and horizontal (P14) — DONE

**GAPS4 closed:** RH-1, RH-9, RH-11, RH-3, RH-5 · **documented:** RH-8

As a Stata user who draws a layer as another type with recast(), and turns it with horizontal, I want recast() read, refused and drawn as twoway reads, refuses and draws it, so that a recast layer on a dashboard is the layer twoway draws: turned where twoway turns it, with both bounds of a range on its axis, title and key, and a recast histogram in the histogram's own style.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-46) and the section decisions D-46-01.a..e and D-46-02.a..g, which hold them in full.

- **Orientation (46-01).** horizontal and vertical judged as twoway judges them: a range source drawn as line, scatter or connected turned; bar, area, spike, dropline and dot targets drawn as twoway draws them; dot with a non-bar recast and recast(b)/(ba) refused in twoway's words; scatteri recast to a bar-like type turned; an unknown name's class notes printed after the flags are judged.
- **Names on range sources (46-01).** Abbreviated yx names (sc, li, co, b) and a repeated yx name on a y2xtype source or histogram noted and drawn as rspike, as twoway does.
- **Second bound (46-02).** A range source or ciplot() band drawn as a yx type keeps its second bound on the axis, in the default title and in the key, in both modes and after a move.
- **Histogram recast (46-02).** A recast histogram drawn in the histogram's fill and outline (the user's colours kept), recast(bar) a bin wide after gap(), and 0 on the height axis.
- **recast() with horizontal on histogram and rbar (46-02).** Documented under Differences from twoway: twoway draws a broken picture, dash the upright layer turned.

- **Entries.** 6 WP-46 entries; 5 closed, 1 documented, 0 partly closed; BUGS.md holds 64 open entries.
- **Left open:** the unknown-name note for two different yx names on a two-y layer (BUGS.md "recast() with two different yx names on a two-y layer: twoway's note runs the names together, once per y; dash's names them apart, once", S3); the mangle() and barbsize() notes (BUGS.md "pcarrow mangle(abc) and barbsize(abc) print no note; twoway names each unknown style", S3).
- **Gate (09nov2026):** `make test-all` on d95dbad: pytest 44,659 passed (746 s), cert 79 of 79 (683 s), 1,429 s in all; `make cert-release` on d95dbad: 3 of 3 (the WP-29/30/31 truth scripts, 586 s). The two run about 34 minutes, over the 5-minute rule (CLAUDE.md 11); the cuts are proposed as their own work.

## WP-47 · Plot-option fidelity (P15) — DONE

**GAPS4 closed:** basic:PT-1, MS-7, MS-2, MS-3, MS-5, basic:PT-3, basic:PT-4, basic:PT-6, basic:PT-5, basic:PT-10, PIC-2, PIC-9, PIC-10, DG-12, PIC-16, DG-7 · **partly closed:** basic:PT-11, PIC-17, MS-15, basic:PT-15

As a Stata user who styles a layer with twoway's plot options (labels, outlines, markers, dots and the older spellings in my do-files), I want each option read and drawn as twoway draws it, so that a dashboard layer looks like the graph twoway makes from the same command: labels where twoway puts them, outlines and markers the size twoway strokes them, and no option only named in a note when twoway draws it.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-47) and the section decisions D-47-01.a..D-47-06.g, which hold them in full.

- **Immediate and pc labels (47-01).** headlabel on pcscatter, pccapsym and pcarrowi puts the labels at the second point; pci and scatteri labels survive recast(); mlabel(nosuch) on scatteri is taken as twoway takes it.
- **Variable labels and formats (47-02).** yvarlabel()/xvarlabel() reach every plot type, yvarlabel("") gives the variable name, a relabel holds graph-wide; xvarformat()/yvarformat() reach the marker labels; mlabel() naming several variables draws none; emptied and unfittable layers take twoway's titles and keys.
- **Outline alignment (47-03).** Bars, bins, areas and rbar stroked inside under lalign() as twoway strokes them (an outline-only Quad over the fill); markers sized by mlalign(); dots sized by dlalign().
- **Older spellings (47-04).** symbol(), msymangle(), mlabels(), bcolor(), bfintensity(), blwidth(), blpattern(), afcolor(), afintensity() and bmsize() on arrows drawn as the options they stand for, with twoway's precedence.
- **Noted options drawn (47-05).** Back markers, mlabalignment, mlabjustification, bartype(spanning), dropto(), numkeys(), omitanymiss and the other options twoway draws, drawn rather than noted.
- **Markers, dots, bins and labels (47-06).** twoway's marker shapes and msymbol(invisible); empty histogram bins draw nothing; a dot row for a missing y; zero- and missing-weight markers drawn; dot sizes floored on fill plus outline; rarea over twoway's span; marker labels past the plot region, leaving with their point on pan or zoom.

- **Entries.** 20 WP-47 entries; 16 closed, 0 documented, 4 partly closed; BUGS.md holds 52 open entries.
- **Left open:** omitanymiss on lpolyci, area under nodropbase, the contour outline (BUGS.md "lpolyci under omitanymiss draws its fit line one vertex short; twoway draws area under nodropbase without its drops to the base; any plot option on contour changes how twoway strokes one blue outline", S3); rarea under the stair connections and an unsorted outline (BUGS.md "rarea under connect(stairstep) or connect(stepstair) leaves a row missing one bound out of both bounds; an unsorted rarea's outline spikes at such a row", S3); by() panel edges (BUGS.md "Under by(), a marker label stops at its panel's edge; twoway's runs on over the next panel", S3); rarea closing edges, a scheme file twoway refuses, {col #:text} (BUGS.md "rarea's short closing edges are not drawn; a scheme file without the keys twoway needs is drawn where twoway refuses it; {col #:text} is drawn as typed", S3).
- **Gate (10nov2026 and 11nov2026):** `make test-all` on ef353da: pytest 45,776 passed, 1 failed (647 s), cert 77 of 80 (717 s), 1,376 s in all; the four stale readers fixed in fa59d04 and re-run alone. `make cert-release` on fa59d04: the WP-29 and WP-30 truth scripts passed; the WP-31 readers left stale by the outline-only Quad, @dash_diamond and the 0.2 px floor fixed in 17710f9, and blocks S41 and S60 re-run alone and passed. PIC-17 (13d929d) and MS-15 (cec0bf7) landed after that gate; a second gate on 141356b (11-12nov2026) passed: `make test-all` cert 80 of 80 (712 s) with its pytest leg re-run under Python 3.14 (45,946 passed, 603 s; the target's python3 had become 3.15, which has no pytest), and `make cert-release` 3 of 3 (589 s). The two run about 35 minutes, over the 5-minute rule (CLAUDE.md 11); the cuts are proposed as their own work.

## WP-48 · Help, README and tracker accuracy (P16) — DONE

**GAPS4 closed:** LT-27, plot:PT-5, basic:PT-16, GW-22, DT-29, syn:SD-15, RH-15, ECO-16 · **documented:** DT-28

As a Stata user who reads dash's help, README and package description before pasting a twoway command, I want every sentence there to say what dash does, so that I learn what a pasted command keeps and loses from the help rather than from the dashboard: which options are refused as twoway refuses them, which are drawn, which are only named in a note, and which Stata graph commands a dashboard cannot serve.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-48) and the section decisions D-48-01.a..D-48-04.c, which hold them in full.

- **Stale help paragraphs (48-01).** The typo and refusal paragraphs, the graph-prefix paragraph, the passages on headlabel, recast() on dot, degree() above 7, fpfit's smoothing options, the area colours, merged keys and the by() subtitle box, and the units and drawn-options sentences say what dash does, each measured against twoway and pinned.
- **Unsupported list and recast claims (48-02).** The Unsupported list is checked against twoway's own tables of the options it takes (142 probes, none noted and missing); the orientation and recast paragraphs state what WP-46 landed (an rbar recast to a bar-like type drawn upright); the help names what each graph command does after dash and gives recipes for histogram, marginsplot and sts graph; DT-28's two facts are pinned.
- **Tracking documents (48-03).** dash_setup's help, the 0.1.0 CHANGELOG lines, TWOWAY_COVERAGE_AUDIT.md, GAPS3 and DROPIN agree with the code; test/fixtures/rejected_options.json is regenerated.
- **False sentences (48-04).** The audit's 22 false sentences (HR-1..HR-22) are corrected or verified, one test each in test/test_false_sentences.py (HR-17 is 49-01's); README.md and dash.pkg say options are written as for twoway and name the two dash-only options.
- **Closure clauses.** 22 closed BUGS.md entries (18 of WP-47, four of WP-41/43) gained PD-4's Pinned by and Closes GAPS4 clauses after each was checked closed, and a tracking test now requires both.

- **Entries.** 9 WP-48 entries; 8 closed, 1 documented, 0 partly closed; BUGS.md holds 43 open entries.
- **Left open:** none of WP-48's rows. HR-17's sentence check is 49-01's (WP-49).
- **Gate (12nov2026):** `make test-all` on 53fc062: pytest 46,014 passed (613 s), cert 80 of 80 (696 s), 1,320 s in all; `make cert-release` on 53fc062: 3 of 3 (the WP-29/30/31 truth scripts, 590 s); all green first time. The two run about 32 minutes, over the 5-minute rule (CLAUDE.md 11); the cuts are proposed as their own work.

## WP-49 · Messages and notes (P17) — DONE

**GAPS4 closed:** plot:PT-7, plot:PT-6, LT-25, plot:PT-11 · **partly closed:** basic:PT-12

As a Stata user who pastes a twoway command into dash, I want dash's refusals and notes to read as twoway's do, so that a refused command names the option as I typed it in twoway's words, an option twoway draws the same picture with is taken in silence, and a named-style note prints twoway's sentence the number of times twoway prints it.

### Business requirements

Summarised from .ultraplan/sections/index.md (WP-49) and the section decisions D-49-01.a..D-49-02.e, which hold them in full.

- **Refusal first lines (49-01, PD-11, M12).** The first line of every refusal is twoway's, naming the option as typed (option ba() not allowed for ba()), measured in test/fixtures/refusal_line_truth.json (51 probes); dash's second and later lines and the Supported list stay. tsline/tsrline without tsset, a weight written before the varlist and a date tline() on a %tb axis print twoway's lines and return codes. The help states the rule (HR-17, TestHR17).
- **Silence where twoway is silent (49-02).** Catch-all words and text(), title and by() sub-options that twoway draws the same picture with, at two measured values, are taken without a note (test/fixtures/noted_option_truth.json); a value twoway notes, such as a bogus or wrongly cased style name, is still named.
- **Named-style notes (49-02).** All 23 measured named-style cases (position, size, scale, iscale, by() style, xsize/ysize) print twoway's note lines, in its text and count.
- **Library load (49-02).** dash.ado runs the Mata library only when it is not in memory, quietly, so no "already exists" or "lines skipped" line is printed.

- **Entries.** 5 WP-49 entries; 4 closed, 0 documented, 1 partly closed; BUGS.md holds 39 open entries.
- **Left open:** basic:PT-12's residual, BUGS.md "mlabalignment() and mlabjustification() without marker labels, zvarlabel() off contour, xscale()'s noreverse and ring(), and the catch-all words after the plot groups' comma are named where twoway draws the same picture" (S3).
- **Gate (12nov2026):** `make test-all` on c3bb39e: pytest 46,066 passed, 9 failed (628 s), cert 78 of 81 (703 s), 1,343 s in all; the 12 readers left stale by 49-02's silence and notes (controls now taken in silence, the colour and gsize notes in twoway's words, a DROPIN mapping) were flipped in 94ab013, with no code change, and re-run alone: their 7 pytest files 606 passed, test_render_log_clean, test_option_report_paren and test_wp47_truth S04/S05 passed. `make cert-release` on c3bb39e: 3 of 3 (the WP-29/30/31 truth scripts, 592 s). The two run about 32 minutes, over the 5-minute rule (CLAUDE.md 11); the cuts are WP-50's.

## Traceability matrix

Every finding in `GAPS.md`, and the package that closes it.

| Gap | Title | Sev | WP |
|---|---|---|---|
| A1 | Per-plot `if`/`in` dropped before computation | S1 | WP-02 |
| A2 | Linked `by()` facets identical | S1 | WP-02 |
| A3 | Weights parsed and silently discarded | S2 | WP-13 (report), WP-18 (honour) |
| A4 | Estimator divergences (`mspline`, `fpfit`) | S2 | WP-18 |
| A5 | Unimplemented statistical sub-options | S3 | WP-18 |
| A6 | Paren in quoted value deletes `||` segments | S1 | WP-01 |
| A7 | `filter(` in a quoted title harvested | S1 | WP-01 |
| A8 | Malformed input accepted silently | S2 | WP-01 |
| A9 | UTF-8 gate passes surrogates/overlongs | S2 | WP-08 |
| B1 | `net install` breaks all 14 schemes | S1 | WP-05 |
| B2 | Hardcoded renderer fallback path wrong | S3 | WP-05 |
| B3 | Schemes install under invisible/colliding names | S3 | WP-05 |
| B4 | No `adoupdate` metadata; version skew | S3 | WP-05, WP-27 |
| C1 | `dash serve` aborts on every option | S1 | WP-03; closed by WP-23 (broken again by 7ddbc08) |
| C2 | Serve happy path untested | S2 | WP-03; closed by WP-23 (a real launch in the cert suite) |
| C3 | Unexplained "file not found" diagnostic | S3 | WP-03 |
| D1 | Server re-implements 37 of 38 types | S1 | WP-09 |
| D2 | `pci`, `fpfitci`, `pc*`, hover divergences | S1 | WP-10 |
| D3 | Qualifiers unread in server mode | S1 | WP-10 |
| D4 | `by()` drops 20 types in server mode | S1 | WP-11 |
| D5 | `mlabel()` excludes range types | S2 | WP-10 |
| D6 | No "drew nothing" warning in server mode | S2 | WP-10 |
| D7 | Smaller server divergences | S3 | WP-09, WP-10 |
| D8 | Parity guard covers 17 of 38 | S2 | WP-12 |
| E1 | 39 options accepted and inert | S2 | WP-13 |
| E2 | Options dropped with no report | S2 | WP-13 |
| E3 | Sub-options vanish without a note | S2 | WP-14 |
| E4 | `bw()` silently changes meaning | S2 | WP-13 |
| E5 | Only one option validated | S2 | WP-15 |
| E6 | Escaping and encoding holes | S2 | WP-08 |
| E7 | `_dash_validate_path` gaps | S3 | WP-08 |
| F1 | Four twoway types rejected | S2 | WP-22 |
| F2 | Eleven supported types undocumented | S3 | WP-22, WP-23 |
| F3 | Common twoway options surprise the user | S3 | WP-22 |
| F4 | Documented capabilities that do not work | S2 | WP-23 (+ WP-17, WP-15) |
| F5 | Examples run as the help says (parsing alone hid two failures) | S3 | WP-23 |
| G1 | Twelve Stata schemes not translated | S3 | WP-17 |
| G2 | Translations are not Stata scheme files | S3 | WP-17 |
| G3 | Dark minor grid on every figure | S1 | WP-16 |
| G4 | Parsed scheme attributes with no consumer | S2 | WP-16 |
| G5 | `gsize`/`linewidth` scale factors wrong | S2 | WP-16 |
| G6 | Inline styles defeat the scheme on KPI cards | S2 | WP-16 |
| G7 | *(no gap — option precedence correct)* | — | — |
| G8 | `scheme()` warns where it could error | S3 | WP-17 |
| H1 | No image or data export | S2 | WP-21 |
| H2 | *(no gap — interactive layer built)* | — | — |
| H3 | Bootstrap layout in server mode unverified | — | WP-21 |
| I1 | *(no gap — bounded quantities correct)* | — | — |
| I2 | Unbounded dropdowns, facets, rows | S2 | WP-19 |
| I3 | CSP standalone-only; smaller gaps | S3 | WP-20 |
| J1 | Setup declares success after failure | S1 | WP-06 |
| J2 | Version minimums never enforced by pip | S2 | WP-06 |
| J3 | Python probed by running Python | S2 | WP-07 |
| J4 | `dash` never checks Python is available | S2 | WP-07 |
| J5 | Mata compile status never checked | S2 | WP-07 |
| J6 | Smaller `dash_setup` gaps | S3 | WP-06 |
| K1 | KPI silently erases a graph | S1 | WP-04 |
| K2 | Registry in user-writable globals | S3 | WP-04 |
| K3 | Graph options last-write-wins | S3 | WP-04 |
| L1 | No CI, Makefile or pytest config | S2 | WP-25 |
| L2 | Suites run under different interpreters | S2 | WP-25 |
| L3 | UTF-8 rejection branch never executed | S1 | WP-24 (+ WP-08) |
| L4 | Name-existence assertions | S2 | WP-24 |
| L5 | Three tests cannot fail | S2 | WP-24 |
| L6 | Vacuous pass conditions | S2 | WP-24 |
| L7 | Untested programs and functions | S2 | WP-24 |
| L8 | Dead test assets; stale fixture | S3 | WP-25 |
| L9 | Six bugs with no regression test | S3 | WP-24 |
| L10 | *(no gap — no auth model by design)* | — | WP-20 (document) |
| M1 | Tracking documents contradict the code | S2 | WP-23 |
| M2 | Branch state unmerged | S3 | WP-27 |
| M3 | Dev artefacts in the package root | S3 | WP-26 |
| M4 | Duplicated source blocks | S3 | WP-23 |
| M5 | Latent `inlist()` ceiling | S3 | WP-23 (the work was WP-22's, ad13a0f) |
| N | Dead code table | S3 | WP-26 |
| N1 | Stale file headers | S3 | WP-26 |

**70 gaps · 27 work packages · 0 unassigned.**

---

## Corrections to earlier plans

Two technical assumptions in `REMAINING.md` / `phases/` would have sent the
work in the wrong direction. Both were corrected by reading the code at
`187a786`:

1. **"Pass the `view` into the computed mappers."** The computed mappers build
   their **own** `ColumnDataSource` from a computed grid (`map_lfit` at
   `dash_render.py:3865`), so attaching a `CDSView` to the returned renderer
   would change nothing. The input arrays must be masked *before* the
   computation — see WP-02's TR-02.1.
2. **"Server unification is a large lift."** `GlyphMapper`'s entire class
   source is already embedded in the generated app
   (`_inspect.getsource(GlyphMapper)` at `:12405-12409`) and `_DASH_MAPPER` is
   already constructed at `:12432`. All 39 `map_*` methods are available in
   the served app today; `scatter` already delegates correctly at `:14090`.
   WP-09 is a dispatch rewrite, not a port.

One `GAPS.md` finding also needs a scope note carried into the work: **KPI
`fmt()` is not an injection vector.** Measured, `fmt("HACKED" %9.2f)` returns
`r(111)` because `syntax` strips the quotes and the token then resolves as an
identifier. It is an unvalidated input with a confusing failure mode — WP-15's
TR-15.2 — not a security defect.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| WP-02 changes numbers users have already published | High | Land it with a CHANGELOG entry that states plainly which layers were affected and from which version |
| WP-09's dispatch rewrite regresses a working server path | High | WP-12's corpus must be extended **before** the rewrite lands, so the guard is in place to catch it |
| WP-18's `mspline` reimplementation disagrees with Stata at the edges | Medium | Truth fixtures first, from `extract_stat_truth.do`; tolerance agreed and documented |
| WP-05's letter-layout fix is guesswork about Stata internals | Medium | Land TR-05.2 (`findfile`, authoritative) as well as TR-05.1 (layout guess); the integration test exercises a real `net install` |
| WP-16 changes the look of every existing dashboard | Medium | It is a fidelity *fix*; state the visual delta in the CHANGELOG with before/after |
| Test debt (WP-24) discovered mid-flight invalidates earlier green runs | Medium | WP-24 has no dependencies — it can start in parallel with M1 |
| Scope creep from WP-22's twoway parity | Medium | TR-22.1 explicitly recommends documenting `contour`/`contourline` as out of scope rather than implementing them |

---

## Working agreements

From `CLAUDE.md`, applied to every package here:

- **Rule 8 — regression first.** Every gap gets a `BUGS.md` entry and a
  failing test *before* the fix. A test written after the fix proves only that
  the fix is present, not that it works.
- **Rule 4 — a function without a test is not done.** Each WP lists its tests
  as deliverables, not follow-ups.
- **Rule 5 — before committing:** pull `main`, run the **full** suite
  including new tests, fix and re-run until green.
- **Rule 6 — never commit to `main`.** Commit to the working branch and report
  the merge command.
- **Rule 7 — commit messages describe the change only.**
- **Rule 2 — report completion only when complete.** A skip is not a pass
  (WP-25 makes CI enforce this).
