# Section 06: Varlist and plot-spec correctness

## Overview
`dash` loses data. Not by rounding or by rendering — it drops whole series and whole
qualifiers on the floor before Python ever sees them.

`twoway scatter mpg price weight` draws **two** series. `dash` draws **one**:
`_dash_parse_varpart_std` (`dash.ado:665-670`) takes `yvar = word 1` and `xvar = last word`
and discards everything between. Verified by colour census of the generated HTML — one series
colour for the three-variable form, two for the explicitly overlaid form. No error, no
warning. `dash line mpg price weight length` drops two of four variables.

Around that sit six more defects of the same family: commands that cannot run at all, or that
run and produce something other than what was asked.

## User story
> As a Stata user, `dash line y1 y2 y3 x` gives me three lines, `dash function y=x^2` runs,
> and a per-plot `if` applies to that plot.

## Business requirements
- BR-06.1 Every y-variable in a varlist becomes a series, as in `twoway`.
- BR-06.2 Every documented `dash`/`twoway` invocation form runs.
- BR-06.3 A qualifier applies where it was written.

## Technical requirements
- TR-06.1 `_dash_parse_varpart_std` expands `y1 y2 ... x` into one plot spec per y-variable,
  each taking the next scheme style index — the cycle already works for explicitly overlaid
  plots (measured: p1 navy `#1a476f`, p2 maroon `#90353b`), so expansion feeds an existing
  mechanism.
- TR-06.2 `dash.ado:455` gains `equalok` so the `y=` stripper at `:630` becomes reachable.
- TR-06.3 Variable-free plots reach the renderer.
- TR-06.4 `tsline`/`tsrline` read `_dta[_TStvar]` when no x-variable is given.
- TR-06.5 `name(id, replace)` parses before it validates.
- TR-06.6 `saving()` accepts `twoway`'s forms.
- TR-06.7 Per-plot `if_expr` is carried and applied per plot.
- TR-06.8 `scatteri` pairs coordinates and labels correctly.

## Risk: [red] — TR-06.1 changes the shape of the spec JSON for a very common input, and every downstream consumer (linking, filters, `by()`, tabs, the Bootstrap grid) indexes on plot identity.

## Dependencies
- Depends on: S05
- Blocks: S07
- Parallel batch: 2

## The seven defects

| # | Defect | Citation | Observed |
|---|---|---|---|
| 1 | `y1 y2 ... x` renders one series | `dash.ado:665-670` | **[measured]** 1 series vs `twoway`'s 2 |
| 2 | `dash function y=x^2` | `:455` lacks `equalok`; `:630` unreachable | r(101) `=exp not allowed` |
| 3 | `dash scatteri 20 3000 30 4000, saving(x.html)`, `pci`, `function` standalone | `:937-940` | r(198) "no variables identified" |
| 4 | `dash tsline mpg` with no x — `_dta[_TStvar]` never read | `xvar:""` → `KeyError: ''` | r(7102) |
| 5 | `name(g1, replace)` — validated at `:857` before the replace parse at `:864-870`; the error at `:880-883` tells the user to type what cannot work | `:857-883` | r(198), self-contradicting |
| 6 | `saving(myfig)`, `saving(myfig.gph)`, `saving(f.html, replace)` | validated at `:921` before the `.html` append at `:929`; `:158-161` | r(198) ×3 |
| 7 | `scatteri 20 3000 "A" 30 4000 "B"` → `[[20,3000],["A",30],[4000,"B"]]` | `:710-727` pairs blindly, checking only count parity at `:714-717` | malformed |

Plus, in the same family: **per-plot `if` is broken in both directions** — only the first
layer's `if_expr` is promoted to graph level (`:828-835`) and then applied to every layer,
and the renderer never reads a per-plot `if_expr` at all (`dash_render.py:5281`).

## TDD test stubs
- Test: `dash scatter mpg price weight` produces two plot specs, `mpg`-vs-`weight` and
  `price`-vs-`weight`.
- Test: the two specs take style indices 0 and 1, so the rendered HTML contains two distinct
  series colours.
