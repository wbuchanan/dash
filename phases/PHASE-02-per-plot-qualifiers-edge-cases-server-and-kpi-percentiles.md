# Phase 02 — Per-plot qualifiers: edge cases, server and KPI percentiles

**Purpose.** Phase 01 makes a per-plot `if`/`in` qualifier bite where the renderer
can see it. This phase closes the four places where a qualifier never reaches the
renderer at all, and one place where the number a card shows is computed by a
function that is not in scope. Three of the five are in `dash_parse.mata`'s paren
branch, which acts on exactly three characters and silently drops everything else
at depth 0 — so `dash (scatter mpg weight) if foreign==1` and
`dash (scatter mpg weight) garbagetoken` both return `rc=0` and both mean
"draw everything". One is in `dash.ado`, where the JSON escaper is called with
plain double quotes against its own documented usage, so any qualifier containing
a string literal is erased *and* the user's own text chooses the name of the local
macro that gets written. The last is in `DashRenderer._wire_brush_callbacks`,
which assembles the brush callback from a slice of `_FILTER_JS` that stops seven
lines short of `function dash_pctl` — so every `median`, `iqr` and `pNN` KPI
declared `update(brush)` calls an undefined function the moment a user drags a
selection. The phase also carries the regression net that task 06-06 owes under
project rule 8, because the two defects it hunts were both invisible to the tests
that nominally covered them.

---

## At a glance

| | |
|---|---|
| **Items** | 7 (numbered 1–7 below, exactly as handed over) |
| **Functional / deliverable** | 5 functional (1, 3, 4, 5, 7) · 2 deliverable (2, 6) |
| **Effort mix** | small × 4 (3, 4, 5, 7) · medium × 3 (1, 2, 6) · large × 0 |
| **Renderers touched** | `stata` × 4 (1, 3, 4, 5) · `both` × 2 (2, 6) · `standalone` × 1 (7) |
| **Files at the centre** | `dash_parse.mata` (`_dash_split_segs`), `dash.ado` (`_dash_json_str`, `_dash_plot`), `dash_render.py` (`DashRenderer._wire_brush_callbacks`) |
| **Ultraplan tasks discharged** | **06-06** "Carry and apply per-plot if/in qualifiers" (S06) — the edge-case half; **13-04** "Make KPIs show the number the user asked for" (S13) — the brush/percentile residue |
| **Sections advanced** | S06 (06-06 · PARTIAL → the paren-mode and escaping gaps closed), S13 (13-04 · one of the 17 overturned DONE claims) |
| **Depends on** | **Phase 01** — items 2(a)–(d) assert behaviour that only exists once Phase 01's mask threading and server-side qualifier work land. Items 1, 3, 4, 5, 6(a)(b) and 7 are independent of Phase 01 and can start immediately. |
| **Unblocks** | S16-06 / S16-07 release gates (adversarial suite, conformance corpus), and the `dash.sthlp` twoway-parity sentence at `dash.sthlp:128-130`, which cannot be made true until item 1 lands |
| **Project rules in force** | 8 (failing regression test first), 4 (unit test per function), 16 (harden all data inputs), 18 (adversarial cases per input surface) |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`. Where a line was
re-confirmed while writing this document, that is marked explicitly and the
confirmation is read-only.

### The defect family: per-plot `if` on computed layers (REMAINING.md §5)

The headline, item 5 of five:

> 5. **A per-plot `if` qualifier is silently ignored by every computed layer.**
>    `(lfit mpg weight if foreign==1)` draws the *all-rows* fit. Wrong numbers,
>    no warning.

And the blocker section in full — this is the behaviour Phase 01 fixes and this
phase writes the tests for:

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
>
> **Why.** The qualifier is implemented as a `CDSView`/`BooleanFilter` over the
> graph's shared `ColumnDataSource` (`dash_render.py:9957-9990`). That correctly
> restricts which *rows of that source* a glyph draws — but a computed layer
> builds its **own** source from `self.df`, unfiltered, and the view never
> touches it.
>
> This is the worst-shaped defect in the list: a statistical command that
> returns a confidently wrong number, silently. Under project rule 8 it needs a
> failing regression test before the fix.

Appendix A's measurement table for the same task, `06-06 · PARTIAL`:

> **The Python half applies to raw-data layers only, and not to all of those.**
> Measured by rendering `scatter/line/... mpg weight` with and without
> `if_expr: "foreign==1"` and inspecting each renderer's `view.filter.booleans`
> and its source data:
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
>
> `in_expr` has the identical shape (`scatter` viewed, `lfit`/`histogram`
> ignored).

and, from the same Appendix A entry, the two "Remaining" clauses this phase owns:

> 4. Server: `_apply_graph_filter` has **0** occurrences in the emitted app, so
>    none of this exists there.
> 5. The task's explicit test — "`(scatter y x) (scatter y x if foreign)` filters
>    only the second plot; linking still propagates through a qualified plot" —
>    needs to cover a computed layer, which is where it fails.

### Edge case 1 — paren mode drops a *command-level* qualifier

From Appendix B, 06-06:

> **[func · dash.ado · M]** Stop discarding a command-level qualifier in paren
> mode. `_dash_split_segs`'s PAREN branch acts only on `(`, `)` and a depth-0
> `,` (dash_parse.mata:388-441); any other depth-0 text — the `if`/`in` clause
> twoway allows after the last group — falls through `i++` and is lost.

### Edge case 2 — it drops it even when there is only one plot

From Appendix C, 06-06 — this overturns the auditor's own "done" claim:

> **[func · dash.ado · S]** Paren mode loses a trailing qualifier even on a
> SINGLE plot, which the auditor's done_item #2 ("A single-segment
> (command-level) qualifier is still promoted to graph level") claims works.
> It is true only for the un-parenthesised form. Measured: `dash scatter mpg
> weight if foreign==1, name(g4)` -> plots[0].if_expr="foreign==1" and
> graph-level if_expr="foreign==1" (promoted, correct), but `dash (scatter mpg
> weight) if foreign==1, name(g8)` -> rc=0 and the spec is
>
> ```
> {"plots":[{..."if_expr":"","in_expr":""}],"graph_options":{"name":"g8"},"if_expr":"","in_expr":""}
> ```
>
> — the restriction is gone before _dash_plot ever sees it, because
> _dash_split_segs's PAREN branch never captures depth-0 text. … wrapping one
> plot in parentheses must not change what the command means.

Supporting evidence from the help text, quoted in Appendix C's docs item:

> Line 128-130: "For plot types, marker/line/axis options, and {it:if}/{in}
> qualifiers, {cmd:dash} accepts the same syntax as {helpb twoway}." Measured:
> twoway accepts `twoway (scatter mpg weight) (scatter mpg price) if
> foreign==1` with rc=0, dash accepts the same text with rc=0 and drops the
> restriction.

### Edge case 3 — the same hole swallows anything at all

> **[func · dash.ado · S]** `_dash_split_segs`'s paren branch silently
> swallows ANY depth-0 text, not just an if/in clause — a typo'd option
> outside the parentheses is accepted with rc=0 and no message. `dash (scatter
> mpg weight) garbagetoken, name(g9)` returns rc=0 and produces a spec
> identical to the un-garbaged command. The auditor's item 3 asks for a
> `_cmd_qualifier` capture and says dash "should at minimum error rather than
> accept silently", but only for a qualifier; the general case is an
> input-validation hole (CLAUDE.md rule 16) and needs an explicit
> reject-unknown-text path plus an adversarial test, otherwise the qualifier
> capture will simply widen the set of strings that are swallowed.

**Confirmed read-only for this document.** `dash_parse.mata:395-441` is the paren
branch. At depth 0 it recognises `(` (ASCII 40), `)` (41) and `,` (44), plus the
quote-state characters `"` (34) and `` ` `` + `"` (96, 34). The `while` loop's
final statement is a bare `i++`, so every other depth-0 character advances the
cursor and is never recorded in `segs` or in `graph_opts_raw`.

### Edge case 4 — a quoted string in a qualifier erases the qualifier, and picks a macro name

From Appendix C, 06-06 — the highest-severity item in this phase:

> **[func · dash.ado · S]** Fix the silent loss of ANY if/in qualifier that
> contains a double-quoted string, and close the macro-name injection it rests
> on. `dash.ado:1224-1225` call the escaper as `_dash_json_str "`if_expr'"
> _jif` with PLAIN double quotes, contrary to the helper's own documented
> usage at `dash.ado:221`. `_dash_json_str` is `args raw_val out_macro`
> (dash.ado:224-234), so when the expanded value contains a `"` Stata
> re-tokenizes it: the escaped text is truncated at the quote and the macro
> NAME written by `c_local `out_macro'` is taken from the user's own string.
> Result: `"if_expr":""` for every string-valued qualifier, plus a write to an
> attacker-chosen local in `_dash_process_segment`'s frame. Fix both lines to
> the compound-quote form, add the same guard to the helper (reject/ignore an
> out_macro that did not come from the caller), and re-check the other 50 call
> sites (the remaining 12 plain-quote sites, dash.ado:1143-1237, all pass
> variable names, which cannot contain a quote).

