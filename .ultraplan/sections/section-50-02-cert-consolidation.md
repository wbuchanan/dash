# Section 50-02: Certification: fewer loads and balanced shards, one truth script per WP

> Part of: WP-50 (Test-suite speed, Q29; CLAUDE.md rule 11) · Items: none · Risk: yellow · Batch: 50.2 · Depends on: 50-01 · Blocks: 50-04 · Tasks: 4, 2 commits · Case-id prefix: Q5002

## Overview

**What is wrong today.** The certification half of the gate is the larger fixed cost. At 18oct2026 its 69 scripts summed 2,127 s over three sessions (804 s wall), and the two WP truth scripts were 1,023 s of it (test/run_all_cscripts.do:156-157: `test_wp30_truth.cscript 566.6 0 * * *`, `test_wp31_truth.cscript 456.4 0 * * *`). Every truth script in a `* * *` row "starts in every cert session and loads dash_parse.mata + dash.ado (`qui do`, about 26,000 lines) once per session" ([C] §2.4.6); PD-6 adds fourteen more (WP 33, 34, 35, 36, 37, 40, 41, 42, 43, 44, 45, 46, 47, 49), each made from 33-01's template, which reads DASH_CERT_SHARD and so is a `* * *` row. By WP-50 sixteen truth scripts cost sixteen `clear all` + loads in each of three sessions -- 48 loads -- however short a script is. And the template's parts ignore time: its seconds table is `local w@@WP@@_secs S00 1` (33-01, N-6), so every block of a template-made script counts 1 s and a session can draw all the long blocks. The handoff analysis's C3 ("load dash_parse.mata/dash.ado with `run` (no echo) instead of `do`") was never taken ([C] §7.3).

**After this section.** Every WP truth script stays its own file, with its blocks, cases and case ids where they are (A-3; Q38, M13, PD-6: one truth script per WP). Every certification script loads dash with `run`. A template-made truth script splits itself over the sessions only when it is long enough to need it (D-50-02.b); a shorter one runs whole in one session and so clears and loads dash once instead of three times. A splitting script balances its parts on its blocks' measured seconds, which `scripts/cert_shards.py write` records in the runner beside the shard table. The shard table is rewritten from 50-01's measured seconds. Nothing is deleted, moved or merged.

**Scope: `make test-all`, not the PRD metric.** This section changes only certification, which `make test` -- PRD §8's five-minute target -- does not run. Its saving shows in the gate (`make test-all`'s cert half) and in 50-04's cert walls, not in the `make test` figure (REVIEW-5 R5-9); the PRD target is 50-03's and 50-01-04's ruling's.

**Why not consolidation.** A-3 ruled it out: the plan keeps one truth script per WP (REVIEW-5 R5-2, R5-3). The fixed cost is cut instead by loading less often (whole runs), loading more cheaply (`run`) and balancing what remains.

**Test order and commit rule.** 50-02-01 writes the load guard and runs it red (no commit); 50-02-02 loads dash with `run` everywhere and commits group 1 `(WP-50 50-02)`; 50-02-03 first writes the split-rule, block-seconds and template guards and runs them red (saved failure text), then applies the split rule, the measured block seconds and the shard rewrite, runs the changed scripts once, and commits group 2 `(WP-50 50-02)`; 50-02-04 reports what outside this section's files must follow (no commit).

### Section decisions

