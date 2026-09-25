# Phase 20 — S09 axis and text options

**Purpose.** Section 09 is the largest single family of unfinished work in the audit:
**73 options open**, and of the 28 that the plan dispositioned `implement-S09-axes-text`,
exactly **2** are honoured today (`xtick`, `ytick` — and even those have the wrong
semantics, which Phase 14 fixes). The other 26 are accepted with rc 0, named in dash's
own `ignoring unsupported option(s)` note, and then dropped. This phase implements all
26: the thirteen that `dash.ado` does not declare at all (the time-axis `t*` family, the
`*varformat`/`*varlabel` pair, `droplines`) and the thirteen that `dash.ado` already
declares and serializes but no renderer reads (the eight outer title bands, the in-plot
`text()` annotation, the four minor-tick/minor-label options). It also carries one
functional defect that the adversarial pass turned up against task 09-06: the `if`
qualifier translator's `missing()` rewrite does not know about Stata's *string* missing,
and a missing bound inside `inrange()` is turned into a test that can never be true — so
`if missing(make)` and `if inrange(weight, ., 3000)` each draw an empty graph, silently.

---

## At a glance

| | |
|---|---|
| **Items** | 3 (numbered 1–3 below, exactly as handed over) |
| **Functional vs deliverable** | 3 functional · 0 deliverable |
| **Effort mix** | 1 × small · 0 × medium · 2 × large |
| **Renderers touched** | `both` on all three items. Item 2 also needs `dash.ado` work (declaration, serialization, `tsset` resolution). Item 1's fix reaches `dash serve` through the `inspect.getsource` copy at `dash_render.py:12497-12502` — see Risks. |
| **Ultraplan tasks discharged** | `OPT-S09A` — the `implement-S09-axes-text` disposition bucket, 26 of its 28 options (items 2 and 3). `S09` — the 09-06 refutation, `missing()` on strings and ranges (item 1). Section **S09**, which stands at **0 DONE / 7 PARTIAL / 0 NOT DONE**. |
| **Not discharged here** | `xtick`/`ytick` semantics, the minor-tick *mechanism*, the display-format fallback (Phase 14). The axis numlist grammar itself, dates on axes, `minmax` (Phases 14–15). The server port of the axis grammar (Phase 16). The declaration and serialization of the 13 undeclared options (Phase 17, item 1 — the 69). Abbreviation truth and the generator (Phase 18). The `S09-style` 43 (Phase 21). Help reconciliation (Phase 30). |
| **Depends on** | **Phase 17** (declares and serializes the 69, of which 13 are this phase's item 2) and **Phase 18** (abbreviation truth, generator idempotence, the reporter). **Phase 14** for the minor-tick mechanism that item 3's `xmtick`/`ymtick`/`xmlabel`/`ymlabel` ride on. **Phase 15 item 4** (date-aware `_apply_axis_spec`) for the `t*` family's date literals. **Phases 05–08** for anything that must also be true under `dash serve`. Item 1 depends on **nothing** and can be done first. |
| **Unblocks** | **Phase 30** (the help's Unsupported section and the minor-tick deferral note must be edited in lockstep — `test_help_conformance.py` enforces both directions) and **Phase 31** (release gates). |
| **Source of items** | All three from the main body of `REMAINING.md`: item 1 from §"17 DONE claims the adversarial pass overturned" (row `09-06`); items 2 and 3 from §2 "Blocker — the option surface" as split by Appendix A's `05-04` correction. |

---

## Why this phase exists

### The option surface, measured (REMAINING.md §2)

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
> - **S09 axes/text (26):** `b1title` `b2title` `droplines` `l1title` `l2title`
>   `r1title` `r2title` `t1title` `t2title` `text` `tlabel` `tline` `tmlabel`
>   `tmtick` `tscale` `ttext` `ttick` `ttitle` `xmlabel` `xmtick` `xvarformat`
>   `xvarlabel` `ymlabel` `ymtick` `yvarformat` `yvarlabel`
>
> The 11 `t*`/`pcarrow` options were re-probed on `tsset` monthly data and
> `pcarrow` variables to rule out a harness artefact; all 11 are ignored.

That paragraph is the whole of this phase's item 2 + item 3. The 2 honoured members of
the 28 are `xtick` and `ytick`; **confirmed at HEAD** against the fixture
(`test/fixtures/rejected_options.json`, `disposition == "implement-S09-axes-text"` has 28
entries, and the 26 above are the complement).

REMAINING.md also records the choice this phase settles:

> **Two defensible ways to close this**, and the choice is the user's:
> **(a)** implement all 92 — the plan as written; **(b)** implement the high-value
> subset (`text` `ttitle`/`tlabel` family, the `b1/l1/r1/t1title` set,
> `mlabformat` `mstyle` `lstyle` `acolor` `gap` `fxsize` `fysize` `scale`) and
> formally re-disposition the rest to accept-and-report in the plan and help.

**This phase assumes (a).** Note that (b)'s "high-value subset" is, for S09-axes-text,
almost exactly this phase's scope already: `text`, the `ttitle`/`tlabel` family and the
`b1/l1/r1/t1title` set are items 2 and 3 less `droplines`, `xvarformat`/`xvarlabel`/
`yvarformat`/`yvarlabel` and the four minor-tick options. If the maintainer chooses (b),
this phase shrinks rather than disappears — see *Risks and sequencing notes*.

### The split: 13 undeclared, 13 declared-and-dropped (REMAINING.md Appendix A, `05-04`)

Appendix A re-measured §2 and corrected it. The 26 are **two different defects**, and
they need two different fixes:

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
> - **S09 axes/text (13):** `droplines` `tlabel` `tline` `tmlabel` `tmtick`
>   `tscale` `ttext` `ttick` `ttitle` `xvarformat` `xvarlabel` `yvarformat`
>   `yvarlabel`

and its correction of §2:

> > Corrects §2 of this file, which put the figure at 92 by treating every
> > reported option as undeclared. 27 of those are declared and serialized
> > already, and are reported because `_dash_pending` correctly says they are
> > awaiting their section.

**Confirmed at HEAD.** Each of the 13 undeclared options occurs **zero** times in
`dash.ado`:

```
droplines: 0   tlabel: 0    tline: 0      tmlabel: 0   tmtick: 0
tscale: 0      ttext: 0     ttick: 0      ttitle: 0
xvarformat: 0  xvarlabel: 0 yvarformat: 0 yvarlabel: 0
```

(`grep -ic <name> dash.ado`, one per option.) They arrive only through the trailing `*`
catch-all in `_dash_parse_graph_opts` (`dash.ado:281`) and are echoed back to the user by
`_dash_report_ignored` (`dash.ado:1338`) as whatever token they typed.

The other 13 — item 3 — are the opposite shape. `b1title`…`t2title`, `text`, `xmlabel`,
`xmtick`, `ymlabel`, `ymtick` are declared, serialized, on `_dash_pending`, and **read by
nobody**. Confirmed at HEAD in `dash.ado`:

```
293:        FYSIZE(string)            SCALE(string)             TEXT(string asis) ///
365:    if `"`b1title'"' != "" local _dash_pending `"`_dash_pending' b1title"'
379:    if `"`text'"'    != "" local _dash_pending `"`_dash_pending' text"'
381:    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
382:    if `"`xmtick'"'  != "" local _dash_pending `"`_dash_pending' xmtick"'
383:    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
384:    if `"`ymtick'"'  != "" local _dash_pending `"`_dash_pending' ymtick"'
424:    sreturn local text         `"`text'"'
427-430: sreturn local xmtick / ymtick / xmlabel / ymlabel
433:    sreturn local b1title      `"`b1title'"'
751-760: the g_* graph-level twins of all of the above
1129-1130 / 1399-1400 / 1415-1416 / 1469-1470: the four propagation lists that carry
          them into graph_options JSON
```

and on the Python side, at HEAD, the count of `"<key>"` / `'<key>'` in `dash_render.py`:

| key | occurrences in `dash_render.py` |
|---|---:|
| `b1title` `b2title` `l1title` `l2title` `r1title` `r2title` `t1title` `t2title` | 0 each |
| `xmlabel` `xmtick` `ymlabel` `ymtick` | 0 each |
| `text` | 1 — and it is a comment at `:10160` about `legend(label(N "text"))`, not a read |

That is the exact state REMAINING.md describes for this group: *"They are serialized into
the spec and reported as ignored; the renderer reads none of them."*

### The `t*` family is the highest-value part of the 26

The fixture records why, per option, measured against real `twoway`
(`test/fixtures/rejected_options.json`, `rejected_options[].reason` and the first probe
of each):

| option | measured probe | why it matters |
|---|---|---|
| `tlabel` | `twoway tsline y, tlabel(2000m1(12)2004m1) nodraw` | *"time-axis spelling of an axis option dash already implements for x/y. A tsset dataset plus tsline is the single most likely copy-paste source for dash, and every t\* option aborts."* |
| `ttick` | `twoway tsline y, ttick(2000m1(12)2004m1) nodraw` | as above |
| `tmlabel` | `twoway tsline y, tmlabel(2000m1(6)2004m1) nodraw` | as above |
| `tmtick` | `twoway tsline y, tmtick(2000m1(6)2004m1) nodraw` | as above |
| `tscale` | `twoway tsline y, tscale(range(2000m1 2005m1)) nodraw` | as above |
| `ttitle` | `twoway tsline y, ttitle("Month") nodraw` | as above |
| `tline` | `twoway tsline y, tline(2002m1) nodraw` | as above |
| `ttext` | `twoway tsline y, ttext(120 2002m1 "a note") nodraw` | as above |
| `droplines` | `twoway function x, droplines(2 4 6) range(0 10) nodraw` | *"vertical drop lines from the curve to the base, i.e. added-line geometry."* |
| `xvarformat` | `twoway scatter mpg weight, xvarformat(%9.2f) nodraw` | *"axis title / tick format taken from the plotted variable."* |
| `xvarlabel` | `twoway scatter mpg weight, xvarlabel("Weight") nodraw` | as above |
| `yvarformat` | `twoway scatter mpg weight, yvarformat(%9.2f) nodraw` | as above |
| `yvarlabel` | `twoway scatter mpg weight, yvarlabel("Mileage") nodraw` | as above |
| `b1title`…`t2title` | `twoway scatter mpg weight, b1title("bottom 1") nodraw` (one per band) | *"outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only title/subtitle/note/caption."* |
| `text` | `twoway scatter mpg weight, text(20 3000 "a note") nodraw` | *"in-plot text annotation at a (y,x) data coordinate."* |
| `xmlabel` `xmtick` | `twoway scatter mpg weight, xmtick(2000(250)5000) nodraw` | *"axis tick/minor-tick/minor-label placement. dash implements only xlabel()/ylabel() major ticks."* |
| `ymlabel` `ymtick` | `twoway scatter mpg weight, ymtick(10(5)40) nodraw` | as above |

The fixture's environment line records how these were produced:
`StataNow 19.5 MP (arm64 slice, launched via arch -arm64 /usr/local/bin/stata-mp -b)`,
data `sysuse auto` for the cross-sectional probes and a *synthetic 60-month tsset panel*
for the `t*` probes.

### Section 09's own statement of the problem (`.ultraplan/sections/section-09-axes-legend-titles.md`)

> Also here: the new options from S05 — `text()`, `xtick()`, `ytick()`, `xmtick()`, `ymtick()`,
> `xmlabel()`, `ymlabel()`, and the `t1title`/`b1title`/`l1title`/`r1title` family.

and its business requirements, which this phase inherits:

> - BR-09.1 Every `xlabel()`/`ylabel()` form Stata accepts produces the ticks Stata produces.
> - BR-09.2 Sub-option text never leaks into rendered output.

### Item 1 — the qualifier translator and Stata's missing

REMAINING.md, §"17 DONE claims the adversarial pass overturned":

> | 09-06 | `missing()` misses Stata's *string* missing; a missing bound in a range is mishandled |

The relevant code is `_stata_if_to_pandas` (`dash_render.py:6852-6931`), whose docstring
sets out why the translation exists at all — verbatim at HEAD:

```python
def _stata_if_to_pandas(expr: str) -> str:
    """Rewrite Stata's qualifier idioms into plain comparison expressions.

    ``if !missing(rep78)``, ``if inlist(rep78,1,2)`` and ``if rep78 < .`` are
    the three most common qualifier forms in real Stata code, and all three
    failed validation, warned, and rendered the graph UNFILTERED.

    This is a TRANSLATION performed BEFORE validation, not a loosening of the
    whitelist. ...
    """
```

and the two rewrites at fault, also verbatim:

```python
    # inrange(x, a, b) -> ((x >= a) & (x <= b))
    def _inrange(m):
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) != 3 or not all(parts):
            return m.group(0)
        v, lo, hi = parts
        return f"(({v} >= {lo}) & ({v} <= {hi}))"

    out = re.sub(r"\binrange\s*\(([^()]*)\)", _inrange, out)

    # missing(x) -> (x != x).  NaN is the only value not equal to itself.
    out = re.sub(r"\bmissing\s*\(([^()]*)\)",
                 lambda m: f"({m.group(1).strip()} != {m.group(1).strip()})",
                 out)
```

**Confirmed at HEAD by running the function** (the module was imported and
`_stata_if_to_pandas` called directly; no Stata, no test suite):

| input | output at HEAD | what Stata means | what dash draws |
|---|---|---|---|
| `missing(make)` | `(make != make)` | rows where `make == ""` | **nothing** — `"" != ""` is `False` for every object-dtype row |
| `!missing(make)` | `~(make != make)` | rows where `make != ""` | **every row**, blank strings included |
| `inrange(weight, ., 3000)` | `(((weight != weight)) & (weight <= 3000))` | no lower bound: `weight <= 3000` | **nothing** — requires `weight` to be NaN *and* ≤ 3000 |
| `inrange(weight, 2000, .)` | `((weight >= 2000) & ((weight == weight)))` | no upper bound: `weight >= 2000`, missing excluded | correct, by accident — the `<= .` rewrite happens to add the not-missing test |
| `missing(rep78)` | `(rep78 != rep78)` | rows where `rep78` is `.` | correct — numeric missing is NaN |

Note the shape of the failure: the translated expression is **valid**, so
`_validate_if_expr` (`dash_render.py:6932`) accepts it and `df.query` runs it without
error. Nothing warns. The user gets an empty graph — or, for `!missing()` on a string, a
graph with rows Stata would have dropped — and no diagnostic at all. This is the same
class as the defect the docstring already records for string literals:

> Without that,
>
>     if make == "Wow!"
>
> became ``make == "Wow~"``, matched no rows and drew an empty graph
> without a word -- the rewritten expression is still valid, so nothing
> reported that the qualifier had been altered.

The defect reaches `dash serve` too, because the function is copied into the emitted app
verbatim (`dash_render.py:12497-12502`):

```python
                    # The two masking helpers come WITH _stata_if_to_pandas:
                    # it calls them, and a copied function whose callees stay
                    # behind raises NameError on the served page rather than
                    # here, where it would be noticed.
                    _mask_string_literals, _unmask_string_literals,
                    _stata_if_to_pandas, _stata_expr_to_python):
