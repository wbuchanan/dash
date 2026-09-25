# Section 08: Qualifier scoping — bar syntax and `by()` panels

## Overview

Every other section of this phase asks *what a qualifier does to a layer*. This one asks the
question underneath it: **which layer did the user write the qualifier on?** Research measured
two scoping rules in real Stata that dash was never checked against. **S1** — in `||` bar
syntax a trailing `if` binds to the *last plot*, not to the command; command-level scope needs
the explicit empty final segment `|| if exp`. **S2** — under `by()`, Stata intersects strictly
per panel, keeps empty-intersection panels, and then, when one layer's qualifier leaves too few
rows, prints `insufficient observations`, returns rc 0, and silently deletes the whole panel
including its perfectly good scatter.

For S1 the decision was: **probe dash first, then decide.** Task 08-01 is that probe and it
produces a committed artifact, not a formality. A read of the splitter predicts two real
divergences — a legal `twoway` command dash rejects with r(198), and a command-level qualifier
dash drops in complete silence — so tasks 08-02 and 08-03 are written to fix them, with an
explicit stop-and-record instruction if the probe contradicts the prediction. For S2 the
decision was: **do not reproduce Stata's panel deletion.** dash already keeps the panel by
construction, so 08-04 pins that contract and the per-panel intersection with a mutation-proofed
test; the warn-and-draw-empty half belongs to S07.

**Rule 8 convention for this section: the failing tests are written in one task (08-02) before
any product code is touched in 08-03.** Task 08-04 is a pin test on behaviour that is already
correct and names the mutation that must kill it.

## Risk: [yellow] — the fix edits the Stata-side parser, which every other command path also goes through

The mechanism is small and local (one branch of `_dash_split_segs`, one promotion block in
`dash.ado`), but `_dash_split_segs` is the single entry point for **every** `dash` plot command,
so a mistake there is not confined to qualified commands. Two specific hazards: the paren-mode
tail must not swallow text that is not a qualifier, and the `n_segs == 1` promotion at
`dash.ado:1496` is load-bearing for server mode (RESEARCH §1.7, D5 — single-layer commands work
in server mode *because* of it) and must not be removed. The section is also the one place in
this phase that touches `dash.ado` / `dash_parse.mata` at all, which the phase document's line
28 says belongs to Phase 2; see Evidence for why that exclusion is superseded here.

## Dependencies

- Depends on: section-01
- Blocks: section-10
- Parallel batch: 2

## Evidence

### Scope note — why this section touches `dash.ado` at all

`phases/PHASE-01-per-plot-qualifiers-on-computed-layers.md:28` says *"No `dash.ado` /
`dash_parse.mata` change belongs to this phase"*, and `:1113` repeats it. That exclusion is
**superseded for this section only**, by the two approved additions in
`.ultraplan/sections/index.md` — "Bar-syntax `||` scoping probe" and "`by()` panel survival" —
and by RESEARCH §4.6's resolution: *"probe dash's behaviour against the Stata table first, then
decide. If dash already matches, pin it with a regression test; if it diverges, fix it here,
because qualifier scoping is precisely this phase's subject."* Both are flagged for VALIDATE as
deliberate task-beyond-requirement, not scope creep. The change stays surgical: one branch of
one Mata function, one new eight-line `sclass` program, one promotion block. Nothing else in
`dash.ado` moves.

### S1 — Stata's measured bar-syntax binding (RESEARCH §3.2, §4.6)

> **NEW — S1. `||` syntax binds a trailing `if` to the LAST PLOT, not the command.**
> `twoway scatter … if foreign==1 || lfit …` gives a 22-obs scatter and a **full-sample**
> fit. Command-level scope in bar syntax requires the explicit empty final segment
> `|| if exp`. This is a real parsing hazard and needs its own test — `dash.ado:1496`
> promotes a qualifier to graph level when `n_segs == 1`, which is a different rule.

The measured table, with the coefficients from RESEARCH §3.1 and §3.2:

| Stata command | layer-1 serset | `lfit` slope | equals `regress` on |
|---|---|---|---|
| `twoway scatter mpg weight if foreign==1 \|\| lfit mpg weight` | **22 obs** | **-.0060086866** | the **full sample** |
| `twoway scatter mpg weight \|\| lfit mpg weight if foreign==1` | **74 obs** | **-.0104259571** | `if foreign==1` |
| `twoway scatter mpg weight \|\| lfit mpg weight \|\| if foreign==1` | **22 obs** | **-.0104259571** | `if foreign==1` |

Ground-truth doubles (RESEARCH §3.1; the S01 fixture carries these):

| sample | N | slope | intercept |
|---|---:|---|---|
| `if foreign==1` | 22 | `-.010425957587798849` | `48.918297231743246` |
| full sample | 74 | `-.0060086868119993289` | `39.440283530717977` |
| `in 1/60` | 60 | `-.0056974654861187985` | — |
| `foreign==1 in 1/60` | 8 | `-.0096564106174751828` | — |

Two further measured rules the scoping fix must not break (RESEARCH §3.2, points 2-4):
command-level restricts **every** layer including unqualified ones; command-level and per-plot
compose by **logical AND in either order**; and `in` is **absolute dataset observation numbers,
never re-indexed** into an outer subsample — the decisive case being that
`(scatter) (lfit … if foreign==1) in 1/60` and `(scatter) (lfit … in 1/60) if foreign==1` both
give `-.0096564116`, not `-.01042596`.