- Test: `dash line a b c d x` produces four specs.
- Test: a single-y command is byte-identical to today (no regression).
- Test: `dash function y=x^2` runs.
- Test: `dash scatteri 20 3000 30 4000, saving(...)` runs.
- Test: `dash tsline close` on a `tsset` dataset uses the time variable as x.
- Test: `dash tsline close` on an un-`tsset` dataset produces a clear error, not r(7102).
- Test: `name(g1, replace)` replaces an existing registration.
- Test: `saving(myfig)`, `saving(myfig.gph)` and `saving(f.html, replace)` all work.
- Test: `scatteri 20 3000 "A" 30 4000 "B"` pairs `(20,3000)` with `"A"`.
- Test: `(scatter y x) (scatter y x if foreign)` applies the qualifier to the second plot only.

## Tasks

<task type="auto" id="06-01">
  <name>Write the failing varlist-expansion tests</name>
  <files>test/test_varlist_expansion.cscript, test/test_varlist_expansion.py</files>
  <action>
    Start with the measurement that established the defect: build `dash scatter mpg price
    weight` and count distinct series colours in the generated HTML. One today, two required.
    Encode that as the headline test, because it asserts what the user sees rather than an
    internal representation.

    Add the structural tests on the serialized spec: plot-spec count, and the y/x assignment
    of each.

    Add the regression guard: a single-y command's generated HTML must be unchanged apart
    from Bokeh's per-run ids.

    Run and confirm the colour-census test fails with one colour.
  </action>
  <verify>The colour-census test reports 1 where 2 is required; single-y output is unchanged.</verify>
  <done>The measured defect is encoded as a failing test.</done>
</task>

<task type="auto" id="06-02">
  <name>Expand multi-y varlists into one plot spec per y-variable</name>
  <files>dash.ado</files>
  <action>
    In `_dash_parse_varpart_std` (`dash.ado:405`, consumed at `:665-670`), stop taking word 1
    and the last word. Take the last word as x, and emit one plot spec per remaining word,
    each carrying the same options.

    Assign each expanded spec the next style index so the scheme colour cycle applies, the way
    it already does for explicitly overlaid specs.

    Decide and document what happens to options that name a single thing — `mlabel()`,
    `legend(label(...))` — when one written plot becomes N. `twoway` applies plot-level
    options positionally across the expansion; match that, and where the semantics are
    genuinely ambiguous, state the choice in the help rather than guessing silently.

    Check the range and paired-coordinate families are unaffected: they use
    `_dash_parse_varpart_3v` and `_4v` and have fixed arity. Add a test asserting so.
  </action>
  <verify>All 06-01 tests pass; the range and pc families are unchanged.</verify>
  <done>Every y-variable becomes a series, styled by the scheme cycle.</done>
</task>

<task type="auto" id="06-03">
  <name>Fix the four commands that cannot run</name>
  <files>dash.ado</files>
  <action>
    Defect 2: add `equalok` to the `syntax` at `dash.ado:455` so `y=x^2` parses and the
    stripper at `:630` is reached. Note separately for S07 that `x^2` is Python `BitXor` and
    silently yields an empty line — `**` is required. S07 owns translating Stata's `^` to
    Python's `**` in `map_function`.

    Defect 3: `dash.ado:937-940` aborts when no variables are identified. `scatteri`, `pci`,
    `pcscatter` and `function` legitimately have none. Gate the check on the plot type rather
    than removing it — an ordinary `scatter` with no variables is still an error.

    Defect 4: when `tsline`/`tsrline` is given no x-variable, read `_dta[_TStvar]`. If the
    dataset is not `tsset`, fail with a message naming `tsset`, not a `KeyError` surfacing as
    r(7102).

    Defect 5: in `_dash_register_graph`, parse the `, replace` suffix **before** validating
    the name (`:857` currently runs before `:864-870`). The error message at `:880-883`
    becomes accurate once the syntax it recommends works.
  </action>
  <verify>All four commands run; the un-`tsset` case gives a clear error naming `tsset`.</verify>
  <done>Four previously impossible invocations work, and the one genuine error is legible.</done>
</task>

