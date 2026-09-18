# Section 16: Help reconciliation, conformance suite, security and release

## Overview
Everything works. Now the documentation has to say so accurately, the conformance suite has
to prove it, and the security surface has to be re-checked after fifteen sections of change.

The reconciliation counts from the audit: **17** documented-but-not-accepted, **14**
documented-but-not-implemented, **16** implemented-but-undocumented, **19** documented-with-
wrong-values, and **180+** silent-failure sites of which exactly **10** warn. Earlier sections
fixed the code for most of these; this section makes the help match and adds the mechanism
that stops them separating again.

## User story
> As a Stata user, `help dash` describes what `dash` does. As the maintainer, a help file that
> drifts from the code fails a test.

## Business requirements
- BR-16.1 Every documented option exists and behaves as documented.
- BR-16.2 Every working feature is documented.
- BR-16.3 The conformance suite proves the drop-in claim rather than asserting it.
- BR-16.4 The security posture is re-verified against every input surface (rules 13, 18).
- BR-16.5 The package installs and works from a clean `net install` (rule 2 — not reported
  complete until it is complete).

## Risk: [yellow] — low technical risk, high consequence. This is the section where "done" is declared, and project rule 2 makes that declaration binding.

## Dependencies
- Depends on: S15
- Blocks: none
- Parallel batch: 6

## TDD test stubs
- Test: every option in `dash.sthlp`'s syntax diagrams is accepted by the corresponding
  `syntax` statement.
- Test: every `{cmdab:}` abbreviation in the help matches the `syntax` capitalisation.
- Test: every option accepted by a `syntax` statement appears in the help.
- Test: every default stated in the help matches the code.
- Test: the conformance corpus runs with zero `r(198)`, zero dropped series, zero dropped
  graphs.
- Test: three adversarial cases per input surface (auth bypass, injection, resource
  exhaustion) — rule 18.
- Test: a clean `net install` renders every `examples/` dashboard.

## Tasks

<task type="auto" id="16-01">
  <name>Build the mechanical help-conformance test</name>
  <files>test/test_help_conformance.py</files>
  <action>
    S04 started this for abbreviations. Widen it to the whole file.

    Parse `dash.sthlp` and extract: the options in every syntax diagram, every `{cmdab:}`
    abbreviation, and every stated default and accepted-value set. Compare each against the
    `syntax` statements in `dash.ado` and, where the help states a default, against the code.

    Assert bidirectionally — documented-but-absent **and** accepted-but-undocumented. One
    direction only is how 16 working features ended up undocumented.

    Run it before correcting anything. The failures are the work list for 16-02, and their
    count should approximate the audit's 17 + 14 + 16 + 19 minus whatever earlier sections
    already fixed. A large discrepancy means the test is not parsing something it should.
  </action>
  <verify>The test runs over the whole help file and its failure list is consistent with the audit counts.</verify>
  <done>Help/code divergence is measured mechanically rather than by reading.</done>
</task>

<task type="auto" id="16-02">
  <name>Correct the help</name>
  <files>dash.sthlp, dash_setup.sthlp</files>
  <action>
    Work the failure list from 16-01. Specific items carried from the audit that earlier
    sections did not already resolve:

    - Move `jitter()`, `jseed()` and `msangle()` (`:683-695`) out of the *"Unsupported Stata
      twoway options"* heading — they work and are documented under the wrong section.
    - Remove the stale claim that `by()` cannot be combined with `link()` (`:653`), and the
      matching `Raises: ValueError` docstring at `dash_render.py:6966-6968`. The code has
      allowed it since TODO A-80.
    - Document what is working and undocumented: `tabs()`, `filterposition()`, `layout(bs)`
      and the `bs: spec` grammar, the multi-`filter()` mechanism and its `;` separator, the
      `__all__` dropdown sentinel, and the whole `colorvar()` family.
    - Fix `filterposition()`'s error message, which names a non-existent option
      `filter_position()` (`dash.ado:1236`).
    - Correct `degree()`, documented 0-2 and implemented 0-3 (`:566-568`).
    - `dash_setup.sthlp:34` claims a Python version comparison that `dash_setup` never
      performs — implement it or remove the claim.
    - Add a **Migration** section listing every default this plan changed, drawn from
      `.ultraplan/CHANGELOG.md`: histogram bins and y-axis, kernels, bandwidth semantics,
      confidence level, `function` domain and grid, series styling beyond colour, figure
      proportions, legend behaviour on single-series plots, and the scheme default now
      following `c(scheme)`.
    - Rewrite the *"Differences from twoway"* section. It currently lists two unsupported
      options; it should describe the accept-and-report mechanism, point at the note the user
      will see, and state plainly what `dash` does not do.
  </action>
  <verify>The 16-01 conformance test passes in both directions.</verify>
  <done>The help describes the package, and a test enforces it.</done>
</task>

