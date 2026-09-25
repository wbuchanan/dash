# Section 10: Documentation, changelog and release

## Overview

This is the close-out. Sections 01-09 change numbers a user has already seen on screen —
`dash (scatter mpg weight) (lfit mpg weight if foreign==1)` stops drawing the 74-car fit and
starts drawing the 22-car one — and nothing in the package yet says so. This section writes
the three things that make that change legible and one thing that proves it end to end.

It writes the `dash.sthlp` qualifier documentation (discovery Q13: written **here**, not
deferred to Phase 30, because the semantics — which layers can be qualified, what a warning
says, what `link()` and `by()` do to a qualified layer — are being decided in this phase and
Phase 30 would have to re-derive them). It writes the `## S06` CHANGELOG entry with
before-and-after values (Q9). It adds the one end-to-end `.cscript` that drives **real
Stata** from `dash lfit ... if foreign==1` through `dash build` to the rendered coefficients
(Q10) — this repo has a documented history of Python probes built against a spec shape
`dash.ado` never emits, and only a cscript catches that. It records the performance
measurement (Q14: measure, do not cap). It records in `REMAINING.md` the six findings
carried forward and **not** fixed here, so the next phase inherits a list rather than a
surprise. Finally it reports the merge command without running it (rule 6).

**Ordering:** task **10-01 writes every failing guard for this section first**; tasks 10-02
to 10-05 turn them green one at a time.

## Risk: [green] — documentation and recording only; the one executable deliverable is a cscript that can only fail by telling the truth about a number

