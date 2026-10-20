# Section 56: Help reconciliation

> Part of: WP-31 · GAPS3 rows: J1, J2 · Risk: yellow · Batch: 19 · Depends on: 02-55 · Blocks: -- · Tasks: 6, 2 commits · Case-id prefix: U56

## Overview

**What is wrong today.** GAPS3 J1: dash.sthlp:4972-4975 says every supplied option "is named in that command's note, so nothing is dropped in silence", contradicted at `6370ca4` by C1, C2 and C3 (silent drops); and the Unsupported section (:4967-5135) "omits every name that reaches the generic note (atobs, ciplot, fitplot, nofit, boundary, headlabel, mwidth, baroffset, nodropbase, clegend, plegend, pcycle, the six colorvar names, gap(), droplines(), mangle(), barbsize(), ndots(), dotextend(), the d-options, estcmd/estopts/predopts, mlabprefix/mlabsuffix, mlalign, mlabstyle, lalign, yvarlabel/xvarlabel) because test_help_conformance.py reads only the pending blocks" (`_pending`, `_ignored_options`, `_unsupported_section` at test_help_conformance.py:340-373; `TestTheUnsupportedSectionIsTrue` :938). GAPS3 J2 lists nine sentences: the Syntax line :83 writes `filter(varname, type(filter_type) [exclude() label()])` with `type()` outside the brackets though :1697 says "Without type() the widget" defaults; the %tw-%ty period-slider sentence sits in the dropdown paragraph (:1731-1734 region); `legend(ring(0))` "keep the legend inside the plot region" (:3545) where Bokeh's top_right is drawn until S31 lands; `msangle` documented as degrees only (:2816 "or a number of degrees from -360 to 360"; anglestyle names drawn by S34); :572 "Four twoway plot types are not drawn" omits sunflower and matamatrix() (S21 refuses them by name); `dot` listed among types drawn as twoway describes (:252) while S18 draws its rows; :2262-2263 "logs each refusal -- once a minute per limit, so a flood cannot flood the log": the rate constants exist (dash_render.py:48132-48135) but a once-a-minute gate on the refusal log line was not found (unverified); no iframe sentence; no overlay/`link()` qualifier example; no %tC/log-precedence paragraph.

**After this section** the Unsupported list is generated from three sources and pinned both ways: the `_dash_pending` blocks, `_dash_rep_und_tab` (dash_parse.mata:6250-6324) and the catch-all probe fixture of options that reach the generic note; the "nothing is dropped in silence" sentence is rewritten to what is true after S02-S04 (every option not drawn is named; options twoway refuses on a type are refused); and each J2 sentence is corrected to the tree batch 19 inherits, each with a test that reads the help and the code.

**Why one section and why last.** S56 owns every dash.sthlp paragraph no fix section owns (R3) and must see the final pending list, so it runs in batch 19 after every drawing section (S02-S55) has removed its options from the pending blocks and the Unsupported list (M15).

**Test order and commit rule.** Two cycles, two commits: `(WP-31 J1)` (56-01 to 56-03) and `(WP-31 J2)` (56-04 to 56-06). Each cycle: failing tests first, saved to `<scratch>/56-01-failure.txt` and `<scratch>/56-04-failure.txt`, never committed; then the help and test edits; then the closing task closes the entry, rewrites the Tracked line, replaces the marker and commits.

### Section decisions