<task type="auto" id="16-03">
  <name>Formalise the conformance suite</name>
  <files>test/test_conformance.cscript, test/fixtures/twoway_corpus.do</files>
  <action>
    Promote the corpus grown from S05 into the package's headline test.

    Three assertions per command: no `r(198)`; no silently dropped series (compare the
    rendered series count against the varlist); no silently dropped graph (S12's layout guard
    makes this checkable).

    Add a fourth for the statistical layers: agreement with Stata's own computed values,
    driven by S07's `stat_truth.json`.

    Widen the end-to-end coverage while here. Only 4 of 11 cscripts reach Python today —
    `test_parser.cscript`'s single `dash` call passes `name()`, which routes to
    `_dash_register_graph` and never renders. Give the parse-only scripts a render step.

    Add the regression coverage the audit found entirely absent: date/time axes, figure
    sizing, scheme consumption, the series style cycle, server-vs-standalone parity (S15's
    test covers this — confirm it is in the suite), and `tabs()`, for which the string `tabs`
    appears nowhere in `test/` today.
  </action>
  <verify>The conformance suite runs clean; every previously-absent regression area has coverage.</verify>
  <done>The drop-in claim is proved by a test, and the coverage gaps are closed.</done>
</task>

<task type="auto" id="16-04">
  <name>Adversarial pass over every input surface</name>
  <files>test/test_adversarial.cscript, test/test_adversarial_py.py</files>
  <action>
    Project rule 18: three adversarial cases per input surface, targeting auth bypass,
    injection and resource exhaustion.

    Enumerate the surfaces after fifteen sections of change — several are new or reshaped:
    `saving()` paths (the validator was narrowed in S06), scheme names (constrained in S11),
    `if` qualifiers (the whitelist gained a translation layer in S09 — probe it specifically),
    filter specs, KPI colours (S13 closed an initial-render hole), `by()` specs, tab labels
    (no longer title-cased, so they now carry user text), axis label text, title and note
    sub-options (now parsed rather than concatenated), the unsupported-option collector from
    S05 (it reads arbitrary user text and echoes it back — check the echo path), and the
    server endpoints and rate limiter.

    Anything that gains unauthorized access or crashes the process is fixed immediately, with
    a regression test, before this section proceeds.

    Re-run the whole `BUGS.md` history as a regression sweep: 51 entries, all closed. Confirm
    each stays closed, and note any that this plan's changes reopened.
  </action>
  <verify>No adversarial case succeeds; all 51 historical bugs remain closed.</verify>
  <done>The security posture is verified against the surface as it now exists, not as it was.</done>
</task>

<task type="auto" id="16-05">
  <name>Scrub for hardcoded values that came back</name>
  <files>dash_render.py, dash.ado, dash_parse.mata</files>
  <action>
    Project rule 13, applied to this plan's own subject matter. Re-run the hardcoding audit
    over the four ranges of `dash_render.py` and the Stata-side files, and compare against the
    211-finding register in `RESEARCH.md`.

    For each original finding: fixed, deliberately retained, or reintroduced. A deliberately
    retained constant must carry a comment saying why — `_MAX_BINS`, the KPI-per-row maximum
    and `_NONSELECTION_ALPHA` are all defensible, and each should say so in the source.

    Anything reintroduced during the refactor in S15 is the likeliest failure mode; look there
    first.

    Confirm no private key or credential is anywhere in the tree, and that nothing in
    `examples/`, `test/fixtures/` or the generated dashboards embeds one.
  </action>
  <verify>Every register entry is fixed, commented as deliberate, or listed as outstanding with a reason.</verify>
  <done>The hardcoding register is closed out item by item.</done>
</task>

<task type="auto" id="16-06">
  <name>Refresh examples and verify a clean install end to end</name>
  <files>examples/, dash.pkg</files>
  <action>
    Rewrite the `examples/` do-files to exercise what now works — multi-y varlists, dates,
    `bin()`/`level()`/`kernel()`, `xsize()`/`ysize()`, schemes, `tabs()` under any layout,
    `by()` under `layout(bs)`, and `link(_all)` — and remove the workarounds that exist only
    because those were broken. `comprehensive_demo.do` uses `fa()` eight times, which did
    nothing until S09.

    Then the real test: `net install` into a clean directory from the `.pkg`, put only that
    directory on the adopath, and run every example. This is S02's cscript widened to the
    whole example set.

    Verify the responsive claim at 375px, 768px and 1440px using S10's procedure, since it is
    the abstract's headline and this is the last chance to check it.

    Run all suites — pytest, certification, conformance, parity — against the S01 baseline.
  </action>
  <verify>Every example runs from a clean packaged install and renders correctly at all three widths.</verify>
  <done>The package works as installed, proved by installing it.</done>
</task>

<task type="auto" id="16-07">
  <name>Close out and report the merge command</name>
  <files>BUGS.md, TODO.md, .ultraplan/CHANGELOG.md, .ultraplan/STATE.md</files>
  <action>
    Record every defect this plan fixed in `BUGS.md` in the existing style, each with its
    resolution and the regression test that guards it. The audit found 100+ distinct defects;
    they belong in the file that already tracks 51.

    Finalise `.ultraplan/CHANGELOG.md` as the migration document 16-02 links to.

    Update `TODO.md` and `PLAN.md` so they no longer describe a roadmap that has been
    overtaken.

    Final verification, and project rule 2 applies literally here — do not report completion
    until all of it passes:
    - full pytest suite green
    - full certification suite green, with honest skip counts
    - conformance corpus: zero `r(198)`, zero dropped series, zero dropped graphs
    - parity corpus: no undocumented divergence
    - clean `net install` runs every example
    - adversarial suite clean

    Then report the merge command for the feature branch. **Do not run it** (rule 6).
  </action>
  <verify>All six verification gates pass; BUGS.md and the CHANGELOG are complete; the merge command is reported, not executed.</verify>
  <done>`dash` works as advertised, every claim is backed by a test, and the branch is ready for the user to merge.</done>
</task>
