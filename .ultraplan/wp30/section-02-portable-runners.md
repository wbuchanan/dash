# Section 02: Portable runners (P1.34 under M4)

> Part of: WP-30 · Items: P1.34 (entry `P1.34`) · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: 04, 05, 10, 11, 19, 40, 42, 56 · Tasks: 18, 1 commit · Case prefix: RR

## Review amendments

- Blocker: the S02 block kept its own tally (`_s02_expect`, `$s02_nfail`, `exit 9`), so `$w30_ncase` stayed 0 and every `WP30_ONLY=S02` run (02-07, 02-17, AC-02.2, the clean copy) ended "no case ran", r(9); TR-02.14 and 02-01 now report through S01's `_w30_expect`/`_w30_done` with no `exit` in the block (TR-01.10.4).
- Blocker: 02-03's base acceptance ran `WP30_ONLY=S02`, which at the base is S01's stub and ends r(9), so the "verdict rc=0" it records could not occur; the broken form now runs `WP30_ONLY=S01` (TF-01, independent of S02) at the base and after the fix, the clean form `WP30_ONLY=S02` ("Stata truth", 02-03, 02-17).
- Major: 02-18's key check `grep -c '"P1.34"'` prints 2 after a correct close; replaced by TR-01.10.1's `grep -c '^    "P1.34": "'`.
- Minor: RR-01's home-path needle is built by concatenation (the guard scans the cscript); "If RR-01 fails" no longer contradicts RR-02 passing at the base; 02-01 counts distinct FAIL case ids; 02-07 also requires `ALL CHECKS PASSED`.
- Spot-checked at HEAD: stata_slot.sh:10, run_cert_suite.sh:17-18, run_all_cscripts.do:22-28, Makefile STATA lines, test_cert_verdict.py:205-206, test_measure_stata_coverage.py:389-392, regen_option_surface.py:17/:324/:329, wire_option_reporting.py:9-13/:115/:149, extract_function_truth.do:47, extract_filter_truth.do:9, extract_join_order_truth.do:15-16, the 40-line/31-file literal scan; `runner_do`'s lib adopath holds no dash.ado, so the new findfile check stays green under the coverage tool. All hold.
- Batch 1: S02 and S03 share no function; `wire_option_reporting.py` lines are disjoint (S02 :1-13, S03 :115). No open question touches S02.
- Rejected: none.

The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:168 (P1.34) reads: "Windows, Linux, Intel Mac and GUI Stata are untested. `arch -arm64` and the maintainer's path are hard-coded in the runners." GAPS2 K1 (GAPS2.md:1795-1810) adds the measured consequence: `test/run_all_cscripts.do:22-28` "puts `/Users/billy/.../dash/` on the adopath and cds there. From a worktree it therefore tests the main checkout, while `scripts/cert_verdict.py` reads the worktree's list of registered scripts. The verdict can be green for a tree that was never tested."

Measured at `c96facd`:
- **Wrong tree (K1-a).** A copy of the tree with a broken `dash.ado`, run from the copy, resolves `findfile dash.ado` to the main checkout's file (research p1-34.md M1, re-run by its critic through the slot).
- **Hard-coded paths.** The maintainer's home path sits in 40 lines of 20 files under `scripts/`, `test/` and the Makefile (JSON fixture records excluded):
  - the runner;
  - 15 extractors;
  - `test/fixtures/twoway_corpus.do`;
  - the two option generators;
  - `test/test_geometry_visual.md`.
- **Hard-coded arch (K1-b).** `arch -arm64` sits in 22 lines of 18 files. Six are executed call sites, in five runners.
- **The wrong arch rule.** GAPS2's proposed rule, "only when `uname -m` is arm64", is wrong under an x86_64 parent process. That is the very case the prefix exists for (M6 below).
- **The pytest suite.** It hard-codes Stata's install tree in `test_help_claims_1.py:76-78`, `test_help_claims_8.py:558` and `test_scheme.py:532`.

**After this section** (M4: runners only):
- **One Stata-invocation rule** lives in a new `scripts/stata_batch.sh`:
  - `STATA_BIN`, else `/usr/local/bin/stata-mp`;
  - console binaries only;
  - `arch -arm64` only when the machine reports `hw.optional.arm64` = 1 and the binary holds an arm64 slice, so the rule is right under an x86_64 parent;
  - the arguments pass through unchanged.
- **Every runner starts Stata through it:** `stata_slot.sh`, `run_cert_suite.sh`, `run_release_gate.sh` (two sites), `stata_python_exec.sh` and `measure_stata_coverage.py`.
- **The tree under test** is `DASH_REPO`, else the current directory when it holds `dash.ado` and `test/run_all_cscripts.do`, else r(601) (register P1.34.2). The runner, `run_cert_suite.sh`, `measure_stata_coverage.py`, the 15 extractors and the corpus all follow this rule, so `make cert` in a worktree or copy tests that tree.
- **The two option generators** are retired and refuse to run.
- **The help-claims tests** read `DASH_STATA_BASE`/`DASH_STATA_PLUS`.
- **A guard test** fails on any `arch -arm64` literal or home-directory path under `scripts/`, `test/` or the Makefile, with no exemption list.
- **On this Mac the effective command is unchanged:** `arch -arm64 /usr/local/bin/stata-mp -b do <file>`. Measured in "Stata truth" P4.

**Why one section.** Every edit concerns one thing: how a runner names Stata and the tree under test. The guard can only go green when the runners, the extractors and the tests are all clear, in one commit (IR-8). The section lands first, in batch 1, so that the roughly 22 extractors later sections add copy the path-free form.

**Saved and served modes.** P1.34 draws nothing. No shipped file changes (`dash.ado`, `dash_parse.mata`, `dash_render.py`, the help files, `dash.pkg`), so saved pages and served apps are byte-for-byte the same, before and after any filter move. The modes are exercised through the new runner by batch 1's G8 `make cert`:
- `test_e2e_single.cscript` covers the saved page;
- `test_e2e_serve.cscript` covers the served app;
- `test_e2e_filters.cscript` covers both after filter moves.

S58.5's `make gate` covers a served app's `/health` (release_gate_venv.do) through the rewritten `run_release_gate.sh`.

**Test order and commit rule (rule 7, D1).** One cycle and one commit, `(WP-30 P1.34)`.
- **02-01 and 02-02** write the regression tests and flip the pinned tests.
- **02-03** measures the wrong-tree verdict at the base.
- **The saved failure text** is `$S/02-P1.34-failure.txt`, built by 02-01..02-03 against the unmodified tree. Nothing is committed.
- **02-04 to 02-16** make the fix.
- **02-17** certifies against Stata.
- **02-18** closes the entry and makes the one commit, after one full run through the queue.

No test-only commit exists, and no commit is red.

### Rulings this section applies (binding)

- **M4.** Runners only; platform measurement is deferred.
- **M2.** Only `/usr/local/bin/stata-mp` is ever run, and the wrapper never searches for a binary.
- **Register P1.34.1.** The project instructions' rule 10 and the GUI-block hook are not edited.
- **P1.34.2.** `DASH_REPO`, else `c(pwd)` when it is a tree, else r(601).
- **P1.34.3, ratification row 26, IR-7.** The generators are retired. The form used if row 26 is struck is in TR-02.11.
- **P1.34.4 and A130.** Every new WP-30 extractor copies this section's `DASH_REPO` form. The four `W29_REPO` extractors and `extract_date_units_truth.do` hold no literal and stay with P3.7.
- **P1.34.6.** One deferred platform package.
- **IR-8 (binding over P1.34.5).** All files holding a literal are cleared, so the guard has no exemption list.
- **Manifest naming.** The override is `STATA_BIN`. Today's runners read `STATA`, and the rename is TR-02.6.

## Risk: [yellow] — the runners sit on every gate; a mistake turns every gate red or, worse, green for the wrong tree

**Why.** `make cert`, `make gate`, `make test`, `scripts/stata_slot.sh` (used by every WP-30 agent) and `measure_stata_coverage.py` all change how they start Stata and choose the tree.

**Risk factors.**
1. A wrong root rule tests another tree silently. That is the very defect being fixed, and it must not reappear through a PLUS-installed `dash.ado` or a fallback.
2. A wrong arch rule starts the x86_64 slice, which cannot load the arm64-only libpython. Every Python-dependent script then fails for reasons unrelated to dash (`run_all_cscripts.do:6-13`).
3. `stata_slot.sh` is live during WP-30. A landing while a slot is held could disturb a running Stata.
4. A red-first test that executes a runner at the base would start a real Stata, or rewrite the main checkout's `dash.ado`. `regen_option_surface.py` writes `REPO/dash.ado` at :324 before failing at :329.
5. 16 extractor do-files are edited and none is re-run in full, so a stanza typo would surface only when a later section runs that extractor.
6. Batch logs are named after the command line's last word (commit d285cf7). An extra argument would rename the log the verdict reads.

**Mitigation.**
1. **The root block.** It refuses six characters before any expansion, checks the tree, and checks that `findfile dash.ado` resolves inside it (exit 9 otherwise). It is pinned by RR-01..RR-14 in Stata and by `TestTheRunnerRoot`. The copy acceptance (02-03, 02-17) shows a broken copy FAIL after the fix and PASS at the base.
2. **The arch rule.** Decided from `hw.optional.arm64` and `file -L`, never from `uname -m`. `TestTheWrapper` runs it under `/bin/sh` and `/bin/dash`, and under a real x86_64 parent with the real binary in print mode, so Stata never starts.
3. **Landing.** The merger lands S02 only while `ls -d /tmp/dash-stata-slot-*.d` prints nothing (Notes).
4. **Static gates first.** Every test that executes a runner or generator first asserts statically that it routes through the wrapper or refuses at the top. At the base that assertion fails before anything runs.
5. **One stanza.** It is identical in all 16 files, and `TestTheExtractorRoot` checks every copy is whole. 02-17 runs `extract_filter_truth.do` end to end in a scratch copy and runs it unset (r(601)).
6. **Arguments unchanged.** The wrapper passes `"$@"` unchanged and adds nothing to Stata's command line. The root travels in the environment, never as an argument (research M4).

## Dependencies

- **Depends on: 01.** S01 provides four things:
  - BUGS.md entry `P1.34` (open form);
  - its `WP30_OPEN["P1.34"]` key;
  - the CHANGELOG marker `<!-- WP-30 P1.34 -->` under `### Fixed in WP-30`;
  - the S02 stub block in `test/test_wp30_truth.cscript`.
- **Blocks: 04, 05, 10, 11, 19, 40, 42, 56.** These copy an extractor, or edit a runner header or runner script, after S02 (manifest; index "Runners and floor"). S05 adds `DASH_PYTHON_EXEC` to the runner header below S02's root block.
- **Parallel batch: 1, with S03** (Stata 19 floor). Merge order S02, S03.
  - Both edit `scripts/wire_option_reporting.py`: S02 its docstring, the refusal and the `REPO` line (:1-13); S03 the emitted `version 16.0` at :115.
  - Both edit `test/test_wp30_truth.cscript` (own blocks), BUGS.md (own entries), CHANGELOG.md (different lists) and `WP30_OPEN` (adjacent key lines P1.34/P1.35; R5).
- **Can run with S03.** S03 edits no runner, extractor, wrapper or pytest file of this section, and S02 edits no Stata program.

## Evidence