```

with three emitted call sites: the graph-level filter (`dash_render.py:13821`), the
`by()` facet filter (`:15054`) and the filter callback (`:15556`).

### Why none of this will reach `dash serve` for free

REMAINING.md §4:

> **Also unification-shaped:** none of S09's axis/title/legend work reached
> `ServerAppBuilder`. `_parse_axis_label` appears 4× in the renderer and **0×**
> in the emitted app, so the whole `xlabel()` grammar is absent from
> `dash serve` / `dash build, server`. (Agent-reported, path confirmed here.)

and Appendix A, `09-02`:

> 3. **Server mode has no axis-label grammar at all**: `_parse_axis_label` occurs
>    4× in the renderer and **0×** in the emitted app.

Everything this phase adds to the axis path therefore has to be *ported* as well as
written, or explicitly declared a server-mode limitation. Phase 16 owns the port of the
grammar itself; this phase must not add a fourteenth option that exists in one renderer
and not the other without saying so. See *Risks and sequencing notes*.

### Where the section stands

REMAINING.md, "Status by section":

> | 09 | Axes, legend, titles | 7 | 1 done, 6 partial ②, **73 options open** ① | see §2 — largest single family; none of S09 reached `ServerAppBuilder` |

and "Final tally, after the adversarial pass":

> | S09 | … |
> |---|---|
> | 0/7/0 | … |

Zero of S09's seven tasks are DONE. This phase closes the option half of that gap;
Phases 14–16 and 26–27 close the grammar and text-fidelity halves.

---

## Epics

| epic | goal | items |
|---|---|---|
| **20.A — Stata's missing, in the qualifier translator** | `missing()` and `inrange()` mean in dash what they mean in Stata, for strings and for open-ended ranges, in both renderers. | 1 |
| **20.B — The undeclared thirteen: time axis, variable formats, droplines** | `tlabel` `tline` `tmlabel` `tmtick` `tscale` `ttext` `ttick` `ttitle` `droplines` `xvarformat` `xvarlabel` `yvarformat` `yvarlabel` are declared, serialized and honoured. | 2 |
| **20.C — The declared thirteen: title bands, in-plot text, minor ticks** | `b1title` `b2title` `l1title` `l2title` `r1title` `r2title` `t1title` `t2title` `text` `xmlabel` `xmtick` `ymlabel` `ymtick` stop being serialized-and-ignored and start drawing. | 3 |

---

## User stories

### Epic 20.A — Stata's missing, in the qualifier translator

> **As a Stata user pasting a `twoway` command**, I want `if missing(make)` and
> `if inrange(weight, ., 3000)` to select the rows Stata selects, **so that** a qualifier
> I have used for twenty years does not silently produce an empty graph.

- **Given** `sysuse auto` with `replace make = "" in 1/3`
  **When** I run `dash scatter mpg weight if missing(make), name(g1)` and build
  **Then** the figure's data source holds exactly 3 rows.
- **Given** the same data
  **When** I run `dash scatter mpg weight if !missing(make), name(g1)` and build
  **Then** the figure holds 71 rows, not 74.
- **Given** `sysuse auto`
  **When** I run `dash scatter mpg weight if inrange(weight, ., 3000), name(g1)`
  **Then** the figure holds exactly the rows with `weight <= 3000`, the same count
  `count if inrange(weight, ., 3000)` reports in Stata.
- **Given** `sysuse auto`
  **When** I run `dash scatter mpg weight if inrange(weight, 2000, .), name(g1)`
  **Then** the count is unchanged from HEAD — this case is already right and must stay
  right.
- **Given** any of the hostile expressions in
  `test_axis_options.py::TestIfQualifierWhitelistIsNotWeakened`
  **When** they are passed through the amended translator
  **Then** `_validate_if_expr` still returns `False` for every one of them.

> **As a `dash serve` operator**, I want the served page to filter identically to the
> standalone HTML, **so that** the same command does not produce two different datasets.

- **Given** a spec with `if missing(make)`
  **When** the app is emitted and executed
  **Then** the served figure's row count equals the standalone figure's row count, and
  the emitted module resolves every global the copied translator references.

### Epic 20.B — The undeclared thirteen

> **As a Stata user pasting a `twoway` command on `tsset` data**, I want
> `tlabel()`, `ttick()`, `tmlabel()`, `tmtick()`, `tscale()`, `ttitle()`, `tline()` and
> `ttext()` to act on the time axis, **so that** the single most likely copy-paste source
> for `dash` — a `tsset` panel and a `tsline` — does not lose every option I wrote.

- **Given** a `tsset` monthly dataset and `dash tsline y, tlabel(2000m1(12)2004m1)`
  **When** the dashboard is built
  **Then** the x axis carries a `FixedTicker` whose ticks are the five annual January
  positions, expressed in the same units the datetime axis uses, **and** no
  `ignoring unsupported option(s)` note names `tlabel`.
- **Given** `dash tsline y, ttitle("Month")`
  **When** the dashboard is built
  **Then** the x-axis label is exactly `Month`.
- **Given** `dash tsline y, tline(2002m1)`
  **When** the dashboard is built
  **Then** a `Span` is added at the January 2002 position with the same styling
  `xline()` produces.
- **Given** `dash tsline y, ttext(120 2002m1 "a note")`
  **When** the dashboard is built
  **Then** a data-coordinate `Label` reading `a note` sits at y = 120, x = Jan 2002.
- **Given** data that is **not** `tsset` and a command carrying any `t*` option
  **When** `dash` runs
  **Then** it reports the option as unusable with a message naming `tsset`, and does not
  abort — rc stays 0, matching decision 4 ("accept, never abort, report together").

> **As a Stata user**, I want `xvarformat()`/`yvarformat()` and
> `xvarlabel()`/`yvarlabel()` to control the axis's format and title, **so that** the S08
> display-format work is reachable per-axis rather than only per-variable.

- **Given** `dash scatter mpg weight, xvarformat(%9.2f)`
  **When** the dashboard is built
  **Then** the x-axis tick formatter is the one `%9.2f` maps to, overriding the
  variable's own entry in `build_options["formats"]`.
- **Given** a `weight` variable whose Stata variable label is `Weight (lbs.)` and
  `dash scatter mpg weight, xvarlabel`
  **When** the dashboard is built
  **Then** the x-axis title is `Weight (lbs.)` and not `weight`.

> **As a dashboard viewer**, I want `droplines()` to draw the drop lines the command
> asked for, **so that** the chart I am looking at is the chart that was specified.

- **Given** `dash function x, droplines(2 4 6) range(0 10)`
  **When** the dashboard is built
  **Then** three vertical segments run from the base to the curve at x = 2, 4 and 6.

### Epic 20.C — The declared thirteen

> **As a Stata user**, I want the outer title bands to render, **so that** the eight
> `t1title`…`r2title` options stop being accepted, reported and thrown away.

- **Given** `dash scatter mpg weight, b1title("bottom 1") b2title("bottom 2")`
  **When** the dashboard is built
  **Then** two title objects are laid out below the plot, with `bottom 1` nearer the plot
  region than `bottom 2`, and the option no longer appears in the ignored-options note.
- **Given** the same for `t1/t2` (above), `l1/l2` (left) and `r1/r2` (right)
  **Then** each pair is laid out on its own side in the same near/far order.
- **Given** `dash scatter mpg weight, b1title("R&D spend")`
  **When** the dashboard is built
  **Then** the rendered band text is `R&D spend` — these are canvas glyphs, and must not
  be `html.escape`d (the defect class Phase 26 exists to remove; do not add a new
  instance of it here).

> **As a Stata user**, I want `text()` to place a note inside the plot, **so that** an
> annotated chart survives the paste into `dash`.

- **Given** `dash scatter mpg weight, text(20 3000 "a note")`
  **When** the dashboard is built
  **Then** a `Label` in data coordinates reads `a note` at y = 20, x = 3000.
- **Given** `text(20 3000 "a note", size(large) color(red))`
  **Then** the rendered text is `a note` — the sub-option text appears **nowhere** in the
  output — at the requested size and colour (section 09's BR-09.2).

> **As a Stata user**, I want `xmtick()`, `ymtick()`, `xmlabel()` and `ymlabel()` to add
> minor ticks and minor labels, **so that** the help stops telling me they are
> unsupported for a reason that is not true.

- **Given** `dash scatter mpg weight, xmtick(2000(250)5000)`
  **When** the dashboard is built
  **Then** the x axis carries minor ticks at those positions **in addition to** whatever
  major ticks `xlabel()` or the default produced, and the major ticks are unchanged.
- **Given** `dash scatter mpg weight, ymlabel(10(5)40)`
  **Then** the y axis carries *labelled* minor ticks at those positions.

> **As a package maintainer**, I want the ignored-options note and the help's Unsupported
> section to stay true as each option lands, **so that** the two conformance tests that
> police them do not have to be relaxed.

- **Given** any option removed from `_dash_pending` in `dash.ado`
  **When** `test/test_help_conformance.py` runs
  **Then** `test_nothing_listed_there_is_honoured` passes, because the matching entry was
  removed from `dash.sthlp`'s Unsupported section in the same commit.
- **Given** any option newly *added* to `_dash_pending` (the interim state for anything
  declared but not yet implemented)
  **Then** `test_everything_dash_ignores_is_listed_there` passes, because it was added to
  the help in the same commit.

---

## Business requirements

| id | requirement | how it is testable |
|---|---|---|
| **BR-20.1** | A qualifier using `missing()` on a **string** variable selects the rows Stata selects: `missing(s)` is `s == ""`, `!missing(s)` is `s != ""`. | Row count of the rendered source equals Stata's `count if ...`. |
| **BR-20.2** | A qualifier using `inrange()` with a missing bound treats that bound as unbounded, not as a missingness test, and still excludes missing values of the tested variable. | Row counts for `inrange(x, ., b)`, `inrange(x, a, .)` and `inrange(x, ., .)` match Stata's. |
| **BR-20.3** | No change to the qualifier translator widens what `_validate_if_expr` accepts. Every hostile expression currently rejected stays rejected, raw and translated. | The existing 18-case adversarial parametrisation, extended with string-missing and open-range hostiles, all assert `False`. |
| **BR-20.4** | Standalone and server filter the same rows for the same qualifier. | Parity assertion on row counts for each qualifier form. |
| **BR-20.5** | Each of the 26 `implement-S09-axes-text` options, when supplied, changes the rendered output; and no option that changes the output is still named in the `ignoring unsupported option(s)` note. | The converse pair of `test/test_unsupported_report_is_true.py`, driven from `test/fixtures/rejected_options.json`. |
| **BR-20.6** | A `t*` option on `tsset` data behaves as the corresponding `x*` option does on the time axis; on non-`tsset` data it is reported, not honoured, and never aborts (rc 0). | Two cscript cases per option: tsset and un-tsset. |
| **BR-20.7** | Sub-option text supplied to any option this phase implements never appears as rendered text (section 09's BR-09.2). | Assert the sub-option substring is absent from the built HTML and from the Bokeh model's text properties. |
| **BR-20.8** | Text this phase draws on a Bokeh canvas is not HTML-escaped; text this phase writes into the HTML document is escaped exactly once. | Fidelity assertions for `&`, `<`, `'` in a band title, a `text()` annotation and a `ttext()` annotation. |
| **BR-20.9** | `dash.sthlp`'s Unsupported section and `dash.ado`'s `_dash_pending` lists agree at every commit in this phase. | `test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue`, both directions. |
| **BR-20.10** | Nothing this phase adds is honoured in one renderer and silently dropped in the other. Either both honour it, or the server-mode limitation is stated in the help's Server Mode difference table **and** a note fires. | Parity test plus a help-table assertion. |

