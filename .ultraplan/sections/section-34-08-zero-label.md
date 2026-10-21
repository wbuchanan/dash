# Section 34-08: a(b)c rules write the zero label as 0

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: DG-3 · Risk: green · Batch: 34.2 · Depends on: none · Blocks: none · Tasks: 3, 1 commit · Case-id prefix: Q3408

## Overview

**What is wrong today.** `ylabel(-.3(.1).3)` labels `-.3 -.2 -.1 0 .1 .2 .3` in twoway; dash's saved page holds the y ticks `[-0.3, -0.19999999999999998, -0.09999999999999998, 5.551115123125783e-17, 0.10000000000000003, 0.2, 0.3000000000000001]` and the browser writes the middle label `5.551e-17`; `-.7(.1).7` gives `1.110e-16` ([S] §8; DG-3, run1 T17, run2 T26/T27). `_dash_expand_numlist` (dash_render.py:39963) builds every `a(b)c` value as `a + b * k` in plain floats (:40083); the `to`/`:` forms (:40045) and `a/b` (:40099) the same. D41: "A zero label is written 0, never 5.551e-17."

**What Stata does (measured 20oct2026 for this plan, StataNow 19.5 console, on 30 of the 33 rules the extractor records, TR-34-08.4).** `numlist "a(b)c"` (1) counts `floor(q * (1 + 100*eps))` steps, `q = (c - a)/b`, `eps = 2.220446049250313e-16` (DBL_EPSILON): `-1(1.00000000000002)2` gives four values `-1 0 1 2` but `-2(1.00000000000003)0` two, `-2 -1`, and `100000.1(.1)100000.5` four, ending `100000.4`; (2) makes each value `a + k*b` and writes 0 for a value whose magnitude is below `100*eps*|a|`: `-1(.250000000000002)1` writes `0` for a residue of 8.0e-15 (3.2e-14 of |b|, above the bound, so the bound is relative to |a|, not b) and `-1(1.000000000000025)1` keeps `2.50910404e-14`; (3) writes each value as `%15.0g` text and reads it back, so every value is the double nearest a short decimal: `-.3(.1).3` returns `-.3 -.2 -.1 0 .1 .2 .3` (`-.2` is `-1.999999999999aX-003`, the nearest double to -0.2), and twoway's `dlg_tickpos` for `ylabel(-.3(.1).3)` are those doubles; `0(.3333333333333333)1` -> `.3333333333333 .6666666666667`; `123456.123456789(1)123458` -> `123456.1234568`; `-.000123456789012345(.0001)0` -> `-.000123456789 -.000023456789`; `-1e-5(1e-6)1e-5` -> `-.00001 -9.00000000e-06 ...`; `1e14(1e13)1.2e14` -> `1.00000000e+14 ...`; `1e150(1e149)1.2e150` -> `1.0000000e+150 ...` (each equal to `display %15.0g`). The rule in TR-34-08.1 reproduces all 30 measured rules exactly (checked in Python while writing this section); the extractor measures all 33 again, and its fixture is the requirement.

**After this section**, every value the axis-label numlist expander makes -- `a(b)c`, `a[b]c`, `x y to z`, `x y:z`, `a/b` and a plain number -- is the double Stata's numlist makes (the value written as `%15.0g` and read back), in both modes, so a rule crossing zero has a tick at exactly 0 labelled `0`, and every other tick sits where twoway's does.

**Why one section.** One item, one Python function (no JavaScript twin: FixedTicker values are made at build).

**Test order and commit rule.** 34-08-01 records Stata's numlist answers into a fixture, writes the regression tests and the cscript block, runs them red, saves `<scratch>/34-08-01-failure.txt`, no commit. 34-08-02 adds the rounding helper and uses it. 34-08-03 closes DG-3 and commits `(WP-34 DG-3)`.

### Section decisions

- **D-34-08.a. Stata's three steps, in order.** Count by `floor(q * (1 + 100*eps))`; make `a + k*b` and write 0 below `100*eps*|a|`; write as `%15.0g` and read back (`_dash_numlist_value`). Every value takes the read-back, so `-0.19999999999999998` becomes `-0.2` and `0.30000000000000004` becomes `0.3`, as in Stata.
- **D-34-08.b. The count changes only at the edge.** dash counts `floor(q + 1e-9)` today; the two rules differ only when `q` is within 1e-9 of a whole number but further than `100*eps*q` from it (`0(.333333333334)1`, q = 2.999999999994: dash counts four values today and the measured rule predicts three; the fixture row decides, and its answer is the requirement).