The helper's own documented usage, `dash.ado:219-221`:

```
// ================================================================
// _dash_json_str  — simple JSON string escaping in pure Stata
// Usage:  _dash_json_str `"`raw'"' "_escaped"
```

and the two offending call sites, `dash.ado:1223-1225`:

```
    // if/in
    _dash_json_str "`if_expr'" _jif
    _dash_json_str "`in_expr'" _jin
```

**Confirmed read-only for this document.** `dash.ado` has 52 `_dash_json_str`
call sites. 14 use plain double quotes; two of those are lines 1224 and 1225
(the qualifiers). The remaining 12 are at lines 1143, 1148, 1149, 1150, 1154,
1155, 1156, 1157, 1215, 1216, 1236 and 1237, and every one of them passes a
variable name — exactly as REMAINING.md states.

### The 13-04 residue — percentile KPIs are wrong under brushing

`13-04` is one of the 17 DONE claims the adversarial pass overturned:

> | task | what the refutation found |
> |---|---|
> | 13-04 | the brush callback does not carry `dash_pctl`, so percentile KPIs are wrong under brushing |

and REMAINING.md ranks it with the blockers:

> Two of these are functional, not paperwork, and belong beside the four
> blockers: **06-06** (computed layers ignore `if`/`in`) and **13-04**
> (percentile KPIs wrong under brushing).

The mechanism, as handed over in work item 7: *"Make the brush callback carry
`dash_pctl`, so percentile KPIs are right under brushing. Concatenate the
`function dash_pctl` slice into the callback code, or move the definition
somewhere both callbacks see."* — `dash_render.py:11675-11681`, `:7347 onward`.

**Confirmed read-only for this document.** `DashRenderer._wire_brush_callbacks`
(`dash_render.py:11645`) builds the callback source at `:11675-11682`:

```python
        # The helper lives in _FILTER_JS; concatenating puts it in scope
        # without giving the brush path its own copy of the arithmetic.
        _helpers = _FILTER_JS[
            _FILTER_JS.index("// ---- KPI recompute, shared by"):
            _FILTER_JS.index("dash_apply_kpis(new_data,")
        ]
        code = (
            'const ROW_ID = "%s";\n' % _ROW_ID_COLUMN
            + _helpers + _BRUSH_JS
        )
```

The two markers sit at `dash_render.py:7192` and `:7339`. `function dash_pctl`
is defined at `dash_render.py:7347` — **eight lines past the end of the slice.**
Evaluating the two constants and the slice:

```
helpers reference dash_pctl: 5
helpers DEFINE dash_pctl  : False
brush  defines dash_pctl  : False
assembled code defines it : False
assembled code calls it   : 5
```

The five references are inside the shared recompute block at
`dash_render.py:7266-7281`, whose `else` arm handles precisely the statistics
that break:

```javascript
                const s = vals.slice().sort((a, b) => a - b);
                if (stat === 'median') {
                    result = dash_pctl(s, 50);
                } else if (stat === 'iqr') {
                    result = dash_pctl(s, 75) - dash_pctl(s, 25);
                } else {
                    const mp = /^p(\d{1,2}(?:\.\d+)?)$/.exec(stat);
                    if (mp) result = dash_pctl(s, parseFloat(mp[1]));
                }
