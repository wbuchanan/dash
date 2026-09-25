# Phase 19 — S07 statistical options

**Purpose.** Section 07 changed `dash`'s statistical *defaults* to Stata's, and the audit
agrees it worked: two of its six tasks are DONE and none is NOT DONE. What Section 07 did
not finish is the *option surface* that lets a user move those defaults. Of the 25 options
the plan dispositioned `implement-S07`, **13 are accepted and reported as ignored** — they
reach `dash.ado` only through the trailing `*` catch-all, so their values are thrown away
before any renderer could read them, and no renderer reads any of the thirteen as an option:
ten of the names never occur in `dash_render.py` at all, and the three that do — `area`,
`mean` and `discrete` — occur only as a plot type, as the statistic, and as comment prose
about `colordiscrete`, never as an option key. The other 12 are declared, serialized and
honoured in `DashRenderer`,
but nothing proves they survive the option-surface regeneration that Phases 17 and 18 are
about to perform, and at least one of them — `range()` — is honoured by only two of the
seven layers that take it. Alongside that sit the two S07 tasks the adversarial pass
overturned from DONE to PARTIAL: `07-02` shipped a confidence-level test that cannot see
`c(level)` at all, and `07-04` left the session level stranded outside the server plot loop,
so `set level 90` changes a standalone band and leaves the served one at 95. This phase
closes the S07 slice of the option surface and finishes the `c(level)` chain in both
renderers, with tests that are shown to fail first.

---

## At a glance

| | |
|---|---|
| **Items** | 4 (numbered 1–4 below, exactly as handed over) |
| **Functional vs deliverable** | 3 functional · 1 deliverable |
| **Effort mix** | 1 small · 2 medium · 1 large |
| **Renderers touched** | `both` (items 1, 3, 4) · `server` only (item 2). Item 3's largest surface is `GlyphMapper`, which is copied verbatim into the emitted `bokeh serve` app (`dash_render.py:12518` splices `GlyphMapper._histogram_grid` and its siblings), so most standalone work lands in both modes for free — the facet branches are the exception, and they belong to Phases 06–08. |
| **Ultraplan tasks discharged** | `07-02` (the value-asserting `c(level)` test) and `07-04` (the session level, server half) from **Section S07**; plus `OPT-S07` — the S07 slice of the `implement` disposition measured in REMAINING.md §2 and Appendix A's `05-04`: 25 options, 13 undeclared and 12 declared. |
| **Not discharged here** | The 56 non-S07 undeclared options (Phases 20–22), the generator/abbreviation/reporting machinery itself (Phases 17–18), the faceted-server statistical defects owned by `15-03` (Phases 06–08), and the help/CHANGELOG reconciliation sweep (Phase 30). |
| **Depends on** | **Phase 17** — item 3 cannot start until the 13 options are declared and serialized; the item text says so explicitly ("once 05-04 makes their values reachable"). **Phase 18** — the abbreviation truth, the generator's idempotency and the canonical-name reporting all sit under the same regeneration; item 4's `_dash_pending` edits are lost if the generator is re-run afterwards. Item 2 additionally wants **Phases 05–08** (server unification) landed first, or the same merge has to be written twice. |
| **Unblocks** | **Phase 30** (the help's `{marker unsupported}` list and `.ultraplan/CHANGELOG.md` must name whatever this phase implements) and **Phase 31** (the option-surface and conformance gates). |
| **Source of items** | All four come from the **main body** of `REMAINING.md`: §2 "Blocker — the option surface" (items 3, 4) and the "17 DONE claims the adversarial pass overturned" table, rows `07-02` and `07-04` (items 1, 2). Appendix A's `05-04` supplies the declared/undeclared split; Appendix C's `05-04` supplies the regeneration hazard that shapes the sequencing. |

---

## Why this phase exists

### The measurement — REMAINING.md §2, "Blocker — the option surface"  [S05-04, S07, S09, S10]

> Every one of the 115 options in `test/fixtures/rejected_options.json` was
> re-run through `dash` in Stata at HEAD and classified by dash's own report.
>
> | plan disposition | total | honoured | accepted + reported ignored |
> |---|---:|---:|---:|
> | accept-and-report | 4 | 0 | 4 ✅ *as intended* |
> | implement-S06 | 3 | 0 | **3** |
> | implement-S07 | 25 | 12 | **13** |
> | implement-S09-axes-text | 28 | 2 | **26** |
> | implement-S09-style | 50 | 3 | **47** |
> | implement-S10 | 5 | 2 | **3** |
> | **total** | **115** | **19** | **96** |
>
> **0 rejections.** The drop-in claim holds at the syntax layer and decision 4
> (accept, never abort, report together) is satisfied — but **92 options the
> plan said to implement are only accepted and reported**, so their values
> never reach the spec.
>
> Not implemented, by family:
>
> - **S07 (13):** `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts`
>   `fitplot` `logit` `mean` `nofit` `noweight` `predopts`

and, on how large the remaining work is allowed to be:

> **Two defensible ways to close this**, and the choice is the user's:
> **(a)** implement all 92 — the plan as written; **(b)** implement the high-value
> subset (`text` `ttitle`/`tlabel` family, the `b1/l1/r1/t1title` set,
> `mlabformat` `mstyle` `lstyle` `acolor` `gap` `fxsize` `fysize` `scale`) and
> formally re-disposition the rest to accept-and-report in the plan and help.

Note that the (b) shortlist contains **no S07 option**. Choosing (b) does not delete this
phase; it converts item 3 from "implement 13" into "re-disposition 13, in the plan, in
`dash.ado`'s `_dash_pending`, and in `dash.sthlp`'s unsupported list" — which is still work,
still has to round-trip through `test/test_help_conformance.py`, and is still this phase's.

### The declared/undeclared split — REMAINING.md, Appendix A, `05-04 · PARTIAL`

> `dash.ado` declares 158 option tokens across its `syntax` blocks and tracks 39 more in
> `_dash_pending`. Cross-referencing against the 111 options the plan dispositioned
> "implement":
>
> | disposition | total | declared | **not declared** |
> |---|---:|---:|---:|
> | implement-S06 | 3 | 3 | 0 |
> | implement-S07 | 25 | 12 | **13** |
> | implement-S09-axes-text | 28 | 15 | **13** |
> | implement-S09-style | 50 | 7 | **43** |
> | implement-S10 | 5 | 5 | 0 |
> | **total** | **111** | **42** | **69** |
>
> **Remaining: declare and serialize these 69.** They reach `dash.ado` only
> through the trailing `*` catch-all, so no value ever arrives in the spec JSON
> and the sections that own them have nothing to read — which is exactly the
> state 05-04 exists to end.
>
> - **S07 (13):** `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts`
>   `fitplot` `logit` `mean` `nofit` `noweight` `predopts`
>
> […]
>
> Each needs its S04 minimum abbreviation, a serializer entry, and a
> `_dash_pending` line so it stays reported until its section lands.
>
> > Corrects §2 of this file, which put the figure at 92 by treating every
> > reported option as undeclared. 27 of those are declared and serialized
> > already, and are reported because `_dash_pending` correctly says they are
> > awaiting their section.

**The two tables agree exactly on S07**, which is why this phase can be sized precisely
where the S09 phases cannot: the 13 reported-as-ignored options *are* the 13 undeclared
options, and the 12 honoured options *are* the 12 declared ones. There is no third group.

### The two overturned DONE claims — REMAINING.md, "17 DONE claims the adversarial pass overturned"

> | task | what the refutation found |
> |---|---|
> | 07-02 | no value-asserting test for the `c(level)` row |
> | 07-04 | the session level never reaches the server plot loop |

Both are marked `small` in that table's effort summary ("10 small, 5 medium, 1 large, 1
cosmetic"), and both are the reason Section 07 reads **2 DONE / 4 PARTIAL / 0 NOT DONE** in
the final tally, and

> | 07 | Statistical defaults | 6 | done ③, 13 options open ① | see §2 |

in the section-status table — where ③ means "CHANGELOG (self-reported)" and ① means
"measured this session". The CHANGELOG said done; the measurement said 13 options open.

### What the two refutations mean in the source, confirmed at HEAD

These reads confirm the audit's claims against the current tree; where a number is quoted
below it was produced by reading the file, not by restating the plan's own stale line
numbers.

**The Stata half of `07-04` is real.** `dash.ado` reads `c(level)` and serializes it on both
emission paths:

```stata
dash.ado:1720:    local _dash_lvl = c(level)
dash.ado:1723:    local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", … "level": "`_dash_lvl'", "formats": `_dash_fmt_json'}}"'
dash.ado:2335:    local _dash_lvl = c(level)
dash.ado:2343:    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{… ,"level":"`_dash_lvl'", …}}"'
```

and validates a per-plot `level()` in Stata, where the user can see the error
(`dash.ado:548-561`):

```stata
    // level() is validated HERE, where the user can see the error,
    // rather than becoming a Python exception inside the renderer.
    if `"`level'"' != "" {
        capture confirm number `level'
        if _rc {
            display as error "level() must be a number between 0 and 100"
            exit 198
        }
        if `level' <= 0 | `level' >= 100 {
            display as error "level() must be between 0 and 100 (exclusive)"
            exit 198
        }
    }
