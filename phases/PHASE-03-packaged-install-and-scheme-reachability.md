# Phase 03 — Packaged install and scheme reachability

**Purpose.** `dash` installed the advertised way — `net install dash` — silently throws
away every scheme it ships. Stata routes the manifest into letter subdirectories
(`dash_render.py` → `<dir>/py/`, `s1color.scheme` → `<dir>/s/`, `economist.scheme` →
`<dir>/e/`), while `SchemeParser` searches only two directories, both siblings of
`dash_render.py` itself. From `<dir>/py/` those are `<dir>/py/schemes` and `<dir>/py`,
neither of which exists, so all 14 translated StataCorp schemes are inert as installed
and every user gets built-in defaults instead. The build still returns rc 0 and still
writes a file, so nothing fails loudly. This phase widens the scheme search to the
layout Stata actually creates, and then replaces the `shutil` model of `net install`
with a certification script that performs a **real** `net install`, puts only that
directory on the adopath, and proves a named scheme survives it — for one graph and
then for the whole example set. It also closes the packaging regression net that
ultraplan TR-02.4 named and 02-01 did not deliver, and fixes `dash.pkg`'s missing
version metadata so `adoupdate` can work at all. It is the smallest change in the
programme with the largest correctness gain, it depends on nothing, and it unblocks the
fifth release gate (`clean net install runs every example`) — the first four gates pass
at HEAD (3,498 passed / 37 skipped; 25/25 cscripts) and the fifth fails on exactly this
defect.

---

## At a glance

| | |
|---|---|
| **Work items** | 5 |
| **Functional / deliverable** | 1 functional · 4 deliverable |
| **Effort mix** | 4 small · 1 medium |
| **Renderers touched** | standalone (`DashRenderer`) ×1 · Stata/packaging ×3 · n/a (pytest) ×1. The one code fix lands in `SchemeParser`, which **both** renderers resolve through, so `ServerAppBuilder` inherits it. |
| **Ultraplan tasks discharged** | **02-04** (the packaged-install certification script — one of only two NOT_DONE tasks in the whole 89-task plan); the unverified half of **02-02** ("Verify empirically with a real `net install` … do not assume"); the regression net **TR-02.4** names, missing from **02-01** |
| **Sections advanced** | **S02** (`1/2/1` DONE/PARTIAL/NOT_DONE → target `4/0/0`); **S03** — all 14 translations are exact but inert once installed, and this is what makes them reach a user; **S11** — scheme consumption is moot in a packaged install until this lands |
| **Depends on** | Nothing. Wave 1, runnable immediately and in parallel with Phases 01, 02 and 04. |
| **Unblocks** | **Phase 31** (release gates — gate 5, `clean net install runs every example`, fails at HEAD on exactly this defect); **Phase 08** (its server-side packaged-install cscript case becomes meaningful only once the search paths are right); **Phases 23–25** (scheme consumption work has no user-visible effect in an installed package until schemes are reachable) |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md` §1, §7 and the status tables.
It was measured by running Stata against a real install, not modelled.

### The blocker, as reproduced

> ## 1. Blocker — `net install` breaks every scheme  [S02, S03, S11]
>
> Reproduced end to end with Stata, not modelled:

```
net set ado "<clean dir>"
net install dash, from("<repo>")     -> rc 0, "installation complete."
```

Stata routes the manifest into **letter subdirectories**:

| manifest line | where Stata actually puts it |
|---|---|
| `f dash.ado` | `<dir>/d/dash.ado` |
| `f dash_render.py` | `<dir>/py/dash_render.py` |
| `f schemes/s1color.scheme` | `<dir>/s/s1color.scheme` |
| `f schemes/economist.scheme` | `<dir>/e/economist.scheme` |

`SchemeParser` searches exactly two places, both relative to
`dash_render.py` (`dash_render.py:1524-1532`):

```python
_SCHEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")
_SCHEME_SEARCH_DIRS = (_SCHEMES_DIR, os.path.dirname(os.path.abspath(__file__)))
```

From `<dir>/py/` that is `<dir>/py/schemes` and `<dir>/py` — neither exists.
The comment above those lines anticipates *one* flattening
(`<install dir>/x.scheme`); Stata uses a third layout it does not cover.

Measured from the installed copy:

```
. dash scatter mpg weight, name(g1) scheme(s1color)
. dash build, saving(...)
UserWarning: dash: scheme 's1color' was not found ... using s2color
UserWarning: dash: no scheme file could be resolved for the dashboard
  (searched <dir>/py/schemes, <dir>/py). Falling back to built-in defaults.
  The package's schemes/ directory appears to be missing