- **D-56.a Three sources for the Unsupported list.** `_unsupported_section()` must equal `_ignored_options() | _undeclared_twoway_options() | _catchall_options()`, where `_undeclared_twoway_options()` reads the option names of `_dash_rep_und_tab`'s rows (dash_parse.mata:6250-6324; the names in the first column of each `"name", "advice"` pair) and `_catchall_options()` reads `test/fixtures/catchall_options_truth.json` (new, written by `scripts/extract_catchall_options_truth.do`: every twoway option name from `research/stata-ground-truth.md` §1.2-1.3 that dash accepts with the generic "ignoring unsupported option(s)" note at the batch-19 base). A name that batch 19's base draws (removed from the pending block by its section) must not be in the list (the existing other direction).
- **D-56.b The silence sentence** becomes: "every one that is supplied and not drawn is named in that command's note, and an option twoway refuses on a plot type is refused as twoway refuses it (r(198), option X() not allowed)". The example at :4977-4979 stays if `mlpattern()` and `t1title()` are still pending at the base; otherwise it names two options still in the list (read the list; D-56.a's test fails if the example names a drawn option).
- **D-56.c Refusal-log claim.** 56-04 measures: read the emitted app source for the throttle on the refusal log line (`grep -n "once a minute\|_last_logged\|log_every" dash_render.py` around :48270-48290). If a once-per-minute gate exists, the sentence stays and a test pins the gate's constant; if not, the sentence becomes "The server logs each refusal, naming the limit and, for a session limit, its flag" and the claim is dropped. No throttle is added (served logging is S55's; R12).
- **D-56.d `legend(ring(0))`, msangle, dot, Not-drawn count** are written to what the batch-19 base draws: read S31's, S34's, S18's and S21's landed help paragraphs first (R3: those sections own them) and edit only the sentences J2 names outside their paragraphs (:3545 is in the legend synopt table, :2816 in the marker-label section, :252 in the plot-type table, :572 in Not drawn). If a sentence was already corrected by its section, record "already corrected by S<NN>" in the closing Resolution and skip it.

## Risk: [yellow] -- the help is read by 60-odd help-claims tests; a sentence change can fail one that pins the old wording

**Why.** `test_help_claims_*.py` and the `.cscript` twins assert sentences; `test_help_conformance.py` pins the Unsupported list both ways.

**Risk factors.** 1. The pending list at the batch-19 base is unknown at plan time. 2. A help-claims test pins a J2 sentence verbatim. 3. `_dash_rep_und_tab` row shape may have changed by batch 19.

**Mitigation.** 1. D-56.a reads the list, never types it. 2. 56-02 and 56-05 run `python3 -m pytest $(grep -l "<old sentence fragment>" test/test_help_claims_*.py)` and flip the pins with `Flipped:` lines (R9). 3. 56-01's reader test asserts at least 20 rows parsed.

## Dependencies

- **Depends on:** 02-55 (every drawing section removes its options from the pending blocks and the Unsupported list; S18, S21, S31, S34 rewrite the paragraphs D-56.d names).
- **Blocks:** nothing. S61's G3 checks `help Unsupported list == pending blocks`.
- **Parallel batch 19** with S57 (examples/) and S58 (tracking documents); none edits dash.sthlp but S56.

## Evidence

Anchors at `6370ca4`; re-read at the batch-19 base.

- dash.sthlp:4970-4975:
  ```
  {pstd}
  The options below are {it:accepted and not honoured}.  None of them given
  once is an error (given twice, one {cmd:twoway} takes once is refused as
  {cmd:twoway} refuses it, as {it:Differences from twoway} says), so a
  command copy-pasted from a do-file always runs -- and every one that is
  supplied is named in that command's note, so nothing is dropped in silence:
  ```
  :4981-4984: "The note is built from the declarations in {cmd:dash.ado}, and this list is checked against them: {cmd:test/test_help_conformance.py} fails if the two disagree in either direction." Entries are `{phang2}{ul:Heading.}` blocks listing `{opt name(args)}` (:4986-5000).