```

**`DashRenderer` consumes it correctly.** `dash_render.py:8078-8095` reads
`build_options["level"]` into `self.default_level` (falling back to `_DEFAULT_LEVEL = 95.0`
at `:114`, with a `UserWarning` on a value outside `(0, 100)` or a non-number), and
`dash_render.py:9931-9933` merges it into each layer that carries no `level()` of its own:

```python
            # A CI layer with no level() of its own inherits the session's.
            if "level" not in popts and self.default_level != _DEFAULT_LEVEL:
                popts = dict(popts, level=str(self.default_level))
```

**`ServerAppBuilder` has no such line.** The emitted plot loop at `dash_render.py:14031-14036`
reads the layer's options and never consults `build_options`:

```python
            '        for pi, plot in enumerate(plots):',
            "            ptype = plot.get('type', '')",
            "            yvar = plot.get('yvar', '') or plot.get('var', '')",
            "            xvar = plot.get('xvar', '')",
            "            y1var = plot.get('yvar1', '')",
            "            y2var = plot.get('yvar2', '')",
            "            opts = plot.get('options', {})",
```

Two CI layers escape the consequences by accident and the rest do not. `_compute_lfitci` and
`_compute_qfitci` are called with `opts.get('level')` (`dash_render.py:14376`, `:14403`) and
resolve it through the emitted `_dash_level` helper (`dash_render.py:13279-13293`), whose
*fallback* re-opens the spec:

```python
            'def _dash_level(level=None):',
            "    # A per-plot level() wins over the session's c(level), as in Stata.",
            '    # This took no argument, so level() on the plot was ignored and every',
            '    # band in server mode was drawn at c(level).',
            "    if level not in (None, ''):",
            …
            "            _lv = float(_s.get('build_options', {}).get('level', 95.0))",
```

`_compute_lpolyci`, by contrast, resolves its level from the *layer options only*
(`dash_render.py:13640`):

```python
            "    y_lower, y_upper = _bootstrap_ci(",
            "        x, y, x_grid, _fn, fallback=y_fit,",
            "        level=_resolve_level(options), seed=_resolve_seed(options))",
```

and `_resolve_level`'s default is the module constant, not the session
(`dash_render.py:6492`): `def _resolve_level(options: dict, default: float = _DEFAULT_LEVEL) -> float:`.
So at HEAD, `set level 90` followed by a served dashboard draws an `lfitci` band at 90 and an
`lpolyci` band at 95 **in the same figure**. Merging the session level into `opts` once, in
the loop, removes the divergence at its source instead of patching each helper.

**The `07-02` test is vacuous with respect to `c(level)`.** `test/test_statistical_defaults.py:491-526`
holds `TestConfidenceLevel`, whose fixture builds every spec through `make_dr` and sets the
level only in the *plot* options:

```python
    def _band_width(self, level=None):
        …
        opts = {} if level is None else {"level": str(level)}
        dr = make_dr(
            [{"type": "lfitci", "yvar": "mpg", "xvar": "weight",
              "options": opts}],
            df=df,
        )
```

and the session-default test asserts only that the no-option case equals 95:

```python
    def test_default_level_is_the_session_default(self):
        """With no level(), dash must use whatever c(level) was serialized."""
        assert self._band_width(None) == pytest.approx(self._band_width(95),
                                                       rel=1e-9)
```

`make_dr` (`test/conftest.py:246`) exposes `link`, `filters`, `hover`, `graph_name`,
`value_labels`, `value_label_names` and `render` — there is no `build_options["level"]`
parameter, so this test cannot set `c(level)` even in principle. Deleting
`dash_render.py:9932-9933` outright leaves it green. That is the refutation, restated as a
mutation: **the test the section's `<done>` rested on survives the removal of the code it
was written to certify.**

The server suite has the same hole from the other side. `test/test_server_statistics.py:49-58`
hardcodes `"level": "95"` into every spec's `build_options`, and
`test_level_reaches_the_server_ci` (`:230-239`) varies only the per-plot `level()`:

```python
    def test_level_reaches_the_server_ci(self, tmp_path):
        wide = _server_sources(tmp_path, _spec("lfitci", {"level": "99"}))
        narrow = _server_sources(tmp_path, _spec("lfitci", {"level": "50"}))