```

So under `update(brush)` or `update(both)`, a `median`, `iqr`, `p25`, `p75` or
any other `pNN` card raises `ReferenceError: dash_pctl is not defined` on the
first selection change. The comment at `:7267-7270` records that these
statistics *"used to have no branch at all here and fell through to result = 0
on the first filter move"* — this is that defect, displaced from the filter path
to the brush path.

**Why no test caught it.** `test/test_kpi_brush.py` has a class called
`TestTheShippedBrushJsActuallyComputes` whose docstring is *"Run the code users
receive, not a transliteration of it."* Its harness (`test/test_kpi_brush.py:197-229`)
builds the node script like this:

```python
        js = dash_render._FILTER_JS
        helpers = js[js.index("// ---- KPI recompute, shared by"):
                     js.index("dash_apply_kpis(new_data,")]
        pctl = js[js.index("function dash_pctl"):
                  js.index("// agg_sources is a Bokeh model list")]
        ...
        harness = (
            pctl
            + '\nconst ROW_ID = "__dash_row__";\n'
            + helpers
            ...
```

The test supplies `pctl` itself, from a second slice production never takes.
It therefore runs a *superset* of the shipped callback, and its three live cases
(`test_a_selection_gives_the_mean_of_the_selected_rows`,
`test_clearing_the_selection_restores_every_row`, `test_the_title_survives_the_rebuild`)
all exercise `mean`, which never touches `dash_pctl`. The suite is green and the
feature is broken — which is the single most important fact in this phase.

---

## Epics

| epic | goal | items |
|---|---|---|
| **2.A — Paren mode means what it says** | The depth-0 text after the last `)` is captured as a command-level qualifier and applied to every plot; anything that is not a qualifier is rejected with an error instead of being swallowed. | 1, 3, 4 |
| **2.B — A qualifier is data, not Stata source** | A qualifier containing a double-quoted string survives into the spec JSON intact, and cannot choose the name of a macro in `dash.ado`'s frame. | 5, 6 |
| **2.C — Prove it on the artifact the user receives** | Close the 06-06 regression net that rule 8 requires, and fix the percentile KPI defect that survived only because an existing test supplied the missing helper itself. | 2, 7 |

Epics 2.A and 2.B are both `dash_parse.mata`/`dash.ado` work on the same code
path and should be done by the same developer in that order — 2.B's fix makes
2.A's new `_cmd_qualifier` safe to carry a string literal. Epic 2.C is Python
and test work and can run in parallel, except for items 2(a)–(d), which depend
on Phase 01.

---

## User stories

### Epic 2.A — Paren mode means what it says

**US-2.A.1** — *As a Stata user pasting a `twoway` command into `dash`, I want a
trailing `if`/`in` qualifier written after the last parenthesised plot to
restrict every layer, so that the dashboard shows the same subsample the
equivalent `twoway` graph shows.*

- **Given** the auto dataset and the command
  `dash (scatter mpg weight) (scatter mpg price) if foreign==1, name(g)`
  **When** the command runs
  **Then** `rc == 0`, the registered spec's graph-level `if_expr` is
  `foreign==1`, and the built dashboard draws 22 points per layer, not 74.
- **Given** `dash (scatter mpg weight) in 1/10, name(g)`
  **When** the command runs
  **Then** the graph-level `in_expr` is `1/10` and the figure draws 10 rows.

**US-2.A.2** — *As a Stata user, I want wrapping a single plot in parentheses to
leave the meaning of my command unchanged, so that I do not have to know which
of two equivalent spellings dash actually honours.*

- **Given** `dash scatter mpg weight if foreign==1, name(g4)` and
  `dash (scatter mpg weight) if foreign==1, name(g8)`
  **When** both run against the same data
  **Then** both specs carry `foreign==1` at graph level, and the two rendered
  figures contain the same number of visible rows.
- **Given** the measurement recorded in REMAINING.md — that `g8` today produces
  `"if_expr":""` at every level
  **When** the regression test for this story runs against `ca5fe35`
  **Then** it fails; and against the fix, it passes.

**US-2.A.3** — *As a Stata user who mistypes an option outside the parentheses,
I want dash to tell me, so that I do not ship a dashboard built from a command
dash only half-read.*

- **Given** `dash (scatter mpg weight) garbagetoken, name(g9)`
  **When** the command runs
  **Then** it exits non-zero (rc 198) with a message naming `garbagetoken`, and
  no graph named `g9` is registered.
- **Given** `dash (scatter mpg weight) if foreign==1, name(g)`
  **When** the command runs
  **Then** the same validation path accepts it — the reject rule must not fire
  on a legitimate qualifier.

**US-2.A.4** — *As a package maintainer, I want the reject path to run on
already-UTF-8-validated text and to look only at depth-0 spans, so that closing
this hole does not create a new way to reach the parser with unchecked input
(project rule 16).*

- **Given** any command whose parenthesised segments contain quoted text with
  commas, parentheses or the word `if` inside the quotes
  **When** the split runs
  **Then** the depth-0 classifier sees none of that text and the command still
  parses as it does today.

### Epic 2.B — A qualifier is data, not Stata source

**US-2.B.1** — *As a Stata user filtering on a string variable, I want
`if make=="Volvo 260"` to survive into the dashboard, so that my dashboard shows
the rows I asked for instead of all of them.*

- **Given** `dash scatter mpg weight if foreign==1 & make=="Volvo 260", name(g)`
  **When** the spec is registered
  **Then** it contains `"if_expr":"foreign==1 & make==\"Volvo 260\""` and `dash
  build` renders exactly the matching rows.
- **Given** the same qualifier written in the `||` form and in the paren form
  **When** each is registered
  **Then** all three specs carry the identical escaped `if_expr`.

**US-2.B.2** — *As a package maintainer, I want a crafted qualifier to be unable
to write a local in `dash.ado`'s own frame, so that a user's data cannot steer
the command's control flow (project rules 16 and 18).*

- **Given** `dash scatter mpg weight if make=="xvar zz", name(g)`
  **When** the spec is registered
  **Then** the spec's `"xvar"` key still holds `weight`, and no local named
  `xvar` in `_dash_process_segment`'s frame was overwritten by the string.
- **Given** `dash scatter mpg weight if make=="_opts_json zz", name(g)`
  **When** the spec is registered
  **Then** the spec parses as JSON and `"options"` is unchanged.
- **Given** a call `_dash_json_str "x" "9bad name"` with an out-macro name that
  is not a legal Stata local name
  **When** the helper runs
  **Then** it exits with an error instead of executing `c_local` on it.

### Epic 2.C — Prove it on the artifact the user receives

**US-2.C.1** — *As a dashboard viewer dragging a box-select over a scatter, I
want a median or p75 card to update to the median or p75 of what I selected, so
that the card agrees with what I am looking at.*

- **Given** a dashboard with `dash kpi mpg, stat(p75) update(brush)`
  **When** the viewer selects a subset of points
  **Then** the card shows the Stata-rule p75 of the selected rows, and the
  browser console reports no `ReferenceError`.
- **Given** the same dashboard
  **When** the viewer clears the selection
  **Then** the card returns to the p75 of every row (the documented
  empty-selection fallback, `test/test_kpi_brush.py:171`).
- **Given** `stat(median)` and `stat(iqr)` cards
  **When** either is brushed
  **Then** both recompute, because all three go through the same `else` arm at
  `dash_render.py:7266-7281`.

**US-2.C.2** — *As a package maintainer, I want the brush path's JavaScript to
be tested exactly as shipped, so that a test cannot pass by supplying a helper
production does not.*

- **Given** `test/test_kpi_brush.py`'s node harness
  **When** it is rebuilt to use the *same* string `_wire_brush_callbacks`
  assembles
  **Then** the p75 case fails against `ca5fe35` with a `ReferenceError`, and
  passes against the fix.

**US-2.C.3** — *As a `dash serve` operator, I want a per-plot qualifier to
behave the same in the served app as in the standalone HTML, so that switching
output mode does not change the numbers.*

- **Given** a spec with a per-plot `if_expr` on a computed layer
  **When** it is rendered standalone and built through `ServerAppBuilder`
  **Then** the parity test in `test/test_mode_parity.py` reports the same fitted
  values for both.

**US-2.C.4** — *As a package maintainer, I want per-plot `in_expr`, linked
`by()` panels and linked graph-level qualifiers covered by tests, so that a
behaviour measured working today cannot regress unnoticed.*

- **Given** `in_expr` on the second of two plots
  **When** the figure is rendered
  **Then** only the second layer is shortened — asserted, not assumed.

---

## Business requirements

Each is testable as written; the test that proves it is named in the test plan.

| id | requirement |
|---|---|
| **BR-02.1** | A command-level `if`/`in` qualifier written after the last parenthesised plot group restricts **every** layer of the graph, matching `twoway` semantics for the same text. |
| **BR-02.2** | Wrapping a single plot in parentheses does not change what the command means: `dash (P) if E` and `dash P if E` produce figures with the same visible rows. |
| **BR-02.3** | Any depth-0 text in paren mode that is not a qualifier and not the graph-options comma is **rejected with a non-zero rc and a message naming the offending text**. dash never accepts a command it has only partly read. |
| **BR-02.4** | A qualifier containing a double-quoted string literal reaches the spec JSON intact, escaped, and filters the rendered figure to exactly the matching rows — in the flat, `||` and paren forms alike. |
| **BR-02.5** | No user-supplied text can determine the name of a macro `dash.ado` writes. `_dash_json_str` writes only to a macro name its caller chose and that is a legal Stata local name. |
| **BR-02.6** | A crafted qualifier cannot change any other field of the spec, and cannot make the spec unparseable as JSON. |
| **BR-02.7** | A KPI declared `update(brush)` or `update(both)` with a percentile-family statistic (`median`, `iqr`, `pNN`) shows the correct value for the brushed selection, and the empty-selection fallback still restores every row. |
| **BR-02.8** | Stata's percentile rule exists in exactly **one** place in the shipped JavaScript. No path gets a private copy that can drift from `_stata_percentile` in Python. |
| **BR-02.9** | Every JavaScript test that claims to run the shipped callback runs the string production assembles, with nothing added. |
| **BR-02.10** | Every gap named in item 2 has a test that fails before its fix and passes after (project rule 8), and every new Stata-side helper has a unit test (project rule 4). |
| **BR-02.11** | Each new input surface introduced by this phase (the depth-0 classifier, the hardened escaper) has at least three adversarial cases covering auth/parse bypass, injection and resource exhaustion (project rule 18). |

---

## Technical requirements

### 2.A — `_dash_split_segs`, `dash_parse.mata`

**TR-02.1 — where the text is lost.** `_dash_split_segs(string scalar input)`
begins at `dash_parse.mata:355`. The paren branch is entered when the first
non-white character is `(` (ASCII 40) and runs `dash_parse.mata:386-441`. Inside
the `while (i <= len)` loop, depth-0 handling is exactly:

| char | code | action |
|---|---|---|
| `"` | 34 | enter/leave `in_dq` |
| `` ` `` followed by `"` | 96, 34 | enter `in_cq`; leaves on `"'` |
| `(` | 40 | `depth==0` → `seg_start = i+1; depth = 1`; else `depth++` |
| `)` | 41 | `depth--`; at `depth==0` push `substr(trimmed, seg_start, i - seg_start)` onto `segs` |
| `,` | 44 | at `depth==0` → `graph_opts_raw = strtrim(substr(trimmed, i+1, .))`, `break` |
| anything else | — | falls through to the loop's trailing `i++` and is **discarded** |

**TR-02.2 — capture.** Track the index at which `depth` last returned to 0
(call it `last_close`). When the loop ends — either at the depth-0 `,` or at
`i > len` — take `tail = strtrim(substr(trimmed, last_close + 1, stop - last_close - 1))`,
where `stop` is the comma's index or `len + 1`. `tail` is the depth-0 text. It
must be computed from the *trimmed* input so column arithmetic matches the rest
of the function, and it must never include text seen while `in_dq` or `in_cq`
was set.

**TR-02.3 — classify.** If `tail == ""`, behave exactly as today. Otherwise:

- if `tail` matches `^(if|in)[ \t]` (case-sensitive, Stata keywords are lower
  case here), return it as the command-level qualifier;
- otherwise `errprintf` naming the offending text and `exit(198)`. Use the same
  message shape the function already uses for the empty-specification case at
  `dash_parse.mata:369-372` (`errprintf("dash: ...\n"); exit(198)`).

The classifier must not try to *parse* the qualifier — that is `syntax`'s job on
the Stata side. It decides only "qualifier" vs "not a qualifier".

**TR-02.4 — return it.** `_dash_split_segs` currently sets `_n_segs`,
`_seg_1..N` and `_graph_opts_raw`. Add `_cmd_qualifier`, set to `tail` (or `""`).
Set it in both branches so flat mode's callers see a defined local.

**TR-02.5 — consume it.** `_dash_plot` (`dash.ado:1377`) reads the new local and
splits it into `if`/`in` parts using the same `regexr` strip that
`dash.ado:1099-1109` already applies to `s(if_clause)`/`s(in_clause)`:

```
    local if_expr = strtrim(regexr(`"`if_cl'"', "^[ ]*if[ ]+", ""))
    local in_expr = strtrim(regexr(`"`in_cl'"', "^[ ]*in[ ]+", ""))
```

The value is written into the graph-level `if_expr`/`in_expr` in the graph-JSON
assembly at `dash.ado:1488-1503`.

**TR-02.6 — interaction with the existing promotion gate.** `dash.ado:1496` is:

```
    if `n_segs' == 1 {
        mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
```

with the comment above it (`dash.ado:1490-1495`) explaining why promotion is
gated on a single segment. A command-level qualifier captured by TR-02.4 must
take precedence over — and must not be duplicated by — this promotion: set
`if_expr`/`in_expr` from `_cmd_qualifier` **before** the gate, and skip the
`_dash_json_get_str` promotion when `_cmd_qualifier` is non-empty. In paren mode
with one segment there is nothing to promote anyway (the segment's own
`if_expr` is `""`), so the two paths cannot both fire on the same text; the
ordering requirement is about not regressing the flat single-segment case.

**TR-02.7 — the single-plot equivalence, exactly.** After the fix:

| command | graph-level `if_expr` | `plots[0].if_expr` |
|---|---|---|
| `dash scatter mpg weight if foreign==1, name(g4)` | `foreign==1` (promoted) | `foreign==1` |
| `dash (scatter mpg weight) if foreign==1, name(g8)` | `foreign==1` (captured) | `""` |

The `plots[0]` column differs because in the flat form Stata's `syntax` binds
the qualifier inside the segment; in the paren form the qualifier was never part
of a segment. The rendered figures must nonetheless be identical, because
`_apply_graph_filter` shortens the graph frame before any layer is built. Record
this asymmetry in `dash.sthlp` rather than forcing the spec shapes to match.

**TR-02.8 — reject-unknown-text, measured target.** Today
`dash (scatter mpg weight) garbagetoken, name(g9)` returns `rc=0` and a spec
identical to the un-garbaged command. After the fix it returns `rc=198` and
registers nothing. The check runs after `_dash_check_utf8` (`dash.ado:1384`), so
the classifier only ever sees validated UTF-8 (project rule 16).

### 2.B — `_dash_json_str` and its qualifier call sites, `dash.ado`

**TR-02.9 — the helper.** `dash.ado:219-234`:

```
program define _dash_json_str
    version 16.0
    args raw_val out_macro
    local v = subinstr(`"`raw_val'"', `"\"', `"\\"', .)
    local v = subinstr(`"`v'"', `"""', `"\""', .)
    local v = subinstr(`"`v'"', char(9),  `"\t"', .)
    local v = subinstr(`"`v'"', char(10), `"\n"', .)
    local v = subinstr(`"`v'"', char(13), `"\r"', .)
    c_local `out_macro' `"`v'"'
