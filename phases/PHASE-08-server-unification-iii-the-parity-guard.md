# Phase 08 — Server unification III — the parity guard

**Purpose.** Phases 05–07 collapse the server renderer's hand-written drawing code
into the shared `GlyphMapper`. This phase is the instrument that proves it happened
and stops it un-happening. Today the standalone/server parity guard
(`test/test_mode_parity.py`) covers 17 of 36 plot types, never constructs a spec with
`by()`, KPIs, `filter()`, `link()` or `tabs()`, and has no assertion at all for the two
properties ultraplan task 15-03 was accepted against — that the generated app carries
no glyph dispatch table of its own, and that it is self-contained. Five plot types have
already drifted under that blind spot, two of them drawing **nothing** in server mode.
Phase 08 widens the corpus to every type and to the four structural paths, adds the
three missing acceptance assertions (no dispatch table, self-contained, packaged-install
build), fixes the two divergences the widened corpus will immediately catch inside the
*delegated* surface (`mlabel()` and the `kdensity` grid), and closes the five measured
drifts. When this phase lands, the sentence "a behaviour is implemented once" is
enforced by a test rather than asserted in a changelog.

---

## At a glance

| | |
|---|---|
| **Work items** | 9 (numbered 1–9 below, exactly as handed over) |
| **Functional vs deliverable** | 3 functional · 6 deliverable |
| **Effort mix** | 6 small · 3 medium · 0 large |
| **Renderers touched** | 7 server-only (`ServerAppBuilder` and its emitted app) · 2 both (`DashRenderer` + `ServerAppBuilder`) |
| **Ultraplan discharged** | task **15-03** — its `<verify>` clause ("the generated app contains no dispatch table of its own") and its packaged-install clause; section **S15** — the guard tasks 15-01 and 15-04 promised |
| **Depends on** | Phase 05 (main-loop delegation), Phase 06 (facet-loop unification), Phase 07 (the twenty blank types + data comparison in the guard) |
| **Unblocks** | Phases 10, 13, 16 and 27 — every later server port is verified by this guard · Phase 31, gate 4 ("parity corpus") |
| **Primary files** | `dash_render.py`; `test/test_mode_parity.py`; `test/test_packaging.py`; `test/test_server_build_options.py`; `test/test_server_build.cscript`; new `test/test_server_dispatch.py` |

---

## Why this phase exists

All evidence in this section is copied from `REMAINING.md`. Line numbers there are
current against `dash_render.py` at ~16,000 lines; line numbers in the ultraplan's own
section files are stale and are not used here.

### The guard is narrower than it reads

From `REMAINING.md` §4, *"S15 — the parity guard covers less than half the surface, and
five layers have already drifted"*:

> **The collapse is 1/46 done.** `ServerAppBuilder` holds **51 `ptype ==`
> comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`)
> delegates to `_DASH_MAPPER`. 39 `map_*` methods exist.
>
> **The guard is narrower than it reads.** The parity corpus is 32 cases over
> **17 distinct plot types**, against **36 server `ptype` branches** — so
> **19 types are unguarded** (`fpfit` `fpfitci` `function` `lfitci` `lowess`
> `pcbarrow` `pci` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rconnected`
> `rline` `rscatter` `rspike` `tsline` `tsrline`). It also never constructs a
> spec with `by()`, KPIs, `filter()`, `link()` or `tabs()` — grep for each of
> those keys in the corpus returns 0.

Confirmed at HEAD while writing this document: `grep -c "ptype ==" dash_render.py`
→ **51**; the single delegating branch is `_DASH_MAPPER.map_scatter` at
`dash_render.py:14090`. The corpus at `test/test_mode_parity.py:187-284` is 32 tuples
covering `scatter`, `line`, `area`, `bar`, `histogram`, `kdensity`, `mband`,
`dropline`, `spike`, `connected`, `lfit`, `lpoly`, `lpolyci`, `dot`, `rcapsym`,
`scatteri`, `mspline` — 17 types. Its own inline comment admits the shape of the hole:

```python
    # Every entry above is a scatter, which is how seven glyph types and
    # every annotation drifted without this file noticing.
```

### Five of the nineteen have already drifted

Also from `REMAINING.md` §4 — measured at HEAD by building both renderers' figures from
the same spec and diffing every glyph property, with spec shapes taken from `dash.ado`'s
own emission (`yvar1`/`yvar2` for range plots, `expr` for `function`, `points` for
`pci`):

