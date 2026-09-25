# Phase 30 — Documentation and help reconciliation

**Purpose.** `dash.sthlp` is a shipped artefact: it installs with the package, it is the
only documentation a Stata user ever sees, and at HEAD several of its sentences describe
behaviour the code does not have. It tells the reader that `xtick()` draws tick positions
*without* labels when the code draws labelled ones and discards `xtick()` entirely whenever
`xlabel()` is present; it justifies deferring minor ticks with a Bokeh limitation that does
not exist (Bokeh 3.9 exposes `FixedTicker.minor_ticks` and nine `minor_tick_*` axis
properties, both confirmed at HEAD) and redirects the reader to the one option that is
wrong; it claims `twoway` parity for `if`/`in` qualifiers that the parser drops; it tells
users to drop a `.scheme` file in the working directory, which is the path-traversal surface
the plan ordered retired; and it advertises the whole new axis-label grammar with no
server-mode caveat although none of that grammar reaches `dash serve`. Against those
retractions stand four capabilities the code *does* have and the help never mentions:
date-axis precedence, `hover()`, per-plot qualifier semantics, and what a qualifier does
**not** reach. This phase makes every sentence in `dash.sthlp` true at the commit where it
ships, adds the entries that are missing, records the `06-06` behaviour change in
`.ultraplan/CHANGELOG.md`, and — because prose rots silently — extends
`test/test_help_conformance.py` so each claim is checked mechanically against the code
rather than by reading two files side by side. It is nine deliverable items, all small, no
renderer work, and it is the last phase before the release gates in Phase 31.

---

## At a glance

