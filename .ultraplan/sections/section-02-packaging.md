# Section 02: Packaging — make `net install` work

## Overview
`dash` is completely non-functional when installed the advertised way. `dash.pkg` declares
six files and omits `schemes/`. `SchemeParser._SCHEMES_DIR` (`dash_render.py:702`) resolves
as a sibling of `dash_render.py`, so after a `net install` it does not exist, and the
recovery path calls the same failing constructor a second time outside the `try`:

```python
try:    self.scheme = SchemeParser(_scheme_name)
except (ValueError, OSError):
        self.scheme = SchemeParser("s2color")     # dash_render.py:5004
```

Reproduced by staging exactly the six declared files into a clean directory: `DashRenderer`
construction raises `ValueError: dash: scheme 's2color' not found`. Every `dash` command
would end in a Python traceback for every user who installs the package. It works on the
author's machine only because the development tree contains `schemes/`.

No existing test can catch this, because every test runs from the repo.

This is the smallest section in the plan and the most urgent.

## User story
> As a Stata user, when I run `net install dash` and then `dash scatter mpg weight`, I get a
> dashboard — not a Python traceback.

## Business requirements
- BR-02.1 A clean `net install` must produce a working command with no further setup beyond
  `dash_setup`.
- BR-02.2 A missing or unparseable scheme must never traceback; it must degrade with a
  message a user can act on.

## Technical requirements
- TR-02.1 `dash.pkg` ships every file the package needs at run time.
- TR-02.2 `DashRenderer.__init__`'s scheme fallback cannot raise.
- TR-02.3 `GlyphMapper.__init__:1142` has the same defect and the same fix.
- TR-02.4 A certification test installs into a temp directory from the `.pkg` manifest and
  renders, so the defect cannot return.

## Risk: [green] — small, well understood, and immediately verifiable.

## Dependencies
- Depends on: none
- Blocks: S16 (release verification)
- Parallel batch: 1 (with S01 and S03 — disjoint file sets)

## TDD test stubs
- Test: staging only the files listed in `dash.pkg` into a temp directory and constructing a
  `DashRenderer` succeeds.
- Test: with `schemes/` deliberately absent, `DashRenderer` construction does not raise.
- Test: with `schemes/` absent, a `UserWarning` names the missing directory.
- Test: `GlyphMapper` likewise does not raise.
- Test: every file referenced at run time appears in `dash.pkg` (a manifest-completeness
  test that reads the `.pkg` and compares against a known required set).

## Tasks

<task type="auto" id="02-01">
  <name>Write the packaging regression test first</name>
  <files>test/test_packaging.py</files>
  <action>
    Write a test that parses `dash.pkg`, copies exactly the files it declares into a fresh
    temp directory, loads `dash_render.py` from that directory by path, and constructs a
    `DashRenderer` with a minimal master spec and data JSON.

    It must currently fail with `ValueError: dash: scheme 's2color' not found`. Run it and
    read that failure before proceeding.

    Add a second test asserting `GlyphMapper` construction under the same conditions.

    Add a third, different in kind: a manifest-completeness test that walks the repo for
    files `dash_render.py` and `dash.ado` reference at run time and asserts each appears in
    `dash.pkg`. This is the test that catches the next omission, not just this one.
  </action>
  <verify>All three tests fail, and the first fails with exactly the ValueError above.</verify>
  <done>The failures have been read and confirmed correct.</done>
</task>

<task type="auto" id="02-02">
  <name>Ship the scheme files</name>
  <files>dash.pkg</files>
  <action>
    Add an `f` line for every file in `schemes/`. Note that S03 is authoring additional
    translated schemes in parallel — coordinate so the final manifest covers the full set
    rather than only today's five. If S03 has not landed yet, add today's five and leave a
    task note in S03 to extend the manifest, and make the manifest-completeness test from
    02-01 the thing that enforces it.

    Check how Stata's `net install` handles a subdirectory in a `.pkg` file before assuming
    `f schemes/s2color.scheme` places the file in a `schemes/` subdirectory of the install
    target. If it flattens, either adjust `_SCHEMES_DIR` to look alongside `dash_render.py`
    as well as in `schemes/`, or rename the files. Verify empirically with a real
    `net install` from a local directory — do not assume.
  </action>
  <verify>A real `net install` from a local directory places the scheme files where `_SCHEMES_DIR` looks for them.</verify>
  <done>The packaged install contains the schemes, verified by installing, not by reading the manifest.</done>
</task>

<task type="auto" id="02-03">
  <name>Make the scheme fallback incapable of raising</name>
  <files>dash_render.py</files>
  <action>
    At `dash_render.py:5002-5005`, the `except` handler calls `SchemeParser("s2color")`
    outside any `try`. Restructure so that a total failure to resolve any scheme produces a
    usable in-memory default — a small hardcoded set of properties equivalent to today's
    s2color colours — together with a `UserWarning` naming the directory that was searched.

    The same defect exists at `GlyphMapper.__init__:1142`. Fix both, and make them share one
    helper so they cannot diverge.

    Be precise about the distinction this creates, because S11 depends on it: a scheme the
    user *asked for* that cannot be found is an **error** (S11 restricts `scheme()` to the
    translated set and reports unknown names). A scheme directory that is missing entirely is
    a **degradation** with a warning. Do not collapse the two.
  </action>
  <verify>All tests from 02-01 pass; a render with `schemes/` removed succeeds and warns.</verify>
  <done>No scheme resolution failure can produce a traceback.</done>
</task>

<task type="auto" id="02-04">
  <name>Add an end-to-end packaged-install certification script and commit</name>
  <files>test/test_netinstall.cscript, test/run_all_cscripts.do</files>
  <action>
    Write a Stata certification script that performs a real local `net install` into a temp
    directory, puts only that directory on the adopath, and runs a full
    `dash scatter` + `dash build` cycle. This is the only test that exercises what a user
    actually does.

    Add it to the runner. Run the full suite, both halves, against the S01 baseline. Commit
    with a single-issue message such as "Ship scheme files and make scheme fallback
    non-raising".
  </action>
  <verify>The new cscript passes from a genuinely packaged install; full suite green against baseline.</verify>
  <done>`net install` produces a working `dash`, proved by a test that installs it.</done>
</task>