### What dash's parser actually does — read from source

`dash` hands its raw argument text straight to the splitter with no `[if] [in]` strip anywhere
in between: `dash.ado:97` is `_dash_plot \`0'`, and `_dash_plot`'s first real statement is
`mata: _dash_split_segs(strtrim(\`"\`0'"'))` at `dash.ado:1388`. Only `_n_segs`, `_seg_1..N`
and `_graph_opts_raw` come back (`dash_parse.mata:521-525`). **There is no channel for a
command-level qualifier at all.**

- **PAREN branch, `dash_parse.mata:388-442`.** The loop collects top-level `(...)` groups
  (`:419-434`) and treats a top-level comma as the start of graph options (`:435-439`). Text at
  depth 0 that is neither `(`, `)` nor `,` matches no branch and falls through to `i++` at
  `:440`. A trailing `if exp` after the last `)` is therefore **never stored anywhere**.
- **FLAT branch, `dash_parse.mata:444-511`.** Splitting on `||` at depth 0 (`:488-497`) leaves a
  trailing `if` inside the last segment, where `_dash_process_segment`'s `syntax varlist [if]
  [in]` (`dash.ado:781`, `:1093-1108`) captures it as that plot's qualifier. A final `|| if exp`
  becomes a *segment whose first word is `if`*.
- **`_expand_plottype_str`, `dash_parse.mata:159-226`.** The table holds 38 plot types and
  neither `if` nor `in`; `if` is a prefix of none of them, so `nhits == 0` and it returns `""`.
  `dash.ado:936-945` then prints *"dash: unrecognised plot type 'if'"* and `exit(198)`.

A faithful port of `_dash_split_segs` (both branches, character for character) was run
read-only against the five forms. Result:

```
'scatter mpg weight if foreign==1 || lfit mpg weight'
   n_segs=2 segs=['scatter mpg weight if foreign==1', 'lfit mpg weight'] gopts=''
'scatter mpg weight || lfit mpg weight if foreign==1'
   n_segs=2 segs=['scatter mpg weight', 'lfit mpg weight if foreign==1'] gopts=''
'scatter mpg weight || lfit mpg weight || if foreign==1'
   n_segs=3 segs=['scatter mpg weight', 'lfit mpg weight', 'if foreign==1'] gopts=''
'(scatter mpg weight) (lfit mpg weight) if foreign==1'
   n_segs=2 segs=['scatter mpg weight', 'lfit mpg weight'] gopts=''
'(scatter mpg weight) (lfit mpg weight) if foreign==1, name(g1)'
   n_segs=2 segs=['scatter mpg weight', 'lfit mpg weight'] gopts='name(g1)'
```

**Predicted verdict, to be confirmed by task 08-01 in real Stata:**

| form | Stata | dash (predicted) | verdict |
|---|---|---|---|
| A `scatter … if foreign==1 \|\| lfit …` | if binds to plot 1 | if binds to plot 1 | **matches — pin it** |
| B `scatter … \|\| lfit … if foreign==1` | if binds to plot 2 | if binds to plot 2 | **matches — pin it** |
| C `scatter … \|\| lfit … \|\| if foreign==1` | command-level, rc 0 | **r(198)** "unrecognised plot type 'if'" | **diverges — fix** |
| D `(scatter …) (lfit …) if foreign==1` | command-level, rc 0 | rc 0, **qualifier silently gone** | **diverges — fix** |
| E `(scatter …) (lfit …) in 1/60` | command-level, rc 0 | rc 0, **qualifier silently gone** | **diverges — fix (BR-01.4)** |

Form D is the worse of the two: rc 0, no warning, and a dashboard drawn on the wrong sample —
the exact failure shape this whole phase exists to remove (PRD §2). Form C breaks the drop-in
promise by rejecting a command `twoway` accepts.

No existing test covers either. Every Python test that exercises a graph-level qualifier sets
`if_expr` on the spec dict directly (`test/test_axis_options.py:724`,
`test/test_linking_filters.py:195`, `test/test_graph_options.py:31`, …) and so never goes
through `dash.ado`; the only cscript that touches per-plot scoping,
`test/test_varlist_expansion.cscript:629-660` (V2-11), uses paren syntax with the qualifier
*inside* the parentheses and asserts only that it is **not** promoted.

### The promotion rule, and why it must survive

`dash.ado:1483-1503`:

```stata
    // Promote if_expr / in_expr from the first plot segment to the graph level.
    // The renderer looks for graph-level "if_expr"/"in_expr" in graph_options or
    // at the top level; per-plot qualifiers are not read in build/server flows.
    …
    if `n_segs' == 1 {
        mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
```

RESEARCH §1.7 (D5) records the consequence of the `:1485` comment as measured fact:
`plot.get('if_expr')` **does not occur anywhere in the emitted `bokeh serve` app** — every read
there is graph-scoped (`:13812`, `:13819`, `_graph_qualifiers` `:15007`). **So single-layer
commands work in server mode today only because of this promotion.** Deleting it would silently
break server mode for the one case that currently works. The fix adds a command-level channel
*beside* the promotion; it does not replace it.

