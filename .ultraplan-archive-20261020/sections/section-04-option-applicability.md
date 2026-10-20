# Section 04: Option applicability per plot type

> Part of: WP-31 · GAPS3 rows: C3 (A12; the open BUGS.md kernel() entry) · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: 05, 06 · Tasks: 4, 1 commit · Case-id prefix: U04

## Overview

**What is wrong today.** GAPS3 C3 (GAPS3.md:122) reads: "Options twoway refuses on a type are dropped in silence: `kernel() n() level() bwidth() bands() range() base()` are written to every spec with no applicability table; only fpfit/fpfitci warn. BUGS.md open entry." Its evidence is dash.ado:4448-4449 (the JSON key list writes every declared option whatever the type) and :2987-3010 (the rules have no type list). The open BUGS.md entry is "kernel() on a type that takes no kernel is written to the spec without a note" (BUGS.md:2601). The same silence covers `degree()` on anything but lpoly/lpolyci, `bin() width() start()` outside histogram, and `barwidth()` on the types WP-30 S14 left for P2.21 (rspike, rscatter, rarea, rline, rconnected, scatter, line: twoway r(198) "option barwidth() not allowed", measured 03oct2026, `.ultraplan-archive-20261010/wp30/section-14-bar-widths-caps.md` "Stata truth"). `dash scatter mpg weight, kernel(gaussian) n(5) level(80) bwidth(.3) bands(4) range(1 2) base(3)` is rc 0 with no note; twoway refuses the first of those with r(198).

**Why twoway refuses them.** research/stata-ground-truth.md §0: every plot parser leaves undeclared options in `.options`; the graph class strips `xaxis() yaxis() serset()` and runs `syntax [, FAKE_OPT_FOR_BETTER_MSG ]` on the rest (`twowaygraph_g.class:268`), so an option a type does not declare is refused by Stata's compiled `syntax` with the standard `option X() not allowed` r(198). Which type declares which option is the parse-class table of §1.1-1.3: `n() range()` lfit qfit lfitci qfitci fpfitci (and kdensity, function with their own forms; mspline/mband `n()`); `level()` lfitci qfitci fpfitci lpolyci; `bwidth()` lowess lpoly lpolyci kdensity; `kernel()` lpoly lpolyci kdensity; `degree()` lpoly lpolyci; `bands()` mspline mband; `base()` the BarOrBarDerived viewtypes (bar area dot dropline scatteri spike rbspike); `bin() width() start()` histogram (width also kdensity's bwidth synonym); `barwidth()` the bar-derived types plus rbar/rbarm/histogram. The exact spelling of the refusal (parentheses, casing) "needs measurement" (§0, §1.4): nothing is transcribed, everything is measured by this section's extract script.

**After this section** `_dash_option_rules` carries an `applies` table, one token per option, `opt@type|type|...`, GENERATED from `test/fixtures/applicability_truth.json` by `scripts/gen_applicability_table.py`; `_dash_validate_opts` refuses an option written on a type outside its list with twoway's measured line and r(198), before the value rules run (so a bad value on a wrong type is refused for the type first, as twoway's `syntax` refuses it before any class reads a value). Every pair twoway accepts stays accepted; nothing twoway accepts is newly refused (AC-04.3). The applies table is also what S05 and S06 build on: their relaxed value bounds apply only where the option applies.

**Why these rows share this section.** C3 is one row; A12 is its DROPIN id; the BUGS.md kernel() entry is the same defect for one option. One commit `(WP-31 C3)`.

**Test order and commit rule (rule 7, BRIEF).** 04-01 writes and runs the extractor (twoway only), writes `test/test_option_applicability.py` red against the unmodified tree, saves `<scratch>/04-01-failure.txt`, never commits. 04-02 writes the generator, the table and the check. 04-03 flips the pins, moves the counts and adds the cscript cases. 04-04 updates the help, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, GAPS3 Tracked, CHANGELOG and commits once.

### Section decisions (binding on the executor)

