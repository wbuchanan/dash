# GAPS.md — what `dash` promises versus what `dash` does

Source review of `dash.ado`, `dash_setup.ado`, `dash_parse.mata`, `dash_render.py`
and `schemes/*.scheme`, against `187a786`
(`feature/batch4-interactive-layer`, 62 commits ahead of `main`).

Reviewed 2026-09-21.

---

## Scope and method

"Intended capability" is taken from four sources, in this order of authority:

1. **`dash.sthlp`** — the promise made to the user. 1196 lines.
2. **The accepted option surface** — an option that `syntax` accepts is a
   promise the command will honour it. `dash.ado` declares 66 graph-level and
   137 plot-level options.
3. **Stata `twoway` parity** — `dash.sthlp:123,162` claims a copy-pasted
   `twoway` command runs unchanged.
4. **`CLAUDE.md`** — the project's own standing rules (testing, input
   hardening, resource limits, health checks, environment verification).

Findings are labelled by how they were established:

| Label | Meaning |
|---|---|
| **MEASURED** | Reproduced by executing Stata or the renderer and reading the result back. |
| **READ** | Established by reading the code; the behaviour is unambiguous. |
| **SUSPECTED** | Inferred; needs a runtime check before acting on it. |

Severity:

| | |
|---|---|
| **S1** | Produces silently wrong output, or breaks a documented feature outright. |
| **S2** | A documented or accepted capability does not work, but fails visibly or is reported. |
| **S3** | Fidelity, hygiene, coverage, or documentation drift. |

---

## Executive summary

The structure is built and the standalone renderer is broadly faithful. Eight
gaps stand between this tree and the product `dash.sthlp` describes:

1. **Every computed layer ignores its row filter.** `lfit`, `qfit`, `lowess`,
   `lpoly`, `kdensity`, `histogram`, `mband`, `mspline` and the four CI
   variants compute from the *whole* dataset regardless of a per-plot `if`,
   a linked `by()` facet, or a graph-level filter. The numbers are wrong and
   nothing warns. **S1.**
2. **The parser silently deletes plots and rewrites titles.** A `(` inside a
   quoted option value makes every later `||` segment vanish; the word
   `filter(` inside a quoted title is harvested as a real filter widget and
   cut out of the user's text. Both return `rc=0`. **S1.**
3. **A real `net install` makes all 14 schemes unreachable.** Stata fans the
   package into letter subdirectories; the renderer searches two directories,
   neither of which is one of them. Every installed user gets built-in
   fallback defaults whatever `scheme()` says. **S1.**
4. **`dash serve` aborts on every option it documents.** `dash serve,
   port(5006)` — the example in the help — returns `r(198) invalid 'port'`. **S1.**
5. **The generated server app is a separate hand-written renderer that has
   drifted.** 1 of 38 plot types delegates to the shared `GlyphMapper`; the
   rest are re-implemented. `pci` draws nothing, `fpfitci` loses its band,
   `pc*` types crash or vanish on a shared variable, `hover()` is ignored,
   per-plot and KPI qualifiers are not read, and `by()` silently drops 20
   plot types. The parity guard covers 17 of 38 types and none of these
   features. **S1/S2.**
6. **39 accepted options are inert**, plus a further set dropped with *no*
   report — `link()` and `filter()` at plot level, `saving()` on a named
   graph, and all four weight types. **S2.**
7. **Schemes are consumed only in part**, and the renderer draws a dark
   `#505050` minor grid on every figure that Stata never draws. **S2.**
8. **There is no image or data export** anywhere in the product. **S2.**

---

## A. Correctness — input silently discarded or rewritten

Two families of defect, both producing `rc=0` and plausible-looking output
from the wrong input: the computed layers ignore the rows they were given
(A1–A5), and the Mata parser discards or edits the command text before
anything downstream sees it (A6–A9).

### A1. Per-plot `if`/`in` is dropped before every statistical computation — S1, MEASURED

`dash.ado` does its part: the qualifier is parsed, stripped and written into
each plot object as `if_expr` (`dash.ado:1098-1109`, emitted at `:1240`).
`DashRenderer` builds a correct `CDSView` from it (`dash_render.py:9979-9989`)
and passes it to the mapper as `view=`.

**Thirteen `map_*` methods accept `view=` and never reference it.** They read
the whole source instead — `map_lfit` at `dash_render.py:3845-3846`:

```python
x = np.array(source.data[xvar], dtype=float)
y = np.array(source.data[yvar], dtype=float)
```

Affected: `map_lfit` (3821), `map_qfit` (3873), `map_lfitci` (3918),
`map_qfitci` (3998), `map_lowess` (4091), `map_lpoly` (4272),
`map_lpolyci` (4344), `map_fpfit` (4517), `map_fpfitci` (4569),
`map_histogram` (4636), `map_kdensity` (4806), `map_mspline` (5912),
`map_mband` (5983). `map_area` (3592) has the same defect.

Measured on data where the subset answer is unmistakable (`y = x` for `g==0`,
`y ≈ 50 + 2x` for `g==1`):

| layer | rendered with `if_expr: "g==0"` | correct answer |
|---|---|---|
| `lfit` | 25.5 → 30.0 | **1.0 → 4.0** |
| `qfit` | 25.5 → 30.0 | **1.0 → 4.0** |

25.5 → 30.0 is the *full-data* fit. The qualifier changed nothing, and no
warning was emitted.

