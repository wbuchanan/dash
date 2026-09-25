# Phase 28 — Varlist, server-fix and parser leftovers

**Purpose.** Sections 06 (varlist and plot-spec correctness) and 14 (the server root fix)
both did the hard part and stopped one clause short. S06 taught `dash` to expand
`y1 y2 ... x` into one series per y-variable, to run `function y=x^2`, to accept `twoway`'s
`saving()` forms and to pair `scatteri` labels with their own points — but it never
distributed a plot option *positionally* across an expansion, it left the variable-free
exemption on only one of the two render routes, it stopped short of the emitted server app
when it fixed `scatteri` labels, and it wrote no CHANGELOG entry at all. S14 made
`bokeh serve` serve a real document and unified `dash build` and `dash serve` on one master
JSON — but left a third hardcoded copy of that JSON on the immediate-render path, left six
`shell` browser launches with no `_rc` check, and left both server-test fixtures able to leak
a `bokeh serve` process when startup fails. On top of those sit the three options REMAINING.md
§2 measured as the whole of the `implement-S06` disposition — `horizontal`, `sort`,
`vertical` — declared, serialized, and reported as ignored. This phase is eight small-to-medium
items that close S06 and S14 and leave the record straight: two of them are the paperwork the
audit says was missing, and six change behaviour a user can see.

---

## At a glance