- **D-04.a The table is data, generated, never typed.** `scripts/gen_applicability_table.py` reads the fixture and rewrites the lines between `// BEGIN applies` and `// END applies` in `_dash_option_rules`; `test_option_applicability.py::TestTheTableIsTheFixture` regenerates to a string and compares. A hand edit of the table fails that test.
- **D-04.b Accepted = rc 0 in the fixture.** An option applies to a type when `twoway <type> ..., <opt>(<value>)` returned rc 0; it does not apply when rc 198 and the message line matches `option <opt>() not allowed`. Any other rc (a class-level message, r(111), r(103)) is recorded with its text and the pair is treated as applying (dash's own value rules then run), so no pair is refused on a message this section did not measure.
- **D-04.c The check sits before the typed-rule loop.** In `_dash_validate_opts`, after the `colorcuts`/`colorlevels` block and before `local typed ""` (dash.ado:3920-3923), against `s(<opt>)` by value; `ptype` is `_rc_own`, the layer's own type (recast is read by the renderer, twoway refuses on the parser's type). Echoed text is the option's name from the table, never user text.
- **D-04.d Pending entries that cannot fire are deleted.** When an option is refused on every type where dash does not draw it (today `bands` on kdensity, named by `PLOT_VALUES["bands"]` test_unsupported_report_is_true.py:91), its `PLOT_VALUES` entry goes. At `6370ca4` NO `_dash_pending` line names any of the twelve options (`grep -n "_dash_pending' bands" dash.ado` prints nothing; the kdensity naming comes from the generic catch-all, REVIEW-1 R1-10), so no dash.ado pending line is deleted. The plot count in `test_the_blocks_were_actually_found` (:262, `== 43` at the base) moves only if `_plot_pending()` changes, with the measured `# <old> -> <new>: C3 <why>` comment (A33: the old value is the one read at this worktree's base).
- **D-04.e `width` is measured on kdensity as its own name.** `_dash_fold_bw` turns kdensity's `width()` into `bwidth()` before validation, so the table's `width@...` row lists histogram and kdensity as the fixture measures them; the fold leaves nothing for the check to see on kdensity. Same for `bw()` (folds to barwidth or bwidth first).
- **D-04.f `horizontal`/`vertical` and the stat flags stay where they are.** `_dash_hz_check` and `flags` already refuse them with measured words; the extractor records them for the record but the table lists value options only (the twelve of the probe table).

## Risk: [yellow] -- a new refusal on every segment, and tests across the tree write options on types they never meant

**Why.** Every `dash` command passes the check; a wrong table row refuses what twoway draws. Dozens of test specs use `n()`, `level()`, `base()` on convenient types.

**Risk factors.** 1. A typo in the generated table. 2. A test that draws `bands()` on kdensity or `level()` on scatter to probe a note. 3. `_dash_fold_typed` names options after validation; a now-refused option must not also be named. 4. Batch 1 partners S02 and S03 declare options (`mangle barbsize headlabel mwidth`); their rules must not be in this table (no fixture row, no token). 5. S05/S06 edit the same `local plot` block in batch 2: their tokens are value kinds, this section's are the `applies` block only.

**Mitigation.** 1. D-04.a: the table is regenerated and compared by a test. 2. 04-01 runs the directly covering files (list in Evidence) on a simulated table and records the red nodes; 04-03 flips them with `Flipped:` lines (R9). 3. The check exits before `_dash_fold_typed` runs (:5594 is after :5584). 4. The probe set is the twelve options of the table below, nothing S02/S03 declares. 5. The `applies` block is its own `local applies` with its own markers, placed after `local onevalue` (:3073); S05/S06 never touch it (index R12 owner table: rules table S04 in batch 1, S05 then S06 in batch 2 for disjoint tokens).

## Dependencies

- **Depends on: 01** (BUGS.md entry "C3" opened, GAPS3 `## 9. Tracking` line, CHANGELOG markers; no truth block: S04 is refusal-only, D-01.e).
- **Blocks: 05, 06.** Both relax value bounds that are meaningful only where the option applies (S05 `level`, `bwidth`, `n`, `range`; S06 `degree`); their extractors probe accepted pairs only.
- **Parallel batch: 1**, merge order 04, 02, 03. Can run with S02 (pc mappers, `MANGle BARBSize HEADlabel` declarations) and S03 (`map_rbar`, `map_dot`, `MWidth`, `_dash_recast_opt`): none edits `_dash_option_rules`, `_dash_validate_opts`, `test_option_validation.py`'s contract or `test_unsupported_report_is_true.py`'s counts. S02 and S03 do edit the `syntax` block and the pending blocks (R6: append in place; R10: each moves the counts it changes with its own comment; the merger resolves the adjacent `# old -> new` lines in order 04, 02, 03).

## Evidence

Anchors at `6370ca4` (dash.ado 11,039 lines, dash_render.py 52,280).

### The rules have no type column

`_dash_option_rules` (dash.ado:2987-3079); the plot tokens :2990-3008:

```stata
2995        yaxis=int,1,2  xaxis=int,1,2 ///
2997        base=num  barwidth=pos  level=num,0,100,x ///
2998        degree=int,0,3  bwidth=pos,1@lowess  bwidth=pos ///
2999        kernel=enum,epanechnikov|epan2|biweight|cosine|gaussian|parzen|rectangle|triangle ///
3000        n=int,1,300@mspline  n=int,2,10000  bin=int,1,1000  width=pos  start=num  bands=int,1,200 ///
3005        colorcuts=numlist,1  colorvar=var  mlabel=var  range=numlist,2,2 ///
3073    local onevalue "barwidth@rbar|histogram|rcap|rspike  base@rbar|histogram"
```

The `@type` suffix today means "this VALUE rule for these types" (research/codebase-mechanics.md §1a step 4); the untyped twin covers every other type. There is no token saying "refused on these types". `flags` (:3064-3066) is the only applicability list, for bare flags.

`_dash_validate_opts` (:3837-4012) runs the flags (:3859-3872), the std/discrete/colorcuts pairs, then builds `typed` (:3920-3932) and the rule loop (:3933-3969). The check goes before `local typed ""`.

### The JSON writer writes every key

`_dash_plot_opts_to_json` (:4400-4477), key list :4441-4458 includes `bwidth degree ... kernel n level bands ... range` unconditionally. A kernel on scatter is `{"kernel":"gaussian"}` in the spec, read by nothing.

### The refusal patterns that exist

research/codebase-mechanics.md §1d(c): (i) `flags`; (ii) typed value rule; (iii) the typed-spelling Mata pattern (`_dash_barwidth_typed`, dash_parse.mata:6514-6528, with the block at dash.ado:5564-5574); (iv) `onevalue`. This section adds pattern (v), the `applies` table, read in `_dash_validate_opts`.

### Fixtures on disk

None for applicability. `test/fixtures/bar_geometry_truth.json` `refusals.*` holds barwidth's measured lines on 12 types (S14) and is the template for the message form (`option barwidth() not allowed`).

### Existing tests that pin today's behaviour (flip, never delete)

Measured by grep at `6370ca4`; 04-01 re-measures on a simulated table (Tasks).

| Node | Today | After |
|---|---|---|
| test/test_unsupported_report_is_true.py `PLOT_VALUES["bands"]` = ("20","55","kdensity") (:91) and `test_every_pending_option_is_covered` | bands named on kdensity | bands refused on kdensity; the `PLOT_VALUES` entry deleted (no dash.ado pending line exists, D-04.d); `test_the_blocks_were_actually_found`'s plot count moves only if `_plot_pending()` changes, from the measured base value (A33) |
| test/test_unsupported_report_is_true.py:725 `len(_declared_plot()) == 196` | 196 | unchanged by S04 (no declaration added); S02/S03 move it |
| test/test_option_validation.py `CONTRACT_PLOT_RULES` (:75-90) and `test_every_kind_is_one_the_validator_knows` | 41 tokens, kinds list | unchanged tokens; a new `TestTheAppliesTable` is added in test_option_applicability.py, not here |
| test/test_option_validation.cscript OV-67 `kdensity n(1)` (:674) | rc 198 naming n() | unchanged (n applies to kdensity; the value bound is S05's) |
| test/test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed (:1410, `_CONTEXT` :1380) | derives from the pending blocks | follows the deleted `bands` line automatically |
| test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue (:938-960) | Unsupported list == pending blocks | the `bands` line leaves the help list in the same commit (04-04) |
| any test spec drawing a C3 option on a type twoway refuses (04-01 lists them from the simulated run) | rc 0 | r(198); the spec moves to a type that takes the option, with a `Flipped:` line |

## User stories

- **US-04.1** As a Stata user pasting a twoway command after `dash`, I want `dash scatter mpg weight, kernel(gaussian)` refused with the line and code twoway gives, so a do-file that fails in Stata does not silently succeed in dash.
- **US-04.2** As the same user, I want every option twoway accepts on a type still accepted on it, so no working command breaks.
- **US-04.3** As a maintainer, I want the per-type table generated from a measured fixture, so a new option or type is added by re-running one script.

## Business requirements

- **BR-04.1** For every (option, type) pair of the probe table where twoway returned r(198) `option <opt>() not allowed`, dash returns r(198) and prints that same line (the first error line of the logged output), in comma mode, inside `( )` and after `||`.
- **BR-04.2** For every pair where twoway returned rc 0, dash returns rc 0 with no new note and the spec carries the option as before.
- **BR-04.3** No pair outside the probe table changes behaviour.
- **BR-04.4** The refusal comes before any value check: `dash scatter mpg weight, kernel(nosuch)` names the type's refusal, not the kernel name (twoway's `syntax` runs before any class reads a value).
- **BR-04.5** An option refused on every non-drawing type is no longer listed as "accepted and not honoured" in the help or the note.

## Technical requirements

- **TR-04.1 Extractor** `scripts/extract_applicability_truth.do` (Stata truth below) writes `test/fixtures/applicability_truth.json`.
- **TR-04.2 Generator** `scripts/gen_applicability_table.py` (new, ~60 lines, standard library only): `python3 scripts/gen_applicability_table.py [--check]`. Reads the fixture; for each option of `OPTIONS = ("kernel","n","level","bwidth","bands","range","base","degree","bin","width","start","barwidth")` collects the types with `rc == 0` in the fixture's `pairs`, in `TYPES` order (the 40 types below), and emits one line `        <opt>@<t1>|<t2>|... ///` (eight spaces, trailing ` ///` on every line but the last). It replaces the text between the lines `    // BEGIN applies (generated by scripts/gen_applicability_table.py from test/fixtures/applicability_truth.json; do not edit)` and `    // END applies` in dash.ado, keeping both markers. `--check` prints the would-be block and exits 1 if dash.ado differs. It never reads any other file and writes dash.ado only without `--check`.
- **TR-04.3 The table.** In `_dash_option_rules`, after `local onevalue ...` (:3073) and before `c_local _dash_rules_plot` (:3074), insert:
  ```stata
      // Applicability (WP-31 C3, A10): opt@type|type|... lists the plot
      // types twoway accepts the option on; on any other type dash refuses
      // it as twoway's syntax does, r(198) "option <opt>() not allowed"
      // (measured per pair: test/fixtures/applicability_truth.json).
      // BEGIN applies (generated by scripts/gen_applicability_table.py from test/fixtures/applicability_truth.json; do not edit)
      local applies ///
          kernel@lpoly|lpolyci|kdensity ///
          ... one line per option, as generated ...
      // END applies
  ```
  and after `c_local _dash_rules_onevalue "`onevalue'"` add `c_local _dash_rules_applies "`applies'"`. The generator writes the `local applies ///` line and the option lines; the comments and markers are typed once by 04-02.
- **TR-04.4 The check** in `_dash_validate_opts`, inserted after the `_cvcl` block (:3918) and before `// Options that have a type-specific rule for THIS type` (:3920):
  ```stata
      // Applicability (WP-31 C3): an option on a type twoway's parser does
      // not declare falls to Stata's syntax there and is refused before any
      // value is read; the same here, naming the option from the table.
      foreach tok of local _dash_rules_applies {
          local at    = strpos("`tok'", "@")
          local o     = substr("`tok'", 1, `at' - 1)
          local types = substr("`tok'", `at' + 1, .)
          local types : subinstr local types "|" " ", all
          if `: list ptype in types' continue
          mata: st_local("_ap_v", strofreal(st_global("s(" + st_local("o") + ")") != ""))
          if `_ap_v' {
              display as error "option `o'() not allowed"
              exit 198
          }
      }
  ```
  The message text is a literal copied from the fixture's `message` field after 04-01 measured it; if the fixture's line differs from `option <opt>() not allowed` for any pair, 04-02 writes the fixture's form and `test_the_message_is_twoways` compares them per option.
- **TR-04.5 Pending entries and counts (D-04.d).** 04-02 runs `grep -n "bands" dash.ado` and `grep -n "_dash_pending' \(kernel\|n\|level\|bwidth\|bands\|range\|base\|degree\|bin\|width\|start\|barwidth\)\"" dash.ado`: at `6370ca4` the second prints nothing (no pending line names any of the twelve; `bands` appears only in the rules token :3000, the JSON key list and the mspline/mband type rule :5637-5690 `_pt_bands`), so no dash.ado line is deleted. Delete `PLOT_VALUES["bands"]` (test_unsupported_report_is_true.py:91). Then run `python3 -m pytest test/test_unsupported_report_is_true.py -k blocks -q -n0 -p no:cacheprovider`: if `test_the_blocks_were_actually_found` fails because `_plot_pending()` changed, move its plot count from the value read at the base (`== 43`, :262) to the measured one with `# 43 -> <new>: C3 bands is refused where it is not drawn`; if it passes, the count is not edited. `_dash_rep_und_tab` has no row for any of the twelve: nothing to delete there.
- **TR-04.6 `_dash_fold_typed`** (:2201-2272) is not edited: the check exits first.
- **TR-04.7 Renderer.** No change: the spec never carries a refused option. `_dash_plot_opts_to_json`'s list is unchanged (the keys still serve the accepting types).
- **TR-04.8 Maps.** test/program_coverage_map.py `COVERAGE["dash.ado"]`: no new program (the check lives in `_dash_validate_opts`, already mapped); add under a `# WP-31 S04 (C3)` comment `"_dash_option_rules": ("test_option_validation.cscript:U04-01",)` only if the key is absent (grep first). test/function_test_map.py: nothing (no Python function added).
- **TR-04.9 Security (rule 1).** The echoed name is a table literal; user text is tested for presence only (`!= ""`), never displayed; no `shell`, no `eval`.