---

## Technical requirements

### Epic 20.A — the translator (item 1)

- **TR-20.1** `_stata_if_to_pandas` (`dash_render.py:6852-6931`) gains knowledge of which
  columns are strings. The single caller in `DashRenderer` is `_apply_graph_filter` at
  `dash_render.py:8640`, where the `DataFrame` is in scope:

  ```python
            pandas_expr = _stata_if_to_pandas(if_expr)
  ```

  Either (a) add an optional second parameter — `_stata_if_to_pandas(expr, str_cols=())`
  — defaulting to the empty set so the existing behaviour is preserved for numeric-only
  callers, or (b) emit the dtype-agnostic form `((x != x) | (x == ""))` for every
  `missing(x)`. REMAINING.md's item text names both: *"emit `((x != x) | (x == \"\"))`,
  or pass the string-variable set into the translator"*. Option (b) is safe against a
  numeric column only if `x == ""` does not raise under
  `df.query(..., engine="python")`; **measure that before choosing**, because a raise
  inside `query` is caught at `dash_render.py:8654-8659` and degrades to *unfiltered*,
  which turns a silent wrong answer into a different silent wrong answer.
- **TR-20.2** The `_inrange` rewrite must special-case a bound that is Stata's missing
  (`.`, or `.a`–`.z`). Required output shape, for a variable `v`:
  - `inrange(v, ., hi)` → `((v == v) & (v <= hi))`
  - `inrange(v, lo, .)` → `((v == v) & (v >= lo))` — same result as today, reached
    deliberately rather than by accident
  - `inrange(v, ., .)` → `(v == v)`
  Note `(v == v)` is the file's existing idiom for "not missing"; the `< .` family of
  rewrites immediately below `_inrange` already uses it.