end
```

`args` splits on whitespace after macro expansion, so a `raw_val` passed in
plain double quotes that itself contains a `"` is re-tokenised: `raw_val` gets
the text up to the embedded quote and `out_macro` gets the next token — a word
from the user's own string. `c_local` then writes to that name.

**TR-02.10 — fix the two call sites.** `dash.ado:1224-1225` become:

```
    _dash_json_str `"`if_expr'"' _jif
    _dash_json_str `"`in_expr'"' _jin
```

This is the form the helper documents at `dash.ado:221`.

**TR-02.11 — harden the helper itself.** Before `c_local`, validate the name:

```
    if !regexm(`"`out_macro'"', "^[A-Za-z_][A-Za-z0-9_]{0,30}$") {
        display as error "_dash_json_str: illegal target macro name"
        exit 198
    }
```

Stata local names are at most 31 characters. The guard must be added *and* the
call sites fixed — the call-site fix removes the vector, the guard removes the
class.

**TR-02.12 — the other call sites.** `dash.ado` has 52 `_dash_json_str` calls.
14 use plain double quotes. After TR-02.10 the remaining 12 are at
`dash.ado:1143, 1148, 1149, 1150, 1154, 1155, 1156, 1157, 1215, 1216, 1236,
1237` — all within `dash.ado:1143-1237` and all passing variable names, which
cannot contain a quote. Leave them, but add a comment at the helper naming the
invariant so a future variable-name-like argument does not quietly become
user-controlled.

**TR-02.13 — what lands in the JSON.** The segment assembly at
`dash.ado:1236-1244` emits

```
{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}
```

so after the fix `if make=="Volvo 260"` must appear as
`"if_expr":"make==\"Volvo 260\""`. The graph-level promotion at
`dash.ado:1497-1498` reads it back with `_dash_json_get_str`, whose own comment
at `dash.ado:1486-1487` states it "correctly handles `\"` escape sequences
inside the value" — so the escaped form must round-trip through it unchanged.
The Python end reads the key at `dash_render.py:9951`.

**TR-02.14 — Python side is already correct and must stay that way.**
`test/test_security_surface.py:164-199` (`TestIfQualifierLeavesStringLiteralsAlone`)
already proves `dash_render._stata_if_to_pandas` leaves string literals alone,
including `make == "inlist(a,b)"` and `make == "missing(z)"`. Those tests call
the translator directly and never travel through `dash.ado`, which is why they
did not catch this defect; item 6 adds the missing half at the Stata boundary.
Do not weaken the existing class.