## Boundaries

- Not S04's: `horizontal`/`vertical` (`_dash_hz_check`), the stat flags (`flags`), `mlabel()` (`_dash_fold_mlab`, S06 for the element rule), `colorvar()` companions (twoway drops them silently on area/rarea/fits, `yxview_parse:206-208`; S15/S17), `jitter()` (S15), `barwidth()` lists (`onevalue`), the value bounds of any option (S05, S06), axes 3-9 (S09), the declarations S02 (`MANGle BARBSize HEADlabel`) and S03 (`MWidth`) add, dash.sthlp paragraphs other than "Option values" lines :838-840 and the Unsupported list's `bands` sentence, the JSON key list.
- PRD §7: no module split; no new dependency.

## Stata truth

**New extractor** `scripts/extract_applicability_truth.do`, in `scripts/extract_default_base_truth.do`'s head form (the `DASH_REPO` root with guards, :21-43; `adopath ++`, the mata and ado loaded, `global dash_nobrowser 1`, :45-48; the work directory; `quietly shell git -C "${ZB_REPO}" rev-parse HEAD > "${ZB_WORK}/git_head.txt"`; the python block reads it through `Macro.getLocal`/the file, never `shell=True`). Run only as

```sh
DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s04 $WT/scripts/extract_applicability_truth.do
```