```

Per-plot `level()` in server mode is therefore already guarded. The **session** level is not
guarded anywhere, in either mode.

**The 13 undeclared options are absent from the renderer as well as from `dash.ado`.**
Grepping `dash_render.py` for `adjust`, `atobs`, `ciplot`, `estcmd`, `estopts`, `fitplot`,
`logit`, `nofit`, `noweight` and `predopts` returns **no match** — not even as a substring.
The remaining three names do occur in the file, but never as an option key: `area` (65
substring hits) is the `area`/`rarea` plot type, `mean` (65) is the statistic, and
`discrete` (18) is comment and docstring prose about `colordiscrete` and discrete colour
mapping — `dash.ado` does not declare `discrete` at all, and `_histogram_grid` has no
`discrete` branch. There is no half-built
implementation waiting for a value: the whole chain, from `syntax` to spec key to mapper, has
to be built for these thirteen.

### Where the 25 S07 options sit today

Reasons are quoted from `test/fixtures/rejected_options.json`, the same fixture §2 was
measured from (`disposition == "implement-S07"`, 25 entries).

| family (fixture `reason`) | declared + honoured (12) | **undeclared + reported (13)** |
|---|---|---|
| fit/CI estimation control (`ciopts`/`fitopts` family) | `level` | `atobs` `ciplot` `estcmd` `estopts` `fitplot` `nofit` `predopts` |
| lowess estimation control | — | `adjust` `logit` `mean` `noweight` |
| kernel-density / local-polynomial parameter | `bands` `kernel` `n` | `area` |
| histogram binning control | `bin` `start` `width` | `discrete` |
| histogram y-axis family | `density` `fraction` `frequency` `percent` | — |
| estimation range | `range` | — |

The whole `lowess` column is empty on the left: **not one** `lowess` estimation option
reaches the spec today.

### The regeneration hazard that sets this phase's order

REMAINING.md Appendix C, `05-04`, measured what re-running the option-surface generator does
to hand-written code in `dash.ado` — and two of the casualties are S07's:

> re-running scripts/regen_option_surface.py also deletes: (a) the whole level()
> validation block in _dash_parse_plot_opts (dash.ado:549-561), which is the
> only thing stopping `level(150)` becoming a Python exception inside the
> renderer; (b) the ENTIRE plot-level `local _dash_pending` accumulation
> (dash.ado:593-641) and `local _dash_unknown` (:642) plus its `sreturn local
> _pending`/`_unknown` (:770-771) — after a regen the whole file contains zero
> `sreturn local _pending`, so 05-03's reporter is dead at BOTH levels, not
> just graph level

Phases 17 and 18 exist to extend and de-fang that generator. Item 4's deliverable — "removing
each from `_dash_pending` as it lands" — is edits to exactly the block Appendix C says the
generator deletes. **Doing item 4 before Phase 18 means doing it twice.**

A second Appendix C finding bites S07 directly:

> `bw()` is hijacked: a legal twoway abbreviation of `bwidth()` is routed to `barwidth` and
> silently discarded, so kdensity/lowess/lpoly draw at the DEFAULT bandwidth with no note.

`bwidth()` is not one of this phase's 25 (it is already declared and honoured under its long
spelling), but the abbreviation fix lands in Phase 18 and changes which statistical layers
receive a bandwidth. Phase 19's statistical tests must be written so they still hold after it.

### What Section 07 itself asked for

From `.ultraplan/sections/section-07-statistical-defaults.md` — the requirements this phase
is finishing rather than restating:

> - BR-07.1 Every statistical default matches Stata's documented rule for the same command.
> - **BR-07.2 Every Stata option controlling those computations is honoured.**
> - **BR-07.3 `c(level)` is the default confidence level.**
> - BR-07.4 A value computed at render time and recomputed in JavaScript under filtering must
>   use the **same** rule, so the picture does not jump.

and, from task `07-04`'s own `<verify>`:

> Band endpoints match Stata at 90, 95 and 99; `set level 90` changes the default; all four
> sites move together.

The middle clause — `set level 90` changes the default — is the clause that was never tested
in standalone and never implemented in server mode.

---

## Epics

| epic | goal | items |
|---|---|---|
| **E19.1 — The confidence-level chain, proved end to end** | `c(level)` reaches, and is proved to reach, every CI layer in both renderers; a per-plot `level()` still wins. | 1, 2 |
| **E19.2 — Close the 12 declared S07 options** | Audit each of the twelve declared-and-serialized options against both renderers, close the gaps found, and take each off `_dash_pending` and out of the help's unsupported list as it lands. | 4 |
| **E19.3 — The 13 undeclared S07 options** | Once Phase 17 makes their values reachable, implement (or formally re-disposition) the thirteen options that today are accepted and thrown away. | 3 |

---

## User stories

### E19.1 — The confidence-level chain

**US-19.1.1** — *As a Stata user who has run `set level 90`, I want every confidence band
`dash` draws to be a 90% band, so that the dashboard reports the same interval as the rest of
my session.*

- **Given** a session where `c(level)` is 90, **when** I run
  `dash (scatter mpg weight) (lfitci mpg weight)` and `dash build, saving(d.html)`,
  **then** the band in `d.html` is narrower than the band the same command produces at
  `c(level)` 99, and matches the band produced by `level(90)` written on the layer.
- **Given** the same session, **when** the layer is `lpolyci` or `fpfitci` instead of
  `lfitci`, **then** the band is at 90 as well — no CI layer is exempt.
- **Given** `c(level)` is 90 **and** the layer carries `level(99)`, **when** the dashboard is
  built, **then** the layer's band is at 99: the per-plot option wins, as in Stata.

**US-19.1.2** — *As a `dash serve` operator, I want the served dashboard's bands to be the
bands the standalone HTML would have drawn, so that choosing a delivery mode never changes a
number.*

- **Given** a spec whose `build_options.level` is `"90"` and whose `lfitci` layer carries no
  `level()`, **when** the emitted app is built and `make_document` is run, **then** the
  `y_lower`/`y_upper` columns match the standalone renderer's for the same spec, within the
  tolerance `test/test_server_statistics.py` already uses for band comparison.
- **Given** the same spec with an `lpolyci` layer, **when** the document is built, **then**
  its band is at 90 too — today it is at 95 while `lfitci` in the same figure is at 90.
- **Given** a spec with `build_options.level` absent entirely (an older `dash.ado` against a
  newer renderer), **when** the app is built, **then** the level is 95 and no exception is
  raised.

**US-19.1.3** — *As a package maintainer, I want the level tests to die when the level code is
removed, so that a green suite means the feature works.*

- **Given** `dash_render.py:9932-9933` is deleted, **when** the statistical suite runs,
  **then** at least one test in `test/test_statistical_defaults.py` fails.
- **Given** the new server-side merge is deleted, **when** `test/test_server_statistics.py`
  runs, **then** at least one test fails.

### E19.2 — The 12 declared S07 options

**US-19.2.1** — *As a Stata user pasting a `twoway` command, I want `kdensity mpg, range(10 30)`
and `lfit mpg weight, range(2000 4000)` to mean what they mean in Stata, so that I do not have
to learn which layers `dash` happens to have wired `range()` into.*

- **Given** `dash kdensity mpg, range(10 30)`, **when** the dashboard is built, **then** the
  density is estimated over 10–30 — this already holds (`dash_render.py:4871-4885`).
- **Given** `dash (lfit mpg weight, range(2000 4000))`, **when** the dashboard is built,
  **then** the fitted line spans 2000–4000, **or** `range()` is named in the command's
  ignoring-unsupported note. Today `_fit_grid` (`dash_render.py:6419-6439`) takes its span
  from the observed data and never reads `range`, and no note is emitted.

**US-19.2.2** — *As a package maintainer, I want each of the twelve declared S07 options to be
either honoured or reported, in both renderers, with a test that says which, so that the
ignoring-unsupported note can be trusted as an inventory.*

- **Given** any of the twelve, **when** it is supplied with two different values, **then**
  either the rendered output differs (honoured) or the option is named in the note (reported)
  — never neither.
- **Given** the same twelve, **when** the assertion is run against `ServerAppBuilder` as well
  as `DashRenderer`, **then** it still holds.
- **Given** an option that this phase closes, **when** it is removed from `_dash_pending`,
  **then** `test/test_help_conformance.py` passes only because `dash.sthlp`'s
  `{marker unsupported}` list was updated in the same commit.

### E19.3 — The 13 undeclared S07 options

**US-19.3.1** — *As a Stata user pasting `twoway lowess mpg weight, bwidth(0.4) mean noweight`,
I want the estimation options to change the smoother, so that the curve I see is the curve
Stata computes.*

- **Given** `dash lowess mpg weight, mean`, **when** the dashboard is built, **then** the
  smoother is the running-mean variant, **or** `mean` is named in the note — today the token
  is swallowed by the `*` catch-all, the value is discarded, and the note names the raw token
  the user typed rather than a canonical option.
- **Given** `dash histogram rep78, discrete`, **when** the dashboard is built, **then** the
  bins are one per distinct value, **or** `discrete` is named in the note.
- **Given** `dash fpfit mpg weight, estopts(degree(1))`, **when** the dashboard is built,
  **then** the fit honours the estimation option **or** reports it. The fixture
  `test/fixtures/stat_truth.json` records that Stata accepts exactly this spelling
  (`fpfit_optsupport["auto:estopts_degree"] = {"cmd": "twoway fpfit mpg weight, estopts(degree(1))", "rc": 0}`)
  while rejecting `bwidth()` and `degree()` on the same command with rc 198.

**US-19.3.2** — *As a package maintainer, I want any of the thirteen that we decline to
implement to be declined **in writing**, so that the plan, the code and the help agree.*

- **Given** a decision to re-disposition an option to accept-and-report, **when** the commit
  lands, **then** the option is declared in `dash.ado`, listed in its `_dash_pending` block,
  described under `dash.sthlp`'s `{marker unsupported}` heading, and its disposition is
  changed in the plan — and `test/test_help_conformance.py` passes.
- **Given** a user supplies the abbreviated form of such an option, **when** the note is
  printed, **then** it names the canonical option, not the prefix typed.

---

## Business requirements

| id | requirement | how it is testable |
|---|---|---|
| **BR-19.1** | `c(level)` is the default confidence level for **every** CI-bearing layer (`lfitci`, `qfitci`, `lpolyci`, `fpfitci`) in **both** renderers. A per-plot `level()` overrides it. | Band width at `c(level)` 90 < 95 < 99 with no per-plot option, asserted per layer and per renderer. |
| **BR-19.2** | The same spec produces the same band in standalone and server mode, to the tolerance already used by `test/test_server_statistics.py`. | Direct comparison of `y_lower`/`y_upper` for each CI layer. |
| **BR-19.3** | No test that certifies the level chain may pass when the level code is removed. | Mutation: delete `dash_render.py:9932-9933`, and the new server merge, and watch named tests fail. |
| **BR-19.4** | Every one of the 25 `implement-S07` options is, at the end of this phase, either **honoured** (its value changes the output) or **reported** (named in the ignoring-unsupported note) — in both renderers. Never silently dropped. | A converse parametrised test over the S07 slice of `test/fixtures/rejected_options.json`, run against both renderer classes. |
| **BR-19.5** | An option that becomes honoured is removed from `_dash_pending` **and** from `dash.sthlp`'s unsupported list in the same commit. | `test/test_help_conformance.py`, which the help itself advertises fails "if they disagree in either direction". |
| **BR-19.6** | An option that is re-dispositioned to accept-and-report is declared (not left to the `*` catch-all), listed in `_dash_pending`, documented in the help, and its disposition changed in the plan. | Same conformance test, plus the note naming the canonical option rather than the typed prefix. |
| **BR-19.7** | Stata remains the place where a bad statistical value is reported: `level(150)` exits 198 at the Stata prompt, never as a Python traceback. | `test/test_option_surface.cscript` check; the validation block at `dash.ado:548-561` must survive Phase 18's regeneration. |
| **BR-19.8** | Every default this phase changes is written into `.ultraplan/CHANGELOG.md` with before and after values and the dataset that demonstrates the change, as `07-06` requires of every S07 change. | CHANGELOG diff reviewed against the test output that produced the numbers. |

---

## Technical requirements

### TR-19.1 — Session level, standalone: the reference implementation (do not change it)

`DashRenderer.__init__` reads the session level into `self.default_level`
(`dash_render.py:8078-8095`), defaulting to `_DEFAULT_LEVEL = 95.0` (`:114`) and warning on a
value outside `(0, 100)` or a non-number. The per-layer merge is `dash_render.py:9931-9933`.
`_resolve_level(options, default)` (`:6492-6520`) is the single resolver: a per-plot `level()`
wins, a bad one warns and falls back. **This chain is correct and is the mirror item 2 names.**
Changing it is out of scope; it is the oracle the server side is measured against.

### TR-19.2 — Session level, server: merge once, in the loop

Add to the emitted plot loop at `dash_render.py:14031-14036`, immediately after
`opts = plot.get('options', {})`, the mirror of `:9932-9933`: when `'level'` is not in `opts`
and the spec's `build_options['level']` differs from 95, rebind `opts` to a copy carrying the
session level as a string. The spec is already reachable in the emitted app — `_dash_level`
reads `_s.get('build_options', {})` at `dash_render.py:13293` — so the value needs no new
transport.

Consequences to verify rather than assume:

- `_compute_lfitci` / `_compute_qfitci` (`dash_render.py:13237`, `:13302`) are called with
  `opts.get('level')` at `:14376` and `:14403`; after the merge they receive the session level
  explicitly instead of relying on `_dash_level`'s fallback. Behaviour must not change for
  these two — this is the regression risk of the change.
- `_compute_lpolyci` (`:13605`) calls `_resolve_level(options)` at `:13640`, whose default is
  `_DEFAULT_LEVEL`. After the merge it receives the session level. **This is the layer the fix
  actually repairs.**
- `fpfitci`'s server path is owned by the `15-03` phases (REMAINING.md §4 records that
  `fpfitci` renders `VArea`(α .2) + `Line` in standalone and `Line` only in server mode, i.e.
  "the confidence band is missing in server mode"). Item 2 must not be blocked on it: merge the
  level now, and the band inherits it when Phases 05–08 restore the band.

### TR-19.3 — The failing test for the standalone session level

`test/test_statistical_defaults.py:491-526` (`TestConfidenceLevel`) needs a fixture that can
set `build_options["level"]`. `make_dr` (`test/conftest.py:246-258`) has no parameter for it,
so either extend `make_dr` with a `build_options`/`level` keyword or build the spec inline in
the test module as `test/test_server_statistics.py:49-58` (`_spec`) does. Item 1 names the
three layers to cover: `lfitci`, `lpolyci`, `fpfitci`. The assertion is comparative — band at
90 strictly narrower than band at 99 with **no per-plot `level()`** — which is robust to the
bootstrap seed in a way an absolute endpoint is not (`_bootstrap_ci` is at
`dash_render.py:2651`, `_resolve_seed` at `:6522`, default 42).

Ground truth for the absolute form, should it be wanted, is already committed:
`test/fixtures/stat_truth.json` carries `ci_bands` keys
`auto:lfitci:level90|level95|level99|no_level_option` and the same four for `qfitci`, across
the `auto`, `census`, `nlsw88` and `sp500` datasets, with `_meta.c_level_default == 95`.
`test/test_statistical_truth.py:405` (`TestConfidenceBandsAgainstStata`) already consumes that
fixture — the `no_level_option` rows are the ones a `c(level)` test should be driven from.

### TR-19.4 — The failing test for the server session level

`test/test_server_statistics.py:49-58` hardcodes `"level": "95"` in `_spec`. Parametrise it,
or add a sibling helper, so a spec can be emitted with `build_options["level"]` set to 90 and
no per-plot `level()`. `_server_sources` (`:70-82`) builds the app with
`dr.ServerAppBuilder(sp, dp).build(str(ap))`, imports it and runs `make_document(doc)`;
`_standalone_sources` (`:84-97`) renders the same spec through `DashRenderer`; `_pick`
(`:99-104`) selects a source by column names. Everything the comparison needs exists — only
the session-level dimension is missing.

### TR-19.5 — The 13 undeclared options: the chain each one needs

Nothing exists for these today. Per option, in order:

1. **Declaration** — `dash.ado:_dash_parse_plot_opts` syntax block (the plot-level block
   spans `:484-540`; `LEvel(string)`, `BAnds(string)`, `Kernel(string)`, `N(string)`,
   `BIN(string)`, `Width(string)`, `START(string)`, `PERCENT`, `FREQuency`, `DENsity`,
   `FRACtion` and `RAnge(string asis)` are the declared S07 twelve, at `:488-499`). This is
   **Phase 17's** work; item 3 consumes it.
2. **Abbreviation** — an entry in `test/fixtures/abbrev_truth.json` measured by
   `scripts/extract_abbrev_truth.do`, because `resolve_minimums()` in
   `scripts/regen_option_surface.py` asserts on ambiguity. **Phase 18's** work.
3. **Serialization** — `sreturn local <opt>` beside the existing statistical returns
   (`dash.ado:696` `bands`, `:711` `range`, `:670` `jseed`) and a key in
   `_dash_plot_opts_to_json` (`:854`, whose key list at `:865-870` currently ends
   `… blabel horizontal vertical sort range colorlist jitterseed`).
4. **Consumption** — a read in the owning `GlyphMapper` method, listed in TR-19.6.
5. **Reporting** — a `_dash_pending` line in the plot-level block (`dash.ado:593-641`) until
   step 4 lands, then its removal.
6. **Help** — an entry under `dash.sthlp`'s `{marker unsupported}` heading while pending,
   removed and replaced by a real option description when honoured.

### TR-19.6 — Where each of the 13 lands in the renderer

Current mapper offsets in `dash_render.py`, read at HEAD:

| mapper | line | options it owns from this phase |
|---|---:|---|
| `map_area` | 3592 | — (plot type, not the `area()` option) |
| `map_lfit` | 3821 | `range` (via `_fit_grid`) |
| `map_qfit` | 3873 | `range` (via `_fit_grid`) |
| `map_lfitci` | 3918 | `level` · `ciplot` `fitplot` `nofit` `atobs` `estcmd` `estopts` `predopts` |
| `map_qfitci` | 3998 | `level` · same CI family |
| `map_lowess` | 4091 | `adjust` `logit` `mean` `noweight` |
| `map_lpoly` | 4272 | `area` `kernel` `n` `range` |
| `map_lpolyci` | 4344 | `level` `area` `kernel` `n` |
| `map_fpfit` | 4517 | `estcmd` `estopts` `predopts` (`bwidth`/`degree` are **not** Stata options here — see TR-19.8) |
| `map_fpfitci` | 4569 | `level` + the same estimation family |
| `map_histogram` | 4636 | `bin` `start` `width` `discrete` · `density` `fraction` `frequency` `percent` |
| `map_kdensity` | 4806 | `area` `bands` `kernel` `n` `range` |
| `map_mspline` | 5912 | — |
| `map_mband` | 5983 | `bands` (already honoured at `:6026`) |

The shared helpers those mappers read through, and which most of the 13 should extend rather
than bypass:

- `_stat_option_float(options, key, default, layer, lo=None, hi=None)` — `:6534-6592`. The
  house rule for reading a numeric statistical option: a bad value warns and falls back
  instead of taking the whole render down. **Every numeric option added by this phase must go
  through it.**
- `_fit_grid(x, options)` — `:6419-6439`. Reads `n()` (default `_FIT_GRID`, bounds 2–10000)
  and spans the observed min/max. Does **not** read `range()`.
- `_histogram_grid(arr, options)` — `GlyphMapper` static method at `:4707`, called from
  `map_histogram` at `:4668`. Resolves `start()`, `width()`, `bin()` with Stata's precedence
  and returns `(edges, ymode)`, with a `_MAX_BINS = 1000` clamp that warns rather than
  clamping silently. `discrete` belongs here.
- `_histogram_heights(counts, edges, ymode)` — `:6711-6741`. Implements the y-axis family:
  `frequency` → counts, `fraction` → counts/total, `percent` → 100·counts/total, otherwise
  density (`counts / (total * widths)`).
- `_stata_bin_count(n)` — `:6743`. Stata's `k = min(sqrt(N), 10·ln(N)/ln(10))`, truncated.
- `_KERNELS` — `:6595`, the kernel dictionary `kernel()` selects from.
- `_bootstrap_ci` — `GlyphMapper._bootstrap_ci` at `:2651`, signature carries `level` and
  `seed`; `_resolve_seed` at `:6522` (default 42).

### TR-19.7 — The emitted app's copies

`ServerAppBuilder` splices the standalone statistical helpers into the generated source rather
than re-implementing them — `dash_render.py:12518` splices `GlyphMapper._histogram_grid` and
siblings, and `:12488` lists `_resolve_level`, `_resolve_seed`, `_jitter_seed` among the
module-level helpers carried over. Consequently an option added inside `_histogram_grid`,
`_histogram_heights`, `_fit_grid` or `_stat_option_float` reaches server mode automatically.
An option added to a *mapper body* does not, because the emitted app calls its own
`_compute_*` functions (`_compute_histogram` `:13192`, `_compute_lfit` `:13212`,
`_compute_qfit` `:13227`, `_compute_lfitci` `:13237`, `_compute_qfitci` `:13302`,
`_compute_kdensity` `:13354`, `_compute_lowess` `:13396`, `_compute_lpoly` `:13428`,
`_compute_fpfit` `:13492`, `_compute_mspline` `:13509`, `_compute_mband` `:13524`,
`_compute_lpolyci` `:13605`). **Prefer the helper.** Where a mapper body must change, the
matching `_compute_*` must change with it, and the parity test named in the test plan is what
catches a divergence.

### TR-19.8 — Measured facts that constrain the 13

Taken from `test/fixtures/stat_truth.json`, which `07-01` produced by running Stata:

- `fpfit_optsupport` records `twoway fpfit mpg weight, bwidth(5)` → **rc 198** and
  `twoway fpfit mpg weight, degree(1)` → **rc 198**, while
  `twoway fpfit mpg weight, estopts(degree(1))` → **rc 0** and
  `twoway fpfit mpg weight, estopts(powers(1 2))` → **rc 0**, on both `auto` and `census`.
  The fixture's own `contradictions_with_section_07_plan` entry states the consequence
  plainly: dash's help is wrong to document `bwidth()`/`degree()` on `fpfit`, "degree() is
  spelled estopts(degree(#)) and there is no bandwidth concept in fpfit at all. The right fix
  is to report them as unsupported, not to honour them." So `estopts` is the real lever for
  the `fpfit` family, and anything this phase does for `estcmd`/`estopts`/`predopts` must
  respect Stata's spelling rather than inventing one.
- `dash.sthlp:770` already carries the corrected statement (`{bf:{cmd:fpfit} does not take
  {cmd:bwidth()} or {cmd:degree()}.}`), so the help and the fixture agree; only the option
  plumbing is missing.
- `_meta.c_level_default` is `95`, which is why `_DEFAULT_LEVEL = 95.0` is the right fallback
  and why a `c(level)` test must use a value **other than 95** to be non-vacuous.

### TR-19.9 — `range()` is the measurable gap among the declared twelve

`range()` is declared (`dash.ado:499` `RAnge(string asis)`), serialized (`:711`) and read in
exactly two places:

- `map_kdensity`, `dash_render.py:4865-4885`, with a comment that records the earlier defect
  verbatim: *"dash read range() in the `function' branch and nowhere else, so `kdensity mpg,
  range(10 30)' estimated over the default span and said nothing about it."*