### 2.C — the brush callback and the regression net

**TR-02.15 — the defect, precisely.**
`DashRenderer._wire_brush_callbacks` (`dash_render.py:11645`) slices
`_FILTER_JS` between the markers at `dash_render.py:7192`
(`// ---- KPI recompute, shared by the filter path and the brush path ----`)
and `:7339` (`dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);`), then
concatenates `_BRUSH_JS` (`dash_render.py:7513`). `function dash_pctl` is
defined at `dash_render.py:7347-7359`, outside both. The assembled `code` at
`dash_render.py:11679-11682` therefore contains **4 calls and 0 definitions** of
`dash_pctl` (`dash_pctl(s, 50)` at `:7275`, `dash_pctl(s, 75)` and
`dash_pctl(s, 25)` at `:7277`, `dash_pctl(s, parseFloat(mp[1]))` at `:7280`; a
fifth occurrence of the token, at `:7267`, is inside a comment). The two further
calls in `_FILTER_JS`, `dash_pctl(sorted, 25)` and `dash_pctl(sorted, 75)` at
`:7474-7475`, sit *after* the slice's end marker and are not carried either.

**TR-02.16 — the fix, and the constraint that shapes it.** Three test files take
four slices of `_FILTER_JS` by literal marker text and will break if the markers
move:

| file:line | slice |
|---|---|
| `test/test_kpi_values.py:275` | `"function dash_pctl"` … `"// agg_sources is a Bokeh model list"` |
| `test/test_kpi_values.py:501` | same |
| `test/test_statistical_defaults.py:283` | same |
| `test/test_kpi_brush.py:205-208` | both slices (`helpers` at `:205-206`, `pctl` at `:207-208`) |

and `test/test_kpi_brush.py:159-165` asserts
`(_FILTER_JS + _BRUSH_JS).count("function dash_pctl") == 1`, so a second copy is
forbidden by test.

- **Rejected: move the definition above `dash_render.py:7192`.** The
  `"function dash_pctl"` … `"// agg_sources…"` slice would then span the whole
  KPI recompute block, including the top-level call
  `dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);` at `:7339`, which
  throws under the node harnesses because `new_data` is undefined there. Three
  test files break.
- **Preferred: hoist to a constant.** Define `_PCTL_JS` holding
  `function dash_pctl(...) {...}` (`dash_render.py:7346-7359`, including the
  six-line comment above it that ties the rule to `_stata_percentile`),
  interpolate it into `_FILTER_JS` at its present position so every existing
  marker and slice still resolves identically, and prepend `_PCTL_JS` in
  `_wire_brush_callbacks`:

  ```python
        code = (
            'const ROW_ID = "%s";\n' % _ROW_ID_COLUMN
            + _PCTL_JS + _helpers + _BRUSH_JS
        )
  ```

  `_FILTER_JS + _BRUSH_JS` still contains the definition exactly once, so
  `test/test_kpi_brush.py:160` still passes, and the assembled callback contains
  it exactly once too.
- **Acceptable alternative: widen the slice in place** by adding a second slice
  `_FILTER_JS[index("function dash_pctl"):index("// Stata's kernels")]`
  (`dash_render.py:7347` … `:7360`) and concatenating it. Cheaper, but it adds a
  fourth marker dependency; if this is chosen, BR-02.9's marker test becomes
  mandatory rather than advisory.

**TR-02.17 — the statistics affected.** `dash_render.py:7266-7281`. `median`
(`dash_pctl(s, 50)`), `iqr` (`dash_pctl(s, 75) - dash_pctl(s, 25)`) and every
`pNN` matched by `/^p(\d{1,2}(?:\.\d+)?)$/`. `count`, `mean`, `sum`, `min`,
`max`, `sd`, `var`, `cv` and `skewness` are computed inline above and are
unaffected — which is why the existing mean-only brush tests pass.

**TR-02.18 — do not duplicate the rule.** `dash_pctl`'s comment
(`dash_render.py:7341-7346`) states the constraint: *"This must stay identical to
`_stata_percentile()` in Python, because the KDE bandwidth is derived from it and
the two curves have to coincide."* Whatever mechanism TR-02.16 chooses, there
must remain exactly one definition in the shipped document.

**TR-02.19 — the regression net's server half.** Item 2(c) asks for a
server-mode parity test that the generated app applies a per-plot qualifier.
Appendix A records that `_apply_graph_filter` has **0** occurrences in the
emitted app, and Appendix C records that the emitted plot loop calls module-level
`_compute_*` helpers on the graph-level dataframe rather than `GlyphMapper`.
That test therefore cannot pass until Phase 01's server work lands; write it
`xfail(strict=True)` in this phase so it flips to a failure the moment the
behaviour arrives without the test being updated.

**TR-02.20 — the regression net's existing state.**
`test/test_varlist_expansion.cscript` V2-11 (`:624-667`) asserts only on the
registered spec string (`strpos` over `${dash_json_v2if1}`), never on a rendered
figure. `test/test_varlist_expansion.py:334` and `:354` render, but only
`scatter`. `test/test_per_plot_qualifier_linking.py` covers the linked/unlinked
shared-source cases for `scatter` only
(`TestALinkedLayerStaysOnTheSharedSource`, `TestTheUnlinkedCaseIsUnchanged`,
`TestItComposesWithAGraphLevelQualifier`). None of them touches a computed
layer, `in_expr`, or server mode.

---

## Work items

Every item below is reproduced with the kind/renderer/effort tag, the *Where*
and the evidence it was handed over with. Nothing is merged or dropped.

---

### Item 1 — Stop discarding a command-level qualifier in paren mode
`[functional · stata · medium]` · origin **06-06** · Appendix B

Stop discarding a command-level qualifier in paren mode. `_dash_split_segs`'s
PAREN branch acts only on `(`, `)` and a depth-0 `,` (dash_parse.mata:388-441);
any other depth-0 text — the `if`/`in` clause twoway allows after the last group
— falls through `i++` and is lost. Capture the depth-0 text between the last `)`
and the graph-options comma, hand it back as a new `_cmd_qualifier` local, and
have `_dash_plot` (dash.ado:1377) write it to the graph-level
`if_expr`/`in_expr` so it applies to every plot. Until then dash should at
minimum error rather than accept silently.

**Where:** `dash_parse.mata:_dash_split_segs (355; paren branch 386-441);
dash.ado:_dash_plot (1377), graph-JSON assembly at 1488-1503`

**Requirements:** TR-02.1 – TR-02.6. **Stories:** US-2.A.1.

---

### Item 2 — The regression tests rule 8 requires for every 06-06 gap
`[deliverable · both · medium]` · origin **06-06** · Appendix B

Add the regression tests project rule 8 requires for each gap above: (a) a
per-plot qualifier on each computed type asserting the fit/band/bin/density
matches the qualified subsample — test/test_per_plot_qualifier_linking.py and
test/test_varlist_expansion.py currently exercise `scatter` only; (b) per-plot
`in_expr` (measured working, untested); (c) a server-mode parity test that the
generated app applies a per-plot qualifier; (d) a linked-by() /
linked-graph-level computed-layer test; (e) a cscript case for
`dash (plot) (plot) if <expr>` and `... in 1/10` in paren mode. V2-11 in
test/test_varlist_expansion.cscript checks only the spec JSON, never a rendered
figure.

**Where:** `test/test_per_plot_qualifier_linking.py,
test/test_varlist_expansion.py:test_second_plot_if_expr_filters_only_the_second_plot
(334) and :test_first_plot_if_expr_does_not_leak_onto_later_plots (354),
test/test_varlist_expansion.cscript:V2-11 (624-667), test/test_mode_parity.py,
test/test_statistical_truth.py`