### S2 — `by()` panels (RESEARCH §3.6, §4.7)

Stata's measured per-panel behaviour for
`(scatter mpg weight) (lfit mpg weight if foreign==1), by(rep78)`:

| panel | scatter | lfit | recovered slope | `regress … if rep78==k & foreign==1` |
|---|---|---|---|---|
| 1 | 2 obs (all panel rows) | **0 obs** | — | N=0 |
| 2 | 8 obs | **0 obs** | — | N=0 |
| 3 | 30 obs | 3 pts | -.015476189 | N=3, **-.0154761904761905** |
| 4 | 18 obs | 3 pts | -.005500296 | N=9, **-.0055002961792872** |
| 5 | 11 obs | 3 pts | -.019698354 | N=9, **-.0196983546617916** |

**Each panel's fit equals `regress … if <panel> & <layer>` exactly**, the scatter keeps all its
panel's rows, and **empty-intersection panels are kept and rendered**. Then:

> **NEW — S2, the biggest surprise. `by()` swallows a fatal rc and silently deletes the
> panel.** The same 1-observation case that aborts an ordinary graph with rc 2001 returns
> **rc 0** under `by()` — the message `insufficient observations` still prints, the graph is
> built, and the offending **panel disappears from the layout entirely**, taking its
> perfectly valid scatter layer with it. SVG export confirms the panel label is gone.

**Resolution (RESEARCH §4.7): do not reproduce it.** Keep the panel, warn, draw the failing
layer empty — consistent with §4.4's uniform degenerate policy, which S07 implements.

**dash already keeps the panel, structurally.** Panels are built from the data alone:
`_build_figures` calls `self._expand_by_groups(g, base_df=self.df)` (`dash_render.py:11403` for
the linked path, `:11436` for the unlinked path), `_expand_by_groups` (`:8776-8858`) groups
`work_df` with `groupby(..., dropna=False)` and returns one `(label, frame)` per group, and the
render loop at `:11457-11490` builds one figure per entry of `self._facet_map[name]`. **No plot's
qualifier is consulted anywhere in that chain.** So the S2 deliverable here is a pin test plus
the documented divergence, not a code change.

**Where the per-panel intersection is actually formed** — `_make_figure_body`,
`dash_render.py:9951-9998`:

```python
 9962    _pdf = self._apply_graph_filter({"if_expr": _p_if, "in_expr": _p_in})
 9974    _ids = list(source.data.get(_ROW_ID_COLUMN, []))
 9978    _wanted = {_pos.get(i, -1) for i in _pdf.index}
 9979    _mask  = [bool(r in _wanted) for r in _ids]
 9986    if _prev_bools is not None and len(_prev_bools) == len(_mask):
 9987        _mask = [bool(a and b) for a, b in zip(_prev_bools, _mask)]
```

`_apply_graph_filter` filters **`self.df`**, and the mask is then taken by `__dash_row__`
identity against whatever rows the panel's source carries. So:

- **Unlinked `by()`** — each panel gets its own pre-subset source (`:11450-11456`),
  `facet_view` is `None` (`:11481`), and `_mask` is `panel ∩ qualifier` by construction.
- **Linked `by()`** — every panel shares `shared_src_render` and is distinguished only by
  `panel_view_r` (`:11461-11476`); the AND at `:9986-9987` forms the intersection.

Two fragilities to name in the test, both from RESEARCH §1.5: **D3** — the length guard at
`:9986` *silently* skips the intersection when the lengths differ, and `except Exception`
(`:9993`) cannot catch it because nothing raises; and the registration at `:9991-9992` passes
`self._row_ids_for(_pdf)`, the qualifier's rows **alone**, so the first widget move discards the
panel AND-term. That second one is **TR-01.7 and belongs to section-06** — this section asserts
the *first-paint* intersection only and must say so in the test docstring rather than
overlapping S06.

### The trap that governs every assertion here

`test/test_varlist_expansion.py:101`'s `_visible_count`, and its clone `_visible` at
`test/test_per_plot_qualifier_linking.py:82`, both read
`renderer.view.filter.booleans`. A **computed** layer draws from its own `ColumnDataSource`
built inside the mapper (RESEARCH §1.2: all 14 computed mappers accept `view=None` and the
token `view` never appears in any of their bodies), so those helpers report it as fully visible
no matter what it drew. **Assertions about a computed layer must compare the layer's own source
values against an independently computed subsample, never a view's booleans.** Task 08-04
asserts on the *mask the renderer registered* and on the *panel source's rows* — the inputs the
mapper will consume once section-02 lands — and must say in its docstring that it deliberately
does not assert drawn values, which belong to section-02 and section-06.

## TDD test stubs

All S1 stubs live in a new `test/test_qualifier_scoping.cscript`, because the behaviour is
`dash.ado`-side and only real Stata exercises it (DISCOVERY Q10 — a pure-Python probe cannot
catch a spec-shape mismatch, a documented failure mode in this repo). The S2 stub is pytest.

