# WP-28 plan review — feasibility, task quality, risk, user experience, cost/complexity

Reviewed: `PLAN.md`, `sections/BRIEF.md`, `sections/index.md`, all nineteen `sections/section-*.md` (159 XML tasks), against `xml-task-format.md`. Mechanical checks were run with a Python pass over every `<task>` block (schema fields, id sequence, XML well-formedness, file counts, name length) and with spot-checks against the repository at `91d97be` (`test/test_cscript_hygiene.py:292,308`, `dash_render.py` `np.histogram(` count = 1, no `.mlib` in the tree, `CHANGELOG.md` headings, the epoch arithmetic in 04-04).

Severity: **critical** = the plan cannot be executed as written or produces a wrong result; **major** = an executor will stall, merge-conflict or ship a defect unless the text changes; **minor** = schema/consistency defects that cost time but not correctness.

Counts: 6 critical, 12 major, 32 minor, 1 compliant (51 findings).

---

## A. Task schema

**1. [major] 117 of 159 tasks are not well-formed XML.** `xml.etree.ElementTree.fromstring` fails on every task whose `<action>`/`<verify>` holds a raw `&` (`&&` ×70, `2>&1` ×43, bare `&` ×2: 04-08 line 785, 09-02) or a raw `<` placeholder (`<scratch>`, `<dir>`, `<file>`, `<id>`, `<repo>`, `<ddmonyyyy>`, `<locals>`, `<!--` …). Only 42 tasks parse. Every section is affected (first offenders: `section-01:01-01:450`, `section-02:02-01:370`, … `section-19:19-08:511`).
*Fix (mechanical, one pass):* wrap every `<action>…</action>` and `<verify>…</verify>` body in CDATA. For each section file:
```
perl -0pi -e 's#<action>\s*(.*?)\s*</action>#<action><![CDATA[\n$1\n]]></action>#sg; s#<verify>(.*?)</verify>#<verify><![CDATA[$1]]></verify>#sg' sections/section-*.md
```
then re-run the parse check (`python3 - <<EOF … ET.fromstring(block) …`) and require 159/159. `<name>`, `<files>`, `<done>` hold no `&`/`<` today and need no change.

**2. [minor] 49 task names exceed the 3-8-word rule** (schema: "3-8 words, starts with a verb"). All start with a verb; none is under 3 words. Full list with proposed ≤8-word names:

| id | words | proposed name |
|---|---|---|
| 01-02 | 9 | Teach the guards GAPS2 and commit it |
| 02-07 | 10 | Pin the module to the old reader |
| 03-05 | 10 | Pin the E2 and X1 measurements |
| 04-01 | 12 | Write the failing format-writer tests |
| 04-04 | 9 | Implement the Python date writer |
| 04-05 | 11 | Write and thread the JavaScript twin |
| 04-06 | 14 | Export storage types into both renderers |
| 04-07 | 14 | Widen the loaders and flip what moves |
| 04-08 | 11 | Refuse %x and %H in kpi fmt() |
| 06-05 | 9 | Compare d3colors against Stata's SVG |
| 07-04 | 9 | Flip the pinned jitter tests |
| 07-06 | 10 | Flip the remaining pinned name tests |
| 07-07 | 9 | Reserve the prefix and close G1 |
| 07-09 | 10 | Replace the ASCII name regex |
| 08-09 | 10 | Give the renderer the same accounting |
| 09-03 | 9 | Build the launcher that reads exit status |
| 09-08 | 11 | Raise the floor in check, message, package |
| 09-11 | 9 | Document the floor in help and CHANGELOG |
| 10-05 | 9 | Draw served range layers from the group source |
| 10-06 | 13 | Give the served bs grid the saved layout |
| 10-07 | 9 | Move the saved bs filter bar down |
| 11-01 | 10 | Write the failing card tests |
| 11-02 | 13 | Write the card through the writer at first paint |
| 11-03 | 11 | Write the card through the JS twin |
| 11-05 | 10 | Run the suite and flip the card pins |
| 11-06 | 10 | Certify the card against Stata's display |
| 12-02 | 9 | Format dropdown and slider labels |
| 12-03 | 13 | Move period kinds onto numeric sliders |
| 12-04 | 10 | Format tooltips through CustomJSHover |
| 12-05 | 9 | Write axis ticks through the formatter |
| 12-06 | 9 | Format marker, facet and colorvar labels |
| 12-07 | 10 | Write float32 digits in the CSV |
| 12-10 | 10 | Flip the helper pins and run the suite |
| 12-11 | 9 | Close E3 and G6 in the documents |
| 13-04 | 9 | Name the rest and honour prefix, suffix, axis |
| 13-05 | 9 | Add the Python axis(2) title rewrite |
| 13-06 | 9 | Route axis(2) titles in Mata |
| 13-08 | 10 | Flip the pinned textbox tests |
| 13-10 | 9 | Close B3, B6 and B7 |
| 14-09 | 9 | Show value labels in tooltips |
| 15-05 | 9 | Add the order parser and key list |
| 15-06 | 11 | Resolve, select, order and insert legend rows |
| 16-06 | 11 | Draw the z options on the colour key |
| 17-04 | 11 | Make the saved mask the served one's twin |
| 17-06 | 11 | Mask each served target by its filters |
| 17-07 | 11 | Mask each saved target by its filters |
| 17-08 | 9 | Close E2 and X1 in the documents |
| 18-07 | 10 | Share the primary-renderers limit |
| 18-09 | 9 | Flip the date-range tests |

**3. [minor] `<files>` carries a non-path annotation `(new)` in 18 tasks** (04-01, 04-02, 05-01, 05-05, 06-01, 06-03, 11-01, 11-06, 12-01, 13-01, 13-02, 15-01, 16-01, 16-02, 16-07, 17-01, 17-02, 17-05). A comma-splitting reader gets `test/test_kpi_format.py (new)` as a path. *Fix:* delete ` (new)` from every `<files>`; the action already says "Create".

**4. [minor] `<done>` is present tense in about 83 tasks** (schema: "past tense as a statement of fact"), e.g. 03-02 "`test/js_runner.py` exposes …", 04-03 "The Python numeric writer reproduces …", 09-08 "`dash_setup` refuses …". The convention is uniform and readable. *Fix (cheapest):* amend BRIEF line 34 to "done: one sentence stating what is now true (present or past tense)" so the schema and the sections agree; do not rewrite 83 sentences.