**Requirements:** TR-02.19, TR-02.20; BR-02.10. **Stories:** US-2.C.3, US-2.C.4.
**Note:** (a)–(d) assert Phase 01 behaviour; (e) asserts this phase's item 1 and
item 3.

---

### Item 3 — Paren mode loses a trailing qualifier even on a single plot
`[functional · stata · small]` · origin **06-06** · Appendix C

Paren mode loses a trailing qualifier even on a SINGLE plot, which the auditor's
done_item #2 ("A single-segment (command-level) qualifier is still promoted to
graph level") claims works. It is true only for the un-parenthesised form.
Measured: `dash scatter mpg weight if foreign==1, name(g4)` ->
plots[0].if_expr="foreign==1" and graph-level if_expr="foreign==1" (promoted,
correct), but `dash (scatter mpg weight) if foreign==1, name(g8)` -> rc=0 and
the spec is
`{"plots":[{..."if_expr":"","in_expr":""}],"graph_options":{"name":"g8"},"if_expr":"","in_expr":""}`
— the restriction is gone before _dash_plot ever sees it, because
_dash_split_segs's PAREN branch never captures depth-0 text. Fix belongs with the
`_cmd_qualifier` work the auditor scoped, but it needs its own case: wrapping one
plot in parentheses must not change what the command means. Add the case to
test/test_varlist_expansion.cscript beside V2-11.

**Where:** `dash_parse.mata:_dash_split_segs (355; paren branch 386-441);
dash.ado:1496 (`if `n_segs' == 1` promotion gate);
test/test_varlist_expansion.cscript:V2-11`

**Requirements:** TR-02.6, TR-02.7. **Stories:** US-2.A.2.

---

### Item 4 — The paren branch swallows any depth-0 text, not just a qualifier
`[functional · stata · small]` · origin **06-06** · Appendix C

`_dash_split_segs`'s paren branch silently swallows ANY depth-0 text, not just an
if/in clause — a typo'd option outside the parentheses is accepted with rc=0 and
no message. `dash (scatter mpg weight) garbagetoken, name(g9)` returns rc=0 and
produces a spec identical to the un-garbaged command. The auditor's item 3 asks
for a `_cmd_qualifier` capture and says dash "should at minimum error rather than
accept silently", but only for a qualifier; the general case is an
input-validation hole (CLAUDE.md rule 16) and needs an explicit
reject-unknown-text path plus an adversarial test, otherwise the qualifier
capture will simply widen the set of strings that are swallowed.

**Where:** `dash_parse.mata:_dash_split_segs (355; paren branch 386-441);
test/test_varlist_expansion.cscript`

**Requirements:** TR-02.3, TR-02.8; BR-02.3, BR-02.11. **Stories:** US-2.A.3,
US-2.A.4.

---

### Item 5 — The quoted-string qualifier loss, and the macro-name injection under it
`[functional · stata · small]` · origin **06-06** · Appendix C

Fix the silent loss of ANY if/in qualifier that contains a double-quoted string,
and close the macro-name injection it rests on. `dash.ado:1224-1225` call the
escaper as `_dash_json_str "`if_expr'" _jif` with PLAIN double quotes, contrary
to the helper's own documented usage at `dash.ado:221`
(``Usage: _dash_json_str `"`raw'"' "_escaped"``). `_dash_json_str` is
`args raw_val out_macro` (dash.ado:224-234), so when the expanded value contains
a `"` Stata re-tokenizes it: the escaped text is truncated at the quote and the
macro NAME written by `c_local `out_macro'` is taken from the user's own string.
Result: `"if_expr":""` for every string-valued qualifier, plus a write to an
attacker-chosen local in `_dash_process_segment`'s frame. Fix both lines to the
compound-quote form, add the same guard to the helper (reject/ignore an
out_macro that did not come from the caller), and re-check the other 50 call
sites (the remaining 12 plain-quote sites, dash.ado:1143-1237, all pass variable
names, which cannot contain a quote).

**Where:** `dash.ado:1224, dash.ado:1225 (call sites), dash.ado:219-234
(_dash_json_str), dash.ado:1093-1106 (if_cl/if_expr capture), dash.ado:1240/1244
(segment JSON assembly)`

**Requirements:** TR-02.9 – TR-02.14; BR-02.4, BR-02.5, BR-02.6.
**Stories:** US-2.B.1, US-2.B.2.

---

### Item 6 — The two adversarial/regression tests the injection requires
`[deliverable · both · medium]` · origin **06-06** · Appendix C

Add the two adversarial/regression tests that the injection above requires under
project rules 8 and 18: (a) a cscript asserting that
`dash scatter y x if svar=="text"` (and the `||` and paren forms) puts
`"if_expr":"svar==\"text\""` in the registered spec and that `dash build` then
renders only the matching rows; (b) an adversarial case asserting that a crafted
qualifier cannot change any other spec field — e.g. `if make=="xvar zz"` must not
alter `"xvar"`, and `if make=="_opts_json zz"` must not produce unparseable JSON.
Neither exists: no test in the tree uses a quoted-string qualifier, and the
security suites never touch `if_expr`.

**Where:** `test/test_security_surface.py, test/test_adversarial.cscript,
test/test_varlist_expansion.cscript, test/test_per_plot_qualifier_linking.py`

**Requirements:** BR-02.4, BR-02.6, BR-02.11; TR-02.13, TR-02.14.
**Stories:** US-2.B.1, US-2.B.2.

---

### Item 7 — Make the brush callback carry `dash_pctl`
`[functional · standalone · small]` · origin **S13 (13-04)** · main body

Make the brush callback carry `dash_pctl`, so percentile KPIs are right under
brushing. Concatenate the `function dash_pctl` slice into the callback code, or
move the definition somewhere both callbacks see.

**Where:** `dash_render.py:11675-11681, :7347 onward`

**Requirements:** TR-02.15 – TR-02.18; BR-02.7, BR-02.8, BR-02.9.
**Stories:** US-2.C.1, US-2.C.2.

---

## Test plan

Project rule 8 governs the order: **the failing test is written and seen to
fail before the fix exists.** Project rule 4 governs the coverage: every
function this phase touches or adds gets a unit test. Every test below names
the file it goes in and how to prove it is not vacuous.

### Epic 2.A — Paren mode means what it says

**Write first (must fail at `ca5fe35`).**

| id | file | case | fails today because |
|---|---|---|---|
| V2-13 | `test/test_varlist_expansion.cscript` | `dash (scatter mpg weight) (scatter mpg price) if foreign==1, name(v2q1)` → assert graph-level `"if_expr":"foreign==1"` in `${dash_json_v2q1}` | the tail is dropped; graph-level `if_expr` is `""` |
| V2-14 | `test/test_varlist_expansion.cscript` | `dash (scatter mpg weight) if foreign==1, name(v2q2)` → same assertion, plus `assert` the spec is **not** byte-equal to the spec of the same command without the qualifier | REMAINING.md's measured spec for `g8` has `"if_expr":""` at every level |
| V2-15 | `test/test_varlist_expansion.cscript` | `dash (scatter mpg weight) in 1/10, name(v2q3)` → graph-level `"in_expr":"1/10"` | same code path |
| P2-86 | `test/test_adversarial.cscript` | `capture noisily dash (scatter mpg weight) garbagetoken, name(v2q4)` → `assert _rc == 198`; `assert "${dash_json_v2q4}" == ""` | returns `rc=0` and registers a spec identical to the un-garbaged command |

**Unit tests (rule 4).**

