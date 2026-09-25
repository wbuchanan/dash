# UltraPlan Discovery — `dash` as a true drop-in replacement for `twoway`

## Project Idea

Close every remaining gap between what `dash` **advertises** and what `dash` **does**, and
replace every hardcoded value that should instead be derived from user input, from the data,
or from the combination of the two — so that the package's central claim holds:

> "a new command intended to serve as a near drop-in replacement for twoway ... Just replace
> twoway with dash and you can be on your way."
> — submitted 2026 Stata Conference abstract

This is not a greenfield project. `dash` is ~14,000 lines across five source files with 122
commits of history, a 51-entry `BUGS.md` in which every entry is closed, and a passing
certification suite. The work here is **parity and de-hardcoding**, not construction.

---

## Codebase Context

### Source inventory (verified at HEAD `3948ce8`, 2026-05-01)

| File | Lines | Role |
|---|---|---|
| `dash.ado` | 1,649 | Subcommand routing; all option parsing via Stata `syntax`; JSON assembly by string concatenation |
| `dash_parse.mata` | 1,033 | Two-pass tokenizer for `()` / `\|\|` plot specs; **fixed** option-abbreviation lookup table |
| `dash_render.py` | 10,455 | `DashRenderer`, `GlyphMapper`, `OptionTranslator`, `SchemeParser`, `ServerAppBuilder` |
| `dash.sthlp` | 744 | SMCL help — the advertised surface |
| `dash_setup.ado` | 158 | Dependency installer/verifier |
| `schemes/*.scheme` | 5 files | Hand-written approximations of s2color, s1color, s1mono, economist, sj |
| `test/` | 45 files | pytest suites + Stata `.cscript` / `.do` certification scripts |
| `examples/` | 9 do-files | Demos against `auto.dta` and `kelly22ex` |

**Pipeline:** twoway-like syntax -> Mata tokenizer -> Stata `syntax` parse -> JSON IR ->
`jsonio` for the data -> Python `GlyphMapper`/`OptionTranslator` -> Bokeh models + generated
CustomJS -> standalone HTML *or* a generated Bokeh Server app.

### Verified environment (probed live, 2026-09-18)

| Fact | Value | Why it matters |
|---|---|---|
| Stata | StataNow 19.5, batch mode works | Certification scripts are runnable in this plan |
| `c(scheme)` | **`stcolor`** | The Stata 18+ default. `dash` ships no `stcolor` and never consults `c(scheme)`. |
| `c(level)` | `95` | The canonical source for CI level on `lfitci`/`qfitci`/`lpolyci`/`fpfitci` |
| Stata's scheme library | **26** files in `/Applications/Stata/ado/base/s/` | `dash` bundles 5 approximations instead |
| Real `scheme-s2color.scheme` | **2,588 lines** | `dash`'s approximation is ~100 lines, "only properties that have a Bokeh equivalent" |
| `sysuse sp500` `date` format | `%td` | The canonical date test fixture |
| Python | 3.14.5 | |
| bokeh / pandas / numpy | 3.9.0 / 3.0.1 / 2.4.3 | pandas 3.x — watch for API drift in `_load_data` |
| scipy | 1.17.1 — importable | `lfitci`, `qfitci`, `kdensity`, `mspline` OK |
| statsmodels | **BROKEN** (`ModuleNotFoundError: packaging`) | `lowess` is the only consumer; see baseline below |

### Baseline test state (measured, not assumed)

```
python3 -m pytest test/ -q   ->   1,480 passed, 14 failed
```

All 14 failures are `lowess` tests failing on the broken `statsmodels` import, not on `dash`
logic. This is itself a finding: `dash_setup.ado` declares `statsmodels>=0.13` a hard
dependency and `dash.pkg` lists it, but only `map_lowess` imports it (`dash_render.py:2547`),
and nothing verifies it at run time before a `lowess` plot is attempted — contrary to
project rule 15 (verify environment on start-up).

---

## Prior art consumed

`/Users/billy/Desktop/Programs/JavaScript/stataConference2026/.ultraplan/` contains a
completed 6-phase plan for the 2026 conference talk. Its **`DASH_AUDIT.md` (58 KB)** is a
line-cited audit of `dash` verified against this same HEAD, and its sections 02-09 already
specify fixes for:

- date support (sections 02-04): `formats` map from Stata, epoch conversion, datetime axes,
  date-aware hover/filters/facets/KPIs
- seven silent failures (05): `link(_all)`, `layout(name:r,c)`, `falpha()`, graph-level
  `scheme()`, standalone `update(brush)`, `p25`/`p75` in the JS recompute, `if`/`in` on
  `dash kpi`
- server mode (06), five correctness fixes (07), six ergonomics items (08), help
  reconciliation (09)

**This plan is a superset.** It adopts that work by reference and adds the three dimensions
the conference plan did not need, because its goal was a demo rather than parity:

1. **Systematic `twoway` surface parity** — every plottype and every option, not just the
   handful a demo would touch.
2. **The hardcoding inventory as a first-class deliverable** — figure sizing, the per-series
   style cycle, statistical defaults (bins, bandwidth, kernel, CI level, grid points), hover
   and tick formatting, and the Bootstrap CSS constants.
3. **The scheme pipeline** — `dash` reimplements Stata schemes as small approximations in its
   own directory instead of reading the user's installed schemes and honouring `set scheme`.

