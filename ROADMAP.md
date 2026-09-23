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

## WP-10 · Server layer defects

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

## WP-11 · Server facets

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
- `scheme` legend_position/legend_cols are parsed and consumed by nothing in
  either mode; not activated here, since that would move every s2color
  legend in both modes without a Stata measurement.

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
  silence.

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
`xscale(bogus)`, `barwidth(abc)`); one note (`connect(bogus)`, pending);
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
  14pt where Stata draws 8pt.
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
  4.667). Not fixed here; recorded as a follow-up.
- s1rcolor's bar alpha 0.8 is scheme-driven (`intensity bar inten80`), not
  a defect; `p_mark_colors` equals `p_colors` in all 14 shipped schemes,
  so TR-16.5 exists for user schemes only.
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
that tolerance.

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
| The BokehJS sink walk | text nodes and canvas text everywhere except a slider-family title holding a TeX pair (`innerHTML` after `process_tex`, which copies the text around the TeX raw), a Div's MathJax pass (`\href{javascript:}` a live link), and a tooltip field `@{name}` (parsed as HTML after filling) |
| `dash_setup` | a crafted version string reached `Version("...")` as code and created a marker file; a renderer directory whose name closed `r"..."` ran `sfi.Macro.setGlobal` |

### Technical requirements, as delivered

- **TR-20.1 / TR-20.2** Two policies, both `default-src 'none'`:
  `_DASH_CSP_STANDALONE` (scripts and styles inline only, images and fonts
  from `data:`, `connect-src 'none'`, `object-src 'none'`, `base-uri 'none'`,
  `form-action 'none'`) and `_DASH_CSP_SERVED` (the same with `'self'` and
  `connect-src 'self'` for the websocket).  `_dash_csp_meta` refuses any
  character a policy does not need.  The meta is the first element of
  `<head>` on both saved pages (the `layout(bs)` page had it after the
  inlined BokehJS -- `BUGS.md`) and on the served page, through a Bokeh
  document template (`_dash_served_template`, set in `make_document`).  The
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
  in the formatter's `args`, not its code.
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
  the meta first in `<head>` on every page, and nine against a live served
  app on a free port -- the headers on `/` and `/health`, the meta in the
  document, a session and its websocket.  Checked in Chromium on the real
  served app: headers and meta present, websocket open, no violation.
- **AC-20.2** `test_label_sinks.py` (918 tests): a hostile label through
  every sink in both modes, the TeX and MathJax paths, the tooltip field,
  the served app's source; checked in Chromium in both modes (text shown, no
  `<img>`).
- **AC-20.3** `test_adversarial_matrix.py` (202 tests: the registry and its
  gap tests), `test_adversarial.cscript` P20-01..29,
  `test_setup_injection.cscript` INJ-01..11, `test_echo_text.cscript`
  ECH-01..09.

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
