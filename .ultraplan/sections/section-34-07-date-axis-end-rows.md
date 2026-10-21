# Section 34-07: Date axis with a missing y at an end row (ts-operator probe first)

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: TR-4 · Risk: yellow · Batch: 34.3 · Depends on: 34-03 · Blocks: 34-09 · Tasks: 6, 2 commits · Case-id prefix: Q3407

## Overview

**What is wrong today.** `twoway area d.gnp96 date` (twoway_area.sthlp's own example) and `line d.gnp96 date` label x 1970q1 1980q1 1990q1 2000q1; dash ticks 1967q2 1976q1 1984q4 1993q3 2002q2, 35 quarters apart (TR-4). The audit's verifier and [S] §4 showed the cause is any missing y at the first or last row, operator or not: `replace gnp96 = . in 1; line gnp96 date` (N06), the same with the last row (N07: dash 1965q1 1970q1 ... 2000q1, 8 ticks) and `area` (N08) are wrong too, while `if date >= tq(1970q1)` (N15), `S4.` (four missing rows, N17) and no tsset (N14) happen to land right. At export `_dash_axis_ticks_stata` (dash.ado:7483) summarizes each axis's variables over the layer's marker rows (`quietly summarize \`v' if \`lu' & \`grp' == \`g', meanonly`, :7533), so a row whose y is missing still counts for x; Stata's range then starts at 1967q1 while the renderer draws from 1967q2, `_dash_stata_pick` (dash_render.py:41708) finds no match within 1e-9, and the date model ticks the axis.

**The precondition (D41, PD-16, DISCOVERY Q28).** Before any operator work, twoway is asked again whether time-series operators are allowed in twoway graphs: scripts/extract_ts_operator_truth.do is extended with the 22 probes of [S] §4 (N01-N20 on `sysuse gnp96`, S01-S02 on sp500) and re-run; the regenerated fixture is committed first. [S] §4 measured all 121 probes on 20oct2026: twoway allows operators on 29 types, refuses the rest exactly where dash refuses (r(101), r(198), r(5), r(111), r(109)), and its answers equal the 18oct2026 fixture's. If any answer now differs, the section stops at its checkpoint (34-07-02).

**After this section**, in both modes: Stata's own ticks are asked over the rows each series of a layer draws -- a row counts for an axis only when every variable of that series is non-missing (for `line y x`, y and x; for each y of `scatter y1 y2 x`, that y and x; for a range or pc layer, all of its variables) -- so the export's range is the drawn range and the date axis of every N/S probe equals twoway's. Refusals are unchanged (they already match twoway).

**Why one section.** One item; batch 34.3's one editor of the saved page's JavaScript (if the move-back check needs `dash_axis_extent`) and of the export's tick requests.

**Test order and commit rule.** Commit 1 (PD-16): 34-07-01 regenerates the fixture with the 22 probes and compares; 34-07-02 is the checkpoint; 34-07-03 commits the extract script and fixture `(WP-34 TR-4)` with the existing tests green. Commit 2: 34-07-04 writes the regression tests (red, saved failure text, no commit), 34-07-05 makes the fix and regenerates the fixture again, 34-07-06 closes TR-4 and commits `(WP-34 TR-4)`.

### Section decisions

- **D-34-07.a. The row rule is per series.** The request layer token gains a third part, the series' complete-case variables: `<axis vars>:<marks>:<cc vars>` (each `+`-joined). A multi-y yx layer is sent as one token per y (that y with the x variables); a range or pc layer as one token whose cc is every variable it names. dash.ado drops a row from the summary when any cc variable is missing (`missing()` covers `.` and `.a`-`.z`).
- **D-34-07.b. The renderer is the reference.** The cc rule must select exactly the rows the renderer draws (else the table never matches). A pytest computes the cc-rule range in Python for every type family over data with missing ends and asserts `_dash_stata_pick` finds it for the drawn axis; a family whose drawn rows differ from twoway's is recorded in the handback, not changed here.
- **D-34-07.c. Two commits.** PD-16 requires the regenerated fixture committed before any operator work; that commit changes no code and keeps every test green. The fix commit regenerates the fixture again (the X probes' specs then carry the corrected `stata_ticks`).

## Risk: [yellow] -- the export's summary changes for every axis of every layer

**Why.** Every Stata tick request carries the new token; a wrong cc set loses the table match (model fallback, as today) rather than drawing wrong ticks, so the failure mode is benign but silent.

**Risk factors.** 1. The token grammar is parsed in Stata (`gettoken`/`substr`) and must stay names-only (DECISIONS A25; test_stata_ticks.py::TestNoQualifierText). 2. Pins asserting the 2-part token (test_stata_ticks.py TestTheRequests, TestTheExportHelpers). 3. 34-02 runs in parallel and touches no request code; 34-09 later extends the same function. 4. The saved page's move-back restore compares the JS extent with the table.

**Mitigation.** The agreement test of D-34-07.b; the pins flipped with reasons; a node test of move-back for N06/N07; a cscript case per family.

## Dependencies

- **Depends on:** 34-03 (the finish's range join changed in batch 34.2; date axes were already exempt).
- **Blocks:** 34-09 (extends `_dash_stata_tick_requests` and adds the build-time oracle).
- **Parallel batch:** 34.3 with 34-02 (by() count and cells; no request, dash.ado or JS code).

## Evidence

### Code at 090d928 (re-read before editing)

dash.ado `_dash_axis_ticks_stata` (:7483), the layer loop:
```stata
    foreach L of local layers {
        local vs = subinstr(substr("`L'", 1, strpos("`L'", ":") - 1), "+", " ", .)
        local ms = subinstr(substr("`L'", strpos("`L'", ":") + 1, .), "+", " ", .)
        capture drop `lu'
        quietly generate byte `lu' = 1
        foreach m of local ms {
            confirm numeric variable `m', exact
            quietly replace `lu' = 0 if `m' != 1
        }
        foreach v of local vs {
            confirm numeric variable `v', exact
            forvalues g = 1/`ng' {
                quietly summarize `v' if `lu' & `grp' == `g', meanonly
```
(:7522-7533). dash_render.py `_dash_stata_tick_requests` (:41815) collects `groups[key].append((tuple(vs), tuple(marks)))` with `ys`/`xs` read from `yvar yvar1 yvar2 y1var y2var` / `xvar x1var x2var` (:41860-41875); `_dash_stata_tick_plan` writes `"+".join(vs) + ":" + "+".join(ms)` (:41912-41913). The ts columns are made before the request (`_dash_tsop_gen` dash.ado:8112, run at :11789; the request at :11821; build route :13236-13250).

### Fixture and probes

test/fixtures/ts_operator_truth.json (scripts/extract_ts_operator_truth.do, 18oct2026): 99 probes, datasets `_zt_data` sp/spd/us/nt/xt/au (:100-141), registration `zt <id> <ds> "<body>" "<opts>" "<flags>"` (:147-155), flags S (keys) and X (sersets plus dash's spec and data). Probe T01 `line D.close date` records `stata_ticks` `[14977, 15340, 5, "d", ...]` including the missing row. The 22 new probes ([S] §4): N01 `line gnp96 date`, N02 `line D.gnp96 date`, N03 `area d.gnp96 date`, N04 `line L.gnp96 date`, N05 `line L.gnp96 gnp96`, N06 `replace gnp96=. in 1` then `line gnp96 date`, N07 the same `in L`, N08 `replace gnp96=. in 1` then `area gnp96 date`, N09 `scatter D.gnp96 date`, N10 `line D.gnp96 L.gnp96`, N11 `tsline D.gnp96`, N12 `sort gnp96` then `line D.gnp96 date`, N13 `tsset, clear` then `line D.gnp96 date`, N14 `tsset, clear` then `line gnp96 date`, N15 `line D.gnp96 date if date >= tq(1970q1)`, N16 `line F.gnp96 date`, N17 `line S4.gnp96 date`, N18 `line D.gnp96 date, sort`, N19 `rarea L.gnp96 gnp96 date`, N20 `bar D.gnp96 date`; S01 (sp500, `tsset date`) `line D.close L.close`, S02 `line D.close date`. twoway's x labels ([S] §4 table): 1970q1(40)2000q1 on N01-N04, N06-N09, N11, N14-N20; N05/N10/S01 numeric; S02 01jan2001 ... 01jan2002; N12 r(5), N13 r(111).

### Tests pinning today's behaviour (flip, never delete)

- test/test_stata_ticks.py::TestTheRequests::test_secondary_axes_are_their_own (:245) asserts `[(("a",), ())] in ys` -- becomes the 3-tuple `[(("a",), (), ("a", "t"))]`.
- test/test_stata_ticks.py::TestTheExportHelpers::test_plan (:381) asserts the 2-part plan text -- becomes the 3-part text.
- test/test_ts_operators.py::TestBothModesMatchTwoway::test_every_probe (:384) compares titles and value labels only; it gains no flip (ticks are a new test).

## User stories

- US-34-07.1 As a Stata user with an existing twoway command, I want `dash area d.gnp96 date` to label 1970q1 1980q1 1990q1 2000q1, as twoway's own help example does.
- US-34-07.2 As that user, I want any series with a missing first or last value ticked as twoway ticks it.
- US-34-07.3 As the maintainer, I want twoway's acceptance of time-series operators re-confirmed before this work starts.

## Business requirements

- BR-34-07.1 twoway's answers on the 99 fixture probes and the 22 new ones are measured again and committed before any operator work; any difference stops the section.
- BR-34-07.2 A date (or numeric) axis is ticked over the rows each series draws, in both modes, so the N/S probes' axes equal twoway's.
- BR-34-07.3 Operator refusals stay twoway's (rc and first line).

## Technical requirements

- TR-34-07.1 Extract script: in `_zt_data` add dataset `gn` (`sysuse gnp96, clear`; `quietly tsset date`) and its variants through the probe body (the body may hold a `replace`/`sort`/`tsset, clear` prefix: register those as a new 6th `zt` argument `pre`, run with `quietly <pre>` after `_zt_data` and before twoway and before dash, and record it in probes.txt and the JSON as `"pre"`); `spd` already exists for S01-S02. Register N01-N20 and S01-S02 with flags `TX` (N12, N13 flags `""`), where the new flag T records, for rc 0, `.Graph.xaxis1.major.dlg_tickpos` (all elements) and `.Graph.plotregion1.xscale.curmin/curmax` into `<id>_xt.txt` (the `_dt_axis` reader of scripts/extract_date_axes_truth.do:90-106, copied as `_zt_axis`), written to the JSON as `"twoway": {..., "xticks": [...], "xcur": [lo, hi]}`. `_meta.probes` becomes 121.
- TR-34-07.2 `<scratch>/34-07/compare.py` (not committed): loads the committed fixture (git show HEAD:test/fixtures/ts_operator_truth.json) and the regenerated one, and for each of the 99 old probes compares `twoway.rc`, `twoway.err`, `twoway.titles`, `twoway.keys`, `twoway.sersets` exactly; prints `N differences` and each one; and checks each N/S probe's `twoway.rc` against [S] §4 (0 except N12 5, N13 111).
- TR-34-07.3 `_dash_stata_tick_requests` (D-34-07.a): per plot, when its ys come from the `yvar` key alone and xs from `xvar`, emit one series per y: `series = [((y,), tuple(xs), (y,) + tuple(xs)) for y in ys]` -> for letter y the axis vars `(y,)`, for letter x `tuple(xs)`, cc `(y,) + tuple(xs)`; otherwise (range or pc keys) one series with the existing ys/xs and cc `tuple(ys + xs)`. `groups[key].append((tuple(vs), tuple(marks), tuple(cc)))`. Every cc name passes `_DASH_STATA_NAME_RE` (same check as today). `_dash_stata_tick_plan`: each token is `"+".join(vs) + ":" + "+".join(ms) + ":" + "+".join(cc)`.
- TR-34-07.4 dash.ado `_dash_axis_ticks_stata`: parse `L` as `<vs>:<ms>:<cs>`: `local r1 = substr("\`L'", strpos("\`L'", ":") + 1, .)`; `local ms = subinstr(cond(strpos("\`r1'", ":"), substr("\`r1'", 1, strpos("\`r1'", ":") - 1), "\`r1'"), "+", " ", .)`; `local cs = cond(strpos("\`r1'", ":"), subinstr(substr("\`r1'", strpos("\`r1'", ":") + 1, .), "+", " ", .), "")`; after the marker loop, `foreach c of local cs { confirm numeric variable \`c', exact` / `quietly replace \`lu' = 0 if missing(\`c') }`. A 2-part token (an older plan) keeps today's behaviour. The header comment documents the third part. Version 19 unchanged; no new program, so no program_coverage_map.py row.
- TR-34-07.5 Saved page: build N06's and N07's pages, move a filter and move it back (node through test/js_runner.py, as test/test_stata_ticks.py::TestAfterAMove does); the restored x ticks must be Stata's (the plan's `stata` rows). If they are not because `dash_axis_extent` reads a row the Python extent does not, make `dash_axis_extent` skip that row exactly as `_dash_layer_extent` does (this section is batch 34.3's one JS editor); otherwise no JS change.
- TR-34-07.6 Served: no literal change; `_dash_stata_tick_requests` runs in Stata at export only.

## Boundaries

- No refusal changes (all 121 probes agree, [S] §4); Q28 applies only if 34-07-02 finds a difference.
- Do not touch `_dash_stata_or_model`, `_dash_stata_pick` or add counts to the requests (34-09's); do not touch `_dash_by_numticks` (34-02's, same batch).
- The tsset/tsrevar machinery (`_dash_tsop_gen`) is unchanged.

## Stata truth

TR-34-07.1, run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_ts_operator_truth.do` (twice: 34-07-01 and 34-07-05); `git add -f test/fixtures/ts_operator_truth.json`. Truth block, inserted directly above the first block whose `S<MM>` is higher than S07 (BRIEF "Block order"; at the batch-34.3 base that is S08, which 34-08 landed in batch 34.2), not above the marker (REVIEW R2-20); it uses S01's helpers:

```
* ==== S07 TR-4: a date axis ticked over the rows each series draws ====
local only : env WP34_ONLY
if inlist("`only'", "", "S07") & `: list posof "S07" in w34_run' {
    display as text "S07 start " c(current_date) " " c(current_time)
    ...
    display as text "S07 end " c(current_date) " " c(current_time)
}
* ==== end S07 ====
```
- Q3407-1: on `sysuse gnp96` with `tsset date`: for `line D.gnp96 date`, `area d.gnp96 date`, `replace gnp96=. in 1` + `line gnp96 date`, and `in L` + `line gnp96 date`, twoway's x ticks (`_q34_drawn .Graph x1`) equal the saved page's x FixedTicker (`_q34_has ... "tq"`).
- Q3407-2: `scatter D.gnp96 L.gnp96 date` (two series, one missing at each end) and `rarea L.gnp96 gnp96 date`: the same equality.

Q3407-3 is a refusal and return-code case, so it is not in the S07 block: it goes in test/test_parser.cscript, the area cscript of the time-series operator cases (its TSO block, :3664-3973), under its own id (BRIEF "Certification scripts", R1). It checks the two refusals among the 22 new probes, which no case compares with dash yet: TSO-07 (:3928-3962) already holds dash to twoway's rc and first line on every B probe -- by() with an operator, r(5), the B01 `scatter D.close t, by(g)` case included -- and on the O and Y probes, but its loop reads only ids starting B, O or Y. Directly after the line `display "TSO-07 PASS: ..."` (:3962), inside the same `if c(python_exec)` block:
```
    // Q3407-3 (WP-34 TR-4): the refusals among the 22 probes of 20oct2026
    // -- N12 (sort gnp96 first, r(5)) and N13 (tsset, clear first,
    // r(111)) -- are twoway's rc and first line, read from the fixture.
    foreach pid in N12 N13 {
        python: _tq = _tj.load(open("fixtures/ts_operator_truth.json", encoding="utf-8"))["probes"][_ts.Macro.getLocal("pid")]; _ts.Macro.setLocal("tso_b", _tq["body"]); _ts.Macro.setLocal("tso_pre", _tq.get("pre") or "")
        quietly sysuse gnp96, clear
        quietly tsset date
        quietly `tso_pre'
        _tso_vs Q3407-3 `pid' gn `"dash `tso_b', name(q3407)"'
    }
    dash clear
    display "Q3407-3 PASS: N12 r(5) and N13 r(111) are refused with twoway's rc and first line"
```
(`_tso_vs` compares the rc and the first line and prints `Q3407-3 FAIL: ...` itself; `_tso_data gn` matches none of its branches, so the data loaded above are kept.) It is no regression test: it would pass on commit 1's tree (the refusals agree, [S] §4), so 34-07-05 adds it with the fix, and it guards BR-34-07.3 across the token change.

## TDD test stubs

Commit 1: none new (the existing test_ts_operators.py suite must pass against the regenerated fixture).
Commit 2 regression tests (red at commit 1):
- Test: for every T-flagged probe with rc 0, both modes draw twoway's x ticks (`twoway.xticks`, converted from Stata units to the axis' epoch ms as test_ts_operators.py's `_DAY`/`_EPOCH` do) -- test/test_ts_operators.py::TestTheDateAxisTicks::test_every_tick_probe[saved|served] (red on N02-N04, N06-N09, N11, N16, N18-N20)
- Test: the requests send one cc token per y of a multi-y layer and one with every variable for a range/pc layer -- test/test_stata_ticks.py::TestTheRequests::test_complete_case_tokens
- Test: for each family (scatter, line, connected, area, bar, spike, dropline, tsline, rarea, rline, rcap, pcspike, pcscatter) over data whose first y and last x are missing, the cc-rule range computed in Python is the renderer's drawn range on both axes (`_dash_stata_pick` finds it) -- ::TestTheRowRule::test_matches_the_drawn_range[family]
- Test: the saved page restores Stata's ticks after a move back to all rows on N06 and N07 (node) -- test/test_ts_operators.py::TestTheDateAxisTicks::test_move_back[N06|N07]
cscript: Q3407-1, Q3407-2 (the S07 block); Q3407-3 in test/test_parser.cscript (the refusals of N12 and N13).
Pinned tests to flip: test/test_stata_ticks.py::TestTheRequests::test_secondary_axes_are_their_own, ::TestTheExportHelpers::test_plan.
Parity: append `_case("line with a missing first y on a date axis", [plot_for("line", {}, yvar=<the frame's y>, xvar=<its date>)], if_expr="")` (`plot_for` takes `yvar=`/`xvar=` keywords, test/test_server_layer_defects.py:82) built over test_mode_parity's `_DF` with row 0's y set missing (follow the file's pattern for a custom frame) to `CORPUS`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Precondition: twoway's answers unchanged | compare.py + checkpoint | ts_operator_truth.json (old vs new) | n/a |
| Ticks over drawn rows | pytest TestTheDateAxisTicks | ts_operator_truth.json N/S probes | yes |
| Token grammar | pytest TestTheRequests | -- | n/a |
| cc rule = renderer rows | pytest TestTheRowRule | -- | yes |
| Move back | node | -- | saved |
| Live twoway vs dash | cscript Q3407-1, Q3407-2 (S07 block) | -- | saved |
| Refusals of the new probes unchanged | test/test_parser.cscript Q3407-3 | ts_operator_truth.json N12, N13 | saved |

AC-34-07.1 the precondition is recorded (no difference, or the maintainer's ruling); AC-34-07.2 every N/S probe's x ticks equal twoway's in both modes; AC-34-07.3 refusals unchanged; AC-34-07.4 two green commits.

## Tasks

**Commit boundary.** Commit 1 = 34-07-01 to 34-07-03, subject `Ask twoway again about time-series operators: 22 probes on gnp96 and sp500 (WP-34 TR-4)`, made by 34-07-03 (extract script and fixture only; the tree is green). Commit 2 = 34-07-04 to 34-07-06, subject `Ask Stata for a date axis's ticks over the rows each series draws (WP-34 TR-4)`, made by 34-07-06. Branch `wp34-s07` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s07`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (34-07-06 for TR-4; 34-07-03's precondition commit closes nothing and only pulls) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-07/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-07 <scratch>/34-07/run_test_wp33_truth.do` and read `<scratch>/34-07/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-07/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-07-01">
  <name>Regenerate the ts-operator truth with 22 probes</name>
  <files>scripts/extract_ts_operator_truth.do, test/fixtures/ts_operator_truth.json</files>
  <action><![CDATA[
Apply TR-34-07.1 to scripts/extract_ts_operator_truth.do (the `gn` dataset, the 6th `pre` argument, the T flag and `_zt_axis`, the 22 registrations after Y01), run it through scripts/stata_slot.sh, and git add -f the fixture. Write and run <scratch>/34-07/compare.py per TR-34-07.2, saving its output to <scratch>/34-07/compare.txt. Run `python3 -m pytest test/test_ts_operators.py test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider > <scratch>/34-07/01.log`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/ts_operator_truth.json'));print(d['_meta']['probes'], d['probes']['N02']['twoway']['rc'], d['probes']['N12']['twoway']['rc'])"` prints `121 0 5`; `tail -1 <scratch>/34-07/01.log` reports 0 failed; `head -1 <scratch>/34-07/compare.txt` is the difference count line.]]></verify>
  <done>twoway's answers on 121 operator probes were measured again and compared with the 18oct2026 fixture.</done>
</task>

<task type="checkpoint" id="34-07-02">
  <name>Confirm twoway still allows the operators</name>
  <files>none</files>
  <action><![CDATA[
Read <scratch>/34-07/compare.txt. If it reports 0 differences and every N/S rc as [S] §4 gives it, write `PRECONDITION MET <date>` to <scratch>/34-07/checkpoint.txt and continue with 34-07-03 without waiting (D41's precondition is then met, as research measured on 20oct2026). If anything differs, stop: give the maintainer the differing probes (id, command, old and new rc and first line) and wait for a ruling; DISCOVERY Q28 says dash then refuses exactly where twoway refuses, with its rc and words, and the operator work proceeds only where twoway draws.
  ]]></action>
  <verify><![CDATA[`cat <scratch>/34-07/checkpoint.txt` prints `PRECONDITION MET` and the date, or the maintainer's ruling is recorded there.]]></verify>
  <done>twoway's acceptance of time-series operators was re-confirmed (or ruled on) before any operator work.</done>
</task>

<task type="auto" id="34-07-03">
  <name>Commit the regenerated operator truth</name>
  <files>scripts/extract_ts_operator_truth.do, test/fixtures/ts_operator_truth.json</files>
  <action><![CDATA[
Commit only the extract script and the fixture (no BUGS, GAPS4 or CHANGELOG change: TR-4 stays Open), with a body that says "D41/PD-16 precondition: twoway's answers on the 99 probes of 18oct2026 are unchanged (<scratch>/34-07/compare.txt: 0 differences); 22 probes added ([S] §4 N01-N20, S01-S02) with twoway's x ticks (flag T)." and the line `Fixture: test/fixtures/ts_operator_truth.json (scripts/extract_ts_operator_truth.do)`. First pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main) and run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`git log -1 --format=%s` ends `(WP-34 TR-4)`; `git show --stat HEAD | grep -c "dash_render.py\|dash.ado"` prints 0.]]></verify>
  <done>The re-measured operator truth was committed before any operator code changed.</done>
</task>

<task type="auto" id="34-07-04">
  <name>Write failing date-axis tick tests</name>
  <files>test/test_ts_operators.py, test/test_stata_ticks.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read _dash_stata_tick_requests, _dash_stata_tick_plan, dash.ado's _dash_axis_ticks_stata and dash_axis_extent at the batch base; run `node .gitnexus/run.cjs impact "_dash_stata_tick_requests" --direction upstream --repo .` and the same for `_dash_stata_tick_plan`, writing callers to <scratch>/34-07/anchors.txt. Add the commit-2 stubs to test/test_ts_operators.py (TestTheDateAxisTicks, reading each probe's `dash.spec`/`dash.data` through the file's `_write` and both renderers) and test/test_stata_ticks.py (TestTheRequests::test_complete_case_tokens, TestTheRowRule). Insert the S07 block where the Stata truth section says (above S08). Run `python3 -m pytest test/test_ts_operators.py test/test_stata_ticks.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-07/04.log`, the S07 block with WP34_ONLY=S07, and save the failures to <scratch>/34-07-04-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/34-07/04.log` is at least 10; `grep -c "Q3407-[12] FAIL" <scratch>/34-07/run_test_wp34_truth.log` is at least 1; `test -s <scratch>/34-07-04-failure.txt`.]]></verify>
  <done>The date-axis, token and row-rule tests were shown failing on the tree after commit 1.</done>
</task>

<task type="auto" id="34-07-05">
  <name>Summarize each series over its drawn rows</name>
  <files>dash_render.py, dash.ado, test/test_parser.cscript</files>
  <action><![CDATA[
Apply TR-34-07.3 (per-series cc tokens in _dash_stata_tick_requests and the 3-part plan text) and TR-34-07.4 (dash.ado parses and applies the cc part). Regenerate the fixture test/fixtures/ts_operator_truth.json (TR-34-07.1's run again) so the X probes' specs carry the corrected stata_ticks; git add -f. Do TR-34-07.5's move-back check; change dash_axis_extent only if it fails. Add Q3407-3 to test/test_parser.cscript after TSO-07, as the Stata truth section gives it. Run test/test_ts_operators.py, test/test_stata_ticks.py, test/test_date_axis_ticks.py, test/test_default_axes.py, test/test_natscale_js.py, test/test_env_guards*.py if present, test/test_program_coverage_map.py and the S07 block; and test/test_parser.cscript and test/test_env_guards.cscript through the driver (dash.ado changed), their logs at <scratch>/34-07/run_test_parser.log and <scratch>/34-07/run_test_env_guards.log.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ts_operators.py test/test_stata_ticks.py -k "not secondary_axes_are_their_own and not test_plan" test/test_date_axis_ticks.py -q -n0 -p no:cacheprovider` ends with 0 failed; `grep -c "Q3407-[12] PASS" <scratch>/34-07/run_test_wp34_truth.log` prints 2; `grep -c "Q3407-3 PASS" <scratch>/34-07/run_test_parser.log` prints 1; both area cscripts end with 0 FAIL.]]></verify>
  <done>Stata's ticks are asked over the rows each series draws and every N/S probe's axis equals twoway's in both modes.</done>
</task>

<task type="auto" id="34-07-06">
  <name>Flip pins, document, close TR-4</name>
  <files>test/test_stata_ticks.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
Flip TestTheRequests::test_secondary_axes_are_their_own and TestTheExportHelpers::test_plan to the 3-part forms with `# Flipped (WP-34 TR-4): a layer's token carries the variables its rows need, so a row with a missing y counts for no axis.` Append the CORPUS entry to test/test_mode_parity.py. Help: after the date-axis paragraph's sentence ending "as {cmd:twoway} does." (dash.sthlp:4690, the `line close date` example) add "Each axis is asked of Stata over the rows a layer draws, so a series whose first or last value is missing -- every {cmd:L.} or {cmd:D.} series -- is ticked as {cmd:twoway} ticks it ({cmd:area d.gnp96 date} labels 1970q1 ... 2000q1)." and test/test_ts_operators.py::TestTheHelp::test_the_rows_sentence (the `_between(_help(), ...)` pattern). Append `[WP-34 TR-4: corrected -- an axis is asked of Stata over the rows each series draws, so a missing end row keeps Stata's ticks]` to the Axes row of TWOWAY_COVERAGE_AUDIT.md (:140; M13, G1, REVIEW R2-9). Close the BUGS.md entry 33-01 registered for TR-4 (closed form: _dash_stata_tick_requests sends each series' complete-case variables and _dash_axis_ticks_stata drops a row any of them misses, both modes through build_options.stata_ticks; the precondition commit's compare result; pinned by test/test_ts_operators.py::TestTheDateAxisTicks::test_every_tick_probe, Q3407-1 and test_parser.cscript's Q3407-3; fixture ts_operator_truth.json); rewrite `- **TR-4 Tracked:**` to the Closed form with `commit pending`; delete TR-4's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- A date axis whose layer has a missing y in its first or last row takes Stata's ticks (area d.gnp96 date: 1967q2 ... 2002q2 -> 1970q1 ... 2000q1) (WP-34, TR-4)` under `### Fixed in WP-34`. Run the Closing steps for TR-4 (Tasks; BRIEF steps (1)-(3)): (1) delete TR-4's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py TR-4`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-07) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_ts_operators.py, test/test_stata_ticks.py, test/test_mode_parity.py -k "missing first y", test/test_help_conformance.py, test/test_tracking_documents.py, test/test_fixtures_are_committed.py and the S07 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ts_operators.py test/test_stata_ticks.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends with 0 failed; `awk -F'\t' '$1 == "TR-4"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py TR-4` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-07/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 TR-4)`; `grep -c "TR-4 Tracked:\*\* Closed in WP-34" GAPS4.md` prints 1.]]></verify>
  <done>Series with missing end rows take Stata's ticks in both modes and TR-4 is closed after its precondition commit.</done>
</task>

## Section completion criteria

- The precondition recorded (compare.txt, checkpoint.txt) and committed first; 121 probes in the fixture; every N/S probe's x ticks equal twoway's in both modes; the row-rule agreement test green for every family; pins flipped; help sentence pinned; two green commits; BUGS/GAPS4/CHANGELOG per BRIEF in commit 2.

## Notes

- **R11/R12:** 34-07 is batch 34.3's one JS editor (TR-34-07.5, only if needed); 34-02 edits no JS.
- **A25:** the cc part holds Stata names only (the same `_DASH_STATA_NAME_RE` gate); TestNoQualifierText stays green.
- **Help (R3):** this section owns the one sentence after dash.sthlp:4690.
- **R1:** Q3407-3 is the one case this section adds outside test_wp34_truth.cscript (a refusal case, in the area cscript); it uses test_parser.cscript's own `_tso_vs`, `_tj` and `_ts`, so add no helper there.
- **For 34-09:** it extends `_dash_stata_tick_requests` (counts) in batch 34.4 on top of this token form.
- **Manifest note (REVIEW R2-25):** the index's Owns cell names `_dash_stata_ticks_gen` (dash.ado:7431); this section edits dash.ado `_dash_axis_ticks_stata` (:7483) and, in dash_render.py, `_dash_stata_tick_requests` (:41815) and `_dash_stata_tick_plan` (:41887), plus `dash_axis_extent` (:43118) only if TR-34-07.5 needs it. `_dash_stata_ticks_gen` is not edited. The cell's correction is the index's (the orchestrator's).
- **Commit body line forms (commit 2):** `Regression: test/test_ts_operators.py::TestTheDateAxisTicks::test_every_tick_probe -- failed at <commit-1 sha> with <text>`; `Flipped: test/test_stata_ticks.py::TestTheRequests::test_secondary_axes_are_their_own -- the 2-part token was wrong because a row with a missing y counted for x`; `Fixture: test/fixtures/ts_operator_truth.json (scripts/extract_ts_operator_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: TR-4 Tracked`.
- Merge rules touched: R1, R6 (dash.ado), R7, R8, R9, R11.