---

## Discovery Q&A

### Category 1 — Core Requirements

**Q1.1 What does "drop-in replacement" have to mean operationally?**
Sourced from the abstract and `dash.sthlp`. Three tiers, in priority order:
1. **No aborts.** A `twoway` command that works must not fail with `r(198)` when `twoway` is
   replaced by `dash`. Today a large class of options is rejected outright.
2. **No silent wrongness.** Where `dash` accepts an option it must honour it, or say why not.
   Today a second class is accepted and discarded without a word.
3. **Visual fidelity.** Defaults should come from the user's active scheme and from the data,
   not from literals in the renderer.

**Q1.2 What is explicitly out of scope?**
Anything that has no meaning in an interactive HTML target: `play()`, `nodraw`, `saving()` of
a `.gph`, printer/PostScript options, `graph export` formats, `graph combine` semantics
beyond what `layout()` already provides. These should be **accepted and documented as
ignored**, never rejected — accepting-and-ignoring preserves tier 1.

**Q1.3 Minimum viable version?**
Tier 1 plus tier 2 for every option `dash.sthlp` currently documents. Tier 3 is the scheme
work, which is separable and larger.

### Category 2 — Users & Context

**Q2.1 Who uses this?** Stata users who already know `twoway`. They will paste existing
do-file syntax. They will not read the help first — the abstract explicitly promises they
don't have to.

**Q2.2 What is their failure experience today?** Two shapes. `r(198) option bin() not
allowed` stops a do-file dead, which is loud and diagnosable. A silently-dropped `fa(0.4)`
or a silently-unlinked `link(_all)` is neither, and is the more damaging of the two.

**Q2.3 Environment?** Local Stata 17+ on macOS/Windows/Linux with Python and Bokeh >= 3.0,
`jsonio` from SSC. Output is opened in whatever browser the OS hands back.

### Category 3 — Integration Points

- **`jsonio`** carries the data and four metadata classes (`varnames varlabels vallabs
  labelnames`). It has no option to emit **display formats**, which is the root cause of the
  total absence of date handling. The fix is to carry formats in `dash`'s own master JSON —
  `jsonio` is not modified.
- **Stata's scheme library** — currently not integrated at all. `SchemeParser` reads only
  `dash`'s own `schemes/` directory, resolved as a sibling of `dash_render.py`.
- **Bokeh >= 3.0** — `TabPanel` makes 3.x a hard floor.
- **Bootstrap** — injected for `layout(bs)`.

### Category 4 — Edge Cases

Carried forward from the prior audit and to be re-verified by this plan's research phase:
all-missing columns, string columns in numeric widgets, zero-column layouts, the `__all__`
sentinel collision, facet/qualifier propagation through filter callbacks, minimum-N guards on
every fitted layer, Stata's date range exceeding pandas' nanosecond range, and `filter()`
combined with `by()` masking the wrong rows.

### Category 5 — Quality Attributes

Governed by the project's own 21 rules. The binding ones here: every function unit-tested
(4); a regression test written **before** the fix for every defect (8); adversarial tests per
input (18); no hardcoded secrets (13); environment verified at start-up (15); never commit to
`main` (6); no AI-tooling references in commit messages (7).

### Category 6 — Existing Patterns

- Option parsing is Stata `syntax`, never hand-rolled — Mata only splits segments and expands
  abbreviation keys.
- JSON is assembled by string concatenation in `dash.ado` and escaped through `_dash_json_str`.
- Python-side failures degrade to an empty glyph rather than raising; several sites warn via
  `warnings.warn`, many do not.
- Commit style is one focused single-issue commit per fix, message in the imperative.
- Tests are split: pytest for Python units, `.cscript` for Stata end-to-end certification.

### Category 7 — Preferences & Tradeoffs

**Backward compatibility is required in both directions.** An older `dash.ado` must keep
working against a newer `dash_render.py` (the `formats` key will simply be absent), and no
existing dashboard may change its rendering except where the change is the fix.

**Accept-and-warn beats reject.** For anything with no HTML analogue, the preferred
resolution is to accept the option and emit a note, because rejecting breaks tier 1.

### Category 8 — Monetization

Not applicable. `dash` is a free Stata package distributed by `net install`.

### Category 9 — Visual & UX Vision

The target is: a user's existing `twoway` command produces a dashboard that looks like the
graph they would have got from `twoway`, in their own scheme, with the same fonts, colors,
series cycle, and proportions — and then adds interactivity on top.

---

## Discovery Summary

- Source: the two repositories, a live Stata probe, a measured test baseline, and the prior
  `DASH_AUDIT.md`. The user's brief was precise and self-contained, so discovery was
  conducted against artifacts rather than by interview.
- Categories covered: 9 of 9 (category 8 is N/A by the nature of the project).
- Key themes:
  1. Three distinct failure classes — rejected options, accepted-and-ignored options, and
     hardcoded values that should be derived.
  2. The scheme pipeline is the largest single source of hardcoded visual defaults.
  3. Statistical defaults (bins, bandwidth, kernel, CI level, evaluation grids) are baked in
     where Stata derives them from the data or from `c(level)`.
  4. Server mode and standalone mode implement overlapping behaviour twice and have drifted.
  5. The documentation and the code disagree in both directions.
