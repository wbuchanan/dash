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

## WP-01 · Parser integrity

**Gaps closed:** A6, A7, A8 · **Severity:** S1 · **Effort:** S · **Depends on:** —

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

## WP-02 · Computed layers must honour their rows

**Gaps closed:** A1, A2 · **Severity:** S1 · **Effort:** M · **Depends on:** —

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

## WP-03 · `dash serve` accepts its own options

**Gaps closed:** C1, C2, C3 · **Severity:** S1 · **Effort:** S · **Depends on:** —

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

## WP-04 · Registry integrity

**Gaps closed:** K1, K2, K3 · **Severity:** S1 · **Effort:** S · **Depends on:** —

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

## WP-05 · Packaged install and scheme reachability

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
>   behaviour is loud — just raw.
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

## WP-06 · `dash_setup` tells the truth

**Gaps closed:** J1, J2, J6 · **Severity:** S1 · **Effort:** S · **Depends on:** —

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

## WP-07 · Environment verification at entry

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

> **User story.** As a user without Python linked, I want `dash` to tell me to
> run `dash_setup` — the way it already does for `jsonio` — instead of
> handing me a raw Stata Python error.

### Business requirements

- **BR-07.1** Every external dependency is verified before use, with a
  message naming the remedy (CLAUDE.md rule 15).
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

## WP-08 · Input hardening — UTF-8, JSON escaping, paths

**Gaps closed:** A9, E6, E7 · **Severity:** S2 · **Effort:** M · **Depends on:** —

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

## WP-09 · Server unification — table-driven dispatch

**Gaps closed:** D1, D7 · **Severity:** S1 · **Effort:** L · **Depends on:** WP-02

> **User story.** As a maintainer, I want one implementation of each plot
> type, so that a fix lands in both render modes at once.

### Business requirements

- **BR-09.1** Every plot type is implemented exactly once.
- **BR-09.2** A new plot type requires no server-specific code.

### Technical requirements

This is cheaper than it looks, and the audit established why: **the whole
`GlyphMapper` class source is already embedded in the generated app** via
`_inspect.getsource(GlyphMapper)` at `dash_render.py:12405-12409`, and
`_DASH_MAPPER` is constructed at `:12432`. All 39 `map_*` methods are
available in the served app today. The server simply does not call 37 of them.
`scatter` already delegates correctly at `:14090` and is the working
reference.

- **TR-09.1** Replace the `if/elif ptype == …` chain at
  `dash_render.py:14058-14890` with a table-driven dispatch mirroring the
  standalone one at `:10360-10398` — a plain dict, a `range_dispatch` dict and
  a `pc_dispatch` dict, emitted into the app as source.
- **TR-09.2** Factor the per-type column preparation (the
  `g_df[cols].dropna()` → `ColumnDataSource` step) into one helper. Every
  branch repeats it, and the repetition is where D2's defects live. De-dup
  column lists with `dict.fromkeys` **in the helper**, so the `pc*` crash and
  the `pcscatter` silent no-draw are structurally impossible.
- **TR-09.3** Lower-case `ptype` at `:14031`. The main chain does not; the
  facet chains at `:15137, 15237` do; and the main chain lacks the `'hist'`
  alias the facet chains have. Three tables, three behaviours.
- **TR-09.4** Add an `else` branch that warns on an unrecognised type, so a
  future gap is loud.
- **TR-09.5** Retire the now-unreachable per-branch style literals — `size=6`
  at `:15145, 15200, 15246` and `width=0.8` at `:15150`.

### Acceptance criteria

- **AC-09.1** All 38 plot types render in server mode through `GlyphMapper`.
- **AC-09.2** `grep -c "elif ptype ==" dash_render.py` falls to 0 in the main
  chain.
- **AC-09.3** An unknown plot type warns rather than drawing nothing.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Unit | `test_server.py` | The generated app contains a dispatch table, not a chain; every type maps to a `_DASH_MAPPER` call |
| Parity | `test_mode_parity.py` | See WP-12 — the corpus expansion is the real gate |
| Integration | `test_server_serves.py` | The generated app still compiles and serves |

---

## WP-10 · Server layer defects

**Gaps closed:** D2, D3, D5, D6 · **Severity:** S1 · **Effort:** M · **Depends on:** WP-09

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

## WP-11 · Server facets

**Gaps closed:** D4 · **Severity:** S1 · **Effort:** M · **Depends on:** WP-09

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

## WP-12 · The parity guard earns its name

**Gaps closed:** D8 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-09, WP-10, WP-11

> **User story.** As a maintainer, I want the next divergence between the two
> renderers to fail a test rather than reach a user.

### Business requirements

- **BR-12.1** The guard covers every plot type and every cross-cutting
  feature.
- **BR-12.2** Legitimate differences are enumerated, never tolerated by a
  loose comparison.

### Technical requirements