- `test/test_varlist_expansion.cscript`: a direct Mata unit test of
  `_dash_split_segs` — call it on `(scatter a b) if x==1`, `(scatter a b) in 1/5`,
  `(scatter a b), name(g)`, `(scatter a b) if x=="a, b" ` and
  `(scatter a b) junk`, and assert `_cmd_qualifier` and the rc for each. This is
  the only place the classifier's own behaviour is pinned.
- A case with a comma and a `)` **inside** a double-quoted string within a
  segment — `(scatter mpg weight if make=="a, b)")` — asserting the segment
  count is 1 and `_cmd_qualifier` is empty. This proves the classifier reads
  only genuine depth-0 spans (TR-02.2, US-2.A.4).

**Integration.**

- `test/test_varlist_expansion.py`: render the paren-form command end to end and
  assert every layer draws the qualified row count (22 of 74 for
  `if foreign==1` on the auto data), mirroring the existing
  `test_second_plot_if_expr_filters_only_the_second_plot` (`:334`) shape.
- Run the conformance corpus; a command that previously parsed must still parse.
  A new `r(198)` anywhere in the corpus means the classifier is too strict.

**Adversarial (rule 18), in `test/test_adversarial.cscript`.**

1. *Parse bypass* — `dash (scatter mpg weight) iffy foreign==1, name(g)` must be
   rejected: `iffy` is not `if` followed by whitespace.
2. *Injection* — `dash (scatter mpg weight) if foreign==1 ", name(x)" , name(g)`
   must not let the quoted fragment become graph options; assert the graph is
   named `g`.
3. *Resource exhaustion* — 100 nested parens (the shape `P2-83` already uses)
   with a trailing qualifier must still terminate with a graceful error, not a
   hang; the capture must not be quadratic in `len`.

**Non-vacuity by mutation.** Delete the `exit(198)` from the classifier →
`P2-86` must fail. Change the classifier's accept pattern from `^(if|in)[ \t]`
to `.*` → the *parse bypass* adversarial case must fail. Revert the `_dash_plot`
consumption (TR-02.5) so `_cmd_qualifier` is captured and then ignored → V2-13,
V2-14 and V2-15 must fail while the Mata unit test still passes, which is how
you tell a capture bug from a consumption bug.

### Epic 2.B — A qualifier is data, not Stata source

**Write first (must fail at `ca5fe35`).**

| id | file | case | fails today because |
|---|---|---|---|
| V2-16 | `test/test_varlist_expansion.cscript` | `dash scatter mpg weight if make=="Volvo 260", name(q1)` → assert `strpos(spec, `"if_expr":"make==\"Volvo 260\""`) > 0` | `args` re-tokenisation truncates at the quote; the key is `"if_expr":""` |
| V2-17 | same | the `||` form and the paren form of the same command → identical escaped `if_expr` | same |
| P2-87 | `test/test_adversarial.cscript` | `dash scatter mpg weight if make=="xvar zz", name(q2)` → assert the spec's `"xvar"` is still `weight`; and `if make=="_opts_json zz"` → assert the spec parses (`mata: _dash_json_get_str(...)` returns without error) | `c_local` writes to a macro named from the user's string |
| — | `test/test_security_surface.py` | a Python-side unit test that a spec carrying `"if_expr":"make==\"Volvo 260\""` renders exactly the matching rows through `_stata_if_to_pandas` and `_apply_graph_filter` | asserts the downstream half stays correct once the Stata half is fixed |

**Unit tests (rule 4).** A dedicated cscript block for `_dash_json_str`:

- `_dash_json_str `"a\"b"' out` → `out == "a\\\"b"` (the escaping still works);
- `_dash_json_str `"a"b"' _jif` with the compound-quote call form → no stray
  local is created in the caller's frame; assert with
  `capture confirm existence` on a probe name;
- `_dash_json_str "x" "9illegal"` → `_rc == 198` (TR-02.11);
- `_dash_json_str "x" "legal_name"` → still works, so the guard is not a
  regression for the 12 remaining plain-quote sites.

**Integration.** `dash build` on the V2-16 spec and assert the rendered figure's
row count equals the number of matching observations, i.e. the qualifier bites
rather than merely surviving into JSON (this is the half V2-11 never had —
`test/test_varlist_expansion.cscript:624-667` asserts only on the spec string).

**Non-vacuity by mutation.** Revert `dash.ado:1224` to the plain-quote form →
V2-16 and V2-17 must fail. Remove the regex guard in `_dash_json_str` → the
`9illegal` unit case must fail. Change `_apply_graph_filter` to ignore
`if_expr` → the Python-side render test must fail.

### Epic 2.C — Prove it on the artifact the user receives

**Write first (must fail at `ca5fe35`).**

1. **`test/test_kpi_brush.py` — the harness must stop helping.** Change
   `TestTheShippedBrushJsActuallyComputes._run` (`:197-239`) to build its node
   script from the *same expression* `_wire_brush_callbacks` uses — ideally by
   calling a small extracted helper, e.g. `DashRenderer._brush_callback_code()`,
   so production and test cannot diverge again — and add
   `test_a_brushed_p75_is_the_p75_of_the_selection`. Against `ca5fe35` it fails
   with `ReferenceError: dash_pctl is not defined`; the assertion message should
   say so, because that is the whole finding.
2. **`test/test_kpi_brush.py` — a structural test that needs no node.**
   `assert "function dash_pctl" in DashRenderer(...)._brush_callback_code()`.
   This one runs everywhere, including where `node` is absent and the
   `pytest.skip` at `:200-202` would otherwise hide the defect. Per the project
   memory note, *a skip is not a pass*.
3. **`test/test_kpi_brush.py` — `median` and `iqr`** through the same harness,
   since all three share the `else` arm at `dash_render.py:7266-7281`.
4. **`test/test_mode_parity.py` — item 2(c)**, `xfail(strict=True)` until
   Phase 01 lands the server-side qualifier (TR-02.19).
5. **`test/test_statistical_truth.py` — item 2(a)**: for each of `lfit`, `qfit`,
   `lfitci`, `qfitci`, `lowess`, `lpoly`, `lpolyci`, `fpfit`, `fpfitci`,
   `mband`, `mspline`, `histogram`, `kdensity`, assert the qualified layer's
   computed values equal the values computed from the qualified subsample. The
   anchor case is REMAINING.md's own ground truth:
   `regress mpg weight if foreign==1` → slope `-.01042596`, intercept
   `48.918297`; the unqualified fit is slope `-.00600869`, intercept
   `39.440284`, and today dash draws the second.
6. **`test/test_varlist_expansion.py` — item 2(b)**: per-plot `in_expr` on the
   second of two plots; measured working, currently untested.
7. **`test/test_per_plot_qualifier_linking.py` — item 2(d)**: a computed layer
   inside a linked `by()` graph and under a linked graph-level qualifier, beside
   the existing `TestALinkedLayerStaysOnTheSharedSource` and
   `TestItComposesWithAGraphLevelQualifier`.

**Unit tests (rule 4).** `_brush_callback_code()` (new, if TR-02.16's preferred
shape is taken): asserts it contains exactly one `function dash_pctl`, contains
`dash_apply_kpis`, and does **not** contain the top-level
`dash_apply_kpis(new_data,` call that belongs to the filter path.
`_PCTL_JS`: asserted to appear exactly once across `_FILTER_JS + _BRUSH_JS`, so
`test/test_kpi_brush.py:159-165` keeps its meaning.

**Integration / cscript.** `test/test_e2e_kpi.cscript` gains a case that builds a
dashboard with `update(brush)` on a `p75` KPI and asserts the emitted HTML
contains `function dash_pctl` within the selection callback's `code` payload —
an artifact-level check that survives any refactor of the Python slicing.

**Non-vacuity by mutation.**

- Remove `_PCTL_JS` from the concatenation in `_wire_brush_callbacks` → tests
  1, 2, 3 and the e2e case must all fail. This is the exact mutation that
  reproduces today's defect, so it is also the proof the fix is load-bearing.
