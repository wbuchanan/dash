# Phase 04 — Security, resource limits and honest declarations

**Purpose.** This phase closes the three places where `dash` currently tells the user
something that is not true, and the one place where it accepts an input it cannot afford to
honour. `scheme()` warns and silently draws `s2color` where the plan's first binding
decision says it must error, and the arbitrary-`.scheme`-file path that decision was
supposed to retire — the package's path-traversal surface — is still reachable from the
working directory. Three resource limits named in the plan do not exist at all: a dropdown
filter on a continuous variable emits 200,001 `<option>` elements on 200,000 observations,
`by(id)` builds one figure per distinct value with no ceiling, and the served app's
`_MAX_IPS` is an eviction primitive rather than a limiter — one machine cycling 10,000
forwarded keys took 300 sessions inside a nominal-60 window. Finally, five separate files
declare `kdensity` to be scipy-dependent when it provably is not, the certification runner's
hard-won "cannot report a false pass" behaviour has no regression test, and the BASELINE.md
coverage note task 01-05 required was never written. Every item here is small or medium; none
of them needs a renderer redesign; and together they discharge task 11-05, the whole of the
S01 residue, and the resource-limit clauses of S12/S13 — which are four of the six gates
S16-07 has to pass.

---

## At a glance

| | |
|---|---|
| **Items** | 9 (numbered 1–9, all from REMAINING.md's main body) |
| **Functional vs deliverable** | 6 functional (1, 2, 3, 4, 5, 8) · 3 deliverable (6, 7, 9) |
| **Effort mix** | 3 medium (1, 2, 3) · 6 small (4, 5, 6, 7, 8, 9) · 0 large |
| **Renderers touched** | `stata` 2 (1, 6) · `standalone` 1 (2) · `server` 1 (3) · `both` 2 (4, 5) · `n/a` 3 (7, 8, 9) |
| **Files touched** | `dash.ado`, `dash_render.py`, `dash.pkg`, `dash.sthlp`, `dash_setup.ado`, `dash_setup.sthlp`, `test/run_all_cscripts.do` (test only), `.ultraplan/BASELINE.md`, `test/` |
| **Ultraplan tasks discharged** | **11-05** in full · **01-03**'s outstanding refutation · **01-04**'s missing regression test · **01-05**'s missing BASELINE note · the resource-limit clauses of **S12** and **S13** (REMAINING.md §6, headed `[S13, S14, S16-04]`) |
| **Sections closed outright** | **S01** (the only two open items in the section are 6 and 7 here, plus the 01-03 refutation as item 8) |
| **Sections partly advanced** | S11 (11-05 only — the other five S11 partials are not in scope), S12, S13, S14, S16-04 |
| **Depends on** | *Soft:* the phase that owns REMAINING.md §1 (`net install` scheme search paths). Items 1–2 are correct without it, but "a named scheme survives a real install" can only be certified once §1 lands. No hard dependency. |
| **Unblocks** | Two of the six S16-07 release gates — *"full certification suite with honest skips"* (item 6) and *"adversarial suite"* (items 2–5) — plus 16-04's resource-exhaustion cases, which have no bounded surface to assert against today. |

> **Origin note, for accuracy.** The work-item list assigns item 3 (`_MAX_IPS`) origin
> `S13`. REMAINING.md's section-status table lists `_MAX_IPS` under **S14** ("Server root
> fix"), and §6 itself is headed `[S13, S14, S16-04]`. Both statements are recorded here;
> the item is worked in this phase either way.

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md` (the audit of all 89 tasks against
`ca5fe35` / `187a786` on `feature/batch4-interactive-layer`). Where a fact was re-confirmed
against the source at HEAD for this document, it is marked **[confirmed at HEAD]**. Nothing
below is inferred unless it says so.

### 3. Binding decision 1 is violated  [S11-05]

> `PLAN.md:36-37` — `scheme()` is "**restricted** to the translated set with a
> clear error naming the supported names — never a silent fallback to black or
> to `s2color`." S11-05 adds: validate "in **Stata**, where the user sees the
> error", and retire the arbitrary-`.scheme`-file path, "which also removes the
> path-traversal surface".
>
> Measured at HEAD:
>
> | required | actual |
> |---|---|
> | error naming the set | `warnings.warn(...)` then `_raw_name = ""` → **`s2color`** (`dash_render.py:7970-7982`) |
> | validated in Stata | `dash.ado` has **no** scheme-name validation |
> | `.scheme` file path retired | `SchemeParser._resolve_path` still resolves `name.endswith(".scheme")` from the CWD (`:1691-1714`); `_resolve_scheme_name` explicitly exempts it (`not _raw_name.endswith(".scheme")`) |
> | help matches code | `dash.sthlp:1084` still tells users to "put its Stata-format `.scheme` file in the working directory" |
>
> So a typo in `scheme()` silently produces the wrong aesthetic, and the
> path-traversal surface the plan wanted closed is still reachable.

**[confirmed at HEAD]** The fallback is exactly as described. `dash_render.py:7966-7982`:

```python
    _lower = _raw_name.lower()
    if (_raw_name and _lower not in _THEME_SCHEME_MAP
            and _lower not in SchemeParser._BUILTIN_NAMES
            and not _raw_name.endswith(".scheme")):
        warnings.warn(
            f"dash: {_raw_name!r} is not a known theme or scheme; using "
            f"s2color. Themes: "
            f"{', '.join(sorted(_THEME_SCHEME_MAP))}. Schemes: "
            f"{', '.join(sorted(SchemeParser._BUILTIN_NAMES))}.",
            UserWarning,
        )
        _raw_name = ""
        _lower = ""
```

The `and not _raw_name.endswith(".scheme")` clause is the exemption REMAINING.md names: any
value ending in `.scheme` skips the known-name check entirely and is handed to
`SchemeParser._resolve_path`, whose file-reference branch tries the **current working
directory first** (`dash_render.py:1691-1714`):

```python
    def _resolve_path(self, name: str) -> str:
        """Return absolute path for a scheme name, blocking path traversal."""
        is_file_ref = name.endswith(".scheme") or os.sep in name or "/" in name

        search_dirs = list(self._SCHEME_SEARCH_DIRS)

        if is_file_ref:
            # Try CWD first, then each scheme search dir
            candidates = [os.path.abspath(os.path.join(os.getcwd(), name))]
```

**[confirmed at HEAD]** The supported set is exactly fourteen names
(`dash_render.py:1538-1545`) and fourteen files ship in `schemes/`:

```python
    _BUILTIN_NAMES: frozenset[str] = frozenset({
        # Stata 18+ family (stcolor is Stata's default since v18)
        "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
        # legacy defaults (s2color was the default from v10 to v17)
        "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
        # journal styles
        "economist", "sj",
    })
```

plus six theme aliases (`_THEME_SCHEME_MAP`): `default`→`s2color`, `clean`→`s1color`,
`mono`→`s1mono`, `dark`→`s1rcolor`, `economist`, `sj`.

**[confirmed at HEAD]** Name resolution precedence, which constrains where the error may be
raised (`dash_render.py:7956-7963`):

```python
    _raw_name: str = (
        _build_opts.get("scheme", "").strip()
        or _build_opts.get("theme", "").strip()
        or _graph_scheme
        or _build_opts.get("session_scheme", "").strip()
        or ""
    )
```

`session_scheme` is not user-typed: `dash.ado:1721` and `dash.ado:2340` both set it from
`c(scheme)`. A Stata session may legitimately be running a scheme `dash` has not translated,
so the hard error must apply to the three *typed* surfaces and never to `session_scheme`.
(This is analysis of the measured precedence, not a separate measurement.)

### 6. Resource limits still open  [S13, S14, S16-04]

> Confirmed absent at HEAD — no constant, no clamp:
>
> - **`_MAX_IPS` is an eviction primitive, not a limiter.** One machine cycling
>   10,000 forwarded keys took 300 sessions inside a 60-second window against a
>   nominal 60. Needs a different structure, not a larger cap. (Project rule 3.)
> - **Dropdown filter on a continuous variable** emits one `<option>` per
>   distinct value, uncapped — 200,001 options on 200,000 observations.
>   (`_MAX_FILTER_OPTIONS`/`_MAX_DROPDOWN`: not defined.)
> - **`by()` has no group cap** — `by(id)` builds one figure per value.
>   (`_MAX_BY_GROUPS`/`_MAX_FACETS`/`_MAX_TABS`: not defined.)

REMAINING.md records the same dropdown defect a second time, from the date side, in its
Appendix A review of **08-05**:

> 2. **No dropdown cardinality warning.** The task requires a warning above a
>    reasonable cardinality suggesting `type(range)`. Measured on 5,000 distinct
>    dates: **5,001 options, zero warnings**. (Same defect as the uncapped
>    dropdown already recorded in §6 of this file; this is the date-specific
>    clause of it.)

So the cap has two witnesses at two magnitudes: 200,001 options on 200,000 observations, and
5,001 options on 5,000 distinct dates. The "+1" in both is the dropdown's own *All* entry.

**[confirmed at HEAD]** The emitted limiter (`dash_render.py:12989-13027`, quoted from the
`ServerAppBuilder` string list that becomes the served app):

```python
"_RATE_LIMIT_RPM = 60   # max dashboard session connections per IP per minute",
"_HEALTH_LIMIT_RPM = 600  # max /health requests per IP per minute (infrastructure checks)",
"class _RateLimiter:",
"    '''Sliding-window per-IP rate limiter.",
"    Empty per-IP lists are deleted after pruning so unique-IP churn",
"    cannot grow _store without bound.  A hard _MAX_IPS cap evicts the",
"    oldest tracked IP when the store is full.'''",
"    _MAX_IPS = 10000  # max simultaneous tracked IPs (evict oldest when exceeded)",
...
"        if ip not in self._store and len(self._store) >= self._MAX_IPS:",
"            # Least RECENTLY SEEN, not first inserted.  Insertion",
"            # order let a sprayer of 10,000 fresh keys evict the",
"            # record of a client that is still active, which makes",
"            # the cap itself an eviction primitive.",
"            oldest = min(self._store,",
"                         key=lambda k: self._store[k][-1]",
"                         if self._store[k] else 0)",
"            del self._store[oldest]",
```

An earlier pass already moved eviction from insertion order to least-recently-seen, and
`test/test_server_rate_limit.py::TestTheCapIsNotAnEvictionPrimitive::test_eviction_drops_the_least_recently_seen`
certifies that half. What the LRU change does **not** fix, and what the 300-in-60 measurement
records, is that the evicted record can be the sprayer's *own* earlier key: a client cycling
more keys than the store can hold erases its own history and is re-admitted with a fresh
per-key allowance on every cycle. A larger `_MAX_IPS` buys a longer cycle, not a bound —
which is exactly REMAINING.md's "needs a different structure, not a larger cap".

**[confirmed at HEAD]** Forwarded keys only become bucket keys when the operator has opted
in — `_client_ip_from_request` returns `remote` unless `_TRUST_FORWARDED_FOR` is true
(`dash_render.py:13065-13066`, set by `--trust-forwarded-for`). The measured overshoot is
therefore the behaviour of the reverse-proxy deployment that flag exists for, which is the
deployment where per-IP limiting is the only limiting there is.

**[confirmed at HEAD]** There is an established house pattern for caps to follow — a
module-level constant, a `warnings.warn` naming the limit, and a clamp:
`_FP_GRID_MAX = 1000` (`:121`), `_MAX_KPIS_PER_ROW = 4` (`:125`),
`_MAX_FIGURE_HEIGHT = 560` (`:131`), `_MAX_EXPR_CHARS = 5000` (`:2271`),
`_MAX_MBANDS = 1000` (`:2313`), `_MAX_BINS = 1000` (`:4725`, warn-and-clamp at `:4767-4775`),
and `_LARGE_DATASET_CELLS = 1_000_000` with `_report_dataset_size` at `:538-566`:

```python
    warnings.warn(
        f"dash: {rows:,} observations on {cols} variables is a large "
        f"dataset to embed; this {mode} will be roughly {mb:,.0f} MB and "
        f"slow to open. Reduce it with an `if' or `in' qualifier, or keep "
        f"only the variables the dashboard uses.",
        UserWarning, stacklevel=3,
    )
```

The two new caps in this phase are the same shape, in the same voice.

### 01-03 — the dependency declarations are false in five places

From REMAINING.md's table of *17 DONE claims the adversarial pass overturned*:

> | task | what the refutation found |
> |---|---|
> | 01-03 | guards hold under attack, but `kdensity` is declared scipy-dependent in five places and provably is not; `dash_render.py:43-49` still lists scipy/statsmodels as hard dependencies |

**[confirmed at HEAD]** All five declaration sites, quoted:

| site | text |
|---|---|
| `dash_setup.ado:99` | `//   scipy       -> lfitci, qfitci, kdensity, mspline` |
| `dash_setup.ado:111` | `local feat_scipy       "lfitci, qfitci, kdensity and mspline"` |
| `dash.pkg:15` | `d Optional: scipy>=1.9 (lfitci, qfitci, kdensity, mspline) and` |
| `dash.sthlp:1182-1183` | `…optional} — scipy≥1.9 for {cmd:lfitci}, {cmd:qfitci}, {cmd:kdensity} and {cmd:mspline}…` |
| `dash_setup.sthlp:76` | `{synopt:{opt scipy}}1.9 or later — {cmd:lfitci}, {cmd:qfitci},` / `{cmd:kdensity} and {cmd:mspline}{p_end}` |

**[confirmed at HEAD]** The flat dependency list in the module docstring
(`dash_render.py:43-49`), which does not distinguish required from optional at all, although
`dash_setup.ado:103-104` does:

```
Dependencies
------------
  bokeh >= 3.0
  numpy >= 1.23
  scipy >= 1.9
  statsmodels >= 0.13
  pandas >= 1.5
```

```stata
    local pkg_required "bokeh numpy pandas"
    local pkg_optional "scipy statsmodels"
```

**[confirmed at HEAD]** `kdensity` uses dash's own kernels, not scipy: `_KERNELS` is defined
at `dash_render.py:6595` and read at `:4243`, `:4322`, `:4405`, `:4840` — there is no
`gaussian_kde` call left, and `test/test_dependency_guards.py::TestKdensityNeedsNoOptionalDependency::test_kdensity_source_has_no_scipy_import`
already asserts it. The same file already holds `TestQfitciNeedsNoScipy::test_qfitci_works_without_scipy`
for the **standalone** path — and item 8 is explicit that `qfitci` must nonetheless stay in
the scipy list, because the **server** path does use `scipy.stats.t.ppf`
(`dash_render.py:13320`, `:13344`; `lfitci`'s at `:13256`, `:13270`; `mspline`'s
`PchipInterpolator` at `:13512`).

### 01 — two deliverables the section never produced

From REMAINING.md's status-by-section table:

> | # | Section | Tasks | Status | What is left |
> |---|---|---:|---|---|
> | 01 | Baseline, env, test integrity | 6 | 4 done, 2 partial ② | runner skip-accounting regression test; BASELINE.md coverage note |

Task 01-04's own `<action>` asked for the test *first*:

> Third — and this is the one that matters — make the runner **fail loudly** if the number
> of skips equals the number of scripts. A machine with no `jsonio` and no Python currently
> prints ALL TESTS PASSED having asserted nothing. That must become a hard error.
>
> Write the test for this before the change: assert that a run in which every script skips
> does not report success.

**[confirmed at HEAD]** The behaviour landed (`test/run_all_cscripts.do:721-741`):

```stata
local n_total = `n_pass' + `n_fail' + `n_skip'
...
if `n_fail' > 0 {
    display as error "SOME TESTS FAILED"
    exit 1
}
else if `n_pass' == 0 {
    // Every script skipped: nothing was asserted.  Reporting success here
    // would be a false pass -- a machine without jsonio or Python would
    // previously print ALL TESTS PASSED having verified nothing.
    display as error "NO TESTS RAN -- all `n_skip' script(s) skipped."
    display as error "Install the missing dependencies (run dash_setup) and re-run."
    exit 1
}
```

…and the test did not. `test/test_cscript_hygiene.py` asserts that every cscript is wired
into the runner and that nothing probes Python by executing it, but nothing asserts the
`n_pass == 0` branch. Deleting the `else if` block above leaves the whole suite green.

Task 01-05's `<action>` asked for the second deliverable:

> Also note in BASELINE.md that only 4 of 11 cscripts currently reach Python end to end —
> `test_parser.cscript`'s single `dash` call passes `name()`, which routes to
> `_dash_register_graph` and never renders. S16 owns widening that.

**[confirmed at HEAD]** `.ultraplan/BASELINE.md` records the orphan count ("11 on disk, 9
invoked, 2 orphaned", `:206-211`) and the false-green finding (F1, `:504`), but carries no
end-to-end coverage note. The figure has also moved: REMAINING.md's gates line reports
**25/25 cscripts** passing at HEAD, and `ls test/*.cscript` returns 25 files, so the note
must be **recomputed**, not copied from the plan's stale 4-of-11.

### The gates this phase feeds

> ## Gates still to pass (S16-07)
>
> full pytest · full certification suite with honest skips · conformance corpus
> (zero `r(198)`, zero dropped series, zero dropped graphs) · parity corpus ·
> clean `net install` runs every example · adversarial suite.
>
> At HEAD the first four pass (3,498 passed / 37 skipped; 25/25 cscripts);
> the fifth fails on §1.

And REMAINING.md's own ordering puts this phase's two halves at steps 2 and 3:

> 2. **S11-05.** Turn the warning into a Stata-side error, retire the CWD
>    `.scheme` path, fix `dash.sthlp:1084`. Closes a binding decision and a
>    security surface together.
> 3. **The three resource caps.** Each is a constant plus a clamp plus a test.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **E4.1 — Constrain the scheme surface** | `scheme()`/`theme()` accept only the fourteen translated names and six aliases, error in Stata when they do not, and no longer read an arbitrary file from the working directory. | 1, 2 |
| **E4.2 — Bound what a spec can ask the renderer to build** | No user input can make `dash` emit an unbounded number of widgets, figures or rate-limiter buckets; each ceiling is a named constant, a warning and a clamp, identical in both renderers. | 3, 4, 5 |
| **E4.3 — Honest declarations and a suite that cannot lie** | What the package says about its dependencies matches what the code does, and the two test-integrity deliverables S01 owes are written and self-guarding. | 6, 7, 8, 9 |

---

## User stories

### E4.1 — Constrain the scheme surface

**US-4.1.1** — *As a Stata user pasting a `twoway` command, I want a mistyped `scheme()` name
to stop my command with an error that lists the names I can use, so that I never present a
dashboard whose colours are not the ones I asked for.*

- **Given** a session at the `dash` prompt,
  **when** I run `dash build, saving(d.html) scheme(s1colour)`,
  **then** the command exits non-zero (`r(198)`), prints a message naming the fourteen
  supported schemes and six theme aliases, and **no HTML file is written**.
- **Given** the same session,
  **when** I run `dash scatter mpg weight, name(g1) scheme(economist)`,
  **then** the command succeeds and the graph is registered with `scheme(economist)`.
- **Given** a session whose `c(scheme)` is a scheme `dash` has not translated,
  **when** I run `dash build, saving(d.html)` with no `scheme()` and no `theme()`,
  **then** the build succeeds and falls back to `s2color` without an error, because I did not
  type that name.
- **Given** `dash serve` and `dash build, server`,
  **when** either is given a bad `scheme()`,
  **then** the same error is raised at the same point, with the same text.

**US-4.1.2** — *As a package maintainer, I want `dash` to stop resolving `.scheme` files from
the working directory, so that the path-traversal surface the plan told us to retire is gone
rather than merely guarded.*

- **Given** a directory containing a crafted `evil.scheme`,
  **when** a user runs `dash build, scheme(evil.scheme)`,
  **then** Stata rejects the name before the renderer is reached and the file is never opened.
- **Given** the same directory,
  **when** a user runs `dash build, scheme(../../etc/passwd.scheme)`,
  **then** the name is rejected on the same code path, with the same message, and
  `SchemeParser._resolve_path` is never called with it.
- **Given** the bundled `schemes/` directory,
  **when** any of the fourteen names is used,
  **then** `_resolve_path`'s containment guards still run and still pass — defence in depth is
  retained, not deleted.

**US-4.1.3** — *As a Stata user reading `help dash`, I want the help to describe the scheme
surface the command actually has, so that I do not follow an instruction that now errors.*

- **Given** `dash.sthlp` at HEAD,
  **when** I read the scheme section,
  **then** the sentence at `:1084` telling me to put a `.scheme` file in the working
  directory is gone, replaced by the supported list and a note to request a translation.
- **Given** the claim at `dash.sthlp:176` that `scheme()` is "fully supported",
  **when** I read it after this phase,
  **then** it is accurate: supported means the fourteen, and the help says so.

### E4.2 — Bound what a spec can ask the renderer to build

**US-4.2.1** — *As a Stata user who typed `filter(price, type(dropdown))` on a continuous
variable, I want `dash` to refuse to build a 200,001-entry dropdown and tell me to use
`type(range)`, so that my browser opens the dashboard.*

- **Given** a dataset with 200,000 distinct values of `price`,
  **when** I build with `filter(price, type(dropdown))`,
  **then** the build succeeds, a `UserWarning` names the option count, names the limit and
  suggests `type(range)`, and the emitted `<select>` carries no more than the limit.
- **Given** a dataset with 5,000 distinct dates,
  **when** I build a `%td` dropdown,
  **then** the same warning fires (this is 08-05's date-specific clause of the same defect).
- **Given** a dataset with 12 distinct values of `rep78`,
  **when** I build the same dropdown,
  **then** nothing is warned and all options are present — the cap is invisible at ordinary
  cardinality.

**US-4.2.2** — *As a Stata user who typed `by(id)` on an identifier, I want a ceiling on the
number of facets, so that `dash` does not try to build one figure per observation.*

- **Given** a dataset with 2,000 distinct values of `id`,
  **when** I run `dash scatter y x, by(id)` and build,
  **then** the build succeeds, a `UserWarning` names the group count and the limit, and no
  more than the limit of figures is produced.
- **Given** `by(foreign)` on `auto.dta`,
  **when** I build,
  **then** both facets are drawn and nothing is warned.
- **Given** the same over-cardinality `by()` spec,
  **when** it is rendered in **both** standalone and server mode,
  **then** the cap and the warning are identical in both — the parity corpus sees one
  behaviour, not two.

**US-4.2.3** — *As a `dash serve` operator behind a reverse proxy, I want the per-IP limiter
to hold under a client that cycles forwarded addresses, so that one machine cannot take five
times the nominal session budget.*

- **Given** a served app with `_RATE_LIMIT_RPM = 60` and `--trust-forwarded-for` enabled,
  **when** one client cycles 10,000 distinct `X-Forwarded-For` values inside a 60-second
  window,
  **then** the total admitted sessions attributable to that client stay within a stated
  bound, rather than the measured 300.
- **Given** the same app,
  **when** an ordinary client makes 60 requests in a minute from one address,
  **then** all 60 are admitted and the 61st receives 429 — the honest client is unaffected.
- **Given** the store at capacity,
  **when** a new key arrives,
  **then** memory stays bounded and the eviction that occurs cannot grant the *evicting*
  client a fresh allowance.
- **Given** infrastructure liveness probes on `/health`,
  **when** the session budget is exhausted,
  **then** `/health` still answers 200 — the two limiters stay independent
  (`_SESSION_LIMITER`, `_HEALTH_LIMITER`).

### E4.3 — Honest declarations and a suite that cannot lie

**US-4.3.1** — *As a package maintainer running the certification suite on a bare machine, I
want a regression test that fails if the runner is ever able to report success without
asserting anything, so that the 01-04 fix cannot be undone by a later edit.*

- **Given** `test/run_all_cscripts.do` at HEAD,
  **when** the `n_pass == 0` branch is deleted or weakened to `exit 0`,
  **then** the pytest suite fails with a message naming the file and the branch.
- **Given** the runner unmodified,
  **when** the suite runs,
  **then** the test passes without invoking Stata (it is a source-level assertion, in the
  style of `test_cscript_hygiene.py`).

**US-4.3.2** — *As a package maintainer, I want BASELINE.md to record how far the
certification suite actually reaches, so that "25/25 cscripts pass" is never read as
"25 cscripts render a dashboard".*

- **Given** `.ultraplan/BASELINE.md` after this phase,
  **when** I read it,
  **then** it states, for the current 25 cscripts, how many reach Python end to end, names
  the ones that do not and why (e.g. `test_parser.cscript`'s `dash … , name()` call routes
  to `_dash_register_graph` and never renders), and names S16 as the owner of widening it.

**US-4.3.3** — *As a Stata user deciding whether to install scipy, I want the package to tell
me which plot types actually need it, so that I do not install a dependency for a feature
that has not used it since S07.*

- **Given** `dash_setup`, `dash.pkg`, `dash.sthlp` and `dash_setup.sthlp` after this phase,
  **when** I read any of them,
  **then** `kdensity` does not appear in the scipy feature list in any of the five places.
- **Given** the module docstring at `dash_render.py:43-49`,
  **when** I read it,
  **then** scipy and statsmodels are marked optional, matching
  `dash_setup.ado:103-104`.
- **Given** `qfitci`,
  **when** I read the scipy list,
  **then** it is still there, because the served app uses `scipy.stats.t.ppf`.

**US-4.3.4** — *As a package maintainer, I want a test that compares the advertised feature
lists against the guarded call sites, so that these declarations cannot go stale a second
time.*

- **Given** any of the five declaration sites,
  **when** a plot type is added to or removed from an optional-dependency feature list
  without a matching change to the guarded call sites,
  **then** `test/test_dependency_guards.py` fails and names the site and the disagreement.
- **Given** the four sites and the code in agreement,
  **when** the suite runs,
  **then** the test passes.

---

## Business requirements

| ID | Requirement | How it is judged |
|---|---|---|
| **BR-04.1** | A `scheme()` or `theme()` name that `dash` cannot honour must stop the command with an error, never a silent substitution. | `dash build, scheme(<bad>)` returns non-zero; no output file is produced. |
| **BR-04.2** | The error must name every name the user may use. | The message contains all 14 scheme names and all 6 theme aliases. |
| **BR-04.3** | The error must be raised in Stata, where the user sees it, not only in Python. | The failure occurs with `python`-side rendering never reached; the message appears in the Stata results window. |
| **BR-04.4** | `dash` must not read a scheme definition from a path the user supplies. | No code path passes a user-typed string ending in `.scheme`, or containing a separator, to a file open. |
| **BR-04.5** | Defence in depth around the bundled schemes is retained. | `_resolve_path`'s containment check still runs for the 14 bundled names and still rejects traversal. |
| **BR-04.6** | The help must describe the surface the code has. | No sentence in `dash.sthlp` instructs the user to supply their own `.scheme` file; `test_help_conformance.py` passes. |
| **BR-04.7** | No single user input may cause an unbounded number of HTML elements, figures or rate-limiter entries. | Each of the three surfaces has a named constant, a clamp and a warning. |
| **BR-04.8** | Exceeding a ceiling degrades with an explanation; it never aborts the build. | The build returns rc 0 and emits a `UserWarning` naming the count, the limit and the remedy. |
| **BR-04.9** | A ceiling behaves identically in standalone and server mode. | The parity corpus sees one behaviour; `test_mode_parity.py` covers the capped spec. |
| **BR-04.10** | One client must not be able to obtain materially more than the nominal session rate by varying a header it controls. | The measured 300-in-60 against a nominal 60 falls to a stated, tested bound. |
| **BR-04.11** | Rate-limiter memory stays bounded under unique-key churn. | Store size never exceeds its configured maximum across a churn test. |
| **BR-04.12** | Health checks stay answerable while sessions are rate-limited. | `/health` returns 200 with `_SESSION_LIMITER` exhausted. |
| **BR-04.13** | The certification runner cannot report success having asserted nothing, and that property is itself tested. | Mutating the `n_pass == 0` branch fails the pytest suite. |
| **BR-04.14** | The baseline records the real end-to-end reach of the certification suite. | `.ultraplan/BASELINE.md` carries a dated note with the current counts. |
| **BR-04.15** | Every advertised optional-dependency feature list matches the code. | `kdensity` absent from all five scipy lists; `qfitci` present; scipy/statsmodels marked optional in the module docstring. |
| **BR-04.16** | The declarations are protected by a test, not by discipline. | `test/test_dependency_guards.py` fails on a deliberate disagreement. |

---

## Technical requirements

### E4.1 — Constrain the scheme surface

**TR-04.1 — One list, one helper, in `dash.ado`.** Add `_dash_validate_scheme` to `dash.ado`.
It takes a typed name and the surface it came from (`scheme` or `theme`), lower-cases it, and
checks it against a single local holding the fourteen schemes
(`stcolor stcolor_alt stgcolor stmono1 stmono2 stsj s2color s2mono s2gcolor s1color s1mono
s1rcolor economist sj`) and, for `theme()`, the six aliases
(`default clean mono dark economist sj`). On failure it emits an error naming both lists and
`exit 198`.

**TR-04.2 — Three call sites, not one.** `dash.ado` parses `scheme()` on three surfaces and
each must validate before it serialises:

| surface | where the value is captured today |
|---|---|
| graph-level `dash <plot> … , scheme()` | `sreturn local scheme` at `dash.ado:405`; `sreturn local g_scheme` at `:732`; reaches the spec as the graph's `graph_options.scheme` |
| `dash build , scheme()` | `_dash_json_str \`"\`scheme'"' _scheme_esc` at `dash.ado:2341`, written into `build_options.scheme` at `:2343` |
| `dash serve` | `global dash_opts_scheme` at `dash.ado:2458` |

Validation must fire on all three; a graph registered with a bad scheme must fail at
registration, not at build, so the user is told at the command they typed.

**TR-04.3 — `session_scheme` is exempt.** `dash.ado:1721` and `:2340` set
`local _dash_sess_scheme = c(scheme)`; that value is serialised as
`build_options.session_scheme` (`dash.ado:1723`, `:2343`) and is the **fourth** term in
`_resolve_scheme_name`'s precedence chain. It is not user-typed at the `dash` prompt and must
never raise. When it is outside the set, resolution continues to fall through to `s2color`
silently, as today.

**TR-04.4 — rc and the conformance gate.** The error uses `exit 198` (Stata's invalid-syntax
return code). S16-07's conformance gate requires *"zero `r(198)`"* over the conformance
corpus, so the corpus must not contain a non-translated scheme name; confirm this when
wiring the gate rather than weakening the rc.

**TR-04.5 — Remove the renderer's `.scheme` exemption.** In `_resolve_scheme_name`
(`dash_render.py:7970-7982`), delete the `and not _raw_name.endswith(".scheme")` clause so
a `.scheme`-suffixed name is treated as any other unknown name. The renderer's
`warnings.warn` + `s2color` fallback **stays** as the second line of defence for specs that
did not come through `dash.ado` (a hand-written master spec, a test fixture), but it is no
longer the user-facing behaviour because TR-04.1 stops the command first.

**TR-04.6 — Retire the CWD file-reference branch.** In `SchemeParser._resolve_path`
(`dash_render.py:1691-1714`) remove the `is_file_ref` branch — the one whose first candidate
is `os.path.abspath(os.path.join(os.getcwd(), name))`. Keep the bare-name branch, keep
`_SCHEME_SEARCH_DIRS` (`:1524-1532`) and **keep the containment check** that follows
(`allowed = [os.path.abspath(d) for d in search_dirs]`). The task is explicit: *"Keep the
`_resolve_path` guards for the bundled set; do not delete defence in depth just because the
input is now constrained."*

**TR-04.7 — Two copies of the name list must be proven equal.** After TR-04.1 the fourteen
names exist in `dash.ado` and in `dash_render.py:1538-1545` (`SchemeParser._BUILTIN_NAMES`),
and the six aliases in `dash.ado` and `_THEME_SCHEME_MAP`. A test must parse both sources and
assert set equality, so the two cannot drift. This is the same shape as TR-04.16's
doc-consistency test and should live beside it or in `test/test_scheme.py`.

**TR-04.8 — Help.** Delete the instruction at `dash.sthlp:1084` ("put its Stata-format
`.scheme` file in the working directory and give its base name without the extension") and
replace it with the supported list plus a note that a user wanting another scheme should
request a translation. Re-check the surrounding claims 11-05 named: `dash.sthlp:176`
("`scheme()` is fully supported") is now accurate and stays; the theme list at
`dash.sthlp:289-290` already reads `default, clean, mono, dark, economist, sj`, which matches
`_THEME_SCHEME_MAP` at HEAD, so that half of 11-05 is already done and needs no edit.

### E4.2 — Bound what a spec can ask the renderer to build

**TR-04.9 — `_MAX_FILTER_OPTIONS`.** Define a module-level constant beside the existing caps
(`dash_render.py:121-131`) and clamp in `FilterBuilder.build_dropdown`
(`dash_render.py:7571`, class at `:7557`), immediately after `raw_values` is built —
REMAINING.md locates the insertion point as `dash_render.py:7629-7638`. The warning must name
the distinct-value count, the limit and the remedy (`type(range)`), following
`_report_dataset_size`'s voice. **Proposed value: 1,000**, matching the house precedent of
`_MAX_BINS`, `_MAX_MBANDS` and `_FP_GRID_MAX`; this is a judgement to be ratified, not a
measurement. REMAINING.md grepped for both `_MAX_FILTER_OPTIONS` and `_MAX_DROPDOWN` and
found neither; `_MAX_FILTER_OPTIONS` is the name adopted here.

**TR-04.10 — The dropdown cap is shared, not duplicated.** The same clamp must govern the
served app's filter-widget loop. REMAINING.md's 08-05 entry locates it: *"filter-widget loop:
dropdown at 15378, range at 15403"*. Emit the constant into the app (or have the builder apply
the clamp before emission) so there is one number, not two.

**TR-04.11 — `_MAX_BY_GROUPS`.** Define the constant beside the others and clamp in
`DashRenderer._expand_by_groups` (`dash_render.py:8776`; called at `:11403` and `:11436`).
Warn naming the group count, the limit, and that the remaining groups were dropped.
**Proposed value: 50** — a screenful of facets, above every plausible legitimate `by()` on a
Stata example dataset (`auto`'s `rep78` is 5, `foreign` is 2) and far below `by(id)`; again a
judgement to be ratified. REMAINING.md grepped for `_MAX_BY_GROUPS`, `_MAX_FACETS` and
`_MAX_TABS` and found none; `_MAX_BY_GROUPS` is adopted.

**TR-04.12 — The `by()` cap must reach the emitted app, which has its own facet code.**
REMAINING.md's 15-03 entry records that *"`_expand_by_groups` occurs 3× in `DashRenderer` and
**0×** in the emitted app, which still carries its own `by_total` handling"*. Until 15-03's
collapse lands, this phase must apply the clamp in the emitted `by()` / `by(total)` loops as
well, and a parity test must assert the two agree. If the unification phase lands first, the
clamp inherits for free — note this in the sequencing (see Risks).

**TR-04.13 — Replace `_MAX_IPS` with a structure that cannot be reset by its own client.**
The defect is that a client cycling more keys than the store holds evicts its own earlier
record and is re-admitted with a fresh per-key allowance. The required properties are:

1. **Bounded memory** — the store never exceeds a configured maximum (the property
   `_MAX_IPS` does deliver, and which must survive).
2. **No allowance from eviction** — admitting a key whose record was evicted must not
   restore a full budget to the traffic that caused the eviction.
3. **No collateral damage** — an active honest client's record must not be evictable by a
   sprayer. `test_server_rate_limit.py::test_eviction_drops_the_least_recently_seen` already
   guards the least-recently-seen ordering that gives this; keep it green.
4. **Separate key spaces preserved** — forwarded keys stay prefixed `xff:`
   (`dash_render.py:13080`) so a forged `10.0.0.1` cannot land in a real peer's bucket, and
   `_SESSION_LIMITER` / `_HEALTH_LIMITER` stay independent.

*Design proposal, to be ratified in review:* keep the per-key sliding window for keys that fit
in the store, and add a **second, coarse bucket** that charges every admission from a key not
currently tracked — an overflow allowance shared by all churn. A client cycling 10,000 keys is
then limited by the overflow bucket regardless of how often it forces eviction, while an
honest client keeps its own window. Additionally cap the number of `xff:`-space keys
separately from `remote_ip`-space keys, so the opt-in proxy path cannot consume the whole
store. Two implementation notes, both confirmed by reading the emitted source: the window is a
`list` pruned with `ts.pop(0)` (`dash_render.py:13010`), which is O(n) per call — a
`collections.deque` with `popleft()` is the drop-in; and the docstring at `:12993-12996`
currently *advertises* the cap as a limiter and must be rewritten to describe whatever
structure replaces it, or it becomes the next stale declaration.

**TR-04.14 — Emitted-source discipline.** `_RateLimiter` lives inside `ServerAppBuilder`'s
emitted string list (everything after `class ServerAppBuilder` at `dash_render.py:12265` is
emitted-app source). Changes are edits to string literals; the test must import the built
module the way `test/test_server_rate_limit.py`'s `app_module` fixture already does, not
introspect `dash_render` directly.

### E4.3 — Honest declarations and a suite that cannot lie

**TR-04.15 — Correct the five declaration sites.** Remove `kdensity` from the scipy feature
list at `dash_setup.ado:99`, `dash_setup.ado:111`, `dash.pkg:15`, `dash.sthlp:1182-1183` and
`dash_setup.sthlp:76`. Keep `lfitci`, `qfitci` and `mspline`. Mark scipy and statsmodels
optional in the module docstring at `dash_render.py:43-49` so it agrees with
`dash_setup.ado:103-104` (`local pkg_required "bokeh numpy pandas"` /
`local pkg_optional "scipy statsmodels"`), and re-read the sentence at
`dash_render.py:465-470` — the item cites `:469-470`, which is exactly the
`kdensity`/`lowess` sentence inside the `_optional_import` docstring (the function begins at
`:466`).

**TR-04.16 — The doc-consistency test.** Add to `test/test_dependency_guards.py` (375 lines
at HEAD) a class that (a) parses the feature lists out of all five declaration sites with
regular expressions, (b) derives the true feature sets from the code — the guarded call sites
are `_optional_import(...)` for standalone and the emitted `from scipy import stats`
(`dash_render.py:13256`, `:13320`) / `PchipInterpolator` (`:13512`) /
`statsmodels…smoothers_lowess` (`:12860`) for server — and (c) asserts they agree, naming the
disagreeing site in the failure message. The test must also encode the two asymmetries that
make this non-obvious, so a future reader does not "simplify" them away: **standalone
`qfitci` needs no scipy** (`TestQfitciNeedsNoScipy` already asserts it) while **served
`qfitci` does** (`scipy.stats.t.ppf` at `:13344`), and `kdensity` needs neither in either mode
(`_KERNELS` at `:6595`).

**TR-04.17 — The runner skip-accounting regression test.** Add to
`test/test_cscript_hygiene.py` — which already reads `test/run_all_cscripts.do` as text in
`test_the_runner_does_not_probe_python_by_executing_it` — a test that asserts the runner
reaches a non-zero exit when nothing passed. Assert on the *structure*, not on a string: that
the summary block contains a branch keyed on the pass count being zero and that its body
contains `exit 1`, and that no reachable path prints `ALL TESTS PASSED` when `n_pass` is zero.
A source-level assertion keeps the test runnable without Stata, in line with the file's
existing style and with the project memory that the cert suite needs `arch -arm64` from
`test/`.

**TR-04.18 — The BASELINE.md note.** Append a dated addendum to `.ultraplan/BASELINE.md`
(which already carries dated addenda — `# Addendum — defects surfaced while executing S01
(2026-09-18)` at `:499`, `# Addendum — batch 2 (2026-09-18)` at `:703`). It must state, for
the **current 25** cscripts, how many reach Python end to end, list those that do not with the
reason, and name S16 as the owner of widening the coverage. Recompute the numbers — the plan's
"4 of 11" is stale, as is BASELINE.md's own `:206-211` orphan record (2 orphans; both
`test_adversarial.cscript` and `test_e2e_serve.cscript` are wired into the runner now, which
`test_cscript_hygiene.py::TestEveryCscriptIsWiredIntoTheRunner` enforces).

---

## Work items

Every item below is reproduced with the number it carries in the phase assignment.

### 1. Validate `scheme()` in Stata

> Validate `scheme()` in Stata and raise a clear error naming the fourteen supported names,
> instead of the renderer warning and falling back to `s2color`. Binding decision 1 says
> "never a silent fallback".

- **Tags:** functional · `stata` · **medium** · origin **S11-05**
- **Where:** `dash.ado` (no scheme validation exists today), `dash_render.py:_resolve_scheme_name` (`:7970-7982`)
- **Evidence:** `PLAN.md:36-37` requires "a clear error naming the supported names — never a
  silent fallback to black or to `s2color`". Measured at HEAD: `warnings.warn(...)` then
  `_raw_name = ""` → `s2color`; `dash.ado` has **no** scheme-name validation.
- **Requirements:** TR-04.1, TR-04.2, TR-04.3, TR-04.4, TR-04.5, TR-04.7

### 2. Retire the arbitrary-`.scheme`-file path

> Retire the arbitrary-`.scheme`-file path, which is also the path-traversal surface the plan
> said to remove. `SchemeParser._resolve_path` still resolves any `name.endswith(".scheme")`
> from the CWD, and `_resolve_scheme_name` explicitly exempts it from the known-name check.
> Keep the `_resolve_path` guards for the bundled set — defence in depth stays.

- **Tags:** functional · `standalone` · **medium** · origin **S11-05**
- **Where:** `dash_render.py:SchemeParser._resolve_path` (`:1691-1714`), `_resolve_scheme_name`
- **Evidence:** `_resolve_path`'s `is_file_ref` branch tries
  `os.path.abspath(os.path.join(os.getcwd(), name))` first; `_resolve_scheme_name` exempts the
  suffix with `not _raw_name.endswith(".scheme")`. 11-05: *"This retires the
  arbitrary-`.scheme`-file path, which also removes the path-traversal surface that commits
  `fae476d` and its predecessor were hardening — note that in the commit message."*
- **Requirements:** TR-04.5, TR-04.6, TR-04.8

### 3. Replace `_MAX_IPS` with a real limiter structure

> Replace `_MAX_IPS` with a real limiter structure. It is an eviction primitive: one machine
> cycling 10,000 forwarded keys took 300 sessions inside a 60-second window against a nominal
> 60. A larger cap does not fix it. (Project rule 3.)

- **Tags:** functional · `server` · **medium** · origin **S13** (REMAINING.md's status table files `_MAX_IPS` under S14; §6 is headed `[S13, S14, S16-04]`)
- **Where:** `dash_render.py:_RateLimiter._MAX_IPS` — emitted source, `:12997`; class at `:12992`; eviction at `:13016-13024`
- **Evidence:** 300 sessions in a 60-second window against a nominal 60. The emitted comment
  itself concedes the shape: *"which makes the cap itself an eviction primitive."*
- **Requirements:** TR-04.13, TR-04.14

### 4. Cap the dropdown filter's option count and warn

> Cap the dropdown filter's option count and warn. A dropdown on a continuous variable emits
> one `<option>` per distinct value with no cap — 200,001 options on 200,000 observations. No
> `_MAX_FILTER_OPTIONS`/`_MAX_DROPDOWN` constant exists.

- **Tags:** functional · `both` · **small** · origin **S13**
- **Where:** `dash_render.py:FilterBuilder.build_dropdown` (`:7571`; class `:7557`; insertion
  point `:7629-7638`); served filter-widget loop (dropdown at `:15378`)
- **Evidence:** 200,001 options on 200,000 observations; and, from 08-05, *"Measured on 5,000
  distinct dates: **5,001 options, zero warnings**."*
- **Requirements:** TR-04.9, TR-04.10

### 5. Cap the number of `by()` groups and warn

> Cap the number of `by()` groups and warn. `by(id)` builds one figure per distinct value with
> no limit. No `_MAX_BY_GROUPS`/`_MAX_FACETS`/`_MAX_TABS` constant exists.

- **Tags:** functional · `both` · **small** · origin **S12**
- **Where:** `dash_render.py:_expand_by_groups` (`:8776`; callers `:11403`, `:11436`); the
  emitted app's own `by()` / `by(total)` loops
- **Evidence:** no constant, no clamp at HEAD. 15-03's audit: *"`_expand_by_groups` occurs 3×
  in `DashRenderer` and **0×** in the emitted app, which still carries its own `by_total`
  handling."*
- **Requirements:** TR-04.11, TR-04.12

### 6. Regression test for the certification runner's skip accounting

> Write the regression test for the certification runner's skip accounting. Nothing prevents a
> regression to `exit 0`; 01-04 required the test and it was never written.

- **Tags:** deliverable · `stata` · **small** · origin **S01**
- **Where:** `test/run_all_cscripts.do` (the code under test; the new test belongs in
  `test/test_cscript_hygiene.py`)
- **Evidence:** 01-04: *"Write the test for this before the change: assert that a run in which
  every script skips does not report success."* The behaviour is present at
  `run_all_cscripts.do:721-741`; the test is not.
- **Requirements:** TR-04.17

### 7. The BASELINE.md end-to-end coverage note

> Write the BASELINE.md note on end-to-end cscript coverage that 01-05 required.

- **Tags:** deliverable · `n/a` · **small** · origin **S01**
- **Where:** `.ultraplan/BASELINE.md`
- **Evidence:** 01-05: *"Also note in BASELINE.md that only 4 of 11 cscripts currently reach
  Python end to end — `test_parser.cscript`'s single `dash` call passes `name()`, which routes
  to `_dash_register_graph` and never renders. S16 owns widening that."* REMAINING.md's status
  table lists "BASELINE.md coverage note" as one of S01's two open items.
- **Requirements:** TR-04.18

### 8. Correct the stale dependency declarations

> Correct the stale dependency declarations. `kdensity` is declared scipy-dependent in five
> places and provably is not (S07 replaced `gaussian_kde` with dash's own `_KERNELS`);
> `dash_render.py:43-49` still lists scipy and statsmodels as flat dependencies although
> `dash_setup.ado:103-104` marks them optional. Keep `qfitci` in the scipy list — the server
> path does use `scipy.stats.t.ppf`.

- **Tags:** functional · `n/a` · **small** · origin **S01**
- **Where:** `dash_setup.ado:99`, `:111`; `dash.pkg:15`; `dash.sthlp:1182-1183`;
  `dash_setup.sthlp:76`; `dash_render.py:43-49`, `:469-470`
- **Evidence:** the 01-03 refutation — *"`kdensity` is declared scipy-dependent in five places
  and provably is not; `dash_render.py:43-49` still lists scipy/statsmodels as hard
  dependencies"*. All five sites are quoted verbatim in *Why this phase exists*.
- **Requirements:** TR-04.15

### 9. The doc-consistency test for optional dependencies

> Add a doc-consistency test asserting the advertised optional-dependency feature lists agree
> with the actually-guarded call sites, so the declarations cannot go stale again.

- **Tags:** deliverable · `n/a` · **small** · origin **S01**
- **Where:** `test/test_dependency_guards.py`
- **Evidence:** the declarations went stale once already (item 8); nothing at HEAD compares
  the advertised lists against the guarded call sites.
- **Requirements:** TR-04.16

---

## Test plan

Project rule 8 governs every functional item: **the regression test is written first and must
fail against HEAD**. Project rule 4 governs every new function: a unit test each. Every test
below names a real file. A test that cannot be made to fail is not evidence, so each group
states the mutation that must kill it.

### E4.1 — Constrain the scheme surface (items 1, 2)

**Write these first — they must fail at HEAD.**

| # | Test | File | Fails at HEAD because |
|---|---|---|---|
| F1 | `dash build, saving(t.html) scheme(s1colour)` returns non-zero and writes no file | new `test/test_scheme_validation.cscript` | today it returns rc 0, warns, and writes an `s2color` dashboard |
| F2 | `dash scatter mpg weight, name(g1) scheme(nosuch)` fails at registration | same cscript | `dash.ado` has no validation at `:405`/`:732` |
| F3 | a crafted `evil.scheme` in the CWD is never opened by `dash build, scheme(evil.scheme)` | `test/test_path_validation.cscript` (extend; it already covers `_dash_validate_path` traversal at `:89-92`, `:131`) | `_resolve_path`'s `is_file_ref` branch tries the CWD first |
| F4 | `_resolve_scheme_name` treats a `.scheme` name as unknown | `test/test_scheme.py` | the `and not _raw_name.endswith(".scheme")` exemption |

**Unit tests (rule 4).**

- `_dash_validate_scheme`: one case per accepted name (14 + 6 aliases), case-insensitivity,
  empty input, a name with a leading/trailing space, a name containing `/`, a name containing
  `..`, and a name that is exactly `.scheme`. Home: the new cscript for the Stata side;
  `test/test_scheme.py` for the Python side of TR-04.5.
- `SchemeParser._resolve_path` after TR-04.6: each of the 14 bundled names still resolves;
  a traversal attempt is still rejected by the containment check — i.e. **prove the guard
  still runs** rather than assuming it is unreachable. Home: `test/test_scheme.py`,
  `test/test_scheme_consumption.py`.
- List equality (TR-04.7): the `dash.ado` name list equals `SchemeParser._BUILTIN_NAMES`, and
  the alias list equals `_THEME_SCHEME_MAP`'s keys. Home: `test/test_scheme.py`.
- `session_scheme` exemption (TR-04.3): a spec whose only scheme key is a non-translated
  `session_scheme` builds with a warning and rc 0, not an error. Home:
  `test/test_scheme_coercion.py` (which already owns fallback behaviour) or
  `test/test_theme_aliases.py`.

**Integration / cscript coverage.** The new `test_scheme_validation.cscript` must be added to
`test/run_all_cscripts.do` — `test_cscript_hygiene.py::TestEveryCscriptIsWiredIntoTheRunner`
will fail if it is not — and must guard Python availability through `c(python_exec)` rather
than by executing Python, which
`test_cscript_hygiene.py::test_no_script_probes_python_by_executing_it` enforces. Extend
`test/test_help_conformance.py` to assert `dash.sthlp` no longer contains the
working-directory `.scheme` instruction. `test/test_security_surface.py` is the right home for
an assertion that the help does not advertise a capability the code has removed — it already
carries `test_the_help_does_not_claim_an_access_control_it_has_not_got`.

**Mutation proofs.**

- Re-insert `and not _raw_name.endswith(".scheme")` → F4 must die.
- Restore the `is_file_ref` CWD candidate in `_resolve_path` → F3 must die.
- Change the `exit 198` in `_dash_validate_scheme` to `exit 0` → F1 and F2 must die.
- Delete one name from the `dash.ado` list → the TR-04.7 equality test must die.
- Delete the containment check in `_resolve_path` → the "guard still runs" unit test must die.
  (If it does not, the guard is already unreachable and the test is vacuous — fix the test.)

### E4.2 — Bound what a spec can ask the renderer to build (items 3, 4, 5)

**Write these first — they must fail at HEAD.**

| # | Test | File | Fails at HEAD because |
|---|---|---|---|
| F5 | a dropdown built on 200,000 distinct values yields ≤ `_MAX_FILTER_OPTIONS` options and warns | `test/test_resource_limits.py` | no cap exists; 200,001 options, no warning |
| F6 | a `%td` dropdown on 5,000 distinct dates warns and suggests `type(range)` | `test/test_filters.py` or `test/test_filter_widget_parity.py` | measured: 5,001 options, zero warnings |
| F7 | `by()` with 2,000 distinct groups yields ≤ `_MAX_BY_GROUPS` figures and warns | `test/test_resource_limits.py`, cross-checked in `test/test_layout_facets.py` | no cap exists |
| F8 | the same over-cardinality dropdown and `by()` specs behave identically in both renderers | `test/test_mode_parity.py` | the emitted app has its own filter loop and its own facet loop |
| F9 | one client cycling 10,000 forwarded keys inside one window is admitted no more than the stated bound | `test/test_server_rate_limit.py` | measured 300 against a nominal 60 |
| F10 | the store never exceeds its configured maximum during that churn | `test/test_server_rate_limit.py` | (guards the property `_MAX_IPS` does deliver, so the fix cannot trade memory for correctness) |

**Unit tests (rule 4).**

- The two new constants exist, are integers, are > 0, and are the *same* number the emitted app
  uses — the shape `test_resource_limits.py::TestMbandBandsIsBounded::test_the_two_modes_use_the_same_limit`
  already establishes for `_MAX_MBANDS`. Copy it.
- `build_dropdown` at, just below and just above the limit (boundary: `n = limit-1`, `limit`,
  `limit+1`) — exactly, warning count and option count asserted separately.
- `_expand_by_groups` at the same three boundaries, asserting figure count and warning text.
- Ordinary-cardinality silence: `rep78` (5 groups) and `foreign` (2) warn nothing; a 12-value
  dropdown warns nothing. A cap that fires at ordinary sizes is a regression, not a fix.
- The new limiter structure: admit/deny at the boundary for a single key; window expiry;
  overflow-bucket behaviour for untracked keys; `xff:` key-space separation
  (`test_a_trusted_key_cannot_collide_with_a_real_remote_ip` already covers the principle);
  `/health` still answers 200 with `_SESSION_LIMITER` exhausted.
- Keep `TestTheCapIsNotAnEvictionPrimitive::test_eviction_drops_the_least_recently_seen` green
  throughout — the new structure must not regress the LRU property that test bought.

**Integration / cscript coverage.** `test/test_e2e_filters.cscript` gains a high-cardinality
dropdown case asserting the build completes with rc 0 and the warning reaches the Stata log
(`test_render_log_clean.cscript` already establishes the pattern for asserting on renderer
output). `test/test_serve_options.cscript` and `test/test_server_serves.py` cover the served
side end to end.

**Mutation proofs.**

- Raise `_MAX_FILTER_OPTIONS` to 10,000,000 → F5 must die.
- Delete the `warnings.warn` but keep the clamp → F5/F6/F7 must die on the warning assertion,
  proving the test checks the *explanation* and not only the count.
- Delete the clamp but keep the warning → the same tests must die on the count assertion.
- Apply the clamp in `DashRenderer` only → F8 must die.
- Revert the limiter to the `_MAX_IPS` eviction cap → F9 must die while F10 stays green
  (which is exactly the HEAD state, and the reason F10 alone is not sufficient evidence).
- Set the overflow bucket's budget to infinity → F9 must die.

### E4.3 — Honest declarations and a suite that cannot lie (items 6, 7, 8, 9)

**Write these first — they must fail at HEAD.**

| # | Test | File | Fails at HEAD because |
|---|---|---|---|
| F11 | the runner has a zero-pass branch whose body exits non-zero, and no path prints `ALL TESTS PASSED` when `n_pass` is zero | `test/test_cscript_hygiene.py` | no such test exists (the behaviour does; the guard does not) |
| F12 | every advertised scipy/statsmodels feature list matches the guarded call sites | `test/test_dependency_guards.py` | `kdensity` is in five scipy lists and uses `_KERNELS` |
| F13 | the module docstring marks scipy and statsmodels optional | `test/test_dependency_guards.py` | `dash_render.py:43-49` lists them flat |

**Unit tests (rule 4).** F12's parser is a function and needs its own tests: given a synthetic
declaration string, it returns the expected feature set; given a malformed one, it fails loudly
rather than returning an empty set (an empty set would make F12 pass vacuously — this is the
single most important test in E4.3). Add explicit cases pinning the two asymmetries:
standalone `qfitci` needs no scipy, served `qfitci` does; `kdensity` needs neither anywhere.

**Integration coverage.** F12 must read the real files, not fixtures, so that editing
`dash.pkg` without editing the code fails the suite. Item 7's BASELINE note is prose and is
reviewed, not tested — but the numbers in it must be produced by running the suite, not
estimated, and the note must say which run produced them.

**Mutation proofs.**

- Change the runner's `exit 1` in the zero-pass branch to `exit 0` → F11 must die.
- Delete the whole `else if \`n_pass' == 0` block → F11 must die.
- Add `kdensity` back to `dash.pkg:15` only → F12 must die, naming `dash.pkg`.
- Remove `qfitci` from a scipy list → F12 must die (it is still required in server mode).
- Make the declaration parser return an empty set on any input → the parser's own unit test
  must die; if F12 still passes, F12 is vacuous.

### Suite-level

The whole pytest suite and the whole certification suite run before any commit (project rule
5). Per project memory, the cert suite runs with `arch -arm64` from `test/`, and **a skip is
not a pass** — which is the very property item 6 makes permanent. Set `$dash_nobrowser` before
any Stata run that builds a dashboard.

---

## Definition of done

A reviewer can tick each of these.

**E4.1 — scheme surface**

- [ ] `_dash_validate_scheme` exists in `dash.ado` and is called from all three typed
      surfaces (graph-level `scheme()`, `dash build, scheme()`, `dash serve`).
- [ ] A non-translated `scheme()`/`theme()` name exits 198 with a message naming all 14
      schemes and all 6 aliases; no output file is written.
- [ ] A non-translated `c(scheme)` (`session_scheme`) does **not** error and still falls back
      to `s2color`.
- [ ] `_resolve_scheme_name`'s `.scheme` exemption is gone.
- [ ] `_resolve_path`'s CWD file-reference branch is gone; the containment guards remain and
      are proven to still run by a test that dies when they are deleted.
- [ ] `dash.sthlp:1084`'s working-directory instruction is replaced; `test_help_conformance.py`
      passes.
- [ ] A test asserts the `dash.ado` name list and `_BUILTIN_NAMES` are equal sets.
- [ ] The commit message notes that this retires the path-traversal surface
      (11-05's instruction), naming no tooling or vendor.

**E4.2 — resource limits**

- [ ] `_MAX_FILTER_OPTIONS` and `_MAX_BY_GROUPS` are defined beside the existing caps at
      `dash_render.py:121-131`, with a comment stating the measurement each answers.
- [ ] Both are enforced in `DashRenderer` **and** in the emitted server app, from one number.
- [ ] Each over-limit case warns with the count, the limit and the remedy, and returns rc 0.
- [ ] Ordinary cardinality (`foreign`, `rep78`, a 12-value dropdown) warns nothing.
- [ ] `_MAX_IPS` is replaced by a structure for which the 300-in-60 measurement no longer
      reproduces; the replacement keeps bounded memory, keeps LRU eviction, keeps the `xff:`
      key space and keeps `/health` independent.
- [ ] The `_RateLimiter` docstring describes the structure that is actually there.
- [ ] `test_server_rate_limit.py`'s existing classes are all still green.

**E4.3 — declarations and suite integrity**

- [ ] `kdensity` appears in no scipy feature list in `dash_setup.ado`, `dash.pkg`,
      `dash.sthlp` or `dash_setup.sthlp`.
- [ ] `qfitci` still does, and a comment or test says why (served `scipy.stats.t.ppf`).
- [ ] `dash_render.py:43-49` distinguishes required from optional.
- [ ] `test/test_dependency_guards.py` fails when any one declaration site is edited alone.
- [ ] `test/test_cscript_hygiene.py` fails when the runner's zero-pass branch is weakened.
- [ ] `.ultraplan/BASELINE.md` carries a dated note giving the current end-to-end cscript
      coverage, the scripts that do not reach Python and why, and S16 as the owner.

**Phase-level**

- [ ] Every functional item has a regression test that was demonstrated to fail before the fix
      (rule 8) — the demonstration recorded in the commit or PR body.
- [ ] Every new function has a unit test (rule 4).
- [ ] Full pytest suite green; full certification suite green with honest skips.
- [ ] Conformance corpus still reports zero `r(198)` — confirm no corpus entry uses a
      non-translated scheme name.
- [ ] Work committed on `feature/batch4-interactive-layer`, never directly to `main`; the
      merge command reported rather than run (rule 6).

---

## Risks and sequencing notes

**R1 — The Stata-side error could break a working session.** `session_scheme` carries
`c(scheme)`, which on a user's machine may be any Stata scheme, translated or not. If
validation is applied to the resolved name rather than to the typed one, every user running a
non-translated session scheme gets `r(198)` on a command that works today. TR-04.3 is the
mitigation and its test (a spec whose only scheme key is a non-translated `session_scheme`)
is not optional.

**R2 — Constraining the input is not a reason to delete the guard.** 11-05 says so explicitly.
The temptation after TR-04.6 is to drop `_resolve_path`'s containment check as unreachable.
The mutation proof in E4.1 exists to keep that check both present and *live*; if deleting it
fails no test, the guard has already become decorative and that is itself a finding.

**R3 — Cap values are judgements, not measurements.** 1,000 options and 50 facets are proposed
from house precedent (`_MAX_BINS`, `_MAX_MBANDS`, `_FP_GRID_MAX` are all 1,000) and from what
Stata's own example datasets need. They must be ratified in review. A cap that fires on
legitimate work is worse than no cap, because the user cannot tell whether the dashboard is
wrong or merely truncated — which is why every clamp warns with a remedy and none aborts.

**R4 — The `by()` cap has to be written twice until 15-03 lands.** `_expand_by_groups` occurs
3× in `DashRenderer` and 0× in the emitted app, which carries its own `by_total` handling.
TR-04.12 requires both copies now and a parity test to hold them together. If the unification
phase is scheduled before or alongside this one, coordinate: the clamp should be applied to the
single delegated path instead of being duplicated and later deduplicated. This is the only
item in the phase with a real cross-phase interaction.

**R5 — The rate-limiter fix is design work inside emitted string literals.** It is the one
medium item here that could grow. Keep the change inside `_RateLimiter` and
`_client_ip_from_request`; do not touch `_SESSION_LIMITER` / `_HEALTH_LIMITER` separation or
the `--trust-forwarded-for` default (`_TRUST_FORWARDED_FOR = False`), both of which are
already tested and already correct. If the design review cannot settle the overflow-bucket
shape quickly, land items 4 and 5 first — they are independent and small — and keep item 3 on
its own commit.

**R6 — The two S01 deliverables are cheap and unblock a gate; do them first.** Item 6 is a
source-level pytest and item 7 is prose; together they close S01 and convert the S16-07 gate
*"full certification suite with honest skips"* from a promise into something a test enforces.
Doing them first also means every subsequent test in this phase runs under a suite that cannot
report a false pass.

**R7 — The adversarial suite gate has no home file yet.** Task 16-04 names
`test/test_adversarial_py.py`; `ls test/` shows `test_adversarial.cscript` but no such Python
file. Items 2–5 are precisely the resource-exhaustion and injection surfaces 16-04 enumerates
("scheme names (constrained in S11) … `by()` specs … the server endpoints and rate limiter"),
so the tests written here should be shaped so 16-04 can cite them rather than re-write them.

**Suggested internal order.** 6 → 7 → 8 → 9 → 4 → 5 → 1 → 2 → 3. Test integrity first, then
the declarations (small, self-contained, and they make the suite's claims true), then the two
small caps, then the scheme pair as one unit (they share a commit and a help edit), then the
limiter redesign last so it can take the time it needs without holding anything else up.