- **TR-12.1** Extend `CORPUS` (`test/test_mode_parity.py:186-274`) from 17 to
  all 38 plot types. The 21 missing: `function pci pcspike pcarrow pcbarrow
  pcscatter lfitci qfit qfitci fpfit fpfitci lowess rarea rbar rspike rcap
  rline rconnected rscatter tsline tsrline`.
- **TR-12.2** Add corpus entries for `by()`, `link()`, `filter()`, `tabs()`
  and KPIs — no entry sets any of them today.
- **TR-12.3** Extend `_glyph_profile` (`:128-147`) and `_annotations`
  (`:150-174`) to collect tools and tooltips. Every D2 hover finding was
  invisible because they do not.
- **TR-12.4** Add a completeness assertion: the corpus must cover every name
  in the dispatch table, so a new plot type cannot be added without a parity
  entry.

### Acceptance criteria

- **AC-12.1** The corpus covers 38/38 types and the five cross-cutting
  features.
- **AC-12.2** Reverting any WP-10 or WP-11 fix makes this file fail.
- **AC-12.3** Adding a plot type without a corpus entry fails TR-12.4's
  assertion.

### Test plan

This package *is* a test plan. Its own acceptance is verified by mutation:
revert each WP-10/WP-11 fix in a scratch branch and confirm the guard fails.

---

# Milestone 3 — An honest surface

## WP-13 · Options: honour or report, never silence

**Gaps closed:** A3, E1, E2, E4 · **Severity:** S2 · **Effort:** M · **Depends on:** —

> **User story.** As a user, I want to be told when `dash` ignores something
> I wrote — and never to be told it ignored something it actually used.

### Business requirements

- **BR-13.1** Every accepted option is either honoured or named in the
  ignored-options report.
- **BR-13.2** The report never names an option that was honoured.

### Technical requirements

- **TR-13.1** Report the silently-dropped set (E2): plot/graph-level `link()`
  and `filter()` (written to `graph_options` at `dash.ado:1465` but read only
  from `build_options` by the renderer), and `saving()` on a named graph
  (`_dash_plot` routes to `_dash_register_graph` at `:1487` and never reaches
  the extraction at `:1602`). Decide per option whether to honour or report;
  report is acceptable, silence is not.
- **TR-13.2** Weights (A3): feed `s(_weight)` to `_dash_report_ignored` so the
  comment at `dash.ado:782-783` becomes true. Note `sreturn clear` at `:1112`
  destroys it before the option parse — the value must be carried across.
  Honouring weights in the computed layers is WP-18.
- **TR-13.3** Remove `nodraw` from both `_dash_pending` blocks
  (`dash.ado:371, 615`) — it is honoured at `:1765`, so dash currently reports
  ignoring an option it just applied. Fix the contradiction between
  `dash.sthlp:296` and `:1149-1152` in WP-23.
- **TR-13.4** Make the `bw` alias plot-type-aware (E4). `dash.ado:560` folds
  `bw` → `barwidth` unconditionally; real `twoway` accepts `bw()` on `lpoly`
  (meaning `bwidth`) and rejects it on `bar`. Fold to `bwidth` for
  `lpoly`/`lowess`/`kdensity` and `barwidth` for `bar`, or drop the alias.
- **TR-13.5** Keep `test_unsupported_report_is_true.py` authoritative and
  extend it to assert the *converse*: no option on the pending list has any
  effect, **and** no option off the list is silently dropped.

### Acceptance criteria

- **AC-13.1** `dash scatter mpg weight [aw=price]` reports weights as ignored.
- **AC-13.2** `dash scatter y x, link(g1)` reports `link()` or honours it.
- **AC-13.3** `dash scatter mpg weight, nodraw` prints no ignored-option note.
- **AC-13.4** `dash (lpoly mpg weight, bw(400))` sets `bwidth`, not
  `barwidth`.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | `test_option_surface.cscript` — extend | Each newly-reported option appears in the note exactly once |
| Unit | `test_unsupported_report_is_true.py` | Bidirectional: pending ⇒ inert, and non-pending ⇒ has an effect |
| Cert | new `test_alias_semantics.cscript` | `bw()` resolves per plot type, measured against `twoway`'s own rc |

---

## WP-14 · Sub-options stop vanishing

**Gaps closed:** E3 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-13

> **User story.** As a user writing `legend(span stack)`, I want to know those
> sub-options did nothing — `dash.sthlp:162` promises "nothing is ever dropped
> without being named".

### Business requirements

- **BR-14.1** `dash.sthlp:162`'s promise — "nothing is ever dropped without
  being named" — holds for sub-options as well as options.
- **BR-14.2** A security filter may refuse input, but never silently.

### Technical requirements

- **TR-14.1** Add an unknown-sub-option warning to `_rebuild_legend`
  (`dash_render.py:8956`), the axis-label and axis-scale parsers, `xline()`,
  and `xtitle()`. Only `xscale`/`yscale` warn today
  (`_report_unhandled_scale_opts:805`), and only for 5 tokens.