- **TR-20.3** The rewrites must still run **before** validation and must still produce
  only node types `_validate_if_expr` (`dash_render.py:6932`) permits: comparisons,
  boolean combinators, names and literals. No new function call may survive into the
  validated string. This is the invariant the 700e770 whitelist depends on, and
  `test_axis_options.py:774` `TestIfQualifierWhitelistIsNotWeakened` is its guard.
- **TR-20.4** String literals are masked before any rewrite and restored after
  (`_mask_string_literals` / `_unmask_string_literals`, `dash_render.py:6845`). A new
  emitted `""` literal is produced *by the translator*, after masking, so it must not be
  fed back through `_unmask_string_literals`' index substitution — verify that the
  literal marker `_LITERAL_MARK` scheme is unaffected by injecting a bare `""` into the
  output.
- **TR-20.5** **Server carry.** The emitted app receives the translator by
  `inspect.getsource` from the tuple at `dash_render.py:12497-12502`. If the fix
  introduces a *new* module-level helper or constant, it must be added to that tuple, and
  to the name list in
  `test/test_mode_parity.py:465` `test_the_scan_found_the_copied_helpers`, or the served
  page raises `NameError` — the exact failure that test's docstring records happening
  three times already. If the fix changes the signature (option (a) of TR-20.1), the
  three emitted call sites must pass the new argument:
  `dash_render.py:13821` (graph-level), `:15054` (`by()` facets) and `:15556` (the filter
  callback).
- **TR-20.6** `dash.ado` needs no change for this item. The qualifier is already carried
  as `if_expr` (written at `dash.ado:1240`/`:1244`, read at `dash_render.py:9951`).

### Epic 20.B — the undeclared thirteen (item 2)

- **TR-20.7** **Declaration is Phase 17's item 1, not this one.** All thirteen appear in
  that item's list of 69. This phase consumes the result: each must be declared in
  `_dash_parse_graph_opts`'s syntax block (`dash.ado:281`), serialized through the four
  propagation lists (`dash.ado:1129`, `:1399`, `:1415`, `:1469`), and — per Appendix B —
  *"The t\*/pc\* family are graph-level (graph syntax block + the four `foreach
  gk`/`foreach gkey` propagation lists)"*. If Phase 17 has not landed, this phase's first
  commit does that declaration for these thirteen only, using
  `scripts/regen_option_surface.py`'s `GRAPH` inventory — **and Phase 18's generator
  idempotence fix must land first**, because re-running the generator at HEAD deletes
  hand-added declarations including `sreturn local _pending`, which is the only channel
  feeding `_dash_report_ignored`.
- **TR-20.8** **The time variable.** `dash.ado` already resolves the `tsset` time
  variable for `tsline`/`tsrline` at `dash.ado:1082`:

  ```stata
                    local xvar `"`_dta[_TStvar]'"'
  ```

  The `t*` family needs the same value on *any* plot type, so resolve `_dta[_TStvar]`
  once in the graph-option path and emit it as a new graph-option key — `tvar` — into
  `graph_options` JSON. When `_dta[_TStvar]` is empty and any `t*` option was supplied,
  add those options to `_dash_pending` for that command so they are reported, and do not
  abort (rc 0). Do **not** copy `dash.ado:1087`'s `exit(111)`: that is correct for
  `tsline` with no x variable, and wrong for an option.
- **TR-20.9** **Axis routing.** In `dash_render.py:_make_figure_body` (`:9495`), the axis
  loop at `:9903-9913` iterates a fixed pair:

  ```python
        for ax_key, axis_obj, grid_obj, var in (
            ("xlabel", fig.xaxis, fig.xgrid, xvar),
            ("ylabel", fig.yaxis, fig.ygrid, yvar),
        ):
            raw_ax = graph_opts.get(ax_key, "")
            tick_key = "xtick" if ax_key == "xlabel" else "ytick"
            raw_tick = graph_opts.get(tick_key, "")
            if not raw_ax and not raw_tick:
                continue
            spec = self._parse_axis_spec(raw_ax or raw_tick)
            self._apply_axis_spec(fig, axis_obj, grid_obj, spec, var)
  ```

  Route the `t*` family by **aliasing onto whichever axis carries `tvar`** before this
  loop runs: if `graph_opts["tvar"]` equals `xvar`, then `tlabel`→`xlabel`,
  `ttick`→`xtick`, `tmlabel`→`xmlabel`, `tmtick`→`xmtick`, `tscale`→`xscale`,
  `ttitle`→`xtitle`, `tline`→`xline`, `ttext`→`text`; and symmetrically for y. An
  explicit `x*` option supplied alongside its `t*` twin wins — record the collision and
  report it rather than silently picking one. Aliasing, rather than a parallel
  implementation, is what makes the `t*` family inherit every later fix to the grammar
  (Phases 14–16) for free.
- **TR-20.10** **Date literals.** Every `t*` probe in the fixture carries Stata *date*
  literals — `tlabel(2000m1(12)2004m1)`, `tscale(range(2000m1 2005m1))`,
  `tline(2002m1)`, `ttext(120 2002m1 "a note")`. `_parse_axis_spec`
  (`dash_render.py:9305`) handles `a(b)c`, `#N`, `minmax`, `none` and bare values, all
  numerically. REMAINING.md, Appendix C, `09-02` records the consequence:

  > `_apply_axis_spec` has no date awareness, so every axis_label and axis_scale form is
  > wrong on a %t\* axis. … explicit ticks are passed through as raw Stata date numbers;
  > `minmax` emits `float(vals.min())` of a datetime column, i.e. MICROseconds (1000x too
  > large); `#N` replaces the DatetimeTicker with a BasicTicker; `format(%td...)` is
  > silently ignored … and `xscale(range())` builds a Range1d in date

  So the `t*` family is **blocked on Phase 15 item 4**. Until that lands, the `t*`
  aliasing may be implemented and tested against a *numeric* time index only, with the
  date-literal cases marked `xfail` referencing Phase 15 — never silently skipped.
  (Project memory: a skip is not a pass.)
- **TR-20.11** **`tline()`** reuses the reference-line machinery at
  `dash_render.py:9843-9857`: `_parse_refline("xline", "xline_values")` then
  `fig.add_layout(Span(location=float(...), ...))`. The location for a date literal is
  the same epoch-millisecond value the datetime axis uses; convert through the same
  helper the loader uses to build `self.date_vars` (`dash_render.py:8193-8228`). The
  emitted server app carries its own copy of this block at
  `dash_render.py:13954-13982` — port or declare the limitation (BR-20.10).