- test_help_conformance.py:340-373: `_pending(prog)` reads `_dash_pending' (\w+)"` between `program define <prog>` and `local _dash_unknown`; `_unsupported_section()` collects `{opt...}` names inside `{phang2}`/`{phang}` entries between `{marker unsupported}` and `{marker dependencies}`. `TestTheUnsupportedSectionIsTrue` at :938.
- dash_parse.mata:6250-6324 `_dash_rep_und_tab`: the table of undeclared twoway option names with advice (GAPS3 §5 lists them).
- dash.sthlp:83 Syntax: `{cmd:filter(}{it:varname}{cmd:, type(}{it:filter_type}{cmd:)} [{cmd:exclude(}{it:namelist}{cmd:)} {cmd:label(}{it:string}{cmd:)}]{cmd:)}`; :1691-1700 the filter type paragraph ("Without {cmd:type()} the widget ...").
- dash.sthlp:3545-3546: `{synopt:{cmdab:leg:end(ring(0))}}keep the legend inside the plot region rather than beside it{p_end}`.
- dash.sthlp:2816: `...) or a number of degrees from -360 to 360.`; :965, :1019, :1091 other msangle mentions.
- dash.sthlp:572: `{ul:Not drawn.}  Four {cmd:twoway} plot types are not drawn by {cmd:dash}:`; :252 `{cmd:area}, {cmd:bar}, {cmd:spike}, {cmd:dropline}, {cmd:dot}{p_end}`.
- dash.sthlp:2260-2264 the refusal-log sentence; dash_render.py:48132-48135 `_RATE_LIMIT_RPM`, `_NEW_CLIENTS_RPM`, `_SESSIONS_TOTAL_RPM`, `_HEALTH_LIMIT_RPM`; :48278 the refusal text.
- `grep -c iframe dash.sthlp` → 0; %tC mentions at :471, :3915, :4127; no "precedence" paragraph for %tC and the log axis.
- Existing tests to flip (read at the base): any `test_help_claims_*.py` node that quotes a J2 sentence (found by `grep -ln "dropped in silence\|Four {cmd:twoway} plot types\|inside the plot region\|once a minute" test/test_help_claims_*.py test/*.cscript`), flipped in place with `Flipped:` lines.

## User stories

- **US-56.1** As a Stata user reading `help dash`, I want the Unsupported list to name every option dash accepts and does not draw, so I know what my pasted command loses.
- **US-56.2** As a Stata user, I want each help sentence to describe what dash does at this release, so I am not misled about `type()`, `ring(0)`, msangle, dot or the refusal log.

## Business requirements

- **BR-56.1** The Unsupported list equals the set of accepted-not-drawn options from the three sources, in both directions, pinned by a test.
- **BR-56.2** The silence sentence states the rule the code implements after S02-S04.
- **BR-56.3** Each J2 sentence is true of the batch-19 tree and pinned by a test that reads both the help and the code or fixture.
- **BR-56.4** Every help-claims test stays green or is flipped with a reason.

## Technical requirements