- **TR-14.2** `by()` — covered by TR-11.2.
- **TR-14.3** Stop `_parse_filter_raw` (`:8730-8774`) discarding a whole
  `filter()` group in silence when its text trips `_UNSAFE_F` or the varname
  regex. A legitimate `label("R&D __ spend")` makes the widget vanish with
  `rc=0`. Warn, and narrow the pattern so it matches genuine injection rather
  than ordinary label text.
- **TR-14.4** Warn on an unrecognised filter `type()` (`:11804-11805`, server
  `:15462-15463`), which currently produces no widget and no message.

### Acceptance criteria

- **AC-14.1** Every sub-option in the GAPS E3 list produces a named warning.
- **AC-14.2** `filter(x, label("R&D __ spend"))` produces a widget.
- **AC-14.3** `filter(x, type(bogus))` warns.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | new `test_suboption_reporting.cscript` | Each E3 sub-option is named once |
| Unit | `test_filters.py` | Benign labels survive; genuine injection payloads are still refused **and reported** |

---

## WP-15 · Systematic option validation

**Gaps closed:** E5 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-13

> **User story.** As a user who typed a bad value, I want a clear `dash` error
> naming the option — the way `level()` already does.

### Business requirements

- **BR-15.1** An invalid option value produces a `dash` error naming the
  option, before it reaches Python.
- **BR-15.2** Validation is declarative and uniform, not per-option
  hand-written exceptions.

### Technical requirements

- **TR-15.1** Build a declarative validation table (option → kind: number,
  range, colour, symbol, enum, numlist) and apply it in
  `_dash_parse_plot_opts` / `_dash_parse_graph_opts`. `level()`
  (`dash.ado:549-558`) is the model and the only validated option today; the
  other 69 plot-level and 54 graph-level values go to JSON verbatim.
- **TR-15.2** Validate KPI `fmt()`. It is interpolated into an *evaluating*
  context at `dash.ado:1918` (`local kpi_display : display `fmt' `kpi_value'`).
  **It is not an injection vector** — measured: `fmt("HACKED" %9.2f)` returns
  `r(111)` because `syntax` strips the quotes and the token resolves as an
  identifier — but the failure is confusing. Validate it as a Stata format and
  error clearly.
- **TR-15.3** Where validation must stay renderer-side, make it consistent:
  `_stat_option_float` (`dash_render.py:9228-9254`) and `_resolve_kpi_color`
  (`:10484-10485`) are the existing good examples.

### Acceptance criteria

- **AC-15.1** A bad value for any validated option exits 198 naming the option.
- **AC-15.2** `dash kpi mean(mpg), name(k) title(T) fmt(bogus)` gives a
  format error, not `r(111)`.
- **AC-15.3** No documented example regresses (the F5 baseline: all parse
  clean today).

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | new `test_option_validation.cscript` | One good and one bad value per validated option |
| Cert | `test_conformance.cscript` | All documented examples still rc 0 with empty pending/unknown |
| Adversarial | `test_adversarial.cscript` | Hostile values for each validated option |

---

## WP-16 · Schemes reach the page

**Gaps closed:** G3, G4, G5, G6 · **Severity:** S1/S2 · **Effort:** M · **Depends on:** WP-09

> **User story.** As a user who chose `scheme(s1color)`, I want the dashboard
> to look like s1color — including *not* drawing gridlines s1color does not
> draw.

### Business requirements

- **BR-16.1** A chosen scheme governs what is drawn, including what is *not*
  drawn.
- **BR-16.2** No scheme directive is parsed without reaching rendered output.
- **BR-16.3** Relative-size units convert on Stata's scale, not an invented
  one.

### Technical requirements

- **TR-16.1 (G3, highest severity here).** Stop setting the minor grid
  unconditionally at `dash_render.py:2185`. Measured: s1color and stmono1
  draw **no** major grid and a `#505050` minor grid on both axes; s2color
  draws a pale `#eaf2f3` major and a dark `#505050` minor. Stata draws none of
  these — its schemes declare `draw_minor_grid no`. Add `draw_minor_hgrid` /
  `draw_minor_vgrid` to the translated scheme files and to the parser, and
  default to off.
- **TR-16.2 (G5).** Fix the `gsize` scale factor at `:1846-1849`:
  `int(val * 1.2)` should be `× 2.880` — Stata's `gsize-medium.style` is
  `3.8194` = 11 pt on a 4-inch graph. `economist`'s `gsize heading 6.0` means
  ≈17 pt; dash renders 7 pt, smaller than its own subtitle.
- **TR-16.3 (G5).** Fix the `linewidth` interpretation at `:1899-1911`, which
  takes the number as pixels. Stata's `linewidth medium` is `.30`; economist's
  `linewidth p 1.2` is 4× medium, and currently renders *thinner* than every
  other scheme.
- **TR-16.4 (G4).** Wire or remove the parsed-but-unconsumed attributes:
  `note_font_size` (`:2047`, note/caption sizes hardcoded at `:9866-9868`),
  `p_mark_colors` (`:1980`, never indexed by `default_color` at `:2103-2112`),
  `legend_position` and `legend_cols` (`:2086-2088` — dead standalone, and
  dead in the server too because `lg.location = 6` at `:12661` raises
  `ValueError` in Bokeh 3.9 and takes `legend_cols` down with it inside the
  same `try`). **Split that `try` block** regardless.
- **TR-16.5 (G4).** Apply `color heading` / `gsize heading` to Bokeh figure
  titles — they reach only the dashboard CSS today, so every scheme renders
  `#444444` / `13px`.
- **TR-16.6 (G6).** Stop the inline `style=` on KPI cards (`:10484-10495`,
  server `:12977-12982`) overriding `css_block()`'s `.db-kpi-card` rule. Move
  the scheme-driven values into the class.
- **TR-16.7** Remove the hardcoded `g.grid_line_color = "#e5e5e5"` at `:9188`
  in favour of the scheme's `color major_grid`.

### Acceptance criteria

- **AC-16.1** Under s1color and stmono1, both major and minor grids are absent.
- **AC-16.2** economist's title renders larger than its subtitle, and its
  lines render thicker than s2color's.
- **AC-16.3** A KPI card under economist uses the scheme's legend colours.
- **AC-16.4** No scheme attribute is parsed without a consumer.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Unit | `test_scheme_fidelity.py` — **strengthen** | Today it asserts attributes are *exposed*; it must assert they reach rendered output. This is why G4 passed the suite |
| Unit | new `test_scheme_rendered_output.py`, all 14 schemes | Grid colours, title colour/size, line width, KPI card colours read back off real Bokeh models |
| Truth | `scripts/extract_scheme_truth.py` | Add `draw_minor_*`, and the `gsize`/`linewidth` unit conversions |
| Regression | `BUGS.md` entry for G3 | Written first |

---

## WP-17 · Scheme coverage and custom schemes

**Gaps closed:** G1, G2, G8 · **Severity:** S2/S3 · **Effort:** M · **Depends on:** WP-05

> **User story.** As a user with a house scheme, I want to point `dash` at it
> the way the help says I can.

### Business requirements

- **BR-17.1** A user-supplied scheme file works by the route the help
  documents, on every entry point.
- **BR-17.2** An explicitly requested scheme that cannot be resolved is an
  error; an untranslatable inherited `c(scheme)` is a single clear warning.
- **BR-17.3** The shipped scheme set covers Stata's user-selectable schemes.

### Technical requirements

- **TR-17.1 (G8/F4).** Make the documented bare-name path work: at
  `dash_render.py:7967-7970`, `_resolve_scheme_name` rejects any name that is
  neither a theme alias nor a builtin **unless** it ends in `.scheme`, before
  `_resolve_path`'s CWD bare-name branch (`:1704-1716`, added for exactly this
  purpose) can run. Let a bare name try CWD first. Note graph-level `scheme()`
  already works (`:9484-9487` bypasses the gate) — the same name behaving
  differently on `dash scatter` and `dash build` is itself the bug.