- **TR-20.12** **`ttext()` and `text()` share one helper.** Both are
  `(y x "string" [, suboptions])` tuples in data coordinates. Write **one**
  `_add_text_annotations(fig, raw, xvar, yvar)` that parses repeated triples, reuses
  `_parse_textbox_opt` (`dash_render.py:860`), `_textbox_size` (`:825`) and
  `_textbox_color` (`:845`) for the sub-options, and emits `Label(x=…, y=…,
  x_units='data', y_units='data', text=…)`. The note/caption block at
  `dash_render.py:9860-9886` is the existing pattern to follow — and the existing
  counter-example for hardcoded style, since it hardcodes
  `{"size": 11.0, "color": "#555555"}`. Do not add a fourth hardcoded literal; take the
  defaults from the scheme where the scheme has them (Phase 23/24 territory — leave a
  named constant, not an inline literal).
- **TR-20.13** **`droplines(numlist)`** draws a vertical segment at each listed x from the
  plot's base to the curve. The base is the same value `base()` supplies — `base` is
  already in the fixture's `accepted_option_keys_probed` list, so a value reaches the
  spec. Implement as `Segment` glyphs (not `Span`, which is unbounded) added in
  `_make_figure_body` after the layers are drawn, so the y at each x can be read off the
  layer's own source.
- **TR-20.14** **`xvarformat()`/`yvarformat()`** override the per-variable entry in
  `build_options["formats"]` for that axis only. The format map is written by `dash.ado`
  at `:1723` and `:2343` and consumed at `dash_render.py:8188`, populating
  `self.date_vars` (`:8193`) and `self.numeric_formats` (`:8194`), which are copied onto
  the mapper at `:8141-8142`. Implement as a **per-axis override dict** consulted by
  `_apply_axis_spec`'s format fallback (`dash_render.py:9159-9171`) ahead of
  `numeric_formats`. Note that fallback is currently unreachable on a default axis —
  `if not raw_ax and not raw_tick: continue` at `:9910` — which **Phase 14 item 3 fixes**;
  `xvarformat()` supplied on its own must reach the formatter, so either Phase 14 lands
  first or this phase must make `xvarformat` count as a reason to enter the loop.
- **TR-20.15** **`xvarlabel()`/`yvarlabel()`** select the variable's Stata variable label
  as the axis title. The label map is already loaded:
  `self.variable_labels = stata_json.get("variableLabels", {})`
  (`dash_render.py:8168`), read by `_axis_label` (`:9300-9302`) and used as the axis-title
  fallback at `:9518-9519`:

  ```python
        x_label = raw_xtitle if raw_xtitle else self._axis_label(xvar)
        y_label = raw_ytitle if raw_ytitle else self._axis_label(yvar)
  ```

  **Probe Stata before implementing.** The fixture records the probe
  `twoway scatter mpg weight, xvarlabel("Weight")` — i.e. the option took an argument in
  that probe — while the name suggests a toggle. Resolve the real signature against
  `twoway` the way `scripts/extract_abbrev_truth.do` resolves abbreviations, and record
  the result in the fixture. Do not guess: this document's requirement is *"the axis title
  comes from the variable label rather than the variable name"*, and the exact argument
  form is a measurement, not a design decision.
- **TR-20.16** Precedence, stated once and tested: an explicit `xtitle()` beats
  `xvarlabel`; an explicit `format()` sub-option inside `xlabel()` beats `xvarformat()`;
  `xvarformat()` beats the variable's own `build_options["formats"]` entry; that beats
  Bokeh's default.

### Epic 20.C — the declared thirteen (item 3)

- **TR-20.17** **No `dash.ado` work is needed for the values** — all thirteen already
  reach `graph_options` JSON (`dash.ado:1129-1130`, `:1399-1400`, `:1415-1416`,
  `:1469-1470`; `sreturn` at `:424`, `:427-430`, `:433` and the `g_*` twins at
  `:751-760`). What `dash.ado` needs is the **removal** of each option's `_dash_pending`
  line as it lands: `dash.ado:365-384` (graph-level) and `dash.ado:595-632` (plot-level).
  That removal is load-bearing in both directions —
  `test/test_unsupported_report_is_true.py` reads the block and asserts each named option
  does *not* change the output, so an implemented option left on the list **fails that
  test**; and `test/test_help_conformance.py` asserts the help's Unsupported section and
  the pending lists are the same set. The comment above the block says so at HEAD:

  ```stata
    // test_unsupported_report_is_true.py reads this block and renders
    // every option it names with two different values, asserting the
    // output does not change.  Implement one and forget to remove it
    // here, and that test fails.
  ```

- **TR-20.18** **The eight title bands.** Bokeh lays out extra titles with
  `fig.add_layout(Title(text=...), place)` where `place` is `"above"`, `"below"`,
  `"left"` or `"right"`. Add them in `_make_figure_body` immediately after the
  note/caption/subtitle block (`dash_render.py:9860-9898`), which is the existing example
  of the same call — it uses `Label` at screen coordinates; the bands want `Title`, which
  stacks. Mapping: `t1title`/`t2title` → `"above"`, `b1title`/`b2title` → `"below"`,
  `l1title`/`l2title` → `"left"`, `r1title`/`r2title` → `"right"`. **Stacking order —
  measure it.** The `1` band is nearer the plot region than the `2` band; confirm against
  a real `twoway` render before shipping, the same way REMAINING.md's own note/caption
  fix was confirmed (*"Measured in Stata: the note is ring(4) and the caption ring(5)"*).
  Because `add_layout` appends, the near band must be added first on `above`/`left` and
  the order may differ on `below`/`right` — verify per side, do not assume symmetry.
- **TR-20.19** **The `t()`/`b()`/`l()`/`r()` aliases.** `dash.ado` folds the single-letter
  aliases onto `t1title`/`b1title`/`l1title`/`r1title` at `:316-319` and `:338-341`
  (graph-level, duplicated — see Risks) and at `:534-537` (plot-level). REMAINING.md's
  04-03 refutation records that the plot-level fold is dead:

  > `T() B() L() R()` never added to `_dash_parse_plot_opts`, so the folding code at
  > `dash.ado:534-537` is dead

  **Phase 17 item 6 adds them.** Once it has, a `b("x")` written inside a plot's
  parentheses must reach the same band as `b1title("x")`; this phase's tests must cover
  both spellings.
- **TR-20.20** **`text()`** uses the shared annotation helper of TR-20.12. Its current
  state at HEAD is the cleanest possible evidence that nothing reads it: `grep -c` for
  `"text"`/`'text'` in `dash_render.py` returns **1**, and that one hit is a comment at
  `:10160` about `legend(label(N "text"))`.
- **TR-20.21** **The four minor-tick options.** REMAINING.md, Appendix A, `09-02`:

  > 2. **`xmtick()` `ymtick()` `xmlabel()` `ymlabel()` are not implemented** — all
  >    four leave a default `BasicTicker` and are reported as unsupported options.
  >    (They are also in 05-04's undeclared list, so that work comes first.)

  and Appendix B, `09-02`, which is the item **Phase 14 owns**:

  > **[func · both · M]** Implement xmtick(), ymtick(), xmlabel(), ymlabel()
  > (minor ticks and minor labels). They are accepted by dash.ado, promoted into
  > graph_options JSON, and then read by nobody — and dash.ado still names them
  > in its 'ignoring unsupported option(s)' list, which is the honest state
  > today.     *Where:* `dash.ado:381-384 and dash.ado:629-632 (the
  > `_dash_pending` entries to remove once implemented);
  > dash.ado:1129/1399/1415/1469 already carry the keys through to graph_options
  > JSON; dash_render.py:9906 loop (add the four ke`

  **Mechanism:** `_apply_axis_spec` (`dash_render.py:9112`) needs a minor-tick path.
  Bokeh's `FixedTicker` carries `minor_ticks`; a minor *label* requires a second axis or a
  `major_label_overrides` strategy — decide and document which, and record the decision
  where the help's false rationale currently sits (Appendix C: *"It says Bokeh draws one
  tick level per axis — Bokeh 3.9 supports minor ticks directly"*). **Do not implement
  this twice**: if Phase 14 has landed, item 3 here reduces to the nine title/text
  options; if it has not, implement it here and mark Phase 14 item 2 discharged.
- **TR-20.22** **Canvas text, not HTML.** Every string this epic renders — band titles,
  `text()`, `ttext()` — is drawn by Bokeh as a canvas glyph. Section 09's own register
  records the rule:

  > `:5638`, `:5610-5611` | graph titles and axis titles are `html.escape`d but drawn as
  > **canvas text** — Bokeh's `Title` and axis labels are glyphs, not HTML, so
  > `title("R&D spend")` displays as `R&amp;D spend` … | do not escape canvas text

  Do not add `html.escape` to any of them. Phase 26 is removing the remaining instances;
  adding new ones there would be a regression against work already scheduled.
- **TR-20.23** **Server parity.** `ServerAppBuilder` (everything after
  `dash_render.py:12265`) has none of this. Its `_Label` emission sits at
  `dash_render.py:13943` and `:13952`, its reference lines at `:13954-13982`, and its
  axis loop iterates only `('xlabel', fig.xaxis), ('ylabel', fig.yaxis)`. For every option
  this phase implements, either emit the equivalent into the app or add the option to the
  help's Server Mode difference table (`dash.sthlp:512-525`) **and** make the note fire in
  server mode. BR-20.10 is not satisfied by a silent drop.

---

## Work items

Three items, numbered exactly as handed over. Tags are `[kind · renderer · effort]`.

---

### Item 1 — `[functional · both · small]`

> Fix `_stata_if_to_pandas`: `missing()` must cover Stata's *string* missing (emit
> `((x != x) | (x == ""))`, or pass the string-variable set into the translator), and a
> missing bound in a range must be handled.