```

The build returns rc 0 and writes a file, so nothing fails loudly. Every
installed user silently gets built-in defaults instead of the translated
StataCorp schemes.

### Why no test caught it

> **Why no test caught it.** `test/test_packaging.py:89-123` is a
> `shutil` model of `net install` — "no network, no Stata" — and models only
> two layouts, `flat` (basename in dest) and `as-declared` (keeps `schemes/`).
> Stata's real layout is neither. S02-04 asked for an "end-to-end
> packaged-install certification script" and S16-06 for "`net install` into a
> clean directory ... and run every example"; **no cscript performs a
> `net install`** (`grep -rn "net install" test/*.cscript` → nothing).

Re-run while writing this document, at `187a786`: `grep -rn "net install" test/*.cscript`
still returns nothing across all 25 certification scripts.

### Scope of the damage, measured

> **Scope, measured.** The package otherwise works: all **12 example do-files
> run from the packaged install with rc 0**. But **all 12 also emit the
> scheme-fallback warning** — so the breakage is exactly and only the scheme
> layer, and it is silent at the Stata prompt.

That is the whole shape of this phase: nothing else about the package is broken, and
the one thing that is broken is invisible from the Stata prompt.

### What `REMAINING.md` prescribes

> **Work:** widen the scheme search to the sibling letter directories (and the
> install root), *and* replace the shutil model with a cscript that does a real
> `net install` and asserts a named scheme survives it.

And in the suggested order, this phase is item 1 of 6:

> 1. **Scheme search paths + a real `net install` cscript.** Smallest change,
>    largest correctness gain, and it unblocks the S16-06 release gate.

### Where it leaves the section tallies

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 02 | Packaging (`net install`) | 4 | **partial** ① | real `net install` cscript; scheme search paths |
| 03 | Scheme translation | 5 | 3 done, 2 partial ② | `color foreground`; all 14 inert once installed ① |

Per-section DONE / PARTIAL / NOT DONE at HEAD: **S02 = 1/2/1**. From the final tally:

> The two NOT_DONE are 02-04 (the packaged-install cscript) and 16-07 (close-out, which
> is gated on everything else).

And from the 17 DONE claims the adversarial pass overturned:

| task | what the refutation found |
|---|---|
| 02-01 | the manifest test is strong, but the regression net TR-02.4 names is absent |

### The release gate this blocks

> ## Gates still to pass (S16-07)
>
> full pytest · full certification suite with honest skips · conformance corpus
> (zero `r(198)`, zero dropped series, zero dropped graphs) · parity corpus ·
> clean `net install` runs every example · adversarial suite.
>
> At HEAD the first four pass (3,498 passed / 37 skipped; 25/25 cscripts);
> the fifth fails on §1.

S16-06 is the task that widens 02-04 to the whole corpus:

> **`net install` + run every example** — the gate S16-06 names. Item 1 above
> means it does not pass today.

### The advisory item

> ### Advisory, outside the plan
>
> `dash.pkg` carries its version only as prose (`d Version: 1.0.0 25mar2026`).
> There is no `v` line and no `d Distribution-Date:` line, so `adoupdate` can
> never detect an update, and the stated date is six months stale. The manifest
> itself is complete — all 20 declared files exist and nothing shippable is
> missing.

### The server renderer is in scope by inheritance

From Appendix C, filed under 15-03 (the item itself belongs to Phase 08; the evidence
belongs here because the root cause is the one this phase fixes):

> The task's packaged-install clause is still open in
> its superseded form: `ServerAppBuilder.__init__` resolves the scheme at
> BUILD time through `SchemeParser.resolve_or_fallback`, so the S02/S03
> net-install layout defect (dash_render.py lands in `<dir>/py/`, schemes in
> `<dir>/s/`) silently degrades server mode to built-in defaults too. No cscript
> builds a server app with a scheme from a net-installed copy.
> *Where:* `dash_render.py:12311 (ServerAppBuilder.__init__ scheme resolution);
> SchemeParser search dirs at dash_render.py:1524-1532;
> test/test_server_build.cscript is the place to add the packaged-install case`

One fix in `SchemeParser` therefore repairs both renderers. Phase 08 owns the *test* for
the server arm; Phase 03 owns the fix.

### Source confirmation (read at `187a786`, consistent with the above)

These were checked in the tree to make the work items actionable. They confirm
`REMAINING.md`; they do not amend it.

- `dash_render.py:1524-1532` reads exactly as quoted, comment included.
- `SchemeParser.resolve_or_fallback` is at `dash_render.py:1589`; the two warning strings
  quoted in the measurement are emitted at `:1609-1616` (unknown name) and `:1617-1625`
  (nothing resolvable).
- Four call sites resolve through it, so one fix serves all of them:
  `GlyphMapper.__init__` (`:2489`) at `:2500`; `DashRenderer.__init__` (`:8042`) at
  `:8099`; `DashRenderer._make_figure` (`:9459`) at `:9486`; `ServerAppBuilder.__init__`
  (`:12291`) at `:12311`.
- `dash.pkg` declares 20 `f` lines: 6 top-level files plus the 14 schemes. Applying the
  two scheme rows the audit measured, 13 of the 14 (`s1color` … `stsj`, including `sj`)
  land in `<dir>/s/` and `economist` alone lands in `<dir>/e/`.
- `dash.ado` locates the renderer with `capture findfile dash_render.py`
  (`dash.ado:1731-1747`, `:2464-2480`, `:2608-2621`), which is why the *command* still
  works from `<dir>/py/`; the last-resort fallback in each of those blocks is
  `` local render_py "`c(sysdir_plus)'d/dash_render.py" ``, which assumes the `d/`
  directory and would not find the installed copy if `findfile` ever failed.
- `examples/` holds 12 do-files: `basic_scatter.do`, `bootstrap_equal_cols.do`,
  `bootstrap_kpi_hero.do`, `bootstrap_responsive.do`, `bootstrap_stacked.do`,
  `comprehensive_demo.do`, `feature_tour.do`, `full_dashboard.do`,
  `geometry_responsive.do`, `kelly22ex_categorical.do`, `multi_graph_dashboard.do`,
  `sp500_dates.do` — matching the "all 12" measurement.

---

## Epics

| epic | goal | items |
|---|---|---|
| **E3.1 — Reachability** | The 14 shipped schemes resolve from the directory layout Stata's `net install` actually creates, without widening the path-traversal surface. | 1 |
| **E3.2 — Proof by installation, not by model** | Replace the `shutil` model with a real `net install` certification script; extend it to every example; close the packaging regression net TR-02.4 named. | 2, 3, 5 |
| **E3.3 — Manifest metadata** | `dash.pkg` carries machine-readable version and distribution-date lines so `adoupdate` can detect a release. | 4 |

---

## User stories

### E3.1 — Reachability

**US-3.1.1** — *As a Stata user who installed `dash` with `net install`, I want
`scheme(s1color)` to actually apply s1color, so that the dashboard looks like the Stata
graphs beside it rather than silently falling back to built-in defaults.*

- **Given** a clean directory holding only a real `net install` of `dash`, and only that
  directory on the adopath,
  **when** I run `dash scatter mpg weight, name(g1) scheme(s1color)` followed by
  `dash build, saving(out.html)`,
  **then** the command returns rc 0, **and** `out.html` carries s1color's palette
  (`color p1 #006000` from `schemes/s1color.scheme:54`) rather than s2color's
  (`#1a476f`, `schemes/s2color.scheme:49`).
- **Given** the same install,
  **when** any `dash build` runs,
  **then** neither `dash: scheme 's1color' was not found` nor
  `no scheme file could be resolved … The package's schemes/ directory appears to be
  missing` appears in the log.
- **Given** the same install,
  **when** each of the 14 shipped scheme names is requested in turn,
  **then** all 14 resolve from a file — `SchemeParser.is_fallback` is `False` and
  `SchemeParser.name` equals the requested name for each.

**US-3.1.2** — *As a `dash serve` operator, I want the served app to carry the scheme I
asked for, so that the served dashboard and the standalone HTML look the same on a
machine that installed the package rather than cloned the repo.*

- **Given** a packaged install,
  **when** `ServerAppBuilder` resolves its scheme at build time
  (`dash_render.py:12311`),
  **then** it gets the requested scheme file, not `SchemeParser.fallback()`.

**US-3.1.3** — *As a package maintainer, I want the widened search to stay inside
directories derived from the package's own location, so that adding search paths does
not hand a caller a new path-traversal surface.*

- **Given** a `scheme()` value containing `..`, an absolute path, or an embedded
  separator,
  **when** `SchemeParser._resolve_path` (`dash_render.py:1691-1714`) validates it,
  **then** it is rejected exactly as it is today, because every directory added to
  `_SCHEME_SEARCH_DIRS` is derived from `__file__` and from nothing else.
- **Given** `test/test_path_validation.cscript` and the traversal tests in
  `test/test_packaging.py`,
  **when** the suite runs after the change,
  **then** they pass unchanged — no assertion was relaxed to make room for a new
  directory.

### E3.2 — Proof by installation, not by model

**US-3.2.1** — *As a package maintainer, I want a certification script that installs
`dash` the way a user does, so that the next packaging regression is caught by a test
instead of by a user.*

- **Given** a temporary directory and `net set ado` pointed at it,
  **when** `test/test_netinstall.cscript` runs `net install dash, from(<repo>)` and puts
  only that directory on the adopath,
  **then** a full `dash scatter` + `dash build` cycle completes with rc 0 and a named
  scheme is demonstrably applied.
- **Given** a machine without Python, `jsonio` or `bokeh`,
  **when** the script runs,
  **then** it exits 222 (the suite's skip convention) with a message naming the missing
  dependency — it never reports a pass it did not earn.
- **Given** `test/run_all_cscripts.do`,
  **when** the full certification suite runs,
  **then** the new script appears in the numbered RUN/PASS/SKIP/FAIL sequence and the
  count rises from 25 to 26.

**US-3.2.2** — *As a Stata user pasting a `twoway` command from the documentation, I
want every shipped example to run from an installed copy, so that the examples are a
promise about the package and not about the author's working tree.*

- **Given** the packaged install from US-3.2.1,
  **when** all 12 do-files in `examples/` are executed against it,
  **then** every one returns rc 0 **and** none emits the scheme-fallback warning — the
  before state was 12/12 rc 0 with 12/12 warning.

**US-3.2.3** — *As a package maintainer, I want the pytest packaging model to know about
the layout Stata really uses, so that the fast test catches the defect in seconds
instead of waiting for the Stata run.*

- **Given** `stage_package` (`test/test_packaging.py:89-123`),
  **when** it is asked for the net-install layout,
  **then** it places `dash_render.py` in `py/` and each scheme in its letter directory,
  and the existing `staged_install` assertions run against that layout too.
- **Given** the regression net TR-02.4 names,
  **when** the suite runs,
  **then** it asserts render-from-install, no-fallback-warning, and all-14-schemes-
  resolvable under every modelled layout, not only manifest completeness.

### E3.3 — Manifest metadata

**US-3.3.1** — *As a Stata user who installed `dash` months ago, I want `adoupdate` to
tell me when a newer `dash` exists, so that I am not stuck on a stale copy without
knowing it.*

- **Given** `dash.pkg` with a `v` line and a `d Distribution-Date:` line,
  **when** `adoupdate` inspects the installed package against the distribution source,
  **then** it can compare and report — today it can never detect an update at all.
- **Given** the release,
  **when** the manifest is read,
  **then** the stated date is the real distribution date, not `25mar2026`, which is six
  months stale.

---

## Business requirements

| id | requirement | how it is tested |
|---|---|---|
| **BR-03.1** | A clean `net install` produces a working `dash` with no setup beyond `dash_setup`. *(carried from S02 BR-02.1)* | `test/test_netinstall.cscript` |
| **BR-03.2** | A missing or unparseable scheme never tracebacks; it degrades with a message the user can act on. *(carried from S02 BR-02.2 — preserved, not regressed)* | `test/test_packaging.py` warning tests |
| **BR-03.3** | Every scheme the package ships — all 14 — is selectable by name from a packaged install. | cscript loop over `_BUILTIN_NAMES`; pytest letter-layout arm |
| **BR-03.4** | No `dash` command run from a packaged install emits `The package's schemes/ directory appears to be missing`. | log assertion in the cscript; `pytest.warns` negative in pytest |
| **BR-03.5** | The claim "`net install` works" is established by installing, not by modelling. A `shutil` copy is a supporting test, never the proof. | the cscript is the gate; the pytest model is the fast guard |
| **BR-03.6** | All 12 shipped examples run from the packaged install with rc 0 **and** with the requested scheme applied. | example loop inside `test/test_netinstall.cscript` |
| **BR-03.7** | Widening the scheme search adds no new path-traversal surface: every added directory is derived from the package's own location. | `test/test_path_validation.cscript`; traversal tests in `test/test_packaging.py` |
| **BR-03.8** | `adoupdate` can detect a new release of `dash`. | manifest lint test in `test/test_packaging.py` |
| **BR-03.9** | Every defect fixed here has a regression test that failed before the fix. *(project rule 8)* | recorded in the Definition of done |

---

## Technical requirements

### TR-03.1 — Widen `_SCHEME_SEARCH_DIRS` to Stata's install layout

*File:* `dash_render.py:1524-1532`, class `SchemeParser` (`:1509`).

Today:

```python
_SCHEMES_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")

# A `net install` may flatten a `f schemes/x.scheme` manifest line to
# `<install dir>/x.scheme` instead of preserving the subdirectory.  Search
# both layouts so the package works however Stata chose to place the files.
_SCHEME_SEARCH_DIRS: "tuple[str, ...]" = (
    _SCHEMES_DIR,
    os.path.dirname(os.path.abspath(__file__)),
)
```

The search must additionally cover, with `_PKG_DIR = os.path.dirname(os.path.abspath(__file__))`
and `_INSTALL_ROOT = os.path.dirname(_PKG_DIR)`:

| candidate | covers |
|---|---|
| `_SCHEMES_DIR` | development tree (`<repo>/schemes/`) — **keep first** |
| `_PKG_DIR` | the flattening the current comment anticipates |
| `_INSTALL_ROOT` | `net install` that drops files at the install root |
| `_INSTALL_ROOT/<letter>/` | Stata's measured layout — `<dir>/s/s1color.scheme`, `<dir>/e/economist.scheme` |
| `_INSTALL_ROOT/schemes/` | a `schemes/` subdirectory preserved beside `py/` |

Ordering matters: the development tree must stay first so a repo checkout cannot be
shadowed by an unrelated directory above it. The comment must be rewritten — it
currently states that two layouts are enough, which the measurement disproves.

### TR-03.2 — Derive the letter directory from the scheme name, do not enumerate

`_resolve_path` already builds a *candidate list* per name. The letter directory is
`name[0].lower()` (`s1color` → `s/`, `economist` → `e/`), so the candidate is
constructible without listing `_INSTALL_ROOT`. No `os.listdir`, no `glob`, no walking:
a fixed, small candidate set per call, so the change costs nothing at render time
(project rule 14 — no performance penalty). `_INSTALL_ROOT` may not exist or may not be
readable; every candidate must be tried with the same `os.path.isfile` guard the
existing code uses, and a non-existent directory must not raise.

### TR-03.3 — The allow-list is derived from the search dirs, so keep the derivation pure

*File:* `dash_render.py:1691-1714`, `SchemeParser._resolve_path`.

```python
# Security: a resolved path must lie within an allowed directory.
# Loop-invariant, so computed once.
allowed = [os.path.abspath(d) for d in search_dirs]
allowed.append(os.path.abspath(os.getcwd()))
```

`allowed` is computed **from `_SCHEME_SEARCH_DIRS`**. Every directory added by TR-03.1
therefore becomes an allowed root for the traversal check as well. Consequences that are
binding on the implementation:

1. Added directories must be computed from `__file__` only — never from an environment
   variable, a Stata local, a spec-JSON key or anything else a caller controls.
2. `_INSTALL_ROOT` is one level up from the package; it must not be climbed further. No
   `os.path.dirname` chain, no `..` segments left unnormalised in a candidate.
3. The candidate/allow-list comparison (`candidate.startswith(d + os.sep) or candidate == d`)
   stays exactly as it is. Nothing is relaxed to admit the new layout.
4. The CWD candidate is untouched here. Retiring it is S11-05's job (a later phase);
   this phase must leave that retirement easy, so the install-layout directories should
   be assembled in one place that the S11 work can edit without re-deriving the layout
   logic.

### TR-03.4 — One fix, four consumers, both renderers

All scheme resolution funnels through `SchemeParser.resolve_or_fallback`
(`dash_render.py:1589`):

| call site | owner | mode |
|---|---|---|
| `:2500` | `GlyphMapper.__init__` (`:2489`) | both |
| `:8099` | `DashRenderer.__init__` (`:8042`) | standalone |
| `:9486` | `DashRenderer._make_figure` (`:9459`) | standalone (per-figure `scheme()`) |
| `:12311` | `ServerAppBuilder.__init__` (`:12291`) | server, resolved at **build** time |

No call site changes. `ServerAppBuilder` resolving at build time is what makes the
server renderer inherit the fix, and is also why the emitted app carries whatever the
builder resolved — a fallback baked in at build time cannot be recovered at serve time.

### TR-03.5 — The two warning strings are the test surface

*File:* `dash_render.py:1589-1625`.

```python
warnings.warn(
    f"dash: scheme {candidate!r} was not found for "
    f"{context}; using s2color. Supported schemes: "
    f"{', '.join(sorted(cls._BUILTIN_NAMES))}. "
    f"({exc})",
    UserWarning, stacklevel=3,
)
...
warnings.warn(
    f"dash: no scheme file could be resolved for {context} (searched "
    f"{', '.join(cls._SCHEME_SEARCH_DIRS)}). Falling back to built-in "
    "defaults. The package's schemes/ directory appears to be missing "
    "— reinstall dash or run dash_setup.",
    UserWarning, stacklevel=3,
)
```

Both must still fire when the schemes genuinely are absent (BR-03.2 — S02-03's
degradation contract is preserved). Neither may fire from a correct packaged install
(BR-03.4). Note that the second warning interpolates `_SCHEME_SEARCH_DIRS`, so after
TR-03.1 its text lists the widened set — any test that pins the old two-directory string
must be updated deliberately, and the message remains the user's diagnostic.

### TR-03.6 — `fallback()` is indistinguishable by name, so assert on `is_fallback`

*File:* `dash_render.py`, `SchemeParser.fallback()`:

```python
inst._props = dict(cls._FALLBACK_PROPS)
# _FALLBACK_PROPS mirrors s2color, so that is what this renders as;
# is_fallback records that no file was read, which the name alone
# cannot express.
inst.name = "s2color"
inst.is_fallback = True
```

A degraded scheme reports `name == "s2color"`, identical to a genuine s2color. Python-level
assertions must therefore use `is_fallback is False`, not the name, or they certify
nothing.

### TR-03.7 — Discriminating colours for output-level assertions

Asserting on rendered output is stronger than asserting on a warning. Use a scheme whose
palette differs from the fallback:

| scheme | `color p1` | source |
|---|---|---|
| `s1color` | `#006000` | `schemes/s1color.scheme:54` (`color p1line #006000` at `:71`) |
| `s2color` | `#1a476f` | `schemes/s2color.scheme:49` (`color p1line #1a476f` at `:69`) |
| `economist` | `#3e647d` | `schemes/economist.scheme:57` (`color p1line #3e647d` at `:77`) |

Because `_FALLBACK_PROPS` mirrors s2color, a test that builds with `scheme(s1color)` and
finds `#006000` in the HTML has ruled out both "s2color was used instead" and "the
in-memory fallback was used". `economist` is the second useful probe: it is the only one
of the 14 that lands in `<dir>/e/`, so it exercises a different letter directory from
the other 13.

### TR-03.8 — Certification-script mechanics

*New file:* `test/test_netinstall.cscript`. Conventions taken from the existing 25
scripts and from `test/run_all_cscripts.do`:

- Header `cscript "dash net install" adodir ".."`, `*!` banner explaining why the file
  exists, in the style of `test/test_examples_run.cscript`.
- Dependency gates **before** any work, each `exit 222` with a `SKIP:` message:
  `capture which jsonio`; `if "\`c(python_exec)'" == ""` (never probe Python by running
  it — see `test/test_cscript_hygiene.py`); then `bokeh` import.
- `global dash_nobrowser 1` before the first build. A verification loop that opens a
  browser window per example takes over the user's desktop.
- Install into a fresh temp directory: `net set ado "<tmp>"`, then
  `net install dash, from("<repo>")`, expecting rc 0 and `installation complete.`
- **Adopath isolation is the point of the test.** Only the install directory (plus
  whatever `jsonio` needs) may be on the path; the repo must not be, or the test proves
  nothing. Save and restore the caller's adopath so the runner's later scripts are
  unaffected.
- Print the installed tree once (`dir` recursion or `findfile` on each declared file) so
  the real layout is *observed*, not assumed. The four rows the audit measured generalise
  to "`.py` → `py/`, everything else → `<first letter of basename>/`", but the cscript is
  what settles any file the measured table does not cover — and `test_packaging.py`'s
  model (TR-03.9) must be built from what the cscript observes, never the other way round.
- Assert positively (`#006000` present in the built HTML) and negatively (neither warning
  string in the log), per TR-03.5 and TR-03.7.
- Restore `net set ado` and the working directory on exit, including on failure.
- Register it in `test/run_all_cscripts.do` as a numbered block matching the existing
  `[ RUN ] / [ PASS ] / [ SKIP] / [ FAIL ]` shape, feeding `n_pass` / `n_fail` / `n_skip`.
- Run the suite as its own header documents:
  `arch -arm64 /usr/local/bin/stata-mp -b do test/run_all_cscripts.do` — on Apple silicon
  the x86_64 slice cannot load the arm64 `libpython`, and a skip is not a pass.

### TR-03.9 — Extend the packaging model to the real layout

*File:* `test/test_packaging.py`, `stage_package` (`:89-123`), fixture `staged_install`
(parametrised `["flat", "as-declared"]`).

```python
def stage_package(dest: str, layout: str = "flat") -> list[str]:
    """Copy exactly the files ``dash.pkg`` declares into *dest*.

    This is a pure-``shutil`` model of ``net install`` — no network, no Stata,
    and deliberately nothing that the manifest does not name.
    ...
        layout: ``"flat"`` installs each file under its basename (Stata's
                documented ``f`` behaviour); ``"as-declared"`` preserves any
                directory component written in the manifest.
    """
```

Add a third layout — `"net-install"` — that reproduces what the cscript observes:
`dash_render.py` → `<dest>/py/`, `dash.ado`/`dash.sthlp` → `<dest>/d/`, each
`schemes/<x>.scheme` → `<dest>/<x[0]>/`. Add it to the fixture's `params` so
`test_dashrenderer_constructs_from_packaged_install` (`:208`) and
`test_glyphmapper_constructs_from_packaged_install` (`:238`) run against it. The fixture
already `monkeypatch.chdir`s into the install root so the repo's own `schemes/` cannot
leak in through a relative lookup — that property must be preserved for the new layout,
and it is what makes the new arm fail today.

### TR-03.10 — The regression net TR-02.4 names

TR-02.4 reads: *"A certification test installs into a temp directory from the `.pkg`
manifest and renders, so the defect cannot return."* `test_pkg_manifest_lists_every_runtime_file`
(`test/test_packaging.py:328`) is the manifest-completeness half and is strong. Missing
is the net around it. Add, under each modelled layout:

1. a render-to-HTML test (not merely a constructor test) that writes a file and asserts
   the scheme palette reached the output;
2. a no-fallback-warning test — `warnings.catch_warnings(record=True)` around the build,
   asserting no message contains `appears to be missing`;
3. an all-14 test — every name in `SchemeParser._BUILTIN_NAMES` resolves with
   `is_fallback is False` (this is the test that catches a scheme added to `schemes/`
   but never added to `dash.pkg`, and the one that proves S03's 14 translations are
   reachable rather than merely correct);
4. a traversal test asserting the widened `allowed` list still rejects `..`, absolute
   paths and separator-bearing names (TR-03.3).

### TR-03.11 — `dash.pkg` version metadata

*File:* `dash.pkg`. Current state — version as prose only:

```
d Version: 1.0.0  25mar2026
```

Add a `v` line and a `d Distribution-Date:` line in the form `adoupdate` reads, and set
the date to the real distribution date. The 20 `f` lines are complete and correct — all
declared files exist and nothing shippable is missing — so this is metadata only, and it
is explicitly advisory (outside the plan) rather than an ultraplan task. Guard it with a
manifest lint in `test/test_packaging.py` so it cannot silently rot again.

### TR-03.12 — Renderer location (context, not work)

`dash.ado` finds the renderer with `capture findfile dash_render.py`
(`dash.ado:1731-1747`, `:2464-2480`, `:2608-2621`), which searches the whole adopath and
so succeeds from `<dir>/py/`. That is why the *command* works from a packaged install
while the *schemes* do not. The last-resort branch in each of those three blocks is
`` local render_py "`c(sysdir_plus)'d/dash_render.py" ``, which assumes `d/`; it is
unreached while `findfile` succeeds. No change is required by this phase — but the
cscript's installed-tree printout (TR-03.8) is the measurement that would reveal it if
`findfile` ever stopped covering the layout.

---

## Work items

All five items, numbered as handed over.

### 1 — Widen the scheme search to Stata's real install layout

`[func · standalone · small]`

> Widen `SchemeParser`'s scheme search to the sibling letter directories Stata's
> `net install` actually creates (`<install>/s/`, `<install>/e/`, …) and to the install
> root, so the 14 translated schemes are reachable from a packaged install.

*Where:* `dash_render.py:SchemeParser._SCHEME_SEARCH_DIRS (:1524-1532)`, `_resolve_path`.

*Evidence:* `REMAINING.md` §1. Stata puts `s1color.scheme` in `<dir>/s/` and
`dash_render.py` in `<dir>/py/`; the search covers `<dir>/py/schemes` and `<dir>/py`.
Measured result: `scheme 's1color' was not found … using s2color`, then
`no scheme file could be resolved … (searched <dir>/py/schemes, <dir>/py)`, rc 0
throughout. Tagged `standalone` because that is where the class lives, but
`ServerAppBuilder.__init__` (`:12311`) resolves through the same classmethod, so the fix
carries to server mode. Requirements: TR-03.1, TR-03.2, TR-03.3, TR-03.4.

### 2 — Replace the `shutil` model with a real `net install` certification script

`[deli · stata · medium]`

> Replace the `shutil` model of `net install` with a certification script that performs a
> real `net install` into a clean directory, puts only that directory on the adopath, and
> asserts a named scheme survives it. This is task 02-04, the only NOT_DONE in S02.

*Where:* `test/test_netinstall.cscript` (new), `test/test_packaging.py:stage_package (:89-123)`.

*Evidence:* `REMAINING.md` §1 — `test/test_packaging.py:89-123` is a `shutil` model,
"no network, no Stata", modelling only `flat` and `as-declared`; Stata's real layout is
neither. `grep -rn "net install" test/*.cscript` returns nothing across all 25 scripts,
re-confirmed at `187a786`. 02-04 is one of only two NOT_DONE tasks in the 89-task plan.
Requirements: TR-03.8, TR-03.9.

### 3 — Run every example from the packaged install in the same script

`[deli · stata · small]`

> Run every example from the packaged install as part of the same cscript — S16-06 widens
> 02-04 to the whole example set. All 12 run with rc 0 today but all 12 emit the
> scheme-fallback warning.

*Where:* `test/test_netinstall.cscript`, `examples/*.do`.

*Evidence:* `REMAINING.md` §1 ("all 12 example do-files run from the packaged install
with rc 0 … all 12 also emit the scheme-fallback warning") and §7 ("`net install` + run
every example — the gate S16-06 names. Item 1 above means it does not pass today").
S16-06's own text: *"net install into a clean directory, put only that directory on the
adopath, and run every example. This is S02's cscript widened to the whole example set."*
`test/test_examples_run.cscript` already enumerates the corpus with
`` local files : dir "`exdir'" files "*.do" `` and is the model to copy — the difference
is that this loop runs against the install directory, not the repo. Requirements:
TR-03.8, BR-03.6.

### 4 — Give `dash.pkg` machine-readable version metadata

`[deli · stata · small]`

> `dash.pkg` carries its version only as prose and has no `v` line and no
> `d Distribution-Date:`, so `adoupdate` can never detect an update; the stated date
> (25mar2026) is six months stale. Advisory — outside the plan.

*Where:* `dash.pkg`.

*Evidence:* `REMAINING.md` §7, "Advisory, outside the plan". The manifest itself is
complete — all 20 declared files exist and nothing shippable is missing — so this is
metadata only. Requirements: TR-03.11, BR-03.8.

### 5 — Close the packaging regression net TR-02.4 names

`[deli · n/a · small]`

> Add the packaging regression net TR-02.4 names, which 02-01 did not deliver — the
> manifest-completeness test is strong but the regression net around it is absent.

*Where:* `test/test_packaging.py`.

*Evidence:* the adversarial pass overturned 02-01's DONE claim with exactly this finding:
*"the manifest test is strong, but the regression net TR-02.4 names is absent."*
TR-02.4: *"A certification test installs into a temp directory from the `.pkg` manifest
and renders, so the defect cannot return."* `test_pkg_manifest_lists_every_runtime_file`
(`:328`) covers completeness; render-from-install, no-warning and all-14-resolvable are
absent. Requirements: TR-03.9, TR-03.10.

---

## Test plan

Project rule 8: the regression test comes first and must fail before the fix. Project
rule 4: every function gets a unit test, and the application gets end-to-end coverage.
Rule 2 applies to this section in particular — a test that has not been *seen* to fail
has not been shown to work, and this repository has a documented history of tests that
passed against broken implementations.

### E3.1 — Reachability

**Write this first (must fail at HEAD).**
`test/test_packaging.py::test_dashrenderer_constructs_from_packaged_install` parametrised
with the new `"net-install"` layout (TR-03.9), strengthened to assert
`renderer.scheme.name == "s1color"` and `renderer.scheme.is_fallback is False` after
building with `scheme(s1color)`. At HEAD this must fail: the staged `dash_render.py` sits
in `py/`, `s1color.scheme` sits in `s/`, the search covers neither, and the renderer
comes back with `is_fallback True` and `name "s2color"` (TR-03.6). Read that failure
before writing any fix.

**Unit tests (rule 4).** In `test/test_packaging.py` unless noted:

| target | test |
|---|---|
| `SchemeParser._SCHEME_SEARCH_DIRS` | the tuple contains the package dir, the schemes dir, the install root and is free of `..` segments; every entry is absolute |
| letter-directory derivation (TR-03.2) | `s1color` → candidate under `s/`; `economist` → candidate under `e/`; name casing handled; no directory listing performed |
| `SchemeParser._resolve_path` | resolves from each of the five candidate roots in turn, with the development-tree root winning when two copies exist |
| `SchemeParser._resolve_path` traversal (TR-03.3) | `../../etc/passwd`, an absolute path and a separator-bearing name are all still rejected under the widened allow-list |
| `SchemeParser.resolve_or_fallback` | unknown name → first warning only; no schemes anywhere → both warnings and `fallback()`; correct install → **no** warning (`test/test_immediate_scheme.py` is the sibling file for scheme-name behaviour) |
| `SchemeParser.fallback` | `is_fallback is True` while `name == "s2color"`, so name-based assertions elsewhere are known-invalid |
| all 14 | every member of `_BUILTIN_NAMES` resolves with `is_fallback is False` from every modelled layout |

**Integration / cscript.** `test/test_netinstall.cscript` — the real install, the
`scheme(s1color)` build, the `#006000` assertion and the two negative log assertions.
`test/test_scheme_consumption.py` gets no new work here; it already covers what a
resolved scheme does, and this phase is about resolution.

**Mutation — how each test is proved non-vacuous.**

| break this | this must die |
|---|---|
| Revert `_SCHEME_SEARCH_DIRS` to the two-entry tuple at `:1529-1532` | the `"net-install"` layout arm; the cscript; the all-14 test |
| Drop only the install-root entry, keep the letter dirs | the install-root layout arm |
| Drop only the letter-dir candidate | the `"net-install"` arm and the cscript; the flat arm survives, proving the two are independent |
| Change the assertion target from `#006000` to `#1a476f` | the output assertion must now fail, proving it discriminates s1color from the fallback |
| Assert `scheme.name == "s1color"` *instead of* `is_fallback` | must be shown to pass against a deliberately-degraded scheme, which is why `is_fallback` is the assertion (TR-03.6) |
| Append `os.getcwd()`'s parent to `_SCHEME_SEARCH_DIRS` | the traversal tests and `test/test_path_validation.cscript` must fail |

### E3.2 — Proof by installation

**Write this first (must fail at HEAD).** `test/test_netinstall.cscript` itself, in its
minimal form: install, adopath, `dash scatter mpg weight, name(g1) scheme(s1color)`,
`dash build`, assert `#006000` in the HTML and assert the log carries neither warning.
At HEAD this fails on all three assertions while returning rc 0 from every `dash`
command — which is precisely the failure mode that made the defect invisible.

**Unit tests (rule 4).**

| target | test |
|---|---|
| `stage_package(layout="net-install")` | places `dash_render.py` under `py/`, schemes under their letter dirs, nothing else; returns the staged paths; asserts every declared file exists in the repo, as the current implementation already does |
| `parse_pkg_files` | still parses all 20 `f` lines after the manifest edit of item 4, including the new `v` and `d` lines being ignored as non-`f` directives |
| the example loop | a helper that enumerates `examples/*.do` sorted, so the count is asserted (12) rather than assumed — an empty glob must fail, not pass silently |
| runner registration | `test/test_cscript_hygiene.py` extended so that every `*.cscript` in `test/` appears in `test/run_all_cscripts.do`; this is what stops the new script from being written and never run |

**Integration / cscript.**

- `test/test_netinstall.cscript` — install; single-graph scheme proof; then the loop over
  all 12 examples from the install directory, asserting rc 0 per file **and** zero
  occurrences of `appears to be missing` across the run.
- `test/run_all_cscripts.do` — new numbered block; suite count 25 → 26.
- Skip accounting: with `jsonio`, Python or `bokeh` missing, the script exits 222 and the
  runner records a SKIP. A skip is not a pass, and the run summary must say so.

**Mutation.**

| break this | this must die |
|---|---|
| Put the repo back on the adopath inside the cscript | the cscript must still pass *only* because of the install — so re-add the repo and confirm the test would have passed spuriously; that is the proof the isolation is load-bearing |
| Remove one scheme `f` line from `dash.pkg` | the all-14 test and `test_pkg_manifest_lists_every_runtime_file` |
| Make the example loop's rc check `capture` without testing `_rc` | a deliberately broken example must then still "pass" — restore and confirm it fails |
| Point the example loop at `../examples` (the repo) instead of the install | the loop must be shown to fail when the install is incomplete, or it is testing the repo again |
| Delete the new block from `run_all_cscripts.do` | the hygiene test |

### E3.3 — Manifest metadata

**Write this first (must fail at HEAD).**
`test/test_packaging.py::test_pkg_declares_a_machine_readable_version` — parse `dash.pkg`,
assert a `v` line exists and that a `d Distribution-Date:` line exists and parses as a
date. Fails at HEAD, where the version is prose only.

**Unit tests (rule 4).** The date is not in the future and not stale beyond the release
being cut; the `v` line is a single integer as Stata's format requires; the prose
`d Version:` line, if kept, agrees with the machine-readable one — two version strings
that can disagree are worse than one.

**Mutation.** Remove the `v` line → the test dies. Set the distribution date back to
`25mar2026` → the staleness assertion dies. Make the prose and machine-readable versions
disagree → the agreement assertion dies.

### Suite-level gates for this phase

- Full pytest suite green (baseline at HEAD: 3,498 passed / 37 skipped).
- Full certification suite green with honest skips, 26/26 after this phase (25/25 at HEAD).
- `test/test_path_validation.cscript` green, unmodified.
- `test/test_examples_run.cscript` green, unmodified — the repo-side example run must not
  regress while the install-side one is added.

---

## Definition of done

- [ ] `test/test_packaging.py` has a `"net-install"` layout that reproduces `<dir>/py/`
      and `<dir>/s/`, and the failing-first test was run and its failure read before any
      fix was written (rule 8).
- [ ] `SchemeParser._SCHEME_SEARCH_DIRS` (`dash_render.py:1524-1532`) covers the schemes
      dir, the package dir, the install root, the install root's letter directories and
      `<root>/schemes/`; the stale comment about "both layouts" is rewritten.
- [ ] Letter directories are derived per scheme name, with no directory listing or glob
      (TR-03.2).
- [ ] Every added directory is derived from `__file__`; `_resolve_path`'s allow-list and
      its `startswith` check are unchanged in kind; `test/test_path_validation.cscript`
      and the traversal tests pass unmodified (TR-03.3, BR-03.7).
- [ ] All 14 shipped schemes resolve with `is_fallback is False` from every modelled
      layout (BR-03.3).
- [ ] A packaged-install build with `scheme(s1color)` emits HTML containing `#006000` and
      not `#1a476f` (TR-03.7).
- [ ] No `dash` command from a correct packaged install emits
      `The package's schemes/ directory appears to be missing` (BR-03.4).
- [ ] The degradation contract still holds: with `schemes/` genuinely absent, both
      warnings fire and nothing tracebacks (BR-03.2).
- [ ] `test/test_netinstall.cscript` exists, performs a real `net install`, isolates the
      adopath, restores it and `net set ado` on every exit path, and skips with `exit 222`
      when `jsonio`, Python or `bokeh` is unavailable (TR-03.8).
- [ ] The cscript prints the installed tree, so the layout is recorded by measurement.
- [ ] The cscript runs all 12 examples from the install with rc 0 and zero fallback
      warnings (BR-03.6).
- [ ] `test/run_all_cscripts.do` registers the new script; the suite reports 26/26 with
      honest skips; the run used `arch -arm64`.
- [ ] The regression net TR-02.4 names is present: render-from-install, no-fallback-warning,
      all-14-resolvable, traversal-still-blocked (item 5).
- [ ] `dash.pkg` carries a `v` line and a `d Distribution-Date:` line with a real date,
      guarded by a manifest lint (item 4).
- [ ] Every mutation in the test plan was applied and the named test observed to fail,
      then reverted.
- [ ] Full pytest and full certification suite green against the S01 baseline before any
      commit (rule 5); commit on `feature/batch4-interactive-layer`, with the merge
      command reported rather than run (rule 6), and no Claude/Anthropic reference in the
      message (rule 7).
- [ ] `BUGS.md` records the defect and the test that guards it, in the existing style,
      for S16-07 to reconcile.

---

## Risks and sequencing notes

**This phase has no upstream dependencies and should start immediately.** It is item 1 in
`REMAINING.md`'s suggested order after the wrong-numbers fix, and it is the only thing
standing between HEAD and release gate 5.

**Risk: the letter-directory rule is known for four files, inferred for the rest.** The
audit measured `dash.ado`, `dash_render.py`, `s1color.scheme` and `economist.scheme`.
`dash_parse.mata`, `dash.sthlp`, `dash_setup.ado` and `dash_setup.sthlp` are not in that
table. Mitigation: the cscript prints the installed tree and the pytest model is derived
from what it prints (TR-03.8, TR-03.9). Never the reverse — a model that was guessed and
then "confirmed" by a test built from the same guess proves nothing. This is the exact
trap that produced the current two-layout model.

**Risk: widening a search path widens a trust boundary.** `allowed` in `_resolve_path`
is computed from `_SCHEME_SEARCH_DIRS`, so every new directory is also a new permitted
root for a user-supplied `scheme()` value (project rule 1). Keeping the derivation to
`__file__` and one `dirname` is what contains it; the traversal tests are what prove it.
Do not add a directory from an environment variable "for development convenience".

**Risk: an over-broad install root.** If `dash` is installed somewhere shallow, the
install root could be a directory with unrelated `.scheme` files in letter
subdirectories. The per-name candidate (TR-03.2) limits exposure to exactly
`<root>/<letter>/<name>.scheme`, and the development-tree-first ordering means a repo
checkout is never shadowed.

**Risk: this collides with S11-05, in a later phase.** S11-05 turns the scheme warning
into a Stata-side error and retires the CWD `.scheme` path — the same function,
`_resolve_path`. Keep the install-layout directories assembled in one clearly-named place
so the S11 work can remove the CWD candidate without re-deriving the layout logic, and
expect to re-run this phase's traversal tests when S11-05 lands.

**Risk: the warning text changes shape.** The `no scheme file could be resolved` message
interpolates `_SCHEME_SEARCH_DIRS`, so after this phase it lists five-ish directories
instead of two. Any test pinning the old string must be updated deliberately, and the
message should stay short enough to be useful at a Stata prompt.

**Sequencing out.** Phase 08 owns the server-side packaged-install test
(`test/test_server_build.cscript` is where Appendix C says it belongs). That test becomes
meaningful only after this phase; running it before would certify a fallback. Phase 31
cannot close gate 5 until items 1–3 land. Phases 23–25 make schemes render better — this
phase makes them render at all for anyone who installed rather than cloned, so its value
compounds with theirs rather than competing.

**Effort honesty.** Four of the five items are small and one is medium; the medium one is
the cscript, and its cost is Stata plumbing — temp directories, adopath save/restore,
`net set ado` restoration — not logic. The single code change is a few lines in one class
attribute plus a candidate-building branch. The disproportion between that and the impact
is the reason this phase is first.