- Test: `scatter mpg weight if foreign==1 || lfit mpg weight` puts `if_expr` on plot 1 only,
  leaves plot 2 unqualified, and leaves the graph-level `if_expr` empty. **Pin — passes
  today.** Mutation that must kill it: change `dash.ado:1496` from `if \`n_segs' == 1` to
  `if \`n_segs' >= 1`; the graph-level `if_expr` becomes `foreign==1` and the test must fail.
  → `test/test_qualifier_scoping.cscript`
- Test: `scatter mpg weight || lfit mpg weight if foreign==1` puts `if_expr` on plot 2 only.
  **Pin**, same mutation. → `test/test_qualifier_scoping.cscript`
- Test: `scatter mpg weight || lfit mpg weight || if foreign==1` returns rc 0, produces exactly
  **two** plots, and carries `if_expr` at the **graph** level with neither plot qualified.
  **Fails today with r(198) "unrecognised plot type 'if'".**
  → `test/test_qualifier_scoping.cscript`
- Test: `(scatter mpg weight) (lfit mpg weight) if foreign==1` carries `if_expr` at the graph
  level. **Fails today — rc 0 and the qualifier is absent from the spec entirely.**
  → `test/test_qualifier_scoping.cscript`
- Test: the same with `in 1/60` carries `in_expr` at the graph level (BR-01.4 — `in` honoured
  identically to `if`). **Fails today.** → `test/test_qualifier_scoping.cscript`
- Test: `(scatter mpg weight) (lfit mpg weight) if foreign==1, name(g1)` captures the qualifier
  **and** still parses `name(g1)` into `graph_options`. **Fails today.**
  → `test/test_qualifier_scoping.cscript`
- Test: `(scatter mpg weight if foreign==1) in 1/60` — one segment carrying its own `if` plus a
  command-level `in` — keeps `if_expr` on the plot and puts `in_expr` at the graph level, so the
  two compose by AND (RESEARCH §3.2 point 3). **Fails today.**
  → `test/test_qualifier_scoping.cscript`
- Test: `(scatter mpg weight) (lfit mpg weight) if nosuchvar==1` returns **r(111)**, as `twoway`
  does. **Fails today — rc 0, because nothing ever evaluates the dropped text.**
  → `test/test_qualifier_scoping.cscript`
- Test: a `|| if exp` segment that is **not** last still returns r(198), and the message names
  the plot type. **Pin** on the documented limit. Mutation: accept an `if`-headed segment at any
  position; the test must fail. → `test/test_qualifier_scoping.cscript`
- Test: a `by()` graph whose computed layer's qualifier empties one panel and leaves exactly one
  row in another still renders **every** panel, and the affected panels' scatter layers still
  carry all their panel's rows. **Pin** on the S2 divergence. Mutation that must kill it: insert
  `if not any(_mask): continue` in the facet render loop at `dash_render.py:11457-11490`, or
  drop a zero-row group from `_expand_by_groups`; panel count falls and the test must fail.
  → `test/test_by_panel_qualifier_survival.py`
- Test: on an **unlinked** `by()` graph the qualifier mask registered for the computed layer
  selects exactly `panel rows ∩ qualifier rows`, compared against an independently computed row
  set — not against any view's booleans. → `test/test_by_panel_qualifier_survival.py`
- Test: on a **linked** `by()` graph the same holds, formed by the AND at
  `dash_render.py:9986-9987` (BR-01.8). Mutation: delete the `_prev_bools` AND; the linked case
  must fail while the unlinked one still passes — which is what proves the two are distinct
  paths. → `test/test_by_panel_qualifier_survival.py`

## Tasks