## Risk: [green] -- one pure function's values change by at most an ulp-scale amount

**Why.** The helper is pure; values move only to the nearest short decimal.

**Risk factors.** 1. Tests comparing raw `a + b*k` floats, or a count at the 1e-9 edge. 2. Six callers of `_dash_expand_numlist` (:7155, :36601, :39500, :39659, :40183, :57115). 3. The `%15.0g` boundaries (fixed versus exponent form) for very small and very large values.

**Mitigation.** Fixture rows across magnitudes (1e-100 to 1.2e14) pin the boundaries; the callers' test files run in 34-08-02.

## Dependencies

- **Depends on:** none. **Blocks:** none.
- **Parallel batch:** 34.2 with 34-03 and 34-06; disjoint (only `_dash_expand_numlist` and a new helper).

## Evidence

### Code at 090d928 (re-read before editing)

```python
40074             span = (c - a) / b + 1e-9
 ...
40079             n_steps = max(0, int(math.floor(span)))
40080             if not _reserve(n_steps + 1):
40081                 i += 1
40082                 continue
40083             values.extend(a + b * k for k in range(n_steps + 1))
```
The `to`/`:` branch: `values.append(x); values.append(y); values.extend(y + step * k for k in range(1, n_steps + 1))` (:40042-40044); `a/b`: `values.extend(a + step * k for k in range(n_steps + 1))` (:40098); the `y:z` token branch (`_DASH_AXIS_COLON_RE`, :40100ff) and plain numbers (the final branch) append floats too. Copied to the served app by name (`"_dash_expand_numlist", "_dash_axis_too_many",`, dash_render.py:67514).

### Fixtures and tests

test/fixtures/axis_truth.json group b1_label (forms); test/test_axis_label_grammar.py `_FORMS` (:182-189, exact-binary values) and `TestTheExpander` (:262ff). No zero-crossing truth exists (the only zero-crossing grammar test is `-1(.5)2.5`, exact in binary).

## User stories

- US-34-08.1 As a Stata user with an existing twoway command, I want `ylabel(-.6(.2).6)` to label the middle tick `0`, as twoway does.
- US-34-08.2 As that user, I want every tick of a numlist rule placed where twoway places it.

## Business requirements

- BR-34-08.1 A label or tick rule that crosses zero has a tick at exactly zero, labelled 0, in both modes.
- BR-34-08.2 Every value of a numlist rule equals the value Stata's numlist makes for it.
- BR-34-08.3 The number of values a rule makes is the number Stata's numlist makes.

## Technical requirements