**Where:** `dash_render.py:_stata_if_to_pandas (:6852-6931)`

**Origin:** REMAINING.md main body, "17 DONE claims the adversarial pass overturned",
row `09-06` — *"`missing()` misses Stata's string missing; a missing bound in a range is
mishandled"*. Task 09-06 is *"Support Stata functions in if qualifiers, then commit"*;
this is its unfinished remainder.

**Evidence.** Measured at HEAD by calling the function (table reproduced from *Why this
phase exists*):

| input | output at HEAD | Stata's meaning | dash's result |
|---|---|---|---|
| `missing(make)` | `(make != make)` | `make == ""` | no rows |
| `!missing(make)` | `~(make != make)` | `make != ""` | all rows |
| `inrange(weight, ., 3000)` | `(((weight != weight)) & (weight <= 3000))` | `weight <= 3000` | no rows |
| `inrange(weight, 2000, .)` | `((weight >= 2000) & ((weight == weight)))` | `weight >= 2000`, non-missing | correct |

The translated expression parses and validates, so nothing warns; `df.query` simply
returns an empty frame. Carried into `dash serve` verbatim by the `inspect.getsource`
copy at `dash_render.py:12497-12502`, used at emitted `:13821`, `:15054`, `:15556`.

**Requirements:** TR-20.1 … TR-20.6. **Business:** BR-20.1, BR-20.2, BR-20.3, BR-20.4.

---

### Item 2 — `[functional · both · large]`

> Implement the 13 S09 axes/text options once declared: `droplines` `tlabel` `tline`
> `tmlabel` `tmtick` `tscale` `ttext` `ttick` `ttitle` `xvarformat` `xvarlabel`
> `yvarformat` `yvarlabel`. The `t*` family is the time-axis equivalent of the `x*` family
> and needs the tsset time variable; `*varformat`/`*varlabel` tie into S08.

**Where:** `dash_render.py` axis and annotation paths; `dash.ado` graph syntax block

**Origin:** REMAINING.md §2, the `implement-S09-axes-text` disposition — task `OPT-S09A`.
The same thirteen are the S09 slice of Appendix A `05-04`'s 69 undeclared options.

**Evidence.** Zero occurrences of each name in `dash.ado` at HEAD (grep counts in *Why
this phase exists*), so no value reaches the spec JSON; all thirteen arrive through the
trailing `*` catch-all at `dash.ado:281` and are echoed by `_dash_report_ignored`
(`dash.ado:1338`) as the raw token the user typed. Appendix B, `05-04`, on where they
belong:

> The t\*/pc\* family are graph-level (graph syntax block + the four `foreach
> gk`/`foreach gkey` propagation lists) … *Where:* `dash.ado:_dash_parse_graph_opts
> (syntax block, :281), dash.ado:_dash_parse_plot_opts (syntax block, :475),
> dash.ado:_dash_plot_opts_to_json (:854), dash.ado:_dash_plot (gopts_json loop, :1462),
> dash.ado:_dash_process_seg`

The fixture's own reason for the `t*` family: *"A tsset dataset plus tsline is the single
most likely copy-paste source for dash, and every t\* option aborts."* §2 adds that the
eleven `t*`/`pcarrow` options *"were re-probed on `tsset` monthly data and `pcarrow`
variables to rule out a harness artefact; all 11 are ignored."*

**Requirements:** TR-20.7 … TR-20.16, TR-20.22, TR-20.23.
**Business:** BR-20.5 … BR-20.10.

---

### Item 3 — `[functional · both · large]`

> Implement the declared-but-pending axes/text options: `b1title` `b2title` `l1title`
> `l2title` `r1title` `r2title` `t1title` `t2title` `text` `xmlabel` `xmtick` `ymlabel`
> `ymtick`. They are serialized into the spec and reported as ignored; the renderer reads
> none of them.

**Where:** `dash_render.py:_make_figure_body`, the axis/annotation helpers

**Origin:** REMAINING.md §2, the `implement-S09-axes-text` disposition — task `OPT-S09A`
— as corrected by Appendix A `05-04`:

> Measured, that is wrong for 23 of them: b1title b2title colorlist fxsize fysize
> horizontal l1title l2title lstyle mlstyle mstyle r1title r2title scale sort t1title
> t2title text vertical xmlabel xmtick ymlabel ymtick are reported as ignored AND already
> serialized with their value. The 05-04 gap is 69 options, not 92; the other 23 are
> waiting on S06/S09/S10 renderer work, not on dash.ado.

Thirteen of those 23 are S09-axes-text and are this item.

**Evidence.** Declared and serialized in `dash.ado` (`:293`, `:365-384`, `:424-433`,
`:751-760`, `:1129-1130`/`:1399-1400`/`:1415-1416`/`:1469-1470`), on `_dash_pending`, and
with **zero** reads in `dash_render.py` — 0 occurrences for each of the eight bands and
the four minor-tick keys, and for `text` a single occurrence that is a comment at
`:10160`. Appendix A, `09-02`, on the minor-tick four: *"all four leave a default
`BasicTicker` and are reported as unsupported options."*

**Requirements:** TR-20.17 … TR-20.23. **Business:** BR-20.5, BR-20.7, BR-20.8, BR-20.9,
BR-20.10.

---

## Test plan

Two project rules shape this plan. **Rule 8** — every bug fix needs a regression test that
fails before the fix and passes after; the "failing test first" line below is that test.
**Rule 4** — every function needs a unit test, and the application needs end-to-end
coverage. The mutation column is not optional: this repository has a documented history of
tests that passed against broken implementations, and REMAINING.md's own audit found ten
more. A test that has not been shown to fail has not been shown to work.

### Epic 20.A — the translator

**Failing test first** (write and watch it fail before touching `dash_render.py`), in
`test/test_axis_options.py`, alongside `TestIfQualifierFunctions` (`:718`), whose
`_n_rows(if_expr)` helper already builds a figure and returns its source length:

| test | assertion | fails at HEAD because |
|---|---|---|
| `test_string_missing_selects_the_blank_rows` | `_n_rows('missing(make)')` on auto with 3 blanked `make` values `== 3` | returns 0 |
| `test_not_string_missing_excludes_the_blank_rows` | `_n_rows('!missing(make)') == 71` | returns 74 |
| `test_inrange_with_a_missing_lower_bound_is_unbounded` | `_n_rows('inrange(weight, ., 3000)')` equals the count of `weight <= 3000` | returns 0 |
| `test_inrange_with_a_missing_upper_bound_is_unbounded` | `_n_rows('inrange(weight, 2000, .)')` equals the count of `weight >= 2000` | **passes at HEAD** — it is the pin that stops the fix regressing the case that works |

**Unit tests** (rule 4) — direct on the pure function, no renderer:

| test | assertion |
|---|---|
| `test_translate_string_missing` | `_stata_if_to_pandas('missing(make)')` contains an `== ""` clause |
| `test_translate_inrange_missing_bounds` | the three bound combinations produce the TR-20.2 shapes exactly |
| `test_translate_is_idempotent_on_numeric_missing` | `missing(rep78)` is unchanged from HEAD's `(rep78 != rep78)` — or, if the dtype-agnostic form is chosen, still selects the same rows |
| `test_a_literal_containing_a_dot_is_not_rewritten` | `make == "St. Regis"` survives — the masking invariant of TR-20.4 |

**Adversarial** (rule 18, and the whitelist invariant of TR-20.3): extend
`TestIfQualifierWhitelistIsNotWeakened`'s `hostile` parametrisation at
`test/test_axis_options.py:783` with at least
`missing(open("/etc/passwd"))`, `inrange(__import__('os').getpid(), ., 1)` and
`missing(make) or __import__('os').system('true')`, asserting `False` both raw and
translated. Extend the `ok` parametrisation at `:819` with `missing(make)`,
`!missing(make)` and the three `inrange` bound forms.

**Integration / cscript:** `test/test_axis_options.py` is Python-side. Add the Stata-side
end-to-end to `test/test_conformance.cscript` or a new `test/test_qualifier_missing.cscript`:
`sysuse auto`, blank three `make` values, run `dash scatter mpg weight if missing(make)`,
build, and assert the built HTML's series length against Stata's own
`count if missing(make)`. Run with `arch -arm64` from `test/`, per the project's cert-suite
procedure.