- **D-50-02.a — A-3.** No truth script is moved, renamed, merged or deleted; no block, case or case id changes or moves. The readers that name the per-WP scripts therefore stay as they are: test/program_coverage_map.py's `test_wpNN_truth.cscript:<case>` rows and `_shows_case`, test_cscript_hygiene.py `TestTheWp30TruthScript`, `TestTheWp31TruthScript` and `TestTheWpTruthScripts`, test_corpus_guard.py (33-09), test_tracking_documents.py's `_displayed_cases`, scripts/cert_shards.py's `WP30` helpers, and the merge tooling `../dash-wt/_tools/picks.sh`/`blockorder.py`.
- **D-50-02.b — The split rule.** Let `total` be the sum of every registered script's seconds in the shard table and `SPLIT_MIN = 0.5 * total / 3` (half of one session's balanced load under `scripts/run_cert_suite.sh`'s three sessions). A truth script that can run whole (D-50-02.c; the template-made scripts) is `*` for every N when its seconds are at least `SPLIT_MIN`, and otherwise is placed whole by the longest-first rule like any other script (one shard number per N). A script that splits itself but cannot run whole (test_wp30_truth.cscript and test_wp31_truth.cscript, which keep their own `w30_secs`/`w31_secs` parts and are not made from the template) stays `*`, as today. A whole script is at most half a session, so the longest-first rule still balances the sessions. The commit body records `SPLIT_MIN`, each truth script's seconds and placement, 50-01's measured per-script fixed cost `f` (script seconds minus its blocks' seconds) and the projected saving, `f * 2` for each script placed whole under three sessions.
- **D-50-02.c — How a whole script knows.** The template's parts section (between `// ---- parts: begin` and `// ---- parts: end`) gains a Mata function `_w@@WP@@_whole(string scalar runner, string scalar script, real scalar n)`: it reads `runner` (`run_all_cscripts.do`; the script runs from test/) with `cat()`, takes the lines between the shard table's `// ---- shards: begin` and `// ---- shards: end` markers, finds the row whose first word is `script`, and returns 1 when that row's column for `n` (the fourth word for n = 2, the fifth for 3, the sixth for 4) is a digit, else 0 (no file, no row, or `*`: 0, so the script splits as today). After `DASH_CERT_SHARD = k/N` and `WP@@WP@@_ONLY` are read, `N > 1` and a return of 1 set `k = 1`, `N = 1`: the runner calls the script only in its own shard, so the session runs every block. Run alone (DASH_CERT_SHARD unset), a script behaves as today.
- **D-50-02.d — Measured block seconds.** `scripts/cert_shards.py write <log>` also writes a second generated block in test/run_all_cscripts.do, between `// ---- block seconds: begin (scripts/cert_shards.py writes this block) ----` and `// ---- block seconds: end ----`, placed directly after the shard table's end marker: one comment line per template-made truth script, `// secs test_wpNN_truth.cscript S01 12 S02 4 ...`, each block's seconds from the log's `S<MM> start <date> <time>` and `S<MM> end <date> <time>` lines that sit between the previous `[ TIME]` line and the script's own (end minus start, a midnight wrap adding 86,400 s, summed over the logs given and over a block id's repeats, rounded up, at least 1). The template's `local w@@WP@@_secs S00 1` line becomes a Mata call, `_w@@WP@@_secs(runner, script)`, that reads its own `// secs` line (missing: `S00 1`, today's value), and a block it does not list still counts 1 s. test_wp30_truth and test_wp31_truth keep their own tables.
- **D-50-02.e — Template heads move together.** The template's head (its text up to the end of its S00 block, which holds the loads and the parts section) changes; in the same commit every `test_wpNN_truth.cscript` made from it gets the new head (a one-off script in <scratch>, not committed, replaces each file's text up to `* ==== end S00 ====\n` with the template's, `@@WP@@` replaced by the WP number), so `TestTheWpTruthScripts::test_every_script_keeps_the_templates_head_and_tail` stays green and no block changes. The anchors of `test_the_scaffold_is_in_order` keep their order.
- **D-50-02.f — Loads with `run`.** `qui do "../dash_parse.mata"` and `qui do "../dash.ado"` become `qui run "../dash_parse.mata"` and `qui run "../dash.ado"` in the template (so in every template-made head), in test_wp30/31 and in every other cscript that loads them, unless a script reads its own log for load output (`grep -n cert_file_has` near a load line); such a script keeps `do` with the comment `// do: this script reads its own load echo` on the load line. `run` still shows an error, so a failed load is not hidden.
- **D-50-02.g — A new truth script after WP-50.** W0.2's row form `test_wpNN_truth.cscript 1.0 0 * * *` no longer passes `check` (a 1-second template-made script runs whole). New subcommand `python3 scripts/cert_shards.py add <script>` inserts a registered script's row at 1.0 s with the rule's placement and keeps `check` green; the template's header comment says to use it. The index's W0.2 text is not edited here; 50-02-04 reports it.

## Risk: [yellow] -- the shard table, the template head and the runner change shape

**Why.** Every template-made truth script's head, the runner's table and the shard checker change at once; the blocks do not.

**Risk factors.** 1. A head that differs from the template by one byte fails the head/tail test. 2. A whole script that relied on running in parallel parts (none should: each part already starts from `clear all`). 3. The `check` rule changes for `*` rows. 4. A `*` script with a part that holds no block loads dash for nothing. 5. A load error hidden by `run`.

**Mitigation.** 1. D-50-02.e's one-off regeneration, then `python3 -m pytest test/test_cscript_hygiene.py -q -n0`. 2. 50-02-03 runs one whole script and one splitting script through `scripts/stata_slot.sh` under `DASH_CERT_SHARD`. 3. Unit tests for the rule (TDD stubs) and `cert_shards.py check`. 4. `parts_check` (TR-50-02.1). 5. `run` prints errors; the batch-end gate runs every script.

## Dependencies

- **Depends on:** 50-01 (the per-script and per-block seconds, the fixed cost, and the levers 50-01-03 lists in wp50-profile.txt; none of them is put to approval, and this section takes the certification ones it names).
- **Blocks:** 50-04.
- **Parallel batch 50.2** with 50-03 (pytest: conftest.py and slow test files). Disjoint files: 50-02 owns test/run_all_cscripts.do, scripts/cert_shards.py, test/templates/wp_truth_template.cscript, the heads of the template-made truth scripts, the load lines of every cscript, and the pins it moves in test/test_cert_shards.py and test/test_cscript_hygiene.py; 50-03 edits none of them. Neither section adds a fixture (50-03's frozen case counts are a module constant in its guard), so test/test_fixtures_are_committed.py is not edited in batch 50.2 (REVIEW-5 R5-37).

## Evidence

- test/test_wp31_truth.cscript's parts section :92-182 (`w31_secs` :105-111, `DASH_CERT_SHARD` :112, `WP31_ONLY` :124, `_w31_part()` :145-179), loads :41-45 (`qui do "../dash_parse.mata"`, `qui do "../dash.ado"`). The template is made from it by 33-01's N-6 (`<scratch>/make_template.py`), which replaces the seconds table by `local w@@WP@@_secs S00 1`; read `test/templates/wp_truth_template.cscript` at the section's base.
- test/run_all_cscripts.do: shard table :75-158 between `// ---- shards: begin (scripts/cert_shards.py writes this block) ----` and `// ---- shards: end ----`, row form `<script> <seconds> <port 0|1> <N=2> <N=3> <N=4>`; one numbered block per script; `[ TIME] <script> timer=..s wall=..s` per script.
- scripts/cert_shards.py (356 lines): `splits_itself` :108, `assign` :114 (`every` scripts share their seconds over the n shards), `wp30_parts` :147, `wp30_seconds` :160, `read_table` :174, `render_table` :191, `seconds_from_log` :218, `check` :236 (today: "* marks exactly the scripts that split themselves", "a row is * for some N and not for every N", `wp30_check` :283), `main` `write` :331.
- Load lines: 56 cscripts load `../dash_parse.mata` with `do`, 3 with `run` (`grep -ln 'do "../dash_parse.mata"' test/*.cscript`).
- Pins: test/test_cert_shards.py (the `*` rule's tests; re-read), test/test_cscript_hygiene.py `TestTheWpTruthScripts` (33-01's N-5: (2) scaffold order anchors `"// ---- parts: begin"`, `"local wNN_sh : environment DASH_CERT_SHARD"`, `"// ---- parts: end"`; (5) `t.count("@@WP@@") >= 100`; (6) head/tail equality with the template; (8) `test_the_seconds_table_may_change`, which replaces `"local w47_secs S00 1\n"` in the template made for WP 47 and asserts `u != t` and `len(_SECS.findall(t)) == 1` -- red once the template's seconds statement becomes D-50-02.d's Mata call, so TR-50-02.6 flips it).
- [C] §2.4.6 and §7.3; .ultraplan/handoff/TEST-PRUNING-ANALYSIS.md C1 ("Keep it to ≤4 shards") and C3.

## User stories

- US-50-02.1 As the maintainer, I want the certification run to clear and load dash fewer times, with every truth check kept in its own WP script, so that the gate is shorter.
- US-50-02.2 As a coding agent, I want each WP's truth script, its `WP<NN>_ONLY` switch and its blocks to stay where they are, so that adding or running a truth block is as before.

## Business requirements

- BR-50-02.1 Every truth case and block of the base runs and passes after the change, in the same script as before; none is removed or moved.
- BR-50-02.2 The cert run's wall falls by at least the fixed cost the whole-run rule removes, as 50-04 measures.
- BR-50-02.3 One WP's truth script, and one block of it, can still be run alone exactly as before.

## Technical requirements

- TR-50-02.1 scripts/cert_shards.py: new `SPLIT_SHARE = 0.5` and `SESSIONS = 3`; `split_min(seconds)` = `SPLIT_SHARE * sum(seconds.values()) / SESSIONS`; `runs_whole(text)` = the text calls `_w\d\d_whole(` (D-50-02.c); the starred set is `{s : splits_itself(s) and (not runs_whole(s) or seconds[s] >= split_min(seconds))}`, used by `write` (`render_table(..., every=starred)`) and demanded by `check` (its message: `* marks <...>, the scripts the split rule stars <...>`); `check` keeps "a row is * for some N and not for every N"; `parts_check(text, secs, name)` generalises `wp30_check` to every starred template-made script: each part of every N holds at least one block (blocks counted at their `// secs` seconds or 1 s); `block_seconds_from_log(log_text)` -> `{script: {block: seconds}}` (D-50-02.d); `render_block_seconds(...)` and `write` writing the block-seconds block after the shard table; `add <script>` (D-50-02.g). Every new function gets a unit test in test/test_cert_shards.py; the module docstring's `*` paragraph and usage lines are rewritten to the rule.
- TR-50-02.2 test/templates/wp_truth_template.cscript, parts section: `capture mata: mata drop _w@@WP@@_whole()` and `_w@@WP@@_secs()` beside the existing drop of `_w@@WP@@_part()`; the two Mata functions of D-50-02.c/d; `local w@@WP@@_secs S00 1` replaced by `mata: st_local("w@@WP@@_secs", _w@@WP@@_secs("run_all_cscripts.do", "test_wp@@WP@@_truth.cscript"))`; after the `WP@@WP@@_ONLY` test, `if \`w@@WP@@_N' > 1 {` / `mata: st_local("w@@WP@@_whole", strofreal(_w@@WP@@_whole("run_all_cscripts.do", "test_wp@@WP@@_truth.cscript", \`w@@WP@@_N')))` / `if \`w@@WP@@_whole' {` / `local w@@WP@@_k 1` / `local w@@WP@@_N 1` / `}` / `}`; the header comment's "its row ... is `* * *`" sentence becomes "its row in run_all_cscripts.do's shard table is `*` when the script is long enough to split (scripts/cert_shards.py's rule), else a shard number, and then the session that runs it runs every block"; the header gains "A new WP's row: `python3 scripts/cert_shards.py add test_wpNN_truth.cscript`". The display line after the allocator also names `whole` when the script runs whole.
- TR-50-02.3 Every template-made truth script (`ls test/test_wp*_truth.cscript`, all but 29, 30 and 31): head replaced per D-50-02.e; blocks, marker and tail untouched.
- TR-50-02.4 Loads per D-50-02.f over `grep -ln 'do "../dash_parse.mata"\|do "../dash.ado"' test/*.cscript` and the template.
- TR-50-02.5 Shards: concatenate 50-01's three session logs (`cat <scratch>/s1/run_all_cscripts.log <scratch>/s2/run_all_cscripts.log <scratch>/s3/run_all_cscripts.log > <scratch>/cert-50-01.log`), then `python3 scripts/cert_shards.py write <scratch>/cert-50-01.log "WP-50 50-01 profile <date>"` (the table and the block seconds), then `python3 scripts/cert_shards.py check` exits 0.
- TR-50-02.6 Pins: the test_cert_shards.py tests that assert today's `*` rule are flipped to the new rule with `# Flipped (WP-50 50-02): ... was wrong because a short template-made truth script now runs whole (A-3, D-50-02.b)`; counts move with `# old -> new: WP-50 50-02 <why>` (R10). test/test_cscript_hygiene.py `TestTheWpTruthScripts::test_the_seconds_table_may_change` (33-01's method 8) is flipped in place, under the comment `# Flipped (WP-50 50-02): the seconds moved from the script head to the runner (D-50-02.d)`, to assert: (a) `t = _read(_WP_TEMPLATE).replace("@@WP@@", "47")` holds `_w47_secs(` and no `local w47_secs` statement (`_SECS.findall(t) == []`); (b) no script in `_WP_TRUTHS` holds a `// secs ` line or a `_SECS` statement (`"// secs " not in text` and `_SECS.findall(text) == []`), and test/run_all_cscripts.do holds the block-seconds markers of D-50-02.d, so the seconds live only in the runner and rewriting a `// secs` line there changes no script's `_head_and_tail`; (c) a change elsewhere in the head is still caught: `u2 = t.replace("SKIP: Python not available.", "SKIP: x.")` gives `_head_and_tail(u2) != _head_and_tail(t)`. `_SECS` and `_head_and_tail` stay as they are (the substitution finds nothing to remove).

## Boundaries

- A-3: no truth script moved, renamed, merged or deleted; no block, case or case id changed or moved; no consolidated script, no block files.
- No pytest change except the guards and pins this section names (50-03 owns the rest); no product code; no fixture.
- test_wp29_truth.cscript (fixed-port shard) and the area cscripts change only their load lines; test_wp30/31 change only their load lines and keep `*`.
- Do not edit `../dash-wt/_tools/` (outside the repository) or the index: report (50-02-04).
- No `make cert` or `make test-all` inside the section; the script runs of 50-02-02/03 are one cscript each through `scripts/stata_slot.sh`.

## Stata truth

None new: the cases are the truth scripts' own; 50-02-03 runs the changed scripts once each.

## TDD test stubs

In test/test_cert_shards.py:
- `TestTheSplitRule::test_split_min` -- `split_min({"a": 600, "b": 300, "c": 300})` == 200 (red: no function).
- `TestTheSplitRule::test_a_short_whole_capable_script_runs_whole` -- with synthetic texts, a template-made script below `split_min` gets a shard number for every N, one at or above it `*`, and test_wp30's text stays `*` below it (red).
- `TestTheSplitRule::test_every_starred_part_has_a_block` -- `parts_check` reports a starred script with fewer blocks than parts (red).
- `TestTheBlockSeconds::test_from_log` -- a synthetic log with `S01 start 20 Oct 2026 10:00:01` / `S01 end 20 Oct 2026 10:00:05` lines before `[ TIME] test_wp47_truth.cscript timer=9.0s wall=9.0s` gives `{"test_wp47_truth.cscript": {"S01": 4}}` (red).
- `TestTheBlockSeconds::test_render_and_read_back` -- the rendered block holds `// secs test_wp47_truth.cscript S01 4` between its markers (red).
- `TestAdd::test_add_places_a_new_script` -- `add` on a runner text without the script's row gives a row at 1.0 s with a shard number and `check` passes (red).
In test/test_cscript_hygiene.py:
- `TestTheWpTruthScripts::test_the_template_reads_its_row` -- the template's parts section defines and calls `_w@@WP@@_whole(` and, inside the `if \`w@@WP@@_whole' {` branch, sets `local w@@WP@@_k 1` and `local w@@WP@@_N 1` (red). The seconds half is the flipped method 8's, not repeated here.
- Flipped in place: `TestTheWpTruthScripts::test_the_seconds_table_may_change` per TR-50-02.6 (red once flipped, until the template and the heads change).
- `TestEveryCscriptLoadsWithRun::test_no_do_load[script]` -- parametrised over `_CSCRIPTS` plus the template: no line loads `../dash_parse.mata` or `../dash.ado` with `do` unless it carries `// do: this script reads its own load echo` (red for the 56 `do` scripts).
cscript: none new; the changed scripts' own scaffold and blocks are run in 50-02-03.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| the split rule, block seconds, add | pytest test_cert_shards.py | synthetic in-test texts | n/a |
| template, heads, load lines | pytest test_cscript_hygiene.py | -- | n/a |
| a whole script and a splitting script under the runner's shard | stata_slot.sh runs (50-02-03) | -- | n/a |
| the table | `python3 scripts/cert_shards.py check` | -- | n/a |
| speed | 50-04's batch-end measurement | 50-01's profile | n/a |

- AC-50-02.1 Each group's guards were red before its change (50-02-01-failure.txt, 50-02-03-failure.txt) and are green after; every moved pin carries its reason.
- AC-50-02.2 `python3 scripts/cert_shards.py check` exits 0; the whole script's run prints `ALL CHECKS PASSED` with every block id displayed, under a `DASH_CERT_SHARD` that is not its own part.
- AC-50-02.3 No truth script, block or case id differs from the base except the template-made heads and the load lines (`git diff <base> --stat -- test/test_wp*_truth.cscript` shows head-only hunks).

## Tasks

**Commit boundary.** Group 1 (50-02-01 + 50-02-02, the load guard and the `run` loads): `Load dash with run in the certification scripts (WP-50 50-02)`. Group 2 (50-02-03, its guards written red first): `Run short WP truth scripts in one session and balance parts on measured seconds (WP-50 50-02)`. 50-02-04 makes no commit. Branch `wp50-s02`.

<task type="auto" id="50-02-01">
  <name>Write the load guard</name>
  <files>test/test_cscript_hygiene.py</files>
  <action><![CDATA[Add `TestEveryCscriptLoadsWithRun::test_no_do_load[script]` (TDD stubs) to test/test_cscript_hygiene.py. Run `python3 -m pytest test/test_cscript_hygiene.py -k LoadsWithRun -q -n0 > <scratch>/50-02-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/50-02-01-failure.txt` prints at least 50 (one per cscript that loads dash with `do`).]]></verify>
  <done>The load guard fails against the base for every script that loads dash with do, with the failure text saved.</done>
</task>

<task type="auto" id="50-02-02">
  <name>Load dash with run everywhere</name>
  <files>test/templates/wp_truth_template.cscript</files>
  <action><![CDATA[Apply TR-50-02.4 (D-50-02.f) to the template and to every cscript its grep lists (`grep -ln 'do "../dash_parse.mata"\|do "../dash.ado"' test/*.cscript`, test/test_wp30_truth.cscript and test/test_wp31_truth.cscript among them; save the list to <scratch>/50-02-02-loads.txt for the commit body); regenerate the head of every template-made test/test_wp*_truth.cscript from the new template (D-50-02.e). Run the scripts whose load line changed and whose shard-table seconds are under 60 s once each through two-line drivers and `scripts/stata_slot.sh` (BRIEF "Running one cscript"); the long ones are covered by the batch-end gate. Run `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_shards.py test/test_cert_verdict.py -q -n0`. Commit group 1 with the 50-02-01 failure lines as `Regression:` lines (Notes: before each commit).]]></action>
  <verify><![CDATA[The short scripts' logs end with their success lines; pytest prints 0 failed; `git log -1 --format=%s` ends `(WP-50 50-02)`.]]></verify>
  <done>Every certification script loads dash without echo, the template-made heads still equal the template's, and group 1 is committed.</done>
</task>

<task type="auto" id="50-02-03">
  <name>Split only long truth scripts, measured</name>
  <files>scripts/cert_shards.py, test/templates/wp_truth_template.cscript, test/run_all_cscripts.do</files>
  <action><![CDATA[First add the test/test_cert_shards.py stubs and, to test/test_cscript_hygiene.py, `TestTheWpTruthScripts::test_the_template_reads_its_row` (TDD stubs) and flip `TestTheWpTruthScripts::test_the_seconds_table_may_change` in place (TR-50-02.6); run `python3 -m pytest test/test_cert_shards.py test/test_cscript_hygiene.py -k "SplitRule or BlockSeconds or TestAdd or reads_its_row or seconds_table_may_change" -q -n0 > <scratch>/50-02-03-failure.txt; true` (they must fail). Then apply TR-50-02.1, TR-50-02.2, TR-50-02.3 (the head of every template-made test/test_wp*_truth.cscript) and TR-50-02.6 (D-50-02.b-e, g; its flips and count moves in test/test_cert_shards.py), and TR-50-02.5 (the table and the block seconds from 50-01's logs, written into test/run_all_cscripts.do). Pick from the rewritten table one template-made truth script that now runs whole (shard k for N = 3) and run it once with `DASH_CERT_SHARD=j/3` for a j that is not k, through a two-line driver and `STATATMP=<scratch>/tmpw/ sh scripts/stata_slot.sh <scratch>/w <scratch>/run_whole.do`: every block runs (the display line says `whole`). If any template-made script is still starred, run it once per part (`DASH_CERT_SHARD=1/3`, `2/3`, `3/3`, each with its own STATATMP and log folder, the trailing slash kept). Run `python3 scripts/cert_shards.py check`, `python3 scripts/cert_shards.py show > <scratch>/50-02-03-show.txt` and `python3 -m pytest test/test_cert_shards.py test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_program_coverage_map.py test/test_tracking_documents.py -q -n0` (test_cscript_hygiene.py's flipped `TestTheWpTruthScripts::test_the_seconds_table_may_change` among them). Commit group 2 with a body giving `SPLIT_MIN`, each truth script's seconds and placement, the measured fixed cost, the projected saving, the moved pins (`old -> new`), the line `Flipped: test/test_cscript_hygiene.py::TestTheWpTruthScripts::test_the_seconds_table_may_change -- one seconds statement in the template head was expected; it was wrong because the seconds moved from the script head to the runner (D-50-02.d)`, the runs' seconds and the 50-02-03 failure lines as `Regression:` lines; grep the message for claude|anthropic (Notes: before each commit).]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/50-02-03-failure.txt` prints at least 8; the whole script's log ends `ALL CHECKS PASSED` with every block id displayed; each starred part ends `ALL CHECKS PASSED` or `part k/3 has no block to run`; `cert_shards.py check` exits 0; pytest 0 failed; `git diff <base> --stat -- test/test_wp*_truth.cscript` shows only head hunks; `git log -1 --format=%s` ends `(WP-50 50-02)`.]]></verify>
  <done>Short truth scripts run whole in one session, long ones split on measured block seconds, every case stays in its own WP script, and group 2 is committed.</done>
</task>

<task type="auto" id="50-02-04">
  <name>Report the follow-ups outside the section</name>
  <files>none</files>
  <action><![CDATA[Write to <scratch>/50-02-04-report.txt, and append under `50-02 follow-ups` in .ultraplan/handoff/wp50-profile.txt (uncommitted; 50-04 commits it): (1) index W0.2's shard-row step for any WP after WP-50 becomes `python3 scripts/cert_shards.py add test_wpNN_truth.cscript` (D-50-02.g; the index is not edited here); (2) the merge tooling `../dash-wt/_tools/picks.sh` and `blockorder.py` need no change, because no truth script moved (A-3); (3) this section saves certification time only: `make test` (PRD §8) is unchanged by it (R5-9). Put the three lines in the hand-back to the orchestrator. Nothing is asked of the maintainer.]]></action>
  <verify><![CDATA[<scratch>/50-02-04-report.txt holds the three lines and wp50-profile.txt has the `50-02 follow-ups` heading.]]></verify>
  <done>The W0.2 change for later WPs and the unchanged tooling are reported to the orchestrator.</done>
</task>

## Section completion criteria

- The guards green; every moved pin carries its reason; `cert_shards.py check` passes; the whole and split runs pass.
- No truth case, block or script removed, moved or renamed (A-3); `run` loads everywhere a log is not read.

## Notes

- **A-3 (binding):** "50-02 keeps one truth script per WP (Q38). No consolidation; 50-02 cuts per-session load cost and rebalances shards instead." REVIEW-5 R5-2 and R5-34 described readers a consolidation would have broken; with no file moved, none of them changes.
- **Trap:** the head/tail test compares the template-made heads with the template byte for byte: regenerate every head in the same commit as the template change, never edit one by hand.
- **Trap:** `_w@@WP@@_whole()` must return 0 when it cannot read the runner (a script copied elsewhere, a section's own run from another folder): the script then splits as today and still passes.
- **Trap:** STATATMP must end with a slash, and its folder must differ from the log's (memory: concurrent cert runs).
- **Before each commit (CLAUDE.md rule 4; REVIEW-5 R5-39):** `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp50-s02 pull --ff-only . main` (BRIEF "Pull form": inside a worktree, with `$WT` the absolute worktree path; CLAUDE.md rule 4; expect `Already up to date.` at the batch base); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch. WP-50 closes no GAPS4 item, so BRIEF's corpus-ledger, known-differences and guard steps (1)-(3) have no lead id and are not taken. Then run the tests named in the task, `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back), grep the message for `claude|anthropic`, commit, and grep again.
- **Merge rules touched:** R1 (W0.2's row step changes for later WPs -- reported, D-50-02.g), R10, R14.
- **Commit-body lines:** group 1: the scripts left on `do` and why; group 2: `SPLIT_MIN`, each truth script's seconds and placement, the fixed cost and projected saving, each moved pin as `# old -> new`, the `Flipped:` line of method 8, the runs' wall seconds.