- **TR-56.1** `test/test_help_conformance.py`: add `_undeclared_twoway_options()` (parse `_dash_rep_und_tab`'s body between `string matrix _dash_rep_und_tab` and its closing `}` for `"([a-z0-9_]+)",` first-column names; lower-case) and `_catchall_options()` (read `test/fixtures/catchall_options_truth.json`'s `"options"` list); extend `TestTheUnsupportedSectionIsTrue`'s two-direction test to the union; add `TestTheParsersFoundSomething::test_the_undeclared_table_was_found` (at least 20 names) and `::test_the_catchall_fixture_was_found` (`_meta` keys `stata_version, born_date, dash_commit, extracted, source`).
- **TR-56.2** `scripts/extract_catchall_options_truth.do` (R7 shape, copy the head of `scripts/extract_default_base_truth.do` :21-48): for each name of `research/stata-ground-truth.md` §1.2-1.3's option tables that is neither in a pending block nor in `_dash_rep_und_tab`, run `capture noisily dash scatter mpg weight, <name>(<a safe value>)` on `sysuse auto` under `global dash_nobrowser 1` with the log captured, and record the name when the log holds `ignoring unsupported option(s)`; write `test/fixtures/catchall_options_truth.json` with `_meta` and `"options": [...]`. `git add -f`.
- **TR-56.3** dash.sthlp edits (S56's paragraphs, R3): :4970-4975 per D-56.b; the Unsupported list gains one `{phang2}{ul:<Heading>.}` entry per group of names the list lacks (grouped: fit options; distribution options; arrow options; dot options; colorvar options; marker-label options; axis-title options), each name as `{opt name(args)}` or `{opt name}`; :83 → `{cmd:filter(}{it:varname} [{cmd:, type(}{it:filter_type}{cmd:)} {cmd:exclude(}{it:namelist}{cmd:)} {cmd:label(}{it:string}{cmd:)}]{cmd:)}`; move the %tw-%ty period-slider sentence from the dropdown paragraph to the slider paragraph (:1700-1720 region; find it with `grep -n '%tw' dash.sthlp`); :3545 per D-56.d; :2816 add `, or one of Stata's anglestyle names (horizontal, vertical, rvertical, rhorizontal)` if S34 landed msangle names; :572 count and names per the base; :252 dot: add `({cmd:dot} draws twoway's dot rows)` if S18 landed; :2262-2263 per D-56.c; add after :2264 an `{pstd}` on the iframe (the saved page's CSP `frame-ancestors`, read from `_DASH_CSP_STANDALONE` dash_render.py:4620: state what it allows); add under Linking an example `dash build, link(g1 g2) ... if foreign==1` with the sentence that a `link()` graph's own qualifier is applied before the link; add under Temporary files or Server Mode a `{pstd}` "%tC and log axes: a `%tC` variable is drawn in the leap-second-free scale (G2, S43) ...", reading S43's landed text and linking to it rather than restating it.
- **TR-56.4** `test/test_help_claims_9.py` (new; or the next free number at the base: `ls test/test_help_claims_*.py`): one test per J2 sentence reading dash.sthlp and the code: `test_the_syntax_line_brackets_type`, `test_the_period_slider_sentence_is_in_the_slider_paragraph`, `test_ring0_says_what_is_drawn` (reads S31's legend code), `test_msangle_names_anglestyles`, `test_not_drawn_names_every_refused_type` (reads `_dash_undrawn_plottype` dash_parse.mata:1802), `test_dot_sentence_matches_map_dot`, `test_the_refusal_log_claim` (D-56.c), `test_an_iframe_sentence_exists_and_matches_the_csp`, `test_a_link_qualifier_example_exists`, `test_a_tc_precedence_paragraph_exists`.
- **TR-56.5** `test/test_help_claims_9.cscript` is NOT created (R1: one new cscript only); the Stata-side checks (the Not-drawn names are refused by name, the dot sentence) go to `test/test_help_claims_1.cscript` as cases U56-1 (each name in the Not-drawn sentence is refused r(198) with advice) and U56-2 (`dash twoway, ` form runs, A1) appended before its summary with `*! U56-1, U56-2` header lines.

## Boundaries

- Not edited: the paragraphs owned by S02-S55 (R3 table in index.md: each section's Notes name its paragraph); dash.ado, dash_parse.mata, dash_render.py; `test_help_conformance.py`'s `_pending`, `_fold_aliases` and the abbreviation tests; `test_unsupported_report_is_true.py`'s counts (R10: if the Unsupported list's declared count moves, the pin moves with `# old -> new: J1 <why>`).
- No throttle is added to the served refusal log (S55's area).

## Stata truth

- `scripts/extract_catchall_options_truth.do` → `test/fixtures/catchall_options_truth.json` (TR-56.2). Run: `DASH_REPO=<W> scripts/stata_slot.sh <scratch>/s56 <W>/scripts/extract_catchall_options_truth.do`. `_meta` as R7; `git add -f`; named by `test_the_catchall_fixture_was_found`.
- cscript cases U56-1, U56-2 in `test/test_help_claims_1.cscript` (TR-56.5). No block in `test_wp31_truth.cscript` (nothing is compared with twoway's drawing).

## TDD test stubs

Regression (56-01; red at the batch-19 base):
- Test: `test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue::test_every_accepted_undrawn_option_is_listed` -- fails naming at least `atobs`, `ciplot`, `headlabel`, `mwidth` (whatever is still undeclared at the base).
- Test: `test/test_help_conformance.py::TestTheParsersFoundSomething::test_the_undeclared_table_was_found` -- `NameError: _undeclared_twoway_options`.
- Test: `...::test_the_catchall_fixture_was_found` -- `FileNotFoundError`.
- Test: `test/test_help_claims_9.py::TestTheSilenceSentence::test_it_states_the_refusal_rule` -- `'dropped in silence' in text`.
Regression (56-04): the ten J2 tests of TR-56.4, each red for its sentence.
cscript: U56-1, U56-2 (test_help_claims_1.cscript).
Pinned tests to flip: the help-claims nodes `grep` finds (Evidence); parity corpus: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Unsupported list == three sources, both ways | pytest `TestTheUnsupportedSectionIsTrue` | catchall_options_truth.json | n/a |
| Silence sentence | pytest `test_help_claims_9.py::TestTheSilenceSentence` | -- | n/a |
| Nine J2 sentences | pytest `test_help_claims_9.py` (10) | -- | n/a |
| Not-drawn names refused; bare prefix draws | cscript U56-1, U56-2 | auto | Stata |
| No claim pin broken | pytest `test/test_help_claims_*.py test/test_help_conformance.py test/test_unsupported_report_is_true.py` | -- | n/a |

AC-56.1 `grep -c 'dropped in silence' dash.sthlp` → 0. AC-56.2 `python3 -m pytest test/test_help_conformance.py -q -p no:cacheprovider` 0 failed. AC-56.3 `python3 -m pytest test/test_help_claims_9.py -q` 10 passed. AC-56.4 the driver log holds `U56-1 PASS`, `U56-2 PASS`, `ALL CHECKS PASSED`.

## Tasks

**Commit boundary.** 56-01..56-03 form the J1 commit, subject `Generate the help's Unsupported list from every source and state the refusal rule (WP-31 J1)`; 56-04..56-06 the J2 commit, subject `Correct the help's syntax, legend, msangle, dot, not-drawn and log sentences (WP-31 J2)`. Bodies per BRIEF: saved failure text; defect; change; `Regression:` lines; `Flipped:` lines; `Fixture: test/fixtures/catchall_options_truth.json (scripts/extract_catchall_options_truth.do)` (J1 only); `BUGS.md: "<title>" (closed)`; `GAPS3: <row> Tracked`. Worktree `<W>` = `.../dash-wt/wp31-s56`, branch `wp31-s56`.

<task type="auto" id="56-01">
  <name>Measure the catch-all names and write failing tests</name>
  <files>scripts/extract_catchall_options_truth.do, test/fixtures/catchall_options_truth.json, test/test_help_conformance.py</files>
  <action><![CDATA[Create scripts/extract_catchall_options_truth.do per TR-56.2 (head copied from scripts/extract_default_base_truth.do :21-48; the option names read from .ultraplan/research/stata-ground-truth.md §1.2-1.3 tables, typed into a local list in the do-file with the value each takes: `1` for numeric, `red` for colour, `on` for flags). Run it through the slot (Stata truth) and `git add -f test/fixtures/catchall_options_truth.json`. In test/test_help_conformance.py add `_undeclared_twoway_options()` and `_catchall_options()` after `_unsupported_section()` (:373), the two `TestTheParsersFoundSomething` tests after :660, and widen `TestTheUnsupportedSectionIsTrue`'s expected set to the union, renaming nothing. Run `python3 -m pytest test/test_help_conformance.py -q -n0 -p no:cacheprovider -rf > <scratch>/s56/56-01.log 2>&1` and write <scratch>/56-01-failure.txt (base sha, each FAILED node and reason). Do not commit.]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/catchall_options_truth.json'));print(sorted(d['_meta']), len(d['options'])>0)"` prints the five _meta keys and True; `grep -c FAILED <scratch>/s56/56-01.log` is at least 2 and the first E line names an undeclared option; `test -s <scratch>/56-01-failure.txt`.]]></verify>
  <done>The options that reach the generic note were recorded in a stamped fixture, and the Unsupported-list test failed on the unmodified help naming them.</done>
</task>

<task type="auto" id="56-02">
  <name>Rewrite the Unsupported section</name>
  <files>dash.sthlp, test/test_help_claims_9.py</files>
  <action><![CDATA[Edit dash.sthlp :4970-4975 per D-56.b and add the grouped entries per TR-56.3 for every name `python3 -m pytest test/test_help_conformance.py -q -n0 -k Unsupported` still reports missing, until it passes. Create test/test_help_claims_9.py with `TestTheSilenceSentence::test_it_states_the_refusal_rule` (asserts `dropped in silence` absent and `option X() not allowed` present between `{marker unsupported}` and `{marker dependencies}`). Run `python3 -m pytest test/test_help_conformance.py test/test_help_claims_9.py test/test_unsupported_report_is_true.py $(grep -l "dropped in silence\|Unsupported" test/test_help_claims_*.py) -q -p no:cacheprovider`; flip any node that pinned the old sentence in place with a docstring line `Flipped (WP-31 J1): ...` and record it in <scratch>/s56/56-flips.txt.]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c 'dropped in silence' dash.sthlp` prints 0; `grep -c 'option X() not allowed' dash.sthlp` is at least 1.]]></verify>
  <done>The help listed every accepted-undrawn option from the three sources and stated the refusal rule, with the pins flipped.</done>
</task>

<task type="auto" id="56-03">
  <name>Close J1 and commit</name>
  <files>BUGS.md, GAPS3.md, CHANGELOG.md</files>
  <action><![CDATA[Close the J1 entry (BRIEF closed form: `Fixed <ddmonyyyy> (WP-31, J1). ... Pinned by test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue::test_every_accepted_undrawn_option_is_listed, test/test_help_claims_9.py::TestTheSilenceSentence::test_it_states_the_refusal_rule; fixture test/fixtures/catchall_options_truth.json. Closes GAPS3 J1 (WP-31, J1).`); delete the `"J1": "` line of WP31_OPEN in test/test_tracking_documents.py (a fourth file: list it in the commit, the task's three are the documents); rewrite `- **J1 Tracked:**` to the Closed form `- **J1 Tracked:** Closed in WP-31, BUGS.md "<J1 title>", commit pending.` (DECISIONS A11: the merger's step k.3b replaces `pending` with the landed sha on `s3-bugs` in one tracking commit per batch; S01's reader accepts `pending`; no amend, no second commit). Replace `<!-- WP-31 J1 -->` under `### Fixed in WP-31` with `- The help's Unsupported list names every option dash accepts and does not draw -- the pending blocks, the undeclared twoway options and the names that reach the generic note -- and says that an option twoway refuses on a plot type is refused. (WP-31, J1)`. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`; stage by name; commit per the Commit boundary; `grep -Eic 'claude|anthropic'` on the message prints 0.]]></action>
  <verify><![CDATA[`grep -c '^    "J1": "' test/test_tracking_documents.py` prints 0; `grep -c '<!-- WP-31 J1 -->' CHANGELOG.md` prints 0; `grep -c 'J1 Tracked:\*\* Closed in WP-31' GAPS3.md` prints 1; the tracking test reports 0 failed; `git log -1 --format=%s` ends `(WP-31 J1)`.]]></verify>
  <done>J1 was closed in BUGS.md, GAPS3.md and CHANGELOG.md in one commit with its fixture and tests.</done>
</task>

<task type="auto" id="56-04">
  <name>Write the failing J2 sentence tests</name>
  <files>test/test_help_claims_9.py, test/test_help_claims_1.cscript</files>
  <action><![CDATA[Append to test/test_help_claims_9.py the ten tests of TR-56.4, each reading dash.sthlp (and the code it checks against) and asserting the corrected sentence. For D-56.c first measure: `grep -n "once a minute\|_last_logged\|log_every\|_LOG_EVERY" dash_render.py`; record the finding in <scratch>/s56/56-log-gate.txt and write `test_the_refusal_log_claim` to assert either the gate's constant appears in the sentence or the sentence drops the once-a-minute claim. Append U56-1 and U56-2 to test/test_help_claims_1.cscript before its summary (its nfail/faillist form; header `*!` lines). Run `python3 -m pytest test/test_help_claims_9.py -q -n0 -p no:cacheprovider -rf > <scratch>/s56/56-04.log 2>&1` and the cscript through the driver; write <scratch>/56-04-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s56/56-04.log` is at least 8 (a sentence already corrected by S18, S21, S31 or S34 passes and is noted in the failure file as "already corrected by S<NN>"); the driver log holds `U56-1` lines; `test -s <scratch>/56-04-failure.txt`.]]></verify>
  <done>Each J2 sentence had a test that failed on the unmodified help, and the refusal-log claim was measured.</done>
</task>

<task type="auto" id="56-05">
  <name>Correct the nine sentences</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Make TR-56.3's J2 edits (:83, the period-slider move, :3545, :2816, :572, :252, :2262-2263 per D-56.c, the iframe pstd, the link() example, the %tC paragraph), reading S18's, S21's, S31's, S34's and S43's landed paragraphs first (D-56.d) and editing only the sentences J2 names. Run `python3 -m pytest test/test_help_claims_9.py test/test_help_conformance.py $(grep -l "Four {cmd:twoway}\|inside the plot region\|once a minute\|type(}{it:filter_type" test/test_help_claims_*.py) -q -p no:cacheprovider`; flip pins of the old wording in place with `Flipped (WP-31 J2)` docstring lines, recorded in <scratch>/s56/56-flips.txt; run test_help_claims_1.cscript through the driver.]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -c 'Four {cmd:twoway} plot types' dash.sthlp` prints 0; `grep -c iframe dash.sthlp` is at least 1; the driver log ends `ALL CHECKS PASSED` with `U56-1 PASS` and `U56-2 PASS`.]]></verify>
  <done>Every J2 sentence described the batch-19 tree and was pinned.</done>
</task>

<task type="auto" id="56-06">
  <name>Close J2 and commit</name>
  <files>BUGS.md, GAPS3.md, CHANGELOG.md</files>
  <action><![CDATA[Close the J2 entry (closed form; `Pinned by test/test_help_claims_9.py::<each class>::<test> (ten nodes), test/test_help_claims_1.cscript U56-1, U56-2`; a sentence left as a documented difference, such as ring(0) if S31 could not match twoway, goes in `Residual, deferred (WP-31): ... (GAPS3 J2 Tracked)` and its Tracked line takes the Partly form naming a new open BUGS.md entry); delete the `"J2": "` WP31_OPEN line; rewrite the J2 Tracked line to the Closed form with `commit pending` (A11; the Partly form, if a residual is filed, also ends `commit pending`); replace `<!-- WP-31 J2 -->` under `### Fixed in WP-31` with `- help dash: the Syntax line brackets filter()'s type(), the period-slider sentence sits with the slider, legend(ring(0)), msangle(), dot and the not-drawn types are described as drawn, the refusal-log sentence says what the server logs, and the page's iframe rule, a link() qualifier example and the %tC paragraph are new. (WP-31, J2)`. Run the tracking test; commit per the Commit boundary.]]></action>
  <verify><![CDATA[`grep -c '^    "J2": "' test/test_tracking_documents.py` prints 0; `grep -c '<!-- WP-31 J2 -->' CHANGELOG.md` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` reports 0 failed; `git log -1 --format=%s` ends `(WP-31 J2)`; `git log -2 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>J2 was closed in one commit with its tests and the two flipped pins recorded.</done>
</task>

## Section completion criteria

- Two commits on `wp31-s56` ending `(WP-31 J1)` and `(WP-31 J2)`; no test-only commit.
- `test_help_conformance.py` pins the Unsupported list to three sources both ways; `test_help_claims_9.py` (11) green; U56-1, U56-2 PASS.
- J1 and J2 closed in BUGS.md, Tracked Closed (or Partly with a residual entry), markers replaced, `WP31_OPEN` keys gone.

## Notes

- **R3.** S56 owns every dash.sthlp paragraph not named in another section's Notes; before editing a J2 sentence inside another section's paragraph, read that section's landed text and change only the J2 sentence.
- **R10.** `test_unsupported_report_is_true.py`'s declared counts move with `# old -> new: J1 <why>`.
- **R1.** No new cscript; Stata checks join test_help_claims_1.cscript.
- **Trap:** `_unsupported_section()` reads `{opt...}` only inside `{phang2}`/`{phang}` entries; a name written `{cmd:...}` in a prose `{pstd}` is not collected. Write every listed option as `{opt name}` inside an entry.
- **Tracked lines (A11):** both closing tasks write `commit pending`; the merger's step k.3b writes the sha; no amend anywhere. **A14:** no truth block (nothing is compared with twoway's drawing). **Files (A13):** `<files>` lists primary files; the tracking documents and flipped tests are implied.
- **Decisions for maintainer ratification:** D-56.c (drop the once-a-minute claim rather than add a throttle).


## Addendum (17oct2026, DECISIONS D36): row E10b added to this section

**Gap.** BUGS.md "textboxstyle and color-*.style files on the ado-path are not read" (found by WP-31 S44; graded S3: a user textbox or colour style falls to a note and the default).

**Requirement.** Document the limit in the help's scheme and style paragraph with the measured picture (a user textboxstyle or color style draws the default with twoway's note text); failing tests first; close the BUGS entry, the GAPS3 E10b Tracked line (`commit pending`), the CHANGELOG `<!-- WP-31 E10b -->` marker in "Fixed in WP-31" and the WP31_OPEN line; one commit ending `(WP-31 E10b)`.