So `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws the
all-cars regression line labelled as the foreign-cars one.

### A2. The same defect makes linked `by()` facets identical — S1, MEASURED

`_linked_graph_views` builds a per-panel `BooleanFilter`/`CDSView`
(`dash_render.py:11466-11480`) which the computed mappers then discard.
`histogram mpg, by(foreign) link(_all)` produces byte-identical bars in both
panels (`tops=[0.075, 0.0563, 0.0562]`). Unlinked `by()` is correct, because
`:11455` builds a genuinely separate source per facet — so the same command
gives different answers depending on whether `link()` is present.

### A3. Weights are parsed and silently discarded — S2, MEASURED

`_dash_parse_varpart_*` declares `[aweight fweight pweight iweight]`
(`dash.ado:781, 795, 809, 823`) and stores the type in `s(_weight)`
(`:784, 798, 812, 826`). Nothing ever reads it, and `sreturn clear` at
`dash.ado:1112` destroys it before the option parse. The weight *expression*
is discarded outright. There is no weight handling anywhere in
`dash_render.py`.

The code comment at `dash.ado:782-783` claims "it is reported as ignored".
It is not. Measured: `dash scatter mpg weight [aw=price], name(w1)` → `rc=0`,
"graph 'w1' registered", **no note**. Stata's `lfit`, `qfit`, `lowess`,
`lpoly`, `fpfit`, `histogram` and `kdensity` all honour weights.

### A4. Estimator divergences from Stata — S2, READ

- **`mspline` is a different estimator.** Stata fits a cubic spline through
  the cross-medians of `bands()` bands. `dash_render.py:5953-5972`
  PCHIP-interpolates through *every* observation after averaging duplicate x.
  No band computation exists in the function, and `bands()` and `n()` are both
  ignored — the grid is hardcoded to 200 points at `:5973`.
- **`fpfit` never fits a repeated-power FP2.** `_fit_fp2` (`:4483`) iterates
  `combinations_with_replacement`, which yields `(p, p)` pairs, but
  `_fp_transform` (`:4452-4459`) has no repeated-power branch. Royston–Altman
  requires `β₁·xᵖ + β₂·xᵖ·ln x` when `p₁ == p₂`; instead `z1 == z2`, the design
  matrix is singular, and the model collapses to FP1. About a third of Stata's
  FP2 candidates are unreachable.
- **`fpfit` applies no origin shift.** `:4456-4458` maps `x <= 0` to NaN and
  drops those rows. Stata's `fp`/`fracpoly` shifts x so all values are
  positive.

### A5. Statistical sub-options with no implementation — S3, READ

Zero occurrences in `dash_render.py`: `histogram, discrete`;
`lfitci`/`qfitci` `stdf`/`stdp`/`stdr` (only one band type is ever drawn);
`lowess` `mean`, `noweight`, `logit`, `adjust`.

**What is honoured** (verified): `lfit`/`qfit`/`fpfit` `n()`; `lowess`
`bwidth()`; `lpoly` `bwidth()`/`degree()`/`kernel()`; `histogram`
`start()`/`width()`/`bin()`/`frequency`/`percent`/`fraction`/`density`;
`kdensity` `kernel()`/`bwidth()`/`n()`; `mband` `bands()`; `level()` with
session `c(level)` inheritance and a proper t quantile (`_t_ppf`, `:6373`).
`fpfit` correctly *rejects* `bwidth()`/`degree()` the way Stata does
(`_fp_report_unsupported`, `:6474-6490`).

### A6. A paren inside a quoted option value deletes every later `||` segment — S1, MEASURED

`_dash_split_segs` gates its double-quote and compound-quote checks on
`depth == 0` (`dash_parse.mata:468, 473`). Paren mode (`:410, 415`) has **no
such gate**. So in flat (`||`) mode, any `(` inside a quoted option value
permanently unbalances `depth`, and every subsequent `||` stops being a
separator. `_first_comma_pos` carries the identical defect at `:303, 308`.

Measured, with and without the paren:

```
. dash scatter mpg weight, title("a b")   name(ctl) || line mpg weight
dash: graph 'ctl' registered.

. dash scatter mpg weight, title("a ( b") name(bad) || line mpg weight
dash: ignoring unsupported option(s): |() line() mpg() weight()
dash: graph 'bad' registered.
```

The `line` plot is **silently deleted**, the user is handed a nonsense
diagnostic naming four options that do not exist, and `rc=0`. Real `twoway`
accepts the identical line and draws both plots.

The same shape appears with `legend(label(1 "a ( b"))` — the sort of value a
user writes without thinking about it.

**Fix:** drop `& depth == 0` at `dash_parse.mata:468, 473, 303, 308` so flat
mode matches paren mode.

### A7. `filter(` inside a quoted title becomes a real filter and is cut from the text — S1, MEASURED

`_dash_extract_filters` (`dash_parse.mata:752-828`) scans the raw `0` for
`filt|filte|filter` with only a preceding-character word-boundary test
(`:787`). It never tracks quotes, and it lower-cases the text first, so the
match is case-insensitive too.

Measured end to end:

```
. dash scatter mpg weight, name(g1)
. dash build, title("Q1 filter(foreign) report") saving("b2.html") replace nobrowser
dash: dashboard saved to b2.html
```

`rc=0`, no warning — and the rendered dashboard title is **`Q1 report`**.
`foreign` became a live filter widget the user never asked for, and their
title was silently edited. `note("see FILTER(abc) here")` behaves the same
way.

This fires on `dash build` and `dash serve` (`dash.ado:2368, 2536`);
`_dash_plot` does not call it. No test covers it.

### A8. The splitter accepts malformed input that `twoway` rejects — S2, MEASURED

Paren mode `break`s at the first top-level comma (`dash_parse.mata:439`), so
anything after it is treated as graph options regardless of shape:

| Input | `twoway` | `dash` | dash behaviour |
|---|---|---|---|
| `(a) junk (b)` | `r(198)` | `rc=0` | `junk` silently discarded |
| `(a)) (b)` | `r(198)` | `rc=0` | the extra `)` silently ignored |
| `(a), (b)` | `r(198)` | `rc=0` | `(b)` swallowed into the graph-option string |

There is also **no balance check at end of scan** — `depth != 0` or
`in_dq != 0` on exit should be an error but is not. So an unclosed `(` or an
unterminated `"` yields one segment and no message:

- `scatter y x, legend(off || line y2 x` → 1 segment, silent
- `scatter y x, title("oops || line y2 x` → 1 segment, silent

Empty groups `()` are dropped silently at `:428`.

`test/test_tokenizer.cscript` passes 20/20 with all of the above live. No test
constructs a quote containing a paren.

### A9. The UTF-8 gate passes the encodings it exists to stop — S2, MEASURED

**RESOLVED (WP-08).** Every sequence in the table below was measured to be
accepted by the old validator, and every one is now rejected. The rewrite
applies RFC 3629 s.4's per-lead second-byte ranges and was verified against
Python's own decoder over 41,976 sequences with zero mismatches; 2,245 are
committed as `test/fixtures/utf8_cases.txt`. C0 control bytes remain accepted
here on purpose — they are well-formed UTF-8, and it is `_dash_json_str`'s
job to escape them. See the BUGS.md entries.

`_is_utf8` (`dash_parse.mata:90-109`) checks only the **lead-byte range** and
that continuation bytes are `0x80-0xBF`. It never constrains the second byte
per lead byte, which RFC 3629 requires:

| Input | `_is_utf8` | should be |
|---|---|---|
| overlong `E0 80 AF` | **passes** | reject |
| overlong `E0 9F BF` | **passes** | reject |
| UTF-16 surrogate `ED A0 80` | **passes** | reject |
| surrogate `ED B0 80` | **passes** | reject |
| overlong `F0 80 80 80` | **passes** | reject |
| above U+10FFFF `F4 90 80 80` | **passes** | reject |
| NUL, ESC, BEL, DEL | **passes** | policy |

Correctly rejected: `C0 80`, `C1 BF`, a bare continuation byte, 5-byte `F8`,
truncated `C3`.

The validator exists to give a clean `r(198)` before bad bytes reach the
backend. It does the opposite — measured:

- `title("x" + char(237)+char(160)+char(128) + "y")` →
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xed`, **`r(7102)`**,
  raw Python traceback.
- `title("bad" + char(1) + "title")` →
  `json.decoder.JSONDecodeError: Invalid control character`, **`r(7102)`** —
  because `_dash_json_str` leaves C0 control bytes raw (see E6).

This is not code injection; no user text reaches Python as code. It is an
availability and diagnostics defect against CLAUDE.md rules 14 and 16, at the
rule's own designated enforcement point.

Related: `_dash_option_names` (`dash_parse.mata:945`) toggles its in-quote
flag on every `"` with no compound-quote handling, so an odd quote count
drops trailing options — measured, `title("unbalanced quote) xlabel(1)`
reports only `title`.

---

## B. Packaging — `net install` makes every scheme unreachable

### B1. The scheme search path does not survive installation — S1, MEASURED

`dash_render.py:1524-1532` searches exactly two directories, both derived
from `__file__`:

```python
_SCHEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")
_SCHEME_SEARCH_DIRS = (_SCHEMES_DIR, os.path.dirname(os.path.abspath(__file__)))
```

A real `net install` from this repo's `stata.toc` + `dash.pkg` into a sandbox
PLUS produces:

```
plus/d/dash.ado   plus/d/dash.sthlp   plus/d/dash_parse.mata
plus/d/dash_setup.ado                 plus/d/dash_setup.sthlp
plus/py/dash_render.py                 <- .py routed to py/, not d/
plus/e/economist.scheme                <- letter subdirectory, flattened
plus/s/s1color.scheme … plus/s/stsj.scheme   (13 files)
```

So the search path evaluates to `plus/py/schemes` (does not exist) and
`plus/py` (holds only `dash_render.py`). Measured against the installed copy:

```
resolve_or_fallback('stcolor') -> name='s2color', is_fallback=True
UserWarning: dash: scheme 'stcolor' was not found …
UserWarning: dash: no scheme file could be resolved … Falling back to built-in defaults.
```

The build returns `rc=0` and writes a file, so nothing fails loudly. **Every
installed user gets `_FALLBACK_PROPS` (`:1552-1569`) whatever `scheme()`,
`theme()` or `c(scheme)` says, and all 14 schemes collapse to one look** —
one that is not even s2color. Measured deltas: `grid_line_width` 0.8 vs 1.5;
`bar_alpha`/`area_alpha` 0.8 vs 1.0; text 10pt vs 11pt; heading 13pt vs 14pt;
`graphsize` absent; **no horizontal grid at all**; and no `symbol p#` or
`linepattern` keys, so every mono scheme loses its whole symbol and dash
cycle (`p_symbols` measures all-`circle`).

The comment above those lines anticipates *one* flattening
(`<install dir>/x.scheme`); Stata uses a third layout it does not cover.

`findfile s2color.scheme` **does** locate the installed file (`plus/s/…`,
rc=0). `dash.ado` never looks, and never tells Python where to look.

**RESOLVED (WP-05).** `SchemeParser` now has a `_PLUS_ROOT` guarded on the
package directory being named `py`, and an `_installed_letter_dir(name)` that
returns a directory only for one of the fourteen literal `_BUILTIN_NAMES`.
The lookup is an isolated block *after* the candidate loop and does not extend
`allowed`: doing so would also authorise the caller-controlled CWD candidate,
letting a symlink named `s2color.scheme` reach any file in `PLUS/s`. That
over-broad variant was built and measured — 25 files reachable under the test
PLUS, the whole subtree once CWD was inside it, and the entire home tree when
`dash_render.py` was not under `py/`. Verified end to end against a real
install: `scheme(s1color)` now emits zero warnings and the HTML no longer
carries s2color's `#eaf2f3`. The `_FALLBACK_PROPS` deltas this section
measured are fixed too — it now carries s2color's grid, graphsize, gsize,
linewidth, symbolsize and intensity values, held there by
`test_scheme_fallback_provenance.py`. Tests: `test/test_installed_layout.py`
(INST-01..16).

### B2. The hardcoded fallback renderer path points at the wrong directory — S3, READ

`dash.ado:1747`, `:2480`, `:2621` all fall back to
`` `c(sysdir_plus)'d/dash_render.py ``. The installer puts it in `py/`. Masked
today because `findfile` succeeds first.

**RESOLVED (WP-05), with a correction.** Measured: `findfile dash_render.py`
does succeed on an installed tree — it searches the *extension* subdirectory,
returning `PLUS/py/dash_render.py` — so neither fallback was ever reached by a
real user and this was never a live failure. What made it worth removing is
that nothing confirmed the file existed before the path reached
`runpy.run_path`, so when a branch *was* reached the user got a Python
`FileNotFoundError` naming a Stata internal directory, `r(7102)`, and no
message from dash; `dash serve` announced the server first and died after. All
three copies are replaced by one `_dash_find_render` holding only the two
candidates that can succeed, exiting 601 with a dash-authored message
otherwise. Tests: `test/test_render_locate.cscript` (LOC-01..09).

### B3. Schemes install under names Stata cannot see, and may collide — S3, READ

They install as bare `s2color.scheme`, not `scheme-s2color.scheme`, so they
are invisible to Stata's own `set scheme`. `plus/s/sj.scheme` and friends also
sit in the shared PLUS letter directories, where they can collide with other
packages.

**CORRECTED, then CLOSED as a documented limitation (WP-05).** "Invisible" is
the wrong word, and the mechanism matters. Stata's own
`/Applications/StataNow/ado/base/s/scheme.class:171-173` reads:

```
capture findfile scheme-`scheme'.scheme
if (_rc) capture findfile `scheme'.scheme
```

so a bare `<name>.scheme` is *second in line*, not unseen. dash's files are
shadowed rather than invisible, and shadowed by StataCorp's own copy for all
fourteen names, so `set scheme s2color` is unaffected — measured, rc 0 with
StataCorp's background colour.

The collision with other packages is real but was measured to be inert for
dash: `net install` refuses a duplicated basename with `rc 602` and
`, replace` overwrites it, which is generic packaging behaviour for any
duplicated name rather than anything specific to schemes. Renaming to
`dash_<name>.scheme` would end it, but `scheme(<file>.scheme)` is a supported
way to name a file, so the names are kept and the limitation is now stated in
`dash.sthlp` rather than left implicit.

### B4. `dash.pkg` cannot be updated by `adoupdate`, and states the wrong version — S3, READ

The manifest carries its version only as prose (`dash.pkg:25`,
`d Version: 1.0.0 25mar2026`). There is no `v` line and no
`d Distribution-Date:` line, so `adoupdate` can never detect an update.

It is also **out of step with the code**: `dash.ado` and `dash_parse.mata`
both declare `v2.0 27mar2026`. An installed package reports 1.0.0.

**RESOLVED (WP-05), with a correction.** The joint attribution above is wrong.
`v` is the manifest's **file-format** version — the same field `stata.toc`
sets to 3, maximum 3, with `v 4` being `r(610)` — not the package's version,
and `net install` does not copy it into `stata.trk`, so it cannot take part in
an update comparison at all. Only `d Distribution-Date:` can. `dash.pkg` now
leads with `v 3` (StataCorp conformance, not the fix) and carries
`d Version: 2.0  27mar2026` and `d Distribution-Date: 20260327`;
`dash_setup.ado`, `dash.sthlp` and `dash_setup.sthlp` were moved to the same
version so all six agree. Tests: `test/test_pkg_metadata.py` (PKG-01..08),
which asserts the date and the format version **separately** so the two
reasons cannot be conflated again.

All 20 declared files exist and nothing shippable is missing; `stata.toc` is
correct and minimal.

---

## C. `dash serve` — every documented option aborts the command

### C1. The option string is forwarded with its leading comma — S1, MEASURED

`_dash_serve` forwards `` `0' `` verbatim at `dash.ado:2601`:

```stata
_dash_serve_spec, specpath("`master_json_path'") datapath("`data_json_path'") `0'
```

`` `0' `` still carries the leading comma, so the call becomes
`…datapath("…") , port(5006)` — two commas on one line, and everything after
the second is read as a positional argument. This is the exact defect
`_dash_build` fixes with `: subinstr local _fwd_opts "," ""` at `dash.ado:2440`
and documents at `:2434-2439`. It was never applied here.

Measured:

```
. dash scatter mpg weight, name(g1)
dash: graph 'g1' registered.
. dash serve, port(5099) timeout(1) nobrowser
invalid 'port'
r(198);
. dash serve
dash serve: starting Bokeh Server on port 5006.
```

So `port()`, `timeout()`, `nobrowser` and every inherited build option are
unreachable. Only the bare form runs. `dash serve, port(5006)` is the
documented example at `dash.sthlp`.

`_dash_serve_spec` itself is correct and complete — it validates the port
range, the timeout, and inherits the build options. The defect is one line
above it.

### C2. Nothing could catch it — S2, READ

`test_serve_options.cscript` deliberately calls `_dash_serve_spec` *directly*
(`:55, 99, 113, 137-146`), bypassing the only line where the defect lives.
Its own header at `:28` says it covers "everything `dash serve` does except
the launch". All five of its PASS banners are labelled "dash serve …" and none
of them runs `dash serve`. The other five Stata-level `dash serve`
invocations in the suite are all `capture` + `assert _rc == 198` error-path
tests. **The happy path has zero coverage.**

### C3. An unexplained diagnostic on the bare form — S3, MEASURED

Bare `dash serve` prints `(file /var/…/S_26952.000002 not found)` before
starting the server, and starts it anyway. The same message appears on a
plain `dash build`. It is suppressed in normal use and surfaces only under
`capture noisily`; the cause was not isolated. Worth tracing — it indicates a
`capture confirm file` failing somewhere in the spec path.

---

## D. Standalone versus server — one product, two renderers

`dash.sthlp:516-533` carries a Server Mode comparison table. Every one of its
13 rows is accurate. The gap is everything the table does not list.

### D1. The unification never happened — S1, READ

`ServerAppBuilder` emits `_DASH_MAPPER = GlyphMapper(...)` at
`dash_render.py:12432` and calls it **once**, for `scatter` (`:14090`). The
other 37 plot types remain a hand-written `if/elif` chain in generated string
literals (`:14058-14890`), plus **two further near-duplicate reduced chains**
for facet and "Total" panels (`:15144-15212`, `:15245-15315`). Three dispatch
tables, independently maintained.

The comment at `:12318-12327` claims the server branches call the shared
mapper. They do not.

### D2. Confirmed divergences — S1, MEASURED

| Plot / feature | Standalone | Server |
|---|---|---|
| `pci` | `[Segment]` | **`[]` — draws nothing, silently.** `:14781-14796` reads `y1var/x1var/y2var/x2var`; `dash.ado:1164-1212` emits `"values"` for `pci`. The gate is never true. This is the same bug already fixed standalone (see the note at `:10015-10018`), never ported. |
| `fpfitci` | `[VArea, Line]` | **`[Line]` — no confidence band.** `:14253-14263` is a verbatim copy of the `fpfit` branch. `lfitci` (`:14375`) and `qfitci` (`:14402`) do draw bands. |
| `pcspike`/`pcarrow`/`pcbarrow` with a repeated variable | draws | **`ValueError: Expected unique column names`** — `:14681-14683`, `:14697-14699` build `cols` with no de-duplication. |
| `pcscatter` with a repeated variable | `[Scatter]` | **`[]`** — `dict.fromkeys` dedupe at `:14788` shortens the list, so `if len(_cols) == 4` at `:14789` is false. |
| `bar` / `histogram` / `area` hover | 1 HoverTool | **none** |
| `hover(foreign)` | `[weight, mpg, foreign]` | **`[weight, mpg]` — `hover()` ignored** |

`HoverTool` is imported at `:12879` and never instantiated. The only server
hovers that appear come indirectly from the three mappers the server does
delegate to.

### D3. Qualifiers are not read at all in server mode — S1, READ

There is no `plot.get('if_expr')` anywhere past `dash_render.py:12700`; the
server reads only graph-level qualifiers (`:13812/13819`, `:15011-15012`,
`:15528-15529`). KPI `if`/`in` is likewise ignored (`:15331`, `:15645`,
`:15694`) — producing a wrong-but-plausible number, the exact failure
`dash.ado:1938-1945` was written to fix on the standalone side.

`dash.ado:1484`'s comment ("per-plot qualifiers are not read in build/server
flows") is now stale for standalone and accurate for server.

### D4. `by()` drops 20 plot types in server mode — S1, READ

The facet and Total chains (`:15144-15212`, `:15245-15302`) handle 18 types.
Missing: `lfitci qfitci rarea rbar rspike rcap rline rconnected rcapsym
rscatter scatteri pci pcspike pcarrow pcbarrow pcscatter tsline tsrline
mspline function`. They fall off the end of the `elif` chain with no `else`
and no warning. Standalone's facet path reuses `_make_figure` and therefore
the full dispatch.

Those blocks also hardcode the style the parity test exists to catch:
`size=6` at `:15145, 15200, 15246`; `width=0.8` at `:15150`.

### D5. `mlabel()` excludes all range types in server mode — S2, READ

`dash.sthlp:698-700` says `mlabel()` applies to "scatter, line, connected,
bar, spike, dot, dropline, and all range plot types". Standalone honours
every one (`_apply_mlabel_opts:3301`, wired at 13 call sites).
`dash_render.py:14897-14901` skips the mlabel block for every range type, and
for `scatteri`, the `pc*` family, `lfit`, `qfit`, `lfitci`, `qfitci`,
`lowess`, `mspline`, `function`, `histogram` and `kdensity`.

### D6. No "drew nothing" warning in server mode — S2, READ

Standalone warns at `:10078-10091` when a layer adds no data from a non-empty
source. The generated app has no equivalent, which is why D2's silent
failures are silent.

### D7. Smaller divergences — S3, READ

- Server `ptype` is not lower-cased (`:14031`) while the facet chains are
  (`:15137, 15237`); the main chain lacks the `'hist'` alias the facet chains
  have. Unreachable through `dash.ado` today, but three tables disagree.
- `layout(name:row,col)` is 1-indexed in server mode (`:15795`) and accepts
  **0-based too** standalone (`:11126-11128`) — one spec, two meanings.
- Tabs: an unassigned item is drawn *below* the tabs in plain-grid and server
  modes (`:11981, 12072, 15855`) as documented, but *above* them under
  `layout(bs)` (`:10888-10889`).
- KPI `fmt()`: server `_format_kpi` (`:13665-13682`) always comma-groups,
  ignores the `c` suffix, and has no `%9.0g` default or width-overflow
  fallback. `fmt(%12.0fc)` ≡ `fmt(%12.0f)` when served.
- Legend text size: standalone uses `text_font_size` (`:9067-9068`), server
  uses `tick_label_font_size` (`:12660`). These differ for 13 of 14 schemes.
- `_MAX_EXPR_CHARS` is a module constant standalone (`:2271`) and hardcoded
  `5000` in the server copy (`:14872`).
- No CSP in server mode: `_CSP_META` (`:660-668`) is injected at `:10897` and
  `:12139`, both standalone.

### D8. The parity guard covers less than half the surface — S2, READ

`test/test_mode_parity.py` `CORPUS` (`:186-274`) covers **17 of 38** plot
types: scatter, line, area, bar, histogram, kdensity, mband, dropline, spike,
connected, lfit, lpoly, lpolyci, dot, rcapsym, scatteri, mspline.

**Uncovered (21):** `function pci pcspike pcarrow pcbarrow pcscatter lfitci
qfit qfitci fpfit fpfitci lowess rarea rbar rspike rcap rline rconnected
rscatter tsline tsrline`.

No corpus entry sets `by()`, `link()`, `filter()`, `tabs()` or a KPI, and
`_glyph_profile` (`:128-147`) collects neither tools nor tooltips. **Every
finding in D2–D6 would have been caught by a corpus that did.**

---

## E. The option surface

### E1. 39 options are accepted, reported, and inert — S2, READ

Two `_dash_pending` blocks: graph-level at `dash.ado:364-384` (20 entries)
and plot-level at `:593-632` (39, a strict superset).

**Union, 39 distinct:**

```
at          b1title     b2title     blabel      ciopts      cmissing
colorlist   coloruseplegend         connect     fitopts     fxsize
fysize      horizontal  l1title     l2title     lineopts    lstyle
mlabwidth   mlpattern   mlstyle     mstyle      nodraw      play
pstyle      r1title     r2title     recast      scale       sort
subtitle2   t1title     t2title     text        title2      vertical
xmlabel     xmtick      ymlabel     ymtick
```

This list matches `dash.sthlp`'s "Unsupported Stata twoway options" section
exactly, in both directions — help and code agree, and
`test_unsupported_report_is_true.py` enforces it. **This is honest reporting,
not a silent gap**, and it is the best-governed part of the surface.

Two nuances:

- The 19 plot-level entries are still written into the JSON by
  `_dash_plot_opts_to_json` (`dash.ado:862-874`); they are dropped by the
  *renderer*, not the ado. Two are read and explicitly discarded
  (`coloruseplegend` at `dash_render.py:3037`, `mlabwidth` at `:3398`).
- **`nodraw` is on both pending lists but is actually honoured**
  (`dash.ado:1765` suppresses the browser launch). So dash prints
  "ignoring unsupported option(s): nodraw()" for an option it just applied —
  precisely the stale-list failure the comment at `dash.ado:578-592` was
  written to prevent. It slips past the enforcing test because `nodraw`
  changes browser behaviour, not file output.

### E2. Options dropped with *no* report — S2, MEASURED

These are not on either pending list, so `_dash_report_ignored` never names
them:

| Option | Declared | Behaviour |
|---|---|---|
| `link()` at plot/graph level | `dash.ado:289, 507` | Stored, promoted, written to `graph_options.link` (`:1465`). The renderer reads only `build_options["link"]` (`dash_render.py:11288, 12763`). Silently inert. |
| `filter()` at plot/graph level | `dash.ado:289, 507` | Same path; renderer reads only `build_options["filter"]` (`:11295, 12764, 8726`). |
| `saving()` on a **named** graph | `dash.ado:283, 506` | `_dash_plot` routes to `_dash_register_graph` (`:1487`) and never reaches the `saving` extraction at `:1602`. `dash build`'s own `saving()` wins. |
| weights | `dash.ado:781-826` | See A3. |
| `saving()`, `replace`, `server` in `_dash_prepare_spec` | `:2009, 2019, 2020` | Declared and never referenced in the body. Harmless for `dash build`; `dash serve` forwards them through its `*`, so they would be accepted-and-ignored if C1 were fixed. |

### E3. Sub-options vanish without a note — S2, MEASURED

`legend()`, `xlabel()`, `yscale()`, `by()`, `xline()`, `filter()` are all
declared `string asis`, so unknown *sub*-keys never reach the ignored-option
report. `dash.sthlp:162-163` claims "Nothing is ever dropped without being
named". Measured as silently accepted and unhandled:

`legend(span|stack|colfirst|holes()|keygap()|symxsize()|textwidth()|bmargin())`,
`xlabel(, valuelabel)`, `ylabel(, labcolor())`,
`yscale(reverse|noline|titlegap())`, `xtitle(, orientation())`,
`xline(3000, lcolor() lpattern())`.

`_rebuild_legend` (`dash_render.py:8956`) has no unknown-key warning. Only
`xscale`/`yscale` get one (`_report_unhandled_scale_opts:805`), and only for
5 tokens.

`by()` is the same shape: `_parse_by_raw` (`:8669-8701`) regex-matches
`cols()`, `total` and `missing` and discards everything else with no
diagnostic. Stata's `by()` also takes `rows()`, `holes()`, `iscale()`,
`compact`, `noedgelabel`, `style()`, `colfirst`, `norescale`, `yrescale`,
`xrescale`, `noixlabel`, `noiylabel`, `noixtick`, `noiytick`, `imargin()`,
`ixaxes`, `iyaxes`, `altshowyvars`, plus its own `title()`/`note()`/`legend()`.

`_parse_filter_raw` (`:8730-8774`) is worse: a spec whose text contains
`;` `` ` `` `$` `\` `__` or the words `import`/`eval`/`exec`/`open`/`getattr`
is discarded **whole**, with `rc=0` and no message. A legitimate
`label("R&D __ spend")` makes the entire filter widget vanish. An
unrecognised `type()` is likewise skipped silently (`:11804-11805`, server
`:15462-15463`).

### E4. `bw()` silently changes meaning — S2, MEASURED

`dash.ado:560` folds `bw` → `barwidth` unconditionally. Real Stata accepts
`bw(400)` on `twoway lpoly` (measured `rc=0`) and rejects it on `twoway bar`
(`r(198)`). So `dash (lpoly mpg weight, bw(400))` sets `barwidth`, not
`bwidth`, with no note — a valid twoway command whose meaning changes. This
directly undercuts the drop-in claim at `dash.sthlp:123, 162`.

### E5. Validation is applied to exactly one option — S2, READ

`level()` is validated in the ado (`dash.ado:549-558`) with a clear message.
All 69 other plot-level values and all 54 graph-level values are emitted
verbatim as JSON strings. Some get downstream validation
(`_stat_option_float` for `xsize`/`ysize`/`aspectratio`,
`dash_render.py:9228-9254`; `_resolve_kpi_color`, `:10484-10485`), but it is
not systematic.

`dash kpi` is the best-validated surface — statspec regex (`:1839`), stat
whitelist (`:1845`), percentile bounds (`:1850`), `confirm variable`
(`:1863`), name regex (`:1865`), `update()` whitelist (`:1871`). Its one gap
is `fmt()`, which is unvalidated and interpolated into an evaluating context:
`local kpi_display : display `fmt' `kpi_value'` (`:1918`). Measured:
`fmt("HACKED" %9.2f)` → `r(111) HACKED not found`. **Not an injection
vector** — the quotes are stripped by `syntax` and the token is then resolved
as an identifier — but a confusing failure where `level()` gets a clear one.

### E6. Escaping and encoding holes — S2, READ

- **`_dash_json_str` (`dash.ado:224-232`) handles `\`, `"`, TAB, LF, CR and
  nothing else.** `\b` (8), `\f` (12) and every other C0 control byte are
  illegal raw inside a JSON string and would surface as a Python
  `JSONDecodeError` rather than a Stata-side diagnostic.
- **`theme()` is the one build option written unescaped** — `"theme":"`theme'"`
  at `dash.ado:2343`, while `title`, `subtitle`, `tabs`, `scheme` and `filter`
  all go through `_dash_json_str` first.
- **`saving()` backslashes are doubled and never un-escaped.** `_dash_json_str`
  turns `\` into `\\`; the extractor at `dash.ado:1602-1607` slices the raw
  JSON text and uses it as a filesystem path. Measured: `C:\dir\out.html`
  comes back as `C:\\dir\\out.html`. **Breaks every Windows `saving()` path on
  the immediate-render route.** `dash build` is unaffected — it uses the local
  directly.
- **`_dash_check_utf8` is called once**, at `dash.ado:1385`, on `` `0' `` in
  `_dash_plot`. `_dash_kpi`, `_dash_build`, `_dash_prepare_spec`,
  `_dash_serve` and `_dash_serve_spec` do not call it. So KPI `title()`,
  build `title()`/`subtitle()`/`tabs()` and `filter(… label("…"))` reach the
  JSON with no UTF-8 gate — contrary to CLAUDE.md rule 16.

### E7. `_dash_validate_path` — what slips through — S3, MEASURED

`dash.ado:157` rejects `" \` $ ; & | < >`, TAB/LF/CR, a literal `..` anywhere,
and enforces the extension. Measured to pass with `rc=0`:

`~/x.html` · `out.HTML` · `a*b.html` · `a?b.html` · `-rf.html` ·
`/etc/passwd.html` · `a!b.html` · `a\b.html` · `a#b.html` · `a%b.html`

Notable: **no directory confinement** — any absolute path is writable; `~` is
accepted but expanded by neither `shell open` nor Python; a **leading `-`**
survives, and `shell open "-e.html"` has the target parsed as a flag.
Conversely a legitimate `my..report.html` is refused.

`main()` in `dash_render.py:16121-16157` does not validate `output_path` at
all — the protection is real via the Stata entry point and absent if the
renderer is invoked directly.

---

## F. `twoway` parity

### F1. Four real `twoway` plot types are rejected outright — S2, MEASURED

`contour`, `contourline`, `pcarrowi`, `pccapsym` → `r(198) unrecognised plot
type` (`dash.ado:938-948`, against the 38-row table at
`dash_parse.mata:174-211`). They appear nowhere in `dash_render.py` either.

`dash.sthlp:174` claims "An unknown option is never an error, so a command
copy-pasted from a do-file always runs." That is true of *options* and false
of *plot types* — **and the help lists no supported plot types anywhere**, so
a user has no way to anticipate it. The error message itself does list all 38.

### F2. Eleven supported plot types are undocumented — S3, READ

Present in `dash_parse.mata:174-211`, routed in `dash.ado`, rendered in
`dash_render.py`, and mentioned nowhere in `dash.sthlp`:

`rconnected rscatter pcspike pcarrow pcbarrow pci pcscatter tsline tsrline
mband function`

`tsline`/`tsrline` even carry bespoke `tsset` fallback logic and error text
(`dash.ado:1013-1024, 1080-1092`).

### F3. Common twoway options land in "unknown" rather than the documented list — S3, MEASURED

These are reported — correct behaviour — but none appears in the help's
"Unsupported twoway options" list, so the note arrives as a surprise:

`clcolor() clpattern() clwidth()` (the standard `line`/`connected` styling
triple), `addplot()`, `margin()`, `region()`, `bargap()`, `xreverse`
`yreverse`, `xalternate` `yalternate`, `xoverhang` `yoverhang`, `xcommon`
`ycommon`, `lockaspect`, `zoom()`, `altaxis`, `mlabangle()`, `mlabformat()`,
`mlabvposition()`, `mlabtextstyle()`, `ddensity`, and `sort(varname)` — dash
declares `SORT` as a flag, so the twoway `sort(x)` form is *unknown* rather
than merely ignored.

### F4. Documented capabilities that do not work as described — S2, MEASURED

| Claim | `dash.sthlp` | Reality |
|---|---|---|
| "`p97.5`" — any percentile | 466-467 | **`dash kpi p97.5(price)` → `r(198)`.** The statspec regex (`dash.ado:1839`) rejects the `.`, and `:1849` is integers-only. Both renderers already accept fractional percentiles (`dash_render.py:8339, 7278`); it can never be entered. |
| "`nodraw` has the same effect [as `nobrowser`]" — in the **`dash build`** table | 296 | **False for `dash build`.** `dash.ado:2509` tests only `` `nobrowser' `` and `$dash_nobrowser`. The help contradicts itself at `:1149-1152`. |
| "put its `.scheme` file in the working directory and give its **base name**" | 1084-1086 | **Fails at build level.** `dash_render.py:7967-7970` rejects any name that is neither an alias nor a builtin unless it ends in `.scheme`, *before* the CWD bare-name branch (`:1704-1716`, added for exactly this) can run. Measured: `scheme(mycustom)` → s2color + warning; `scheme(mycustom.scheme)` → works. Graph-level `scheme()` *does* work (`:9484-9487` bypasses the gate) — so the same name behaves differently on `dash scatter` and `dash build`. |
| "joins them with a **semicolon** internally" | 408 | Joiner is `" \|\| "` (`dash_parse.mata:812`). Semicolon is only a legacy accepted separator. Mechanism description wrong; behaviour unaffected. |
| scipy needed for "lfitci, qfitci, **kdensity** and mspline" | 1182-1183; `dash_setup.sthlp:76-77` | **2 of 4 wrong.** `qfitci` uses `np.polyfit` + a hand-written `_t_ppf` (`:6373-6400`, docstring says "WITHOUT scipy"); `kdensity` uses the hand-rolled `_KERNELS` table (`:6592-6600`). |
| `xtick()`/`ytick()` = "tick positions **without labels**" | 866-869 | **Inert when combined, wrong when alone.** `dash_render.py:9906-9913` does `spec = self._parse_axis_spec(raw_ax or raw_tick)` — `xtick()` is discarded whenever `xlabel()` is also given (the normal Stata idiom), and alone it produces *labelled* ticks. No `MinorTicker` is touched anywhere. |
| `colorvar()` — "a **plot layer** may take its colour from a third variable" | 926-948 | Scatter family only. `_apply_colorvar` (`:2995`) has one call site, `map_scatter:3480`. Silently dropped on bar, area, spike, dropline, rarea, rbar, pcscatter, rscatter, histogram — and it is not on the pending list, so nothing tells the user. |
| `legend(top\|bottom\|left\|right)` | 853 | Honoured but with wrong geometry — mapped to `leg.location="top_center"` etc. (`:10139-10157`), i.e. *inside* the plot. Stata places these outside. `_move_legend` (`:9193`) exists and is used for `position(#)` but not the bare keywords. |
| `ylabel2()`/`xlabel2()` | 905-912 | Plain numlists only. `#5`, `10(5)40`, `minmax`, `none`, `format()`, `labsize()`, `grid` all yield **zero ticks, silently** — it uses the bare `_parse_axis_label_opt` (`:9393`), which keeps only `float()`-able tokens, not `_parse_axis_spec` (`:9304`). |

### F5. Every documented example parses clean — no gap

All numbered examples in `dash.sthlp:613-1000` were executed through the real
`syntax` declarations: **all `rc=0`, empty `_pending`, empty `_unknown`** —
including `xtitle(Weight (lbs))`, `note(Source: 1978 Automobile Data)`,
`xlabel(#8, grid) ylabel(10(5)40, format(%9.0f))`,
`legend(order(1 2) cols(2) size(small) label(1 "A"))` and the two-`filter()`
form. The negative examples behave as documented. `dash kpi` values match
`summarize, detail` exactly (p25 = 4195, skewness = 1.6534335,
mean if foreign==1 = 24.772727), confirming the Hyndman-Fan type 2
percentile claim at `:467-471`.

---

## G. Schemes

### G1. Twelve of Stata's 26 schemes are not translated — S3, MEASURED

Shipped (14): `economist s1color s1mono s1rcolor s2color s2gcolor s2mono sj
stcolor stcolor_alt stgcolor stmono1 stmono2 stsj`.

Missing and user-selectable: **`s2manual`, `s1manual`, `s2gmanual`,
`s2color8`, `sttrans`, `stgcolor_alt`**. The rest (`meta`, `stcolor_meta`,
`stgcolor_meta`, `stcolor_mv`, `stgcolor_mv`, `stcoloralias`) are internal.

`dash` can also reach **none** of the 129 third-party `scheme-*.scheme` files
installed on this machine — see F4's bare-name row and §G5.

### G2. The translations are exact, but they are not Stata scheme files — S3, MEASURED

Flattening every Stata `#include` chain and resolving every colour name
through `style/color-*.style` gives **0 mismatches across all 14 schemes**, on
every directive Stata's chain declares. s2color's `p1`–`p15`
(`navy`→`#1a476f` … `bluishgray`→`#d9e6eb`) match byte-for-byte.

But Stata's `scheme-s2color.scheme` has **2060** directives; dash's has
**118**. The ~1940 absent ones cover bar/box/pie/dot/matrix styling, margins,
tick geometry, `draw_minor_*`, `alignstroke`, and the `linestyle`/`textboxstyle`
stubs. They are also flattened (no `#include`), so they are **not drop-in
Stata scheme files**. Per scheme, 46–76 keys are dash's own inference rather
than transcription (`color p#line`, `color p#bar`, `color p#mark`, `symbol p#`,
`linepattern p#line`, `intensity area`) — defensible and traceable through
`test/fixtures/scheme_truth.json`'s `sources` map, but the provenance does not
survive into the shipped files.

### G3. Every dashboard draws a dark grid Stata never draws — S1, MEASURED

`dash_render.py:2185` sets the minor grid unconditionally:

```python
grid.minor_grid_line_color = self.minor_grid_color
```

Bokeh's `BasicTicker.num_minor_ticks == 5` and `minor_grid_line_alpha == 1.0`,
so these lines render. Measured on real figures:

| scheme | major x | major y | **minor x** | **minor y** |
|---|---|---|---|---|
| s2color | none | `#eaf2f3` | **`#505050`** | **`#505050`** |
| s1color | none | none | **`#505050`** | **`#505050`** |
| stmono1 | none | none | **`#505050`** | **`#505050`** |
| economist | none | `#ffffff` | `#ffffff` | `#ffffff` |

Stata's own s2color declares `draw_minor_grid no`, `draw_minor_hgrid no`,
`draw_minor_vgrid no`. dash's translated file carries no `draw_minor_*` key at
all. So schemes that draw **no grid whatsoever** get a dark grid on both axes.

### G4. Parsed scheme attributes with no consumer — S2, MEASURED

Confirmed by reference count (a count of 1 means the assignment and nothing
else):

| Directive | Parsed at | Status |
|---|---|---|
| `gsize note` → `note_font_size` | `:2047` | **Fully dead.** Note/caption sizes hardcoded 11.0/12.0 px at `:9866-9868`. |
| `color p#mark` → `p_mark_colors` | `:1980-1982` | **Fully dead.** `default_color()` (`:2103-2112`) never indexes it. Invisible today only because `p_mark_colors == p_colors` in all 14 shipped schemes; a user scheme declaring it gets nothing. |
| `clockdir legend_position` | `:2086-2087` | **Dead in both modes.** Standalone has no consumer; the server sets `lg.location = 6` (`:12661-12662`), and Bokeh 3.9 raises `ValueError` on a numeric `Legend.location`. All 14 schemes declare a numeric clock position. |
| `numstyle legend_cols` | `:2088` | **Dead in both modes** — it sits *after* the failing assignment **inside the same `try:`** (`:12655-12666`), so the `ValueError` skips it too. |
| `color heading` / `gsize heading` | `:1965, 2044` | Reach only the dashboard CSS (`.db-title`), never a Bokeh figure title. Measured: `fig.title.text_color == '#444444'` and `text_font_size == '13px'` under s2color, s2mono, stmono1 and economist alike — all Bokeh defaults. |
| `graphsize x/y` | `:2054-2055` | Ratio only (`:9244-9245`); absolute size never used. |

Parser branches no shipped scheme exercises (dead code, not a rendering gap):
`color plineplot`, `linepattern plineplot`, `linepattern p`, `linepattern
p1`–`p15`, bare `graphsize`, and `#include` support (`:1786-1800`) — **zero**
of the 14 files contain an `#include`, whereas 25 of Stata's 26 do.

### G5. Numeric scale factors are wrong — S2, MEASURED

- **`gsize`**: `dash_render.py:1846-1849` computes `int(val * 1.2)`. Stata's
  relative-size unit is fixed — `gsize-medium.style` = `3.8194` = 11 pt on a
  4-inch graph; `gsize-large.style` = `4.8611` = 14 pt. The factor is **2.880**.
  `economist` declares `gsize heading 6.0` → Stata means **≈17 pt**; dash
  produces **7 pt**. Measured: economist's dashboard title renders *smaller*
  than its 11 pt subtitle.
- **`linewidth`**: `:1899-1911` takes the number as pixels. Stata
  `linewidth medium` = `.30`; economist declares `linewidth p 1.2`, i.e. 4×
  medium. Measured `default_line_width`: s2color/s2mono/stcolor = **1.5**,
  economist = **1.2** — economist's deliberately heavy lines render *thinner*
  than every other scheme's.

### G6. Inline styles defeat the scheme on KPI cards — S2, MEASURED

`css_block()` (`:2214-2215`) emits `.db-kpi-card { background-color: …;
border-color: …; }`, but the Div is written with an inline
`style="background:…; border:1px solid #dee2e6;"` (`:10484-10495`). Inline
shorthand wins, so `color legend` / `color legend_line` never reach a card.
Verified under `economist`: scheme wants `#c6d3df`, card renders `#f8f9fa`
with a `#dee2e6` border. Same in the server path (`:12977-12982`).

Similarly `:9188` hardcodes `g.grid_line_color = "#e5e5e5"` when
`xlabel(, grid)` turns on a grid the scheme left off, ignoring the scheme's
`color major_grid`.

### G7. What works — no gap

Scheme-then-option precedence is correct throughout: `apply_to_figure`
(`:9606`) runs before `_apply_marker_opts` (`:3478`), so explicit options win.
Measured: s2color two scatters → `#1a476f`/`#90353b`, circle, 8.0px;
`mcolor(red) msymbol(triangle) msize(large)` → `#ff0000`, triangle, 15px;
s2mono symbol cycle circle/diamond; s2mono line `p#lineplot` split with
dashes `[]`/`[8,4]`; stmono1 `symbolsize p small` → 5.82px; `lcolor(green)
lwidth(thick) lpattern(dash)` → `#008000`, 2.5, `[8,4]`. Grid orientation
(`draw_major_hgrid`→`xgrid`, `draw_major_vgrid`→`ygrid`) is correct.

Path traversal is **properly contained** — `_resolve_path` (`:1718-1752`)
validates both `abspath` and `realpath` against `{CWD, schemes dirs}`.
Measured: `../../../../etc/hosts.scheme` → `ValueError`; a symlink to
`/etc/passwd` → `ValueError`; an absolute path into Stata's own scheme
directory → `ValueError`.

### G8. `scheme()` warns and falls back where it could error — S3, MEASURED

`dash.ado` performs **no** validation of `scheme()`; it is escaped and passed
through verbatim (`:2341-2343`). All policy is Python-side, and it is
warn-and-fall-back, never error (`:7967-7983`, `:1589-1622`). A typo in
`scheme()` therefore produces a dashboard in the wrong scheme with a warning
buried in the log rather than a refusal.

---

## H. The interactive layer

### H1. There is no export of any kind — S2, READ

Zero occurrences of `SaveTool`, `download`, `export` or `to_csv` in
`dash_render.py`. Both toolbars are fixed:

- standalone `"pan,wheel_zoom,box_select,lasso_select,reset"` (`:9552`)
- server `[PanTool, WheelZoomTool, BoxSelectTool, LassoSelectTool, ResetTool]`
  (`:13801, 15127, 15230`)

No PNG save, no CSV download, no `BoxZoomTool`, no `UndoTool`/`RedoTool`, no
`CrosshairTool`. For a product whose output is a dashboard someone will want
to put in a paper or a deck, this is the most conspicuous single omission.

### H2. What is built — no gap

Linking/shared source (`:11300-11460`), brushing→KPI (`:11645`, server
`:15664-15732`), non-selection dimming (`:9438`, α = 0.15), cross-filter
widgets (dropdown/slider/range, `FilterBuilder:7557-7890`, 33 `CustomJS`
callbacks; server via `on_change` `:15477-15662`), tabs (`:10914, 11013`;
server `:15746-15809`, both validating names against the registry), KPI tiles
with 11 statistics and `update(filter|brush|both)`, Bootstrap 12-column and
plain-grid layouts, responsive `sizing_mode` and viewport meta.

The live-recompute-versus-JS-rescale difference between modes is real,
documented in the help's comparison table, and explicitly allowed by the
parity test.

### H3. Bootstrap layout in server mode is unverified — SUSPECTED

`_render_bootstrap_html` is standalone-only. What `layout(bs…)` does when
served needs a runtime check.

---

## I. Resource limits and security

### I1. The bounded quantities — no gap

`_MAX_BINS = 1000` (`:4725, 4767`), `_MAX_MBANDS = 1000` (`:2313`),
`_MAX_EXPR_CHARS = 5000` (`:2271`), function points capped at 10 000
(`:10056, 14824`), `_WEBGL_THRESHOLD = 10_000` (`:569`), port clamped to
`[1024, 65535]` (`:16153`).

The generated server app has a genuine per-IP sliding-window rate limiter
(`_RATE_LIMIT_RPM = 60`, `_HEALTH_LIMIT_RPM = 600`), separate buckets for
sessions and health checks, an LRU `_MAX_IPS = 10000` eviction, and a
`/health` endpoint returning 200/429 — satisfying CLAUDE.md rules 3 and 17.
It binds loopback by default.

### I2. The unbounded ones — S2, MEASURED

No constant exists for any of these — grep for
`_MAX_FILTER_OPTIONS`, `_MAX_DROPDOWN`, `_MAX_BY_GROUPS`, `_MAX_FACETS`,
`_MAX_TABS`, `_MAX_OBS`, `_MAX_ROWS`, `_MAX_GRAPHS`, `_MAX_PLOTS` returns
**0 hits each**:

- **Dropdown filters emit one `<option>` per distinct value, uncapped.**
  `build_dropdown` (`:7628-7660`) takes `set(source.data[varname])` with no
  ceiling and no warning — 200 001 options on 200 000 observations.
- **`by()` has no group cap.** `by(id)` builds one figure per value.
- **No row, column, graph or facet cap.** `_report_dataset_size`
  (`:538-567`) *warns* — its own docstring records 2 M rows → 90.6 MB of HTML
  at 1.71 GB RSS — but never refuses or truncates.
- **`_MAX_IPS` is an eviction primitive, not a limiter.** A client cycling
  10 000 forwarded keys took 300 sessions inside a 60-second window against a
  nominal 60.

### I3. Escaping — mostly solid — S3, READ

`html.escape` is applied at 20 sites (KPI title/value/subtitle, dashboard
title/subtitle, facet labels, tick-label maps, legend overrides, scheme CSS,
filter widget values with `quote=True`). Colours go further —
`_sanitize_css_color` (`:7013`) and `_resolve_kpi_color` (`:6970`) exist
because `html.escape` does not neutralise `{`/`}`/`;` inside a `style=`
attribute.

`function` expression evaluation is a real AST whitelist
(`_stata_expr_to_python:6763` → `_validate` → `compile:6173` →
`eval(code, {"__builtins__": {}}, ns):6204`), with keyword args and `*args`
rejected and int literals coerced to float to stop `9^9^9^9`. `if`
expressions go through `_stata_if_to_pandas` (`:6852`) with string-literal
masking and validation.

Remaining:

- **CSP is standalone-only** and thin: `script-src 'unsafe-inline'
  'unsafe-eval'` with no `default-src`, `object-src`, `base-uri` or
  `frame-ancestors`.
- **Hover tooltip labels are not escaped** — `:10234` appends
  `self._axis_label(col)`, a user-controlled variable label, into `tooltips`.
  Bokeh 3.x builds tooltip rows as DOM text nodes so this is almost certainly
  safe, but the safety comes from BokehJS, not from dash. **SUSPECTED** —
  worth a version-pinned check.
- `dash_setup.ado:158` interpolates `` `pkgver' `` — unsanitised distribution
  metadata — into a `python:` line as `Version("`pkgver'")`.
  `_dash_pkg_version` guards the package *name* (`:307`) but not the returned
  version string. The only unvalidated interpolation into executable Python in
  the file.

---

## J. `dash_setup` and environment verification

### J1. It reports failure and then declares success — S1, READ

`dash_setup.ado:53-57` prints "Python … version X is below the minimum" — and
there is **no `exit`**. Execution continues, installs packages against the
too-old interpreter, and ends at `:199` with:

```
dash_setup complete. All dependencies are satisfied.
```

`exit` appears only at `:37, 141, 185, 190, 309` — never on this branch.

**RESOLVED (WP-06), and the branch was never even reached.** The fall-through
is real and is fixed by a failure accumulator plus `_dash_setup_summary`. But
measuring it turned up something worse: `_dash_pyver_ok` is correct when
called from a certification script and returned **1 for every input** when
called from `dash_setup`, which declares `version 16.0` — `return scalar`
followed by `exit` inside its `forvalues` took effect under neither, so every
comparison fell through to the closing `ok = 1`. Measured: `3.7.9 >= 3.8`
gave 1, `0.9 >= 1.5` gave 1. So this branch never ran at all and the user was
told "Python ............. OK (version 3.7.9)". The comparator now decides
once and returns after the loop, and `test_setup_python_gate.cscript` gained
seven cases that call it through a `version 16.0` program — the calling
context none of its fourteen existing cases covered, which is why it passed
throughout. See the BUGS.md entries.

### J2. Version minimums are declared but never enforced by pip — S2, READ

Minimums are declared (`:106-110`) and compared with
`packaging.version.Version` (`:155-159`), but pip gets a **bare name, no
specifier** — `:123` is `pip install bokeh`, never `bokeh>=3.0`. A package
present but below minimum is warned about and **never upgraded**, and the
summary still claims all dependencies are satisfied.

Worse, if `packaging` itself failed to install, the `else` at `:169-171`
prints "OK (version unknown)" for *every* package, although
`_dash_pkg_version` already retrieved the real version. A below-minimum bokeh
is then reported as OK.

**RESOLVED (WP-06), partly, and one part corrected.** The bare pip name is
fixed: pip now receives `<pkg>>=<min>` built from the minimum declared beside
it. The "below minimum is never upgraded" half is deliberate rather than
fixed — an importable package below its minimum is now *reported as unmet*,
with the exact upgrade command printed, rather than upgraded behind the
user's back, because something else in their environment may depend on the
version they have. AC-06.2 accepts either. The `packaging`-unavailable
masking is fixed by `_dash_setup_gate` (see J6 and BUGS.md).

### J3. Python availability is probed by running Python — S2, MEASURED

`c(python_exec)` appears **nowhere** in `dash.ado` or `dash_setup.ado`.
`dash_setup.ado:32` probes with `capture python query`, and package presence
with `capture python: import …` — i.e. by running Python, contrary to the
project convention. There is no `shell` invocation of Python anywhere (pip
runs via `subprocess` *inside* `python:`), so that half of the rule holds.

`test/test_cscript_hygiene.py:12-14` enforces the rule only for `.cscript`
files, so `dash_setup.ado` is outside the net.

**RESOLVED (WP-07).** `_dash_python_ok` takes the value as an argument and
`_dash_require_python` passes it `c(python_exec)`. Split that way because the
failing state cannot otherwise be reached on a machine that has Python: `c()`
is read-only and `set python_exec` refuses a nonexistent path (measured,
r(601)). `dash_setup`'s `capture python query` is replaced by the same probe;
`python query` is kept for *reporting* the version. `test_cscript_hygiene.py`
now applies its rule to `dash.ado` and `dash_setup.ado` — enforcing it for
`.cscript` files only is how `dash_setup` kept that probe.

### J4. `dash` itself never checks that Python is available — S2, READ

`_dash_do_render` goes straight to `python:`. A user without a linked Python
gets a raw Stata Python error rather than the "run dash_setup" message the
`jsonio` check (`dash.ado:1683-1687`) gives for the other dependency.
CLAUDE.md rule 15 asks for environment verification at startup.

### J5. The Mata library's compile status is never checked — S2, READ

**RESOLVED (WP-07), and this section's account is wrong twice over.** It names
`_dash_split_segs()`; the function actually reached first is
`_dash_check_utf8()`. And "a failed Mata compile surfaces much later as
r(3499)" is only one of three measured outcomes — with one unrelated function
broken, `dash scatter mpg weight` returned **rc 0** and reported "graph
registered", which is worse, because the user has no reason to look.

ROADMAP TR-07.4's remedy — check the return code of the `run` — was measured
to be a regression. A benign *second* load returns r(3000), the same code as a
total compile failure, so vetoing on a non-zero code breaks every user and
every cscript that loads `dash_parse.mata` before `dash.ado`.

`_dash_require_mata` instead checks whether the functions dash calls are
present and, on a miss, **loads the library itself** before re-checking and
reporting. It therefore cannot false-positive, and it repairs a library
cleared by `clear all` rather than complaining about it. See the BUGS.md
entries.

`dash.ado:55` does `capture run "`_dash_matalib'"` and **discards the return
code**. A failed Mata compile therefore surfaces much later as
`_dash_split_segs() not found`, r(3499) — a message that names an internal
function and gives the user nothing to act on.

### J6. Smaller gaps — S3, READ

**RESOLVED (WP-06)** for: the missing `syntax` line (added; measured, a bare
`syntax` gives r(101), not r(198)); the uncaptured `Version(...)` (now
captured, with a fallback); the missing `--user` retry (added, tried once
after a failed install); pip output discarded on the `packaging` install (now
printed, as the package loop already did); no check that `dash_render.py` and
the schemes are reachable (added as `_dash_setup_check_files`, which asks the
RENDERER rather than `findfile`, because `findfile s2color.scheme` succeeds
on the very install where the renderer could read none); and the two sections
both numbered 3 (now 1-6). Rollback is NOT addressed and remains open.

- **`dash_setup` has no `syntax` line at all** (`:15-17`), so
  `dash_setup, garbage(1)` runs normally, silently ignoring the input.
- **No rollback**: bokeh can install before pandas fails, leaving a
  half-configured state.
- **`Version(...)` at `:155-159` has no `capture`** — an unparseable version
  string kills `dash_setup` outright with `r(7102)`.
- **No `--user` retry** on a permission-denied system Python (`:120-127`).
- `r.returncode` from pip is never checked; success is judged by re-import,
  which is the more robust choice but hides *why* an install failed.
- pip output is discarded (`capture_output=True`, `:72-73`), so a `packaging`
  install failure produces no diagnostic.
- `dash_setup` never verifies that `dash_render.py` or the schemes are
  installed and findable — which is why B1 survives a "successful" setup.
- Two sections are both numbered "3" (`:90`, `:175`).
- Idempotency is genuine — every install is guarded (`:67, 117, 177`).
- jsonio from SSC is handled correctly, with `exit 198` on either failure
  (`:177-192`).
- `_dash_pyver_ok` is **correct**, and unit-tested against the classic trap:
  `3.10 vs 3.8`→1, `3.9`→1, `3.7`→0, `3.8.0rc1`→1, `2.7`→0,
  `""`/`abc`/`3.x`→−1, `3.8.19+local`→1.

---

## K. State management

### K1. A KPI silently erases a graph of the same name — S1, MEASURED

`_dash_register_graph` (`dash.ado:1556-1575`) refuses a duplicate name unless
`name(g1, replace)` is given. **`_dash_kpi` has no such check** — it writes
its globals and appends to the registry unconditionally (`:1928-1956`).

At build time the KPI marker wins: `_dash_prepare_spec:2280` does
`if "${dash_kpi_`gname'}" != "" continue`, skipping the graph.

Measured end to end:

```
. dash scatter mpg weight, name(g1)
dash: graph 'g1' registered.
. dash kpi mean(mpg), name(g1) title("Avg")
dash: KPI 'g1' registered (mean(mpg) = 21.2972972972973).
. dash build, saving("collide_out.html") replace nobrowser
dash: dashboard saved to collide_out.html
```

`rc=0` throughout, no warning. The built file contains **0 Figure models and
0 Scatter models** — the scatter plot is gone. The graph's JSON is still in
`${dash_json_g1}`; it is simply never read.

### K2. The registry lives in user-writable globals, read back unvalidated — S3, READ

`dash_json_*`, `dash_opts_*`, `dash_graph_registry` and `dash_kpi_*` are
ordinary Stata globals, read back at `dash.ado:2038, 2159, 2167` and flowed
into the JSON spec without revalidation. A user or a stray do-file can
overwrite any of them between `dash … name()` and `dash build`. This is a
design consequence of using globals for session state rather than an
exploitable hole, but it is the one place where spec content bypasses every
input check the command applies at entry.

### K3. Graph-level option precedence across segments — RESOLVED, MEASURED

Was: "`dash.ado:1125-1133` propagates only non-empty values, so a later segment
can override an earlier one but never clear it, silently." Half right, and it
was READ off the propagation loop rather than measured.

Measured, and against `twoway`'s own answer read out of a saved `.gph`:

- A later segment DOES override an earlier one — as `twoway` does. Correct.
- A later segment CAN clear an earlier value: `title("")` blanks it, in both
  `dash` and `twoway`. The "never clear" half was wrong.
- The real divergence, which neither this entry nor TR-04.4 named: an option
  written after the top-level comma LOST to one written inside a segment.
  `twoway ... , title("AFTER")` over a segment's `title("INSIDE")` gives
  "AFTER"; `dash` gave "INSIDE", because `_dash_plot` fills the `g_*`
  accumulators from the after-comma parse first and the segment loop then
  overwrites them through `c_local`.

Fixed: after-comma values are held in `_gafter_<key>` and restored once the
segment loop has run. `test/test_graph_option_scope.cscript` (GOS-01..08).

A separate claim — that a graph-level option inside a segment is dropped
entirely — was raised against this entry and is FALSE; it came from a probe
that ran `dash clear` between registrations. See the retracted `BUGS.md` entry.

---

## L. Test coverage

The suite is large and, in several places, genuinely rigorous: **3536 pytest
tests across 84 files**, 25 `.cscript` files, all 38 plot types rendered twice
by `test_every_plot_type_draws.py`, all 14 schemes exercised, 17 real
subprocess server tests (measured: 17 passed in 19.75 s), and a runner that
tracks skips separately and exits 1 if nothing passed. On this machine only
~37 of 3536 pytest tests skip (~1.0%) and **no** cscript skips.

The gaps:

### L1. No CI, no Makefile, no pytest config — S2, MEASURED

No `.github`, `.gitlab`, `travis` or `circle` config; no `pytest.ini`,
`pyproject.toml` or `setup.cfg`. Both suites are invoked by hand. **Nothing
enforces that either runs before a commit.**

### L2. The two suites run under different interpreters — S2, MEASURED

pytest runs on `/opt/homebrew/bin/python3` 3.14.5 (bokeh 3.9.0, pandas 3.0.1);
Stata's `c(python_exec)` is `/opt/anaconda3/bin/python3` (bokeh 3.8.0, pandas
2.3.3). `conftest.py:41-52` documents this exactly and only `warnings.warn`s.
**A green pytest run does not prove the Stata path works against the libraries
it actually loads.**

### L3. The UTF-8 guard's rejection branch has never executed — S1, READ

`_dash_check_utf8` is called by exactly two tests
(`test_ado_loads.cscript:94`, `test_mata_autoload.cscript:52`) and **both pass
`""`**, which is trivially valid. The failure path (`dash_parse.mata:149-153`)
and all of `_is_utf8` (`:90-133`) are unproven. No test feeds invalid UTF-8,
overlong encodings, or surrogate halves — precisely the "string encoding to
bypass standard injection vectors" case CLAUDE.md rule 16 names, at the rule's
designated enforcement point.

### L4. Tests that assert a name exists rather than a behaviour — S2, READ

`_dash_json_get_str` — added *as the fix* for the "immediate render truncates
quoted `if` expressions" bug — is covered only by
`assert "_dash_json_get_str" in src` (`test_server.py:4694-4712, 4828-4833`).
The regression test for the fix asserts the fix's *name* exists. Same shape at
`test_paired_coordinate_plots.py:139,151` and `test_serve_options.py:71-157`,
which parse `dash.ado` as a string.

`test_server.py` is 474 KB / 423 test functions and **never starts a server** —
all coverage is `ServerAppBuilder` text/AST inspection. So ~420 "server" tests
prove the generated *source* is right and 17 prove it *runs*.

### L5. Three tests cannot fail — S2, READ

- `test_filter_label.py:155-161`, `test_a_payload_does_not_reach_the_document`:
  wraps the render in `except Exception: return`, so any exception is green;
  its `out = dr.render() if False else None` at `:159` is dead code, so the
  render it claims to inspect never runs; and it asserts only that a widget
  list is non-empty — it never checks the payload.
- `test_options.py:260-262` catches `AssertionError`, so it cannot fail by
  construction.
- `test_filters.py:209-211` swallows `ValueError`/`KeyError`.

A further 19 of 2340 test functions have no verification at all. Eleven are
honest "does not crash" cases; the rest promise more than they check —
notably `test_resource_limits.py:206`
`test_a_power_tower_does_not_hang_the_served_app`, a resource-exhaustion test
with no assertion and no timeout.

### L6. Pass conditions that go vacuously green on a wording change — S2, READ

`test_conformance.cscript:126-146` (C-03) detects failure by string-matching
`"drew nothing"` in a Stata log. `test_every_plot_type_draws.py:77-95` derives
its parametrization from a regex over the display string at `dash.ado:940-944`;
reflow that message and a type silently drops out, and the `>= 30` guard at
`:139` would not notice losing one or two.

### L7. Untested programs and functions — S2, READ

Never named in any test file: `_dash_formats_json` (`dash.ado:1266`),
`_dash_date_fmts_swap` (`:1309`), `_dash_date_fmts_restore` (`:1322`). These
three are also the only three omitted from the existence loop at
`test_ado_loads.cscript:69-77`. Format strings are user-supplied and flow into
the spec JSON.

**`dash_setup` itself is never executed** — 75 textual hits, zero invocations.

`dash serve`'s happy path: zero coverage (see C2).

### L8. Dead test assets — S3, MEASURED

15 of 17 `.do` files in `test/` are referenced by nothing
(`test_build_s3.do`, `test_r_trace{,2..6}.do`, `test_if_expr{,2}.do`, …).
`test/fixtures/scheme_visual/` (9 PNGs + `truth.json`) is referenced by zero
test files, yet `test_fixtures_are_committed.py:83-90` enforces them as
git-tracked with a docstring claiming each is "read by the test suite" —
false for these 9.

`test_scheme_fidelity.py:213-234, 721-731` asserts the parser *exposes*
`symbolsize`, `graphsize_x/y`, `legend_position`, `legend_cols` — never that
they reach rendered output. That is exactly why G4's dead attributes pass the
suite today.

`test/fixtures/abbrev_truth.json` records 7 historical option-key
mis-mappings and 18 declared options that rejected Stata's minimum
abbreviation. **All 25 were verified fixed in current code** (measured live,
reading the key back out of the emitted JSON): `xl`→`xlabel`, `yl`→`ylabel`,
`m`→`msymbol`, `mlc`→`mlcolor`, `mlw`→`mlwidth`, `mls`→`mlstyle`,
`mlp`→`mlpattern`, plus `ml c xli yli psty mlabc aspect barw cmiss colorcut
colordis colorv mlabg mlabp mlabs xt yt`. The fixture is a **stale pre-fix
record, not current behaviour**, and should say so — otherwise the next
auditor re-reports 25 resolved items as live gaps.

### L9. Bug-regression convention — S3, READ

`BUGS.md` holds 73 entries, all `[x]`. 67 name a regression test in their
Resolution; **six do not** (`BUGS.md:341, 359, 383, 395, 413, 431`), two of
which are security fixes. CLAUDE.md rule 8 asks for a test per fixed defect.

### L10. Auth bypass — not a gap

`dash` has no auth model, and `test_security_surface.py:95` establishes that
the help does not claim one. CLAUDE.md rule 19 is N/A. Worth stating
explicitly rather than leaving as an apparent hole.

---

## M. Documentation and repository hygiene

### M1. The tracking documents no longer describe reality — S2, MEASURED

`TODO.md` holds 555 items, **all checked**. `BUGS.md` holds 73, **all
closed**. Yet 39 options are inert, `dash serve` aborts on every option, and
every `net install` loses its schemes. The tracking documents and the code
disagree.

`PLAN.md` and `TODO.md` were last touched at `5f857fc`. `REMAINING.md` (198 KB)
and `phases/` (31 phase documents, 249 work items) are the current record;
the older two describe an overtaken roadmap.

### M2. Branch state — S3, MEASURED

62 commits ahead of `main`, with 53 uncommitted working-tree entries
(a `.ultraplan` reorganisation, an archive directory, and a modified
`REMAINING.md`). None of this has been merged or released.

### M3. Development artefacts in the package root — S3, READ

`regen_bootstrap_examples.py`, `regen_comprehensive.py`, `regen_dashboards.py`
and eight generated `*.html` files (1.2–2.0 MB each, ~13 MB total) sit
alongside the shippable sources. They are not in `dash.pkg`, so they do not
ship, but they dominate the repository.

### M4. Duplicated source blocks — S3, READ

The generator NOTE comment appears twice back-to-back at `dash.ado:266-275`
and again at `:459-469`. The T/B/L/R folding block is duplicated verbatim
within `_dash_parse_graph_opts` (`:316-319` and `:340-343`). The rationale
those comments give is also measurably wrong: `T1title` yields minimum
abbreviation `t`, not `t1` — measured, `_dash_parse_plot_opts , t("Top")`
resolves to `t1title` without any `T(string)` declaration, so the explicit
`T B L R` declarations at `:301-302` are redundant.

### M5. Latent `inlist()` ceiling — S3, READ

`dash.ado:1004-1005` and `:1146-1147` carry exactly 9 literals plus `ptype` —
Stata's 10-argument `inlist()` limit. **A tenth range plot type will fail to
compile.**

---

## N. Dead code

| Item | Location | Evidence |
|---|---|---|
| `_dash_graph_opts_to_json` | `dash.ado:891-913` | Zero callers. Graph JSON is assembled inline at `:1462-1480`. The dead helper emits a *smaller* key set, so it is a trap: an auditor reading it would report ~26 false inert options. |
| `_dash_kv_json` | `dash.ado:242-251` | Zero callers. |
| `_json_escape`, `_html_escape` | `dash_parse.mata:53, 71` | Called only by `_dash_json_esc`/`_dash_html_esc`… |
| `_dash_json_esc`, `_dash_html_esc` | `dash_parse.mata:82, 85` | …which have zero callers anywhere. `dash.ado` escapes in `_dash_json_str` (`:224`) instead. |
| `map_pci` | `dash_render.py:5516` | Unreachable — delegates to `map_pcspike`, which needs variable names, but `pci` is emitted as a literal `values` array. The live path is `map_pci_literal` (`:5548`). Still listed in `pc_dispatch` (`:10454`). |
| `"sc"`, `"li"`, `"hist"` dispatch aliases | `dash_render.py:10362, 10365, 10379` | Unreachable — `_expand_plottype_str` always writes the full name. |
| Scheme `#include` support | `dash_render.py:1786-1800` | Zero of the 14 shipped schemes use it. |
| The ambiguity branch in `_expand_plottype_str` | `dash_parse.mata:225` | **Unreachable.** Brute-forcing every prefix of all 38 plot-type names gives a maximum hit count of 1: the `strlen(name) >= strlen(minab)` gate at `:218` structurally suppresses the longer candidate in every colliding pair. The comment "or an ambiguous prefix" describes nothing that can happen. |
| 15 `.do` files, 9 PNG fixtures | `test/` | See L8. |

### N1. Stale file headers — S3, READ

`dash_parse.mata`'s header **lists `_dash_json_esc` and `_dash_html_esc` as
"Public API (called from dash.ado)"** at lines 34-35. Both are dead. The same
header claims at line 8 that Mata performs option-key abbreviation expansion
— that code was removed (`dash_parse.mata:239-268`); Stata's `syntax` resolves
option prefixes now. `dash.ado:14-16` repeats the same stale architecture
claim. The Public API list also omits four functions that *are* called:
`_dash_extract_filters`, `_dash_extract_qual_vars`, `_dash_option_names`,
`_dash_path_badchar`.

---

## Prioritised remediation

**Wave 1 — wrong numbers and broken installs**

1. **A6/A7** — two one-line-ish parser fixes with the worst
   consequence-to-effort ratio in the list. Drop `& depth == 0` at
   `dash_parse.mata:468, 473, 303, 308`; add quote tracking to
   `_dash_extract_filters`. Add a cert case for a paren inside a quoted
   option value, and one for `filter(` inside a quoted title.
2. **A1/A2** — pass `view` (or a pre-filtered frame) into the 13 computed
   mappers. One defect, three user-visible wrong-answer bugs, and the facet
   one produces confidently wrong statistics with no warning.
3. **B1** — make installed schemes reachable: add the PLUS letter fan-out to
   `_SCHEME_SEARCH_DIRS`, or have `dash.ado` `findfile` each scheme and pass a
   directory into the spec. Add a `net install`-and-render gate to the suite.
4. **C1** — strip the leading comma at `dash.ado:2601`, exactly as
   `_dash_build` does at `:2440`. Then give `dash serve` a happy-path test
   (C2).
5. **K1** — make `_dash_kpi` check the registry and require `replace`, as
   `_dash_register_graph` does.
6. **J1** — add `exit 198` after `dash_setup.ado:53-57`, or stop claiming
   success at `:199`.

**Wave 2 — the server-unification lever**

7. **D1** — route the server's plot dispatch through `GlyphMapper`. Once a
   type delegates, it inherits every standalone fix instead of needing its own
   copy. Doing the dependent work first means doing it twice.
8. **D2/D3/D4/D5** — `pci`, `fpfitci`, the `pc*` shared-variable cases, hover,
   per-plot and KPI qualifiers, and the facet dispatch.
9. **D8** — extend `test_mode_parity.py`'s `CORPUS` to all 38 types plus
   `by()`/`link()`/`tabs()`/KPI, and make `_glyph_profile` collect tools and
   tooltips.

**Wave 3 — honesty of the surface**

10. **A3/E2** — either honour weights, `link()`, `filter()` and named-graph
    `saving()`, or report them. Silence is the problem.
11. **E1** — take `nodraw` off both pending lists.
12. **E3** — give `by()`, `legend()` and `filter()` an unknown-sub-option
    warning; stop discarding a whole `filter()` group in silence.
13. **E4** — make the `bw` fold plot-type-aware, or drop the alias.
14. **E6/A9** — `\uXXXX`-escape all C0 controls in `_dash_json_str`; tighten
    `_is_utf8`'s second-byte ranges to reject surrogates, overlongs and
    anything above U+10FFFF; escape `theme()`; un-escape the extracted
    `saving()` path; and call `_dash_check_utf8` from `_dash_kpi`,
    `_dash_build` and `_dash_serve`.
15. **A8** — make the splitter error on an unbalanced `(` or `"` at
    end of scan, instead of silently returning one segment.

**Wave 4 — fidelity, limits, coverage**

16. **G3** — stop drawing the minor grid unconditionally.
17. **G5/G4/G6** — fix the `gsize` and `linewidth` scale factors; wire or
    remove `note_font_size`, `p_mark_colors`, `legend_position`,
    `legend_cols`; stop the inline KPI style overriding `css_block()`.
18. **I2** — add caps for dropdown cardinality, `by()` groups, facets and
    dataset size; replace `_MAX_IPS` with a structure that actually limits.
19. **L3/L5/L6** — test `_dash_check_utf8` with real invalid UTF-8; fix the
    three tests that cannot fail; replace the string-matching pass conditions.
20. **J3/J4/J5** — probe Python with `c(python_exec)` before the first
    `python:`; give `dash` the same "run dash_setup" diagnostic it gives for
    `jsonio`; check `_rc` from the Mata `run` at `dash.ado:55`.
21. **L1/L2** — add a CI config that runs both suites, and make the
    interpreter-drift warning a failure there.
22. **L8** — annotate `test/fixtures/abbrev_truth.json` as a pre-fix record,
    and fix or delete the stale file headers (N1).
23. **F4/F2/F1** — reconcile the help: fractional percentiles, `nodraw` on
    `dash build`, bare-name custom schemes, the scipy attribution, the
    semicolon claim, the `xtick()` semantics, `colorvar()`'s scatter-only
    scope, and a supported-plot-types list naming the 11 undocumented types
    and the 4 that error.
24. **N** — delete the dead code, especially `_dash_graph_opts_to_json`.

**Wave 5 — release**

25. **H1** — add a `SaveTool` to both toolbars.
26. **B4** — give `dash.pkg` a `v` line and a `Distribution-Date:`, and sync
    its version to the 2.0 the code declares.
27. **M1** — reconcile `TODO.md`, `PLAN.md` and `BUGS.md` against the code,
    or retire them in favour of `REMAINING.md` and `phases/`.
28. **G1** — translate the six missing user-selectable schemes.

---

## Appendix — environment this review ran in

| | |
|---|---|
| Stata | StataNow 19.5 (StataMP), plus Stata 14–18 present |
| Stata's Python | `/opt/anaconda3/bin/python3` — bokeh 3.8.0, pandas 2.3.3 |
| pytest's Python | `/opt/homebrew/bin/python3` 3.14.5 — bokeh 3.9.0, pandas 3.0.1, numpy 2.4.3, scipy 1.17.1, pytest 9.0.2 |
| `jsonio` | installed, `which jsonio` rc=0 |
| `statsmodels` | installed but **unimportable** in the homebrew interpreter (`ModuleNotFoundError: No module named 'packaging'`), so every `lowess` layer renders empty here |
| node | v24.13.1 |

All Stata probes were run with `global dash_nobrowser 1` set, under
`arch -arm64`, writing to the session scratchpad. No repository files were
modified by this review, and no probe artefacts were left in the tree.

One Bokeh server was started by the `dash serve` probe and was stopped; port
5006 was verified free afterwards.
