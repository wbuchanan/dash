# Section 05: Measured Python floor (P1.33, M3/M10)

> Part of: WP-30 · Items: P1.33 (entry `P1.33`) · Risk: yellow · Batch: 2 · Depends on: 02, 03 · Blocks: 25, 41 · Tasks: 19, 2 commits (P1.33 measure, then P1.33 lower) · Case prefixes: PYF; HON-31..39

## Review amendments

- Blocker: PYF-03/PYF-04 used `assert` and bare `display "PYF-0n PASS"`, so `WP30_ONLY=S05` ended "no case ran", r(9) (05-17's and AC-05.6's pass line could not appear) and a failed assert would stop every later block of the certification run; both now report through `_w30_expect`/`_w30_done` (TR-01.10.4) and 05-17 requires `ALL CHECKS PASSED`.
- Major (rule 1): TR-05.7's runner paragraph tested `"`_dash_pyx'"'` without `macval()`, expanding a `$` or backquote in `DASH_PYTHON_EXEC` before the Mata check, and relied on unconfirmed `\x22` regex escapes; it now uses S02's form (`: environment`, `macval()`, by-value `strpos`/`char()`/`ascii()` check) and sits below S02's `// ---- root: end ----` line as S02's Boundaries require (it said "after set more off", which is above the root block). 05-04's probe and `TestTheCertRunnerLink`'s needles follow.
- Major: TR-05.5's `floor_stata_leg.do` read `DASH_REPO` its own way; it now uses S02's TR-02.9 stanza (A130) and checks its other three variables by value; `TestTheStataLeg`'s needles follow.
- Minor: "Can run with" now names the files shared with S06 (`scripts/release_verdict.py`, `test/test_release_verdict.py`; distinct symbols) and S04/S06's dash.ado lines.
- Spot-checked at HEAD: `_dash_pymin` dash_setup.ado:489-500, `_dash_launch_app`'s `-P` dash_render.py:37318, dash_setup_lib.py:85 and :459-463, conftest `_BASELINES` :207 / `_baseline_name` :234 / `_strict` :252, test_setup_honesty.cscript:970-979, `VERIFIED_BOKEH` test_label_sinks.py:154. All hold (test_strict_mode's skipif is :156-157, not :158-159; harmless).
- Checked: M3 (measure 3.11/3.12 in scratch venvs; lowest passing version; guards for 3.13-only code), M10 (downloads only into `<scratch>/venv-s05-*`), two-commit form (A156: commit A leaves entry, key and marker; both subjects end `(WP-30 P1.33)`); key check by import (correct). D-05a moves the one floor certification run into commit B's cycle; index.md step 2.2 still lists it under commit A (cross-file fix recorded in review-notes/g01.md).
- Rejected: none.
- Ratification 06oct2026 (index row 25, A125 / P1.33.4), CHANGED to "Manual only": no release-gate floor leg. Removed task 05-16 ("Add the release gate's floor leg"), TR-05.16, BR-05.7 (the gate fails without the floor leg), the `TestTheFloorLeg` stubs (five tests in `test/test_release_verdict.py`), the `floor_verdict` mutation row, the "gate floor leg" test-plan row, the `main` blast-radius row, and the S58.5 hand-off; D-05f now records the ruling (ratification 06oct2026).
- Renumbered after the removal: tasks 05-17..05-20 are now 05-16..05-19, TR-05.17..TR-05.20 are TR-05.16..TR-05.19, BR-05.8 is BR-05.7. Older amendment lines above keep the old numbers (ratification 06oct2026).
- AC-05.3, 05-18 (was 05-19) and "Stata truth" item 2 judge the commit-B Stata legs by `grep` for the six `GATE` lines instead of `release_verdict.py --floor`; 05-11 and 05-12 no longer touch `test/test_release_verdict.py`; the Resolution text, CHANGELOG line, GAPS2 K2 note and AGENTS.md invariant no longer promise a gate leg (ratification 06oct2026).
- Manual re-measure procedure recorded in `scripts/floor_matrix.sh`'s header (TR-05.3, six steps, "not part of make gate"), pinned by the new `TestTheScript::test_the_header_gives_the_manual_re_measure_procedure`; `make test-floor` (TR-05.4) stays as the one-leg manual runner, its help line saying it is not part of `make gate` (ratification 06oct2026).
- Two commits kept (A156): commit A still measures with no product change and commit B declares from it, each with its own red-to-green cycle; only the gate leg left commit B (ratification 06oct2026).

The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:167 (P1.33, source GAPS2-H4g): "Python floor 3.13 excludes 3.11/3.12 users. Setup reports failure although dash may still render."

- WP-28 K2 set the floor to 3.13 because 3.13 is the interpreter Stata is linked to on the maintainer's Mac, not because anything needs 3.13 (BUGS.md:2644, DISCOVERY Q8 "declare only what is tested today"). Its residual reads: "no interpreter or bokeh below the floor is run by any test".
- Measured at `c96facd` (research p1-33 §2b): `dash_setup` with only `sys.version` faked to 3.12.12 and the real bokeh 3.8.0, numpy 2.3.5 and pandas 2.3.3 present prints "version 3.12.12 is below the minimum 3.13. / bokeh and pandas will not install or import reliably." and ends r(198) with `Unmet:  Python 3.12.12 (needs 3.13)`. Every package was OK.
- **The advice loop** (research §2b, critic gap 4). A Homebrew `python@3.12` user (externally managed, PEP 668) is told to run `dash_setup, venv("~/.dash/venv")`, and that refuses too: `venv() ............ not started: Python 3.12.12 is below 3.13.`, r(198). dash_setup offers such a user no way forward. The loop is structural: lowering the number moves it below the new floor, it does not remove it.
- The help (dash.sthlp:3787, dash_setup.sthlp:44-45, 116, 127, 150-152), `dash.pkg:17`, dash.ado's `_dash_require_python` message and CHANGELOG's Requirements all say 3.13.

**After this section.** The declared floor is the lowest Python at which, measured on this Mac in scratch environments, both pytest suites (the Stata pins and the development pins), a fresh resolve as `dash_setup` installs, the Stata venv-link leg (a saved page, a served app answering `/health`, `dash_setup, venv()`) and one full certification run all pass (M3; register P1.33.2). The expected result is 3.11: numpy 2.3 needs Python 3.11 (research §2d), and every file compiles and every stdlib name resolves on 3.11 and 3.12 (research §2c). The number is never assumed: commit A measures it, commit B declares it.

- `dash_setup` accepts 3.11 and 3.12. On a managed or pip-less Python below the floor it names the floor and suggests no `venv()` (register P1.33.6), and `r(hint_cmd)` is empty.
- `_dash_pymin`, the `_dash_require_python` message, `dash.pkg`, both help files and CHANGELOG state the measured floor.
- `test/conftest.py` gains a baseline per measured stack, `test/requirements-stata.txt` and `test/requirements-dev.txt` hold their exact pins, and `scripts/floor_matrix.sh` with `make test-floor` re-runs any leg.
- No release-gate leg re-tests the floor (register P1.33.4, ratification item 25, answered 06oct2026: "Manual only"). The floor is measured once, here; `scripts/floor_matrix.sh`'s header records the manual re-measure procedure (TR-05.3).

**Why one section, two commits.** Every piece reads or sets one number (`_dash_pymin`). The manifest (A138, A156) splits it into a measuring commit A (harness, runners, baselines, the matrix; no product file changes) and a declaring commit B (the floor, the advice loop, the help, the entry closed). The split still earns its keep without a gate leg: commit A's measurement is what commit B's number is read from, and each commit has its own red-to-green cycle.

**Test order and commit rule (rule 7, A156).** Two cycles share the entry `P1.33`.

- **Commit A (measure).**
  - 05-01 writes commit A's failing tests and saves `<scratch>/05-P1.33-1-failure.txt`. It never commits.
  - 05-02 to 05-09 add the baselines, pins, runner, Stata leg and runner link, build the interpreters, make the setup harness floor-independent, run the six pytest legs and the Stata legs, and decide the floor.
  - 05-10 certifies and commits. The BUGS.md entry, its `WP30_OPEN` key and its CHANGELOG marker stay in place (A156).
- **Commit B (declare).**
  - 05-11 and 05-12 write commit B's failing tests on commit A's tree and save `<scratch>/05-P1.33-2-failure.txt`.
  - 05-13 to 05-18 lower the floor, stop the advice loop, guard what the matrix found (if anything), fill the truth block, update the help, and re-run the Stata legs and the floor certification run.
  - 05-19 closes the entry and commits.

No test-only commit exists, and no commit is red.

### Section decisions (this file; binding on the executor)

- **D-05a. The floor certification run belongs to commit B's cycle.** Index step 2.2 lists it among commit A's matrix runs; the count (1) is unchanged. At commit A's floor (3.13), every cscript case that runs the real `dash_setup` against the linked interpreter refuses a linked 3.11 by construction, which is the defect. Examples: `_hon_run_setup` (test_setup_honesty.cscript:432-454) and PEP-18 (:919-950), which runs `dash_setup, venv()` from `c(python_exec)` and asserts rc 0. So the run can only pass once the floor is lowered. Commit A's Stata evidence is the venv-link leg (05-08).
- **D-05b. Commit A makes the setup harness floor-independent.** This is the manifest's "harness pins to 3.13 fixed".
  - The cscript cases that hard-code 3.13 (PC-16, PC-17, PEP-13, PEP-14, HON-30) read `_dash_pymin`'s `r(pymin)`, and their below-floor examples become 3.10.x, which is below every candidate floor.
  - `test_setup_pep668.py`'s `MINS["python"]` is read from dash_setup.ado.
  - So commit B flips only what asserts the floor itself.