- the `function` branch of `DashRenderer`, `:10046-10052` (and the emitted twin at `:13383`
  inside `_compute_kdensity`).

`_fit_grid` — the grid for `lfit`, `qfit`, and anything else that draws a fitted line — does
not read it. The fixture's disposition reason for `range` is "estimation range for a
fit/smoother plot", so item 4's "confirm which of these the renderer already honours and close
the rest" has a concrete first answer: **`range()` on a fit or smoother layer is neither
honoured nor reported.** Either thread it into `_fit_grid` (clamping to the observed range is
not acceptable — Stata's `range()` may extend beyond the data, exactly as `map_kdensity`
allows) or add `range` back to `_dash_pending` with a note that it applies to `kdensity` and
`function` only.

### TR-19.10 — The other eleven declared options: what the audit already proves

Each was measured as honoured in §2's table; the specific machinery, for the confirmation
pass item 4 requires:

| option | honoured where | proof already in the suite |
|---|---|---|
| `bin` | `_histogram_grid` (`:4707`) | `test_statistical_defaults.py:566` `test_bin_option_overrides` — 20 bins from `{"bin": "20"}` |
| `width` | `_histogram_grid` | `:569` `test_width_option_sets_the_grid` — `right - left == 2.0` |
| `start` | `_histogram_grid` | `:573` `test_start_option_sets_the_left_edge` — `left[0] == -10.0` |
| `density` | `_histogram_heights` (`:6711`) | `:576` `test_default_y_axis_is_density` (areas sum to 1) and `test_explicit_density_is_honoured` |
| `fraction` `frequency` `percent` | `_histogram_heights` | the sibling tests in `TestHistogramDefaults` |
| `kernel` | `_KERNELS` (`:6595`), read by `map_kdensity` and `map_lpoly` | `test_server_statistics.py` `test_the_kernel_option_reaches_the_server` |
| `n` | `_fit_grid` (`:6419`) and the `function` branch (`:10053-10060`, capped at 10000) | `test_statistical_defaults.py:127` `test_n_option_is_honoured` |
| `bands` | `map_mband` at `:6026` via `_stat_option_float(options, "bands", …)`; emitted twin at `:13536` | `test_statistical_truth.py:305` `TestMbandAgainstStata` |
| `level` | `_resolve_level` (`:6492`), merge at `:9932` | `TestConfidenceLevel` (per-plot only — the gap item 1 fills) |

