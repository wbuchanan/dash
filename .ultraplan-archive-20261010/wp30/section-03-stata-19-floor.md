# Section 03: Stata 19 floor declared and enforced (P1.35 under M2)

> Part of: WP-30 · Items: P1.35 (entry `P1.35`) · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: 05, 12, 25 · Tasks: 11, 1 commit · Case prefixes: SF; ENV-24..29

## Review amendments

- Major: the S03 truth block named "the scaffold's copies of `_w29_expect`/`_w29_done`"; it now reports through `_w30_expect`/`_w30_done` (TR-01.10.4), so `WP30_ONLY=S03` counts its cases and ends `ALL CHECKS PASSED` (AC-03.3 says so); `_s03_future`'s `version 99` is recorded as the one deliberate helper exception.
- Major: 03-11's key check `grep -c '"P1.35"'` prints 2 after a correct close; replaced by TR-01.10.1's `grep -c '^    "P1.35": "'`.
- Minor: `TestTheStataFloor` is 12 tests but 13 nodes (one parametrised over two files); 03-01 and 03-09 counts corrected. ENV-27 now erases the two files it writes.
- Spot-checked at HEAD: 79/13 `version 16.0` matches, dash.ado:84-92, :189-215, :5994-5995, dash_setup.ado:19-24, :60-64, :489-500, :521, dash.pkg:17, dash.sthlp:3779-3787, dash_setup.sthlp:122-125, test_env_guards.cscript:472-478 and :812-820, PC-15 :684-690, the 20-column `Python .............` alignment. All hold.
- Checked: M2 (only 19.5 run; nothing below 19 executed), M5 (r(9), Stata's own code for a version it cannot run, measured by SF-01), M6 (silent on 19+). Batch 1 with S02: no shared program; `wire_option_reporting.py` hunks disjoint; truth-script blocks separated by S02's unchanged end lines. No open question touches S03.
- Rejected: none.

The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:169 (P1.35) reads: "`version 16.0` is declared, but only StataNow 19.5 is ever run. Every truth fixture is also 19.5-only." Its sources say the same from three sides:

- GAPS2-J8-e (GAPS2.md:1757): "The 70 `version 16.0` statements imply Stata 16 support, which is never documented or tested."
- GAPS2-H-intro-stataver (GAPS2.md:1512): the package promises to run "wherever Stata 16+ ... run", and Stata 16-18 "have never been tested".
- GAPS2-K3-d (GAPS2.md:1834): "Every truth was measured once, on StataNow 19.5."

Measured at `c96facd` (research `.ultraplan/wp30/research/p1-35.md` §1, re-counted for this section):

- `version 16.0` is the first statement of all 79 programs in dash.ado and of 12 of the 13 in dash_setup.ado: 91 statements, not GAPS2's 70. `_dash_pymin` declares none.
- No file states a Stata minimum. dash.pkg:17 is `d Requires: Python 3.13+, bokeh>=3.8, numpy>=2.3, pandas>=2.3.`; dash.sthlp's Dependencies (3779-3817) and dash_setup.sthlp's (122-189) name no Stata release.
- Nothing reads `c(stata_version)`. A Stata 14 or 15 stops at dash's first line with Stata's own "cannot run version 16.0 programs", r(9), naming neither dash nor what it needs. Stata 16-18.5 run dash untested, where twoway itself lacks colours, schemes and plot types dash draws (research §3.2).

**After this section.** Under M2 ("Raise floor to 19") and the register's rulings P1.35.1-P1.35.7:

- `dash` (every subcommand) and `dash_setup` refuse a Stata below 19 as their first act, with `dash requires Stata 19 or later; this is Stata X.Y` and r(9). Nothing is registered, written, served or installed.
- On Stata 19 or later the check is silent in `dash`. `dash_setup` reports one line, `Stata .............. OK (version 19.5)`.
- All 91 statements read `version 19` (not 19.5: the guard admits 19.0, P1.35.3/P1.35.5). The two generators that write such a line write `version 19`.
- dash.pkg, dash.sthlp and dash_setup.sthlp say "Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64" and "Measured on MP only" (P1.35.6). CHANGELOG states the floor under Requirements and the refusal under Changed behaviour (P1.35.7).
- A do-file that sets `version 16` or `version 17` on Stata 19 still works. CV-01..CV-11 stay, because the floor is the Stata being run, not the version a do-file sets.
- dash's specs and function-layer points are byte-identical at the new language level. The prototype in Evidence E5 measured this.

**Why one section.** P1.35 is one entry with one commit. The register makes the sweep and the guard "one first-batch commit" (P1.35.3, A131), so that every later batch writes `version 19` in its new programs instead of rebasing over 91 changed lines.

**Test order and commit rule (rule 7, D1, A156).**

- **03-01 and 03-02** write every regression test and run them against the unmodified tree. The failure text is saved to `<scratch>/03-P1.35-failure.txt`. 03-02 also records the spec baseline. Neither commits.
- **03-03 to 03-10** add the guards, sweep, flip the pinned cscripts, register the programs, state the floor and certify through the slot.
- **03-11** closes the entry, runs the full suite once through the queue and makes the one commit, `(WP-30 P1.35)`.

No test-only commit exists, and no commit is red. The full certification run of the sweep is the orchestrator's (batch 1's G8, index step 1.4), never this section's.

## Risk: [yellow] — the guard sits at the entry of every command, and the sweep changes the language level of 91 programs

**Why.**

- A wrong comparison in the guard refuses every user, on every route, in both modes.
- BUGS.md:568 is the measured proof that the language level changes behaviour inside dash. `_dash_pyver_ok` answered 1 for every input under `version 16.0` and correctly at the session's version.

**Risk factors.**

1. The guard runs on a Stata that cannot be run here (M2: no 14-18.5 binary). A guard that uses anything newer than its target reaches Stata's own error instead of dash's words.
2. The sweep can change a result silently: a spec, a function layer's points, dash_setup's comparisons.
3. The callerver fallback (dash.ado:5995) now reads 19 instead of 16.
4. Two generators re-emit `version 16.0` if they are run again.
5. Program names collide between dash.ado and dash_setup.ado when a script `do`es both files.
6. A missed exemption fails the new pin for the wrong reason (critic C).

**Mitigation.**

1. **Factor 1.** The guards declare `version 13` and use only `c(stata_version)`, `real()`, `missing()`, `cond()`, `display` formats and Mata's `strtoreal`/`strofreal`/`st_local`, all of which Stata 13 has. `TestTheStataFloor::test_the_guards_need_nothing_newer_than_stata_13` forbids `strtrim(`, `ustr*`, `regexm(`, `python`, `_dash_say` and any `version` above 13 in their bodies. dash.ado and dash_setup.ado hold no `python:`…`end` block, so an older Stata loads both files whole (critic D). The refusal state is reached on 19.5 through the pure comparator and stubs (ENV-24..29).
2. **Factor 2.**
   - The spec probe of 03-02/03-05 diffs every `dash_*` global and the assembled spec before and after the sweep. It was measured identical in a prototype (E5).
   - The full certification run follows in batch 1's G8.
   - `test_setup_python_gate.cscript` passed in full on a swept copy.
3. **Factor 3.** SF-02 pins that the fallback's points equal the old fallback's, byte for byte, for a seeded `runiform()` and for `normalden(x)`.
4. **Factor 4.** Both generators are updated, the generated region is regenerated (03-06), and `test_no_version_16_line_remains` reads both scripts.
5. **Factor 5.** Distinct names, measured necessary (E4).
6. **Factor 6.** The exempt set is closed and named in the test: the three guards and the two constants.

## Dependencies

- **Depends on: 01.** S01 provides:
  - the open BUGS.md entry `P1.35` and its `WP30_OPEN` key;
  - the CHANGELOG markers `<!-- WP-30 P1.35 -->` at the end of `### Changed behaviour (may need your do-files changed)` and of `### Requirements` (index "P1 coverage": "Requirements; Changed behaviour");
  - S03's stub block in `test/test_wp30_truth.cscript`;
  - the S03 anchors in `test/program_coverage_map.py` (A148: end of `COVERAGE["dash.ado"]`, before :298, and end of `COVERAGE["dash_setup.ado"]`, before :338).
- **Blocks: 05, 12, 25.**
  - S05 (Python floor) edits the same Dependencies paragraphs, `test_version_floor.py` and the setup scripts.
  - S12 (prefix strip) and S25 (dependency guard) insert their statements after S03's guard and the Mata guard at the top of `dash` (A154).
- **Parallel batch: 1, with S02 (portable runners). Merge order: S02, S03.** Both edit `scripts/wire_option_reporting.py`:
  - S02 edits its REPO and refusal lines (IR-7);
  - S03 edits only the `version` line of its `HELPER` text (:115).

  S02 does not touch dash.ado or dash_setup.ado.
- **Can run with:** S02 only. No other section of batch 1 exists.

## Evidence

All anchors are at `c96facd` (dash.ado 8,487 lines; dash_setup.ado 1,026; dash.sthlp; dash_setup.sthlp). Stata and Mata symbols are not indexed by GitNexus, so every caller below was confirmed by `grep`.

### E1 The declarations

`grep -c 'version 16.0' dash.ado dash_setup.ado` prints `79` and `13`. Twelve of dash_setup.ado's are statements. The thirteenth is the comment at :521: "neither took effect under `version 16.0', which is the version dash_setup declares". The index's gate counts comments too, so that comment is reworded (TR-03.6). A parse with `test/test_program_coverage_map.py`'s `_ado_programs`/`_logical_lines` gives `dash.ado 79 []` and `dash_setup.ado 13 [('_dash_pymin', 'return local pymin "3.13"')]`: every program's first statement is `version 16.0` except `_dash_pymin`'s.

The two entry programs, dash.ado:84-92:

```stata
84  program define dash
85      version 16.0
86
87      // Every subcommand parses through Mata, so this is the one place that
88      // covers all of them.  Without it a broken or missing dash_parse.mata
...
92      _dash_require_mata
```

dash_setup.ado:19-24, with the header it prints at :63-64:

```stata
19  program define dash_setup, rclass
20      version 16.0
...
24      syntax [, VENV(string)]
...
60      _dash_pymin
61      local c_pymin "`r(pymin)'"
63      display as text _newline "{txt}dash_setup: checking dependencies..."
64      display as text "{hline 60}"
```

The neighbour pattern this section copies, dash.ado:189-215: a pure probe and a guard that calls it.

```stata
189  program define _dash_python_ok, rclass
190      version 16.0
191      args probe
192      local probe = strtrim(`"`probe'"')
193      return scalar ok = cond(`"`probe'"' == "", 0, 1)
194  end
...
206  program define _dash_require_python
207      version 16.0
208      _dash_python_ok `"`c(python_exec)'"'
209      if r(ok) != 1 {
```

The constant this section's constant sits beside, dash_setup.ado:489-500:

```stata
489  program define _dash_pymin, rclass
490      /*
491          The minimum Python version dash requires, named once.
...
499      return local pymin "3.13"
500  end
```

The other declarations:

- dash.pkg:17 is `d Requires: Python 3.13+, bokeh>=3.8, numpy>=2.3, pandas>=2.3.` `TestTheFloorIsTheTestedBaseline::test_every_declaration_agrees_with_dash_setup` asserts that exact substring, so the Stata floor goes on its own line and this line stays verbatim.
- dash.sthlp:3779-3787: `{marker dependencies}`, `{title:Dependencies}`, then `{phang2}{ul:Python 3.13+} -- linked to Stata; see {helpb python}.`
- dash_setup.sthlp:122-127: `{marker dependencies}`, `{title:Dependencies}`, then `{pstd}{ul:Python}`.
- CHANGELOG.md:607 is `### Requirements`. Its first line is the Python floor.

### E2 Where the language level reaches behaviour

- **BUGS.md:568** ("The Python version gate never fired, because `version 16.0' broke the comparator"). `return scalar` and `exit` inside a `forvalues` took effect under neither level in the old `_dash_pyver_ok`. The fix decides once and returns after the loop. The critic re-ran its six pairs through a `version 19` wrapper: `0 0 1 1 1 0`, correct.
- **The callerver fallback**, dash.ado:5994-5995, inside `_dash_fn_points` (program at :5973):

  ```stata
  5994      local uv : copy global dash__uv
  5995      if "`uv'" == "" local uv = string(c(version))
  ```

  `$dash__uv` is set by `dash` at :144 (`global dash__uv = string(_caller())`) right before its only call of `_dash_plot` (:145), and dropped at :5363. `grep` finds no other caller of `_dash_plot` in dash.ado. So in production the fallback is reached only by a direct internal call, as `test_parser.cscript` FX-06 (:2570-2583) makes one. After the sweep, `c(version)` there is 19 instead of 16.
- **regexm()** follows the caller's user version, not dash's `version` (BUGS.md:1287, test_caller_version.cscript). The sweep does not change it.

### E3 Measured in StataNow 19.5 for this section (scratch probes, `scripts/stata_slot.sh`)

Probe `p.do`:

```
display c(stata_version) c(version) c(userversion)        -> stata_version=19.5 version=19.5 userversion=19.5
version 13: display c(stata_version) c(version)           -> P-A13 stata_version=19.5 version=13
version 16: display ... c(userversion)                    -> P-A16 stata_version=19.5 version=16 userversion=16
local s : display %9.1f 18.5 ; local s `s'                -> [18.5]      (17 -> [17.0])
a version-19 program called plainly / under version 16:   -> version=19 userversion=19.5 caller=19.5
                                                             version=19 userversion=16 caller=16
twoway__function_gen y = runiform() (seed 12345, n 5) at callerver 16 and 19
                                                          -> .35762972288842587 .57445129399171091 both, same=1
twoway__function_gen y = normalden(x) at 16 and 19        -> .24197072451914334 both, same=1
```

`c(stata_version)` is the release whatever the caller's `version` is, so the guard reads the Stata being run. `creturn.sthlp` of Stata 14 (:98) and 15 (:107) document `c(stata_version)`. That was a read-only file read; no older binary was run.

Probe `p2.do`, with dash loaded by `do` as the truth scripts load it:

```
program with `version 99', run          -> "this is version 19.5 of StataNow; it cannot run version 99.0 programs"  rc=9
_dash_fn_points, seed 20261003, range(-2 2) n(5):
  $dash__uv=16    runiform  callerver=16 json="1":{"x0":-2,"dx":1,"y":[0.29532715122208952,0.85214134402019426,0.71770895713862248,0.19297981637520489,0.36342502008799593]}
  $dash__uv=19    runiform  callerver=19 json=(identical)
  $dash__uv empty runiform  callerver=16 json=(identical)          <- HEAD's fallback
  normalden(x)    all three json="1":{"x0":-2,"dx":1,"y":[0.053990966513188049,0.24197072451914334,0.39894228040143265,0.24197072451914334,0.053990966513188049]}
version 16: dash function y = normalden(x), range(-2 2) n(5) name(p2v16) -> callerver=16, the same points
```

Stata's own code for a `version` it cannot run is 9, and that is the code dash's refusal uses (M5: the code Stata uses). Points at callerver 19 equal those at 16.

Probe `p3.do` ran the exact program text of TR-03.1, TR-03.2 and TR-03.4 on 19.5:

```
_dash_stata_ok  19.5|19 -> ok=1 shown=19.5   19|19 -> 1 19.0   20|19 -> 1 20.0
                18.5|19 -> 0 18.5   17|19 -> 0 17.0   15.1|19 -> 0 15.1
                ""|19 -> 0 .   abc|19 -> 0 .   19.5|"" -> 0 19.5   "19 | 1"|19 -> 0 .   (by value: never evaluated)
_dash_require_stata              -> rc 0, silent;  under version 16: -> rc 0
_dash_setup_stata                -> rc 0, silent
_dash_statamin stubbed to "99"   -> "dash requires Stata 99 or later; this is Stata 19.5"  rc=9
```

### E4 Subprograms are local to their ado-file, so there are two guards

Probe `p.do`:

- Two ado-files, `p35a1.ado` and `p35a2.ado`, each define a subprogram `_p35dup`.
- After `p35a1` ran, `p35a2` printed `dup from a2` with rc 0. A program defined inside an autoloaded ado-file is reachable only from that file.
- So dash.ado cannot call a program defined in dash_setup.ado, nor the reverse.
- The scripts that `do` both files define every program globally:
  - `test_program_coverage.cscript:82-83` does `do "../dash.ado"` then `quietly do "../dash_setup.ado"`;
  - `test_adversarial`, `test_by_suboptions`, `test_help_claims_8`, `test_render_locate` and this section's ENV block do the same.
- In those scripts a name defined in both files would be "already defined", r(110).
- Hence:
  - dash.ado holds `_dash_stata_ok` and `_dash_require_stata`, with the floor as a local;
  - dash_setup.ado holds `_dash_statamin`, the one named constant beside `_dash_pymin`, and its own guard `_dash_setup_stata`;
  - `test_version_floor.py` pins the two numbers equal. This is the register's P1.32.4 pattern for the Python floor.

### E5 Prototype of the sweep (scratch copy of `c96facd`, every `version 16.0` statement made `version 19` with `perl -pi -e 's/^(\s*)version 16\.0\s*$/$1version 19\n/'`)

- `grep -c 'version 16.0'` then gave `dash.ado:0`, `dash_setup.ado:1` (the :521 comment). `grep -cE '^\s*version 19$'` gave 79 and 12.
- The spec probe `s03_specs.do` (TR-03.10; its text is in "Stata truth"):
  - it registers 12 graphs and a KPI: scatter, a qualified lfit, by(), two function layers (one seeded `runiform()`), lpolyci, histogram, line with a format, rcap, colorvar, bar, and one graph under `version 16:`;
  - it assembles the spec with two filters through the `_dash_prepare_spec` test seam (as `test_e2e_single.cscript` P1C-19 does);
  - it writes every `dash_*` global and the spec as text.
  - It was run twice on HEAD (`diff` empty: deterministic), then on the swept copy: `SPECS_SAME`, `SPEC_SAME`. The 9,810-byte global dump and the 9,693-byte spec were byte-identical.
- `test_setup_python_gate.cscript` on the swept copy ended `ALL TESTS PASSED`.
- `test_caller_version.cscript` and `test_env_guards.cscript` on the swept copy stopped at the same line as on an unswept copy of the same location, with the same PASS lines (5 and 18). The copy's location breaks the renderer and library lookup (`dash: cannot locate dash_render.py`, ENV-10's "not on the ado-path"). That is a property of the scratch copy, not of the sweep.

### E6 What the floor makes moot (recorded in the BUGS entry, manifest note)

- **The rpcap and rpspike advice** at dash.ado:3496-3512 ("Use Stata's own twoway rpcap …") is right on every admitted Stata. StataNow's `ado/base/w/whatsnew18to19.sthlp:906-919` lists `twoway rpcap` and `rpspike` as Stata 19 features, without the StataNow mark. Only the comment at :3496, "twoway plot types in StataNow 19.5", is reworded to "since Stata 19".
- **Break in GUI Stata.** `_dash_stata_poller` (dash_render.py:37114) needs `sfi.BreakError`, which StataNow's `sfi.py:5723` has and 16, 17 and 18.0 lack (research §3.3; critic A re-verified 18.5). At a floor of 19, dash.sthlp:1563's Break claim holds on every admitted Stata. dash_render.py is not edited.

### E7 The generators

- `scripts/wire_option_reporting.py:115` writes `version 16.0` into the `_dash_report_ignored` program it emits (`HELPER`, :111-115; the program is dash.ado:4951). S02 retires the script with a refusal before any write (IR-7, ratification item 26). S03 still rewrites the emitted text "so the repository holds none" (IR-7).
- `scripts/gen_string_varlists_cscript.py:226` writes `"    version 16.0",` into `_sv_case`, in the generated region of `test/test_adversarial.cscript` (`_sv_case` at :2899-2901).
  - `python3 scripts/gen_string_varlists_cscript.py --check` prints `gen_string_varlists_cscript: region is current (87 cases).` at HEAD.
  - `test/test_string_plot_variables.py::TestTheGeneratedRegion::test_the_region_is_current` asserts `mod.render().strip() == region.strip()`, so the generator and the region must change together (03-06).
  - GitNexus: `gitnexus impact _sv_case_program -d upstream -r dash` → risk LOW, impactedCount 3 (`render`, `main`).

### E8 Both modes

- The guard is the first statement of `dash`, so both modes are behind it:
  - the saved page (the one-line `saving()` route, `dash build, saving()`);
  - the served app (`dash build, saving(app.py) server`, `dash serve`).
- An app started by hand (`python app.py`) is Python and reads no Stata version. The served child is launched with `sys.executable` (dash_render.py:37318).
- After a filter move nothing re-enters Stata in either mode. The saved page moves in its JS, and the served app recomputes in its Python process.
- The sweep changes no spec (E5). The renderer, the served template and every JS string are untouched. So both modes draw what they drew, before and after a move, by construction.
- **No served copy-list entry** (index R2 row "S01-S03": no copy-list change). **No JS twin. No `function_test_map.py` entry**, since dash_render.py is not edited.

### E9 Blast radius (GitNexus CLI; Stata is not indexed)

| Symbol | File | `gitnexus impact … -d upstream -r dash` | Confirmed by grep |
|---|---|---|---|
| `dash` (entry; edited: guard call, `version`) | dash.ado:84 | "Target 'dash' not found" (UNKNOWN) | 59 of 67 cscripts and all 12 examples call `dash`: HIGH in practice |
| `dash_setup` (edited the same way, plus the OK line) | dash_setup.ado:19 | not found (UNKNOWN) | 26 of 67 cscripts name it |
| every program's `version` line (91 programs) | both files | UNKNOWN | the whole Stata surface: certification run in G8 |
| `_dash_fn_points` (fallback now 19) | dash.ado:5973 | UNKNOWN | one call, dash.ado:5360 in `_dash_plot`; FX-06 calls it directly |
| `_dash_pymin` (neighbour, read only) | dash_setup.ado:489 | UNKNOWN | one call, dash_setup.ado:60 |
| new `_dash_stata_ok`, `_dash_require_stata`, `_dash_statamin`, `_dash_setup_stata` | both files | new | none yet |
| `_sv_case_program` | scripts/gen_string_varlists_cscript.py:222 | LOW (3: `render`, `main`) | test_string_plot_variables.py loads the module by path |
| `_setup_ado_floor` (helper beside the new class, read only) | test/test_version_floor.py:48 | UNKNOWN (impactedCount 0) | used only in that file |

The index's step 1.0 expects no HIGH or CRITICAL result from dash_render.py in this batch. The UNKNOWN rows are recorded in `<scratch>/batch-1-impact.txt` as unresolved (E4), not as low.

### E10 Tests that pin today's behaviour (flip, never delete)

No pytest node asserts `version 16.0` or the absence of a Stata floor. `grep -n "version 16" test/*.py` finds only `test/test_measure_stata_coverage.py:41`, a synthetic ado text that the measurement script's tests parse. It is not a pin and stays. These cscript lines model or restate today's level and are changed in place, each with a `Flipped:` line:

- `test/test_setup_python_gate.cscript:111-130`. The first `_gate16` wrapper (`version 16.0`) and its seven `_chk "v16: …"` cases are introduced by "These cases call it the way dash_setup does". dash_setup now declares 19, so they become `_gate19` with `version 19` and labels `v19: …`. The second `_gate16` block (:152-161, two cases) stays at `version 16.0` as the caller-at-16 case the manifest keeps.
- `test/test_env_guards.cscript:472-478`. The body of `_dash_python_ok` is restated after ENV-17..19 ("Re-`do'ing dash.ado over the programs already in memory is r(110), so the body is restated here"). Its `version 16.0` becomes `version 19`, so the restatement equals the shipped body. A new pytest pins that equality.
- `test/test_caller_version.cscript:5` and `:14` (header comments only). "dash's programs declare `version 16.0'" and "`version 16' -- dash's own minimum" are reworded. CV-01..CV-11 are unchanged.
- `test/test_adversarial.cscript:2899-2901`. The generated `_sv_case` is regenerated by the generator (03-06), never hand-edited.
- `test/test_program_coverage.cscript` PC-15 (:684-690). Its list of lines a full `dash_setup` prints gains `"Stata .............. OK (version"`. This is an extension in place, failing first (03-02).

These stay green unchanged, and the section relies on them (guards):

- `test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_every_declaration_agrees_with_dash_setup`: the Python Requires line is kept verbatim.
- `test/test_parser.cscript` FX-06: `y = x` gives `[0,0.5,1]` at callerver 19 as at 16.
- `test/test_parser.cscript` FX-09: `version 17:` sets callerver 17.
- `test/test_caller_version.cscript` CV-01..CV-11.
- `test/test_help_claims_8.py::TestTheDependenciesAreOneList::test_every_file_states_the_same_minimums` (additive text only).

## User stories

- **US-03.1** (US-30.24) As an installer on Stata 16-18.5, I want `dash` and `dash_setup` to tell me at once, in one sentence, that dash needs Stata 19, not to fail obscurely later or to run a package that was never tested on my Stata.
- **US-03.2** As an analyst whose do-files begin `version 16`, I want them to keep running dash on Stata 19 exactly as before.
- **US-03.3** As an installer reading `net describe dash` or the help, I want to see which Stata dash needs and on which Stata and edition it was measured.
- **US-03.4** As the maintainer, I want one floor number, declared everywhere and pinned by tests, so the package never again implies support for a Stata it never ran.

## Business requirements

- **BR-03.1** On a Stata older than 19, every `dash` command and `dash_setup` stop before doing anything else. They print `dash requires Stata 19 or later; this is Stata X.Y`, with X.Y the running release to one decimal, and return r(9). Nothing is registered, written, served or installed. (BR-30.35)
- **BR-03.2** On Stata 19 or later, dash's check prints nothing (M6: silent where Stata is). `dash_setup` reports `Stata .............. OK (version <release>)` before its Python line.
- **BR-03.3** A do-file that sets `version 16` or `version 17` on Stata 19 runs dash, in both modes, as before. A function layer still evaluates under the caller's version.
- **BR-03.4** Every program in dash.ado and dash_setup.ado declares `version 19`, except the guards and constants that must run on an older Stata. No `version 16.0` remains in dash.ado, dash_setup.ado or the generators. dash's specs and function-layer points are unchanged by the new language level, and a full certification run is green after the sweep (batch 1 G8). (BR-30.35)
- **BR-03.5** dash.pkg, dash.sthlp and dash_setup.sthlp say "Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64" and "Measured on MP only". CHANGELOG states the floor under Requirements and the refusal under Changed behaviour. The floor is one number everywhere it appears. (BR-30.35, P1.35.6, P1.35.7)

## Technical requirements

**TR-03.1 `_dash_stata_ok` (dash.ado, new).** Insert it after `_dash_require_python`'s `end` (dash.ado:215) and before the `_dash_require_mata` header (:218), with a header in the file's form. The header says:

- it is pure so a certification script reaches the refusal on a Stata that passes;
- its values are read by value in Mata;
- it is written for the Stata it refuses.

The program text, measured in E3:

```stata
program define _dash_stata_ok, rclass
    version 13
    args have want
    mata: st_local("h", strofreal(strtoreal(st_local("have"))))
    mata: st_local("w", strofreal(strtoreal(st_local("want"))))
    local shown : display %9.1f `h'
    local shown `shown'
    return local shown "`shown'"
    return scalar ok = cond(missing(`h') | missing(`w'), 0, `h' >= `w')
end
```

**TR-03.2 `_dash_require_stata` (dash.ado, new).** Insert it directly after TR-03.1. Its header says three things:

- it is the first statement of `dash`, before `version 19`, because without it an older Stata stops at that line with Stata's own "cannot run version 19.0 programs";
- dash_setup.ado's `_dash_statamin` holds the same number, because a subprogram of one ado-file cannot be called from another (E4);
- `test_version_floor.py` pins the two numbers equal, and equal to every `version` line.

```stata
program define _dash_require_stata
    version 13
    local floor 19
    _dash_stata_ok "`c(stata_version)'" "`floor'"
    if r(ok) != 1 {
        display as error "dash requires Stata `floor' or later; this is Stata `r(shown)'"
        exit 9
    }
end
```

It takes no argument. The refusal is reached in tests by stubbing `_dash_stata_ok` (ENV-25, ENV-28), never through a seam a user could pass text to.

**TR-03.3 `dash` (dash.ado:84-92).** The first statement becomes `_dash_require_stata`, preceded by a three-line comment naming WP-30 P1.35 and A154's order. The second statement is `version 19`. `_dash_require_mata` stays where it is, now third. Nothing else in `dash` changes. In particular, `global dash__uv = string(_caller())` (:144) is untouched: `_caller()` is still the user's version (E3: `caller=16` under `version 16:`).

**TR-03.4 `_dash_statamin` and `_dash_setup_stata` (dash_setup.ado, new).** Insert both after `_dash_pymin`'s `end` (:500) and before `_dash_pyver_ok` (:502).

```stata
program define _dash_statamin, rclass
    /*
        The oldest Stata release dash runs on, named once.

        returns r(statamin): "19".

        _dash_setup_stata refuses below it.  dash.ado's
        _dash_require_stata holds the same number (a program defined in
        one ado-file cannot be called from another), and
        test/test_version_floor.py pins the two, every program's
        `version' line, dash.pkg and both help files equal.  No `version'
        line: it runs on the Stata it refuses.
    */
    return local statamin "19"
end

program define _dash_setup_stata
    version 13
    _dash_statamin
    local floor "`r(statamin)'"
    local h = c(stata_version)
    local w = real("`floor'")
    if missing(`w') | `h' < `w' {
        local shown : display %9.1f `h'
        local shown `shown'
        display as error "dash requires Stata `floor' or later; this is Stata `shown'"
        exit 9
    }
end
```

A missing or unreadable constant refuses (fails closed).

**TR-03.5 `dash_setup` (dash_setup.ado:19-64).** The first statement becomes `_dash_setup_stata`, preceded by a two-line comment. Then comes `version 19`, then the existing `syntax [, VENV(string)]`. After `display as text "{hline 60}"` (:64) add:

```stata
    display as text "  Stata .............. {res}OK{txt} (version `c(stata_version)')"
```

The line has 14 dots, so `Stata` plus the dots fill the same 20 columns as `Python .............`. It comes before the Python check, which `if `"`c(python_exec)'"' == ""` opens. A refused Stata never reaches the header.

**TR-03.6 The sweep.**

- In dash.ado and dash_setup.ado every line matching `^\s*version 16\.0\s*$` becomes the same indentation plus `version 19`: 79 and 12 lines.
- Reword the comment at dash_setup.ado:521 so that it holds no `version 16.0` text, for example: "neither took effect under language level 16, which dash_setup declared until WP-30 raised it to 19, and therefore the level this ran under in production". The behaviour it records stays recorded.
- Reword dash.ado:3496's "twoway plot types in StataNow 19.5" to "twoway plot types since Stata 19 (whatsnew18to19), so the advice holds on every Stata dash runs on".
- Afterwards `grep -c 'version 16.0' dash.ado dash_setup.ado` prints `0` and `0`, and `grep -cE '^\s*version 19$'` prints `79` and `12`. The new guards add none: they say `version 13`.
- dash_parse.mata declares no `version` and is not edited.

**TR-03.7 The generators.**

- `scripts/wire_option_reporting.py:115`: `    version 16.0` → `    version 19` inside `HELPER`. Do not run the script. After S02 it refuses to run (IR-7).
- `scripts/gen_string_varlists_cscript.py:226`: `"    version 16.0",` → `"    version 19",`. Then run `python3 scripts/gen_string_varlists_cscript.py` (rewrite mode; pure Python, no Stata), which rewrites only the marked region of `test/test_adversarial.cscript`, then `--check`.

**TR-03.8 Declarations.**

- **dash.pkg.** Insert two lines before :17, keeping :17 verbatim:
  - `d Requires: Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64.`
  - `d Measured on MP only; Stata 19.0, Stata/BE and Stata/SE have not been run.`
- **dash.sthlp Dependencies.** Insert before :3787:

  ```
  {phang2}{ul:Stata} -- Stata 19 or later; tested on StataNow 19.5 (MP), macOS
      arm64.  Measured on MP only: Stata 19.0, Stata/BE and Stata/SE are
      admitted but have not been run.  On an older Stata, {cmd:dash} and
      {helpb dash_setup} stop before doing anything else with "dash requires
      Stata 19 or later; this is Stata {it:#}", r(9).  The floor is the Stata
      you run, not the version a do-file sets: a do-file that begins
      {cmd:version 16} still runs {cmd:dash} on Stata 19.

  ```

- **dash_setup.sthlp Dependencies.** Insert between :123 and :125:

  ```
  {pstd}{ul:Stata}

  {phang2}Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64.
  Measured on MP only: Stata 19.0, Stata/BE and Stata/SE are admitted but
  have not been run.  {cmd:dash_setup} checks this before anything else and
  reports {cmd:Stata .............. OK} with the release; on an older Stata
  it stops at once with "dash requires Stata 19 or later; this is Stata
  {it:#}", r(9), and checks and installs nothing.

  ```

- **CHANGELOG.md.** The closing task replaces the two `<!-- WP-30 P1.35 -->` markers in place (R4). The text is in task 03-11.
- No other help paragraph is edited (R3).

**TR-03.9 Registries.** Add these to `test/program_coverage_map.py`, under the S03 anchors (A148), alphabetical within each:

- `COVERAGE["dash.ado"]`:
  - `"_dash_require_stata": ("test_env_guards.cscript:ENV-25", "test_env_guards.cscript:ENV-28")`
  - `"_dash_stata_ok": ("test_env_guards.cscript:ENV-24", "test_env_guards.cscript:ENV-26")`
- `COVERAGE["dash_setup.ado"]`:
  - `"_dash_setup_stata": ("test_env_guards.cscript:ENV-29", "test_program_coverage.cscript:PC-15")`
  - `"_dash_statamin": ("test_env_guards.cscript:ENV-29", "test_program_coverage.cscript:PC-15")`

Each referenced case displays its id literally (`display "ENV-24 PASS: …"`), as `TestEveryReferenceIsATest::test_every_case_is_shown_by_its_script` requires. Then:

- No `function_test_map.py` entry, since no dash_render.py or dash_setup_lib.py function changes.
- No `_needed` entry, since the guards call only Mata built-ins.
- `test_no_orphans.py` stays green: each new program has a caller.

**TR-03.10 Tests.** These are:

- `test/test_version_floor.py::TestTheStataFloor` (12 tests, "TDD test stubs");
- ENV-24..ENV-29, appended to `test/test_env_guards.cscript` after ENV-23b and before its closing `display "All environment guard tests PASSED."`;
- SF-01..SF-04 in S03's block of `test/test_wp30_truth.cscript`;
- PC-15's extension;
- the flips of E10;
- the spec probe, a scratch do-file run before and after the sweep (not committed).

**TR-03.11 Both modes.** dash_render.py, the served template and every JS string are untouched. ENV-27 builds a saved page and a served app under a `version 16` caller, and ENV-28 shows every route of both modes refused under the stubbed comparator. The spec probe shows the spec both modes draw from unchanged.

**TR-03.12 Security (rule 1).**

- No user text reaches either guard. Their inputs are `c(stata_version)` and dash's own constant.
- `_dash_stata_ok` reads its arguments by value in Mata, so a hostile argument is never evaluated (E3: `"19 | 1"` → ok 0).
- The message expands only `floor` and a `%9.1f`-formatted number. Neither name is in `test_security_surface.py`'s `_USER_TEXT_LOCALS`.
- No `shell`, no `python:`, no `eval`.
- The test stubs are defined only inside cscripts and restored before the script continues.

## Boundaries

- **S02 (batch partner) owns:**
  - `scripts/stata_slot.sh`, `run_cert_suite.sh`, `run_release_gate.sh`, `stata_python_exec.sh`, the Makefile and the header of `test/run_all_cscripts.do`;
  - every `scripts/extract_*` and `test/fixtures/twoway_corpus.do`;
  - `regen_option_surface.py`, and every line of `wire_option_reporting.py` except the `HELPER` `version` line;
  - `_STATA_BASE`/`_STATA_PLUS` in `test_help_claims_1.py` and `test_help_claims_8.py`;
  - the runner path guard test and the literal-command pins.

  S03 touches none of these. S03's new test text holds no `arch -arm64` literal and no maintainer path, because S02's guard reads `test/`.
- **Test-side `version 16.0` lines stay.** They are callers, and a version-16 caller is supported: `test/cert_helpers.do:160,183,204`, `test/cert_svg.do` (6), the extractors (S02 owns their paths; P3.7 the rest), and the test programs of `test_by_suboptions`, `test_conformance`, `test_custom_scheme`, `test_help_claims_2` and `test_adversarial` outside the generated region. The pin reads only dash.ado, dash_setup.ado and the two generators.
- **S05 (batch 2) owns:**
  - the Python floor: `_dash_pymin`'s value, `TestTheFloorIsTheTestedBaseline`, dash.pkg:17, `{ul:Python 3.13+}` and dash_setup.sthlp's `{ul:Python}` paragraph;
  - the Python Requires line in CHANGELOG;
  - HON-31..39.

  S03 adds `_dash_statamin` beside `_dash_pymin` without editing it.
- **S25 (batch 9)** owns the dependency guard, after S03's guard and the Mata guard (A154), and `dash_setup`'s first Python call. **S12 (batch 4)** owns the prefix strip and **S22 (batch 8)** the rclass dispatch, both later in `dash`.
- **Not done (M2, residual item 35):**
  - no Stata 14-18.5 binary is run;
  - no `python_exec` is set for 17 or 18;
  - no version-keyed truth, Break fallback or version-dependent advice is built;
  - project rule 10 and the GUI hook are not edited (P1.34.1).

  Stata 19.0, BE and SE are declared, not measured.
- **Not touched:**
  - dash_render.py (no copy-list entry, R2);
  - dash_parse.mata;
  - `_dash_fn_points` beyond its `version` line;
  - the rpcap/rpspike advice beyond its comment;
  - dash.sthlp:1563;
  - BUGS.md's closed entries (:568, :1287 say "version 16" historically and stay);
  - every tracking document (A145).

## Stata truth

No fixture and no extractor: every truth this section needs is measured live, in the same run, by the cases themselves. So there is no `_meta` stamp, no `git add -f` and no `test_fixtures_are_committed.py` change.

**Live truth in the S03 block of `test/test_wp30_truth.cscript`**, run with `WP30_ONLY=S03` through the driver:

- **SF-01, Stata's code for a release it cannot run.**
  - Above S03's header line, define `capture program drop _s03_future` and then `program define _s03_future` / `version 99` / `end`. The program is stored, not run.
  - In the block, `capture _s03_future` then `local sf01 = _rc`. Expected `9` (E3: "this is version 19.5 of StataNow; it cannot run version 99.0 programs").
  - Display the measured code with the case. dash's refusal uses that code: ENV-25, ENV-28 and ENV-29 assert r(9).
- **SF-02, the callerver fallback leaves function points unchanged.** Use `sysuse auto, clear`, `tempname r o`, and Mata `st_strscalar` as FX-06 does. For each of `y = runiform()` and `y = normalden(x)`:
  - `set seed 20261003`, `global dash__uv 16`, `_dash_fn_points `r' -2 2 5 1 `o'`. Save the scalar as `a`.
  - `set seed 20261003`, `macro drop dash__uv`, the same call. Save it as `b`, and `local cv "`._Gr_Global.callerver'"`.
  - Expect `a == b` (compared in Mata, by value: `st_strscalar` equality, so no brace appears in the block's text) and `"`cv'" == "19"`.
  - At `c96facd` the JSON is equal and `cv` is `16`, so the case fails first on `cv`.
- **SF-03, a version-16 caller keeps its own version.** `version 16: dash function y = normalden(x), range(-2 2) n(5) name(sf03)`. Expect `._Gr_Global.callerver == "16"`, and Mata `strpos(st_global("dash_fpts_sf03"), "0.053990966513188049,0.24197072451914334,0.39894228040143265") > 0`. Then `dash clear`. This case is green at `c96facd` and is a guard.
- **SF-04, the certifying Stata is at or above the floor.**
  - Expect `c(stata_version) >= 19`.
  - `capture noisily _dash_require_stata` → rc 0.
  - `capture _dash_stata_ok "`c(stata_version)'" "19"` → `_rc == 0` and `r(ok) == 1`. Every call in the case is under `capture`, so a missing program is a FAIL, never an abort of the script.
  - Display `SF-04: certified on Stata `c(stata_version)' `c(edition_real)'`.
  - At `c96facd` `_dash_require_stata` is r(199) "command _dash_require_stata is unrecognized".

Each case reports through S01's tally helpers: `_w30_expect SF-0n "<cond>" "<msg>"` lines closed by one `_w30_done SF-0n "<msg>"` (TR-01.10.4), so a run with `WP30_ONLY=S03` counts its cases and ends `ALL CHECKS PASSED`. `_s03_future` is the one helper that does not declare `version 19` (TR-01.10.4): its `version 99` is the measurement. It holds no `python:` line and no brace inside a string. It assumes the scaffold loads dash.ado by `do`, as `test_wp29_truth.cscript:44-45` does. If `capture program list _dash_fn_points` is nonzero, SF-02 records a FAIL with "dash.ado is not loaded by do". It never skips.

**The spec probe** (not committed, run twice). Write it as `<scratch>/s03/s03_specs.do`:

```stata
* S03 language-level probe: every dash global and the assembled spec, as text.
adopath ++ "$S03_REPO/"
global dash_nobrowser 1
cd "$S03_REPO/test"
qui do "../dash_parse.mata"
qui do "../dash.ado"
set linesize 255
sysuse auto, clear
set seed 20261003
dash clear
dash scatter mpg weight, name(c01)
dash (scatter mpg weight) (lfit mpg weight if foreign==1), name(c02) title("A") legend(off)
dash scatter mpg weight, by(foreign) name(c03)
dash function y = normalden(x), range(-3 3) name(c04)
dash (function y = runiform(), range(0 1) n(7)) (scatter mpg weight), name(c05)
dash (lpolyci mpg weight) (scatter mpg weight), name(c06)
dash histogram mpg, name(c07)
dash line price weight, sort name(c08) ylabel(, format(%9.0fc))
dash rcap mpg trunk weight, name(c09)
dash scatter mpg weight, colorvar(price) name(c10)
dash bar mpg rep78, name(c11)
dash kpi mean(mpg), title("Avg MPG") name(k1) fmt(%9.1f) update(filter)
version 16: dash scatter price mpg, name(c12)
local sp "$S03_OUT/spec-$S03_TAG.json"
local dp "$S03_OUT/data-$S03_TAG.json"
_dash_prepare_spec, cmdname("dash build") specpath("`sp'") datapath("`dp'") filter(foreign, type(dropdown)) filter(weight, type(range))
mata:
names = sort(st_dir("global", "macro", "dash_*"), 1)
fh = fopen(st_global("S03_OUT") + "/specs-" + st_global("S03_TAG") + ".txt", "w")
for (i = 1; i <= rows(names); i++) fput(fh, names[i] + "=" + st_global(names[i]))
fclose(fh)
end
display "S03-SPECS wrote " "$S03_OUT/specs-$S03_TAG.txt"
```

Its driver, `<scratch>/s03/run_specs_<tag>.do`, is four lines:

```stata
global S03_REPO "<WT>"
global S03_OUT "<scratch>/s03"
global S03_TAG "<tag>"
do "<scratch>/s03/s03_specs.do"
```

Run it as `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s03 <scratch>/s03/run_specs_<tag>.do`, with tag `base` in 03-02 and `sweep` in 03-05. The probe opens with `adopath ++` and sets `$dash_nobrowser` (E5), as the index requires of a probe. The spec writer goes through Python (`_dash_prepare_spec` writes from Python, 0600).

## TDD test stubs

The first stubs are the regression tests that fail at the batch-1 base (`<scratch>/batch-1-base.txt`).

### `test/test_version_floor.py::TestTheStataFloor` (new class, after `TestTheFloorIsTheTestedBaseline`)

Import `_logical_lines` and `_ado_programs` from `test_program_coverage_map` (sys.path already holds `test/`). Add a helper, `_bodies(rel)` → `{program: [logical code lines between its define and end]}`. Constants:

- `_GUARDS = {"_dash_require_stata", "_dash_stata_ok", "_dash_setup_stata"}`
- `_CONSTANTS = {"_dash_statamin", "_dash_pymin"}`

The exempt set is closed; a later section that needs another exemption adds it here with its reason.

- **Test: dash_setup names the Stata floor once.** `TestTheStataFloor::test_dash_setup_names_the_stata_floor_once`. `_dash_statamin` is a program of dash_setup.ado, and its body is exactly `['return local statamin "19"']`. `re.findall(r'return local statamin "([^"]+)"', text)` has one match. Fails at base: no such program.
- **Test: dash.ado holds the same floor.** `::test_dash_ado_holds_the_same_floor`. `_dash_require_stata`'s body contains `local floor <statamin>`. Fails at base.
- **Test: every program declares version 19.** `::test_every_program_declares_version_19`, parametrised over `dash.ado` and `dash_setup.ado`. For each program outside `_GUARDS | _CONSTANTS | {"dash", "dash_setup"}`, `body[0] == "version 19"`. The failure lists every `(program, first)` pair. Fails at base with 79 and 12 pairs (`'version 16.0'`).
- **Test: no version 16.0 line remains.** `::test_no_version_16_line_remains`. `re.search(r"version\s+16\.0", text)` is None in dash.ado, dash_setup.ado, scripts/wire_option_reporting.py and scripts/gen_string_varlists_cscript.py, comments included (the index's gate). Fails at base.
- **Test: the guard is the first statement.** `::test_the_guard_is_the_first_statement_of_dash_and_dash_setup`. `dash`'s body[0] is `_dash_require_stata`, body[1] is `version 19`, and `_dash_require_mata`'s index is greater than 1. `dash_setup`'s body[0] is `_dash_setup_stata`, body[1] is `version 19`, and the first `syntax` line's index is greater than 1. Fails at base.
- **Test: the guards declare no version above 13.** `::test_the_guards_declare_no_version_above_13`. Each of `_GUARDS` has `body[0]` matching `version (\d+(?:\.\d+)?)` with the number at most 13, and no other `version` line. Neither of `_CONSTANTS` has a `version` line. Fails at base.
- **Test: the guards need nothing newer than Stata 13.** `::test_the_guards_need_nothing_newer_than_stata_13`. No guard body matches `\bstrtrim\(|\bustr\w*\(|\bregexm\(|\bpython\b|_dash_say|\bversion\s+(1[4-9]|[2-9]\d)`. The only programs the guards call are `_dash_stata_ok` and `_dash_statamin`: every token of the form `_dash_\w+` at the start of a body line is one of those two. Fails at base.
- **Test: the refusal is r(9) in dash's words.** `::test_the_refusal_is_r9_in_dashs_words`. Both `_dash_require_stata` and `_dash_setup_stata` contain `` display as error "dash requires Stata `floor' or later; this is Stata `` and `exit 9`. Fails at base.
- **Test: every Stata declaration agrees.** `::test_every_stata_declaration_agrees`. With `n = statamin`:
  - dash.pkg holds the line `d Requires: Stata n or later; tested on StataNow 19.5 (MP), macOS arm64.` and `Measured on MP only`;
  - `_flat` of dash.sthlp between `{marker dependencies}` and `{marker author}` holds `Stata n or later; tested on StataNow 19.5 (MP), macOS arm64` and `Measured on MP only`;
  - `_flat(dash_setup.sthlp)` holds both;
  - CHANGELOG's `### Requirements` slice holds `Stata n or later`;
  - every non-exempt program's `version` equals `n`.

  Fails at base.
- **Test: dash_setup reports the Stata line.** `::test_dash_setup_reports_the_stata_line`. dash_setup.ado holds `` display as text "  Stata .............. {res}OK{txt} (version `c(stata_version)')" `` after the first `{hline 60}` display and before `python: import sys; from sfi import Macro; Macro.setLocal("pyver"`. Fails at base.
- **Test: the generators emit version 19.** `::test_the_generators_emit_version_19`. Read wire_option_reporting.py as text and never import it (it runs at import): it holds `program define _dash_report_ignored\n    version 19\n`. Load gen_string_varlists_cscript.py by path as `test_string_plot_variables.py` does: `"    version 19"` is in `_sv_case_program()` and `"version 16.0"` is not in `render()`. Fails at base.
- **Test: the restated comparators match the shipped ones.** `::test_the_restated_comparators_match_the_shipped_ones`. In test_env_guards.cscript, the last restatement of `program define _dash_stata_ok` … `end` has the same logical lines as dash.ado's `_dash_stata_ok`, and the restatement of `_dash_python_ok` (:472-478) has the same logical lines as dash.ado's. Fails at base: no restated `_dash_stata_ok`, and no shipped one.

### `test/test_env_guards.cscript` ENV-24..ENV-29

Append these after ENV-23b, as one contiguous run, before the closing display. At that point the script has `run` dash_parse.mata and `do`ne cert_helpers.do again (:796-798), and dash.ado's programs are global from :97. Update the header's `Tests:` line to "ENV-01 through ENV-29", with one sentence on ENV-24..29.

Each log is opened with `quietly log using "`lg'", replace text name(_e2x)` and read with `cert_file_has "`lg'", needle(…)`. Define every stub before opening the case's log, so its program text is not echoed into the log being searched. Copy `r(ok)`, `r(shown)` and `_rc` into locals before calling `cert_file_has` or `cert_log_has`, because they clobber `r()`.

- **Test: the comparator's table (ENV-24).** `_dash_stata_ok` gives the E3 table:

  | have | want | r(ok) | r(shown) |
  |---|---|---|---|
  | 19.5 | 19 | 1 | 19.5 |
  | 19 | 19 | 1 | 19.0 |
  | 20 | 19 | 1 | 20.0 |
  | 18.5 | 19 | 0 | 18.5 |
  | 17 | 19 | 0 | 17.0 |
  | 15.1 | 19 | 0 | 15.1 |
  | "" | 19 | 0 | . |
  | abc | 19 | 0 | . |
  | "19 \| 1" | 19 | 0 | . |
  | 19.5 | "" | 0 | 19.5 |

  `display "ENV-24 PASS: the floor comparator answers by value, 1 at or above, 0 below or unreadable"`. At base: r(199), "command _dash_stata_ok is unrecognized".
- **Test: the refusal's words and code (ENV-25).**
  - Stub `_dash_stata_ok` as `rclass` with `version 13`, `return local shown "18.5"`, `return scalar ok = 0`. Log `capture noisily _dash_require_stata`.
  - Expect rc 9, and the log holds `dash requires Stata 19 or later; this is Stata 18.5`.
  - Repeat with shown `17.0`.
  - Restore the shipped body, restated verbatim (TR-03.1).
- **Test: the silent pass (ENV-26).** With the real comparator, `capture noisily _dash_require_stata` under no prefix, `version 16:` and `version 13:` gives rc 0 each time, and the log holds no `dash requires`.
- **Test: a version-16 caller, both modes (ENV-27).**
  - `version 16: dash scatter mpg weight, saving("`f'_v16.html") replace` gives rc 0 and the file exists.
  - `dash clear`, then `version 16: dash scatter mpg weight, name(e27)`, then `version 16: dash build, saving("`f'_v16.py") server replace` gives rc 0 and the file exists. `f` is under `c(tmpdir)`.
  - `dash clear`; erase both files (`capture erase`), so the case leaves nothing behind.
- **Test: every route refused before anything (ENV-28).** Stub the comparator as in ENV-25 (shown `18.5`). With one log open, run each of these with `capture noisily`:
  - `dash scatter mpg weight, saving("`f'_28i.html") replace`
  - `dash scatter mpg weight, name(e28)`
  - `dash kpi mean(mpg), name(k28)`
  - `dash build, saving("`f'_28.html") replace nobrowser`
  - `dash build, saving("`f'_28.py") server replace`
  - `dash serve, port(5098) timeout(1) nobrowser`
  - `dash clear`

  Expect:
  - each rc is 9;
  - `${dash_graph_registry}` is `""`;
  - none of the three files exists;
  - the log holds the refusal on seven lines (`cert_log_has … , needle("dash requires Stata 19 or later; this is Stata 18.5")` gives `r(count) == 7`) and no `starting Bokeh Server`.

  Restore the shipped body and run `dash clear`.
- **Test: dash_setup's guard (ENV-29).** `quietly do "../dash_setup.ado"`, then:
  - **a.** `_dash_statamin` gives `r(statamin) == "19"`.
  - **b.** `capture noisily _dash_setup_stata` gives rc 0 and logs nothing.
  - **c.** Stub `_dash_statamin` to return `"99"`. Log `capture noisily dash_setup`. Expect rc 9; the log holds `dash requires Stata 99 or later; this is Stata ` followed by `strtrim(string(c(stata_version), "%9.1f"))`; and the log holds no `checking dependencies`.
  - **d.** Restore `_dash_statamin`, restated verbatim.

  `display "ENV-29 PASS: …"`.

### `test/test_wp30_truth.cscript`, S03 block

These are SF-01..SF-04 as "Stata truth" gives them. At base, SF-02 fails on `cv` (`16`) and SF-04 on r(199). SF-01 and SF-03 pass and are guards.

### `test/test_program_coverage.cscript` PC-15 (in place)

**Test: dash_setup reports Stata OK.** Add `"Stata .............. OK (version"` to the `foreach p in …` list at :684. It fails at base with `assert r(found) == 1` false. (`_pc_said` is a by-value search of the logical lines.)

### Mutation table (what each mutation fails)

| Mutation | Fails |
|---|---|
| guard moved after `version 19` in `dash` | `test_the_guard_is_the_first_statement…` |
| `version 19` reverted in one program | `test_every_program_declares_version_19`; ENV and SF stay green |
| guard declares `version 19` | `test_the_guards_declare_no_version_above_13` |
| `strtrim(` used in a guard | `test_the_guards_need_nothing_newer_than_stata_13` |
| `exit 198` instead of 9 | `test_the_refusal_is_r9…`, ENV-25, ENV-28, ENV-29c |
| floor 18 in dash.ado only | `test_dash_ado_holds_the_same_floor`, `test_every_stata_declaration_agrees` |
| comparator `>` instead of `>=` | ENV-24 (19 vs 19) |
| comparator evaluates its text | ENV-24 (`"19 \| 1"` → 1) |
| OK line removed | `test_dash_setup_reports_the_stata_line`, PC-15 |
| generator reverted | `test_the_generators_emit_version_19`, `test_the_region_is_current` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| The floor's text pins, order, exemptions and generators | pytest `test/test_version_floor.py -k TestTheStataFloor -n0` | none | n/a (static) |
| The comparator, refusal, silence and dash_setup guard | cscript `test_env_guards.cscript` ENV-24..29, through the driver | none | ENV-27 builds the saved page and the served app; ENV-28 refuses every route of both |
| Stata's version-refusal code; callerver fallback; version-16 caller; certifying release | cscript `test_wp30_truth.cscript`, `WP30_ONLY=S03`, SF-01..04 | none (live) | the spec both modes read |
| dash_setup's OK line through a real run | cscript `test_program_coverage.cscript` PC-15 | none | n/a |
| Language level leaves specs and points unchanged | scratch spec probe, before and after, `diff` | none | yes: the shared spec; renderer untouched |
| Production-context comparator at level 19; caller at 16 | cscript `test_setup_python_gate.cscript` (flipped `_gate19`, kept `_gate16`) | none | n/a |
| Callers at version 16 | cscript `test_caller_version.cscript` CV-01..11 (unchanged) | none | CV-07 builds |
| Function layers | cscript `test_parser.cscript` FX-01..FX-11 (unchanged) | none | yes |
| Generated region current | pytest `test_string_plot_variables.py::TestTheGeneratedRegion`; cscript `test_adversarial.cscript` | none | n/a |
| Registries | pytest `test_program_coverage_map.py`, `test_no_orphans.py`, `test_cscript_hygiene.py`, `test_security_surface.py -k UserText` | none | n/a |
| Help and package text | pytest `test_help_claims_8.py`, `test_help_conformance.py`, `test_pkg_metadata.py`, `test_packaging.py` | none | n/a |
| Whole Stata surface at level 19 | `make cert` in batch 1's G8 (orchestrator) | all | yes |

**Acceptance criteria.**

- **AC-03.1** `python3 -m pytest test/test_version_floor.py -q -n0` passes all tests: the 12 new ones and the existing ones.
- **AC-03.2** Through the driver, `test_env_guards.cscript` prints `ENV-24 PASS` … `ENV-29 PASS` and `All environment guard tests PASSED.`.
- **AC-03.3** `WP30_ONLY=S03` on `test_wp30_truth.cscript` prints SF-01..SF-04 PASS and `test_wp30_truth: ALL CHECKS PASSED`, with no FAIL and no SKIP.
- **AC-03.4** `test_program_coverage.cscript` prints `PC-15 PASS`. `test_setup_python_gate.cscript` prints `ALL TESTS PASSED`. `test_caller_version.cscript` prints CV-01..CV-11 PASS.
- **AC-03.5** `diff <scratch>/s03/specs-base.txt <scratch>/s03/specs-sweep.txt` and `diff <scratch>/s03/spec-base.json <scratch>/s03/spec-sweep.json` print nothing.
- **AC-03.6** `grep -c 'version 16.0' dash.ado dash_setup.ado` prints `0` and `0`. `grep -cE '^\s*version 19$' dash.ado dash_setup.ado` prints `79` and `12`. `python3 scripts/gen_string_varlists_cscript.py --check` reports the region current.
- **AC-03.7** The full suite, run once through the queue in the worktree, has 0 failed (E6 for the known flaky tests).
- **AC-03.8** Batch 1's `make cert` (G8) is green. That is the orchestrator's run; a red result returns to this entry's fix cycle in a fresh S03 worktree.

## Tasks

**Commit boundary.** Tasks 03-01 to 03-11 form the one commit of entry P1.35. Its subject is `Declare and enforce a Stata 19 floor and raise every program to version 19 (WP-30 P1.35)`, made by 03-11 on `wp30-s03` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s03` (`$WT`), after one full run through the queue.

The help update (03-09) is part of that commit. The body:

1. opens with `<scratch>/03-P1.35-failure.txt`;
2. then gives the measured defect: 91 `version 16.0` statements, no Stata floor stated or enforced, only StataNow 19.5 measured;
3. then says what changed and where;
4. then carries one line each:
   - `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-1 base sha> with <text>` for each of the 12 pytest tests, and `Regression: test/test_env_guards.cscript ENV-24 -- failed at <sha> with r(199) command _dash_stata_ok is unrecognized`, and the same for SF-02, SF-04 and PC-15;
   - `Flipped:` lines from `<scratch>/s03/03-flips.txt`;
   - `Fixture: none (measured live: test_wp30_truth.cscript SF-01..SF-04)`;
   - `BUGS.md: "<title>" (closed)`.

No message, BUGS line, CHANGELOG line or help line names a tool or vendor (G7). Every command runs from `$WT`; `S=<scratch>/s03` (`mkdir -p "$S"`). A cscript runs only through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`), prefixed `WP30_ONLY=S03` for the truth script.

<task type="auto" id="03-01">
  <name>Write the failing floor regression tests</name>
  <files>test/test_version_floor.py, test/test_env_guards.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Add class `TestTheStataFloor` to `test/test_version_floor.py` after `TestTheFloorIsTheTestedBaseline` (:59-155), before `TestTheGeneratedAppEvaluatesNoAnnotationAtImport` (:157), with the twelve tests, the `_bodies` helper, `_GUARDS` and `_CONSTANTS` exactly as "TDD test stubs" names them, importing `_logical_lines` and `_ado_programs` from `test_program_coverage_map`.
    Append ENV-24..ENV-29 to `test/test_env_guards.cscript` after ENV-23b's display (:817) and before `display "All environment guard tests PASSED."`, as stated in "TDD test stubs". Each case ends with a literal `display "ENV-2n PASS: …"`. Each stub is followed by the shipped body restated verbatim from TR-03.1 / TR-03.4. Update the header's `Tests:` line.
    In S03's stub block of `test/test_wp30_truth.cscript`, write SF-01..SF-04 between its start and end display lines and `_s03_future` directly above its header, as "Stata truth" gives them.
    Run `python3 -m pytest test/test_version_floor.py -q -n0 -p no:cacheprovider -rf > "$S/03-01-pytest.log" 2>&1`, the driver for `test_env_guards.cscript`, and the driver for `test_wp30_truth.cscript` with `WP30_ONLY=S03`.
    Write `<scratch>/03-P1.35-failure.txt`: the base sha (`cat <scratch>/batch-1-base.txt`), each failing pytest node with its assertion line, the first failing cscript line of each script, and the guard cases that passed (SF-01, SF-03). Do not commit. Edit no shipped file.
  ]]></action>
  <verify><![CDATA[`grep -c "^FAILED" "$S/03-01-pytest.log"` prints 13 (twelve tests; `test_every_program_declares_version_19` is two nodes); `grep -c "unrecognized" "$S/run_test_env_guards.log"` is at least 1 and `grep -c "ENV-24 PASS" "$S/run_test_env_guards.log"` prints 0; `grep -c "SF-02 FAIL" "$S/run_test_wp30_truth.log"` and `grep -c "SF-04 FAIL" "$S/run_test_wp30_truth.log"` each print at least 1 and `grep -cE "SF-0[13] PASS" "$S/run_test_wp30_truth.log"` prints 2; `test -s <scratch>/03-P1.35-failure.txt`.]]></verify>
  <done>Every regression test of the floor existed and was shown failing on the unmodified tree, with the failure text saved for the commit body.</done>
</task>

<task type="auto" id="03-02">
  <name>Extend PC-15 and record the spec baseline</name>
  <files>test/test_program_coverage.cscript</files>
  <action><![CDATA[
    In `test/test_program_coverage.cscript` PC-15, add `"Stata .............. OK (version"` as the first item of the `foreach p in …` list (:684), keeping the `///` continuations. Change nothing else. Run its driver and append the PC-15 failure (`assertion is false` after `_pc_said "Stata .............. OK (version"`) to `<scratch>/03-P1.35-failure.txt`.
    Create `$S/s03_specs.do` with the exact text of "Stata truth / The spec probe". Create `$S/run_specs_base.do` with `S03_REPO` = `$WT`, `S03_OUT` = `$S` and `S03_TAG` = `base`. Run it through `scripts/stata_slot.sh "$S" "$S/run_specs_base.do"` on the unmodified tree.
    Copy the impact record's UNKNOWN rows for `dash`, `dash_setup`, `_dash_fn_points` and `_dash_pymin` from `<scratch>/batch-1-impact.txt` into `$S/03-impact.txt` beside Evidence E9's grep counts. Report any HIGH or CRITICAL result for this section's symbols to the orchestrator before editing.
  ]]></action>
  <verify><![CDATA[`grep -c "PC-15 PASS" "$S/run_test_program_coverage.log"` prints 0; `grep -c "S03-SPECS wrote" "$S/run_specs_base.log"` prints 1; `test -s "$S/specs-base.txt" && test -s "$S/spec-base.json"`; `test -s "$S/03-impact.txt"`.]]></verify>
  <done>dash_setup's missing Stata line was shown failing, and the specs and globals of the unmodified tree were recorded for the sweep's comparison.</done>
</task>

<task type="auto" id="03-03">
  <name>Add dash's Stata guard and comparator</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In dash.ado, after `_dash_require_python`'s `end` (:215) and before the `_dash_require_mata` header (:218), add `_dash_stata_ok` and `_dash_require_stata` with their headers, exactly as TR-03.1 and TR-03.2 give them (`version 13`, by-value Mata reads, `local floor 19`, the message, `exit 9`).
    In `dash` (:84), insert above `version 16.0` a three-line comment ("WP-30 P1.35: the Stata floor first, before `version', so an older Stata is refused in dash's words; then the Mata guard, the dependency guard, the prefix strip, the rclass dispatch (A154).") and the statement `_dash_require_stata`.
    Do not change the `version` lines yet, and nothing else in `dash`.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_env_guards.cscript` prints `ENV-24 PASS` through `ENV-28 PASS` and stops at ENV-29 (`_dash_statamin` is unrecognized until 03-04); `grep -c "dash requires Stata 19 or later; this is Stata 18.5" "$S/run_test_env_guards.log"` is at least 1.]]></verify>
  <done>dash refused a Stata below 19 as its first act, in dash's words with r(9), through a by-value comparator a certification script could reach on 19.5.</done>
</task>

<task type="auto" id="03-04">
  <name>Add dash_setup's guard and Stata line</name>
  <files>dash_setup.ado</files>
  <action><![CDATA[
    In dash_setup.ado, after `_dash_pymin`'s `end` (:500) and before `program define _dash_pyver_ok` (:502), add `_dash_statamin` (rclass, no `version`, `return local statamin "19"`, with the docstring of TR-03.4) and `_dash_setup_stata` (`version 13`) exactly as TR-03.4 gives them.
    In `dash_setup` (:19), insert above `version 16.0` a two-line comment naming WP-30 P1.35 and the statement `_dash_setup_stata`.
    After `display as text "{hline 60}"` (:64), add the display line of TR-03.5 (14 dots).
  ]]></action>
  <verify><![CDATA[Through the driver, `test_env_guards.cscript` prints `ENV-29 PASS` and `All environment guard tests PASSED.`; `test_program_coverage.cscript` prints `PC-15 PASS`; `test_setup_honesty.cscript` reports no FAIL.]]></verify>
  <done>dash_setup refused a Stata below 19 before anything else and reported the Stata release as its first OK line, from one named constant beside the Python one.</done>
</task>

<task type="auto" id="03-05">
  <name>Sweep every version line to 19</name>
  <files>dash.ado, dash_setup.ado</files>
  <action><![CDATA[
    In dash.ado and dash_setup.ado replace every line matching `^\s*version 16\.0\s*$` by the same indentation plus `version 19`: 79 and 12 lines. Use `perl -pi -e 's/^(\s*)version 16\.0\s*$/$1version 19\n/' dash.ado dash_setup.ado`, then read the diff: every hunk must be one such line.
    Reword the comment at dash_setup.ado:521 and the comment at dash.ado:3496 as TR-03.6 says, so that no `version 16.0` text remains.
    Create `$S/run_specs_sweep.do` (tag `sweep`) and run it through the slot. Then diff both outputs against the base. Any difference stops the section: report it, never adjust the probe.
  ]]></action>
  <verify><![CDATA[`grep -c 'version 16.0' dash.ado dash_setup.ado` prints `dash.ado:0` and `dash_setup.ado:0`; `grep -cE '^\s*version 19$' dash.ado dash_setup.ado` prints 79 and 12; `diff "$S/specs-base.txt" "$S/specs-sweep.txt" && diff "$S/spec-base.json" "$S/spec-sweep.json" && echo SAME` prints `SAME`; `WP30_ONLY=S03` on `test_wp30_truth.cscript` prints SF-01..SF-04 PASS.]]></verify>
  <done>Every program of dash and dash_setup declared version 19, and the specs, globals and function points dash writes were byte-identical to the unmodified tree's.</done>
</task>

<task type="auto" id="03-06">
  <name>Make both generators emit version 19</name>
  <files>scripts/wire_option_reporting.py, scripts/gen_string_varlists_cscript.py, test/test_adversarial.cscript</files>
  <action><![CDATA[
    In `scripts/wire_option_reporting.py`, change only `    version 16.0` inside `HELPER` (:115) to `    version 19`. Do not run the script.
    In `scripts/gen_string_varlists_cscript.py` `_sv_case_program` (:226), change `"    version 16.0",` to `"    version 19",`.
    Run `python3 scripts/gen_string_varlists_cscript.py` (rewrite mode, pure Python), which rewrites only the marked region of `test/test_adversarial.cscript`. Then run `--check`. Check with `git diff --stat test/test_adversarial.cscript` that the only change is the one `_sv_case` line. Record its `Flipped:` line in `$S/03-flips.txt`: "test/test_adversarial.cscript _sv_case (generated) -- version 16.0 was the generator's level; it now emits dash's level, 19".
  ]]></action>
  <verify><![CDATA[`python3 scripts/gen_string_varlists_cscript.py --check` prints `region is current (87 cases)`; `git diff --numstat test/test_adversarial.cscript` prints `1	1`; `python3 -m pytest test/test_string_plot_variables.py test/test_version_floor.py -q -n0 -p no:cacheprovider -k "GeneratedRegion or generators"` passes.]]></verify>
  <done>Neither generator could write a version 16.0 line again, and the generated region matched its generator.</done>
</task>

<task type="auto" id="03-07">
  <name>Flip the cscripts that model the level</name>
  <files>test/test_setup_python_gate.cscript, test/test_caller_version.cscript, test/test_env_guards.cscript</files>
  <action><![CDATA[
    In `test/test_setup_python_gate.cscript`, rename the first wrapper (:111-116) to `_gate19`, with `version 19`. Its seven calls (:118-130) use `_gate19`, with labels `v19: …`, and `capture program drop _gate19` follows them. The comment above it says dash_setup declares 19 since WP-30. Keep the second block (:152-161) as `_gate16` at `version 16.0`, with a one-line comment: "a caller at version 16 is still supported on Stata 19 (WP-30 P1.35)".
    In `test/test_caller_version.cscript`, reword :5 to "dash's programs declare their own version (19 since WP-30), but …" and :14 to "a do-file that begins `version 16' -- once dash's declared minimum, still a supported caller on Stata 19, and the first line of many do-files --". Change no case.
    In `test/test_env_guards.cscript`, change the restated `_dash_python_ok`'s `version 16.0` (:474) to `version 19`.
    Append one `Flipped:` line per file to `$S/03-flips.txt`, each saying the old line modelled dash_setup's or dash's level 16.0, which is now 19.
  ]]></action>
  <verify><![CDATA[Through the driver: `test_setup_python_gate.cscript` ends `ALL TESTS PASSED`; `test_caller_version.cscript` prints `CV-01 PASS` … `CV-11 PASS` (11 lines, counted with `grep -cE "CV-[0-9]+[a-z]? PASS"`); `test_env_guards.cscript` ends `All environment guard tests PASSED.`; `python3 -m pytest test/test_version_floor.py -q -n0 -p no:cacheprovider -k restated` passes; `wc -l < "$S/03-flips.txt"` prints 4.]]></verify>
  <done>The cscripts that modelled dash's language level modelled 19, one caller-at-16 case was kept in each setup and caller script, and every change was recorded as a flip.</done>
</task>

<task type="auto" id="03-08">
  <name>Register the four new programs</name>
  <files>test/program_coverage_map.py</files>
  <action><![CDATA[
    Under the S03 anchor comment `# WP-30 S03 (P1.35): …` at the end of `COVERAGE["dash.ado"]`, add `"_dash_require_stata"` and `"_dash_stata_ok"`. Under the S03 anchor at the end of `COVERAGE["dash_setup.ado"]`, add `"_dash_setup_stata"` and `"_dash_statamin"`. Use the references of TR-03.9, alphabetical within each anchor, each with a one-line comment saying what the first case asserts (direct or e2e). Edit no other entry.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py test/test_cscript_hygiene.py test/test_file_headers.py -q -n0 -p no:cacheprovider` reports 0 failed; `python3 -m pytest test/test_security_surface.py -q -n0 -p no:cacheprovider -k "UserText"` passes.]]></verify>
  <done>Every new Stata program was mapped to a case that displays its id, and the registry, orphan, hygiene and echo guards were green.</done>
</task>

<task type="auto" id="03-09">
  <name>State the floor in package and help</name>
  <files>dash.pkg, dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
    In dash.pkg, insert the two lines of TR-03.8 directly above `d Requires: Python 3.13+, bokeh>=3.8, numpy>=2.3, pandas>=2.3.` (:17), which stays verbatim.
    In dash.sthlp's Dependencies, insert TR-03.8's `{phang2}{ul:Stata} …` paragraph above `{phang2}{ul:Python 3.13+}` (:3787).
    In dash_setup.sthlp's Dependencies, insert TR-03.8's `{pstd}{ul:Stata}` paragraph between `{title:Dependencies}` (:123) and `{pstd}{ul:Python}` (:125).
    Edit no other paragraph (R3). Run the help and package tests and the new agreement test. Any help-claims pin that quotes a changed paragraph is updated with the reason, never deleted.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_version_floor.py test/test_help_claims_8.py test/test_help_conformance.py test/test_pkg_metadata.py test/test_packaging.py test/test_installed_layout.py -q -n0 -p no:cacheprovider` reports 0 failed, `TestTheStataFloor` included (13 nodes passed).]]></verify>
  <done>dash.pkg and both help files stated Stata 19 or later, tested on StataNow 19.5 (MP), macOS arm64, measured on MP only, in the same words the floor test pins.</done>
</task>

<task type="auto" id="03-10">
  <name>Certify the floor through the slot</name>
  <files>none</files>
  <action><![CDATA[
    Run through the driver, at most three at once (the slot enforces it), each with its own log:
    - `test_env_guards`, `test_wp30_truth` (with `WP30_ONLY=S03`), `test_program_coverage`, `test_setup_python_gate`, `test_setup_honesty`;
    - `test_caller_version`, `test_parser` (FX cases), `test_adversarial` (the regenerated SV region), `test_e2e_single`.
    Do not run `run_all_cscripts.do` or `make cert`: the full certification of the sweep is batch 1's G8.
    A `SKIP: Python not available` line means `python_exec` was dropped from `~/.stata19/console/stata19.rc` by concurrent sessions. Restore nothing yourself; report it and re-run that script alone, since a skip is not a pass.
    Write the PASS counts per script to `$S/03-cert.txt`.
  ]]></action>
  <verify><![CDATA[Every listed log has no line matching ` FAIL\b|^r\([0-9]+\);$|SKIP` (`grep -cE " FAIL\b|^r\([0-9]+\);$|SKIP" "$S"/run_test_*.log` prints 0 for each); `test_wp30_truth` prints SF-01..SF-04 PASS; `test_env_guards` prints ENV-24..ENV-29 PASS.]]></verify>
  <done>Stata itself certified the guards, the refusal, the version-16 caller in both modes and the unchanged function points, and the scripts nearest the language level stayed green.</done>
</task>

<task type="auto" id="03-11">
  <name>Close P1.35 and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.35"]`. Close that BUGS.md entry in place (`- [x]`) with this Resolution (date `<ddmonyyyy>` of the commit):
    `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.35). dash.ado's 79 and dash_setup.ado's 12 programs declare version 19 (were 16.0), and scripts/wire_option_reporting.py and scripts/gen_string_varlists_cscript.py emit it. dash calls _dash_require_stata and dash_setup calls _dash_setup_stata as their first statement; both declare version 13 and refuse a Stata below 19 with "dash requires Stata 19 or later; this is Stata X.Y" and r(9), Stata's own code for a version it cannot run. _dash_stata_ok compares by value, and _dash_statamin names the floor beside _dash_pymin. dash_setup reports "Stata .............. OK". dash.pkg and both help files state Stata 19 or later, tested on StataNow 19.5 (MP), macOS arm64, measured on MP only. The saved page and the served app are both built behind the guard; the served child is Python and reads no Stata version. The specs dash writes are byte-identical at the new level, and the function-layer callerver fallback reads 19 with the points unchanged. The rpcap/rpspike advice and Break below 18.5 are moot at this floor: those plot types are Stata 19's, and sfi.BreakError is in 18.5 and later. Pinned by test/test_version_floor.py::TestTheStataFloor::test_every_program_declares_version_19, test/test_version_floor.py::TestTheStataFloor::test_the_guard_is_the_first_statement_of_dash_and_dash_setup, test/test_version_floor.py::TestTheStataFloor::test_every_stata_declaration_agrees, test/test_env_guards.cscript ENV-24, test/test_env_guards.cscript ENV-28, test/test_env_guards.cscript ENV-29, test/test_wp30_truth.cscript SF-02. Residual, deferred (WP-30): Stata 19.0, BE and SE are declared, not measured; Stata 16-18.5 are refused, not certified (the platform package).`
    Delete the `"P1.35"` key line from `WP30_OPEN`.
    In CHANGELOG.md, replace the marker at the end of `### Requirements` in place with: `- Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64, and measured on MP only. Every dash and dash_setup program declared version 16.0, which implied Stata 16 support that was never tested; all 91 now declare version 19. (WP-30, P1.35)`
    Replace the marker at the end of `### Changed behaviour (may need your do-files changed)` with: `- On a Stata older than 19, dash and dash_setup stop before doing anything else with "dash requires Stata 19 or later; this is Stata 18.5" (the running release) and r(9). Stata 16-18.5 used to run dash untested, and Stata 14-15 stopped with Stata's own "cannot run version 16.0 programs". A do-file that sets version 16 or 17 on Stata 19 is unaffected. (WP-30, P1.35)`
    Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Then run `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run, `<scratch>/full_suite_queue.sh "$WT" <scratch>/03-full-1.log`, waited for on its `exit=` line.
    Stage only: dash.ado, dash_setup.ado, dash.pkg, dash.sthlp, dash_setup.sthlp, BUGS.md, CHANGELOG.md, scripts/wire_option_reporting.py, scripts/gen_string_varlists_cscript.py, test/test_version_floor.py, test/test_env_guards.cscript, test/test_wp30_truth.cscript, test/test_program_coverage.cscript, test/test_setup_python_gate.cscript, test/test_caller_version.cscript, test/test_adversarial.cscript, test/program_coverage_map.py, test/test_tracking_documents.py. Check `git diff --cached --name-only` against that list (G6). It must hold no project instructions file, .gitignore, AGENTS.md, `.ultraplan/` or scratch file.
    Write the message to `$S/03-message.txt` in the boundary's form and run G7 on it. Confirm `git branch --show-current` prints `wp30-s03`, commit with `git commit -F "$S/03-message.txt"`, and run G7 on `git log -1 --format=%B`. Report the sha to the merger.
  ]]></action>
  <verify><![CDATA[The full run's log shows 0 failed; `grep -c '<!-- WP-30 P1.35 -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.35": "' test/test_tracking_documents.py` prints 0 (TR-01.10.1's key-deletion check; `WP30_LISTS`/`WP30_SECTION` keep their rows); `git log -1 --format=%s | grep -c '(WP-30 P1.35)$'` prints 1; G7 on `git log -1 --format=%B` prints 0; `git show --name-only --format= HEAD | wc -l` prints 18, plus one for each help-claims file 03-09 had to update (named in the commit body).]]></verify>
  <done>P1.35 was closed in BUGS.md naming existing tests, its two CHANGELOG markers carried the floor and the refusal, and one green commit on wp30-s03 was ready for the merger.</done>
</task>

## Section completion criteria

- On Stata below 19 (reached on 19.5 through stubs), every `dash` route and `dash_setup` stop first, with `dash requires Stata 19 or later; this is Stata X.Y` and r(9). Nothing is registered, written, served or installed. On 19.5, dash's check is silent and `dash_setup` prints `Stata .............. OK (version 19.5)`.
- All 91 statements read `version 19`. The guards and constants are the only exceptions, and declare `version 13` or none. No `version 16.0` text remains in dash.ado, dash_setup.ado or the two generators, and the generated region is current.
- The spec probe is identical before and after the sweep, and SF-02 shows the function points unchanged with the fallback at 19.
- dash.pkg, both help files and CHANGELOG state one floor, 19, with "tested on StataNow 19.5 (MP), macOS arm64" and "Measured on MP only".
- `TestTheStataFloor` (12), ENV-24..29, SF-01..04 and PC-15 pass. CV-01..11, FX-01..11 and `test_setup_python_gate` pass unchanged or flipped as listed.
- One green commit `(WP-30 P1.35)` exists on `wp30-s03`, with its failure text, `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines and no tool or vendor name. The entry is closed in place, its key deleted and both markers replaced.
- Batch 1's G8 `make cert` (orchestrator) is green after S02 and S03 land. `grep -c 'version 16.0' dash.ado dash_setup.ado` then prints 0 and 0 in the main checkout.

## Notes

**Traps.**

- **Two guards, on purpose (E4).** A program defined inside an autoloaded ado-file is reachable only from that file, and the scripts that `do` both files would refuse a shared name with r(110). Never "deduplicate" by calling one file's guard from the other.
- **The guards run on the Stata they refuse.** Keep them at `version 13` with Stata-13 functions only: no `strtrim`, no `ustr*`, no `regexm`, no `_dash_say`, no call to a `version 19` program. `_dash_statamin` has no `version` line for the same reason.
- **The `version 16.0` count includes comments.** dash_setup.ado:521's docstring must be reworded, or the index's gate prints 1. dash.ado:2817 ("version 16 or 17") and :6293 ("`version 16'") do not match `version 16.0` and stay.
- **`cert_file_has` clobbers `r()`.** In ENV-24..29, copy `r(ok)`, `r(shown)` and `_rc` into locals before any log search.
- **Restate, never re-`do`.** Re-`do`ing dash.ado over programs in memory is r(110). After each stub, restate the shipped body verbatim. `test_the_restated_comparators_match_the_shipped_ones` catches drift.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. Scripts then exit 222, and a SKIP is not a pass (E5 of the index; never set it `permanently` yourself; report it).
- **A cscript stops at its first failing assert.** The red-first text of `test_env_guards` and PC-15 shows only the first failure, which is expected.
- **Do not run `wire_option_reporting.py`.** It rewrites dash.ado, and after S02 it refuses anyway. Its pin reads the file as text.
- **The callerver fallback** is reached only by direct internal calls (`_dash_plot` has one caller, `dash`, which sets `$dash__uv` first). Production callers keep the user's version.

**Merge rules touched.**

- **R1:** ENV-24..29 are one contiguous run at the end of `test_env_guards.cscript`'s last case block. S25 appends after them in batch 9. S03's block in `test_wp30_truth.cscript`, with `_s03_future` above its header. PC-15 is an in-place extension of a named case.
- **R2:** no copy-list change. `program_coverage_map.py` entries go under the S03 anchors only.
- **R3:** only the Dependencies paragraphs of dash.sthlp and dash_setup.sthlp. S05 (batch 2) writes after S03's `{ul:Stata}` paragraph.
- **R4:** the two P1.35 markers.
- **R5:** BUGS.md's P1.35 entry in place, and the `"P1.35"` key line.
- **R6:**
  - every program after S03 opens with `version 19`, which `test_every_program_declares_version_19` enforces;
  - A154's order is `_dash_require_stata`, `version 19`, `_dash_require_mata`, then S25, S12 and S22. The first-statement test reads only the first two statements of `dash` and the position of `_dash_require_mata`, so their later insertions do not trip it.
- **R9:** four `Flipped:` lines (E10).
- **R10:** no combined pin moves. `test_program_coverage_map.py`'s floors (`>= 56`, `>= 7`) are unaffected.

**Merge with S02 (lands first).** S02 changes `wire_option_reporting.py`'s REPO line (:9) and adds a refusal before any write. S03's hunk is the `HELPER` line (:115) alone, so `git apply -3` merges them. If S02 restructures the file so that `HELPER` moves, the merger keeps S02's text and re-applies `version 19` to the emitted `_dash_report_ignored` line, then names it in `batch-1-merge.log`.

**Commit body line forms** are BRIEF's with WP-30 ids (index deltas): `Regression: … -- failed at <batch-1 base sha> with <text>`, `Flipped: <node> -- <old> was wrong because <why>`, `Fixture: none (…)`, `BUGS.md: "<title>" (closed)`.

**Notes for later sections.**

- **S05.** `TestTheStataFloor` sits beside `TestTheFloorIsTheTestedBaseline` in `test_version_floor.py`; edit only the Python class. dash.pkg's Python Requires line stays on its own line (:19 after S03). In `test_setup_python_gate.cscript` the production-context wrapper is `_gate19` and the caller case `_gate16`.
- **S12, S22, S25.** Insert after `_dash_require_mata` in `dash` (A154). S25's dash_setup changes go after the Stata OK line.
- **Every section.** A new program opens with `version 19`. A program that must run before the guard on an older Stata is a new exemption: add it to `_GUARDS` or `_CONSTANTS` with its reason.

**Notes for the closeout (S58; A145).**

- **GAPS2.**
  - **H-intro-stataver** is closed by declaration: the intro's "Stata 16+" becomes "Stata 19 or later, refused below".
  - **J8 part e** is closed: the `version` statements now declare the measured floor, stated in dash.pkg and both help files. J8's author, README, licence and Jump To parts stay open.
  - **K3 part d** is closed by declaration: the help says tested on StataNow 19.5 (MP), macOS arm64, measured on MP only. K3's generator parts stay with P3.7.
  - Tracked lines: `Closed in WP-30, BUGS.md "<title>", commit <sha>`.
- **ROADMAP.**
  - The WP-30 P1.35 row.
  - ROADMAP.md:4750 ("Stata before 19 (the package's non-goals)") becomes "Stata before 19 is refused (WP-30 P1.35)".
  - The platform package carries the manifest's item-35 residual: certifying Stata 16-18.5 (version-parametrised runners, version-keyed truth, a Break fallback below 18.5, version-dependent rpcap/rpspike advice), and any measurement of Stata 19.0, BE or SE.
- **DROPIN-REMAINING.md P1.35 row:** closed under M2 (declared and enforced floor 19), with the sha.
- **AGENTS.md invariant** (E7: only if it has no uncommitted edits): "Every program in dash.ado and dash_setup.ado opens with `version 19`, except the Stata guards (`_dash_require_stata`, `_dash_stata_ok`, `_dash_setup_stata`: version 13) and the constants (`_dash_statamin`, `_dash_pymin`). The guard is the first statement of `dash` and `dash_setup` (test_version_floor.py::TestTheStataFloor)."
- **BUGS.md:1287-1291** (WP-19's closed entry) calls version 16 "dash's own declared minimum". It is historical and left as written.

**Line numbers** are `c96facd`'s. S01 lands before this section and edits none of dash.ado, dash_setup.ado, dash.pkg or the help. The test-file anchors it adds (`test_wp30_truth.cscript`, the map anchors, `WP30_OPEN`) are found by their text.