**Server:** add a parity case to `test/test_mode_parity.py`'s `CORPUS` (near `:287`)
carrying `if_expr: 'missing(make)'`, and assert equal row counts. If a new helper was
introduced, add its name to `test_the_scan_found_the_copied_helpers`
(`test/test_mode_parity.py:465`).

**Mutation — prove each test non-vacuous:**

| break this | this test must die |
|---|---|
| revert the `missing()` rewrite to `f"({v} != {v})"` | `test_string_missing_selects_the_blank_rows` |
| revert `_inrange` to the unconditional `((v >= lo) & (v <= hi))` | `test_inrange_with_a_missing_lower_bound_is_unbounded` |
| drop the `(v == v)` not-missing conjunct from the upper-bound case | `test_inrange_with_a_missing_upper_bound_is_unbounded` |
| add `isin` (or any `Call`) to `_validate_if_expr`'s allow-set | every `test_hostile_expressions_are_rejected` case |
| remove the new helper from the copy tuple at `dash_render.py:12497` | `test_every_global_a_copied_helper_calls_is_defined` (`test/test_mode_parity.py:437`) |

### Epic 20.B — the undeclared thirteen

**Failing test first**, one per option, driven from the fixture so it cannot go stale.
The fixture already holds the exact measured probe command for each
(`test/fixtures/rejected_options.json`, `rejected_options[].probes[].command`), so the
first test is a parametrisation over
`[e for e in rejected_options if e['disposition'] == 'implement-S09-axes-text']`:

```
test/test_s09_axes_text.py
  TestTheThirteenUndeclaredOptionsReachTheSpec
    test_the_option_is_declared            -> the name occurs in dash.ado (0 at HEAD)
    test_the_value_reaches_graph_options   -> spec JSON carries the key with its value
    test_the_option_is_not_reported_as_ignored_once_implemented
```

These fail at HEAD for all thirteen, which is the point.

**Unit tests** (rule 4), in `test/test_s09_axes_text.py` unless noted:

| area | tests |
|---|---|
| `t*` routing | `tlabel` on a graph whose `tvar == xvar` produces the same figure as the equivalent `xlabel`; the same for `ttick`/`xtick`, `tmlabel`/`xmlabel`, `tmtick`/`xmtick`, `tscale`/`xscale`, `ttitle`/`xtitle`, `tline`/`xline`, `ttext`/`text`. One test per pair — eight tests, each an equality assertion between two rendered figures, which is also the cheapest possible guard against the two paths drifting. |
| `t*` collision | `xlabel(...)` and `tlabel(...)` together: the `x` form wins and the collision is reported |
| `t*` without tsset | no `tvar` in the spec ⇒ the option is reported, rc 0, figure unchanged |
| `tvar` emission | `dash.ado` writes `tvar` when `_dta[_TStvar]` is set and omits it otherwise (cscript) |
| `droplines` | `droplines(2 4 6)` adds exactly three `Segment` renderers, at x = 2, 4, 6, each running from the base to the curve's y at that x |
| `xvarformat` | `xvarformat(%9.2f)` sets the x formatter; it overrides `build_options["formats"]["weight"]`; an explicit `xlabel(, format(...))` overrides *it* (TR-20.16 precedence, one test per rung) |
| `xvarlabel` | with `variableLabels = {"weight": "Weight (lbs.)"}`, the axis title is the label; an explicit `xtitle()` still wins |
| date literals | `tlabel(2000m1(12)2004m1)` on a `%tm` axis — `xfail(reason="Phase 15 item 4: _apply_axis_spec has no date awareness")` until that lands, never `skip` |

**Integration / cscript:** a new `test/test_axes_text.cscript` running each of the
thirteen fixture probe commands through `dash` on the right data — `sysuse auto` for the
cross-sectional ones, a `tsset` monthly panel for the `t*` ones (the fixture's own
environment used a *"synthetic 60-month tsset panel"*) — asserting rc 0, asserting the
option's name is **absent** from the `ignoring unsupported option(s)` note, and asserting
one measurable property of the built HTML per option. Also extend
`test/test_option_surface.cscript` with the new checks, and
`test/test_conformance.cscript` so the corpus covers a `tsset` command.

**Reporting contract:** `test/test_unsupported_report_is_true.py` must keep passing in
both directions as each option leaves `_dash_pending`; and
`test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue` must pass in the same
commit, which means the help edit is part of the code commit, not a follow-up (Phase 30
reconciles the *prose*; the list membership is enforced here).

**Mutation:**

| break this | this test must die |
|---|---|
| delete the `tlabel`→`xlabel` alias | the `tlabel`/`xlabel` figure-equality test |
| make the alias fire even when `tvar` is empty | the no-tsset reporting test |
| emit `tvar` as the y variable's name | every `t*` routing test on an x-time graph |
| drop the `base` term from `droplines` so segments start at 0 | the `droplines` geometry test |
| let `xvarformat` be consulted *after* `numeric_formats` | the `xvarformat` override test |
| return `varname` from `_axis_label` unconditionally | the `xvarlabel` test |
| leave `tlabel` on `_dash_pending` after implementing it | `test_unsupported_report_is_true.py` **and** `test_help_conformance.py::test_nothing_listed_there_is_honoured` |

### Epic 20.C — the declared thirteen

**Failing test first**, in a new `test/test_title_bands.py`: render
`scatter mpg weight` with all eight band options set to distinct strings and assert that
each string appears in the figure's layout on the expected side. At HEAD every assertion
fails, because `dash_render.py` contains the substring `b1title` zero times.

**Unit tests** (rule 4):

| area | tests |
|---|---|
| bands | one test per band (8): the string is present, on the right side. One test for stacking: `b1title` is nearer the plot than `b2title`, and the same per side. One for the `t()`/`b()`/`l()`/`r()` alias spellings (TR-20.19, after Phase 17 item 6). |
| band fidelity | `b1title("R&D spend")` renders `R&D spend` — assert the band's `text` property, not the HTML, and assert `&amp;` is absent (BR-20.8) |
| `text()` | `text(20 3000 "a note")` adds one data-coordinate `Label` at (3000, 20); two triples add two; `text(20 3000 "a note", size(large) color(red))` renders `a note` with the requested size and colour and **the substring `size(large)` appears nowhere** in the model or the HTML (BR-20.7) |
| shared helper | `text()` and `ttext()` produce identical `Label` objects for equivalent coordinates — the one-helper requirement of TR-20.12 |
| minor ticks | `xmtick(2000(250)5000)` adds minor ticks at those positions **and leaves the major ticks unchanged**; `xmlabel(...)` adds labelled minor ticks; both together; `xmtick` alongside an explicit `xlabel()` (the regression that `xtick` currently has, per Phase 14 item 1 — do not repeat it here) |

**Integration / cscript:** extend `test/test_axes_text.cscript` (from Epic 20.B) with the
thirteen declared options' probe commands from the fixture, same assertions: rc 0, name
absent from the ignored note, one measurable property each. Add one command carrying a
band title and a `text()` annotation to `test/test_conformance.cscript`'s corpus so the
"every layer drew something" pass exercises them.

**Parity:** add a `CORPUS` entry to `test/test_mode_parity.py` carrying band titles and a
`text()` annotation. REMAINING.md, Appendix C, `09-02` records why this matters:

> its figure-chrome comparison checks only background/border colour and grid presence —
> never ticker type, tick positions, formatter or major_label_text_font_size — and its
> CORPUS carries no axis graph_options at all. That is structurally why every 09-02
> server gap went unnoticed.

So the `_chrome` comparison at `test/test_mode_parity.py:178` must be widened to include
the extra title layouts and the tick configuration, or the new corpus entry certifies
nothing. That widening is Phase 16 item 6's deliverable; if it has not landed, this phase
adds the corpus entry **and** the assertions it needs.

**Mutation:**

| break this | this test must die |
|---|---|
| swap `"above"` and `"below"` in the band place map | the per-side band tests |
| add the far band before the near band | the stacking test |
| wrap a band title in `html.escape` | the band-fidelity test |
| pass the raw option string to `Label.text` without `_parse_textbox_opt` | the `text()` sub-option-leak test |
| set minor ticks by replacing the major ticker rather than adding | the "major ticks unchanged" test |
| delete the `_dash_pending` removal for `text` | `test_unsupported_report_is_true.py` |
| delete the matching `dash.sthlp` entry removal | `test_help_conformance.py::test_nothing_listed_there_is_honoured` |

---

## Definition of done

A reviewer can tick each of these.

**Epic 20.A**

- [ ] `_stata_if_to_pandas` emits a string-aware `missing()` rewrite (TR-20.1) and a
      bound-aware `inrange()` rewrite (TR-20.2).
- [ ] The four regression tests named above failed before the change and pass after; the
      `inrange(x, a, .)` pin passed both before and after.