`jitterseed`, which item 4 lists, is **not** one of the 25 `implement-S07` options in
`test/fixtures/rejected_options.json`; it is dash's own declaration
(`dash.ado:500 JITTERSEED(string)`, serialized as `jseed` at `:670`) and it is honoured —
`dash_render.py:2346-2362` reads both spellings, with `jseed()` winning when both are given,
and `_resolve_seed` at `:6522` documents the same. It is included here because it travels with
the statistical-seed family; the confirmation pass should record it as already closed rather
than open work.

### TR-19.11 — `_dash_pending` is already clean for these options — and fragile

The plot-level pending block at `dash.ado:593-641` does **not** name `bands`, `bin`,
`density`, `fraction`, `frequency`, `jitterseed`, `kernel`, `level`, `n`, `percent`, `range`,
`start` or `width`. The comment immediately above it (`:584-592`) records why:

```stata
    // This list went stale once.  Later sections implemented bin(),
    // level(), kernel(), width(), start(), n(), fraction/percent/
    // frequency, falpha(), mlcolor(), mlwidth() and -- at graph level --
    // scheme(), xsize(), ysize(), xtick() and ytick(), and nothing took
    // them off it.  So
    //     . dash scatter mpg weight, level(90)
    //     dash: ignoring unsupported option(s): level()
    // while the interval was in fact computed at 90.  A note that names
    // the wrong options is worse than no note: it tells the user to stop
    // using something that works.
```

So item 4's removal clause is **already satisfied at HEAD for the twelve declared options**,
and its remaining substance is (a) the confirmation pass, (b) `range()` on fits (TR-19.9), and
(c) making sure the state survives. Appendix C establishes that re-running
`scripts/regen_option_surface.py` deletes this entire block — so the correct closure for item 4
is a *test* that pins it, not a code edit that a regeneration silently reverts.

### TR-19.12 — The reporting contract must be checked in both modes

REMAINING.md Appendix C, `05-04`, on the shape of the existing guard:

> `test/test_unsupported_report_is_true.py` only tests ONE direction — for each option ON the
> pending list, that rendering twice does not change the output. Nothing asserts the converse:
> every option dash DECLARES must either change the rendered output or be named on
> `_dash_pending`. […] The existing test also instantiates `dr.DashRenderer` only
> (test_unsupported_report_is_true.py:178) and never `ServerAppBuilder`, so it is blind to
> every server-mode gap by construction.

The converse test is **Phase 18's** deliverable. This phase owns the S07 slice of it: the 25
options from `test/fixtures/rejected_options.json` with
`disposition == "implement-S07"`, asserted in both renderers. Driving it from the fixture
rather than from a literal list is what keeps it from going stale.

### TR-19.13 — Validation stays in Stata

`dash.ado:548-561` rejects `level(150)` with rc 198 and a message the user sees. Appendix C
records that this block is deleted by a generator re-run. Phase 19's cscript coverage must
assert the rc, so that a Phase 18 regeneration that drops the block fails a test rather than
shipping a Python traceback. The renderer's own guards (`_resolve_level` at `:6492`,
`self.default_level` validation at `:8082-8095`) stay as defence in depth; they are not a
substitute, because the user never sees the warning at the Stata prompt.

---

## Work items

All four items are reproduced with the tag, `files` and `origin` they were handed over with.
`kind`: `functional` = a user-visible behaviour gap; `deliverable` = a test, cscript, help
sentence or changelog entry the task asked for.

---

### Item 1 — value-asserting tests for the `c(level)` row

