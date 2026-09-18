# Section 03: Scheme translation — author the translated `.scheme` files

## Overview
**Decision taken:** `dash` keeps its own `schemes/` directory of *translated* schemes rather
than parsing Stata's native scheme grammar. `scheme()` is restricted to the translated set.
This section authors the files; S11 makes the renderer consume them.

The gap being closed is large. `dash` ships five translations of roughly 100 lines each and
can read **33 of the 2,048 distinct keys** in Stata's real 2,588-line `scheme-s2color.scheme`
— 1.6%, of which it acts on about 1.1%. Worse, **75 of `dash`'s own 108 keys do not exist in
real Stata schemes**: `dash` invented `color p1line`, `symbol p1` and `linepattern p1line`
where Stata writes `markerstyle p1 p1` and `linestyle p1 p1`.

And the set is missing the ones people use. `c(scheme)` on this machine is **`stcolor`** —
the default since Stata 18 — which `dash` does not have. Handed the real `scheme-stcolor.scheme`
it renders **every series black**, because `color p1 stc1` fails `translate_mcolor` and
`_color()` (`:863`) swallows the failure and returns its `"#000000"` default (`:934`).

## User story
> As a Stata user who has `set scheme stcolor` — or never changed it, which amounts to the
> same thing since Stata 18 — my `dash` dashboard looks like my other graphs, without my
> passing any option.

## Business requirements
- BR-03.1 The translated set covers the StataCorp schemes users actually have set.
- BR-03.2 A translation faithfully reproduces the Stata aesthetic — colours, marker symbols,
  line patterns and widths, text sizes, background and region treatment, legend placement —
  not merely the colour cycle.
- BR-03.3 A scheme outside the translated set is reported clearly, never silently substituted.

## Technical requirements
- TR-03.1 Translated set (14): the Stata 18+ family **stcolor, stcolor_alt, stgcolor,
  stmono1, stmono2, stsj**; the legacy defaults **s2color, s2mono, s2gcolor, s1color,
  s1mono, s1rcolor**; and **economist, sj**. Nine are new; five exist and are deepened.
  Record the selection criterion in the file header so the set can be revisited.
- TR-03.2 Each translated file carries every property `dash` can render, in `dash`'s own
  documented key vocabulary, with the source Stata scheme and version named in a header
  comment.
- TR-03.3 Property coverage per file must include, at minimum: the `p1`-`p15` cycle for
  colour, **marker symbol, marker size, line pattern and line width**; background, plot
  region and grid colours; foreground and axis-line colours; title, subtitle, axis-title,
  tick-label, note and caption text sizes and colours; legend background, border and
  position; fill/bar/area alpha; and **graph size** (`graphsize x`, `graphsize y`), which is
  what S10 uses for figure geometry.
- TR-03.4 A fidelity harness compares each translation against the real Stata scheme file and
  reports coverage, so the claim "faithfully reproduces" is measured rather than asserted.

## Risk: [yellow] — no difficult code, but 14 files of detail work where a wrong hex value is invisible until someone looks at a chart.

## Dependencies
- Depends on: none (touches only `schemes/` and new tests)
- Blocks: S11
- Parallel batch: 1 (with S01 and S02 — disjoint file sets)

## TDD test stubs
- Test: every name in the translated set resolves through `SchemeParser` without warning.
- Test: each translated scheme defines all 15 `p#` entries for colour, symbol, line pattern
  and line width.
- Test: `stcolor`'s `p1` colour equals the RGB that Stata's `stc1` resolves to — derived from
  Stata, not from memory.
- Test: no translated scheme produces `#000000` for `p1` (the current `stcolor` failure mode).
- Test: each translated scheme defines `graphsize x` and `graphsize y`.
- Test: the fidelity harness reports coverage per scheme and fails below an agreed threshold.
- Test: a scheme name outside the set is rejected with a message naming the supported set.
  (The enforcement lands in S11; the test is written here and marked xfail until then.)

## Tasks