| | |
|---|---|
| **Items** | 8 (numbered 1–8 below, exactly as handed over) |
| **Functional vs deliverable** | 6 functional (1, 2, 4, 6, 7, 8) · 2 deliverable (3, 5) |
| **Effort mix** | 6 small · 2 medium (items 2 and 8) · 0 large |
| **Renderers touched** | `server` (1, 7) · `stata` (2, 4, 6) · `both` (8) · `n/a` (3, 5). Item 8's real home is `GlyphMapper.map_bar`/`map_rbar`, which the emitted app also carries, so doing it there rather than in the hand-written server branches makes it land twice for the price of once. |
| **Ultraplan tasks discharged** | **S06** — `06-02`'s positional-options clause (item 2), `06-03` defect 3 on the `dash build` route (item 4), `06-05`'s server half (item 1), `06-07`'s CHANGELOG clause (item 3). **S14** — `14-01`'s "tear the process down reliably even on failure" (item 5), `14-03`'s third hardcoded JSON (item 7), `14-04`'s `_rc`-check-and-report-the-path clause (item 6). **OPT-S06** — the three `implement-S06` options (item 8). |
| **Not discharged here** | Per-plot `if`/`in` on computed layers (`06-06`) — Phases 01–02. The `_MAX_IPS` rate-limiter structure, the dropdown option cap and the `by()` group cap from §6 — Phase 04. The 15-03 collapse that will delete the hand-written server branches items 1 and 8 touch — Phases 05–08. The help rewrite and the CHANGELOG reconciliation sweep — Phase 30. The six release gates — Phase 31. |
| **Depends on** | Nothing hard. The phase index records Phase 28 as having no predecessor, and every item can be done against HEAD. Two soft orderings matter and are argued in *Risks and sequencing notes*: items 1 and 8's server halves are cheaper **after** Phases 05–08, and item 8's `_dash_pending` edits are **fragile before** Phase 18. |
| **Unblocks** | **Phase 30** (the help's `{marker unsupported}` list at `dash.sthlp:1143-1145` and the missing S06 CHANGELOG section) and **Phase 31** (the conformance and certification gates, which item 4 currently keeps from covering the `dash build` route for variable-free graphs). |
| **Source of items** | All eight come from the **main body** of `REMAINING.md`: the "Status by section" rows 06 and 14, the "17 DONE claims the adversarial pass overturned" rows `06-05` and `14-01`, and §2 "Blocker — the option surface" (item 8). Appendix A's `05-04` supplies the declared/undeclared split that proves the three S06 options are *declared* and still ignored; Appendix B's `15-03` supplies the sequencing constraint on items 1 and 8. |

---

## Why this phase exists

### The two section rows this phase closes — REMAINING.md, "Status by section"

Sources in that table are marked: ① measured this session · ② deep-audit agent ·
③ CHANGELOG (self-reported).

> | # | Section | Tasks | Status | What is left |
> |---|---|---:|---|---|
> | 06 | Varlist / plot-spec | 7 | 2 done, 5 partial ② | `horizontal` `sort` `vertical` ①; positional plot-options across an expanded varlist; **no S06 entry in CHANGELOG** ② |
> | 14 | Server root fix | 5 | 2 done, 3 partial ② | `_MAX_IPS` structure ①; no `_rc` check after the six shell browser launches ② |

The `_MAX_IPS` half of row 14 belongs to Phase 04 (§6, "Resource limits still open"). Every
other clause in both rows is in this document.

In the final tally the two sections read **S06 2 DONE / 5 PARTIAL / 0 NOT DONE** and
**S14 1 / 4 / 0**, and REMAINING.md is explicit about what PARTIAL means here:

> **Read PARTIAL carefully — it is not "half-built".** In most cases the audit
> found the defect the task was written against genuinely fixed and proven
> load-bearing by mutation, with a *secondary* deliverable missing: a cscript
> the TDD stubs named, a CHANGELOG entry, a help sentence, a no-caller test.

That is the shape of this phase: mostly last clauses, two of them paperwork, none of them
large, and four of them things a user can see.

### The two refutations — REMAINING.md, "17 DONE claims the adversarial pass overturned"

> | task | what the refutation found |
> |---|---|
> | 06-05 | `scatteri` marker labels missing from the server app |
> | 14-01 | both server-fixture `__enter__` paths can leak a process on failure |

Both were DONE claims. Both are now PARTIAL. Items 1 and 5 are these two rows.

### The three S06 options — REMAINING.md §2, "Blocker — the option surface"

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
> Not implemented, by family:
>
> - **S06 (3):** `horizontal` `sort` `vertical`
>   — note `sort` is reported "unsupported" although dash sorts by default; if
>   that is a no-op it should say so, not imply the plot is wrong.

S06 is the one family that is **fully declared**. Appendix A's `05-04` table:

> | disposition | total | declared | **not declared** |
> |---|---:|---:|---:|
> | implement-S06 | 3 | 3 | 0 |
> | implement-S07 | 25 | 12 | **13** |
> | implement-S09-axes-text | 28 | 15 | **13** |
> | implement-S09-style | 50 | 7 | **43** |
> | implement-S10 | 5 | 5 | 0 |
> | **total** | **111** | **42** | **69** |

So unlike Phases 19–22, this phase does **not** wait on Phase 17. The values already arrive:
`horizontal`, `vertical` and `sort` are declared, `sreturn`-ed and serialized into the plot
options JSON at HEAD. Confirmed by reading `dash.ado`:

```stata
dash.ado:606:    if `"`horizontal'"' != "" local _dash_pending `"`_dash_pending' horizontal"'
dash.ado:622:    if `"`sort'"'       != "" local _dash_pending `"`_dash_pending' sort"'
dash.ado:628:    if `"`vertical'"'   != "" local _dash_pending `"`_dash_pending' vertical"'
dash.ado:708:    sreturn local horizontal       `"`horizontal'"'
dash.ado:709:    sreturn local vertical         `"`vertical'"'
dash.ado:710:    sreturn local sort             `"`sort'"'
dash.ado:870:                   blabel horizontal vertical sort range colorlist jitterseed {
```

Line `:870` is inside `_dash_plot_opts_to_json`'s key loop, so all three reach
`plot["options"]` in the spec JSON. Nothing reads them on the other side.

### The five things this phase fixes, confirmed at HEAD

Everything below was produced by reading the current tree. Where REMAINING.md or the plan
quotes a different line number, the measurement here supersedes it and says so — the plan's
own numbers are stale (`dash_render.py` grew from ~10,455 to ~16,000 lines).

**1 · The server `scatteri` branch reads two elements of each triple and drops the third.**
`GlyphMapper.map_scatteri` builds the labels and the `LabelSet` (`dash_render.py:5370-5466`):

```python
        # An optional third element on a pair is that point's marker label:
        #   scatteri 20 3000 "A" 30 4000 "B"  ->  [[20,3000,"A"],[30,4000,"B"]]
        _labels = [
            (str(pair[2]) if len(pair) > 2 and pair[2] is not None else "")
            for pair in values
        ]
        _has_labels = any(_labels)
        ...
        if _has_labels:
            from bokeh.models import LabelSet
            _lsrc = ColumnDataSource({
                "x": list(x_vals), "y": list(y_vals), "lab": _labels,
            })
            fig.add_layout(LabelSet(
                x="x", y="y", text="lab", source=_lsrc,
                x_offset=4, y_offset=4,
                text_font_size=self.scheme.text_font_size,
            ))
```

The emitted server branch (`dash_render.py:14658-14674`) takes `p[0]` and `p[1]` and stops:

```python
            "            elif ptype == 'scatteri':",
            "                vals = plot.get('values', [])",
            "                if vals:",
            "                    si_y = [float(p[0]) for p in vals]",
            "                    si_x = [float(p[1]) for p in vals]",
            "                    si_src = ColumnDataSource({'x': si_x, 'y': si_y})",
            ...
            "                    fig.scatter(x='x', y='y', source=si_src, marker=_si_sym,",
            "                                fill_color=_si_mfc, line_color=color, size=_si_sz)",
```

A three-element pair does not raise there — `p[0]`/`p[1]` still index — so the failure mode is
the silent one: `dash scatteri 20 3000 "A" 30 4000 "B"` draws labelled points in standalone
mode and unlabelled points in server mode, with no message anywhere.

**2 · An expanded varlist hands every series the *same* option set.** The expansion
(`dash.ado:1053-1074`) takes the last word as x and every earlier word as its own y, exactly as
`twoway` does. The assembly (`dash.ado:1231-1241`) then attaches one `_opts_json` — built once,
before the loop — to every spec:

```stata
    // Options JSON
    _dash_plot_opts_to_json _opts_json
    ...
    if `"`yvarlist'"' != "" {
        local seg_json ""
        local _nyv : word count `yvarlist'
        forvalues _yi = 1/`_nyv' {
            local _thisy = word(`"`yvarlist'"', `_yi')
            _dash_json_str "`_thisy'" _jyv
            _dash_json_str "`xvar'"   _jxv
            local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
            if `_yi' > 1 local seg_json `"`seg_json',"'
            local seg_json `"`seg_json'{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'
        }
    }
```

`twoway` reads a plot option supplied on a multi-y varlist **positionally** — one value per
y-variable. `dash` gives the whole list to each. So `dash line mpg price weight, lcolor(red blue)`
hands `lcolor` the literal string `red blue` twice. Downstream, `translate_mcolor`
(`dash_render.py:1331-1400`) tries an RGB triplet (three parts — this has two), then the named
colour map, then the hex pattern, and raises:

```python
        raise ValueError(
            f"Unknown Stata color: '{value}'. "
            "Use a Stata named color (e.g. 'navy'), an RGB triplet "
            "(e.g. '0 0 128'), or a hex code (e.g. '#1a476f')."
        )
```

and `_apply_line_opts` swallows it (`except (ValueError, AttributeError): pass`). Both series
fall back to the scheme cycle and the user is told nothing. That is what "currently undone and
silently wrong" means in item 2. The plan asked for exactly this in `06-02`:

> Decide and document what happens to options that name a single thing — `mlabel()`,
> `legend(label(...))` — when one written plot becomes N. `twoway` applies plot-level
> options positionally across the expansion; match that, and where the semantics are
> genuinely ambiguous, state the choice in the help rather than guessing silently.

**3 · The variable-free exemption exists on one route and not the other.** The immediate-render
route carries it (`dash.ado:1655-1671`):

```stata
    // scatteri, pci, pcscatter and function take literal coordinates or an
    // expression rather than variables, so having no varlist is correct for
    // them -- this guard used to reject those plot types outright.
    local _varfree = 0
    foreach _vf in scatteri pci pcscatter function {
        if strpos(`"`json_spec'"', `""type":"`_vf'""') > 0 local _varfree = 1
    }
    if "`needed_vars'" == "" & `_varfree' {
        // Nothing to serialise, but jsonio still needs a non-empty varlist, so
        // send a single variable the renderer will simply not read.
        capture unab _allv : _all
        if _rc == 0 local needed_vars : word 1 of `_allv'
    }
    if "`needed_vars'" == "" {
        display as error "dash: no variables identified in plot specification."
        exit(198)
    }
```

`_dash_prepare_spec` — the shared assembly `dash build` and `dash serve` both go through — has
no such exemption (`dash.ado:2237-2241`):

```stata
    local all_vars = strtrim("`all_vars'")

    if "`all_vars'" == "" {
        display as error "`cmdname': no variables identified across registered graphs."
        exit(198)
    }
```

So `dash scatteri 20 3000 30 4000, saving(x.html)` works and
`dash scatteri 20 3000 30 4000, name(g1)` followed by `dash build, saving(x.html)` exits 198.

**Why no test caught it.** `test/test_varlist_expansion.cscript`'s V2-07 — the check written
for this very defect — drives the **immediate** route only:

```stata
dash clear
capture noisily dash scatteri 20 3000 30 4000, saving("`si_out'")
local rc_si = _rc
...
dash clear
capture noisily dash function x^2, saving("`fn_out'")
```

There is no `name()` + `dash build` case in the file. The cscript's own header lists V2-07 as
"variable-free plot types must render (today r(198))" — half the surface was certified.

**4 · Six `shell` launches, no `_rc` check.** All six sites, read at HEAD:

```stata
dash.ado:1770:        if "`c(os)'" == "MacOSX"  shell open        "`saving_path'"
dash.ado:1771:        if "`c(os)'" == "Windows" shell start "" "`saving_path'"
dash.ado:1772:        if "`c(os)'" == "Unix"    shell xdg-open "`saving_path'"
dash.ado:2510:            if "`c(os)'" == "MacOSX"  shell open        "`saving'"
dash.ado:2511:            if "`c(os)'" == "Windows" shell start "" "`saving'"
dash.ado:2512:            if "`c(os)'" == "Unix"    shell xdg-open "`saving'"
```

The `dash build` group at `:2510-2512` is preceded by `display as text "dash: dashboard saved
to \`saving'"` at `:2504`, so that path at least prints the file. The immediate group at
`:1770-1772` sits in the `if "\`open_browser'" == "1"` branch and the path is displayed only in
the **`else`**: when a launch is attempted and fails, the user gets nothing at all — no rc, no
path, and the file is in a tempdir they cannot guess. `14-04` named this:

> There is also no `_rc` check after any of the six `shell` lines, and the immediate path
> never displays the temp file path, so a failed `xdg-open` leaves the output unreachable —
> report the path on failure.

**5 · Three master-JSON assemblies, not two.** `14-03` unified `dash build` and `dash serve` on
`_dash_prepare_spec`, whose assembly is `dash.ado:2343` and carries thirteen keys. The third
copy is still a literal in `_dash_render_immediate` (`dash.ado:1723`) and carries five:

```stata
    local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "", "session_scheme": "`_sess_scheme_esc'", "level": "`_dash_lvl'", "formats": `_dash_fmt_json'}}"'
```

against

```stata
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"`layout'","link":"`link'","filter":"`filter_json'","theme":"`theme'","scheme":"`_scheme_esc'","session_scheme":"`_sess_scheme_esc'","title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`filterposition'","level":"`_dash_lvl'","formats":`_dash_fmt_json'}}"'
```

`14-03`'s own note said why this matters, and the comment block `_dash_prepare_spec` carries
(`dash.ado:1972-1989`) records what drift between two copies already cost once:

> There were two copies of this, and they had drifted. `dash build'
> carried every option the user gave it. `dash serve' declared three
> options -- port(), nobrowser(), timeout() -- and wrote build_options
> that were literal constants:
>
>     "layout":"auto","link":"","filter":"","theme":"","title":"","subtitle":""
>
> with no scheme, tabs or filter_position key present at all.

One clause of `14-03`'s complaint **is** fixed: the immediate literal no longer says
`"theme":"default"`, and it now carries `session_scheme`, which the renderer's precedence
chain reads (`dash_render.py:7957-7962`: `scheme` → `theme` → a graph's own scheme →
`session_scheme`). What remains is structural: eight `build_options` keys exist on one route
and not the other, and nothing stops them drifting again.

**6 · Both server fixtures can leave a `bokeh serve` running.** `test/test_server_serves.py`,
`_Served.__enter__` (`:106-125`) and `_Launched.__enter__` (`:167-184`) both `Popen`, poll for
readiness, and raise on timeout without touching the process:

```python
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise AssertionError(
                    f"bokeh serve exited early:\n{out[:3000]}")
            try:
                self.get("/app")
                return self
            except Exception:
                time.sleep(0.4)
        raise AssertionError("bokeh serve never answered")
```

Because `__enter__` raised, the `with` statement never binds and `__exit__` — which holds the
only teardown (`:127-133`) — never runs. `_Launched` inherits that teardown by assignment
(`:186  __exit__ = _Served.__exit__`), so the fix has one natural shape: factor the teardown
into `_stop()` and call it from the failure paths of both `__enter__`s. `14-01`'s own action
clause asked for this in advance:

> Make the fixture robust: pick a free port, wait for readiness rather than sleeping, and
> tear the process down reliably even on failure. An orphaned `bokeh serve` in CI is its own
> problem.

---

## Epics

| epic | goal | items |
|---|---|---|
| **E28.1 — The S06 parser leftovers (Stata side)** | Every documented `twoway` invocation survives the `dash build` route as well as the immediate one, and an expanded varlist distributes its plot options the way `twoway` does instead of copying them whole. | 2, 4 |
| **E28.2 — The S06 render leftovers, and the S06 record** | `scatteri` labels reach server mode; `horizontal`, `sort` and `vertical` are each honoured or honestly declined, in both renderers; and what S06 changed is finally written down. | 1, 8, 3 |
| **E28.3 — The S14 leftovers** | A server fixture that cannot leak a process, a browser launch that reports its rc and its path, and one master-JSON assembly instead of three. | 5, 6, 7 |

---

## User stories

### E28.1 — The S06 parser leftovers

**US-28.1.1** — *As a Stata user pasting `twoway line mpg price weight, lcolor(red blue) lpattern(solid dash)`,
I want each series to take its own colour and pattern, so that the picture means what the
command says.*

- **Given** `dash line mpg price weight, lcolor(red blue)`, **when** the dashboard is built,
  **then** the `mpg` line is red and the `price` line is blue. Today both are scheme colours
  and the option is discarded without a note.
- **Given** `dash line mpg price weight, lcolor(red)` — fewer values than series — **when** the
  dashboard is built, **then** `dash` follows the rule it documents (either recycle the last
  value, as `twoway` does for several style options, or apply to the first and let the scheme
  supply the rest) and the rule is stated in `dash.sthlp`, not guessed silently.
- **Given** a plot option whose positional semantics are genuinely ambiguous across an
  expansion — `mlabel()` naming one variable, `legend(label(...))` naming one slot — **when**
  the command runs, **then** `dash`'s choice is documented in the help and the command still
  returns rc 0.
- **Given** a single-y command (`dash line mpg weight, lcolor(red)`), **when** the dashboard is
  built, **then** nothing changes: the generated HTML is identical to today apart from Bokeh's
  per-run ids.
- **Given** a range or paired-coordinate plot (`rarea`, `pcspike`), **when** it is built,
  **then** it is unaffected — those families have fixed arity and go through
  `_dash_parse_varpart_3v` / `_4v`.

**US-28.1.2** — *As a Stata user who registers a `scatteri` annotation graph with `name()` and
then runs `dash build`, I want the dashboard to build, so that the route I use for every other
graph works for this one too.*

- **Given** `dash scatteri 20 3000 30 4000, name(g1)` followed by
  `dash build, saving(d.html)`, **when** the build runs, **then** it returns rc 0 and writes
  `d.html`. Today it exits 198 with "no variables identified across registered graphs."
- **Given** the same for `pci`, `pcscatter` and `function`, **when** each is built, **then**
  each returns rc 0.
- **Given** a genuinely empty registry, **when** `dash build` runs, **then** it still exits 198
  with the message naming `name()` — the exemption must not swallow the real error.
- **Given** a registry mixing a variable-free graph with an ordinary `scatter`, **when** it is
  built, **then** both graphs draw, and the ordinary graph's variables are serialized exactly
  as before.
- **Given** a variable-free graph built against a dataset with no variables at all, **when**
  `dash build` runs, **then** it fails with a legible message rather than a Stata error from
  `unab`.

### E28.2 — The S06 render leftovers, and the S06 record

**US-28.2.1** — *As a `dash serve` operator, I want `scatteri` marker labels to appear in the
served dashboard, so that choosing a delivery mode does not silently delete annotations.*

- **Given** a spec whose `scatteri` layer carries `values` of the form
  `[[20, 3000, "A"], [30, 4000, "B"]]`, **when** the emitted app builds its document, **then**
  the figure carries a `LabelSet` with `text` `["A", "B"]`.
- **Given** that same spec, **when** it is compared with the standalone figure by
  `test/test_mode_parity.py`'s `_annotations`, **then** the two agree on `text`,
  `text_font_size`, `text_color`, `x_offset` and `y_offset` — the five properties that helper
  collects.
- **Given** a `scatteri` layer with **no** labels, **when** the app builds, **then** no
  `LabelSet` is added, exactly as standalone does when `_has_labels` is false.

**US-28.2.2** — *As a Stata user pasting `twoway bar count category, horizontal`, I want either
horizontal bars or a note telling me they are not coming, so that I never ship a plot that is
silently the wrong orientation.*

- **Given** `dash bar mpg foreign, horizontal`, **when** the dashboard is built, **then** the
  bars run along the x-axis from the y-variable's baseline, **or** `horizontal` is named in the
  command's `dash: ignoring unsupported option(s):` note.
- **Given** the same command through `dash build, server`, **when** the emitted app builds its
  document, **then** it draws what standalone drew — `test/test_mode_parity.py` compares glyph
  types, and `HBar` against `VBar` is a failure there.
- **Given** `dash area mpg weight, sort` on unsorted data, **when** the dashboard is built,
  **then** the area is drawn in x order, **or** the note names `sort`. `map_line`
  (`dash_render.py:3526`) already sorts; `map_area` (`:3592`) and `map_rarea` (`:4920`) do not,
  so "already sorted" is not true of every layer that accepts the option.
- **Given** `dash line mpg weight, sort`, **when** the dashboard is built, **then** `dash` says
  the option is a no-op *because the layer already sorts by x* rather than implying the plot is
  wrong — REMAINING.md §2's explicit request.
- **Given** `dash bar mpg foreign, vertical`, **when** the dashboard is built, **then** the
  bars are vertical and nothing is reported as ignored, because vertical is what `dash` already
  draws.
- **Given** any of the three becomes honoured, **when** the commit lands, **then**
  `_dash_pending` (`dash.ado:606`, `:622`, `:628`) and `dash.sthlp:1143-1145` change in the
  same commit and `test/test_help_conformance.py` passes.

**US-28.2.3** — *As a package maintainer, I want an S06 section in the CHANGELOG, so that a
user who sees a different picture after upgrading can find out why.*

- **Given** `.ultraplan/CHANGELOG.md`, **when** it is read, **then** it contains a `## S06`
  section in the file's established shape — a before/after/evidence table plus a "Bugs fixed"
  list — covering the behaviour changes S06 actually made.
- **Given** a row in that table, **when** a reviewer checks it, **then** the "after" value is
  one a named test or a named measurement produces, not a restatement of the plan.
- **Given** a defect S06 was written against but did **not** close — per-plot `if` on computed
  layers, positional options across an expansion — **when** the section is read, **then** it is
  listed as still open and pointed at the phase that owns it, not recorded as fixed.

### E28.3 — The S14 leftovers

**US-28.3.1** — *As a package maintainer running the suite, I want a failed server start-up to
kill its own process, so that a red test does not leave a `bokeh serve` holding a port.*

- **Given** `_Served.__enter__` where the server never answers within the deadline, **when**
  the `AssertionError` is raised, **then** the subprocess has been terminated and
  `proc.poll()` is not `None`.
- **Given** the same on `_Launched.__enter__`, **then** the same holds.
- **Given** a normal successful run, **when** the `with` block exits, **then** teardown
  behaviour is exactly what it is today — terminate, wait 15s, kill on timeout.
- **Given** `_Launched`, which takes its teardown by assignment from `_Served`, **when** the
  refactor lands, **then** both classes still share one implementation and neither grows a
  second copy.

**US-28.3.2** — *As a Stata user whose machine has no working `xdg-open`, I want `dash` to tell
me the rc and the path, so that I can open the dashboard myself instead of wondering where it
went.*

- **Given** a build whose browser launch fails, **when** the command finishes, **then** `dash`
  displays the output path and reports that the browser could not be opened, and the command's
  own rc is unchanged — a failed *viewer* is not a failed *build*.
- **Given** the immediate-render path (`dash scatter mpg weight` with no `saving()`), **when**
  the launch fails, **then** the temp file path is displayed. Today that path prints only in
  the branch where no browser is attempted.
- **Given** `${dash_nobrowser}` is set, or `nobrowser` is given, **when** the command runs,
  **then** no shell launch is attempted and no failure message is produced.
- **Given** a successful launch, **when** the command finishes, **then** the output is what it
  is today — no new chatter on the happy path (project rule 14).

**US-28.3.3** — *As a package maintainer, I want one master-JSON assembly, so that a key added
for `dash build` cannot be missing from `dash`'s own immediate render.*

- **Given** the three emission paths — immediate render, `dash build`, `dash serve` — **when**
  the master JSON is written, **then** all three go through one helper and the `build_options`
  key set is identical by construction.
- **Given** a new `build_options` key added to that helper, **when** the suite runs, **then**
  a test asserts it appears on every path rather than on the one the author was working on.
- **Given** the immediate path, **when** its JSON is compared with `dash build`'s for the same
  single graph, **then** they differ only where they legitimately must (`registry`, which the
  immediate path has no registry for; `layout`, which is `1 1` for one graph).

---

## Business requirements

| id | requirement | how it is testable |
|---|---|---|
| **BR-28.1** | A plot option supplied on a multi-y varlist is distributed across the expanded series the way `twoway` distributes it, and where `dash` must choose, the choice is documented. | Render `dash line y1 y2 x, lcolor(red blue)` and assert two distinct glyph colours matching the two named colours; assert the documented rule for a short list. |
| **BR-28.2** | A single-y command's output is byte-identical to today apart from Bokeh's per-run ids. | The existing V2-05 regression guard in `test/test_varlist_expansion.cscript`, re-run. |
| **BR-28.3** | Every variable-free plot type (`scatteri`, `pci`, `pcscatter`, `function`) builds on **both** the immediate route and the `dash build` route. | New cscript cases driving `name()` + `dash build` for each of the four; rc 0 and the file exists. |
| **BR-28.4** | A genuinely empty registry, and a registry whose graphs name no variables for any other reason, still fail with the existing legible message. | Negative cases in the same cscript: rc 198 and the message text. |
| **BR-28.5** | A `scatteri` marker label drawn in standalone mode is drawn in server mode, with the same font size, colour and offsets. | A labelled `scatteri` case added to `test/test_mode_parity.py`'s `CORPUS`; `test_same_annotations` compares them. |
| **BR-28.6** | Each of `horizontal`, `sort` and `vertical` is, at the end of this phase, either **honoured** (its presence changes the output) or **reported** (named in the ignoring-unsupported note with a reason that is true of the layer it was given to) — in both renderers. Never silently dropped, and never reported in terms that imply a correct plot is wrong. | A converse test over the three, driven from `test/fixtures/rejected_options.json`'s `implement-S06` slice, run against `DashRenderer` and `ServerAppBuilder`. |
| **BR-28.7** | An option that becomes honoured leaves `_dash_pending` **and** `dash.sthlp`'s unsupported list in the same commit. | `test/test_help_conformance.py`, which the help states "fails if they disagree in either direction". |
| **BR-28.8** | `.ultraplan/CHANGELOG.md` contains an S06 section recording every behaviour change S06 made, each with a before value, an after value and evidence, and naming what S06 did **not** close. | Review against the file's own stated contract: "Each one records the value before, the value after, and the evidence." |
| **BR-28.9** | A server-test fixture that fails to start leaves no live subprocess. | A test that forces the timeout path and asserts `proc.poll() is not None`. |
| **BR-28.10** | A failed browser launch reports the rc and the output path, on every one of the six launch sites, and does not change the command's own return code. | Cscript exercising the failure seam on both routes; assert message and rc 0. |
| **BR-28.11** | The `build_options` key set is identical across the immediate, `dash build` and `dash serve` paths, by construction rather than by inspection. | A test that builds one graph through each path and compares `sorted(build_options.keys())`. |
| **BR-28.12** | Nothing in this phase makes the Stata log noisier on the happy path (project rule 14), and no new `shell` interpolation surface is introduced (project rules 1 and 16). | `test/test_render_log_clean.cscript`; review of any new shell argument against the validator at `dash.ado:150-215`. |

---

## Technical requirements

### TR-28.1 — Positional plot-options across an expanded varlist  *(item 2)*

**Where.** Expansion: `dash.ado:1053-1074` (`_dash_parse_varpart_std` at `:779`, consumed at
`:1061`). Assembly: `dash.ado:1218-1245`. The option JSON is built **once** at `:1220`
(`_dash_plot_opts_to_json _opts_json`) and interpolated unchanged into every expanded spec at
`:1239`.

**Mechanism.** The fix belongs at the assembly, not at the parse: for each expanded index
`_yi`, build that series' own option JSON by taking the `_yi`-th token of each list-valued
option and the whole value of each scalar option. Two sub-problems, and both must be decided
in writing:

1. **Which options are list-valued.** `_dash_plot_opts_to_json`'s key loop (`dash.ado:860-870`)
   carries 60 keys. `twoway` accepts a per-series list for the style options —
   `lcolor` `lwidth` `lpattern` `lalpha` `mcolor` `msymbol` `msize` `mfcolor` `mlcolor`
   `mlwidth` `mangle` `fcolor` `falpha` `fintensity` `pstyle` `connect` `recast` — and a
   single value for the estimation and geometry options (`bwidth`, `level`, `n`, `bin`,
   `start`, `width`, `range`, `base`, `barwidth`, `jitter`, `jseed`). Build the list from the
   key loop at `:860-870`, not from memory, so the two cannot drift.
2. **What a short list means.** `twoway` recycles: the last supplied value applies to every
   remaining series for the style options. Match that, and state it in `dash.sthlp`. Where the
   option names one thing and cannot be split — `mlabel(varname)`, `legend(label(...))` —
   `06-02` requires the choice be documented rather than guessed; the defensible choice is
   "applies to the first expanded series only", because the alternative labels N series with
   one variable's values and looks deliberate.

**Failure mode to keep in mind while implementing.** A multi-token colour does not raise
anywhere the user can see it: `translate_mcolor` (`dash_render.py:1331-1400`) raises
`ValueError`, and the call sites swallow it — `_apply_line_opts` with
`except (ValueError, AttributeError): pass`, `map_scatteri` with `except ValueError: pass`
(`dash_render.py:5429-5436`). So a half-done split degrades to "scheme colours, no message",
which is indistinguishable at a glance from correct output. The test must assert the **two
distinct resolved colours**, not the absence of an error.

**Out of scope.** The range (`_dash_parse_varpart_3v`) and paired-coordinate
(`_dash_parse_varpart_4v`) families have fixed arity and are not expanded; `06-02` asked for a
test asserting they are unaffected, and that test belongs here.

### TR-28.2 — The variable-free exemption on the `dash build` route  *(item 4)*

**Where.** The working copy: `dash.ado:1655-1671` (`_dash_render_immediate`, program at
`:1589`). The missing copy: `dash.ado:2237-2241` (`_dash_prepare_spec`, program at `:2001`).

**Mechanism.** `_dash_prepare_spec` accumulates `all_vars` by walking the registry
(`dash.ado:2127-2174`), reading each graph's JSON from `${dash_json_<gname>}` through
`mata: _dash_extract_vars` and `mata: _dash_extract_qual_vars`, then adding filter variables
(`:2183-2234`). The exemption goes immediately before the abort at `:2237`: for each registered
graph, apply the same `strpos(..., "\"type\":\"<vf>\"")` test the immediate path uses over the
four variable-free types, and if **every** contributing graph is variable-free, substitute one
placeholder variable exactly as `:1665-1670` does:

```stata
        capture unab _allv : _all
        if _rc == 0 local needed_vars : word 1 of `_allv'
```

Three constraints:

- The existing abort must survive for the genuinely empty case. `_dash_prepare_spec` already
  exits 198 earlier if `${dash_graph_registry}` is empty (`:2046-2049`) with a different
  message; the `:2237` abort must still fire when a registry holds graphs that name no
  variables for reasons other than being variable-free.
- `capture unab _allv : _all` can legitimately return nothing on an empty dataset. The
  immediate path guards with `if _rc == 0`; the build path must do the same and then fall
  through to the existing 198 rather than emitting a spec with an empty varlist.
- A mixed registry (one `scatteri` graph, one `scatter` graph) already works, because
  `all_vars` is non-empty. The exemption must not alter that path at all.

**Do not** duplicate the four type names in a third place. Factor them into one local or one
small program (`_dash_is_varfree`) used by both routes, so the next plot type that takes
literal coordinates is added once.

### TR-28.3 — The `scatteri` LabelSet in the emitted app  *(item 1)*

**Where.** Source of truth: `GlyphMapper.map_scatteri`, `dash_render.py:5370-5466` (the
`_labels`/`_has_labels` block at `:5409-5413`, the `LabelSet` at `:5455-5464`). Target: the
emitted `elif ptype == 'scatteri':` branch, `dash_render.py:14658-14674`.

**Mechanism.** Mirror the standalone block, with exactly its values:

| property | standalone value | source |
|---|---|---|
| `x` / `y` | the same coordinate lists the markers use | `map_scatteri` builds `_lsrc` from `x_vals` / `y_vals` |
| `text` | `"lab"` — the third element of each pair, `""` when absent | `dash_render.py:5409-5413` |
| `x_offset` | `4` | `dash_render.py:5462` |
| `y_offset` | `4` | `dash_render.py:5462` |
| `text_font_size` | `self.scheme.text_font_size` (`gsize text`, default `"10pt"`, `dash_render.py:2043`) | `dash_render.py:5463` |
| `text_color` | not set — Bokeh's default | `map_scatteri` passes none |

**The transport gap this exposes.** The emitted app's scheme constants are written at
`dash_render.py:12595-12624`. `_SCHEME_CHROME` carries `axis_title_font_size` and
`tick_label_font_size` but **not** `text_font_size`, and there is no `_SCHEME_TEXT_FONT_SIZE`
beside `_SCHEME_MARKER_SIZE` (which the same `scatteri` branch already uses at `:14663`). Add
one of the two; do not hardcode a size. This is what the parity assertion on
`text_font_size` will catch.

**Do not copy the neighbouring convention.** The emitted `rcapsym` branch four screens up
(`dash_render.py:14450-14455`) builds its `LabelSet` with `text_font_size='9px'`,
`text_color=_r_mlc or '#333333'`, `x_offset=5, y_offset=5`. Those are a *different* marker-label
path (`mlabel()` on a range plot), and using them here would fail
`test/test_mode_parity.py::test_same_annotations` on four of the five compared properties.

**`LabelSet` is already imported** in the emitted app — the `rcapsym` branch calls
`LabelSet(**_r_mlab_kw)` unguarded — so no new import is needed.

**Note on `by()`.** Appendix B records `scatteri` as one of the 20 plot types that draw nothing
under `by()` / `by(total)` in server mode, because the two emitted facet chains handle only 18
types. That is Phase 07's item. The parity case written for this item must therefore **not**
use `by()`, or it will fail for a reason this phase does not own.

### TR-28.4 — `horizontal`: the eight drawing sites  *(item 8)*

Confirmed at HEAD, `fig.hbar` appears nowhere in `dash_render.py`. The bar-drawing sites are:

| site | line | what it draws |
|---|---:|---|
| `GlyphMapper.map_bar` — empty-source guard | `dash_render.py:3687` | `fig.vbar(x=xvar, top=yvar, bottom=0, width=0.8, …)` |
| `GlyphMapper.map_bar` — real | `:3728-3739` | `fig.vbar(**_vbar_kwargs)` |
| `GlyphMapper.map_rbar` — empty-source guard | `:4984` | `fig.vbar(x=xvar, top=y2var, bottom=y1var, …)` |
| `GlyphMapper.map_rbar` — real | `:4998` | `fig.vbar(**_rbar_kwargs)` |
| emitted main loop, `ptype == 'bar'` | `:14310-14313` | `fig.vbar(x=xvar, top=yvar, bottom=_bar_bottom, …)` |
| emitted main loop, `ptype == 'rbar'` | `:14478` | `fig.vbar(x=xvar, bottom=y1var, top=y2var, …)` |
| emitted `by()` facet chain | `:15149` | `_fac_fig.vbar(...)` |
| emitted `by(total)` facet chain | `:15250` | `_tot_fig.vbar(...)` |

**Mechanism.** `horizontal` swaps the roles of the two axes: `fig.hbar(y=<the categorical/x
variable>, right=<the value variable>, left=base, height=<the computed width>)`. The
bar-width computation in `map_bar` (`:3692-3705`) — 80% of the smallest gap between distinct
x values, with a string-x fallback to uniform spacing — carries over unchanged as the bar
*height*. Axis titles swap with the geometry, or the figure is mislabelled.

**Do the work in `map_bar` / `map_rbar`.** Both are already emitted into the generated app
(the emitted branches are the hand-written copies `15-03` exists to delete). Implementing in
the mappers means the server inherits it the moment Phases 05–08 land, and the interim server
edit is a two-line mirror rather than a second implementation. The two facet copies at
`:15149` and `:15250` belong to Phase 06 and should be left to it — but note in the handover
that they now have an option to carry.

### TR-28.5 — `sort`: what is already sorted and what is not  *(item 8)*

REMAINING.md leaves this open — "note `sort` may be a genuine no-op because dash already sorts
by x — if so it should say that rather than imply the plot is wrong". Measured at HEAD, the
answer differs by layer, so one blanket disposition will be wrong either way:

| layer | sorts by x today? | evidence |
|---|---|---|
| `line`, `connected` | **yes** | `map_line`: `df.dropna(subset=[xvar, yvar]).sort_values(xvar)` (`dash_render.py:3526`); the docstring says so. `map_connected` delegates to `map_line` (`:3585-3587`). |
| `tsline`, and the emitted line/connected/tsline branches | **yes** | emitted `sort_values(xvar)` at `:14100`, `:14266`, `:14333`, `:14721` |
| `bar` | no — but order does not change the picture | `map_bar` (`:3688-3691`) drops NaN and draws each bar at its own x |
| `area` | **no** | `map_area` (`:3614-3630`) takes `source.data[xvar]` in row order and hands it straight to `fig.varea` |
| `rarea` | **no** | `map_rarea` (`:4946-4954`) draws `fig.varea` from the shared source with no sort at all |

So the honest disposition is per-family: a no-op for the line family (say *why* — "already
sorted by x"), a real behaviour change for `area`/`rarea` (either sort, or report), and
irrelevant for `bar`. `dash.sthlp`'s current wording (`:1143-1145`) covers bars and lines and
is silent on `area`:

> {opt at(varname)}, {opt blabel(...)}, {opt horizontal}, {opt vertical},
> {opt sort} — bars are drawn vertically at the x variable's values, and
> {cmd:line} plots are already sorted by x, as in {cmd:twoway}.

Whatever is decided, that sentence changes in the same commit as the code (TR-28.7).

### TR-28.6 — `vertical`: the option that asks for what already happens  *(item 8)*

`vertical` is `twoway`'s explicit spelling of the bar default, and `dash` draws vertical bars
everywhere (TR-28.4). The correct close is therefore to **honour it by accepting it as a
no-op** — remove it from `_dash_pending` (`dash.ado:628`) and from the help's unsupported list,
and make `horizontal` and `vertical` mutually exclusive with a legible error if both are given.
Reporting an option as "ignored" when the output already matches it is the failure mode the
comment at `dash.ado:584-592` was written about:

```stata
    // A note that names the wrong options is worse than no note: it tells
    // the user to stop using something that works.
```

### TR-28.7 — The pending / help / conformance contract  *(item 8)*

Three places must move together for each of the three options:

1. `dash.ado` `_dash_pending` at `:606` (`horizontal`), `:622` (`sort`), `:628` (`vertical`).
2. `dash.sthlp:1143-1145`, the "Bar and dot geometry" entry under `{marker unsupported}`
   (`:1092`).
3. `test/fixtures/rejected_options.json`, whose `implement-S06` slice is the fixture §2 was
   measured from.

`dash.sthlp:1104-1107` states the contract the help itself advertises:

> This list and that note are generated from the same declarations in
> {cmd:dash.ado}, and {cmd:test/test_help_conformance.py} fails if they
> disagree in either direction.

No serialization work is required: all three keys already reach `plot["options"]` through
`_dash_plot_opts_to_json`'s key loop (`dash.ado:870`).

### TR-28.8 — The S06 CHANGELOG section  *(item 3)*

**Where.** `.ultraplan/CHANGELOG.md`. Read at HEAD, its section headings are `S07`, `S08`,
`S09`, `S10`, `S11`, then four topical sections, then `S14`, `S15`, `S16`. There is **no S06
heading**, which is the audit's claim, confirmed.

**Shape.** The file's own contract (`.ultraplan/CHANGELOG.md:1-7`):

> Every entry here changes a number or a picture a user has already seen. Each
> one records the value before, the value after, and the evidence.

and the established layout is `### Changed defaults` (a before/after/evidence table) followed
by `### Bugs fixed` (prose bullets). The S06 section's rows are the seven defects the section
was written against, each of which is verifiable in the current tree:

| change | before | after | where to verify |
|---|---|---|---|
| multi-y varlist | `dash scatter mpg price weight` drew **one** series | one plot spec per y-variable, each taking the next scheme style index | `dash.ado:1053-1074`, `:1231-1241`; V2-01…V2-05 |
| `function y=x^2` | r(101) `=exp not allowed` | parses; `equalok` on `_dash_parse_varpart_any` | `dash.ado:836-840`; V2-06 |
| variable-free plots | r(198) "no variables identified" | render on the immediate route | `dash.ado:1655-1671`; V2-07. **Still open on the `dash build` route — item 4 of this phase.** |
| `tsline` with no x | r(7102) `KeyError: ''` | reads `_dta[_TStvar]`; un-`tsset` gives r(111) naming `tsset` | `dash.ado:1077-1091`; V2-12 |
| `name(g1, replace)` | r(198), the error recommending syntax that could not work | the `, replace` suffix is split before the name is validated | `dash.ado:1524-1564`; V2-08 |
| `saving()` forms | r(198) on `saving(myfig)`, `saving(myfig.gph)`, `saving(f.html, replace)` | all three accepted; `.gph` reported and written as `.html`; parenthesised paths accepted | `dash.ado:1604-1620`, `:192-212`; V2-09 |
| `scatteri` labels | `[[20,3000],["A",30],[4000,"B"]]` | numeric pairs with an optional trailing label per point | `dash.ado:710-727`-family parse, `dash_render.py:5395-5413`; V2-10. **Server half is item 1 of this phase.** |

**What must not be claimed.** Two S06 defects are not closed and the section must say so with a
pointer: per-plot `if`/`in` on computed layers (`06-06`, Phases 01–02 — REMAINING.md §5 has the
measurement: `regress mpg weight if foreign==1` gives slope `-.01042596`, `dash` draws the
unqualified `-.00600869`) and positional plot-options across an expansion (item 2 here). Rule 2
binds: a CHANGELOG that records an open defect as fixed is worse than no CHANGELOG.

### TR-28.9 — The server fixtures' `_stop()`  *(item 5)*

**Where.** `test/test_server_serves.py`: `_Served` (`:92`), `__enter__` (`:106-125`), `__exit__`
(`:127-133`); `_Launched` (`:150`), `__enter__` (`:167-184`), `__exit__ = _Served.__exit__`
(`:186`).

**Mechanism.** Move the body of `_Served.__exit__` into `_stop()`:

```python
    def _stop(self):
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except Exception:
                self.proc.kill()

    def __exit__(self, *exc):
        self._stop()
        return False
```

then wrap each `__enter__` body in `try: … except BaseException: self._stop(); raise`.
`BaseException`, not `Exception`: a `KeyboardInterrupt` during the 60-second readiness loop is
exactly when a stray server is most likely. `_Launched` keeps `__exit__ = _Served.__exit__` and
gains `_stop = _Served._stop`, or simply subclasses — either way there stays **one**
implementation, which is the item's own instruction ("Factor the existing `__exit__` teardown
into a `_stop()` and call it from both").

Note that the "exited early" branch (`:116-119`, `:174-176`) is not itself a leak — `poll()`
has already returned non-`None` — but it must go through the same path so the cleanup is
unconditional rather than a judgement made per branch.

### TR-28.10 — `_rc` and the path after each browser launch  *(item 6)*

**Where.** `dash.ado:1770-1772` (immediate render, inside `if "\`open_browser'" == "1"`) and
`:2510-2512` (`dash build`, inside `if "\`nobrowser'" == "" & "${dash_nobrowser}" == ""`).

**Mechanism.** Factor the OS dispatch into one program — `_dash_open_browser <path>` — called
from both sites. Six `shell` lines become three, and the failure handling is written once:

```stata
program define _dash_open_browser
    version 16.0
    args target
    if "`c(os)'" == "MacOSX"  capture shell open        "`target'"
    else if "`c(os)'" == "Windows" capture shell start "" "`target'"
    else if "`c(os)'" == "Unix"    capture shell xdg-open "`target'"
    if _rc {
        display as text "dash: could not open a browser (rc `=_rc'). " ///
            "The dashboard is at:"
        display as text `"  `target'"'
    }
end
```

Four constraints:

- **The command's own rc must not change.** A failed viewer is not a failed build; `capture`
  keeps `_rc` local to the launch and the caller returns 0 as it does today.
- **The path is already validated.** `dash.ado:150-215` rejects shell metacharacters and `..`
  before any of this runs, and the comment at `:198-205` records that parentheses are
  deliberately *not* rejected because every call site quotes the path. Keep the quoting; add no
  new interpolation. (Project rules 1 and 16.)
- **The immediate path must display the path on failure**, which today it does only in the
  `else` branch at `dash.ado:1773-1775`. That is the whole user-visible point of the item.
- **Silence on success.** `test/test_render_log_clean.cscript` exists because a single-line
  `python:` once dumped ~10 KB of module globals into the log; do not trade that for a chatty
  browser launch. (Project rule 14.)

**Test seam.** Forcing a real `xdg-open` failure in CI is not reliable. Give
`_dash_open_browser` a boolean escape read from a global — a flag, never a command string, so
no new shell surface is created — that makes it take the failure branch without launching
anything, and drive the cscript through that. The suite already sets `${dash_nobrowser}` to
keep runs from opening browsers, so the convention exists.

### TR-28.11 — One master-JSON assembly  *(item 7)*

**Where.** The three assemblies: `dash.ado:1723` (`_dash_render_immediate`, 5 keys),
`dash.ado:2343` (`_dash_prepare_spec`, 13 keys plus `kpis`), and `_dash_serve_spec` (`:2530`),
which already delegates — it calls `_dash_prepare_spec, … inherit` at `:2578-2580` and so is
*not* a third copy any more. The third copy is the immediate literal.

Key sets, read at HEAD:

| key | immediate (`:1723`) | shared (`:2343`) |
|---|:--:|:--:|
| `layout` | hardcoded `"1 1"` | from the option |
| `theme` | hardcoded `""` | from the option |
| `session_scheme` | ✔ | ✔ |
| `level` | ✔ | ✔ |
| `formats` | ✔ | ✔ |
| `link` `filter` `scheme` `title` `subtitle` `registry` `tabs` `filter_position` | **absent** | ✔ |
| `kpis` (top level) | **absent** | ✔ |

**Mechanism — what to factor, and what not to.** Do **not** route the immediate path through
`_dash_prepare_spec`: that program requires a non-empty `${dash_graph_registry}` and exits 198
otherwise (`dash.ado:2046-2049`), and it builds its graphs JSON from `${dash_json_<gname>}`,
neither of which the immediate path has. Factor only the **assembly tail** — a new
`_dash_master_json` taking the graphs JSON, the KPI JSON and the build-option macros and
returning the string — and call it from both `:1723` and `:2343`. Then the key set is one list
in one place, and the immediate path's remaining differences are deliberate and visible
(`registry` empty, `layout` `1 1`).

**What this buys, and what must be measured rather than assumed.** The renderer reads
`build_options` for the dashboard title and subtitle, `filter`, `filter_position`, `link`,
`tabs`, `registry` and `scheme` — none of which the immediate literal emits. Which of those a
user can actually reach on the immediate route (that is, which are accepted by the immediate
path's syntax and then dropped) is a **measurement this item owes**, not a claim to repeat: run
each through `dash scatter mpg weight, <opt>` and record what arrives. Whatever the answer,
BR-28.11's test — same graph, three paths, compare `sorted(build_options.keys())` — is what
stops the sets diverging again.

---

## Work items

All eight items are reproduced with the tag, `files` and `origin` they were handed over with.
`kind`: `functional` = a user-visible behaviour gap; `deliverable` = a test, cscript, help
sentence or changelog entry the task asked for.

---

### Item 1 — the `scatteri` marker-label LabelSet in the generated server app

> Add the `scatteri` marker-label LabelSet to the generated server app, mirroring
> `map_scatteri`'s `_labels`/`_has_labels` block.

| | |
|---|---|
| **kind** | functional |
| **renderer** | server |
| **effort** | small |
| **Where** | `dash_render.py:14658-14674` (server `scatteri` branch), `:5407-5462` (`map_scatteri`) |
| **Origin** | `S06` — REMAINING.md main body, "17 DONE claims the adversarial pass overturned", row `06-05`: "`scatteri` marker labels missing from the server app" |
| **Epic** | E28.2 |

**Evidence.** `06-05`'s `<done>` was "`scatteri` produces well-formed output with labels
attached to the right points"; the adversarial pass found that true in `DashRenderer` and false
in the emitted app. Confirmed at HEAD: `map_scatteri` builds `_labels` from each pair's optional
third element (`dash_render.py:5409-5413`) and adds a `LabelSet` at `:5455-5464`; the emitted
branch reads `p[0]`/`p[1]` only (`:14661-14663`) and adds no annotation. Three-element pairs do
not raise there, so the labels vanish silently. Property values to mirror, and the
`_SCHEME_CHROME` gap that blocks a faithful mirror, are in TR-28.3.

---

### Item 2 — positional plot-options across an expanded multi-y varlist

> Apply positional plot-options correctly across an expanded multi-y varlist — currently undone
> and silently wrong.

| | |
|---|---|
| **kind** | functional |
| **renderer** | stata |
| **effort** | medium |
| **Where** | `dash.ado` varlist expansion |
| **Origin** | `S06` — REMAINING.md, "Status by section" row 06: "positional plot-options across an expanded varlist" |
| **Epic** | E28.1 |

**Evidence.** The expansion itself landed (`dash.ado:1053-1074`) and is guarded by V2-01…V2-05
in `test/test_varlist_expansion.cscript`. The option half did not: `_opts_json` is built once at
`dash.ado:1220` and interpolated into every expanded spec at `:1239`, so a list-valued option is
handed whole to each series. `twoway` applies such options positionally — `06-02`'s action
clause says so explicitly and requires the ambiguous cases be documented rather than guessed.
The failure is silent because a multi-token colour raises `ValueError` in `translate_mcolor`
(`dash_render.py:1396-1400`) and every call site swallows it. Mechanism, the option
classification, and the short-list rule are in TR-28.1.

---

### Item 3 — the S06 CHANGELOG entry

> Write the S06 CHANGELOG entry. There is no S06 section in `.ultraplan/CHANGELOG.md` at all.

| | |
|---|---|
| **kind** | deliverable |
| **renderer** | n/a |
| **effort** | small |
| **Where** | `.ultraplan/CHANGELOG.md` |
| **Origin** | `S06` — REMAINING.md, "Status by section" row 06: "**no S06 entry in CHANGELOG** ②" |
| **Epic** | E28.2 |

**Evidence.** Confirmed at HEAD: the file's section headings are `S07`, `S08`, `S09`, `S10`,
`S11`, four topical sections, `S14`, `S15`, `S16` — no `S06`. `06-07` required that every
example whose output changed be recorded "with the before and after series count", and S06
changed the series count of every multi-y command in the repository. The required shape, the
seven rows, and the two defects that must be recorded as **still open** rather than fixed are
in TR-28.8.

---

### Item 4 — restore the variable-free exemption on the `dash build` route

> Restore the variable-free exemption on the `dash build` route, which still aborts.

| | |
|---|---|
| **kind** | functional |
| **renderer** | stata |
| **effort** | small |
| **Where** | `dash.ado` |
| **Origin** | `S06` — REMAINING.md, "Status by section" row 06 (the S06 partial set); `06-03` defect 3 |
| **Epic** | E28.1 |

**Evidence.** `06-03` defect 3 reads: "`dash.ado:937-940` aborts when no variables are
identified. `scatteri`, `pci`, `pcscatter` and `function` legitimately have none. Gate the check
on the plot type rather than removing it." The gate was added to `_dash_render_immediate`
(`dash.ado:1655-1671`, with its own comment recording the fix) and not to `_dash_prepare_spec`,
whose abort at `:2237-2241` is what `dash build` and `dash serve` reach. The certification case
written for this defect — V2-07 in `test/test_varlist_expansion.cscript` — drives
`dash scatteri …, saving(…)` and `dash function x^2, saving(…)`, i.e. the immediate route only,
which is why the build route went uncovered. Mechanism in TR-28.2.

---

### Item 5 — server-fixture `__enter__` must not leak a process

> Wrap both server-fixture `__enter__` bodies in try/except, terminating the process before
> re-raising, so a failed startup cannot leak a process. Factor the existing `__exit__` teardown
> into a `_stop()` and call it from both.

| | |
|---|---|
| **kind** | deliverable |
| **renderer** | n/a |
| **effort** | small |
| **Where** | `test/test_server_serves.py:106-125`, `:167-182` |
| **Origin** | `S14` — REMAINING.md main body, "17 DONE claims the adversarial pass overturned", row `14-01`: "both server-fixture `__enter__` paths can leak a process on failure" |
| **Epic** | E28.3 |

**Evidence.** `14-01` asked for a fixture that would "tear the process down reliably even on
failure. An orphaned `bokeh serve` in CI is its own problem." Confirmed at HEAD: both
`__enter__` methods `Popen` and then raise `AssertionError` on the 60-second timeout
(`test/test_server_serves.py:125`, `:184`) without terminating; because `__enter__` raised, the
`with` statement never binds and `__exit__` — the only teardown, at `:127-133` — never runs.
`_Launched` takes that teardown by assignment at `:186`, so one `_stop()` serves both. Exact
refactor in TR-28.9.

---

### Item 6 — an `_rc` check and a path on failure after each browser launch

> Add an `_rc` check and a path-on-failure after each of the six shell browser launches.

| | |
|---|---|
| **kind** | functional |
| **renderer** | stata |
| **effort** | small |
| **Where** | `dash.ado` (six browser-launch sites) |
| **Origin** | `S14` — REMAINING.md, "Status by section" row 14: "no `_rc` check after the six shell browser launches ②"; `14-04` |
| **Epic** | E28.3 |

**Evidence.** All six sites confirmed at HEAD: `dash.ado:1770-1772` (immediate) and
`:2510-2512` (`dash build`), none with an `_rc` check. `14-04` states the consequence — "a
failed `xdg-open` leaves the output unreachable — report the path on failure" — and its TDD
stub list includes "Test: a failed browser launch reports the output path instead of failing
silently", which no test in the repository performs. The `dash build` group prints the path
first (`:2504`); the immediate group prints it only when no browser is attempted
(`:1773-1775`), so that is the route where a failure leaves the user with nothing. Single-helper
refactor, the rc contract, the security constraint and the test seam are in TR-28.10.

---

### Item 7 — fold the third hardcoded `build_options` literal into the shared helper

> Fold the third hardcoded `build_options` literal into the shared helper — 14-03 left it out.

| | |
|---|---|
| **kind** | functional |
| **renderer** | server |
| **effort** | small |
| **Where** | `dash_render.py:_dash_serve_spec / build_options helpers` (as handed over). Confirmed at HEAD in `dash.ado`: the literal is `dash.ado:1723` in `_dash_render_immediate`; the shared assembly is `dash.ado:2343` in `_dash_prepare_spec`; `_dash_serve_spec` (`dash.ado:2530`) already delegates. The plan named the immediate copy at `:974` — stale. |
| **Origin** | `S14` — `14-03`: "Factor the assembly into one helper called by both, plus the immediate-render path at `:974` whose `{"layout":"1 1","theme":"default"}` is the third hardcoded copy." |
| **Epic** | E28.3 |

**Evidence.** `14-03` unified two of the three paths and left the third. Confirmed at HEAD: the
immediate literal carries five `build_options` keys against the shared assembly's thirteen
(table in TR-28.11). One clause of `14-03`'s complaint is already closed — the immediate literal
now says `"theme": ""`, not `"default"`, and carries `session_scheme`, which the renderer's
precedence chain reads at `dash_render.py:7957-7962` — so the remaining substance is structural:
eight keys exist on one route and not the other, with nothing stopping them drifting again, in a
file whose own comment block (`dash.ado:1972-1989`) records what the last such drift cost.
Factor the assembly tail, not `_dash_prepare_spec` itself — TR-28.11 says why.

---

### Item 8 — implement `horizontal`, `sort` and `vertical`

> Implement `horizontal` `sort` `vertical`. All three are declared and serialized and reported
> as ignored. Note `sort` may be a genuine no-op because dash already sorts by x — if so it
> should say that rather than imply the plot is wrong.

| | |
|---|---|
| **kind** | functional |
| **renderer** | both |
| **effort** | medium |
| **Where** | `dash_render.py:map_bar/map_line/map_rbar`, `dash.ado:_dash_pending` |
| **Origin** | `OPT-S06` — REMAINING.md §2, the whole of the `implement-S06` disposition (3 options, 0 honoured, 3 reported ignored), confirmed declared by Appendix A's `05-04` table (3 of 3 declared) |
| **Epic** | E28.2 |

**Evidence.** Declared and serialized at `dash.ado:606`, `:622`, `:628` (pending), `:708-710`
(`sreturn`), `:870` (the JSON key loop) — so the values reach `plot["options"]` and nothing
reads them. `fig.hbar` appears nowhere in `dash_render.py`; the eight bar-drawing sites are
listed in TR-28.4. `sort` is a no-op for the line family (`map_line` sorts at
`dash_render.py:3526`, and the emitted line/connected/tsline branches at `:14100`, `:14266`,
`:14333`, `:14721`) and is **not** a no-op for `area` (`map_area`, `:3614-3630`) or `rarea`
(`map_rarea`, `:4946-4954`), neither of which sorts — TR-28.5. `vertical` names the default
`dash` already draws — TR-28.6. The help currently disposes of all three in one sentence at
`dash.sthlp:1143-1145`, tied to `dash.ado` in both directions by
`test/test_help_conformance.py` — TR-28.7.

---

## Test plan

Two project rules govern this plan. **Rule 8** — every bug fix gets a regression test written
*before* the fix, shown to fail, and shown to pass after. **Rule 4** — every function gets a
unit test, and the application keeps end-to-end coverage. This repository has a documented
history of tests that passed against broken implementations — item 4's defect survived because
V2-07 certified one of the two routes — so every test below carries the mutation that must kill
it. Per the project's certification convention, Stata-side tests are `.cscript` files, and the
suite is run with `$dash_nobrowser` set so no run opens a browser.

### E28.1 — The S06 parser leftovers (items 2, 4)

#### Write these first, and watch them fail

| # | test | file | fails at HEAD because |
|---|---|---|---|
| T1 | `V2-13` — `dash line mpg price weight, lcolor(red blue)` gives two distinct, *named* series colours | `test/test_varlist_expansion.cscript` (beside V2-01's colour census) | **Red.** One `_opts_json` is attached to both specs (`dash.ado:1239`); `translate_mcolor` rejects `red blue` and the call site swallows the error, so both series render in scheme colours. |
| T2 | `test_list_valued_option_is_split_across_expanded_series` | `test/test_varlist_expansion.py` | **Red** for the same reason, asserted on the spec JSON and on the resolved glyph colours rather than on an HTML colour census. |
| T3 | `test_scalar_option_is_copied_to_every_expanded_series` | `test/test_varlist_expansion.py` | Green at HEAD; it pins the half that must **not** change (`bwidth`, `level`, `n`, `base` are not lists). |
| T4 | `V2-14` — `dash scatteri 20 3000 30 4000, name(g1)` then `dash build, saving(…)` returns rc 0 and writes the file; the same for `pci`, `pcscatter`, `function` | `test/test_varlist_expansion.cscript` (beside V2-07) | **Red.** `_dash_prepare_spec` aborts at `dash.ado:2237-2241` with "no variables identified across registered graphs." |
| T5 | `V2-15` — an empty registry still exits 198, and a registry mixing a variable-free graph with a `scatter` builds both | same file | Green at HEAD; it is the guard that stops T4's fix swallowing a real error. |

#### Unit tests (rule 4)

- The new option-splitting helper (whatever it is called): one y-variable and one value; N
  y-variables and N values; N y-variables and one value (recycling rule); N and M where
  `M > N` (surplus ignored or reported — assert the documented choice); an empty value; a
  value containing an embedded space that is **not** a list (`mlabel()` on a single variable).
- The new `_dash_is_varfree` helper (TR-28.2): each of the four types; a spec carrying two
  types; a spec carrying none; a spec whose JSON contains the substring inside a *label* rather
  than as a type (the `strpos` test is textual — prove it does not false-positive on
  `title("scatteri")`).
- `_dash_parse_varpart_3v` / `_4v` unaffected: `rarea`, `rbar`, `pcspike`, `pcarrow` produce the
  same spec they do today (`06-02`'s own required test).

#### Integration / cscript coverage

- `test/test_varlist_expansion.cscript` — V2-13…V2-15 above, in the file's existing style: each
  check wrapped in `capture`, failures tallied, the script exiting non-zero if any failed.
- `test/test_conformance.cscript` — the conformance corpus must still report zero `r(198)`,
  zero dropped series and zero dropped graphs; T4's fix removes one source of `r(198)`.
- `test/test_examples_run.cscript` — every example still runs; any example using a multi-y
  varlist **with a list-valued option** is expected to change and each change must be recorded
  in the S06 CHANGELOG section (item 3).

#### Mutations — each must kill a named test

| id | break this | must kill |
|---|---|---|
| **M1** | Revert the option split: interpolate one `_opts_json` into every expanded spec again. | T1, T2 |
| **M2** | Split *every* option positionally, including the scalar estimation options. | T3 |
| **M3** | Delete the `dash build` variable-free exemption. | T4 |
| **M4** | Make the exemption unconditional — drop the `_varfree` test and always substitute a placeholder variable. | T5 (the empty-registry case must still exit 198) |

### E28.2 — The S06 render leftovers, and the S06 record (items 1, 8, 3)

#### Write these first, and watch them fail

| # | test | file | fails at HEAD because |
|---|---|---|---|
| T6 | a **labelled** `scatteri` case added to `CORPUS` — `values: [[20.0, 3000.0, "A"], [30.0, 4000.0, "B"]]` | `test/test_mode_parity.py` (beside the existing unlabelled `("scatteri", …)` case at `:257-259`) | **Red** on `test_same_annotations`: standalone yields one `LabelSet`, the server yields none. Once `_SCHEME_CHROME` carries `text_font_size`, it also guards the font size, colour and offsets. |
| T7 | `test_server_scatteri_labels_match_the_mapper` | `test/test_server.py` | **Red.** Asserts the built server document's figure carries a `LabelSet` whose `text` is `["A", "B"]`. |
| T8 | `test_horizontal_draws_hbar_or_is_reported` | `test/test_glyphs.py` | **Red.** `fig.hbar` appears nowhere in `dash_render.py`; `horizontal` is on `_dash_pending`, so the disjunction is satisfiable only after the decision in TR-28.4/TR-28.7 is taken and implemented. |
| T9 | `test_sort_is_honoured_or_honestly_reported`, parametrised over `line`, `area`, `rarea`, `bar` | `test/test_glyphs.py` | **Red for `area`/`rarea`**: `map_area` (`:3614-3630`) and `map_rarea` (`:4946-4954`) draw in row order, and `sort` is reported with a reason ("line plots are already sorted") that is not true of those layers. |
| T10 | `test_s06_options_are_honoured_or_reported`, driven from the `implement-S06` slice of `test/fixtures/rejected_options.json`, run against `DashRenderer` **and** `ServerAppBuilder` | `test/test_unsupported_report_is_true.py` | **Red** on whichever of the three this phase honours without updating `_dash_pending`; it is the converse assertion that keeps the note trustworthy as an inventory. |
| T11 | `test_changelog_has_a_section_for_every_completed_section` | `test/test_cscript_hygiene.py` or a new `test/test_changelog_sections.py` | **Red.** `.ultraplan/CHANGELOG.md` has no `## S06` heading. Keep the assertion to sections the audit records as having shipped behaviour changes, so it does not become a nag. |

#### Unit tests (rule 4)

- `map_bar` with and without `horizontal`: glyph type (`VBar` vs `HBar`), the value axis, the
  baseline, and the computed bar width/height — including the string-x fallback at
  `dash_render.py:3695-3699` where x values are not numeric.
- `map_rbar` with `horizontal`: both bounds swap together (`y1var`/`y2var` become `left`/`right`).
- `horizontal` and `vertical` given together: one legible error, in Stata, not a Python
  exception (project rule 16's spirit — validate where the user can see it).
- `map_area` / `map_rarea` with `sort`: the drawn x sequence is monotone; without it, whatever
  the decision in TR-28.5 says, asserted explicitly rather than left to chance.
- `map_line` with `sort`: output is identical with and without the option — the no-op claim,
  proved rather than asserted in prose.
- The new emitted `text_font_size` constant: the built app's `LabelSet` font size equals
  `SchemeParser.text_font_size` for a non-default scheme (`economist` is already used in the
  parity corpus), not a literal `10pt`.

#### Integration / cscript coverage

- `test/test_option_surface.cscript` — `dash bar mpg foreign, horizontal`,
  `dash area mpg weight, sort` and `dash bar mpg foreign, vertical` each return rc 0, and the
  ignoring-unsupported note says exactly what the help says.
- `test/test_help_conformance.py` — must pass after `dash.sthlp:1143-1145` and `_dash_pending`
  move together (BR-28.7).
- `test/test_every_plot_type_draws.py` — `scatteri` with labels still draws its markers; the
  label work must not disturb the glyph.

#### Mutations — each must kill a named test

| id | break this | must kill |
|---|---|---|
| **M5** | Delete the new emitted `LabelSet` block. | T6, T7 |
| **M6** | Emit the `LabelSet` with the `rcapsym` branch's values (`9px`, `#333333`, offsets 5/5). | T6 (`test_same_annotations` compares all five properties) |
| **M7** | Hardcode `text_font_size='10pt'` in the emitted block instead of reading the scheme constant. | The scheme-specific font-size unit test, and T6 under the `economist` corpus entry |
| **M8** | Make `map_bar` ignore `horizontal` again. | T8 |
| **M9** | Take `sort` off `_dash_pending` without honouring it anywhere. | T9, T10 |
| **M10** | Restore `horizontal`/`vertical` to `dash.sthlp`'s unsupported list while leaving them honoured in code. | `test/test_help_conformance.py` |

### E28.3 — The S14 leftovers (items 5, 6, 7)

#### Write these first, and watch them fail

| # | test | file | fails at HEAD because |
|---|---|---|---|
| T12 | `test_a_failed_start_leaves_no_process` — construct `_Served` against an app that never answers, shorten the deadline, assert `__enter__` raises **and** `proc.poll() is not None` | `test/test_server_serves.py` | **Red.** The timeout path at `:125` raises without touching the process; `__exit__` never runs because `__enter__` never returned. |
| T13 | the same for `_Launched` | `test/test_server_serves.py` | **Red** at `:184` for the same reason. |
| T14 | `test_a_failed_browser_launch_reports_the_path` — drive the failure seam on the immediate route and on `dash build`; assert the path is displayed and the command's rc is 0 | `test/test_render_log_clean.cscript` or a new `test/test_browser_launch.cscript` | **Red.** No `_rc` check exists at any of the six sites, and the immediate route displays the path only when no launch is attempted. |
| T15 | `test_build_options_keys_are_identical_across_paths` — one graph through immediate render, `dash build` and `dash serve`; compare `sorted(build_options.keys())` | `test/test_server_build_options.py` | **Red.** Five keys against thirteen (`dash.ado:1723` vs `:2343`). |

#### Unit tests (rule 4)

- `_stop()` — called twice is harmless (idempotent); called when `self.proc is None` is
  harmless; the `wait(timeout=15)` → `kill()` escalation still happens.
- `_dash_open_browser` — each of the three OS branches selects the expected command (assert on
  the branch taken, not by running a browser); the failure branch displays the path; the
  success branch displays nothing; `${dash_nobrowser}` and `nobrowser` prevent the call from
  being made at all (that gate stays at the call sites, `dash.ado:1760` and `:2509`).
- `_dash_master_json` — the key set is the documented list; a value containing a double quote
  survives (`_dash_json_str` escaping, the failure this file has been bitten by twice per its
  own comment at `dash.ado:2028-2032`); an empty optional value serialises as `""` and not as
  the literal macro name.

#### Integration / cscript coverage

- `test/test_serve_options.cscript` — still passes; it calls `_dash_serve_spec` directly and
  reads the master JSON it writes, so it is the regression guard on TR-28.11's refactor.
- `test/test_e2e_single.cscript`, `test/test_e2e_multi.cscript` — both routes still build with
  `$dash_nobrowser` set.
- `test/test_server_serves.py` — the full 17-test file still passes; the fixture change must be
  invisible to the tests that use it.
- `test/test_e2e_serve.cscript` — unchanged; an honest skip when `bokeh` is unavailable is a
  skip, not a pass.

#### Mutations — each must kill a named test

| id | break this | must kill |
|---|---|---|
| **M11** | Remove `self._stop()` from `_Served.__enter__`'s failure path. | T12 |
| **M12** | Remove it from `_Launched.__enter__`'s failure path only. | T13 (proves the two are tested separately, which is what the refutation was about) |
| **M13** | Drop the `capture` from the shell launch so `_rc` is never set. | T14 |
| **M14** | Make the failure branch display the rc but not the path. | T14 |
| **M15** | Give `_dash_master_json` a caller-specific key subset again. | T15 |

---

## Definition of done

**E28.1 — the S06 parser leftovers**

- [ ] `dash line y1 y2 x, lcolor(red blue)` renders two distinctly, correctly coloured series;
      the assertion is on the resolved colours, not on the absence of an error.
- [ ] The recycling rule for a short list, and the choice made for options that cannot be split
      (`mlabel()`, `legend(label(...))`), are implemented **and** stated in `dash.sthlp`.
- [ ] Scalar estimation and geometry options are still copied whole to every expanded series
      (M2 demonstrated).
- [ ] A single-y command's output is unchanged (V2-05 green).
- [ ] The range and paired-coordinate families are unchanged, with a test asserting it.
- [ ] `scatteri`, `pci`, `pcscatter` and `function` each build through `name()` + `dash build`
      with rc 0; V2-14 exists and M3 kills it.
- [ ] An empty registry still exits 198 with its own message; a mixed registry builds both
      graphs (M4 demonstrated).
- [ ] The four variable-free type names live in one place, used by both routes.

**E28.2 — the S06 render leftovers, and the S06 record**

- [ ] A labelled `scatteri` spec produces a `LabelSet` in server mode whose `text`,
      `text_font_size`, `text_color`, `x_offset` and `y_offset` match standalone's
      (`text` from the third element, offsets 4/4, the scheme's `gsize text`).
- [ ] The emitted app carries the scheme's text font size as a constant; no literal size is
      hardcoded in the new block (M7 demonstrated).
- [ ] An unlabelled `scatteri` adds no annotation, in both renderers.
- [ ] `horizontal` draws horizontal bars in both renderers, **or** is named in the note with a
      reason that is true; `horizontal` with `vertical` is a legible Stata error.
- [ ] `sort` is dispositioned **per layer family**, with the line family's no-op stated as a
      no-op and `area`/`rarea` either sorted or reported.
- [ ] `vertical` is accepted as a no-op and no longer reported as ignored.
- [ ] For each of the three, `dash.ado`'s `_dash_pending`, `dash.sthlp:1143-1145` and
      `test/fixtures/rejected_options.json` moved in the same commit, and
      `test/test_help_conformance.py` passes.
- [ ] `.ultraplan/CHANGELOG.md` has an `## S06` section in the file's established shape, with a
      before value, an after value and evidence for each of the seven defects.
- [ ] That section records per-plot `if` on computed layers and positional plot-options as
      **still open**, naming the phase that owns each, and claims nothing this phase has not
      shipped (project rule 2).

**E28.3 — the S14 leftovers**

- [ ] `_Served` and `_Launched` share one `_stop()`; both `__enter__` failure paths call it
      before re-raising; both leak tests pass and M11/M12 kill them individually.
- [ ] All six browser launches go through one helper that checks `_rc`, reports the rc and the
      output path on failure, and leaves the command's own return code unchanged.
- [ ] The immediate-render route displays the output path on a failed launch.
- [ ] No new shell interpolation surface: the path validator at `dash.ado:150-215` still runs
      first and every argument stays quoted.
- [ ] The happy path is no noisier than today (`test/test_render_log_clean.cscript` green).
- [ ] One `build_options` assembly serves the immediate, `dash build` and `dash serve` paths;
      the key sets are identical by construction and a test asserts it.
- [ ] The measurement item 7 owes is recorded: which `build_options`-backed options a user can
      supply on the immediate route today, and what each now does.

**Cross-cutting**

- [ ] Every new test has a named mutation that kills it, demonstrated and recorded in the
      commit message (rule 8; the repository's history of vacuous tests is why).
- [ ] Full pytest and the full certification suite pass with honest skip accounting — at the
      time of the audit, 3,498 passed / 37 skipped and 25/25 cscripts; a skip is not a pass.
- [ ] The conformance corpus reports zero `r(198)`, zero dropped series and zero dropped
      graphs; the parity corpus is green, including the new labelled-`scatteri` case.
- [ ] `$dash_nobrowser` is set for every suite run, and no test opens a browser.
- [ ] Work committed to `feature/batch4-interactive-layer`, never to `main`, in single-issue
      commits; the merge command reported, not run (project rules 5–7).

---

## Risks and sequencing notes

**1. Items 1 and 8's server halves are cheaper after Phases 05–08, and are wasted work if done
twice.** Appendix B's `15-03` list names the exact branches both items touch:

> **[func · server · L]** Delegate the remaining 37 main-loop ptype branches
> to `_DASH_MAPPER`. The chain at dash_render.py:14031 (`ptype =
> plot.get('type','')`) through ~14850 still hand-writes drawing code for:
> area, bar, connected, dot, dropline, fpfit, fpfitci, function, histogram,
> kdensity, lfit, lfitci, line, lowess, lpoly, lpolyci, mband, mspline,
> pcarrow, pcbarrow, pci, pcscatter, pcspike, qfit, qfitci, rarea, rbar, rcap,
> rcapsym, rconnected, rline, rscatter, rspike, scatteri, spike, tsline,
> tsrline. Each has a `GlyphMapper.map_<type>` already emitted into the app
> and unused.

When that delegation lands, the emitted `scatteri` branch is **deleted** and replaced by a call
into `map_scatteri` — which already has the LabelSet. So item 1's *code* becomes free and its
durable deliverable is the parity-corpus case (T6) that proves it. The same holds for item 8's
server half: implement `horizontal` in `map_bar`/`map_rbar` and Phase 05 carries it across for
nothing. Recommended order if both phases are in flight: write T6, T7 and T8 now, implement in
the mappers now, and add the interim two-line server mirror only if Phase 28 ships first. If it
does, flag both blocks in the Phase 05 handover so the delegation does not silently drop them.

**2. Item 8's `_dash_pending` edits are fragile until Phase 18.** REMAINING.md Appendix C,
`05-04`, measured what re-running the option-surface generator does to hand-written `dash.ado`:

> re-running scripts/regen_option_surface.py also deletes: (a) the whole level()
> validation block in _dash_parse_plot_opts (dash.ado:549-561) […]; (b) the ENTIRE
> plot-level `local _dash_pending` accumulation (dash.ado:593-641) and `local
> _dash_unknown` (:642) plus its `sreturn local _pending`/`_unknown` (:770-771) —
> after a regen the whole file contains zero `sreturn local _pending`, so 05-03's
> reporter is dead at BOTH levels, not just graph level

Lines `:606`, `:622` and `:628` — the three this item edits — are inside that block. Removing an
option from `_dash_pending` before the generator is de-fanged means the removal is reverted the
next time anyone regenerates, silently. Mitigation, in order of preference: run item 8 after
Phase 18; or, if it runs first, land T10 (the converse test) in the same commit, so a
regeneration that restores the stale entries fails a test rather than shipping a note that names
options which now work.

**3. `scatteri` draws nothing under `by()` in server mode, and that is not this phase's bug.**
Appendix B lists `scatteri` among the 20 types that fall off the end of the emitted facet
`elif` chains. A parity case written with `by()` would go red for Phase 07's reason. Keep T6 and
T7 unfaceted, and if a faceted labelled-`scatteri` assertion is wanted, mark it `xfail` against
that named item rather than omitting it.

**4. Item 2 changes the spec shape for a common command, and everything downstream indexes on
plot identity.** Section 06's own risk line is `[red]` for exactly this reason: "every
downstream consumer (linking, filters, `by()`, tabs, the Bootstrap grid) indexes on plot
identity." The expansion itself already shipped, so the shape is not changing again — but the
*options* attached to each expanded plot are, and `link()`, KPI update targets and the legend
all read plot options. `06-07`'s sweep is the right discipline: regenerate every dashboard in
`examples/`, diff against the pre-change versions, and expect a change only where a multi-y
command carries a list-valued option. Any other change is a bug in this item.

**5. Item 4 widens what `dash build` accepts, which widens what the serialiser is handed.**
The exemption substitutes a placeholder variable so `jsonio` has something to serialise. Two
edges to test rather than assume: a dataset with no variables at all (where `unab` yields
nothing and the existing 198 must still fire), and a very wide first variable (the placeholder
is serialised in full and then never read — if that is a size concern on a large dataset, pick
the narrowest available variable rather than `word 1`, and say so in a comment).

**6. Item 6 adds a code path that only runs when something is already broken.** A failure branch
that is never exercised is a branch that rots. The test seam in TR-28.10 is therefore part of
the item, not an optional extra — and it must be a **boolean** flag, never a configurable
command string, or item 6 would reopen the shell-injection surface `dash.ado:150-215` exists to
close (project rules 1 and 16).

**7. Item 7's refactor touches the only code path `dash scatter mpg weight` takes.** The
immediate route is the first thing any new user runs. Its literal is five keys and the shared
assembly is thirteen; changing the immediate path to emit all thirteen changes what the renderer
sees on that route (`registry`, `filter`, `tabs`, `filter_position` arriving as empty strings
where they were previously absent). `_build_opts.get(key, "")` handles both, but the renderer
has grown behaviour keyed on absence before — the scheme precedence chain at
`dash_render.py:7957-7962` reads `.get("scheme", "").strip() or .get("theme", "").strip() or …`,
which treats absent and empty identically, but not every consumer has been checked. Run
`test/test_immediate_scheme.py`, `test/test_server_build_options.py` and the full parity corpus
before and after, and treat any diff as a finding.

**8. Two items are paperwork, and paperwork is where honesty is tested.** Item 3 asks for a
CHANGELOG section covering work that is partly still open. The temptation is to write the seven
defects as closed because six of them are. Rule 2 binds here more than anywhere else in this
phase: the section records what shipped, and names item 2 and Phases 01–02 for what did not.