- **D-05c. `_baseline_name` prefers a full match.** With two baselines per Python (`py311` and `py311-dev`), the first baseline whose Python matches is the wrong one for a `-dev` leg. Example: `TestStrictModeOnARun`'s skipif (test_strict_mode.py:158-159) would skip it, and a skip is red under strict mode. The rule becomes: the baseline named by `DASH_BASELINE`; else the one the running stack matches in every pin; else the first whose Python matches; else `dev`.
- **D-05d. The `verify_in` pass test stops depending on the floor.** `TestVerifyIn::test_a_venv_seeing_the_packages_passes_versions_and_schemes` tests the pass path of the packages and schemes. It uses the running interpreter's major.minor as its Python minimum. The floor has its own tests (`test_a_venv_below_the_python_floor_is_refused` at "99.0", test_version_floor, HON-31/32). The research's proposed `verify_in(..., MINS, (3, 11, 0))` test is dropped: the fourth argument only chooses `safe_flags`, and the child checks its own `sys.version_info` (dash_setup_lib.py:85), so it would test nothing.
- **D-05e. The advice-loop fix covers both guidance kinds.** `stata_guide` serves both the managed (PEP 668) and the pip-less guidance. `nopip_message` also suggests `dash_setup, venv(path)` (dash_setup_lib.py:461-462). With `pyok == 0`, both give `below_floor_message`'s text and no command: same root cause, same function (fold rule).
- **D-05f. No release-gate floor leg (ratification item 25, A125 / P1.33.4, answered 06oct2026, CHANGED: "Manual only").**
  - The floor is measured once in WP-30 (05-05 to 05-08, and 05-18 at commit B's tree) and declared from that measurement.
  - This section does not edit `make gate`, `scripts/run_release_gate.sh` or `scripts/release_verdict.py`. No `DASH_FLOOR_VENV`, `FLOOR_REQUIRED`, `declared_floor`, `floor_verdict`, `--floor` form or `TestTheFloorLeg` exists.
  - TR-05.6's `GATE venv-python` line stays: the Stata leg reuses `release_gate_venv.do` and must say which Python ran. In `make gate`'s own venv phase it is one more line that `venv_verdict` ignores.
  - Re-measuring is manual: `scripts/floor_matrix.sh`'s header gives the procedure (TR-05.3), and `make test-floor` runs one leg. Neither is called by `make gate`.
- **D-05g. Interpreters and downloads (M10, E12).**
  - 3.11: conda-forge arm64 into `<scratch>/venv-s05-base311`, with `CONDA_PKGS_DIRS` in scratch.
    - The base conda is `/opt/anaconda3/bin/conda`, conda 26.1.1, whose only channel is `defaults`. `--override-channels -c conda-forge` avoids the defaults channel's terms prompt.
    - If any terms prompt or `CondaToSNonInteractiveError` appears, stop and ask the maintainer; terms are never accepted on their behalf.
    - The local `/usr/local/bin/python3.11` is x86_64 and cannot be linked to arm64 Stata (research §2e: `PYRUN rc=7100`).
  - 3.12: Homebrew's arm64 `/opt/homebrew/bin/python3.12` (3.12.12) as the base; its own site-packages are never written (it is externally managed; venvs are not).
  - pip: wheels only (`--only-binary=:all:`), cache in scratch, `PIP_CONFIG_FILE=/dev/null`.
  - `~/.conda/environments.txt` is copied before `conda create` and restored from the copy afterwards. `~/.stata19/console/stata19.rc`'s `shasum` is the same before and after every Stata run.
- **D-05h. The fresh-resolve leg (register P1.33.5, A126).**
  - It installs what `dash_setup` installs (`packaging`, `bokeh`, `numpy`, `pandas` at its minimums), with M9's window applied to bokeh (`bokeh>=3.8,<3.10`), plus the test tools.
  - It runs strict against the baseline `_baseline_name` picks for the resolved stack.
  - A failure that also occurs on the development interpreter with the same resolved versions is a package-window finding for S41, not a floor failure. An example is bokeh 3.9.1 against `VERIFIED_BOKEH = {"3.8.0", "3.9.0"}` (test_label_sinks.py:154). It is recorded and handed over in Notes.
- **D-05i. No fixture.** P1.33 draws nothing. The record of "what passed" is `_BASELINES` itself: commit A keeps a baseline only for a stack whose legs passed, and `test_the_python_floor_is_the_lowest_baseline_python` pins `_dash_pymin` to the lowest baseline Python. The leg logs are quoted in the commit bodies (E11).
- **D-05j. The decision table (05-09).**

  | Matrix result | Floor | Commit A keeps | Commit B |
  |---|---|---|---|
  | 3.11 and 3.12 pass every leg | 3.11 | `py311`, `py311-dev`, `py312`, `py312-dev` | as written |
  | 3.11 fails a leg on a product difference that a guard or fallback removes (M3) | 3.11 | all four | 05-15 adds the guard and its regression test; 05-18 re-runs that Python's failed legs |
  | 3.11 fails for a reason no guard removes (no wheel for a pinned package on cp311), 3.12 passes | 3.12 | `py312`, `py312-dev` | "3.11" reads "3.12" in 05-13/05-17/05-19; HON-32 asserts 3.11.2 is refused, rc 198 |
  | neither passes, or Stata cannot link the conda-forge 3.11 at all | stop | — | report to the maintainer (PLAN K15); nothing is committed |

  A timing test that misses its bound on one interpreter is triaged (Notes, "Timing bounds"), never widened silently.

## Risk: [yellow] — the number is measured on downloads, and the measurement takes six suite runs, two Stata legs per Python and one certification run

**Why.** The runtime on 3.11 and 3.12 is unmeasured today. Static evidence says it works: compile and import checks on 3.10-3.12, 415 stdlib attribute chains resolved, no 3.11+ API found (research §2c). Measuring needs downloads, a second interpreter linked to Stata, and the queue's time.

**Risk factors.**
1. A wheel for a pinned package may be missing on cp311 or cp312 for macOS arm64, so the stack cannot be built.
2. Stdlib behaviour changes between 3.11 and 3.13 that static checks cannot see. Each was probed by the critic and found harmless, but only the matrix proves it:
   - `sum()` of floats is compensated from 3.12 (`_dash_ts_cost`, dash_render.py:22316; 0 of 27,951 tick lists differ);
   - the C tokenizer from 3.12 (dash_render.py:27501-27510; same AST);
   - `ipaddress` formatting of `::ffff:` addresses on 3.11.2 (dash_render.py:4203-4205; both forms valid, no test pins the string).
3. Timing bounds calibrated on 3.13/3.14 (test_qualifier_logic.py:821 ran 11.1 s against 10 s under tracemalloc on 3.13; BUGS.md:2315).
4. Linking Stata to a scratch interpreter could leave the maintainer's link changed.
5. The served launcher passes `-P` unconditionally (dash_render.py:37318). That flag exists only from 3.11: `/usr/local/bin/python3.10 -P -c pass` prints `Unknown option: -P`, rc 2 (measured 03oct2026). A floor below 3.11 would break `dash serve`.
6. The advice-loop fix touches the guidance every managed-Python user sees.
7. Two baselines per Python break today's one-baseline-per-interpreter assumption in strict mode.

**Mitigation.**
1. Wheels only, exact pins, and D-05j's rule for an unbuildable stack.
2. The full suites run under each Python with both pin sets, including the parity corpus (both modes, before and after filter moves) and the served-app tests. A product difference gets a guard plus a regression test (M3, 05-15).
3. Notes, "Timing bounds".
4. Session-only links (`python set exec` without `permanently`, release_gate_venv.do:32), the `stata19.rc` hash checked around every run, and conda's registry restored (D-05g, E12).
5. `TestTheFloorAdmitsTheServedLauncher` pins `_dash_pymin >= 3.11` against the `-P` in `_dash_launch_app`'s command.
6. Only `pyok == 0` changes the guidance. Every existing PEP/PC case runs on a Python above the floor and is unchanged (`test_stata_guide_prints_plain_text`, PEP-01, PEP-04, PEP-15).
7. D-05c, with `test_the_baseline_is_the_one_named_or_the_one_whose_python_runs` extended.

## Dependencies

- **Depends on: 02, 03** (batch 1, landed before this batch's base).
  - **S02** made the runners portable: one Stata-invocation rule (`STATA_BIN`, the arch decided from the binary), `DASH_REPO` for new scripts (A130), and a guard test that fails on any `arch -arm64` literal or maintainer path under `scripts/`, `test/` or the Makefile. Every script this section writes (`scripts/floor_matrix.sh`, `scripts/floor_stata_leg.do`, the `run_all_cscripts.do` link paragraph) follows that form and names no interpreter.
  - **S03** added `_dash_statamin` beside `_dash_pymin`, the Stata guard, `version 19` in every program (including `_dash_setup_guide`), and its Stata line in `dash.pkg`, the Dependencies paragraphs and CHANGELOG Requirements. This section edits the Python number in those same paragraphs and lines, as S03 left them (A154, R3).
- **Blocks: 25, 41.**
  - **S25** (batch 9) creates one dash.ado floor constant, pinned equal to `_dash_pymin` by test_version_floor (register P1.32.4). It replaces the literal this section writes in `_dash_require_python`'s message, and its guard refuses a Python below the floor in both modes.
  - **S41** (batch 14) extends `test/requirements-*.txt` with the bokeh window rather than recreating them (IR-16). Every new `_BASELINES` entry must carry a verified bokeh (3.8 or 3.9).
- **Parallel batch: 2**, merge order S04, S05, S06.
- **Can run with:** S04 and S06. They share no program with this section (index, "Batch 2").
  - S04: the page assembly, `_dash_served_template`, `_dash_open_page`.
  - S06: `__main__`, the note channel and the 11 txt note sites.
  - Shared files are edited in distinct hunks:
    - `dash.sthlp`: S04 Dashboard Options and Server Mode; S06 :594-604; S05 Dependencies.
    - `CHANGELOG.md`: each section's own markers.
    - `BUGS.md` and `test/test_tracking_documents.py`: each section's own entry and key line.
    - `test/function_test_map.py`: each section's own anchor.
    - `test/test_wp30_truth.cscript`: each section's own block.
    - `test/test_release_verdict.py` (commit A, with S06): S05 adds one test to `TestTheVenvSessions`; S06 adds tests in `TestEachFailureFails` (and one needle to `DIAGNOSTICS` in `scripts/release_verdict.py`, which S05 does not edit). Distinct classes and hunks; S06 lands last and keeps both.
    - `dash.ado`: S05 only `_dash_require_python`'s message; S04 `_dash_open_page` and `_needed` (:242); S06 the note sites and `_needed` (:247).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines; dash_setup.ado 1,026; dash_setup_lib.py 724). S02 and S03 land before this section's base and shift some lines in `dash_setup.ado`, `dash.pkg`, the help Dependencies paragraphs, `Makefile` and `test/run_all_cscripts.do`. **The quoted text and symbols are authoritative; re-find each line by its text at the batch-2 base.**

### The floor and the gate (dash_setup.ado)

`_dash_pymin`, dash_setup.ado:489-500. It is the one source the gate, `venv()` and the tests read:

```stata
489  program define _dash_pymin, rclass
490      /*
491          The minimum Python version dash requires, named once.
...
499      return local pymin "3.13"
500  end
```

Read at :60-61 (`_dash_pymin` / `local c_pymin "`r(pymin)'"`); compared at :92-110:

```stata
92      python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])
93      _dash_pyver_ok "`pyver'" "`c_pymin'"
94      local pyok = r(ok)
...
98      else if `pyok' == 0 {
99          display as error "  Python ............. version `pyver' is below the minimum `c_pymin'."
100         display as error "    bokeh and pandas will not install or import reliably."
101         display as error "    Link Stata to Python `c_pymin' or later: {help python}"
```

Line 100 is false for 3.11 and 3.12 (research §2d: bokeh 3.8.0 needs Python ≥3.10, numpy 2.3.5 ≥3.11, pandas 2.3.3 ≥3.9).

The comment block at :38-47 ties the minimums to "The stata baseline of test/conftest.py, measured 25sep2026: Python 3.13.9 …; nothing older is tested (GAPS2 K2)".

`venv()` refuses below the floor, :131-137:

```stata
131     if `"`venv'"' != "" {
132         if `pyok' == 0 {
133             display as error "  venv() ............ not started: Python `pyver' is below `c_pymin'."
134             local n_fail = `n_fail' + 1
135             local fail_items `"`fail_items' venv() (Python `pyver' needs `c_pymin')"'
136             _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
137                 items(`"`fail_items'`warn_items'"')
```

(`_dash_setup_summary` exits 198 when failures > 0, :678-690.)

### The advice loop

The guidance is chosen without reading `pyok`. `_dash_setup_guide`, dash_setup.ado:997-1003:

```stata
997  program define _dash_setup_guide, rclass
998      version 16.0
999      args kind ensurepip managed
1000     local guide_cmd ""
1001     python: import sys; sys.modules["_dash_setup_lib"].stata_guide()
1002     return local cmd `"`guide_cmd'"'
1003 end
```

It is called at seven sites: :228 and :239 (packaging missing), :301 and :304 (a required package missing on a managed or pip-less Python), :330 and :336 (pip's own refusal), and :414 (the below verdict on a managed Python).

`stata_guide`, dash_setup_lib.py:592-611, picks `managed_message` or `nopip_message`. `managed_message`, :433-449, always suggests `venv()`:

```python
433  def managed_message(exe, windows, environ):
...
436      default = default_venv_path(windows, environ)
437      if any(c in default for c in '`$"'):
438          cmd = "dash_setup, venv(<a directory of your choice>)"
439      else:
440          cmd = 'dash_setup, venv("%s")' % default
```

`nopip_message`'s fallback (:461-462) also ends "or use dash_setup, venv(path)."

Measured by the research at `c96facd` with a real Homebrew 3.12 linked for one session (`link312.do`, stata19.rc unchanged):

```
  Python ............. version 3.12.12 is below the minimum 3.13.
  bokeh ............. missing
  This Python is externally managed (PEP 668): ...
    dash_setup, venv("~/.dash/venv")
  Unmet:  Python 3.12.12 (needs 3.13) bokeh (externally managed Python)
SETUP rc=198
```

and, following that advice (`venv312.do`, `PIP_NO_INDEX=1`):

```
  venv() ............ not started: Python 3.12.12 is below 3.13.
  Unmet:  Python 3.12.12 (needs 3.13) venv() (Python 3.12.12 needs 3.13)
VENVSETUP rc=198
```

### The gate, measured again for this section (03oct2026, `c96facd`)

`<scratch>/s05probe/floorprobe.do`, run through `scripts/stata_slot.sh`. It `run`s dash_setup.ado and calls the two programs:

```
PROBE pymin=3.13
PROBE pyver_ok 3.10.10 vs 3.13 -> 0
PROBE pyver_ok 3.11.0 vs 3.13 -> 0
PROBE pyver_ok 3.11.2 vs 3.13 -> 0
PROBE pyver_ok 3.12.12 vs 3.13 -> 0
PROBE pyver_ok 3.13.0 vs 3.13 -> 1
PROBE executable=/opt/anaconda3/bin/python3 child(-P)=True 3.13.9 rc=0
```

`shasum ~/.stata19/console/stata19.rc` began `c084dc78a56f` after the run, the same as before.

### Other declarations of the floor

- dash.ado:206-214, `_dash_require_python`. It checks only that `c(python_exec)` is set and never the version; its message:
  ```stata
  211          display as error "      Run {cmd:dash_setup} first, or link Stata to " ///
  212              "Python 3.13+: {help python}"
  ```
- dash.pkg:17 `d Requires: Python 3.13+, bokeh>=3.8, numpy>=2.3, pandas>=2.3.`
- dash.sthlp:3787 `{phang2}{ul:Python 3.13+} -- linked to Stata; see {helpb python}.` (Dependencies, 3780-3818).
- dash_setup.sthlp:
  - :43-46 "compared with the 3.13 minimum, … a version below 3.13 is reported as such and counted as unmet";
  - :115-116 "so is a linked Python below 3.13, or a reused environment whose Python is";
  - :127 "Python 3.13 or later must be installed and linked to Stata.";
  - :150-152 "These minimums are the versions dash's own test suites run under (Python 3.13.9, bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3 when this was written); nothing older is tested."
  - The PEP 668 section (:191-207) recommends `dash_setup, venv("~/.dash/venv")` with no word about a Python below the minimum.
- CHANGELOG.md `### Requirements` (:607):
  - :609-611 "Python 3.13 or later, linked to Stata (`dash_setup` checks this). Was 3.8 …";
  - :619-623 "The declared minimums are the tested ones -- Python 3.13, bokeh 3.8, numpy 2.3, pandas 2.3 …".
  - S01 places `<!-- WP-30 P1.33 -->` at the end of this list (R4).

### What already handles versions (not edited)

- `safe_flags`, dash_setup_lib.py:169-172, adds `-P` from 3.11. GitNexus: **HIGH**, 6 impacted, 4 flows. Under a 3.11 floor its `< 3.11` branch is dead but harmless; it is **not edited**.
  ```python
  169  def safe_flags(version):
  170      """["-P"] (safe path) where the interpreter knows it, 3.11 and later."""
  171      v = tuple(version[:2]) if version else ()
  172      return ["-P"] if v and v >= (3, 11) else []
  ```
- The served launcher, dash_render.py:37318-37319, passes `-P` unconditionally:
  ```python
  37318    _cmd = [sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port",
  37319            str(port)]
  ```
  `_DASH_BOOT`'s fallback for an interpreter without `safe_path` (:36947, `if not getattr(sys.flags, 'safe_path', False) and sys.path[:1] == ['']:`) is dead from 3.11. It is not edited; `_dash_launch_app` is read only (GitNexus LOW, 7).
- `verify_in` (dash_setup_lib.py:418-430; LOW, 1) and `stata_venv` (:636-724) read the floor from Stata's `pymin` local (:645-647, :676-678); no literal.
- `dash_setup_lib.py` must stay parseable at `feature_version=(3, 8)` (`TestModuleShape::test_stdlib_only_python38_parseable_and_run_looked_up_at_call_time`, test_setup_pep668.py:769-773).

### The harness (test/)

`test/conftest.py:207-212`, `_BASELINES`, two stacks:

```python
207  _BASELINES = {
208      "stata": {"python": "3.13", "bokeh": "3.8", "pandas": "2.3",
209                "numpy": "2.3", "scipy": "1.16"},
210      "dev": {"python": "3.14", "bokeh": "3.9", "pandas": "3.0",
211              "numpy": "2.4", "scipy": "1.17"},
212  }
```

`_baseline_name`, :234-242, falls back to `dev` for any other Python, so `DASH_STRICT=1` stops a 3.11 or 3.12 run before any test (`pytest_sessionstart`, :88-95):

```python
234  def _baseline_name(actual: dict, requested: str = "") -> str:
...
237      if requested:
238          return requested
239      for name, env in _BASELINES.items():
240          if env["python"] == actual.get("python"):
241              return name
242      return "dev"
```

`_running_env` (:221-231) reads scipy's version too. A venv without scipy is `missing`, which is drift, so the pins carry scipy although no test imports it.

The two baseline interpreters, measured 03oct2026 with `importlib.metadata`. These become the requirements files' exact pins:

```
/opt/anaconda3/bin/python3  3.13.9 arm64 bokeh==3.8.0 numpy==2.3.5 pandas==2.3.3 scipy==1.16.3 pytest==8.4.2 pytest-xdist==3.8.0 packaging==25.0
/opt/homebrew/bin/python3   3.14.5 arm64 bokeh==3.9.0 numpy==2.4.3 pandas==3.0.1 scipy==1.17.1 pytest==9.0.2 pytest-xdist==3.8.0 packaging==26.3
```

Third-party imports of `test/*.py`, `dash_render.py` and `dash_setup_lib.py` (AST scan, 03oct2026) are `bokeh`, `numpy`, `pandas`, `pytest`, `tornado` (with bokeh), `xdist`, and `sfi` (Stata only, guarded). No test imports scipy or statsmodels. The JS tests need `node` on PATH or `DASH_NODE` (test/js_runner.py:82-84); a skip is red under strict mode.

The local interpreters (research §2e, re-checked 03oct2026):

```
/usr/local/bin/python3.10  3.10.10 x86_64   (-P: "Unknown option: -P", rc 2)
/usr/local/bin/python3.11  3.11.2  x86_64   (safe_path True; cannot be linked to arm64 Stata)
/opt/homebrew/bin/python3.12 3.12.12 arm64  EXTERNALLY-MANAGED True
/opt/anaconda3/bin/conda   conda 26.1.1, channels: defaults
```

### Blast radius (E4; the orchestrator's batch-2 impact file holds the full output)

| Symbol | File | GitNexus (03oct2026, upstream) | Edited? | Grep-confirmed callers |
|---|---|---|---|---|
| `stata_guide` | dash_setup_lib.py | UNKNOWN, 0 resolved | yes (05-14) | dash_setup.ado:1001; test_setup_pep668.py:720, :726; function_test_map.py:886 |
| `managed_message`, `nopip_message` | dash_setup_lib.py | LOW, 1 each (`stata_guide`) | no (a new `below_floor_message` beside them) | — |
| `safe_flags` | dash_setup_lib.py | **HIGH**, 6 impacted, 4 flows | **no** | warn at 2.0; not edited |
| `verify_in` | dash_setup_lib.py | LOW, 1 | no | — |
| `_dash_launch_app` | dash_render.py | LOW, 7 | no (read only) | — |
| `_baseline_name` | test/conftest.py | UNKNOWN, 0 resolved | yes (05-02) | conftest.py:259; test_strict_mode.py:41-44, :151 |
| `venv_verdict` | scripts/release_verdict.py | LOW, 2 | no | — |
| `_dash_pymin` | dash_setup.ado | UNKNOWN (ado not indexed) | yes (05-13) | dash_setup.ado:60; test_setup_python_gate.cscript:81; test_setup_honesty.cscript:420, :480 (stubbed in HON-19); program_coverage_map.py:307; test_no_orphans.py:356 |
| `_dash_setup_guide` | dash_setup.ado | UNKNOWN | yes (args, 05-13) | dash_setup.ado:228, :239, :301, :304, :330, :336, :414; program_coverage_map.py:334 |
| `dash_setup` (the body: message :100 and the seven guide calls) | dash_setup.ado | UNKNOWN | yes (05-13) | every setup cscript |
| `_dash_require_python` (message only) | dash.ado | UNKNOWN | yes (05-13) | dash.ado 12 call sites (:413 … :8424); test_env_guards.cscript:359, :372; test_private_files.py:2004 |

No `dash_render.py` symbol is edited unless 05-09 records a product difference (05-15). No HIGH or CRITICAL symbol is edited.

### Tests that pin today's behaviour (flip, never delete)

| Node | Today | Commit | Flip |
|---|---|---|---|
| `test/test_strict_mode.py::TestTheBaselines::test_each_interpreter_has_one` (:30-33) | `set(C._BASELINES) == {"stata", "dev"}` | A | the six names (fewer if 05-09 drops a Python) |
| `test/test_strict_mode.py::TestTheBaselines::test_the_baseline_is_the_one_named_or_the_one_whose_python_runs` (:40-44) | four assertions | A | the four kept; py311, py312 and the full-match rule added |
| `test/test_setup_pep668.py::TestVerifyIn::test_a_venv_seeing_the_packages_passes_versions_and_schemes` (:557-564) with `MINS` (:546, `"python": "3.13"`) | fails on 3.11/3.12 with `why: python` | A | D-05d |
| `test/test_program_coverage.cscript` PC-16 (:697-714), PC-17 (:718-728), PEP-13 (:1149-1164), PEP-14 (:1166-1182) | literal "3.13"; PEP-13/14 use 3.12.11/3.12.1 as "below" | A | `r(pymin)`; 3.10.10/3.10.1 (D-05b) |
| `test/test_setup_honesty.cscript` HON-30 (:830-848) | 3.12.11 below "3.13" | A | 3.10.10 below `r(pymin)` |
| `test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_dash_setup_declares_the_stata_baseline` (:60-67) | floor Python == `_BASELINES["stata"]["python"]` | B | the package minimums only; the Python assertion moves to `test_the_python_floor_is_the_lowest_baseline_python` |
| `test/test_setup_python_gate.cscript` :136-151 | comparator cases with `want` "3.13" and a comment "the floor is 3.13" | B | cases kept (they test the comparator's shape); comment rewritten |

Unchanged, and must stay green: `test_setup_pep668.py::TestStataEntryPoints::test_stata_guide_prints_plain_text` (no `pyok` local means "not below"); `test_program_coverage.cscript` PEP-01, PEP-04, PEP-08, PEP-15; `test_setup_honesty.cscript` HON-19 (pymin stubbed to 99.0, packages present, no guide); `test_setup_pep668.py::TestVersionAndFlags::test_safe_flags_only_from_3_11`; `test_release_verdict.py::TestTheVenvSessions::test_the_venv_gate_never_links_permanently_and_reads_whole` (the new `GATE venv-python` line comes after the link and holds no `permanently`).

## User stories

- **US-05.1** As an installer whose Stata is linked to Python 3.11 or 3.12, I want `dash_setup` to accept my Python when dash's test suites pass on it, so that I am not told to replace a working interpreter. (US-30.23)
- **US-05.2** As an installer on a Homebrew or Debian Python that is below dash's floor, I want `dash_setup` to tell me to link a newer Python and not to suggest `venv()`, so that I do not follow advice that refuses too. (US-30.23)
- **US-05.3** As a maintainer, I want to re-run the floor matrix by hand with one command per leg, following a written procedure, so that I can re-check the declared floor when a pin or a minimum changes.
- **US-05.4** As a reader of the help, `dash.pkg` or the CHANGELOG, I want the Python floor stated once, with what was measured, so that I know before installing whether my Python will work.

## Business requirements

- **BR-05.1** The declared Python floor is the lowest of 3.11 and 3.12 at which all of these pass (BR-30.33; register P1.33.2):
  - strict pytest with the Stata pins;
  - strict pytest with the development pins;
  - strict pytest on a fresh resolve as `dash_setup` installs;
  - the Stata venv-link leg;
  - one full certification run.
- **BR-05.2** `dash_setup` reports a Python at or above the floor as OK and, with every package present, ends "All dependencies are satisfied", rc 0, installing nothing.
- **BR-05.3** `dash_setup` reports a Python below the floor as unmet, r(198). On a managed or pip-less Python it says to link Python <floor> or later. It never suggests `venv()`, and `r(hint_cmd)` is empty.
- **BR-05.4** `dash_setup, venv(path)` on a linked Python at or above the floor creates, installs into and verifies the environment, as it does on 3.13.
- **BR-05.5** `dash.pkg`, `dash.sthlp`, `dash_setup.sthlp`, the `_dash_require_python` message and CHANGELOG Requirements state the same floor, and the help names the Pythons the suites pass under.
- **BR-05.6** The saved page and the served app behave identically under the floor Python, before and after a filter move. The served app's launch flags need no newer Python than the floor.
- **BR-05.7** No download lands outside scratch, and the maintainer's Stata–Python link is unchanged after every measurement (M10, E12).

## Technical requirements

### Commit A — measure (no product file changes)

- **TR-05.1 `test/conftest.py`.**
  - `_BASELINES` gains four entries after `dev`, in this order:
    ```python
    "py311": {"python": "3.11", "bokeh": "3.8", "pandas": "2.3", "numpy": "2.3", "scipy": "1.16"},
    "py311-dev": {"python": "3.11", "bokeh": "3.9", "pandas": "3.0", "numpy": "2.4", "scipy": "1.17"},
    "py312": {"python": "3.12", "bokeh": "3.8", "pandas": "2.3", "numpy": "2.3", "scipy": "1.16"},
    "py312-dev": {"python": "3.12", "bokeh": "3.9", "pandas": "3.0", "numpy": "2.4", "scipy": "1.17"},
    ```
    Each `py3NN` entry carries the `stata` pins and each `py3NN-dev` the `dev` pins on an older Python.
  - The comment block (:189-205) gains one paragraph. It says these stacks are the floor matrix's (`scripts/floor_matrix.sh`, `make test-floor`), that every entry is a stack both suites pass under, and that the lowest entry's Python is the declared floor (test_version_floor). The comment names no path to an interpreter outside `/opt` (S02's guard).
  - `_baseline_name` takes D-05c's rule:
    ```python
    if requested:
        return requested
    for name, env in _BASELINES.items():
        if not _env_drift(actual, env):
            return name
    for name, env in _BASELINES.items():
        if env["python"] == actual.get("python"):
            return name
    return "dev"
    ```
    `_env_drift` is defined below it and resolved at call time. Its docstring states the three steps.
- **TR-05.2 `test/requirements-stata.txt` and `test/requirements-dev.txt`** (new). Each holds:
  - a comment header naming its baselines (`stata`, `py311`, `py312` / `dev`, `py311-dev`, `py312-dev`), WP-30 P1.33, and that S41 extends it with the bokeh window;
  - one `name==version` line per package: bokeh, numpy, pandas, scipy, packaging, pytest, pytest-xdist, with the measured versions of Evidence.

  No option lines, URLs, `-e`, `@` or environment markers (a line that could redirect an install is refused by `TestTheRequirementsFiles`). Hash pinning is out of scope (P1.30.5).
- **TR-05.3 `scripts/floor_matrix.sh`** (new, POSIX `sh`, `set -eu`; `REPO` from the script's own directory, as `run_release_gate.sh` does).
  - **`make PYTHON VENVDIR stata|dev|fresh`**
    - `PYTHON` is an absolute path to an executable and `VENVDIR` an absolute path; otherwise exit 2 with a message.
    - A `VENVDIR/gatevenv` that exists without `pyvenv.cfg` is refused (exit 2, "not a virtual environment"), and nothing is written.
    - It creates `VENVDIR/gatevenv` with `PYTHON -m venv` when absent.
    - It exports `PIP_CONFIG_FILE=/dev/null`, `PIP_DISABLE_PIP_VERSION_CHECK=1` and `PIP_CACHE_DIR=VENVDIR/pip-cache`.
    - `stata` and `dev` run `<venv python> -m pip install --require-virtualenv --only-binary=:all: -r "$REPO/test/requirements-<set>.txt"`.
    - `fresh` runs `<venv python> -m pip install --require-virtualenv --only-binary=:all: packaging "bokeh>=3.8,<3.10" "numpy>=2.3" "pandas>=2.3" scipy pytest pytest-xdist` (D-05h).
    - It then prints one line, from inside `$REPO/test`: `FLOOR made python=… bokeh=… numpy=… pandas=… scipy=… baseline=<name> drift=<pins|none>`. The line comes from conftest's `_running_env`, `_baseline_name` and `_env_drift`, run by the venv's Python.
  - **`run VENVDIR BASELINE`**
    - `BASELINE` must match `stata`, `dev`, `py3[0-9][0-9]` or `py3[0-9][0-9]-dev`; otherwise exit 2. The venv's Python must exist.
    - `DASH_NODE` must be set or `node` found; otherwise exit 2, naming `DASH_NODE`.
    - It runs, from `$REPO`, `DASH_STRICT=1 DASH_BASELINE=<BASELINE> <venv python> -m pytest test/ ${PYTEST_ARGS:--q -p no:cacheprovider}`, after printing `FLOOR run python=<x.y.z> baseline=<BASELINE>`. Its exit status is pytest's.
  - **`FLOOR_DRY_RUN=1`** prints each command as `FLOOR would run: <argv…>` and runs none (the unit tests use it).
  - Nothing is `eval`ed, every expansion is quoted except the documented `PYTEST_ARGS` word list, and no interpreter path or `arch` prefix is written in the file.
  - **Header comment: the manual re-measure procedure** (ratification item 25, "Manual only"). Besides usage, WP-30 P1.33 and the M10 scratch-only rule, it states, in order:
    1. when: before lowering or raising `_dash_pymin`, or changing a `test/requirements-*.txt` pin or a `dash_setup` package minimum;
    2. per candidate Python (an interpreter Stata can link; venvs in scratch only): `sh scripts/floor_matrix.sh make <python> <dir> stata|dev|fresh`;
    3. per venv: `FLOOR_VENV=<dir> FLOOR_BASELINE=<name> make test-floor`, expecting 0 failed and 0 skipped;
    4. the Stata leg: `PIP_NO_INDEX=1 DASH_REPO=<repo> DASH_FLOOR_WORK=<dir> scripts/stata_slot.sh <dir> <repo>/scripts/floor_stata_leg.do`, then the six `GATE` lines of `<dir>/floor_stata_leg.log`: `venv-link rc=0`, `venv-python rc=0 ver=<x.y.z>`, `venv-setup2 rc=0 linked=1`, `venv-saved rc=0 html=1`, `venv-served rc=0 health=1`, `venv-done`;
    5. one certification run with `DASH_PYTHON_EXEC=<dir>/gatevenv/bin/python make cert`;
    6. the floor is the lowest Python that passes every leg; `_BASELINES` keeps an entry only for a passing stack (test_version_floor pins `_dash_pymin` to the lowest).

    It says this procedure is not part of `make gate`. It names no interpreter path.
- **TR-05.4 `Makefile`.** A `test-floor` target, in `.PHONY` and in `help` ("make test-floor  one floor-matrix leg, run by hand (not part of make gate): FLOOR_VENV=<dir> FLOOR_BASELINE=<name>"). Its recipe:
  - exits 2 with `make test-floor: set FLOOR_VENV (prepared by scripts/floor_matrix.sh make) and FLOOR_BASELINE (e.g. py311)` when either variable is empty;
  - otherwise runs `PYTEST_ARGS='$(PYTEST_ARGS)' sh scripts/floor_matrix.sh run "$(FLOOR_VENV)" "$(FLOOR_BASELINE)"`.

  The queue reaches it as `FLOOR_VENV=… FLOOR_BASELINE=… <scratch>/full_suite_queue.sh <wt> <log> test-floor` (its `*)` mode runs `make test-floor PYTEST_ARGS='-q -p no:cacheprovider -n 6'`, and make reads the two variables from the environment).
- **TR-05.5 `scripts/floor_stata_leg.do`** (new).
  - It reads `DASH_REPO` through S02's TR-02.9 root stanza, verbatim (A130: `: environment DASH_REPO`, the `c(pwd)` fallback, r(198)/r(601)), with the message prefix `floor_stata_leg.do`; and `DASH_FLOOR_WORK` and, optionally, `DASH_FLOOR_MODE` (`dev` or `plus`, default `dev`) and `DASH_FLOOR_ADO` (default `<repo>/`) with `local … : environment …`.
  - Each of those three is tested by value in Mata before any expansion (TR-05.7's `strpos`/`ascii` test; emptiness through `macval()`). It refuses r(198), with one line naming the variable, an empty `DASH_FLOOR_WORK`, any of them holding `"`, a backquote, `$` or a control character, and a mode other than `dev`/`plus`.
  - It then runs `adopath ++ "<repo>/"`, `global dash_nobrowser 1` and `do "<repo>/scripts/release_gate_venv.do" "<work>" "<ado>" <mode> venvuse`.
  - It starts no Python itself, so the venvuse phase's `python set exec "gatevenv/bin/python"` (session only) is the session's first Python. Its header comment says so, names `stata_slot.sh` as the way to run it, and says the log is `<work>/floor_stata_leg.log`.
  - It opens with `version 19` (R6).
- **TR-05.6 `scripts/release_gate_venv.do`.** In the `venvuse` branch, directly after `display "GATE venv-link rc=`lrc'"`, add:
  ```stata
  capture noisily python: import sys, sfi; sfi.Macro.setLocal("gv_ver", "%d.%d.%d" % tuple(sys.version_info[:3]))
  display "GATE venv-python rc=`=_rc' ver=`gv_ver'"
  ```
  Only that branch reaches it. `venv_verdict` ignores the new tag (it reads `VENV_REQUIRED` only).
- **TR-05.7 `test/run_all_cscripts.do`.** Directly after S02's `// ---- root: end ----` line (never inside the root block, S02 Boundaries), before any line that runs Python, add a paragraph. The value is tested by value in Mata before it is ever expanded, and the emptiness test uses `macval()`, as S02's root block does (rule 1: a `$` or backquote in the variable must never be expanded as a macro):
  ```stata
  // WP-30 P1.33: link this session, and only this session, to another
  // interpreter (the floor certification run).  Unset, nothing changes.
  local _dash_pyx : environment DASH_PYTHON_EXEC
  if `"`macval(_dash_pyx)'"' != "" {
      mata: st_local("_dash_pyx_bad", strofreal(any(strpos(st_local("_dash_pyx"), (char(34), char(36), char(96)))) | any(ascii(st_local("_dash_pyx")) :< 32)))
      if `_dash_pyx_bad' {
          display as error "DASH_PYTHON_EXEC holds a quote, backquote, dollar sign or control character"
          exit 198
      }
      python set exec `"`_dash_pyx'"'
      display as text "  Python linked for this run only: `_dash_pyx'"
  }
  ```
  It never uses `permanently`. The check uses only `strpos`, `char()` and `ascii()` (no regex escapes to confirm); the executor still runs it once through the slot with a value holding a double quote and one holding a tab, each expected to print the refusal and r(198).
- **TR-05.8 Harness floor-independence (D-05b).**
  - `test/test_setup_pep668.py`: `MINS["python"]` is read from dash_setup.ado. Import `_setup_ado_floor` from `test_version_floor` (both live in `test/`), and add `MINS = dict(MINS, python=_setup_ado_floor()[0])` after the literal.
  - `test_a_venv_seeing_the_packages_passes_versions_and_schemes` passes `dict(MINS, python="%d.%d" % sys.version_info[:2])`, with a docstring line citing D-05d.
  - `test_the_python_minimum_is_dash_setups_floor` (new guard) asserts `MINS["python"] == _setup_ado_floor()[0]`.
  - PC-16 and PC-17 read `_dash_pymin` into a local before `_pc_setup` and build their needles from it ("version 3.7.9 is below the minimum `pymin'.", "Unmet:  Python 3.7.9 (needs `pymin')", "could not be compared to `pymin')").
  - PEP-13 uses `3.10.10 (dash test sandbox)` and `"not started: Python 3.10.10 is below `pymin'."`.
  - PEP-14 uses `venv_env` version `[3, 10, 1]` and `"The environment's Python 3.10.1 is below `pymin'."`.
  - HON-30 uses `3.10.10` and the needles `"version 3.10.10 is below the minimum `pymin'."` and `"Unmet:  Python 3.10.10 (needs `pymin')"`.
  - Each case's display line drops the number. The honesty header comment (:11, :21-30) and the HON-29..30 banner (:797) stop naming 3.13 ("the minimum `_dash_pymin` returns").
- **TR-05.9 Measurement, not code.** Six pytest legs, one Stata leg per Python, the decision (05-05 to 05-09). The commit body quotes, per leg: the `FLOOR made` line, the pytest summary line and `exit=`. Per Stata leg, it quotes every `GATE` line.

### Commit B — declare

- **TR-05.10 `dash_setup.ado`.**
  - `_dash_pymin` returns the measured floor (`"3.11"` expected). Its docstring says the value is the lowest Python the floor matrix passes (`scripts/floor_matrix.sh`; test_version_floor pins it to the lowest `_BASELINES` Python).
  - The comment at :38-47 replaces "The stata baseline … nothing older is tested (GAPS2 K2)" with the measured statement: the minimums are the stata pins; both suites, with both pin sets, pass under Python <floor> and above (WP-30 P1.33).
  - Line :100 becomes `display as error "    dash and the packages it needs are not tested below Python `c_pymin'."`.
  - `_dash_setup_guide` becomes `args kind ensurepip managed pyok pymin`. Its header comment (:989-996) documents the two new arguments, and each of the seven call sites appends `"`pyok'" "`c_pymin'"`.
  - No other line changes. The `venv()` refusal at :132-137 stays: step 1 already printed "Link Stata to Python <floor> or later".
- **TR-05.11 `dash_setup_lib.py`.**
  - New `below_floor_message(exe, pymin, kind)`, placed after `nopip_message`, in 3.8-parseable syntax. It returns `(text, "")`. The text names what the Python is (`kind` "managed": "is externally managed (PEP 668)"; otherwise "has no pip"), the floor and the interpreter path, and says:
    - a private environment made from it would be below the floor too, so dash_setup suggests none;
    - install Python <floor> or later, link Stata to it (`help python`), restart Stata and run dash_setup again.
  - It names no command, no `venv(` and no `--break-system-packages`.
  - `stata_guide` reads `pyok` and `pymin` (`sfi.Macro.getLocal`). When `pyok == "0"` and `version_tuple(pymin)` is non-empty, it uses `below_floor_message`; otherwise it keeps today's branches. `guide_cmd` is then `""`.
  - The text is printed with `print` as today (plain text; `{bf:X}` stays literal).
- **TR-05.12 `dash.ado`:** `_dash_require_python`'s message reads `"Python <floor>+: {help python}"`. S25 later replaces this literal with its constant (A123); this section adds no constant.
- **TR-05.13 `dash.pkg`:** in the `Requires:` line as S03 left it, `Python 3.13+` becomes `Python <floor>+`. Nothing else on the line changes.
- **TR-05.14 Help.**
  - `dash.sthlp` Dependencies: `{ul:Python <floor>+}`, followed by one sentence: the test suites pass under Python <floor> through 3.14, and a Stata session linked to <floor> builds and serves dashboards (measured <ddmonyyyy>); numpy 2.3 needs Python 3.11, so nothing older is supported.
  - `dash_setup.sthlp`:
    - :44-45 and :116 give the floor;
    - :127 reads "Python <floor> or later must be installed and linked to Stata.";
    - :150-152 reads "These minimums are what {cmd:dash}'s own test suites run under: bokeh 3.8.0, numpy 2.3.5 and pandas 2.3.3 under Python <floor>, 3.12 and 3.13, and bokeh 3.9, numpy 2.4 and pandas 3.0 under <floor>, 3.12 and 3.14 (measured <ddmonyyyy>); nothing older is tested.";
    - the PEP 668 section gains: "On a Python below the minimum, a private environment made from it would be below the minimum too, so {cmd:dash_setup} does not suggest one: link Stata to Python <floor> or later instead."

  All of `test_version_floor.py::test_every_declaration_agrees_with_dash_setup` stays green (it reads the floor from the ado).
- **TR-05.15 Guards for interpreter-specific code (M3)**, only if 05-09 recorded a product difference.
  - Edit the function in place with a version-independent form, or a `sys.version_info` guard whose comment names the matrix leg.
  - Add a regression test that fails without the guard on the 3.13 interpreter, by monkeypatching the behaviour.
  - Add no new module-level name. A new name would need a served copy-list anchor this section was not given (R2 row: "S05 — no copy-list change"); if one is unavoidable, stop and report before editing.
- **TR-05.16 Truth block S05** in `test/test_wp30_truth.cscript`, between S01's start and end lines (R1):
  - **PYF-03:** the linked interpreter is at or above `_dash_pymin`, through `_dash_pyver_ok`, loaded with `capture program list _dash_pyver_ok` / `if _rc quietly do "../dash_setup.ado"`.
  - **PYF-04:** `sys.executable -P` starts a child in safe-path mode, as `_dash_launch_app` starts the app.

  Python lines hold no brace (a skipped block's braces are still scanned).
- **TR-05.17 Both modes.** No drawing changes, so there is no CORPUS case, no JS twin and no copy-list entry (R2 row S05). The floor claim covers:
  - the saved page, rendered by `dash_render` in Stata's linked interpreter;
  - the served app, the child started by `sys.executable -P` (`_dash_launch_app`) and recomputing after each filter move.

  The evidence:
  - the matrix's pytest legs run `test_mode_parity.py` (both modes, before and after moves), `test_served_linked_views.py` and the served-app suites under each Python and pin set;
  - the Stata leg builds a saved page and serves `/health` from a session linked to the venv;
  - the floor certification run runs `test_e2e_filters.cscript` and `test_e2e_serve.cscript` with the floor interpreter.
- **TR-05.18 Maps.**
  - `test/function_test_map.py` `SETUP_FUNCTIONS`, under the S05 anchor (A148 (2)): `"below_floor_message": _P + "TestMessages::test_below_the_floor_the_guidance_names_the_floor_and_never_venv"`.
  - No new Stata program, so `program_coverage_map.py`'s S05 anchors stay empty (S58 removes them). No `FUNCTIONS` entry.
- **TR-05.19 Security (rule 1).**
  - Downloads: wheels only, so no package build script runs.
  - Fixed requirement sets: no caller-supplied requirements path or URL, and the pins files refuse option lines.
  - pip runs with `--require-virtualenv`, an empty pip config and a scratch cache.
  - Absolute, quoted paths, with no `eval`, no `shell=True` and no `subprocess` call with a string command.
  - Environment-supplied paths in Stata are refused when they hold `"`, a backquote, `$` or a control character (TR-05.5, TR-05.7).
  - Every interpreter link is for one session only.
  - `below_floor_message` validates the floor with `version_tuple` and suggests no command to paste.
  - The Stata legs run offline (`PIP_NO_INDEX=1`).

## Boundaries

- **Batch partners.**
  - S04 owns `_assemble_layout`, `_render_bootstrap_html`, the generated `doc.template` line in `_generate_app_source`, `_dash_served_template`, `_dash_csp_meta`, `_dash_open_page`, `scripts/extract_saving_chars_truth.do`, `test/fixtures/saving_chars_truth.json`, and dash.sthlp's `saving()` synopt and its Server Mode CSP paragraph.
  - S06 owns `__main__`, `_dash_smcl_escape`, `_dash_emit_note`, `_dash_note_scope`, dash.ado's Mata `_dash_note` and its 11 txt note sites, dash.sthlp:594-604, `test/test_note_channel.py` and the 29 `UserWarning` needles.

  This section touches none of them.
- **Later sections.**
  - S25 owns the render-time guard (`_dash_dep_fail`, `_DASH_MIN_PYTHON`, `_dash_require_deps`), the dash.ado floor constant, and dash_setup's first `python:` call (:92). This section changes no line of :92 and adds no version check to `dash`.
  - S41 owns the bokeh window: `dash_setup`'s pip specs, `VERIFIED_BOKEH`, the requirements-file bokeh lines beyond the pins written here, and the internals guards.
  - S58 owns every tracking document (A145).
- **Not changed.**
  - `safe_flags` (HIGH).
  - `_dash_launch_app` and `_DASH_BOOT` (the `-P` flag stays; the floor admits it).
  - `verify_in`, `stata_venv`, `create_venv`.
  - The non-managed below-floor path, which still pip-installs into the linked Python before reporting it unmet (P2.40's `dash_setup` residual).
  - Python 3.10 and older (manifest residual, item 33). numpy 2.3 needs 3.11, and relaxing the package floors is outside M3.
  - Windows patch levels (A124, P1.34.6). Linux and Intel Mac (M4).
- **Never.** The section never installs into `/opt/homebrew`, `/opt/anaconda3`, `~/.local`, the user's pip cache or any site-packages outside `<scratch>/venv-*`. It never links Stata `permanently`, never accepts a channel's terms of service, and never runs the Stata 14-18.5 binaries (M2).

## Stata truth

**None for twoway:** nothing is drawn. No extractor and no fixture, so there is no `_meta` stamp (D-05i). The Stata-side measurements are:

1. **The gate probe** (Evidence, re-run 03oct2026). The executor re-runs it at commit A's tree as part of 05-01's failure record, and at commit B's tree in 05-18, with this do-file:
   ```stata
   adopath ++ "<repo>/"
   global dash_nobrowser 1
   set linesize 200
   quietly run "<repo>/dash_setup.ado"
   _dash_pymin
   local fl "`r(pymin)'"
   display "PROBE pymin=`fl'"
   foreach v in 3.10.10 3.11.0 3.11.2 3.12.12 3.13.0 {
       _dash_pyver_ok "`v'" "`fl'"
       display "PROBE pyver_ok `v' vs `fl' -> `r(ok)'"
   }
   ```
   Run as `scripts/stata_slot.sh "$S/probe" "$S/probe/floorprobe.do"`. At commit B the expected output is `pymin=3.11`, and 0, 1, 1, 1, 1.
2. **The Stata venv-link leg per Python** (05-08, 05-18): `DASH_REPO="$WT" DASH_FLOOR_WORK=<venvdir> scripts/stata_slot.sh <venvdir> "$WT/scripts/floor_stata_leg.do"`. The log is `<venvdir>/floor_stata_leg.log`, and every `GATE` line is quoted in the commit body.
   - Commit A expects: `venv-link rc=0`, `venv-python rc=0 ver=3.11.x` (or `3.12.12`), `venv-setup2 rc=198` (the defect: the floor refuses the venv), `venv-saved rc=0 html=1`, `venv-served rc=0 health=1`, `venv-done`.
   - Commit B expects `venv-setup2 rc=0 linked=1` on both Pythons, with all six `GATE` lines present (AC-05.3).
3. **The floor certification run** (05-18): `DASH_PYTHON_EXEC=<scratch>/venv-s05-py311-stata/gatevenv/bin/python <scratch>/full_suite_queue.sh "$WT" "$S/05-cert-floor.log" cert`, once, through the queue (D-05a).
4. **The truth block S05** (PYF-03, PYF-04) runs in the floor certification run, under the floor interpreter, and in G8 under the maintainer's 3.13.9.

Each Stata run's `stata19.rc` hash is compared before and after (E12).

## TDD test stubs

### Commit A — red at the batch-2 base (`<scratch>/batch-2-base.txt`), saved to `<scratch>/05-P1.33-1-failure.txt` by 05-01 (plus 05-05's targeted 3.12 run)

`test/test_strict_mode.py` (edited)
- Test: `TestTheBaselines::test_each_interpreter_has_one` (flipped): `set(C._BASELINES) == {"stata", "dev", "py311", "py311-dev", "py312", "py312-dev"}`; every entry has exactly the five pins. Fails at base: `{'stata', 'dev'}`.
- Test: `TestTheBaselines::test_the_baseline_is_the_one_named_or_the_one_whose_python_runs` (extended): today's four assertions, plus `_baseline_name({"python": "3.11"}) == "py311"`, `_baseline_name({"python": "3.12"}) == "py312"`, `_baseline_name(dict(C._BASELINES["py311-dev"])) == "py311-dev"` and `_baseline_name(dict(C._BASELINES["py312"])) == "py312"`. Fails at base: `'dev' == 'py311'`.
- Test: `TestTheBaselines::test_each_older_python_runs_both_pin_sets` (new): for every `py3NN` key, `py3NN-dev` exists; the pins other than python equal `stata`'s and `dev`'s respectively; every python is below `stata`'s. Fails at base: no `py3NN` key (asserted non-empty).

`test/test_floor_matrix.py` (new; every test fails at base: file or script missing)
- Test: `TestTheRequirementsFiles::test_each_file_pins_its_baseline_exactly`: parse `name==version` lines. The major.minor of bokeh, numpy, pandas and scipy equal `_BASELINES["stata"]` and `["dev"]`; bokeh is in `test_label_sinks.VERIFIED_BOKEH`; pytest, pytest-xdist and packaging are present.
- Test: `TestTheRequirementsFiles::test_no_line_can_redirect_an_install`: every non-blank, non-comment line matches `^[A-Za-z0-9_.-]+==[0-9][0-9A-Za-z.]*$`.
- Test: `TestTheScript::test_usage_and_refusals`: no arguments gives exit 2 and `usage:`. These also exit 2, each with its message: a relative `PYTHON`; a missing interpreter; set `nosuch`; `run` with baseline `py3x; rm`; `run` with a venv lacking `bin/python`. Runs through `subprocess.run(["sh", script, …])`, no shell string.
- Test: `TestTheScript::test_a_dry_run_prints_the_exact_commands`: with `FLOOR_DRY_RUN=1`:
  - `make <sys.executable> <tmp> stata` prints `FLOOR would run: <exe> -m venv <tmp>/gatevenv` and `FLOOR would run: <tmp>/gatevenv/bin/python -m pip install --require-virtualenv --only-binary=:all: -r <repo>/test/requirements-stata.txt`;
  - `fresh` prints `bokeh>=3.8,<3.10`;
  - `run <tmp> py311` (with a stub `bin/python`) prints `DASH_STRICT=1`, `DASH_BASELINE=py311` and `-m pytest test/`.
- Test: `TestTheScript::test_it_refuses_a_directory_that_is_not_a_venv`: `<tmp>/gatevenv` exists without `pyvenv.cfg`. Exit 2 with "not a virtual environment"; the directory's listing is unchanged.
- Test: `TestTheScript::test_the_header_gives_the_manual_re_measure_procedure`: the script's leading comment block holds `make test-floor`, `floor_stata_leg.do`, `venv-setup2 rc=0 linked=1`, `DASH_PYTHON_EXEC` and `not part of make gate` (TR-05.3; ratification item 25).
- Test: `TestTheScript::test_it_names_no_interpreter_and_evaluates_nothing`: the script text has `set -eu`, no `eval`, no `python3.1`, no `/opt/`, no `/Users/`, no `arch -`, and no `--break-system-packages`.
- Test: `TestTheMakeTarget::test_make_test_floor_runs_one_leg`:
  - the Makefile has `test-floor` in `.PHONY` and `help`, and a recipe line with `sh scripts/floor_matrix.sh run "$(FLOOR_VENV)" "$(FLOOR_BASELINE)"`;
  - `make -s test-floor`, with both variables removed from the environment, exits 2 naming `FLOOR_VENV`.
- Test: `TestTheStataLeg::test_the_leg_reads_its_paths_and_links_for_one_session`: in `scripts/floor_stata_leg.do`:
  - `: environment DASH_REPO`, `: environment DASH_FLOOR_WORK`, `global dash_nobrowser 1`, `release_gate_venv.do`, `venvuse` and `version 19` are present;
  - `permanently` is absent, and so is any `python:` line (the venvuse link must be first).
- Test: `TestTheCertRunnerLink::test_the_runner_links_only_when_asked`: in `test/run_all_cscripts.do`:
  - `: environment DASH_PYTHON_EXEC` appears once, after `// ---- root: end ----`, and `python set exec` once, inside the `if` on that local, which tests `macval(_dash_pyx)`;
  - the link comes before the first `python:` and the first `do "` line;
  - no `permanently`, and the refusal line is present.

`test/test_release_verdict.py` (edited)
- Test: `TestTheVenvSessions::test_the_use_phase_reports_its_python` (new): the venvuse branch of `release_gate_venv.do` holds `GATE venv-python` after `python set exec`. Fails at base: absent.

Targeted red evidence on a matrix interpreter (05-05, before 05-06 edits the test):
- `DASH_STRICT=0 <scratch>/venv-s05-py312-stata/gatevenv/bin/python -m pytest "test/test_setup_pep668.py::TestVerifyIn::test_a_venv_seeing_the_packages_passes_versions_and_schemes" -q -n0 -p no:cacheprovider` fails at base with `'why': 'python'`.

Guard (passes before and after):
- Test: `test/test_setup_pep668.py::TestVerifyIn::test_the_python_minimum_is_dash_setups_floor`.

### Commit B — red at commit A's tree, saved to `<scratch>/05-P1.33-2-failure.txt` by 05-12

`test/test_version_floor.py` (edited; module docstring gains the P1.33 paragraph)
- Test: `TestTheFloorIsTheTestedBaseline::test_the_python_floor_is_the_lowest_baseline_python` (new): `_setup_ado_floor()[0] == min((b["python"] for b in _BASELINES.values()), key=lambda v: tuple(map(int, v.split("."))))`. Fails at A: `'3.13' == '3.11'`.
- Test: `TestTheFloorIsTheTestedBaseline::test_dash_setup_declares_the_stata_baseline` (flipped): the bokeh, numpy and pandas assertions stay. The Python assertion is removed, with the `Flipped:` reason "the Python floor is the lowest measured Python, not the stata baseline's".
- Test: `TestTheFloorIsTheTestedBaseline::test_the_old_floor_is_named_nowhere_it_matters` (extended), for whatever floor 05-09 decided below 3.13:
  - no `return local pymin "3.13"` in dash_setup.ado;
  - none of `Python 3.13+`, `{ul:Python 3.13+}` and `Python 3.13 or later` in dash.ado, dash.pkg, dash.sthlp or dash_setup.sthlp;
  - no `will not install or import reliably` in dash_setup.ado.

  Fails at A.
- Test: `TestTheFloorAdmitsTheServedLauncher::test_the_launch_flags_need_no_newer_python_than_the_floor` (new guard):
  - the source of `dash_render._dash_launch_app` (`inspect.getsource`) contains `"-P"`;
  - `dash_setup_lib.version_tuple(floor) >= (3, 11)`;
  - `dash_setup_lib.safe_flags(version_tuple(floor)) == ["-P"]`.

  Passes at A and B (it stops a future floor below 3.11).

`test/test_setup_pep668.py` (edited)
- Test: `TestMessages::test_below_the_floor_the_guidance_names_the_floor_and_never_venv` (new). For `kind` in ("managed", "nopip"), `below_floor_message("/opt/homebrew/bin/python3.10", "3.11", kind)`:
  - returns `cmd == ""`;
  - the text holds the path, `3.11 or later`, `help python` and `restart Stata`;
  - it holds neither `venv(` nor `break-system-packages`;
  - managed says `externally managed (PEP 668)`, nopip says `has no pip`.

  Fails at A: `AttributeError`.
- Test: `TestStataEntryPoints::test_stata_guide_below_the_floor_suggests_no_venv` (new).
  - `fake_sfi["local"].update(kind="managed", ensurepip="1", managed="1", pyok="0", pymin="3.11")` gives `guide_cmd == ""`, an output without `venv(`, and an output holding `3.11 or later`.
  - With `pyok="1"`, `guide_cmd == 'dash_setup, venv("~/.dash/venv")'`.
  - With `pyok="0", pymin="abc"`, the managed guidance is unchanged.

  Fails at A.

cscripts (edited; driver runs at A's tree; each FAILs or errors there)
- Test: `test/test_setup_honesty.cscript` **HON-31**: sandbox `{"pyversion": "3.12.12 (dash test sandbox)"}`, expect `[]`, gives `r(match) 1`, rc 0, "All dependencies are satisfied" found, and "below the minimum" not found. Fails at A: rc 198.
- Test: `test/test_setup_honesty.cscript` **HON-32**: the same with `3.11.2`; rc 0. If 05-09 set the floor to 3.12, the case asserts rc 198 and "version 3.11.2 is below the minimum 3.12." instead. Fails at A: rc 198, needs 3.13.
- Test: `test/test_program_coverage.cscript` **PYF-01**: PEP-08's case with `"pyversion": "3.12.12 (dash test sandbox)"` added to the spec and its own directory `pyf01 dir`:
  - the same four recorded vectors (`-m venv`, the detect probe, the pip install of `packaging bokeh>=3.8 numpy>=2.3 pandas>=2.3`, the verify);
  - rc 0, `r(venv_python)` the venv's python, `r(hint_cmd)` its `python set exec … permanently` line, and "dash_setup complete for the environment named above." present.

  Fails at A: "not started: Python 3.12.12 is below 3.13.", rc 198, no vectors.
- Test: `test/test_program_coverage.cscript` **PYF-02**: spec `{"block": ["bokeh"], "env": {"managed": true}, "pyversion": "3.10.10 (dash test sandbox)"}`, vectors `[["PYTHON_EXEC", "-c", "<ANY>"]]`. Gives rc 198 and `r(hint_cmd) == ""`. The log holds "A private environment made from it would be below" and `Link Stata to Python `pymin' or later`, and holds neither `venv(` nor `break-system-packages`. Fails at A: the managed guidance prints `dash_setup, venv("~/.dash/venv")` and `r(hint_cmd)` is that command.
- Test: `test/test_setup_python_gate.cscript`, the block "the floor dash_setup declares admits 3.11 and 3.12 (WP-30 P1.33)":
  - `_dash_pymin`, then `_dash_pyver_ok` against `r(pymin)`;
  - `3.12.12` gives 1 and `3.11.0` gives 1 (each red at A), and `3.10.10` gives 0;
  - labels `"3.12.12 >= the floor `_fl'"`, etc.

  With floor 3.12 (D-05j), the `3.11.0` check expects 0.

Guards written in commit B (pass at A and B): `TestTheFloorAdmitsTheServedLauncher` above; truth S05 **PYF-03**, **PYF-04**.

### Mutation table (each line must turn a named test red)

| Mutation | Red test |
|---|---|
| `_dash_pymin` back to "3.13" | `test_the_python_floor_is_the_lowest_baseline_python`, HON-31, HON-32, PYF-01, python_gate checks |
| `_dash_pymin` "3.10" | `test_the_python_floor_is_the_lowest_baseline_python`, `test_the_launch_flags_need_no_newer_python_than_the_floor` |
| `stata_guide` ignores `pyok` | `test_stata_guide_below_the_floor_suggests_no_venv`, PYF-02 |
| a guide call site misses its two arguments | PYF-02 (the call at :301 is the one PYF-02 reaches) |
| `_baseline_name` back to python-only | `test_the_baseline_is_the_one_named_or_the_one_whose_python_runs` |
| a pins file line `bokeh>=3.8` | `test_no_line_can_redirect_an_install`, `test_each_file_pins_its_baseline_exactly` |
| `floor_matrix.sh` drops `--only-binary=:all:` | `test_a_dry_run_prints_the_exact_commands` |
| the re-measure procedure drops its Stata leg | `test_the_header_gives_the_manual_re_measure_procedure` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| baselines, full-match selection | pytest `test_strict_mode.py` | none | n/a |
| pins files exact and inert | pytest `test_floor_matrix.py::TestTheRequirementsFiles` | none | n/a |
| runner refusals, dry-run commands, no interpreter named, manual re-measure procedure | pytest `test_floor_matrix.py::TestTheScript`, `TestTheMakeTarget` | none | n/a |
| Stata leg and runner link text | pytest `TestTheStataLeg`, `TestTheCertRunnerLink`, `TestTheVenvSessions::test_the_use_phase_reports_its_python` | none | n/a |
| both suites under 3.11 and 3.12, both pin sets and a fresh resolve | six `make test-floor` legs through the queue (05-07) | none | yes: the parity corpus, linked views and served-app suites run in every leg |
| Stata linked to each Python | `floor_stata_leg.do` through the slot (05-08, 05-18) | none | saved page and served `/health` |
| full certification on the floor | `make cert` with `DASH_PYTHON_EXEC` through the queue (05-18) | none | yes (`test_e2e_filters`, `test_e2e_serve`) |
| floor declared once and lowest | pytest `test_version_floor.py` | none | n/a |
| advice loop | pytest `TestMessages`, `TestStataEntryPoints`; cscript PYF-02 | none | n/a |
| setup accepts 3.11/3.12 | cscript HON-31, HON-32; python_gate block | none | n/a |
| `venv()` on 3.12 | cscript PYF-01 | none | n/a |
| linked interpreter at or above floor; `-P` child | truth S05 PYF-03, PYF-04 | none | served launch |
| setup harness floor-independent | cscript PC-16, PC-17, PEP-13, PEP-14, HON-30 | none | n/a |

Acceptance criteria:
- **AC-05.1** `python3 -m pytest test/test_strict_mode.py test/test_floor_matrix.py test/test_release_verdict.py test/test_setup_pep668.py test/test_version_floor.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes with no skip, on the main interpreter.
- **AC-05.2** Each of the six legs' logs ends with a pytest summary showing 0 failed and 0 skipped, then `exit=0`:
  - `05-leg-py311-stata.log`, `05-leg-py311-dev.log`, `05-leg-py311-fresh.log`;
  - `05-leg-py312-stata.log`, `05-leg-py312-dev.log`, `05-leg-py312-fresh.log`.

  A fresh leg's package-window failure is recorded under D-05h instead.
- **AC-05.3** At commit B, each of `<scratch>/venv-s05-py311-stata/floor_stata_leg.log` and `<scratch>/venv-s05-py312-stata/floor_stata_leg.log` holds the six lines `GATE venv-link rc=0`, `GATE venv-python rc=0 ver=<that Python>.`, `GATE venv-setup2 rc=0 linked=1`, `GATE venv-saved rc=0 html=1`, `GATE venv-served rc=0 health=1` and `GATE venv-done` (checked by `grep`; there is no release-gate floor verdict).
- **AC-05.4** The floor certification log has the runner's all-pass line, no `FAIL` and no unexpected `SKIP`, and holds `Python linked for this run only:` naming the floor venv. Its truth block prints `PYF-03 PASS` with the floor version and `PYF-04 PASS`.
- **AC-05.5** Through the driver:
  - `test_setup_honesty.cscript` prints `HON-30 PASS`, `HON-31 PASS` and `HON-32 PASS`;
  - `test_program_coverage.cscript` prints `PC-16 PASS`, `PC-17 PASS`, `PEP-13 PASS`, `PEP-14 PASS`, `PYF-01 PASS` and `PYF-02 PASS`;
  - `test_setup_python_gate.cscript` prints `ALL TESTS PASSED`;
  - `WP30_ONLY=S05` on `test_wp30_truth.cscript` prints `PYF-03 PASS` and `PYF-04 PASS`.
- **AC-05.6** `shasum ~/.stata19/console/stata19.rc` is identical before 05-05 and after 05-18. `~/.conda/environments.txt` is identical to its pre-05-05 copy. `find <scratch> -maxdepth 1 -name 'venv-s05-*'` lists every downloaded tree.
- **AC-05.7** The BUGS.md entry is closed in place, `WP30_OPEN` has no `P1.33` key, `grep -c '<!-- WP-30 P1.33 -->' CHANGELOG.md` prints 0, and `test_tracking_documents.py` passes.
- **AC-05.8** Two commits on `wp30-s05` end `(WP-30 P1.33)`, with no `claude|anthropic` in either message. The full suite was green once before each.

## Tasks

**Commit boundary.** Both commits are made on `wp30-s05` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s05` (`$WT`), after one full run each through the queue. Shell variables:
- `S=<scratch>/s05`, where `<scratch>` is the orchestrator's WP-30 scratch directory;
- venvs under `<scratch>/venv-s05-*` (E12).

- **Commit A:** tasks 05-01 to 05-10, subject `Measure the Python floor: run both test suites under Python 3.11 and 3.12 (WP-30 P1.33)`.
- **Commit B:** tasks 05-11 to 05-19, subject `Declare the measured Python floor and stop the venv advice loop (WP-30 P1.33)`.

Each body:
1. opens with its saved failure text;
2. then gives the measured defect;
3. then the matrix lines (commit A: every leg's `FLOOR made`, summary and `exit=` line, and every `GATE` line; commit B: the floor-run and re-run legs);
4. then what changed, where;
5. then one line each: `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>` (commit A's sha is `batch-2-base`, commit B's is commit A's), `Flipped: <node> -- <old expectation> was wrong because <why>`, and in commit B `BUGS.md: "<the P1.33 title as S01 wrote it>" (closed)`.

No message names a tool or vendor (G7). `CLAUDE.md`, `.gitignore`, `AGENTS.md` and `.ultraplan/` are never staged (E7, G6).

<task type="auto" id="05-01">
  <name>Write commit A's failing tests</name>
  <files>test/test_strict_mode.py, test/test_floor_matrix.py, test/test_release_verdict.py</files>
  <action><![CDATA[
    First check the base: `git -C "$WT" rev-parse HEAD` equals `cat <scratch>/batch-2-base.txt` and `git -C "$WT" branch --show-current` prints `wp30-s05`; stop and report otherwise. Run `mkdir -p "$S"`. Read `<scratch>/batch-2-impact.txt`; it must list `_baseline_name`, `stata_guide`, `_dash_pymin`, `_dash_setup_guide` and `_dash_require_python`, each with its result (Evidence "Blast radius"). If any symbol is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout and report any HIGH or CRITICAL before editing. In `test/test_strict_mode.py`, flip `TestTheBaselines::test_each_interpreter_has_one` (:30-33) and extend `test_the_baseline_is_the_one_named_or_the_one_whose_python_runs` (:40-44) exactly as "TDD test stubs / Commit A" says, and add `test_each_older_python_runs_both_pin_sets`. Create `test/test_floor_matrix.py` with the classes `TestTheRequirementsFiles`, `TestTheScript`, `TestTheMakeTarget`, `TestTheStataLeg` and `TestTheCertRunnerLink` and the test names of the stubs. `ROOT` comes from `__file__`. Every process runs as an argument list (`subprocess.run(["sh", …])`, `["make", "-s", "test-floor"]` with `env` lacking `FLOOR_VENV`/`FLOOR_BASELINE`), never a shell string. In `test/test_release_verdict.py::TestTheVenvSessions` add `test_the_use_phase_reports_its_python`. Write each `Flipped:` line to `$S/05-A-flips.txt`. Run `python3 -m pytest test/test_strict_mode.py test/test_floor_matrix.py test/test_release_verdict.py -q -n0 -p no:cacheprovider -rf > "$S/05-A-red.log" 2>&1`. Write `$S/05-P1.33-1-failure.txt` from it: the base sha, then each failing node with its first assertion line. Do not commit, and do not touch any other file.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/05-A-red.log"` is at least 12; `grep -c "test_each_interpreter_has_one\|test_the_use_phase_reports_its_python\|test_make_test_floor_runs_one_leg" "$S/05-A-red.log"` is at least 3; `test -s "$S/05-P1.33-1-failure.txt"`; `git -C "$WT" status --porcelain` lists only the three files.]]></verify>
  <done>Commit A's regression tests existed and failed on the unmodified tree, and their failure text was saved for the commit body.</done>
</task>

<task type="auto" id="05-02">
  <name>Add the floor baselines and exact pins</name>
  <files>test/conftest.py, test/requirements-stata.txt, test/requirements-dev.txt</files>
  <action><![CDATA[
    In `test/conftest.py` add the four `_BASELINES` entries of TR-05.1 after `"dev"` (:210-211), in the order `py311`, `py311-dev`, `py312`, `py312-dev`. Rewrite `_baseline_name` (:234-242) with D-05c's three steps and a docstring stating them, and add the comment paragraph of TR-05.1 below the existing one (:189-205). Write no path to an interpreter outside `/opt`. Create `test/requirements-stata.txt` and `test/requirements-dev.txt` exactly as TR-05.2 says, with the versions measured in Evidence (stata: bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3, scipy 1.16.3, packaging 25.0, pytest 8.4.2, pytest-xdist 3.8.0; dev: bokeh 3.9.0, numpy 2.4.3, pandas 3.0.1, scipy 1.17.1, packaging 26.3, pytest 9.0.2, pytest-xdist 3.8.0), one `name==version` per line under a `#` header. Re-measure both interpreters with the `importlib.metadata` probe of Evidence first; if a version moved, use the measured one and record it in `$S/05-pins.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_strict_mode.py "test/test_floor_matrix.py::TestTheRequirementsFiles" -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_strict_mode.py -q -n0 -p no:cacheprovider -k StrictModeOnARun` reports no skip.]]></verify>
  <done>The test harness knew a baseline for each Python and pin set of the matrix, chose the fully matching one, and two exact, inert pins files existed.</done>
</task>

<task type="auto" id="05-03">
  <name>Write the floor matrix runner</name>
  <files>scripts/floor_matrix.sh, Makefile</files>
  <action><![CDATA[
    Create `scripts/floor_matrix.sh` per TR-05.3, with the subcommands `make` and `run`, `FLOOR_DRY_RUN=1`, the refusals (exit 2, one line on stderr each), `REPO="$(cd "$(dirname "$0")/.." && pwd)"`, `set -eu` and a header comment giving usage, WP-30 P1.33 and the M10 scratch-only rule. Implement the dry-run printer as a shell function `run_cmd` that either prints `FLOOR would run:` plus its quoted arguments or executes `"$@"`. Export `DASH_STRICT=1` and `DASH_BASELINE` before calling it in `run`, and print them in a dry run. The `FLOOR made` line is printed by the venv's Python running conftest's `_running_env`, `_baseline_name` and `_env_drift` from `$REPO/test`; the dry run prints the command instead. Add the `test-floor` target to `Makefile` per TR-05.4 (recipe lines begin with a tab), add it to `.PHONY` and add its `help` line. Keep S02's Stata variables and lines as they are. Write no interpreter path, `arch` prefix or maintainer path.
  ]]></action>
  <verify><![CDATA[`sh -n scripts/floor_matrix.sh` prints nothing; `python3 -m pytest "test/test_floor_matrix.py::TestTheScript" "test/test_floor_matrix.py::TestTheMakeTarget" -q -n0 -p no:cacheprovider` passes; S02's path-guard test (its node as S02 named it in `test/`) passes.]]></verify>
  <done>One floor-matrix leg could be prepared and run by a portable script and a make target that named no interpreter and installed only wheels into the venv it was given.</done>
</task>

<task type="auto" id="05-04">
  <name>Write the Stata leg and runner link</name>
  <files>scripts/floor_stata_leg.do, scripts/release_gate_venv.do, test/run_all_cscripts.do</files>
  <action><![CDATA[
    Create `scripts/floor_stata_leg.do` per TR-05.5. Its header comment states the environment variables, the session-only link, the log name and `scripts/stata_slot.sh <work> <repo>/scripts/floor_stata_leg.do` as the way to run it. In `scripts/release_gate_venv.do`, add TR-05.6's two lines directly after `display "GATE venv-link rc=`lrc'"` (:34), inside the `venvuse` branch. In `test/run_all_cscripts.do`, add TR-05.7's paragraph directly after S02's `// ---- root: end ----` line, before any line that runs Python. Probe the refusal once through the slot: a do-file in `$S/probe-pyx` holding TR-05.7's paragraph, run with `DASH_PYTHON_EXEC` set to a value holding a double quote and then one holding a tab; each must print the refusal and end r(198). Record both in `$S/05-notes.txt`. Run no Stata session linked to anything here.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_floor_matrix.py::TestTheStataLeg" "test/test_floor_matrix.py::TestTheCertRunnerLink" test/test_release_verdict.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider` passes; `grep -c permanently scripts/floor_stata_leg.do scripts/release_gate_venv.do test/run_all_cscripts.do` prints 0 for each.]]></verify>
  <done>A Stata session could be linked to a scratch interpreter for one run only, by the Stata leg and by the certification runner, and the venv-linked session reported which Python it ran.</done>
</task>

<task type="auto" id="05-05">
  <name>Build the matrix interpreters in scratch</name>
  <files>none</files>
  <action><![CDATA[
    Record `shasum ~/.stata19/console/stata19.rc > "$S/05-rc-before.txt"` and copy `~/.conda/environments.txt` (if present) to `$S/conda-environments.before`. Create the arm64 3.11 base with `CONDA_PKGS_DIRS=<scratch>/venv-s05-pkgs /opt/anaconda3/bin/conda create --yes --quiet --override-channels -c conda-forge -p <scratch>/venv-s05-base311 "python=3.11"`. If conda shows any terms-of-service prompt or error, stop and ask the maintainer. Check that `<scratch>/venv-s05-base311/bin/python3.11 -c "import platform,sys;print(platform.machine(),sys.version)"` prints `arm64 3.11.`. Restore `~/.conda/environments.txt` from the copy if it changed; if it did not exist before, report the new file instead of removing it. Then run `sh "$WT/scripts/floor_matrix.sh" make <base> <scratch>/venv-s05-<py>-<set> <set>` for the bases `<scratch>/venv-s05-base311/bin/python3.11` (py311) and `/opt/homebrew/bin/python3.12` (py312), and for each set `stata`, `dev` and `fresh`: six venvs. Each `FLOOR made` line goes to `$S/05-made.txt`. A pip failure (no wheel) is recorded there with pip's last 20 lines. Then record the targeted red evidence for D-05d on the unmodified test file: `cd "$WT" && DASH_STRICT=0 <scratch>/venv-s05-py312-stata/gatevenv/bin/python -m pytest "test/test_setup_pep668.py::TestVerifyIn::test_a_venv_seeing_the_packages_passes_versions_and_schemes" -q -n0 -p no:cacheprovider`. Append its failure line to `$S/05-P1.33-1-failure.txt`. Nothing is installed outside `<scratch>/venv-s05-*`.
  ]]></action>
  <verify><![CDATA[`grep -c '^FLOOR made' "$S/05-made.txt"` prints 6 (or names each stack that could not be built); `grep 'py311-stata\|py312-stata' "$S/05-made.txt"` shows `baseline=py311 drift=none` and `baseline=py312 drift=none`; `diff <(shasum ~/.stata19/console/stata19.rc) "$S/05-rc-before.txt"` prints nothing; the appended failure shows `'why': 'python'`.]]></verify>
  <done>Six scratch environments held the Stata pins, the development pins and a fresh resolve on arm64 Python 3.11 and 3.12, and nothing outside scratch was changed.</done>
</task>

<task type="auto" id="05-06">
  <name>Make the setup harness floor-independent</name>
  <files>test/test_setup_pep668.py, test/test_program_coverage.cscript, test/test_setup_honesty.cscript</files>
  <action><![CDATA[
    Apply TR-05.8. In `test/test_setup_pep668.py`, read `MINS["python"]` from dash_setup.ado (import `_setup_ado_floor` from `test_version_floor`). Pass the running interpreter's major.minor in `test_a_venv_seeing_the_packages_passes_versions_and_schemes` (docstring: D-05d), and add the guard `test_the_python_minimum_is_dash_setups_floor`. In `test/test_program_coverage.cscript`, rewrite PC-16 (:697-714), PC-17 (:718-728), PEP-13 (:1149-1164) and PEP-14 (:1166-1182) in place: each reads `_dash_pymin` into a local `pymin` before its sandbox run (as `test_setup_python_gate.cscript:81-82` does), builds its needles with it, and uses 3.10.10 or `[3, 10, 1]` as the below-floor version. In `test/test_setup_honesty.cscript`, rewrite HON-30 (:830-848) the same way and update the comments at :11, :21-30 and :797. Each rewritten case is a `Flipped:` line in `$S/05-A-flips.txt` ("the literal 3.13 and a 3.12 'below' example made the case false at any lower floor"). Edit no other case.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_pep668.py -q -n0 -p no:cacheprovider` passes; through the driver ("The cscript driver"), `test_program_coverage.cscript` prints `PC-16 PASS`, `PC-17 PASS`, `PEP-13 PASS`, `PEP-14 PASS` and its all-pass line, and `test_setup_honesty.cscript` prints `HON-30 PASS` and `All dash_setup honesty tests PASSED.`; `DASH_STRICT=0 <scratch>/venv-s05-py312-stata/gatevenv/bin/python -m pytest test/test_setup_pep668.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>No setup test asserted 3.13 or used a 3.12 example as below the floor, and the verify_in pass test passed on 3.12.</done>
</task>

<task type="auto" id="05-07">
  <name>Run the six pytest legs</name>
  <files>none</files>
  <action><![CDATA[
    For each of the six venvs, launch one leg through the queue in the background: `FLOOR_VENV=<scratch>/venv-s05-<py>-<set> FLOOR_BASELINE=<name> <scratch>/full_suite_queue.sh "$WT" "$S/05-leg-<py>-<set>.log" test-floor`. The `<name>` is `py311` or `py312` for `stata`, `py311-dev` or `py312-dev` for `dev`, and for `fresh` the `baseline=` that `$S/05-made.txt` printed for that venv. If a fresh stack's `drift=` is not `none`, record it in `$S/05-triage.txt` as a package-window finding (D-05h), and launch its leg with the `-dev` baseline only if the drift is confined to a patch level. Wait for each log's `exit=` line (Monitor or an until-loop); never relaunch a leg to check on it (E1). For each leg, copy the summary line and `exit=` to `$S/05-matrix.txt`. Classify every failed node in `$S/05-triage.txt`:
    - (a) a product difference between interpreters;
    - (b) a harness assumption (a literal version, a timing bound; Notes "Timing bounds");
    - (c) an environment problem (missing node, port collision; E6 re-runs a known flaky node once in isolation with the same venv python and `-n0`);
    - (d) a package-window finding (D-05h).

    Fix (b) in the failing test file inside this commit, with a `Flipped:` line, and re-run only that leg. Record (a) for 05-15. No product file is edited here.
  ]]></action>
  <verify><![CDATA[`grep -c 'exit=' "$S"/05-leg-*.log` totals 6 (one per log, more only for a re-run leg); `cat "$S/05-matrix.txt"` shows every stata and dev leg with `0 failed` or a triage line in `$S/05-triage.txt` naming the node and its class.]]></verify>
  <done>Both pytest suites and a fresh resolve were run under Python 3.11 and 3.12, and every failure, if any, was classified.</done>
</task>

<task type="auto" id="05-08">
  <name>Run the Stata leg per Python</name>
  <files>none</files>
  <action><![CDATA[
    For `<py>` in py311 and py312, record the rc hash, then run `cd <scratch>/venv-s05-<py>-stata && PIP_NO_INDEX=1 DASH_REPO="$WT" DASH_FLOOR_WORK=<scratch>/venv-s05-<py>-stata /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/venv-s05-<py>-stata "$WT/scripts/floor_stata_leg.do"`. Copy every `GATE` line of `<scratch>/venv-s05-<py>-stata/floor_stata_leg.log` to `$S/05-stata-legs.txt`. Expected at this tree:
    - `venv-link rc=0`;
    - `venv-python rc=0 ver=3.11.` or `ver=3.12.12`;
    - `venv-setup2 rc=198` (the floor refuses the venv: the defect commit B removes);
    - `venv-saved rc=0 html=1`;
    - `venv-served rc=0 health=1`;
    - `venv-done`.

    A `venv-link` failure (for example `r(7100)` loading libpython) is an environment finding: stop and report it (D-05j last row). A saved or served failure is triaged as in 05-07. Afterwards compare the rc hash with `$S/05-rc-before.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c 'GATE venv-saved rc=0 html=1' "$S/05-stata-legs.txt"` prints 2 and `grep -c 'GATE venv-served rc=0 health=1' "$S/05-stata-legs.txt"` prints 2 (or a triage line exists); `diff <(shasum ~/.stata19/console/stata19.rc) "$S/05-rc-before.txt"` prints nothing.]]></verify>
  <done>A Stata session linked for one run to each older Python built a saved page and served the app, and dash_setup's refusal of that Python was recorded as the defect to remove.</done>
</task>

<task type="auto" id="05-09">
  <name>Decide the floor from the matrix</name>
  <files>test/conftest.py</files>
  <action><![CDATA[
    Apply D-05j to `$S/05-matrix.txt`, `$S/05-stata-legs.txt` and `$S/05-triage.txt`. Write `$S/05-floor.txt` with one line `FLOOR=<3.11|3.12>`, followed by the reason and the class (a) items 05-15 must guard. If 3.11 cannot be the floor, delete the `py311` and `py311-dev` entries from `_BASELINES` and update `test_each_interpreter_has_one`'s expected set the same way; the Python is not measured as passing. If neither Python passes, stop: report the logs to the orchestrator and the maintainer (PLAN K15), and commit nothing. Otherwise leave `test/conftest.py` as it is and say so in `$S/05-floor.txt`.
  ]]></action>
  <verify><![CDATA[`head -1 "$S/05-floor.txt"` prints `FLOOR=3.11` or `FLOOR=3.12`; `python3 -c "import sys;sys.path.insert(0,'test');import conftest as C;print(sorted(C._BASELINES))"` lists exactly the baselines whose legs passed plus `dev` and `stata`.]]></verify>
  <done>The floor was decided from the measured legs alone, and the harness kept a baseline only for a stack the suites passed under.</done>
</task>

<task type="auto" id="05-10">
  <name>Certify and make commit A</name>
  <files>none</files>
  <action><![CDATA[
    Run `python3 -m pytest test/test_strict_mode.py test/test_floor_matrix.py test/test_release_verdict.py test/test_setup_pep668.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider`. Run the two cscripts 05-06 changed through the driver, and S02's path-guard test. Run `git -C "$WT" merge --no-edit main`; it must print `Already up to date.`. Then run one full suite through the queue: `<scratch>/full_suite_queue.sh "$WT" "$S/05-full-1.log"`, waited for, 0 failed (E6 for the known flaky tests). Check `git -C "$WT" diff --name-only` lists only these files:
    - `test/conftest.py`, `test/requirements-stata.txt`, `test/requirements-dev.txt`;
    - `test/test_strict_mode.py`, `test/test_floor_matrix.py`, `test/test_release_verdict.py`, `test/test_setup_pep668.py`;
    - `test/test_program_coverage.cscript`, `test/test_setup_honesty.cscript`, `test/run_all_cscripts.do`;
    - `scripts/floor_matrix.sh`, `scripts/floor_stata_leg.do`, `scripts/release_gate_venv.do`, `Makefile`;
    - any test file a class (b) fix touched.

    Stage exactly those (with `git add`; there is no new JSON). Write the message to `$S/05-msg-A.txt`: the commit A subject, then the body of the Commit boundary paragraph:
    - `$S/05-P1.33-1-failure.txt`;
    - the defect;
    - `$S/05-made.txt`, `$S/05-matrix.txt`, `$S/05-stata-legs.txt`, `$S/05-triage.txt` and `$S/05-floor.txt`;
    - the `Regression:` lines and the `Flipped:` lines from `$S/05-A-flips.txt`.

    Check G7: `grep -Eic 'claude|anthropic' "$S/05-msg-A.txt"` prints 0. Confirm the branch prints `wp30-s05`, run `git commit -F "$S/05-msg-A.txt"`, and check G7 again on `git log -1 --format=%B`. Do not touch BUGS.md, CHANGELOG.md or `WP30_OPEN` (A156).
  ]]></action>
  <verify><![CDATA[The full-run log ends with `exit=0` and 0 failed; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.33)`; `git -C "$WT" show --name-only --format= HEAD | grep -c 'dash_setup.ado\|dash.ado\|dash_render.py\|dash_setup_lib.py\|sthlp\|dash.pkg'` prints 0.]]></verify>
  <done>Commit A, the measurement with no product change, was green on wp30-s05 and carried the matrix evidence in its body.</done>
</task>

<task type="auto" id="05-11">
  <name>Write commit B's failing pytest tests</name>
  <files>test/test_version_floor.py, test/test_setup_pep668.py</files>
  <action><![CDATA[
    Read `FLOOR` from `$S/05-floor.txt`. In `test/test_version_floor.py`:
    - add the P1.33 paragraph to the module docstring;
    - add `test_the_python_floor_is_the_lowest_baseline_python`;
    - flip `test_dash_setup_declares_the_stata_baseline` (:60-67) by removing only its Python assertion;
    - extend `test_the_old_floor_is_named_nowhere_it_matters` (:98-115);
    - add the class `TestTheFloorAdmitsTheServedLauncher`.

    Load `dash_setup_lib` the way `test_the_upgrade_line_names_the_linked_interpreter` does (:138-141). In `test/test_setup_pep668.py` add `TestMessages::test_below_the_floor_the_guidance_names_the_floor_and_never_venv` and `TestStataEntryPoints::test_stata_guide_below_the_floor_suggests_no_venv`, using the `fake_sfi` fixture. Do not touch `test/test_release_verdict.py`: there is no floor leg (ratification item 25, "Manual only"). Use `FLOOR` wherever a stub says 3.11. Record the `Flipped:` line in `$S/05-B-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_version_floor.py test/test_setup_pep668.py -q -n0 -p no:cacheprovider --co 2>&1 | tail -1` collects with no error.]]></verify>
  <done>Commit B's pytest regression tests existed, with the stata-baseline pin flipped for its stated reason.</done>
</task>

<task type="auto" id="05-12">
  <name>Write commit B's cscript cases and record red</name>
  <files>test/test_setup_honesty.cscript, test/test_program_coverage.cscript, test/test_setup_python_gate.cscript</files>
  <action><![CDATA[
    Append HON-31 and HON-32 to `test/test_setup_honesty.cscript` as one contiguous run after PEP-19's block ends and its `PEP FAILED` check (:970-976), before `macro drop HON_SB_SPEC …` (:979), in HON-30's form (`_hon_sb_setup`, `r(match)`, `_hon_has`). Append PYF-01 and PYF-02 to `test/test_program_coverage.cscript` after PC-31, the script's last case block, directly before the closing `local pep_failed` (:1382), where `_pep_fail`, `_pep_vec`, `_pc_setup` and `local pep_tmp` are still defined, in the PEP form (`capture noisily { … }` then `if _rc _pep_fail PYF-0n`, `_pep_vec`, `_pep_match`, `_pc_setup`, `_pc_said`; PYF-01 copies PEP-08 (:1078-1108) with its own directory). In `test/test_setup_python_gate.cscript`, add the floor block of the stubs after the Q27 block (before `if `fail'`, :182), and rewrite the comment at :136-143 ("the floor is 3.13" becomes "comparator inputs with a 3.13 want; the declared floor is read below"). Then, at this tree (commit A), run the three scripts through the driver and `python3 -m pytest test/test_version_floor.py test/test_setup_pep668.py -q -n0 -p no:cacheprovider -rf`. Also re-run "Stata truth" probe 1. Write `$S/05-P1.33-2-failure.txt`: commit A's sha, each failing pytest node with its first assertion line, the HON-31/32 and PYF-01/02 failure lines, the python_gate `FAIL:` lines and the probe output. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c 'HON-31\|HON-32\|PYF-01\|PYF-02' "$S/05-P1.33-2-failure.txt"` is at least 4; `grep -c 'test_the_python_floor_is_the_lowest_baseline_python\|test_below_the_floor_the_guidance' "$S/05-P1.33-2-failure.txt"` is at least 2; no PASS line for HON-31, HON-32, PYF-01 or PYF-02 appears in the driver logs.]]></verify>
  <done>Every commit B regression case was shown failing on commit A's tree, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="05-13">
  <name>Lower the declared floor in Stata</name>
  <files>dash_setup.ado, dash.ado, dash.pkg</files>
  <action><![CDATA[
    In `dash_setup.ado`:
    - set `_dash_pymin`'s `return local pymin` to `FLOOR` and rewrite its docstring;
    - rewrite the comment at :38-47;
    - replace line :100 with TR-05.10's text;
    - change `_dash_setup_guide`'s `args` to `kind ensurepip managed pyok pymin` and update its header comment (:989-996);
    - append `"`pyok'" "`c_pymin'"` to each of its seven calls (:228, :239, :301, :304, :330, :336, :414). Find them with `grep -n '_dash_setup_guide ' dash_setup.ado`, which must show 7 calls plus the definition.

    Keep `version 19` and every other line as S03 left them. In `dash.ado`, `_dash_require_python`'s message `"Python 3.13+: {help python}"` becomes `"Python <FLOOR>+: {help python}"`. In `dash.pkg`, `Python 3.13+` in the `Requires:` line becomes `Python <FLOOR>+`. Nothing else changes on that line.
  ]]></action>
  <verify><![CDATA[`grep -c '_dash_setup_guide [a-z]* .*pyok.*c_pymin' dash_setup.ado` prints 7; `python3 -m pytest "test/test_version_floor.py::TestTheFloorIsTheTestedBaseline" -q -n0 -p no:cacheprovider -k "lowest or declares_the_stata"` passes.]]></verify>
  <done>dash_setup declared the measured floor, passed whether the linked Python met it to every guidance call, and dash's own message and package description named the same floor.</done>
</task>

<task type="auto" id="05-14">
  <name>Stop the venv advice loop</name>
  <files>dash_setup_lib.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `dash_setup_lib.py`, add `below_floor_message(exe, pymin, kind)` after `nopip_message` (:452-467), per TR-05.11. Its docstring cites WP-30 P1.33 and the loop it closes. Use 3.8-parseable syntax and only `%` formatting. In `stata_guide` (:592-611), read `pyok` and `pymin` with `sfi.Macro.getLocal`. When `pyok == "0"` and `version_tuple(pymin)` is non-empty, call `below_floor_message(exe, pymin, kind)`; otherwise keep the two existing branches exactly. Add the `below_floor_message` entry of TR-05.18 under the S05 anchor at the end of `SETUP_FUNCTIONS` in `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_pep668.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes (including `TestModuleShape`); through the driver, `test_program_coverage.cscript` prints `PYF-02 PASS`, `PEP-01 PASS`, `PEP-04 PASS` and `PEP-15 PASS`.]]></verify>
  <done>A managed or pip-less Python below the floor was told to link a newer Python, with no venv() suggestion and no hint command, while every Python at or above the floor got the guidance it got before.</done>
</task>

<task type="auto" id="05-15">
  <name>Guard interpreter-specific code if found</name>
  <files>dash_render.py, test/test_version_floor.py</files>
  <action><![CDATA[
    Only if `$S/05-floor.txt` lists class (a) items. For each, make the TR-05.15 change in the function named, in place, after `gitnexus impact <function> -d upstream -r dash` (report any HIGH or CRITICAL before editing). Add a regression test to `test/test_version_floor.py`, class `TestTheFloorInterpretersBehaveAlike`. It reproduces the older interpreter's behaviour by monkeypatching and fails without the guard on 3.13, and is saved red to `$S/05-P1.33-2-failure.txt` before the edit. Re-run that Python's failed legs through the queue (as 05-07) and record their lines in `$S/05-matrix.txt`. If there are no class (a) items, change nothing and write `05-15: no interpreter-specific code found` to `$S/05-notes.txt`.
  ]]></action>
  <verify><![CDATA[Either `grep -c '05-15: no interpreter-specific code found' "$S/05-notes.txt"` prints 1, or the guard's test passes, the re-run legs end `exit=0`, and `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Any behaviour that differed under the floor Python was guarded and pinned, or the record stated that none was found.</done>
</task>

<task type="auto" id="05-16">
  <name>Fill the S05 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Between S01's `S05 start` and `S05 end` lines, inside the `WP30_ONLY` gate, write PYF-03 and PYF-04 per TR-05.16. PYF-03:
    ```stata
    capture program list _dash_pyver_ok
    if _rc quietly do "../dash_setup.ado"
    _dash_pymin
    local s05_min "`r(pymin)'"
    python: import sys, sfi; sfi.Macro.setLocal("s05_ver", "%d.%d.%d" % tuple(sys.version_info[:3]))
    _dash_pyver_ok "`s05_ver'" "`s05_min'"
    local s05_ok = r(ok)
    _w30_expect PYF-03 "(`s05_ok' == 1)" "Python `s05_ver' is below the declared floor `s05_min'"
    _w30_done PYF-03 "Python `s05_ver' is at or above the declared floor `s05_min'"
    ```
    PYF-04 runs `subprocess.run([sys.executable, "-P", "-c", "import sys; print(int(sys.flags.safe_path))"], capture_output=True, text=True, timeout=60)` in one `python:` line, sets a local to `"<rc> <stdout>"`, checks it equals `0 1` with `_w30_expect PYF-04 …` and closes with `_w30_done PYF-04 "…"` (TR-01.10.4: no `assert`, which would stop every later block; the tally prints `PYF-0n PASS: …` and counts the case, so `WP30_ONLY=S05` ends `ALL CHECKS PASSED`). No Python line holds a brace, and no helper goes inside another section's block.
  ]]></action>
  <verify><![CDATA[`WP30_ONLY=S05` through the driver on `test_wp30_truth.cscript` prints `PYF-03 PASS: Python 3.13.9 is at or above the declared floor <FLOOR>`, `PYF-04 PASS` and `test_wp30_truth: ALL CHECKS PASSED`; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes with its pins unchanged.]]></verify>
  <done>The certification suite checked that the interpreter it ran under met the declared floor and could start the served app's child as dash serve does.</done>
</task>

<task type="auto" id="05-17">
  <name>State the floor in the help</name>
  <files>dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
    Apply TR-05.14 with the measured values from `$S/05-made.txt` and the date of 05-07. In `dash.sthlp`, edit only the Dependencies paragraph's Python line and add its one sentence (R3; S03's Stata line is kept as it is). In `dash_setup.sthlp`, edit :41-46, :113-117, :127 and :150-152, and add the sentence to the PEP 668 section after "which leaves the managed Python as it is:" and the venv() example paragraph. Name no tool or vendor, and write no path that exists only on this machine.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_version_floor.py test/test_help_claims_8.py test/test_help_examples.py -q -n0 -p no:cacheprovider` passes; through the driver, `test_setup_python_gate.cscript` prints `ALL TESTS PASSED` (its "dash_setup.sthlp states the same minimum" check included).]]></verify>
  <done>Both help files stated the measured floor, what it was measured on, and that a Python below it is pointed at a newer Python instead of a private environment.</done>
</task>

<task type="auto" id="05-18">
  <name>Re-run the Stata legs and floor certification</name>
  <files>none</files>
  <action><![CDATA[
    Re-run 05-08's Stata leg for py311 and py312 on this tree, and copy every `GATE` line to `$S/05-stata-legs-B.txt`. Judge each log by `grep` for AC-05.3's six lines; each must hold all six, including `venv-setup2 rc=0 linked=1`. Then run the one floor certification run (D-05a) in the background: `DASH_PYTHON_EXEC=<scratch>/venv-s05-<floor py>-stata/gatevenv/bin/python <scratch>/full_suite_queue.sh "$WT" "$S/05-cert-floor.log" cert`, and wait for `exit=`. A script that fails is re-run once, alone, through a driver whose first line is `python set exec "<that python>"`; record both results in `$S/05-cert-floor.txt`. Re-run "Stata truth" probe 1 at this tree and append its output to `$S/05-cert-floor.txt`. Compare the rc hash with `$S/05-rc-before.txt` and `~/.conda/environments.txt` with its copy.
  ]]></action>
  <verify><![CDATA[For each of the two logs, `grep -c 'GATE venv-link rc=0\|GATE venv-python rc=0 ver=\|GATE venv-setup2 rc=0 linked=1\|GATE venv-saved rc=0 html=1\|GATE venv-served rc=0 health=1\|GATE venv-done' <venvdir>/floor_stata_leg.log` prints 6; `$S/05-cert-floor.log` ends with `exit=0`, its runner summary shows no FAIL, and it holds `Python linked for this run only:` and `PYF-03 PASS: Python <FLOOR>.`; the probe prints `pymin=<FLOOR>`; `diff <(shasum ~/.stata19/console/stata19.rc) "$S/05-rc-before.txt"` prints nothing.]]></verify>
  <done>A Stata session linked to each measured Python passed dash_setup, venv(), a saved page and a served app, and the whole certification suite passed with Stata linked to the floor Python for that run only.</done>
</task>

<task type="auto" id="05-19">
  <name>Close the entry and make commit B</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Close the P1.33 entry in place in `BUGS.md`. Its title is the one S01 wrote, the key of `WP30_OPEN["P1.33"]`. Change `- [ ]` to `- [x]` and replace its Resolution with `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.33).` followed by the text of Notes "Resolution text", filled with the measured values. Delete the `"P1.33": …` key line from `WP30_OPEN` in `test/test_tracking_documents.py`, and nothing else there. Replace `<!-- WP-30 P1.33 -->` in CHANGELOG.md's `### Requirements` in place with Notes' "CHANGELOG line", filled; add nothing elsewhere (R4). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Run the changed pytest files (AC-05.1). Through the driver, run `test_setup_honesty.cscript`, `test_program_coverage.cscript`, `test_setup_python_gate.cscript`, and `test_wp30_truth.cscript` with `WP30_ONLY=S05`. Run `git -C "$WT" merge --no-edit main`, expecting `Already up to date.`. Run one full suite through the queue to `$S/05-full-2.log`, 0 failed. Stage only the files of tasks 05-11 to 05-19 (G6). Write `$S/05-msg-B.txt` in the Commit boundary form, with:
    - `$S/05-P1.33-2-failure.txt`;
    - `$S/05-stata-legs-B.txt` and `$S/05-cert-floor.txt`;
    - the `Regression:` lines, the `Flipped:` lines from `$S/05-B-flips.txt`;
    - `BUGS.md: "<title>" (closed)`.

    Check G7, confirm the branch prints `wp30-s05`, commit, then check G7 again. Report both shas and both message files to the orchestrator for landing (E2).
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-30 P1.33 -->' CHANGELOG.md` prints 0; `python3 -c "import sys;sys.path.insert(0,'test');import test_tracking_documents as t;print('P1.33' in t.WP30_OPEN)"` prints `False`; `$S/05-full-2.log` ends `exit=0`; `git -C "$WT" log -2 --format=%s | grep -c '(WP-30 P1.33)'` prints 2; `git -C "$WT" log -2 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>P1.33 was closed in BUGS.md naming existing tests, its CHANGELOG marker became the measured Requirements line, and the section's second green commit was ready for landing.</done>
</task>

## Section completion criteria

- `_dash_pymin` is the lowest Python at which the six pytest legs, the Stata venv-link leg and one full certification run passed (3.11 expected). The dash.ado message, `dash.pkg`, both help files and CHANGELOG Requirements state it, and `test_the_python_floor_is_the_lowest_baseline_python` pins it to `_BASELINES`.
- `dash_setup` accepts 3.11 and 3.12 with every package present (HON-31, HON-32). `venv()` works from 3.12 (PYF-01). On a managed or pip-less Python below the floor, the guidance names the floor, suggests no `venv()` and leaves `r(hint_cmd)` empty (PYF-02, `test_stata_guide_below_the_floor_suggests_no_venv`).
- `scripts/floor_matrix.sh`, `make test-floor`, `scripts/floor_stata_leg.do`, the `DASH_PYTHON_EXEC` link and the pins files exist, are tested, and name no interpreter, `arch` prefix or maintainer path.
- No release-gate floor leg exists (ratification item 25, "Manual only"): `make gate`, `run_release_gate.sh` and `release_verdict.py` are unchanged by this section, and `scripts/floor_matrix.sh`'s header records the manual re-measure procedure.
- Nothing was installed outside `<scratch>/venv-s05-*`. `stata19.rc` and `~/.conda/environments.txt` are as they were.
- Two green commits exist on `wp30-s05`, both ending `(WP-30 P1.33)`:
  - commit A changed no product file;
  - commit B closed the entry in place, deleted its `WP30_OPEN` key and replaced its marker.
- No runner block, hygiene pin, other section's truth block, copy-list entry or tracking document beyond BUGS.md and CHANGELOG.md was edited.

## Notes

- **Line numbers are `c96facd`'s.** S02 and S03 land first and move lines in dash_setup.ado (S03's `version 19` sweep and `_dash_statamin`), `dash.pkg`, the help Dependencies paragraphs, the Makefile and `run_all_cscripts.do`. Find each edit by its quoted text. In dash_setup.ado, `_dash_setup_guide`'s seven calls are the authority, not their line numbers.
- **Timing bounds.** A bound is a test of complexity, not of an interpreter's speed. Example: test_qualifier_logic.py:821 timed the translation under tracemalloc, and BUGS.md:2315 records 11.1 s against 10 s on 3.13.
  - If a timing test fails on 3.11 or 3.12, first re-run that node once in isolation with `-n0` (E6).
  - If it fails again, measure the same node under 3.13 and the older Python. A bound may move only to keep the same ratio to the 3.13 measurement, with a `Flipped:` line giving both measurements.
  - A slowdown that is pathological (more than twice the 3.13 time) is a class (a) item, not a bound to widen.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The scripts then exit 222, and a SKIP is not a pass. Use `stata_slot.sh`, which keeps sessions at three, and compare the rc hash around every run.
- **Session-only links.** `python set exec` must be the session's first Python act:
  - `floor_stata_leg.do` starts no Python before `release_gate_venv.do`'s venvuse link;
  - the runner's link paragraph sits before any `python:` and before the first `do`;
  - a driver that re-runs one cscript under the floor Python puts `python set exec` on its first line.
- **Shared files within batch 2 (index R1-R6).**
  - R1: S05's truth block; HON-31/32 appended after PEP-19 in `test_setup_honesty.cscript`; PYF-01/02 after PC-31 (before :1382) in `test_program_coverage.cscript`; in-place flips of PC-16, PC-17, PEP-13, PEP-14 and HON-30.
  - R2: `SETUP_FUNCTIONS` under the S05 anchor only; no copy-list entry.
  - R3: dash.sthlp Dependencies and the `dash_setup.sthlp` paragraphs of TR-05.14 only.
  - R4: the one Requirements marker.
  - R5: the one entry and the one key line.
  - R6: no new Stata program and no option key.

  `len(with_probes) == 13` (test_cscript_hygiene.py:322) does not move: no captured `python:` import probe is added.
- **For S25.**
  - The floor is `<FLOOR>`. dash.ado's `_dash_require_python` message holds the literal `Python <FLOOR>+`, which S25 replaces with its constant (A123).
  - S25's guard must refuse below `<FLOOR>` before `dash serve` launches the `-P` child.
  - `TestTheFloorAdmitsTheServedLauncher` is the pin to keep when S25 adds `_DASH_MIN_PYTHON`.
- **For S41.**
  - The pins files are `name==version` lines under a `#` header, refused if any line is an option or URL; S41 keeps that rule when it adds the window.
  - `_BASELINES` now has six entries, each with bokeh 3.8 or 3.9, which S41's `TestTheWindowIsDeclaredOnce` must accept.
  - Package-window findings from the fresh legs are listed in `$S/05-triage.txt` class (d), quoted in commit A's body.
- **Resolution text** (05-19; fill `<…>`): "dash_setup's floor (_dash_pymin) is <FLOOR>, the lowest Python at which both pytest suites (the stata and dev pins, and a fresh resolve as dash_setup installs), the Stata venv-link leg (a saved page, a served app answering /health, dash_setup, venv()) and the full certification run passed, measured <ddmonyyyy> under arm64 Python <3.11.x> and <3.12.12> in scratch environments (scripts/floor_matrix.sh, make test-floor, scripts/floor_stata_leg.do). The dash.ado _dash_require_python message, dash.pkg, dash.sthlp, dash_setup.sthlp and CHANGELOG state it. On a managed or pip-less Python below the floor, stata_guide (dash_setup_lib.py, new below_floor_message) names the floor and suggests no venv(); r(hint_cmd) is empty. test/conftest.py holds a baseline per measured stack, and test/requirements-stata.txt and test/requirements-dev.txt their exact pins. The floor is re-measured by hand when a pin or minimum changes (the procedure in scripts/floor_matrix.sh's header); the release gate has no floor leg. No renderer change: the served app's -P launch flag needs 3.11, which the floor meets. Pinned by test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_the_python_floor_is_the_lowest_baseline_python, test/test_version_floor.py::TestTheFloorAdmitsTheServedLauncher::test_the_launch_flags_need_no_newer_python_than_the_floor, test/test_setup_pep668.py::TestStataEntryPoints::test_stata_guide_below_the_floor_suggests_no_venv, test/test_strict_mode.py::TestTheBaselines::test_each_older_python_runs_both_pin_sets, test/test_floor_matrix.py::TestTheScript::test_a_dry_run_prints_the_exact_commands, test/test_setup_honesty.cscript HON-31, HON-32, test/test_program_coverage.cscript PYF-01, PYF-02. Residual, deferred (WP-30): Python 3.10 and older (numpy 2.3 needs 3.11); Windows patch levels of 3.11 without the os.mkdir 0o700 fix (platform package, P1.34.6)."
- **CHANGELOG line** (05-19, in place of the marker): "- Python <FLOOR> or later (was 3.13). Both test suites, with the pins they run under and with a fresh install as `dash_setup` resolves it, pass under Python <FLOOR> and 3.12, and a Stata session linked to either builds and serves dashboards; the whole certification suite passes with Stata linked to <FLOOR> (measured <ddmonyyyy>). numpy 2.3 needs Python 3.11, so nothing older is supported. `dash_setup` no longer refuses 3.11 and 3.12. On a Python below the minimum it says to link a newer Python instead of suggesting `dash_setup, venv()`, which refused too. (WP-30, P1.33)"
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md H4** (:1529): H4g is closed by S05's commit B (the Python half of "declared dependency minimums are untested"); H4b-e are S41's. The Tracked line names both commits once S41 lands.
  - **GAPS2.md K2** (:1811): its WP-28 residual "no interpreter or bokeh below the floor is run by any test" is closed for Python by S05 (the floor matrix, measured once in WP-30 and re-run by hand per `scripts/floor_matrix.sh`'s header; no release-gate leg, ratification item 25) and for bokeh by S41.
  - **DROPIN-REMAINING.md:167** (P1.33): closed, commit B's sha. The Decisions bullet "Should Python stay at 3.13 or return to 3.11 (P1.33)?" gets "Decided for WP-30: M3, measured; floor <FLOOR>".
  - **ROADMAP:**
    - the WP-30 P1.33 row;
    - the deferred platform package gains the Windows 3.11 patch-level caveat (CPython's os.mkdir 0o700 fix, CVE-2024-4030; dash_render.py:2074, 2465 rely on it; register P1.33.3/A124);
    - P3.9 notes that `test/requirements-stata.txt` and `test/requirements-dev.txt` exist (the matrix pins only; xdist, node and Chrome declarations stay P3.9's, IR-16);
    - the manifest's item-33 residual is filed: "Python 3.10 and older, and any version above the floor that the matrix does not pass".
  - **CHANGELOG (S58.4):** the older Requirements lines at CHANGELOG.md:609-611 ("Python 3.13 or later … Was 3.8") and :619-623 ("The declared minimums are the tested ones -- Python 3.13, …") are superseded by S05's line and are consolidated with it.
  - **AGENTS.md invariant:** "the declared Python floor is `_dash_pymin`; every `_BASELINES` entry is a stack both suites pass under and the floor is the lowest of their Pythons (test_version_floor); a new floor is measured by hand with `scripts/floor_matrix.sh` and `make test-floor` (the procedure is the script's header; `make gate` does not re-test it), never assumed."
  - **PLAN K15:** record the outcome (the floor, the Pythons measured, and whether any class (a) guard was needed).
