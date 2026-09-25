# Section 04: Abbreviations via Stata's own `syntax`

## Overview
`dash.ado` declares every option in **lowercase**, which tells Stata's `syntax` to permit no
abbreviation at all. Abbreviation is then simulated by a fixed exact-match table in Mata
(`dash_parse.mata:179-253`) that accepts exactly one short form per option and rejects every
other prefix.

Three consequences, all measured:

1. **About 25 standard `twoway` abbreviations hard-fail** with `r(198)`: `mlab` `msym` `msy`
   `xlab` `ylab` `xtit` `ytit` `lcol` `lwid` `lpat` `mcol` `msiz` `lege` `subt` `capt` `xli`
   `yli` `tit` `aspe` `conn` `drop` `scat` and more. Confirmed by execution: `dash scatter
   mpg weight, mlab(make)` → `r(198)`.
2. **Five are mis-mapped to a different option**, which is worse than failing because it is
   silent: `mlc`→`mlabcolor` (Stata: `mlcolor`, the marker outline), `mlw`→`mlabwidth`
   (Stata: `mlwidth`, which `dash` does not even declare), plus `mls`, `mlp`, `mlg`.
3. **`dash.sthlp` documents five spellings that do not work**: `mlac` (537), `mlas` (538),
   `mlap` (540), `mlag` (543), and `xlab` (639) — the last directly contradicting `xla` at
   line 637. KPI `nam()` (61) and `upd()` (66) likewise fail.

The fix is the one StataCorp commands use: capitalise the minimum abbreviation in the
`syntax` declaration and let Stata do the work. This resolves all three classes at once and
deletes roughly 80 lines of Mata.

No test covers any of this today.

## User story
> As a Stata user, the abbreviations I have typed for twenty years work, and no abbreviation
> silently means a different option than the one I meant.

## Business requirements
- BR-04.1 Every abbreviation Stata's own `twoway` accepts is accepted by `dash`.
- BR-04.2 No abbreviation resolves to a different option than it does in `twoway`.
- BR-04.3 Plot-type abbreviations follow the same rule.

## Technical requirements
- TR-04.1 Capitalise minimum abbreviations in `_dash_parse_graph_opts` (`dash.ado:230-246`),
  `_dash_parse_plot_opts` (`:293-326`), `dash kpi` (`:1060-1071`) and `dash build`
  (`:1174-1185`), matching Stata's documented minimums exactly.
- TR-04.2 Delete `_expand_optkey` and its caller `_dash_expand_opts_str`
  (`dash_parse.mata:174-388`) once `syntax` covers the same ground.
- TR-04.3 Widen `_expand_plottype_str` (`dash_parse.mata:126-167`) to accept every prefix
  Stata accepts, or replace it with the same capitalisation approach.
- TR-04.4 `mlcolor()` and `mlwidth()` become real, distinct options (their implementation is
  S05/S09; this section only stops them being aliases of the `mlab*` family).

## Risk: [yellow] — mechanical, but it touches the parse path every single command goes through, and a wrong minimum abbreviation creates a new ambiguity error.

## Dependencies
- Depends on: S01
- Blocks: S05
- Parallel batch: 2

## TDD test stubs
- Test: each of the ~25 failing abbreviations is accepted and maps to the correct full option.
- Test: `mlc` maps to `mlcolor`, not `mlabcolor`; `mlw` maps to `mlwidth`, not `mlabwidth`.
- Test: the five spellings `dash.sthlp` documents (`mlac`, `mlas`, `mlap`, `mlag`, `xlab`)
  all work.
- Test: KPI `nam()` and `upd()` work.
- Test: every option's minimum abbreviation matches Stata's documented minimum for the same
  option name — a table-driven test over the whole option set.
- Test: plot-type abbreviations `scat`, `conn`, `lin`, `kdens` are accepted.
- Test: an ambiguous prefix produces Stata's own ambiguity error, not a wrong mapping.
- Test: every previously-working full option name and short form still works (regression).

## Tasks

<task type="auto" id="04-01">
  <name>Build the abbreviation truth table from Stata</name>
  <files>test/fixtures/abbrev_truth.json, scripts/extract_abbrev_truth.do</files>
  <action>
    For every option `dash` declares, determine the minimum abbreviation `twoway` itself
    accepts. Derive it from Stata — probe each prefix length against a real `twoway` command
    and record the shortest that is accepted — rather than from the help file or from memory.

    Record the result as a fixture: option name, minimum abbreviation, and the probe that
    established it.

    Include the plot types, which have the same problem.

    This fixture is the specification for the whole section, and the test in 04-02 is driven
    from it.
  </action>
  <verify>The fixture covers every option in the four `syntax` blocks, with a traceable probe per entry.</verify>
  <done>Stata-derived ground truth exists for every abbreviation.</done>
