# Section 05: Open the option surface + unsupported-option reporting

## Overview
This is the section the abstract's promise actually rests on, and the one that gates batches
3 and 4.

`dash.sthlp:668-673` says:

> *"No error is produced for unknown options, so existing Stata graph commands copy-pasted
> into `dash` will still run."*

It is false by construction. `_dash_parse_graph_opts` (`dash.ado:230-246`) and
`_dash_parse_plot_opts` (`:293-326`) are **closed allow-lists** invoked with no `capture` and
no catch-all (`:666-669`). Anything unlisted aborts the do-file. Measured: of 59 ordinary
`twoway` commands, **37 were rejected**; a dedicated probe run confirmed **46 full-name
options** rejected by execution.

**Decision taken:** every `twoway` option is accepted. Options `dash` can honour are honoured
(in later sections). Options it cannot are accepted, ignored, and **reported together in a
single note per command that lists every unsupported option that command used**. Never an
abort, never silence.

## User story
> As a Stata user, I paste a `twoway` command that works, change one word, and it runs. If
> some of what I asked for cannot be drawn in a browser, `dash` tells me which parts in one
> line and draws the rest.

## Business requirements
- BR-05.1 No `twoway` command that runs under `twoway` may abort under `dash`.
- BR-05.2 Every ignored option is named to the user, once per command, in one message.
- BR-05.3 The help's claim about unknown options becomes true.

## Technical requirements
- TR-05.1 Add all 46 confirmed-rejected options to the two `syntax` blocks, grouped and
  commented by whether they are to be implemented (and where) or accepted-and-ignored.
- TR-05.2 Add a catch-all so an option nobody anticipated is collected rather than fatal.
  Stata's `syntax` cannot do this alone; the segment text is already in hand in Mata, so the
  unknown-option sweep belongs there, before `syntax` runs, in the same place the filter
  pre-extractor already works.
- TR-05.3 A single reporting helper accumulates unsupported options across all plot segments
  of one command and emits one `display as text` line naming them all.
- TR-05.4 `play()` and `nodraw` — currently documented as warning-and-ignored and in reality
  `r(198)` — become genuinely warning-and-ignored.
- TR-05.5 Options destined for later sections are accepted and serialized now, so the
  renderer work in batches 3 and 4 has something to read.

## Risk: [red] — this changes what every `dash` command accepts. A catch-all that is too greedy will swallow genuine typos and turn a helpful error into a silent no-op.

## Dependencies
- Depends on: S04
- Blocks: S06 through S13
- Parallel batch: 2

## The 46 rejected options, grouped by disposition

| Disposition | Options | Owner |
|---|---|---|
| Implement — statistical | `bin()` `width()` `start()` `percent` `frequency` `density` `fraction` `kernel()` `n()` `level()` `bands()` `at()` | S07 |
| Implement — axes/text | `xtick()` `ytick()` `xmtick()` `ymtick()` `xmlabel()` `ymlabel()` `text()` `t1title()` `t2title()` `b1title()` `b2title()` `l1title()` `l2title()` `r1title()` `r2title()` `title2()` `subtitle2()` | S09 |
| Implement — style | `color()` `mlwidth()` `mstyle()` `lstyle()` `blabel()` `horizontal` `vertical` `sort` `base()` on all types | S06/S09 |
| Implement — geometry | `xsize()` `ysize()` `fxsize()` `fysize()` `scale()` | S10 |
| Implement — layers | `ciopts()` `lineopts()` `fitopts()` | S07 |
| Accept and report | `play()` `nodraw` `zoom()` `xoverhang()` `yoverhang()` and any `.gph`/print option | this section |

Exact membership is settled in 05-01 by probing, not by this table — the table is the
starting hypothesis.

## TDD test stubs
- Test: every one of the 46 options is accepted (`_rc == 0`).
- Test: a genuinely unknown option (`, notarealoption(3)`) is accepted and reported.
- Test: the report lists **all** unsupported options used in one command, in one message.
- Test: a command using no unsupported option produces no note.
- Test: a command using unsupported options in two different plot segments reports both.
- Test: `play()` and `nodraw` are accepted and reported, matching `dash.sthlp:157-160`.
- Test: options destined for later sections appear in the serialized JSON with their values.
- Test: a misspelled *supported* option is still reported (it cannot be distinguished from an
  unknown one — document this consequence).
- Test: the full corpus of ordinary `twoway` commands from the parity probe runs with zero
  `r(198)`.

## Tasks

<task type="auto" id="05-01">
  <name>Establish the full rejected-option set by probing, not by listing</name>
  <files>test/fixtures/twoway_corpus.do, test/fixtures/rejected_options.json</files>
  <action>
    Build a corpus of `twoway` commands covering the documented option surface of `twoway`
    and its plottypes. Run each through `dash` under `capture`, recording the return code.

    This extends the 59-command probe that produced the current numbers. Aim for coverage of
    every option in `help twoway_options`, `help scatter`, `help histogram`, `help kdensity`,
    `help lpoly`, `help lowess`, `help fpfit` and the range and paired-coordinate families.

    Record the result as a fixture: option, plottype context, observed rc, and disposition
    (implement-in-SNN / accept-and-report). The disposition column is a decision — make it
    explicitly and write down the reasoning for anything not obvious.

    This corpus becomes the conformance suite that S16 formalises. Build it properly now.
  </action>
  <verify>The fixture covers every option in the relevant Stata help files with an observed rc and an assigned disposition.</verify>
  <done>The real rejected set is known by measurement, and every member has an owner.</done>
