# Section 36-01: Use the Python Stata finds or the user sets

> Part of: WP-36 (Python discovery and environment) · Items: plat:PT-1 · Risk: red · Batch: 36.1 · Depends on: none · Blocks: 36-04 · Tasks: 4, 1 commit · Case-id prefix: Q3601

## Overview

**What is wrong today.** The audit (package 2, plat:PT-1, audit :88-90 and appendix :2250-2255): "dash and dash_setup refuse a Python that Stata found by itself (python_exec never set), and the remedy loops back to the same refusal." Measured with a fresh HOME: `c(python_exec)` is empty until `python set exec` is typed, even after a `python:` line has run with the interpreter Stata found itself (`/usr/local/bin/python3`, 3.14.6). `_dash_require_python` (dash.ado:307-319) then stops every dash command but `dash clear` with "dash: Python is required but is not available to Stata." r(198), and `dash_setup` (dash_setup.ado:96-107) stops with "Python is not available to Stata." r(198) and "Unmet: Python (not linked to Stata)". Both tell the user to run `dash_setup`, which refuses the same way. The whole test harness makes the same decision: 50 cscripts and `test/cert_svg.do` skip r(222) when `c(python_exec)` is empty, 65 `scripts/extract_*.do` exit 601, 222 or 198, `test/run_all_cscripts.do:235-238` announces that the Python scripts will skip, and `scripts/stata_python_exec.sh` (used by `make test`, Makefile:45, and `scripts/run_cert_suite.sh:59`) fails.

**What will be true after.** Ruling M8 / conflict C5: there is no pre-check of Python. When `c(python_exec)` is empty, dash and dash_setup go straight to the `python:` lines they run anyway, so Stata picks its own Python; if that Python cannot start, Stata's own message is shown and is followed by dash's advice; the command stops with Stata's return code. No `python query` probe is added anywhere. The harness follows the same rule: no script skips or exits for want of a `c(python_exec)` value, `stata_python_exec.sh` reports the Python Stata actually runs, and a release-tier pytest that starts a console Stata with a fresh HOME through `scripts/stata_slot.sh` (one slot; DECISIONS A-8) proves dash and dash_setup work with nothing set.

**Reconciling the guards.** The hygiene rule in test/test_cscript_hygiene.py:442-485 and the maintainer's standing rule ("probe c(python_exec), never execute Python just to probe") both exist to stop one failure: a script or command concluding "no Python" from running Python. Under M8 nothing decides availability at all. `c(python_exec)` stays the one place dash reads which Python is *set* (for its messages); Python is run only for work dash needs anyway (`_dash_require_deps`'s version and package check, the render). So the parts of the guards that forbid `python query`, forbid deciding from a bare `capture python: pass`, and require `python_exec` to appear in each ado file all stay; the parts that require a script or ado file to *refuse* on an empty `c(python_exec)` are flipped with that reason.

**Test order and commit rule.** One item, one commit. Task 36-01-01 writes every regression test (the release-tier fresh-HOME file included) and the two by-value certification cases and saves the failure text without committing; 36-01-02 changes dash.ado, dash_parse.mata, dash_setup.ado and dash_setup_lib.py; 36-01-03 changes the harness; 36-01-04 flips the pins, edits the help, runs the section's tests and the changed cscripts, and makes the one commit ending `(WP-36 plat:PT-1)`.

### Section decisions

- **D-36-01.a The refusal is removed, the program stays (DECISIONS A-8).** `_dash_require_python` keeps its name, its 19 call sites and its place before every `python:` site (test_env_guards.cscript ENV-12 and test/test_dependency_guards.py keep reading "the guard comes first"), as an empty program whose header comment documents it as the hook every `python:` site passes: an empty `c(python_exec)` means Stata finds its own Python on the first `python:` line. `_dash_python_ok` is unchanged (a pure reader of the setting, ENV-01..04 unchanged) and is now used for wording only.
- **D-36-01.b Stata's own failure, then dash's advice.** `_dash_require_deps` keeps its first `capture python:` version probe (the first call of a session can fail where Python works); its retry becomes `capture noisily python:` so a real failure prints Stata's own message, and a new pure program `_dash_python_failed <rc> "<c(python_exec)>"` prints dash's advice and exits with that rc (198 when the rc read is 0). The decision is still made from the value `_dd_v`, never from `_rc`; `_rc` is read once, only to pass Stata's code on.
- **D-36-01.c The Python dash names.** The version probe also sets `_dd_x` to `sys.executable`; every message of `_dash_require_deps` names `c(python_exec)` when it is set and `_dd_x` when it is empty ("the Python Stata found, <path>"). dash_setup_lib's `_linked()` falls back to `sys.executable` when `c(python_exec)` is empty, so `dash_setup`'s pip line names the interpreter Stata is running.
- **D-36-01.d The harness gates go.** The 50 cscript skip gates, cert_svg.do's gate, the five in-script `if c(python_exec) != ""` branches and the 65 extract-script gates are removed (not replaced by another probe). A script on a machine with no Python now fails where it skipped; `scripts/cert_verdict.py` already fails a run with any skip, so no verdict changes. The pip-line oracles that read `c(python_exec)` fall back to `sys.executable` exactly as dash_setup_lib does.
- **D-36-01.e The fresh-HOME case is a release-tier pytest (DECISIONS A-8).** test/test_python_discovery_fresh_home.py (`pytestmark = pytest.mark.release`) starts console Stata only through `sh scripts/stata_slot.sh <scratch> <do-file>` -- one of the three slots, waited for like any other run -- with `HOME` set to an empty temporary folder, `PIP_NO_INDEX=1`, `PIP_FIND_LINKS=<empty folder>` and no `DASH_PYTHON_EXEC`; no certification script starts a nested Stata. The found Python's `pip list` is read before and after with `subprocess.run([exe, "-m", "pip", "list", "--format=freeze"], ...)` (an argument list, no shell: REVIEW R2-38), so nothing is ever installed and no path reaches a shell. test/test_wp36_truth.cscript gets no S01 block (BRIEF: an item whose Stata comparison is not a certification case adds no block); the by-value cases Q3601-6..8 go in test/test_env_guards.cscript (R1).

## Risk: [red] -- every dash command and the whole certification harness pass through the code this changes

**Why.** `_dash_require_deps` runs before every subcommand but `dash clear`; the harness edit touches about 120 files; a mistake either blocks every command or makes the suite skip or fail everywhere.

**Risk factors.** 1. A `python:` failure that is not the first call (a genuinely broken Python) must still stop with a clear message, not a traceback. 2. The mechanical gate rewrite can delete code that is not a gate. 3. The hygiene and dependency-guard pins encode the old rule in several places (one missed pin turns `make test-all` red). 4. The fresh-HOME run must hold one of the three Stata slots, never a fourth session, and must not hang the release tier. 5. dash_setup must never install into the Python a fresh HOME finds.

**Mitigation.** 1. TR-36-01.2's two-step probe, Q3601-6/7 (they drive `_dash_python_failed` directly) and the ENV-17..19 flips (they drive it through the dispatcher); the flipped ENV-06/07 show that `_dash_require_python` refuses nothing. 2. The rewrite is a script with exact regexes and a recorded before/after count per file (TR-36-01.5), and `git diff --stat` must list only the recorded files. 3. The pin list in Evidence is complete as of 090d928; task 01 re-greps and records it. 4. Every Stata run of the fresh-HOME test goes through `scripts/stata_slot.sh` (which waits for a free slot) under `subprocess.run(..., timeout=900)`; a timeout fails the test with the log path. 5. `PIP_NO_INDEX=1`, an empty `PIP_FIND_LINKS`, a before/after `pip list` assertion run with the same fresh HOME, and an assertion that the fresh HOME holds no `site-packages` folder afterwards.