Data: `sysuse auto, clear`; `gen yl = mpg - 1`; `gen yh = mpg + 1`; `gen t = _n`; `tsset t`. Every probe is `capture noisily twoway <type-command>, <opt>(<value>) nodraw` with the log of that one command captured (`log using "${ZB_WORK}/p.log", replace text` around it), `local rc = _rc`, and the message line = the first line of the log beginning `option ` or otherwise the first line after the command echo; both recorded.

**Type commands** (`TYPES`, 40, the dash.ado "Supported:" set):

| Type | Command |
|---|---|
| scatter line connected area bar spike dropline dot | `<type> mpg weight` |
| tsline | `tsline mpg` |
| tsrline | `tsrline yl yh` |
| rarea rbar rspike rcap rline rconnected rcapsym rscatter | `<type> yl yh weight` |
| pcspike pccapsym pcarrow pcbarrow pcscatter | `<type> mpg weight trunk turn` |
| pci pcarrowi | `<type> 20 2000 30 4000` |
| scatteri | `scatteri 20 2000` |
| lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband | `<type> mpg weight` |
| kdensity histogram | `<type> mpg` |
| function | `function y = x` |

**Options and probe values** (`OPTIONS`, 12): `kernel(gaussian)`, `n(50)`, `level(90)`, `bwidth(.5)`, `bands(5)`, `range(1 10)`, `base(0)`, `degree(1)`, `bin(5)`, `width(1)`, `start(0)`, `barwidth(.5)`. 480 probes.