<task type="auto" id="03-01">
  <name>Extract ground truth from Stata for all 14 schemes</name>
  <files>test/fixtures/scheme_truth.json, scripts/extract_scheme_truth.do</files>
  <action>
    Do not translate from memory or from the existing approximations — both are how the
    current files drifted.

    Write a do-file that, for each of the 14 schemes, uses Stata itself to resolve the
    properties `dash` needs to render. Colour aliases are the critical part: `stcolor`
    defines its cycle as `stc1`..`stc15`, which are named colours that must be resolved to
    RGB. Use Stata's own colour resolution rather than reading the scheme text.

    For each scheme record: the 15-entry colour cycle as RGB, the marker symbol, marker size,
    line pattern and line width cycles, background/plotregion/grid/foreground/axisline
    colours, the text sizes in the `gsize` family, legend placement and colours, and
    `graphsize x` / `graphsize y`.

    Write the result to a JSON fixture and commit it. Record in the do-file exactly how each
    value was obtained, so a reviewer can re-derive it.

    Where a property cannot be extracted from Stata programmatically, record it as null and
    list it explicitly — an honest gap is worth more than a guess.
  </action>
  <verify>The fixture contains an entry for all 14 schemes with the properties above, and every non-null value is traceable to a command in the do-file.</verify>
  <done>Ground truth exists, is derived from Stata, and its provenance is documented.</done>
</task>

<task type="auto" id="03-02">
  <name>Write the fidelity harness and the failing coverage tests</name>
  <files>test/test_scheme_fidelity.py</files>
  <action>
    Write the tests before the schemes (rule 8).

    For each of the 14 names, assert `SchemeParser` resolves it and that its resolved
    properties match `scheme_truth.json` within a stated tolerance for colour.

    Add the coverage harness: for each scheme, compute what fraction of the properties in the
    truth fixture the translated file actually supplies, and assert it exceeds an agreed
    threshold. Set the threshold from what the deepened translations achieve in 03-03, but
    write the harness first so the number is measured rather than chosen to fit.

    Add the specific regression this section exists for: `stcolor`'s `p1` must not be
    `#000000`.

    Run. Nine schemes should fail to resolve at all; the five existing ones should fail on
    coverage. Confirm those are the failures you see.
  </action>
  <verify>The nine new names fail to resolve; the five existing ones fail coverage; `stcolor` p1 fails.</verify>
  <done>A measured fidelity harness exists and currently fails for the right reasons.</done>
</task>

<task type="auto" id="03-03">
  <name>Author the nine new translations and deepen the five existing ones</name>
  <files>schemes/*.scheme</files>
  <action>
    Write one file per scheme in `dash`'s key vocabulary, populated from `scheme_truth.json`.

    Deepen the five existing files to the same standard. Today they carry colour and little
    else: `p_symbols`, `p_line_patterns`, `default_line_width`, `fill_alpha`, `bar_alpha`,
    `area_alpha` and the `gsize` family are either absent or present-but-thin. All of these
    have consumers waiting in S11.

    Give each file a header comment naming the source Stata scheme, the Stata version it was
    extracted from, and the date — so a future reader knows when it was last true.

    Where `dash` has no rendering equivalent for a Stata property, omit it rather than
    inventing a key. The invented-key problem (`color p1line`, `symbol p1`) is part of what
    this section is correcting; do not add more.
  </action>
  <verify>All 14 resolve; all coverage tests pass at the agreed threshold; `stcolor` p1 is a real colour.</verify>
  <done>Fourteen faithful translations exist, each traceable to extracted ground truth.</done>
</task>

<task type="auto" id="03-04">
  <name>Extend SchemeParser's vocabulary to the properties the translations now carry</name>
  <files>dash_render.py</files>
  <action>
    The translations now carry properties `SchemeParser` does not parse — `graphsize` in
    particular, and whatever else 03-03 added.

    Extend the parser's key list to read them. Parsing only; **do not wire up consumers** —
    that is S11's job, and doing it here would create a merge conflict with batch 3, which is
    editing the same file.

    Keep the change strictly additive so it cannot alter behaviour for an existing scheme.

    Note for S11: the parser's coercion layer (`_color`, `_gsize`, `_intensity`, `_symbol`,
    `_lpattern`, `_lwidth`, `_parse_file`, `_init_properties`) has **no unit tests** — 8 of
    15 functions — and that is precisely where the silent-black failure lives. S11 adds them.
  </action>
  <verify>Every property in the translated files is readable from the parsed scheme object; existing behaviour is byte-identical for the five original schemes.</verify>
  <done>The parser can see everything the translations carry; nothing yet consumes it.</done>
</task>

<task type="auto" id="03-05">
  <name>Update the manifest, run the full suite, commit</name>
  <files>dash.pkg, test/</files>
  <action>
    Add all 14 scheme files to `dash.pkg`, coordinating with S02 which is editing the same
    file in this batch. The manifest-completeness test from 02-01 must pass.

    Run the full pytest suite and the certification suite against the S01 baseline.

    Commit, e.g. "Translate fourteen StataCorp schemes and extend the scheme parser".
  </action>
  <verify>Manifest test passes; full suite green against baseline.</verify>
  <done>The translated scheme set ships, is tested for fidelity, and is ready for S11 to consume.</done>
</task>