</task>

<task type="auto" id="05-02">
  <name>Write the failing conformance test</name>
  <files>test/test_option_surface.cscript</files>
  <action>
    Drive the corpus from 05-01: every command must return `_rc == 0`.

    Add the reporting tests: a command using several unsupported options emits exactly one
    note naming all of them; a clean command emits none; unsupported options in two plot
    segments are both reported.

    Run. The failures should reproduce the measured rejected set exactly. If the count
    differs from 05-01, one of the two is wrong — reconcile before proceeding.
  </action>
  <verify>Failures match the fixture exactly in count and identity.</verify>
  <done>The conformance test exists and fails for precisely the known reasons.</done>
</task>

<task type="auto" id="05-03">
  <name>Build the unsupported-option collector and reporter</name>
  <files>dash_parse.mata, dash.ado</files>
  <action>
    Add an unknown-option sweep in Mata, alongside the existing filter pre-extractor
    (`_dash_extract_filters`, `:884-975`), which already demonstrates the pattern of
    inspecting raw segment text before `syntax` runs.

    The sweep identifies option-shaped tokens in a segment that are not in the declared set,
    removes them from the text `syntax` will see, and returns them. Removing them is what
    makes the catch-all work at all, since `syntax` has no permissive mode.

    Be careful with two things. First, an option's argument may itself contain parentheses and
    quoted strings — reuse the existing tokenizer rather than writing a second one. Second,
    the sweep must not swallow `filter()`, which the existing pre-extractor already removed,
    nor the `if`/`in` qualifier.

    In `dash.ado`, accumulate the collected names across every plot segment of one command
    into a single local, then emit one line:

        dash: ignoring unsupported option(s): play() nodraw zoom()

    Emit nothing when the list is empty. One message per command, not per segment and not
    per option — this is the behaviour specified in the decisions.

    Document the known consequence in the help: a misspelled supported option is
    indistinguishable from an unknown one and will be reported as ignored rather than
    rejected. That is the price of BR-05.1 and it should be stated, not hidden.
  </action>
  <verify>All reporting tests pass; an unknown option is accepted and named; a clean command is silent.</verify>
  <done>No option can abort a command, and every ignored option is named exactly once.</done>
</task>

<task type="auto" id="05-04">
  <name>Declare the options destined for later sections</name>
  <files>dash.ado</files>
  <action>
    Add every option from the "implement" rows of the disposition table to the two `syntax`
    blocks, with the correct minimum abbreviation per S04's truth table, and serialize each
    into the spec JSON.

    Nothing consumes them yet. That is deliberate — the later sections need the values to
    arrive before they can honour them, and splitting acceptance from implementation is what
    lets batches 3 and 4 proceed without re-editing `dash.ado`.

    Group them in the source with a comment naming the owning section, so it is obvious which
    are wired up and which are waiting.

    Important: an option accepted here but not yet implemented must be **reported as ignored**
    by 05-03's reporter until its section lands. An accepted-but-silently-dropped option is
    exactly the defect class this plan exists to remove; do not create new instances of it
    while passing through this state.
  </action>
  <verify>Every "implement" option is accepted, serialized with its value, and reported as ignored pending its section.</verify>
  <done>The renderer work in batches 3 and 4 has values to read, and nothing is silently dropped in the interim.</done>
</task>

<task type="auto" id="05-05">
  <name>Make the existing silent no-ops honest</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    Nine options are accepted today and never read: `falpha`/`fa`, `pstyle`, `recast`,
    `cmissing`, `connect`, `mlcolor`, `mlabwidth`, `coloruseplegend`, and graph-level
    `scheme`. Each currently fails silently.

    Route each through the reporter from 05-03 so that, until its owning section implements
    it, using it produces a note. `falpha` goes to S09, `mlcolor` to S09, graph-level
    `scheme` to S11; `pstyle`, `recast`, `cmissing` and `connect` are accept-and-report
    permanently.

    Note for S11: `coloruseplegend` is read into `_use_plegend` at `dash_render.py:1602-1605`
    and marked `# noqa: F841`. That `noqa` is a marker for a known dead assignment — treat
    any other `noqa: F841` in the file as a candidate for the same problem and check them.
  </action>
  <verify>Each of the nine produces a note naming it; none is silently dropped.</verify>
  <done>Every accepted option either works or says it does not.</done>
</task>

<task type="auto" id="05-06">
  <name>Correct the help, run the full suite, commit</name>
  <files>dash.sthlp, test/</files>
  <action>
    `dash.sthlp:668-673` now becomes true, but it needs rewording: unknown options are
    accepted **and reported**, not silently ignored. Replace the "not yet supported:
    `play()`, `nodraw`" list at `:157-160` with an accurate description of the mechanism and
    a pointer to the note the user will see.

    Run the full pytest suite and the certification suite against the S01 baseline, plus the
    new conformance test. The conformance corpus must show **zero** `r(198)`.

    Commit, e.g. "Accept the full twoway option surface and report unsupported options".
  </action>
  <verify>Zero r(198) across the conformance corpus; full suite green against baseline.</verify>
  <done>The load-bearing claim in the help is true, and a test proves it.</done>
</task>