- **TR-17.2 (G8).** Decide the unknown-scheme policy: today it warns and falls
  back, so a typo yields a wrongly-styled dashboard and a warning in the log.
  Error on an explicitly requested name; keep the fallback only for an
  inherited `c(scheme)` dash cannot translate — that path is common (129
  third-party schemes on the test machine alone) and must stay non-fatal, but
  must say so once, clearly.
- **TR-17.3 (G1).** Translate the six missing user-selectable Stata schemes:
  `s2manual`, `s1manual`, `s2gmanual`, `s2color8`, `sttrans`, `stgcolor_alt`.
  `s2gmanual` is the best test of the `p#lineplot` logic — it is one of only
  two Stata schemes declaring a `lineplot` directive.
- **TR-17.4 (G2).** Document in `dash.sthlp` that the shipped `.scheme` files
  are dash-format translations (≈118 keys, flattened, no `#include`), not
  drop-in Stata scheme files (s2color's Stata original has 2060 directives).
  Preserve the `sources` provenance from `test/fixtures/scheme_truth.json`
  into the shipped files as comments.

### Acceptance criteria

- **AC-17.1** A `mytheme.scheme` in the working directory is found by
  `scheme(mytheme)` on **both** `dash scatter` and `dash build`.
- **AC-17.2** `scheme(nosuchthing)` errors; an untranslatable `c(scheme)`
  warns once and falls back.
- **AC-17.3** All 20 schemes ship, translate faithfully and render.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Cert | new `test_custom_scheme.cscript` | Bare name and `.scheme` name both resolve, on both entry points |
| Unit | `test_scheme_fidelity.py` | Extend the 14-scheme parametrization to 20; `scheme_truth.json` coverage assertion updated |
| Security | `test_scheme.py` | The WP-05 containment checks still reject traversal and symlink escape |

---

## WP-18 · Statistical fidelity

**Gaps closed:** A4, A5 · **Severity:** S2 · **Effort:** L · **Depends on:** WP-02

> **User story.** As a researcher, I want `mspline` and `fpfit` to be the
> estimators Stata documents, and weights to be honoured.

### Business requirements

- **BR-18.1** Every statistical layer is the estimator Stata documents, not
  an approximation of it.
- **BR-18.2** Options that change an estimate are honoured or rejected —
  never accepted and ignored.
- **BR-18.3** Behaviour already verified correct against Stata is locked by a
  truth fixture before any refactor.

### Technical requirements

- **TR-18.1 (A4).** Reimplement `mspline` (`dash_render.py:5912-5980`) as
  Stata's estimator: a cubic spline through the **cross-medians of `bands()`
  bands**. It currently PCHIP-interpolates through every observation after
  averaging duplicate x, ignores `bands()` and `n()`, and hardcodes a 200-point
  grid at `:5973`. This is a different estimator, not a tuning difference.
- **TR-18.2 (A4).** Add the repeated-power branch to `_fp_transform`
  (`:4452-4459`): Royston–Altman requires `β₁·xᵖ + β₂·xᵖ·ln x` when
  `p₁ == p₂`. `_fit_fp2` (`:4483`) already generates those pairs via
  `combinations_with_replacement`, but the design matrix is then singular and
  the model collapses to FP1 — about a third of Stata's FP2 candidates are
  unreachable.
- **TR-18.3 (A4).** Apply Stata's origin shift in `fpfit` rather than dropping
  `x <= 0` rows to NaN (`:4456-4458`).
- **TR-18.4 (A5).** Implement `histogram, discrete`; `lfitci`/`qfitci`
  `stdf`/`stdp`/`stdr` (only one band type is drawn today); and `lowess`
  `mean`, `noweight`, `logit`, `adjust`. All have zero occurrences currently.
- **TR-18.5 (A3 follow-on).** Honour weights in the computed layers, carrying
  the weight expression through the spec. Stata's `lfit`, `qfit`, `lowess`,
  `lpoly`, `fpfit`, `histogram` and `kdensity` all accept them.
- **TR-18.6** Preserve what already matches Stata: `_fit_grid`'s observed-range
  rule, `_stata_bin_count`, `_stata_kde_bandwidth`, the ROT bandwidths,
  `_t_ppf`, `_stata_percentile` (Hyndman-Fan type 2), and `fpfit`'s correct
  *rejection* of `bwidth()`/`degree()`. These are verified correct — lock them
  with truth fixtures before refactoring.

### Acceptance criteria

- **AC-18.1** `mspline` output matches Stata's `twoway mspline` within
  tolerance, for two `bands()` values.
- **AC-18.2** `fpfit` selects a repeated-power model where Stata does.
- **AC-18.3** `fpfit` on data containing `x <= 0` uses all observations.
- **AC-18.4** Each A5 option changes the output in the documented direction.
- **AC-18.5** Weighted fits match Stata's weighted estimates.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Truth | `scripts/extract_stat_truth.do` → `stat_truth.json` | Ground truth from Stata for `mspline` (2 band counts), `fpfit` (incl. repeated-power and non-positive x), each A5 option, and weighted fits |
| Unit | `test_statistical_truth.py` | Compare against the fixture within tolerance |
| Regression | `BUGS.md` entries for A4's three sub-findings | Written first |

---

## WP-19 · Resource limits

**Gaps closed:** I2 · **Severity:** S2 · **Effort:** M · **Depends on:** —

> **User story.** As a user who pointed a filter at a continuous variable, I
> want a warning and a sane widget — not a 200 001-option dropdown.

### Business requirements

- **BR-19.1** No user input can produce unbounded output or memory use
  (CLAUDE.md rule 3).
- **BR-19.2** Every clamp warns, naming the limit and the option that would
  raise it.

### Technical requirements

- **TR-19.1** Cap dropdown cardinality. `build_dropdown` (`:7628-7660`) takes
  `set(source.data[varname])` with no ceiling: 200 000 observations give
  200 001 options. Add `_MAX_FILTER_OPTIONS`, warn, and suggest
  `type(range)`/`type(slider)` for continuous variables.
- **TR-19.2** Add `_MAX_BY_GROUPS` — `by(id)` builds one figure per value.
- **TR-19.3** Add `_MAX_TABS` and `_MAX_GRAPHS`.
- **TR-19.4** Add a row/column cap with a clear refusal.
  `_report_dataset_size` (`:538-567`) warns — its docstring records 2 M rows →
  90.6 MB of HTML at 1.71 GB RSS — but never refuses or truncates.
- **TR-19.5** Replace `_MAX_IPS` with a structure that actually limits.
  Measured: a client cycling 10 000 forwarded keys took 300 sessions inside a
  60-second window against a nominal 60. It is an eviction primitive, not a
  limiter; a larger cap does not fix it.
- **TR-19.6** Keep the bounds that already work: `_MAX_BINS`, `_MAX_MBANDS`,
  `_MAX_EXPR_CHARS`, the function-point cap, `_WEBGL_THRESHOLD`, the port
  clamp.

### Acceptance criteria

- **AC-19.1** A dropdown filter on a continuous variable warns and is capped.
- **AC-19.2** `by()` on a high-cardinality variable warns and is capped.
- **AC-19.3** An oversized dataset is refused with a clear message.
- **AC-19.4** The forwarded-key attack cannot exceed the nominal session rate.

### Test plan

| Kind | Test | Asserts |
|---|---|---|
| Unit | `test_resource_limits.py` | Each new cap fires, warns, and names the limit |
| Adversarial | `test_server_rate_limit.py` | The 10 000-key cycle is held to the nominal rate |
| Adversarial | `test_adversarial.cscript` | Resource-exhaustion cases per input surface (CLAUDE.md rule 18) |

---

## WP-20 · Security hardening

**Gaps closed:** I3 · **Severity:** S2/S3 · **Effort:** S · **Depends on:** WP-09

> **User story.** As someone deploying a served dashboard on a shared
> machine, I want the same protections the saved file already has.

### Business requirements

- **BR-20.1** Security controls apply equally in both render modes.
- **BR-20.2** Every input surface has adversarial coverage for auth bypass,
  injection and resource exhaustion (CLAUDE.md rule 18).
- **BR-20.3** Defences that depend on a third-party library's behaviour are
  pinned by a test, not assumed.

### Technical requirements

- **TR-20.1** Emit the CSP in server mode. `_CSP_META` (`:660-668`) is
  injected at `:10897` and `:12139`, both standalone; the Bokeh-server
  document sets no security headers.
- **TR-20.2** Strengthen the CSP itself: it is `script-src 'unsafe-inline'
  'unsafe-eval'` with no `default-src`, `object-src 'none'`, `base-uri` or
  `frame-ancestors`.
- **TR-20.3** Resolve the hover-tooltip label question (SUSPECTED). `:10234`
  appends `self._axis_label(col)` — a user-controlled variable label — into
  `tooltips`. Bokeh 3.x builds tooltip rows as DOM text nodes, so this is
  almost certainly safe, but the safety comes from BokehJS. Add a
  version-pinned test; escape if the test shows otherwise.
- **TR-20.4** Sanitise `` `pkgver' `` at `dash_setup.ado:158`, which
  interpolates distribution metadata into a `python:` line as
  `Version("`pkgver'")`. `_dash_pkg_version` guards the package *name*
  (`:307`) but not the returned version.
- **TR-20.5** Preserve the defences that are already correct and verified: the
  `function` AST whitelist, `_stata_if_to_pandas` validation, the scheme
  abspath+realpath containment, `_sanitize_css_color`, `FilterBuilder._safe`,
  and loopback-by-default binding. Add tests that pin them.

### Acceptance criteria

- **AC-20.1** A served document carries the CSP.
- **AC-20.2** A hostile variable label cannot execute script in either mode.
- **AC-20.3** Three adversarial cases (auth bypass, injection, exhaustion) per
  input surface exist and pass (CLAUDE.md rule 18).

### Test plan

Extend `test_security_surface.py`, `test_kpi_security.py` and
`test_adversarial.cscript`. Add a standing note that `dash` has no auth model
(L10) so rule 19 is N/A by design, not by omission.

---

# Milestone 4 — Complete and covered

## WP-21 · Export

**Gaps closed:** H1, H3 · **Severity:** S2 · **Effort:** S · **Depends on:** WP-09

> **User story.** As a user, I want to save the chart as an image and the
> filtered rows as CSV, so the dashboard can feed a paper or a deck.

### Business requirements

- **BR-21.1** A user can get the chart out as an image and the data out as
  CSV, in both modes.
- **BR-21.2** Exported data reflects the filters the user has applied.

### Technical requirements

- **TR-21.1** Add `SaveTool` to both toolbars — the standalone string at
  `dash_render.py:9552` and the server lists at `:13801, 15127, 15230`. There
  are zero occurrences of `SaveTool`, `download`, `export` or `to_csv` in the
  file today.
- **TR-21.2** Consider `BoxZoomTool`, `UndoTool`, `RedoTool`, `CrosshairTool`
  in the same pass.
- **TR-21.3** Add a CSV download of the current (filtered) selection, via
  `CustomJS` standalone and a Bokeh callback in server mode.
- **TR-21.4** (H3) Verify what `layout(bs…)` does in server mode —
  `_render_bootstrap_html` is standalone-only, and the behaviour is currently
  unknown. Fix or document.
- **TR-21.5** Document the new tools in `dash.sthlp`.

### Acceptance criteria

- **AC-21.1** Both modes offer PNG save and CSV download.
- **AC-21.2** The CSV reflects active filters.
- **AC-21.3** `layout(bs)` in server mode is specified and tested.

### Test plan

`test_mode_parity.py` toolbar comparison (WP-12's `_glyph_profile` now
collects tools); a `test_html_output.py` assertion for the tools; a
`test_server_serves.py` case exercising the CSV callback.

---

## WP-22 · `twoway` parity

**Gaps closed:** F1, F2, F3 · **Severity:** S2/S3 · **Effort:** L · **Depends on:** WP-09

> **User story.** As a Stata user, I want `dash.sthlp`'s drop-in claim to hold
> — or to be told precisely where it does not.

### Business requirements

- **BR-22.1** Every `twoway` plot type either renders or is documented as
  unsupported — the user is never surprised at the command line.
- **BR-22.2** Options that are aliases of implemented ones behave as `twoway`
  does.
- **BR-22.3** No implementation limit may silently cap future growth.

### Technical requirements

- **TR-22.1** Implement the four rejected `twoway` plot types — `contour`,
  `contourline`, `pcarrowi`, `pccapsym` — or state their absence explicitly in
  the help. They exit 198 today (`dash.ado:938-948`) and the help lists no
  supported types at all, so users cannot anticipate it. **Recommendation:**
  implement `pcarrowi` and `pccapsym` (cheap — siblings of implemented types);
  document `contour`/`contourline` as out of scope (they need a different
  data model).
- **TR-22.2** Add the 38 supported types to `dash.sthlp`, naming the 11
  currently undocumented ones (F2): `rconnected rscatter pcspike pcarrow
  pcbarrow pci pcscatter tsline tsrline mband function`. This is WP-23's
  deliverable but its content is specified here.
- **TR-22.3** Triage the F3 list — `clcolor() clpattern() clwidth()`,
  `addplot()`, `margin()`, `region()`, `bargap()`, `xreverse`/`yreverse`,
  `xalternate`/`yalternate`, `lockaspect`, `zoom()`, `mlabangle()`,
  `mlabformat()`, and `sort(varname)`. These currently land in "unknown" and
  are reported, which is correct behaviour, but none appears in the help's
  unsupported list, so the note surprises. Implement the cheap and common ones
  (`clcolor`/`clpattern`/`clwidth` are aliases of `lcolor`/`lpattern`/`lwidth`
  and should simply fold); declare the rest.
- **TR-22.4** Raise the latent `inlist()` ceiling at `dash.ado:1004-1005` and
  `:1146-1147` — exactly 9 literals plus `ptype`, Stata's limit. **A tenth
  range plot type will fail to compile.** Replace with a local macro list and
  `` `: list ptype in …' ``.

### Acceptance criteria

- **AC-22.1** Every twoway plot type either renders or is documented as
  unsupported.
- **AC-22.2** `clcolor()`/`clpattern()`/`clwidth()` work as `twoway` does.
- **AC-22.3** Adding a tenth range type compiles.

### Test plan

Extend `test/fixtures/conformance_corpus.txt` and `test_conformance.cscript`;
add parity entries for any newly implemented type (WP-12's TR-12.4 will
require them).

---

## WP-23 · Documentation reconciliation

**Gaps closed:** F4, M1, M4, M5 · **Severity:** S2/S3 · **Effort:** M · **Depends on:** all feature packages

> **User story.** As a user, I want the help file to describe the command I
> actually have.

### Business requirements

- **BR-23.1** Every claim in `dash.sthlp` is true of the shipped code.
- **BR-23.2** Every supported capability is documented.
- **BR-23.3** No tracking document in the repository claims work that is not
  done.

### Technical requirements

- **TR-23.1** Correct every F4 claim: fractional percentiles
  (`dash.sthlp:466-467` — `p97.5` is documented and cannot be entered; both
  renderers already accept it, so fix `dash.ado:1839, 1849` instead of the
  help); `nodraw` on `dash build` (`:296` contradicts `:1149-1152`); bare-name
  custom schemes (`:1084-1086`, fixed in WP-17); the semicolon joiner claim
  (`:408` — it is `" || "`); the scipy attribution (`:1182-1183` and
  `dash_setup.sthlp:76-77` — `qfitci` and `kdensity` do not use scipy);
  `xtick()`/`ytick()` semantics (`:866-869`, fixed in WP-14/WP-15);
  `colorvar()`'s scatter-only scope (`:926-948`); `legend()` keyword geometry
  (`:853`); `ylabel2()`/`xlabel2()` grammar (`:905-912`).
- **TR-23.2** Add a supported-plot-types section (WP-22's TR-22.2).
- **TR-23.3** Document the undocumented-but-honoured options: `hover()`,
  `bands()`, `mlg()`, `range()`, `n()`, `base()`, `marker()`, `color()`, and
  the `$dash_nobrowser` global.
- **TR-23.4** Add a "server mode limitations" block, or delete it once WP-09
  through WP-12 make it unnecessary.
- **TR-23.5** (M1) Reconcile `TODO.md` (555 items, all checked) and `BUGS.md`
  (73 entries, all closed) against reality, or retire them in favour of
  `GAPS.md`, `REMAINING.md` and `phases/`. Documents that claim completion
  while 39 options are inert are worse than absent.
- **TR-23.6** (M4) Remove the duplicated generator NOTE comment
  (`dash.ado:266-275`, `:459-469`) and the duplicated T/B/L/R folding block
  (`:316-319`, `:340-343`). Correct the rationale those comments give: it is
  measurably wrong — `T1title` yields minimum abbreviation `t`, not `t1`, so
  the explicit `T B L R` declarations at `:301-302` are redundant.
- **TR-23.7** (M5) Fix the `inlist()` ceiling — tracked in TR-22.4.

### Acceptance criteria

- **AC-23.1** Every claim in `dash.sthlp` is verified by a test or corrected.
- **AC-23.2** Every supported plot type and honoured option is documented.
- **AC-23.3** No tracking document claims work that is not done.

### Test plan

Extend `test_help_conformance.py` — already strong — to assert the
plot-type list matches the dispatch table, and that every documented option
appears in a `syntax` block. Make it fail when the help and code diverge in
either direction.

---

## WP-24 · Test integrity

**Gaps closed:** L3, L4, L5, L6, L7, L9 · **Severity:** S1/S2 · **Effort:** M · **Depends on:** —

> **User story.** As a maintainer, I want a green suite to mean the code
> works.

### Business requirements

- **BR-24.1** Every test fails when its subject is broken.
- **BR-24.2** Every function of every feature has a behavioural test
  (CLAUDE.md rule 4).
- **BR-24.3** Every fixed defect has a regression test (CLAUDE.md rule 8).

### Technical requirements

- **TR-24.1 (L3, highest severity here).** Test `_dash_check_utf8` with real
  invalid UTF-8. Its only two callers
  (`test_ado_loads.cscript:94`, `test_mata_autoload.cscript:52`) pass `""`, so
  the rejection branch (`dash_parse.mata:149-153`) and all of `_is_utf8` have
  **never executed**. Delivered jointly with WP-08.
- **TR-24.2 (L5).** Fix the three tests that cannot fail:
  `test_filter_label.py:155-161` (returns green on any exception; its
  `dr.render() if False else None` at `:159` is dead code, so the render it
  claims to inspect never runs), `test_options.py:260-262` (catches
  `AssertionError`), `test_filters.py:209-211`.
- **TR-24.3 (L5).** Give the 19 no-assertion tests real assertions, starting
  with `test_resource_limits.py:206`
  (`test_a_power_tower_does_not_hang_the_served_app` — no assertion, no
  timeout). The eleven honest "does not crash" cases may stay, renamed to say
  so.
- **TR-24.4 (L6).** Replace the vacuous pass conditions:
  `test_conformance.cscript:126-146` string-matches `"drew nothing"` in a log;
  `test_every_plot_type_draws.py:77-95` derives its parametrization from a
  regex over the display string at `dash.ado:940-944`. Drive both from the
  dispatch table.
- **TR-24.5 (L4).** Replace name-existence assertions with behavioural ones —
  `_dash_json_get_str` is covered only by `assert "_dash_json_get_str" in src`
  (`test_server.py:4694-4712`), although it *is* the fix for a parsing bug.
  Give it hostile-JSON tests. Same for
  `test_paired_coordinate_plots.py:139,151` and `test_serve_options.py:71-157`.
- **TR-24.6 (L7).** Add direct tests for `_dash_formats_json`,
  `_dash_date_fmts_swap` and `_dash_date_fmts_restore` — never named in any
  test file — and add them to the existence loop at
  `test_ado_loads.cscript:69-77`. Add a `dash_setup` execution test (75
  textual hits, zero invocations).
- **TR-24.7 (L9).** Add the six missing bug-regression tests
  (`BUGS.md:341, 359, 383, 395, 413, 431`), two of which are security fixes.

### Acceptance criteria

- **AC-24.1** Every test fails when its subject is reverted (mutation-checked
  for the ones this package touches).
- **AC-24.2** No test catches `AssertionError` or returns green on a bare
  `except Exception`.
- **AC-24.3** Every `program define` and every Mata function has at least one
  behavioural test.
- **AC-24.4** Every `BUGS.md` entry names a regression test.

### Test plan

This package is tests. Verify by mutation: revert each fix from WP-01 … WP-08
in a scratch branch and confirm the suite goes red.

---

## WP-25 · Test infrastructure

**Gaps closed:** L1, L2, L8 · **Severity:** S2 · **Effort:** M · **Depends on:** WP-24

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

---

## WP-26 · Dead code removal

**Gaps closed:** N, N1, M3 · **Severity:** S3 · **Effort:** S · **Depends on:** WP-09, WP-10

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

---

# Milestone 5 — Shippable

## WP-27 · Release closeout

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

---

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
| C1 | `dash serve` aborts on every option | S1 | WP-03 |
| C2 | Serve happy path untested | S2 | WP-03 |
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
| F5 | *(no gap — examples parse clean)* | — | — |
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
| M5 | Latent `inlist()` ceiling | S3 | WP-22 |
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