## Dependencies

- **Depends on:** none in WP-36 (WP-33..35 have closed; test_wp36_truth.cscript exists from W0).
- **Blocks:** 36-04 (its Dependencies text describes the behaviour this section makes true; 36-04's plat:PT-11 cycle also rewrites the `{ul:Python 3.11+}` item, dash.sthlp:6709, which this section leaves alone -- REVIEW R2-43).
- **Parallel batch:** 36.1 with 36-02 and 36-03; merge order 36-01, 36-02, 36-03.
- **Can run with:** 36-02 (dash_render.py figure backend only) and 36-03 (dash.ado `_dash_register_graph`, dash_parse.mata function-point accessors, test_parser.cscript FX-07/08): this section edits dash.ado's Python programs (:270-410), dash_setup.ado, dash_setup_lib.py and the harness gates. Shared files: test_parser.cscript (this section edits the branches at :3517 and :3743, 36-03 the FX cases at :3295-3365), test_wp36_truth.cscript (this section removes only the gate at its top; 36-02 and 36-03 append S02 and S03), and `_dash_require_mata`'s `_needed` list and the dash_parse.mata `*!` header index (both 36-01 and 36-03 add names): this section adds its name on one new continuation line directly before the list's last line (dash.ado:506 at 090d928) and its `*!` entry after the `_dash_say` entry; 36-03 adds its line directly after the line holding `_dash_fn_spec_tail` (:486) and its entries after the `_dash_fn_spec_tail` entry, so the two insertions never meet and neither touches an existing line (REVIEW R2-22).

## Evidence

### The refusal (dash.ado, re-read before editing)

```stata
290 program define _dash_python_ok, rclass
...
294     return scalar ok = cond(`"`probe'"' == "", 0, 1)
307 program define _dash_require_python
309     _dash_python_ok `"`c(python_exec)'"'
310     if r(ok) != 1 {
313         display as error "dash: Python is required but is not available to Stata."
314         display as error "      Run {cmd:dash_setup} first, or link Stata to " ///
316         exit 198
```
Comment :270-288 explains the rule ("`capture python query' and `capture python: pass' both run Python"). Callers of `_dash_require_python`: dash.ado:209 (`_dash_py_tidy`), 355 (`_dash_require_deps`), 661, 7413, 7438, 7587, 7618, 7723, 7763, 7792, 7811, 11813, 11875, 13241, 13439, 13870. `_dash_require_deps` (:353-400): version probe `capture python: import sys; ... setLocal("_dd_v", ...)` :357, retry :361, failure message :364-369 naming `c("python_exec")`, floor check :371-385, package check :391-398 naming `c("python_exec")`. Dispatcher :100-105 calls `_dash_require_deps` for every subcommand but `clear`. `_dash_require_mata`'s `_needed` list runs from :469 to its last line :506 (`_dash_abs_path _dash_graph_names ... _dash_at_isnum`, no `///`).

### dash_setup (dash_setup.ado)

`:88-107`: comment, then `if `"`c(python_exec)'"' == "" { display as error "Python is not available to Stata." ... local fail_items ... Python (not linked to Stata) ... exit 198 }`. `_dash_setup_pystart` (:757-768): two `capture python:` lines setting `pyver`. Failure display :115-128 prints `c("python_exec")`. dash_setup_lib.py `_linked()` :829-834 returns `(resolve_exe(raw, pwd), raw)`; `resolve_exe` :155-166 returns None for an empty value; callers :848, :882, :928, :961, :983, :1041. dash_render.py `_dash_child_python()` :72987 already falls back to `sys.executable` (no change).

### twoway's rule

`help python` / [P] p.pdf "Configuring Python": with no `python set exec`, Stata searches for a Python on first use; `c(python_exec)` reports only the setting. Measured by the audit's verifier: `quietly python query` gives `r(execpath)=/usr/local/bin/python3`, `r(initialized)=0` with an empty `c(python_exec)`. On this machine `/usr/local/bin/python3` is Python 3.14.6 with none of numpy, pandas or bokeh (checked 20oct2026), so in a fresh HOME dash must reach its package check and name that Python.

### The harness

- Skip gates, exact shape (50 cscripts and test/cert_svg.do:69-72; counted at 090d928 by the regex of TR-36-01.5): `if "`c(python_exec)'" == "" {` / `display as error "SKIP: Python not available."` (44), `"SKIP: no Python is linked to this Stata."` (6), `"SKIP: Python not available (ECH-09 needs dash_render.py)."` (1) / `exit 222` / `}`.
- In-script branches: test_parser.cscript:3517 (`if `"`c(python_exec)'"' != "" & !`bad' {`), :3743; test_option_surface.cscript:965; test_statistical_options.cscript:543 (else branch :635-638 prints `UN-02 SKIP`, `UN-03 SKIP`), :872 (else :911 `SO-74 SKIP`); test_setup_python_gate.cscript:182-188.
- pip-line oracles reading `c(python_exec)`: test_setup_honesty.cscript:532, :846, :897, :962, :1011; test_program_coverage.cscript:178; test_setup_python_gate.cscript:185.
- Extract scripts: 65 `scripts/extract_*.do` gate the same way, with one of three messages ending `(c(python_exec) is empty)` and `exit 601`, `exit 222` or `exit 198` (extract_lpoly_rot_truth.do:44-47, extract_lpolyci_truth.do:44-47, extract_style_files_truth.do:48-51, extract_twoway_command_form_truth.do:53-56 among them); scripts/extract_axis_truth.do:114 says so in a comment.
- test/run_all_cscripts.do:231-238 (comment and NOTE); :54-63 (DASH_PYTHON_EXEC, unchanged).
- scripts/stata_python_exec.sh: writes `c(python_exec)` to pyexec.txt; exits 1 when it is empty.
- scripts/stata_slot.sh: `cd "$dir" && STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do "$dofile"` while holding `/tmp/dash-stata-slot-<n>.d`; it passes the caller's environment (HOME included) on unchanged.
- The WP truth template `test/templates/wp_truth_template.cscript` (33-01) and test_wp29/30/31/33/34/35/36_truth.cscript carry the gate (each W0.2 of WP-33..36 added one).

### Pins that encode the old rule (flip, never delete)

- test/test_env_guards.cscript: ENV-06 (:390-392, stubs `_dash_python_ok` to 0, expects r(198)), ENV-07 (:394-395, message names dash_setup), ENV-17..19 and PF-10 (:395-510, expect r(198) and "Python is required but is not available" with the stub). ENV-01..05, 12..16 stay.
- test/test_cscript_hygiene.py: `test_every_script_that_skips_for_python_is_read` (:304-321, `len(names) == 51` at 090d928, moved by each W0.2 since); `test_a_script_that_needs_python_says_so_through_the_setting` (:393-411, parametrised over scripts matching `_SKIPS_FOR_PYTHON` :174); the WP-30/WP-31 scaffold-order tests (`TestTheWp30TruthScript`, `TestTheWp31TruthScript`, :1150, :1278-1321) and 33-01's `TestTheWpTruthScripts::test_the_scaffold_is_in_order`, which list `SKIP: Python not available.`; the docstrings of the module (:1-23) and of `TestTheShippedAdoFilesFollowTheSameRule` (:442-455).
- test/test_dependency_guards.py::...::test_the_guard_decides_from_values (:775-783: every `python:` line of `_dash_require_deps` starts `capture python:` and no `_rc` appears).
- test/test_help_claims_8.py::TestDashSetupHelpMatchesTheAdo::test_availability_is_the_setting_not_python_query (:1766-1797: asserts `if `"`c(python_exec)'"' == ""` is in dash_setup.ado).
- test/test_setup_pep668.py:677 (its fake sfi maps only `c(python_exec)` and `c(pwd)`): read it; it gains `sys.executable` only if `_linked()`'s fallback reaches it.

## User stories

- US-36-01.1 As a Stata user with an existing twoway command, I want `dash scatter mpg weight` to run on a Stata that found Python by itself, so that I never have to type `python set exec` for a Python Stata already uses.
- US-36-01.2 As a Stata user evaluating dash, I want `dash_setup` to check and complete the Python Stata uses, so that its remedy does not loop back to the same refusal.
- US-36-01.3 As a Stata user whose Python cannot start, I want Stata's own error followed by what to do, so that I can fix the link.
- US-36-01.4 As the maintainer, I want the test suite to run on a machine where Stata finds its own Python, so that a skipped or failed run never hides that case.

## Business requirements

- BR-36-01.1 With nothing set (`c(python_exec)` empty) and a Python Stata finds, every dash command reaches its normal work; no message says Python is unavailable.
- BR-36-01.2 With nothing set, `dash_setup` reports the found Python's version and continues to the package steps, naming that Python in every pip line.
- BR-36-01.3 When the Python cannot start, the user sees Stata's own message, then dash's advice naming `python set exec` (or the linked path) and `dash_setup`, and the command stops with Stata's return code; nothing is written.
- BR-36-01.4 No shipped file or test script runs `python query` or decides availability from a bare `python: pass`.
- BR-36-01.5 No certification script or extract script skips or exits because `c(python_exec)` is empty; `make test` finds the Python Stata runs.
- BR-36-01.6 dash.sthlp and dash_setup.sthlp say what happens with nothing set (Appendix B HR-20).

## Technical requirements

- **TR-36-01.1 `_dash_require_python`** (dash.ado:298-319): replace the header comment (:298-306) and body with:
  ```stata
  // ================================================================
  // _dash_require_python  -- the entry every python: site passes
  // ================================================================
  // WP-36 plat:PT-1 (M8, C5): no pre-check.  An empty c(python_exec) means
  // no Python is set and Stata finds one itself on the first python: line
  // (help python), so nothing is refused here.  A Python that cannot start
  // is reported by _dash_require_deps: Stata's own message, then dash's
  // advice (_dash_python_failed).  The program stays where it stands, an
  // empty hook before every python: site (test_env_guards.cscript ENV-12).
  // ================================================================
  program define _dash_require_python
      version 19
  end
  ```
  The comment above `_dash_python_ok` (:270-288) is rewritten to say it reports whether a Python is set, for wording, and decides nothing; its body is unchanged.
- **TR-36-01.2 `_dash_require_deps`** (dash.ado:353-400): line :357 becomes `capture python: import sys; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_v", "%d.%d.%d" % tuple(sys.version_info[:3])); _dash_M.setLocal("_dd_x", sys.executable)`; the retry block :358-362 becomes `if "`_dd_v'" == "" {` / `capture noisily python: <the same line>` / `local _dd_prc = _rc` / `}`; the failure block :363-370 becomes `if "`_dd_v'" == "" {` / `_dash_python_failed `_dd_prc' `"`c(python_exec)'"'` / `}`. Add after `local _dd_v ""` the lines `local _dd_x ""` and `local _dd_prc 0`. In the floor message (:383) and the package message (:394) replace `c("python_exec")` with `_dash_pyname()`, a new Mata function (TR-36-01.3). The Mac processor line moves into `_dash_python_failed`.
- **TR-36-01.3 New code.** dash.ado, after `_dash_require_python`:
  ```stata
  // _dash_python_failed <rc> "<c(python_exec)>"  -- Stata could not start
  // the Python it was given or found (WP-36 plat:PT-1).  Stata's own message
  // has been shown (capture noisily); this adds what to do, and stops with
  // Stata's code (198 when the code read is 0).  Pure in its arguments, so a
  // certification script reaches both wordings (Q3601-6, Q3601-7).
  program define _dash_python_failed
      version 19
      args rc exe
      if "`rc'" == "" | "`rc'" == "0" local rc 198
      _dash_python_ok `"`exe'"'
      if r(ok) == 1 {
          mata: _dash_say("err", "dash: the Python linked to Stata could not be started (", st_local("exe"), ").")
      }
      else {
          display as error "dash: no Python is set, and Stata could not start one it found by itself."
      }
      if strpos(c(machine_type), "Mac") {
          mata: _dash_say("err", "      Stata reports this computer as ", c("machine_type"), "; on a Mac, Stata and Python must be built for the same processor, both arm64 (Apple Silicon) or both x86_64 (Intel).")
      }
      display as error "      Link Stata to a Python that starts here with {cmd:python set exec} ({help python}), then run {cmd:dash_setup}."
      exit `rc'
  end
  ```
  dash_parse.mata, beside `_dash_say`: `string scalar _dash_pyname()` returning `c("python_exec")` when non-empty, else `"the Python Stata found, " + st_local("_dd_x")` when `_dd_x` is non-empty, else `"the Python Stata found"`. Add `_dash_pyname` to `_dash_require_mata`'s `_needed` list on a new continuation line `        _dash_pyname ///` inserted directly before the list's last line (dash.ado:506; R2-22), and one `*!` entry for it directly after the `*!   _dash_say(style, before, value, after)` entry (dash_parse.mata:99-102 at 090d928; re-read). test/program_coverage_map.py (R6): under `"dash.ado"`, after the `_dash_python_ok` entry (:49), `"_dash_python_failed": ("test_env_guards.cscript:Q3601-6", "test_env_guards.cscript:Q3601-7"),`; under `"dash_parse.mata"`, after the `_dash_say` entry (:509), `"_dash_pyname": ("test_env_guards.cscript:Q3601-8",),`. test_program_coverage_map.py::TestTheMapCoversEveryUnit::test_every_unit_has_an_entry fails without either.
- **TR-36-01.4 dash_setup.** dash_setup.ado:88-107: delete the `if `"`c(python_exec)'"' == "" { ... exit 198 }` block and replace the comment with one stating M8 (Stata finds a Python itself when none is set; `_dash_setup_pystart` runs the Python dash_setup checks). `_dash_setup_pystart` (:757-768): the retry becomes `capture noisily python: ...`; it also sets `pyexe` from `sys.executable` (`Macro.setLocal("pyexe", sys.executable)` on both lines) and returns `r(pyexe)`. The failure display :115-118: when `c(python_exec)` is empty print `    (no Python is set; Stata could not start one it found by itself)` instead of the path. The success line that prints the Python (:119 area, "Python .... OK") names `r(pyexe)` when `c(python_exec)` is empty. dash_setup_lib.py `_linked()`:
  ```python
  def _linked():
      """(resolved interpreter or None, c(python_exec) as Stata holds it).
      With no Python set, the one Stata found and is running: sys.executable
      (WP-36 plat:PT-1)."""
      import sfi
      import sys
      raw = sfi.SFIToolkit.macroExpand("\x60c(python_exec)'")
      pwd = sfi.SFIToolkit.macroExpand("\x60c(pwd)'")
      if not raw:
          return (sys.executable or None), raw
      return resolve_exe(raw, pwd), raw
  ```
  test/function_test_map.py's entry for `_linked` (if any) names `test/test_python_discovery.py::TestLinked::test_empty_setting_is_sys_executable`.
- **TR-36-01.5 The harness rewrite** (one Python script run by task 03 from `<scratch>`, never committed): over `test/*.cscript`, `test/cert_svg.do`, `test/templates/wp_truth_template.cscript` and `scripts/extract_*.do`, delete every match of this gate regex (Python `re`, `re.M`; measured at 090d928 it matches exactly once in each of 116 files -- 50 cscripts, test/cert_svg.do and 65 extract scripts -- and no gate escapes it; the truth scripts W0.2 added since carry the same gate and are matched too):

  ```
  ^[ \t]*if `?"?`c\(python_exec\)'"?'? == "" \{\n[ \t]*display as (?:error|text) "(?:SKIP:[^"\n]*|[^"\n]*\(c\(python_exec\) is empty\))"\n[ \t]*exit (?:222|601|198)\n[ \t]*\}[ \t]*\n
  ```

  together with the comment block directly above it when every line of that block mentions `python_exec` or `SKIP` (read each one; keep any comment that says something else). Record per file the count of matches before (must be 1) and after (must be 0) in `<scratch>/36-01-gates.tsv`. Then by hand: test_parser.cscript:3517 → `if !`bad' {`, :3743 → remove the `if`/`}` pair keeping the body; test_option_surface.cscript:965 and test_statistical_options.cscript:543, :872 → remove the `if` and the `else` branches (their SKIP lines), keeping the body; test_setup_python_gate.cscript:182 → unconditional. In each pip-line oracle replace `sfi.SFIToolkit.macroExpand(chr(96) + "c(python_exec)'")` with `(sfi.SFIToolkit.macroExpand(chr(96) + "c(python_exec)'") or sys.executable)` (add `sys` to that line's imports), and `SFIToolkit.macroExpand(chr(96) + "c(python_exec)'")` likewise at test_program_coverage.cscript:178 and test_setup_honesty.cscript:962. test/run_all_cscripts.do:231-238 → replace the NOTE block with `// WP-36 plat:PT-1 (M8): no script decides whether Python is there; with no` / `// Python set, Stata finds one on the first python: line.` (no display). scripts/extract_axis_truth.do:114: drop the sentence about exit 222.
- **TR-36-01.6 scripts/stata_python_exec.sh**: the here-document becomes
  ```stata
  local _pyx `"`c(python_exec)'"'
  if `"`_pyx'"' == "" {
      python: import sys; from sfi import Macro; Macro.setLocal("_pyx", sys.executable)
  }
  file open fh using "pyexec.txt", write text replace
  file write fh `"`_pyx'"'
  file close fh
  ```
  and the header comment says: with no Python set, the interpreter Stata found, read from inside it (M8); never `python query`. test/test_cert_verdict.py:348, :373 keep passing (the script name is unchanged).
- **TR-36-01.7 Help (R3; HR-20).** dash_setup.sthlp step 1 (:41-50) becomes: "1.  Python.  The Python {cmd:dash_setup} checks is the one Stata runs: the one {cmd:python set exec} set ({cmd:c(python_exec)}), or, with none set, the one Stata finds by itself the first time Python runs (see {helpb python}).  Its version is compared with the 3.11 minimum, numerically per component, so 3.10 is correctly newer than 3.9; a version below 3.11 is reported as such and counted as unmet.  Python is started to read its version; a first start that fails is tried once more, and a Python that still cannot be started is reported with Stata's own message and its path, and, on a Mac, a reminder that Stata and Python must be built for the same processor (both arm64 or both x86_64), r(198)." :164-166 "must be installed and linked to Stata" → "must be installed; Stata either finds it or uses the one {cmd:python set exec} names."; :216-218 "names the Python Stata is linked to, {cmd:c(python_exec)}" → "names the Python Stata runs ({cmd:c(python_exec)}, or the one Stata found)"; :293-297 "A Python linked to Stata that cannot be started" → "A Python Stata cannot start". dash.sthlp Dependencies paragraph :6743-6754 ("Before it starts ...") → replace "the linked Python starts" with "the Python Stata uses starts -- the one {cmd:c(python_exec)} names, or, with none set, the one Stata finds by itself" and "the Python it looked in ({cmd:c(python_exec)})" with "the Python it looked in"; add: "With no Python set and none Stata can start, Stata's own message comes first, then {cmd:dash}'s advice, and the command stops with Stata's return code." The `{ul:Python 3.11+}` item (:6709) is 36-04's (R2-43); leave it.
- **TR-36-01.8 Both modes.** No renderer code changes (`_dash_child_python` already falls back; the served app is launched by that function). No served copy-list entry.
- **TR-36-01.9 The fresh-HOME test** (test/test_python_discovery_fresh_home.py, new; `pytestmark = pytest.mark.release`; one module-scoped fixture runs the three Stata steps once, the five nodes read its results). The fixture: `repo` = the folder holding dash.ado (`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`); `w = tmp_path_factory.mktemp("fresh")` with subfolders `home`, `wheels` (empty) and `run`; `env = {k: v for k, v in os.environ.items() if k != "DASH_PYTHON_EXEC"}` updated with `HOME=<w>/home`, `PIP_NO_INDEX="1"`, `PIP_FIND_LINKS=<w>/wheels`, `PIP_DISABLE_PIP_VERSION_CHECK="1"`; each Stata step is `subprocess.run(["sh", os.path.join(repo, "scripts", "stata_slot.sh"), str(w / "run"), <do-file name>], env=env, timeout=900, capture_output=True, text=True)`, and a `subprocess.TimeoutExpired` fails the test naming the log. Step (i) `exe.do`: `python: import sys; from sfi import Macro; Macro.setLocal("_x", sys.executable)` and three `file` lines writing `_x` to `exe.txt`. The test then reads `exe.txt`, requires `os.path.isabs(exe) and os.access(exe, os.X_OK)` (else it fails with the text), and runs `subprocess.run([exe, "-m", "pip", "list", "--format=freeze"], env=env, capture_output=True, text=True, timeout=300)` into `before`. Step (ii) `fresh.do` (written by the test into `<w>/run`, where `scripts/stata_slot.sh` runs it, so every file it names is relative; `<repo>` is written as plain text, and the test fails before writing when that path holds a double quote, a backtick or a dollar sign):
  ```stata
  adopath ++ "<repo>"
  global dash_nobrowser 1
  file open fh using "pyx.txt", write text replace
  file write fh `"[`c(python_exec)']"'
  file close fh
  sysuse auto, clear
  capture noisily dash scatter mpg weight, saving("p.html", replace)
  display "##RC dash " _rc
  capture noisily dash_setup
  display "##RC setup " _rc
  ```
  Step (iii) the same pip line into `after`. Nodes (each assertion message starts with its case id, PD-5): `TestAFreshHome::test_no_python_is_set` (Q3601-1: `pyx.txt` is `[]`); `::test_nothing_says_python_is_unavailable` (Q3601-2: `fresh.log` holds neither `Python is required but is not available` nor `Python is not available to Stata`); `::test_dash_reaches_its_work` (Q3601-3: `##RC dash 0` and `p.html` exists, or `##RC dash 198` and the log holds `not installed for the Python Stata uses (the Python Stata found, ` followed by the path in `exe.txt`); `::test_dash_setup_checks_the_found_python` (Q3601-4: the log holds dash_setup's Python line with `OK` and no `Unmet: Python`); `::test_nothing_is_installed` (Q3601-5: `after == before`, and no folder named `site-packages` exists under `<w>/home`). The module skips, with its reason, only when `STATA_BIN` (default `/usr/local/bin/stata-mp`) is not an executable file; under `make test-release` (`DASH_STRICT=1`) that skip fails the run, as every release-tier skip does.

## Boundaries

- Do not add `python query`, `capture python: pass` decisions or any other probe (M8). Do not touch `_dash_child_python`, `_dash_xm_load` or `_dash_require_mata`'s logic (only its `_needed` list).
- Do not change the Stata 19 floor, the platform text or the Dependencies list items (36-04 owns them, the `{ul:Python 3.11+}` item included); edit only the dash.sthlp paragraph TR-36-01.7 names.
- Do not edit the bokeh/numpy/pandas import probes (`SKIP: bokeh not installed` lines): they ask about packages, with warm-up and retry, and stay.
- No certification script starts a second Stata; the only Stata the fresh-HOME case starts is through `scripts/stata_slot.sh` (CLAUDE.md rule 9, A-8).
- Never `python set exec`, never `set ..., permanently`, never run `dash_setup` without `PIP_NO_INDEX=1` in a test.

## Stata truth

No extract script, no fixture and no block in test/test_wp36_truth.cscript (D-36-01.e): the truth is Stata's own behaviour in a fresh HOME, measured live by the release-tier pytest of TR-36-01.9 (Q3601-1..5), one Stata slot at a time through `scripts/stata_slot.sh`.

Message and rc cases go in test/test_env_guards.cscript under this section's ids (R1, PD-5): ENV-06 and ENV-07 flipped (TDD stubs), plus Q3601-6 `_dash_python_failed 7102 ""` → r(7102), log holds `no Python is set, and Stata could not start one it found by itself` and `python set exec`; Q3601-7 `_dash_python_failed 0 "/usr/bin/python3"` → r(198), log names `/usr/bin/python3`; Q3601-8 `_dash_pyname()` by value: when `c(python_exec)` is set (the certification runner's usual state), `mata: st_local("_q8", _dash_pyname())` gives exactly `c(python_exec)`; when it is empty, the case sets `local _dd_x "/q3601/python3"` first and the result is `the Python Stata found, /q3601/python3` (so the case asserts on whichever state the session is in and never skips); `display "Q3601-8 PASS: ..."` on success.

## TDD test stubs

First, failing at the base (task 01):
- Test: the dispatcher does not refuse an empty python_exec -- test/test_python_discovery.py::TestNoPreCheck::test_require_python_refuses_nothing (reads `_dash_require_python`'s body from dash.ado: no `exit`, no `display`).
- Test: the retry surfaces Stata's message -- test/test_python_discovery.py::TestNoPreCheck::test_the_retry_is_noisy_and_hands_on_the_code (`_dash_require_deps` body: first probe `capture python:`, retry `capture noisily python:`, then `local _dd_prc = _rc`, then `_dash_python_failed`).
- Test: no refusal text survives -- test/test_python_discovery.py::TestNoPreCheck::test_no_file_says_python_is_unavailable (dash.ado and dash_setup.ado code, comments dropped, hold neither `Python is required but is not available` nor `Python is not available to Stata`).
- Test: dash_setup has no empty-setting gate -- test/test_python_discovery.py::TestNoPreCheck::test_setup_does_not_stop_on_an_empty_setting.
- Test: `_linked()` falls back -- test/test_python_discovery.py::TestLinked::test_empty_setting_is_sys_executable (fake `sfi` returning "" for `c(python_exec)`; `_linked()` returns `(sys.executable, "")`), ::test_a_set_path_is_resolved (unchanged behaviour, guard).
- Test: the harness has no Python gate -- test/test_python_discovery.py::TestTheHarness::test_no_script_gates_on_the_setting (no `test/*.cscript`, `test/cert_svg.do`, `test/templates/*.cscript` or `scripts/extract_*.do` holds the TR-36-01.5 regex or an `if ... c(python_exec) ... != ""` branch), ::test_stata_python_exec_reads_sys_executable (the script's here-document holds `sys.executable` and no `python query`).
- Test (release tier): test/test_python_discovery_fresh_home.py::TestAFreshHome::test_no_python_is_set, ::test_nothing_says_python_is_unavailable, ::test_dash_reaches_its_work, ::test_dash_setup_checks_the_found_python, ::test_nothing_is_installed (Q3601-1..5; at the base Q3601-1 and Q3601-5 pass and Q3601-2..4 fail: the session prints "Python is required but is not available" and dash_setup "Unmet: Python").
- cscript: Q3601-6, Q3601-7, Q3601-8 (test_env_guards.cscript).

Pins flipped (task 04): twelve nodes, one `Flipped:` line each in the commit body -- ENV-06, ENV-07, ENV-17, ENV-18, ENV-19, the two hygiene tests, the three scaffold-order lists, test_the_guard_decides_from_values and test_availability_is_the_setting_not_python_query:
- test_env_guards.cscript ENV-06 → with `_dash_python_ok` stubbed to 0, `_dash_require_python` returns rc 0 ("ENV-06 PASS: an empty python_exec is not refused (WP-36 plat:PT-1)"); ENV-07 → its log holds no `Python is required`; ENV-17..19 → stub `_dash_require_deps` instead (body: `_dash_python_failed 7102 ""`) and expect r(7102), no announced server, no page, no renderer run, and PF-10 unchanged; restore `_dash_require_deps` with a new Mata helper `_env_restore_program("../dash.ado", "_dash_require_deps")` that copies the program's lines (from `program define _dash_require_deps` to its first `end` at column 1) into a tempfile, `capture program drop`s it and `run`s the tempfile (so the script holds no `python:` line of its own).
- test_cscript_hygiene.py `test_every_script_that_skips_for_python_is_read`: `<count at the batch base> → 0` -- task 01 reads the count the pin holds at the batch-36.1 base (51 at 090d928, raised by each W0.2 of WP-33..36) into `<scratch>/36-01-sites.txt`, and the comment reads `# <count> -> 0: WP-36 plat:PT-1 -- no script skips for want of a Python setting (M8)` (R10; REVIEW R2-37); `test_a_script_that_needs_python_says_so_through_the_setting` → renamed in place to `test_no_script_skips_for_want_of_python` (not parametrised, so it never collects an empty parameter set, which a strict run would count as a skip; it asserts what the count pin does not cover: neither test/templates/wp_truth_template.cscript nor test/cert_svg.do -- outside `_CSCRIPTS`, the test/*.cscript glob the count pin reads -- holds a `_SKIPS_FOR_PYTHON` match, so no future truth script is born with the skip and cert_svg.do cannot skip for its callers); the scaffold-order lists of TestTheWp30TruthScript, TestTheWp31TruthScript and TestTheWpTruthScripts drop `SKIP: Python not available.`; the two docstrings gain the M8 paragraph.
- test_dependency_guards.py::test_the_guard_decides_from_values → the retry line starts `capture noisily python:` and `_rc` appears exactly once, in `local _dd_prc = _rc`.
- test_help_claims_8.py::test_availability_is_the_setting_not_python_query → asserts the gate is NOT in dash_setup.ado, and keeps every `python query` assertion.
- Parity: none (no renderer change).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| no refusal, noisy retry, advice program | pytest test_python_discovery.py | -- | n/a (ado) |
| dash_setup_lib fallback | pytest TestLinked | -- | n/a |
| harness has no gate | pytest TestTheHarness | -- | n/a |
| fresh HOME: dash and dash_setup run the found Python | release pytest test_python_discovery_fresh_home.py (Q3601-1..5), Stata through `scripts/stata_slot.sh` | -- | saved page (served starts the same Python, `_dash_child_python`) |
| advice wording and rc; the Python dash names | test_env_guards.cscript ENV-06/07 flipped, Q3601-6/7, Q3601-8 | -- | n/a |
| routes stop before the renderer on a failed start | ENV-17..19 flipped | -- | build, serve, one-line |
| no plain plat:PT-1 ledger or known-differences row; guard verdicts unchanged or regenerated | pytest test_corpus_ledger.py; `python3 test/known_differences.py plat:PT-1` and its hygiene command; S09 block of test_wp33_truth.cscript (`WP33_ONLY=S09`) | corpus_ledger.json, corpus_guard_truth.json | n/a |

- AC-36-01.1 In a fresh HOME, `dash scatter mpg weight, saving(...)` reaches the package check or writes the page, and never prints "not available".
- AC-36-01.2 In a fresh HOME, `dash_setup` reports the found Python OK and installs nothing under `PIP_NO_INDEX=1`.
- AC-36-01.3 `_dash_python_failed` prints the advice for both settings and exits with the code it is given.
- AC-36-01.4 No harness file gates on `c(python_exec)`; `sh scripts/stata_python_exec.sh` prints a path.
- AC-36-01.5 Every flipped pin carries its reason; `make test-all` at the batch end is green, and `make test-release` runs the fresh-HOME file.

## Tasks

**Commit boundary.** One commit, made by 36-01-04: subject `Use the Python Stata finds when none is set, in dash, dash_setup and the harness (WP-36 plat:PT-1)`; it stages dash.ado, dash_parse.mata, dash_setup.ado, dash_setup_lib.py, dash.sthlp, dash_setup.sthlp, scripts/stata_python_exec.sh, the rewritten harness files listed in `<scratch>/36-01-gates.tsv`, test/test_python_discovery.py, test/test_python_discovery_fresh_home.py, test/test_env_guards.cscript, test/test_cscript_hygiene.py, test/test_dependency_guards.py, test/test_help_claims_8.py, test/program_coverage_map.py, BUGS.md, GAPS4.md, CHANGELOG.md and test/test_tracking_documents.py, plus scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json (and test/fixtures/corpus_guard_truth.json) when 36-01-04's ledger step changes them, and each test file whose `*_KNOWN` or `*_DELIBERATE` table its known-differences step edits (BRIEF "The corpus ledger and the known-differences tables"). TWOWAY_COVERAGE_AUDIT.md has no row for Python discovery: the commit body says "no coverage-audit row" (REVIEW R2-9). `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp36-s01` (BRIEF "Pull form": every command names the worktree by this absolute path; `scripts/stata_slot.sh` runs `cd <scratch>` before Stata starts, so a relative path is not found).

<task type="auto" id="36-01-01">
  <name>Write the failing discovery tests</name>
  <files>test/test_python_discovery.py, test/test_python_discovery_fresh_home.py, test/test_env_guards.cscript</files>
  <action><![CDATA[
    In $WT at the batch base, re-read dash.ado:270-410 and :469-506, dash_setup.ado:80-130 and :757-768, dash_setup_lib.py:820-840, and re-run `grep -rn 'python_exec' test/*.cscript test/*.do test/templates scripts/*.do scripts/*.sh test/*.py` into `<scratch>/36-01-sites.txt` (the lists in Evidence are at 090d928; record any new site, and the count `test_every_script_that_skips_for_python_is_read` pins now). Run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` for `_dash_require_python`, `_dash_require_deps`, `_dash_python_ok`, `_dash_setup_pystart` and `_linked`, writing callers and risk to `<scratch>/36-01/anchors.txt` (HIGH, CRITICAL or UNKNOWN is named in the hand-back; an UNKNOWN is confirmed with `grep -n` before editing). Create test/test_python_discovery.py with the classes and nodes of "TDD test stubs" (TestNoPreCheck, TestLinked, TestTheHarness), reading files as text (comments dropped with the `_code` helper pattern of test_cscript_hygiene.py:458-467) and importing dash_setup_lib with a fake `sfi` module put in `sys.modules`. Create test/test_python_discovery_fresh_home.py per TR-36-01.9. Append Q3601-6, Q3601-7 and Q3601-8 to test/test_env_guards.cscript before its summary, each with `display "Q3601-<k> PASS: ..."` on success. Run `python3 -m pytest test/test_python_discovery.py -q -n0 -p no:cacheprovider -rf > <scratch>/36-01-01.log`, then `python3 -m pytest test/test_python_discovery_fresh_home.py -q -n0 -p no:cacheprovider -rf > <scratch>/36-01-01-fresh.log` (a file named on the command line runs the release tier), and test_env_guards.cscript through the driver of BRIEF "Running one cscript"; write the failing node list and the FAIL lines to `<scratch>/36-01-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/36-01-01.log` prints at least 6 (every TestNoPreCheck and TestTheHarness node, and test_empty_setting_is_sys_executable); `grep -c FAILED <scratch>/36-01-01-fresh.log` prints 3 (test_nothing_says_python_is_unavailable, test_dash_reaches_its_work, test_dash_setup_checks_the_found_python) and the log shows `2 passed` and no `skipped`; `grep -c "Q3601-[678] PASS" <scratch>/run_test_env_guards.log` prints 0; `test -s <scratch>/36-01-01-failure.txt`.]]></verify>
  <done>Every regression test and certification case for plat:PT-1 existed and was shown failing on the unmodified tree, with the fresh-HOME run made through one Stata slot and the failure text saved.</done>
</task>

<task type="auto" id="36-01-02">
  <name>Remove the refusal from dash and dash_setup</name>
  <files>dash.ado, dash_setup.ado, dash_setup_lib.py</files>
  <action><![CDATA[
    Apply TR-36-01.1 (`_dash_require_python` body and both comments), TR-36-01.2 (`_dash_require_deps`: `_dd_x` on the probe line, the noisy retry, `local _dd_prc = _rc`, `_dash_python_failed`, `_dash_pyname()` in the two messages), TR-36-01.3 (`_dash_python_failed` after `_dash_require_python`; `_dash_pyname()` in dash_parse.mata beside `_dash_say`, its own `*!` header-index entry, its own new `_needed` continuation line directly before the list's last line; the two test/program_coverage_map.py entries, after `_dash_python_ok`'s and after `_dash_say`'s) and TR-36-01.4 (dash_setup.ado gate and comment, `_dash_setup_pystart` with `pyexe` and the noisy retry, the empty-setting failure line, dash_setup_lib.py `_linked()`). Every user path reaches a message through `_dash_say` or `display` of a fixed text; nothing is inlined into a `python:` line. Run `python3 -m pytest test/test_python_discovery.py test/test_dependency_guards.py test/test_cscript_hygiene.py::TestTheShippedAdoFilesFollowTheSameRule test/test_setup_pep668.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[TestNoPreCheck and TestLinked pass; `grep -c "Python is required but is not available" dash.ado` prints 0; `grep -c 'capture noisily python:' dash.ado` is one more than at the base; `diff <(git show HEAD:dash.ado | sed -n '/^    local _needed /,/[^\/]$/p') <(sed -n '/^    local _needed /,/[^\/]$/p' dash.ado) | grep -c '^<'` prints 0 (no base line of the `_needed` list is removed or changed; the check reads the list alone, since this task also deletes `_dash_require_python`'s body line `        _dash_pyfloor`, dash.ado:311) and the same command with `grep -c '^>'` prints 1 (the one new `_dash_pyname` line); test_program_coverage_map.py passes; test_dependency_guards.py::test_the_guard_decides_from_values fails only on the retry line and the one `_rc` read (it is flipped in 36-01-04); test_setup_pep668.py passes.]]></verify>
  <done>dash and dash_setup ran the Python Stata uses with nothing set, and a Python that could not start was reported with Stata's message, dash's advice and Stata's return code.</done>
</task>

<task type="auto" id="36-01-03">
  <name>Rewrite the harness gates and oracles</name>
  <files>scripts/stata_python_exec.sh, test/cert_svg.do, test/run_all_cscripts.do</files>
  <action><![CDATA[
    Write `<scratch>/rewrite_gates.py` (never committed) implementing TR-36-01.5's regex over the files it names (test/*.cscript, test/cert_svg.do, test/templates/wp_truth_template.cscript and scripts/extract_*.do: the script edits every file `<scratch>/36-01-gates.tsv` lists, about 116); run it once with `--dry-run` printing per file the match count, check every count is 1, then run it for real and write `<scratch>/36-01-gates.tsv` (file, before, after). Read each deleted comment block in the diff and restore any line that says something other than the gate's reason. Make the five hand edits of TR-36-01.5 (test/test_parser.cscript:3517 and :3743, test/test_option_surface.cscript:965, test/test_statistical_options.cscript:543 and :872 with their else branches, test/test_setup_python_gate.cscript:182) and the seven oracle edits (`or sys.executable`, with `sys` imported on that line: test/test_setup_honesty.cscript:532, :846, :897, :962, :1011, test/test_program_coverage.cscript:178, test/test_setup_python_gate.cscript:185), the test/run_all_cscripts.do comment and scripts/extract_axis_truth.do:114. Apply TR-36-01.6 to scripts/stata_python_exec.sh. Check `git diff --stat` lists only the files in the tsv plus the hand-edited files; run `sh scripts/stata_python_exec.sh` once (it prints a path) and `python3 -m pytest test/test_python_discovery.py::TestTheHarness test/test_cert_verdict.py test/test_cert_shards.py -q -n0`.
  ]]></action>
  <verify><![CDATA[`awk -F'\t' 'NR>1 && ($2!=1 || $3!=0)' <scratch>/36-01-gates.tsv | wc -l` prints 0; `grep -lE '^[[:space:]]*if .*c\(python_exec\).*== ""' test/*.cscript test/cert_svg.do scripts/extract_*.do test/templates/*.cscript | wc -l` prints 0 (the pattern reads `if` lines only: test_env_guards.cscript's ENV-04, `assert r(ok) == ...cond(...c(python_exec)... == "", 0, 1)`, stays and is not a gate; at 090d928 the pattern matches the 116 gate files and nothing else); `grep -c 'SKIP: no Python is linked\|SKIP: Python not available' test/*.cscript | grep -v ':0' | wc -l` prints 0; `sh scripts/stata_python_exec.sh` exits 0 and prints an absolute path; TestTheHarness passes.]]></verify>
  <done>No certification script, extract script or runner decided anything from an empty Python setting, and the pip-line oracles and stata_python_exec.sh named the Python Stata runs.</done>
</task>

<task type="auto" id="36-01-04">
  <name>Flip the pins, fix the help, commit</name>
  <files>test/test_env_guards.cscript, test/test_cscript_hygiene.py, dash_setup.sthlp</files>
  <action><![CDATA[
    Flip the pins of "TDD test stubs" in place with their comments: ENV-06, ENV-07, ENV-17..19 (with `_env_restore_program`, a Mata function defined beside `_env_progs_with` in test_env_guards.cscript, version 19, reading the file with `cat()`, writing with `fopen`/`fput`/`fclose`), the two hygiene count/parametrised tests (`# <count> -> 0: ...` with the count recorded in `<scratch>/36-01-sites.txt`), the scaffold-order lists of TestTheWp30TruthScript, TestTheWp31TruthScript and TestTheWpTruthScripts, the two docstrings, test/test_dependency_guards.py::test_the_guard_decides_from_values, test/test_help_claims_8.py::test_availability_is_the_setting_not_python_query. Apply TR-36-01.7's help edits (dash_setup.sthlp :41-50, :164-166, :216-218, :293-297; dash.sthlp :6743-6754 only). Run: `python3 -m pytest test/test_python_discovery.py test/test_python_discovery_fresh_home.py test/test_cscript_hygiene.py test/test_dependency_guards.py test/test_help_claims_8.py test/test_setup_pep668.py test/test_version_floor.py test/test_cert_verdict.py test/test_cert_shards.py test/test_program_coverage_map.py test/test_help_conformance.py -q -p no:cacheprovider`; through the driver: test_env_guards.cscript, test_setup_python_gate.cscript, test_setup_honesty.cscript, test_program_coverage.cscript, test_parser.cscript, test_statistical_options.cscript, test_option_surface.cscript and test_wp36_truth.cscript (the scaffold alone at this point: `part 1/1 has no block to run` or the scaffold PASS). Close the BUGS.md entry 33-01 opened for plat:PT-1 (`grep -n 'WP-36 section 36-01 has not landed' BUGS.md`) in PD-4's closed form (Pinned by test/test_python_discovery.py::TestNoPreCheck, test/test_python_discovery_fresh_home.py::TestAFreshHome (Q3601-1..5), Q3601-6..8; no fixture), flip `- [ ]` to `- [x]`; rewrite GAPS4.md's `- **plat:PT-1 Tracked:**` line to `Closed in WP-36, BUGS.md "<title>", commit pending.`; delete plat:PT-1's line from `GAPS4_OPEN`; add under CHANGELOG `### Changed behaviour (may need your do-files changed)`: `- With no Python set, dash and dash_setup refused with "Python is required but is not available to Stata", r(198); they run the Python Stata finds, and a Python that cannot start is reported with Stata's message and its return code (WP-36, plat:PT-1)`. The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h): (1) run `awk -F'\t' '$1 == "plat:PT-1" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the item's plain rows; a `plat:PT-1 (documented)` or `plat:PT-1 (residual)` row stays, A-10), rerun `python3 scripts/corpus/ledger.py` (33-05; no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py plat:PT-1` (33-10) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion dict 33-10 names for it (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`, `ABBREV_DELIBERATE` in test/test_abbreviations.py for `ABBREV_KNOWN`, and beside 33-11..33-13's tables `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); M8 keeps none here, so none is expected -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes, and stage each table file the step edited, by the path the printed row names; (3) run the corpus guard block (`WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`, the driver of BRIEF "Running one cscript" written for test/test_wp33_truth.cscript with `<repo>` = `$WT`) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes), and put each Q3309-1 message and the fixture's `Fixture:` line in the commit body (a worse verdict this item's change does not explain is a regression: fix the code first, CLAUDE.md rule 2). Before committing, in `$WT`: `git pull --ff-only . main` (CLAUDE.md rule 4; at the batch base it prints `Already up to date.` -- if it refuses, stop and report to the orchestrator, never make a merge commit on a section branch) and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk is named in the hand-back). Grep the message for `claude|anthropic`; commit with the body lines of BRIEF (Regression; one `Flipped:` line for each of the twelve flipped nodes listed in "TDD test stubs"; a `Fixture:` line for corpus_ledger.json or corpus_guard_truth.json only when the ledger step changed it; BUGS.md; GAPS4; "no coverage-audit row"); grep again.
  ]]></action>
  <verify><![CDATA[The pytest run's last line reads `<n> passed in ...` with no `failed`, `error` or `skipped` (the fresh-HOME file runs: it was named); every listed cscript log ends with its pass line (`ALL TESTS PASSED`, `ALL CHECKS PASSED` or the script's own); `grep -c "Q3601-[678] PASS" <scratch>/run_test_env_guards.log` prints 3; `awk -F'\t' '$1 == "plat:PT-1"' scripts/corpus/ledger.tsv | wc -l` prints 0, test/test_corpus_ledger.py passes, `python3 test/known_differences.py plat:PT-1` prints no `<file>:<line>` row and the hygiene command it prints passes, and the S09 guard block ends with its pass line; `git log -1 --format=%s | grep -c "(WP-36 plat:PT-1)"` prints 1; `git log -1 --format=%B | grep -c '^Flipped: '` prints 12; `grep -c "plat:PT-1 Tracked:\*\* Closed in WP-36.*commit pending" GAPS4.md` prints 1; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>plat:PT-1 was closed: the help said what happens with nothing set, every pin stated the new rule with its reason, the fresh-HOME release test passed through one Stata slot, the corpus ledger kept no plain plat:PT-1 row, and the one commit landed on wp36-s01.</done>
</task>

## Section completion criteria

- `_dash_require_python` refuses nothing and is documented as the empty hook; `_dash_require_deps` and `_dash_setup_pystart` retry noisily and hand on Stata's code; `_dash_python_failed` and `_dash_pyname()` exist and are mapped in program_coverage_map.py; `_dash_pyname` is in `_needed` on its own new line.
- `_linked()` falls back to `sys.executable`; `stata_python_exec.sh` prints the found Python.
- No harness file gates on `c(python_exec)`; the gate table in `<scratch>/36-01-gates.tsv` is all 1 → 0.
- Q3601-1..5 (release pytest) and Q3601-6..8 (test_env_guards.cscript) pass; each of the twelve flipped pins has its own `Flipped:` line; BUGS/GAPS4/CHANGELOG/GAPS4_OPEN updated in the one commit.
- No plain `plat:PT-1` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py plat:PT-1` prints none); test/fixtures/corpus_ledger.json is regenerated from the ledger by `scripts/corpus/ledger.py`; test/test_corpus_ledger.py, the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script if Q3309-1 reported any change for a guard example.

## Notes

- **Traps.** (1) `capture noisily python:` prints nothing when the line succeeds: the user sees Stata's message only on a real failure. (2) The fresh-HOME environment must not carry `DASH_PYTHON_EXEC` (test/run_all_cscripts.do:54-63 reads it): the test builds `env` without it. (3) The bound on each Stata run is `subprocess.run(..., timeout=900)` in the test, never /usr/local/bin/timeout (an Intel Homebrew binary on this machine; a parent of another architecture is what stata_batch.sh's STATA_ARCH=auto guards against) and never a nested `perl -e alarm`. (4) `scripts/stata_slot.sh` waits for a free slot: run `make test-release` after `make cert` (as `make release` does), never beside three cert shards. (5) The gate regex must not match `if `"`c(python_exec)'"' != ""` branches: those are the five hand edits. (6) W0.2 for WP-37 onward then moves only the glob-count pin and test_cert_shards.py's count: the Python-skip pin is 0 and stays 0 (reported to the orchestrator; the index's W0.2 text names three pins).
- **GitNexus and rule 4.** `impact` on every function this section edits before its first edit (36-01-01); `git pull --ff-only . main` (in `$WT`, BRIEF "Pull form") and `detect-changes --scope all` before the commit (36-01-04); HIGH, CRITICAL or UNKNOWN risk goes in the hand-back (REVIEW R2-8).
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** 36-01-04 deletes plat:PT-1's plain rows of scripts/corpus/ledger.tsv and regenerates test/fixtures/corpus_ledger.json with `scripts/corpus/ledger.py` (D-33-05.i), deletes every row `python3 test/known_differences.py plat:PT-1` prints and runs the hygiene command it prints (D-33-10.h; M8 keeps no difference on purpose, so no deliberate-dict entry), and regenerates corpus_guard_truth.json with its extract script if Q3309-1 reports any change for a guard example (33-09).
- **Help paragraphs owned (R3):** dash_setup.sthlp :41-50, :164-166, :216-218, :293-297; dash.sthlp Dependencies :6743-6754 (the "Before it starts" paragraph only). Appendix B HR-20 (the `{ul:Python 3.11+}` item's half is 36-04's).
- **Merge rules touched:** R1 (Q3601-6..8 in test_env_guards.cscript; no truth block), R6 (`_dash_python_failed` version 19, `_dash_pyname` in `_needed` on its own line, both in program_coverage_map.py), R9 (twelve flips, one `Flipped:` line each: ENV-06, ENV-07, ENV-17, ENV-18, ENV-19, test_every_script_that_skips_for_python_is_read, test_a_script_that_needs_python_says_so_through_the_setting (renamed test_no_script_skips_for_want_of_python), TestTheWp30TruthScript's, TestTheWp31TruthScript's and TestTheWpTruthScripts's scaffold-order lists, test_the_guard_decides_from_values, test_availability_is_the_setting_not_python_query), R10 (`<count>` → 0), R14 (no edition text).
- **The standing rule.** The maintainer's memory note "probe c(python_exec), never by running Python" predates M8; the commit does not edit it, and the hand-back asks the maintainer to restate it as "never decide Python's availability by running it; with no Python set, run the normal python: path (M8)".
- **Commit-body line forms:** `Regression: test/test_python_discovery.py::TestNoPreCheck::test_require_python_refuses_nothing -- failed at <base> with <text>`; `Regression: test/test_python_discovery_fresh_home.py::TestAFreshHome::test_nothing_says_python_is_unavailable -- failed at <base> with <text>`; `Flipped: test/test_env_guards.cscript ENV-06 -- r(198) on an empty python_exec was wrong because Stata finds its own Python (M8)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` only when 36-01-04's ledger step changed them; `BUGS.md: "<title>" (closed)`; `GAPS4: plat:PT-1 Tracked`; `no coverage-audit row`.