- Add a second copy of `function dash_pctl` to `_BRUSH_JS` → `test_the_statistic_is_defined_exactly_once`
  (`test/test_kpi_brush.py:160`) must fail.
- Replace `dash_pctl`'s body with numpy's linear-interpolation rule → the
  `p75` value assertions in `test/test_kpi_values.py` and the new brush cases
  must disagree with the initial render, which is the drift
  `dash_render.py:7341-7346` warns about.
- Change one computed mapper to ignore its mask → the matching
  `test_statistical_truth.py` case must fail, per layer, so a partial Phase 01
  fix cannot pass as a complete one.

### Suite-level gates for this phase

Before commit, per project rule 5: full pytest, the full certification suite run
with `arch -arm64` from `test/` (a skip is not a pass — the node-dependent brush
cases must actually run on the developer's machine, or the structural test 2
above must carry the load), the conformance corpus with zero `r(198)` on
previously-valid commands, and the adversarial suite.

---

## Definition of done

A reviewer can tick each of these.

**Epic 2.A**

- [ ] `dash_parse.mata:_dash_split_segs` captures depth-0 text between the last
      `)` and the graph-options comma and returns it as `_cmd_qualifier`, set in
      both the paren and flat branches.
- [ ] Depth-0 text that does not begin `if ` or `in ` produces `rc=198` with a
      message naming the offending text; `dash (scatter mpg weight) garbagetoken,
      name(g9)` no longer returns `rc=0`.
- [ ] `_dash_plot` (`dash.ado:1377`) writes the captured qualifier to the
      graph-level `if_expr`/`in_expr` at `dash.ado:1488-1503`, and the
      `if `n_segs' == 1` promotion at `:1496` does not double-apply it.
- [ ] `dash (scatter mpg weight) if foreign==1, name(g8)` and
      `dash scatter mpg weight if foreign==1, name(g4)` render figures with the
      same visible row count.
- [ ] `dash (P) (P) if <expr>` restricts every layer; `dash (P) in 1/10`
      restricts to 10 rows.
- [ ] Quoted text inside a segment is never seen by the classifier.
- [ ] V2-13, V2-14, V2-15 and P2-86 exist, were seen to fail before the fix, and
      pass after.

**Epic 2.B**

- [ ] `dash.ado:1224` and `:1225` use the compound-quote form the helper
      documents at `dash.ado:221`.
- [ ] `_dash_json_str` validates `out_macro` against
      `^[A-Za-z_][A-Za-z0-9_]{0,30}$` and exits 198 otherwise.
- [ ] The 12 remaining plain-quote call sites (`dash.ado:1143`–`:1237`) are
      re-checked and the variable-name invariant is recorded in a comment.
- [ ] `if make=="Volvo 260"` reaches the spec as
      `"if_expr":"make==\"Volvo 260\""`, round-trips through
      `_dash_json_get_str`, and filters the rendered figure.
- [ ] `if make=="xvar zz"` leaves `"xvar"` unchanged; `if make=="_opts_json zz"`
      yields parseable JSON.
- [ ] V2-16, V2-17 and P2-87 exist, failed before, pass after.
- [ ] `TestIfQualifierLeavesStringLiteralsAlone`
      (`test/test_security_surface.py:164`) still passes unmodified.

**Epic 2.C**

- [ ] The string `_wire_brush_callbacks` (`dash_render.py:11645`) assembles
      contains exactly one `function dash_pctl`.
- [ ] `(_FILTER_JS + _BRUSH_JS).count("function dash_pctl") == 1` still holds
      (`test/test_kpi_brush.py:160`).
- [ ] The four `_FILTER_JS` marker slices in `test/test_kpi_values.py:275`,
      `:501`, `test/test_statistical_defaults.py:283` and
      `test/test_kpi_brush.py:206` still resolve and those tests still pass.
- [ ] `test/test_kpi_brush.py`'s node harness builds its script from the same
      expression production uses; no test supplies a helper production omits.
- [ ] `p25`, `p75`, `median` and `iqr` cards recompute correctly under brush,
      and the empty-selection fallback still restores every row.
- [ ] Item 2(a)–(e) tests exist; (a), (b), (d) pass against Phase 01; (c) is
      `xfail(strict=True)` if Phase 01's server work has not landed, with the
      reason recorded in the test.
- [ ] Every mutation listed in the test plan was performed and killed the test
      it is supposed to kill.

**Phase-level**

- [ ] `dash.sthlp` no longer claims a twoway parity the code does not honour
      (`dash.sthlp:128-130`), and states what a command-level qualifier in paren
      mode does. *(The full 06-06 documentation item belongs to its own phase;
      what is required here is that this phase does not leave the sentence more
      false than it found it.)*
- [ ] Full pytest, full cscript suite, conformance corpus and adversarial suite
      green (project rule 5).
- [ ] Commits are on `feature/batch4-interactive-layer`, one per defect, and the
      merge command into local `main` is reported rather than run (project
      rule 6).
- [ ] No commit message mentions the assistant or its vendor (project rule 7).

---

## Risks and sequencing notes

**Order within the phase.** Do item 5 before item 1. Item 1 introduces a new
path carrying user text into `dash.ado`'s locals; if the escaper is still called
with plain quotes when that path opens, the new `_cmd_qualifier` becomes a
second injection vector rather than a fix. Then item 4 (the reject path), then
items 1 and 3 together — they are one change in `_dash_split_segs` with two
distinct acceptance cases. Item 7 is independent of all of it and can be done
first by a second developer.

**Risk: the reject path breaks a command that parses today.** `_dash_split_segs`
has discarded depth-0 text since it was written, so somebody's working command
may depend on the silence. Mitigation: run the conformance corpus before and
after; any new `r(198)` is a finding, not a pass. The corpus is a named S16-07
gate, so this is a check the phase owes anyway.

**Risk: moving `dash_pctl` breaks three test files.** Four test slices index
`_FILTER_JS` by literal marker text (TR-02.16), and the obvious fix — hoisting
the definition above `dash_render.py:7192` — makes the
`"function dash_pctl"` … `"// agg_sources…"` slice swallow the top-level
`dash_apply_kpis(new_data, ...)` call at `:7339`, which throws under every node
harness. Take the `_PCTL_JS` constant route, which leaves every marker where it
is.

**Risk: item 2 cannot be finished inside this phase.** (a), (c) and (d) assert
behaviour Phase 01 delivers. Write them here — rule 8 wants the failing test
first — but mark (c) `xfail(strict=True)` so it converts to a hard failure the
moment the server behaviour appears without anyone updating the test. Do not
mark (a) or (d) xfail if Phase 01 has already merged.

**Risk: a green suite that proves nothing.** This phase exists partly because
`test/test_kpi_brush.py` was green while the feature was broken, and because
V2-11 asserted on a spec string rather than a figure. Every new test here must
be killed by the mutation named beside it before it is committed. Where a test
depends on `node`, add the structural counterpart that runs without it — the
project's own note that a skip is not a pass applies directly.

**Risk: asymmetric spec shapes confuse a later reader.** After item 1, the same
user intent produces two different spec shapes (TR-02.7): the flat form carries
the qualifier on `plots[0]` *and* at graph level, the paren form only at graph
level. Both render identically. Write the reason into the comment block at
`dash.ado:1490-1495`, which already explains the promotion gate, so the next
audit does not read the difference as a bug.

**Dependency out.** Nothing else in the plan waits on this phase, but two gates
do: the adversarial suite named in S16-07 cannot be called complete while a
user string can pick a macro name (item 5), and the S16-06 "run every example"
gate will surface any conformance fallout from item 4's reject path.