Anchors re-verified at `c96facd` (the base is S01's commit; S01 edits none of these files, so the lines hold). Symbols govern if a line drifts.

### The runners

`scripts/stata_slot.sh:4-15` (all of it; used by every section's Stata run):
```sh
set -u
dir="$1"; dofile="$2"; mkdir -p "$dir/tmp"
while :; do
  for n in 1 2 3; do
    if mkdir "/tmp/dash-stata-slot-$n.d" 2>/dev/null; then
      trap 'rmdir "/tmp/dash-stata-slot-'"$n"'.d"' EXIT
      cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 /usr/local/bin/stata-mp -b do "$dofile"
      exit $?
```

`scripts/run_cert_suite.sh:11-20`. `$REPO` is the checkout the script sits in, but the runner it starts ignores it:
```sh
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STATA="${STATA:-/usr/local/bin/stata-mp}"
PYTHON="${PYTHON:-python3}"
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_cert.XXXXXX")" || exit 1
mkdir -p "$dir/tmp"
echo "certification suite: running in $dir"
(cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
    "$REPO/test/run_all_cscripts.do" >/dev/null 2>&1)
"$PYTHON" "$REPO/scripts/cert_verdict.py" "$dir/run_all_cscripts.log" \
    "$REPO/test/run_all_cscripts.do"
```

`scripts/stata_python_exec.sh:8,17-18` (has no `REPO` line):
```sh
STATA="${STATA:-/usr/local/bin/stata-mp}"
(cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do pyexec.do \
    >/dev/null 2>&1)
```

`scripts/run_release_gate.sh:11-12,34,42`:
```sh
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STATA="${STATA:-/usr/local/bin/stata-mp}"
(cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
    (cd "$dir/work" && PIP_NO_INDEX=1 STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
```

`Makefile:12-14,31,43,46`. There is no arch prefix here; the binary is passed as `STATA`:
```make
STATA       ?= /usr/local/bin/stata-mp
	@py="$${STATA_PYTHON:-$$(STATA='$(STATA)' sh scripts/stata_python_exec.sh)}"; \
	@STATA='$(STATA)' PYTHON='$(PYTHON)' sh scripts/run_cert_suite.sh
	@STATA='$(STATA)' PYTHON='$(PYTHON)' sh scripts/run_release_gate.sh
```

`test/run_all_cscripts.do:1-13` (the header comment gives the `arch -arm64` command) and `:18-28`:
```stata
clear all
set more off

// Add dash ado files to the path
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"

// Root project directory (all cd calls return here)
local dashdir "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
local testdir "`dashdir'/test"

cd "`dashdir'"
```

Each script block `cd`s to `` `testdir' `` and then back to `` `dashdir' `` (block 68 at :1744-1768). Each cscript loads `../dash.ado` relative to `test/`. So the tree under test is whatever `dashdir` names. `cscript … adodir ".."` does nothing with the adopath: `cscript.ado` collects the words up to `adofile` as its title. Read at `/Applications/StataNow/ado/base/c/cscript.ado:5-8`.

`scripts/measure_stata_coverage.py:62,69,236-237,375-405,461-466`:
```python
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATA = ["arch", "-arm64", "/usr/local/bin/stata-mp", "-b", "do"]
def _stata_path_ok(p):
    return not any(c in p for c in '"`$\'\n\r')
    src = src.replace('adopath ++ "%s"' % dirs[0],
                      'adopath ++ "%s/"' % tree.rstrip("/"))
    src, n = re.subn(r'^local dashdir "[^"]*"\s*$',
                     'local dashdir "%s"' % tree.rstrip("/"), src, flags=re.M)
def _stata(work, dofile):
    env = dict(os.environ)
    env["STATATMP"] = os.path.join(work, "stata_tmp") + "/"
    subprocess.run(STATA + [dofile], cwd=work, env=env, check=False)
```
`runner_do` rewrites the two literals for its scratch tree. That works only because the runner holds literals; with an environment root there is nothing to rewrite.

### Maintainer paths and arch literals (the guard's scan set, measured)

```
git grep -n -E '/Users/[^/]+/|/home/[^/]+/' -- scripts test Makefile ':!*.json' ':!*.png' ':!*.svg' ':!*.csv'   -> 40 lines, 20 files
git grep -n -E 'arch -arm64|"arch", "-arm64"' -- (same)                                                -> 22 lines, 18 files
union                                                                                                  -> 31 files
```

The 31 files:
- **The runners and the coverage script:** `scripts/{stata_slot,run_cert_suite,run_release_gate,stata_python_exec}.sh`, `scripts/measure_stata_coverage.py`, `test/run_all_cscripts.do`.
- **The 15 path extractors:** `scripts/extract_{abbrev,axis,colorvar_qualifier,colorvar,date,embedded_rows,emptied_layer,filter,format,function,join_order,stat,text,unlabelled}_truth.do` and `scripts/extract_svg_truth_smoke.do`.
- **One extractor with a comment only:** `scripts/extract_alias_spelling_truth.do:23`.
- **The corpus:** `test/fixtures/twoway_corpus.do` (:31-34 comment; :53 the StataJSON adopath; :54 the dash adopath).
- **The generators:** `scripts/{regen_option_surface,wire_option_reporting}.py`.
- **Two docstrings:** `test/test_date_range.py:36`, `test/test_qualifier_logic.py:31`.
- **The procedure doc:** `test/test_geometry_visual.md:15,21`.
- **The three pinned tests:** `test_cert_verdict.py:205`, `test_release_verdict.py:221,354`, `test_measure_stata_coverage.py:391`.

IR-8's count of 27 excludes the three pinned tests (flipped here) and the `.md` procedure. S02 clears all 31.

JSON fixtures are excluded from the scan, because they are records of where a measurement ran (R7: never hand-patched). Their provenance strings stay:
- `geometry_truth.json`, `kpi_pctile_truth.json`, `kpi_truth.json`, `qualified_stat_truth.json`, `rejected_options.json` and `value_truth.json` hold the arch literal;
- `date_truth.json`, `geometry_truth.json` and `rejected_options.json` hold the home path.

Shipped files: only a comment at `dash_render.py:292` mentions the prefix. It is outside the guard's scope and is not edited.

How the extractors find the root today (lines named so each task can find them):

| File | Root lines | Form |
|---|---|---|
| extract_abbrev_truth.do | :39 StataJSON adopath, :40 dash adopath, :45 `global ZQ_REPO "/Users/…"` | literal |
| extract_date_truth.do | :64-65 adopaths, :67 `ZQ_REPO`, :69-71 `ZQ_JSONIO_*` literals | literal |
| extract_axis_truth.do | :85 `ZA_REPO` | literal |
| extract_text_truth.do | :59-65 (comment telling agents to repoint and restore it) | literal |
| extract_unlabelled_truth.do | :54 `ZU_REPO` | literal |
| extract_format_truth.do / extract_function_truth.do | :38 / :56 `ZF_REPO` | literal |
| extract_stat_truth.do | :67 `ZQ_REPO` | literal |
| extract_svg_truth_smoke.do | :45 `ZS_REPO` | literal |
| extract_filter_truth.do / extract_embedded_rows_truth.do | :9 `if ${ZA_REPO}=="" global ZA_REPO "/Users/…"` | falls back to main |
| extract_join_order_truth.do | :15-16 `local repo : env DASH_REPO`, else the literal | falls back to main |
| extract_colorvar_truth.do / _qualifier / extract_emptied_layer_truth.do | :34-37 / :30-33 / :29-32: literal, then env override | falls back to main |

`extract_abbrev_truth.do` and `twoway_corpus.do` never call `jsonio` (`grep -c jsonio` prints 0 for both), and dash stopped using jsonio on 24sep2026. Their StataJSON adopath lines are dead. `extract_date_truth.do` section D (:277-312) does call `jsonio`, under `capture`.

### The two generators

`scripts/regen_option_surface.py:17-18` and `:324-329`. It writes the main checkout's `dash.ado`, then crashes on a missing `/tmp` file:
```python
REPO = "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
truth = json.load(open(REPO + "/test/fixtures/abbrev_truth.json"))
open(REPO + "/dash.ado", "w").write(src)
json.dump({"graph": GRAPH_NAMES, "plot": PLOT_NAMES, "pending": PENDING},
          open("/tmp/dash-wf/b2/option_inventory.json", "w"), indent=1)
```
`scripts/wire_option_reporting.py:9-13` (`REPO` literal, then `/tmp/dash-wf/b2/option_inventory.json`, absent), :115 `version 16.0` (S03's line) and :149 (writes `REPO/dash.ado`). Neither script is imported or run by any test (`grep -rn` finds only ROADMAP/REMAINING/BUGS prose).

### The pytest suite's Stata tree

- `test/test_help_claims_1.py:76-79` defines `_STATA_BASE`, `_STATA_PLUS` and `_TWOWAY_CLASS`. They are read at :126-158, and `TestTheHeader::test_stata_is_installed_where_the_links_are_checked` fails without the directory.
- `test/test_help_claims_8.py:558` defines `_STATA_BASE`, read by `_stata_file` (:561-566) and :1464.
- `test/test_scheme.py:530-541`, `TestSecurity::test_real_stata_scheme_via_cwd_copy`, reads `/Applications/Stata 15/ado/base/s/scheme-s2color.scheme`, a Stata 15 tree, and skips without it.

Research M5 measured that the suite with the tree elsewhere gives `2 failed, 4 passed, 1 skipped`.

Measured 03oct2026: SchemeParser on a copy of StataNow's `scheme-s2color.scheme` gives `p_colors[0] == "#1a476f"`, the value the test asserts. So pointing the test at the configured 19.5 tree keeps its assertion.

### Blast radius (GitNexus at `c96facd`; Stata, sh and do files are not indexed)

| Symbol | Risk | Note |
|---|---|---|
| `runner_do` (measure_stata_coverage.py) | LOW, 3 impacted | process `main` |
| `_stata` | LOW, 2 impacted | |
| `prepare` | LOW, 2 impacted | signature unchanged |
| `STATA` (measure_stata_coverage.py) | UNKNOWN | grep: defined :69, used only :464, pinned by test_measure_stata_coverage.py:391 |
| `_STATA_BASE`/`_STATA_PLUS` (help_claims_1, _8) | UNKNOWN | grep: module-local, :79, :126-157; :563, :1464 |
| `REPO` in the two generators | UNKNOWN | grep: module-local, never imported |
| shell runners, `run_all_cscripts.do`, extractors, Makefile | not indexed | grep callers: `run_cert_suite.sh` and `stata_python_exec.sh` ← Makefile, test_cert_verdict; `run_release_gate.sh` ← Makefile, test_release_verdict; `stata_slot.sh` ← 17 extractor headers, svg_truth.py docstring, every WP-30 agent; `run_all_cscripts.do` ← run_cert_suite.sh, measure_stata_coverage, cert_verdict, test_cscript_hygiene, test_fixtures_are_committed, test_measure_stata_coverage |

No symbol is HIGH or CRITICAL. Each UNKNOWN was confirmed by grep and is recorded as unresolved, not as low (index E4).

### Tests that pin today's behaviour (flip, never delete)

| Node | Pins | Flip |
|---|---|---|
| `test/test_cert_verdict.py::TestMakeCheckIsWired::test_stata_runs_only_through_the_console_binary` (params `run_cert_suite.sh`, `stata_python_exec.sh`) | `arch -arm64 "$STATA" -b do` and `STATA="${STATA:-…}"` (:205-206) | the wrapper call; params extended to `stata_slot.sh` and `run_release_gate.sh` |
| `test/test_release_verdict.py::TestTheGateIsWiredUp::test_the_runner_uses_the_console_binary_in_batch` | `arch -arm64 "$STATA" -b do` (:221) | the wrapper call, exactly 2 sites |
| `test/test_release_verdict.py::TestTheVenvSessions::test_the_runner_runs_both_phases_offline` | the same (:354) | `PIP_NO_INDEX=1 STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do` |
| `test/test_measure_stata_coverage.py::test_stata_runs_the_console_binary_with_its_own_tmp` | argv `["arch","-arm64","/usr/local/bin/stata-mp","-b","do",…]` (:391) | `["sh", <REPO>/scripts/stata_batch.sh, "-b", "do", …]` and `env["DASH_REPO"] == <work>/tree` |
| `test/test_measure_stata_coverage.py::TestTheGeneratedRunner::test_paths_marks_and_flushes` | `adopath ++ "/w/tree/"` and `local dashdir "/w/tree"` written in (:211, :213) | the runner's own env-rooted header is kept; no tree path is written |
| `test/test_measure_stata_coverage.py::TestTheGeneratedRunner::test_a_malformed_runner_is_refused` | one adopath line (kept) | also refuses a runner whose root is a literal |
| `test/test_scheme.py::TestSecurity::test_real_stata_scheme_via_cwd_copy` | reads Stata 15's tree | reads `<stata_base()>/s/scheme-s2color.scheme` |

Two more need care:
- The module constant `_RUNNER` (`test_measure_stata_coverage.py:174-200`) changes to the env-rooted header. Until 02-07 lands, every `TestTheGeneratedRunner` and `TestPrepare` test that feeds it to `runner_do` fails at the base. 02-02 records these in the failure text as consequences of the fixture flip.
- Baseline: `python3 -m pytest -q -n0 -p no:cacheprovider test/test_cert_verdict.py test/test_release_verdict.py test/test_measure_stata_coverage.py` gives `95 passed`, measured 03oct2026. This count must never fall.

## User stories

- **US-02.1** As the maintainer, I want `make cert` in a worktree or a copy to test that tree, and to fail when that tree's `dash.ado` is broken, so a green verdict means the tree I am committing was certified.
- **US-02.2** As the maintainer, I want every runner to start Stata one way: the console binary I name with `STATA_BIN`, in the arm64 slice exactly when the machine and the binary support it, even from an x86_64 terminal. Then a Python-dependent script never fails because the wrong slice could not load libpython.
- **US-02.3** As the maintainer, I want no runner, extractor or test to carry my home path or a fixed `arch -arm64`, guarded by a test, so the repository works from any checkout on any machine.
- **US-02.4** As the maintainer, I want the two stale option generators to refuse to run, so neither can rewrite a checkout's `dash.ado` again.
- **US-02.5** As the maintainer, I want the help-claims tests to read Stata's install tree from an environment variable, so a machine with Stata elsewhere can run the suite strictly.

## Business requirements

- **BR-02.1** `make cert`, run from any checkout or copy, certifies that tree:
  - The tree is `DASH_REPO`, else the current directory when it holds `dash.ado` and `test/run_all_cscripts.do`.
  - Anything else stops the run with r(601). A root holding a double quote, `$`, a single quote, a backtick, LF or CR stops it with r(198).
  - A copy whose `dash.ado` is broken gets a FAIL verdict, and a clean copy gets PASS.
- **BR-02.2** Every Stata start under `scripts/` and the Makefile goes through one rule:
  - `STATA_BIN`, else `/usr/local/bin/stata-mp`, never searched for.
  - Only the console binaries `stata`, `stata-mp`, `stata-se`, `stata-be` and `stata-ic`, judged by name and by the file a symlink resolves to. Anything else is refused with rc 2 and never started.
  - `arch -arm64` only when the machine reports arm64 capability and the binary has an arm64 slice, the same under an x86_64 parent.
  - Stata's arguments, and so its batch log names, are unchanged.
  - On this Mac the command is `arch -arm64 /usr/local/bin/stata-mp -b do <file>`.
- **BR-02.3** No text file under `scripts/` or `test/`, and not the Makefile, holds `arch -arm64` or a home-directory path. A test fails otherwise, and it has no exemption list.
- **BR-02.4** The 15 extractors and the twoway corpus read their root as BR-02.1 does, and never fall back to another checkout. `extract_date_truth.do` reads jsonio's location from `STATAJSON_DIR`, when set.
- **BR-02.5** `scripts/regen_option_surface.py` and `scripts/wire_option_reporting.py` exit nonzero, saying they are historical and must not be run, before reading or writing any file.
- **BR-02.6** The pytest suite reads Stata's base and PLUS trees from `DASH_STATA_BASE` and `DASH_STATA_PLUS`, defaulting to StataNow's.
- **BR-02.7** The Make variable is `STATA_BIN`. `make <target> STATA=<path>` stops with a message naming `STATA_BIN`.
- **BR-02.8** No shipped file changes, and dashboards are identical in both modes.

## Technical requirements

**TR-02.1 `scripts/stata_batch.sh` (new, POSIX sh, mode 100755).** This is the only file that runs `arch`. The text below was measured under `/bin/sh` and `/bin/dash`; see "Stata truth" P4.

```sh
#!/bin/sh
# scripts/stata_batch.sh [Stata arguments]: start console Stata with the
# arguments unchanged, so Stata names its batch log as it always has
# (WP-30 P1.34).  STATA_BIN names the binary (default /usr/local/bin/stata-mp;
# it is never searched for).  STATA_ARCH is auto (default), none, arm64 or
# x86_64: auto starts the arm64 slice exactly when the machine reports
# hw.optional.arm64 = 1 and the binary holds an arm64 slice -- never from
# uname -m, which reports x86_64 under an x86_64 parent process.
# STATA_BATCH_PRINT=1 prints the command instead of running it.
set -u
bin="${STATA_BIN:-/usr/local/bin/stata-mp}"
mode="${STATA_ARCH:-auto}"
case "$mode" in
  auto|none|arm64|x86_64) ;;
  *) echo "stata_batch: STATA_ARCH must be auto, none, arm64 or x86_64" >&2; exit 2 ;;