</task>

<task type="auto" id="04-02">
  <name>Write the failing abbreviation tests</name>
  <files>test/test_abbreviations.cscript, test/test_abbreviations.py</files>
  <action>
    Write a certification script driven by `abbrev_truth.json`: for each option, issue a
    `dash` command using the minimum abbreviation and assert `_rc == 0`, then assert the
    resulting registry JSON contains the **full** option name with the value supplied.

    The second assertion is the one that catches the mis-mappings. `mlc(navy)` must appear as
    `mlcolor`, not `mlabcolor`. A test that only checks `_rc` would pass today for `mlc` and
    miss the silent bug entirely.

    Add the ambiguity test: a prefix short enough to be ambiguous must produce Stata's own
    ambiguity error.

    Run. Expect roughly 25 rc failures and 5 wrong-mapping failures. Read them and confirm
    the counts match the audit.
  </action>
  <verify>The failures match the audited set in both count and identity.</verify>
  <done>A complete failing test exists for every abbreviation defect.</done>
</task>

<task type="auto" id="04-03">
  <name>Capitalise the minimum abbreviations in all four syntax blocks</name>
  <files>dash.ado</files>
  <action>
    Rewrite the option declarations in `_dash_parse_graph_opts`, `_dash_parse_plot_opts`,
    `dash kpi` and `dash build` so the minimum abbreviation is capitalised, using
    `abbrev_truth.json` as the specification.

    Two cases need care because they are currently aliases and must become distinct:
    `mlcolor()` (marker outline colour) and `mlwidth()` (marker outline width). `mlwidth` is
    not declared at all today; declare it. Their *implementation* belongs to S09 — here they
    only need to parse to the right key and be serialized.

    Remove the header comment at `dash.ado:228-229` that explains why the names are lowercase;
    it is about to be untrue.

    Run the tests after this task alone, before touching Mata. Most should now pass, which
    isolates any remaining failure to the Mata layer.
  </action>
  <verify>The rc failures from 04-02 clear; the mapping assertions for `mlc`/`mlw` now pass.</verify>
  <done>Stata's own abbreviation covers the whole option surface.</done>
</task>

<task type="auto" id="04-04">
  <name>Delete the Mata abbreviation table</name>
  <files>dash_parse.mata, dash.ado</files>
  <action>
    With `syntax` handling abbreviation, `_expand_optkey` and `_dash_expand_opts_str`
    (`dash_parse.mata:174-388`) are dead weight — and actively harmful, because they rewrite
    keys before `syntax` sees them and are the source of the five mis-mappings.

    Remove them and their call sites. Keep the segment splitting and the filter pre-extractor
    (`_dash_extract_filters`, `:884-975`), which do necessary work `syntax` cannot do.

    Widen or replace `_expand_plottype_str` (`:126-167`) so plot-type prefixes behave like
    Stata's: `scat`, `conn`, `lin`, `kdens` and every other valid prefix must work.

    Re-run the whole suite. Anything that breaks here was depending on a mis-mapping, which
    makes it a bug the tests were encoding — fix the code, and record it in the CHANGELOG.
  </action>
  <verify>All abbreviation tests pass; full pytest and certification suites green against the S01 baseline.</verify>
  <done>The abbreviation table is gone and Stata's own mechanism does the work.</done>
</task>

<task type="auto" id="04-05">
  <name>Correct the help's abbreviation markup and commit</name>
  <files>dash.sthlp</files>
  <action>
    The help's `{cmdab:}` markup must now match the capitalisation in the `syntax`
    declarations. Fix the five documented-but-broken spellings (`mlac` 537, `mlas` 538,
    `mlap` 540, `mlag` 543) and the `xlab`/`xla` contradiction between lines 637 and 639.

    Add a conformance test that parses `{cmdab:...}` markup out of `dash.sthlp` and asserts
    each matches the corresponding `syntax` declaration. This makes the help mechanically
    unable to drift from the code again — which matters, because the audit found 17
    documented-but-not-accepted rows across the file.

    Commit, e.g. "Use Stata syntax abbreviation and remove the Mata option-key table".
  </action>
  <verify>The help-conformance test passes; full suite green.</verify>
  <done>Code, help and tests agree on every abbreviation, enforced mechanically.</done>
</task>