<task type="auto" id="08-01">
  <name>Probe dash's bar-syntax and paren-syntax qualifier scoping against the Stata table</name>
  <files>.ultraplan/audits/probes/bar-syntax-scoping-probe.do, .ultraplan/audits/probes/bar-syntax-scoping-probe.txt</files>
  <action>
    Create the directory `.ultraplan/audits/probes/` (it does not exist at HEAD).

    Write `.ultraplan/audits/probes/bar-syntax-scoping-probe.do`. It measures only — it
    asserts nothing and must never fail. Header comment: this probe discharges RESEARCH §4.6's
    "probe dash's behaviour against the Stata table first, then decide", and its recorded
    output is the input to task 08-02.

    Preamble, copied from `test/run_all_cscripts.do:22-25` and `:50`:
      `global dash_nobrowser 1`
      `adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON/"`
      `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"`
      `qui sysuse auto, clear`
    Then `do "dash_parse.mata"` and `do "dash.ado"` from the repository root, as
    `test/test_parser.cscript:23-24` does with `..` prefixes.

    For each of the eight forms below, run it inside `capture noisily`, record `_rc`, and — when
    `_rc == 0` — record the registered spec from `${dash_json_NAME}`, where NAME is that form's `name()` (written by
    `dash.ado:1570`). Use a distinct `name()` per form so the globals do not collide, and
    `dash clear` between forms. A named graph only registers; it does not render, so no Python
    and no browser are involved.

      F-A  dash scatter mpg weight if foreign==1 || lfit mpg weight, name(pA)
      F-B  dash scatter mpg weight || lfit mpg weight if foreign==1, name(pB)
      F-C  dash scatter mpg weight || lfit mpg weight || if foreign==1, name(pC)
      F-D  dash (scatter mpg weight) (lfit mpg weight) if foreign==1
      F-D2 dash (scatter mpg weight) (lfit mpg weight) if foreign==1, name(pD2)
      F-E  dash (scatter mpg weight) (lfit mpg weight) in 1/60, name(pE)
      F-F  dash (scatter mpg weight if foreign==1) in 1/60, name(pF)
      F-G  dash (scatter mpg weight) (lfit mpg weight) if nosuchvar==1, name(pG)

    F-D has no `name()` on purpose: without one `dash.ado:1508-1511` routes to
    `_dash_render_immediate`, so run F-D under `capture noisily` and record only its rc; F-D2 is
    the inspectable twin.

    For every rc-0 form print, on its own line: the form id, `_rc`, the count of `"type":`
    occurrences in the spec (the number of plot segments), whether `"if_expr":"foreign==1"`
    appears anywhere, and whether it appears in the tail of the string starting at
    `"graph_options"` (the graph-level slot, emitted after `graph_options` by
    `dash.ado:1503`). Use the `strpos` + `substr` tail technique from
    `test/test_varlist_expansion.cscript:652-657`. Do the same for `"in_expr":"1/60"`.

    Run it and capture the whole log into
    `.ultraplan/audits/probes/bar-syntax-scoping-probe.txt`, then append to that file a
    hand-written VERDICT table with one row per form: `form | Stata (from RESEARCH §3.2) |
    dash measured | matches / diverges`.

    STOP CONDITION — this is the decision point the brief reserves. If the measured verdicts
    match the Evidence section's prediction (A and B match Stata, C is r(198), D/D2/E drop the
    qualifier silently, G is rc 0 instead of r(111)), continue to 08-02 unchanged. If any row
    differs, record the difference in the VERDICT table, do **not** silently re-plan: adjust
    08-02's assertions to the measured behaviour and note the adjustment in the same file.

    Do not run the pytest or cscript suites in this task.
  </action>
  <verify>`arch -arm64 /usr/local/bin/stata-mp -b do .ultraplan/audits/probes/bar-syntax-scoping-probe.do` from the repository root exits 0, and `.ultraplan/audits/probes/bar-syntax-scoping-probe.txt` contains one line per form F-A…F-G plus a VERDICT table. `grep -c "^F-" .ultraplan/audits/probes/bar-syntax-scoping-probe.txt` prints at least 8.</verify>
  <done>dash's actual scoping behaviour for all eight forms is measured in real Stata and committed as a probe script plus its recorded output, with a per-form verdict against RESEARCH §3.2. No product code and no test has been changed.</done>
</task>