- TR-34-08.1 New module constant and function before `_dash_expand_numlist` (:39963):
```python
#: WP-34 DG-3: numlist's relative tolerance, 100 DBL_EPSILON (measured).
_DASH_NUMLIST_TOL = 100.0 * 2.220446049250313e-16


def _dash_numlist_value(v):
    """The double Stata's numlist writes for *v* (WP-34 DG-3): the value
    as %15.0g text, read back (measured 20oct2026, numlist_truth.json):
    the fixed form for a decimal exponent e of -5 to 13, with 13
    decimals when e < 0 and 12 - e (none past 12) otherwise; else the
    exponent form, 8 mantissa decimals, 7 when |e| >= 100.  A
    non-finite value is returned as it is; -0 is 0."""
    try:
        v = float(v)
    except (TypeError, ValueError, OverflowError):
        return v
    if not math.isfinite(v):
        return v
    if v == 0.0:
        return 0.0
    e = int(("%.16e" % abs(v)).split("e")[1])
    if -5 <= e <= 13:
        d = 13 if e < 0 else max(0, 12 - e)
        return float("%.*f" % (d, v)) or 0.0
    return float(("%.8e" if abs(e) < 100 else "%.7e") % v)


def _dash_numlist_step(start, step, k):
    """``start + k*step`` as numlist makes it: 0 when its magnitude is
    below ``_DASH_NUMLIST_TOL * |start|`` (measured: -1(.250000000000002)1
    writes 0), then :func:`_dash_numlist_value`."""
    v = start + step * k
    if abs(v) < _DASH_NUMLIST_TOL * abs(start):
        v = 0.0
    return _dash_numlist_value(v)
```
- TR-34-08.2 `_dash_expand_numlist`: (a) `a(b)c`/`a[b]c` (:40074): `span = (c - a) / b * (1.0 + _DASH_NUMLIST_TOL)` replaces `+ 1e-9`, and `values.extend(_dash_numlist_step(a, b, k) for k in range(n_steps + 1))`; (b) `x y to z` and `x y : z` (:40031): `span = (z - y) / step * (1.0 + _DASH_NUMLIST_TOL)`, `values.append(_dash_numlist_value(x))`, `values.append(_dash_numlist_value(y))`, `values.extend(_dash_numlist_step(y, step, k) for k in range(1, n_steps + 1))`; (c) the `y:z` token branch (`_DASH_AXIS_COLON_RE`, :40100ff) the same as (b) with its own `x`; (d) `a/b`: values `_dash_numlist_step(a, step, k)` (count unchanged, integer steps); (e) a plain number: `_dash_numlist_value(float(tok))`. `_reserve`, the zero-step and non-finite checks are unchanged; a negative `span` still gives `max(0, ...)` steps as today.
- TR-34-08.3 Served copy list (R2): add `"_dash_numlist_value", "_dash_numlist_step",` after `"_dash_expand_numlist", "_dash_axis_too_many",` (:67514). test/function_test_map.py: `'_dash_numlist_value': 'test/test_axis_label_grammar.py::TestTheNumlistRule::test_the_helper',` and `'_dash_numlist_step': 'test/test_axis_label_grammar.py::TestTheNumlistRule::test_every_rule_reads_back_as_statas',`; the constant `_DASH_NUMLIST_TOL` goes in the served constants tuple beside `_MAX_AXIS_TICKS` (grep `"_MAX_AXIS_TICKS"` for the anchor).
- TR-34-08.4 Stata truth: create `scripts/extract_numlist_truth.do` (header, root, `_meta` and git stamp per scripts/extract_ts_operator_truth.do:1-90). For each rule in `-.3(.1).3`, `-.7(.1).7`, `-.6(.2).6`, `1(-.1)-1`, `-.05(.01).05`, `-3(.3)3`, `-.3[.1].3`, `-.3 -.2 to .3`, `-.3 -.2:.3`, `0(.1)1`, `-2/2`, `-1e-5(1e-6)1e-5`, `0(.3333333333333333)1`, `123456.123456789(1)123458`, `0(1.234567890123456)3`, `-1(0.0000001234567891)-0.9999995`, `1e6(.25)1000001`, `-.000123456789012345(.0001)0`, `12345678.123456(1)12345680`, `100000.1(.1)100000.5`, `1e13(1e12)1.2e13`, `1e14(1e13)1.2e14`, `1e-100(1e-101)1.2e-100`, `0.30000000000000004`, `0(.333333333334)1`, and the measured edge rows `-1(1.00000000000002)2`, `-2(1.00000000000003)0`, `-1(1.000000000000025)1`, `-1(.250000000000002)1`, `-4(4.00000000000006)4`, `-4(4.00000000000012)4`, `-1(.99999999999999)1`, `1e150(1e149)1.2e150`: run `numlist "<rule>"` and record `r(numlist)` and each value as `%21x` (a python block converts `%21x` to a JSON double exactly). For `-.3(.1).3`, `-.7(.1).7` and `-.6(.2).6` also draw `twoway scatter y x, ylabel(<rule>)` (data: `set obs 11`, `x = _n`, `y = (_n-6)/10*7`) and record `.Graph.yaxis1.major.dlg_tickpos` and the SVG's y label texts (scripts/svg_truth.py, as extract_ts_operator_truth's `_texts`). Output `test/fixtures/numlist_truth.json` `{"_meta": ..., "rules": {"<rule>": {"text": "...", "values": [...]}}, "drawn": {"<rule>": {"ticks": [...], "labels": [...]}}}`; `git add -f`.

## Boundaries

- Only `_dash_expand_numlist` and the new helper; no change to the axis formatters, to `_dash_parse_axis_spec`'s grammar or to dash.ado (which already passes tline() through Stata's own numlist).
- No JavaScript (the label rules are build-time FixedTicker values).

## Stata truth