**Expected per research §1.2-1.3** (the fixture decides; this column is the reading check): kernel -> lpoly lpolyci kdensity; n -> lfit qfit lfitci qfitci fpfitci lpoly lpolyci kdensity function mspline mband; level -> lfitci qfitci fpfitci lpolyci; bwidth -> lowess lpoly lpolyci kdensity; bands -> mspline mband; range -> lfit qfit lfitci qfitci kdensity function (fpfitci refuses); base -> bar area dot dropline spike scatteri (+ rbar histogram per `onevalue`, measured); degree -> lpoly lpolyci; bin width start -> histogram (width also kdensity); barwidth -> bar area dot dropline spike scatteri rbar histogram (rcap rcapsym rspike rscatter rarea rline rconnected scatter line refuse, S14's measurement). A result that contradicts this column stops 04-01 for a second look at the probe, not at the fixture.

**Fixture** `test/fixtures/applicability_truth.json`:

```json
{"_meta": {"stata_version": "19.5", "born_date": "...", "dash_commit": "<sha>", "extracted": "...",
           "source": "scripts/extract_applicability_truth.do"},
 "options": ["kernel", "n", ...], "types": ["scatter", "line", ...],
 "pairs": {"kernel@scatter": {"cmd": "twoway scatter mpg weight, kernel(gaussian) nodraw",
                              "rc": 198, "message": "option kernel() not allowed"},
           "kernel@lpoly": {"cmd": "...", "rc": 0, "message": ""}, ...}}
```

`git add -f test/fixtures/applicability_truth.json`; `test_option_applicability.py::TestTheFixture` names it (test_fixtures_are_committed.py).

**Truth block:** none. S04 appends no block to `test/test_wp31_truth.cscript` (S01 writes no stub, D-01.e): the comparisons are refusals, which go to the area script (a refusal-only section adds area cases only; index.md R1 says so).

**Area cases** in `test/test_option_validation.cscript`, appended after its last `_ov_case` and before `// Summary`, header lines `*!   U04-01..U04-04` added to its case list:
- **U04-01** for each of twelve pairs twoway refuses (one per option: `scatter kernel(gaussian)`, `scatter n(50)`, `scatter level(90)`, `scatter bwidth(.5)`, `kdensity bands(5)`, `scatter range(1 10)`, `scatter base(0)`, `lowess degree(1)`, `scatter bin(5)`, `scatter width(1)`, `scatter start(0)`, `rspike yl yh weight barwidth(.5)`): `capture noisily twoway ...` and `capture noisily dash ..., name(zu04k)` in the same run, both logged; rc equal (198) and the first error line equal.
- **U04-02** twelve pairs twoway accepts (`lpoly kernel(gaussian)`, `lfit n(50)`, `lfitci level(90)`, `lowess bwidth(.5)`, `mband bands(5)`, `function y=x range(1 10)`, `bar base(0)`, `lpoly degree(1)`, `histogram bin(5)`, `histogram width(1)`, `histogram start(0)`, `bar barwidth(.5)`): dash rc 0 and the logged output holds no `(note:` naming the option.
- **U04-03** forms: `dash (scatter mpg weight, kernel(gaussian))` and `dash lfit mpg weight || scatter mpg weight, kernel(gaussian)` r(198) with the same line.
- **U04-04** order: `dash scatter mpg weight, kernel(nosuch)` prints `option kernel() not allowed` (the type refusal, not the enum message); `dash lpoly mpg weight, kernel(nosuch)` still prints the enum message.

## TDD test stubs

### Regression tests, `test/test_option_applicability.py` (new; red at `6370ca4` unless marked guard)

Helpers: the fixture read once at module level; `_rules_block()` = the `local applies` text of `_dash_option_rules` read from dash.ado by regex between the markers; `_validate(ptype, opts)` runs `_dash_validate_opts` through the existing Stata-free parser harness used by test_option_validation.py (`_parse_rules`, `_program_body`), so the table is checked without Stata; the end-to-end rc checks are the cscript's.

- Test: the fixture exists, `_meta` has the five keys, `pairs` has 480 entries, every pair has `rc` in {0, 198} or a non-empty `message` -- `TestTheFixture::test_meta_is_stamped`, `::test_every_pair_was_measured` (guard after 04-01).
- Test: the `applies` block in dash.ado equals `gen_applicability_table.py --check`'s output -- `TestTheTableIsTheFixture::test_the_block_is_generated` (red: no block).
- Test: for every option, the table's types are exactly the fixture's rc-0 types -- `::test_each_option_lists_its_types[opt]` (red).
- Test: every type in the table is one dash draws (`_dash_plot_type_names` | the Mata table) -- `::test_every_type_exists` (red).
- Test: `_dash_validate_opts`'s body holds the `_dash_rules_applies` loop before `local typed ""` -- `TestTheCheck::test_the_check_precedes_the_value_rules` (red).
- Test: the message literal in the check equals the fixture's message form for every refused pair (all 198 pairs share one form, else the test lists the forms) -- `::test_the_message_is_twoways` (red).
- Test: no `_dash_pending` line names an option of the table; no `PLOT_VALUES` key does -- `TestNothingRefusedIsAlsoNamed::test_pending_blocks`, `::test_plot_values` (red: bands).
- Test: the twelve options stay in `_dash_plot_opts_to_json`'s key list (guard) -- `::test_the_json_keys_are_kept`.

### Cases in cscripts

- `test/test_option_validation.cscript` U04-01, U04-03, U04-04 (red), U04-02 (guard).

### Flips (in place, each with a `Flipped:` line)

- test_unsupported_report_is_true.py: `PLOT_VALUES["bands"]` deleted; `test_the_blocks_were_actually_found`'s plot count moved only if the `-k blocks` run shows `_plot_pending()` changed, from the base's `== 43` to the measured value with `# 43 -> <new>: C3 bands is refused where it is not drawn` (TR-04.5).
- Any node 04-01's simulated run lists (Tasks 04-01): the spec moves to an accepting type, docstring gains "Flipped (WP-31 C3): twoway refuses <opt>() on <type>".

### Parity corpus (R8; guards)

`test/test_mode_parity.py` under `# WP-31 C3: option applicability`: `CORPUS` cases "lpoly kernel(gaussian) degree(1)" and "mband bands(5)" (accepted pairs render alike; a refused pair never reaches the renderer, so none is added).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Table == fixture | pytest `TestTheTableIsTheFixture`; `gen_applicability_table.py --check` | `applicability_truth.json` | n/a |
| Refusal rc and line, three forms | cscript U04-01, U04-03 | `pairs` (the cscript compares live) | n/a |
| Accepted pairs unchanged | cscript U04-02; parity CORPUS | -- | yes |
| Order before value rules | cscript U04-04; pytest `TestTheCheck` | -- | n/a |
| Note and help consistency | pytest `TestNothingRefusedIsAlsoNamed`, test_help_conformance.py, test_unsupported_report_is_true.py | -- | n/a |

**Acceptance criteria**
- **AC-04.1** `python3 scripts/gen_applicability_table.py --check` exits 0 after 04-02.
- **AC-04.2** Every fixture pair with rc 198 is refused by dash with rc 198 and the same first error line (U04-01 samples twelve; `TestTheTableIsTheFixture` covers all 480 by the table).
- **AC-04.3** Every fixture pair with rc 0 is rc 0 in dash with no new note (U04-02 samples twelve).
- **AC-04.4** `python3 -m pytest test/test_option_applicability.py test/test_option_validation.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_help_claims_8.py -q -p no:cacheprovider` reports 0 failed; `test_option_validation.cscript` prints U04-01..U04-04 PASS and `ALL CHECKS PASSED`.
- **AC-04.5** `grep -c "kernel() on a type that takes no kernel" BUGS.md` finds the entry closed (`- [x]`).

## Tasks

**Commit boundary.** 04-01 to 04-04 form the one C3 commit, subject `Refuse an option on a type twoway does not take it on, per measured table (WP-31 C3)`, made by 04-04 on `wp31-s04` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s04`. Body: `<scratch>/04-01-failure.txt`, the measured defect (`dash scatter mpg weight, kernel(gaussian)` rc 0 silent; twoway r(198)), what changed where, then one line each `Regression: test/test_option_applicability.py::<Class>::<test> -- failed at 6370ca4 with <text>`, `Flipped: <node> -- <old> was wrong because twoway refuses <opt>() on <type> (C3)`, `Fixture: test/fixtures/applicability_truth.json (scripts/extract_applicability_truth.do)`, `BUGS.md: "kernel() on a type that takes no kernel is written to the spec without a note" (closed)` and `BUGS.md: "<S01's C3 title>" (closed)`, `GAPS3: C3 Tracked`. No tooling names.

<task type="auto" id="04-01">
  <name>Measure applicability and write failing tests</name>
  <files>scripts/extract_applicability_truth.do, test/fixtures/applicability_truth.json, test/test_option_applicability.py</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints `wp31-s04` and `git -C $WT rev-parse HEAD` equals the batch-1 base sha in `<scratch>/batch-1-base.txt`; `mkdir -p <scratch>/s04`. Create scripts/extract_applicability_truth.do by "Stata truth": copy lines 1-60 of scripts/extract_default_base_truth.do (renaming ZB_ to ZA_ and the output to test/fixtures/applicability_truth.json), then two `foreach` loops over the 40 type commands and the 12 option probes, each probe `capture noisily twoway <cmd>, <opt>(<value>) nodraw` inside `log using "${ZA_WORK}/p.log", replace text` / `log close`, recording rc and the first log line starting with `option ` (else the first line after the echoed command) into Stata locals `rc_<k>` and `msg_<k>`, then one `python:` block writing the JSON with `_meta` (stata_version, born_date, dash_commit from `${ZA_WORK}/git_head.txt`, extracted, source) and `pairs` keyed `<opt>@<type>`, `sort_keys=True`, a backtick written as `\x60`. Run it through the slot (the command under "Stata truth"); `git add -f test/fixtures/applicability_truth.json`. Compare the rc-0 sets per option with the "Expected per research" column; a contradiction stops the task with the pair named. Create test/test_option_applicability.py with exactly the classes of "TDD test stubs". Then simulate the table: `python3 scripts/gen_applicability_table.py` cannot run yet, so write `<scratch>/s04/applies.txt` by hand from the fixture (rc-0 types per option) and grep every test file for specs that put a refused pair on a type: `grep -ln '"kernel"\|"bands"\|"level"\|"degree"\|"range"\|"base"\|"bwidth"\|"bin"\|"start"\|"barwidth"' test/*.py` then read each hit's plot type; list the nodes that would be refused in `<scratch>/s04/04-flips.txt`. Run `python3 -m pytest test/test_option_applicability.py -q -n0 -p no:cacheprovider -rf > <scratch>/s04/04-01.log 2>&1` and write `<scratch>/04-01-failure.txt` (base sha, each failing node with its reason, the guards that passed, the flip list). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/applicability_truth.json'));print(sorted(d['_meta']), len(d['pairs']))"` prints `['born_date', 'dash_commit', 'extracted', 'source', 'stata_version'] 480`; `python3 -c "import json;d=json.load(open('test/fixtures/applicability_truth.json'));print(d['pairs']['kernel@scatter']['rc'], d['pairs']['kernel@lpoly']['rc'])"` prints `198 0`; `grep -c FAILED <scratch>/s04/04-01.log` is at least 6; `test -s <scratch>/04-01-failure.txt`.]]></verify>
  <done>twoway's acceptance or refusal of twelve options on forty types was recorded in a stamped fixture, and the regression tests were shown failing on the unmodified tree with the failure text saved.</done>
</task>

<task type="auto" id="04-02">
  <name>Generate the table and add the check</name>
  <files>scripts/gen_applicability_table.py, dash.ado, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[
    Create scripts/gen_applicability_table.py per TR-04.2 (argparse `--check`; constants OPTIONS and TYPES as in "Stata truth"; the fixture path relative to the script's parent; writes dash.ado in place between the two markers, else exits 1 with the diff printed). In dash.ado `_dash_option_rules`, insert TR-04.3's comment, markers and `local applies` after the `local onevalue` line (:3073) and add `c_local _dash_rules_applies "`applies'"` after `c_local _dash_rules_onevalue ...`; run `python3 scripts/gen_applicability_table.py` to fill the block. Insert TR-04.4's loop in `_dash_validate_opts` after the `_cvcl` block (:3918) and before the `// Options that have a type-specific rule` comment (:3920); the literal message is the fixture's form for the refused pairs (read `pairs['kernel@scatter']['message']`), written exactly. Apply TR-04.5: run the two greps (expect no `_dash_pending` line for any of the twelve; none exists at `6370ca4`); delete `PLOT_VALUES["bands"]` (:91); run `python3 -m pytest test/test_unsupported_report_is_true.py -k blocks -q -n0 -p no:cacheprovider` and move the plot count only if `_plot_pending()` changed, from the base's `== 43` to the measured value with `# 43 -> <new>: C3 bands is refused where it is not drawn`. Run `python3 -m pytest test/test_option_applicability.py test/test_option_validation.py test/test_unsupported_report_is_true.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[`python3 scripts/gen_applicability_table.py --check` exits 0; `grep -c "_dash_rules_applies" dash.ado` prints 3; `grep -c "BEGIN applies" dash.ado` prints 1; `grep -c '"bands"' test/test_unsupported_report_is_true.py` fell by 1 (the `PLOT_VALUES` entry; the `LIVE_VALUES` entry at :452 stays); the pytest run reports 0 failed except the nodes listed in `<scratch>/s04/04-flips.txt`.]]></verify>
  <done>The applicability table was generated from the fixture into dash.ado, the check refused an option on a type outside its list before any value rule, and the unreachable pending line and its test entry were gone.</done>
</task>

<task type="auto" id="04-03">
  <name>Flip pins and add the cscript cases</name>
  <files>test/test_option_validation.cscript, test/test_mode_parity.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    Flip every node of `<scratch>/s04/04-flips.txt` in place: move the spec's option to a type the fixture accepts it on (kernel/degree -> lpoly, bands -> mband, level -> lfitci, range/n -> lfit, base/barwidth -> bar, bin/width/start -> histogram), keep the node name, add to the docstring "Flipped (WP-31 C3): twoway refuses <opt>() on <type>", and append `Flipped: <node> -- <old> was wrong because twoway refuses <opt>() on <type> (C3)` to `<scratch>/s04/04-flips.txt`; a node outside a file this task may edit (one to three per task) is reported to the orchestrator, never deleted. Append U04-01..U04-04 to test/test_option_validation.cscript after its last `_ov_case` and before `// Summary`, in its `nfail`/`faillist` form, each dash line compared with twoway's from the same run; add `*!   U04-01..U04-04` header lines. Append the two parity CORPUS cases under `# WP-31 C3: option applicability` in test/test_mode_parity.py. Add the program_coverage_map.py entry of TR-04.8 if absent. Run the cscript through the driver: `printf 'global dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/test_option_validation.cscript"\n' "$WT" "$WT" > <scratch>/s04/run_ov.do` then `scripts/stata_slot.sh <scratch>/s04 <scratch>/s04/run_ov.do`; then `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "C3"` and the flipped files.
  ]]></action>
  <verify><![CDATA[`grep -c "U04-0[1-4] PASS" <scratch>/s04/run_ov.log` prints 4 and the log ends `ALL CHECKS PASSED`; `grep -c "SKIP" <scratch>/s04/run_ov.log` prints 0; the pytest runs report 0 failed; every line of `<scratch>/s04/04-flips.txt` starts `Flipped: test/`.]]></verify>
  <done>Stata certified dash's refusals against twoway's own in three command forms and the accepted pairs unchanged, and every pin that drew a refused pair was flipped with its reason.</done>
</task>

<task type="auto" id="04-04">
  <name>Document, close C3 and commit</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
    dash.sthlp: in "Differences from twoway" at :838-840 (the sentence listing `bwidth(), n(), bands(), range(), base()` as written to every type) rewrite to say each is accepted only on the plot types twoway accepts it on and refused elsewhere, r(198), `option <opt>() not allowed`, with the per-type list generated from a measured fixture (scripts/extract_applicability_truth.do); delete `bands()` from the Unsupported list sentence that names it (grep `bands` between {marker unsupported} :4967 and {marker dependencies} :5136). TWOWAY_COVERAGE_AUDIT.md: append ` [WP-31 C3: corrected -- options are refused on the types twoway refuses them on]` to the rows of lines 87, 90, 94, 99 where they say an option is accepted and unread. BUGS.md: close the open entry at :2601 ("kernel() on a type that takes no kernel is written to the spec without a note") and S01's "C3" entry, each in BRIEF's Resolution form: `Fixed <ddmonyyyy> (WP-31, C3). _dash_option_rules carries a generated applies table (scripts/gen_applicability_table.py from test/fixtures/applicability_truth.json) and _dash_validate_opts refuses an option on a type outside its list before any value rule, r(198) "option <opt>() not allowed", in both renderers' input path (the spec never carries it). Pinned by test/test_option_applicability.py::TestTheTableIsTheFixture::test_each_option_lists_its_types, test/test_option_validation.cscript U04-01; fixture test/fixtures/applicability_truth.json. Closes GAPS3 C3 (WP-31, C3).`, flip `- [ ]` to `- [x]`. GAPS3.md §9: rewrite the C3 line to `- **C3 Tracked:** Closed in WP-31, BUGS.md "<S01's C3 title>", commit pending.` before the commit (DECISIONS A11: the merger's step k.3b rewrites every `pending` of the batch to the landed sha; no `git commit --amend` anywhere). CHANGELOG.md: replace `<!-- WP-31 C3 -->` under `### Changed behaviour (may need your do-files changed)` with one line per newly refused option: `- <opt>() on <the types twoway refuses it on> is refused, r(198), with twoway's line option <opt>() not allowed; dash accepted it and drew nothing different. (WP-31, C3)` -- twelve lines, the type lists from the fixture's rc-198 sets; replace the marker under `### Fixed in WP-31` with `- Options twoway refuses on a type are refused by dash on that type, per a measured table of twelve options by forty types. (WP-31, C3)`. Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider`. Stage dash.ado, dash.sthlp, scripts/extract_applicability_truth.do, scripts/gen_applicability_table.py, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, CHANGELOG.md, GAPS3.md, the test files 04-01..04-03 changed, and `git add -f test/fixtures/applicability_truth.json`; check `git diff --cached --name-only` names no CLAUDE.md, .ultraplan/ or *.html; write the message to `<scratch>/s04/msg.txt` in the boundary's form; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` must print 0 before and after `git commit -F <scratch>/s04/msg.txt`.
  ]]></action>
  <verify><![CDATA[`git log -1 --format=%s` ends `(WP-31 C3)`; `grep -c '<!-- WP-31 C3 -->' CHANGELOG.md` prints 0; `grep -c "(WP-31, C3)" CHANGELOG.md` prints 13; `grep -c "^- \*\*C3 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; the pytest run reports 0 failed; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>C3 was closed in BUGS.md and GAPS3, the help and audit described the measured per-type refusals, the CHANGELOG named each newly refused form, and one green commit on wp31-s04 was ready for the merger.</done>
</task>

## Section completion criteria

- The `applies` block in `_dash_option_rules` equals the generator's output from the committed fixture; the check runs before the value rules.
- Every rc-198 pair of the fixture is refused with twoway's line and code; every rc-0 pair is unchanged; U04-01..U04-04 PASS.
- `bands` is no longer named by `PLOT_VALUES` or listed in the help; any count moved carries its measured `# old -> new` comment (A33); every flip has a `Flipped:` line.
- BUGS.md entries closed (the kernel() entry and S01's C3), GAPS3 C3 Tracked Closed, CHANGELOG markers replaced, one commit `(WP-31 C3)`.

## Notes

- **Order inside `_dash_validate_opts`.** The applies loop goes BEFORE `local typed ""`. Put it after and `kernel(nosuch)` on scatter names the enum, not the type (U04-04 catches it).
- **`_rc_own` is the parser's type.** `_dash_validate_opts "`_rc_own'"` (dash.ado:5584): a `scatter ..., recast(line) kernel(x)` is refused as scatter, which is what twoway does (its parser is scatter's).
- **Folds first.** `_dash_fold_bw` (:5578) runs before the check: kdensity `width()` is already `bwidth`, `bw()` already `barwidth`/`bwidth`, lowess's bare kernel words already `kernel`. The table therefore lists what reaches `s()`, which the fixture measured by twoway's own names; a mismatch shows only on kdensity `width`, which the fixture records as accepted (D-04.e).
- **python_exec hazard** (project memory): check `~/.stata19/console/stata19.rc` holds `python_exec` after 04-01 and 04-03; a SKIP is not a pass.
- **Shared files (R1-R13).** R1: area cases in test_option_validation.cscript only; no truth block content. R2: nothing copied (no renderer change). R3: dash.sthlp :838-840 and the Unsupported `bands` sentence only. R4: the C3 markers only (two lists). R5: two BUGS entries (the pre-existing kernel() entry and S01's). R6: `_dash_option_rules` gains one local and one `c_local`; `_dash_validate_opts` one loop. R7: new fixture, stamped, `git add -f`. R8: two CORPUS cases. R9: flips recorded. R10: the plot count only if `_plot_pending()` changed, with its measured `# old -> new` comment (A33). R12: S04 is batch 1's `_dash_option_rules` editor; it does not edit `_make_figure_body`, `_generate_app_source` or any applier.
- **For S05 and S06 (batch 2).** The `applies` block is regenerated, never edited, by them either; their tokens go in `local plot`. S05's `level=num,10,99.99@lfitci|qfitci|fpfitci|lpolyci` replaces the untyped `level` rule only because `level` now applies to those four alone (this table). S06's `degree=int,0,7` likewise applies to lpoly/lpolyci alone.
- **For S09 (batch 3).** `yaxis`/`xaxis` are stripped by twoway's graph class before `syntax`, so they are not in this table; S09 owns their bounds.
- **For S56 (help reconciliation).** The per-type lists are long; S56 may move the twelve type lists into a table under "Differences from twoway" generated from the same fixture.
- **Commit body line forms** are BRIEF's with WP-31 ids; `failed at` is `6370ca4` (batch-1 base).