<task type="auto" id="06-04">
  <name>Accept twoway's saving() forms</name>
  <files>dash.ado</files>
  <action>
    `saving(myfig)` is the normal `twoway` form and must work — append `.html`. The ordering
    bug is that validation at `:921` runs before the extension is appended at `:929`; swap
    them.

    `saving(myfig.gph)` is a request for a Stata graph file, which `dash` cannot produce.
    Per the accept-and-report decision, accept it, write `myfig.html`, and report the
    substitution by name.

    `saving(f.html, replace)` is `twoway`'s sub-option form and must be equivalent to the
    `replace` option.

    While in the validator (`:150-178`): it rejects `(` and `)`, which breaks every path under
    `C:\Program Files (x86)\`. Narrow the character rejection to what actually poses a shell
    risk, keeping the existing protection against `..`, and add a test with a parenthesised
    path. Note for S16 that server-mode `saving()` bypasses this validator entirely
    (`:1198-1207`) — that is a security item, not a parsing one.
  </action>
  <verify>All four saving() forms work; a parenthesised path is accepted; traversal is still blocked.</verify>
  <done>`saving()` accepts what `twoway` accepts, and path validation no longer rejects ordinary Windows paths.</done>
</task>

<task type="auto" id="06-05">
  <name>Fix scatteri coordinate/label pairing</name>
  <files>dash.ado</files>
  <action>
    `dash.ado:710-727` pairs tokens blindly, checking only that the count is even
    (`:714-717`). With labels present, `scatteri 20 3000 "A" 30 4000 "B"` serializes as
    `[[20,3000],["A",30],[4000,"B"]]`.

    Parse properly: consume numeric pairs, and after each pair optionally consume a quoted
    string as that point's label. Preserve the existing token-parity error for a genuinely
    malformed list, and make its message name what was expected.

    `twoway scatteri` also accepts per-point placement sub-options. If they are in scope of
    S05's accept-and-report set, confirm they are reported rather than silently dropped.
  </action>
  <verify>Labelled and unlabelled `scatteri` both serialize correctly; malformed input still errors clearly.</verify>
  <done>`scatteri` produces well-formed output with labels attached to the right points.</done>
</task>

<task type="auto" id="06-06">
  <name>Carry and apply per-plot if/in qualifiers</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    Two halves.

    Stata side: `dash.ado:828-835` promotes only the **first** layer's `if_expr` to graph
    level and then applies it to all layers. Keep per-plot qualifiers on their plots. A
    command-level qualifier still applies to every plot.

    Python side: the renderer never reads a per-plot `if_expr` (`dash_render.py:5281` reads
    only the graph-level one). Apply the per-plot expression when building that plot's glyph.

    Interaction to get right, and to test explicitly: a linked graph keeps its qualifier via a
    `CDSView` + `BooleanFilter` rather than by filtering the source, so brushing still
    propagates (commit `963e3d6`). Per-plot qualifiers must use the same mechanism, not a
    pre-filtered source, or linking breaks.

    Note for S09, do not fix here: `if` expressions using Stata functions (`!missing()`,
    `inlist()`, `< .`) fail the AST whitelist at `:4318-4353`, warn, and render unfiltered.
  </action>
  <verify>`(scatter y x) (scatter y x if foreign)` filters only the second plot; linking still propagates through a qualified plot.</verify>
  <done>A qualifier applies exactly where it was written, in both linked and unlinked graphs.</done>
</task>

<task type="auto" id="06-07">
  <name>Regression sweep and commit</name>
  <files>dash.ado, dash_render.py, test/, .ultraplan/CHANGELOG.md</files>
  <action>
    The multi-y expansion changes the spec shape for a common input. Sweep every downstream
    consumer that indexes on plot identity and confirm each still behaves: linking, filters,
    `by()` faceting, `tabs()`, the Bootstrap grid, KPI update targets, and the legend.

    Regenerate every dashboard in `examples/` and diff against the pre-section versions. Any
    example using a multi-y varlist is **expected** to change — record each in
    `.ultraplan/CHANGELOG.md` with the before and after series count. An example that changes
    for any other reason is a bug in this section.

    Run the full pytest suite, the certification suite and the S05 conformance corpus against
    the S01 baseline. Commit as a small number of single-issue commits, one per defect.
  </action>
  <verify>Only multi-y examples change, each recorded; all suites green against baseline.</verify>
  <done>No command silently loses a series, a qualifier or a coordinate label.</done>
</task>