## Dependencies
- Depends on: section-01, section-02, section-03, section-04, section-05, section-06,
  section-07, section-08, section-09 (all of them — the brief's `dep: all`)
- Blocks: none
- Parallel batch: 5

## Evidence

### The numbers this section has to publish

`RESEARCH.md` §3.1, measured on StataNow 19.5 MP (arm64), `sysuse auto`, N=74, foreign==1: 22:

| quantity | `if foreign==1` | full sample |
|---|---|---|
| N | **22** | **74** |
| slope `_b[weight]` | **-.010425957587798849** | **-.0060086868119993289** |
| intercept `_b[_cons]` | **48.918297231743246** | **39.440283530717977** |
| se(slope) | .0024941691063949203 | .00051787817670857252 |
| r2 | .46628963289838132 | .65153125290875114 |
| x-range of the drawn segment | **[1760, 3420]** | [1760, 4840] |

Companions from the same section, used by the second cscript case:
`foreign==0` N=52 slope -.0059750835105182119 · `in 1/60` N=60 slope -.0056974654861187985 ·
`foreign==1 & weight>2500` N=6 slope -.0093656523981433745 ·
**`foreign==1 in 1/60` N=8 slope -.0096564106174751828**.

> ⚠️ `auto.dta` ships sorted domestic-first; foreign cars start at observation 53. `in 1/20`
> contains **zero** foreign cars and `regress mpg weight if foreign==1 in 1/20` is `r(2000)`.
> Any intersection case must use `in 1/60`. (`RESEARCH.md` §3.1.)

> **Method caveat.** Sersets store `float`, so coefficients recovered *from a graph* agree
> with `regress` doubles only to ~1e-8 relative. Assertions use the `regress` doubles above,
> never serset-recovered values. Discovery Q4 sets the tolerance at **1e-6 relative**; the
> unqualified fit is wrong by a factor of 1.735, so the bound is nowhere near the decision
> boundary.

### The semantics the help has to state (RESEARCH §3.2, confirmed numerically)

| command | layer 1 serset | `lfit` slope | equals `regress` on |
|---|---|---|---|
| `(scatter) (lfit)` | 74 obs | -.0060086866 | full sample |
| **`(scatter) (lfit … if foreign==1)`** | **74 obs** | **-.0104259571** | `if foreign==1` |
| `(scatter) (lfit) if foreign==1` | 22 obs | -.0104259571 | `if foreign==1` |
| `(scatter … if foreign==0) (lfit … if foreign==1)` | 52 obs | -.0104259571 | each its own |
| `(scatter) (lfit … if weight>2500) if foreign==1` | 22 obs | -.0093656528 | the **intersection**, N=6 |
| `(scatter) (lfit … if foreign==1) in 1/60` | 60 obs | -.0096564116 | intersection, N=8 |
| `(scatter) (lfit … in 1/60) if foreign==1` | 22 obs | -.0096564116 | intersection, N=8 |

1. A per-layer qualifier restricts **only its own layer**; the unqualified sibling keeps all
   74 rows. 2. A command-level qualifier restricts every layer. 3. Both together are a
   **logical AND**, and the last two rows are identical, so **order does not matter**.
   4. **`in` is absolute dataset observation numbers, never re-indexed** into an outer
   subsample: if `in 1/60` were re-indexed within the 22 command-level rows it would select
   all 22 and give -.01042; it gives -.00965. 5. Axes span the union across layers; only the
   fitted segment shrinks to its own sample's x-range.

### The two divergences from Stata the help must declare

**(1) Degenerate subsets — `RESEARCH.md` §3.3, decision UPHELD in §4.4.** Stata is not
uniform. At one observation:

| types | message | rc | effect |
|---|---|---|---|
| `lfit` `lfitci` `lpoly` `lpolyci` `kdensity` | `insufficient observations` | **2001** | **whole graph aborts — no graph at all** |
| `qfit` `qfitci` `fpfit` `fpfitci` | `could not fit model` | **0** | all-missing serset, nothing drawn |
| `lowess` `mband` `mspline` `histogram` and every raw type | *(none)* | **0** | 1-obs serset, drawn |

`twoway (scatter mpg weight) (lfit mpg weight if make=="Honda Civic")` → **rc 2001, and the
scatter is not drawn either**; `graph describe` reports *graph not found*. Root cause, read
from `/Applications/StataNow/ado/base/t/twoway__lfit_serset.ado`: `lfit`/`lfitci` re-raise
any rc other than 2000 while `qfit`/`qfitci` re-raise nothing — deliberate in the code,
undocumented, arbitrary rather than principled. **dash keeps the uniform graceful policy:
every layer type warns, names itself and the reason, and draws nothing; the build never
aborts.** That is section 07's behaviour and this section's documented divergence.

**(2) `by()` panel survival — `RESEARCH.md` §3.6 / S2, resolved in §4.7.** Under `by()`, the
same 1-observation case returns **rc 0**, still prints `insufficient observations`, and Stata
**deletes the entire panel from the layout**, taking its perfectly valid scatter layer with
it (confirmed by SVG export: the panel label is gone). **dash does not reproduce it** — the
panel is kept, the failing layer is drawn empty, and a warning names it.

Per-panel intersection is otherwise exact (§3.6): for
`(scatter mpg weight) (lfit mpg weight if foreign==1), by(rep78)` each panel's fit equals
`regress … if <panel> & foreign==1` — panel 3 N=3 slope **-.0154761904761905**, panel 4 N=9
**-.0055002961792872**, panel 5 N=9 **-.0196983546617916** — and empty-intersection panels
(1 and 2) are kept and rendered.

### What the help must say about the mechanism — a superseded decision

Discovery Q3 chose a **private pre-filtered `ColumnDataSource`** for connected-topology
layers. **RESEARCH.md §4.1 supersedes it: a per-layer NaN column on the shared source.** The
measurement decided it (§2.3, instrumented `CanvasRenderingContext2D`, 12 rows, layer must
draw two contiguous runs `[0,1,2]` and `[6,7,8]`):

| approach | drawn | linked selection | `source.data` swap reaches it |
|---|---|---|---|
| `CDSView` + `BooleanFilter` | 1 subpath, 3 pts — rows 6,7,8 silently lost | yes | yes (filter goes stale) |
| **NaN in a per-layer column** | **2 subpaths, 6 pts ✓** | **yes, automatic** | **yes** |
| private pre-filtered source | 1 subpath, 6 pts — **connects straight across the gap** | **no** | **no** |

**Consequence for the documentation:** the help must NOT say that a qualified connected
layer leaves `link()`. It stays inside `link()` and inside the filter callback. Phase 30's
TR-30.6 clause 2 ("a `CDSView` + `BooleanFilter` … not a pre-filtered source, or linking
breaks") stays true as a statement about *why linking still works*; the mechanism sentence
must be written as "the restriction is carried on the graph's shared source — as a view for
marker glyphs, as a per-layer gap column for connected ones — so `link()` and the filter
widgets keep reaching a qualified layer."

Likewise §4.2 supersedes "mask the `LabelSet`": `LabelSet` has no `view` property in Bokeh
3.9 (`LabelSet(view=...) -> AttributeError`), so marker labels are drawn by a `figure.text`
glyph. The help says only what the user sees — labels appear only on rows the layer drew —
not which Bokeh model carries them.

### The second user-visible bug this changelog has to carry (F-A)

`RESEARCH.md` §1.9: at `dash_render.py:11465-11470` a **linked** `by()` graph gives every
panel the same `shared_src_render` and differentiates them only by `panel_view_r`. Since
computed mappers ignore `view`, **every facet panel drew an identical lfit/kdensity/histogram
computed from all rows** — with no qualifier involved at all. An **unlinked** `by()` graph
(`:11481`) gets a genuinely pre-subset source per panel and was correct. So **adding
`link()` silently changed a computed layer's values.** That is its own changelog line.

### Findings carried forward and NOT fixed in this phase (`RESEARCH.md` §4.8)

- **D2** — private sources are invisible to the filter callback *generally*:
  `all_graph_sources` is built only from `self.sources` (`dash_render.py:11882`), so
  `sorted_source`, `clean_source`, `seg_source`, `dl_source` and every computed mapper's CDS
  are never updated when a widget moves. The NaN decision reduces this; it does not close it.
- **D6** — `in_expr` silently discards most legal Stata: `dash_render.py:8628` uses
  `^(\d+)/(\d+)$` with no `else` branch, so `in 1/l`, `in f/20`, `in -10/-1`, `in 10` and
  `1 / 10` are accepted and dropped with no warning. The generated-script paths re-implement
  the same regex (`:13814-13818`, `:15047-15051`), so the gaps are identical there.
- **D7** — `mpg>20` with `mpg=[10, NaN, 30]` returns only `30` under pandas; **Stata includes
  missing**. A silent wrong answer inside the translator, affecting graph-level qualifiers
  too.
- **B1** — after a callback grew a source 10 → 12 rows the `BooleanFilter` still held **10**
  booleans; no error, no warning, and the two new rows were simply invisible.
- The emitted app's **facet/total agg entries omit the `'opts'` key** (`15155ff`, `15256ff`),
  so `agg.get('opts') or {}` at `15605ff` silently degrades to `{}` for faceted layers.
- **`kdensity`'s third serset column** holds all 74 unrestricted `mpg` values in Stata while
  density and grid honour the qualifier (grid min 12 → 14). Unresolved from outside; only
  bites if dash's `kdensity` is ever compared against a serset dump rather than the drawn
  curve.

### Repository facts measured for this section (read-only, at `187a786`)

- `dash.sthlp` is 49,625 bytes. Anchors: the `twoway`-parity sentence at **:128-130**; the
  `{title:Differences from twoway}` list at **:139-183**, six numbered items, item 6 last;
  the `{ul:If qualifier}` example block at **:641-643** (three lines, the single-plot form
  only); `{marker faceting}` at **:660**. The Examples section ends at :658.
- `test/test_help_conformance.py` mechanically checks `dash.sthlp` against `dash.ado`. Three
  rules constrain what may be written: (a) `_help_options()` treats a `{phang}`/`{phang2}`
  line that begins with `{opt`, `{opth`, `{cmdab` or `{ul:` as an **option definition** and
  then registers every `{cmd:name(` inside the block, so a documented name that `dash.ado`
  does not accept fails `test_no_documented_option_is_rejected`; (b)
  `test_every_marker_reference_has_a_marker` requires every `dash##name` to have a
  `{marker name}`; (c) `test_the_markers_are_unique` forbids a duplicate marker. An example
  line written as `{phang2}{cmd:. dash …}` is safe — the character after `{cmd:` is a period,
  which the `\{cmd:\s*,?\s*([A-Za-z_]…)\(` scan cannot match.
- `.ultraplan/CHANGELOG.md` is **tracked at HEAD but deleted in the working tree**
  (`git ls-tree HEAD .ultraplan/` lists it; `ls` does not). The archived copy is
  `.ultraplan-archive-20260921/CHANGELOG.md`, 1,195 lines, carrying eight `## S`-numbered entries from `## S07` to `## S16`
  and **no `## S06` heading** — exactly the gap Phase 30's TR-30.9 records.
- `test/test_cscript_hygiene.py` parameterises over `glob("test/*.cscript")`, so a new script
  is auto-enrolled. It enforces: no script decides Python is missing from the rc of
  `capture python: pass`; a script that reports "SKIP: Python not available" must consult
  `c(python_exec)`; no macro holding a line read from a file is expanded in plain double
  quotes; and **`TestEveryCscriptIsWiredIntoTheRunner::test_the_runner_calls_it` fails unless
  `test/run_all_cscripts.do` names the script**.
- `test/run_all_cscripts.do` sets `global dash_nobrowser 1` at :50 and runs each script as
  `capture noisily { do "<name>.cscript" }` with `rc == 222` meaning skip, then
  `capture file close _all` and `cd` back.
- **Computed-layer data is not greppable in the HTML.** `map_lfit` builds
  `ColumnDataSource({"x": x_fit, "y": y_fit})` from numpy arrays (`dash_render.py:3865`), and
  Bokeh 3.9 serialises a numpy column as
  `{"type":"ndarray","array":{"type":"bytes","data":"H4sIA…"},"shape":[N],"dtype":"float64"}`
  — base64 of gzip of little-endian float64. Verified by decoding a column out of
  `comprehensive_demo.html`. A `cert_file_has` needle search for `30.5686` therefore finds
  **nothing**; the cscript must decode.
- The embedded document appears in two shapes across this repo's own outputs:
  `<script type="application/json">…</script>` (e.g. `scatter.html`) and
  `const docs_json = '…';` (e.g. `comprehensive_demo.html`). A reader must handle both.
- `_fit_grid` (`dash_render.py:6419-6438`) draws a fitted line at **100 points over the
  observed range**, endpoints exactly `min(x)` and `max(x)`. So after section 02 lands the
  qualified `lfit` source is x[0]=**1760**, x[-1]=**3420**, and
  y[0]=**30.568611877217272**, y[-1]=**13.26152228147118** (from the §3.1 doubles).
- The largest example is `examples/comprehensive_demo.do` (268 lines) →
  `comprehensive_demo.html` at **2,003,601 bytes**, against `full_dashboard.html` 1,602,198
  and `kelly22ex_dashboard.html` 1,582,355. `regen_comprehensive.py` regenerates it **without
  Stata**, which makes it the right subject for a repeatable timing.
- The current warning contract, which the help quotes: `dash_render.py:9994-9997` emits
  `dash: per-plot qualifier on layer {pi + 1} could not be applied ({exc}); the layer is
  drawn unfiltered.` BR-01.12 keeps that shape — every new warning in this phase names the
  layer the same way.
- `REMAINING.md` §5 (**:216-255**) is the blocker entry this phase closes; §7 *Release
  closeout* (**:271-282**) already ends with "**Merge command** to be reported, not run
  (project rule 6)".

### Where this section overrides the phase document

`phases/PHASE-01-…md`'s Definition of done ends with: *"Explicitly out of scope for this
phase … the `dash.sthlp` and CHANGELOG text belongs to **Phase 30**."* **Discovery Q13 and Q9
supersede that line.** The semantics are decided here, so the text is written here, and
Phase 30's item 3 (TR-30.6) plus TR-30.9 are marked discharged rather than re-planned. Two
Phase 30 clauses must NOT be written later: TR-30.8's exception **(c)** "a qualifier on any
computed layer" is closed by this phase and must never appear in the Differences list, and
TR-30.6 clause 2's "not a pre-filtered source" wording is narrowed as described above.
Everything else in Phase 30 items 7 and 8 — the `twoway`-parity sentence at `dash.sthlp:129`
and exceptions (a), (b) and (d) — stays with Phase 30: (b) and (d) are still live
(`RESEARCH.md` §1.7, D5: `plot.get('if_expr')` does not occur anywhere in the emitted app,
and `dash.ado:1496` promotes a qualifier to graph level only when `n_segs == 1`).

### The trap that governs every assertion here

Existing coverage is scatter-only and **structurally cannot catch this class of bug**.
`test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans` and reports a *computed* layer as fully visible no matter
what it drew. **Every assertion on a computed layer in this section compares the layer's own
source values against an independently computed subsample** — in the cscript, the decoded
`x`/`y` columns of the fit's own `ColumnDataSource` against Stata's `regress` doubles — never
a view's booleans.

## TDD test stubs

All of these are written in task **10-01** and must fail before tasks 10-02 to 10-05 run.

- **Test: `dash.sthlp` has a `{marker qualifiers}` section and every `dash##qualifiers`
  reference resolves to it.** → `test/test_help_conformance.py`, new class
  `TestTheQualifierIsDocumented`. Fails before 10-02 (no such marker exists at HEAD).
  *Mutation:* rename the marker to `{marker quals}` and leave the link — the existing
  `test_every_marker_reference_has_a_marker` must die too.
- **Test: the qualifier section states all six semantics** — per-plot binding; composition
  with a command-level qualifier as a logical AND in either order; `in` as absolute
  observation numbers that are never re-indexed; what `link()` and `by()` do; which layers
  cannot carry a qualifier (`scatteri`, `pci`, `function`) and that they warn; and the
  degenerate-subset policy. → `test/test_help_conformance.py`. One assertion per fact, each
  matching a distinctive phrase. *Mutation:* delete the sentence saying the two qualifiers
  intersect and the AND assertion dies.
- **Test: the two divergences appear in the Differences list.** The uniform degenerate policy
  and the kept `by()` panel each have a numbered `{phang2}` item. →
  `test/test_help_conformance.py`. *Mutation:* delete item 8 and the `by()`-panel assertion
  dies.
- **Test: documenting the qualifier introduces no phantom option.** The set returned by
  `_help_options()` gains no name that `dash.ado` does not declare. → already enforced by
  `test_help_conformance.py::test_no_documented_option_is_rejected`; 10-01 adds nothing, 10-02
  must not break it. *Mutation:* write an example line as `{phang2}{cmd:qualif(x)}` — that
  test dies immediately.
- **Test: `.ultraplan/CHANGELOG.md` exists and carries an `## S06` entry with both the before
  and the after value.** The entry must contain `-.0060086868119993289` **and**
  `-.010425957587798849`, `39.440283530717977` **and** `48.918297231743246`. →
  new `test/test_closeout_docs.py`. Fails before 10-03 (the file is not in the working tree).
  *Mutation:* drop the "before" column from the table and the test dies — an entry that shows
  only the new number does not tell a user their old dashboard was wrong.
- **Test: the `## S06` entry carries the separate F-A line** — a linked `by()` graph drew an
  identical computed layer in every panel with no qualifier involved. →
  `test/test_closeout_docs.py`. *Mutation:* delete the `link()` sentence; the test dies.
- **Test: the changelog records the performance measurement** — a `### Performance` block
  holding a before and an after number for both render wall time and ColumnDataSource count
  on `comprehensive_demo`. → `test/test_closeout_docs.py`. Fails before 10-05.
- **Test: `REMAINING.md` records the six carried-forward findings** — `D2`, `D6`, `D7`, `B1`,
  the facet/total `opts` omission and the `kdensity` third serset column — each in a section
  that says they were **not** fixed in this phase. → `test/test_closeout_docs.py`. Fails
  before 10-05. *Mutation:* remove the "not fixed" wording and leave the identifiers; the
  test asserts the disclaimer, so it dies.
- **Test: every cscript is wired into the runner** — already enforced by
  `test/test_cscript_hygiene.py::TestEveryCscriptIsWiredIntoTheRunner::test_the_runner_calls_it`,
  which auto-enrols the new file via its `glob`. Fails the moment
  `test/test_per_plot_qualifier.cscript` exists and before `run_all_cscripts.do` names it.
- **Test (the cscript itself): real Stata → `dash build` → decoded coefficients.**
  `test/test_per_plot_qualifier.cscript` asserts the rendered `lfit` implies slope
  `-.010425957587798849` and intercept `48.918297231743246` to 1e-6 relative, that it is
  **not** `-.0060086868119993289`, that the fit spans [1760, 3420], that the sibling scatter
  still holds 74 rows, and that a second layer written `if foreign==1 in 1/60` implies slope
  `-.0096564106174751828`. *Mutation that must kill it:* revert the two `row_mask` lines
  section 02 inserts after `dash_render.py:3846` in `map_lfit` — the script must then fail on
  the slope assertion, reporting `-.00600869`. It asserts on the fit source's decoded values,
  never on a view's booleans.

## Tasks

<task type="auto" id="10-01">
  <name>Write the failing close-out guards</name>
  <files>test/test_help_conformance.py, test/test_closeout_docs.py (new)</files>
  <action>
    Write the tests that the rest of this section must satisfy. Nothing else in this task
    changes; every assertion below must FAIL now.

    1. In `test/test_help_conformance.py`, append a class in the file's existing style (a
       docstring that states what went wrong, then one assertion per fact):

       ```python
       class TestTheQualifierIsDocumented:
           """Phase 01 decided the qualifier's semantics; the help has to state them.

           Discovery Q13: written here rather than in Phase 30, because which layers can
           be qualified, what each warning says, and what link() and by() do to a
           qualified layer are all decided by this phase.
           """
       ```

       Assertions, each reading `_help_text()`:
       - `"{marker qualifiers}" in h` — the section exists.
       - the section's body (slice from `{marker qualifiers}` to the next `{marker `)
         contains, case-insensitively: `"binds to that plot"`; `"logical AND"` or
         `"intersection"` together with `"either order"`; `"absolute observation numbers"`
         and `"never re-indexed"`; `"link("` and `"by("`; `"scatteri"`, `"pci"` and
         `"function"` in one sentence with `"warn"`; `"draws nothing"` for the degenerate
         policy.
       - the Differences list gained two numbered items: `"{phang2}7."` and `"{phang2}8."`
         exist, item 7's text mentions `"insufficient"` or `"too few"` and `"every layer
         type"`, item 8's mentions `"panel"` and `"kept"`.
       - the `{ul:If qualifier}` example block (search for `"{ul:If qualifier}"`) is followed
         within 12 lines by a line containing `"(lfit"` and `"if foreign"` — the overlay
         companion TR-30.6 asks for.
       Do NOT assert on option names; the file's existing `_help_options()` machinery already
       polices those and 10-02 must not add any.

    2. Create `test/test_closeout_docs.py` with a module docstring explaining that this phase
       changes numbers users have already seen, so the record of that change is itself under
       test. Use `os.path.dirname(__file__)` + `".."` to reach the repo root, as the other
       test modules do. Assertions:
       - `.ultraplan/CHANGELOG.md` exists and contains a heading matching
         `^## S06\b` (re.M).
       - the S06 block (slice from `## S06` to the next `\n## `) contains all four literal
         strings `-.0060086868119993289`, `-.010425957587798849`, `39.440283530717977`,
         `48.918297231743246`.
       - the S06 block contains `"link("` and `"by("` in one line together with `"identical"`
         — the F-A entry.
       - the S06 block contains a `### Performance` sub-heading, and that sub-block contains
         at least two numbers matched by `r"\d+\.\d+\s*s"` and at least two matched by
         `r"\b\d+\s+ColumnDataSource"` (before and after, for time and for source count).
       - `REMAINING.md` contains a section whose body names `D2`, `D6`, `D7`, `B1`,
         `opts` and `kdensity`, and whose heading or first line contains
         `"not fixed"` (case-insensitive).
       Give each assertion a message naming the task that is supposed to satisfy it
       (`"section 10 task 10-03 writes this"`, etc.) so a failure reads as a to-do, not a
       mystery.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_closeout_docs.py test/test_help_conformance.py -q`
    exits non-zero. Every assertion added in this task must appear in the failure list; the
    pre-existing `test_help_conformance.py` tests must all still pass. Confirm the *reason*:
    the CHANGELOG failure must be "file does not exist", not an import error, and the
    `{marker qualifiers}` failure must be a missing marker, not a regex typo.
  </verify>
  <done>
    Two test files state, in executable form, everything tasks 10-02 to 10-05 owe. Every one
    of them fails, and each failure message names the task that will fix it.
  </done>
</task>

<task type="auto" id="10-02">
  <name>Document the per-plot qualifier in dash.sthlp (Q13, TR-30.6)</name>
  <files>dash.sthlp, phases/PHASE-30-documentation-and-help-reconciliation.md</files>
  <action>
    Cites BR-01.3, BR-01.4, BR-01.6, BR-01.8, BR-01.11, BR-01.12 and TR-30.6.

    1. Insert a new section in `dash.sthlp` immediately **before** `{marker faceting}` at
       `:660` (the Examples section ends at `:658`), opening with:

       ```
       {marker qualifiers}
       {title:if and in qualifiers}
       ```

       Write the body as `{pstd}` prose paragraphs and `{phang2}{cmd:. …}` example lines
       only. **Do not use `{synopt:}`, `{opt }`, `{opth }` or `{cmdab:}` anywhere in this
       section, and begin every `{cmd:}` example with a period and a space** — a
       `{phang2}{cmd:name(` line registers `name` as a documented option in
       `test_help_conformance.py::_help_options()` and then fails
       `test_no_documented_option_is_rejected`.

       Content, in this order:
       - **Binding.** An `if`/`in` written inside a plot's parentheses restricts that plot and
         no other; an unqualified sibling keeps every observation. Give the worked example and
         the numbers: `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws 74
         points and a line fitted on the 22 foreign cars — slope -.0104, not -.0060.
       - **Composition.** A qualifier written for the whole command restricts every layer; the
         two combine as a **logical AND**, and the result is the same in **either order**.
       - **`in`.** `in` counts **absolute observation numbers** in the dataset as sorted, and
         is **never re-indexed** into an outer subsample. State the consequence with the
         measured case: `(lfit … if foreign==1) in 1/60` and `(lfit … in 1/60) if foreign==1`
         both estimate on the same 8 observations.
       - **`link()`.** A qualified layer stays inside a link group: the restriction is carried
         on the graph's shared data source — as a view for marker glyphs, as a per-layer gap
         column for connected ones — so brushing and the filter widgets still reach it. Do not
         claim the layer leaves `link()`; RESEARCH §4.1 superseded that design.
       - **`by()`.** A qualifier narrows each panel rather than removing panels: a panel shows
         the intersection of its own rows and the qualifier's rows, and a panel whose
         intersection is empty is still drawn.
       - **Layers that cannot be qualified.** `scatteri`, `pci` and `function` carry
         coordinates or an analytic expression, not observations. `dash` still **validates**
         the qualifier — an unknown variable or an out-of-range `in` is an error, as in
         `twoway` — and then says so with a warning that names the layer, rather than dropping
         it silently.
       - **Too few observations.** When a qualifier leaves a computed layer too few rows, that
         layer warns, names itself and the reason, and draws nothing; the rest of the
         dashboard is built. `dash` never falls back to the unqualified computation.

    2. Extend the `{ul:If qualifier}` example block at `:641-643` with the overlay companion
       TR-30.6 asks for, keeping the `{phang2}{cmd:. …}` shape:

       ```
       {phang2}{cmd:. dash (scatter mpg weight) (lfit mpg weight if foreign == 1), saving(fit.html)}{p_end}
       ```

    3. Add two numbered items to the `{title:Differences from twoway}` list, after item 6
       (which ends at `:183`) and before `{marker subcommands}` at `:185`, in the list's
       existing `{phang2}N.  {ul:…}` shape:
       - **7. Too few observations never aborts the graph.** Stata is not uniform here: at one
         observation `lfit`, `lfitci`, `lpoly`, `lpolyci` and `kdensity` return rc 2001 and
         abort the whole graph — the companion scatter is lost with it — while `qfit` and
         `fpfit` return rc 0 and draw nothing. `dash` is uniform: every layer type warns and
         draws nothing, and the rest of the dashboard is built.
       - **8. A `by()` panel is never deleted.** Under `by()`, Stata prints
         `insufficient observations`, returns rc 0 and removes the whole panel — including its
         valid layers. `dash` keeps the panel, draws the failing layer empty and names it in a
         warning.
       Both items must link to the new section as `{help dash##qualifiers:if and in
       qualifiers}` so `test_every_marker_reference_has_a_marker` has something to resolve.

    4. In `phases/PHASE-30-documentation-and-help-reconciliation.md`, under `### 3. Document
       the per-plot qualifier` (`:925`), insert a blockquote directly beneath the heading:

       > **Discharged in Phase 01** (discovery Q13). `dash.sthlp` gained `{marker qualifiers}`
       > and Differences items 7 and 8; TR-30.9's `## S06` changelog entry is written by the
       > same phase. Two clauses do not carry over: TR-30.8's exception **(c)** ("a qualifier
       > on any computed layer") is closed and must not be written, and TR-30.6 clause 2's
       > "not a pre-filtered source" is narrowed — connected layers use a per-layer gap column
       > on the shared source, and stay inside `link()`. Exceptions (a), (b) and (d), TR-30.7
       > and the rest of item 8 remain open in this phase.

       Change nothing else in that file.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_help_conformance.py -q`
    exits 0 — the `TestTheQualifierIsDocumented` class from 10-01 passes and no pre-existing
    test regressed, in particular `test_no_documented_option_is_rejected`,
    `test_every_marker_reference_has_a_marker` and `test_the_markers_are_unique`.
    Then `grep -c "{marker qualifiers}" dash.sthlp` prints `1`.
  </verify>
  <done>
    A user who types `help dash` can read what an `if` inside a plot's parentheses does, how
    it composes, what `in` counts, what `link()` and `by()` do to it, which three layer types
    cannot carry it, and what happens when it leaves too few rows — plus the two places
    `dash` deliberately diverges from Stata. Phase 30's item 3 records that it was done here
    and names the two clauses that must not be re-planned.
  </done>
</task>

<task type="auto" id="10-03">
  <name>Write the S06 changelog entry with before and after values (Q9)</name>
  <files>.ultraplan/CHANGELOG.md</files>
  <action>
    `.ultraplan/CHANGELOG.md` is tracked at HEAD but absent from the working tree; the
    1,195-line copy with `## S07`-`## S16` is at `.ultraplan-archive-20260921/CHANGELOG.md`
    and has no `## S06` heading. Create the file fresh for this phase — do not resurrect the
    archived body, which the current ultraplan run deliberately archived.

    Structure, reusing the archived file's voice (header, then per-section entries, then
    "Changed behaviour" tables and a "Bugs fixed" prose block):

    ```markdown
    # CHANGELOG — behaviour changes

    Every entry here changes a number or a picture a user has already seen. Each one records
    the value before, the value after, and the evidence.

    Entries for the conformance sections S07-S16 are in
    `.ultraplan-archive-20260921/CHANGELOG.md`.

    ---

    ## S06 — a qualifier written inside a plot's parentheses now restricts that plot
    ```

    The entry must contain:

    1. **The headline, in prose.** `dash (scatter mpg weight) (lfit mpg weight if
       foreign==1)` returned rc 0, warned about nothing, and drew a fit estimated on all 74
       cars. It now estimates on the 22 foreign ones.

    2. **A `### Changed behaviour` table** with `layer | before | after | evidence` columns,
       matching the archived file's shape. The row that matters, with the full-precision
       values so a user can diff their own output:

       | layer | before | after | evidence |
       |---|---|---|---|
       | `lfit` under a per-plot `if` | fit on all 74 rows — slope `-.0060086868119993289`, intercept `39.440283530717977`, segment spanning [1760, 4840] | fit re-estimated on the qualified subset — slope `-.010425957587798849`, intercept `48.918297231743246`, segment spanning [1760, 3420] | `regress mpg weight if foreign==1`, StataNow 19.5 MP, `sysuse auto` |

       Add a row for each of the other computed types the phase fixed — `qfit`, `lfitci`,
       `qfitci`, `lowess`, `lpoly`, `lpolyci`, `fpfit`, `fpfitci`, `mspline`, `mband`,
       `histogram`, `kdensity`, `area` — stating "computed on all rows" → "computed on the
       qualified rows". For `lowess`, `lpoly` and `mband` note that the derived parameter
       moves with the sample: `frac`, the default bandwidth and the band count are all
       sample-relative, so a qualified layer's smoothing is now subset-relative too.

    3. **A separate `### A linked by() graph drew the same computed layer in every panel`
       block** — the F-A entry, which is a distinct user-visible bug with no qualifier
       involved. Before: a `by()` graph inside a `link()` group gave every panel the same
       shared source and differentiated panels only by a view, so every panel drew an
       **identical** lfit/kdensity/histogram computed from all rows, while the same graph
       *outside* a link group was correct — meaning adding `link()` silently changed a
       computed layer's values. After: each panel computes on its own rows. Evidence:
       `dash_render.py:11465-11470` (linked) against `:11481` (unlinked).

    4. **A `### Bugs fixed` prose block** in the archived file's style, one short paragraph
       each for: marker labels that were drawn for rows the layer excluded; a `colorvar()`
       colour range set by rows the layer never drew; `line`/`tsline`/`rline` and the line
       halves of `connected`/`rconnected`, which drew a line straight across the excluded
       rows and emitted Bokeh validation error E-1024, and now draw the correct gapped shape
       with no validation error; the aggregate recompute that widened a qualified histogram
       or density back to the full sample on the first filter move, for per-plot **and**
       graph-level qualifiers; and the facet/qualifier intersection that was lost on the
       first widget move.

    5. **A `### Divergences from Stata, stated deliberately` block** with the two the help now
       documents: the uniform degenerate-subset policy (Stata aborts the whole graph for
       `lfit`/`lfitci`/`lpoly`/`lpolyci`/`kdensity` at one observation and does not for
       `qfit`/`fpfit`; `dash` warns and draws nothing for all of them) and the kept `by()`
       panel (Stata prints `insufficient observations`, returns rc 0 and deletes the panel).

    6. **A `### Known, not fixed here` block** naming D2, D6, D7, B1, the emitted facet/total
       `opts` omission and the `kdensity` third-serset-column question in one line each, with
       a pointer to `REMAINING.md` for the detail that task 10-05 writes.

    Leave a `### Performance` placeholder heading at the end of the S06 entry; task 10-05
    fills it with measured numbers.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_closeout_docs.py -q -k "s06 or changelog or link"`
    — the S06 heading, the four-number and F-A assertions from 10-01 now pass. The
    `### Performance` and `REMAINING.md` assertions still fail, and must still fail: they
    belong to 10-05.
  </verify>
  <done>
    `.ultraplan/CHANGELOG.md` exists again and its `## S06` entry tells a user who has an old
    dashboard exactly which number changed, from what, to what, and on what evidence —
    including the `link()` + `by()` case that never involved a qualifier at all.
  </done>
</task>

<task type="auto" id="10-04">
  <name>The end-to-end certification script through real Stata (Q10)</name>
  <files>test/test_per_plot_qualifier.cscript (new), test/run_all_cscripts.do</files>
  <action>
    Cites BR-01.1, BR-01.2, BR-01.3, BR-01.4, BR-01.13. This is the deliverable that catches
    spec-shape mismatches a Python probe cannot: it drives `dash.ado`, `dash build` and the
    renderer in one Stata session and reads the numbers back out of the produced HTML.

    1. Create `test/test_per_plot_qualifier.cscript`, modelled on `test/test_e2e_single.cscript`:

       - Header comment block (`*!`), then
         `cscript "dash per-plot qualifier" adodir ".."`.
       - Dependency guards, in this order and this form — `capture which jsonio` → `exit 222`
         on failure, then `if "`c(python_exec)'" == "" { … exit 222 }` with the message
         `SKIP: Python not available.`. **Never decide Python is missing from the rc of
         `capture python: pass`** — `test_cscript_hygiene.py` fails any script that does, and
         the measured reason is in that file's docstring.
       - `global dash_nobrowser 1` before any `dash build`, as the runner does at
         `run_all_cscripts.do:50`.
       - `qui sysuse auto, clear`, then `do "../dash_parse.mata"`, `do "../dash.ado"`,
         `do "cert_helpers.do"`.

       **Case 1 — the headline (BR-01.2).**
       ```
       dash clear
       tempfile out1
       local p1 = "`out1'.html"
       dash (scatter mpg weight) (lfit mpg weight if foreign == 1), name(q1)
       dash build, saving("`p1'") replace
       ```
       Then a `python:` block — native `python:`, never `shell` — that reads `"`p1'"` via
       `sfi.Macro.getLocal`, and:
       - extracts the embedded document: try
         `re.search(r'<script type="application/json"[^>]*>(.*?)</script>', html, re.S)`
         first, and fall back to the text between `const docs_json = '` and the next `';`
         (both shapes occur in this repo's own output); `json.loads` it.
       - walks every dict looking for `"ColumnDataSource"` in `type`+`name`, and normalises
         `attributes.data` from Bokeh 3.x's `{"type":"map","entries":[[k,v],…]}` form — the
         same normalisation `test/test_html_verification.py:145` does.
       - decodes a column that is a dict with `"shape"`: `base64.b64decode` the
         `array.data` (or `__ndarray__`) string, `gzip.decompress` it inside a
         `try/except` that falls back to the raw bytes, then `numpy.frombuffer(..., "<f8")`.
         **This step is not optional**: `map_lfit` builds its source from numpy arrays, so the
         fitted values are gzipped base64 in the file and a text search finds nothing.
       - identifies the fit source as the one whose column names are exactly `{"x","y"}` with
         100 points (`_fit_grid`'s default, `dash_render.py:6419-6438`), and the scatter
         source as the one carrying columns `mpg` and `weight`.
       - computes `slope = (y[-1]-y[0])/(x[-1]-x[0])` and `intercept = y[0] - slope*x[0]` and
         returns them with `sfi.Macro.setLocal("slope", repr(slope))`, plus `x[0]`, `x[-1]`
         and the scatter row count.
       Place this block **after** `dash build`, which has already warmed Python in this
       session; the first Python call under the runner is unreliable for reasons unrelated to
       what is being tested.

       Assertions back in Stata, with the tolerance stated once (discovery Q4, 1e-6 relative):
       ```
       local truth_b = -.010425957587798849
       local truth_a =  48.918297231743246
       assert abs(`slope'     - (`truth_b')) < 1e-6 * abs(`truth_b')
       assert abs(`intercept' - (`truth_a')) < 1e-6 * abs(`truth_a')
       ```
       then the explicit negative guard, so the test states what must NOT be drawn:
       ```
       assert abs(`slope' - (-.0060086868119993289)) > 1e-3
       ```
       then `assert abs(`xmin' - 1760) < 1e-6` and `assert abs(`xmax' - 3420) < 1e-6`
       (RESEARCH §3.1: the fitted segment shrinks to its own sample's x-range), and
       `assert `n_scatter' == 74` (BR-01.3 — the unqualified sibling keeps every row).
       Print `P1Q-01 PASS: …` lines in the style of the other scripts.

       **Case 2 — `in`, and the intersection inside one plot (BR-01.4).**
       Same shape, with
       `dash (scatter mpg weight) (lfit mpg weight if foreign == 1 in 1/60), name(q2)`, and
       assert the slope equals `-.0096564106174751828` to 1e-6 relative. Add a comment stating
       why the range is `1/60` and not `1/20`: `auto.dta` is sorted domestic-first, foreign
       cars start at observation 53, and `regress mpg weight if foreign==1 in 1/20` is
       `r(2000)`.

       Two rules this script must obey, and a comment must say so:
       - **Never assert through a view's booleans.** `test/test_varlist_expansion.py:101`'s
         `_visible_count` reads `renderer.view.filter.booleans`, which reports a computed
         layer as fully visible no matter what it drew. This script reads the fit source's own
         decoded values and compares them with Stata's `regress` doubles.
       - Never expand a macro holding a line read from the HTML inside plain double quotes;
         use `cert_file_has` or the Python block. `test_cscript_hygiene.py` enforces this.

    2. Wire it into `test/run_all_cscripts.do`. Copy an existing block verbatim — the
       `display as text "[ RUN ] …"`, `cd "`testdir'"`, `capture noisily { do … }`,
       `local rc = _rc`, `capture file close _all`, `cd "`dashdir'"`, then the
       222/0/else tally — and change only the script name. Place it after the
       `test_e2e_single.cscript` block.
  </action>
  <verify>
    Two commands.
    (1) `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_cscript_hygiene.py -q` exits 0 — the new script is
    auto-enrolled by the module's `glob` and must satisfy every hygiene rule, including
    `test_the_runner_calls_it`.
    (2) `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash/test && arch -arm64 /usr/local/bin/stata-mp -b do test_per_plot_qualifier.cscript` then
    `grep -E "PASS|SKIP|r\(" test_per_plot_qualifier.log` prints the `P1Q-…​ PASS` lines and
    **no** `SKIP` and no `r(` error. A skip is not a pass: if it skips, install the
    dependency and re-run rather than recording the skip.
    (3) Record the rule-8 evidence by mutation: revert the two `row_mask` lines section 02
    inserted after `dash_render.py:3846`, re-run (2), and confirm the script fails the slope
    assertion with `-.00600869`. Restore the lines afterwards.
  </verify>
  <done>
    One certification script proves the headline case through the real Stata command path —
    parse, spec emission, build, render — and asserts the coefficients that come out, not the
    shape of a Python object. The runner calls it, the hygiene suite accepts it, and a
    recorded mutation shows it can fail.
  </done>
</task>

<task type="auto" id="10-05">
  <name>Measure the cost, record what is carried forward, report the merge</name>
  <files>scripts/measure_qualifier_perf.py (new), .ultraplan/CHANGELOG.md, REMAINING.md</files>
  <action>
    Discharges discovery Q14 (measure, do not cap) and the carry-forward half of the brief.

    1. Create `scripts/measure_qualifier_perf.py`, in the style of the other `scripts/extract_*`
       helpers (module docstring saying what it measures and how to run it). It must:
       - time a full build of the **largest** example — `examples/comprehensive_demo.do`, 268
         lines, whose output `comprehensive_demo.html` is 2,003,601 bytes against
         `full_dashboard.html`'s 1,602,198 — by running the repo's own Stata-free regenerator
         with `runpy.run_path("regen_comprehensive.py", run_name="__main__")` inside
         `time.perf_counter()`. Take **five** runs and report the median, so a single slow
         run does not become the record.
       - then parse the produced `comprehensive_demo.html`, extract the document (the
         `const docs_json = '…';` form for this file; fall back to the
         `<script type="application/json">` form) and report: the number of
         `ColumnDataSource` models, the number of columns serialised as `ndarray` blobs, and
         the file size in bytes.
       - print one line per metric in a fixed `name<TAB>value` shape so the before and after
         runs can be diffed, and exit 0.
       Do not import `dash_render` at module scope for the timing — the measurement is of the
       whole render path, which `regen_comprehensive.py` already drives end to end.

    2. Produce the **before** number. Prefer the figure `section-01` recorded in
       `.ultraplan/BASELINE.md` if it measured this example; otherwise take it from the
       phase's start commit in a throwaway worktree —
       `git worktree add /tmp/dash-pre 187a786`, copy the script in, run it there, then
       `git worktree remove /tmp/dash-pre`. Do not stash, do not check out anything on the
       working branch. Then produce the **after** number on the current branch.

    3. Fill the `### Performance` block task 10-03 left in `.ultraplan/CHANGELOG.md` with a
       four-row table: median render wall time before and after, and ColumnDataSource count
       before and after, for `comprehensive_demo`, each with the commit it was measured at.
       Add one sentence of interpretation grounded in the mechanism: a qualified layer
       computes on **fewer** rows than before, so per-layer cost falls; the only growth is one
       gap column per qualified connected layer and one `ColumnDataSource` per jittered layer.
       **Decision rule, declared by this plan rather than measured:** if the median wall time
       grew by more than 10%, or the ColumnDataSource count grew by more than the number of
       jittered layers in the example, do not silently accept it — record the number and open
       an item in `REMAINING.md` §6. Otherwise record the number and add **no** cap; a cap
       needs a measurement to justify it.

    4. In `REMAINING.md`, rewrite the head of §5 (`:216`) to say the blocker is closed by this
       phase — keep the measured table and the ground-truth block, they are the evidence —
       and append a subsection `### Carried forward, not fixed in this phase` with one entry
       each, each naming its measured location:
       - **D2** — private sources are invisible to the filter callback generally;
         `all_graph_sources` is built only from `self.sources` (`dash_render.py:11882`), so
         `sorted_source`, `clean_source`, `seg_source`, `dl_source` and every computed
         mapper's CDS are never updated when a widget moves.
       - **D6** — `in_expr` silently discards `in 1/l`, `in f/20`, `in -10/-1`, `in 10` and
         `1 / 10`; `dash_render.py:8628` matches `^(\d+)/(\d+)$` with no `else` branch, and
         the generated-script paths repeat the regex at `:13814-13818` and `:15047-15051`.
       - **D7** — `mpg>20` excludes missing where **Stata includes it**; a silent wrong answer
         in the translator itself, affecting graph-level qualifiers too.
       - **B1** — a callback that grows a source leaves `BooleanFilter.booleans` at the old
         length, and the new rows are invisible with no error and no warning.
       - **the emitted facet/total `opts` omission** — the facet and `by(total)` agg entries
         (`15155ff`, `15256ff`) omit the `'opts'` key, so `agg.get('opts') or {}` at
         `15605ff` degrades to `{}` for faceted layers.
       - **`kdensity`'s third serset column** — it holds all 74 unrestricted `mpg` values in
         Stata while density and grid honour the qualifier; unresolved from outside, and it
         only bites if dash's `kdensity` is compared against a serset dump rather than the
         drawn curve.
       Say plainly, in the subsection's first line, that these were found during this phase
       and **not fixed** in it.

    5. Report the merge command in the task's output — **do not run it** (project rule 6):
       ```
       git checkout main && git merge --no-ff feature/batch4-interactive-layer
       ```
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 scripts/measure_qualifier_perf.py` prints one `name<TAB>value` line per metric and
    exits 0. Then
    `/opt/homebrew/bin/python3.14 -m pytest test/test_closeout_docs.py test/test_help_conformance.py test/test_cscript_hygiene.py -q`
    exits 0 — every guard written in 10-01 now passes, including the `### Performance` and
    `REMAINING.md` assertions. Finally
    `/opt/homebrew/bin/python3.14 -m pytest test -q` is green against the baseline
    section 01 recorded, and the 25+1 cscripts run with
    `cd test && arch -arm64 /usr/local/bin/stata-mp -b do run_all_cscripts.do` reporting
    `ALL TESTS PASSED` with no script skipped for a missing dependency.
  </verify>
  <done>
    The cost of the change is a recorded number rather than an assumption, the six findings
    this phase deliberately did not fix are written down where the next phase will look, and
    the merge command is on the record without having been executed.
  </done>
</task>