<task type="auto" id="08-02">
  <name>Write the failing qualifier-scoping certification script</name>
  <files>test/test_qualifier_scoping.cscript, test/run_all_cscripts.do</files>
  <action>
    This task writes tests only. No file under the repository root that ships with the package
    may be edited. Project rule 8: every assertion 08-03 makes true is written and **observed
    failing** here first.

    Create `test/test_qualifier_scoping.cscript`, modelled on `test/test_parser.cscript`:
    `*!` header block, then `cscript "dash qualifier scoping" adodir ".."`, then
    `qui sysuse auto, clear`, `do "../dash_parse.mata"`, `do "../dash.ado"`. Set
    `global dash_nobrowser 1` before anything else. Every case uses `name()` so the command
    registers instead of rendering, reads `${dash_json_NAME}` for its own `name()`, and calls `dash clear` first.

    Add a local helper at the top of the file (a small `program define` or an inline pattern)
    that, given a spec string, yields the substring starting at `"graph_options"` — the
    graph-level slot, because `dash.ado:1503` emits the top-level `"if_expr"` / `"in_expr"`
    after `graph_options`. Use the `strpos` / `substr` technique of
    `test/test_varlist_expansion.cscript:652-657`. Do not use `foreach ... of local` over spec
    text and do not expand spec text inside plain quotes; see `test/cert_helpers.do:10-21` for
    why that breaks.

    Cases, each in `capture { ... }` with a `display` of PASS or a `display as error` of the
    observed values on failure, exactly as `test/test_varlist_expansion.cscript:645-660` does:

      QS-01 (pin, BR-01.3) `dash scatter mpg weight if foreign==1 || lfit mpg weight, name(qs1)`
            rc 0; the spec contains `"if_expr":"foreign==1"`; the graph-level tail does NOT;
            the substring for plot 2 (`lfit`) does not carry it.
      QS-02 (pin, BR-01.3) `dash scatter mpg weight || lfit mpg weight if foreign==1, name(qs2)`
            rc 0; the qualifier is on the lfit segment; the graph-level tail does NOT carry it.
      QS-03 (S1 fix) `dash scatter mpg weight || lfit mpg weight || if foreign==1, name(qs3)`
            rc 0; exactly two `"type":` occurrences; the graph-level tail DOES carry
            `"if_expr":"foreign==1"`; neither plot segment carries an if_expr.
      QS-04 (S1 fix) `dash (scatter mpg weight) (lfit mpg weight) if foreign==1, name(qs4)`
            same assertions as QS-03.
      QS-05 (S1 fix, BR-01.4) `dash (scatter mpg weight) (lfit mpg weight) in 1/60, name(qs5)`
            rc 0; the graph-level tail carries `"in_expr":"1/60"`.
      QS-06 (S1 fix) `dash (scatter mpg weight) (lfit mpg weight) if foreign==1, name(qs6) title("T")`
            rc 0; the graph-level tail carries `"if_expr":"foreign==1"` AND `graph_options`
            still carries `"title":"T"` — the qualifier must not eat the option list.
      QS-07 (S1 fix) `dash (scatter mpg weight if foreign==1) in 1/60, name(qs7)`
            rc 0; the plot segment still carries `"if_expr":"foreign==1"`; the graph-level tail
            carries `"in_expr":"1/60"`; the graph-level `"if_expr"` is empty — the one-segment
            promotion must fill only the slot the command-level qualifier left empty.
      QS-08 (S1 fix) `capture dash (scatter mpg weight) (lfit mpg weight) if nosuchvar==1, name(qs8)`
            `_rc == 111`, matching twoway (RESEARCH §3.4 measured rc 111 for an unknown variable
            name even on layer types that then discard the qualifier).
      QS-09 (pin, documented limit) `capture dash scatter mpg weight || if foreign==1 || lfit mpg weight, name(qs9)`
            `_rc == 198` — only a FINAL `|| if exp` is a command-level qualifier.

    Register the script in `test/run_all_cscripts.do` by copying an existing block verbatim
    (e.g. the `test_parser.cscript` block at `:93-116`) and changing the filename, keeping the
    `capture noisily { do "..." }`, the `capture file close _all`, the `rc == 222` SKIP branch
    and the pass/fail counters. This is required, not optional:
    `test/test_cscript_hygiene.py:132-141` (`TestEveryCscriptIsWiredIntoTheRunner`) asserts every
    `.cscript` filename appears in the runner.

    Run the script and confirm the failures are the RIGHT failures, against 08-01's recorded
    output: QS-01, QS-02 and QS-09 pass; QS-03 fails with r(198) and the message
    "unrecognised plot type 'if'"; QS-04 through QS-07 fail because the graph-level slot is
    empty; QS-08 fails because `_rc` is 0, not 111. A skip is not a pass — read the log and
    confirm each case printed its own line.

    Commit message: describe the new certification script and the runner registration. No
    Claude/Anthropic references (rule 7).
  </action>
  <verify>From `test/`, `arch -arm64 /usr/local/bin/stata-mp -b do test_qualifier_scoping.cscript`; the log shows `QS-01 PASS`, `QS-02 PASS`, `QS-09 PASS` and explicit failures for QS-03…QS-08 (QS-03 naming r(198) / "unrecognised plot type", QS-04…QS-07 naming an empty graph-level slot, QS-08 naming `_rc == 0`). Then `python3 -m pytest test/test_cscript_hygiene.py -q` passes, proving the runner registration.</verify>
  <done>A certification script exists that pins the two forms dash already gets right and fails, for the documented reason, on the six it gets wrong. It is wired into the runner. No product code has changed.</done>
</task>

<task type="auto" id="08-03">
  <name>Give the parser a command-level qualifier channel</name>
  <files>dash_parse.mata, dash.ado</files>
  <action>
    Implement the fix so that every case in `test/test_qualifier_scoping.cscript` passes. Two
    files, one commit.

    **1. `dash_parse.mata`, `_dash_split_segs` (`:355-526`).**

    Declare `string scalar cmd_qual` beside `graph_opts_raw` at `:360`, and initialise
    `cmd_qual = ""` beside `graph_opts_raw = ""` at `:366`.

    PAREN branch (`:388-442`). Add `real scalar tail_start` initialised to `0`. In the
    depth-0 open at `:419-421` set `tail_start = 0` (a new group invalidates any pending tail).
    In the depth-0 close at `:426-433`, after `seg_start = 0`, set `tail_start = i + 1`. In the
    top-level-comma branch at `:435-439`, before `break`, capture the text between the last
    group and the comma:
      `if (tail_start > 0 & i > tail_start) cmd_qual = strtrim(substr(trimmed, tail_start, i - tail_start))`
    After the `while` loop ends without a comma, capture the rest:
      `if (cmd_qual == "" & tail_start > 0) cmd_qual = strtrim(substr(trimmed, tail_start, .))`
    Then guard it — only text that actually begins with the `if` or `in` keyword is a
    qualifier; anything else keeps today's behaviour of being ignored:
      `if (cmd_qual != "" & !regexm(cmd_qual, "^(if|in)[ \t]")) cmd_qual = ""`

    FLAT branch (`:444-511`). Leave the `||` scanner untouched. After the final segment is
    appended at `:503-507`, and before `graph_opts_raw = ""` at `:512`, pop a final
    qualifier-only segment:
      if `n_segs >= 1` and `regexm(segs[n_segs], "^(if|in)[ \t]")`, set
      `cmd_qual = segs[n_segs]`, drop that element (`segs = segs[1..n_segs-1]` when
      `n_segs > 1`, else `segs = J(1, 0, "")`), and decrement `n_segs`.
    Only the LAST segment is eligible, so `scatter … || if … || lfit …` still reaches the
    `_expand_plottype_str` failure and returns r(198) — that is QS-09 and is deliberate.

    The existing `if (n_segs == 0)` error at `:515-518` then correctly rejects a command that is
    nothing but a qualifier.

    Export it: add `st_local("_cmd_qual", cmd_qual)` next to
    `st_local("_graph_opts_raw", graph_opts_raw)` at `:525`.

    **2. `dash.ado`.**

    Add a new parser beside the others, immediately after `_dash_parse_varpart_any` ends at
    `:845` and before the `_dash_plot_opts_to_json` banner at `:848`, mirroring
    `_dash_parse_varpart_std` (`:779-788`) exactly in style:

```stata
// ================================================================
// _dash_parse_cmd_qual  — a COMMAND-LEVEL if/in qualifier
//
// twoway scopes a qualifier to the whole command in two ways: text after
// the last ")" in paren syntax, and a final "|| if exp" segment in bar
// syntax.  Neither is a plot, so neither becomes a segment.  Stata's own
// -syntax- evaluates the expression here, so an unknown variable is r(111)
// and an out-of-range -in- is r(198), exactly as twoway reports them.
// ================================================================
program define _dash_parse_cmd_qual, sclass
    version 16.0
    syntax [if] [in]
    sreturn local if_clause `"`if'"'
    sreturn local in_clause `"`in'"'
end
```

    In `_dash_plot`, after `local gopts_raw \`"\`_graph_opts_raw'"'` at `:1392`, add
    `local cmd_qual \`"\`_cmd_qual'"'`.

    Replace the promotion block at `:1483-1499`. Keep the existing comment and the
    `n_segs == 1` rule — RESEARCH §1.7 (D5) measured that the emitted `bokeh serve` app reads
    **only** graph-scoped `if_expr`, so removing the promotion would break server mode for
    single-layer commands, the one case that works there today. Add the command-level channel
    in front of it and let the promotion fill only what the channel left empty:

```stata
    local if_expr ""
    local in_expr ""
    // A COMMAND-LEVEL qualifier scopes every layer, as twoway does.  It is
    // not a plot and never became a segment; _dash_split_segs hands it over
    // in _cmd_qual.  -syntax- evaluates it here so a bad variable name is
    // r(111) and a bad -in- is r(198), as twoway reports them.
    if `"`cmd_qual'"' != "" {
        sreturn clear
        _dash_parse_cmd_qual `cmd_qual'
        local _cq_if `"`s(if_clause)'"'
        local _cq_in `"`s(in_clause)'"'
        if `"`_cq_if'"' != "" ///
            local if_expr = strtrim(regexr(`"`_cq_if'"', "^[ ]*if[ ]+", ""))
        if `"`_cq_in'"' != "" ///
            local in_expr = strtrim(regexr(`"`_cq_in'"', "^[ ]*in[ ]+", ""))
    }
    if `n_segs' == 1 {
        if `"`if_expr'"' == "" ///
            mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        if `"`in_expr'"' == "" ///
            mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