> Add the value-asserting tests for the `c(level)` row that 07-02 required: render an
> lfitci/lpolyci/fpfitci layer with `build_options["level"]="90"` and no per-plot `level()`,
> and assert the band is narrower than the same spec at 99.

| | |
|---|---|
| **kind** | deliverable |
| **renderer** | both |
| **effort** | small |
| **Where** | `test/test_statistical_defaults.py` |
| **Origin** | `S07` — REMAINING.md main body, "17 DONE claims the adversarial pass overturned", row `07-02` |
| **Epic** | E19.1 |

**Evidence.** The refutation row reads, in full: *"07-02 | no value-asserting test for the
`c(level)` row"*. `07-02`'s own `<done>` was "A failing, value-asserting test exists for every
row of the register", and `c(level)` is a row of that register
(`:1343-1344`, `:2441`, `:8101`, `:8123` — "95% fixed in four places" → "`level()`, defaulting
to `c(level)`"). At HEAD `TestConfidenceLevel` (`test/test_statistical_defaults.py:491-526`)
sets the level only in plot options and asserts the no-option case equals 95 — which is also
`_DEFAULT_LEVEL`, so the test passes whether or not the session level is ever read. Deleting
`dash_render.py:9932-9933` leaves the whole class green.

---

### Item 2 — merge the session level into the server plot loop

> Merge the session level into the server plot loop's `opts` when a layer carries no `level()`
> of its own — the mirror of `DashRenderer:9932-9933`. Today `c(level)` never reaches server
> mode.

| | |
|---|---|
| **kind** | functional |
| **renderer** | server |
| **effort** | medium |
| **Where** | `dash_render.py:14036` (ServerAppBuilder plot loop) |
| **Origin** | `S07` — REMAINING.md main body, row `07-04` ("the session level never reaches the server plot loop") |
| **Epic** | E19.1 |

**Evidence.** The emitted loop at `dash_render.py:14031-14036` ends
`opts = plot.get('options', {})` with no consultation of `build_options`. Two layers escape
by accident — `_compute_lfitci`/`_compute_qfitci` reach `_dash_level`, whose fallback reads
`_s.get('build_options', {}).get('level', 95.0)` (`:13293`) — while `_compute_lpolyci` resolves
through `_resolve_level(options)` (`:13640`), whose default is `_DEFAULT_LEVEL`. So a session
at `set level 90` draws an `lfitci` band at 90 and an `lpolyci` band at 95 in the same served
figure. `07-04`'s `<verify>` required "all four sites move together"; in server mode they do
not. Merging once in the loop, as `DashRenderer` does, makes every downstream helper see the
same level without touching four call sites.

---

### Item 3 — implement the 13 undeclared S07 options

> Implement the 13 S07 statistical options once 05-04 makes their values reachable: `adjust`
> `area` `atobs` `ciplot` `discrete` `estcmd` `estopts` `fitplot` `logit` `mean` `nofit`
> `noweight` `predopts`. Each is accepted today and reported as ignored, so the value never
> reaches the spec.

| | |
|---|---|
| **kind** | functional |
| **renderer** | both |
| **effort** | large |
| **Where** | `dash_render.py` statistical mappers (`map_lfitci`, `map_qfitci`, `map_kdensity`, `map_lpoly`, `map_histogram`, …) |
| **Origin** | `OPT-S07` — REMAINING.md §2, "S07 (13)", confirmed by Appendix A's `05-04` declared/undeclared table |
| **Epic** | E19.3 |

**Evidence.** §2's table: `implement-S07 | 25 | 12 | 13`. Appendix A's table: the same 13 are
the ones declared nowhere — "They reach `dash.ado` only through the trailing `*` catch-all, so
no value ever arrives in the spec JSON and the sections that own them have nothing to read."
Confirmed at HEAD: none of `adjust`, `atobs`, `ciplot`, `estcmd`, `estopts`,
`fitplot`, `logit`, `nofit`, `noweight` or `predopts` appears anywhere in `dash_render.py`;
the other three names (`area`, `mean`, `discrete`) occur only as a plot type, a statistic and
comment prose about `colordiscrete`, never as an option key.
Mapper targets and per-family ownership are in TR-19.6; the `estopts`-vs-`degree()` constraint
that Stata itself imposes on the `fpfit` family is in TR-19.8. §2 also records the alternative
the user may choose — formally re-dispositioning options to accept-and-report — and BR-19.6
states what that costs in `dash.ado`, the help and the plan.

---

### Item 4 — close the 12 declared-and-serialized S07 options

> Implement the S07 options that are already declared and serialized but still reported as
> pending: `bands` `bin` `density` `fraction` `frequency` `jitterseed` `kernel` `level` `n`
> `percent` `range` `start` `width` — confirm which of these the renderer already honours and
> close the rest, removing each from `_dash_pending` as it lands.

| | |
|---|---|
| **kind** | functional |
| **renderer** | both |
| **effort** | medium |
| **Where** | `dash.ado:_dash_pending` (`:363`, `:590`), `dash_render.py` statistical mappers |
| **Origin** | `OPT-S07` — REMAINING.md §2 (the 12 honoured of 25) |
| **Epic** | E19.2 |

**Evidence and the confirmation pass this item asks for.** Twelve of the thirteen names are the
`implement-S07` options that §2 measured as **honoured**; the thirteenth, `jitterseed`, is
dash's own declaration (`dash.ado:500`, serialized as `jseed` at `:670`, honoured at
`dash_render.py:2346-2362`) and is not in the S07 disposition set at all. The `_dash_pending`
blocks at `dash.ado:363` (graph level) and `:590`-onwards (plot level) do not name any of the
twelve at HEAD; the comment at `:584-592` records that they were taken off deliberately when
their sections landed. So the confirmation half of this item resolves to three concrete
outputs:

1. `range()` is honoured by `map_kdensity` (`dash_render.py:4865-4885`) and the `function`
   branch (`:10046`) and by **nothing else** — `_fit_grid` (`:6419`) ignores it. That is a live
   silent drop on every fit and smoother layer. Honour it or report it (TR-19.9).
2. The other eleven have a named, existing test each (TR-19.10). The item's deliverable for
   them is a test that pins the *state*, because Appendix C shows the pending block is deleted
   by a generator re-run.
3. `jitterseed` is already closed; record it as such rather than re-opening it.

---

## Test plan

Two project rules govern this plan. **Rule 8** — every bug fix gets a regression test written
*before* the fix, shown to fail, and shown to pass after. **Rule 4** — every function gets a
unit test, and the application keeps end-to-end coverage. This repository has a documented
history of tests that passed against broken implementations (item 1 *is* one of them), so every
test below carries the mutation that must kill it.

### E19.1 — The confidence-level chain (items 1, 2)

#### Write these first, and watch them fail

| # | test | file | fails at HEAD because |
|---|---|---|---|
| T1 | `test_session_level_narrows_the_standalone_band` | `test/test_statistical_defaults.py` (extend `TestConfidenceLevel`, `:491`) | It does not exist. Once written it **passes** at HEAD — `DashRenderer` is correct — so its value is proved by mutation M1, not by a red run. Record that explicitly in the commit message; this is the one test in the phase that cannot start red. |
| T2 | `test_session_level_reaches_every_ci_layer` (parametrised over `lfitci`, `lpolyci`, `fpfitci`) | `test/test_statistical_defaults.py` | Same — passes at HEAD, guarded by M1. |
| T3 | `test_session_level_reaches_the_server_ci` | `test/test_server_statistics.py` (beside `test_level_reaches_the_server_ci`, `:230`) | **Fails red at HEAD for `lpolyci`**: `_compute_lpolyci` resolves through `_resolve_level(options)` (`dash_render.py:13640`) whose default is 95, so a spec with `build_options["level"] = "90"` and no per-plot `level()` produces the same band as one at 99±nothing. This is the rule-8 regression test for item 2. |
| T4 | `test_server_and_standalone_agree_on_the_session_level` | `test/test_server_statistics.py` | Same failure, expressed as a parity gap against `_standalone_sources` (`:84`). |

#### Unit tests (rule 4)

- `_resolve_level` (`dash_render.py:6492`) — per-plot value wins; empty/absent falls back to
  the passed default; non-numeric and out-of-range each warn once and fall back. Three of these
  exist in spirit (`test_invalid_level_is_reported`, `:523`); assert the *default* argument is
  honoured, which nothing does today.
- `DashRenderer.default_level` (`:8078-8095`) — parametrise `build_options["level"]` over
  `"90"`, `"99"`, `""`, `"0"`, `"100"`, `"abc"`; assert the resolved attribute and the warning
  text for the last three.
- The emitted `_dash_level` (`dash_render.py:13279-13293`) — exercised through the built app in
  T3/T4 rather than directly, since it exists only in generated source.