`scripts/extract_numlist_truth.do` -> `test/fixtures/numlist_truth.json` (TR-34-08.4), run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_numlist_truth.do`. Truth block, inserted directly above the first block whose `S<MM>` is higher than S08 (BRIEF "Block order"), or above `* ==== append new blocks above this line ====` if there is none (in batch 34.2 there is none; 34-07's S07 later lands above it):

```
* ==== S08 DG-3: a(b)c rules crossing zero label 0 ====
local only : env WP34_ONLY
if inlist("`only'", "", "S08") & `: list posof "S08" in w34_run' {
    display as text "S08 start " c(current_date) " " c(current_time)
    ...
    display as text "S08 end " c(current_date) " " c(current_time)
}
* ==== end S08 ====
```
- Q3408-1: for `ylabel(-.3(.1).3)` and `ylabel(-.7(.1).7)`, twoway's `dlg_tickpos` (`_q34_drawn .Graph y1`, S01's helper) equal the saved page's y FixedTicker (`_q34_has`), so the middle tick is 0.

## TDD test stubs

Regression tests (red at the base):
- Test: for every fixture rule, `_dash_expand_numlist(<rule tokens>)[0] == rules[rule]["values"]` exactly -- test/test_axis_label_grammar.py::TestTheNumlistRule::test_every_rule_reads_back_as_statas (red: NameError on the helper first, then value mismatches)
- Test: `_dash_numlist_value` over each fixture value's `%15.0g` text and over 0.0, -0.0, nan, inf -- ::TestTheNumlistRule::test_the_helper
- Test: both modes' y FixedTicker for the three drawn rules equals the fixture's twoway ticks exactly -- ::TestZeroLabel::test_ticks_are_twoways[saved|served]
- Test: the saved page's y tick formatter writes `0` for the zero tick (run the page's formatter code under node through test/js_runner.py; reuse the harness a formatter test already uses, `grep -ln "CustomJSTickFormatter\|formatter" test/test_*axis*.py`) -- ::TestZeroLabel::test_the_label_is_0
cscript: Q3408-1.
Pinned tests to flip: none expected; any test comparing raw `a + b*k` floats is flipped with "numlist rounds each value as %15.0g (WP-34 DG-3)".
Parity: append `_case("ylabel crossing zero", [_sc()], go={"ylabel": "-.3(.1).3"})` to `CORPUS`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Every rule's values | pytest | numlist_truth.json rules | n/a |
| Drawn ticks | pytest | numlist_truth.json drawn | yes |
| Zero label text | node | -- | saved |
| Live twoway vs dash | cscript Q3408-1 | -- | saved |
| Parity | CORPUS | -- | yes |

AC-34-08.1 every fixture rule's values equal Stata's; AC-34-08.2 the zero tick is 0.0 and labelled 0 in both modes; AC-34-08.3 one green commit.

## Tasks