esac
_console() {
  case "$(basename -- "$1")" in
    stata|stata-mp|stata-se|stata-be|stata-ic) return 0 ;;
  esac
  return 1
}
t="$bin"; hops=0
while [ -L "$t" ] && [ "$hops" -lt 40 ]; do
  l="$(readlink -- "$t")" || break
  case "$l" in /*) t="$l" ;; *) t="$(dirname -- "$t")/$l" ;; esac
  hops=$((hops + 1))
done
if ! _console "$bin" || ! _console "$t"; then
  printf 'stata_batch: %.200s is not a console Stata (stata, stata-mp, stata-se, stata-be or stata-ic); the GUI application waits on a modal alert in batch mode\n' "$bin" >&2
  exit 2
fi
if [ ! -f "$t" ] || [ ! -x "$t" ]; then
  printf 'stata_batch: %.200s is not an executable file\n' "$bin" >&2
  exit 2
fi
want=""
case "$mode" in
  arm64|x86_64) want="$mode" ;;
  auto)
    if [ "$(uname -s)" = Darwin ] \
       && [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = 1 ] \
       && file -L -- "$bin" 2>/dev/null | grep -Eq 'executable arm64e?$'; then
      want=arm64
    fi ;;
esac
if [ -n "$want" ]; then set -- arch "-$want" "$bin" "$@"; else set -- "$bin" "$@"; fi
if [ "${STATA_BATCH_PRINT:-}" = 1 ]; then
  out=""; for a in "$@"; do out="$out${out:+ }<$a>"; done
  printf '%s\n' "$out"
  exit 0
fi
exec "$@"
```

Rules this text implements, each pinned by `TestTheWrapper`:
- **No `eval`.** Every expansion is quoted, and the arguments are passed as `"$@"`.
- **Bounded messages.** A user path is echoed at most 200 characters long.
- **GUI names refused.** `StataMP`, `stataMP` (a case-insensitive volume makes it the GUI file) and Linux's `xstata-mp` fail the case-sensitive allow-list. So does a symlink named `stata-mp` that resolves to `StataMP`.
- **The slice match is anchored.** `executable arm64e?$` cannot be satisfied by a path, because `file` prints the path at the start of the line.
- **Short-circuit on Linux.** `sysctl` is never called when `uname -s` is not `Darwin`.
- **No other Stata.** No `/Applications` path, glob, `ls` or `find`, so no 14-18.5 binary is ever chosen (M2).
- **`STATA` is not read.** The old variable is ignored here. The Makefile refuses it (TR-02.6).

**TR-02.2 `scripts/stata_slot.sh`.** It keeps its interface `<scratch-dir> <file.do>`, the three `/tmp/dash-stata-slot-N.d` locks and `STATATMP="$dir/tmp/"`.
- Add `REPO="$(cd "$(dirname "$0")/.." && pwd)"` after `set -u`. It runs before the `cd "$dir"`.
- Line 10 becomes `cd "$dir" && STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do "$dofile"`.
- The header comment gains one line: "Stata is started through scripts/stata_batch.sh (STATA_BIN, STATA_ARCH)."

**TR-02.3 `scripts/run_cert_suite.sh`.**
- Delete the `STATA=` line (:12).
- After `PYTHON=`, refuse a `$REPO` that holds a double quote, `$`, a single quote, a backtick, LF or CR. Use this measured case, then `exit 2`:
  ```sh
  cr="$(printf '\r')"
  nl='
  '
  case "$REPO" in
    *[\"\$\'\`]*|*"$nl"*|*"$cr"*)
      echo "certification suite: this checkout's path holds a quote, dollar sign, backtick or line break, which Stata cannot be handed" >&2
      exit 2 ;;
  esac
  ```
- After the existing `running in $dir` echo, add `echo "certification suite: testing $REPO"`.
- :17 becomes `(cd "$dir" && DASH_REPO="$REPO" STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do \`.
- Rewrite the header comment (:2-9). It names the console-only rule, `STATA_BIN`, `DASH_REPO` (this tree, whichever checkout it is) and `PYTHON`, and does not name the project instructions file.

**TR-02.4 `scripts/stata_python_exec.sh`.**
- Delete :8 and add the `REPO=` line of TR-02.2.
- :17 becomes `(cd "$dir" && STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do pyexec.do \`.
- :24 prints `${STATA_BIN:-/usr/local/bin/stata-mp}` in place of `$STATA`.
- Rewrite the header comment the same way.

**TR-02.5 `scripts/run_release_gate.sh`.**
- Delete :12.
- :34 becomes `(cd "$dir" && STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do \`.
- :42 becomes `(cd "$dir/work" && PIP_NO_INDEX=1 STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do \`.
- The header comment's "STATA names the console binary" becomes "STATA_BIN names the console binary (scripts/stata_batch.sh)".
- The log-renaming loop (:44-48) is untouched.

**TR-02.6 `Makefile`.**
- `STATA       ?= /usr/local/bin/stata-mp` becomes `STATA_BIN   ?= /usr/local/bin/stata-mp`.
- Directly after the variables, add the guard below, measured with GNU Make 3.81:
  ```make
  ifeq ($(origin STATA),command line)
  $(error STATA was renamed STATA_BIN (WP-30); run make $(MAKECMDGOALS) STATA_BIN=$(STATA))
  endif
  ```
  It is measured: `make -n cert STATA=/x` gives rc 2.
- The `test`, `cert` and `gate` recipes pass `STATA_BIN='$(STATA_BIN)'`. The `make test` message names `$(STATA_BIN)`.
- The `help` target gains `@echo "STATA_BIN=<path> names the console Stata (default /usr/local/bin/stata-mp); STATA_ARCH=auto|none|arm64|x86_64"`.
- Comment line 10 becomes "Stata is run only through the console binary, in batch, started by scripts/stata_batch.sh."

**TR-02.7 `test/run_all_cscripts.do` header (lines 1-28).**
- **Comment (:1-13).** The new comment says:
  - run it with `make cert`, or from the dash/ directory with `sh scripts/stata_batch.sh -b do test/run_all_cscripts.do`;
  - the tree under test is `DASH_REPO`, else the current directory, and either must be a dash tree or the run stops with r(601);
  - why the arm64 slice matters (keep the libpython sentence).
- **Lines 21-28.** They become this root block, measured case by case in "Stata truth" P2. Everything between the markers is what the RR cases run:
```stata
// ---- root: begin (WP-30 P1.34) ----
local dashdir : environment DASH_REPO
if `"`macval(dashdir)'"' == "" local dashdir `"`c(pwd)'"'
mata: st_local("_dash_bad", strofreal(any(strpos(st_local("dashdir"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_dash_bad' {
    display as error "run_all_cscripts.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`dashdir'"') > 1 & inlist(substr(`"`dashdir'"', -1, 1), "/", char(92)) {
    local dashdir = substr(`"`dashdir'"', 1, strlen(`"`dashdir'"') - 1)
}
capture confirm file `"`dashdir'/dash.ado"'
local _dash_rc = _rc
capture confirm file `"`dashdir'/test/run_all_cscripts.do"'
if `_dash_rc' | _rc {
    local _dash_show = substr(`"`dashdir'"', 1, 200)
    display as error `"run_all_cscripts.do: `_dash_show' is not a dash tree (it needs dash.ado and test/run_all_cscripts.do); set DASH_REPO to the tree to test"'
    exit 601
}
adopath ++ "`dashdir'/"
local testdir "`dashdir'/test"
cd "`dashdir'"
quietly findfile dash.ado
if `"`r(fn)'"' != `"`dashdir'/dash.ado"' {
    display as error `"run_all_cscripts.do: dash.ado resolves to `r(fn)', not `dashdir'/dash.ado"'
    exit 9
}
// ---- root: end ----
```
- **Why each piece.**
  - The value is checked through Mata's `st_local`, which never expands it. `macval()` keeps `$` and the backtick unexpanded (research M3).
  - The findfile check stops a wrong root from silently testing a PLUS-installed dash.
  - No `python` call is added, so `TestTheAvailabilityGuardIsReliable::test_the_runner_does_not_probe_python_by_executing_it` stays green.
- `global dash_nobrowser 1` and the rest of the file are untouched.

**TR-02.8 `scripts/measure_stata_coverage.py`.**
- `STATA = ["sh", os.path.join(REPO, "scripts", "stata_batch.sh"), "-b", "do"]`, with its comment reading "the console binary, through scripts/stata_batch.sh".
- `_stata(work, dofile)` adds `env["DASH_REPO"] = os.path.join(work, "tree")`. There is no `shell=True`; the argv stays a list.
- `runner_do(work, tree, runner_src)` keeps its signature, but stops rewriting paths:
  - It still requires exactly one `adopath ++ "…"` line ("runner: expected one adopath line, dash's").
  - That line must be exactly ``adopath ++ "`dashdir'/"``, and the source must hold the line `local dashdir : environment DASH_REPO`. Otherwise it raises `ValueError("runner: its root must come from DASH_REPO")`.
  - It raises `ValueError` when `_stata_path_ok(tree)` is false.
  - It no longer replaces the adopath or `local dashdir` line.
  - The setup insertion after ``cd "`dashdir'"\n``, the RUN marks and the flushes are unchanged.
- The docstring says that `_stata` hands the tree over through `DASH_REPO`.

**TR-02.9 The extractor root stanza** (A130's path-free form, which later sections copy).
- In the 15 path extractors and `test/fixtures/twoway_corpus.do`, the literal root lines of the Evidence table are replaced by this stanza, with `<file>` the file's own name:
```stata
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "<file>: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"<file>: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
```
- **What follows the stanza.**
  - The file's own global is set from it, e.g. `global ZQ_REPO "`repo'"` (ZA, ZE, ZF, ZQ, ZS and ZU keep their names). In `extract_join_order_truth.do`, the existing `` `repo' `` uses are kept.
  - Where the file had a dash adopath line, it becomes ``adopath ++ "`repo'/"``. No other line of any extractor changes.
- **The comment headers.** Each header's "Run" lines become `DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/<file>.do`.
  - `extract_text_truth.do:59-64`'s "repoint and restore" comment is deleted.
  - `extract_filter_truth.do:7` and `extract_embedded_rows_truth.do:7` ("ZA_REPO … may be overridden") are reworded to DASH_REPO.
  - `extract_join_order_truth.do:12` ("DASH_REPO defaults to the main checkout") is deleted.
- **jsonio.**
  - `extract_abbrev_truth.do:39` and `twoway_corpus.do:53` (the StataJSON adopath) are deleted, because neither file calls jsonio.
  - In `extract_date_truth.do`, :64 and :69-71 become: `local sj : environment STATAJSON_DIR`; the same six-character check on `sj` (r(198), message naming STATAJSON_DIR); `if `"`sj'"' != "" adopath ++ `"`sj'"'`.
  - The three `ZQ_JSONIO_ADO/JAR/SRC` globals are set to `` `sj'/jsonio.ado ``, `` `sj'/target/jsonio-jar-with-dependencies.jar `` and `` `sj'/src/main/java/org/paces/Stata/JSON `` when `sj` is set, and to `""` otherwise.
  - Section D's `capture`d jsonio calls then record rc 199 without it. That is noted in the header comment: set STATAJSON_DIR to reproduce the committed fixture's JSONIO rows.
- **The corpus.** `twoway_corpus.do` keeps "DELIBERATELY NO version STATEMENT": the stanza has none. Its :31-35 comment names `scripts/stata_slot.sh` and `scripts/stata_batch.sh` (which picks the arm64 slice) instead of the prefix.
- **No regeneration.** No fixture is regenerated (R7; provenance strings stay).

**TR-02.10 Other literals.**
- `extract_alias_spelling_truth.do:23-25` becomes `STATATMP=<scratch>/ sh <repo>/scripts/stata_batch.sh -b do <repo>/scripts/extract_alias_spelling_truth.do <repo>/test/fixtures/alias_spelling_truth.json`. The file takes no root.
- `test/test_geometry_visual.md:13-22`: delete the StataJSON adopath line, and change the last line to `sh <repo>/scripts/stata_batch.sh -b do run.do`.
- `test/test_date_range.py:36` and `test/test_qualifier_logic.py:31` docstrings: "arch -arm64 stata-mp -b" becomes "the console binary, stata-mp -b". These are wording only.

**TR-02.11 The generators are retired (register P1.34.3, ratification row 26).**
- **The refusal.** In each file, the docstring's first line becomes `RETIRED (WP-30 P1.34): historical, do not run.` The first statements after the docstring are `import sys` and the call below, before any `open(`, `json.load` or `REPO` use:
  ```python
  sys.exit("scripts/<name> is retired (WP-30 P1.34): historical, do not run; add an option in dash.ado's five option-surface places by hand")
  ```
  The `REPO = "/Users/…"` line becomes `REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`, with `import os`. It is unreachable, kept for the record.
- **Left alone.** `wire_option_reporting.py:115` (`version 16.0`) is S03's line and is not touched.
- **If row 26 is struck (IR-7)**, the manifest form applies instead. Both scripts take `REPO` from `__file__`, and they take the inventory path as their one required argument. Each exits 2, naming the missing argument or file, before reading or writing anything, and `regen_option_surface.py` writes `dash.ado` last. `TestTheRetiredGenerators` then asserts rc 2 with no argument and with a missing inventory, and an unchanged scratch `dash.ado`.

**TR-02.12 Stata's tree in the pytest suite.**
- `test/conftest.py` gains, after `_strict()` (:252-255), the code below. The values are read at call time:
  ```python
  STATA_BASE_DEFAULT = "/Applications/StataNow/ado/base"
  STATA_PLUS_DEFAULT = "~/Library/Application Support/Stata/ado/plus"
  def stata_base():
      """Stata's base ado tree: DASH_STATA_BASE, else StataNow's (WP-30 P1.34)."""
      return os.environ.get("DASH_STATA_BASE") or STATA_BASE_DEFAULT
  def stata_plus():
      """Stata's PLUS tree: DASH_STATA_PLUS, else the macOS default."""
      return os.path.expanduser(os.environ.get("DASH_STATA_PLUS") or STATA_PLUS_DEFAULT)
  ```
- `test_help_claims_1.py:76-78` becomes `_STATA_BASE = stata_base()` and `_STATA_PLUS = stata_plus()`, with `from conftest import stata_base, stata_plus`, as `test_conftest_helpers.py` imports `make_data_json`. `test_help_claims_8.py:558` becomes `_STATA_BASE = stata_base()`.
- `test_scheme.py:532-534` reads `os.path.join(stata_base(), "s", "scheme-s2color.scheme")`. The skip text becomes "Stata's scheme-s2color.scheme is not under DASH_STATA_BASE"; the assertion is unchanged.
- An empty variable counts as unset. The values are only read from, never executed.

**TR-02.13 `test/test_runner_portability.py` (new).**
- **The scan set.** Every file under `scripts/` and `test/` whose suffix is `.py`, `.do`, `.cscript`, `.sh`, `.md`, `.txt`, `.ado` or `.mata`, every file under `scripts/` with no suffix (`git-hooks/pre-push`), and the `Makefile`. `__pycache__` is skipped. This is a type rule, not a per-file exemption: JSON, CSV, PNG and SVG files are data records.
- **The needles.** `/Users/<name>/`, `/home/<name>/`, `C:\Users\`, `arch -arm64` and `"arch", "-arm64"`. Each is built by concatenation, for example `r"\barch\s+-" + "arm64"`, so this file never holds a literal one. The guard scans its own file too.
- **Execution safety.** Every test that executes a shell runner or a generator first asserts statically that the script calls `scripts/stata_batch.sh` or refuses at the top. At the base, that assertion fails before anything runs, so no real Stata is started and no `dash.ado` is written.
- **No skips.** Fakes live in `tmp_path`. Shells are the existing ones among `/bin/sh` and `/bin/dash`. Machine-dependent cases are collected only where they apply (arm64 macOS with `/usr/bin/arch`; `make` on PATH; `/usr/local/bin/stata-mp` present), because a skip fails `DASH_STRICT=1`.

**TR-02.14 The truth block** (S02's stub in `test/test_wp30_truth.cscript`, R1).
- **Helpers.** They go directly above the S02 header line, outside the gate:
  - a Mata function `real scalar _s02_root_lines(string scalar src, string scalar dst)`, which copies the lines strictly between `// ---- root: begin` and `// ---- root: end` to `dst` (a `tempfile` name, which Stata has not created) and returns their count;
  - no tally of its own: every case reports through S01's `_w30_expect <id> "<cond>" "<msg>"` lines closed by one `_w30_done <id> "<msg>"` (TR-01.10.4), which print `<id> PASS: …` or `<id> FAIL: …` and count the case, so `WP30_ONLY=S02` ends `ALL CHECKS PASSED` (a block with its own tally leaves `$w30_ncase` at 0 and the summary ends "no case ran", r(9));
  - `_s02_realdir dir`, which returns `r(dir)` = `c(pwd)` after `cd`, normalising symlinks such as `/tmp`;
  - `_s02_run_root block cwd`, which is rclass. It saves `` `"$S_ADO"' `` and `c(pwd)`, `cd`s to `cwd` when given, runs `capture noisily do` on the block, and records `r(rc)`, `r(pwd)` and `r(fn)` (findfile after rc 0). It then restores the ado-path with `global S_ADO `"`macval(ado0)'"'` and the directory.
  - Each program opens `version 19`.
- **Python inside the gate.** Single `python: import os; …` lines only, with no braces and never `capture python` (`TestTheWp29TruthScript`-style hygiene and the `:322` pin).
- **Bracketing.** The block saves `local env0 : environment DASH_REPO` first (after its start line) and restores it last (before its end line), through `os.environ`. It never `exit`s: a failed case is counted by `_w30_done` and the summary exits 9, so the blocks after it still run.
- The cases are in "Test plan".

**TR-02.15 Both modes, copy lists, maps, JS.**
- No served copy-list entry (the R2 table's S01-S03 row) and no JS twin.
- No `function_test_map.py` entry, because no function is added to `dash_render.py` or `dash_setup_lib.py`.
- No `program_coverage_map.py` entry, because no program is added to `dash.ado`, `dash_setup.ado` or `dash_parse.mata`.
- No parity CORPUS case (G3 not applicable: nothing is drawn).
- The new Python code lives in `scripts/` and tests, which the maps do not cover. Each changed function has its own test (rule 3): `_stata`, `runner_do` and the wrapper's every branch.

**TR-02.16 Security (rule 1).**
- No `eval`, and no `shell=True`.
- Every environment value that reaches Stata code or a file name is refused before use when it holds one of the six characters, through Mata, never through macro expansion. That covers `DASH_REPO`, `STATAJSON_DIR` and the runner's `$REPO`.
- Messages echoing a user path are bounded to 200 characters.
- GUI binaries are refused and never started.
- The generators refuse before any write.
- Tests run fakes in `tmp_path`. The real-binary cases run the wrapper in print mode, so Stata never starts from pytest.

**TR-02.17 Tracking.**
- Close BUGS.md entry `P1.34` in place, and delete the `"P1.34"` key line of `WP30_OPEN` (R5).
- Replace `<!-- WP-30 P1.34 -->` under `### Fixed in WP-30` in place (R4).
- No help paragraph: `dash.sthlp` and `dash_setup.sthlp` name no runner (`grep -n 'arch -arm64\|make cert\|stata-mp' dash.sthlp dash_setup.sthlp` prints nothing). The maintainer-facing text is the Makefile `help` target and the runner header (TR-02.6, TR-02.7).

## Boundaries

- **No shipped file:** `dash.ado`, `dash_setup.ado`, `dash_parse.mata`, `dash_render.py` (including its :292 comment), `dash_setup_lib.py`, the help files, `dash.pkg`, the scheme files.
- **Not edited (P1.34.1):** the project instructions and the hooks (the GUI-block and full-suite hooks).
- **Fixtures:** none regenerated or hand-patched. `extract_date_units_truth.do`, `extract_axis2_truth.do`, `extract_by_scales_truth.do`, `extract_lpoly_rot_truth.do`, `extract_lpolyci_truth.do`, `extract_value_truth_additions.do`, `release_gate.do` and `release_gate_venv.do` hold no literal and are not edited (P1.34.4; P3.7).
- **S03's lines:** every `version 16.0` line, including `wire_option_reporting.py:115`; `test_env_guards.cscript`, `test_setup_python_gate.cscript`, `test_caller_version`, `test_version_floor.py`; S03's truth block, entry, key and markers.
- **Later sections:**
  - S05 adds `DASH_PYTHON_EXEC` below `// ---- root: end ----`, never inside the root block.
  - New extractors (S04, S10, S11, S19, S40, S42, S56 and others) copy TR-02.9's stanza.
  - The tracking documents are S58's (A145).
- **Not in S02 (M4):** no Windows, Linux or Intel macOS behaviour is measured or claimed, and there is no `cert-matrix`.
- **No runner block.** No new cscript and no hygiene-pin change (R1). No `make cert`, `make gate` or `run_all_cscripts.do` run inside the section (index "Full-suite runs" rule 3).

## Stata truth

There is no fixture and no `_meta` stamp, because nothing here is compared with twoway. Stata is run for three things:
- the RR block, through the driver;
- the copy acceptance, a one-script runner through the slot;
- one converted extractor, in a scratch copy.

Every run goes through a `stata_slot.sh`. From 02-04 on, it is the worktree's own copy, so the new wrapper is used.

**Probes run while writing this section** (03oct2026, StataNow 19.5 MP, through `scripts/stata_slot.sh`; each opened with `adopath ++ "<main>/"` and `global dash_nobrowser 1`):
- **P1, the environment set from Python reaches `: environment`** (`envprobe.do`):
  ```
  BEFORE []
  AFTER [/tmp/from python/x]          <- python: os.environ["DASH_REPO"] = ...
  DOLLAR has=1 raw=[/tmp/co$py]       <- Mata st_local sees the raw $; macval keeps it
  DELETED []                          <- del os.environ["DASH_REPO"]
  ANY bad=1                           <- any(strpos(s, (char(34),char(36),char(39),char(96),char(10),char(13))))
  ```
- **P2, TR-02.7's root block, extracted between its markers and run under nine environments** (`rr_probe.do`):
  ```
  BLOCK lines=25
  CASE 1 DASH_REPO=<main>          rc=0   pwd=<main>  fn=<main>/dash.ado
  CASE 2 DASH_REPO=<main>/         rc=0   pwd=<main>  fn=<main>/dash.ado
  CASE 3 unset, cwd <main>         rc=0   pwd=<main>  fn=<main>/dash.ado
  CASE 4 unset, cwd notree         rc=601
  CASE 5 <p>/co$py                 rc=198
  CASE 6 <p>/co`py                 rc=198
  CASE 7 <p>/co"py                 rc=198
  CASE 8 DASH_REPO=notree          rc=601
  CASE 9 DASH_REPO=<p>/my tree     rc=0   pwd=<p>/my tree  fn=<p>/my tree/dash.ado
  ```
- **P3, the ado-path saves and restores through `S_ADO`, and `cscript` keeps it** (`sado_probe.do`):
  ```
  S_ADO0 [`"<main>/"';BASE;SITE;.;PERSONAL;…]
  S_ADO1 [`"/tmp/zz_x/"';`"<main>/"';…]     <- after adopath ++
  S_ADO2 [`"<main>/"';BASE;…]               <- global S_ADO `"`macval(ado0)'"'
  S_ADO3 [`"<main>/"';BASE;…]               <- after cscript "probe" adodir ".."
  ```
- **P4, TR-02.1's wrapper (no Stata started).** It ran with fake `uname`, `sysctl`, `file` and `arch` on PATH, and with the real tools in print mode, under `/bin/sh` and `/bin/dash` with identical output:
  ```
  arm64 machine        ARCH <-arm64> <W/bin/stata-mp> <-b> <do> <my file.do>
  Intel (sysctl rc 1)  STATA <-b> <do> <my file.do>
  Linux                STATA <-b> <do> <my file.do>        sysctl-called=no
  x86_64-only binary   STATA <-b> <do> <my file.do>
  STATA_ARCH none/arm64/x86_64 -> no prefix / -arm64 / -x86_64;  bogus -> rc 2
  StataMP, stataMP, xstata-mp, a stata-mp symlink to StataMP -> "is not a console Stata", rc 2
  missing binary       "is not an executable file", rc 2
  quote/$/backtick args ARCH <-arm64> <W/rt/stata-mp> <-b> <do> <a"b> <$HOME> <c`d>
  real tools, print:   <arch> <-arm64> </usr/local/bin/stata-mp> <-b> <do> <x.do>
  real tools under /usr/bin/arch -x86_64 (uname -m = x86_64):  <arch> <-arm64> </usr/local/bin/stata-mp> <-b> <do> <x.do>
  ```
  `file -L` of a copy of `/usr/bin/true` ends `executable arm64e`, it runs (rc 0) and it matches `executable arm64e?$`, so it is the harmless stand-in for a universal binary. `file -L /usr/local/bin/stata-mp` lists `x86_64` and `arm64`. The binary is a symlink to `/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp`, whose basename passes the allow-list.
- **P5, the six-character `case` of TR-02.3** under `/bin/sh` and `/bin/dash`: it refuses `"`, `$`, `'`, the backtick, LF and CR, and accepts a space, `\` and `; & |`.

**Runs the section makes:**
- **The driver** (02-01 at the base, 02-07 and 02-17 after the fix):
  ```sh
  printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"
  DASH_REPO="$WT" WP30_ONLY=S02 <slot> "$S" "$S/run_test_wp30_truth.do"     # log $S/run_test_wp30_truth.log
  ```
- **The copy acceptance** (02-03 with the main checkout's slot; 02-17 with `$WT/scripts/stata_slot.sh`):
  ```sh
  rm -rf "$S/copy" && rsync -a --exclude .git "$WT/" "$S/copy/"
  printf 'exit 9\n' | cat - "$S/copy/dash.ado" > "$S/copy/dash.ado.new" && mv "$S/copy/dash.ado.new" "$S/copy/dash.ado"   # broken form only
  python3 -c 'import sys; sys.path.insert(0, sys.argv[1] + "/scripts"); import measure_stata_coverage as m; open(sys.argv[1] + "/test/run_s02.do", "w").write(m.select_scripts(open(sys.argv[1] + "/test/run_all_cscripts.do").read(), ["test_wp30_truth.cscript"]))' "$S/copy"
  mkdir -p "$S/acc" && DASH_REPO="$S/copy" WP30_ONLY=<blk> <slot> "$S/acc" "$S/copy/test/run_s02.do"
  python3 "$S/copy/scripts/cert_verdict.py" "$S/acc/run_s02.log" "$S/copy/test/run_s02.do"; echo "verdict rc=$?"
  ```
  The runner is named `run_s02.do`, so the guard hook's process check (which matches `run_all_cscripts.do`) is not tripped. `<blk>` is `S01` for the broken form (TF-01 alone, which needs nothing from S02, so the verdict turns only on which tree's `dash.ado` is loaded) and `S02` for the clean form (RR-01..RR-14). At the base the main checkout's S02 block is S01's stub, and `WP30_ONLY=S02` there ends "no case ran", r(9), whatever tree is tested.
- **The extractor** (02-17): `DASH_REPO="$S/copy2" $WT/scripts/stata_slot.sh "$S/ext" "$S/copy2/scripts/extract_filter_truth.do"`. Its `filter_truth.json` equals the worktree's apart from `_meta`. Then `env -u DASH_REPO $WT/scripts/stata_slot.sh "$S/ext-unset" "$S/copy2/scripts/extract_filter_truth.do"` logs `r(601);`.

## TDD test stubs

Regression tests (FAIL at the base, saved by 02-01/02-02):

`test/test_runner_portability.py` (new):
- Test: no home-directory path anywhere in the scan set (`TestNoMaintainerPaths::test_no_home_directory_path`). Base: 20 files.
- Test: no `arch -arm64` literal (`TestNoMaintainerPaths::test_no_arch_literal`). Base: 18 files.
- Test: only `scripts/stata_batch.sh` runs `arch` (`TestEveryRunnerUsesTheWrapper::test_only_the_wrapper_invokes_arch`). For `.sh` and the Makefile, comment-stripped `(^|[\s;&|(])arch\s`; for `.py`, `["']arch["']`; for `.do`, `\b(shell|!)\s*arch\b`. The expected set is `{"scripts/stata_batch.sh"}`. Base: the five runners.
- Test, for each shell present (`TestTheWrapper`):
  - `test_an_arm64_machine_gets_the_arm64_slice`;
  - `test_an_x86_64_parent_still_gets_the_arm64_slice` (fake `uname` prints x86_64 for `-m` and logs its arguments; the log never holds `-m`);
  - `test_an_intel_mac_gets_no_prefix`;
  - `test_linux_gets_no_prefix_and_never_asks_sysctl`;
  - `test_an_x86_only_binary_gets_no_prefix`;
  - `test_stata_arch_forces_a_slice_or_none`;
  - `test_a_bad_stata_arch_is_refused`;
  - `test_gui_binaries_are_refused_and_never_run` (the fake binary's marker file is never written);
  - `test_a_missing_binary_is_refused`;
  - `test_arguments_pass_through_unchanged`;
  - `test_print_mode_runs_nothing`.

  Base: the wrapper is missing.
- Test: `TestTheWrapper::test_the_default_is_the_console_binary_and_never_searched_for` (static). The text holds `STATA_BIN:-/usr/local/bin/stata-mp`, and no `/Applications`, `eval`, `ls `, `find ` or backtick command substitution.
- Test: `TestTheWrapper::test_the_real_tools_choose_arm64_from_an_x86_64_parent`, collected on arm64 macOS only. It uses a `stata-mp` copy of `/usr/bin/true` and a fake `arch`, run under `/usr/bin/arch -x86_64 /bin/sh`.
- Test: `TestTheWrapper::test_this_macs_effective_command_is_unchanged`, collected when `/usr/local/bin/stata-mp` exists on arm64 macOS. In print mode, natively and under `/usr/bin/arch -x86_64`, it prints `<arch> <-arm64> </usr/local/bin/stata-mp> <-b> <do> <x.do>`.
- Test: `TestEveryRunnerUsesTheWrapper::test_run_cert_suite_hands_stata_its_own_tree`. A copy of the script, wrapper and verdict goes into `tmp/tree/scripts`. A fake `STATA_BIN` (`stata-mp`, `STATA_ARCH=none`) writes `DASH_REPO`, `STATATMP` and its arguments to `$FAKE_OUT`. The expected values are `DASH_REPO == tmp/tree`, the arguments `-b do tmp/tree/test/run_all_cscripts.do`, and nonzero rc from the verdict on a missing log.
- Test: `TestEveryRunnerUsesTheWrapper::test_run_cert_suite_refuses_a_tree_stata_cannot_be_handed`, with the tree under `tmp/co$py`. It expects rc 2, the message, and that the fake never runs.
- Test: `TestEveryRunnerUsesTheWrapper::test_stata_python_exec_reads_through_the_wrapper`. The fake writes `pyexec.txt`, and the script prints its text.
- Test: `TestEveryRunnerUsesTheWrapper::test_the_makefile_names_stata_bin` (static): `STATA_BIN ?= /usr/local/bin/stata-mp`, the three recipes pass `STATA_BIN=`, no `STATA ?=`, and the rename guard is present.
- Test: `TestEveryRunnerUsesTheWrapper::test_make_refuses_the_old_variable`, collected when `make` is on PATH. `make -n -C <root> cert STATA=/x` gives rc 2 and mentions `STATA_BIN`. `make -n -C <root> cert` prints `STATA_BIN='/usr/local/bin/stata-mp'`.
- Test: `TestTheRunnerRoot::test_the_runner_reads_its_root_from_dash_repo`. Both markers appear once; `local dashdir : environment DASH_REPO`; the `c(pwd)` fallback; one `adopath ++` line, equal to ``adopath ++ "`dashdir'/"``; no `local dashdir "` literal.
- Test: `TestTheRunnerRoot::test_the_root_block_refuses_what_stata_cannot_be_handed`: the six `char()` codes, `exit 198`, `exit 601`, the findfile check, `exit 9`.
- Test: `TestTheRunnerRoot::test_the_header_comment_names_the_wrapper`: `sh scripts/stata_batch.sh -b do test/run_all_cscripts.do` and `DASH_REPO` in lines 1-15.
- Test: `TestTheExtractorRoot::test_each_converted_file_reads_dash_repo`, parametrized over the 16 files (15 extractors and the corpus). Each holds the stanza's first line and sets its own `Z?_REPO` (or uses `` `repo' ``) from it.
- Test: `TestTheExtractorRoot::test_every_root_stanza_is_whole`. Every `scripts/*.do` or `test/fixtures/*.do` holding `local repo : environment DASH_REPO` also holds the `c(pwd)` fallback, the six-code Mata check, `exit 198` and `exit 601`. At least 16 files hold it.
- Test: `TestTheExtractorRoot::test_extract_date_truth_reads_jsonio_from_the_environment`: `: environment STATAJSON_DIR`, no `Programs/Java/StataJSON` literal.
- Test: `TestTheRetiredGenerators::test_each_refuses_before_reading_or_writing[regen_option_surface.py|wire_option_reporting.py]`. First, statically: no home path, and `sys.exit(` precedes the first `open(`. Then a copy runs in `tmp/scripts/` with `tmp/dash.ado` and `tmp/test/fixtures/abbrev_truth.json`. It expects rc ≠ 0, `historical, do not run` in stderr, and `tmp/dash.ado` byte-identical.
- Test: `TestTheStataTree`:
  - `test_DASH_STATA_BASE_overrides_the_default`;
  - `test_DASH_STATA_PLUS_overrides_the_default`;
  - `test_unset_or_empty_gives_the_default`;
  - `test_every_reader_uses_it` (`test_help_claims_1._STATA_BASE == conftest.stata_base()` and the same for `_STATA_PLUS` and `test_help_claims_8._STATA_BASE`; `test_scheme.py` calls `stata_base()` and holds no `Stata 15`).

  Each imports `conftest` inside the test, so the base fails per test, not at collection.

`test/test_wp30_truth.cscript`, S02 block: RR-01..RR-14 ("Test plan"). At the base, RR-01 and RR-03..RR-14 FAIL (no root block) and RR-02 PASSes (the driver runs the worktree).

Guard test (passes at the base; listed apart): `TestNoMaintainerPaths::test_the_scan_covers_every_runner`. The scan set contains the four shell runners, the Makefile, `test/run_all_cscripts.do`, `scripts/measure_stata_coverage.py`, `test/fixtures/twoway_corpus.do` and every `scripts/extract_*.do`, and contains no `test/fixtures/*.json`.

Flipped, never deleted (02-02): the seven nodes of "Tests that pin today's behaviour", with the `_RUNNER` fixture.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Guard: paths, arch literal, only the wrapper runs arch | pytest `TestNoMaintainerPaths`, `TestEveryRunnerUsesTheWrapper` | none | n/a (no page) |
| Wrapper rule, every branch, two shells, real tools | pytest `TestTheWrapper` | fakes in tmp | n/a |
| Runners hand Stata the tree and the wrapper | pytest flips + behavioural runs with a fake binary | none | n/a |
| Runner root block | pytest `TestTheRunnerRoot` (text); cscript RR-01..RR-14 (behaviour) | none | n/a |
| Coverage tool | flipped `test_measure_stata_coverage.py` | `_RUNNER` | n/a |
| Extractors and corpus | pytest `TestTheExtractorRoot`; 02-17 regenerates `filter_truth.json` in a copy | `filter_truth.json` (compared, not committed) | n/a |
| Generators | pytest `TestTheRetiredGenerators` | tmp copy | n/a |
| Stata tree override | pytest `TestTheStataTree`; `test_help_claims_1.py`, `_8.py`, `test_scheme.py` green | none | n/a |
| Wrong tree, end to end | copy acceptance at the base (02-03) and after (02-17) | broken and clean copies | saved and served pages run in batch 1's G8 `make cert` |

**RR cases** (S02 block). `tree` is `c(pwd)` without its trailing `/test`. `scr` is `` `c(tmpdir)'/dash_s02_rr ``, normalised by `_s02_realdir`, holding `notree/` and `my tree/` (an empty `dash.ado` and `test/run_all_cscripts.do`). A `python:` line sets or pops `DASH_REPO`. Each case except RR-01 and RR-02 runs `_s02_run_root`. If RR-01 fails, RR-03..RR-14 FAIL without running (one `_w30_expect` on RR-01's flag each); RR-02 does not depend on the block.

| Case | DASH_REPO | cwd | Expected |
|---|---|---|---|
| RR-01 | — | — | `_s02_root_lines("run_all_cscripts.do", blk) >= 10`; the block holds `: environment DASH_REPO` and no home path (the needle is built as `"/" + "Users/"`, never written whole: the guard scans this script); `tree` and `c(tmpdir)` hold none of the six characters |
| RR-02 | as handed | — | before any case, `c(pwd) == tree + "/test"`; if `DASH_REPO` is set, it names `tree` (a trailing `/` ignored): the run tests the tree it was handed |
| RR-03 | `tree` | test/ | rc 0; `r(pwd) == tree`; `r(fn) == tree + "/dash.ado"` |
| RR-04 | `tree + "/"` | test/ | as RR-03 |
| RR-05 | unset | `tree` | rc 0; `r(pwd) == tree` |
| RR-06 | unset | `scr/notree` | rc 601 |
| RR-07..RR-12 | `scr/co` + `chr(36)`, `chr(96)`, `chr(34)`, `chr(39)`, `chr(10)`, `chr(13)` + `py` | test/ | rc 198 each |
| RR-13 | `scr/notree` | test/ | rc 601 |
| RR-14 | `scr/my tree` | test/ | rc 0; `r(pwd)` is it; `r(fn)` is it + `/dash.ado` |

**Acceptance criteria.**
- **AC-02.1** `python3 -m pytest test/test_runner_portability.py -q -n0` is green with no skip. At the base, every regression test of "TDD test stubs" fails with the recorded text.
- **AC-02.2** Under the driver, `WP30_ONLY=S02` prints RR-01..RR-14 PASS, with no FAIL, no SKIP and no `r(` line.
- **AC-02.3** The broken-copy verdict was PASS (rc 0) at the base and is FAIL (rc ≠ 0) after the fix. A clean copy is PASS and prints RR-01..RR-14 PASS.
- **AC-02.4** The seven flipped nodes pass. The three runner test files report at least 95 passed.
- **AC-02.5** The wrapper's print mode, natively and under an x86_64 parent, prints `<arch> <-arm64> </usr/local/bin/stata-mp> <-b> <do> <x.do>`.
- **AC-02.6** `extract_filter_truth.do`, run on a clean copy with `DASH_REPO` set, writes `filter_truth.json` equal to the committed one apart from `_meta`. Unset from the slot's directory, it stops with r(601).
- **AC-02.7** The full suite is green once in the worktree (queue), and batch 1's G8 `make cert` is green in the main checkout through the new runner: 68 of 68 scripts at that point.

## Tasks

**Commit boundary.** Tasks 02-01 to 02-18 form the one commit, subject `Make the Stata runners portable: the tree from DASH_REPO, the slice from the binary (WP-30 P1.34)`, made by 02-18 on `wp30-s02` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s02`, after one full run through the queue.

The body has three parts:
1. `$S/02-P1.34-failure.txt` first.
2. Then the defect and what changed where.
3. Then one line each:
   - `Regression: test/<file>::<Class>::<test> -- failed at <batch-1 base sha> with <text>` (and `Regression: test/test_wp30_truth.cscript RR-01 -- …`);
   - one `Flipped:` line per flip, from `$S/02-flips.txt`;
   - `BUGS.md: "<title>" (closed)`.

There is no `Fixture:` line, because no fixture is added.

Further rules:
- **Variables.** `S=<scratch>/s02`, with `<scratch>` the orchestrator's WP-30 scratch directory. `MAIN=/Users/billy/Desktop/Programs/StataPrograms/d/dash`.
- **Where commands run.** Every command runs with absolute paths. Never `cd` into the main checkout to edit.
- **No AI references.** No commit text, BUGS line or CHANGELOG line names an AI tool, vendor or the project instructions file (G7, A141).

<task type="auto" id="02-01">
  <name>Write the failing regression tests</name>
  <files>test/test_runner_portability.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    First check the base: `git -C "$WT" rev-parse HEAD` equals `cat <scratch>/batch-1-base.txt`, `git -C "$WT" branch --show-current` prints `wp30-s02`, and `<scratch>/batch-1-impact.txt` lists the symbols of Evidence "Blast radius" (report any HIGH/CRITICAL before editing). Run `mkdir -p "$S"`. Create `test/test_runner_portability.py` with every class and test of "TDD test stubs" under TR-02.13's scan-set and needle rules (needles built by concatenation; fakes written into `tmp_path` and `chmod 0o755`; `subprocess.run` with argv lists, `env=` dicts and `timeout=30`; `conftest` imported inside the `TestTheStataTree` tests; the static precondition before any execution). In `test/test_wp30_truth.cscript`, put TR-02.14's helpers directly above S01's `* ==== S02 P1.34` header and the RR-01..RR-14 cases of "Test plan" between S01's `S02 start` and `S02 end` display lines, each reported through `_w30_expect`/`_w30_done` (TR-02.14), with no `exit` in the block. Run `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -rf > "$S/02-01-pytest.log" 2>&1` and the driver of "Stata truth" with `$MAIN/scripts/stata_slot.sh`. Write `$S/02-P1.34-failure.txt`: the base sha, each failing test's first failure line, RR-01 and RR-03..RR-14 FAIL lines, the guard test that passes and RR-02 PASS. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/02-01-pytest.log"` prints at least 50 (60 by the stub count with both shells); `tail -1 "$S/02-01-pytest.log"` contains `1 passed` (the guard test alone); `grep -oE "^RR-(0[13-9]|1[0-4]) FAIL" "$S/run_test_wp30_truth.log" | sort -u | wc -l` prints 13 (a case may print several FAIL lines, one per failed `_w30_expect`); `grep -c "^RR-02 PASS" "$S/run_test_wp30_truth.log"` prints 1; `test -s "$S/02-P1.34-failure.txt"`.]]></verify>
  <done>Every regression test of the section existed and was shown failing on the unmodified tree, with the failure text saved for the commit body.</done>
</task>

<task type="auto" id="02-02">
  <name>Flip the pinned runner tests</name>
  <files>test/test_cert_verdict.py, test/test_release_verdict.py, test/test_measure_stata_coverage.py</files>
  <action><![CDATA[
    Flip, in place, each node of Evidence "Tests that pin today's behaviour" in these three files.
    - `TestMakeCheckIsWired::test_stata_runs_only_through_the_console_binary` is parametrized over `run_cert_suite.sh`, `stata_python_exec.sh`, `stata_slot.sh` and `run_release_gate.sh`. It asserts `'sh "$REPO/scripts/stata_batch.sh" -b do' in script`, the `REPO="$(cd "$(dirname "$0")/.." && pwd)"` line, `'STATATMP="$dir/tmp/"'`, no `'"$STATA"'`, no `StataMP.app` or `open -a`, and `'STATA_BIN:-/usr/local/bin/stata-mp'` in `scripts/stata_batch.sh`. It never writes the old literal.
    - The two release-verdict tests assert the wrapper call: exactly 2 occurrences, and the `PIP_NO_INDEX=1 STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do` form.
    - In `test_measure_stata_coverage.py`, change `_RUNNER` (:174-200) to the env-rooted header lines `local dashdir : environment DASH_REPO` and ``adopath ++ "`dashdir'/"``. Flip `test_paths_marks_and_flushes` (no `/w/tree` written; the header kept; marks and flushes as before). Extend `test_a_malformed_runner_is_refused` with a literal-root runner, which must raise `ValueError` matching `DASH_REPO`. Flip `test_stata_runs_the_console_binary_with_its_own_tmp` to argv `["sh", os.path.join(m.REPO, "scripts", "stata_batch.sh"), "-b", "do", str(tmp_path / "x.do")]` and `seen["env"]["DASH_REPO"] == str(tmp_path / "tree")`.

    Write one `Flipped: <node> -- <old> was wrong because <why>` line per node to `$S/02-flips.txt`.

    Run the three files at the base. Append every failure line to `$S/02-P1.34-failure.txt`, including the `TestTheGeneratedRunner`/`TestPrepare` nodes the `_RUNNER` change turns red, marked "red at the base because the fixture now carries the env-rooted header".
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_cert_verdict.py test/test_release_verdict.py test/test_measure_stata_coverage.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports failures (red at the base); `grep -c '^Flipped: ' "$S/02-flips.txt"` prints 6; `grep -c 'arch -arm64' test/test_cert_verdict.py test/test_release_verdict.py test/test_measure_stata_coverage.py` prints 0 for each.]]></verify>
  <done>The six pinned nodes asserted the wrapper and the environment root, and their failures at the base were recorded with their reasons.</done>
</task>

<task type="auto" id="02-03">
  <name>Measure the wrong-tree verdict at base</name>
  <files>none</files>
  <action><![CDATA[
    Run the copy acceptance of "Stata truth" in its broken form (`WP30_ONLY=S01`), against the worktree as 02-01/02-02 left it: the runner header is still the base's. Use `$MAIN/scripts/stata_slot.sh` and `$S/acc-base` as the slot directory.

    Record in `$S/02-P1.34-failure.txt`:
    - the verdict's output and rc;
    - `grep -c "$MAIN" "$S/acc-base/run_s02.log"`;
    - `grep -c "RR-0" "$S/acc-base/run_s02.log"`.

    The base header cds into the main checkout and runs its TF-01 against the main checkout's `dash.ado`. So the verdict is PASS, rc 0, for a copy whose `dash.ado` starts with `exit 9`, and no RR line appears. That is K1-a measured.

    Delete `$S/copy` afterwards. Nothing in `$WT` changes.
  ]]></action>
  <verify><![CDATA[`grep -c "verdict rc=0" "$S/02-P1.34-failure.txt"` prints 1; `git -C "$WT" status --porcelain | grep -vc 'test_runner_portability.py\|test_wp30_truth.cscript\|test_cert_verdict.py\|test_release_verdict.py\|test_measure_stata_coverage.py'` prints 0.]]></verify>
  <done>The base runner was shown certifying a copy with a broken dash.ado as passing, because it tested the main checkout.</done>
</task>

<task type="auto" id="02-04">
  <name>Create the Stata batch wrapper</name>
  <files>scripts/stata_batch.sh</files>
  <action><![CDATA[
    Create `scripts/stata_batch.sh` with exactly the text of TR-02.1, and `chmod 755` it.

    Do not edit any caller yet.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k TestTheWrapper` passes with no skip; `STATA_BATCH_PRINT=1 sh "$WT/scripts/stata_batch.sh" -b do x.do` prints `<arch> <-arm64> </usr/local/bin/stata-mp> <-b> <do> <x.do>`; `/usr/bin/arch -x86_64 /bin/sh -c 'STATA_BATCH_PRINT=1 sh "$0" -b do x.do' "$WT/scripts/stata_batch.sh"` prints the same line.]]></verify>
  <done>One script chose the console binary and its slice from the machine and the binary, refused GUI binaries, and on this Mac produced the same command as before.</done>
</task>

<task type="auto" id="02-05">
  <name>Route the slot, cert and pyexec runners</name>
  <files>scripts/stata_slot.sh, scripts/run_cert_suite.sh, scripts/stata_python_exec.sh</files>
  <action><![CDATA[
    Apply TR-02.2, TR-02.3 and TR-02.4.
    - **`stata_slot.sh`:** a `REPO=` line, and the wrapper call at :10.
    - **`run_cert_suite.sh`:** delete `STATA=`; add the six-character refusal (exit 2); add the `testing $REPO` echo; use `DASH_REPO="$REPO"` and the wrapper call at :17; rewrite the header comment.
    - **`stata_python_exec.sh`:** a `REPO=` line, the wrapper call, the message naming STATA_BIN, and the header comment.

    Keep `set -u`, every lock directory, `STATATMP="$dir/tmp/"` and both log paths unchanged.

    Before saving `stata_slot.sh`, confirm that no Stata of this section holds a slot. The edit is in the worktree, and the main checkout's copy keeps serving other agents.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_runner_portability.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider -k "run_cert_suite or stata_python_exec or console_binary"` passes; `/bin/sh -n "$WT/scripts/stata_slot.sh" && /bin/dash -n "$WT/scripts/run_cert_suite.sh" && /bin/dash -n "$WT/scripts/stata_python_exec.sh"` exits 0.]]></verify>
  <done>The slot, the certification runner and the python_exec reader started Stata through the wrapper, and the certification runner handed Stata its own tree.</done>
</task>

<task type="auto" id="02-06">
  <name>Route the release gate and Makefile</name>
  <files>scripts/run_release_gate.sh, Makefile</files>
  <action><![CDATA[
    Apply TR-02.5:
    - delete :12;
    - use the wrapper call at :34 and :42;
    - make the header comment name STATA_BIN.

    Apply TR-02.6:
    - rename `STATA` to `STATA_BIN`, and add the `ifeq ($(origin STATA),command line)` guard;
    - make the `test`, `cert` and `gate` recipes pass `STATA_BIN='$(STATA_BIN)'`;
    - add the `help` line, and rewrite comment line 10.

    Do not change the `check`, `release` or `hooks` recipes, the log-renaming loop, or `PIP_NO_INDEX=1`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_release_verdict.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "makefile or old_variable"` passes; `make -n -C "$WT" cert STATA=/x; echo $?` prints a line naming STATA_BIN and `2`.]]></verify>
  <done>The release gate and every make target started Stata through the wrapper under one variable name, and the old name stopped make with a message.</done>
</task>

<task type="auto" id="02-07">
  <name>Read the runner root from DASH_REPO</name>
  <files>test/run_all_cscripts.do, scripts/measure_stata_coverage.py</files>
  <action><![CDATA[
    In `test/run_all_cscripts.do`:
    - replace the header comment (:1-13) as TR-02.7 says;
    - replace :21-28 (the two comments, the literal adopath, `local dashdir`, `local testdir`, `cd`) with TR-02.7's root block, between its two marker lines.

    In `scripts/measure_stata_coverage.py`, apply TR-02.8: `STATA`, `_stata` (add `DASH_REPO`) and `runner_do` (validate; stop rewriting).

    Do not touch any script block, the summary, or `global dash_nobrowser 1`.

    Then run the driver of "Stata truth" with `$WT/scripts/stata_slot.sh`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_measure_stata_coverage.py test/test_cscript_hygiene.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k TestTheRunnerRoot` passes; `grep -cE "^RR-(0[1-9]|1[0-4]) PASS" "$S/run_test_wp30_truth.log"` prints 14, `grep -c "ALL CHECKS PASSED" "$S/run_test_wp30_truth.log"` prints 1 and `grep -c " FAIL\|^r([0-9]*);" "$S/run_test_wp30_truth.log"` prints 0.]]></verify>
  <done>The certification runner and the coverage tool tested exactly the tree they were handed, refusing a root Stata cannot be handed and any directory that is not a dash tree.</done>
</task>

<task type="auto" id="02-08">
  <name>Root the jsonio extractors and the corpus</name>
  <files>scripts/extract_abbrev_truth.do, scripts/extract_date_truth.do, test/fixtures/twoway_corpus.do</files>
  <action><![CDATA[
    Apply TR-02.9 to these three files.
    - **`extract_abbrev_truth.do`:**
      - rewrite the comment at :10-15;
      - delete :39;
      - replace :40 with the stanza and ``adopath ++ "`repo'/"``;
      - make :45 read ``global ZQ_REPO "`repo'"``.
    - **`extract_date_truth.do`:**
      - rewrite the comment at :10-15;
      - replace :64 with the STATAJSON_DIR lines;
      - replace :65 with the stanza and the adopath;
      - set `ZQ_REPO` from `` `repo' `` at :67;
      - make the `ZQ_JSONIO_*` globals at :69-71 conditional;
      - add one header sentence on STATAJSON_DIR.
    - **`twoway_corpus.do`:**
      - rewrite the comment at :27-35;
      - delete :53;
      - replace :54 with the stanza and the adopath;
      - keep the no-`version` rule.

    The message prefix in each stanza is the file's own name. Change no other line.
  ]]></action>
  <verify><![CDATA[`grep -c '/Users/\|arch -arm64\|Programs/Java' scripts/extract_abbrev_truth.do scripts/extract_date_truth.do test/fixtures/twoway_corpus.do` prints 0 for each; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "abbrev or date_truth or twoway_corpus or jsonio"` passes; `python3 -m pytest test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The two jsonio-era extractors and the twoway corpus read their tree from DASH_REPO or a dash-tree working directory, and jsonio only from STATAJSON_DIR.</done>
</task>

<task type="auto" id="02-09">
  <name>Root the SVG-text extractors</name>
  <files>scripts/extract_axis_truth.do, scripts/extract_text_truth.do, scripts/extract_unlabelled_truth.do</files>
  <action><![CDATA[
    Apply TR-02.9 to these three files.
    - **`extract_axis_truth.do`:** rewrite the comment at :15-16, and replace `global ZA_REPO` at :85 with the stanza and ``global ZA_REPO "`repo'"``.
    - **`extract_text_truth.do`:** rewrite :23-24, delete the comment at :59-64, and replace :65 the same way.
    - **`extract_unlabelled_truth.do`:** rewrite :21-22, and replace `ZU_REPO` at :54.

    The `capture shell cd … && git rev-parse` lines and every python block are unchanged, because they read the globals.
  ]]></action>
  <verify><![CDATA[`grep -c '/Users/\|arch -arm64' scripts/extract_axis_truth.do scripts/extract_text_truth.do scripts/extract_unlabelled_truth.do` prints 0 for each; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "axis_truth or text_truth or unlabelled"` passes.]]></verify>
  <done>The three SVG-text extractors took their tree from DASH_REPO and could no longer write into another checkout.</done>
</task>

<task type="auto" id="02-10">
  <name>Root the format, function and stat extractors</name>
  <files>scripts/extract_format_truth.do, scripts/extract_function_truth.do, scripts/extract_stat_truth.do</files>
  <action><![CDATA[
    Apply TR-02.9 to these three files.
    - **`extract_format_truth.do`:** rewrite the comment at :14-15, and replace `ZF_REPO` at :38.
    - **`extract_function_truth.do`:** rewrite :24-25, and replace `ZF_REPO` at :56. This file is also extended later by S26; keep its `version 19` at :47.
    - **`extract_stat_truth.do`:** rewrite the comment at :13-14 (prefix and path), and replace `ZQ_REPO` at :67.

    Each global is then set from `` `repo' ``.
  ]]></action>
  <verify><![CDATA[`grep -c '/Users/\|arch -arm64' scripts/extract_format_truth.do scripts/extract_function_truth.do scripts/extract_stat_truth.do` prints 0 for each; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "format_truth or function_truth or stat_truth"` passes.]]></verify>
  <done>The format, function and statistics extractors read their tree from DASH_REPO.</done>
</task>

<task type="auto" id="02-11">
  <name>Root the smoke, filter and rows extractors</name>
  <files>scripts/extract_svg_truth_smoke.do, scripts/extract_filter_truth.do, scripts/extract_embedded_rows_truth.do</files>
  <action><![CDATA[
    Apply TR-02.9 to these three files.
    - **`extract_svg_truth_smoke.do`:** rewrite the comment at :16-17, and replace `ZS_REPO` at :45.
    - **`extract_filter_truth.do` and `extract_embedded_rows_truth.do`:**
      - reword the comments at :5-7 to name `DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/<file>.do`;
      - replace :9, the `if ${ZA_REPO}==""` fallback to the main checkout, with the stanza and ``global ZA_REPO "`repo'"``.

    The global ZA_REPO override is dropped. DASH_REPO is the one way in.
  ]]></action>
  <verify><![CDATA[`grep -c '/Users/' scripts/extract_svg_truth_smoke.do scripts/extract_filter_truth.do scripts/extract_embedded_rows_truth.do` prints 0 for each; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "smoke or filter_truth or embedded_rows"` passes.]]></verify>
  <done>The smoke, filter and embedded-rows extractors stopped falling back to the main checkout.</done>
</task>

<task type="auto" id="02-12">
  <name>Root the join-order and colorvar extractors</name>
  <files>scripts/extract_join_order_truth.do, scripts/extract_colorvar_truth.do, scripts/extract_colorvar_qualifier_truth.do</files>
  <action><![CDATA[
    Apply TR-02.9 to these three files.
    - **`extract_join_order_truth.do`:**
      - in the comment at :10-13, delete "DASH_REPO defaults to the main checkout";
      - replace :15-16 with the stanza;
      - keep :17-18 (adopath, `dash_nobrowser`) and every later `` `repo' ``.
    - **`extract_colorvar_truth.do`:** replace :34-37 (the literal and the env override) with the stanza and ``global ZS_REPO "`repo'"``, keeping :40's adopath. Rewrite the comment at :11-12.
    - **`extract_colorvar_qualifier_truth.do`:** replace :30-33 with the stanza and ``global ZQ_REPO "`repo'"``, and rewrite :13.
  ]]></action>
  <verify><![CDATA[`grep -c '/Users/' scripts/extract_join_order_truth.do scripts/extract_colorvar_truth.do scripts/extract_colorvar_qualifier_truth.do` prints 0 for each; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "join_order or colorvar"` passes.]]></verify>
  <done>The join-order and colour-variable extractors refused to run without a dash tree instead of measuring the main checkout.</done>
</task>

<task type="auto" id="02-13">
  <name>Clear the last extractor and doc literals</name>
  <files>scripts/extract_emptied_layer_truth.do, scripts/extract_alias_spelling_truth.do, test/test_geometry_visual.md</files>
  <action><![CDATA[
    Apply TR-02.9 to `extract_emptied_layer_truth.do`: replace :29-32 with the stanza and ``global ZE_REPO "`repo'"``, keep :35's adopath and :38's `dash_nobrowser`, and rewrite :10.

    Apply TR-02.10 to two files:
    - in `extract_alias_spelling_truth.do`, rewrite the comment at :23-25 only;
    - in `test/test_geometry_visual.md`, delete the StataJSON adopath line at :15, and change :21 to the wrapper call.
  ]]></action>
  <verify><![CDATA[`git -C "$WT" grep -n -E '/Users/[^/]+/|arch -arm64' -- 'scripts/*.do' 'test/fixtures/*.do' 'test/*.md'` prints nothing; `python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k TestTheExtractorRoot` passes.]]></verify>
  <done>No do-file or procedure under scripts/ or test/ named the maintainer's path or the fixed prefix.</done>
</task>

<task type="auto" id="02-14">
  <name>Retire the two option generators</name>
  <files>scripts/regen_option_surface.py, scripts/wire_option_reporting.py</files>
  <action><![CDATA[
    Apply TR-02.11 (the ratified form; if `<scratch>/wp30-ratified.txt` row 26 reads "struck", apply TR-02.11's struck form instead).

    In each file:
    - the docstring's first line becomes the RETIRED line;
    - the first statements after the docstring are `import sys` and the `sys.exit(...)` refusal;
    - the `REPO` literal becomes the `__file__` form, with `import os`.

    Do not edit `wire_option_reporting.py:115` or any other line: they are S03's, and historical.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k TestTheRetiredGenerators` passes; `grep -c '/Users/' scripts/regen_option_surface.py scripts/wire_option_reporting.py` prints 0 for each; `grep -c 'version 16.0' scripts/wire_option_reporting.py` prints 1.]]></verify>
  <done>Both generators refused to run before reading or writing any file, so neither could rewrite a checkout's dash.ado.</done>
</task>

<task type="auto" id="02-15">
  <name>Read Stata's tree from the environment</name>
  <files>test/conftest.py, test/test_help_claims_1.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Apply TR-02.12:
    - add `STATA_BASE_DEFAULT`, `STATA_PLUS_DEFAULT`, `stata_base()` and `stata_plus()` to `test/conftest.py`, after `_strict()` (:252-255);
    - in `test_help_claims_1.py`, import them and set `_STATA_BASE`/`_STATA_PLUS` from them (:76-78);
    - in `test_help_claims_8.py`, set `_STATA_BASE` from `stata_base()` (:558).

    No test of either help-claims file changes otherwise.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_runner_portability.py -q -n0 -p no:cacheprovider -k "TestTheStataTree and not every_reader"` passes; `python3 -m pytest test/test_help_claims_1.py test/test_help_claims_8.py -q -p no:cacheprovider` passes; `DASH_STATA_BASE=/nonexistent python3 -m pytest "test/test_help_claims_1.py::TestTheHeader::test_stata_is_installed_where_the_links_are_checked" -q -n0 -p no:cacheprovider` fails naming `/nonexistent`.]]></verify>
  <done>The help-claims tests read Stata's base and PLUS trees from DASH_STATA_BASE and DASH_STATA_PLUS, defaulting to StataNow's.</done>
</task>

<task type="auto" id="02-16">
  <name>Clear the last literals from the tests</name>
  <files>test/test_scheme.py, test/test_date_range.py, test/test_qualifier_logic.py</files>
  <action><![CDATA[
    In `test/test_scheme.py::TestSecurity::test_real_stata_scheme_via_cwd_copy` (:530-541), read `os.path.join(stata_base(), "s", "scheme-s2color.scheme")` with `from conftest import stata_base`, and write TR-02.12's skip text. Record its `Flipped:` line in `$S/02-flips.txt`: Stata 15's tree, which M2 retires and no other machine has, became the configured Stata 19 tree, where `p_colors[0]` is the same `#1a476f`.

    Reword the docstrings at `test_date_range.py:36` and `test_qualifier_logic.py:31` as TR-02.10 says.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_runner_portability.py test/test_scheme.py test/test_date_range.py test/test_qualifier_logic.py -q -n0 -p no:cacheprovider` passes with no skip on this Mac; `grep -c '^Flipped: ' "$S/02-flips.txt"` prints 7.]]></verify>
  <done>The whole portability test file was green: no runner, extractor, doc or test under scripts/, test/ or the Makefile held the maintainer's path or the fixed prefix.</done>
</task>

<task type="auto" id="02-17">
  <name>Certify the runners against Stata</name>
  <files>none</files>
  <action><![CDATA[
    Run everything through `$WT/scripts/stata_slot.sh`, so the new slot and wrapper start the real Stata.

    1. **The driver**, with `DASH_REPO="$WT" WP30_ONLY=S02`.
    2. **The copy acceptance**, twice, in fresh `$S/copy` and `$S/acc-*` directories:
       - broken form (`WP30_ONLY=S01`): the verdict FAILs with rc ≠ 0, and the log shows `r(9)` from `../dash.ado`;
       - clean form (omit the `exit 9` line; `WP30_ONLY=S02`): the verdict PASSes with rc 0, and RR-01..RR-14 PASS and `test_wp30_truth: ALL CHECKS PASSED` appear in `run_s02.log`.
    3. **The extractor run** of "Stata truth" on a clean `$S/copy2`. Compare `$S/copy2/test/fixtures/filter_truth.json` with `$WT/test/fixtures/filter_truth.json` with `_meta` removed (`python3 -c` with `json.load`; equal). Then run it with `env -u DASH_REPO`.

    Append each command and its decisive log line to `$S/02-accept.txt`, with these exact result lines:
    - `broken verdict rc=<n>`;
    - `clean verdict rc=<n>`;
    - `filter_truth equal` (or `filter_truth differs: <keys>`, which stops the task).

    `python_exec` hazard: if a log shows `exit 222` or `SKIP`, check `~/.stata19/console/stata19.rc` and re-run; a skip is not a pass.
  ]]></action>
  <verify><![CDATA[`grep -cE "^RR-(0[1-9]|1[0-4]) PASS" "$S/run_test_wp30_truth.log"` prints 14; `grep -c "broken verdict rc=[1-9]" "$S/02-accept.txt"` prints 1 and `grep -c "clean verdict rc=0" "$S/02-accept.txt"` prints 1; `grep -c "filter_truth equal" "$S/02-accept.txt"` prints 1; `grep -c '^r(601);' "$S/ext-unset/extract_filter_truth.log"` is at least 1.]]></verify>
  <done>Stata itself showed that the runner certified the tree it was handed (failing a broken copy and passing a clean one), and that a converted extractor reproduced its fixture from a copy and refused to run outside a dash tree.</done>
</task>

<task type="auto" id="02-18">
  <name>Close P1.34 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.34"]`. In BUGS.md, close that entry in place (`- [x]`) and replace its Resolution with:

    `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.34). test/run_all_cscripts.do reads the tree under test from DASH_REPO, else the current directory when it holds dash.ado and test/run_all_cscripts.do (r(601) otherwise; r(198) for a double quote, dollar sign, single quote, backtick or line break), and stops (exit 9) unless dash.ado resolves inside it; scripts/run_cert_suite.sh exports DASH_REPO for its own checkout and scripts/measure_stata_coverage.py for its scratch tree, so make cert in a worktree or copy tests that tree and fails a broken one. Every runner starts Stata through scripts/stata_batch.sh: STATA_BIN, else /usr/local/bin/stata-mp, never searched for; console binaries only; arch -arm64 only when the machine reports hw.optional.arm64 and the binary holds an arm64 slice, also from an x86_64 parent process, where uname -m is wrong. The 15 extractors and test/fixtures/twoway_corpus.do read their root the same way, the two option generators are retired and refuse to run, and the help-claims tests read DASH_STATA_BASE and DASH_STATA_PLUS. Nothing is drawn, so saved and served pages are unchanged. Pinned by test/test_runner_portability.py::TestNoMaintainerPaths::test_no_home_directory_path, test/test_runner_portability.py::TestTheWrapper::test_an_x86_64_parent_still_gets_the_arm64_slice, test/test_runner_portability.py::TestEveryRunnerUsesTheWrapper::test_run_cert_suite_hands_stata_its_own_tree, test/test_runner_portability.py::TestTheRetiredGenerators::test_each_refuses_before_reading_or_writing, test/test_wp30_truth.cscript RR-02. Residual, deferred (WP-30): measuring dash on Linux, Windows, Intel macOS and GUI Stata, with WP-29's private-file, lifecycle, served-key and PEP 668 paths there, is the deferred platform package (M4).`

    Delete the `"P1.34"` key line from `WP30_OPEN`.

    In CHANGELOG.md, replace `<!-- WP-30 P1.34 -->` in place with: `- The certification, release and test runners no longer hard-code the maintainer's checkout or arch -arm64. make cert tests the tree it is run in (DASH_REPO, else the current directory when it is a dash tree, else r(601)): it tested the main checkout, so a broken worktree or copy could pass. Stata is started by scripts/stata_batch.sh, which takes the binary from STATA_BIN (the Make variable STATA is now STATA_BIN) and chooses the arm64 slice from the machine and the binary. scripts/regen_option_surface.py and scripts/wire_option_reporting.py are retired and refuse to run. (WP-30, P1.34)`

    Then:
    1. Run `python3 -m pytest test/test_tracking_documents.py test/test_runner_portability.py -q -n0 -p no:cacheprovider`.
    2. Run `git -C "$WT" merge --no-edit main`, expecting `Already up to date.`.
    3. Run one full suite: `<scratch>/full_suite_queue.sh "$WT" "$S/02-full-1.log"`, in the background, waiting for its `exit=` line (E1; E6 for the known flaky tests).
    4. Stage exactly these files, all with `git add` and no `-f`:
       - `scripts/stata_batch.sh`, `scripts/stata_slot.sh`, `scripts/run_cert_suite.sh`, `scripts/stata_python_exec.sh`, `scripts/run_release_gate.sh`, `Makefile`;
       - `test/run_all_cscripts.do`, `scripts/measure_stata_coverage.py`;
       - the 16 extractor do-files, `test/fixtures/twoway_corpus.do`, `test/test_geometry_visual.md`;
       - the two generators;
       - `test/conftest.py`, `test/test_help_claims_1.py`, `test/test_help_claims_8.py`, `test/test_scheme.py`, `test/test_date_range.py`, `test/test_qualifier_logic.py`;
       - the three flipped files, `test/test_runner_portability.py`, `test/test_wp30_truth.cscript`;
       - BUGS.md, CHANGELOG.md, `test/test_tracking_documents.py`.
    5. Check G6: `git -C "$WT" diff --cached --name-only | wc -l` prints 42, and none of the project instructions file, `.gitignore`, `AGENTS.md`, `.ultraplan/`, `.gitnexus/` or `*.html` is staged.
    6. Write the message (the boundary's subject and body) to `$S/02-msg.txt`. Run G7 (`grep -Eic 'claude|anthropic'` prints 0) before committing. Check that `git -C "$WT" branch --show-current` prints `wp30-s02`. Commit with `git -C "$WT" commit -F "$S/02-msg.txt"`, and run G7 again on `git log -1 --format=%B`.
    7. Report the sha to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/02-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s | grep -c '(WP-30 P1.34)$'` prints 1; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.34 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.34": "' "$WT/test/test_tracking_documents.py"` prints 0 (the key-deletion check of TR-01.10.1; `WP30_LISTS`/`WP30_SECTION` keep their `"P1.34"` rows).]]></verify>
  <done>P1.34 was closed in BUGS.md naming existing tests, its CHANGELOG marker became the Fixed line, and one green commit on wp30-s02 was ready for the merger.</done>
</task>

## Section completion criteria

- `scripts/stata_batch.sh` is the only place that runs `arch`. Every runner, the Makefile and `measure_stata_coverage.py` start Stata through it. On this Mac its command is `arch -arm64 /usr/local/bin/stata-mp -b do <file>`, natively and from an x86_64 parent.
- `make cert` and the coverage tool test the tree they are handed. A broken copy FAILs, and a clean copy PASSes, with RR-01..RR-14 PASS.
- No text file under `scripts/` or `test/`, and not the Makefile, holds `arch -arm64` or a home-directory path. The guard has no exemption list.
- The 15 extractors and the corpus read `DASH_REPO`, never falling back to another checkout. `extract_filter_truth.do` reproduced its fixture from a copy.
- Both generators refuse to run. The help-claims tests and `test_scheme.py` read the configured Stata tree.
- No shipped file, fixture, hook or project-instructions line changed.
- One green commit `(WP-30 P1.34)` exists, carrying:
  - the failure text;
  - the `Regression:` and seven `Flipped:` lines;
  - the closed entry, with its key and marker gone.

## Notes

- **Landing `stata_slot.sh` (merger).** Immediately before `git apply`, `ls -d /tmp/dash-stata-slot-*.d 2>/dev/null` must print nothing. A slot held by a running Stata waits.
  - After landing, every agent's slot calls `sh "$REPO/scripts/stata_batch.sh"` from the main checkout. The effective command is identical (AC-02.5).
  - S03's worktree, cut from the same base, keeps its own old slot until it lands. That is harmless.
- **Merge order S02, S03 (index batch 1).** These files are touched by both:
  - `scripts/wire_option_reporting.py`: S02 owns the docstring, refusal and `REPO` lines; S03 owns :115.
  - `test/test_wp30_truth.cscript`: own blocks (R1).
  - BUGS.md, `WP30_OPEN`: adjacent `"P1.34"`/`"P1.35"` key lines conflict in context only, and the merger applies both (R5).
  - CHANGELOG: different lists (R4).

  No two edits share a line.
- **The first full `make cert` through the new runner** is batch 1's G8 (cert mode, the queue), after S03 lands. A red there that traces to the runner header, the wrapper or `run_cert_suite.sh` belongs to S02. It is fixed in a fresh `wp30-s02` worktree (index "A red result belongs to the section that owns the test").
- **Not run in the section:** `stata_python_exec.sh` and `run_release_gate.sh` start Stata outside the slot. Their real runs are `make test` and `make gate` at S58.5; here they are covered by the fake-binary and static tests.
- **R1:** only the S02 block and its helpers, directly above S02's header. No `capture python`, no brace in a gated python line, no new script and no hygiene pin.
- **R4/R5:** one marker, under `### Fixed in WP-30`; one entry; one key.
- **R7:** the stanza is A130's form for every later extractor. A new extractor copies TR-02.9 verbatim, with its own message prefix, and is run as `DASH_REPO=<wt> <slot> <scratch> <wt>/scripts/<file>.do`. No fixture is regenerated here.
- **R9:** seven `Flipped:` lines.
- **No change** under R2, R3, R10 or R12.
- **The guard scans its own file.** Never write a needle literally in a test, a comment or a docstring under `scripts/` or `test/`. Write `arch` and the flag apart, or describe them in words.
- **`clear all` keeps macros.** It keeps the stanza's `repo` local and the globals set from it, as WP-29 measured for `dash_nobrowser`. `cscript` drops globals but keeps `S_ADO` (P3).
- **The full-suite hook's launch check** matches `stata-mp … do …run_all_cscripts.do` in a typed command. It does not see `sh scripts/stata_batch.sh -b do test/run_all_cscripts.do`, although its process check still sees the Stata process. Never type that command; `make cert` goes through the queue.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then exits 222, and a SKIP is not a pass.
- **Commit body line forms.** BRIEF's, with WP-30 ids. "failed at" is `batch-1-base.txt`'s sha.

**Notes for the closeout (S58; A145).**
- **GAPS2 K1:** Tracked `Closed in WP-30, BUGS.md "<WP30 P1.34 title>", commit <sha>`.
  - K1-a (wrong tree) and K1-b (fixed arch) are closed.
  - K1-c and K1-d (extractor paths, no guard; P3.7's sources) are done by this commit too (IR-8). P3.7 loses its extractor-path part, and keeps the four `W29_REPO` extractors' root convention (P1.34.4).
- **GAPS2 H intro (platforms, GUI) and DROPIN P1.34:** closed under M4 by this commit. The rest is one ROADMAP platform package (P1.34.6):
  - Linux, Windows (the `/e` batch flag, cmd.exe, `Scripts\python.exe` venvs), Intel macOS and GUI Stata;
  - WP-29's S08/S09/S13 paths there;
  - P1.28 B3, P1.29 option B and the P1.33 Windows patch;
  - critic item 10: `release_gate_venv.do:32,50` `gatevenv/bin/python`, the `/tmp/dash-stata-slot-N.d` locks, the Makefile's `STATA_BIN` default, and the `W29_REPO` extractors' `capture shell cd … && git rev-parse` (POSIX shell).
- **For the maintainer, not edited (P1.34.1):** project rule 10 and the GUI-block hook's message still name `arch -arm64 /usr/local/bin/stata-mp -b do`. On this Mac that is exactly the wrapper's command. Revisit them with the platform package.
- **For the maintainer:** the full-suite hook's launch-text check does not recognise a wrapper launch of the runner.
- **REMAINING.md:** `regen_option_surface.py` (:813-865, :1615-1659) is retired. Those entries describe a script that now refuses to run.
- **AGENTS.md invariant** (if AGENTS.md is clean, E7): Stata is started only through `scripts/stata_batch.sh` (`STATA_BIN`, `STATA_ARCH`). Runners and extractors read the tree from `DASH_REPO`. `test/test_runner_portability.py` guards `scripts/`, `test/` and the Makefile against the fixed prefix and home paths.