#### Integration / cscript coverage

- `test/test_server_build.cscript` — build a served app from a session where `c(level)` has
  been changed with `set level 90`, assert rc 0 and that the emitted `.py` is produced. The
  numeric assertion stays in pytest; the cscript proves the Stata→spec→app path carries the
  value.
- `test/test_e2e_serve.cscript` — one `lpolyci` layer under `set level 90`, asserting the build
  completes and the app file exists (honest skip if `bokeh` is unavailable — a skip is not a
  pass).

#### Mutations — each must kill a named test

| id | break this | must kill |
|---|---|---|
| **M1** | Delete `dash_render.py:9932-9933` (the standalone merge). | T1, T2. If `TestConfidenceLevel` alone stays green, item 1 has not been done. |
| **M2** | Delete the new server-loop merge (TR-19.2). | T3, T4. |
| **M3** | In `_resolve_level` (`:6492`), ignore the `default` argument and return `_DEFAULT_LEVEL`. | T1/T2's `lpolyci` parametrisation. |
| **M4** | In the emitted `_dash_level` (`:13293`), replace the `build_options` read with the literal `95.0`. | T3 for `lfitci`/`qfitci` — this is the fallback the merge is *not* allowed to regress. |

### E19.2 — The 12 declared S07 options (item 4)

#### Write these first

| # | test | file | fails at HEAD because |
|---|---|---|---|
| T5 | `test_range_is_honoured_or_reported_on_a_fit_layer` | `test/test_statistical_defaults.py` | **Red.** `dash (lfit mpg weight, range(2000 4000))` produces the same grid as without it — `_fit_grid` (`:6419`) spans the observed data — and `range` is not on `_dash_pending`, so nothing is reported. The assertion is the disjunction from BR-19.4: output differs **or** the option is named. |
| T6 | `test_s07_declared_options_are_honoured_or_reported` — parametrised over the 12 `implement-S07` options read from `test/fixtures/rejected_options.json`, run against `DashRenderer` **and** `ServerAppBuilder` | `test/test_unsupported_report_is_true.py` (the S07 slice of the converse test Phase 18 generalises) | **Red on `range`** today, and red on anything Phase 18's regeneration silently reverts. Driving it from the fixture is what stops it going stale. |
| T7 | `test_pending_list_does_not_name_an_implemented_statistical_option` | `test/test_help_conformance.py` or a new `test/test_s07_pending_state.py` | Green at HEAD; it exists to pin TR-19.11 so that a generator re-run that restores the stale list fails a test instead of shipping a wrong note. |

#### Unit tests (rule 4)

- `_fit_grid` (`:6419`) — with and without `range()`; with `range()` wider than the data (must
  extend, not clamp); with a malformed `range()` (must warn through `_stat_option_float`'s
  house rule, not raise).
- `_histogram_grid` (`:4707`) — `bin` / `width` + `start` precedence, the `_MAX_BINS = 1000`
  clamp warning, and a denormal width. Partly covered at
  `test/test_statistical_defaults.py:566-575`; extend rather than duplicate.
- `_histogram_heights` (`:6711`) — each of the four `ymode` values, including the `total <= 0`
  early return.
- `_stat_option_float` (`:6534`) — absent, empty, non-numeric, below `lo`, above `hi`; one
  warning each, default returned.
- `_resolve_seed` (`:6522`) and `_jitter_seed` (`:2346-2362`) — `jseed` wins over `jitterseed`
  when both are given; the default is 42.

#### Integration / cscript coverage

- `test/test_option_surface.cscript` — a new check in the O2 series (O2-08 or later, alongside
  the existing O2-01…O2-07 documented at `:57-76`) asserting that a command carrying every
  `implement-S07` option returns rc 0 and that the note names **exactly** the options still
  pending, no more and no fewer.
- `test/test_statistical_defaults.py` and `test/test_statistical_truth.py` stay the value
  oracles; `test/fixtures/stat_truth.json` supplies Stata's own answers
  (`histogram`, `kdensity`, `lowess`, `lpoly`, `mband`, `fpfit`, `ci_bands`).

#### Mutations

| id | break this | must kill |
|---|---|---|
| **M5** | Make `_fit_grid` ignore `range()` after it is implemented. | T5, T6. |
| **M6** | Re-add `level` to the plot-level `_dash_pending` block (`dash.ado:593-641`) — the exact stale state the comment at `:584-592` describes. | T7, and `test/test_help_conformance.py`. |
| **M7** | In `_histogram_heights` (`:6711`), return raw counts for every `ymode`. | The `density`/`fraction`/`percent` tests in `TestHistogramDefaults`. |
| **M8** | In `_stat_option_float`, swallow the warning and return the default silently. | The bad-value tests in `TestBandwidthSemantics` (`:180-268`) and the new unit tests. |

### E19.3 — The 13 undeclared S07 options (item 3)

#### Write these first

| # | test | file | fails at HEAD because |
|---|---|---|---|
| T8 | `test_thirteen_s07_options_reach_the_spec` — for each of the 13, run `dash` with the option and assert the value appears in the plot's `options` dict in the spec JSON | `test/test_option_surface.cscript` (new check) driven from `test/fixtures/rejected_options.json` | **Red for all 13.** They reach `dash.ado` only through the trailing `*` catch-all, so no key is written. This is the rule-8 regression test for Phase 17's half of the chain and this phase's consumer half. |
| T9 | `test_lowess_estimation_options_change_the_smoother` — `adjust`, `logit`, `mean`, `noweight` | `test/test_statistical_defaults.py` (beside `TestBandwidthSemantics`, `:180`) | **Red.** `dash_render.py` contains no occurrence of `adjust`, `logit` or `noweight`, and reads `mean` only as the statistic, never as a lowess option key. |
| T10 | `test_histogram_discrete_bins_one_per_value` | `test/test_statistical_defaults.py` (`TestHistogramDefaults`, `:534`) | **Red.** `_histogram_grid` has no `discrete` branch. |
| T11 | `test_fpfit_estopts_is_honoured_or_reported`, using the spellings `test/fixtures/stat_truth.json` proves Stata accepts (`estopts(degree(1))`, `estopts(powers(1 2))`) and rejects (`bwidth(5)`, `degree(1)`, both rc 198) | `test/test_statistical_defaults.py` or `test/test_statistical_truth.py` | **Red.** Neither `estopts` nor `estcmd` nor `predopts` exists in `dash_render.py`. |
| T12 | `test_ci_family_options_are_honoured_or_reported` — `atobs`, `ciplot`, `fitplot`, `nofit`, `predopts` on `lfitci`/`qfitci` | `test/test_statistical_defaults.py` | **Red**, under the same disjunction as T6: change the output or be named in the note. |
| T13 | `test_kdensity_area_is_honoured_or_reported` | `test/test_statistical_defaults.py` | **Red.** `area` occurs in the renderer only as the `area`/`rarea` plot type; no kdensity code path reads an `area` option key. |

If the project chooses §2's option **(b)** for any of the thirteen, its test flips from the
"honoured" branch of the disjunction to the "reported" branch — the test itself does not
change shape, which is the point of writing it as a disjunction.

#### Unit tests (rule 4)

Every new reader added to a mapper or helper gets a direct unit test on the helper, not only
an end-to-end render:

- `_histogram_grid` with `discrete` — edges one per distinct value; interaction with `bin()`
  and `width()` (Stata's precedence decides, and the precedence must be asserted, not assumed).
- Whatever function parses `estopts(...)`/`estcmd(...)`/`predopts(...)` — a sub-option string
  parser is an injection surface (CLAUDE.md rule 16): assert it rejects or neutralises anything
  that is not a recognised estimation keyword, and that it never reaches `eval`/`exec`. The AST
  whitelist the `function` layer uses (`map_function`'s validator) is the precedent to follow,
  not to bypass.
- Each lowess estimation option, at the level of the smoother function rather than the figure.

#### Integration / cscript coverage

- `test/test_option_surface.cscript` — extend the O2 series so the corpus walk covers the 13
  with values, asserting rc 0 and the note's exact content after each option lands.
- `test/test_examples_run.cscript` and `test/test_conformance.cscript` — the conformance gate
  (zero `r(198)`, zero dropped series, zero dropped graphs) must stay green as each option is
  declared; a new declaration can collide with an existing abbreviation (Phase 18's
  `resolve_minimums()` assert), and the cscripts are where that surfaces in Stata.
- `test/test_mode_parity.py` — each newly honoured option must be exercised in both renderers,
  or the parity corpus will certify only the standalone half. Note REMAINING.md §4: the corpus
  covers 17 of 36 plot types today, so a new statistical option on an uncovered type is
  unguarded until Phase 08 widens it.

#### Mutations

| id | break this | must kill |
|---|---|---|
| **M9** | Remove one of the 13 from the `syntax` block so it falls back to the `*` catch-all. | T8 for that option. |
| **M10** | Have the mapper read the option and discard it (assign to a local that is never used). | T9–T13 — this is the exact failure mode the audit found in 14 `map_*` methods that "currently accept `view=` and never reference it". |
| **M11** | Return a constant from the new `discrete` branch. | T10. |
| **M12** | Accept an unrecognised keyword inside `estopts(...)`. | The injection unit test. |

### Suite-level gates for the whole phase

- Full pytest, full certification suite with **honest** skips (a skip is not a pass), the
  conformance corpus and the parity corpus — the first four of the six `16-07` gates. Run from
  `test/` with `arch -arm64`.
- `test/test_help_conformance.py` must pass, which by construction means `dash.sthlp`'s
  `{marker unsupported}` list and `dash.ado`'s declarations agree in both directions.
- `test/test_fixtures_are_committed.py` — any fixture this phase regenerates must be committed.

---

## Definition of done

**E19.1 — the confidence-level chain**

- [ ] `test/test_statistical_defaults.py` contains a test that sets `build_options["level"]`
      (not a per-plot `level()`) and asserts a 90 band is narrower than a 99 band, for
      `lfitci`, `lpolyci` **and** `fpfitci`.
- [ ] Deleting `dash_render.py:9932-9933` makes that test fail (M1 demonstrated and recorded).
- [ ] The emitted server plot loop merges the session level into `opts` when the layer carries
      no `level()`, mirroring `dash_render.py:9932-9933`.
- [ ] A served `lpolyci` band under `c(level) == 90` matches the standalone band for the same
      spec; `lfitci`/`qfitci` are unchanged by the merge (M4 demonstrated).
- [ ] A per-plot `level()` still overrides the session level in both renderers.
- [ ] A spec with no `build_options["level"]` still renders at 95 without raising.

**E19.2 — the 12 declared options**

- [ ] Each of `bands` `bin` `density` `fraction` `frequency` `kernel` `level` `n` `percent`
      `range` `start` `width` is recorded, with evidence, as honoured or reported — in both
      renderers.
- [ ] `range()` on a fit or smoother layer is honoured, or named in the ignoring-unsupported
      note; the silent drop is gone either way.
- [ ] `jitterseed` is recorded as already closed (`dash.ado:500` → `jseed` at `:670` →
      `dash_render.py:2346-2362`), not re-opened.
- [ ] A test pins the `_dash_pending` state so a generator re-run that restores the stale list
      fails rather than ships (M6 demonstrated).

**E19.3 — the 13 undeclared options**

- [ ] For each of `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts` `fitplot`
      `logit` `mean` `nofit` `noweight` `predopts`: the value reaches the spec JSON (Phase 17)
      **and** either changes the render or is named in the note (this phase).
- [ ] Any option re-dispositioned to accept-and-report is declared in `dash.ado`, listed in
      `_dash_pending`, described in `dash.sthlp`, and re-dispositioned in the plan — all four,
      in one commit.
- [ ] `estopts`/`estcmd`/`predopts` parsing rejects anything that is not a recognised
      estimation keyword, with a unit test proving it, and never reaches `eval`/`exec`.
- [ ] The `fpfit` family follows Stata's measured truth: `estopts(degree(#))` is the lever;
      `bwidth()`/`degree()` are reported, not honoured (`stat_truth.json:fpfit_optsupport`).

**Cross-cutting**

- [ ] `level(150)` still exits 198 **in Stata**, and a cscript asserts it
      (`dash.ado:548-561` survived).
- [ ] Every changed default is in `.ultraplan/CHANGELOG.md` with before/after values and the
      dataset that demonstrates the change.
- [ ] `dash.sthlp` and `dash.ado` agree; `test/test_help_conformance.py` passes.
- [ ] Full pytest and the full certification suite pass with honest skip accounting; the
      conformance and parity corpora are green.
- [ ] Every new test has a named mutation that kills it, demonstrated and recorded.
- [ ] Work committed to the feature branch, never to `main`; the merge command reported, not
      run (project rules 5–7).

---

## Risks and sequencing notes

**1. Item 3 cannot start before Phase 17, and item 4's edits cannot survive before Phase 18.**
Item 3's own text says "once 05-04 makes their values reachable". Item 4's removal clause edits
`dash.ado:593-641`, which Appendix C proves `scripts/regen_option_surface.py` deletes wholesale
along with the `level()` validation block at `:549-561` and both `sreturn local _pending` /
`_unknown` lines. Running item 4 before the generator is fixed means writing it twice and, in
the interval, shipping a `dash.ado` with no reporter at either level.

**2. Items 1 and 2 have no such dependency and should go first.** They touch
`test/test_statistical_defaults.py`, `test/test_server_statistics.py` and one block in the
emitted loop. Item 2 is cleaner after Phases 05–08 (the server plot loop is exactly what the
`15-03` collapse rewrites), but the merge is three lines and is worth landing early rather than
leaving `lpolyci` at the wrong level through six phases. If it lands before Phase 05, flag it
in the phase-06 handover so the unification does not drop it.

**3. `fpfitci` has no confidence band in server mode at all.** REMAINING.md §4:

> | **`fpfitci`** | `VArea`(α .2) + `Line` | `Line` only | **the confidence band is missing in server mode** |

So item 1's `fpfitci` case is standalone-only until the `15-03` phases restore the band. Write
the server-side `fpfitci` level assertion, mark it `xfail` against that named item rather than
omitting it, and let it turn green when Phase 07 lands.

**4. Four faceted statistical defects are adjacent and are *not* this phase's.** Appendix C's
`15-03` list records that faceted `kdensity`/`lowess` call their compute helpers with the
options argument omitted (`dash_render.py:15170`, `:15175`, `:15271`, `:15276`), that faceted
`lpolyci`/`fpfitci` collapse into their band-less siblings (`:15179`, `:15186`, twins at
`:15280`, `:15287`), that faceted aggregate registrations omit the `'opts'` key so options are
lost after the first filter interaction (`:15156`-`:15189`, consumer at `:15609-15630`), and
that server `fpfit`/`fpfitci` still use the 200-point 1st–99th-percentile linspace at `:13502`
although `_fp_grid` is copied in at `:12395`. Every one of these will *look* like an S07 option
bug when a reviewer tests `by(foreign)`. Do not fix them here — they belong to Phases 06–08 —
but note them in any bug report, and do not write a Phase 19 test whose only failure mode is
one of them.

**5. The (a)/(b) decision from §2 sizes item 3 and must be taken before it starts.** §2 states
the choice is the user's, the suggested order says "Decide (a) or (b) from §2 first — that
decision sizes everything after it", and the (b) shortlist contains no S07 option. Until the
decision is recorded, item 3 is ambiguous between "implement thirteen estimation options" and
"formally decline thirteen estimation options" — a large difference in effort and none at all
in the test *shape*, which is why every E19.3 test above is written as a disjunction.

**6. Abbreviation collisions are a real failure mode for the thirteen.** Appendix B's `05-04`
entry warns that `resolve_minimums()` "asserts on ambiguity, so adding these names with real
measured minimums may trip that assert and force longer minimums than existing dash do-files
use", and Appendix C shows one collision has already bitten (`bw` hijacked from `bwidth` to
`barwidth`, leaving kdensity/lowess/lpoly at the default bandwidth with no note). `area`,
`adjust`, `atobs` and `estcmd`/`estopts` are the names most likely to collide with existing
declarations. Measure with `scripts/extract_abbrev_truth.do`; do not guess.

**7. Sub-option pass-through is an input surface, not a formatting convenience.**
`estopts()`, `estcmd()` and `predopts()` carry arbitrary Stata text into the renderer. Project
rule 16 requires every data input to be hardened against injection and confirmed UTF-8 before
it crosses into the backend, and `dash.sthlp:1137-1140` currently documents the whole
`ciopts()`/`lineopts()`/`fitopts()` family as accepted-and-unread. Whatever this phase does
with `estopts` must keep the "unread" safety property or replace it with an explicit allow-list
of estimation keywords — never a pass-through to an evaluator.

**8. Do not regress the note.** `dash.sthlp` states that the unsupported list and the note "are
generated from the same declarations in `dash.ado`, and `test/test_help_conformance.py` fails
if they disagree in either direction". Every option this phase moves — in either direction —
touches both. Land the help edit in the same commit as the `_dash_pending` edit, or the suite
goes red for a reason that has nothing to do with the statistics.