**Commit boundary.** 34-08-01 to 34-08-03 form one commit, subject `Make each numlist value as Stata's numlist makes it, so a zero tick is 0 (WP-34 DG-3)`, made by 34-08-03 on branch `wp34-s08` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s08`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (34-08-03 for DG-3) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-08/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-08 <scratch>/34-08/run_test_wp33_truth.do` and read `<scratch>/34-08/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-08/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-08-01">
  <name>Record Stata's numlist values and failing tests</name>
  <files>scripts/extract_numlist_truth.do, test/test_axis_label_grammar.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read _dash_expand_numlist at the batch-34.2 base; run `node .gitnexus/run.cjs impact "_dash_expand_numlist" --direction upstream --repo .` and write callers and anchors to <scratch>/34-08/anchors.txt. Create the extractor per TR-34-08.4, run it, `git add -f test/fixtures/numlist_truth.json`. Add TestTheNumlistRule and TestZeroLabel to test/test_axis_label_grammar.py (tokens of a rule are `rule.split()`; pages through the file's `_figures` helper). Insert the S08 block where the Stata truth section says. Run `python3 -m pytest test/test_axis_label_grammar.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-08/01.log`, the S08 block with WP34_ONLY=S08, and save the failures to <scratch>/34-08-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/numlist_truth.json'));print(d['rules']['-.3(.1).3']['values'][3], d['rules']['0(.3333333333333333)1']['text'])"` prints `0.0 0 .3333333333333 .6666666666667 1`; `grep -c FAILED <scratch>/34-08/01.log` is at least 3; `test -s <scratch>/34-08-01-failure.txt`.]]></verify>
  <done>Stata's numlist values for 33 rules were recorded and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-08-02">
  <name>Round each numlist value as Stata does</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Add _dash_numlist_value (TR-34-08.1) and use it for every value _dash_expand_numlist makes (TR-34-08.2); add the copy-list entry and the function map row (TR-34-08.3). Run test/test_axis_label_grammar.py, test/test_axis_options.py, test/test_axis_label*.py, test/test_minor_ticks*.py, test/test_reference_lines*.py, test/test_added_text*.py (the callers' files; find more with `grep -ln "_dash_expand_numlist\|xlabel(\|ylabel(" test/test_*.py | head -40` and run those that name a(b)c rules), test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName and test/test_function_test_map.py; flip only tests that compared raw `a + b*k` floats, with the reason in Pinned tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_label_grammar.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py -q -n0 -p no:cacheprovider` ends with 0 failed.]]></verify>
  <done>Every numlist value matches Stata's and a rule crossing zero ticks exactly 0 in both modes.</done>
</task>

<task type="auto" id="34-08-03">
  <name>Pin the help sentence and close DG-3</name>
  <files>dash.sthlp, test/test_mode_parity.py, test/test_axis_label_grammar.py</files>
  <action><![CDATA[
Help: after the sentence ending "with Stata's own {cmd:numlist} before the dashboard is drawn, and the renderer reads the same grammar for a spec written by hand;" (dash.sthlp:4520-4521) the paragraph already claims numlist; append to that paragraph the sentence "Each value is the one {cmd:numlist} makes, so a rule that crosses zero, such as {cmd:ylabel(-.3(.1).3)}, labels its middle tick 0." and add test/test_axis_label_grammar.py::TestZeroLabel::test_the_help_sentence (the `_between(_help(), ...)` pattern). Append the CORPUS entry to test/test_mode_parity.py. Append `[WP-34 DG-3: corrected -- every numlist value is the one Stata's numlist makes, so a zero tick is labelled 0]` to the Axes row of TWOWAY_COVERAGE_AUDIT.md (:140; M13, G1, REVIEW R2-9). Close the BUGS.md entry 33-01 registered for DG-3 (closed form: _dash_numlist_value rounds each value of _dash_expand_numlist as %15.0g, both modes; pinned by test/test_axis_label_grammar.py::TestTheNumlistRule::test_every_rule_reads_back_as_statas and Q3408-1; fixture numlist_truth.json); rewrite `- **DG-3 Tracked:**` to the Closed form with `commit pending`; delete DG-3's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- A label or tick rule that crosses zero labels its zero tick 0 (ylabel(-.3(.1).3): 5.551e-17 -> 0) (WP-34, DG-3)` under `### Fixed in WP-34`. Run the Closing steps for DG-3 (Tasks; BRIEF steps (1)-(3)): (1) delete DG-3's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py DG-3`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-08) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_axis_label_grammar.py, test/test_mode_parity.py -k "crossing zero", test/test_help_conformance.py, test/test_tracking_documents.py, test/test_fixtures_are_committed.py and the S08 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_label_grammar.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3408-1 PASS" <scratch>/34-08/run_test_wp34_truth.log` prints 1; `awk -F'\t' '$1 == "DG-3"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py DG-3` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-08/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 DG-3)`.]]></verify>
  <done>Zero-crossing label rules write 0 and every numlist value matches Stata's, and DG-3 is closed in one commit.</done>
</task>

## Section completion criteria

- 33 fixture rules' values and counts exact; the three drawn rules' ticks equal twoway's in both modes; the zero label is 0; the helper in the copy list and the function map; help sentence pinned; tracking documents and the Axes coverage-audit row tagged; one green commit.

## Notes

- **Help (R3):** this section owns the one sentence it appends to the paragraph at dash.sthlp:4518-4524.
- **Trap:** `float("%.*f" % (d, v))` can give `-0.0`; the `or 0.0` returns positive zero.
- **Trap:** count from the unrounded `a`, `b`, `c` (D-34-08.a): rounding `c` first would change the count for a rule whose end is not a short decimal.
- **Commit body line forms:** `Regression: test/test_axis_label_grammar.py::TestTheNumlistRule::test_every_rule_reads_back_as_statas -- failed at <base sha> with <text>`; `Fixture: test/fixtures/numlist_truth.json (scripts/extract_numlist_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: DG-3 Tracked`.
- Merge rules touched: R1, R2, R3, R6 (function map), R7, R8.