| type | standalone | server | consequence |
|---|---|---|---|
| **`fpfitci`** | `VArea`(α .2) + `Line` | `Line` only | **the confidence band is missing in server mode** |
| **`function`** | `Line` | *nothing* | **server-mode `function` draws no layer** |
| **`pci`** | `Segment` | *nothing* | **server-mode `pci` draws no layer** |
| `lowess` | `#1f77b4`, width 1 | `#1a476f`, width 1.5 | **standalone `lowess` ignores the scheme** (matplotlib's default blue) |
| `rscatter` | marker size 8.0 | marker size 6 | two default size tables |

> `test_conformance.cscript`'s "every layer drew something" assertion runs in
> **standalone mode only**, which is precisely why the two server-mode layers
> that draw nothing are invisible to it.
>
> These five are new defects, not plan items. Under project rule 8 each needs a
> regression test that fails first — the natural home is widening the parity
> corpus to all 36 types, which closes the class rather than the instances.

Note the `lowess` row: the drift runs the *other* way. This is the one place where the
standalone renderer is the wrong one, and a corpus entry that simply asserts "both agree"
would be satisfiable by breaking the server. The requirement is that both equal the
**scheme**, not merely each other.

### What 15-03 actually delivered, and what it did not

From `REMAINING.md` Appendix A, *15-03 — Collapse the glyph dispatch tables to one ·
PARTIAL*:

> **What landed:** the emitted app carries `GlyphMapper`, `OptionTranslator` and
> `SchemeParser` copied verbatim, and **the scheme is wired through**. The task's
> stated symptom is gone: `grep "scheme"` over the emitted region returned zero
> hits when the task was written and returns **44** now, and `#1f77b4` — the
> uniform colour the task complained of — occurs **0** times.

The task's `<verify>` clause, from `.ultraplan/sections/section-15-unification.md`,
reads: *"The parity test passes except for documented capability differences; the
generated app contains no dispatch table of its own."* The second half is asserted
nowhere. Section 15's own TDD stub list contains the line *"Test: the generated app
contains no glyph dispatch table of its own."* — also absent.

The count that assertion has to drive down, from `REMAINING.md` Appendix C:

> the count of hand-written server dispatch chains is 4 (36 + 16 + 16 + 14 = 82
> branches), not 3

— the main `ptype` loop (36), the `by()` facet chain (16), the `by(total)` twin (16),
and the live-recompute `atype` chain (14). Phases 05–07 remove the first three; Phase 05
item 5 removes the fourth. Phase 08 is what notices if any of them comes back.

### The self-containment promise nobody tests

`REMAINING.md` Appendix B, 15-03:

> **[deli · server · S]** Add a test that the generated app is self-contained
> — imports nothing from dash_render and executes with the package absent from
> sys.path. This property replaced the task's 'the app must import
> dash_render' clause and is asserted nowhere, while dash.sthlp and the
> CHANGELOG both promise it.

Both promises confirmed at HEAD: `dash.sthlp:292` ("write a self-contained Bokeh Server
`.py` app"), `dash.sthlp:549` ("`dash build, saving(app.py) server` writes a
self-contained server app"), and `.ultraplan/CHANGELOG.md:1175` ("…`inspect.getsource`,
and stays self-contained: the scheme arrives as a …").

### The packaged install degrades server mode too

`REMAINING.md` §1 reproduced the packaging defect end to end with Stata:

```
net set ado "<clean dir>"
net install dash, from("<repo>")     -> rc 0, "installation complete."
```

| manifest line | where Stata actually puts it |
|---|---|
| `f dash.ado` | `<dir>/d/dash.ado` |
| `f dash_render.py` | `<dir>/py/dash_render.py` |
| `f schemes/s1color.scheme` | `<dir>/s/s1color.scheme` |
| `f schemes/economist.scheme` | `<dir>/e/economist.scheme` |

`SchemeParser` searches exactly two places, both relative to `dash_render.py`
(`dash_render.py:1524-1532`):

```python
_SCHEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")
_SCHEME_SEARCH_DIRS = (_SCHEMES_DIR, os.path.dirname(os.path.abspath(__file__)))
```

Phase 03 widens that search. What is *this* phase's business is that
`ServerAppBuilder` resolves the scheme at **build** time, so the same defect silently
degrades `dash serve` — and nothing tests it (Appendix B, 15-03):

> The task's packaged-install clause is still open in its superseded form:
> `ServerAppBuilder.__init__` resolves the scheme at BUILD time through
> `SchemeParser.resolve_or_fallback`, so the S02/S03 net-install layout defect
> (dash_render.py lands in `<dir>/py/`, schemes in `<dir>/s/`) silently degrades
> server mode to built-in defaults too. No cscript builds a server app with a
> scheme from a net-installed copy.

The code at `dash_render.py:12310-12312`, confirmed at HEAD:

```python
        self.scheme: SchemeParser = SchemeParser.resolve_or_fallback(
            _resolve_scheme_name(self.spec), "the dashboard",
        )
```

### The copied-callee guard does not look at what 15-03 copied

`REMAINING.md` Appendix C, 15-03:

> The copied-callee guard does not cover the classes 15-03 copied.
> `TestTheCopiedHelpersBringTheirCallees.test_every_global_a_copied_helper_calls_is_defined`
> (test/test_mode_parity.py:436) filters `vars(mod)` with `isinstance(_obj,
> types.FunctionType)`, which matches module-level functions only — the 97
> methods of the copied `OptionTranslator`, `SchemeParser` and `GlyphMapper`
> are class attributes and are never scanned. Its companion
> `test_the_scan_found_the_copied_helpers` (:464) greps `_shared_stat_lines`
> for four names and never mentions `_glyph_layer_lines`. This is the exact
> failure mode the test exists for (`_stata_if_to_pandas` gaining
> `_mask_string_literals`, per its own docstring), now applying to a
> 5,000-line copied block that it does not look at.

That test's own docstring records three prior occurrences of exactly this bug
("`_stata_if_to_pandas` gained `_mask_string_literals` and the served page raised on
every qualifier", "`_resolve_seed` gained `_jitter_seed` and the served lpolyci band
raised on every session", and a body referencing `_LPOLY_ROT_C`). The unscanned block is
emitted at `dash_render.py:12406-12410`; confirmed at HEAD, `dash_render.py:12408`:

```python
        for _cls in (OptionTranslator, SchemeParser, GlyphMapper):
            out += _inspect.getsource(_cls).rstrip("\n").split("\n")
```

### `mlabel()` — the duplicated table TR-15.3 named, closed for scatter only

`REMAINING.md` Appendix C, 15-03:

> `mlabel()` diverges for every plot type except scatter in server mode. The
> emitted app carries a SECOND marker-label builder at dash_render.py:14894-14930
> with its own font-size map (`_mls_map2`, large=14px), its own offset map
> (`_mlabpos_map2`, position 9 = x_offset -10) and its own defaults (9px /
> #333333 / (5,5)), while `GlyphMapper._apply_mlabel_opts` (dash_render.py:3301)
> — which IS copied into the app and is what the delegated scatter branch uses —
> says 10px / #444444 / (4,0), large=15px, position 9 = x_offset -4. Worse, the
> block is gated on `_mlab_var in _cur_src.data` (dash_render.py:14904), which is
> false for `bar` and `spike`, so those draw no labels at all. `mlabgap()` is not
> read by the second copy either. This is precisely the duplicated size/offset
> table TR-15.3 asked to collapse and that `test_mode_parity._annotations`' own
> docstring warns about — closed for scatter only.

The corpus gap that lets it through: the only two `mlabel` entries in the corpus are
scatters, at `test/test_mode_parity.py:244` (`"scatter with marker labels"`) and `:271`
(`"scatter with marker labels and a size"`, `mlabsize(large)`). Both symbols confirmed
present at HEAD (`_mls_map2` at `dash_render.py:14910`, `_mlabpos_map2` at `:14915`, the
`_mlab_var in _cur_src.data` gate at `:14904`).

### `kdensity` — a divergence *inside* the guarded corpus

`REMAINING.md` Appendix C, 15-03:

> `kdensity` evaluates on a different grid in each mode: 300 points standalone,
> 200 served. `GlyphMapper.map_kdensity` defaults `n` to 300.0
> (dash_render.py:4806+, `n_pts = _stat_option_float(options, "n", 300.0, ...)`);
> the emitted `_compute_kdensity` hardcodes `n_pts = 200` (dash_render.py:13380).
> kdensity IS in the parity corpus and the guard is green, because the guard
> never compares data.

Confirmed at HEAD: `dash_render.py:4863` holds
`n_pts = _stat_option_float(options, "n", 300.0, "kdensity", lo=2.0,` and
`dash_render.py:13380` holds the emitted string literal `'        n_pts = 200'`.

This is the sharpest statement of why widening the corpus alone is not enough. The
neighbouring finding — **owned by Phase 07, item 5** — is that the guard compares no
data at all:

> `_glyph_profile` (test/test_mode_parity.py:129) reads only
> type/marker/size/fill_color/line_color/line_width/line_dash/fill_alpha;
> `_annotations` and `_chrome` add labels and background/grid colours.
> `data_source.data` is touched in exactly two places, both histogram bar counts
> (test/test_mode_parity.py:365, 382). … Consequence measured: kdensity (300 vs
> 200 points) and fpfit/fpfitci (10 vs 200) diverge inside the existing corpus and
> the file still reports 165 passed. Separately, `ALLOWED`
> (test/test_mode_parity.py:55) gates no comparison — its only assertions are that
> it is non-empty and that each reason is over 40 characters
> (test/test_mode_parity.py:388-392), so the 'explicit allowance' design is
> decorative.

Phase 08 widens *what* the guard builds; Phase 07 deepens *what it compares*. Neither is
sufficient alone, which is why Phase 08 sequences after Phase 07.

### Where this sits in the section audit

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 15 | Unification | 4 | **15-03 1/46; 5 live drifts** | 45 undelegated branches; corpus covers 17/36 types, no `by()`/KPI/filter/`link()`/`tabs()` |

S15 is 0 DONE / 4 PARTIAL / 0 NOT DONE in the final tally, and had no DONE claim left for
the adversarial pass to refute. The suite state the widened guard must stay green
against: **3,498 passed / 37 skipped; 25/25 cscripts**, of Phase 31's six gates the
first four passing today.

---

## Epics

| epic | goal | items |
|---|---|---|
| **8A — Prove the collapse happened** | The two properties 15-03 was accepted against become executable assertions, and the copied-block guard scans the block 15-03 actually copied. | 1, 2, 6 |
| **8B — The packaged install reaches server mode** | A server app built from a real net-installed copy keeps its scheme, and a source-less deployment fails with a dash-level message instead of a traceback. | 3, 7 |
| **8C — Widen the guard, then fix what it was not watching** | Every plot type and every structural path enters the parity corpus; the five measured drifts, the second `mlabel` builder and the `kdensity` grid are closed against it. | 4, 5, 8, 9 |

---

## User stories

### Epic 8A — Prove the collapse happened

> **As a package maintainer,** I want a test that fails the moment the generated app
> grows a glyph dispatch table of its own, so that the collapse Phases 05–07 perform
> cannot be quietly undone by the next server-side fix.

- **Given** `ServerAppBuilder.build()` output for any spec, **when** the test parses it
  and counts `if`/`elif` chains branching on `ptype`, **then** the count is 0 — and the
  same walk reports the `by()`, `by(total)` and `atype` chains separately so no chain can
  hide behind another's name.
- **Given** a developer who reintroduces one `elif ptype == 'lfit':` drawing branch,
  **when** the suite runs, **then** `test/test_server_dispatch.py` fails and names the
  branch.

> **As a `dash serve` operator,** I want the generated `.py` to run on a machine where
> `dash` is not installed, so that I can hand the file to a server that has Bokeh and
> nothing else.

- **Given** an app built by `dash build, saving(app.py) server`, **when** the emitted text
  is searched, **then** it contains no `dash_render` import.
- **Given** the same file, **when** it is executed with the repository removed from
  `sys.path`, **then** it imports and builds its document without raising.

> **As a package maintainer,** I want the copied-callee guard to scan the classes
> `_glyph_layer_lines` copies, so that the failure mode that has already shipped three
> times cannot ship a fourth time from a 5,000-line block the guard does not look at.

- **Given** the generated app module, **when** the guard walks every function *and every
  method of every class defined in it*, **then** every global those bodies load resolves
  in the module or in `builtins`.
- **Given** a copied `GlyphMapper` method that calls a module-level helper left behind,
  **when** the guard runs, **then** it fails naming the method and the missing global.

### Epic 8B — The packaged install reaches server mode

> **As a Stata user who installed `dash` with `net install`,** I want `dash serve` to use
> the scheme I asked for, so that the served dashboard looks like the standalone one.

- **Given** a clean `net install` of the package and `dash scatter mpg weight,
  scheme(economist)`, **when** `dash build, saving(app.py) server` runs, **then** no
  scheme-fallback warning is emitted and the app's embedded scheme properties are
  `economist`'s.
- **Given** the same install, **when** the cscript asserts on the emitted app text,
  **then** a named `economist` colour is present and the built-in default is not.

> **As a package maintainer,** I want a build on a deployment without `dash_render.py`'s
> source text to fail with a dash-level message, so that a byte-compiled or zipimported
> install reports a cause instead of a bare traceback.

- **Given** an install where `inspect.getsource` cannot read `dash_render.py`, **when**
  `ServerAppBuilder.build()` runs, **then** it raises a `dash:`-prefixed error naming
  source availability as the cause.
- **Given** a staged manifest-only install, **when** `ServerAppBuilder(...).build(path)`
  runs and the result is executed, **then** it succeeds — the same assertion
  `test_packaging.py` already makes for `DashRenderer` and `GlyphMapper`.

### Epic 8C — Widen the guard, then fix what it was not watching

> **As a Stata user pasting a `twoway` command,** I want every plot type to render the
> same in both modes, so that `dash build, server` is not a different product from
> `dash build`.

- **Given** any of the 21 currently unguarded plot types, **when** the parity corpus
  builds both modes from one spec, **then** glyph types, data and visual properties agree
  or an `ALLOWED` entry names the reason.
- **Given** `(function y = x^2)` or `(pci 20 3000 30 4000)`, **when** the server app is
  built, **then** it draws a layer — the "every layer drew something" assertion runs in
  **both** modes, not standalone only.
- **Given** `(fpfitci mpg weight)`, **when** both modes render, **then** both produce a
  `VArea` at alpha 0.2 plus a `Line`.
- **Given** `(lowess mpg weight)`, **when** both modes render, **then** both take colour
  and width from the **scheme** — not `#1f77b4` at width 1.

> **As a dashboard viewer,** I want marker labels to appear on bar and spike layers and
> to sit where they sit in the standalone file, so that a served dashboard is not missing
> annotations the HTML file shows.

- **Given** `(bar mpg weight, mlabel(make))`, **when** the app is served, **then** labels
  are drawn.
- **Given** `mlabsize(large)` on any type, **when** both modes render, **then** the label
  font size is one value (15px, `GlyphMapper._apply_mlabel_opts`), not 14px in one and
  15px in the other.
- **Given** `mlabposition(9)` and `mlabgap()`, **when** both modes render, **then** the
  offset is computed once, by `_apply_mlabel_opts`, and `mlabgap()` is honoured in both.

> **As a Stata user,** I want `kdensity` to evaluate on the same grid in both modes, so
> that a density curve is not smoother in one output than the other.

- **Given** `(kdensity mpg)` with no `n()`, **when** both modes render, **then** both
  evaluate on the same number of points from one shared default.
- **Given** `(kdensity mpg, n(120))`, **when** both modes render, **then** both produce
  120 points.

---

## Business requirements

Each is testable as written.

| id | requirement |
|---|---|
| **BR-8.1** | The generated server app contains no glyph dispatch table of its own. A test asserts this and fails if one returns. *(Discharges 15-03's `<verify>` clause and section 15's TDD stub "Test: the generated app contains no glyph dispatch table of its own.")* |
| **BR-8.2** | The generated server app is self-contained: it imports nothing from `dash_render` and executes with the `dash` package absent from `sys.path`. The claim at `dash.sthlp:292`, `dash.sthlp:549` and `.ultraplan/CHANGELOG.md:1175` becomes a tested property. |
| **BR-8.3** | Every global referenced by any copied function **or method** in the generated app resolves at import time. The guard covers the classes `_glyph_layer_lines` copies, not only the module-level functions `_shared_stat_lines` copies. |
| **BR-8.4** | A server app built from a real `net install`ed copy resolves the requested scheme. A cscript proves it; no scheme-fallback warning is emitted. |
| **BR-8.5** | A deployment where `dash_render.py`'s source text is unavailable fails the build with a dash-level message naming the cause, never a bare traceback. |
| **BR-8.6** | The parity corpus covers every plot type the server dispatches and every type `dash.ado` can emit, plus the `by()`, `by(total)`, KPI, `filter()`, `link()` and `tabs()` paths. |
| **BR-8.7** | Identical input produces identical output in both modes for `fpfitci`, `function`, `pci`, `lowess` and `rscatter`; `function` and `pci` draw a layer in server mode. *(BR-15.1 applied to the five measured drifts.)* |
| **BR-8.8** | `mlabel()` behaves identically in both modes for **every** plot type, including `bar` and `spike`, and `mlabsize()`, `mlabposition()` and `mlabgap()` resolve through one table. |
| **BR-8.9** | `kdensity` evaluates on the same grid in both modes, and `n()` is honoured in both. |
| **BR-8.10** | Every fix in this phase is preceded by a test that fails against HEAD and passes after (project rule 8), and every new helper has a unit test (project rule 4). |

---

## Technical requirements

### TR-8.1 — the no-dispatch-table assertion (item 1)

New file `test/test_server_dispatch.py` (or a class in `test/test_mode_parity.py`).

- Build an app with `dr.ServerAppBuilder(spec_path, data_path).build(app_path)` — the
  same construction `TestTheCopiedHelpersBringTheirCallees._app_module` already uses
  (`test/test_mode_parity.py:395-436`), so the helper can be lifted rather than rewritten.
- `ast.parse` the emitted text. Walk every `ast.If`; classify a node as a dispatch branch
  when its test is a `Compare`/`BoolOp` whose operands include a `Name` or `Subscript`
  resolving to `ptype` (`ptype == '...'`, `ptype in (...)`). Report per-chain counts.
- Assert **0** `ptype` branches. Report the other three chains by their own names so a
  regression cannot migrate: the `by()` facet chain (emitted at `dash_render.py:15137-15230`),
  the `by(total)` twin (`:15237-15330`) and the live-recompute `atype` chain (`:15604-15640`).
- Baseline to drive down, from `REMAINING.md`: **82 branches across 4 chains
  (36 + 16 + 16 + 14)**; `grep -c "ptype ==" dash_render.py` → **51** at HEAD; the single
  delegating branch is `_DASH_MAPPER.map_scatter` at `dash_render.py:14090`.
- Because Phases 05–07 land the collapse, the assertion ships as a **ratchet**: a recorded
  expected-count constant in the test file, lowered by each delegating commit, with the
  final form asserting 0. The ratchet must be strictly monotone — a test that accepts a
  count *higher* than recorded fails, so the guard is live from the first commit rather
  than from the last.

### TR-8.2 — the self-containment assertion (item 2)

In `test/test_server_build_options.py` or `test/test_packaging.py`.

- Text assertion: `"dash_render" not in emitted_source` — covering `import dash_render`,
  `from dash_render import …` and any `importlib` call naming it.
- Execution assertion: copy the emitted `.py` to a `tmp_path` outside the repo, remove the
  repository root and the `dash` package directory from `sys.path` (and from
  `sys.modules`), then `importlib` it. It must import and construct its document.
- Promises this closes: `dash.sthlp:292`, `dash.sthlp:549`, `.ultraplan/CHANGELOG.md:1175`.

### TR-8.3 — packaged-install server build (item 3)

- `ServerAppBuilder.__init__` resolves the scheme at BUILD time at
  `dash_render.py:12310-12312`:
  `self.scheme = SchemeParser.resolve_or_fallback(_resolve_scheme_name(self.spec), "the dashboard")`.
- `SchemeParser`'s search dirs are `dash_render.py:1524-1532` (`_SCHEMES_DIR`,
  `_SCHEME_SEARCH_DIRS`) — two paths relative to `dash_render.py`, neither of which exists
  under Stata's `<dir>/py/` + `<dir>/s/` letter layout. **Phase 03 owns the search-path
  widening**; this item owns the proof that server mode benefits.
- Add the packaged-install case to `test/test_server_build.cscript`: `net install` into a
  clean directory, `dash scatter mpg weight, name(g1) scheme(economist)`,
  `dash build, saving(app.py) server`, then assert (a) rc 0, (b) no scheme-fallback
  warning in the log, (c) a named `economist` property appears in `app.py`.
- The cscript must follow the project's skip rules: `capture which jsonio` and
  `c(python_exec)` probes as in the file's existing preamble — never probe Python by
  running it — and a skip is not a pass.

### TR-8.4 — collapse the second marker-label builder (item 4)

- Delete the emitted second builder at `dash_render.py:14894-14930`. Its tables, confirmed
  at HEAD: `_mls_map2` at `:14910` (`'tiny':'7px','vsmall':'8px','small':'9px','medsmall':'10px',…`,
  large = **14px**), `_mlabpos_map2` at `:14915` (position **9** → `x_offset -10`),
  defaults **9px / `#333333` / (5,5)**, `mlabgap()` unread.
- The single surviving implementation is `GlyphMapper._apply_mlabel_opts`
  (`dash_render.py:3301`), already copied into the app and already used by the delegated
  scatter branch: defaults **10px / `#444444` / (4,0)**, large = **15px**, position **9** →
  `x_offset -4`.
- Remove the gate at `dash_render.py:14904` (`if _cur_src and _mlab_var in _cur_src.data:`),
  which is false for `bar` and `spike` and is why those draw no labels at all. Labels must
  be built from whatever source the delegated branch produced, as `_apply_mlabel_opts` does.
- `mlabgap()` must reach `_apply_mlabel_opts` in server mode.
- Corpus consequence: `test/test_mode_parity.py:244` and `:271` are both scatters; the
  widened corpus (TR-8.8) must carry an `mlabel` entry on a **non-scatter** type, minimally
  `bar` and `spike`.

### TR-8.5 — one `kdensity` grid (item 5)

- Standalone: `GlyphMapper.map_kdensity`, `dash_render.py:4863` —
  `n_pts = _stat_option_float(options, "n", 300.0, "kdensity", lo=2.0, …)`.
- Server: emitted `_compute_kdensity`, `dash_render.py:13380` — the string literal
  `'        n_pts = 200'`.
- Resolve to one default in one place. The delegating fix is to route the server's
  kdensity through `GlyphMapper.map_kdensity` (Phase 05, item 1); if this phase lands
  first, the interim fix is for the emitted `_compute_kdensity` to read the same
  `_stat_option_float(options, "n", 300.0, …)` call rather than a literal — never a second
  literal set to 300.
- `n()` must be honoured in both. Note the neighbouring facet defect (Phase 06, item 8):
  the facet branches call `_compute_kdensity(_fac_gdf, _kdvar)` with `options` omitted, so
  `bwidth()`, `kernel()`, `n()` and `range()` are dropped under `by()`.

### TR-8.6 — the copied-callee guard covers the copied classes (item 6)

- `test/test_mode_parity.py:436-462` —
  `test_every_global_a_copied_helper_calls_is_defined` filters `vars(mod)` with
  `isinstance(_obj, types.FunctionType)`, so only module-level functions are walked. Extend
  the walk to `isinstance(_obj, type)` → every function-valued attribute in
  `vars(_cls)` (including `staticmethod`/`classmethod` `__func__`, properties' `fget`, and
  nested `ast`-reachable closures), then run the existing `dis`-based `LOAD_GLOBAL` /
  `LOAD_NAME` scan on each. The unscanned surface is **97 methods** of `OptionTranslator`,
  `SchemeParser` and `GlyphMapper`.
- `test/test_mode_parity.py:464-470` — `test_the_scan_found_the_copied_helpers` greps
  `_shared_stat_lines` for `_stata_if_to_pandas`, `_resolve_seed`, `_bootstrap_ci`,
  `_kpi_statistic` and never mentions `_glyph_layer_lines`. Extend it to grep
  `_glyph_layer_lines` for the three class names and for the module-level helpers that
  block copies. `REMAINING.md` records "three classes and 15 helpers"; the tuple at
  `dash_render.py:12386-12400` names 16 candidates — `_parse_textbox_opt`,
  `_optional_import`, `_extract_finite`, `_apply_jitter`, `_with_color_alias`,
  `_jitter_seed`, `_floats_only`, `_parse_stata_numeric_fmt`, `_format_stata_numeric`,
  `_format_date_value_standalone`, `_fp_grid`, `_fp_report_unsupported`, `_betacf`,
  `_betainc`, `_t_cdf`, `_t_ppf` — of which those already emitted by `_shared_stat_lines`
  are skipped by the `if _fn_name in _emitted_names: continue` guard. The test should read
  the tuple rather than hardcode a count, so adding a helper cannot silently drop it.
- The class copy loop the guard must know about is `dash_render.py:12406-12410`
  (`for _cls in (OptionTranslator, SchemeParser, GlyphMapper)`, confirmed at `:12408`).

### TR-8.7 — packaging coverage and the `inspect.getsource` dependency (item 7)

- `test/test_packaging.py` exercises `DashRenderer` at `:208`
  (`test_dashrenderer_constructs_from_packaged_install`) and `GlyphMapper` at `:238`
  (`test_glyphmapper_constructs_from_packaged_install`) from a staged install, and never
  `ServerAppBuilder`. Add a staged-install `ServerAppBuilder(...).build(path)` case beside
  them, and execute the result.
- There is **no `test_netinstall.cscript` in `test/`** at all — the Stata-level gap Phase 03
  fills; this phase's cscript case (TR-8.3) is the server half of it.
- `_glyph_layer_lines` calls `inspect.getsource` on three classes and the helper tuple at
  `dash_render.py:12386-12410` with no `try`/`except`. Wrap those calls so that
  `OSError`/`TypeError` (byte-compiled-only install, zipimport, a stripped copy) raises a
  `dash:`-prefixed error naming source availability, and add a unit test that forces the
  failure (monkeypatch `inspect.getsource` to raise) and asserts the message shape.

### TR-8.8 — widen the parity corpus (item 8)

- Corpus location: `test/test_mode_parity.py:187-284`, normalised at `:284` by
  `CORPUS = [(c + ({},))[:4] for c in CORPUS]` and consumed by the parametrized
  `TestTheTwoModesAgree` at `:289`. New entries are 3- or 4-tuples:
  `(name, plots, build_options, graph_options)`.
- **Today:** 32 cases, 17 distinct types — `scatter`, `line`, `area`, `bar`, `histogram`,
  `kdensity`, `mband`, `dropline`, `spike`, `connected`, `lfit`, `lpoly`, `lpolyci`, `dot`,
  `rcapsym`, `scatteri`, `mspline`.
- **Missing, per `REMAINING.md` §4 (19, against 36 server `ptype` branches):** `fpfit`
  `fpfitci` `function` `lfitci` `lowess` `pcbarrow` `pci` `pcspike` `qfit` `qfitci` `rarea`
  `rbar` `rcap` `rconnected` `rline` `rscatter` `rspike` `tsline` `tsrline`.
- **Missing, per Appendix B (21, against 38 user-facing types):** the same list plus
  `pcarrow` and `pcscatter`. The two denominators differ because §4 counts server dispatch
  branches and Appendix B counts user-facing types; the corpus must satisfy the **union** —
  21 new types.
- **Structural paths, all at zero occurrences today:** `by()`, `by(total)`, KPIs,
  `filter()`, `link()`, `tabs()`. Grep for each of those keys in the corpus returns 0.
- Spec shapes must be taken from `dash.ado`'s own emission, as `REMAINING.md` did:
  `yvar1`/`yvar2` for range plots, `expr` for `function`, `points`/`values` for `pci` and
  `scatteri` (note `dash.ado:1212` writes literal `pci` as `"values":[[y,x],…]`, guarded at
  `dash.ado:1655-1667`). A corpus entry with a spec shape `dash.ado` never emits proves
  nothing.
- An entry that cannot pass until an owning phase lands gets an `ALLOWED` entry naming
  the phase and the item, not a loose comparison or a bare `skip`. `ALLOWED`
  (`test/test_mode_parity.py:55`) currently gates nothing — its only assertions are
  non-emptiness and a >40-character reason at `:388-392` — so Phase 07's item 5, which makes
  `ALLOWED` gate the comparison, is a hard prerequisite for this item to mean anything.
- Runtime: the file reports **165 passed** today for 32 cases × ~5 assertions. Widening to
  ~38 types plus six structural paths roughly doubles the build count; build once per case
  and share the figures across the five assertions rather than rebuilding per assertion.

### TR-8.9 — close the five measured drifts (item 9)

| type | standalone at HEAD | server at HEAD | target |
|---|---|---|---|
| `fpfitci` | `VArea`(α .2) + `Line` | `Line` only | both: `VArea` α 0.2 + `Line`, one implementation (`GlyphMapper.map_fpfitci`) |
| `function` | `Line` | *nothing* | server draws the `Line`; `expr` is read as `dash.ado` emits it |
| `pci` | `Segment` | *nothing* | server draws the `Segment`, including the literal `values` shape (`GlyphMapper.map_pci` / `map_pci_literal`, `dash_render.py:5516`, `:5548`) |
| `lowess` | `#1f77b4`, width 1 | `#1a476f`, width 1.5 | **both take the scheme's colour and width** — the standalone side is the wrong one here |
| `rscatter` | marker size 8.0 | marker size 6 | one size table; the scheme's marker size (`REMAINING.md` records scheme 10.18 for the `rscatter`/`pcscatter` family) |

- Related Phase 05 item 3 covers 13 further main-loop divergences under a non-default
  scheme (`rarea` fill_alpha 1.0 vs 0.5, `rbar`'s white 1.2px outline vs line_alpha 0,
  `rcapsym` caps 1.2 vs 1.5, `rline`/`rconnected`/`tsrline` drawing series 2 in colour index
  0, `pcspike`/`pcarrow`/`pcbarrow` at 1.2 vs 1.5, `lowess` running `_compute_lowess`
  against standalone's statsmodels `map_lowess`). Where a drift in this item's five is the
  same defect as one of those thirteen, fix it once, in `GlyphMapper`, and let both phases'
  tests assert it.
- `test_conformance.cscript`'s "every layer drew something" assertion runs standalone-only.
  Extend it to run in both modes, or add the server pass in
  `test/test_server_build.cscript` — this is what would have caught `function` and `pci`
  drawing nothing.

---

## Work items

All nine items, numbered exactly as handed over. Tags are `[kind · renderer · effort]`.

---

**1. `[deliverable · server · small]` — the no-dispatch-table assertion** *(origin: task 15-03, Appendix B)*

> Add the assertion the task's `<verify>` names: that the generated app contains no glyph
> dispatch table of its own. Nothing in test/ counts or forbids ptype chains in the emitted
> source, so the collapse has no acceptance test.

*Where:* `test/test_mode_parity.py` (or a new `test/test_server_dispatch.py`); the check is
an ast walk of `ServerAppBuilder` output counting `if`/`elif` chains on `ptype`.

*Evidence:* 15-03's `<verify>` reads "the generated app contains no dispatch table of its
own"; section 15's TDD stubs include "Test: the generated app contains no glyph dispatch
table of its own." Neither exists. At HEAD, `grep -c "ptype ==" dash_render.py` → 51, and
`REMAINING.md` counts 4 chains / 82 branches (36 + 16 + 16 + 14). Epic 8A · TR-8.1.

---

**2. `[deliverable · server · small]` — the self-containment test** *(origin: task 15-03, Appendix B)*

> Add a test that the generated app is self-contained — imports nothing from dash_render
> and executes with the package absent from sys.path. This property replaced the task's
> 'the app must import dash_render' clause and is asserted nowhere, while dash.sthlp and
> the CHANGELOG both promise it.

*Where:* `test/test_server_build_options.py` or `test/test_packaging.py`; assert no
`dash_render` import in the emitted text and exec the app with `sys.path` stripped of the
repo.

*Evidence:* the promise appears at `dash.sthlp:292`, `dash.sthlp:549` and
`.ultraplan/CHANGELOG.md:1175`; no test asserts it. Epic 8A · TR-8.2.

---

**3. `[deliverable · server · small]` — the packaged-install server build** *(origin: task 15-03, Appendix B)*

> The task's packaged-install clause is still open in its superseded form:
> `ServerAppBuilder.__init__` resolves the scheme at BUILD time through
> `SchemeParser.resolve_or_fallback`, so the S02/S03 net-install layout defect
> (dash_render.py lands in `<dir>/py/`, schemes in `<dir>/s/`) silently degrades server
> mode to built-in defaults too. No cscript builds a server app with a scheme from a
> net-installed copy.

*Where:* `dash_render.py:12311` (`ServerAppBuilder.__init__` scheme resolution);
`SchemeParser` search dirs at `dash_render.py:1524-1532`; `test/test_server_build.cscript`
is the place to add the packaged-install case.

*Evidence:* the `net install` letter-directory table and the measured
`UserWarning: dash: scheme 's1color' was not found … using s2color` in §1 of
`REMAINING.md`; all 12 example do-files run rc 0 from the packaged install and all 12 emit
the fallback warning. Epic 8B · TR-8.3.

---

**4. `[functional · server · medium]` — the second marker-label builder** *(origin: task 15-03, Appendix C)*

> `mlabel()` diverges for every plot type except scatter in server mode. The emitted app
> carries a SECOND marker-label builder at dash_render.py:14894-14930 with its own
> font-size map (`_mls_map2`, large=14px), its own offset map (`_mlabpos_map2`, position 9 =
> x_offset -10) and its own defaults (9px / #333333 / (5,5)), while
> `GlyphMapper._apply_mlabel_opts` (dash_render.py:3301) — which IS copied into the app and
> is what the delegated scatter branch uses — says 10px / #444444 / (4,0), large=15px,
> position 9 = x_offset -4. Worse, the block is gated on `_mlab_var in _cur_src.data`
> (dash_render.py:14904), which is false for `bar` and `spike`, so those draw no labels at
> all. `mlabgap()` is not read by the second copy either. This is precisely the duplicated
> size/offset table TR-15.3 asked to collapse and that `test_mode_parity._annotations`' own
> docstring warns about — closed for scatter only.

*Where:* `dash_render.py:14894-14930` (the emitted second builder); target
`dash_render.py:3301 GlyphMapper._apply_mlabel_opts`; corpus gap at
`test/test_mode_parity.py:244,271`.

*Evidence:* symbols confirmed at HEAD — `_mls_map2` at `:14910`, `_mlabpos_map2` at `:14915`,
the data gate at `:14904`. Both corpus `mlabel` entries are scatters. Epic 8C · TR-8.4.

---

**5. `[functional · server · small]` — one `kdensity` grid** *(origin: task 15-03, Appendix C)*

> `kdensity` evaluates on a different grid in each mode: 300 points standalone, 200 served.
> `GlyphMapper.map_kdensity` defaults `n` to 300.0 (dash_render.py:4806+, `n_pts =
> _stat_option_float(options, "n", 300.0, ...)`); the emitted `_compute_kdensity` hardcodes
> `n_pts = 200` (dash_render.py:13380). kdensity IS in the parity corpus and the guard is
> green, because the guard never compares data (see the parity-corpus item below).

*Where:* `dash_render.py:13380` (emitted default) vs `dash_render.py:~4863` in
`GlyphMapper.map_kdensity`.

*Evidence:* confirmed at HEAD — `dash_render.py:4863` is the `_stat_option_float(… 300.0 …)`
call and `dash_render.py:13380` is the emitted literal `n_pts = 200`. Epic 8C · TR-8.5.

---

**6. `[deliverable · server · small]` — the copied-callee guard must scan the copied classes** *(origin: task 15-03, Appendix C)*

> The copied-callee guard does not cover the classes 15-03 copied.
> `TestTheCopiedHelpersBringTheirCallees.test_every_global_a_copied_helper_calls_is_defined`
> (test/test_mode_parity.py:436) filters `vars(mod)` with `isinstance(_obj,
> types.FunctionType)`, which matches module-level functions only — the 97 methods of the
> copied `OptionTranslator`, `SchemeParser` and `GlyphMapper` are class attributes and are
> never scanned. Its companion `test_the_scan_found_the_copied_helpers` (:464) greps
> `_shared_stat_lines` for four names and never mentions `_glyph_layer_lines`. This is the
> exact failure mode the test exists for (`_stata_if_to_pandas` gaining
> `_mask_string_literals`, per its own docstring), now applying to a 5,000-line copied block
> that it does not look at.

*Where:* `test/test_mode_parity.py:436-462` and `:464-470`; the unscanned block is emitted by
`dash_render.py:12406-12410` (`for _cls in (OptionTranslator, SchemeParser, GlyphMapper)`).

*Evidence:* the class copy loop confirmed at `dash_render.py:12408`; the test's docstring
records three prior shipped instances of this failure mode. Epic 8A · TR-8.6.

---

**7. `[deliverable · server · small]` — packaging coverage and the `inspect.getsource` dependency** *(origin: task 15-03, Appendix C)*

> The task's explicit clause 'test the packaged-install case against S02's cscript' is
> unmet, and the substitution introduced a new hard dependency with no guard.
> test/test_packaging.py exercises `DashRenderer` (:208) and `GlyphMapper` (:238) from a
> staged install but never `ServerAppBuilder`, and there is no test_netinstall.cscript in
> test/ at all. `_glyph_layer_lines` now calls `inspect.getsource` on three classes and 15
> helpers (dash_render.py:12386-12410) with no try/except, so any deployment where
> dash_render.py's source text is not on disk — byte-compiled-only install, zipimport, a
> stripped copy — fails the BUILD with a bare traceback rather than a dash-level message.

*Where:* `test/test_packaging.py` (add a staged-install `ServerAppBuilder.build` + exec case
alongside `:208`/`:238`); `dash_render.py:12386-12410` (`inspect.getsource` calls, no
fallback).

*Evidence:* `test_packaging.py:208` and `:238` confirmed as the `DashRenderer` and
`GlyphMapper` staged-install tests; no `test_netinstall.cscript` exists in `test/`. Epic 8B ·
TR-8.7.

---

**8. `[deliverable · both · medium]` — widen the parity corpus** *(origin: S15, main body §4)*

> Widen the parity corpus from 17 of 36 plot types to all of them, and add the four
> structural paths it never builds: `by()`, KPIs, `filter()`, `link()` and `tabs()`. Grep for
> each of those keys in the corpus returns 0.

*Where:* `test/test_mode_parity.py:CORPUS (:187-284)`.

*Evidence:* the 19 unguarded types listed in §4; Appendix B's parallel statement ("covers 17
of the 38 user-facing plot types … Missing types: fpfit, fpfitci, function, lfitci, lowess,
pcarrow, pcbarrow, pci, pcscatter, pcspike, qfit, qfitci, rarea, rbar, rcap, rconnected,
rline, rscatter, rspike, tsline, tsrline") — union of 21; the corpus comment at
`test/test_mode_parity.py:213-214` admitting "Every entry above is a scatter, which is how seven
glyph types and every annotation drifted without this file noticing." Epic 8C · TR-8.8.

---

**9. `[functional · both · medium]` — the five measured drifts** *(origin: S15, main body §4)*

> Fix the five measured standalone/server drifts: `fpfitci` loses its VArea confidence band
> in server mode; `function` and `pci` draw nothing in server mode; standalone `lowess` uses
> matplotlib's `#1f77b4` at width 1 instead of the scheme; `rscatter` uses marker size 8.0
> standalone against 6 in server.

*Where:* `dash_render.py`: the `fpfitci`/`function`/`pci`/`lowess`/`rscatter` branches in both
renderers.

*Evidence:* the measured drift table in §4, reproduced in full under "Why this phase exists".
These are new defects, not plan items, so project rule 8 applies to each. Epic 8C · TR-8.9.

---

## Test plan

Project rule 8 governs items 4, 5 and 9 (bug fixes): a regression test that **fails before
the fix and passes after**. Project rule 4 governs every new helper. For the tests most at
risk of certifying nothing, the mutation that must kill them is named — this repository has a
documented history of tests that passed against broken implementations, and a test that has
not been shown to fail has not been shown to work.

### Epic 8A — Prove the collapse happened

**Failing test first**

| test | file | fails at HEAD because |
|---|---|---|
| `test_the_generated_app_has_no_ptype_dispatch` | `test/test_server_dispatch.py` (new) | 36 `ptype` branches in the emitted main loop; 51 `ptype ==` comparisons in `dash_render.py` |
| `test_the_generated_app_imports_nothing_from_dash_render` | `test/test_server_build_options.py` | asserted nowhere today; must be written before any refactor that could break it |
| `test_every_global_a_copied_METHOD_calls_is_defined` | `test/test_mode_parity.py` | the existing scan skips 97 methods of the three copied classes |

**Unit tests (rule 4)**

- The ast classifier itself: a unit test feeding it a hand-written snippet with a known
  number of `ptype` chains and asserting the count. A counter with no test is a counter that
  can return 0 by accident.
- The class-walking helper in TR-8.6: a unit test over a fixture module containing a class
  with a `staticmethod`, a `classmethod` and a property, asserting all four function objects
  are visited.
- `test_the_scan_found_the_copied_helpers` extended to read the helper tuple from
  `_glyph_layer_lines` rather than hardcode names, with a unit test that adding a name to
  the tuple extends the scan.

**Integration / cscript coverage**

- `test/test_server_build.cscript` — the app builds and the command *returns* (the file's
  existing rationale: "if it launched, this script would hang and the runner would never
  reach the summary").
- `test/test_e2e_serve.cscript` — unchanged behaviour after the guard lands.

**Mutation — what to break so the test dies**

| test | mutation | expected |
|---|---|---|
| no-dispatch assertion | reinstate one `elif ptype == 'lfit':` drawing branch in the emitted source | fails, naming `lfit` |
| no-dispatch assertion | change the classifier to count only `Compare` nodes with a literal string right-hand side | the unit test over the fixture snippet fails (the `ptype in (...)` form must be counted) |
| self-containment | add `import dash_render  # noqa` to the emitted preamble | text assertion fails |
| self-containment | leave the import out but have a copied body call `dash_render.something` | exec-with-stripped-`sys.path` assertion fails |
| callee scan | delete `_with_color_alias` from `_glyph_layer_lines`' helper tuple while a copied `GlyphMapper` method still calls it | fails, naming the method and the missing global |
| callee scan | remove one class from the copy loop at `dash_render.py:12408` | `test_the_scan_found_the_copied_helpers` fails |

### Epic 8B — The packaged install reaches server mode

**Failing test first**

| test | file | fails at HEAD because |
|---|---|---|
| `test_serverappbuilder_builds_from_packaged_install` | `test/test_packaging.py` (beside `:208`, `:238`) | `ServerAppBuilder` is never exercised from a staged install |
| `test_build_reports_a_dash_error_when_source_is_unavailable` | `test/test_packaging.py` | `inspect.getsource` at `dash_render.py:12386-12410` has no `try`/`except` |
| the packaged-install server case | `test/test_server_build.cscript` | no cscript builds a server app with a scheme from a net-installed copy |

**Unit tests (rule 4)**

- The new `inspect.getsource` wrapper: one test per raised type (`OSError`, `TypeError`)
  asserting the `dash:`-prefixed message and that the original exception is chained.
- Scheme resolution at build time: a unit test that `ServerAppBuilder(...).scheme` is the
  requested scheme (not the fallback) when the scheme file is reachable, paired with one
  asserting the warning text when it is not.

**Integration / cscript coverage**

- `test/test_server_build.cscript` gains the `net install` → `scheme(economist)` →
  `dash build, saving(app.py) server` case, asserting rc 0, no fallback warning, and an
  `economist` colour present in the emitted file.
- The skip discipline the suite already uses applies: `capture which jsonio` and
  `c(python_exec)` probes only; a skip is **not** a pass, and the runner's skip accounting
  must show the case either ran or was skipped for a named reason.

**Mutation — what to break so the test dies**

| test | mutation | expected |
|---|---|---|
| packaged-install cscript | point `_SCHEME_SEARCH_DIRS` back at the two-path form while the install uses Stata's letter layout | cscript fails on the fallback warning |
| packaged-install cscript | assert only rc 0 | the mutation above passes — proving the rc-only form is vacuous; the scheme assertion is the load-bearing one |
| getsource wrapper | monkeypatch `inspect.getsource` to raise `OSError` | build raises the dash-level message, not a bare traceback |
| staged-install builder test | stage the install without `schemes/` | the test must still build (fallback is legal) but the cscript must warn — the two assertions are deliberately different |

### Epic 8C — Widen the guard, then fix what it was not watching

**Failing test first (rule 8, one per measured defect)**

| test | file | fails at HEAD because |
|---|---|---|
| corpus entry `"fpfitci"` | `test/test_mode_parity.py` | server draws `Line` only; standalone draws `VArea`(α .2) + `Line` |
| corpus entry `"function"` | `test/test_mode_parity.py` | server draws nothing — caught by `test_the_profile_is_not_empty` (`:328`) |
| corpus entry `"pci"` (both the var form and the literal `values` form) | `test/test_mode_parity.py` | server draws nothing |
| corpus entry `"lowess, economist"` | `test/test_mode_parity.py` | standalone uses `#1f77b4` width 1 against the scheme's `#1a476f` width 1.5 |
| corpus entry `"rscatter"` | `test/test_mode_parity.py` | marker size 8.0 vs 6 |
| corpus entry `"bar with marker labels"` and `"spike with marker labels"` | `test/test_mode_parity.py` | the `_mlab_var in _cur_src.data` gate at `dash_render.py:14904` means no labels are drawn at all in server mode |
| corpus entry `"scatter, mlabsize(large)"` compared by size | `test/test_mode_parity.py` | 14px (`_mls_map2`) vs 15px (`_apply_mlabel_opts`) |
| `test_kdensity_grid_agrees` | `test/test_mode_parity.py` | 300 points standalone, 200 served |
| `test_kdensity_n_option_is_honoured_in_both_modes` | `test/test_server_statistics.py` | the emitted literal ignores `n()` |

**Unit tests (rule 4)**

- `GlyphMapper._apply_mlabel_opts` — one test per resolved property: default size 10px,
  `mlabsize(large)` → 15px, default colour `#444444`, default offset `(4, 0)`,
  `mlabposition(9)` → `x_offset -4`, and `mlabgap()` applied. These are the values the second
  builder must be deleted *in favour of*, so each needs an assertion of its own.
- The shared kdensity grid default: a unit test asserting the default is read from one
  symbol, and one asserting `n(120)` produces 120 points.
- The `fpfitci`, `function`, `pci`, `lowess` and `rscatter` mappers: a unit test each
  asserting the glyph set (`VArea` + `Line`, `Line`, `Segment`, scheme colour/width, scheme
  marker size) independent of the parity comparison, so a mapper bug is distinguishable from
  a corpus bug.

**Integration / cscript coverage**

- `test/test_conformance.cscript` — extend the "every layer drew something" assertion to run
  in **server** mode as well as standalone. This is the assertion that would have caught
  `function` and `pci`, and it is the Stata-level twin of the corpus entries above.
- `test/test_server_build.cscript` — one build per structural path (`by()`, KPI, `filter()`,
  `link()`, `tabs()`) asserting rc 0 and a non-empty document, complementing the pytest-level
  parity comparison.
- `test/test_server_scheme.py` — the `lowess` fix must not regress the scheme wiring this
  file guards.

**Mutation — what to break so the test dies**

| test | mutation | expected |
|---|---|---|
| `"fpfitci"` corpus entry | drop the `VArea` from `GlyphMapper.map_fpfitci` | parity fails naming `fpfitci` and `VArea` |
| `"function"` / `"pci"` entries | make the mapper return an empty renderer list | `test_the_profile_is_not_empty` fails — if it does not, the entry's spec shape is wrong and reaches no branch |
| `"lowess"` entry | set the standalone colour back to `#1f77b4` | parity fails **and** the scheme unit test fails; an entry that only compares the two modes to each other would pass, which is why the scheme assertion is separate |
| `mlabel` on `bar` | restore the `_mlab_var in _cur_src.data` gate | the `bar`/`spike` label entries fail |
| `mlabsize` comparison | set `_apply_mlabel_opts`' large to 14px | the size unit test fails, proving the comparison reads the size rather than mere label presence |
| kdensity grid | set the shared default to 200 | `test_kdensity_grid_agrees` must still pass (both modes agree) while the unit test asserting 300 fails — the pair is what pins the value, and neither alone is sufficient |
| any new corpus entry | delete the entry | the count assertion on `CORPUS` (a test asserting the corpus covers every dispatched type) fails, so entries cannot be quietly removed |

**Corpus completeness test.** Add one meta-test: enumerate the plot types `dash.ado` can
emit and the types the server dispatches, and assert every one appears in `CORPUS`. Without
it, "widen the corpus" is a one-off edit rather than a standing property, and the 22nd plot
type added next year re-opens the hole.

---

## Definition of done

A reviewer can tick these.

**Epic 8A**

- [ ] `test/test_server_dispatch.py` exists, parses `ServerAppBuilder` output, and asserts
      zero `ptype` dispatch branches; the `by()`, `by(total)` and `atype` chains are counted
      and reported separately.
- [ ] The ast classifier has its own unit test over a fixture snippet with a known count.
- [ ] A test asserts the emitted app contains no `dash_render` import.
- [ ] A test executes the emitted app with the repository removed from `sys.path` and it
      imports and builds its document.
- [ ] `test_every_global_a_copied_helper_calls_is_defined` walks class attributes, covering
      the 97 methods of `OptionTranslator`, `SchemeParser` and `GlyphMapper`.
- [ ] `test_the_scan_found_the_copied_helpers` reads `_glyph_layer_lines` (not only
      `_shared_stat_lines`) and derives its name list from the source rather than hardcoding
      it.
- [ ] Each of the six Epic 8A mutations was applied, observed to fail the intended test, and
      reverted.

**Epic 8B**

- [ ] `test/test_packaging.py` builds **and executes** a server app from the staged install,
      beside the existing `DashRenderer` (`:208`) and `GlyphMapper` (`:238`) cases.
- [ ] `inspect.getsource` calls at `dash_render.py:12386-12410` are wrapped; a source-less
      deployment raises a `dash:`-prefixed message; a unit test forces both
      `OSError` and `TypeError`.
- [ ] `test/test_server_build.cscript` carries a packaged-install case asserting rc 0, **no
      scheme-fallback warning**, and a named `economist` property in the emitted app.
- [ ] The cscript probes Python with `c(python_exec)` only and its skip path is accounted for
      by the runner.

**Epic 8C**

- [ ] `CORPUS` covers every plot type the server dispatches and every type `dash.ado` can
      emit — the union of the 19 in §4 and the 21 in Appendix B — with spec shapes taken from
      `dash.ado`'s own emission.
- [ ] `CORPUS` contains entries using `by()`, `by(total)`, KPIs, `filter()`, `link()` and
      `tabs()`; grep for each key returns a non-zero count.
- [ ] A meta-test asserts corpus completeness against the dispatched-type list.
- [ ] `fpfitci` produces `VArea`(α 0.2) + `Line` in both modes.
- [ ] `function` and `pci` draw a layer in server mode, including literal `pci`
      (`"values":[[y,x],…]`).
- [ ] `lowess` takes colour and width from the scheme in **both** modes; `#1f77b4` occurs 0
      times for `lowess` in either renderer.
- [ ] `rscatter` marker size comes from one table in both modes.
- [ ] The emitted second marker-label builder at `dash_render.py:14894-14930` is gone;
      `_mls_map2` and `_mlabpos_map2` return 0 matches in `dash_render.py`.
- [ ] `mlabel()` draws on `bar` and `spike` in server mode; `mlabsize()`, `mlabposition()`
      and `mlabgap()` resolve through `GlyphMapper._apply_mlabel_opts` in both modes.
- [ ] `kdensity` evaluates on one shared default grid and honours `n()` in both modes; the
      literal `n_pts = 200` at `dash_render.py:13380` is gone.
- [ ] `test_conformance.cscript`'s "every layer drew something" assertion runs in server mode
      as well as standalone.
- [ ] Each Epic 8C mutation was applied, observed to fail the intended test, and reverted.

**Phase-wide**

- [ ] Every fix in items 4, 5 and 9 has a regression test committed **before** the fix, with
      the failing run recorded (rule 8).
- [ ] Every new function or helper has a unit test (rule 4).
- [ ] `REMAINING.md` is unmodified.
- [ ] Full pytest suite green (baseline: 3,498 passed / 37 skipped) and 25/25 cscripts, with
      honest skip accounting.
- [ ] Work committed to the feature branch, never directly to `main`; the merge command is
      reported, not run (rule 6); commit messages describe the code changes only (rule 7).

---

## Risks and sequencing notes

**This phase must run after 05, 06 and 07, and the reason is not politeness.**

- **Item 1 cannot pass before Phase 05/06 land.** The assertion's target count is 0, and
  HEAD has 82 branches across 4 chains. Ship it as a strictly monotone ratchet — a recorded
  expected count that a commit may lower but never raise — so the guard is live from its
  first commit and the final tightening to 0 is a one-line change when Phase 06 finishes. A
  `skip` or a non-strict `xfail` here would be the exact failure mode this phase exists to
  end.
- **Item 8 is close to worthless before Phase 07 item 5.** The guard compares no data
  (`_glyph_profile`, `test/test_mode_parity.py:129`) and `ALLOWED`
  (`test/test_mode_parity.py:55`) gates no comparison — its only assertions are
  non-emptiness and a >40-character reason at `:388-392`. Widening the corpus under those
  conditions adds cases that cannot fail on a data divergence, which is precisely how
  `kdensity` (300 vs 200) sits inside the existing corpus with the file reporting 165 passed.
  Land Phase 07's data comparison first, or land item 8 and accept that its `kdensity`,
  `fpfit` and `fpfitci` entries are provisional until it does.
- **Item 8 overlaps Phase 06 item 5.** Phase 06 extends the corpus to the plot types 15-03 is
  about; Phase 08 completes it to *every* type and adds the six structural paths. Treat
  Phase 06's entries as the first tranche and Phase 08's completeness meta-test as the
  closing assertion, so the two do not write the same entries twice or, worse, disagree about
  spec shape.

**Widening the corpus will surface more failures than the five measured here.** `REMAINING.md`
records 13 further main-loop divergences under a non-default scheme (Phase 05 item 3), 20
plot types drawing nothing under `by()` (Phase 07 item 1), and four CI types losing their
band under `by()` (Phase 07 items 3 and 6). Each new corpus entry that fails for a reason
owned by another phase gets an `ALLOWED` entry naming that phase and item — never a loose
comparison, never a bare skip — and the entry is removed from `ALLOWED` by the phase that
fixes it. Plan for the allowance list to shrink monotonically across Phases 05–08; a growing
one means the guard is being negotiated with rather than fixed.

**The `lowess` drift points the wrong way.** It is the one row in the table where
`DashRenderer` is the defective renderer. A parity assertion of the "both modes agree" shape
can be satisfied by breaking the server to match. Every entry for `lowess` must assert
against the **scheme's** colour and width, and the mutation test above exists to prove it
does.

**The `kdensity` fix has a false-agreement trap.** Once both modes read one default, a
parity comparison passes whatever that default is. The value is pinned by the unit test
asserting 300 with no `n()`, not by the parity test. Ship both; neither alone is sufficient.

**Runtime.** The corpus builds both renderers per case. At 32 cases the file reports 165
passed; the widened corpus roughly doubles the build count and adds the structural paths,
which build KPI, filter and link machinery as well as glyphs. Build once per case and share
the result across the five assertions, and measure the file's wall time before and after —
a parity guard that developers skip locally because it is slow is a guard that runs only in
CI, after the drift has been committed.

**Item 3 depends on Phase 03.** The cscript can be written and committed now — it will fail
on the fallback warning until Phase 03 widens `_SCHEME_SEARCH_DIRS`, which is the correct
rule-8 ordering — but the phase cannot be closed until Phase 03 lands. Sequence the cscript's
*assertion* with Phase 03's fix, or accept a recorded, named failing test in the interim.

**Item 7's wrapper must not swallow real bugs.** Wrapping `inspect.getsource` in a bare
`except Exception` would convert a genuine `GlyphMapper` import error into a misleading
"source unavailable" message. Catch `OSError` and `TypeError` only, chain the original with
`raise ... from`, and assert the chaining in the unit test.

**Do not let the dispatch assertion become a grep.** A text search for `ptype ==` is
trivially defeated by `elif p_type ==` or a dict lookup, and a guard that can be walked
around is worse than none because it reads as coverage. The ast walk resolves the compared
name, and its own unit test over a fixture snippet is what proves it resolves correctly.