| | |
|---|---|
| **Work items** | 9 |
| **Functional / deliverable** | 0 functional · **9 deliverable** |
| **Effort mix** | **9 small** |
| **Renderers touched** | None. `renderer: n/a` on all nine. Files touched: `dash.sthlp` (all nine), `dash.ado` (`_dash_pending` lockstep only, items 5), `.ultraplan/CHANGELOG.md` (item 8), `test/test_help_conformance.py` (the new guards) |
| **Ultraplan tasks discharged** | the documentation clauses of **06-06** (items 3, 7, 8), **08-04** (item 1), **09-02** (items 4, 5, 6), **09-07** (item 2), **11-05** (item 9) — five tasks whose `<verify>` clauses each contain a documentation half that no code change can satisfy |
| **Sections advanced** | **S06** (06-06's help + the missing CHANGELOG entry: REMAINING.md's status table records "**no S06 entry in CHANGELOG** ②"), **S08**, **S09** (`0/7/0` DONE/PARTIAL/NOT_DONE at audit), **S11** (`11-05`'s help clause), **S16** (16-01..05 done; the help must stay true for 16-06/16-07 to close) |
| **Depends on** | Every feature phase whose behaviour it documents. Items 1 and 6 depend on Phases 09/10 (dates) and 14/15/16 (axis grammar); items 3, 7, 8 on Phases 01/02 (per-plot qualifiers); item 2 on Phase 11 (`hover()`); item 4 on Phases 14/16 (`xtick()` semantics); item 5 on the phase that implements `xmtick()`/`ymtick()`/`xmlabel()`/`ymlabel()`; item 9 on Phases 03/04 (scheme reachability and the Stata-side `scheme()` error) |
| **Unblocks** | **Phase 31** — release gates 16-06 and 16-07. `test/test_help_conformance.py` is in the pytest gate, so a help sentence left out of lockstep fails the first gate, not a user's bug report |
| **Wave** | 7 (leftovers, docs and release) |

**Two of the nine can be done immediately and must not wait**: item 4 (the `xtick()`/`ytick()`
synopt) and item 5 (the minor-tick note) are *independently shipped false claims*. They are
false now, they will still be false tomorrow, and correcting the sentence does not require
the code fix to land first. The rest are lockstep items: they describe behaviour another
phase creates, and their edit belongs in that phase's commit or immediately after it.

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md` — its blocker sections, its
Appendix A measurements and the item texts from Appendices B and C. Nothing here was
inferred. Where a read-only check at HEAD confirmed or sharpened a claim, it is marked
**[confirmed at HEAD]** and the command is given.

### The pattern: five tasks each left a documentation clause unsatisfied

`REMAINING.md`'s own summary of what "PARTIAL" means across the 89 tasks:

> **Read PARTIAL carefully — it is not "half-built".** In most cases the audit
> found the defect the task was written against genuinely fixed and proven
> load-bearing by mutation, with a *secondary* deliverable missing: a cscript
> the TDD stubs named, a CHANGELOG entry, **a help sentence**, a no-caller test.

Nine such help sentences are collected here. Four are retractions (something false is
shipped), four are additions (something true is undocumented), one is a scoping caveat
(something true in one mode only).

### 1. `scheme()` — the help contradicts both the code and the binding decision

Copied verbatim from `REMAINING.md` §3:

> ## 3. Binding decision 1 is violated  [S11-05]
>
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

And from `REMAINING.md`'s suggested order, item 2:

> 2. **S11-05.** Turn the warning into a Stata-side error, retire the CWD
>    `.scheme` path, fix `dash.sthlp:1084`. Closes a binding decision and a
>    security surface together.

The help paragraph in question, **[confirmed at HEAD]** (`sed -n '1080,1085p' dash.sthlp`):

```
A name that is neither a translated scheme nor one of those aliases is
reported and {cmd:s2color} is used -- {cmd:dash} does not silently draw
something other than what you asked for.  To use a scheme {cmd:dash} does not
ship, put its Stata-format {cmd:.scheme} file in the working directory and
give its base name without the extension.
```

Both sentences are wrong once Phase 04 lands: the first describes the fallback the binding
decision forbids, the second describes the path that is being deleted.

### 2. Per-plot `if` — a parity claim the parser does not honour

Copied verbatim from `REMAINING.md` §5:

> ## 5. Blocker — per-plot `if` is ignored by every computed layer  [S06-06]
>
> `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws the fit for
> **all 74 cars**, not the 22 foreign ones. Measured, with the key `dash.ado`
> actually emits (`if_expr`, written at `dash.ado:1240` and `:1244`, read at
> `dash_render.py:9951`):
>
> | layer | per-plot `if_expr` |
> |---|---|
> | `lfit` | **ignored** — identical y to the unqualified fit |
> | `qfit` | **ignored** |
> | `kdensity` | **ignored** |
>
> Ground truth for that command, from Stata:
>
> ```
> regress mpg weight if foreign==1   ->  slope -.01042596, intercept 48.918297
> regress mpg weight                 ->  slope -.00600869, intercept 39.440284
> ```
>
> dash draws the second.

and the mechanism, which is what the help must explain (Appendix A, 06-06):

> **The Python half applies to raw-data layers only, and not to all of those.**
>
> | layer | behaviour |
> |---|---|
> | `scatter` `bar` `spike` | correct — `CDSView` + `BooleanFilter` |
> | `line` `connected` | view attached, but Bokeh raises **E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`** — filters do not apply to connected-topology glyphs, so the qualifier is **inert at runtime** and the document carries a validation error |
> | `area` | **no view attached at all** — qualifier silently dropped |
> | 12 computed layers | **ignored entirely** |
>
> The 12: `lfit` `qfit` `lfitci` `qfitci` `fpfit` `fpfitci` `lpoly` `lpolyci`
> `mband` `mspline` `histogram` `kdensity`.

The help's claim, `dash.sthlp:128-130` **[confirmed at HEAD]**:

```
For plot types, marker/line/axis options, and {it:if}/{in} qualifiers,
{cmd:dash} accepts the same syntax as {helpb twoway}.
```

And the measurement from Appendix C, 06-06:

> Measured: twoway accepts `twoway (scatter mpg weight) (scatter mpg price) if
> foreign==1` with rc=0, dash accepts the same text with rc=0 and drops the
> restriction. The only `if` example in the help (line 641-643) is the single
> un-parenthesised plot form.

Differences item 5 makes a second promise the qualifier surface breaks — `dash.sthlp:174`
**[confirmed at HEAD]**, inside the block at `:161-177`:

```
    is in the note.  Nothing is ever dropped without being named.  The full list
    is in {help dash##unsupported:Unsupported Stata twoway options}.
```

Appendix C enumerates exactly where that is false:

> both are false today for (a) a quoted-string qualifier, (b) a command-level
> qualifier written outside the parens, (c) a qualifier on any computed layer,
> (d) any qualifier in server mode.

Which layer types can never carry a qualifier is a fact about the code, not an opinion.
Appendix B, 06-06: *"map_scatteri (5370), map_pci_literal (5548) and map_function (6065)
take no `view` parameter at all — decide and document that inline-coordinate/analytic
layers cannot be qualified rather than leaving it silent."* **[confirmed at HEAD]** by
signature introspection:

```
map_scatteri     'view' in signature: False
map_pci_literal  'view' in signature: False
map_function     'view' in signature: False
map_lfit         'view' in signature: True
map_area         'view' in signature: True
map_line         'view' in signature: True
```

### 3. `xtick()`/`ytick()` — the help documents the opposite of the behaviour

Copied verbatim from `REMAINING.md`, Appendix C, 09-02:

> - **[deli · docs · S]** dash.sthlp documents xtick()/ytick() as "x-axis tick
>   positions without labels" — the opposite of what the code does. The xtick
>   semantics item (auditor item 3) names only dash_render.py; the help sentence
>   is a second, independently shipped false claim and must be corrected now or
>   fixed together with the code.     *Where:* `dash.sthlp:866-869 (the
>   xtick()/ytick() synopt entries); code side dash_render.py:9906-9913`

The code side, from Appendix B, 09-02:

> **[func · both · S]** Fix xtick()/ytick() semantics. Stata's xtick() adds
> UNLABELLED tick marks alongside the labelled ticks xlabel() (or the default)
> produces; dash treats xtick as a fallback spelling of xlabel — it draws
> LABELLED ticks at those positions, and discards xtick entirely whenever
> xlabel is also present.     *Where:* `dash_render.py:9906-9913 (`tick_key =
> "xtick" if ax_key == "xlabel" else "ytick"` then `spec =
> self._parse_axis_spec(raw_ax or raw_tick)`)`

The synopt rows, **[confirmed at HEAD]** (`sed -n '866,869p' dash.sthlp`):

```
{synopt:{cmdab:xtic:k(}{it:#}[{it:#} ...]{cmd:)}}x-axis tick positions
    without labels{p_end}
{synopt:{cmdab:ytic:k(}{it:#}[{it:#} ...]{cmd:)}}y-axis tick positions
    without labels{p_end}
```

### 4. The minor-tick deferral note — false rationale, broken redirect

Copied verbatim from `REMAINING.md`, Appendix C, 09-02:

> - **[deli · docs · S]** dash.sthlp's minor-tick deferral note gives a false
>   technical rationale and redirects users to a broken option. It says Bokeh
>   draws one tick level per axis — Bokeh 3.9 supports minor ticks directly —
>   and tells the reader that xtick() and xlabel() are honoured, when xtick() is
>   exactly the option that is wrong. This note must also be removed in lockstep
>   with dash.ado's _dash_pending entries when
>   xmtick()/ymtick()/xmlabel()/ymlabel() are implemented, or
>   test/test_help_conformance.py::test_nothing_listed_there_is_honoured fails.
>   *Where:* `dash.sthlp:1116-1119; dash.ado:381-384 and dash.ado:629-632
>   (_dash_pending); test/test_help_conformance.py:184 and :352`

The note, **[confirmed at HEAD]** (`sed -n '1116,1119p' dash.sthlp`):

```
{phang2}{ul:Minor ticks and minor labels.}
    {opt xmtick(numlist)}, {opt ymtick(numlist)},
    {opt xmlabel(numlist)}, {opt ymlabel(numlist)} — Bokeh draws one tick
    level per axis.  {cmd:xtick()} and {cmd:xlabel()} are honoured.
```

The rationale is refutable in one command. **[confirmed at HEAD]**:

```
$ python3 -c "import bokeh; from bokeh.models import FixedTicker, LinearAxis; \
  print(bokeh.__version__); print('minor_ticks' in FixedTicker.properties()); \
  print(sorted(p for p in LinearAxis.properties() if 'minor' in p))"
3.9.0
True
['minor_tick_in', 'minor_tick_line_alpha', 'minor_tick_line_cap',
 'minor_tick_line_color', 'minor_tick_line_dash', 'minor_tick_line_dash_offset',
 'minor_tick_line_join', 'minor_tick_line_width', 'minor_tick_out']
```

The `_dash_pending` entries the note must be removed in lockstep with,
**[confirmed at HEAD]** at both sites (`dash.ado:381-384` and `dash.ado:629-632`):

```
    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
    if `"`xmtick'"'  != "" local _dash_pending `"`_dash_pending' xmtick"'
    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
    if `"`ymtick'"'  != "" local _dash_pending `"`_dash_pending' ymtick"'
```

### 5. The axis grammar is advertised without a server-mode caveat

Copied verbatim from `REMAINING.md`, Appendix C, 09-02:

> - **[deli · docs · S]** dash.sthlp advertises the whole new axis_label grammar
>   and xscale(range()) with no server-mode caveat, while none of it reaches
>   `dash serve`. The help's Server Mode difference table (dash.sthlp:512-525)
>   lists what differs between the two modes and does not mention axes, so a
>   served user is told the grammar works. Either port it (auditor items 1 and
>   2) or state the limitation in the table until then.     *Where:*
>   `dash.sthlp:873-895 (axis-label grammar block), dash.sthlp:512-525 (Server
>   Mode difference table)`

What the help advertises, Appendix A, 09-02 — all of it measured working in
`DashRenderer`:

> | form | result |
> |---|---|
> | `2000(500)4000` | `FixedTicker[2000, 2500, 3000, 3500, 4000]` |
> | `2000 3000 4000` | `FixedTicker[2000, 3000, 4000]` |
> | `#5` | `BasicTicker(desired_num_ticks=5)` |
> | `minmax` | `FixedTicker[1800, 4080]` (the data bounds) |
> | `none` | `FixedTicker[]` |
> | `2000 "low" 4000 "high"` | ticks + `major_label_overrides` |
> | `, format(%9.0fc)` | `NumeralTickFormatter(format='0,0')` |
> | `, labsize(large)` | `major_label_text_font_size='15px'` |
> | `, angle(45)` | `major_label_orientation=0.7854` rad |
> | `, grid` / `, nogrid` | grid `#e5e5e5` / `None` |

and what reaches `dash serve`, from the same section:

> 3. **Server mode has no axis-label grammar at all**: `_parse_axis_label` occurs
>    4× in the renderer and **0×** in the emitted app.

The same measurement shape recurs for every other feature in this phase's blast radius
(Appendix A, 08-04 and 09-07):

| feature | occurrences in the emitted `bokeh serve` app |
|---|---|
| `DatetimeAxis`, `DatetimeTickFormatter`, `date_vars`, `numeric_formats` | **0**, 0, 0, 0 |
| `_parse_axis_label` | **0** (4× in `DashRenderer`) |
| `extra_y_ranges`, `ytitle2`, `yscale2`, `_compute_secondary_range` | **0**, 0, 0, 0 |
| `_apply_graph_filter` (per-plot and graph-level qualifiers) | **0** |

The Server Mode table that ought to say so, **[confirmed at HEAD]** at `{marker
server_mode}` (`dash.sthlp:508`), rows at `:516-528`:

```
{synopt:{it:}}                         {it:Standalone HTML}  {it:Bokeh Server}
{synopt:Requires internet / server}    No                  Yes (local)
{synopt:Shareable as a single file}    Yes                 No (.py, run with python)
{synopt:Filter widgets}                CustomJS (in-browser) Python callbacks
{synopt:KPI recomputation on filter}   Yes (JS aggregation) Yes (Python/pandas)
{synopt:Histogram recompute on filter} Bar heights only    Yes, including bin edges
{synopt:Kernel density on filter}      Yes (JS)            Yes (Python)
{synopt:Fit-line recompute on filter}  No                  Yes
{synopt:Brush/lasso KPI update}        Yes                 Yes
{synopt:{cmd:scheme()} / {cmd:theme()}}            Yes                 Yes
```

Ten rows, none about axes, dates, the secondary axis or qualifiers.

### 6. Dates work, completely, and are documented nowhere

Copied verbatim from `REMAINING.md`, Appendix A, 08-04:

> **Standalone is done**, and more completely than the task asked. All seven
> Stata date kinds produce a `DatetimeAxis` with a `DatetimeTickFormatter` tuned
> per kind (`%ty` → `%Y` at every scale; `%tm`/`%tq`/`%th` → `%b %Y` at day
> scale; `%tc` → `%d %b %H:%M`):
>
> ```
> %td %tm %tq %tw %th %ty %tc  ->  DatetimeAxis + DatetimeTickFormatter
> no "formats" key             ->  LinearAxis + BasicTickFormatter (unchanged)
> y-axis date                  ->  DatetimeAxis
> xscale(log) on a date        ->  DatetimeAxis + "dash: xscale(log) is
>                                  meaningless for the date variable 'd'"
> ```

and the backlog item, Appendix B, 08-04:

> - **[deli · docs · S]** Document the date-axis precedence in dash.sthlp: that
>   `%t*` display formats produce a datetime axis on either axis, that
>   `xscale(log)`/`yscale(log)` on a date variable is overridden by the date
>   axis and warns, and (per the section) that `%tC` is converted with the `%tc`
>   epoch without leap-second correction.     *Where:* `dash.sthlp (the
>   xscale()/yscale() and xlabel()/ylabel() option entries, and a new paragraph
>   in the options or remarks section)`

Task 08-04's own action clause, from `.ultraplan/sections/section-08-formats-dates.md`:

> `xscale(log)` on a date variable is meaningless: choose datetime, warn naming the
> variable, and **document the precedence**.

The two warning texts a user will see, **[confirmed at HEAD]** —
`dash_render.py:9562-9573` and `dash_render.py:309-316`:

```python
f"dash: xscale(log) is meaningless for the date variable "
f"'{xvar}'; drawing a date axis instead."
```

```python
"dash: %tC is a leap-second-corrected millisecond count. dash "
"converts it with the same epoch as %tc, so timestamps are off "
"by the accumulated leap seconds (up to 27 seconds for recent "
"dates). Use %tc if that matters."
```

### 7. `hover()` is accepted, does nothing, and is undocumented

Copied verbatim from `REMAINING.md`, Appendix A, 09-07:

> 1. **`hover()` is accepted and does nothing.** The decision the task demanded
>    was taken in the direction of *implement* — `dash.ado:423`/`:750` `sreturn`
>    it, it is in the option lists at `:1129`/`:1399`/`:1415`, and the renderer
>    reads it at `dash_render.py:8036` and `:10197`. But the variables it names
>    are never extracted, so they never reach the data JSON. Measured end to end
>    through Stata:
>
>    ```
>    dash scatter mpg weight, hover(price foreign) name(h1)
>    dash build, saving(hv.html) replace
>    ```
>
>    No "ignoring unsupported option(s)" note, rc 0 — and the strings `price`
>    and `foreign` occur **zero times** in the 1.2 MB of output. […] The help
>    does not document it either, which the task's `<verify>` requires.

Task 09-07's `<verify>` clause, from `.ultraplan/sections/section-09-axes-legend-titles.md`:

> the `hover()` decision is **implemented and documented**.

And the backlog item, Appendix B, 09-07:

> - **[deli · docs · S]** Document the hover() decision in the help file. The
>   task's <verify> requires the decision to be "implemented and documented";
>   hover() is not in dash.sthlp's option table.     *Where:* `dash.sthlp — the
>   only occurrence of the word is prose at :143 ("and hover tooltips
>   automatically"); no `hover(varlist)` entry in the graph-option syntax table
>   or option descriptions.`

**[confirmed at HEAD]**: `grep -n hover dash.sthlp` returns exactly one line, `:143`,
inside the Differences prose — while `grep -n hover dash.ado` returns six declaration and
carry-through sites (`:423`, `:750`, `:1129`, `:1399`, `:1415`, `:1469`).

That single prose mention is not incidental — it is why the existing conformance suite does
not already fail. `test/test_help_conformance.py:145-147` defines the weak tier:

```python
def _help_mentions(name):
    """A weaker tier: the name appears in the help at all, anywhere."""
    return re.search(r"\b%s\b" % re.escape(name), _help_text()) is not None
```

and `test_an_option_twoway_does_not_have_is_documented` (`:319`) accepts it at `:336-337`
with the comment `# named in prose: weaker, allowed`. `hover` is a dash-only option — no
`twoway` equivalent — so the help's redirect to the `twoway` manual cannot cover it, and
prose is all that stands between it and an undocumented option.

### 8. Why a documentation phase needs its own tests

The repository has already paid for reading two files side by side. From
`test/test_help_conformance.py`'s own docstring:

> Sixteen sections of work added roughly a hundred option declarations to
> `dash.ado`. The help file did not follow, and nothing made it: reading two
> files side by side is how 98 accepted options ended up undocumented, how five
> options that dash honours ended up under a heading that says they are
> unsupported, and how `xlabel()` came to be advertised with two different
> minimum abbreviations nine lines apart.

Everything in this phase is prose, and prose is exactly what that file exists to police.
Each item below therefore ships with a mechanical check, not with a reviewer's assurance.

### Where this leaves the release

`REMAINING.md`'s status table:

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 09 | Axes, legend, titles | 7 | 1 done, 6 partial ②, **73 options open** ① | largest single family; none of S09 reached `ServerAppBuilder` |
| 11 | Scheme consumption | 6 | **11-05 not done** ①, 6 partial ② | error not warning; Stata-side validation; retire `.scheme` path; **help** |
| 16 | Help, conformance, release | 7 | 16-01..05 done ③ | 16-06, 16-07 gated on §1 |

and the gates:

> full pytest · full certification suite with honest skips · conformance corpus
> (zero `r(198)`, zero dropped series, zero dropped graphs) · parity corpus ·
> clean `net install` runs every example · adversarial suite.

`test/test_help_conformance.py` runs inside the first gate. A help claim left out of
lockstep with the code fails the release, which is the correct place for it to fail.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **E30.1 — Retract what is false** | No sentence shipped in `dash.sthlp` describes behaviour `dash` does not have at that commit. Three independently shipped false claims, each fixable without waiting for its code phase. | 4, 5, 9 |
| **E30.2 — Document the qualifier, and stop over-claiming `twoway` parity** | A user who writes `if`/`in` inside a plot's parentheses can find out from the help exactly what it does, what it does not reach, and how it interacts with `link()` and `by()`; the `twoway`-parity sentence and Differences item 5 are narrowed to what the code honours; the change is recorded in the changelog. | 3, 7, 8 |
| **E30.3 — Document the new surfaces, and scope them by mode** | Date-axis precedence and `hover()` are documented option-table entries rather than undocumented behaviour, and every capability that exists only in standalone mode says so in the Server Mode table. | 1, 2, 6 |

---

## User stories

### E30.1 — Retract what is false

**US-30.1.1** — *As a Stata user pasting a `twoway` command, I want `dash.sthlp` to describe
what `xtick()` actually does, so that I do not spend an afternoon wondering why my
"unlabelled" ticks came out labelled and why adding `xlabel()` made `xtick()` vanish.*

- **Given** `dash.sthlp` at HEAD documents `xtick()` as "x-axis tick positions without
  labels" and `dash_render.py:9906-9913` treats `xtick` as a fallback spelling of `xlabel`,
  **when** I read the axis-options synopt table, **then** the entry describes the behaviour
  the code has: labelled ticks at the given positions, ignored when `xlabel()` is also
  given.
- **Given** the code side (Phase 14/16) later lands true Stata semantics — unlabelled tick
  marks alongside the labelled ones — **when** that change is committed, **then** the synopt
  entry is updated in the same commit and the conformance test that pinned the old wording
  is updated with it.

**US-30.1.2** — *As a Stata user, I want the minor-tick entry to tell me the truth about why
`xmtick()` is not implemented and what to use instead, so that I am not redirected to a
second broken option.*

- **Given** the note claims "Bokeh draws one tick level per axis" and Bokeh 3.9 exposes
  `FixedTicker.minor_ticks` and nine `minor_tick_*` axis properties, **when** I read the
  Unsupported section, **then** the entry states that minor ticks are not yet implemented
  (a `dash` limitation, not a Bokeh one) and does not offer `xtick()` as the remedy.
- **Given** `xmtick()`/`ymtick()`/`xmlabel()`/`ymlabel()` are later implemented, **when**
  their `_dash_pending` lines are deleted from `dash.ado:381-384` and `:629-632`, **then**
  the help entry is deleted in the same commit, and
  `test_help_conformance.py::test_nothing_listed_there_is_honoured` passes rather than
  failing on an option documented as unsupported that now works.

**US-30.1.3** — *As a package maintainer, I want the scheme section to name the supported
set and say nothing about loading a `.scheme` file from the working directory, so that the
help does not advertise the path-traversal surface the plan ordered retired.*

- **Given** Phase 04 makes `scheme()` a Stata-side error naming the fourteen translated
  names and deletes `_resolve_path`'s CWD branch, **when** I read `dash.sthlp`'s scheme
  section, **then** it lists the supported names, says an unsupported name is an error, and
  tells a user wanting another scheme to request a translation.
- **Given** a user greps the help for `.scheme`, **when** the phase is done, **then** no
  instruction to place a file in the working directory remains anywhere in the file.

### E30.2 — Document the qualifier, and stop over-claiming `twoway` parity

**US-30.2.1** — *As a Stata user writing an overlay, I want to know that `if` inside a
plot's parentheses binds to that plot only, so that I can predict which layers are
restricted before I read numbers off the screen.*

- **Given** the help's only qualifier example (`dash.sthlp:641-643`) is the single
  un-parenthesised form, **when** I read the qualifier documentation, **then** there is an
  overlay example — `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` — stating
  that only the second layer is restricted.
- **Given** `scatteri`, `pci` and `function` take no `view` parameter (confirmed by
  signature introspection at HEAD), **when** I read that entry, **then** those three are
  named as layer types that cannot carry a qualifier.
- **Given** the mechanism is a `CDSView` + `BooleanFilter` over the graph's shared
  `ColumnDataSource` (`dash_render.py:9957-9990`), **when** I read the entry, **then** it
  states that `link()` and filter callbacks still propagate through a qualified plot, and
  what happens inside a `by()` facet.

**US-30.2.2** — *As a Stata user copying a command from a do-file, I want the parity
sentence to be true, so that "accepts the same syntax as `twoway`" does not mean "accepts
and silently discards".*

- **Given** `twoway (scatter mpg weight) (scatter mpg price) if foreign==1` returns rc=0 in
  Stata and `dash` returns rc=0 and drops the restriction, **when** the command-level capture
  is implemented (Phases 01/02) **then** the sentence stands unchanged; **otherwise** the
  sentence is qualified to name exactly the forms `dash` honours.
- **Given** Differences item 5 promises "Nothing is ever dropped without being named",
  **when** any of the four exceptions (quoted-string qualifier, command-level qualifier
  outside the parens, qualifier on a computed layer, any qualifier in server mode) is still
  live, **then** the Differences section names it.

**US-30.2.3** — *As a package maintainer, I want the 06-06 behaviour change in
`.ultraplan/CHANGELOG.md` with before/after/evidence, so that the one section with no
changelog entry stops being the one section whose user-visible numbers changed silently.*

- **Given** `.ultraplan/CHANGELOG.md` has section headings for S07, S08, S09, S10, S11, S14,
  S15 and S16 and none for S06, **when** the qualifier work lands, **then** an S06 entry
  records the before value (`regress mpg weight` slope `-.00600869`), the after value
  (`regress mpg weight if foreign==1` slope `-.01042596`) and the evidence, in the shape the
  existing entries use.

### E30.3 — Document the new surfaces, and scope them by mode

**US-30.3.1** — *As a Stata user plotting a time series, I want the help to tell me that a
`%t*` display format produces a date axis and that `xscale(log)` loses to it, so that the
warning on my console is something I was told about rather than something I discover.*

- **Given** all seven date kinds produce a `DatetimeAxis` with a per-kind
  `DatetimeTickFormatter` on either axis, **when** I read the `xlabel()`/`ylabel()` and
  `xscale()`/`yscale()` entries, **then** the precedence is stated: date format wins, a date
  axis is drawn, `log` is dropped and named in a warning.
- **Given** `%tC` is converted with the `%tc` epoch, **when** I read the date paragraph,
  **then** it says timestamps are off by the accumulated leap seconds (up to 27 seconds for
  recent dates) and that `%tc` should be used if that matters.

**US-30.3.2** — *As a dashboard viewer, I want the variables shown in a tooltip to be the
ones the analyst asked for, and as the analyst I want `hover(varlist)` to appear in the
option table so I can find it at all.*

- **Given** `hover()` is accepted by `dash.ado` at six sites and read by the renderer at
  `dash_render.py:8036` and `:10197`, **when** I read the graph-option synopt table, **then**
  `hover(varlist)` has an entry describing that the named variables are added to every
  layer's tooltip.
- **Given** the only occurrence of the word today is prose at `:143`, **when** the entry is
  added, **then** `hover` satisfies the strict documentation tier and not merely
  `_help_mentions`.

**US-30.3.3** — *As a `dash serve` operator, I want the Server Mode difference table to tell
me which options do not reach the served app, so that I do not ship a dashboard whose axis
labels, dates and secondary axis silently differ from the HTML I tested.*

- **Given** `_parse_axis_label` occurs 0× in the emitted app, **when** I read the Server Mode
  table, **then** a row states that the `xlabel()`/`ylabel()` grammar and `xscale(range())`
  are standalone-only.
- **Given** `DatetimeAxis`, `extra_y_ranges` and `_apply_graph_filter` each occur 0× in the
  emitted app, **when** I read the table, **then** date axes, the secondary axis and
  per-plot qualifiers each have a row.
- **Given** a later phase ports one of those features, **when** the port lands, **then** the
  corresponding row is deleted in the same commit and the mode-parity guard covers it
  instead.

---

## Business requirements

Each is testable; the test that establishes it is named in the test plan.

| ID | Requirement |
|---|---|
| **BR-30.1** | No sentence in `dash.sthlp` may describe behaviour `dash` does not have at the commit where the help ships. The four claims named in this phase (`xtick()`/`ytick()` semantics, the minor-tick rationale, the `twoway` `if`/`in` parity sentence, the CWD `.scheme` instruction) are each either corrected or removed. |
| **BR-30.2** | Every option `dash` honours that `twoway` does not have must appear in an option table in `dash.sthlp`, not only in prose. This phase applies it to `hover(varlist)`; the rule is enforced for the whole dash-only surface. |
| **BR-30.3** | Where a documented capability exists in standalone HTML and not in `dash serve`, the Server Mode difference table (`dash.sthlp:508-528`) must carry a row saying so. A capability with zero occurrences in the emitted app and no row is a defect. |
| **BR-30.4** | Documentation lands in lockstep with the code it documents. An option removed from `_dash_pending` in `dash.ado` must lose its Unsupported-section entry in the same commit, and vice versa. |
| **BR-30.5** | Every behaviour change a user can already have seen is recorded in `.ultraplan/CHANGELOG.md` with before, after and evidence — the shape the existing S07–S16 entries use. S06 gains its missing entry. |
| **BR-30.6** | A user who pastes a `twoway` command gets either `twoway`'s result or a difference documented in `dash.sthlp`'s Differences section. Silent divergence is a defect, and "Nothing is ever dropped without being named" must be literally true of the qualifier surface or be narrowed. |
| **BR-30.7** | Each of the five ultraplan tasks whose `<verify>` clause contains a documentation half (06-06, 08-04, 09-02, 09-07, 11-05) can be closed only when that half is satisfied and mechanically checked. |
| **BR-30.8** | The help never advertises a remedy that is itself broken. A deferral note may not redirect the reader to an option listed in this programme as defective. |

---

## Technical requirements

Mechanism, files, symbols and exact line numbers. Line numbers are those `REMAINING.md`
gives (current at the audit commit) unless marked **[HEAD]**, where a read-only check in
this session located the text. Plan-file line numbers are stale by design — the renderer
grew from ~10,455 to ~16,000 lines — and are marked as such where quoted.

### E30.1 — Retract what is false

**TR-30.1 — `xtick()`/`ytick()` synopt rows.** Edit `dash.sthlp:866-869` **[HEAD: the two
`{synopt:{cmdab:xtic:k(}…}` / `{cmdab:ytic:k(}…}` rows inside `{marker axis_options}` at
`:826`]**. The current text reads "x-axis tick positions / without labels" and "y-axis tick
positions / without labels". The code is `dash_render.py:9906-9913`:

```python
tick_key = "xtick" if ax_key == "xlabel" else "ytick"
spec = self._parse_axis_spec(raw_ax or raw_tick)
```

`raw_ax or raw_tick` is the whole defect in one expression: `xtick` is parsed by the same
`_parse_axis_spec` as `xlabel`, so it produces **labelled** ticks, and it is evaluated only
when `raw_ax` is empty, so it is **discarded whenever `xlabel()` is present**. Two
acceptable exits, in this order of preference:

- **(a) Lockstep with the code.** Phases 14/16 implement Stata semantics (`xtick()` adds
  unlabelled marks alongside whatever `xlabel()` or the default produces; a tick-only path
  in `_apply_axis_spec`, `dash_render.py:9112`). The synopt text then becomes true as
  written and only the "discarded when `xlabel()` is present" clause needs no mention.
- **(b) Ship the truth now.** If this phase runs first, the rows become "tick positions,
  drawn **with** labels; ignored when `xlabel()` is given" and a `{phang2}` note records
  that Stata's unlabelled-tick semantics are not yet implemented. The wording changes again
  under (a); the conformance test written for it changes with it.

Do not leave the current wording under either exit.

**TR-30.2 — the minor-tick note.** Edit `dash.sthlp:1116-1119` **[HEAD: confirmed, inside
`{marker unsupported}` at `:1092`]**. Remove the false rationale — Bokeh 3.9.0 exposes
`FixedTicker.minor_ticks` and nine `minor_tick_*` properties on `LinearAxis`, so "Bokeh
draws one tick level per axis" is refuted by one import — and remove the redirect to
`xtick()`, which TR-30.1 establishes is the wrong option. The replacement states that
`xmtick()`, `ymtick()`, `xmlabel()` and `ymlabel()` are accepted and reported as ignored,
that this is a `dash` limitation, and (once TR-30.1(a) lands) that `xlabel()` is the
working alternative — `xlabel()` alone, not `xtick()`.

**TR-30.3 — the minor-tick lockstep.** The four options are named in `_dash_pending` at two
sites, **[HEAD: confirmed]** `dash.ado:381-384` (`_dash_parse_plot_opts`) and
`dash.ado:629-632` (`_dash_parse_graph_opts`), one line each in the form:

```
if `"`xmtick'"' != "" local _dash_pending `"`_dash_pending' xmtick"'
```

`test/test_help_conformance.py:180-188` scans them with

```python
def _pending(prog):
    src = _ado_text()
    i = src.index("program define " + prog)
    j = src.index("local _dash_unknown", i)
    return set(re.findall(r"_dash_pending' (\w+)\"", src[i:j]))
```

and `:352 test_nothing_listed_there_is_honoured` asserts `listed - ignored` is empty. So
deleting the `_dash_pending` lines without deleting the help entry fails that test, and
deleting the help entry without deleting the `_dash_pending` lines fails its sibling
`:362 test_everything_dash_ignores_is_listed_there`. The two files are already
interlocked — this TR is the instruction to respect the interlock, in both directions, in
one commit.

**TR-30.4 — the scheme section.** Three edits, tracked against task 11-05's own action
clause (line numbers in that clause are the plan's and are stale; the **[HEAD]** locations
are given beside each):

| 11-05's claim | plan cite | **[HEAD]** location | edit |
|---|---|---|---|
| CWD `.scheme` loading | `:708-713` | `dash.sthlp:1080-1085`, the paragraph beginning "A name that is neither a translated scheme…" | delete the instruction to "put its Stata-format `.scheme` file in the working directory"; replace with the fourteen supported names and "request a translation" |
| the fallback sentence | — | same paragraph, first sentence ("…is reported and `s2color` is used") | replace: an unsupported name is now a Stata-side **error** naming the set |
| `dark` "does not exist" | `:248` | theme alias list at `dash.sthlp:289-290`; expansion at `:1076` (`{cmd:dark} is {cmd:s1rcolor}`) | **[HEAD] verify only.** `s1rcolor.scheme` is one of the fourteen files in `schemes/`, and `dark` is documented as an alias for it, matching `_THEME_SCHEME_MAP`. Phase 04's TR-04.8 reaches the same conclusion: this half needs no edit. Do not delete `dark`; confirm the alias list equals `_THEME_SCHEME_MAP` under TR-30.12 |
| `scheme()` "fully supported" | `:161-162` | `dash.sthlp:176-177` | **[HEAD] verify only.** Phase 04's TR-04.8 records that once `scheme()` errors on an unsupported name the sentence is accurate and stays. Re-check after Phase 04 lands; change only if that phase's outcome differs |

The shipped scheme set, **[HEAD]** `ls schemes/`: `economist` `s1color` `s1mono` `s1rcolor`
`s2color` `s2gcolor` `s2mono` `sj` `stcolor` `stcolor_alt` `stgcolor` `stmono1` `stmono2`
`stsj` — fourteen.

**TR-30.5 — no duplicate, no gap, with Phase 04.** Phase 04 TR-04.8 already assigns the
`dash.sthlp:1084` deletion as part of the code change, because a security-surface removal
whose documentation lags is a documented attack surface. That is the right home. This
phase's item 9 therefore has two states: if Phase 04 made the edit in lockstep, item 9 is
**verification plus the mechanical guard** (TR-30.12); if Phase 04 shipped code only, item 9
**makes the edit**. It must not be done twice and it must not be dropped on the assumption
the other phase did it — check `git log -p -- dash.sthlp` for the scheme paragraph before
editing.

### E30.2 — the qualifier and the parity claim

**TR-30.6 — the per-plot qualifier entry.** Add to `dash.sthlp` a qualifier entry covering
five facts, each traceable to a measured line in `REMAINING.md`:

1. **Binding.** An `if`/`in` written inside a plot's parentheses restricts that plot only.
   A single-plot command still promotes its qualifier to graph level —
   `dash.ado:1483`/`:1496` promote a lone segment's qualifier `if n_segs == 1`, where
   `_apply_graph_filter` filters the data outright.
2. **Mechanism, and why it matters to the user.** The restriction is a `CDSView` +
   `BooleanFilter` over the graph's shared `ColumnDataSource`
   (`dash_render.py:9957-9990`), not a pre-filtered private source, *so that `link()` and
   the filter callbacks still propagate through a qualified plot*. This is the interaction
   task 06-06 names explicitly: *"a linked graph keeps its qualifier via a `CDSView` +
   `BooleanFilter` rather than by filtering the source, so brushing still propagates (commit
   `963e3d6`). Per-plot qualifiers must use the same mechanism, not a pre-filtered source,
   or linking breaks."*
3. **`by()`.** Every panel of a linked `by()` graph carries the restriction as a view
   (`dash_render.py:11465-11476`); state that a qualifier narrows each facet rather than
   removing facets.
4. **Layers that cannot be qualified.** `scatteri`, `pci` and `function`.
   **[HEAD confirmed]** `map_scatteri`, `map_pci_literal` and `map_function` accept no
   `view` parameter, while `map_lfit`, `map_area` and `map_line` do. These are
   inline-coordinate and analytic layers with no rows to restrict; Appendix B's instruction
   is to "decide and document that … rather than leaving it silent".
5. **Computed layers.** Once Phases 01/02 land, a qualifier on `lfit`, `qfit`, `lfitci`,
   `qfitci`, `fpfit`, `fpfitci`, `lpoly`, `lpolyci`, `mband`, `mspline`, `histogram` or
   `kdensity` **re-estimates on the subset** — it is not a post-hoc filter of a fit computed
   on all rows. Say so: it is the difference between slope `-.01042596` and `-.00600869`.

The existing example block at `dash.sthlp:641-643` **[HEAD confirmed]** gains an overlay
companion:

```
{pstd}{ul:If qualifier}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight if foreign == 1, saving(foreign.html)}{p_end}
```

**TR-30.7 — the `twoway`-parity sentence.** `dash.sthlp:128-130` **[HEAD confirmed]**. The
measurement: `twoway (scatter mpg weight) (scatter mpg price) if foreign==1` → rc=0,
restriction applied; `dash` with the same text → rc=0, restriction **dropped**. The cause is
in `dash_parse.mata:_dash_split_segs` (`355`; paren branch `386-441`), whose PAREN branch
acts only on `(`, `)` and a depth-0 `,`, so the depth-0 `if` clause after the last group
falls through `i++` and is lost. Two exits, matching the two the item gives:

- **(a)** Phases 01/02 implement the command-level capture (`_cmd_qualifier` handed to
  `_dash_plot` at `dash.ado:1377`, written to the graph-level `if_expr`/`in_expr`), and the
  sentence stands.
- **(b)** Until then, the sentence is qualified: name the forms `dash` honours (a qualifier
  on a single un-parenthesised plot; a qualifier inside a plot's parentheses) and the form
  it does not (a command-level qualifier written after the last `)`), and note that the
  backlog's interim instruction is that `dash` "should at minimum error rather than accept
  silently".

**TR-30.8 — Differences item 5.** `dash.sthlp:162-177` **[HEAD: the block at `:161-177`,
with the promise at `:174`]** says "Nothing is ever dropped without being named". Add a
Differences-from-`twoway` entry that either removes each exception or names it. The four,
verbatim from Appendix C: **(a)** a quoted-string qualifier — `dash.ado:1224-1225` call
`_dash_json_str "`if_expr'"` with plain double quotes against the helper's documented usage
at `dash.ado:221`, so a `"` in the value re-tokenizes and truncates the escaped text;
**(b)** a command-level qualifier written outside the parens (TR-30.7); **(c)** a qualifier
on any computed layer; **(d)** any qualifier in server mode — `_apply_graph_filter` occurs
**0** times in the emitted app. Each exception that is still live when this phase ships gets
a sentence; each one a feature phase closes gets its sentence deleted in that phase's
commit (BR-30.4).

**TR-30.9 — the S06 changelog entry.** `.ultraplan/CHANGELOG.md` **[HEAD]** carries
`## S07`, `## S08`, `## S09`, `## S10`, `## S11`, `## S14`, `## S15`, `## S16` plus five
thematic sections, and **no S06 heading** — matching `REMAINING.md`'s status row for section
06 (*"**no S06 entry in CHANGELOG** ②"*). Add one in the established shape: a "Changed
behaviour" table with `layer | before | after | evidence` columns, and a "Bugs fixed"
prose block. The row that matters:

| layer | before | after | evidence |
|---|---|---|---|
| `lfit` under a per-plot `if` | fit computed on all 74 rows — slope `-.00600869`, intercept `39.440284` | fit re-estimated on the qualified subset — slope `-.01042596`, intercept `48.918297` | `regress mpg weight if foreign==1` in Stata; `REMAINING.md` §5 |

with the same treatment for `qfit`, `kdensity` and the rest of the twelve, and a note that
`area` gained the view it never had and that `line`/`connected` no longer emit Bokeh
validation error **E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`**.

### E30.3 — new surfaces and mode scoping

**TR-30.10 — the date paragraph.** Add to the `xlabel()`/`ylabel()` and
`xscale()`/`yscale()` entries, plus a paragraph in the options or remarks section
(the *Where* the backlog item gives). Content, all measured in Appendix A, 08-04:

| fact | measured value |
|---|---|
| which formats trigger a date axis | `%td %tm %tq %tw %th %ty %tc` → `DatetimeAxis` + `DatetimeTickFormatter` |
| absent-key path | no `formats` key → `LinearAxis` + `BasicTickFormatter`, unchanged |
| either axis | a y-axis date variable → `DatetimeAxis` |
| per-kind formatter | `%ty` → `%Y` at every scale; `%tm`/`%tq`/`%th` → `%b %Y` at day scale; `%tc` → `%d %b %H:%M` |
| precedence over `log` | `xscale(log)` on a date → `DatetimeAxis` plus the warning `dash: xscale(log) is meaningless for the date variable 'd'` |
| `%tC` | converted with the `%tc` epoch; **[HEAD]** `dash_render.py:309-316` warns that timestamps are off by the accumulated leap seconds, "up to 27 seconds for recent dates" |

**[HEAD]** the eight kinds the classifier recognises are `td tc tC tw tm tq th ty`
(`_STATA_DATE_KINDS`, `dash_render.py:165`); `_datetime_formatter_for`
(`dash_render.py:247-268`) groups them exactly as the measured table above describes. The
help paragraph should be written against those groupings so that TR-30.13's test can hold it
to them.

**TR-30.11 — the `hover(varlist)` entry.** Add a synopt row to the graph-option table and a
description. The option's real wiring, so the entry is accurate: declared and `sreturn`ed at
`dash.ado:423` (plot level) and `:750` (graph level, as `g_hover`), carried in the option
lists at `:1129`, `:1399`, `:1415`, `:1469`, and read by the renderer at
`dash_render.py:8036` and `:10197`. Until Phase 11 adds `hover` to the key scan in
`_dash_extract_vars` (`dash_parse.mata:537`, keys vector at `:545-551`), the named variables
never reach the data JSON — measured: `dash scatter mpg weight, hover(price foreign)` then
`dash build` produced 1.2 MB of output containing the strings `price` and `foreign`
**zero** times, with rc 0 and no "ignoring unsupported option(s)" note. **The help entry must
not ship before that fix**, or BR-30.1 is violated by the very item meant to satisfy
BR-30.2; documenting an inert option is worse than leaving it undocumented, because the
"ignoring unsupported option(s)" note no longer covers it. Sequence: Phase 11's code, then
item 2, in that order, ideally in the same commit.

**TR-30.12 — Server Mode difference rows.** Extend the table at `dash.sthlp:512-525`
**[HEAD: `{marker server_mode}` at `:508`, ten rows at `:516-528`]**. Minimum rows, each
justified by a zero-occurrence measurement in the emitted app (everything after
`class ServerAppBuilder`, `dash_render.py:12265`):

| new row | Standalone | Bokeh Server | evidence |
|---|---|---|---|
| `xlabel()`/`ylabel()` grammar (`#N`, `minmax`, `none`, `a(b)c`, `format()`, `labsize()`, `angle()`, `grid`) | Yes | No | `_parse_axis_label` 4× in `DashRenderer`, **0×** emitted |
| `xscale(range())` / `yscale(range())` | Yes | No | emitted app still reads the dead `xrange`/`yrange` keys at `dash_render.py:13907-13920`; only `log` and `reverse` are handled at `:13851-13866` |
| Date axes from `%t*` formats | Yes | No | `DatetimeAxis` 0, `DatetimeTickFormatter` 0, `date_vars` 0, `numeric_formats` 0 |
| Secondary axis (`yaxis(2)`/`xaxis(2)`) | Yes | No | `extra_y_ranges` 0, `ytitle2` 0, `yscale2` 0, `_compute_secondary_range` 0 |
| Per-plot `if`/`in` qualifier | Yes | No | `_apply_graph_filter` 0 |

Each row is **temporary by construction**: Phase 16 ports the axis grammar, Phase 10 the
dates, Phase 27 the secondary axis, Phase 02 the qualifier. The phase that ports a feature
deletes its row and extends `test/test_mode_parity.py` to cover it instead (BR-30.4). A row
whose feature has landed is itself a BR-30.1 violation, which is why TR-30.14 makes the
table mechanically checkable rather than a comment.

### Cross-cutting: the guards

**TR-30.13 — extend `test/test_help_conformance.py`, do not start a new file.** The file
already owns this contract, already parses both sides, and is already in the pytest gate.
Its reusable machinery: `_help_text()`, `_help_options()`, `_ado_declarations()`,
`_ignored_options()`, `_unsupported_section()`, `_pending(prog)`, `_help_mentions(name)`,
`_twoway_options()` (backed by `test/fixtures/abbrev_truth.json`), and the marker-based
section slicing used by `_unsupported_section` (`h.index("{marker unsupported}")` →
`h.index("{marker dependencies}")`). New classes follow the existing naming style
(`TestTheUnsupportedSectionIsTrue`, `TestEveryDashOnlyOptionIsDocumented`, …).

**TR-30.14 — prefer introspection to string matching.** A test that greps the help for a
sentence dies the moment someone rewords it, and passes forever if the code changes. Three
of this phase's guards can be written against the code instead:

- **Unqualifiable layers** — introspect `GlyphMapper.map_*` signatures; any mapper without a
  `view` parameter must be named in the help's qualifier entry. Today that is
  `map_scatteri`, `map_pci_literal`, `map_function`.
- **Date kinds** — iterate `_STATA_DATE_KINDS` (`dash_render.py:165`); each kind must appear
  in the help's date paragraph.
- **Server Mode rows** — for each feature symbol in a small table (`_parse_axis_label`,
  `DatetimeAxis`, `extra_y_ranges`, `_apply_graph_filter`), count occurrences in the emitted
  app source and require a table row **iff** the count is zero.

**TR-30.15 — a strict documentation tier.** `_help_mentions` is deliberately weak
(`test_help_conformance.py:145-147`) and is what lets `hover` pass on one prose word at
`:143`. Add a strict tier: a named set of dash-only options — starting with `hover` — that
must appear in an **option table**, i.e. in `_help_options()`, not merely in the text. Keep
the weak tier for the rest; the point is to stop `hover`'s prose mention from certifying its
own documentation.

---

## Work items

All nine items are reproduced with the number they carry in the phase assignment. Every one
is `kind: deliverable`, `renderer: n/a`, `effort: small`.

### 1. Document the date-axis precedence

> Document the date-axis precedence in dash.sthlp: that `%t*` display formats produce a
> datetime axis on either axis, that `xscale(log)`/`yscale(log)` on a date variable is
> overridden by the date axis and warns, and (per the section) that `%tC` is converted with
> the `%tc` epoch without leap-second correction.

- **Tags:** deliverable · `n/a` · **small** · origin **08-04** (Appendix B)
- **Where:** `dash.sthlp` (the `xscale()`/`yscale()` and `xlabel()`/`ylabel()` option
  entries, and a new paragraph in the options or remarks section)
- **Evidence:** Appendix A, 08-04 — *"Standalone is done, and more completely than the task
  asked. All seven Stata date kinds produce a `DatetimeAxis` with a `DatetimeTickFormatter`
  tuned per kind"*; the measured block `%td %tm %tq %tw %th %ty %tc -> DatetimeAxis +
  DatetimeTickFormatter`, `no "formats" key -> LinearAxis + BasicTickFormatter (unchanged)`,
  `y-axis date -> DatetimeAxis`, `xscale(log) on a date -> DatetimeAxis + "dash: xscale(log)
  is meaningless for the date variable 'd'"`. 08-04's action clause: *"document the
  precedence"*.
- **Requirements:** TR-30.10, TR-30.13, TR-30.14
- **Depends on:** Phase 09 (standalone dates, already true at HEAD) for the primary-axis
  text; Phase 10 for any secondary-axis sentence; interacts with item 6's date row.

### 2. Document the `hover()` decision

> Document the hover() decision in the help file. The task's <verify> requires the decision
> to be "implemented and documented"; hover() is not in dash.sthlp's option table.

- **Tags:** deliverable · `n/a` · **small** · origin **09-07** (Appendix B)
- **Where:** `dash.sthlp` — the only occurrence of the word is prose at `:143` ("and hover
  tooltips automatically"); no `hover(varlist)` entry in the graph-option syntax table or
  option descriptions.
- **Evidence:** Appendix A, 09-07 — the option is accepted (`dash.ado:423`/`:750` `sreturn`,
  lists at `:1129`/`:1399`/`:1415`) and read (`dash_render.py:8036`, `:10197`), but the
  variables never reach the data JSON: `dash scatter mpg weight, hover(price foreign)` then
  `dash build` gave rc 0, no ignore note, and the strings `price`/`foreign` **zero** times in
  1.2 MB of output. 09-07's `<verify>`: *"the `hover()` decision is implemented and
  documented"*.
- **Requirements:** TR-30.11, TR-30.15
- **Depends on:** **Phase 11** — the entry must not ship while the option is inert.

### 3. Document the per-plot qualifier

> Document the per-plot qualifier in dash.sthlp: that `if`/`in` written inside a plot's
> parentheses binds to that plot, what happens under `link()` and `by()`, and which layer
> types cannot be qualified (scatteri, pci, function). The help's only qualifier example is
> the single-plot form.

- **Tags:** deliverable · `n/a` · **small** · origin **06-06** (Appendix B)
- **Where:** `dash.sthlp:641-643` ('If qualifier' example block), `dash.sthlp:129`
- **Evidence:** Appendix B, 06-06 — *"map_scatteri (5370), map_pci_literal (5548) and
  map_function (6065) take no `view` parameter at all — decide and document that
  inline-coordinate/analytic layers cannot be qualified rather than leaving it silent"*
  (**[HEAD] confirmed** by signature introspection). §5 gives the mechanism: a
  `CDSView`/`BooleanFilter` over the graph's shared `ColumnDataSource`
  (`dash_render.py:9957-9990`), chosen so `link()` and the filter callback keep reaching the
  layer.
- **Requirements:** TR-30.6, TR-30.13, TR-30.14
- **Depends on:** Phases 01/02 for clauses 4 and 5 of TR-30.6; the `link()`/`by()` and
  unqualifiable-layer clauses are true at HEAD and can ship earlier.

### 4. Correct the `xtick()`/`ytick()` synopt entries

> dash.sthlp documents xtick()/ytick() as "x-axis tick positions without labels" — the
> opposite of what the code does. The xtick semantics item (auditor item 3) names only
> dash_render.py; the help sentence is a second, independently shipped false claim and must
> be corrected now or fixed together with the code.

- **Tags:** deliverable · `n/a` · **small** · origin **09-02** (Appendix C)
- **Where:** `dash.sthlp:866-869` (the `xtick()`/`ytick()` synopt entries); code side
  `dash_render.py:9906-9913`
- **Evidence:** the code is `tick_key = "xtick" if ax_key == "xlabel" else "ytick"` followed
  by `spec = self._parse_axis_spec(raw_ax or raw_tick)` — the same parser as `xlabel`, hence
  labelled ticks, and `or` semantics, hence discarded when `xlabel()` is present. Appendix
  B, 09-02: *"Stata's xtick() adds UNLABELLED tick marks alongside the labelled ticks
  xlabel() (or the default) produces; dash treats xtick as a fallback spelling of xlabel."*
- **Requirements:** TR-30.1
- **Depends on:** nothing. **Runnable immediately** under exit (b); revisited under Phases
  14/16 exit (a).

### 5. Fix the minor-tick deferral note

> dash.sthlp's minor-tick deferral note gives a false technical rationale and redirects users
> to a broken option. It says Bokeh draws one tick level per axis — Bokeh 3.9 supports minor
> ticks directly — and tells the reader that xtick() and xlabel() are honoured, when xtick()
> is exactly the option that is wrong. This note must also be removed in lockstep with
> dash.ado's _dash_pending entries when xmtick()/ymtick()/xmlabel()/ymlabel() are
> implemented, or test/test_help_conformance.py::test_nothing_listed_there_is_honoured fails.

- **Tags:** deliverable · `n/a` · **small** · origin **09-02** (Appendix C)
- **Where:** `dash.sthlp:1116-1119`; `dash.ado:381-384` and `dash.ado:629-632`
  (`_dash_pending`); `test/test_help_conformance.py:184` and `:352`
- **Evidence:** **[HEAD] confirmed** — `bokeh 3.9.0`, `'minor_ticks' in
  FixedTicker.properties()` is `True`, and `LinearAxis` carries nine `minor_tick_*`
  properties. The `_dash_pending` lines exist at both cited sites; `_pending()` at
  `test/test_help_conformance.py:180-188` scans them and `test_nothing_listed_there_is_honoured`
  at `:352` is the interlock.
- **Requirements:** TR-30.2, TR-30.3, TR-30.8 (shares the "never redirect to a broken
  remedy" rule, BR-30.8)
- **Depends on:** nothing for the rationale and redirect fix (**runnable immediately**);
  lockstep with whichever phase implements the four minor-tick options.

### 6. Add the server-mode caveat for the axis grammar

> dash.sthlp advertises the whole new axis_label grammar and xscale(range()) with no
> server-mode caveat, while none of it reaches `dash serve`. The help's Server Mode
> difference table (dash.sthlp:512-525) lists what differs between the two modes and does not
> mention axes, so a served user is told the grammar works. Either port it (auditor items 1
> and 2) or state the limitation in the table until then.

- **Tags:** deliverable · `n/a` · **small** · origin **09-02** (Appendix C)
- **Where:** `dash.sthlp:873-895` (axis-label grammar block), `dash.sthlp:512-525` (Server
  Mode difference table)
- **Evidence:** Appendix A, 09-02 remaining item 3 — *"Server mode has no axis-label grammar
  at all: `_parse_axis_label` occurs 4× in the renderer and **0×** in the emitted app."*
  Appendix B, 09-02 adds the range half: the emitted app still reads the dead
  `xrange`/`yrange` keys (`dash_render.py:13907-13920`) and handles only `log` and `reverse`
  (`:13851-13866`), *"so the task's 'do not leave both' was satisfied in DashRenderer and
  neither option was taken in ServerAppBuilder"*. The neighbouring zero counts (dates,
  secondary axis, qualifiers) justify extending the same row set.
- **Requirements:** TR-30.12, TR-30.14
- **Depends on:** nothing to add the rows; **each row is deleted by** Phase 16 (grammar),
  Phase 10 (dates), Phase 27 (secondary axis), Phase 02 (qualifiers).

### 7. Qualify the `twoway`-parity sentence and add an overlay example

> dash.sthlp states a twoway-parity claim for if/in that the code does not honour, and never
> documents per-plot qualifier semantics. Line 128-130: "For plot types, marker/line/axis
> options, and {it:if}/{in} qualifiers, {cmd:dash} accepts the same syntax as {helpb
> twoway}." Measured: twoway accepts `twoway (scatter mpg weight) (scatter mpg price) if
> foreign==1` with rc=0, dash accepts the same text with rc=0 and drops the restriction. The
> only `if` example in the help (line 641-643) is the single un-parenthesised plot form.
> Either implement the command-level capture and keep the sentence, or qualify the sentence
> and add an overlay example showing that a qualifier written inside a paren group binds to
> that layer only — and state which layer types cannot honour one.

- **Tags:** deliverable · `n/a` · **small** · origin **06-06** (Appendix C)
- **Where:** `dash.sthlp:128-130` (twoway-parity sentence), `dash.sthlp:641-643` ("If
  qualifier" example block)
- **Evidence:** the rc=0-both-ways measurement above; the parser cause in
  `dash_parse.mata:_dash_split_segs` (`355`, paren branch `386-441`), whose depth-0
  non-`,` text falls through `i++`.
- **Requirements:** TR-30.7, TR-30.6
- **Depends on:** Phases 01/02 (exit (a)); shippable now under exit (b).

### 8. Correct the parity claim, add a Differences entry, record the changelog

> Correct the help text, which currently asserts a parity this task has not achieved, and
> record the section in the changelog. `dash.sthlp:129-131` says "For plot types,
> marker/line/axis options, and if/in qualifiers, dash accepts the same syntax as twoway",
> and Differences item 5 (dash.sthlp:~162-177) says "Nothing is ever dropped without being
> named" — both are false today for (a) a quoted-string qualifier, (b) a command-level
> qualifier written outside the parens, (c) a qualifier on any computed layer, (d) any
> qualifier in server mode. The only qualifier documentation is a one-line example at
> dash.sthlp:641-643. Add a Differences-from-twoway entry stating what a per-plot qualifier
> does (shared-source CDSView so link() still propagates) and what it does not reach, and add
> the 06-06 entry to the changelog.

- **Tags:** deliverable · `n/a` · **small** · origin **06-06** (Appendix C)
- **Where:** `dash.sthlp:129-131`, `dash.sthlp:162-177` (Differences item 5),
  `dash.sthlp:641-643` (If qualifier example), `.ultraplan/CHANGELOG.md`
- **Evidence:** **[HEAD] confirmed** — the promise "Nothing is ever dropped without being
  named" sits at `dash.sthlp:174`; `.ultraplan/CHANGELOG.md` has no `## S06` heading, which
  matches `REMAINING.md`'s status row for section 06 (*"no S06 entry in CHANGELOG ②"*). The
  four exceptions are enumerated in the item text; exception (a)'s mechanism is the
  plain-double-quote call to `_dash_json_str` at `dash.ado:1224-1225` against the documented
  usage at `dash.ado:221`.
- **Requirements:** TR-30.7, TR-30.8, TR-30.9
- **Depends on:** Phases 01/02 for which exceptions survive; the changelog entry is written
  when the qualifier behaviour change lands, since it records before/after values.
- **Overlaps item 7** on `dash.sthlp:128-131` — make that edit once, in one commit, covering
  both items.

### 9. Correct the scheme section

> Correct the help: `dash.sthlp:1084` still tells users to put a `.scheme` file in the
> working directory; `:248` lists a `dark` scheme that does not exist; `:161-162` claims
> `scheme()` is "fully supported".

- **Tags:** deliverable · `n/a` · **small** · origin **S11-05** (main body, §3)
- **Where:** `dash.sthlp:1084`, `:248`, `:161-162`, `:708-713`
- **Evidence:** `REMAINING.md` §3's measured table — *"help matches code | `dash.sthlp:1084`
  still tells users to 'put its Stata-format `.scheme` file in the working directory'"* — and
  task 11-05's action clause, whose line numbers (`:248`, `:708-713`, `:161-162`) are the
  plan's and are stale. **[HEAD]**: the CWD instruction is at `dash.sthlp:1080-1085`; the
  theme alias list is at `:289-290` and expands `dark` to `s1rcolor` at `:1076`, and
  `s1rcolor.scheme` is one of the fourteen files in `schemes/`, so the `dark` clause is a
  verification, not an edit; "fully supported" is at `:176-177`.
- **Requirements:** TR-30.4, TR-30.5, TR-30.12 (scheme row already exists and stays "Yes /
  Yes")
- **Depends on:** **Phase 04**, which owns the code change and already assigns the `:1084`
  edit as TR-04.8. Read TR-30.5 before touching the file.

---

## Test plan

Rule 4: every function gets a unit test. Rule 8: every bug fix gets a regression test that
**fails before the fix and passes after**. For a documentation phase the "function" is a
help-parsing or code-introspecting helper, and the "bug" is a false sentence — so the
failing-first test is a test that fails against the help as it stands today.

All new tests go in **`test/test_help_conformance.py`** unless named otherwise. Run with
`python3 -m pytest test/test_help_conformance.py -v`; the cscripts run from `test/` under
`arch -arm64` per the project's cert-suite convention, and `$dash_nobrowser` must be set for
any Stata run that builds a dashboard.

### E30.1 — Retract what is false

**Write these first; each must fail at HEAD.**

| # | Test | File | Fails today because |
|---|---|---|---|
| T1 | `TestAxisTickDocumentationMatchesBehaviour::test_xtick_is_not_described_as_unlabelled` | `test_help_conformance.py` | the synopt rows at `:866-869` contain "without labels" while `dash_render.py:9906-9913` parses `xtick` with `_parse_axis_spec` |
| T2 | `TestAxisTickDocumentationMatchesBehaviour::test_xtick_yields_labelled_ticks` | `test/test_axis_options.py` | pins the *behaviour* the help must describe: build a figure with `xtick(2000 3000)` via `_fig_with_gopts` and assert the axis has a `FixedTicker` **and** visible major labels; add a second case with both `xlabel()` and `xtick()` asserting `xtick` is discarded |
| T3 | `TestTheMinorTickNoteIsHonest::test_bokeh_supports_minor_ticks` | `test_help_conformance.py` | asserts `'minor_ticks' in FixedTicker.properties()` and that `LinearAxis` exposes `minor_tick_line_color` — true at 3.9.0 — then asserts the help's minor-tick entry does not attribute the deferral to Bokeh |
| T4 | `TestTheMinorTickNoteIsHonest::test_the_note_does_not_redirect_to_a_broken_option` | `test_help_conformance.py` | the entry names `xtick()` as honoured; assert the entry's cross-references are drawn only from a set of options with no open defect (today: `xlabel()`) |
| T5 | `TestTheSchemeSectionMatchesTheCode::test_no_cwd_scheme_instruction` | `test_help_conformance.py` | `dash.sthlp:1080-1085` still instructs the reader to put a `.scheme` file in the working directory |
| T6 | `TestTheSchemeSectionMatchesTheCode::test_the_documented_set_equals_the_shipped_set` | `test_help_conformance.py` or `test/test_scheme.py` | parse the scheme names from the help's `{marker scheme}` section and assert set equality with `SchemeParser._BUILTIN_NAMES` and with `ls schemes/*.scheme`; assert each theme alias in the help resolves through `_THEME_SCHEME_MAP` to a shipped file (this is what turns item 9's `dark` clause into a check rather than a guess) |

**Unit tests (rule 4)** for every new helper: `_section_text(marker_start, marker_end)`,
`_synopt_rows(section)`, `_scheme_names_from_help()`, `_cross_references(entry)`. Each gets a
test against a small inline SMCL fixture, in the style the file already uses for its parser
rules — the docstring records that "the naive regexes each miss most of the surface", and a
new parser that silently matches nothing is the failure mode to guard.

**Non-vacuity (mutation).** For each guard, the mutation that must make it die:

| Test | Mutation | Expected |
|---|---|---|
| T1 | restore "without labels" in the synopt rows | fails |
| T1 | reword the synopt to a synonym of the true behaviour | still passes (it must key on behaviour, not phrasing) |
| T2 | change `raw_ax or raw_tick` to `raw_tick or raw_ax` | the "discarded when `xlabel()` is present" case flips and the test fails |
| T3 | assert against a stubbed Bokeh lacking `minor_ticks` | the test's premise fails loudly rather than the help check silently passing |
| T5 | re-add the CWD sentence | fails |
| T6 | delete `s1rcolor.scheme` from `schemes/`, or drop `dark` from `_THEME_SCHEME_MAP` | fails, naming the missing side |

### E30.2 — The qualifier and the parity claim

| # | Test | File | Fails today because |
|---|---|---|---|
| T7 | `TestQualifierDocumentation::test_unqualifiable_layers_are_named` | `test_help_conformance.py` | introspects `GlyphMapper.map_*` for a `view` parameter; `map_scatteri`, `map_pci_literal`, `map_function` have none and none is named in the help |
| T8 | `TestQualifierDocumentation::test_an_overlay_example_exists` | `test_help_conformance.py` | the only `if` example is the single-plot form at `:641-643`; assert an example block contains a parenthesised layer carrying `if` |
| T9 | `TestTheParityClaimIsTrue::test_the_claim_matches_the_forms_dash_honours` | `test_help_conformance.py` | drives the claim off a fixture of qualifier forms and whether `dash` honours each; the command-level paren form is honoured=False while the sentence claims parity |
| T10 | `test_a_command_level_qualifier_is_not_silently_dropped` | `test/test_varlist_expansion.cscript` | the cscript form of the measurement: `dash (scatter mpg weight) (scatter mpg price) if foreign==1` must either register `if_expr` in the spec or return a non-zero rc — today it returns rc 0 with no restriction |
| T11 | `test_a_quoted_string_qualifier_survives_serialization` | `test/test_varlist_expansion.cscript` | exception (a): `dash scatter mpg weight if make=="VW Rabbit"` must put `"if_expr":"make==\"VW Rabbit\""` in the spec; today the escaper is called with plain double quotes at `dash.ado:1224-1225` |
| T12 | `test_the_changelog_records_s06` | `test/test_fixtures_are_committed.py` or a new `TestChangelogCoverage` | asserts `.ultraplan/CHANGELOG.md` carries a heading for every section that changed user-visible behaviour; S06 is absent today |

T10 and T11 are rule-8 regression tests for defects Phases 01/02 fix; they belong to those
phases' commits but are listed here because item 8's Differences text is the documentation
half of the same defects, and the Differences entry must be deleted when they go green.

**Integration/cscript coverage.** Extend `test/test_per_plot_qualifier_linking.py` with a
documentation-parity case: for each layer type the help claims is qualifiable, assert a
qualified layer's rendered data really is the subset — so the help's list and the code's
capability cannot drift. `test/test_conformance.cscript` should run the documented overlay
example verbatim from the help, which is the cheapest way to keep an example from rotting.

**Non-vacuity.**

| Test | Mutation | Expected |
|---|---|---|
| T7 | add `view=None` to `map_function`'s signature | the test's required set shrinks; it must then **fail** if the help still names `function` as unqualifiable |
| T8 | delete the overlay example | fails |
| T9 | flip one row of the honoured-forms fixture | fails |
| T11 | restore the plain-double-quote call at `dash.ado:1224-1225` | fails |
| T12 | delete the `## S07` heading | fails, naming S07 — proving the test reads headings rather than asserting a constant |

### E30.3 — New surfaces and mode scoping

| # | Test | File | Fails today because |
|---|---|---|---|
| T13 | `TestDateDocumentation::test_every_date_kind_is_documented` | `test_help_conformance.py` | iterates `_STATA_DATE_KINDS` (`td tc tC tw tm tq th ty`); the help's date paragraph does not exist |
| T14 | `TestDateDocumentation::test_the_log_precedence_is_documented` | `test_help_conformance.py` | asserts the `xscale()`/`yscale()` entries state that a date axis overrides `log` and warns |
| T15 | `test_the_documented_formatter_matches_the_attached_one` | `test/test_dates.py` (class `TestDatetimeAxis`, currently `:334-404`) | pins the per-kind `DatetimeTickFormatter` the help describes: `%ty` → `%Y` at years/months/days; `%tc` → an hours pattern carrying the time; `%tm`/`%tq`/`%th` → a month-grain days pattern. This is also the missing test Appendix B, 08-04 asks for, covering `dash_render.py:9598-9603` and `_datetime_formatter_for` at `:247-268` |
| T16 | `TestEveryDashOnlyOptionIsInTheOptionTable::test_hover_has_a_synopt_row` | `test_help_conformance.py` | `hover` passes only the weak `_help_mentions` tier on the prose word at `:143`; the strict tier requires it in `_help_options()` |
| T17 | `test_hover_variables_reach_the_output` | `test/test_html_output.py` + `test/test_e2e_single.cscript` | the rule-8 regression for Phase 11: the named variables must occur in the built HTML. Today they occur zero times in 1.2 MB. Item 2 must not ship until this is green |
| T18 | `TestServerModeTableIsComplete::test_a_standalone_only_feature_has_a_row` | `test_help_conformance.py` | for each symbol in `{_parse_axis_label, DatetimeAxis, extra_y_ranges, _apply_graph_filter}`, count occurrences in the emitted app source (everything after `class ServerAppBuilder`, `dash_render.py:12265`) and require a Server Mode row **iff** the count is zero. Fails today: four zero counts, no rows |
| T19 | `TestServerModeTableIsComplete::test_no_row_survives_its_port` | `test_help_conformance.py` | the other direction — a row claiming "No" for a symbol now present in the emitted app fails, which is what deletes the caveat when Phase 10/16/27/02 lands |

**Unit tests (rule 4).** `_emitted_app_source()` (slice `dash_render.py` from
`class ServerAppBuilder`), `_server_mode_rows()` (parse the table into
`{feature: (standalone, server)}`), `_date_paragraph()`. Each gets a fixture-based test,
including a negative one: a parser that returns an empty set must fail its own "found
something" test, following the existing `TestTheParsersFoundSomething` class at `:224`.

**Non-vacuity.**

| Test | Mutation | Expected |
|---|---|---|
| T13 | drop `tC` from `_STATA_DATE_KINDS` | the required set shrinks and the test must fail if the help still documents a kind the code does not classify |
| T15 | swap `%ty`'s formatter for the default | fails |
| T16 | delete the `hover` synopt row | fails; deleting the prose at `:143` alone must **not** rescue it |
| T18 | insert a fake `DatetimeAxis` reference into the emitted app | the requirement flips; the test must then demand the row be **removed** |
| T19 | leave a stale "No" row after a port | fails |

### Suite-level

- `python3 -m pytest test/` — the whole suite; the audit baseline is **3,498 passed / 37
  skipped**, and this phase adds tests only, so the pass count rises and the skip count must
  not.
- `test/run_all_cscripts.do` under `arch -arm64` from `test/` — **25/25** at the audit; a
  skip is not a pass.
- `test/test_cscript_hygiene.py` still passes for any new cscript case.
- Every example command this phase adds to `dash.sthlp` is executed by
  `test/test_conformance.cscript` (zero `r(198)`, zero dropped series, zero dropped graphs),
  so a documented example that does not run fails the third release gate.

---

## Definition of done

A reviewer can tick each line.

**Retractions (E30.1)**

- [ ] `dash.sthlp:866-869` no longer describes `xtick()`/`ytick()` as producing ticks
      "without labels"; the wording matches `dash_render.py:9906-9913` at this commit, under
      exit (a) or (b) of TR-30.1, and the exit taken is stated in the commit message.
- [ ] The minor-tick note at `dash.sthlp:1116-1119` no longer attributes the deferral to
      Bokeh and no longer offers `xtick()` as the remedy.
- [ ] `_dash_pending` at `dash.ado:381-384` and `:629-632` and the Unsupported-section entry
      agree: `test_nothing_listed_there_is_honoured` and
      `test_everything_dash_ignores_is_listed_there` both pass.
- [ ] No instruction anywhere in `dash.sthlp` to place a `.scheme` file in the working
      directory (`grep -n '\.scheme' dash.sthlp` shows only the supported-set prose).
- [ ] The scheme section lists the fourteen shipped names; the documented set, the theme
      aliases, `SchemeParser._BUILTIN_NAMES` and `ls schemes/` are proven equal by test.
- [ ] The `dark` alias and the "`scheme()` is fully supported" sentence were re-checked
      against Phase 04's outcome and the decision recorded, not assumed.

**Qualifier and parity (E30.2)**

- [ ] A qualifier entry in `dash.sthlp` states: per-plot binding; shared-source
      `CDSView`/`BooleanFilter` so `link()` and filters still propagate; `by()` behaviour;
      that `scatteri`, `pci` and `function` cannot be qualified; and that a computed layer is
      re-estimated on the subset.
- [ ] An overlay example showing a qualifier inside a paren group sits beside the existing
      single-plot example at `:641-643`, and it runs in `test_conformance.cscript`.
- [ ] `dash.sthlp:128-131` is either true (command-level capture implemented) or narrowed to
      the forms `dash` honours, and the choice is the same one the code made.
- [ ] Differences item 5 names every surviving exception to "Nothing is ever dropped without
      being named", and names none that has been fixed.
- [ ] `.ultraplan/CHANGELOG.md` has an S06 entry with before/after/evidence, carrying the
      `-.00600869` → `-.01042596` slope change.

**New surfaces and mode scoping (E30.3)**

- [ ] A date paragraph documents: which `%t*` formats produce a date axis, that it applies to
      either axis, the per-kind formatter groupings, that `log` loses to a date axis and
      warns, and the `%tC` leap-second caveat with its "up to 27 seconds" figure.
- [ ] `hover(varlist)` has a synopt row and a description; it passes the strict
      documentation tier; and the variables it names demonstrably reach the output (T17
      green) at the commit where the entry ships.
- [ ] The Server Mode table carries a row for every capability with zero occurrences in the
      emitted app — at minimum the axis grammar, `xscale(range())`, date axes, the secondary
      axis and per-plot qualifiers.
- [ ] T18/T19 pass in both directions, so a later port deletes its own caveat.

**Process**

- [ ] Every test named in the test plan exists, was shown to fail before its edit, and passes
      after (rule 8), with the mutation result recorded in the commit message for T1, T7,
      T16 and T18 — the four most at risk of certifying nothing.
- [ ] Every new helper has a unit test, including a negative "the parser found something"
      test (rule 4).
- [ ] Full pytest suite green (≥ 3,498 passed, skips not increased); 25/25 cscripts under
      `arch -arm64`.
- [ ] `REMAINING.md` unmodified.
- [ ] Work committed on `feature/batch4-interactive-layer` (or a branch off it), never
      directly to `main`, with the merge command supplied (rule 6) and no mention of the
      assistant in the message (rule 7).

---

## Risks and sequencing notes

**R1 — Documenting an option that is still inert.** Item 2 (`hover()`) is the sharpest
instance: writing the synopt row before Phase 11 extracts the variables converts an
accepted-and-reported option into an accepted-and-documented-but-silent one, which is worse,
because the "ignoring unsupported option(s)" note is a user's only remaining signal.
*Mitigation:* T17 gates item 2; ship the entry in Phase 11's commit or immediately after.

**R2 — The same edit made twice, or not at all.** Items 7 and 8 both edit
`dash.sthlp:128-131`; item 9 overlaps Phase 04's TR-04.8 at `dash.sthlp:1084`; item 5's
`_dash_pending` deletion belongs to whichever phase implements the minor-tick options.
*Mitigation:* TR-30.5's instruction to check `git log -p -- dash.sthlp` first; the
conformance tests are idempotent and will pass whichever phase made the edit, so the risk is
duplication and merge conflict, not correctness.

**R3 — Caveats outliving their cause.** Every row item 6 adds is a promise to delete it
later. A stale "No" row is a BR-30.1 violation shipped by the phase that fixed the defect.
*Mitigation:* T19 fails on a stale row, so the porting phase cannot merge without removing
it. This is the single most valuable test in the phase.

**R4 — Prose tests that certify nothing.** This repository has a documented history of them:
ten were found and fixed during the plan, and the adversarial pass found more. A `grep` for
a sentence is exactly that shape. *Mitigation:* TR-30.14 — three of the guards are written
against code introspection (`GlyphMapper` signatures, `_STATA_DATE_KINDS`, symbol counts in
the emitted app) rather than against wording, and every guard has a named mutation it must
die under.

**R5 — Stale line numbers.** Task 11-05 cites `dash.sthlp:248`, `:708-713`, `:161-162`; the
text now lives at `:289-290`, `:1080-1085` and `:176-177`. `dash_render.py` grew from ~10,455
to ~16,000 lines, so every plan-file line number is suspect. *Mitigation:* locate by
`{marker}` and by symbol, never by line; `REMAINING.md`'s own line numbers are current and
are preferred; this document marks each **[HEAD]** check it performed.

**R6 — Exit (b) wording that must change again.** Items 4 and 7 can ship the truth now and
will need rewording when Phases 14/16 and 01/02 land. That is intended: a sentence that is
true for two months and then updated beats a sentence that is false for two months.
*Mitigation:* the tests written for exit (b) are behaviour-keyed (T2, T9), so they flip when
the behaviour flips and force the wording update rather than silently passing.

### Sequencing

```
Immediately, in parallel, no dependencies:
  item 4  (xtick/ytick synopt, exit (b))
  item 5  (minor-tick rationale + redirect; NOT the _dash_pending deletion)
  item 6  (Server Mode rows — the caveat is accurate the moment it is written)
  T18/T19 (the mechanism that later deletes item 6's rows)

After Phase 04 (scheme error + .scheme path retirement):
  item 9  (verify or make the edit — TR-30.5)

After Phases 01/02 (per-plot qualifiers):
  items 3, 7, 8  (one commit for :128-131; changelog with the measured slopes)

After Phase 09/10 (dates):
  item 1

After Phase 11 (hover extraction):
  item 2

Lockstep, whenever the owning phase lands:
  item 5's _dash_pending deletion   <- the minor-tick implementation phase
  item 4's rewording                <- Phases 14/16
  item 6's row deletions            <- Phases 02, 10, 16, 27
```

Phase 31 runs the gates. If any row added by item 6 is still present when Phase 31 starts,
that is a correct statement of the shipped product, not a failure — the failure mode is a row
that should have been deleted, and T19 catches it.