```

    The keyword-strip regexes are the same ones already used at `:1105-1108`; do not invent a
    new form. Leave `:1500-1503` (the `_dash_json_str` escaping and the `graph_json` assembly)
    untouched.

    Note for the reviewer, in the commit body: the per-plot `if_expr` stays on its segment
    (`dash.ado:1240`, `:1244`) in every case, so when both a command-level and a per-plot
    qualifier are present they compose by AND — the command-level one through
    `_apply_graph_filter` and the per-plot one through the mask section-02 installs. That is
    Stata's measured rule (RESEARCH §3.2, points 2-3). The renderer's guard at
    `dash_render.py:9957` (`if (_p_if and _p_if != _g_if) or ...`) already skips building a
    second, redundant view when the two are identical, which is the promoted single-segment
    case.
  </action>
  <verify>From `test/`, `arch -arm64 /usr/local/bin/stata-mp -b do test_qualifier_scoping.cscript` — all nine cases print PASS and none is skipped. Then `arch -arm64 /usr/local/bin/stata-mp -b do test/run_all_cscripts.do` from the repository root shows no new failures against section-01's committed baseline, with `test_parser.cscript`, `test_varlist_expansion.cscript` and `test_option_report_paren.cscript` still passing. Then `python3 -m pytest test/ -q` matches section-01's baseline counts.</verify>
  <done>A command-level `if`/`in` is captured from both syntaxes and lands in the graph-level slot; `|| if exp` is accepted as twoway accepts it; an unknown variable in a command-level qualifier is r(111); the one-segment promotion still runs and still feeds server mode; and per-plot qualifiers are untouched.</done>
</task>

<task type="auto" id="08-04">
  <name>Pin `by()` panel survival and the first-paint per-panel intersection</name>
  <files>test/test_by_panel_qualifier_survival.py</files>
  <action>
    Test-only task. It records the S2 divergence in the suite so no later change can reintroduce
    Stata's panel deletion, and pins the strict per-panel intersection that RESEARCH §3.6
    measured.

    Create `test/test_by_panel_qualifier_survival.py`. Module docstring must state, in prose:
    (a) Stata's measured behaviour — strict per-panel intersection, empty-intersection panels
    KEPT, and a panel silently DELETED when one layer's qualifier leaves too few rows
    (`insufficient observations`, rc 0); (b) dash's decision (RESEARCH §4.7) to keep the panel,
    warn, and draw the failing layer empty; (c) that the warn-and-empty half is section-07's
    uniform degenerate policy and the drawn-value assertions are section-02's and section-06's,
    so this file asserts panel survival and the first-paint mask only; (d) **the trap** — that
    `test/test_varlist_expansion.py:101`'s `_visible_count` and `test/test_per_plot_qualifier_linking.py:82`'s
    `_visible` read `renderer.view.filter.booleans` and report a computed layer as fully visible
    whatever it drew, so this file never uses them and asserts on source values and registered
    masks instead.

    Follow the conventions of `test/test_per_plot_qualifier_linking.py:29-76`: `sys.path` insert
    of the repository root and of `test/`, `import dash_render as dr`, `from conftest import
    make_data_json`, a module-level DataFrame, and a `_render(tmp_path, ...)` helper that writes
    a spec JSON and a data JSON and returns a rendered `DashRenderer`.

    Build a deterministic frame with a `panel` column of four groups sized so the intersection
    with `foreign==1` is, respectively: 0 rows, 1 row, 3 rows and 5 rows. The 0-row panel is the
    case Stata keeps (RESEARCH §3.6 panels 1 and 2); the 1-row panel is the case Stata deletes.
    Every panel must have at least two rows overall so its scatter is non-trivial.

    Graph spec: `graph_options` carrying `{"name": "g1", "by": "panel"}`, plots
    `[{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
      {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}, "if_expr": "foreign==1"}]`.
    Parameterise the whole file over `link` in `("", "_all")` so both the unlinked path
    (`dash_render.py:11428-11456`, one pre-subset source per panel) and the linked path
    (`:11396-11412` and `:11461-11476`, one shared source plus `panel_view_r`) are covered;
    RESEARCH §1.9 (F-A) is exactly the case where those two paths diverge.

    Tests:

    1. `test_every_panel_survives_a_degenerate_layer_qualifier` — render the graph twice, once
       with the `if_expr` on the lfit layer and once without, and assert
       `len(r._facet_map["g1"])` is equal in both, equal to the number of groups in the data,
       and that `sum(1 for k in r.figures if k.startswith("g1__by__"))` matches. Assert by name
       that the 0-row and 1-row panels are among the keys. The assertion message must say that
       Stata deletes the 1-row panel and dash deliberately does not, citing RESEARCH §4.7.
    2. `test_the_companion_scatter_keeps_its_panel_rows` — for the 1-row-intersection panel,
       take the figure's scatter renderer and assert `len(renderer.data_source.data["mpg"])`
       (unlinked) or the count of `True` in that panel's `panel_view_r` booleans (linked) equals
       the panel's full row count. This is the layer Stata takes down with the panel.
    3. `test_the_registered_mask_is_the_panel_qualifier_intersection` — locate the lfit layer's
       `BooleanFilter` through `r._view_filters` (`dash_render.py:8509-8524` stores
       `(source, filter, member_ids)`), map its `True` positions through the source's
       `__dash_row__` column (`_ROW_ID_COLUMN`, `dash_render.py:591`), and compare the resulting
       row-id set to a set computed independently in the test from the DataFrame —
       `set(df.index[(df.panel == k) & (df.foreign == 1)])` mapped to positions. Assert set
       equality, not counts. Add an inline comment naming why this is not the trap: it asserts
       the mask the renderer built (the mapper's future input), and explicitly not what the
       computed layer drew, which section-02 owns.
    4. `test_an_empty_intersection_panel_is_still_built_with_an_empty_mask` — for the 0-row
       panel the same mask must exist and be all-`False`, and the figure must still be present.
       A missing figure and an absent mask are different failures; assert both separately.

    Do not assert anything about `member_ids` surviving a filter-widget move — that is TR-01.7
    and section-06's test; say so in a comment so the two do not overlap.

    Run the file and confirm every test passes on the current tree — these are pins. Then prove
    they are not certifying nothing by applying each mutation below, one at a time, confirming
    the named test goes red, and reverting:
      - insert `if not any(_mask): continue` in the facet render loop
        (`dash_render.py:11457-11490`) → test 1 and test 4 must fail;
      - delete the `_prev_bools` AND at `dash_render.py:9986-9987` → test 3 must fail for
        `link="_all"` and still pass for `link=""`;
      - change `_register_view_filter`'s call at `:9991-9992` to register no ids → test 3 must
        fail for both.
    Record the three mutation results in the module docstring. Revert every mutation before
    committing; `git diff --stat` must show only the new test file.
  </action>
  <verify>`python3 -m pytest test/test_by_panel_qualifier_survival.py -q` passes for both `link` parameterisations. `git status --short` lists exactly one added file and no modified file. The mutation runs are recorded in the module docstring.</verify>
  <done>The suite now fails if any future change deletes a `by()` panel whose layer qualifier is degenerate, or breaks the first-paint per-panel intersection on either the linked or the unlinked path. The divergence from Stata is recorded in the test file and ready for section-10's `dash.sthlp` and CHANGELOG entries.</done>
</task>

---

**Merge (rule 6 — report, do not run).** After all four tasks land on
`feature/batch4-interactive-layer`:

```
git checkout main && git merge --no-ff feature/batch4-interactive-layer
```