- [ ] Every hostile case in `TestIfQualifierWhitelistIsNotWeakened` still returns `False`,
      raw and translated, including the three new ones.
- [ ] The emitted `bokeh serve` app filters the same rows as the standalone HTML for
      `missing(s)`, `!missing(s)` and the three `inrange` bound forms.
- [ ] If a new helper or constant was added, it is in the copy tuple at
      `dash_render.py:12497-12502` and in
      `test/test_mode_parity.py:465`'s name list.
- [ ] The CHANGELOG records the defect and the fix (task 09-06's own `<action>` requires
      it).

**Epic 20.B**

- [ ] All thirteen names occur in `dash.ado`'s graph syntax block and their values arrive
      in `graph_options` JSON, proved by a test that reads the spec — not by grep.
- [ ] `tvar` is emitted when `_dta[_TStvar]` is set, absent when it is not.
- [ ] Each of the eight `t*` options produces the same figure as its `x*` twin on a graph
      whose time variable is on x.
- [ ] A `t*` option on non-`tsset` data is reported, rc is 0, and nothing aborts.
- [ ] `droplines()`, `xvarformat()`, `xvarlabel()`, `yvarformat()`, `yvarlabel()` each
      change the rendered output and each has a unit test.
- [ ] `xvarlabel`'s real Stata signature was measured, not guessed, and the measurement is
      recorded in `test/fixtures/rejected_options.json` (or `abbrev_truth.json`).
- [ ] Date-literal cases are `xfail` with a reason naming Phase 15 item 4, or they pass.
      **No skips.**
- [ ] Every one of the thirteen has left `_dash_pending` and left `dash.sthlp`'s
      Unsupported section, in the same commit, with
      `test/test_help_conformance.py` green.

**Epic 20.C**

- [ ] The eight bands render on the correct side in the correct near/far order, verified
      against a real `twoway` render.
- [ ] `text()` draws data-coordinate annotations; sub-option text appears nowhere in the
      output.
- [ ] `ttext()` and `text()` go through one helper.
- [ ] `xmtick`/`ymtick`/`xmlabel`/`ymlabel` add minor ticks/labels without disturbing the
      major ticks — or Phase 14 item 2 did it and this phase records that.
- [ ] None of the new canvas text is `html.escape`d; `&`, `<` and `'` all survive.
- [ ] Every one of the thirteen has left `_dash_pending` and the help's Unsupported
      section in the same commit.

**Phase-wide**

- [ ] All 26 `implement-S09-axes-text` options that were "accepted + reported ignored" at
      HEAD now change the rendered output; re-running §2's classification over
      `test/fixtures/rejected_options.json` puts the row at **28 / 28 honoured / 0**.
- [ ] `test/test_unsupported_report_is_true.py` passes in both directions.
- [ ] `test/test_mode_parity.py` carries at least one corpus entry exercising a band
      title, a `text()` annotation and an axis option, and its comparison actually reads
      them.
- [ ] For each option, either the emitted server app honours it or the help's Server Mode
      difference table (`dash.sthlp:512-525`) states the limitation and a note fires
      (BR-20.10). No silent drops.
- [ ] Full pytest and the full certification suite pass with honest skip counts, run with
      `arch -arm64` from `test/`.
- [ ] Committed to the feature branch, never to `main`; the merge command is reported, not
      run (project rule 6); no mention of the assistant in the commit message (rule 7).

---

## Risks and sequencing notes

**1. This phase is gated on Phase 17, and Phase 17 is gated on Phase 18.** Item 2 cannot
start until the thirteen options are declared and serialized, and that declaration goes
through `scripts/regen_option_surface.py`. REMAINING.md, Appendix B, `05-04`:

> Re-running scripts/regen_option_surface.py against HEAD's dash.ado silently deletes
> hand-added declarations that are not in its inventory: `HOVer(string)`, the `T()/B()/L()/R()`
> title aliases, `PBGC/XLA2/XSC2/XTI2/YLA2/YSC2/YTI2`, `BINS(string)`, `sreturn local hover`,
> and — critically — `sreturn local _pending` and `sreturn local _unknown`, which are the only
> channel feeding `_dash_report_ignored`. Deleting those two lines disables 05-03's reporter
> entirely. Since the block comment in dash.ado says "Do not hand-edit … run the generator",
> this is the procedure a developer will follow to do the item above.

Appendix C adds that the splice has **already** double-applied: the generated banner
appears four times, twice per syntax block, and the `t()/b()/l()/r()` fold ladder appears
twice in `_dash_parse_graph_opts` — confirmed at HEAD at `dash.ado:316-319` and
`:338-341`. Both copies run, so behaviour is unchanged, but the next regeneration diff is
unreadable. **De-duplicate before extending.** Item 1 has none of this exposure and should
go first regardless of where Phases 17/18 stand.

**2. Abbreviation collisions are a real risk for this family, not a theoretical one.**
Appendix B, `05-04`:

> Watch for collisions this will force: dash currently accepts shorter prefixes than
> twoway precisely because it declares fewer options (measured:
> `dash scatter mpg weight, mlabel(make) mlabs(3)` -> `"mlabsize":"3"`, while twoway also
> has mlabstyle/mlabtextstyle). `resolve_minimums()` in the generator asserts on
> ambiguity, so adding these names with real measured minimums may trip that assert and
> force longer minimums than existing dash do-files use.

Adding `tlabel`, `tline`, `tmlabel`, `tmtick`, `tscale`, `ttext`, `ttick`, `ttitle` at
once introduces eight new names sharing a `t` prefix, next to the existing `t()` alias for
`t1title` and `title()`. Expect `resolve_minimums()` to fire. The resolution is a
measurement against real `twoway`, not a choice.

**3. The `t*` family cannot be finished before Phase 15.** Every fixture probe uses a date
literal. `_apply_axis_spec` has no date awareness (Appendix C, `09-02`, quoted in
TR-20.10): explicit ticks pass through as raw Stata date numbers, `minmax` is 1000×
too large, `#N` replaces the `DatetimeTicker`, and `format(%td...)` is silently ignored.
Implementing `t*` as an alias onto the `x*` path (TR-20.9) is what makes Phase 15's fix
land on the `t*` family automatically; implementing it as a parallel date parser would
create a second thing to fix. **Alias, do not fork.**

**4. Overlap with Phase 14 on the minor-tick four.** `xmtick`/`ymtick`/`xmlabel`/`ymlabel`
appear both in this phase's item 3 and in Phase 14's item 2 (Appendix B, `09-02`). They
are the same work. Whichever phase runs first implements them; the other records them as
discharged. Do not implement the mechanism twice — a second `FixedTicker` path is exactly
the kind of duplication S15 exists to remove.

**5. Overlap with Phase 26 on escaping.** Phase 26 is removing `html.escape` from canvas
text at, among other sites, the figure title, the axis labels, the legend, the facet
titles and the secondary-axis tick labels. Every string this phase draws is canvas text.
If Phase 26 runs first, follow the pattern it establishes; if this phase runs first, do
not add the escape and leave a comment saying why, citing section 09's register.

**6. Server mode will quietly halve this work.** `_parse_axis_label` occurs 4× in the
renderer and **0×** in the emitted app; `ServerAppBuilder` has no axis grammar, no
secondary axis, and its own cut-down `_Label` emission. Every option added here is a new
opportunity to create a standalone-only behaviour. BR-20.10 is the gate: honour it in both
or say so in the help and fire the note. The cheapest way to satisfy it durably is to run
this phase **after** Phases 05–08 and 16, so that the emitted app delegates rather than
duplicating. If schedule forces this phase earlier, expect to revisit it once Phase 16
lands, and say so in the CHANGELOG rather than leaving the divergence to be found by a
user.

**7. If the maintainer chooses option (b) from §2.** REMAINING.md leaves the choice open:
implement all 92, or implement the high-value subset and formally re-disposition the rest
in the plan and the help. For this phase, (b) keeps `text`, the `ttitle`/`tlabel` family
and the `b1/l1/r1/t1title` set — and drops `droplines`, the four `*varformat`/`*varlabel`
options, the `2`-suffixed bands and the four minor-tick options. That is a smaller item 2
and item 3, **not** a cancelled phase, and the dropped options still need the paperwork:
a re-disposition in `.ultraplan/`, a `_dash_pending` entry that stays, and a help entry
that stays. Make the decision before starting, because it sizes both large items.

**8. Suggested internal order.** (i) Item 1 — independent, small, and it is a wrong-answer
defect, which REMAINING.md's own suggested order puts above everything else. (ii) The
`tvar` plumbing and the `t*` aliasing, which is mechanical once Phase 17 has declared the
names. (iii) The title bands and `text()`/`ttext()`, which share one helper and one
fidelity rule. (iv) `droplines` and the `*varformat`/`*varlabel` pair, which touch the S08
format path and are best done next to Phase 14's display-format fallback. (v) The
minor-tick four, or the note that Phase 14 did them.