**5. [major] Seven tasks edit more files than `<files>` lists** (the ≤3 rule is breached in the action, not the header, so a reader cannot see it):
- `section-02:02-04:394` — "fix `svg_axis_extent` in `scripts/svg_truth.py` (allowed here as the one exception…)". *Fix:* if the smoke run exposes a reader defect, stop and reopen 02-02 (one task, one commit); delete the exception sentence.
- `section-07:07-06:341` — "flip `test/test_marker_label_parity.py` … the fourth file of this task". *Fix:* move that one-line flip into 07-05 (which lists three files but edits three; swap `test/test_date_range.py`'s one-line flip into 07-04 — 07-04's three files gain nothing because `test_option_validation.py` is one line too; simplest: 07-04 files = `test_jitter.py, test_html_verification.py, test_marker_label_parity.py`; 07-05 files = `test_saved_filter_layers.py, test_date_range.py, test_server.py`; 07-06 files = `test_served_filter_move.py, test_server_facets.py, test_twoway_option_parity.py, test_option_validation.py` → still four; therefore add task 07-06b "Flip the two one-line pins" with `test/test_option_validation.py, test/test_marker_label_parity.py`).
- `section-12:12-04:619` — "Update `test_server_layer_defects.py::TestTheHoverBuilder` only if …" (conditional 4th file). *Fix:* move it to 12-08 unconditionally (12-08 lists three date/served files; replace `test_saved_filter_layers.py` there with `test_server_layer_defects.py` and put the single `TestADateDropdown` flip into 12-02's verify-driven flip list of 12-10).
- `section-12:12-05:637` — edits `test/test_help_claims_7.py:255-262` beyond its three files. *Fix:* move that flip to 12-10 (which has room: replace `test_help_claims_4.py`'s one-line `{custom}` flip with it and put the hc4 line into 12-08).
- `section-14:14-05:693` — "bump the count `test_cscript_hygiene.py:294` reads if …" (4th file, conditional; the pin exists at :292). *Fix:* see finding 22.
- `section-17:17-04:342` — "Flip S03's `test/test_js_runner.py::TestMaskParity…` … if that file counts against this task's three-file limit, flip it in 17-07". *Fix:* delete the conditional; the flip belongs to 17-07's flip commit.
- `section-17:17-07:374` — "this task then touches four files — commit `test_js_runner.py`'s flips with `test_help_claims_3.py`'s". *Fix:* add task 17-07a "Flip the S03 measurement pins" (`test/test_js_runner.py`) immediately before 17-07, holding both `test_js_runner.py` flips (X1 parity, E2 sequence, the `1.0` value).

**6. [minor] 19-05 lists six files.** Justified: `test/test_pkg_metadata.py:49-60` and `test_help_claims_1.py:190-196` hold the six version lines equal, so they cannot land in separate green commits. Accept; add to the task's `<action>` the exact `grep -n '\*! Version:' dash_parse.mata` so the sixth anchor is not "the `*! Version:` line".

**7. [minor] Vague or phantom instructions in `<action>`.**
- `section-04:04-03:672` "and so on" (function-map entries) → list the seven entries.
- `section-12:12-08:692` "etc." (`_dash_stata_date_text(value, "%td")` etc.) → name the five kinds.
- `section-16:16-03:309` and `16-04:321` "Rebuild the Mata library the way the repo does (see the `lmata`/`mlib` step the Makefile or dash_setup runs; do not hand-edit the .mlib)". There is no `.mlib` in the repository (`ls *.mlib` → none); cscripts load `do "../dash_parse.mata"`. *Fix:* delete the sentence in both tasks.
- `section-16:16-04:321` "sreturn local ztitle etc." → write the three lines.

**8. [minor] `section-18:18-08:693` `<action>` is one sentence** (schema 2-6). Split at the semicolons.

**9. [minor] Stale anchors.** `section-02:02-03` and `14-05` cite `test_cscript_hygiene.py:294`; the pin is `:292` (`len(_CSCRIPTS) == 65`) and `:308` (`len(names) == 47`), as S07/S08 cite. `section-19` Evidence, TR-19.6 and the test plan say "65 scripts"/"65 cscripts"; after WP-28 the runner holds 79 (65 + S02, S05, S06, S07, S08×2, S09 + S11, S13, S14, S15, S16, S17 + S18). *Fix:* "every registered script (79 after WP-28)".

**10. [minor] Ids and types:** every section numbers `NN-01..` sequentially with no gap or duplicate; types are `auto` except 14-12 and 18-12 (`checkpoint`, `files: none`). Verified — no finding.

---

## B. Order and independence

**11. [critical] The plan contradicts CLAUDE.md rule 4 on committing red tests, and contradicts itself on commit granularity.** BRIEF line 34 says "each task = one commit"; BRIEF line 44 and S01 TR-01.9 say "one commit per gap … a red tree is never committed: the regression tests … land in the fix commit that turns them green". S01 01-01 obeys ("Do not commit"). These tasks instead commit failing tests as their own commit: `02-01:368` ("Commit on `s3-bugs`"), `03-01:251`, `04-01:628`, `09-01`/`09-02` (S09 preamble :676 "Each task is one commit"), `10-01`/`10-02` (S10 Notes "One commit per task"), `16-01:292`, `17-01:314`; S06 tasks 06-01..06-03 each "commit". A red commit violates rule 4 and the pre-commit full-suite rule 11 (a full run before each of S09's twelve commits is 24 minutes and a hook refusal after the second).
*Fix:* (a) BRIEF line 34: replace "each task = one commit" with "each gap = one commit (its tests, fix, flips, BUGS.md entry); a shared-component section (01, 02, 03) is one commit per component; the full suite runs once before each commit". (b) In 02-01, 03-01, 04-01, 09-01, 09-02, 10-01, 10-02, 16-01, 17-01 replace the commit sentence with: "Do not commit: save the failure summary to `<scratch>/NN-01-failure.txt`; it opens the fix commit's body (S01 TR-01.9)." (c) S09 preamble :676-681 → "F1 is one commit (09-01..09-06), K2 one (09-07..09-12)"; S10 Notes → "one commit (E14) at 10-08"; S06 → "one commit (D1) at 06-04"; S02 → "one commit at 02-07"; S03 → "one commit at 03-05"; S04 → "one commit at 04-09".

**12. [major] S09 admits two red intermediate states** (`section-09:41-42` "red between 09-03 and 09-04"; `09-10:891` "this test is red until then"). Finding 11 removes the first (one K2/F1 commit each). For the second, even inside one commit the task order is backwards (a flip before the sentence it asserts). *Fix:* move the `test_help_claims_8.py` flip out of 09-10 into 09-11 and move CHANGELOG out of 09-11 into 09-12:
```xml
<task type="auto" id="09-10">
  <name>Flip the help-claims cscript for dash_setup</name>
  <files>test/test_help_claims_8.cscript</files>
  <action>`test_help_claims_8.cscript:786`: `items(bokeh 2.4 (needs 3.8))`. Run the script from a scratch directory (rule 10 invocation, `STATATMP=<dir>/tmp/`).</action>
  <verify>The batch log ends in its PASS line with `HC8-19` present.</verify>
  <done>The certification script states the new floor.</done>
</task>
<task type="auto" id="09-11">
  <name>Document the floor and flip its pytest</name>
  <files>dash_setup.sthlp, dash.sthlp, test/test_help_claims_8.py</files>
  <action>Apply TR-09.8's help parts (dash_setup.sthlp 40-42, 70, 80-82, 97-98, 110-113, the new {pstd}; dash.sthlp 3131-3134), keeping verbatim the sentences `test_help_claims_8.py` asserts, and in the same edit flip `test_help_claims_8.py::TestDashSetupHelpMatchesTheAdo::test_a_package_below_its_minimum_is_unmet_not_a_warning` (1640-1660) to "one below 3.8 is reported as an unmet requirement -- it is not upgraded for you -- and the run ends with r(198)."</action>
  <verify>`python3 -m pytest test/test_version_floor.py test/test_help_claims_8.py -q 2>&1 | tail -3` passes; the `test_setup_python_gate.cscript` log shows "states the same minimum (3.13)".</verify>
  <done>The help states the tested floor and the test that reads it passes in the same change.</done>
</task>
```
and 09-12 gains `CHANGELOG.md` (the `### Requirements` rewrite and the K2 line) beside `BUGS.md`.

**13. [critical] S05 breaks after S03 merges (same batch).** `section-03:03-03:271` deletes `_NODE` and `_run_filter_js_block` from `test/test_statistical_helpers.py` (812-856) and re-imports only `run_filter_js_block as _run_filter_js_block, requires_node`. `section-05:05-01:497` writes `from test_statistical_helpers import _hist, _run_filter_js_block, _NODE` and decorates with `@pytest.mark.skipif(_NODE is None, …)`. On the merged batch-1 tree `test_histogram_edge_rule.py` fails at collection with `ImportError: cannot import name '_NODE'`. Neither section's Risk factors or Boundaries mention the other.
*Fix:* in 05-01 replace the import with `from test_statistical_helpers import _hist, _run_filter_js_block` and add `_NODE = os.environ.get("DASH_NODE") or shutil.which("node")` at module level (matching S03's rule); add to S03 Risk factors: "S05 imports `_run_filter_js_block` by that name — the alias must be kept".

**14. [critical] Batch 2 is not parallel as declared; the dependency graph in `index.md`/`PLAN.md` is incomplete.**
- S12 must merge after S17: both edit the dropdown branch of `_dash_filter_widget` (17570-17622), `_DASH_FILTER_MASK_JS` (S12 slider/range branches + `spec.unit`; S17 dropdown branch + `use` parameter + the comment block above `dash_filter_mask`), `_dash_frame_filter_mask`, and the eight-line `filter_specs_json` block (23707-23714: S12 adds `unit`, S17 adds `numeric`). S12 says so (`12-03`, Notes) but `index.md:57` lists S12 as depending on 03, 04 only.
- S12 must merge after S16: S12 TR-12.9 edits `_apply_colorvar` at 6418 and 6467; 6467 lies inside the 6459-6498 body S16 16-05 replaces.
- S15 must merge after S13: S15 appends `zp` lines to `scripts/extract_text_truth.do`, which 13-02 creates, and regenerates `text_truth.json` (15-04 even says "if section 13's script is not yet in this worktree, create the skeleton"). `index.md:60` lists S15 as depending on 02 only.
- S14 edits `_apply_colorvar` 6399-6405 (14-07) while S16 rewrites the same function and S17 edits 6527 and S12 6418/6467: four batch-2 sections in one function.
- S11 and S17 both edit `_kpi_callback_config`/`kpi_config` (S11 11-03 changes the emitted fields; S17 17-07 adds `"use"`) and `_FILTER_JS` (S11 rewrites `dash_apply_kpis`'s body and deletes 14378-14482; S17 rewrites the call site 14702 and every mask consumer).
*Fix:* `index.md` manifest and `PLAN.md` dependency graph: S12 depends on 03, 04, 16, 17; S15 depends on 02, 13; S17 depends on 03, 11 (S17's `_FILTER_JS` rewrite must see S11's deletion). Batch 2 becomes two waves: 2a = {11, 13, 14, 16}, 2b = {12, 15, 17}; batch 3 = {18}. Hand S14's `_apply_colorvar` hunk to S16: 14-07 leaves 6399-6405 alone and 16-05 makes `_vlookup` call `_dash_value_labels_for` (S16 lists S14 as a dependency for that one line, or 16-05 adds the call only if the helper exists — no: make S16 depend on S14 in wave 2a ordering, S14 first). Rewrite 12-03/12-06's "if section 17's/16's diff has landed" as unconditional ("rebase on S17/S16, which precede this section").

**15. [major] Batch-1 sections insert into the same lists without assigned anchors.** S04, S07, S09, S10 all add names to the served constants list (24326-24428) and functions list (24466-24687); S04, S05, S06, S08, S09, S10 all add keys to `test/function_test_map.py`; S02, S05, S06, S07, S08, S09 each append "block 66/67" to `run_all_cscripts.do`; S07 (`_dash_filter_refusal` 3452-3461) and S08 (its exclude reading ~3430-3447, refactored into `_dash_filter_excludes`) edit the same Mata function five lines apart. `patch -p1` will reject overlapping-context hunks. Only S09 names an anchor ("at the END").
*Fix:* add to `PLAN.md` "Execution order" a table: S04 inserts copy-list names after `"_dash_stata_date_text"`; S07 after `"_dash_parse_filter_raw"`; S09 at the end; S10 after `"_dash_refresh_linked"` and `"_dash_bs_grid"`; `function_test_map.py` keys in alphabetical place (each section states the neighbour key); `run_all_cscripts.do`: every section appends "the next block" and the merger renumbers and sets the two hygiene counts once (S02 Notes already say this — make it the rule for all). For S07/S08: merge S07 before S08 and state in 08-07 that `_dash_filter_excludes` is factored out of the post-S07 text.

**16. [major] The three-concurrent-Stata-sessions cap has no mechanism.** Ten batch-1 worktree agents each run Stata (02-07 runs `make cert` — one session of 65+ scripts for many minutes; 08-04 runs 89 twoway commands; 09-12 runs nine cscripts including HC4 at ~2 min; S05, S06, S07 run their own), and `python_exec` is dropped from `stata19.rc` when too many console sessions run (memory note). Nothing coordinates them.
*Fix:* (a) delete `make cert` from 02-07 (S19 runs it; 02-07 runs `test_cert_svg.cscript` and the six rewired scripts one at a time); (b) in `PLAN.md` "Execution order" add: "Every Stata launch first takes one of three slots with `until mkdir /tmp/dash-stata-slot-{1,2,3} 2>/dev/null; do sleep 5; done` and removes its slot directory after the log is read"; (c) `make cert` and `make gate` are run only by the merging session.

**17. [major] Full-suite launches per section exceed the hook's allowance unless commits are per gap** (S09: twelve; S10: eight; S06: four). Finding 11 resolves it; additionally each section's closing task should say "the section's one full run" and every other task "changed files only" (12-02..12-09 and 09-03..09-11 already do).

**18. [minor] 06-05 is a conditional task placed after the closing task 06-04** ("if `test/cert_svg.do` does not exist … do nothing"). A task whose outcome may be "nothing" and that follows the BUGS.md closure is out of order and unverifiable in a worktree that cannot see S02. *Fix:* delete 06-05; add case CV-08 "d3colors scatter: twoway's SVG p1 fill equals dash's `#1f77b4`" to `section-16:16-07`, whose cscript already exports through `cert_svg.do` and reads marker fills.

**19. [minor] First-task rule holds everywhere** (NN-01 writes tests only; 05-02/13-02/14-02/15-04/16-02/17-02/18-02 write fixtures; no NN-01 fixes). Last-task rule holds except S06 (finding 18) and S14/S18 whose last task is a checkpoint after the close (finding 49). No task depends on a later task within its section except 09-10→09-11 (finding 12) and 18-03's flips that stay red until 18-05 (acceptable inside S18's single commit; say so in 18-03's `<done>`).

---

## C. Realistic scope

**20. [major] Twenty tasks plainly exceed one commit / ~15 minutes.** Splits proposed (full XML for the four largest):

- **04-03** (the `%w.0g` rule derived from examples, iterated against ~1,300 rows, plus the parser and the float rule):
```xml
<task type="auto" id="04-03">
  <name>Implement the format parser and refusals</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>In the "One implementation, two callers" region after `_dash_stata_date_text` add `_dash_fmt_parse`, `_dash_fmt_kind` and `_dash_fmt_refusal` as TR-04.1 specifies, keeping WP-20's bounds (width ≤ 2045, dec < width, four-digit groups, ASCII, ≤ 60 characters). Add a stub `_dash_fmt(value, fmt, storage=None, strip=False)` that returns `str(value)` padded to the width so later tasks replace it. Map the three functions in `test/function_test_map.py` to `TestParser::test_kinds` and `TestParser::test_refusal_messages`.</action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k "TestParser or refused_or_unknown"` passes; `python3 -m pytest test/test_adversarial_matrix.py -q -k NumericFormatBounds` still passes.</verify>
  <done>The parser classifies every fixture `confirm` format and refuses what Stata refuses within WP-20's bounds.</done>
</task>
<task type="auto" id="04-03b">
  <name>Implement the f and e writers</name>
  <files>dash_render.py</files>
  <action>Add `_dash_fmt_number(parsed, value)` for kinds `f` and `e` per TR-04.2 (sign column, `fc` comma drop, two-decimal exponent fallback, `%0w.df`, `%-w`, the European comma in one pass, Stata's rounding), and route `_dash_fmt` to it. Iterate against the fixture's `%9.0f %9.0fc %9.2f %9.2fc %-9.2f %12.2fc %9.3e %9.4f %9,2f %9,2fc %09.2f %10.3e %9.0e` rows only.</action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k "numeric_display" 2>&1 | grep -c "%.*g'" ` shows only `%g` rows failing; `python3 -c "import dash_render as d;print(repr(d._dash_fmt(1000.03,'%9,2fc')))"` prints `' 1.000,03'`.</verify>
  <done>Every f and e fixture row is reproduced, padding included.</done>
</task>
<task type="auto" id="04-03c">
  <name>Implement the g writer from the fixture</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>Print the fixture's `%12.0g` and `%20.0g` rows for 0.1 as float and as double and choose the `storage="float"` rule they demand, recording both strings in `_dash_fmt`'s docstring. Implement the `%w.dg`/`%w.dgc` branch per the derived rule in §Evidence; where a row contradicts the rule, follow the row and note the case in the docstring. Add `_dash_float32_text` and `_dash_fmt_text`. Map `_dash_fmt`, `_dash_fmt_text`, `_dash_float32_text`, `_dash_fmt_number` in `test/function_test_map.py`.</action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k "TestPythonWriter and numeric or text_strips"` passes; `python3 -c "import json,dash_render as d;r=[x for x in json.load(open('test/fixtures/format_truth.json'))['numeric_formats']['%10.0g']['values'] if x['value']==6165.2567 and x['storage']=='double'][0];assert d._dash_fmt(6165.2567,'%10.0g')==r['display'],r"` prints nothing.</verify>
  <done>Every numeric fixture row is reproduced by the Python writer, the g rule included.</done>
</task>
```
- **14-03** (expander + tokenizer + head split + rebuilt label parser + rewritten `_dash_parse_axis_spec` + `_dash_apply_axis_spec` + `_dash_place_count_ticks`):
```xml
<task type="auto" id="14-03">
  <name>Add the numlist expander and tokenizer</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>Beside `_MAX_AXIS_TICKS` add `_dash_expand_numlist`, `_dash_axis_tokens` and `_dash_axis_head_split` exactly as TR-14.1/14.2 specify (count before value, `too_many`, `bad`, quote-aware split). Read `a1_spaces_incr`, `a1_single_quote`, `a1_str_first` and `label_refusals` first and cite the probe id in a comment where a rule follows one. Add the three to the served function list and map them to `TestTheExpander::test_forms` and `TestTheTokenizer::test_the_head_split_is_quote_aware`.</action>
  <verify>`python3 -m pytest test/test_axis_label_grammar.py -q -k "Expander or Tokenizer"` passes; `python3 -c "import dash_render as d;print(d._dash_expand_numlist(['1','2','3/5','8(2)12']))"` prints `([1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 12.0], False, [])`.</verify>
  <done>Stata's numlist forms and the quote-aware tokenizer exist as bounded, mapped, copied functions.</done>
</task>
<task type="auto" id="14-03b">
  <name>Rebuild the axis label parsers on them</name>
  <files>dash_render.py, test/test_graph_options.py</files>
  <action>Rebuild `_dash_parse_axis_label_opt` on the two helpers (same `(ticks, labels)` contract; a `str` labels the last value; further strings join with `"\n"`; a string before any value goes to `unsupported`). In `_dash_parse_axis_spec` replace the `_m_tail`/`m_sub` regexes and the sub-option-stripping regex with `_dash_axis_head_split`, read a leading rule token, replace the a(b)c block with the expander keeping the `_too_many` warning text, append `bad` and stray words to `unsupported`, and honour `valuelabel` by prefix. Flip `test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label` to ticks `[1.0, 2.0]`, labels `{}`.</action>
  <verify>`python3 -m pytest test/test_axis_label_grammar.py -q -k "Labelled or Numlist or Bound or Hostile"` passes except `test_a_rule_then_a_labelled_list` (14-03c); `python3 -m pytest test/test_axis_options.py test/test_graph_options.py test/test_adversarial_matrix.py -k "Grammar or AxisLabel" -q` passes.</verify>
  <done>Every numlist form, quoted string, line and compound quote is read as twoway reads it, bounded as before.</done>
</task>
<task type="auto" id="14-03c">
  <name>Carry count-mode lists into the tickers</name>
  <files>dash_render.py</files>
  <action>In `_dash_apply_axis_spec` add `value_labels=None`, stash `ax._dash_extra_ticks` and the overrides in mode `"count"`, and add the value-label override merge of TR-14.5 (explicit text wins, or the reverse if `g16_vl_mixed` says so — cite it). In `_dash_place_count_ticks` union `_dash_extra_ticks` into the FixedTicker and into `t_lo`/`t_hi`.</action>
  <verify>`python3 -m pytest test/test_axis_label_grammar.py test/test_served_dates.py test/test_help_claims_8.py test/test_natscale.py -q 2>&1 | tail -3` is green including `test_a_rule_then_a_labelled_list`.</verify>
  <done>A rule before a labelled list draws both, and count ticks keep the listed values.</done>
</task>
```
- **17-07** (rewires `_build_filter_widgets`, three `FilterBuilder` placeholders, a memoised mask in a 740-line script, the graph/derived/aggregate/KPI consumers, and flips in two test files):
```xml
<task type="auto" id="17-07">
  <name>Compute per-target use lists in the saved wiring</name>
  <files>dash_render.py, test/test_filter_exclude.py</files>
  <action>In `_build_filter_widgets` implement TR-17.9: compute `use` per target once through `_dash_filter_applies`, build `_graph_srcs`/`_graph_use`/`_excluded_srcs`/`_agg_*`/`_der_*`/`_kpi_config` (with `"use"`)/`_kpi_divs` once and set the same args on every callback, adding `graph_use_json`, `agg_use_json`, `derived_use_json`; give `FilterBuilder.build_dropdown/build_slider/build_range` the three placeholders as `"[]"`. Do not edit `_FILTER_JS` yet. In `test_filter_exclude.py` give `_script_args` and `TestThePrimarySourceFallback` the three keys (`[[0]]` for a listed source) and reword the section-1 docstrings.</action>
  <verify>`python3 -m pytest test/test_filter_exclusion_sets.py -k TheCallbackArgs test/test_filter_exclude.py -q 2>&1 | tail -3` passes (the JS still uses `active`; sources are listed with their `use`).</verify>
  <done>Every callback carries the same per-target use lists and the protected-source invariant still holds.</done>
</task>
<task type="auto" id="17-07b">
  <name>Mask graph and derived sources per target in the script</name>
  <files>dash_render.py</files>
  <action>In `_FILTER_JS` add memoised `dash_mask_for(use)` and `dash_ids_for(use)` over `dash_filter_mask(orig, filter_specs, all_widgets, use)`; keep `active`/`_active_ids`/`new_data` for the fallback `source`; make the graph-source loop (14235-14263, shape kept) read `dash_ids_for(_graph_use[_si])` and the derived loop (14310-14340) `dash_ids_for(_derived_use[_di])`. Read the whole script end to end first.</action>
  <verify>`python3 -m pytest test/test_filter_exclusion_sets.py -k "saved and (ExclusionHolds or OrderOfMoves or LinkGroup or ByPanel)" test/test_linking_filters.py -q 2>&1 | tail -3` passes; the identity-loop text pin in `test_linking_filters.py:331-360` is untouched.</verify>
  <done>Graph and derived sources on the saved page take their own target's mask on every move.</done>
</task>
<task type="auto" id="17-07c">
  <name>Mask KPIs and aggregates per target in the script</name>
  <files>dash_render.py, test/test_help_claims_3.py</files>
  <action>Group `kpi_config` entries by `JSON.stringify(k.use)`, build one `new_data_<g>` per group from `dash_mask_for(use)` and call `dash_apply_kpis` per group in place of the single call at 14702; in the aggregate block (14725-14915) read each config's `use` wherever it read `active`, `_active_ids` or `new_data`. Rewrite `test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` as `TestAnExclusionHoldsAgainstEveryMove` (docstring citing dash.sthlp:1128-1138; the four-state sequence in both modes) and flip `"1"` → `1.0` at 452, 494, 404, 408.</action>
  <verify>`python3 -m pytest test/test_filter_exclusion_sets.py test/test_help_claims_3.py test/test_saved_filter_layers.py test/test_export.py test/test_dropdown_values.py test/test_mode_parity.py -q 2>&1 | tail -3` passes; the served-name guards pass.</verify>
  <done>Cards and aggregate layers on the saved page follow their own filters, and both modes agree on every sequence.</done>
</task>
```
- **18-05** (seven new functions and three rewrites):
```xml
<task type="auto" id="18-05">
  <name>Add the hull and padding helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>Between `_dash_place_count_ticks` and `_dash_finish_count_ticks` add `_dash_padded_range`, `_dash_range_hull`, `_dash_range_reversed` (TR-18.7) and `_dash_axis_hull` (TR-18.6, bar half-widths read through the view rows `_dash_secondary_values` uses, `norescale` flags honoured). Add the four to the copy list and the function map (`TestTheHelpers`).</action>
  <verify>`python3 -m pytest test/test_axis_extents.py -k TheHelpers test/test_function_test_map.py -q 2>&1 | tail -3` is green.</verify>
  <done>The hull, padding, inversion and reversal helpers exist, are copied and are pinned.</done>
</task>
<task type="auto" id="18-05b">
  <name>Run the hull after the layers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>Give `_dash_count_axes` its `every_axis=True` form with `letter`/`name` per entry (TR-18.5); add `_dash_hull_ranges` (TR-18.8); rewrite `_dash_finish_count_ticks` per TR-18.9 (count ticks over data ∪ scale values first, then the hull) and widen `_dash_place_count_ticks`'s Range1d common branch to `d_lo`/`d_hi`. Map `_dash_hull_ranges`; rewrite the two docstrings.</action>
  <verify>`python3 -m pytest test/test_axis_extents.py -k "Widen or RangeOnly or LogAndDate or Reverse or CountTicks or Computed or Bars or Twoway" -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_natscale.py test/test_html_output.py -k "Ticks or Xrange" -q` is green.</verify>
  <done>Every axis with an explicit position or range() value spans its padded hull in both modes; an axis without one is untouched.</done>
</task>
<task type="auto" id="18-05c">
  <name>Share one hull across by() panels</name>
  <files>dash_render.py</files>
  <action>In `_dash_common_count_ticks` group every panel's `_dash_hull_entries` by key after the tick loop, union the hulls with each panel's data, and call `_dash_hull_ranges(f, entries_of(f), common={key: (lo, hi)})` per panel (TR-18.10).</action>
  <verify>`python3 -m pytest test/test_axis_extents.py -k ByPanels test/test_natscale_axes.py -k Panels -q 2>&1 | tail -3` is green.</verify>
  <done>Every panel of a by() graph spans one extent under a range() or label value.</done>
</task>
```
- One-line splits for the rest (same style): **04-01** → Python-side tests / JS-twin tests (the node harness); **04-05** → JS numeric twin / JS date twin / thread into the three scripts + copy list; **04-07** → loaders + `_NUM_FORMATS` / wrapper + guard + `%g` case / full run + flips; **07-01** → one task per file; **08-01** → one task per file; **09-01** → launcher pytest / floor pytest / cscript; **09-03** → `_dash_port_value` at every site + `_FakeProc` / `_dash_launch_app` + `__main__`; **10-01** → `test_served_bs_layout.py` / `test_mode_parity.py` harness; **12-01** → widget+tooltip tests / axis+label+CSV tests; **12-06** → marker labels + `_mlabformat_column` / facet titles + retire date helpers / colorvar labels + retire numeric helpers; **13-01** → pytest / cscript + JSE-46; **14-01** → one task per file; **16-01** → one task per file; **16-07** → CV-01..CV-04 / CV-05..CV-07 + HC7-02 flip; **17-01** → one task per file; **18-02** → register probes + `.Graph` reads / python-block findings + run.

**21. [minor] Section sizes.** S01 has 3 tasks (the minimum) — justified: documents and one test module. S09, S14, S18 sit at 12 (two of them including a checkpoint) — acceptable. After the splits above S04 (≈15), S14 (≈15), S17 (≈12) and S18 (≈15) exceed 12; accept rather than renumber sections (BRIEF forbids renumbering), but state in each section's header "tasks: n, grouped into k commits".

---

## D. Verification quality

**22. [critical] `section-04:04-04:710` verify expects a wrong number.** `d._dash_stata_value_of(978393600000,'td')` should print `14977.0`: 978,393,600,000 ms is 2001-01-02 00:00 UTC and `(978393600000 + 315619200000) / 86400000 = 14977.0`; `15341.0` is 2002-01-01 (1,009,843,200,000 ms). An executor coding to the verify would build a converter that is a year off, or "fix" a correct one. *Fix:* `15341.0` → `14977.0` (or the ms argument → `1009843200000`).

**23. [critical] cscript registration and the hygiene count pins are missed in nine sections; two new cscripts are never registered at all.**
- **S13** creates `test/test_textbox_grammar.cscript` (13-01) and **S15** creates `test/test_legend_order.cscript` (15-01); no task in either section touches `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py`; `TestEveryCscriptIsWiredIntoTheRunner` (`:418`) and `test_the_glob_finds_every_script` (`:292`) go red and `make cert` never runs the scripts. *Fix:* add to each section, right after NN-01:
```xml
<task type="auto" id="13-01b">
  <name>Register the grammar cscript in the runner</name>
  <files>test/run_all_cscripts.do, test/test_cscript_hygiene.py</files>
  <action>Append a block for `test_textbox_grammar.cscript` to `test/run_all_cscripts.do` in the shape of the last block (the merger renumbers). In `test/test_cscript_hygiene.py` add 1 to the `len(_CSCRIPTS)` pin at :292 and, because the script exits 222 without `c(python_exec)`, 1 to the `len(names)` pin at :308; say in the commit message that the merge reconciles both numbers.</action>
  <verify>`python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -2` passes in this worktree.</verify>
  <done>The new certification script is wired into the runner and counted.</done>
</task>
```
(15-01b identical for `test_legend_order.cscript`.)
- **05-05, 06-03, 09-02, 11-06, 16-07, 17-05, 18-10** register their script but never bump `:292` (and `:308` where the script gates on Python: all but 06-03), yet each `<verify>` asserts `python3 -m pytest test/test_cscript_hygiene.py -q` passes — it cannot. **02-03** bumps `:292` (65→66) but not `:308` (`test_cert_svg.cscript` exits 222 without Python). **14-05** makes the bump conditional ("if Section 02's #66 made it a count") — the pin exists at `91d97be`. *Fix:* each of these tasks adds `test/test_cscript_hygiene.py` to `<files>` with the sentence "add 1 at :292 and 1 at :308 (the script exits 222 without Python); the merger sets the final numbers". Where `<files>` would then exceed three (11-06, 16-07), move the registration into a separate NN-xxb task as above.
- **S19** counts must read "every registered script (79)" (finding 9).

**24. [minor] Weak or wrong verify commands.**
- `section-02:02-04:400` `grep -c '\x60' scripts/extract_svg_truth_smoke.do` — grep does not interpret `\x60`; use `python3 -c "t=open('scripts/extract_svg_truth_smoke.do').read(); b=t[t.index('python:'):]; assert '\x60' not in b"`.
- `section-07:07-03:317` "prints nothing" vs AC-07.4 "prints nothing but comments" — pick one (`grep -v '^\s*#'`).
- `section-16:16-07:365` and `17-05:359` "the log ends without `r(`" — `r(` also matches `r(N)`/`r(mean)` in PASS text; use `grep -c '^r([0-9]*);' <log>` prints 0.
- `section-06:06-05:528` is an either/or verify (finding 18 removes the task).
- `section-15:15-03:274` concedes the four parity cases "may pass" pre-fix — then they are guards, not regression tests; move them from "Regression stubs" to "Guards" in the stub list.
- `section-16:16-04:329` accepts two outputs for `g['zlabel']`; decide (the graph-option loop does not normalise `zlabel` unless S14's `axislist` kind lands, which is batch 2 too — with finding 14's ordering S14 precedes S16, so require `1 2 3 4 5`).
- `section-04:04-03:691` hard-codes `'  6165.257'` for `%10.0g` while the section says the fixture decides the `%g` rule; replace with the fixture-reading one-liner given in finding 20 (04-03c).

**25. [minor] Stata truth blocks.** All sections that run Stata give the `arch -arm64 /usr/local/bin/stata-mp -b do` line with `STATATMP=<dir>/tmp/` and the `git add -f` rule (S01, S03, S10, S19 correctly say "none"). Exception: **S12** (`section-12:430-440`) says "rule 10's console command with its own `STATATMP`" without the literal line; add the standard block or "no Stata run in this section".

**26. [minor] TDD stubs and both-modes coverage.** Every section with a page asserts both renderers (S05 `TestBothModes`, S06, S07, S08, S10-S18); S09 is served-only by nature; S16's fixture test is mapper-only with `TestBothModes` beside it — fine. Stubs name `file::Class::test` except S04's module-level tests and S11/S12's `Class::test` (file named once at the top) — acceptable.

**27. [minor] Refusal text left as `…`.** `section-18:TR-18.1:323` and `18-03` name a non-number "once through `_dash_warn_once(("scale", "range", option, tok), …)`" while `test_a_non_number_is_named_once_and_the_axis_left_alone` asserts identical text in both modes. *Fix:* quote it: `"dash: %s(range()) ignores %s, which is not a number" % (option, _dash_display(tok))`. (S08's r(109) and S14's TR-14.13 wording are measured from twoway by design — acceptable.)

---

## E. Risk ratings

**28. [major] S09 yellow → red.** Its own "Why" lists seven risk factors on a process boundary (a launcher with two pump threads inside Stata's embedded Python where a thread must never print, pipes that hang the child when undrained, `SO_REUSEADDR`/TIME_WAIT semantics reasoned not measured, a `runpy` box protocol), inverts three pinned tests plus the adversarial registry, flips five cscripts, and admits two red intermediate states. That is the plan's own definition of red (S17: "one code path … changes under tests that pin"). Red buys the section a single-commit-per-gap discipline and the merger's attention at the copy-list tail (finding 15).

**29. [major] S14 yellow → red.** One parser rewrite that every `xlabel/ylabel/xtick/ytick/xlabel2/ylabel2` and every date axis passes through in both modes; a dash.ado `axislist` normalisation that runs on ten options for every graph and every segment; a new derived column on every source a tooltip attaches to plus a served-redraw hook; two undocumented readings settled only by probes; S18 (red) depends on it. It touches more of the option surface than S18. Red is the honest colour; yellow understates the blast radius for the merger.

**30. [minor] S08 stays yellow, but its "Why" must state the unverified assumption**: that `syntax varlist(numeric)` prints twoway's r(109) wording byte-for-byte for all five families (tsline/tsrline have their own front end; the section says "may print other words"). Add the fallback now, or 08-04 can loop: "where a family's words cannot be matched through `syntax`, assert rc equality and record the two texts in the generator header as a residual in the G2 entry".

**31. [minor] S03 stays green** but must list the `_NODE` removal that breaks S05 (finding 13) under Risk factors.

**32. [minor] S13 stays yellow**; add to Risk factors that `_dash_route_axis2` runs on the raw option text of every `dash` command before `syntax`, so an exception there is an r(3xxx) on every call; mitigation is the stated "everything else returned as typed" plus a JSE-42..49 hostile-title probe in TBG (13-06 already mentions it — make it a case, TBG-06).

Unchanged and justified: S01 green, S02 yellow, S04 red, S05 yellow, S06 green, S07 yellow, S10 yellow, S11 yellow, S12 red, S15 yellow, S16 yellow, S17 red, S18 red, S19 green.

---

## F. User experience (PRD §5)

**33. [critical] The CHANGELOG convention is broken between S01/S19 and every gap section.** S01 TR-01.7 (`section-01:287-323`) creates `### Fixed in WP-28` holding four labelled sub-lists with 23 `<!-- WP-28 <ID> -->` markers and says "a section replaces its gap's marker with its line(s)"; S19 19-01 (`section-19:378`) fails if any marker survives and 19-02's verify (`:403`) reads the lines inside `### Fixed in WP-28`. But the closing tasks write elsewhere: 05-06 "under `### Results that change` (:10)", 06-04 "(:113)", 07-10 top-level "Changed behaviour" and "Fixed", 08-06/08-10 top-level, 10-08 top-level "Results that change", 14-06 "under `### Results that change`", 14-11 "under `### Fixed` (or `### New`)", 16-08 "(113)", "`### New`", "`### Fixed`", 17-08 "(60)", 18-11 top-level; 04-09, 11-07, 12-11, 13-10, 15-08 are ambiguous. Result: all 23 markers survive, 19-01 fails, 19-02's awk finds nothing. The tag form also varies: `(WP-28 C2)`, `(WP-28, X2)`, `(WP-28, GAPS2 F1)`, `(WP-28)`; S19 greps for `(WP-28)`.
*Fix:* one sentence in every closing task (04-09, 05-06, 06-04, 07-07, 07-10, 08-06, 08-10, 09-06, 09-11, 10-08, 11-07, 12-11, 13-10, 14-06, 14-11, 15-08, 16-08, 17-08, 18-11): "Write the line in place of its `<!-- WP-28 <ID> -->` marker under `### Fixed in WP-28` (S01 TR-01.7), ending `(WP-28, <ID>)`; add nothing to the top-level lists." In S19 19-02's verify and AC-19.1 grep for `"(WP-28, "`.

**34. [major] Placement disagreements with S19's inventory (AC-19.1).** E2: S17 puts it under "Results that change" (rows change: g1 3→5), S01/S19 under "Fixed" — S17 is right; move E2 to "Results that change" in TR-01.7, TR-19.2 and AC-19.1. E14: S10 puts both items under "Results that change"; S01/S19 expect the bar move there and the served items under "Fixed" (marker `E14 served`) — 10-08 must split them. G3: S08 "Changed behaviour", S19 "Fixed" — 08-10 must change (no picture changes for a command that built). G16: S14 "Fixed (or New)", S19 "Results that change" — 14-11 must change (`hover()` and `valuelabel` draw different text). G1: S07 writes under both "Changed behaviour" and "Fixed" — S19 counts each gap once; keep the "Changed behaviour" line only and fold the renames into it. K2/F1: 09-06/09-11 write under `### Fixed in WP-28` with no sub-label — put F1 under "Fixed:" and K2 under "Requirements:".

**35. [none] Silent when honoured.** No task prints a note for an option that is now drawn; every new output is a refusal (r(109), r(110), r(134), r(198)), a named unwritable value (`%21x` on a variable, `range(abc)`, an unknown z sub-option), or S09's status line "dash: the server answers at …", which the help documents and which is not an option note. Compliant.

**36. [minor] Every refusal task quotes message and code** (04-08 r(198); 07-07 r(110); 07-08 r(198); 08-08 r(134) both forms; 09-03/09-05 exit 2 and r(198); 16-03 r(198) both forms; 05 r(198) existing). Exceptions: finding 27 (S18's note) and the measured ones (S08 G2, S14 TR-14.13), which are acceptable because the plan forbids typing twoway's words.

**37. [minor] Help-text tasks cite dash.sthlp line ranges** everywhere (S04 1259-1261; S05 2040-2052; S06 2804-2814; S07 166-171, 1108-1109, 1194-1197; S08 181-193, 1519-1522, 1560-1572; S09 727-729, 1353-1357, 1367-1374, 3131-3134; S10 five ranges; S11 1242-1261; S12 862-866, 1110-1128, 1783-1784, 2361, 2441-2461; S13 455-458, 519-525, 2396-2417; S14 672-680, 2318-2331; S15 2290-2312; S16 2478-2507; S17 1109-1138; S18 2333-2335, 2431-2432). Only 16-08's graph-option table is located by `grep xsc:ale`; give the line.

---

## G. Over-engineering / simplification

**38. [major] Two SVG readers are kept on purpose and then the reason disappears.** S02 keeps `extract_axis_truth.do`'s private `parse_svg`/`axis_facts` and pins it to `svg_truth` by `exec`-ing a slice of the `.do` file's python block in a pytest (02-07, `TestEquivalenceWithExtractAxisTruth`) because "its fixture … cannot be re-checked without a full Stata re-run". S14 14-02 and S18 18-02 both re-run that script and regenerate the whole fixture. *Fix:* drop the equivalence test from 02-07 (keep the suite run); in 14-02 replace the private reader with `from svg_truth import …` for every group and add to its verify "the pre-existing probes' `axis_low/axis_high/tick_labels` are unchanged: `git diff` of `axis_truth.json` restricted to old ids shows only the two new record fields". One reader, no fragile exec.

**39. [minor] A fifth node runner.** After WP-28: `js_runner.run_js` (S03), `test_export._run_js`, `test_help_claims_4._run_js`, plus the private runner 04-01 writes "modelled on `test_export.py:41-53`". *Fix:* 04-01 imports `test_export._run_js` (exists at `91d97be`, batch-safe); 12-01 uses `js_runner.run_js` (S03 is its dependency) instead of `test_export._run_js`.

**40. [minor] `.Graph` is probed twice.** S02's smoke fixture records `matches_svg.drawn_extent_member` and AC-02.4 says "section 18 can read the verdict without running Stata"; S18 18-02 re-probes all four candidates on 25 cases and writes its own verdict. DISCOVERY Q14 says once. Keep S18's (the real sample); delete AC-02.4's second clause and the sentence "What section 18 must read from here" in S02 Notes, so nobody builds on the one-graph smoke verdict.

**41. [minor] `_dash_fmt_tick_code`** (`section-12` Notes) is to be exposed "so section 14 can compose it"; S14 never references it and its TR-14.4 leaves the explicit-label formatter untouched. Drop it (a function nobody calls that `function_test_map.py` must still name), or have 14-03c consume it.

**42. [minor] d3colors fixture size and provenance.** A verbatim 3,701-line third-party scheme is committed where the tests read lines 26 and 300-315. Copy lines 1-320 (line numbers preserved; the `*!` provenance header kept) and state the d3colors package's licence in the test docstring.

**43. [minor] S16's fixture repeats the nlsw88 columns per probe** (`values` for `grade wage ttl_exp age` × 2,246 on four probes plus `fill_groups`). Write the columns once under `_data[dataset]` and reference them.

**44. [minor] S09 launcher plumbing.** TR-09.2 step 4 sends stderr both to a `deque(maxlen=50)` and "the same queue tagged"; the message needs the deque only and the live print needs stdout only. One structure per pipe.

---

## H. Checkpoints

**45. [major] 14-12 should go; S10 needs one; 18-12 stays.** 14-12 re-runs `make test`/`make cert` (S19 does this on the merged tree, and per finding 16 only the merger runs `make cert`) and asks a human to eyeball value labels that `test_value_labels_drawn.py` and AL-17..19 already hold to twoway's SVG; B3, B5, D1 and X2, equally pictorial, have none. Remove 14-12. 18-12 is justified: extents change on every axis with an option and the `.Graph` verdict is a decision to present. S10 is the one section that deliberately changes a picture every saved `layout(bs)` page has shown (the bar below the header) and whose item 4 rests on a Chrome measurement — add after 10-08:
```xml
<task type="checkpoint" id="10-09">
  <name>Approve the bs page changes in Chrome</name>
  <files>none</files>
  <action>Render `examples`' six `layout(bs)` dashboards saved and served, open one of each in Chrome at 375, 768 and 1440 px, and show the maintainer: the filter bar below the title on the saved page, the served cards two per line at 768 with 130 px cells, and the `filterposition(left)` page unchanged. Present the E14 commit hash and the Chrome measurements from 10-06's commit message.</action>
  <verify>The maintainer approves the bar move and the served reflow, or names a page to revisit before S19.</verify>
  <done>The one deliberate picture change of WP-28 was seen and approved.</done>
</task>
```
Also make the residual approval explicit in S19: insert before 19-03 a checkpoint "Approve the deferred residuals" (`files: none`; present the G1, G3, X2, E14 and C4/E4 reasons of TR-19.3 for a yes) — a human approves residuals once, before they are written into GAPS2.md.

---

## I. Miscellaneous consistency

**46. [minor] `PLAN.md:208` file map lists `dash.ado` "05 (start() text)"; S05 Boundaries forbid touching dash.ado's `start()` check.** Delete "05 (start() text)".

**47. [minor] `section-02:AC-02.2` "66 of 66"** → "n of n" (batch 1 ends at 72).

**48. [minor] Block numbers collide** (02-03 "#66", 05-05 "block 66", 06-03 "block 67", 07-02 "block 67", 08-02/08-03 "the next block", 09-02 "after the last"). Say "the next block; the merger renumbers" everywhere.

**49. [minor] `section-11:11-02:449`** "binding `_storage_types` in `make_document` if section 04 left it as `meta['storage_types']` only" — 04-06 binds `_storage_types = meta.get('storage_types', {})`; delete the conditional.

**50. [minor] `section-12:12-03:612` and `12-06:665`** conditional merge sentences become unconditional under finding 14 ("S17 and S16 precede this section").

**51. [minor] `section-19:19-03`** rewrites 23 Tracked lines; its verify expects `git diff --stat` of "23 insertions and 23 deletions" — true only if every Tracked line is one physical line; add "(each Tracked line is one line; wrap nothing)".
